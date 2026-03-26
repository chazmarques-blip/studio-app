"""Directed Studio v2 — Screenwriter Chat + Multi-Scene Video Production."""
import uuid
import base64
import os
import asyncio
import urllib.request
import litellm
import threading
import subprocess
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv(override=False)

# Set OpenAI client to NOT retry internally (we handle retries ourselves)
os.environ["OPENAI_MAX_RETRIES"] = "0"

from core.deps import supabase, get_current_user, get_current_tenant, logger
from pipeline.config import STORAGE_BUCKET, EMERGENT_PROXY_URL, ELEVENLABS_VOICES, MUSIC_LIBRARY

router = APIRouter(prefix="/api/studio", tags=["studio"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


# ── Ensure FFmpeg is available (runs once at module load) ──

_ffmpeg_checked = False

def _ensure_ffmpeg():
    """Check if FFmpeg is installed, install it if missing. Idempotent."""
    global _ffmpeg_checked
    if _ffmpeg_checked:
        return True
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            _ffmpeg_checked = True
            logger.info("Studio: FFmpeg is available")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    logger.warning("Studio: FFmpeg not found, attempting install...")
    try:
        subprocess.run(["apt-get", "update", "-qq"], capture_output=True, timeout=30)
        result = subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], capture_output=True, timeout=120)
        if result.returncode == 0:
            _ffmpeg_checked = True
            logger.info("Studio: FFmpeg installed successfully")
            return True
        else:
            logger.error(f"Studio: FFmpeg install failed: {result.stderr.decode()[:200]}")
    except Exception as e:
        logger.error(f"Studio: FFmpeg install error: {e}")
    return False

# Run check at import time
_ensure_ffmpeg()


# ── Direct Sora 2 Client (no proxy) ──

from core.llm import DirectSora2Client


# ── Helpers ──

def _get_settings(tenant_id: str) -> dict:
    for attempt in range(3):
        try:
            r = supabase.table("tenants").select("settings").eq("id", tenant_id).single().execute()
            return r.data.get("settings", {}) if r.data else {}
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(1 * (attempt + 1))
            else:
                logger.error(f"_get_settings failed after 3 attempts: {e}")
                raise

def _save_settings(tenant_id: str, settings: dict):
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    for attempt in range(3):
        try:
            supabase.table("tenants").update({"settings": settings}).eq("id", tenant_id).execute()
            return
        except Exception as e:
            if attempt < 2:
                import time
                time.sleep(2 * (attempt + 1))
                logger.warning(f"_save_settings retry {attempt+1}: {e}")
            else:
                logger.error(f"_save_settings failed after 3 attempts: {e}")
                raise

def _get_project(tenant_id: str, project_id: str):
    settings = _get_settings(tenant_id)
    projects = settings.get("studio_projects", [])
    project = next((p for p in projects if p.get("id") == project_id), None)
    return settings, projects, project

def _save_project(tenant_id: str, settings: dict, projects: list):
    settings["studio_projects"] = projects
    _save_settings(tenant_id, settings)

def _update_project_field(tenant_id: str, project_id: str, updates: dict):
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        return
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(project.get(k), dict):
            project[k].update(v)
        else:
            project[k] = v
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant_id, settings, projects)


def _add_milestone(project: dict, key: str, label: str):
    """Add a milestone to the project if not already present."""
    milestones = project.get("milestones", [])
    if not any(m.get("key") == key for m in milestones):
        milestones.append({"key": key, "label": label, "done": True, "at": datetime.now(timezone.utc).isoformat()})
        project["milestones"] = milestones


def _cleanup_stale_storyboards():
    """Reset stale storyboard statuses that were orphaned by hot-reloads."""
    try:
        tenants = supabase.table("tenants").select("id, settings").execute().data or []
        cleaned = 0
        stale_phases = {"starting", "generating"}
        for t in tenants:
            settings = t.get("settings") or {}
            projects = settings.get("studio_projects", [])
            dirty = False
            for proj in projects:
                sb_status = proj.get("storyboard_status", {})
                if sb_status.get("phase") in stale_phases:
                    panels = proj.get("storyboard_panels", [])
                    done = sum(1 for p in panels if p.get("image_url"))
                    proj["storyboard_status"] = {
                        "phase": "complete" if done > 0 else "error",
                        "current": len(panels), "total": len(panels),
                        "recovered": True,
                    }
                    dirty = True
                    cleaned += 1
                # Also recover stale continuity tasks
                cs = proj.get("continuity_status", {})
                if cs.get("phase") in ("analyzing", "correcting"):
                    proj["continuity_status"] = {"phase": "error", "detail": "Recovered after restart", "recovered": True}
                    dirty = True
                    cleaned += 1
            if dirty:
                _save_settings(t["id"], settings)
        if cleaned:
            logger.info(f"Studio startup: Recovered {cleaned} stale storyboard tasks")
    except Exception as e:
        logger.warning(f"Studio stale cleanup failed: {e}")


def _upload_to_storage(file_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
    """Upload to Supabase Storage with retry and chunked fallback for large files."""
    file_size_mb = len(file_bytes) / (1024 * 1024)

    # For files under 45MB, use the standard client upload
    if file_size_mb < 45:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            filename, file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    # For larger files, use the REST API directly with proper headers
    import httpx
    supabase_url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or not service_key:
        # Fall back to standard upload
        supabase.storage.from_(STORAGE_BUCKET).upload(
            filename, file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    upload_url = f"{supabase_url}/storage/v1/object/{STORAGE_BUCKET}/{filename}"
    headers = {
        "Authorization": f"Bearer {service_key}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }

    for attempt in range(3):
        try:
            with httpx.Client(timeout=300) as client:
                resp = client.put(upload_url, content=file_bytes, headers=headers)
                if resp.status_code in (200, 201):
                    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
                logger.warning(f"Storage upload attempt {attempt+1} failed: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Storage upload attempt {attempt+1} error: {e}")
        if attempt < 2:
            import time
            time.sleep(2 * (attempt + 1))

    # Final fallback: try standard client
    supabase.storage.from_(STORAGE_BUCKET).upload(
        filename, file_bytes,
        file_options={"content-type": content_type, "upsert": "true"}
    )
    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)


async def _call_claude_async(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
    """Call Claude via Anthropic API directly (async). 3 retries with timeout."""
    for attempt in range(3):
        try:
            response = await litellm.acompletion(
                model="anthropic/claude-sonnet-4-5-20250929",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                timeout=120,
                num_retries=0,
                api_key=ANTHROPIC_API_KEY,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < 2 and any(code in str(e) for code in ["502", "503", "529", "timeout", "disconnected", "overloaded"]):
                logger.warning(f"Claude async attempt {attempt+1} failed: {e}. Retrying...")
                await asyncio.sleep(5 * (attempt + 1))
                continue
            raise


def _call_claude_sync(system_prompt: str, user_prompt: str, max_tokens: int = 4000, timeout_per_attempt: int = 120) -> str:
    """Call Claude via Anthropic API directly (sync). 3 retries, no proxy."""
    import time as _time

    for attempt in range(3):
        t_start = _time.time()
        try:
            response = litellm.completion(
                model="anthropic/claude-sonnet-4-5-20250929",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                timeout=timeout_per_attempt,
                num_retries=0,
                api_key=ANTHROPIC_API_KEY,
            )
            text = response.choices[0].message.content
            elapsed = _time.time() - t_start
            logger.info(f"Claude responded in {elapsed:.1f}s ({len(text)} chars)")
            return text
        except Exception as e:
            elapsed = _time.time() - t_start
            err_str = str(e).lower()
            retryable = any(k in err_str for k in ["502", "503", "529", "timeout", "disconnected", "overloaded", "connection", "reset", "eof", "broken pipe", "server"])

            logger.warning(f"Claude attempt {attempt+1}/3 failed ({elapsed:.0f}s): {str(e)[:150]}. {'Retrying...' if attempt < 2 else 'FAILED'}")

            if attempt < 2 and retryable:
                _time.sleep(5)
                continue
            raise Exception(f"Claude failed after 3 attempts: {e}")


def _parse_json(text):
    import json
    import re

    # Strip markdown code blocks
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_match:
        text = code_match.group(1).strip()

    if '{' not in text:
        return None

    try:
        start = text.index('{')
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            if depth == 0:
                return json.loads(text[start:i+1])

        # JSON was truncated — try to repair by closing open braces/brackets
        raw = text[start:]
        # Count open structures
        open_brackets = raw.count('[') - raw.count(']')
        open_braces = raw.count('{') - raw.count('}')
        # Close them
        repair = raw
        if repair.rstrip().endswith(','):
            repair = repair.rstrip()[:-1]  # remove trailing comma
        repair += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
        try:
            return json.loads(repair)
        except json.JSONDecodeError:
            # Try more aggressive repair: truncate to last complete scene
            last_complete = repair.rfind('},')
            if last_complete > 0:
                truncated = repair[:last_complete+1]
                truncated += ']' * max(0, truncated.count('[') - truncated.count(']'))
                truncated += '}' * max(0, truncated.count('{') - truncated.count('}'))
                try:
                    return json.loads(truncated)
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return None


# ── Pre-Production Intelligence ──

def _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id):
    """ONE Claude Vision call to analyze ALL character avatars and produce canonical descriptions.
    Returns dict: {character_name: detailed_english_description}
    """
    if not char_avatars:
        return {}

    content_parts = [{"type": "text", "text": """Analyze each character avatar image below. For EACH character, describe their EXACT visual appearance in English.
Focus on: species/type (if animal: which exact animal, fur/feather color and texture; if human: features), body shape, size relative to others, ALL colors and textures, clothing, accessories, unique distinguishing features.

Return ONLY valid JSON: {"Character Name": "Precise 50-word visual description"}"""}]

    names_with_images = []
    for ch in characters:
        name = ch.get("name", "")
        url = char_avatars.get(name)
        if not url:
            continue
        local_path = avatar_cache.get(url)
        if not local_path or not os.path.exists(local_path):
            continue
        try:
            with open(local_path, 'rb') as f:
                img_bytes = f.read()
                img_b64 = base64.b64encode(img_bytes).decode()
            # Detect MIME type from file content
            if img_bytes[:3] == b'\xff\xd8\xff':
                mime = "image/jpeg"
            elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                mime = "image/png"
            elif img_bytes[:4] == b'RIFF' and img_bytes[8:12] == b'WEBP':
                mime = "image/webp"
            else:
                mime = "image/jpeg"  # default fallback
            content_parts.append({"type": "text", "text": f"CHARACTER: {name}"})
            content_parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}})
            names_with_images.append(name)
        except Exception as e:
            logger.warning(f"Studio [{project_id}]: Avatar read error for {name}: {e}")

    if not names_with_images:
        return {}

    try:
        response = litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": content_parts}],
            max_tokens=2000, timeout=60, api_key=ANTHROPIC_API_KEY,
        )
        result = response.choices[0].message.content
        parsed = _parse_json(result)
        if parsed:
            logger.info(f"Studio [{project_id}]: Avatar Vision analysis — {len(parsed)} characters: {list(parsed.keys())}")
            return parsed
    except Exception as e:
        logger.warning(f"Studio [{project_id}]: Avatar Vision analysis failed: {e}")
    return {}


def _build_production_design(briefing, characters, scenes, avatar_descriptions, visual_style, lang, project_id):
    """ONE Claude call to create the complete Production Design Document.
    Replaces separate music, style, location, and continuity planning with a single efficient call.
    Outputs: style_anchors, color_palette, character_bible, location_bible, scene_directions, music_plan, voice_plan.
    """
    STYLE_NAMES = {
        "animation": "High-quality 3D Pixar/DreamWorks animation with warm lighting and expressive characters",
        "cartoon": "Vibrant 2D cartoon with bold outlines and saturated colors",
        "anime": "Japanese anime with detailed backgrounds and dramatic lighting",
        "realistic": "Cinematic photorealistic live-action with natural lighting",
        "watercolor": "Watercolor painting with soft edges and pastel tones",
    }

    char_info = "\n".join([
        f"- {ch['name']}: {ch.get('description', '')} | Avatar visual: {avatar_descriptions.get(ch['name'], 'No avatar reference')}"
        for ch in characters
    ])

    scene_list = "\n".join([
        f"Scene {s.get('scene_number', i+1)}: {s.get('title', '')} — {s.get('description', '')[:120]} [{s.get('emotion', '')}] Chars: {', '.join(s.get('characters_in_scene', []))}"
        for i, s in enumerate(scenes)
    ])

    system = """You are a PRODUCTION DESIGNER for animated films. Create ONE comprehensive document ensuring PERFECT visual and narrative continuity across independently-rendered scenes.

Return ONLY valid JSON:
{
  "style_anchors": "EXACT 40-word visual style description to include VERBATIM in EVERY scene prompt. Specific: art technique, lighting quality, texture detail, camera quality, color temperature.",
  "color_palette": {"global": "3-4 dominant color names", "morning": "morning light description", "afternoon": "afternoon light", "sunset": "sunset/evening light", "night": "night light"},
  "character_bible": {"CharacterName": "CANONICAL 80-word English appearance. MUST match avatar analysis EXACTLY. Include: 1) SPECIES (e.g. 'anthropomorphic camel'), 2) BODY POSTURE (e.g. 'bipedal, standing upright on two legs like a human'), 3) EXACT fur/skin color and texture, 4) EXACT clothing with colors, 5) FACE details (eyes, snout/nose, expressions), 6) UNIQUE marks/accessories, 7) BODY BUILD (tall/short, thin/stocky). This description is used VERBATIM in every scene — consistency depends on it."},
  "location_bible": {"LocationKey": "40-word English description. Landscape, terrain, vegetation, architecture, sky, ambient details."},
  "scene_directions": [{"scene": 1, "time_of_day": "morning|afternoon|sunset|night", "location_key": "from location_bible", "camera_flow": "camera movement description", "transition_note": "visual link to previous/next scene", "ambient": "environmental sounds"}],
  "music_plan": [{"scenes": [1,2,3], "mood": "description", "category": "cinematic|epic|gentle|tense|triumphant", "intensity": "low|medium|high"}],
  "voice_plan": [{"scene": 1, "tone": "warm|whisper|powerful|dramatic|sad", "pace": "slow|medium|fast"}]
}

CRITICAL RULES:
- character_bible MUST derive from avatar visual analysis when available — avatar is TRUTH
- If characters are animals or anthropomorphic, describe EXACT SPECIES from the avatar, EXACT BODY POSTURE (bipedal vs quadruped), and how they move. If avatar shows a bipedal anthropomorphic animal (standing on two legs), EVERY scene MUST show that character as BIPEDAL — NEVER as a quadruped
- NEVER change a character's species across scenes — if the avatar is a camel, the character is ALWAYS a camel, NEVER a lion or other animal
- If characters are animals, describe ONLY animal features (fur, feathers, hooves, snouts, tails) — NEVER human features (hands, fingers, human skin)
- style_anchors must be specific enough to force Sora 2 into consistent output across all scenes
- scene_directions transition_note creates visual flow between independently generated videos
- All text in ENGLISH for Sora 2 compatibility"""

    user_prompt = f"""Story: {briefing[:500]}
Art style: {STYLE_NAMES.get(visual_style, visual_style)}
Scenes: {len(scenes)} | Language: {lang}

CHARACTERS WITH VISUAL REFERENCES:
{char_info}

SCENES:
{scene_list}

Create production design. VISUAL CONSISTENCY is the #1 priority."""

    try:
        result = _call_claude_sync(system, user_prompt, max_tokens=5000)
        parsed = _parse_json(result)
        if parsed:
            logger.info(f"Studio [{project_id}]: Production Design — {len(parsed.get('character_bible', {}))} chars, {len(parsed.get('location_bible', {}))} locations")
            return parsed
    except Exception as e:
        logger.warning(f"Studio [{project_id}]: Production Design failed: {e}")
    return {}


def _create_composite_avatar(chars_in_scene, char_avatars, avatar_cache, size="1280x720"):
    """Create a side-by-side collage of ALL character avatars in a scene for Sora 2 reference.
    Single character → returns original path. Multiple → creates composite image.
    """
    from PIL import Image as _PILImage
    import tempfile

    w, h = [int(x) for x in size.split("x")]

    avatar_paths = []
    for ch_name in chars_in_scene:
        url = char_avatars.get(ch_name)
        if url and url in avatar_cache and avatar_cache[url]:
            avatar_paths.append(avatar_cache[url])

    if not avatar_paths:
        return None
    if len(avatar_paths) == 1:
        return avatar_paths[0]

    # Multiple avatars — create composite collage
    canvas = _PILImage.new("RGB", (w, h), (0, 0, 0))
    num = len(avatar_paths)
    slot_w = w // num

    for i, path in enumerate(avatar_paths):
        try:
            img = _PILImage.open(path).convert("RGB")
            ratio = min(slot_w / img.width, h / img.height)
            nw, nh = int(img.width * ratio), int(img.height * ratio)
            resized = img.resize((nw, nh), _PILImage.LANCZOS)
            canvas.paste(resized, (i * slot_w + (slot_w - nw) // 2, (h - nh) // 2))
        except Exception:
            pass

    composite_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    canvas.save(composite_file.name, format="PNG")
    return composite_file.name


# ═══════════════════════════════════════════════════════════
# ── CONTINUITY ENGINE v2 ──
# ═══════════════════════════════════════════════════════════

_ANTI_INSTRUCTIONS = """
CRITICAL RULES (VIOLATION = SCENE REJECTED):
- EVERY character MUST match their reference avatar image EXACTLY — same species, same face shape, same body proportions, same fur/skin color, same clothing.
- NEVER change the species of any character. If the avatar shows a camel, render a camel. If the avatar shows a lion, render a lion. NEVER substitute one animal for another.
- NEVER change the art style mid-scene or between scenes. If the style is 3D CGI, EVERY frame must be 3D CGI. NEVER mix 2D and 3D.
- NEVER change clothing colors. Match the avatar reference exactly.
- Character age MUST match the scene context exactly (baby = tiny, held in arms; child = small, half adult height; elder = tall, weathered features).
"""

def _extract_last_frame(video_path: str, output_path: str = None) -> str:
    """P0.1 — Extract the last frame from a video using FFmpeg for visual anchoring."""
    import tempfile
    if not output_path:
        output_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    try:
        # Get duration first
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, timeout=10
        )
        duration = float(probe.stdout.decode().strip() or "10") - 0.1
        # Extract last frame
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{max(0, duration):.2f}", "-i", video_path,
             "-vframes", "1", "-q:v", "2", output_path],
            capture_output=True, timeout=15
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            return output_path
    except Exception as e:
        logger.warning(f"Frame extraction failed: {e}")
    return None


def _generate_character_sheet(character_name: str, description: str, avatar_path: str,
                              style_hint: str, project_id: str) -> bytes:
    """P0.2 — Generate a canonical 'character sheet' image via Gemini for consistent reference."""
    try:
        from emergentintegrations.llm.gemeni.image_generation import GeminiImageGeneration
        gen = GeminiImageGeneration(api_key=os.environ.get("GEMINI_API_KEY", ""))

        sheet_prompt = f"""Create a CHARACTER REFERENCE SHEET for animation production.
Character: {description}
Art style: {style_hint}

Show the character in a NEUTRAL standing pose, front-facing, on a plain neutral background.
Full body visible, well-lit, sharp details. This is a production reference for visual consistency.
The character must look EXACTLY as described — this image will be used to maintain consistency across multiple scenes."""

        results = gen.generate_images(prompt=sheet_prompt, model="imagen-3.0-generate-002", number_of_images=1)
        if results and results[0]:
            return results[0]
    except Exception as e:
        logger.warning(f"Studio [{project_id}]: Character sheet gen failed for {character_name}: {e}")
    return None


def _build_style_dna(animation_sub: str, production_design: dict) -> str:
    """P1.3 — Build a rigid 'Style DNA' block that must appear verbatim in every scene prompt.
    Combines art style, color palette, rendering technique, and lighting direction.
    V2: Much stricter enforcement of 3D rendering and character identity.
    """
    STYLE_DNA_MAP = {
        "pixar_3d": "MANDATORY VISUAL STYLE — DO NOT DEVIATE: Premium 3D CGI animation (Pixar/DreamWorks quality). This MUST be fully 3D-rendered computer graphics with volumetric lighting, subsurface scattering on all skin and fur, global illumination with warm color temperature 5500K, cinematic depth of field f/2.8, soft ambient occlusion shadows. Characters MUST have 3D-modeled fur with visible individual strands catching light, large expressive eyes with specular reflections, smooth rounded features, slightly oversized heads. Textures MUST be high-resolution 3D materials — NOT flat 2D colors, NOT cell-shaded, NOT painted. This is NOT 2D animation. Every surface must show 3D depth, volume, and realistic material response to light.",
        "cartoon_3d": "MANDATORY VISUAL STYLE — DO NOT DEVIATE: Stylized 3D CGI cartoon with subtle cel-shading overlay. Bright saturated primary colors. Flat directional lighting with minimal soft shadows. 3D-modeled characters with thick dark outlines rendered as post-processing effect. Simplified but VOLUMETRIC facial features, exaggerated proportions. Vibrant solid-color backgrounds with 3D depth. This is 3D-rendered, NOT hand-drawn 2D.",
        "cartoon_2d": "MANDATORY VISUAL STYLE — DO NOT DEVIATE: Classic 2D hand-drawn animation (Disney/Ghibli quality). Clean ink outlines with watercolor-style fill. Painted multi-layered backgrounds with parallax depth. Fluid squash-and-stretch character animation principles. Soft diffused lighting. Warm earth-tone color palette with visible brush texture. EVERY frame must look hand-painted on paper.",
        "anime_2d": "MANDATORY VISUAL STYLE — DO NOT DEVIATE: Japanese anime (Makoto Shinkai quality). Hyper-detailed painted backgrounds with photographic depth. Dramatic rim lighting with visible light rays. Speed lines for motion emphasis. Large expressive eyes with complex highlight patterns. Atmospheric perspective. Cool blue shadows, warm golden highlights. Consistent cel-shaded characters with clean outlines.",
        "realistic": "MANDATORY VISUAL STYLE — DO NOT DEVIATE: Cinematic photorealism. 35mm anamorphic lens distortion. Ultra-shallow DOF f/1.4. Natural film grain ISO 800. Professional three-point lighting. Color grading: slightly desaturated, lifted blacks, compressed highlights. Raytraced reflections and refractions. Photoscanned textures.",
        "watercolor": "MANDATORY VISUAL STYLE — DO NOT DEVIATE: Watercolor painting animation. Visible wet brush strokes with paper texture bleed-through. Bleeding edges where colors meet. Soft pastel tones: cream, sage, dusty rose, soft blue. Dreamy ethereal atmosphere with diffused backlight. Paper grain texture visible in every frame.",
    }
    base = STYLE_DNA_MAP.get(animation_sub, STYLE_DNA_MAP["pixar_3d"])

    # Enhance with Production Design color palette
    color = production_design.get("color_palette", {})
    if color.get("global"):
        base += f" COLOR PALETTE LOCK: {color['global']}."

    # Append anti-instructions
    base += " " + _ANTI_INSTRUCTIONS.strip()

    return base


def _validate_scene_continuity(current_frame_path: str, prev_frame_path: str,
                                character_descriptions: str, project_id: str, scene_num: int) -> dict:
    """P2.5 — Use Claude Vision to validate visual continuity between consecutive scenes.
    Returns: {'consistent': bool, 'issues': [...], 'severity': 'low'|'medium'|'high'}
    """
    try:
        content = [
            {"type": "text", "text": f"""Compare these two consecutive video frames from an animated production.
Frame 1 = END of scene {scene_num - 1}. Frame 2 = START of scene {scene_num}.

EXPECTED characters in these scenes: {character_descriptions}

Check for VISUAL CONTINUITY:
1. Character appearance consistency (same colors, proportions, features)
2. Art style consistency (same rendering technique)
3. Lighting consistency (similar temperature and direction)
4. Color palette consistency

Return ONLY JSON: {{"consistent": true/false, "issues": ["issue1", "issue2"], "severity": "low|medium|high", "fix_suggestion": "prompt adjustment to fix"}}"""}
        ]

        for frame_path in [prev_frame_path, current_frame_path]:
            if frame_path and os.path.exists(frame_path):
                with open(frame_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})

        if len(content) < 3:
            return {"consistent": True, "issues": [], "severity": "low"}

        response = litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": content}],
            max_tokens=500, timeout=30, api_key=ANTHROPIC_API_KEY,
        )
        result = _parse_json(response.choices[0].message.content)
        if result:
            logger.info(f"Studio [{project_id}]: Continuity check scene {scene_num}: consistent={result.get('consistent')} severity={result.get('severity')}")
            return result
    except Exception as e:
        logger.warning(f"Studio [{project_id}]: Continuity validation error scene {scene_num}: {e}")
    return {"consistent": True, "issues": [], "severity": "low"}


def _apply_color_grading(video_path: str, output_path: str, style: str = "warm_cinematic") -> str:
    """P1.4 — Apply uniform color grading via FFmpeg for visual consistency across scenes."""
    GRADING_FILTERS = {
        "warm_cinematic": "eq=contrast=1.05:brightness=0.02:saturation=1.1,colorbalance=rs=0.03:gs=0.01:bs=-0.02:rm=0.02:gm=0.01:bm=-0.01",
        "cool_dramatic": "eq=contrast=1.08:brightness=-0.01:saturation=0.95,colorbalance=rs=-0.02:gs=0:bs=0.03",
        "neutral_clean": "eq=contrast=1.03:brightness=0.01:saturation=1.05",
    }
    vf = GRADING_FILTERS.get(style, GRADING_FILTERS["warm_cinematic"])
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vf", vf,
             "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an", output_path],
            capture_output=True, timeout=60
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
    except Exception as e:
        logger.warning(f"Color grading failed: {e}")
    return video_path



def _generate_scene_keyframe(sora_prompt: str, char_avatars: dict, avatar_cache: dict,
                              chars_in_scene: list, project_id: str, scene_num: int,
                              character_bible: dict = None) -> str:
    """KEYFRAME-FIRST PIPELINE: Generate a starting frame image via Gemini Nano Banana to force
    correct character identity before Sora 2 animation.
    Uses EMERGENT_LLM_KEY with gemini-3.1-flash-image-preview model.
    Now passes ALL character avatars + character_bible for maximum consistency.
    """
    import tempfile
    import asyncio
    try:
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            logger.warning(f"Studio [{project_id}]: No EMERGENT_LLM_KEY — skipping keyframe")
            return None

        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

        async def _gen():
            chat = LlmChat(
                api_key=api_key,
                session_id=f"keyframe-{project_id}-{scene_num}",
                system_message="You are a professional animation art director. Generate exactly one high-quality image."
            )
            chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

            # Build character descriptions from character_bible
            char_desc_block = ""
            if character_bible:
                for cname in chars_in_scene:
                    desc = character_bible.get(cname, "")
                    if desc:
                        char_desc_block += f"\n- {cname}: {desc}"

            prompt_text = f"""Generate a SINGLE FRAME for an animated film. This will be used as a starting keyframe for Sora 2 video generation.

{sora_prompt}

CHARACTER IDENTITY (from avatar analysis — ABSOLUTE TRUTH, match EXACTLY):
{char_desc_block if char_desc_block else 'See reference images below.'}

CRITICAL RULES:
- Every character MUST match the reference avatar images EXACTLY — same species, same face shape, same fur color, same clothing
- If a character is a BIPEDAL ANTHROPOMORPHIC ANIMAL in the reference, they MUST be shown STANDING UPRIGHT ON TWO LEGS — never as a quadruped
- ONLY include the characters listed above — DO NOT add random extra animals or characters
- Style MUST be 3D CGI Pixar quality with volumetric lighting
- This is ONE static frame — capture the opening moment of this scene"""

            # Collect ALL character avatar references for this scene
            ref_images = []
            for char_name in chars_in_scene:
                url = char_avatars.get(char_name)
                cached_path = avatar_cache.get(url) if url else None
                if cached_path and os.path.exists(cached_path):
                    with open(cached_path, 'rb') as f:
                        ref_b64 = base64.b64encode(f.read()).decode('utf-8')
                    ref_images.append(ImageContent(ref_b64))

            if ref_images:
                msg = UserMessage(
                    text=f"{prompt_text}\n\nReference avatar images for characters in this scene (match these EXACTLY):",
                    file_contents=ref_images
                )
            else:
                msg = UserMessage(text=prompt_text)

            text, images = await chat.send_message_multimodal_response(msg)
            if images and len(images) > 0:
                img_bytes = base64.b64decode(images[0]['data'])
                return img_bytes
            return None

        # Run async in sync context
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(lambda: asyncio.run(_gen())).result(timeout=60)
        else:
            result = asyncio.run(_gen())

        if result:
            keyframe_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            with open(keyframe_path, 'wb') as f:
                f.write(result)
            logger.info(f"Studio [{project_id}]: Keyframe generated for scene {scene_num} ({len(result)//1024}KB)")
            return keyframe_path
    except Exception as e:
        logger.warning(f"Studio [{project_id}]: Keyframe gen failed for scene {scene_num}: {e}")
    return None




# ── Models ──

class StudioProject(BaseModel):
    id: Optional[str] = None
    name: str = ""
    scene_type: str = "multi_scene"
    briefing: str = ""
    avatar_urls: list = []
    asset_urls: list = []
    voice_config: Optional[dict] = None
    music_config: Optional[dict] = None
    language: str = "pt"
    visual_style: str = "animation"  # animation, realistic, anime, cartoon
    audio_mode: str = "narrated"  # narrated (voice-over) or dubbed (per-character)
    animation_sub: str = "pixar_3d"  # pixar_3d, cartoon_3d, cartoon_2d, anime_2d, realistic, watercolor
    continuity_mode: bool = True  # enable enhanced continuity engine

class ChatMessage(BaseModel):
    project_id: Optional[str] = None
    message: str = ""
    language: str = "pt"

class StartProductionRequest(BaseModel):
    project_id: str
    video_duration: int = 12
    character_avatars: dict = {}  # {character_name: avatar_url}
    visual_style: str = ""  # override style for this run

class RegenerateSceneRequest(BaseModel):
    scene_number: int
    custom_prompt: Optional[str] = None  # optional custom Sora prompt override

class GenerateAvatarRequest(BaseModel):
    character_name: str
    character_description: str
    style: str = "cinematic"

class GenerateNarrationRequest(BaseModel):
    project_id: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel default
    stability: float = 0.30
    similarity: float = 0.80
    style_val: float = 0.55


class PostProduceRequest(BaseModel):
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    stability: float = 0.30
    similarity: float = 0.80
    style_val: float = 0.55
    music_track: str = ""  # key from MUSIC_LIBRARY (empty = auto from music_plan)
    music_volume: float = 0.15  # 0.0 - 1.0 background music volume
    transition_type: str = "fade"  # fade, cut
    transition_duration: float = 0.5  # seconds


class LocalizeRequest(BaseModel):
    target_language: str = "en"  # en, es, fr, de, it, pt
    voice_id: str = ""  # optional override, empty = same voice
    stability: float = 0.30
    similarity: float = 0.80
    style_val: float = 0.55


# ── Projects CRUD ──

@router.post("/projects")
async def create_project(req: StudioProject, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    now = datetime.now(timezone.utc).isoformat()
    project = {
        "id": req.id or uuid.uuid4().hex[:12],
        "name": req.name or f"Studio {datetime.now(timezone.utc).strftime('%d/%m %H:%M')}",
        "scene_type": "multi_scene",
        "briefing": req.briefing,
        "avatar_urls": req.avatar_urls,
        "scenes": [],
        "characters": [],
        "character_avatars": {},
        "chat_history": [],
        "agents_output": {},
        "agent_status": {},
        "outputs": [],
        "milestones": [{"key": "project_created", "label": "Projecto criado", "done": True, "at": now}],
        "status": "draft",
        "error": None,
        "language": req.language,
        "visual_style": req.visual_style or "animation",
        "audio_mode": req.audio_mode or "narrated",
        "animation_sub": req.animation_sub or "pixar_3d",
        "continuity_mode": req.continuity_mode,
        "created_at": now,
        "updated_at": now,
    }
    projects.insert(0, project)
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return project

@router.get("/projects")
async def list_projects(tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    return {"projects": settings.get("studio_projects", [])}

@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": project.get("status"),
        "chat_status": project.get("chat_status"),
        "chat_history": project.get("chat_history", []),
        "agent_status": project.get("agent_status", {}),
        "agents_output": project.get("agents_output", {}),
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
        "character_avatars": project.get("character_avatars", {}),
        "outputs": project.get("outputs", []),
        "milestones": project.get("milestones", []),
        "narrations": project.get("narrations", []),
        "narration_status": project.get("narration_status", {}),
        "voice_config": project.get("voice_config", {}),
        "visual_style": project.get("visual_style", "animation"),
        "language": project.get("language", "pt"),
        "subtitles": project.get("subtitles", {}),
        "screenplay_approved": project.get("screenplay_approved", False),
        "audio_mode": project.get("audio_mode", "narrated"),
        "storyboard_panels": project.get("storyboard_panels", []),
        "storyboard_status": project.get("storyboard_status", {}),
        "storyboard_approved": project.get("storyboard_approved", False),
        "storyboard_chat_history": project.get("storyboard_chat_history", []),
        "continuity_status": project.get("continuity_status", {}),
        "continuity_report": project.get("continuity_report", {}),
        "error": project.get("error"),
    }

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    projects = [p for p in projects if p.get("id") != project_id]
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return {"status": "ok"}


@router.post("/projects/{project_id}/fix-stuck")
async def fix_stuck_project(project_id: str, tenant=Depends(get_current_tenant)):
    """Fix a stuck project by marking it as error or complete."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    outputs = project.get("outputs", [])
    if any(o.get("url") for o in outputs):
        project["status"] = "complete"
        _add_milestone(project, "fixed_stuck", "Projecto recuperado automaticamente")
    else:
        project["status"] = "scripting"
        project["error"] = None
        # Reset agent status so UI shows ready to restart
        total = len(project.get("scenes", []))
        project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "idle", "videos_done": 0, "scene_status": {}}
        _add_milestone(project, "fixed_stuck", "Produção interrompida — pronto para reiniciar")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": project["status"], "scenes": len(project.get("scenes", []))}



@router.post("/projects/{project_id}/update-characters")
async def update_characters(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update characters list for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["characters"] = payload.get("characters", [])
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _add_milestone(project, "characters_updated", f"Personagens editados — {len(payload.get('characters', []))} personagens")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.put("/projects/{project_id}/character-avatars")
async def update_character_avatars(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update character avatar URLs for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["character_avatars"] = payload.get("character_avatars", {})
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "avatars": len(project["character_avatars"])}


@router.patch("/projects/{project_id}/settings")
async def update_project_settings(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update project-level settings (screenplay_approved, audio_mode, etc.)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    allowed_keys = {"screenplay_approved", "audio_mode", "visual_style", "animation_sub", "continuity_mode", "language"}
    for k, v in payload.items():
        if k in allowed_keys:
            project[k] = v
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    if payload.get("screenplay_approved"):
        _add_milestone(project, "screenplay_approved", "Roteiro aprovado pelo usuário")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


# ══ STORYBOARD ENDPOINTS ══

class StoryboardGenerateRequest(BaseModel):
    pass

class StoryboardRegeneratePanelRequest(BaseModel):
    panel_number: int
    description: str = ""

class StoryboardEditPanelRequest(BaseModel):
    panel_number: int
    title: str = ""
    description: str = ""
    dialogue: str = ""

class StoryboardChatRequest(BaseModel):
    message: str

class StoryboardApproveRequest(BaseModel):
    approved: bool = True


@router.post("/projects/{project_id}/generate-storyboard")
async def generate_storyboard(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate storyboard panels for all scenes using Gemini Nano Banana."""
    from core.storyboard import generate_all_panels
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to generate storyboard from")

    # Mark as generating
    project["storyboard_status"] = {"phase": "starting", "current": 0, "total": len(scenes), "panels_done": 0}
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    # Run generation in background thread
    def _bg_gen():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return
            panels = generate_all_panels(
                tenant_id=tenant["id"],
                project_id=project_id,
                scenes=_project.get("scenes", []),
                characters=_project.get("characters", []),
                char_avatars=_project.get("character_avatars", {}),
                production_design=_project.get("agents_output", {}).get("production_design", {}),
                lang=_project.get("language", "pt"),
                upload_fn=_upload_to_storage,
                update_fn=_update_project_field,
            )
            done_count = len([p for p in panels if p.get("image_url")])
            _update_project_field(tenant["id"], project_id, {
                "storyboard_panels": panels,
                "storyboard_status": {"phase": "complete", "current": len(panels), "total": len(panels), "panels_done": done_count},
                "storyboard_approved": False,
            })
            _add_milestone(_project, "storyboard_generated", f"Storyboard — {done_count}/{len(panels)} painéis")
            _save_project(tenant["id"], _settings, _projects)
            logger.info(f"Storyboard [{project_id}]: Complete — {done_count}/{len(panels)} panels")
        except Exception as e:
            logger.error(f"Storyboard [{project_id}]: Generation failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "storyboard_status": {"phase": "error", "error": str(e)[:200]},
            })

    thread = threading.Thread(target=_bg_gen, daemon=True)
    thread.start()
    return {"status": "generating", "total_scenes": len(scenes)}


@router.get("/projects/{project_id}/storyboard")
async def get_storyboard(project_id: str, tenant=Depends(get_current_tenant)):
    """Get storyboard panels and status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "panels": project.get("storyboard_panels", []),
        "storyboard_status": project.get("storyboard_status", {}),
        "storyboard_approved": project.get("storyboard_approved", False),
        "storyboard_chat_history": project.get("storyboard_chat_history", []),
    }


@router.post("/projects/{project_id}/storyboard/regenerate-panel")
async def regenerate_storyboard_panel(project_id: str, req: StoryboardRegeneratePanelRequest, tenant=Depends(get_current_tenant)):
    """Regenerate a single storyboard panel with 6 individual frames."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == req.panel_number), None)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    scene = next((s for s in project.get("scenes", []) if s.get("scene_number") == req.panel_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Use updated description if provided
    if req.description:
        scene = {**scene, "description": req.description}

    # Mark as generating
    panel["status"] = "generating"
    _save_project(tenant["id"], settings, projects)

    def _bg_regen():
        try:
            import tempfile
            from core.storyboard import _generate_all_frames_for_scene, FRAME_TYPES
            char_avatars = project.get("character_avatars", {})
            production_design = project.get("agents_output", {}).get("production_design", {})
            character_bible = production_design.get("character_bible", {})

            avatar_cache = {}
            chars_in_scene = scene.get("characters_in_scene", [])
            for cname in chars_in_scene:
                url = char_avatars.get(cname)
                if url and url not in avatar_cache:
                    try:
                        supabase_url = os.environ.get('SUPABASE_URL', '')
                        full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
                        ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        urllib.request.urlretrieve(full_url, ref_file.name)
                        avatar_cache[url] = ref_file.name
                    except Exception:
                        avatar_cache[url] = None

            style_dna = "ART STYLE: Premium 3D CGI animation (Pixar/DreamWorks quality). Volumetric lighting."
            style_anchors = production_design.get("style_anchors", "")
            if style_anchors:
                style_dna = f"{style_dna} {style_anchors}"

            frame_results = _generate_all_frames_for_scene(
                scene=scene, scene_num=req.panel_number, project_id=project_id,
                char_avatars=char_avatars, avatar_cache=avatar_cache,
                character_bible=character_bible, style_dna=style_dna,
                lang=project.get("language", "pt"),
            )

            image_url = None
            frames = []
            for fi, (ft, img_bytes) in enumerate(frame_results):
                if img_bytes:
                    frame_fname = f"storyboard/{project_id}/panel_{req.panel_number}_frame_{fi+1}.png"
                    frame_url = _upload_to_storage(img_bytes, frame_fname, "image/png")
                    frames.append({
                        "frame_number": fi + 1,
                        "image_url": frame_url,
                        "label": ft["label"],
                    })
                    if image_url is None:
                        image_url = frame_url

            if image_url:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            p["image_url"] = image_url
                            p["frames"] = frames
                            p["status"] = "done"
                            p["generated_at"] = datetime.now(timezone.utc).isoformat()
                    _save_project(tenant["id"], _s, _p)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            p["status"] = "error"
                    _save_project(tenant["id"], _s, _p)

            for path in avatar_cache.values():
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Storyboard [{project_id}]: Panel {req.panel_number} regen failed: {e}")

    thread = threading.Thread(target=_bg_regen, daemon=True)
    thread.start()
    return {"status": "regenerating", "panel_number": req.panel_number}


@router.patch("/projects/{project_id}/storyboard/edit-panel")
async def edit_storyboard_panel(project_id: str, req: StoryboardEditPanelRequest, tenant=Depends(get_current_tenant)):
    """Edit text fields of a storyboard panel."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    found = False
    for p in panels:
        if p.get("scene_number") == req.panel_number:
            if req.title:
                p["title"] = req.title
            if req.description:
                p["description"] = req.description
            if req.dialogue:
                p["dialogue"] = req.dialogue
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Panel not found")

    project["storyboard_panels"] = panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


class InpaintElementRequest(BaseModel):
    panel_number: int
    edit_instruction: str
    frame_index: int = 0  # Which frame to edit (0-based)


@router.post("/projects/{project_id}/storyboard/edit-element")
async def edit_element_inpaint(project_id: str, req: InpaintElementRequest, tenant=Depends(get_current_tenant)):
    """Edit a specific element in a storyboard panel using AI image editing (Gemini).

    The AI receives the original image + text instruction and generates an edited version
    that preserves everything except the requested change.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == req.panel_number), None)
    if not panel or not panel.get("image_url"):
        raise HTTPException(status_code=400, detail="Panel not found or has no image")

    # Determine which image to edit (selected frame or main image)
    frames = panel.get("frames", [])
    if frames and 0 <= req.frame_index < len(frames):
        source_image_url = frames[req.frame_index].get("image_url", panel["image_url"])
    else:
        source_image_url = panel["image_url"]

    # Mark as editing
    for p in panels:
        if p.get("scene_number") == req.panel_number:
            p["status"] = "generating"
    _save_project(tenant["id"], settings, projects)

    def _bg_inpaint():
        try:
            from core.storyboard_inpaint import inpaint_element
            result_bytes = inpaint_element(
                image_url=source_image_url,
                edit_instruction=req.edit_instruction,
                project_id=project_id,
                panel_number=req.panel_number,
                lang=project.get("language", "pt"),
            )
            if result_bytes:
                fname = f"storyboard/{project_id}/panel_{req.panel_number}_frame_{req.frame_index + 1}_edited.png"
                new_url = _upload_to_storage(result_bytes, fname, "image/png")
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            # Update the correct frame
                            p_frames = p.get("frames", [])
                            if p_frames and 0 <= req.frame_index < len(p_frames):
                                p_frames[req.frame_index]["image_url"] = new_url
                            # Also update main image_url if editing frame 0 or no frames
                            if req.frame_index == 0 or not p_frames:
                                p["image_url"] = new_url
                            p["status"] = "done"
                            p["last_edit"] = req.edit_instruction
                            p["generated_at"] = datetime.now(timezone.utc).isoformat()
                    _save_project(tenant["id"], _s, _p)
                logger.info(f"Inpaint [{project_id}]: Panel {req.panel_number} frame {req.frame_index} edited — {req.edit_instruction[:50]}")
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            p["status"] = "error"
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"Inpaint [{project_id}]: Panel {req.panel_number} failed: {e}")
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                for p in _proj.get("storyboard_panels", []):
                    if p.get("scene_number") == req.panel_number:
                        p["status"] = "error"
                _save_project(tenant["id"], _s, _p)

    thread = threading.Thread(target=_bg_inpaint, daemon=True)
    thread.start()
    return {"status": "editing", "panel_number": req.panel_number}


@router.patch("/projects/{project_id}/storyboard/approve")
async def approve_storyboard(project_id: str, req: StoryboardApproveRequest, tenant=Depends(get_current_tenant)):
    """Approve or unapprove the storyboard."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["storyboard_approved"] = req.approved
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    if req.approved:
        _add_milestone(project, "storyboard_approved", "Storyboard aprovado pelo usuário")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "storyboard_approved": req.approved}


@router.post("/projects/{project_id}/storyboard/chat")
async def storyboard_facilitator_chat(project_id: str, req: StoryboardChatRequest, tenant=Depends(get_current_tenant)):
    """AI Facilitator chat for editing storyboard panels."""
    from core.storyboard import facilitator_chat
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    chat_history = project.get("storyboard_chat_history", [])

    result = facilitator_chat(
        message=req.message,
        panels=panels,
        scenes=project.get("scenes", []),
        chat_history=chat_history,
        lang=project.get("language", "pt"),
    )

    # Save chat history
    chat_history.append({"role": "user", "text": req.message})
    chat_history.append({"role": "assistant", "text": result["response"]})

    # Apply text edits from actions
    for action in result.get("actions", []):
        if action.get("action") == "edit_text" and action.get("panel_number"):
            for p in panels:
                if p.get("scene_number") == action["panel_number"]:
                    field = action.get("field", "dialogue")
                    if field in ("dialogue", "description", "title"):
                        p[field] = action.get("value", "")

    project["storyboard_chat_history"] = chat_history[-20:]  # Keep last 20 messages
    project["storyboard_panels"] = panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    # Handle regenerate_image actions asynchronously
    regen_panels = [a["panel_number"] for a in result.get("actions", []) if a.get("action") == "regenerate_image"]

    return {
        "response": result["response"],
        "actions": result.get("actions", []),
        "regenerating_panels": regen_panels,
    }


# ══ STORYBOARD PREVIEW ENDPOINTS ══

class PreviewGenerateRequest(BaseModel):
    voice_id: str = "onwK4e9ZLuTAKqWW03F9"  # Daniel (British, authoritative)
    music_track: str = ""


@router.post("/projects/{project_id}/storyboard/generate-preview")
async def generate_storyboard_preview(project_id: str, req: PreviewGenerateRequest, tenant=Depends(get_current_tenant)):
    """Generate an animated MP4 preview from storyboard panels with ElevenLabs narration."""
    from core.preview_generator import generate_preview_video
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    valid_panels = [p for p in panels if p.get("image_url")]
    if not valid_panels:
        raise HTTPException(status_code=400, detail="No storyboard panels with images")

    lang = project.get("language", "pt")

    # Find music file path if specified
    music_path = None
    if req.music_track:
        from pipeline.config import MUSIC_LIBRARY
        track_info = MUSIC_LIBRARY.get(req.music_track)
        if track_info:
            music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline", "music")
            candidate = os.path.join(music_dir, track_info["file"])
            if os.path.exists(candidate):
                music_path = candidate

    # Mark as generating
    project["preview_status"] = {"phase": "starting", "current": 0, "total": len(valid_panels)}
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    def _bg_preview():
        try:
            url = generate_preview_video(
                project_id=project_id,
                panels=valid_panels,
                voice_id=req.voice_id,
                lang=lang,
                music_path=music_path,
                upload_fn=_upload_to_storage,
                update_fn=_update_project_field,
                tenant_id=tenant["id"],
            )
            _update_project_field(tenant["id"], project_id, {
                "preview_status": {"phase": "complete", "url": url},
                "preview_url": url,
            })
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                _add_milestone(_proj, "preview_generated", "Preview animado gerado")
                _save_project(tenant["id"], _s, _p)
            logger.info(f"Preview [{project_id}]: Complete — {url}")
        except Exception as e:
            logger.error(f"Preview [{project_id}]: Failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "preview_status": {"phase": "error", "error": str(e)[:200]},
            })

    thread = threading.Thread(target=_bg_preview, daemon=True)
    thread.start()
    return {"status": "generating", "total_panels": len(valid_panels)}


@router.get("/projects/{project_id}/storyboard/preview-status")
async def get_preview_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get preview generation status and URL."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "preview_status": project.get("preview_status", {}),
        "preview_url": project.get("preview_url"),
    }




# ══ LANGUAGE AGENT ENDPOINTS ══

@router.post("/projects/{project_id}/language/convert")
async def convert_project_language(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Convert all project text to target language (background task)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_lang = payload.get("target_lang", "en")
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to translate")

    source_lang = project.get("language", "pt")

    # Mark as converting
    project["language_status"] = {"phase": "converting", "target": target_lang}
    _save_project(tenant["id"], settings, projects)

    def _bg_convert():
        try:
            from core.language_agent import convert_language
            result = convert_language(
                scenes=scenes, project_name=project.get("name", ""),
                source_lang=source_lang, target_lang=target_lang, project_id=project_id,
            )
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj and "translated_scenes" in result:
                translated = result["translated_scenes"]
                for ts in translated:
                    sn = ts.get("scene_number")
                    for panel in _proj.get("storyboard_panels", []):
                        if panel.get("scene_number") == sn:
                            panel["title"] = ts.get("title", panel.get("title", ""))
                            panel["description"] = ts.get("description", panel.get("description", ""))
                            panel["dialogue"] = ts.get("dialogue", panel.get("dialogue", ""))
                    for scene in _proj.get("scenes", []):
                        if scene.get("scene_number") == sn:
                            scene["title"] = ts.get("title", scene.get("title", ""))
                            scene["description"] = ts.get("description", scene.get("description", ""))
                            scene["dialogue"] = ts.get("dialogue", scene.get("dialogue", ""))
                _proj["language"] = target_lang
                _proj["language_status"] = {"phase": "done", "target": target_lang, "count": len(translated)}
                _save_project(tenant["id"], _s, _p)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["language_status"] = {"phase": "error", "detail": result.get("error", "Unknown")}
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"Language convert [{project_id}]: {e}")

    thread = threading.Thread(target=_bg_convert, daemon=True)
    thread.start()
    return {"status": "converting", "target_lang": target_lang}


@router.post("/projects/{project_id}/language/review")
async def review_project_text(project_id: str, tenant=Depends(get_current_tenant)):
    """Review and improve text quality (background task)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to review")

    lang = project.get("language", "pt")

    project["review_status"] = {"phase": "reviewing"}
    _save_project(tenant["id"], settings, projects)

    def _bg_review():
        try:
            from core.language_agent import review_text_quality
            result = review_text_quality(
                scenes=scenes, project_name=project.get("name", ""),
                lang=lang, project_id=project_id,
            )
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj and "revised_scenes" in result:
                revised = result["revised_scenes"]
                for rs in revised:
                    sn = rs.get("scene_number")
                    for panel in _proj.get("storyboard_panels", []):
                        if panel.get("scene_number") == sn:
                            if rs.get("title"): panel["title"] = rs["title"]
                            if rs.get("description"): panel["description"] = rs["description"]
                            if rs.get("dialogue"): panel["dialogue"] = rs["dialogue"]
                    for scene in _proj.get("scenes", []):
                        if scene.get("scene_number") == sn:
                            if rs.get("title"): scene["title"] = rs["title"]
                            if rs.get("description"): scene["description"] = rs["description"]
                            if rs.get("dialogue"): scene["dialogue"] = rs["dialogue"]
                _proj["review_status"] = {
                    "phase": "done",
                    "quality": result.get("overall_quality", ""),
                    "notes": result.get("revision_notes", []),
                    "count": len(revised),
                }
                try:
                    _save_project(tenant["id"], _s, _p)
                    logger.info(f"Language review [{project_id}]: Saved {len(revised)} revisions")
                except Exception as se:
                    logger.error(f"Language review [{project_id}]: Save failed: {se}, retrying...")
                    import time
                    time.sleep(2)
                    _s2, _p2, _proj2 = _get_project(tenant["id"], project_id)
                    if _proj2:
                        _proj2["review_status"] = _proj["review_status"]
                        _save_project(tenant["id"], _s2, _p2)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["review_status"] = {"phase": "error", "detail": result.get("error", "Unknown")}
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"Language review [{project_id}]: {e}")
            try:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["review_status"] = {"phase": "error", "detail": str(e)[:200]}
                    _save_project(tenant["id"], _s, _p)
            except Exception:
                pass

    thread = threading.Thread(target=_bg_review, daemon=True)
    thread.start()
    return {"status": "reviewing"}


@router.get("/projects/{project_id}/language/status")
async def get_language_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Poll language operation status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "language_status": project.get("language_status", {}),
        "review_status": project.get("review_status", {}),
    }


# ══ SMART IMAGE EDITOR ENDPOINTS ══

@router.post("/projects/{project_id}/storyboard/analyze-scene")
async def analyze_storyboard_scene(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Analyze a storyboard panel image and return structured scene map."""
    from core.smart_editor import analyze_scene
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panel_number = payload.get("panel_number", 1)
    frame_index = payload.get("frame_index", 0)

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == panel_number), None)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    # Get the image to analyze
    frames = panel.get("frames", [])
    if frames and 0 <= frame_index < len(frames):
        image_url = frames[frame_index].get("image_url", panel.get("image_url"))
    else:
        image_url = panel.get("image_url")

    if not image_url:
        raise HTTPException(status_code=400, detail="No image to analyze")

    scene_context = {
        "title": panel.get("title", ""),
        "description": panel.get("description", ""),
        "characters_in_scene": panel.get("characters_in_scene", []),
        "emotion": panel.get("emotion", ""),
    }

    analysis = analyze_scene(
        image_url=image_url,
        project_id=project_id,
        panel_number=panel_number,
        scene_context=scene_context,
    )

    # Cache analysis in panel
    for p in panels:
        if p.get("scene_number") == panel_number:
            p_frames = p.get("frames", [])
            if p_frames and 0 <= frame_index < len(p_frames):
                p_frames[frame_index]["scene_analysis"] = analysis
            else:
                p["scene_analysis"] = analysis
    _save_project(tenant["id"], settings, projects)

    return analysis


@router.post("/projects/{project_id}/storyboard/smart-edit")
async def smart_edit_panel(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Edit a panel using scene-aware intelligence."""
    from core.smart_editor import analyze_scene, smart_edit
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panel_number = payload.get("panel_number", 1)
    frame_index = payload.get("frame_index", 0)
    edit_instruction = payload.get("edit_instruction", "")
    if not edit_instruction:
        raise HTTPException(status_code=400, detail="No edit instruction")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == panel_number), None)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    frames = panel.get("frames", [])
    if frames and 0 <= frame_index < len(frames):
        image_url = frames[frame_index].get("image_url", panel.get("image_url"))
        cached_analysis = frames[frame_index].get("scene_analysis")
    else:
        image_url = panel.get("image_url")
        cached_analysis = panel.get("scene_analysis")

    if not image_url:
        raise HTTPException(status_code=400, detail="No image to edit")

    # Mark as editing
    for p in panels:
        if p.get("scene_number") == panel_number:
            p["status"] = "generating"
    _save_project(tenant["id"], settings, projects)

    def _bg_smart_edit():
        try:
            # Step 1: Get or create scene analysis
            analysis = cached_analysis
            if not analysis or "error" in analysis:
                analysis = analyze_scene(
                    image_url=image_url,
                    project_id=project_id,
                    panel_number=panel_number,
                    scene_context={
                        "title": panel.get("title", ""),
                        "description": panel.get("description", ""),
                        "characters_in_scene": panel.get("characters_in_scene", []),
                        "emotion": panel.get("emotion", ""),
                    },
                )

            # Step 2: Smart edit with analysis context
            result_bytes = smart_edit(
                image_url=image_url,
                edit_instruction=edit_instruction,
                scene_analysis=analysis,
                project_id=project_id,
                panel_number=panel_number,
                lang=project.get("language", "pt"),
            )

            if result_bytes:
                fname = f"storyboard/{project_id}/panel_{panel_number}_frame_{frame_index + 1}_smart.png"
                new_url = _upload_to_storage(result_bytes, fname, "image/png")
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == panel_number:
                            p_frames = p.get("frames", [])
                            if p_frames and 0 <= frame_index < len(p_frames):
                                p_frames[frame_index]["image_url"] = new_url
                                p_frames[frame_index]["scene_analysis"] = analysis
                            if frame_index == 0 or not p_frames:
                                p["image_url"] = new_url
                            p["status"] = "done"
                            p["last_edit"] = f"[Smart] {edit_instruction}"
                            p["generated_at"] = datetime.now(timezone.utc).isoformat()
                    _save_project(tenant["id"], _s, _p)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == panel_number:
                            p["status"] = "error"
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"SmartEdit [{project_id}]: Panel {panel_number} failed: {e}")

    thread = threading.Thread(target=_bg_smart_edit, daemon=True)
    thread.start()

    return {"status": "editing", "panel_number": panel_number, "mode": "smart"}



# ══ CONTINUITY DIRECTOR ENDPOINTS ══

@router.post("/projects/{project_id}/continuity/analyze")
async def analyze_continuity_start(project_id: str, tenant=Depends(get_current_tenant)):
    """Start a background continuity analysis of the entire storyboard."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    if not panels:
        raise HTTPException(status_code=400, detail="No storyboard panels to analyze")

    # Check if already running
    cs = project.get("continuity_status", {})
    if cs.get("phase") == "analyzing":
        return {"status": "already_running"}

    project["continuity_status"] = {"phase": "analyzing", "current": 0, "total": len(panels), "issues_found": 0}
    _save_project(tenant["id"], settings, projects)

    def _bg_continuity_analyze():
        try:
            from core.continuity_director import analyze_continuity

            def progress_cb(current, total, batch_issues):
                try:
                    _s, _p, _proj = _get_project(tenant["id"], project_id)
                    if _proj:
                        _proj["continuity_status"] = {
                            "phase": "analyzing",
                            "current": current,
                            "total": total,
                            "issues_found": _proj.get("continuity_status", {}).get("issues_found", 0) + batch_issues,
                        }
                        _save_project(tenant["id"], _s, _p)
                except Exception:
                    pass

            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if not _proj:
                return

            report = analyze_continuity(
                project_id=project_id,
                panels=_proj.get("storyboard_panels", []),
                scenes=_proj.get("scenes", []),
                characters=_proj.get("characters", []),
                character_avatars=_proj.get("character_avatars", {}),
                progress_callback=progress_cb,
            )

            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                _proj["continuity_report"] = report
                _proj["continuity_status"] = {
                    "phase": "done",
                    "total": report.get("total_scenes_analyzed", 0),
                    "current": report.get("total_scenes_analyzed", 0),
                    "issues_found": report.get("total_issues", 0),
                    "high": report.get("high_count", 0),
                    "medium": report.get("medium_count", 0),
                    "low": report.get("low_count", 0),
                }
                _save_project(tenant["id"], _s, _p)
                logger.info(f"Continuity [{project_id}]: Analysis complete — {report.get('total_issues', 0)} issues")
        except Exception as e:
            logger.error(f"Continuity [{project_id}]: Analysis failed: {e}")
            try:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["continuity_status"] = {"phase": "error", "detail": str(e)[:200]}
                    _save_project(tenant["id"], _s, _p)
            except Exception:
                pass

    thread = threading.Thread(target=_bg_continuity_analyze, daemon=True)
    thread.start()
    return {"status": "analyzing", "total_panels": len(panels)}


@router.get("/projects/{project_id}/continuity/status")
async def get_continuity_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Poll continuity analysis/correction status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "continuity_status": project.get("continuity_status", {}),
        "continuity_report": project.get("continuity_report", {}),
    }


@router.post("/projects/{project_id}/continuity/auto-correct")
async def auto_correct_continuity(project_id: str, tenant=Depends(get_current_tenant)):
    """Auto-correct all issues found by the continuity analysis (background task)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = project.get("continuity_report", {})
    issues = report.get("issues", [])
    if not issues:
        raise HTTPException(status_code=400, detail="No issues to correct. Run analysis first.")

    # Filter only high and medium severity issues for auto-correction
    correctable = [i for i in issues if i.get("severity") in ("high", "medium") and i.get("correction")]
    if not correctable:
        return {"status": "no_corrections_needed", "message": "No high/medium issues with corrections available"}

    cs = project.get("continuity_status", {})
    if cs.get("phase") == "correcting":
        return {"status": "already_running"}

    project["continuity_status"] = {
        "phase": "correcting",
        "current": 0,
        "total": len(correctable),
        "corrected": 0,
        "failed": 0,
    }
    _save_project(tenant["id"], settings, projects)

    def _bg_auto_correct():
        try:
            from core.continuity_director import auto_correct_issue
            corrected_count = 0
            failed_count = 0

            for idx, issue in enumerate(correctable):
                scene_num = issue.get("scene_number")
                correction = issue.get("correction", "")
                if not scene_num or not correction:
                    failed_count += 1
                    continue

                # Get the current project state for this panel
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if not _proj:
                    break

                panels = _proj.get("storyboard_panels", [])
                panel = next((p for p in panels if p.get("scene_number") == scene_num), None)
                if not panel:
                    failed_count += 1
                    continue

                # Use frame 0 as the target for correction
                frames = panel.get("frames", [])
                frame_index = 0
                if frames:
                    source_url = frames[frame_index].get("image_url", panel.get("image_url"))
                else:
                    source_url = panel.get("image_url")

                if not source_url:
                    failed_count += 1
                    continue

                try:
                    result_bytes = auto_correct_issue(
                        image_url=source_url,
                        correction_instruction=correction,
                        project_id=project_id,
                        panel_number=scene_num,
                        frame_index=frame_index,
                    )

                    if result_bytes:
                        fname = f"storyboard/{project_id}/panel_{scene_num}_frame_1_corrected.png"
                        new_url = _upload_to_storage(result_bytes, fname, "image/png")

                        # Update the panel
                        _s2, _p2, _proj2 = _get_project(tenant["id"], project_id)
                        if _proj2:
                            for p in _proj2.get("storyboard_panels", []):
                                if p.get("scene_number") == scene_num:
                                    p_frames = p.get("frames", [])
                                    if p_frames and frame_index < len(p_frames):
                                        p_frames[frame_index]["image_url"] = new_url
                                    if frame_index == 0 or not p_frames:
                                        p["image_url"] = new_url
                                    p["status"] = "done"
                                    p["last_edit"] = f"[Continuity Director] {correction[:100]}"
                                    p["generated_at"] = datetime.now(timezone.utc).isoformat()
                            _proj2["continuity_status"] = {
                                "phase": "correcting",
                                "current": idx + 1,
                                "total": len(correctable),
                                "corrected": corrected_count + 1,
                                "failed": failed_count,
                            }
                            _save_project(tenant["id"], _s2, _p2)
                        corrected_count += 1
                        logger.info(f"Continuity [{project_id}]: Corrected scene {scene_num} — {correction[:60]}")
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Continuity [{project_id}]: Correction failed scene {scene_num}: {e}")
                    failed_count += 1

            # Final status update
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                _proj["continuity_status"] = {
                    "phase": "corrected",
                    "current": len(correctable),
                    "total": len(correctable),
                    "corrected": corrected_count,
                    "failed": failed_count,
                }
                _save_project(tenant["id"], _s, _p)
                logger.info(f"Continuity [{project_id}]: Auto-correct complete — {corrected_count} corrected, {failed_count} failed")
        except Exception as e:
            logger.error(f"Continuity [{project_id}]: Auto-correct failed: {e}")
            try:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["continuity_status"] = {"phase": "error", "detail": str(e)[:200]}
                    _save_project(tenant["id"], _s, _p)
            except Exception:
                pass

    thread = threading.Thread(target=_bg_auto_correct, daemon=True)
    thread.start()
    return {"status": "correcting", "total_corrections": len(correctable)}



# ══ BOOK EXPORT ENDPOINTS ══

@router.post("/projects/{project_id}/book/generate-cover")
async def generate_book_cover(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate a book cover image with all characters and creative title."""
    from core.book_generator import generate_cover_image, generate_creative_title
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", [])
    char_avatars = project.get("character_avatars", {})
    production_design = project.get("agents_output", {}).get("production_design", {})
    scenes = project.get("scenes", [])
    lang = project.get("language", "pt")
    name = project.get("name", "Meu Livro")

    # Generate creative title
    creative_title = generate_creative_title(name, scenes, lang)
    logger.info(f"Book [{project_id}]: Creative title: {creative_title}")

    # Generate cover image
    cover_bytes = generate_cover_image(name, characters, char_avatars, production_design, lang)
    cover_url = None
    if cover_bytes:
        fname = f"books/{project_id}/cover.png"
        cover_url = _upload_to_storage(cover_bytes, fname, "image/png")

    # Save to project
    project["book_cover_url"] = cover_url
    project["book_title"] = creative_title
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    return {
        "cover_url": cover_url,
        "creative_title": creative_title,
    }


@router.get("/projects/{project_id}/book/pdf")
async def export_pdf_storybook(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate and return a PDF storybook."""
    from core.book_generator import generate_pdf_storybook
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    if not panels:
        raise HTTPException(status_code=400, detail="No storyboard panels")

    creative_title = project.get("book_title", project.get("name", "Meu Livro"))
    cover_url = project.get("book_cover_url")
    lang = project.get("language", "pt")

    pdf_bytes = generate_pdf_storybook(
        project_name=project.get("name", ""),
        creative_title=creative_title,
        panels=panels,
        cover_url=cover_url,
        lang=lang,
    )

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{creative_title.replace(" ", "_")}.pdf"',
        },
    )


@router.get("/projects/{project_id}/book/interactive-data")
async def get_interactive_book_data(project_id: str, tenant=Depends(get_current_tenant)):
    """Get structured JSON data for the Interactive Book reader."""
    from core.book_generator import build_interactive_book_data
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    if not panels:
        raise HTTPException(status_code=400, detail="No storyboard panels")

    creative_title = project.get("book_title", project.get("name", "Meu Livro"))
    cover_url = project.get("book_cover_url")
    lang = project.get("language", "pt")

    book_data = build_interactive_book_data(
        project_id=project_id,
        project_name=project.get("name", ""),
        creative_title=creative_title,
        panels=panels,
        cover_url=cover_url,
        lang=lang,
    )
    return book_data


@router.post("/projects/{project_id}/book/tts-page")
async def generate_page_tts(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Generate TTS audio for a specific book page."""
    text = payload.get("text", "")
    voice_id = payload.get("voice_id", "onwK4e9ZLuTAKqWW03F9")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ElevenLabs key not configured")

    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": elevenlabs_key, "Content-Type": "application/json"},
            json={
                "text": text[:500],
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.6, "similarity_boost": 0.8},
            },
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"TTS failed: {r.status_code}")

        audio_bytes = r.content
        fname = f"books/{project_id}/tts_{hash(text) % 100000}.mp3"
        audio_url = _upload_to_storage(audio_bytes, fname, "audio/mpeg")
        return {"audio_url": audio_url}



@router.post("/projects/{project_id}/clear-outputs")
async def clear_scene_outputs(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Remove outputs for specific scenes to force re-generation. keep_scenes: list of scene numbers to KEEP."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    keep = set(payload.get("keep_scenes", []))
    outputs = project.get("outputs", [])
    kept = [o for o in outputs if o.get("scene_number") in keep or o.get("type") == "final_video"]
    removed = len(outputs) - len(kept)
    project["outputs"] = kept
    project["status"] = "complete"  # Keep complete so start-production works
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "removed": removed, "kept": len(kept)}


@router.post("/projects/{project_id}/merge-chat-scenes")
async def merge_chat_scenes(project_id: str, tenant=Depends(get_current_tenant)):
    """Extract scenes from ALL chat history messages and merge into a unified scenes array.
    Fixes projects where continuation scenes replaced earlier ones."""
    import re
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_history = project.get("chat_history", [])
    current_scenes = project.get("scenes", [])
    current_nums = {s.get("scene_number") for s in current_scenes}

    # Parse scenes from assistant messages in chat history
    scene_pattern = re.compile(
        r'\*\*CENA\s+(\d+)\*\*\s*\(([^)]+)\)\s*[—-]\s*([^\n]+)\n'
        r'_([^_]+)_\n'
        r'(?:"([^"]*)"\n)?'
        r'Personagens:\s*([^\n]+)',
        re.MULTILINE
    )

    recovered = []
    for msg in chat_history:
        if msg.get("role") != "assistant":
            continue
        text = msg.get("text", "")
        for m in scene_pattern.finditer(text):
            scene_num = int(m.group(1))
            if scene_num not in current_nums:
                recovered.append({
                    "scene_number": scene_num,
                    "time_start": m.group(2).split("-")[0].strip(),
                    "time_end": m.group(2).split("-")[1].strip() if "-" in m.group(2) else "",
                    "title": m.group(3).strip(),
                    "description": m.group(4).strip(),
                    "dialogue": m.group(5).strip() if m.group(5) else "",
                    "characters_in_scene": [c.strip() for c in m.group(6).split(",")],
                    "emotion": "",
                    "camera": "",
                    "transition": "cut",
                })
                current_nums.add(scene_num)

    if not recovered:
        return {"status": "ok", "message": "No missing scenes found in chat history", "total_scenes": len(current_scenes)}

    merged = current_scenes + recovered
    merged.sort(key=lambda x: x.get("scene_number", 0))
    project["scenes"] = merged
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _add_milestone(project, "scenes_merged", f"Cenas recuperadas do histórico — {len(recovered)} cenas adicionadas (total: {len(merged)})")
    _save_project(tenant["id"], settings, projects)

    logger.info(f"Studio [{project_id}]: Merged {len(recovered)} recovered scenes from chat history (total: {len(merged)})")
    return {
        "status": "ok",
        "recovered": len(recovered),
        "total_scenes": len(merged),
        "recovered_scene_numbers": sorted([s["scene_number"] for s in recovered]),
    }


@router.post("/projects/{project_id}/recover-videos")
async def recover_videos(project_id: str, tenant=Depends(get_current_tenant)):
    """Recover video URLs from Supabase Storage when outputs array was lost (race condition fix)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    existing_outputs = {o.get("scene_number") for o in project.get("outputs", []) if o.get("url")}
    recovered = []

    for s in scenes:
        sn = s.get("scene_number", 0)
        if sn in existing_outputs:
            continue
        filename = f"studio/{project_id}_scene_{sn}.mp4"
        try:
            url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
            # Verify the file exists by checking the URL
            import httpx
            resp = httpx.head(url, timeout=5, follow_redirects=True)
            if resp.status_code == 200:
                recovered.append({
                    "id": uuid.uuid4().hex[:8], "type": "video", "url": url,
                    "scene_number": sn, "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            continue

    if recovered:
        outputs = project.get("outputs", [])
        outputs.extend(recovered)
        outputs.sort(key=lambda x: x.get("scene_number", 0))
        project["outputs"] = outputs
        project["status"] = "complete"
        project["error"] = None
        _add_milestone(project, "videos_recovered", f"{len(recovered)} vídeos recuperados do storage")
        _save_project(tenant["id"], settings, projects)

    return {
        "status": "ok",
        "recovered": len(recovered),
        "total_outputs": len(project.get("outputs", [])),
        "project_status": project.get("status"),
    }


# ── STEP 1: Screenwriter Chat ──

SCREENWRITER_SYSTEM_PHASE1 = """You are a MASTER SCREENWRITER and WORLD-BUILDER.

TASK: Create a screenplay structure. Return ONLY valid JSON:
{{
  "title": "Story Title",
  "total_scenes": N,
  "characters": [
    {{"name": "Name", "description": "DETAILED physical: species/type, body shape, size, colors, textures (fur/skin/feathers), clothing/accessories, unique features", "age": "young/adult/old", "role": "protagonist/supporting"}}
  ],
  "scenes": [SCENES_HERE],
  "research_notes": "Sources used",
  "narration": "Brief context"
}}

Each scene:
{{"scene_number": N, "time_start": "M:SS", "time_end": "M:SS", "title": "Title", "description": "RICH visual: WHERE (landscape, nature), WHEN (time of day, weather), WHAT (action), ATMOSPHERE (light, colors)", "dialogue": "Text or narration", "characters_in_scene": ["Name"], "emotion": "mood", "camera": "shot type", "transition": "fade/cut"}}

RULES:
- Each scene = EXACTLY 12 seconds
- Max 8 scenes per response (if more needed, note it)
- Describe characters PHYSICALLY in detail with species-accurate features
- CRITICAL: If the story uses animals as characters, ALL descriptions MUST use animal features (fur, feathers, hooves, tails, snouts, paws). NEVER describe animal characters with human features (hands, fingers, human skin)
- Characters MUST maintain visually consistent appearance across ALL scenes — same colors, same clothing, same distinguishing marks
- Every scene description MUST include: specific location, time of day, atmosphere, background elements
- Be faithful to source material (bible, history, etc.)
- **LANGUAGE RULE (MANDATORY)**: ALL text content — title, scene titles, descriptions, dialogue, narration, research_notes — MUST be written ENTIRELY in {lang_name} ({lang}). Do NOT write in English unless the language IS English. This is NON-NEGOTIABLE."""

LANG_FULL_NAMES = {"pt": "Português (Brazilian Portuguese)", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "it": "Italiano"}


def _run_screenwriter_background(tenant_id: str, project_id: str, message: str, lang: str):
    """Background thread: call Claude screenwriter and save result. Uses chunked approach for reliability."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        chat_history = project.get("chat_history", [])

        history_text = "\n".join([
            f"{'USER' if m['role']=='user' else 'SCREENWRITER'}: {m['text'][:500]}"
            for m in chat_history[-6:]
        ])

        audio_mode = project.get("audio_mode", "narrated")

        system = SCREENWRITER_SYSTEM_PHASE1.replace("{lang}", lang).replace("{lang_name}", LANG_FULL_NAMES.get(lang, lang))

        # Inject audio mode context into prompt
        audio_instruction = ""
        lang_name = LANG_FULL_NAMES.get(lang, lang)
        if audio_mode == "dubbed":
            audio_instruction = f"""

AUDIO MODE: DUBBED (character voices + occasional narrator). The "dialogue" field MUST contain character dialogue lines IN {lang_name}. A narrator may also appear when needed to bridge scenes, explain time passages, or add emotional context — but the MAJORITY of the text should be character dialogue.
Format EXACTLY like this:
"dialogue": "Narrador: 'Naquela noite, sob o manto de estrelas...' / Abraão: 'Meu filho, vamos subir o monte juntos.' / Isaac: 'Sim, pai! Mas onde está o cordeiro?' / Abraão: 'Deus proverá, meu filho.'"

RULES for DUBBED mode:
- Each speaker must be prefixed with their name (or "Narrador") followed by colon
- Separate different speakers with " / "
- Character dialogue should be the MAJORITY (70%+) of the text
- Use "Narrador:" sparingly — only to introduce a scene, mark time passing, or add emotional weight
- Every scene MUST have at least one character speaking
- Keep dialogue natural, emotional, and age-appropriate for each character
- ALL dialogue and narration MUST be in {lang_name}"""
        else:
            audio_instruction = f"""

AUDIO MODE: NARRATED (voice-over narrator). The "dialogue" field should contain narrator text IN {lang_name}.
Format: "dialogue": "Narrador: 'Descrição do que acontece nesta cena...'"
- Use a storytelling narrator voice
- Keep narration concise (2-3 sentences per scene)
- ALL narration MUST be in {lang_name}"""

        # Detect if project already has scenes (continuation vs new screenplay)
        existing_scenes = project.get("scenes", [])
        is_continuation = len(existing_scenes) > 0

        if is_continuation:
            existing_summary = "\n".join([
                f"Scene {s.get('scene_number')}: {s.get('title')} ({s.get('time_start')}-{s.get('time_end')})"
                for s in existing_scenes
            ])
            last_scene_num = max(s.get("scene_number", 0) for s in existing_scenes)
            last_time_end = existing_scenes[-1].get("time_end", "0:00") if existing_scenes else "0:00"
            user_prompt = f"""Previous conversation:
{history_text}

EXISTING SCREENPLAY (already written — DO NOT rewrite these, only ADD new scenes):
{existing_summary}

The user now says: {message}
{audio_instruction}

CONTINUATION RULES:
- Scene numbers MUST start from {last_scene_num + 1}
- Time starts from {last_time_end} (each scene = 12 seconds)
- Keep the same characters, visual style, and narrative tone
- Return ONLY JSON with "scenes" array containing the NEW scenes (continuation only)
- Also return "characters" array with any NEW characters introduced (or empty array if none)
- Return "total_scenes" as the total number of NEW scenes in this batch
- ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}"""
        else:
            user_prompt = f"""Previous conversation:
{history_text}

Current request: {message}
{audio_instruction}

Create the screenplay. If the story needs more than 8 scenes, generate the first 8 now. Return ONLY valid JSON."""

        # Phase 1: Get first batch of scenes (up to 8)
        result = _call_claude_sync(system, user_prompt, max_tokens=6000)
        parsed = _parse_json(result)

        if not parsed:
            # Try to extract from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result)
            if json_match:
                parsed = _parse_json(json_match.group(1))

        # Re-read project (may have changed)
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        chat_history = project.get("chat_history", [])

        if parsed:
            all_scenes = parsed.get("scenes", [])
            all_characters = parsed.get("characters", [])
            total_needed = parsed.get("total_scenes", len(all_scenes))

            # Phase 2: If more scenes needed, generate continuation
            if total_needed > len(all_scenes):
                try:
                    continuation_prompt = f"""Continue the screenplay from scene {len(all_scenes) + 1} to {total_needed}.

Previous scenes already written:
{', '.join(f'Scene {s.get("scene_number")}: {s.get("title")}' for s in all_scenes)}

Characters: {', '.join(c.get('name','') for c in all_characters)}
Story: {message}

ALL text (titles, descriptions, dialogue) MUST be in {LANG_FULL_NAMES.get(lang, lang)}.
Return ONLY JSON with a "scenes" array containing the remaining scenes (same format)."""

                    cont_result = _call_claude_sync(system, continuation_prompt, max_tokens=3000)
                    cont_parsed = _parse_json(cont_result)
                    if not cont_parsed:
                        import re
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', cont_result)
                        if json_match:
                            cont_parsed = _parse_json(json_match.group(1))

                    if cont_parsed and cont_parsed.get("scenes"):
                        all_scenes.extend(cont_parsed["scenes"])
                        if cont_parsed.get("characters"):
                            existing_names = {c["name"] for c in all_characters}
                            for c in cont_parsed["characters"]:
                                if c.get("name") not in existing_names:
                                    all_characters.append(c)
                        logger.info(f"Studio [{project_id}]: Phase 2 added {len(cont_parsed['scenes'])} more scenes (total: {len(all_scenes)})")
                except Exception as e2:
                    logger.warning(f"Studio [{project_id}]: Phase 2 continuation failed: {e2}. Using {len(all_scenes)} scenes.")

            # Re-read existing scenes (project may have been re-fetched)
            prev_scenes = project.get("scenes", [])
            prev_scene_nums = {s.get("scene_number") for s in prev_scenes}
            new_scene_nums = {s.get("scene_number") for s in all_scenes}

            # Smart merge: if new scenes don't overlap with existing, append (continuation)
            if prev_scenes and new_scene_nums and not prev_scene_nums.intersection(new_scene_nums):
                merged_scenes = prev_scenes + all_scenes
                merged_scenes.sort(key=lambda x: x.get("scene_number", 0))
                project["scenes"] = merged_scenes
                # Merge characters (add new ones only)
                existing_char_names = {c.get("name") for c in project.get("characters", [])}
                for c in all_characters:
                    if c.get("name") not in existing_char_names:
                        project.get("characters", []).append(c)
                logger.info(f"Studio [{project_id}]: Merged {len(all_scenes)} new scenes with {len(prev_scenes)} existing (total: {len(merged_scenes)})")
            else:
                # Fresh screenplay or overlap — replace
                project["scenes"] = all_scenes
                project["characters"] = all_characters

            final_scenes = project["scenes"]
            final_characters = project.get("characters", [])

            project["agents_output"] = project.get("agents_output", {})
            project["agents_output"]["screenwriter"] = {
                "title": parsed.get("title", ""),
                "research_notes": parsed.get("research_notes", ""),
                "narration": parsed.get("narration", ""),
            }
            assistant_text = f"**{parsed.get('title', 'Roteiro')}** — {len(all_scenes)} {'novas cenas' if prev_scenes and not prev_scene_nums.intersection(new_scene_nums) else 'cenas'} (total: {len(final_scenes)})\n\n"
            for s in all_scenes:
                assistant_text += f"**CENA {s.get('scene_number','')}** ({s.get('time_start','')}-{s.get('time_end','')}) — {s.get('title','')}\n"
                assistant_text += f"_{s.get('description','')}_\n"
                if s.get('dialogue'):
                    assistant_text += f'"{s["dialogue"]}"\n'
                assistant_text += f"Personagens: {', '.join(s.get('characters_in_scene',[]))}\n\n"
            assistant_text += f"\n**Personagens identificados:** {', '.join(c.get('name','') for c in final_characters)}"
            if parsed.get("research_notes"):
                assistant_text += f"\n\n**Pesquisa:** {parsed['research_notes'][:300]}"
        else:
            assistant_text = result

        chat_history.append({"role": "assistant", "text": assistant_text})
        project["chat_history"] = chat_history[-20:]
        project["status"] = "scripting"
        project["chat_status"] = "done"
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        n_scenes = len(project.get('scenes', []))
        n_chars = len(project.get('characters', []))
        _add_milestone(project, "screenplay_created", f"Roteiro criado — {n_scenes} cenas, {n_chars} personagens")
        _save_project(tenant_id, settings, projects)

        logger.info(f"Studio [{project_id}]: Screenwriter done — {n_scenes} scenes")

    except Exception as e:
        logger.error(f"Studio [{project_id}] screenwriter error: {e}")
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["chat_status"] = "error"
            project["error"] = str(e)[:300]
            _save_project(tenant_id, settings, projects)


@router.post("/chat")
async def screenwriter_chat(req: ChatMessage, tenant=Depends(get_current_tenant)):
    """Start screenwriter in background (avoids K8s 60s proxy timeout)."""
    lang = req.language or "pt"

    if req.project_id:
        settings, projects, project = _get_project(tenant["id"], req.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        settings = _get_settings(tenant["id"])
        projects = settings.get("studio_projects", [])
        now = datetime.now(timezone.utc).isoformat()
        project = {
            "id": uuid.uuid4().hex[:12],
            "name": req.message[:50],
            "scene_type": "multi_scene",
            "briefing": req.message,
            "scenes": [],
            "characters": [],
            "chat_history": [],
            "agents_output": {},
            "agent_status": {},
            "outputs": [],
            "status": "scripting",
            "chat_status": "thinking",
            "error": None,
            "language": lang,
            "created_at": now,
            "updated_at": now,
        }
        projects.insert(0, project)

    # Save user message and set thinking status
    chat_history = project.get("chat_history", [])
    chat_history.append({"role": "user", "text": req.message})
    project["chat_history"] = chat_history[-20:]
    project["chat_status"] = "thinking"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)

    # Start background thread
    thread = threading.Thread(
        target=_run_screenwriter_background,
        args=(tenant["id"], project["id"], req.message, lang),
        daemon=True,
    )
    thread.start()

    return {
        "project_id": project["id"],
        "status": "thinking",
        "message": None,
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
    }



@router.post("/projects/{project_id}/reset-chat")
async def reset_chat(project_id: str, tenant=Depends(get_current_tenant)):
    """Reset a stuck chat_status back to 'idle' so user can retry."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["chat_status"] = "idle"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "chat_status": "idle"}


@router.post("/projects/{project_id}/retry-chat")
async def retry_chat(project_id: str, tenant=Depends(get_current_tenant)):
    """Retry the last user message in the screenwriter chat."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_history = project.get("chat_history", [])
    last_user_msg = None
    for m in reversed(chat_history):
        if m["role"] == "user":
            last_user_msg = m["text"]
            break

    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message to retry")

    project["chat_status"] = "thinking"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)

    lang = project.get("language", "pt")
    thread = threading.Thread(
        target=_run_screenwriter_background,
        args=(tenant["id"], project_id, last_user_msg, lang),
        daemon=True,
    )
    thread.start()

    return {"status": "thinking", "message": last_user_msg}



# ── STEP 3: Multi-Scene Production Pipeline (v3 — Per-Scene Parallel Teams) ──

def _update_scene_status(tenant_id: str, project_id: str, scene_num: int, status: str, total: int):
    """Thread-safe scene status update. Reads current state, merges, writes."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        agent_status = project.get("agent_status", {})
        scene_status = agent_status.get("scene_status", {})
        scene_status[str(scene_num)] = status
        videos_done = sum(1 for v in scene_status.values() if v == "done")
        agent_status.update({
            "current_scene": scene_num, "total_scenes": total,
            "phase": status if status in ("directing", "generating_video", "concatenating") else agent_status.get("phase", "running"),
            "scene_status": scene_status,
            "videos_done": videos_done,
        })
        project["agent_status"] = agent_status
        _save_project(tenant_id, settings, projects)
    except Exception:
        pass


# Thread-safe lock for saving scene videos (prevents race conditions in parallel mode)
_save_video_lock = threading.Lock()


def _save_scene_video(tenant_id: str, project_id: str, scene_num: int, video_url: str, total: int):
    """Save a completed scene video immediately for real-time preview (thread-safe)."""
    try:
        with _save_video_lock:
            settings, projects, project = _get_project(tenant_id, project_id)
            if not project:
                return
            outputs = project.get("outputs", [])
            if not any(o.get("scene_number") == scene_num for o in outputs):
                outputs.append({
                    "id": uuid.uuid4().hex[:8], "type": "video", "url": video_url,
                    "scene_number": scene_num, "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            project["outputs"] = outputs
            _add_milestone(project, f"video_scene_{scene_num}", f"Vídeo cena {scene_num} gerado")
            _save_project(tenant_id, settings, projects)
        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
    except Exception as e:
        logger.warning(f"_save_scene_video scene {scene_num}: {e}")


def _run_multi_scene_production(tenant_id: str, project_id: str, character_avatars: dict = None):
    """v4 — Decoupled Pipeline: ALL Directors first (parallel) → ALL Sora jobs queued.

    Architecture:
    PHASE A (Preparation — ~5s):
    ┌─ Director(Claude) Scene 1  ─┐
    ├─ Director(Claude) Scene 2  ─┤  ALL PARALLEL → 15 Sora prompts ready
    ├─ Director(Claude) Scene N  ─┤
    └─ MusicDirector              ┘

    PHASE B (Production — priority queue):
    Sora Queue → [1,2,3,4,5] → [6,7,8,9,10] → [11,12,13,14,15]
                  5 slots simultaneous

    → FFmpeg concat → Complete
    """
    import json as json_mod
    import tempfile
    import time as _time

    try:
        t_start = _time.time()
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        characters = project.get("characters", [])
        total = len(scenes)
        char_avatars = character_avatars or project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")

        if total == 0:
            _update_project_field(tenant_id, project_id, {"status": "error", "error": "No scenes"})
            return

        _update_project_field(tenant_id, project_id, {
            "status": "running_agents",
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "starting_teams",
                             "scene_status": {str(i+1): "queued" for i in range(total)}}
        })

        # ── Visual Style Mapping ──
        STYLE_PROMPTS = {
            "animation": "ART STYLE: High-quality 3D animation like Pixar/DreamWorks. Colorful, warm, expressive characters with large eyes. Smooth cinematic camera movements. Rich detailed environments.",
            "cartoon": "ART STYLE: Vibrant 2D cartoon style. Bold outlines, saturated colors, exaggerated expressions. Playful and fun atmosphere.",
            "anime": "ART STYLE: Japanese anime style. Detailed backgrounds, expressive eyes, dramatic lighting. Fluid motion.",
            "realistic": "ART STYLE: Cinematic photorealistic live-action. Film grain, natural lighting, professional cinematography.",
            "watercolor": "ART STYLE: Watercolor painting style. Soft edges, pastel tones, dreamy ethereal atmosphere.",
        }
        # Use animation_sub for more specific style
        animation_sub = project.get("animation_sub", "pixar_3d")
        ANIMATION_SUB_PROMPTS = {
            "pixar_3d": "ART STYLE: Premium 3D CGI animation identical to Pixar/DreamWorks (Toy Story, Shrek quality). Subsurface scattering on skin/fur, global illumination, cinematic depth of field, warm color grading. Characters with large expressive eyes, smooth rounded features. MUST maintain consistent 3D rendering across ALL scenes.",
            "cartoon_3d": "ART STYLE: Stylized 3D cartoon animation (similar to Paw Patrol, Cocomelon). Bright saturated colors, simplified shapes, thick outlines on 3D models, flat shading with cel-shading effect. Playful and vibrant. MUST maintain consistent style across ALL scenes.",
            "cartoon_2d": "ART STYLE: Classic 2D hand-drawn animation (Disney Renaissance, Studio Ghibli). Clean line art, watercolor-like coloring, fluid character animation, painted backgrounds. MUST maintain consistent 2D art style across ALL scenes.",
            "anime_2d": "ART STYLE: Japanese anime (Studio Ghibli, Makoto Shinkai quality). Detailed backgrounds with atmospheric perspective, dramatic lighting, speed lines for action, large expressive eyes. MUST maintain consistent anime style across ALL scenes.",
            "realistic": "ART STYLE: Cinematic photorealistic live-action. Shallow depth of field, film grain, natural lighting, 35mm anamorphic lens look. Professional cinematography with handheld camera feel. MUST maintain consistent photorealistic style.",
            "watercolor": "ART STYLE: Watercolor painting animation. Visible brush strokes, bleeding edges, soft pastel tones, paper texture overlay. Dreamy ethereal atmosphere. MUST maintain consistent painted style across ALL scenes.",
        }
        style_hint = ANIMATION_SUB_PROMPTS.get(animation_sub, STYLE_PROMPTS.get(visual_style, STYLE_PROMPTS["animation"]))

        # ── Shared context ──
        briefing = project.get("briefing", "")

        # ── Pre-download avatars ONCE ──
        avatar_cache = {}
        for name, url in char_avatars.items():
            if url and url not in avatar_cache:
                try:
                    full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                    logger.info(f"Studio [{project_id}]: Avatar cached for {name}")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Avatar download failed for {name}: {e}")
                    avatar_cache[url] = None

        # ── Resume support — find already completed videos ──
        _, _, proj_check = _get_project(tenant_id, project_id)
        existing_outputs = proj_check.get("outputs", []) if proj_check else []
        completed_videos = {}
        for o in existing_outputs:
            sn = o.get("scene_number")
            if sn and o.get("url") and o.get("type") == "video" and sn > 0:
                completed_videos[sn] = o["url"]
        if completed_videos:
            logger.info(f"Studio [{project_id}]: Resuming — {len(completed_videos)} scenes already cached: {sorted(completed_videos.keys())}")

        # ══ PRE-PRODUCTION: Avatar Analysis + Production Design Document ══
        # Check if pre-production was already done via Preview Board
        existing_pd = project.get("agents_output", {}).get("production_design")
        existing_ad = project.get("agents_output", {}).get("avatar_descriptions")

        if existing_pd and isinstance(existing_pd, dict) and existing_pd.get("character_bible"):
            logger.info(f"Studio [{project_id}]: PRE-PRODUCTION already done via Preview Board — skipping")
            production_design = existing_pd
            avatar_descriptions = existing_ad or {}
        else:
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "pre_production",
                                 "scene_status": {str(i+1): "queued" for i in range(total)}}
            })
            logger.info(f"Studio [{project_id}]: PRE-PRODUCTION — Analyzing avatars and building production design")

            # Step 1: Analyze avatars with Claude Vision (ONE call for all avatars)
            avatar_descriptions = _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id)

            # Step 2: Build Production Design Document (ONE call — replaces music, style, location, continuity planning)
            production_design = _build_production_design(
                briefing, characters, scenes, avatar_descriptions, visual_style,
                project.get("language", "pt"), project_id
            )

            _update_project_field(tenant_id, project_id, {
                "agents_output": {**project.get("agents_output", {}),
                                  "production_design": production_design,
                                  "avatar_descriptions": avatar_descriptions},
            })

        # Extract production design elements for efficient access by directors
        pd_style = production_design.get("style_anchors", style_hint)
        # ── CONTINUITY ENGINE: Build rigid Style DNA ──
        continuity_mode = project.get("continuity_mode", True)
        if continuity_mode:
            style_dna = _build_style_dna(animation_sub, production_design)
            pd_style = f"{style_dna} {pd_style}"
            logger.info(f"Studio [{project_id}]: CONTINUITY ENGINE ON — Style DNA injected ({len(style_dna)} chars)")
        pd_chars = production_design.get("character_bible", {})
        pd_locations = production_design.get("location_bible", {})
        pd_scene_dirs = {d.get("scene", 0): d for d in production_design.get("scene_directions", [])}
        pd_color = production_design.get("color_palette", {})
        pd_music = production_design.get("music_plan", [])

        t_preproduction = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: PRE-PRODUCTION complete in {t_preproduction:.1f}s — {len(pd_chars)} characters, {len(pd_locations)} locations")

        _add_milestone(project, "preproduction_done", f"Pré-produção — {t_preproduction:.0f}s")
        _update_project_field(tenant_id, project_id, {
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "pre_production_done",
                             "scene_status": {str(i+1): "queued" for i in range(total)}}
        })

        # ── Rate limiter for Sora 2 ──
        sora_semaphore = threading.Semaphore(5)

        # Use direct OpenAI key for Sora 2
        video_gen = DirectSora2Client(api_key=OPENAI_API_KEY)
        logger.info(f"Studio [{project_id}]: Using DIRECT OpenAI key for Sora 2")

        # Track budget state across threads
        budget_exhausted = threading.Event()

        def _scene_director(scene, scene_num):
            """PHASE A — Scene Director: generates Sora prompt using Production Design Bible.
            Uses pre-computed character_bible, location_bible, and style_anchors for consistency.
            Token-efficient: creative decisions pre-made by Production Designer.
            """
            if scene_num in completed_videos:
                return {"scene_number": scene_num, "sora_prompt": None, "cached": True}

            chars_in_scene = scene.get("characters_in_scene", [])

            # Canonical character descriptions from Production Design Bible
            char_descs = "\n".join([
                f"- {name}: {pd_chars.get(name, next((ch.get('description','') for ch in characters if ch.get('name')==name), 'Unknown character'))}"
                for name in chars_in_scene
            ])

            # Scene-specific direction from Production Design
            scene_dir = pd_scene_dirs.get(scene_num, {})
            loc_key = scene_dir.get("location_key", "")
            loc_desc = pd_locations.get(loc_key, "")
            time_day = scene_dir.get("time_of_day", "afternoon")
            time_light = pd_color.get(time_day, pd_color.get("global", ""))
            cam_flow = scene_dir.get("camera_flow", scene.get("camera", ""))
            trans_note = scene_dir.get("transition_note", "")

            director_system = f"""You are a SCENE DIRECTOR for Sora 2 video generation. Convert scene descriptions into detailed visual prompts.

MANDATORY STYLE (include VERBATIM at the start of your prompt): {pd_style}

Return ONLY JSON: {{"sora_prompt": "ONE detailed English paragraph for Sora 2, max 300 words"}}

CRITICAL RULES:
- START your prompt with the exact mandatory style text above — copy it word for word
- Describe EVERY character by their EXACT PHYSICAL APPEARANCE from the character descriptions below — these descriptions come from analyzing the actual avatar images, so they are the ABSOLUTE SOURCE OF TRUTH
- For EACH character appearing in the scene, copy their FULL character_bible description into the prompt — DO NOT summarize or abbreviate
- SPECIES LOCK: If a character is described as an "anthropomorphic camel", they are ALWAYS a camel in EVERY scene — NEVER a lion, bear, or any other animal
- POSTURE LOCK: If a character is described as "bipedal/standing upright", they MUST be shown standing on two legs — NEVER as a quadruped walking on four legs
- NEVER add extra animals or characters that are NOT in the CHARACTER IDENTITY SHEET below — if only Abraão and Isaac are in the scene, ONLY those two characters appear
- NEVER use character names in the prompt — only physical descriptions
- If a scene describes a "birth" or "baby", the young character MUST be a tiny newborn infant of the SAME SPECIES as the parents — NOT a teenager or adult
- If a scene says "child" or "young", the character must be visibly SMALL and childlike — NOT adult-sized
- Include: specific environment details, lighting matching the time of day, atmospheric elements, character actions/expressions, camera movement
- Each scene must look like it belongs to the SAME FILM — same art technique, same 3D rendering quality, same color grading
- The sora_prompt MUST be in ENGLISH"""

            director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}

CHARACTER IDENTITY SHEET (from avatar image analysis — ABSOLUTE SOURCE OF TRUTH, DO NOT DEVIATE):
{char_descs}

AGE/LIFE STAGE CONTEXT FOR THIS SCENE: Based on the scene description above, determine the correct age of each character.
- If the scene describes a "birth" or "newborn", the baby character is a TINY INFANT of the same species — small enough to be held in arms.
- If the scene describes "growing up" or "childhood", the young character is a SMALL CHILD — about half the height of the adults.

LOCATION: {loc_desc}
TIME OF DAY: {time_day} — Light/Colors: {time_light}
CAMERA: {cam_flow}
CONTINUITY WITH PREVIOUS SCENE: {trans_note}"""

            _update_scene_status(tenant_id, project_id, scene_num, "directing", total)
            try:
                t_p = _time.time()
                result_text = _call_claude_sync(director_system, director_prompt, max_tokens=1000)
                data = _parse_json(result_text) or {}
                sora_prompt = data.get("sora_prompt", scene.get("description", ""))
                elapsed = _time.time() - t_p
                logger.info(f"Studio [{project_id}]: Scene {scene_num} directed in {elapsed:.1f}s")
                return {"scene_number": scene_num, "sora_prompt": sora_prompt, "cached": False}
            except Exception as e:
                logger.warning(f"Studio [{project_id}]: Scene {scene_num} director error: {e}")
                # Fallback: construct prompt directly from production design elements
                char_desc_text = ". ".join([pd_chars.get(n, '') for n in chars_in_scene if pd_chars.get(n)])
                fallback = f"{pd_style}. {loc_desc}. {time_day}, {time_light}. {char_desc_text}. {scene.get('description', '')}."
                return {"scene_number": scene_num, "sora_prompt": fallback[:1000], "cached": False}

        def _sora_render(directed_scene, scene):
            """PHASE B — Sora 2 video render with retries, budget awareness, and continuity anchoring."""
            scene_num = directed_scene["scene_number"]

            if directed_scene.get("cached"):
                _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                return {"scene_number": scene_num, "url": completed_videos[scene_num], "type": "video", "duration": 12}

            if budget_exhausted.is_set():
                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

            sora_prompt = directed_scene["sora_prompt"]
            chars_in_scene = scene.get("characters_in_scene", [])

            # KEYFRAME-FIRST: If continuity mode, generate a Gemini keyframe first
            # This forces correct character identity that Sora 2 can't override
            keyframe_path = directed_scene.get("_keyframe_path")
            char_ref = _create_composite_avatar(chars_in_scene, char_avatars, avatar_cache)
            # Prefer keyframe > avatar composite
            ref_path = keyframe_path if (keyframe_path and os.path.exists(keyframe_path)) else char_ref

            _update_scene_status(tenant_id, project_id, scene_num, "waiting_sora", total)

            max_retries = 3
            last_error = None

            with sora_semaphore:
                for attempt in range(max_retries):
                    if budget_exhausted.is_set():
                        _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                        return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

                    _update_scene_status(tenant_id, project_id, scene_num, "generating_video", total)
                    t_v = _time.time()
                    try:
                        gen_kwargs = {"prompt": sora_prompt[:1000], "model": "sora-2", "size": "1280x720", "duration": 12, "max_wait_time": 600}
                        if ref_path:
                            gen_kwargs["image_path"] = ref_path

                        logger.info(f"Studio [{project_id}]: Scene {scene_num} Sora 2 attempt {attempt+1}/{max_retries} (avatar={'Y' if ref_path else 'N'})")
                        video_bytes = video_gen.text_to_video(**gen_kwargs)
                        elapsed = _time.time() - t_v

                        if video_bytes and len(video_bytes) > 1000:
                            filename = f"studio/{project_id}_scene_{scene_num}.mp4"
                            video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                            logger.info(f"Studio [{project_id}]: Scene {scene_num} DONE {elapsed:.0f}s ({len(video_bytes)//1024}KB)")
                            _save_scene_video(tenant_id, project_id, scene_num, video_url, total)
                            return {"scene_number": scene_num, "url": video_url, "type": "video", "duration": 12}
                        else:
                            sz = len(video_bytes) if video_bytes else 0
                            if elapsed < 30:
                                logger.error(f"Studio [{project_id}]: Scene {scene_num} BUDGET EXHAUSTED ({sz}B in {elapsed:.0f}s)")
                                budget_exhausted.set()
                                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                                return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}
                            else:
                                last_error = f"empty_video_{sz}B"
                                logger.warning(f"Studio [{project_id}]: Scene {scene_num} attempt {attempt+1} empty ({sz}B in {elapsed:.0f}s)")
                                if attempt < max_retries - 1:
                                    _time.sleep(10)

                    except Exception as ve:
                        err_str = str(ve).lower()
                        elapsed = _time.time() - t_v
                        if "budget" in err_str or "exceeded" in err_str or "insufficient" in err_str:
                            logger.error(f"Studio [{project_id}]: Scene {scene_num} BUDGET ERROR: {ve}")
                            budget_exhausted.set()
                            _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                            return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

                        last_error = str(ve)[:200]
                        is_retryable = any(k in err_str for k in ["disconnect", "server", "timeout", "connection", "reset", "eof"])
                        if is_retryable and attempt < max_retries - 1:
                            wait = 15 * (attempt + 1)
                            logger.warning(f"Studio [{project_id}]: Scene {scene_num} Sora attempt {attempt+1} FAIL: {ve}. Retry in {wait}s...")
                            _time.sleep(wait)
                            continue
                        else:
                            logger.warning(f"Studio [{project_id}]: Scene {scene_num} Sora FAIL after {attempt+1} attempts: {ve}")

                # All retries exhausted
                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                return {"scene_number": scene_num, "url": None, "type": "video", "error": last_error or "unknown"}

        # ══ PHASE A: ALL DIRECTORS IN PARALLEL (Production-Design-guided) ══
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info(f"Studio [{project_id}]: PHASE A — Launching {total} Scene Directors (parallel, PD-guided)")

        directed_scenes = []
        with ThreadPoolExecutor(max_workers=total) as executor:
            director_futures = {
                executor.submit(_scene_director, s, s.get("scene_number", i+1)): (i, s)
                for i, s in enumerate(scenes)
            }

            for future in as_completed(director_futures):
                result = future.result()
                directed_scenes.append(result)
                cached = result.get("cached", False)
                logger.info(f"Studio [{project_id}]: Director {result['scene_number']}/{total} done {'(CACHED)' if cached else ''}")

        music_data = {"plan": pd_music, "mood": "cinematic"}

        t_phase_a = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: PHASE A complete in {t_phase_a:.1f}s — {len(directed_scenes)} prompts ready")

        # Sort by scene number for ordered Sora queue
        directed_scenes.sort(key=lambda x: x["scene_number"])

        # ══ PHASE B: SORA RENDERS ══
        # Both modes now use parallel rendering (semaphore controls Sora 2 concurrency)
        # Continuity mode: generates keyframes first (parallel), then renders in parallel
        # Normal mode: renders directly in parallel
        scene_videos = []
        scene_map = {s.get("scene_number", i+1): s for i, s in enumerate(scenes)}

        if continuity_mode:
            logger.info(f"Studio [{project_id}]: PHASE B (CONTINUITY PARALLEL) — Keyframe generation + parallel rendering")

            # B1: Generate ALL keyframes in parallel (Gemini, 5 concurrent)
            keyframe_paths = []

            def _generate_keyframe_for_scene(ds):
                """Generate keyframe for a single scene (thread-safe)."""
                sn = ds["scene_number"]
                if ds.get("cached"):
                    return ds
                sd = scene_map.get(sn, scenes[0])
                chars_in = sd.get("characters_in_scene", [])
                kf_path = None
                for kf_attempt in range(3):
                    kf_path = _generate_scene_keyframe(
                        ds["sora_prompt"], char_avatars, avatar_cache,
                        chars_in, project_id, sn,
                        character_bible=pd_chars
                    )
                    if kf_path:
                        break
                    logger.warning(f"Studio [{project_id}]: Keyframe retry {kf_attempt+1}/3 for scene {sn}")
                    _time.sleep(2)
                if kf_path:
                    ds["_keyframe_path"] = kf_path
                    keyframe_paths.append(kf_path)
                else:
                    logger.warning(f"Studio [{project_id}]: Keyframe FAILED all retries for scene {sn} — using avatar fallback")
                return ds

            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_keyframes",
                                 "videos_done": 0, "scene_status": {str(ds["scene_number"]): "queued" for ds in directed_scenes}}
            })

            with ThreadPoolExecutor(max_workers=5) as executor:
                kf_futures = {executor.submit(_generate_keyframe_for_scene, ds): ds["scene_number"] for ds in directed_scenes}
                for future in as_completed(kf_futures):
                    sn = kf_futures[future]
                    future.result()  # ensures exceptions propagate
                    logger.info(f"Studio [{project_id}]: Keyframe {sn}/{total} ready")

            logger.info(f"Studio [{project_id}]: All {total} keyframes ready — launching parallel Sora 2 renders")

            # B2: Render ALL videos in parallel (Sora 2, controlled by sora_semaphore=5)
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_video",
                                 "videos_done": 0, "scene_status": {str(ds["scene_number"]): "waiting_sora" for ds in directed_scenes}}
            })

            with ThreadPoolExecutor(max_workers=total) as executor:
                sora_futures = {
                    executor.submit(_sora_render, ds, scene_map.get(ds["scene_number"], scenes[0])): ds["scene_number"]
                    for ds in directed_scenes
                }
                for future in as_completed(sora_futures):
                    result = future.result()
                    scene_videos.append(result)
                    done = len([v for v in scene_videos if v.get("url")])
                    _update_project_field(tenant_id, project_id, {
                        "agent_status": {"current_scene": result["scene_number"], "total_scenes": total,
                                         "phase": "generating_video", "videos_done": done,
                                         "scene_status": {str(v["scene_number"]): ("done" if v.get("url") else "error") for v in scene_videos}}
                    })
                    logger.info(f"Studio [{project_id}]: Progress {done}/{total} (scene {result['scene_number']})")

            # Cleanup keyframe files
            for kf in keyframe_paths:
                try:
                    os.unlink(kf)
                except OSError:
                    pass
        else:
            logger.info(f"Studio [{project_id}]: PHASE B — Queueing {total} Sora 2 renders (5 slots, parallel)")

            with ThreadPoolExecutor(max_workers=total) as executor:
                sora_futures = {
                    executor.submit(_sora_render, ds, scene_map.get(ds["scene_number"], scenes[0])): ds["scene_number"]
                    for ds in directed_scenes
                }

                for future in as_completed(sora_futures):
                    result = future.result()
                    scene_videos.append(result)
                    done = len([v for v in scene_videos if v.get("url")])
                    sn = result.get("scene_number", "?")
                    if result.get("url"):
                        logger.info(f"Studio [{project_id}]: Progress {done}/{total} (scene {sn} OK)")
                    elif result.get("error"):
                        logger.warning(f"Studio [{project_id}]: Scene {sn} FAILED: {result.get('error','')}")

        t_prod = _time.time() - t_start
        successful = len([v for v in scene_videos if v.get("url")])
        budget_errors = len([v for v in scene_videos if "budget" in (v.get("error") or "")])
        logger.info(f"Studio [{project_id}]: ALL SCENES done in {t_prod:.0f}s ({t_prod/60:.1f}min) — {successful}/{total} OK, {budget_errors} budget errors")

        # Save production data
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["agents_output"] = {**project.get("agents_output", {}),
                                        "music_director": music_data,
                                        "production_design": production_design,
                                        "avatar_descriptions": avatar_descriptions}
            _add_milestone(project, "preproduction_complete", f"Pré-produção inteligente — {t_preproduction:.0f}s")
            _add_milestone(project, "agents_complete", f"Produção paralela — {t_prod:.0f}s")
            _save_project(tenant_id, settings, projects)

        # Cleanup avatars
        for path in avatar_cache.values():
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass

        # ── Concatenate Videos ──
        successful_videos = sorted(
            [sv for sv in scene_videos if sv.get("url")],
            key=lambda x: x["scene_number"]
        )
        final_url = None

        if len(successful_videos) > 1:
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "concatenating",
                                 "videos_done": len(successful_videos)}
            })
            logger.info(f"Studio [{project_id}]: Concatenating {len(successful_videos)} videos...")
            try:
                final_url = _concatenate_videos(successful_videos, project_id)
            except Exception as ce:
                logger.error(f"Studio [{project_id}]: Concat error: {ce}")
        elif len(successful_videos) == 1:
            final_url = successful_videos[0]["url"]

        # ── Save Final Results ──
        outputs = []
        for sv in sorted(scene_videos, key=lambda x: x.get("scene_number", 0)):
            if sv.get("url"):
                outputs.append({
                    "id": uuid.uuid4().hex[:8], "type": "video", "url": sv["url"],
                    "scene_number": sv["scene_number"], "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        if final_url and len(successful_videos) > 1:
            outputs.insert(0, {
                "id": uuid.uuid4().hex[:8], "type": "video", "url": final_url,
                "scene_number": 0, "label": "complete",
                "duration": len(successful_videos) * 12,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["outputs"] = outputs
            project["scene_videos"] = scene_videos
            project["status"] = "complete"
            project["agent_status"] = {
                "current_scene": total, "total_scenes": total, "phase": "complete",
                "videos_done": len(successful_videos),
                "scene_status": {str(sv["scene_number"]): ("done" if sv.get("url") else "error") for sv in scene_videos},
            }
            _add_milestone(project, "videos_generated", f"Vídeos gerados — {len(successful_videos)} cenas")
            if final_url:
                _add_milestone(project, "film_complete", f"Filme completo — {len(successful_videos)*12}s")
            _save_project(tenant_id, settings, projects)

        t_total = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: COMPLETE! {len(successful_videos)} videos in {t_total:.0f}s ({t_total/60:.1f}min)")

    except Exception as e:
        logger.error(f"Studio [{project_id}] pipeline error: {e}")
        _update_project_field(tenant_id, project_id, {
            "status": "error", "error": str(e)[:500],
        })


def _concatenate_videos(scene_videos: list, project_id: str) -> str:
    """Download scene videos, concatenate with FFmpeg, compress for upload, upload result."""
    import tempfile

    # Ensure FFmpeg is available
    if not _ensure_ffmpeg():
        logger.error(f"Studio [{project_id}]: FFmpeg unavailable, cannot concatenate")
        return None

    tmpdir = tempfile.mkdtemp()
    files = []

    for i, sv in enumerate(scene_videos):
        local_path = f"{tmpdir}/scene_{i:03d}.mp4"
        urllib.request.urlretrieve(sv["url"], local_path)
        files.append(local_path)
        logger.info(f"Studio [{project_id}]: Downloaded scene {sv.get('scene_number')} ({os.path.getsize(local_path)//1024}KB)")

    # Create concat file
    concat_file = f"{tmpdir}/concat.txt"
    with open(concat_file, 'w') as f:
        for fp in files:
            f.write(f"file '{fp}'\n")

    output_path = f"{tmpdir}/final_{project_id}.mp4"

    # Calculate total input size to decide compression strategy
    total_input_size = sum(os.path.getsize(fp) for fp in files)
    total_input_mb = total_input_size / (1024 * 1024)
    num_scenes = len(files)
    logger.info(f"Studio [{project_id}]: Concat {num_scenes} scenes, total input {total_input_mb:.1f}MB")

    # For small total inputs (<40MB), try stream copy first
    if total_input_mb < 40:
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)

        if result.returncode != 0:
            cmd_reencode = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-preset", "fast", "-crf", "28",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                output_path
            ]
            subprocess.run(cmd_reencode, capture_output=True, timeout=300)
    else:
        # For large inputs, re-encode with adaptive CRF based on scene count
        crf = min(35, 26 + num_scenes)  # More scenes = more compression
        resolution = "1280:720" if num_scenes <= 10 else "960:540"
        audio_bitrate = "128k" if num_scenes <= 10 else "96k"
        cmd_reencode = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
            "-vf", f"scale={resolution}",
            "-c:a", "aac", "-b:a", audio_bitrate,
            "-movflags", "+faststart",
            output_path
        ]
        subprocess.run(cmd_reencode, capture_output=True, timeout=600)

    # Check file size — if > 45MB, apply aggressive compression
    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    logger.info(f"Studio [{project_id}]: Concatenated video size: {file_size//1024//1024}MB ({file_size//1024}KB)")

    if file_size > 45 * 1024 * 1024:
        compressed_path = f"{tmpdir}/final_{project_id}_compressed.mp4"
        # Calculate target bitrate for ~40MB output
        try:
            probe = subprocess.run(
                ["ffmpeg", "-i", output_path, "-f", "null", "-"],
                capture_output=True, timeout=60
            )
            duration_match = None
            for line in probe.stderr.decode().split('\n'):
                if 'Duration:' in line:
                    parts = line.split('Duration:')[1].split(',')[0].strip().split(':')
                    duration_match = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    break
        except Exception:
            duration_match = num_scenes * 12  # estimate 12s per scene

        if duration_match and duration_match > 0:
            target_bitrate = int((40 * 8 * 1024) / duration_match)  # kbps for 40MB
            cmd_compress = [
                "ffmpeg", "-y", "-i", output_path,
                "-c:v", "libx264", "-preset", "medium",
                "-b:v", f"{target_bitrate}k", "-maxrate", f"{int(target_bitrate*1.5)}k",
                "-bufsize", f"{target_bitrate*2}k",
                "-vf", "scale=960:540",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                compressed_path
            ]
        else:
            cmd_compress = [
                "ffmpeg", "-y", "-i", output_path,
                "-c:v", "libx264", "-preset", "medium", "-crf", "35",
                "-vf", "scale=960:540",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                compressed_path
            ]
        result = subprocess.run(cmd_compress, capture_output=True, timeout=600)
        if result.returncode == 0 and os.path.exists(compressed_path):
            new_size = os.path.getsize(compressed_path)
            logger.info(f"Studio [{project_id}]: Compressed {file_size//1024//1024}MB -> {new_size//1024//1024}MB")
            output_path = compressed_path
            file_size = new_size

    # If still too large (> 90MB), skip upload and return None
    if file_size > 90 * 1024 * 1024:
        logger.warning(f"Studio [{project_id}]: Final video still too large ({file_size//1024//1024}MB), skipping concat upload")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    with open(output_path, 'rb') as f:
        video_bytes = f.read()

    filename = f"studio/{project_id}_final.mp4"
    try:
        url = _upload_to_storage(video_bytes, filename, "video/mp4")
    except Exception as e:
        logger.error(f"Studio [{project_id}]: Upload failed: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)

    return url


@router.post("/start-production")
async def start_production(req: StartProductionRequest, tenant=Depends(get_current_tenant)):
    """Start multi-scene production pipeline in background."""
    settings, projects, project = _get_project(tenant["id"], req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.get("scenes"):
        raise HTTPException(status_code=400, detail="No scenes defined. Use the Screenwriter first.")

    # Persist character avatars and visual style to project
    if req.character_avatars:
        project["character_avatars"] = req.character_avatars
    if req.visual_style:
        project["visual_style"] = req.visual_style

    project["status"] = "starting"
    project["error"] = None
    total = len(project.get("scenes", []))
    project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "starting"}
    _add_milestone(project, "production_started", f"Produção iniciada — {total} cenas")
    if req.character_avatars:
        _add_milestone(project, "avatars_linked", f"Avatares vinculados — {len(req.character_avatars)} personagens")
    _save_project(tenant["id"], settings, projects)

    # Use saved character_avatars (merge request + saved)
    char_avatars = {**project.get("character_avatars", {}), **req.character_avatars}

    thread = threading.Thread(
        target=_run_multi_scene_production,
        args=(tenant["id"], req.project_id, char_avatars),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "project_id": req.project_id, "total_scenes": total}


# ── Per-Scene Regeneration ──

def _regenerate_single_scene(tenant_id: str, project_id: str, scene_num: int, custom_prompt: str = None):
    """Regenerate a single scene video using the same pipeline logic."""
    import time as _time
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        characters = project.get("characters", [])
        char_avatars = project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")
        total = len(scenes)

        scene = next((s for s in scenes if s.get("scene_number") == scene_num), None)
        if not scene:
            logger.error(f"Studio [{project_id}]: Scene {scene_num} not found for regeneration")
            return

        _update_scene_status(tenant_id, project_id, scene_num, "directing", total)

        # Load Production Design from project (if available from previous production)
        agents_output = project.get("agents_output", {})
        production_design = agents_output.get("production_design", {})
        pd_chars = production_design.get("character_bible", {})
        pd_locations = production_design.get("location_bible", {})
        pd_style = production_design.get("style_anchors", "")
        pd_color = production_design.get("color_palette", {})
        pd_scene_dirs = {d.get("scene", 0): d for d in production_design.get("scene_directions", [])}

        STYLE_PROMPTS = {
            "animation": "ART STYLE: High-quality 3D animation like Pixar/DreamWorks. Colorful, warm, expressive characters with large eyes. Smooth cinematic camera movements. Rich detailed environments.",
            "cartoon": "ART STYLE: Vibrant 2D cartoon style. Bold outlines, saturated colors, exaggerated expressions.",
            "anime": "ART STYLE: Japanese anime style. Detailed backgrounds, expressive eyes, dramatic lighting.",
            "realistic": "ART STYLE: Cinematic photorealistic live-action. Film grain, natural lighting.",
            "watercolor": "ART STYLE: Watercolor painting style. Soft edges, pastel tones, dreamy atmosphere.",
        }
        style_hint = pd_style or STYLE_PROMPTS.get(visual_style, STYLE_PROMPTS["animation"])

        briefing = project.get("briefing", "")

        # Use custom prompt or generate via Claude with Production Design
        if custom_prompt:
            sora_prompt = custom_prompt
        else:
            chars_in_scene = scene.get("characters_in_scene", [])

            # Use canonical descriptions from Production Design if available
            if pd_chars:
                char_descs = "\n".join([
                    f"- {name}: {pd_chars.get(name, next((ch.get('description','') for ch in characters if ch.get('name')==name), ''))}"
                    for name in chars_in_scene
                ])
                scene_dir = pd_scene_dirs.get(scene_num, {})
                loc_key = scene_dir.get("location_key", "")
                loc_desc = pd_locations.get(loc_key, "")
                time_day = scene_dir.get("time_of_day", "afternoon")
                time_light = pd_color.get(time_day, pd_color.get("global", ""))

                director_system = f"""You are a SCENE DIRECTOR for Sora 2 video generation.
MANDATORY STYLE (include VERBATIM): {style_hint}
Return ONLY JSON: {{"sora_prompt": "ONE detailed English paragraph for Sora 2, max 250 words"}}
RULES: Describe characters by EXACT PHYSICAL APPEARANCE, NEVER by name. Include environment, lighting, atmosphere, actions, camera."""

                director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}
CHARACTERS (by appearance): {char_descs}
LOCATION: {loc_desc}
TIME: {time_day} — {time_light}
CAMERA: {scene_dir.get('camera_flow', scene.get('camera', ''))}"""
            else:
                # Fallback: no production design available
                scene_chars = "; ".join([f"{ch['name']}: {ch.get('description','')}" for ch in characters if ch.get("name") in chars_in_scene])
                director_system = f"""You are a SCENE DIRECTOR for Sora 2. {style_hint}
Return ONLY JSON: {{"sora_prompt": "Detailed English paragraph for Sora 2. Max 250 words."}}"""
                director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')} | Camera: {scene.get('camera','')}
Characters: {scene_chars}
Story: {briefing[:300]}"""

            try:
                result_text = _call_claude_sync(director_system, director_prompt, max_tokens=1000)
                data = _parse_json(result_text) or {}
                sora_prompt = data.get("sora_prompt", scene.get("description", ""))
            except Exception as e:
                logger.warning(f"Studio [{project_id}]: Scene {scene_num} regen director error: {e}")
                sora_prompt = f"{style_hint} {scene.get('description', '')}"

        # Build composite avatar for all characters in scene
        chars_in_scene = scene.get("characters_in_scene", [])
        avatar_cache = {}
        for ch_name in chars_in_scene:
            url = char_avatars.get(ch_name)
            if url and url not in avatar_cache:
                try:
                    full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                except Exception:
                    avatar_cache[url] = None

        ref_path = _create_composite_avatar(chars_in_scene, char_avatars, avatar_cache)

        # Generate video with Sora 2 (3 retries)
        _update_scene_status(tenant_id, project_id, scene_num, "generating_video", total)

        video_gen = DirectSora2Client(api_key=OPENAI_API_KEY)

        for attempt in range(3):
            try:
                gen_kwargs = {"prompt": sora_prompt[:1000], "model": "sora-2", "size": "1280x720", "duration": 12, "max_wait_time": 600}
                if ref_path:
                    gen_kwargs["image_path"] = ref_path

                logger.info(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1}/3")
                video_bytes = video_gen.text_to_video(**gen_kwargs)
                if video_bytes and len(video_bytes) > 1000:
                    filename = f"studio/{project_id}_scene_{scene_num}.mp4"
                    video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                    logger.info(f"Studio [{project_id}]: Regen scene {scene_num} DONE ({len(video_bytes)//1024}KB)")

                    # Update project outputs
                    settings, projects, project = _get_project(tenant_id, project_id)
                    if project:
                        outputs = project.get("outputs", [])
                        # Remove old output for this scene
                        outputs = [o for o in outputs if o.get("scene_number") != scene_num]
                        outputs.append({
                            "id": uuid.uuid4().hex[:8], "type": "video", "url": video_url,
                            "scene_number": scene_num, "duration": 12,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })
                        project["outputs"] = outputs
                        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                        _add_milestone(project, f"regen_scene_{scene_num}", f"Cena {scene_num} regenerada")
                        _save_project(tenant_id, settings, projects)

                    # Cleanup temp files
                    for p in avatar_cache.values():
                        if p:
                            try:
                                os.unlink(p)
                            except OSError:
                                pass
                    if ref_path and ref_path not in avatar_cache.values():
                        try:
                            os.unlink(ref_path)
                        except OSError:
                            pass
                    return

                else:
                    logger.warning(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1} empty video")
                    if attempt < 2:
                        _time.sleep(10)
                        continue

            except Exception as ve:
                err_str = str(ve).lower()
                is_retryable = any(k in err_str for k in ["disconnect", "server", "timeout", "connection"])
                if is_retryable and attempt < 2:
                    logger.warning(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1} error: {ve}. Retrying...")
                    _time.sleep(15 * (attempt + 1))
                    continue
                logger.error(f"Studio [{project_id}]: Regen scene {scene_num} FAILED: {ve}")
                break

        # All retries failed
        _update_scene_status(tenant_id, project_id, scene_num, "error", total)
        for p in avatar_cache.values():
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass
        if ref_path and ref_path not in avatar_cache.values():
            try:
                os.unlink(ref_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Regen scene {scene_num} error: {e}")
        _update_scene_status(tenant_id, project_id, scene_num, "error", len(project.get("scenes", [])) if project else 0)


@router.post("/projects/{project_id}/regenerate-scene")
async def regenerate_scene(project_id: str, req: RegenerateSceneRequest, tenant=Depends(get_current_tenant)):
    """Regenerate a single scene video."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scene = next((s for s in project.get("scenes", []) if s.get("scene_number") == req.scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {req.scene_number} not found")

    thread = threading.Thread(
        target=_regenerate_single_scene,
        args=(tenant["id"], project_id, req.scene_number, req.custom_prompt),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "scene_number": req.scene_number}


@router.post("/projects/{project_id}/save-character-avatars")
async def save_character_avatars(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Persist character avatar links to the project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["character_avatars"] = payload.get("character_avatars", {})
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.post("/projects/{project_id}/update-visual-style")
async def update_visual_style(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update visual style for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["visual_style"] = payload.get("visual_style", "animation")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.post("/projects/{project_id}/update-language")
async def update_language(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update language for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["language"] = payload.get("language", "pt")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.post("/projects/{project_id}/update-scene")
async def update_scene(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update a single scene's description, dialogue, etc."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    scene_num = payload.get("scene_number")
    scenes = project.get("scenes", [])
    for s in scenes:
        if s.get("scene_number") == scene_num:
            for key in ["title", "description", "dialogue", "emotion", "camera", "transition"]:
                if key in payload:
                    s[key] = payload[key]
            break
    project["scenes"] = scenes
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


# ── Production Preview (Pre-Production Only) ──

def _generate_preview_task(tenant_id, project_id):
    """Background task: runs ONLY avatar analysis + production design."""
    import time as _time
    import tempfile
    t0 = _time.time()
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        characters = project.get("characters", [])
        scenes = project.get("scenes", [])
        char_avatars = project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")
        briefing = project.get("briefing", "")

        # Download avatars
        avatar_cache = {}
        for name, url in char_avatars.items():
            if url and url not in avatar_cache:
                try:
                    full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                except Exception:
                    avatar_cache[url] = None

        # Step 1: Avatar analysis with Claude Vision
        avatar_descriptions = _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id)

        # Step 2: Production Design Document
        production_design = _build_production_design(
            briefing, characters, scenes, avatar_descriptions, visual_style,
            project.get("language", "pt"), project_id
        )

        # Cleanup
        for p in avatar_cache.values():
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass

        # Save
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["agents_output"] = {
                **project.get("agents_output", {}),
                "production_design": production_design,
                "avatar_descriptions": avatar_descriptions,
            }
            project["preview_status"] = "complete"
            project["preview_time"] = round(_time.time() - t0, 1)
            _save_project(tenant_id, settings, projects)
            logger.info(f"Studio [{project_id}]: Preview generated in {project['preview_time']}s")

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Preview generation failed: {e}")
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["preview_status"] = "error"
            project["preview_error"] = str(e)
            _save_project(tenant_id, settings, projects)


@router.post("/projects/{project_id}/generate-preview")
async def generate_production_preview(project_id: str, tenant=Depends(get_current_tenant)):
    """Start pre-production preview: avatar analysis + production design document."""
    tenant_id = tenant["id"]
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not project.get("scenes"):
        raise HTTPException(400, "No scenes available")

    project["preview_status"] = "generating"
    _save_project(tenant_id, settings, projects)

    thread = threading.Thread(target=_generate_preview_task, args=(tenant_id, project_id), daemon=True)
    thread.start()

    return {"status": "generating", "message": "Pre-production preview started"}


@router.get("/projects/{project_id}/preview")
async def get_production_preview(project_id: str, tenant=Depends(get_current_tenant)):
    """Get pre-production preview data (production design document)."""
    tenant_id = tenant["id"]
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    agents_output = project.get("agents_output", {})
    return {
        "preview_status": project.get("preview_status", "none"),
        "preview_time": project.get("preview_time"),
        "production_design": agents_output.get("production_design"),
        "avatar_descriptions": agents_output.get("avatar_descriptions"),
    }


# ── Image Generation (for scene thumbnails or fallback) ──

@router.post("/generate-image")
async def generate_directed_image(req: StartProductionRequest, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    briefing = project.get("briefing", "")
    avatar_urls = project.get("avatar_urls", [])

    prompt_text = f"Create a professional cinematic image. Briefing: {briefing}. Characters: {len(avatar_urls)}. 16:9 aspect ratio."

    content = [{"type": "text", "text": prompt_text}]
    for url in avatar_urls[:4]:
        try:
            req_obj = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            img_data = urllib.request.urlopen(req_obj, timeout=15).read()
            b64 = base64.b64encode(img_data).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        except Exception:
            pass

    response = litellm.completion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": content}],
        api_key=GEMINI_API_KEY,
    )
    images = []
    if response.choices and response.choices[0].message:
        msg = response.choices[0].message
        if hasattr(msg, 'images') and msg.images:
            for img_d in msg.images:
                if 'image_url' in img_d and 'url' in img_d['image_url']:
                    data_url = img_d['image_url']['url']
                    if ';base64,' in data_url:
                        images.append(data_url.split(';base64,', 1)[1])
    if not images:
        raise HTTPException(status_code=500, detail="No image generated")
    img_bytes = base64.b64decode(images[0])
    filename = f"studio/scene_{uuid.uuid4().hex[:8]}.png"
    public_url = _upload_to_storage(img_bytes, filename)
    return {"image_url": public_url}


# ── Voice & Music Library ──

@router.get("/voices")
async def get_voices(user=Depends(get_current_user)):
    return {"voices": ELEVENLABS_VOICES}

@router.get("/music-library")
async def get_music_library(user=Depends(get_current_user)):
    tracks = [{"id": k, **v} for k, v in MUSIC_LIBRARY.items()]
    return {"tracks": tracks}



# ── Narration Generation (ElevenLabs) ──

def _generate_narration_audio(text: str, voice_id: str, stability: float, similarity: float, style_val: float, language_code: str = "") -> bytes:
    """Generate narration audio using ElevenLabs TTS. Returns mp3 bytes."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise RuntimeError("ELEVENLABS_API_KEY not configured")

    from elevenlabs import ElevenLabs as ELClient, VoiceSettings

    client = ELClient(api_key=elevenlabs_key)
    voice_settings = VoiceSettings(
        stability=stability,
        similarity_boost=similarity,
        style=style_val,
        use_speaker_boost=True,
    )

    # Map language codes to ElevenLabs language hints (ISO 639-1 for multilingual_v2)
    LANG_HINTS = {
        "pt": "pt", "en": "en", "es": "es",
        "fr": "fr", "de": "de", "it": "it",
    }
    lang_hint = LANG_HINTS.get(language_code, "")

    kwargs = {
        "text": text,
        "voice_id": voice_id,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings,
    }
    if lang_hint:
        kwargs["language_code"] = lang_hint

    audio_gen = client.text_to_speech.convert(**kwargs)
    audio_bytes = b""
    for chunk in audio_gen:
        audio_bytes += chunk
    return audio_bytes


def _run_narration_background(tenant_id: str, project_id: str, voice_id: str, stability: float, similarity: float, style_val: float):
    """Background: generate narration for each scene and save to project.
    In 'dubbed' mode: parses character lines, uses different voices per character, and concatenates."""
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        lang = project.get("language", "pt")
        audio_mode = project.get("audio_mode", "narrated")

        _update_project_field(tenant_id, project_id, {
            "narration_status": {"phase": "generating_script", "done": 0, "total": len(scenes)},
        })

        # ── DUBBED MODE: Use scene dialogues directly (already have character lines) ──
        if audio_mode == "dubbed":
            # ElevenLabs voice mapping for character types
            DUBBED_VOICES = {
                "narrator": voice_id,  # User-selected voice for narrator
                "male_elder": "VR6AewLTigWG4xSOukaG",   # Arnold - deep male
                "male_young": "pNInz6obpgDQGcFmaJgB",    # Adam - young male
                "female_elder": "EXAVITQu4vr4xnSDxMaL",  # Bella - female
                "female_young": "jBpfuIE2acCO8z3wKNLl",   # Gigi - young female
                "child": "jsCqWAovK2LkecY7zXl4",          # Freya - light voice for kids
                "angel": "onwK4e9ZLuTAKqWW03F9",          # Daniel - ethereal male
            }

            # Map character names to voice types
            characters = project.get("characters", [])
            char_voice_map = {}
            for c in characters:
                name = c.get("name", "").lower()
                if "narrador" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["narrator"]
                elif "anjo" in name or "angel" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["angel"]
                elif "sara" in name or "rebeca" in name or "agar" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["female_elder"]
                elif "isaque" in name or "isaac" in name:
                    # Check if adolescent or child
                    if "adolescente" in name or "jovem" in name:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_young"]
                    elif "bebê" in name or "bebe" in name or "criança" in name:
                        char_voice_map[c["name"]] = DUBBED_VOICES["child"]
                    else:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_young"]
                elif "abraão" in name or "abraao" in name or "abraham" in name:
                    if "jovem" in name:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_young"]
                    else:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_elder"]
                elif "deus" in name or "god" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["angel"]
                else:
                    char_voice_map[c["name"]] = DUBBED_VOICES["male_elder"]

            # Default mappings for common Portuguese names
            char_voice_map["Narrador"] = DUBBED_VOICES["narrator"]
            char_voice_map["Deus"] = DUBBED_VOICES["angel"]

            logger.info(f"Studio [{project_id}]: DUBBED mode — {len(char_voice_map)} character voices mapped")

            narration_outputs = []
            for i, scene in enumerate(scenes):
                scene_num = scene.get("scene_number", i + 1)
                dialogue = scene.get("dialogue", "")
                if not dialogue.strip():
                    narration_outputs.append({"scene_number": scene_num, "narration": "", "audio_url": None})
                    continue

                try:
                    # Parse character lines: "Narrador: '...' / Abraão: '...' / Isaac: '...'"
                    parts = [p.strip() for p in dialogue.split(" / ")]
                    audio_clips = []

                    with tempfile.TemporaryDirectory() as tmpdir:
                        for pi, part in enumerate(parts):
                            # Extract character name and text
                            if ":" in part:
                                char_name_raw = part.split(":")[0].strip()
                                text = ":".join(part.split(":")[1:]).strip().strip("'\"")
                            else:
                                char_name_raw = "Narrador"
                                text = part.strip().strip("'\"")

                            if not text:
                                continue

                            # Find matching voice
                            matched_voice = DUBBED_VOICES["narrator"]
                            for cname, vid in char_voice_map.items():
                                if char_name_raw.lower() in cname.lower() or cname.lower() in char_name_raw.lower():
                                    matched_voice = vid
                                    break

                            # Generate audio for this character line
                            audio_bytes = _generate_narration_audio(text, matched_voice, stability, similarity, style_val, lang)
                            clip_path = f"{tmpdir}/part_{pi:03d}.mp3"
                            with open(clip_path, 'wb') as f:
                                f.write(audio_bytes)
                            audio_clips.append(clip_path)

                        if len(audio_clips) == 1:
                            with open(audio_clips[0], 'rb') as f:
                                final_audio = f.read()
                        elif len(audio_clips) > 1:
                            # Concatenate all character audio clips with 0.3s pause
                            list_file = f"{tmpdir}/concat_list.txt"
                            silence_path = f"{tmpdir}/silence.mp3"
                            # Generate 0.3s silence
                            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.3", silence_path],
                                           capture_output=True, timeout=10)
                            with open(list_file, 'w') as f:
                                for ci, cp in enumerate(audio_clips):
                                    f.write(f"file '{cp}'\n")
                                    if ci < len(audio_clips) - 1 and os.path.exists(silence_path):
                                        f.write(f"file '{silence_path}'\n")
                            merged_path = f"{tmpdir}/merged.mp3"
                            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c:a", "libmp3lame", "-q:a", "4", merged_path],
                                           capture_output=True, timeout=30)
                            with open(merged_path, 'rb') as f:
                                final_audio = f.read()
                        else:
                            narration_outputs.append({"scene_number": scene_num, "narration": dialogue, "audio_url": None})
                            continue

                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(final_audio, filename, "audio/mpeg")
                    narration_outputs.append({"scene_number": scene_num, "narration": dialogue, "audio_url": audio_url})
                    logger.info(f"Studio [{project_id}]: Dubbed scene {scene_num} done ({len(final_audio)//1024}KB, {len(parts)} voices)")

                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Dubbed scene {scene_num} failed: {e}")
                    narration_outputs.append({"scene_number": scene_num, "narration": dialogue, "audio_url": None, "error": str(e)[:100]})

                _update_project_field(tenant_id, project_id, {
                    "narration_status": {"phase": "generating_audio", "done": i + 1, "total": len(scenes)},
                })

        else:
            # ── NARRATED MODE: Single narrator voice ──
            narration_system = f"""You are a NARRATOR for cinematic storytelling. Given scenes, write compelling narration text for EACH scene.
Rules:
- Each scene narration is MAX 25 words (fits 12 seconds)
- Be dramatic, evocative, emotional
- Use the scene dialogue and description as basis
- **MANDATORY**: Write ALL narration text in {LANG_FULL_NAMES.get(lang, lang)}. NEVER write in English unless the language IS English.
- Output ONLY valid JSON array: [{{"scene_number": 1, "narration": "text..."}}]"""

            scene_summaries = "\n".join([
                f"Scene {s.get('scene_number', i+1)}: {s.get('title','')} — {s.get('description','')} — Dialogue: {s.get('dialogue','')}"
                for i, s in enumerate(scenes)
            ])

            script_result = _call_claude_sync(narration_system, f"Scenes:\n{scene_summaries}")

            import json as json_mod
            narrations = []
            if '[' in script_result:
                try:
                    start = script_result.index('[')
                    end = script_result.rindex(']') + 1
                    narrations = json_mod.loads(script_result[start:end])
                except Exception:
                    pass

            if not narrations:
                narrations = [{"scene_number": i+1, "narration": s.get("dialogue", s.get("description", ""))[:80]} for i, s in enumerate(scenes)]

            _update_project_field(tenant_id, project_id, {
                "narration_status": {"phase": "generating_audio", "done": 0, "total": len(narrations)},
            })

            narration_outputs = []
            for i, narr in enumerate(narrations):
                scene_num = narr.get("scene_number", i + 1)
                text = narr.get("narration", "")
                if not text.strip():
                    narration_outputs.append({"scene_number": scene_num, "text": "", "audio_url": None})
                    continue
                try:
                    audio_bytes = _generate_narration_audio(text, voice_id, stability, similarity, style_val, lang)
                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                    narration_outputs.append({"scene_number": scene_num, "text": text, "audio_url": audio_url})
                    logger.info(f"Studio [{project_id}]: Narration scene {scene_num} done ({len(audio_bytes)//1024}KB)")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Narration scene {scene_num} failed: {e}")
                    narration_outputs.append({"scene_number": scene_num, "text": text, "audio_url": None, "error": str(e)[:100]})

                _update_project_field(tenant_id, project_id, {
                    "narration_status": {"phase": "generating_audio", "done": i + 1, "total": len(narrations)},
                })

        # Save all narrations to project
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["narrations"] = narration_outputs
            project["narration_status"] = {"phase": "complete", "done": len(narration_outputs), "total": len(narration_outputs)}
            project["voice_config"] = {"voice_id": voice_id, "stability": stability, "similarity": similarity, "style_val": style_val}
            _add_milestone(project, "narration_generated", f"Narração gerada — {len([n for n in narration_outputs if n.get('audio_url')])} cenas")
            _save_project(tenant_id, settings, projects)

        logger.info(f"Studio [{project_id}]: All narrations done")

    except Exception as e:
        logger.error(f"Studio [{project_id}] narration error: {e}")
        _update_project_field(tenant_id, project_id, {
            "narration_status": {"phase": "error", "error": str(e)[:300]},
        })


@router.post("/projects/{project_id}/generate-narration")
async def generate_narration(project_id: str, req: GenerateNarrationRequest, tenant=Depends(get_current_tenant)):
    """Generate ElevenLabs narration for all scenes in a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.get("scenes"):
        raise HTTPException(status_code=400, detail="No scenes. Use the Screenwriter first.")

    thread = threading.Thread(
        target=_run_narration_background,
        args=(tenant["id"], project_id, req.voice_id, req.stability, req.similarity, req.style_val),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "total_scenes": len(project["scenes"])}


@router.get("/projects/{project_id}/narrations")
async def get_narrations(project_id: str, tenant=Depends(get_current_tenant)):
    """Get narration status and outputs for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "narrations": project.get("narrations", []),
        "narration_status": project.get("narration_status", {}),
        "voice_config": project.get("voice_config", {}),
    }



# ── Performance Analytics ──

@router.get("/analytics/performance")
async def get_performance_analytics(tenant=Depends(get_current_tenant)):
    """Analyze performance data from all productions — timing, costs, efficiency."""
    from datetime import datetime as dt

    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])

    # Collect data
    completed = [p for p in projects if p.get("status") == "complete" and p.get("milestones")]
    errored = [p for p in projects if p.get("status") == "error"]
    all_projects = projects

    # Parse milestones for timing
    productions = []
    for proj in completed:
        ms = proj.get("milestones", [])
        ms_dict = {m["key"]: m["at"] for m in ms if "at" in m}
        scenes_count = len(proj.get("scenes", []))
        videos_count = len([o for o in proj.get("outputs", []) if o.get("url") and o.get("type") == "video" and o.get("scene_number", 0) > 0])

        # Calculate durations from milestones
        created_at = ms_dict.get("project_created", "")
        agents_at = ms_dict.get("agents_complete", "")
        videos_at = ms_dict.get("videos_generated", "")
        film_at = ms_dict.get("film_complete", "")

        def _parse_ts(ts_str):
            if not ts_str:
                return None
            try:
                return dt.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                return None

        t_created = _parse_ts(created_at)
        t_agents = _parse_ts(agents_at)
        t_videos = _parse_ts(videos_at)
        t_film = _parse_ts(film_at)

        agent_duration = (t_agents - t_created).total_seconds() if t_created and t_agents else None
        video_duration = (t_videos - t_agents).total_seconds() if t_agents and t_videos else None
        total_duration = (t_film - t_created).total_seconds() if t_created and t_film else None

        # Extract timing from milestone labels (e.g., "Produção paralela — 523s")
        for m in ms:
            label = m.get("label", "")
            if "s" in label and any(c.isdigit() for c in label):
                import re
                nums = re.findall(r'(\d+)s', label)
                if nums:
                    if "agente" in label.lower() or "paralela" in label.lower():
                        agent_duration = float(nums[0])
                    elif "vídeo" in label.lower():
                        video_duration = float(nums[0])

        # Per-scene video timing from milestones
        scene_times = []
        for m in ms:
            if m["key"].startswith("video_scene_"):
                scene_times.append(m["at"])

        productions.append({
            "project_id": proj["id"],
            "name": proj.get("name", "Sem nome"),
            "scenes": scenes_count,
            "videos": videos_count,
            "agent_seconds": round(agent_duration) if agent_duration else None,
            "video_seconds": round(video_duration) if video_duration else None,
            "total_seconds": round(total_duration) if total_duration else None,
            "milestones": len(ms),
            "pipeline_version": "v3" if any("paralela" in m.get("label", "") for m in ms) else "v2" if any("Agentes de cinema" in m.get("label", "") for m in ms) else "v1",
        })

    # Compute aggregated stats
    agent_times = [p["agent_seconds"] for p in productions if p["agent_seconds"]]
    video_times = [p["video_seconds"] for p in productions if p["video_seconds"]]
    total_times = [p["total_seconds"] for p in productions if p["total_seconds"]]
    all_scenes = [p["scenes"] for p in productions if p["scenes"] > 0]

    def avg(lst):
        return round(sum(lst) / len(lst)) if lst else 0

    # Estimated Claude tokens used (rough: ~1500 tokens per scene director call)
    total_scenes_produced = sum(p["scenes"] for p in productions)
    est_claude_tokens = total_scenes_produced * 1500
    # v1: 3 calls per scene, v2: 3 batch calls, v3: 1 call per scene
    v1_count = len([p for p in productions if p["pipeline_version"] == "v1"])
    v2_count = len([p for p in productions if p["pipeline_version"] == "v2"])
    v3_count = len([p for p in productions if p["pipeline_version"] == "v3"])

    return {
        "summary": {
            "total_projects": len(all_projects),
            "completed": len(completed),
            "errored": len(errored),
            "total_scenes_produced": total_scenes_produced,
            "total_videos_generated": sum(p["videos"] for p in productions),
        },
        "timing": {
            "avg_agent_seconds": avg(agent_times),
            "avg_video_seconds": avg(video_times),
            "avg_total_seconds": avg(total_times),
            "min_total_seconds": min(total_times) if total_times else 0,
            "max_total_seconds": max(total_times) if total_times else 0,
            "avg_scenes_per_project": avg(all_scenes),
        },
        "pipeline_versions": {
            "v1_sequential": v1_count,
            "v2_batched": v2_count,
            "v3_parallel_teams": v3_count,
        },
        "cost_estimate": {
            "claude_calls_total": total_scenes_produced + len(completed),
            "claude_tokens_est": est_claude_tokens,
            "sora2_videos": sum(p["videos"] for p in productions),
            "optimization_note": f"v3 saves ~{(total_scenes_produced * 2) if total_scenes_produced > 0 else 0} Claude calls vs v1 ({total_scenes_produced}×3 → {total_scenes_produced}×1)",
        },
        "productions": sorted(productions, key=lambda x: x.get("total_seconds") or 999999),
        "recommendations": _generate_recommendations(productions, completed, errored),
    }


def _generate_recommendations(productions, completed, errored):
    """AI-like performance recommendations based on data."""
    recs = []
    if errored:
        error_rate = len(errored) / (len(completed) + len(errored)) * 100 if (len(completed) + len(errored)) > 0 else 0
        recs.append(f"Taxa de erro: {error_rate:.0f}%. Considere usar Pipeline v5 para maior estabilidade.")
    if len(completed) > 3:
        recs.append("Bom volume de produções concluídas. Pipeline estável.")
    return recs


# ═══════════════════════════════════════════════════════════
# ── PHASE A: Post-Production (Audio Engineer) ──
# ═══════════════════════════════════════════════════════════

MUSIC_DIR = "/app/backend/assets/music"

# Map music_plan categories to library tracks
MOOD_TO_TRACK = {
    "gentle": ["emotional", "classical_piano", "ambient_dreamy"],
    "cinematic": ["cinematic", "emotional"],
    "epic": ["cinematic", "gospel_uplifting"],
    "tense": ["cinematic", "ambient_nature"],
    "triumphant": ["gospel_uplifting", "cinematic", "emotional"],
    "contemplative": ["classical_piano", "ambient_dreamy", "jazz_lofi"],
    "joyful": ["gospel_uplifting", "upbeat", "pop_acoustic"],
    "dramatic": ["cinematic", "emotional"],
    "peaceful": ["ambient_dreamy", "classical_piano"],
    "mysterious": ["ambient_nature", "electronic_chill"],
}


def _select_music_for_project(music_plan: list) -> str:
    """Select best background music track based on the Production Design music plan."""
    if not music_plan:
        return "emotional"
    mood_scores = {}
    for entry in music_plan:
        mood = entry.get("mood", "").lower()
        category = entry.get("category", "").lower()
        scenes = entry.get("scenes", [])
        weight = len(scenes) if scenes else 1
        for key, tracks in MOOD_TO_TRACK.items():
            if key in mood or key in category:
                for t in tracks:
                    mood_scores[t] = mood_scores.get(t, 0) + weight
                break
    if mood_scores:
        return max(mood_scores, key=mood_scores.get)
    return "emotional"


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 12.0


def _run_post_production(tenant_id: str, project_id: str, req: PostProduceRequest):
    """Background: Full post-production — narration + music + transitions → final video."""
    import tempfile
    import time as _time

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        outputs = project.get("outputs", [])
        lang = project.get("language", "pt")

        if not scenes:
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "error", "error": "Sem cenas no projeto"}
            })
            return

        scene_videos = sorted(
            [o for o in outputs if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")],
            key=lambda x: x.get("scene_number", 0)
        )
        if not scene_videos:
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "error", "error": "Sem vídeos. Rode a produção primeiro."}
            })
            return

        logger.info(f"Studio [{project_id}]: Post-production starting — {len(scene_videos)} videos")

        if not _ensure_ffmpeg():
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "error", "error": "FFmpeg não disponível"}
            })
            return

        tmpdir = tempfile.mkdtemp()

        # ── Step 1: Generate narrations if needed ──
        narrations = project.get("narrations", [])
        narrations_with_audio = [n for n in narrations if n.get("audio_url")]

        if len(narrations_with_audio) < len(scene_videos):
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "narration", "done": 0, "total": len(scenes), "message": "Gerando narrações..."}
            })

            narration_system = f"""You are a NARRATOR for cinematic storytelling. Write compelling narration for EACH scene.
Rules:
- Each narration MAX 25 words (12 seconds)
- Dramatic, evocative, emotional
- **MANDATORY**: Write ALL narration text in {LANG_FULL_NAMES.get(lang, lang)}. NEVER write in English unless the language IS English.
- Output ONLY valid JSON array: [{{"scene_number": 1, "narration": "text..."}}]"""

            scene_summaries = "\n".join([
                f"Scene {s.get('scene_number', i+1)}: {s.get('title','')} — {s.get('description','')} — Dialogue: {s.get('dialogue','')}"
                for i, s in enumerate(scenes)
            ])

            try:
                script_result = _call_claude_sync(narration_system, f"Scenes:\n{scene_summaries}")
                import json as json_mod
                narrations = []
                if '[' in script_result:
                    start = script_result.index('[')
                    end = script_result.rindex(']') + 1
                    narrations = json_mod.loads(script_result[start:end])
            except Exception as e:
                logger.warning(f"Studio [{project_id}]: Narration script failed: {e}")
                narrations = [{"scene_number": i+1, "narration": s.get("dialogue", s.get("description", ""))[:80]}
                              for i, s in enumerate(scenes)]

            for i, narr in enumerate(narrations):
                scene_num = narr.get("scene_number", i + 1)
                text = narr.get("narration", "")
                _update_project_field(tenant_id, project_id, {
                    "post_production_status": {"phase": "narration", "done": i, "total": len(narrations), "message": f"Narração cena {scene_num}..."}
                })
                if not text.strip():
                    narr["audio_url"] = None
                    continue
                try:
                    audio_bytes = _generate_narration_audio(text, req.voice_id, req.stability, req.similarity, req.style_val, lang)
                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                    narr["audio_url"] = audio_url
                    logger.info(f"Studio [{project_id}]: Narration {scene_num} done ({len(audio_bytes)//1024}KB)")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Narration {scene_num} failed: {e}")
                    narr["audio_url"] = None

            _update_project_field(tenant_id, project_id, {
                "narrations": narrations,
                "narration_status": {"phase": "complete", "done": len(narrations), "total": len(narrations)},
                "voice_config": {"voice_id": req.voice_id, "stability": req.stability, "similarity": req.similarity, "style_val": req.style_val},
            })
        else:
            logger.info(f"Studio [{project_id}]: Using existing narrations ({len(narrations_with_audio)})")

        # ── Step 2: Download scene videos (with retry) ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "downloading", "done": 0, "total": len(scene_videos), "message": "Baixando vídeos..."}
        })

        video_files = []
        for i, sv in enumerate(scene_videos):
            local_path = f"{tmpdir}/scene_{i:03d}.mp4"
            for dl_attempt in range(4):
                try:
                    urllib.request.urlretrieve(sv["url"], local_path)
                    break
                except Exception as dl_err:
                    logger.warning(f"Studio [{project_id}]: Download retry {dl_attempt+1}/4 for scene {sv.get('scene_number', i+1)}: {dl_err}")
                    _time.sleep(2 * (dl_attempt + 1))
            video_files.append({"path": local_path, "scene_number": sv.get("scene_number", i+1)})
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "downloading", "done": i+1, "total": len(scene_videos), "message": f"Vídeo {i+1}/{len(scene_videos)}"}
            })

        # ── Step 3: Download narration audio (with retry) ──
        narration_files = {}
        for narr in narrations:
            sn = narr.get("scene_number", 0)
            url = narr.get("audio_url")
            if url and sn > 0:
                local_path = f"{tmpdir}/narration_{sn:03d}.mp3"
                for dl_attempt in range(3):
                    try:
                        urllib.request.urlretrieve(url, local_path)
                        narration_files[sn] = local_path
                        break
                    except Exception:
                        _time.sleep(1 * (dl_attempt + 1))

        # ── Step 4: Apply fade transitions + color grading + concat ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 0, "total": 4, "message": "Aplicando transições e color grading..."}
        })

        is_continuity = project.get("continuity_mode", True)

        faded_files = []
        for i, vf in enumerate(video_files):
            duration = _get_video_duration(vf["path"])
            sn = vf["scene_number"]
            scene_data = next((s for s in scenes if s.get("scene_number") == sn), {})
            trans = scene_data.get("transition", req.transition_type)
            # Enhanced transition: 1.5s for continuity mode, original for normal
            td = 1.5 if is_continuity else req.transition_duration
            faded_path = f"{tmpdir}/faded_{i:03d}.mp4"

            if trans == "fade" and duration > td * 2:
                fade_out_start = max(0, duration - td)
                # Apply color grading in continuity mode for visual consistency
                vf_filter = f"fade=t=in:st=0:d={td},fade=t=out:st={fade_out_start:.2f}:d={td}"
                if is_continuity:
                    vf_filter += ",eq=contrast=1.05:brightness=0.02:saturation=1.1,colorbalance=rs=0.03:gs=0.01:bs=-0.02"
                cmd = [
                    "ffmpeg", "-y", "-i", vf["path"],
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an", faded_path
                ]
            else:
                if is_continuity:
                    # Even without fades, apply color grading for consistency
                    cmd = [
                        "ffmpeg", "-y", "-i", vf["path"],
                        "-vf", "eq=contrast=1.05:brightness=0.02:saturation=1.1,colorbalance=rs=0.03:gs=0.01:bs=-0.02",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an", faded_path
                    ]
                else:
                    cmd = ["ffmpeg", "-y", "-i", vf["path"], "-c:v", "copy", "-an", faded_path]

            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                shutil.copy2(vf["path"], faded_path)
            faded_files.append(faded_path)

        concat_file = f"{tmpdir}/concat.txt"
        with open(concat_file, 'w') as f:
            for fp in faded_files:
                f.write(f"file '{fp}'\n")

        silent_video = f"{tmpdir}/silent_final.mp4"
        result = subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-movflags", "+faststart", silent_video
        ], capture_output=True, timeout=300)
        if result.returncode != 0:
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", silent_video], capture_output=True, timeout=120)

        total_duration = _get_video_duration(silent_video)
        logger.info(f"Studio [{project_id}]: Video with transitions: {total_duration:.1f}s")

        # ── Step 5: Build narration audio track ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 1, "total": 4, "message": "Mixando narração..."}
        })

        narration_track = None
        if narration_files:
            scene_offsets = {}
            cumulative = 0.0
            for i, vf in enumerate(video_files):
                sn = vf["scene_number"]
                dur = _get_video_duration(faded_files[i])
                scene_offsets[sn] = cumulative
                cumulative += dur

            inputs = ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={total_duration:.2f}"]
            filter_parts = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo[base]"]
            input_idx = 1
            overlay_labels = ["base"]

            for sn in sorted(narration_files.keys()):
                offset = scene_offsets.get(sn, 0.0)
                inputs.extend(["-i", narration_files[sn]])
                label = f"n{input_idx}"
                filter_parts.append(f"[{input_idx}:a]adelay={int(offset*1000)}|{int(offset*1000)},aformat=sample_rates=44100:channel_layouts=stereo[{label}]")
                overlay_labels.append(label)
                input_idx += 1

            if len(overlay_labels) > 1:
                mix_inputs = "".join(f"[{lb}]" for lb in overlay_labels)
                filter_parts.append(f"{mix_inputs}amix=inputs={len(overlay_labels)}:duration=longest:normalize=0[narr_out]")
                narration_track = f"{tmpdir}/narration_track.mp3"
                result = subprocess.run(
                    ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filter_parts), "-map", "[narr_out]", "-c:a", "libmp3lame", "-b:a", "192k", narration_track],
                    capture_output=True, timeout=120
                )
                if result.returncode != 0:
                    logger.warning(f"Studio [{project_id}]: Narration mix failed: {result.stderr.decode()[:200]}")
                    narration_track = None

        # ── Step 6: Prepare background music (segmented by mood) ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 2, "total": 4, "message": "Criando trilha sonora segmentada..."}
        })

        music_plan = project.get("agents_output", {}).get("production_design", {}).get("music_plan", [])
        music_track = req.music_track  # user override

        # Build scene offsets and durations
        scene_offsets = {}
        scene_durations = {}
        cumulative = 0.0
        for i, vf in enumerate(video_files):
            sn = vf["scene_number"]
            dur = _get_video_duration(faded_files[i])
            scene_offsets[sn] = cumulative
            scene_durations[sn] = dur
            cumulative += dur

        # Build music segments based on music_plan
        music_prepared = f"{tmpdir}/music.mp3"
        if music_plan and not music_track:
            # Create segmented music: different tracks for different scene groups
            segment_files = []
            for seg_idx, entry in enumerate(music_plan):
                seg_scenes = entry.get("scenes", [])
                mood = entry.get("mood", "").lower()
                category = entry.get("category", "").lower()

                # Select track for this segment
                seg_track = None
                for key, tracks in MOOD_TO_TRACK.items():
                    if key in mood or key in category:
                        seg_track = tracks[0]
                        break
                if not seg_track:
                    seg_track = "emotional"

                seg_path = os.path.join(MUSIC_DIR, f"{seg_track}.mp3")
                if not os.path.exists(seg_path):
                    seg_path = os.path.join(MUSIC_DIR, "emotional.mp3")

                # Calculate segment duration
                seg_start = min(scene_offsets.get(s, 0) for s in seg_scenes) if seg_scenes else 0
                seg_end = max(scene_offsets.get(s, 0) + scene_durations.get(s, 12) for s in seg_scenes) if seg_scenes else 12
                seg_dur = seg_end - seg_start

                seg_file = f"{tmpdir}/music_seg_{seg_idx}.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-stream_loop", "-1", "-i", seg_path,
                    "-t", f"{seg_dur:.2f}",
                    "-af", f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(0, seg_dur-1.5):.2f}:d=1.5,volume={req.music_volume:.2f}",
                    "-c:a", "libmp3lame", "-b:a", "128k", seg_file
                ], capture_output=True, timeout=30)
                segment_files.append(seg_file)
                logger.info(f"Studio [{project_id}]: Music segment {seg_idx} ({seg_track}): {seg_dur:.1f}s for scenes {seg_scenes}")

            # Concatenate segments
            if segment_files:
                seg_concat = f"{tmpdir}/seg_concat.txt"
                with open(seg_concat, 'w') as f:
                    for sf in segment_files:
                        if os.path.exists(sf):
                            f.write(f"file '{sf}'\n")
                result = subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", seg_concat,
                    "-c:a", "libmp3lame", "-b:a", "128k", music_prepared
                ], capture_output=True, timeout=30)
                has_music = result.returncode == 0
            else:
                has_music = False
        else:
            # Single track (user override or no music plan)
            if not music_track:
                music_track = _select_music_for_project(music_plan)
            music_path = os.path.join(MUSIC_DIR, f"{music_track}.mp3")
            if not os.path.exists(music_path):
                music_path = os.path.join(MUSIC_DIR, "emotional.mp3")
            result = subprocess.run([
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", music_path,
                "-t", f"{total_duration:.2f}",
                "-af", f"afade=t=in:st=0:d=2,afade=t=out:st={max(0, total_duration-3):.2f}:d=3,volume={req.music_volume:.2f}",
                "-c:a", "libmp3lame", "-b:a", "128k", music_prepared
            ], capture_output=True, timeout=60)
            has_music = result.returncode == 0

        # ── Step 7: Final mix ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 3, "total": 4, "message": "Mix final: vídeo + narração + trilha..."}
        })

        final_output = f"{tmpdir}/final_with_audio.mp4"
        if narration_track and has_music:
            cmd = [
                "ffmpeg", "-y", "-i", silent_video, "-i", narration_track, "-i", music_prepared,
                "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest:weights=1 0.3:normalize=0[audio]",
                "-map", "0:v", "-map", "[audio]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", final_output
            ]
        elif narration_track:
            cmd = [
                "ffmpeg", "-y", "-i", silent_video, "-i", narration_track,
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", final_output
            ]
        elif has_music:
            cmd = [
                "ffmpeg", "-y", "-i", silent_video, "-i", music_prepared,
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", final_output
            ]
        else:
            shutil.copy2(silent_video, final_output)
            cmd = None

        if cmd:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Studio [{project_id}]: Final mix failed: {result.stderr.decode()[:300]}")
                shutil.copy2(silent_video, final_output)

        file_size = os.path.getsize(final_output) if os.path.exists(final_output) else 0
        logger.info(f"Studio [{project_id}]: Final video: {file_size//1024//1024}MB, {total_duration:.1f}s")

        # Compress if > 45MB
        if file_size > 45 * 1024 * 1024:
            compressed = f"{tmpdir}/final_compressed.mp4"
            target_br = int((40 * 8 * 1024) / max(total_duration, 1))
            subprocess.run([
                "ffmpeg", "-y", "-i", final_output,
                "-c:v", "libx264", "-preset", "medium", "-b:v", f"{target_br}k",
                "-vf", "scale=960:540", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", compressed
            ], capture_output=True, timeout=600)
            if os.path.exists(compressed):
                final_output = compressed
                file_size = os.path.getsize(compressed)

        # ── Upload ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "uploading", "message": "Enviando vídeo final..."}
        })

        with open(final_output, 'rb') as f:
            video_bytes = f.read()

        filename = f"studio/{project_id}_final_audio_{lang}.mp4"
        try:
            url = _upload_to_storage(video_bytes, filename, "video/mp4")
        except Exception as e:
            logger.error(f"Studio [{project_id}]: Upload failed: {e}")
            url = None

        # Save
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            new_output = {
                "type": "final_video", "url": url, "language": lang,
                "music_track": music_track, "duration": total_duration,
                "has_narration": bool(narration_track), "has_music": has_music,
                "file_size_mb": round(file_size / (1024*1024), 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            project["outputs"] = [o for o in project["outputs"] if not (o.get("type") == "final_video" and o.get("language") == lang)]
            project["outputs"].append(new_output)
            project["post_production_status"] = {
                "phase": "complete", "final_url": url, "language": lang,
                "music_track": music_track, "duration": total_duration,
                "has_narration": bool(narration_track), "has_music": has_music,
            }
            _add_milestone(project, "post_production_complete", f"Pós-produção {lang.upper()} — {total_duration:.0f}s")
            _save_project(tenant_id, settings, projects)

        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info(f"Studio [{project_id}]: Post-production complete! URL: {url}")

    except Exception as e:
        logger.error(f"Studio [{project_id}] post-production error: {e}")
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "error", "error": str(e)[:300]}
        })


@router.post("/projects/{project_id}/post-produce")
async def post_produce(project_id: str, req: PostProduceRequest, tenant=Depends(get_current_tenant)):
    """Trigger full post-production: narration + music + transitions."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scene_videos = [o for o in project.get("outputs", []) if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")]
    if not scene_videos:
        raise HTTPException(status_code=400, detail="Sem vídeos. Rode a produção primeiro.")

    _update_project_field(tenant["id"], project_id, {
        "post_production_status": {"phase": "starting", "message": "Iniciando pós-produção..."}
    })

    thread = threading.Thread(target=_run_post_production, args=(tenant["id"], project_id, req), daemon=True)
    thread.start()

    return {"status": "started", "total_scenes": len(project.get("scenes", [])), "scene_videos": len(scene_videos)}


@router.get("/projects/{project_id}/post-production-status")
async def get_post_production_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get post-production progress."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": project.get("post_production_status", {}),
        "narrations": project.get("narrations", []),
        "voice_config": project.get("voice_config", {}),
        "subtitles": project.get("subtitles", {}),
    }


# ═══════════════════════════════════════════════════════════
# ── PHASE B: Multi-Language Localization (Dubbing) ──
# ═══════════════════════════════════════════════════════════

LANG_NAMES = {"pt": "Português", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "it": "Italiano"}


def _run_localization(tenant_id: str, project_id: str, req: LocalizeRequest):
    """Background: Re-dub video into a new language."""
    import tempfile

    target = req.target_language

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        original_lang = project.get("language", "pt")
        narrations = project.get("narrations", [])

        if not narrations:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "Rode a pós-produção primeiro."}
            })
            return

        logger.info(f"Studio [{project_id}]: Localization {original_lang} → {target}")
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "translating", "message": f"Traduzindo para {LANG_NAMES.get(target, target)}..."}
        })

        # ── Translate narrations ──
        import json as json_mod
        original_texts = [{"scene_number": n.get("scene_number", 0), "narration": n.get("narration", n.get("text", ""))} for n in narrations]

        translate_system = f"""Translate narration texts from {LANG_NAMES.get(original_lang, original_lang)} to {LANG_NAMES.get(target, target)}.
Rules:
- Same dramatic tone
- MAX 25 words each
- Output ONLY JSON array: [{{"scene_number": 1, "narration": "translated..."}}]"""

        try:
            result = _call_claude_sync(translate_system, f"Translate:\n{json_mod.dumps(original_texts, ensure_ascii=False)}")
            translated = []
            if '[' in result:
                translated = json_mod.loads(result[result.index('['):result.rindex(']')+1])
        except Exception as e:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": f"Tradução falhou: {str(e)[:100]}"}
            })
            return

        if not translated:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "Tradução vazia"}
            })
            return

        # ── Generate audio in target language ──
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "generating_audio", "done": 0, "total": len(translated)}
        })

        voice_id = req.voice_id or project.get("voice_config", {}).get("voice_id", "21m00Tcm4TlvDq8ikWAM")
        translated_narrations = []

        for i, t in enumerate(translated):
            sn = t.get("scene_number", i + 1)
            text = t.get("narration", "")
            if i % 5 == 0:  # Update status every 5 scenes to reduce DB pressure
                _update_project_field(tenant_id, project_id, {
                    f"localization_{target}": {"phase": "generating_audio", "done": i, "total": len(translated), "message": f"Áudio cena {sn}..."}
                })
            if not text.strip():
                translated_narrations.append({"scene_number": sn, "narration": text, "audio_url": None})
                continue
            try:
                audio_bytes = _generate_narration_audio(text, voice_id, req.stability, req.similarity, req.style_val, target)
                filename = f"studio/{project_id}_narration_{sn}_{target}.mp3"
                audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                translated_narrations.append({"scene_number": sn, "narration": text, "audio_url": audio_url})
            except Exception as e:
                translated_narrations.append({"scene_number": sn, "narration": text, "audio_url": None, "error": str(e)[:100]})

        # ── Re-mix video with new audio ──
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "mixing", "message": f"Mixando vídeo {LANG_NAMES.get(target, target)}..."}
        })

        if not _ensure_ffmpeg():
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "FFmpeg indisponível"}
            })
            return

        tmpdir = tempfile.mkdtemp()

        # Find base video
        final_videos = [o for o in project.get("outputs", []) if o.get("type") == "final_video" and o.get("url")]
        if not final_videos:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "Rode a pós-produção primeiro."}
            })
            return

        base_video = f"{tmpdir}/base.mp4"
        urllib.request.urlretrieve(final_videos[0]["url"], base_video)
        total_duration = _get_video_duration(base_video)

        # Download translated audio
        narration_files = {}
        for narr in translated_narrations:
            sn = narr.get("scene_number", 0)
            url = narr.get("audio_url")
            if url and sn > 0:
                lp = f"{tmpdir}/narr_{sn}_{target}.mp3"
                try:
                    urllib.request.urlretrieve(url, lp)
                    narration_files[sn] = lp
                except Exception:
                    pass

        # Calculate scene offsets
        sv_sorted = sorted(
            [o for o in project.get("outputs", []) if o.get("type") == "video" and o.get("scene_number", 0) > 0],
            key=lambda x: x.get("scene_number", 0)
        )
        scene_offsets = {}
        cumulative = 0.0
        for sv in sv_sorted:
            scene_offsets[sv.get("scene_number", 0)] = cumulative
            cumulative += sv.get("duration", 12.0)

        # Build narration track
        narration_track = None
        if narration_files:
            inputs = ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={total_duration:.2f}"]
            fp = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo[base]"]
            idx = 1
            labels = ["base"]
            for sn in sorted(narration_files.keys()):
                offset = scene_offsets.get(sn, 0.0)
                inputs.extend(["-i", narration_files[sn]])
                lb = f"n{idx}"
                fp.append(f"[{idx}:a]adelay={int(offset*1000)}|{int(offset*1000)},aformat=sample_rates=44100:channel_layouts=stereo[{lb}]")
                labels.append(lb)
                idx += 1

            if len(labels) > 1:
                mix_in = "".join(f"[{lb}]" for lb in labels)
                fp.append(f"{mix_in}amix=inputs={len(labels)}:duration=longest:normalize=0[out]")
                narration_track = f"{tmpdir}/narr_{target}.mp3"
                r = subprocess.run(
                    ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fp), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", narration_track],
                    capture_output=True, timeout=120
                )
                if r.returncode != 0:
                    narration_track = None

        # Strip audio from base and prepare music
        silent = f"{tmpdir}/silent.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", base_video, "-c:v", "copy", "-an", silent], capture_output=True, timeout=60)

        music_key = project.get("post_production_status", {}).get("music_track", "emotional")
        mp = os.path.join(MUSIC_DIR, f"{music_key}.mp3")
        if not os.path.exists(mp):
            mp = os.path.join(MUSIC_DIR, "emotional.mp3")

        music_prep = f"{tmpdir}/music.mp3"
        r = subprocess.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", mp, "-t", f"{total_duration:.2f}",
            "-af", f"afade=t=in:st=0:d=2,afade=t=out:st={max(0,total_duration-3):.2f}:d=3,volume=0.15",
            "-c:a", "libmp3lame", "-b:a", "128k", music_prep
        ], capture_output=True, timeout=60)
        has_music = r.returncode == 0

        final_loc = f"{tmpdir}/final_{target}.mp4"
        if narration_track and has_music:
            cmd = ["ffmpeg", "-y", "-i", silent, "-i", narration_track, "-i", music_prep,
                   "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest:weights=1 0.3:normalize=0[a]",
                   "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                   "-movflags", "+faststart", "-shortest", final_loc]
        elif narration_track:
            cmd = ["ffmpeg", "-y", "-i", silent, "-i", narration_track, "-map", "0:v", "-map", "1:a",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final_loc]
        else:
            shutil.copy2(base_video, final_loc)
            cmd = None

        if cmd:
            r = subprocess.run(cmd, capture_output=True, timeout=300)
            if r.returncode != 0:
                shutil.copy2(base_video, final_loc)

        # Compress if needed
        file_size = os.path.getsize(final_loc) if os.path.exists(final_loc) else 0
        if file_size > 45 * 1024 * 1024:
            comp = f"{tmpdir}/comp_{target}.mp4"
            tbr = int((40 * 8 * 1024) / max(total_duration, 1))
            subprocess.run(["ffmpeg", "-y", "-i", final_loc, "-c:v", "libx264", "-preset", "medium",
                            "-b:v", f"{tbr}k", "-vf", "scale=960:540", "-c:a", "aac", "-b:a", "128k",
                            "-movflags", "+faststart", comp], capture_output=True, timeout=600)
            if os.path.exists(comp):
                final_loc = comp
                file_size = os.path.getsize(comp)

        # Upload
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "uploading", "message": f"Enviando {LANG_NAMES.get(target, target)}..."}
        })

        with open(final_loc, 'rb') as f:
            vb = f.read()

        try:
            url = _upload_to_storage(vb, f"studio/{project_id}_final_{target}.mp4", "video/mp4")
        except Exception as e:
            url = None
            logger.error(f"Studio [{project_id}]: Loc upload failed: {e}")

        # Save
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            loc_out = {
                "type": "final_video", "url": url, "language": target,
                "duration": total_duration, "has_narration": bool(narration_track),
                "has_music": has_music, "file_size_mb": round(file_size/(1024*1024), 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            project["outputs"] = [o for o in project["outputs"] if not (o.get("type") == "final_video" and o.get("language") == target)]
            project["outputs"].append(loc_out)
            if not project.get("localizations"):
                project["localizations"] = {}
            project["localizations"][target] = {
                "narrations": translated_narrations, "final_url": url, "voice_id": voice_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            project[f"localization_{target}"] = {"phase": "complete", "final_url": url, "language": target}
            _add_milestone(project, f"localization_{target}", f"Localizado → {LANG_NAMES.get(target, target)}")
            _save_project(tenant_id, settings, projects)

        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info(f"Studio [{project_id}]: Localization {target} complete! URL: {url}")

    except Exception as e:
        logger.error(f"Studio [{project_id}] localization error: {e}")
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "error", "error": str(e)[:300]}
        })


@router.post("/projects/{project_id}/localize")
async def localize_project(project_id: str, req: LocalizeRequest, tenant=Depends(get_current_tenant)):
    """Localize a produced video to a new language (re-dub)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.target_language == project.get("language", "pt"):
        raise HTTPException(status_code=400, detail="Idioma alvo é o mesmo do original")

    has_final = any(o.get("type") == "final_video" for o in project.get("outputs", []))
    if not has_final:
        raise HTTPException(status_code=400, detail="Rode a pós-produção primeiro.")

    _update_project_field(tenant["id"], project_id, {
        f"localization_{req.target_language}": {"phase": "starting", "message": "Iniciando localização..."}
    })
    thread = threading.Thread(target=_run_localization, args=(tenant["id"], project_id, req), daemon=True)
    thread.start()
    return {"status": "started", "target_language": req.target_language, "target_name": LANG_NAMES.get(req.target_language, req.target_language)}


@router.get("/projects/{project_id}/localizations")
async def get_localizations(project_id: str, tenant=Depends(get_current_tenant)):
    """Get all localizations for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    final_videos = {}
    for o in project.get("outputs", []):
        if o.get("type") == "final_video" and o.get("url"):
            final_videos[o.get("language", "?")] = o

    statuses = {}
    for lc in ["en", "es", "fr", "de", "it", "pt"]:
        s = project.get(f"localization_{lc}", {})
        if s:
            statuses[lc] = s

    return {
        "localizations": project.get("localizations", {}),
        "statuses": statuses,
        "final_videos": final_videos,
        "original_language": project.get("language", "pt"),
        "post_production_status": project.get("post_production_status", {}),
    }



# ═══════════════════════════════════════════════════════════
# ── PHASE 3: Scene Re-edit + Subtitles ──
# ═══════════════════════════════════════════════════════════

class RegenSceneRequest(BaseModel):
    new_prompt_hint: Optional[str] = ""  # optional override for the scene prompt


@router.post("/projects/{project_id}/regen-scene/{scene_number}")
async def regen_scene(project_id: str, scene_number: int, req: RegenSceneRequest = Body(default=None), tenant=Depends(get_current_tenant)):
    """Re-generate a single scene video without re-producing the entire project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_number") == scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Cena {scene_number} não encontrada")

    # Mark as regenerating
    _update_project_field(tenant["id"], project_id, {
        f"regen_scene_{scene_number}": {"phase": "starting", "message": f"Re-gerando cena {scene_number}..."}
    })

    def _regen_bg():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return

            animation_sub = _project.get("animation_sub", "pixar_3d")
            character_avatars = _project.get("character_avatars", {})

            # Build composite avatar for this scene
            chars_in = scene.get("characters_in_scene", [])
            composite_url = None
            if len(chars_in) > 1:
                urls = [character_avatars.get(c) for c in chars_in if character_avatars.get(c)]
                if urls:
                    composite_url = urls[0]  # Use first avatar as reference
            elif len(chars_in) == 1:
                composite_url = character_avatars.get(chars_in[0])

            # Get production design for character descriptions
            pd = _project.get("agents_output", {}).get("production_design", {})
            char_bible = pd.get("character_bible", {})
            char_descriptions = "\n".join([f"- {name}: {str(info)[:100]}" for name, info in char_bible.items()])

            # Build Sora 2 prompt
            ANIMATION_SUB_PROMPTS = {
                "pixar_3d": "Premium 3D CGI animation (Pixar/DreamWorks quality). Subsurface scattering, global illumination, cinematic DoF.",
                "cartoon_3d": "Stylized 3D cartoon (bright colors, simplified shapes, cel-shading).",
                "cartoon_2d": "Classic 2D hand-drawn animation (Disney/Ghibli quality, painted backgrounds).",
                "anime_2d": "Japanese anime style (detailed backgrounds, dramatic lighting, expressive eyes).",
                "realistic": "Cinematic photorealistic. Shallow DoF, film grain, natural lighting.",
                "watercolor": "Watercolor painting animation. Visible brush strokes, soft pastel tones.",
            }
            style_hint = ANIMATION_SUB_PROMPTS.get(animation_sub, ANIMATION_SUB_PROMPTS["pixar_3d"])

            prompt_hint = ""
            if req and req.new_prompt_hint:
                prompt_hint = f"\nADDITIONAL DIRECTION: {req.new_prompt_hint}"

            video_prompt = f"""{style_hint}
SCENE: {scene.get('title', '')}. {scene.get('description', '')}
CAMERA: {scene.get('camera', 'medium shot')}
LIGHTING: {scene.get('lighting', 'warm natural')}
CHARACTERS: {', '.join(chars_in)}
{char_descriptions}
MOOD: {scene.get('mood', '')}{prompt_hint}
CRITICAL: Maintain EXACT same character designs throughout. CONSISTENT art style."""

            if composite_url:
                video_prompt = f"[Reference character image: {composite_url}]\n{video_prompt}"

            logger.info(f"Studio [{project_id}]: Regenerating scene {scene_number}")

            _update_project_field(tenant["id"], project_id, {
                f"regen_scene_{scene_number}": {"phase": "generating", "message": "Gerando vídeo com Sora 2..."}
            })

            # Call Sora 2
            from openai import OpenAI
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            client = OpenAI(api_key=openai_key)

            try:
                response = client.responses.create(
                    model="sora",
                    input=video_prompt,
                    tools=[{"type": "video_generation", "size": "1080x1920", "duration": 10, "n_variants": 1}],
                )
                # Poll for completion
                import time as _time
                for _ in range(120):
                    response = client.responses.retrieve(response.id)
                    if response.status == "completed":
                        break
                    _time.sleep(5)

                if response.status == "completed":
                    video_url = None
                    for output in response.output:
                        if hasattr(output, 'url'):
                            video_url = output.url
                            break

                    if video_url:
                        # Download and re-upload
                        video_data = urllib.request.urlopen(video_url).read()
                        filename = f"studio/{project_id}_scene_{scene_number}_v2.mp4"
                        new_url = _upload_to_storage(video_data, filename, "video/mp4")

                        # Update the output
                        _settings, _projects, _project = _get_project(tenant["id"], project_id)
                        if _project:
                            for o in _project.get("outputs", []):
                                if o.get("scene_number") == scene_number and o.get("type") == "video":
                                    o["url"] = new_url
                                    o["regenerated"] = True
                                    o["regenerated_at"] = datetime.now(timezone.utc).isoformat()
                                    break
                            _project[f"regen_scene_{scene_number}"] = {"phase": "complete", "url": new_url}
                            _add_milestone(_project, f"regen_scene_{scene_number}", f"Cena {scene_number} regenerada")
                            _save_project(tenant["id"], _settings, _projects)
                        logger.info(f"Studio [{project_id}]: Scene {scene_number} regenerated: {new_url}")
                        return
                    else:
                        raise RuntimeError("No video URL in Sora response")
                else:
                    raise RuntimeError(f"Sora job status: {response.status}")

            except Exception as e:
                logger.error(f"Studio [{project_id}]: Scene regen failed: {e}")
                _update_project_field(tenant["id"], project_id, {
                    f"regen_scene_{scene_number}": {"phase": "error", "error": str(e)[:200]}
                })

        except Exception as e:
            logger.error(f"Studio [{project_id}]: Scene regen error: {e}")
            _update_project_field(tenant["id"], project_id, {
                f"regen_scene_{scene_number}": {"phase": "error", "error": str(e)[:200]}
            })

    thread = threading.Thread(target=_regen_bg, daemon=True)
    thread.start()
    return {"status": "started", "scene_number": scene_number}


@router.post("/projects/{project_id}/generate-subtitles")
async def generate_subtitles(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate SRT subtitles from narrations and burn them into the final video."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    narrations = project.get("narrations", [])
    if not narrations:
        raise HTTPException(status_code=400, detail="Sem narrações. Rode a pós-produção primeiro.")

    outputs = project.get("outputs", [])

    # Calculate scene offsets
    scene_videos = sorted(
        [o for o in outputs if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")],
        key=lambda x: x.get("scene_number", 0)
    )
    scene_durations = {}
    for sv in scene_videos:
        scene_durations[sv.get("scene_number", 0)] = sv.get("duration", 12.0)

    cumulative = 0.0
    srt_entries = []
    for i, narr in enumerate(narrations):
        sn = narr.get("scene_number", i + 1)
        text = narr.get("narration", narr.get("text", ""))
        if not text.strip():
            cumulative += scene_durations.get(sn, 12.0)
            continue

        start_time = cumulative + 0.5  # 0.5s delay for natural feel
        dur = scene_durations.get(sn, 12.0)
        end_time = cumulative + dur - 0.5

        # Format SRT timestamps
        def _fmt_srt(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        srt_entries.append(f"{i+1}\n{_fmt_srt(start_time)} --> {_fmt_srt(end_time)}\n{text}\n")
        cumulative += dur

    srt_content = "\n".join(srt_entries)

    # Save SRT for all languages
    lang = project.get("language", "pt")
    all_srts = {lang: srt_content}

    # Generate SRT for localized versions
    localizations = project.get("localizations", {})
    for loc_lang, loc_data in localizations.items():
        loc_narrations = loc_data.get("narrations", [])
        if loc_narrations:
            cumulative = 0.0
            loc_entries = []
            for i, narr in enumerate(loc_narrations):
                sn = narr.get("scene_number", i + 1)
                text = narr.get("narration", "")
                if not text.strip():
                    cumulative += scene_durations.get(sn, 12.0)
                    continue
                start_time = cumulative + 0.5
                dur = scene_durations.get(sn, 12.0)
                end_time = cumulative + dur - 0.5
                loc_entries.append(f"{i+1}\n{_fmt_srt(start_time)} --> {_fmt_srt(end_time)}\n{text}\n")
                cumulative += dur
            all_srts[loc_lang] = "\n".join(loc_entries)

    # Save SRTs to storage
    srt_urls = {}
    for slang, srt_text in all_srts.items():
        filename = f"studio/{project_id}_subtitles_{slang}.srt"
        srt_bytes = srt_text.encode("utf-8")
        try:
            url = _upload_to_storage(srt_bytes, filename, "text/srt")
            srt_urls[slang] = url
        except Exception as e:
            logger.warning(f"Studio [{project_id}]: SRT upload failed for {slang}: {e}")

    # Save to project
    _update_project_field(tenant["id"], project_id, {
        "subtitles": srt_urls,
    })

    return {
        "status": "complete",
        "subtitles": srt_urls,
        "languages": list(srt_urls.keys()),
    }
