"""Directed Studio v2 — Shared helpers, models, and constants for the studio package."""
__all__ = [
    # Router & Framework
    "router", "APIRouter", "Depends", "HTTPException", "Body", "UploadFile", "File",
    "BaseModel", "Optional", "List",
    # Stdlib
    "uuid", "base64", "os", "asyncio", "threading", "subprocess", "shutil",
    "datetime", "timezone", "urllib", "litellm", "load_dotenv",
    # Core deps
    "supabase", "get_current_user", "get_current_tenant", "logger",
    # Pipeline config
    "STORAGE_BUCKET", "EMERGENT_PROXY_URL", "ELEVENLABS_VOICES", "MUSIC_LIBRARY",
    # API Keys
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
    # Helper functions
    "_ensure_ffmpeg", "_ffmpeg_checked",
    "_get_settings", "_save_settings", "_get_project", "_save_project",
    "_update_project_field", "_add_milestone", "_cleanup_stale_storyboards",
    "_upload_to_storage", "_call_claude_async", "_call_claude_sync", "_parse_json",
    "_analyze_avatars_with_vision", "_build_production_design", "_create_composite_avatar",
    "_ANTI_INSTRUCTIONS", "_extract_last_frame", "_generate_character_sheet",
    "_build_style_dna", "_validate_scene_continuity", "_apply_color_grading",
    "_generate_scene_keyframe",
    # Pydantic Models
    "StudioProject", "ChatMessage", "StartProductionRequest", "RegenerateSceneRequest",
    "GenerateAvatarRequest", "GenerateNarrationRequest", "PostProduceRequest", "LocalizeRequest",
]

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
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
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


# Cache stats endpoint
def _get_settings(tenant_id: str) -> dict:
    from core.cache import project_cache
    return project_cache.get_settings(tenant_id)

def _save_settings(tenant_id: str, settings: dict, flush_now: bool = False):
    from core.cache import project_cache
    project_cache.save_settings(tenant_id, settings, flush_now=flush_now)

def _get_project(tenant_id: str, project_id: str):
    settings = _get_settings(tenant_id)
    projects = settings.get("studio_projects", [])
    project = next((p for p in projects if p.get("id") == project_id), None)
    return settings, projects, project

def _save_project(tenant_id: str, settings: dict, projects: list, flush_now: bool = False):
    settings["studio_projects"] = projects
    _save_settings(tenant_id, settings, flush_now=flush_now)

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

async def _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id):
    """Claude Vision analyzes ALL character avatars and produces structured Identity Cards.
    Returns dict: {character_name: {identity_card}} with immutable traits and prohibitions.
    Also returns legacy format for backward compatibility.
    """
    if not char_avatars:
        return {}

    content_parts = [{"type": "text", "text": """Analyze each character avatar image below with EXTREME PRECISION. For EACH character, produce a structured CHARACTER IDENTITY CARD.

You MUST examine the image carefully and determine:
1. Is the character BIPEDAL (standing on two legs like a human) or QUADRUPED (on four legs)?
2. What EXACT species is it? (e.g., dromedary camel, golden retriever, tabby cat, human)
3. What is the EXACT body anatomy visible in the image?

Return ONLY valid JSON with this EXACT structure:
{
  "CharacterName": {
    "description": "Full 80-word English visual description of exactly what you see in the avatar image",
    "species": "exact species name",
    "body_type": "BIPEDAL_ANTHROPOMORPHIC or QUADRUPED_ANIMAL or HUMAN",
    "locomotion": "How this character moves based on what you see (e.g., 'walks upright on two legs' or 'walks on four legs')",
    "anatomy": {
      "head": "exact head description from avatar",
      "body": "exact torso/body description",
      "arms_or_front_legs": "what you see — arms with hands/hooves, or front legs",
      "legs_or_hind_legs": "what you see — two legs standing upright, or four legs",
      "tail": "tail description if visible, or 'none'"
    },
    "default_clothing": "exact clothing visible in avatar, or 'none'",
    "fur_skin_color": "exact primary color and texture",
    "eye_details": "exact eye color, shape, notable features",
    "immutable_traits": [
      "list of 4-6 visual traits that MUST appear in EVERY frame — derived directly from the avatar image"
    ],
    "prohibitions": [
      "list of 4-6 things that must NEVER happen to this character — opposite of what you see"
    ]
  }
}

CRITICAL: Your analysis must be based SOLELY on what you SEE in the avatar image. The avatar image is the ABSOLUTE VISUAL TRUTH.
- If the character is standing on two legs in the avatar → body_type = BIPEDAL_ANTHROPOMORPHIC, prohibition = "NEVER on four legs"
- If the character is an animal on four legs → body_type = QUADRUPED_ANIMAL, prohibition = "NEVER standing bipedally"
- Immutable traits = what you see that must NEVER change across scenes
- Prohibitions = the OPPOSITE of what you see (to prevent the AI from changing it)"""}]

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
            if img_bytes[:3] == b'\xff\xd8\xff':
                mime = "image/jpeg"
            elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                mime = "image/png"
            elif img_bytes[:4] == b'RIFF' and img_bytes[8:12] == b'WEBP':
                mime = "image/webp"
            else:
                mime = "image/jpeg"
            content_parts.append({"type": "text", "text": f"CHARACTER: {name}"})
            content_parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}})
            names_with_images.append(name)
        except Exception as e:
            logger.warning(f"Studio [{project_id}]: Avatar read error for {name}: {e}")

    if not names_with_images:
        return {}

    try:
        response = await litellm.acompletion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": content_parts}],
            max_tokens=4000, timeout=90, api_key=ANTHROPIC_API_KEY,
        )
        result = response.choices[0].message.content
        parsed = _parse_json(result)
        if parsed:
            logger.info(f"Studio [{project_id}]: Avatar Identity Cards — {len(parsed)} characters: {list(parsed.keys())}")
            # Store both the identity cards and legacy descriptions for backward compat
            for name, card in parsed.items():
                if isinstance(card, dict):
                    # Ensure legacy description field exists
                    if "description" not in card:
                        card["description"] = f"{card.get('species', 'character')} — {card.get('body_type', 'unknown')}"
                else:
                    # Legacy format — convert to minimal identity card
                    parsed[name] = {
                        "description": card,
                        "species": "unknown",
                        "body_type": "UNKNOWN",
                        "locomotion": "unknown",
                        "anatomy": {},
                        "immutable_traits": [],
                        "prohibitions": [],
                    }
            return parsed
    except Exception as e:
        logger.warning(f"Studio [{project_id}]: Avatar Identity Cards failed: {e}")
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

    # Build character info with Identity Cards when available
    char_info_lines = []
    for ch in characters:
        name = ch['name']
        avatar_data = avatar_descriptions.get(name, {})
        if isinstance(avatar_data, dict) and avatar_data.get("body_type"):
            # Identity Card format
            card = avatar_data
            char_info_lines.append(
                f"- {name}: {ch.get('description', '')} | "
                f"AVATAR IDENTITY: species={card.get('species','?')}, "
                f"body_type={card.get('body_type','?')}, "
                f"locomotion={card.get('locomotion','?')}, "
                f"fur/skin={card.get('fur_skin_color','?')}, "
                f"clothing={card.get('default_clothing','?')}. "
                f"IMMUTABLE: {'; '.join(card.get('immutable_traits', [])[:4])}. "
                f"PROHIBITIONS: {'; '.join(card.get('prohibitions', [])[:4])}"
            )
        else:
            # Legacy string format
            desc = avatar_data if isinstance(avatar_data, str) else avatar_data.get("description", "No avatar reference")
            char_info_lines.append(f"- {name}: {ch.get('description', '')} | Avatar visual: {desc}")
    char_info = "\n".join(char_info_lines)

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


async def _validate_scene_continuity(current_frame_path: str, prev_frame_path: str,
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

        response = await litellm.acompletion(
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


