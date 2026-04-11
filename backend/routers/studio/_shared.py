"""Directed Studio v2 — Shared helpers, models, and constants for the studio package."""
__all__ = [
    # Router & Framework
    "router", "APIRouter", "Depends", "HTTPException", "Body", "UploadFile", "File",
    "BaseModel", "Optional", "List",
    # Stdlib
    "uuid", "base64", "os", "asyncio", "threading", "subprocess", "shutil", "tempfile",
    "datetime", "timezone", "urllib", "litellm", "load_dotenv",
    # Core deps
    "supabase", "get_current_user", "get_current_tenant", "logger",
    # Pipeline config
    "STORAGE_BUCKET", "EMERGENT_PROXY_URL", "ELEVENLABS_VOICES", "MUSIC_LIBRARY",
    # API Keys
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
    # Helper functions
    "_ensure_ffmpeg", "_ffmpeg_checked", "_run_async_in_thread",
    "_get_settings", "_save_settings", "_get_project", "_save_project",
    "_update_project_field", "_add_milestone", "_cleanup_stale_storyboards",
    "_upload_to_storage", "_call_claude_async", "_call_claude_sync", "_parse_json",
    "_analyze_avatars_with_vision", "_build_production_design", "_create_composite_avatar",
    "_ANTI_INSTRUCTIONS", "_extract_last_frame", "_generate_character_sheet",
    "_build_style_dna", "_validate_scene_continuity", "_apply_color_grading",
    "_generate_scene_keyframe", "_get_folder_characters", "_simplify_character_name", "_get_audience_guideline",
    # Pydantic Models
    "StudioProject", "ChatMessage", "StartProductionRequest", "RegenerateSceneRequest",
    "GenerateAvatarRequest", "GenerateNarrationRequest", "PostProduceRequest", "LocalizeRequest",
]

import uuid
import base64
import os
import asyncio
import tempfile
import urllib.request
import litellm
import threading
import subprocess
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict
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

def _run_async_in_thread(coro):
    """Execute async function in sync thread context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


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

def _update_project_field(tenant_id: str, project_id: str, updates: dict, flush_now: bool = False):
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        logger.warning(f"_update_project_field: project {project_id} not found for tenant {tenant_id}")
        return
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(project.get(k), dict):
            project[k].update(v)
        else:
            project[k] = v
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant_id, settings, projects, flush_now=flush_now)


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
    """Call LLM via litellm (async). Uses OpenAI as primary, Claude as fallback. 3 retries with timeout."""
    # Primary: OpenAI (Claude quota exhausted)
    models_to_try = [
        ("gpt-4o-mini", os.environ.get("OPENAI_API_KEY")),
        ("anthropic/claude-sonnet-4-5-20250929", ANTHROPIC_API_KEY),
    ]
    
    last_error = None
    for model_name, api_key in models_to_try:
        if not api_key:
            continue
        for attempt in range(3):
            try:
                response = await litellm.acompletion(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=max_tokens,
                    timeout=120,
                    num_retries=0,
                    api_key=api_key,
                )
                text = response.choices[0].message.content
                if text:
                    return text
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                retryable = any(k in err_str for k in ["502", "503", "529", "timeout", "disconnected", "overloaded", "rate"])
                if attempt < 2 and retryable:
                    logger.warning(f"LLM async {model_name} attempt {attempt+1} failed: {str(e)[:100]}. Retrying...")
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                logger.warning(f"LLM async {model_name} failed: {str(e)[:150]}. Trying next model...")
                break
    
    raise Exception(f"All LLM models failed: {last_error}")


def _call_claude_sync(system_prompt: str, user_prompt: str, max_tokens: int = 4000, timeout_per_attempt: int = 300) -> str:
    """Call LLM via litellm (sync). Uses OpenAI as primary, Claude as fallback.
    3 retries per model, with timeout.
    """
    import time as _time

    models_to_try = [
        ("gpt-4o-mini", os.environ.get("OPENAI_API_KEY")),
        ("anthropic/claude-sonnet-4-5-20250929", ANTHROPIC_API_KEY),
    ]
    
    last_error = None
    for model_name, api_key in models_to_try:
        if not api_key:
            continue
        for attempt in range(3):
            t_start = _time.time()
            try:
                response = litellm.completion(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=max_tokens,
                    timeout=timeout_per_attempt,
                    num_retries=0,
                    api_key=api_key,
                )
                text = response.choices[0].message.content
                elapsed = _time.time() - t_start
                if text:
                    logger.info(f"LLM [{model_name}] responded in {elapsed:.1f}s ({len(text)} chars)")
                    return text
            except Exception as e:
                elapsed = _time.time() - t_start
                last_error = e
                err_str = str(e).lower()
                retryable = any(k in err_str for k in ["502", "503", "529", "timeout", "disconnected", "overloaded", "connection", "reset", "eof", "broken pipe", "server", "rate"])
                
                logger.warning(f"LLM [{model_name}] attempt {attempt+1}/3 failed ({elapsed:.0f}s): {str(e)[:150]}")
                
                if attempt < 2 and retryable:
                    _time.sleep(5)
                    continue
                logger.warning(f"LLM [{model_name}] exhausted retries, trying next model...")
                break
    
    raise Exception(f"All LLM models failed after retries: {last_error}")


def _parse_json(text):
    import json
    import re

    # Strip markdown code blocks
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_match:
        text = code_match.group(1).strip()

    # Try to find JSON object or array
    if '{' not in text and '[' not in text:
        return None

    try:
        # Try parsing whole text first
        return json.loads(text)
    except:
        pass

    # Try extracting object
    if '{' in text:
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
        except:
            pass

    # Try extracting array
    if '[' in text:
        try:
            start = text.index('[')
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '[':
                    depth += 1
                elif text[i] == ']':
                    depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
        except:
            pass

    # JSON was truncated — try to repair
    if '{' in text:
        start = text.index('{')
        raw = text[start:]
    elif '[' in text:
        start = text.index('[')
        raw = text[start:]
    else:
        return None
        
    # Count open structures
    open_brackets = raw.count('[') - raw.count(']')
    open_braces = raw.count('{') - raw.count('}')
    
    repaired = raw + ']' * open_brackets + '}' * open_braces
    try:
        return json.loads(repaired)
    except Exception:
        return None
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
        # Production Designer needs longer timeout for large projects (24+ scenes)
        result = _call_claude_sync(system, user_prompt, max_tokens=5000, timeout_per_attempt=240)
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
    """KEYFRAME-FIRST PIPELINE: Generate a starting frame image via Gemini 2.5 Flash Image to force
    correct character identity before Sora 2 animation.
    Now sends ALL character avatars as multimodal references for maximum consistency.
    """
    import tempfile
    from core.llm import generate_image_gemini_sync
    
    try:
        if not GEMINI_API_KEY:
            logger.warning(f"Studio [{project_id}]: No GEMINI_API_KEY — skipping keyframe")
            return None

        # Build character descriptions from character_bible
        char_desc_block = ""
        if character_bible:
            for cname in chars_in_scene:
                desc = character_bible.get(cname, "")
                if desc:
                    char_desc_block += f"\n- {cname}: {desc}"

        # Build avatar reference labels
        avatar_labels = []
        for i, cname in enumerate(chars_in_scene):
            if char_avatars.get(cname):
                avatar_labels.append(f"Imagem de referência {i+1}: {cname}")

        prompt_text = f"""Generate a SINGLE FRAME for an animated film. This will be used as a starting keyframe for Sora 2 video generation.

{sora_prompt}

CHARACTER IDENTITY (from avatar images above — ABSOLUTE TRUTH, match EXACTLY):
{chr(10).join(avatar_labels) if avatar_labels else ''}
{char_desc_block if char_desc_block else 'See reference images.'}

CRITICAL RULES:
- Every character MUST match the reference avatar images EXACTLY — same species, same face shape, same fur color, same clothing
- If a character is a BIPEDAL ANTHROPOMORPHIC ANIMAL in the reference, they MUST be shown STANDING UPRIGHT ON TWO LEGS — never as a quadruped
- ONLY include the characters listed above — DO NOT add random extra animals or characters
- Style MUST be 3D CGI Pixar quality with volumetric lighting
- This is ONE static frame — capture the opening moment of this scene"""

        # Collect ALL character avatar images for multimodal input
        primary_image = None
        extra_images = []
        
        for char_name in chars_in_scene:
            url = char_avatars.get(char_name)
            cached_path = avatar_cache.get(url) if url else None
            if cached_path and os.path.exists(cached_path):
                with open(cached_path, 'rb') as f:
                    img_bytes = f.read()
                if primary_image is None:
                    primary_image = img_bytes
                else:
                    extra_images.append(img_bytes)
        
        avatar_count = 1 + len(extra_images) if primary_image else 0
        logger.info(f"Studio [{project_id}]: Keyframe scene {scene_num} using {avatar_count} avatar references (multimodal)")

        # Generate keyframe using Gemini with ALL avatars
        result = generate_image_gemini_sync(prompt_text, primary_image, extra_images=extra_images)

        if result:
            # Resize to match Sora 2 expected dimensions (1280x720)
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(result))
            img_resized = img.resize((1280, 720), Image.Resampling.LANCZOS)
            
            keyframe_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            img_resized.save(keyframe_path, 'PNG')
            
            logger.info(f"Studio [{project_id}]: Keyframe generated and resized for scene {scene_num} (1280x720)")
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
    # ✅ CRITICAL FIELDS ADDED - Required for Kling support
    target_audience: str = "all"
    character_folder_id: Optional[str] = None
    company_id: Optional[str] = None
    format_strategy: str = "safe_zone"
    formats_requested: list = ["16:9"]
    video_engine: str = "sora"  # ✅ CRITICAL: "sora" or "kling"
    target_duration_minutes: int = 5  # ✅ CRITICAL: duration in minutes

class ChatMessage(BaseModel):
    project_id: Optional[str] = None
    message: str = ""
    language: str = "pt"

class StartProductionRequest(BaseModel):
    project_id: str
    video_duration: int = 12
    character_avatars: dict = {}  # {character_name: avatar_url}
    visual_style: str = ""  # override style for this run
    video_engine: str = "sora"  # "sora" or "kling"

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





# ══════════════════════════════════════════════════════════════════════════════
# CHARACTER FOLDER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _get_folder_characters(tenant_id: str, folder_id: str) -> List[dict]:
    """
    Get ALL characters from a specific folder
    Used by Screenwriter to know which characters are available
    """
    if not folder_id:
        return []
    
    settings = _get_settings(tenant_id)
    avatars = settings.get("avatars", {})
    
    folder_characters = []
    for avatar_id, avatar_data in avatars.items():
        if avatar_data.get("folder_id") == folder_id:
            folder_characters.append({
                "id": avatar_id,
                "name": avatar_data.get("name", ""),
                "description": avatar_data.get("prompt", "")[:200],  # First 200 chars
                "image_url": avatar_data.get("image_url", ""),
                "age": avatar_data.get("age", "adult"),
                "role": avatar_data.get("role", "supporting"),
                "species": avatar_data.get("species", ""),
            })
    
    logger.info(f"Folder {folder_id}: Found {len(folder_characters)} characters")
    return folder_characters


def _simplify_character_name(full_name: str) -> str:
    """
    Simplify character name for narrative
    Ex: "Adão Biblizoo Baby" → "Adão"
    """
    # Remove common suffixes
    name = full_name.replace(" Biblizoo Baby", "").replace(" Studio", "").strip()
    return name


def _get_audience_guideline(target_audience: str, lang: str = "pt") -> str:
    """Get content adaptation guidelines for target audience"""
    guidelines = {
        "pt": {
            "3-6": "Público 3-6 anos: Linguagem EXTREMAMENTE SIMPLES, frases curtas (3-5 palavras). Ações claras e óbvias. Emoções primárias e exageradas. Ritmo lento. Tom alegre e lúdico.",
            "6-9": "Público 6-9 anos: Linguagem SIMPLES com variedade. Ações dinâmicas com pequenos desafios. Emoções primárias e secundárias. Ritmo moderado. Tom educativo e aventureiro.",
            "10-13": "Público 10-13 anos: Linguagem CLARA, conceitos mais complexos. Ações elaboradas com causa-efeito. Emoções amplas incluindo conflitos internos. Ritmo variado. Tom inspirador e épico.",
            "14-17": "Público 14-17 anos: Linguagem NATURAL com nuances. Ações complexas com simbolismo. Emoções profundas e ambiguidade moral. Ritmo cinematográfico. Tom realista e maduro.",
            "18-25": "Público 18-25 anos: Linguagem SOFISTICADA com referências culturais. Ações realistas com consequências. Emoções complexas e sutileza. Ritmo variado. Tom contemporâneo e autêntico.",
            "25+": "Público 25+ anos: Linguagem COMPLETA sem restrições. Ações realistas com simbolismo profundo. Emoções nuançadas. Ritmo sofisticado. Tom maduro e reflexivo.",
            "all": "Público TODAS IDADES: Linguagem CLARA mas não infantilizada. Ações universais. Emoções primárias com camadas sutis. Ritmo equilibrado. Tom caloroso e inspirador com múltiplas camadas."
        },
        "en": {
            "3-6": "Audience 3-6 years: EXTREMELY SIMPLE language, short sentences (3-5 words). Clear obvious actions. Primary exaggerated emotions. Slow pace. Cheerful playful tone.",
            "6-9": "Audience 6-9 years: SIMPLE language with variety. Dynamic actions with small challenges. Primary and secondary emotions. Moderate pace. Educational adventurous tone.",
            "10-13": "Audience 10-13 years: CLEAR language, more complex concepts. Elaborate cause-effect actions. Wide emotions including internal conflicts. Varied pace. Inspiring epic tone.",
            "14-17": "Audience 14-17 years: NATURAL language with nuances. Complex actions with symbolism. Deep emotions and moral ambiguity. Cinematic pace. Realistic mature tone.",
            "18-25": "Audience 18-25 years: SOPHISTICATED language with cultural references. Realistic actions with consequences. Complex emotions and subtlety. Varied pace. Contemporary authentic tone.",
            "25+": "Audience 25+ years: COMPLETE language without restrictions. Realistic actions with deep symbolism. Nuanced emotions. Sophisticated pace. Mature reflective tone.",
            "all": "Audience ALL AGES: CLEAR language but not infantilized. Universal actions. Primary emotions with subtle layers. Balanced pace. Warm inspiring tone with multiple layers."
        }
    }
    
    return guidelines.get(lang, {}).get(target_audience, guidelines[lang]["all"])


# ══════════════════════════════════════════════════════════════════════════════
# DIALOGUE AGE PROFILES - Detailed dialogue adaptation for each age group
# ══════════════════════════════════════════════════════════════════════════════

DIALOGUE_AGE_PROFILES = {
    "pt": {
        "2-5": {
            "name": "Pré-escolar (2-5 anos)",
            "words_per_line": "3-5 palavras",
            "vocabulary": "ULTRA SIMPLES - Palavras concretas e cotidianas (mamãe, papai, água, sol, bola, casa)",
            "sentence_structure": "Frases declarativas curtas. Evitar subordinadas.",
            "repetition": "ALTA - Repetir palavras-chave 3-4 vezes por cena para fixação",
            "rhythm": "MUITO LENTO - Pausas longas entre falas (2-3 segundos)",
            "emotions": "EXAGERADAS - Usar adjetivos intensificadores (muito feliz!, super triste!, tão lindo!)",
            "questions": "Simples e diretas (O que é? Onde vai? Quem é?)",
            "techniques": [
                "Usar MUITAS onomatopeias (piu-piu, au-au, miau, trim-trim, vrum-vrum)",
                "Usar diminutivos carinhosos (papai, mamãe, filhinho, nenê, docinho)",
                "Usar interjeições frequentes (Uau!, Olha!, Eba!, Ai!)",
                "Narrador repete ações que os personagens fazem",
                "Perguntas retóricas para engajamento (Vamos ver? Quer ver?)"
            ],
            "example": """Sara: 'Olha, Isaac! Olha!'
Isaac: 'O quê, mamãe?'
Sara: 'Passarinho! Passarinho azul!'
Isaac: 'Piu-piu! Passarinho piu-piu!'
Abraão: 'Que lindo, filho!'
Isaac: 'Papai, passarinho voando!'
Narrador: 'O passarinho voa alto, alto, alto no céu azul!'"""
        },
        "3-6": {
            "name": "Pré-escolar (3-6 anos)",
            "words_per_line": "5-8 palavras",
            "vocabulary": "MUITO SIMPLES - Objetos concretos, ações básicas, cores primárias",
            "sentence_structure": "Frases simples. Até 2 orações coordenadas.",
            "repetition": "ALTA - Repetir conceitos-chave 2-3 vezes",
            "rhythm": "LENTO - Pausas perceptíveis entre diálogos",
            "emotions": "Claras e nomeadas (alegria, tristeza, medo, amor)",
            "questions": "Simples com 'o que', 'onde', 'quem'",
            "techniques": [
                "Onomatopeias frequentes",
                "Rimas simples ocasionais",
                "Contagem básica (um, dois, três)",
                "Cores e formas mencionadas",
                "Causa-efeito óbvio"
            ],
            "example": """Narrador: 'Era uma vez uma família especial.'
Sara: 'Bom dia, meu filhinho! Quer leite?'
Isaac: 'Quero sim, mamãe! Leite quentinho!'
Abraão: 'Vamos passear hoje, Isaac.'
Isaac: 'Passear? Para onde, papai?'
Abraão: 'Vamos à montanha grande e bonita!'"""
        },
        "6-9": {
            "name": "Infantil (6-9 anos)",
            "words_per_line": "8-12 palavras",
            "vocabulary": "SIMPLES - Vocabulário expandido, verbos de ação, adjetivos descritivos",
            "sentence_structure": "Frases compostas simples. Pode usar 'porque', 'mas', 'então'",
            "repetition": "MODERADA - Repetir conceitos importantes",
            "rhythm": "MODERADO - Diálogos ágeis com pausas narrativas",
            "emotions": "Nomeadas e explicadas (nervoso, animado, preocupado, orgulhoso)",
            "questions": "Incluir 'por que', 'como'",
            "techniques": [
                "Pequenas lições morais",
                "Humor leve",
                "Desafios simples",
                "Amizade e trabalho em equipe",
                "Descobertas e aprendizado"
            ],
            "example": """Abraão: 'Isaac, precisamos fazer uma jornada especial hoje.'
Isaac: 'Uma jornada? Que legal! Vamos ver coisas novas?'
Sara: 'Cuidem um do outro, está bem? A mamãe vai ficar com saudades.'
Isaac: 'Não se preocupe, mamãe! O papai vai cuidar de mim!'
Narrador: 'E assim começou a aventura de pai e filho pela montanha misteriosa.'"""
        },
        "10-13": {
            "name": "Pré-adolescente (10-13 anos)",
            "words_per_line": "12-18 palavras",
            "vocabulary": "INTERMEDIÁRIO - Vocabulário rico, metáforas simples, conceitos abstratos introduzidos",
            "sentence_structure": "Frases complexas. Pode usar subordinadas simples.",
            "repetition": "BAIXA - Apenas para ênfase dramática",
            "rhythm": "DINÂMICO - Alternância entre diálogos rápidos e pausas reflexivas",
            "emotions": "Complexas e sutis (conflito interno, dúvida, esperança, determinação)",
            "questions": "Filosóficas e reflexivas",
            "techniques": [
                "Dilemas morais",
                "Simbolismo básico",
                "Crescimento pessoal",
                "Conflitos e resoluções",
                "Inspiração e coragem"
            ],
            "example": """Abraão: 'Filho, às vezes Deus nos pede coisas que não entendemos completamente.'
Isaac: 'Pai, eu confio em você. Se você diz que precisamos ir, então vamos juntos.'
Sara: 'A fé não é sobre ter todas as respostas, Abraão. É sobre confiar mesmo nas perguntas.'
Narrador: 'Enquanto caminhavam, pai e filho carregavam mais do que apenas suas mochilas. Carregavam uma promessa antiga e um futuro incerto.'"""
        },
        "14-17": {
            "name": "Adolescente (14-17 anos)",
            "words_per_line": "15-25 palavras",
            "vocabulary": "AVANÇADO - Vocabulário sofisticado, metáforas complexas, conceitos filosóficos",
            "sentence_structure": "Livre. Subordinadas, elipses, fragmentos intencionais.",
            "repetition": "MÍNIMA - Apenas para efeito retórico",
            "rhythm": "CINEMATOGRÁFICO - Silêncios carregados, subtext",
            "emotions": "Ambíguas e layered (amor e raiva simultâneos, alegria melancólica)",
            "questions": "Existenciais e provocativas",
            "techniques": [
                "Ambiguidade moral",
                "Simbolismo profundo",
                "Ironia e sarcasmo sutil",
                "Conflitos internos intensos",
                "Realismo emocional"
            ],
            "example": """Abraão: 'Cada passo que dou me afasta da tenda, mas me aproxima de algo que não consigo nomear.'
Isaac: 'Pai... há algo que você não está me contando, não é? Sinto isso no seu silêncio.'
Sara: 'Vá, Abraão. Mas saiba que quando você voltar, nenhum de nós será o mesmo.'
Narrador: 'A montanha os aguardava impassível, testemunha silenciosa de um teste que atravessaria gerações.'"""
        },
        "18-25": {
            "name": "Jovem adulto (18-25 anos)",
            "words_per_line": "20-30 palavras",
            "vocabulary": "SOFISTICADO - Sem restrições, referências culturais, jargões contextuais",
            "sentence_structure": "Totalmente livre e variada",
            "repetition": "Apenas estilística",
            "rhythm": "NATURAL - Como conversas reais",
            "emotions": "Complexas e contraditórias",
            "questions": "Retóricas e filosóficas profundas",
            "techniques": [
                "Subtexto pesado",
                "Referências intertextuais",
                "Crítica social sutil",
                "Psicologia profunda",
                "Realismo cru"
            ],
            "example": """Abraão: 'Há momentos na vida onde a fé deixa de ser conforto e se torna o próprio abismo que nos desafia a saltar.'
Isaac: 'Você está me levando para algum lugar, pai, ou está fugindo de algo que deixamos para trás?'
Sara: 'O amor verdadeiro não é sobre segurar. É sobre soltar e confiar que o que é seu voltará transformado.'"""
        },
        "25+": {
            "name": "Adulto (25+ anos)",
            "words_per_line": "25-35 palavras",
            "vocabulary": "COMPLETO - Sem limitações, literário quando apropriado",
            "sentence_structure": "Complexa e variada, pode ser lírica",
            "repetition": "Artística e intencional",
            "rhythm": "SOFISTICADO - Usa silêncios e pausas como ferramenta narrativa",
            "emotions": "Nuançadas com múltiplas camadas simultâneas",
            "questions": "Profundas, podem ficar sem resposta",
            "techniques": [
                "Simbolismo multicamadas",
                "Filosofia e teologia",
                "Ambiguidade intencional",
                "Beleza lírica",
                "Profundidade psicológica"
            ],
            "example": """Abraão: 'Quando Deus fala, Ele não pede apenas obediência. Ele pede que entreguemos a própria lógica que sustenta nosso mundo, que sacrifiquemos não apenas o que amamos, mas a própria capacidade de entender por que amamos.'
Isaac: 'Pai, há uma diferença entre o que sabemos e o que suportamos saber. Hoje, caminhamos nessa fronteira.'
Sara: 'Cada patriarca, cada matriarca antes de nós enfrentou seu próprio Moriá. O nosso só parece impossível porque é nosso.'"""
        },
        "all": {
            "name": "Todas as idades",
            "words_per_line": "10-15 palavras",
            "vocabulary": "CLARO mas não simplificado - Acessível mas rico",
            "sentence_structure": "Variada mas compreensível",
            "repetition": "Moderada para conceitos-chave",
            "rhythm": "EQUILIBRADO - Dinâmico sem ser frenético",
            "emotions": "Universais e facilmente identificáveis",
            "questions": "Relevantes para múltiplas idades",
            "techniques": [
                "Camadas narrativas (crianças veem ação, adultos veem significado)",
                "Humor universal",
                "Temas atemporais",
                "Emoção genuína",
                "Respeito pela inteligência da audiência"
            ],
            "example": """Narrador: 'Esta é uma história sobre fé, família e o poder do amor que transcende o entendimento.'
Abraão: 'Isaac, hoje vamos fazer algo que vai mudar nossa história para sempre.'
Sara: 'Vocês dois são meu mundo inteiro. Voltem seguros para mim.'
Isaac: 'Não se preocupe, mamãe. Papai e eu cuidamos um do outro!'"""
        }
    },
    "en": {
        "2-5": {
            "name": "Preschool (2-5 years)",
            "words_per_line": "3-5 words",
            "vocabulary": "ULTRA SIMPLE - Concrete everyday words (mommy, daddy, ball, sun)",
            "sentence_structure": "Short declarative sentences. No subordinates.",
            "repetition": "HIGH - Repeat keywords 3-4 times per scene",
            "rhythm": "VERY SLOW - Long pauses between lines (2-3 seconds)",
            "emotions": "EXAGGERATED - Use intensifiers (so happy!, very sad!, so pretty!)",
            "questions": "Simple and direct (What is? Where go? Who is?)",
            "techniques": [
                "Use LOTS of onomatopoeia (tweet-tweet, woof-woof, meow)",
                "Use affectionate diminutives (daddy, mommy, baby)",
                "Use frequent interjections (Wow!, Look!, Yay!, Oh!)",
                "Narrator repeats character actions",
                "Rhetorical questions for engagement (See? Want to see?)"
            ],
            "example": """Sarah: 'Look, Isaac! Look!'
Isaac: 'What, Mama?'
Sarah: 'Bird! Blue bird!'
Isaac: 'Tweet-tweet! Bird tweet-tweet!'
Abraham: 'So pretty, son!'
Isaac: 'Daddy, bird flying!'
Narrator: 'The bird flies high, high, high in the blue sky!'"""
        },
        "3-6": {
            "name": "Preschool (3-6 years)",
            "words_per_line": "5-8 words",
            "vocabulary": "VERY SIMPLE - Concrete objects, basic actions, primary colors",
            "sentence_structure": "Simple sentences. Up to 2 coordinated clauses.",
            "repetition": "HIGH - Repeat key concepts 2-3 times",
            "rhythm": "SLOW - Noticeable pauses between dialogues",
            "emotions": "Clear and named (happy, sad, scared, love)",
            "questions": "Simple with 'what', 'where', 'who'",
            "techniques": [
                "Frequent onomatopoeia",
                "Simple occasional rhymes",
                "Basic counting (one, two, three)",
                "Colors and shapes mentioned",
                "Obvious cause-effect"
            ],
            "example": """Narrator: 'Once upon a time there was a special family.'
Sarah: 'Good morning, my little one! Want milk?'
Isaac: 'Yes, Mama! Warm milk!'
Abraham: 'We'll go for a walk today, Isaac.'
Isaac: 'A walk? Where, Daddy?'
Abraham: 'To the big beautiful mountain!'"""
        }
    }
}


def _get_dialogue_age_profile(target_audience: str, lang: str = "pt") -> Dict:
    """Get detailed dialogue profile for target age group"""
    profiles = DIALOGUE_AGE_PROFILES.get(lang, DIALOGUE_AGE_PROFILES["pt"])
    
    # Map common age formats to profile keys
    age_mapping = {
        "2-5": "2-5",
        "3-6": "3-6",
        "6-9": "6-9", 
        "10-13": "10-13",
        "14-17": "14-17",
        "18-25": "18-25",
        "25+": "25+",
        "all": "all"
    }
    
    profile_key = age_mapping.get(target_audience, "all")
    return profiles.get(profile_key, profiles["all"])

