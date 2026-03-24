"""Directed Studio v2 — Screenwriter Chat + Multi-Scene Video Production."""
import uuid
import base64
import os
import asyncio
import urllib.request
import litellm
import threading
import subprocess
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI client to NOT retry internally (we handle retries ourselves)
os.environ["OPENAI_MAX_RETRIES"] = "0"

from core.deps import supabase, get_current_user, get_current_tenant, logger
from pipeline.config import STORAGE_BUCKET, EMERGENT_PROXY_URL, ELEVENLABS_VOICES, MUSIC_LIBRARY

router = APIRouter(prefix="/api/studio", tags=["studio"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


# ── Direct Sora 2 Client (no proxy) ──

from core.llm import DirectSora2Client


# ── Helpers ──

def _get_settings(tenant_id: str) -> dict:
    r = supabase.table("tenants").select("settings").eq("id", tenant_id).single().execute()
    return r.data.get("settings", {}) if r.data else {}

def _save_settings(tenant_id: str, settings: dict):
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("tenants").update({"settings": settings}).eq("id", tenant_id).execute()

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

def _upload_to_storage(file_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
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
            if text[i] == '{': depth += 1
            elif text[i] == '}': depth -= 1
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
  "character_bible": {"CharacterName": "CANONICAL 50-word English appearance. MUST match avatar analysis. Species, body type, exact colors, textures, clothing, unique marks. Used VERBATIM in every scene with this character."},
  "location_bible": {"LocationKey": "40-word English description. Landscape, terrain, vegetation, architecture, sky, ambient details."},
  "scene_directions": [{"scene": 1, "time_of_day": "morning|afternoon|sunset|night", "location_key": "from location_bible", "camera_flow": "camera movement description", "transition_note": "visual link to previous/next scene", "ambient": "environmental sounds"}],
  "music_plan": [{"scenes": [1,2,3], "mood": "description", "category": "cinematic|epic|gentle|tense|triumphant", "intensity": "low|medium|high"}],
  "voice_plan": [{"scene": 1, "tone": "warm|whisper|powerful|dramatic|sad", "pace": "slow|medium|fast"}]
}

CRITICAL RULES:
- character_bible MUST derive from avatar visual analysis when available — avatar is TRUTH
- If characters are animals, describe ONLY animal features (fur, feathers, hooves, snouts, tails) — NEVER human features
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
        project["status"] = "error"
        project["error"] = "Produção interrompida"
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": project["status"]}



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
- Language: {lang}"""


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

        system = SCREENWRITER_SYSTEM_PHASE1.replace("{lang}", lang)
        user_prompt = f"""Previous conversation:
{history_text}

Current request: {message}

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

            project["scenes"] = all_scenes
            project["characters"] = all_characters
            project["agents_output"] = project.get("agents_output", {})
            project["agents_output"]["screenwriter"] = {
                "title": parsed.get("title", ""),
                "research_notes": parsed.get("research_notes", ""),
                "narration": parsed.get("narration", ""),
            }
            assistant_text = f"**{parsed.get('title', 'Roteiro')}** — {len(all_scenes)} cenas\n\n"
            for s in all_scenes:
                assistant_text += f"**CENA {s.get('scene_number','')}** ({s.get('time_start','')}-{s.get('time_end','')}) — {s.get('title','')}\n"
                assistant_text += f"_{s.get('description','')}_\n"
                if s.get('dialogue'):
                    assistant_text += f'"{s["dialogue"]}"\n'
                assistant_text += f"Personagens: {', '.join(s.get('characters_in_scene',[]))}\n\n"
            assistant_text += f"\n**Personagens identificados:** {', '.join(c.get('name','') for c in all_characters)}"
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


def _save_scene_video(tenant_id: str, project_id: str, scene_num: int, video_url: str, total: int):
    """Save a completed scene video immediately for real-time preview."""
    try:
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
        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
    except Exception:
        pass


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
        style_hint = STYLE_PROMPTS.get(visual_style, STYLE_PROMPTS["animation"])

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

Return ONLY JSON: {{"sora_prompt": "ONE detailed English paragraph for Sora 2, max 250 words"}}

RULES:
- START with the style anchors text verbatim
- Describe characters by EXACT PHYSICAL APPEARANCE from character descriptions below — NEVER use character names in the prompt
- Include: environment details, lighting matching the time of day, atmospheric elements, character actions/expressions, camera movement
- Maintain visual continuity with transition notes
- The sora_prompt MUST be in ENGLISH"""

            director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}

CHARACTERS IN THIS SCENE (describe by appearance, NOT by name):
{char_descs}

LOCATION: {loc_desc}
TIME OF DAY: {time_day} — Light/Colors: {time_light}
CAMERA: {cam_flow}
CONTINUITY: {trans_note}"""

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
            """PHASE B — Sora 2 video render with retries and budget awareness."""
            scene_num = directed_scene["scene_number"]

            if directed_scene.get("cached"):
                _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                return {"scene_number": scene_num, "url": completed_videos[scene_num], "type": "video", "duration": 12}

            if budget_exhausted.is_set():
                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

            sora_prompt = directed_scene["sora_prompt"]
            chars_in_scene = scene.get("characters_in_scene", [])

            ref_path = _create_composite_avatar(chars_in_scene, char_avatars, avatar_cache)

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

        # ══ PHASE B: ALL SORA RENDERS (queued — 5 concurrent slots) ══
        logger.info(f"Studio [{project_id}]: PHASE B — Queueing {total} Sora 2 renders (5 slots)")

        scene_videos = []
        scene_map = {s.get("scene_number", i+1): s for i, s in enumerate(scenes)}

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
                try: os.unlink(path)
                except OSError: pass

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
    import shutil

    # Ensure FFmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        logger.warning(f"Studio [{project_id}]: FFmpeg not found, attempting install...")
        subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], capture_output=True, timeout=60)

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

    # First try stream copy (fastest, no quality loss)
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)

    if result.returncode != 0:
        # Try re-encoding if copy fails
        cmd_reencode = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        subprocess.run(cmd_reencode, capture_output=True, timeout=300)

    # Check file size — if > 45MB, re-encode with higher compression
    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    logger.info(f"Studio [{project_id}]: Concatenated video size: {file_size//1024//1024}MB ({file_size//1024}KB)")

    if file_size > 45 * 1024 * 1024:  # > 45MB
        compressed_path = f"{tmpdir}/final_{project_id}_compressed.mp4"
        cmd_compress = [
            "ffmpeg", "-y", "-i", output_path,
            "-c:v", "libx264", "-preset", "medium", "-crf", "32",
            "-vf", "scale=1280:720",
            "-c:a", "aac", "-b:a", "96k",
            "-movflags", "+faststart",
            compressed_path
        ]
        result = subprocess.run(cmd_compress, capture_output=True, timeout=300)
        if result.returncode == 0 and os.path.exists(compressed_path):
            new_size = os.path.getsize(compressed_path)
            logger.info(f"Studio [{project_id}]: Compressed {file_size//1024//1024}MB → {new_size//1024//1024}MB")
            output_path = compressed_path
            file_size = new_size

    # If still too large (> 48MB), skip upload and return None
    if file_size > 48 * 1024 * 1024:
        logger.warning(f"Studio [{project_id}]: Final video still too large ({file_size//1024//1024}MB), skipping concat upload")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    with open(output_path, 'rb') as f:
        video_bytes = f.read()

    filename = f"studio/{project_id}_final.mp4"
    url = _upload_to_storage(video_bytes, filename, "video/mp4")

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
            t_v = _time.time()
            try:
                gen_kwargs = {"prompt": sora_prompt[:1000], "model": "sora-2", "size": "1280x720", "duration": 12, "max_wait_time": 600}
                if ref_path:
                    gen_kwargs["image_path"] = ref_path

                logger.info(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1}/3")
                video_bytes = video_gen.text_to_video(**gen_kwargs)
                elapsed = _time.time() - t_v

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
                            try: os.unlink(p)
                            except OSError: pass
                    if ref_path and ref_path not in avatar_cache.values():
                        try: os.unlink(ref_path)
                        except OSError: pass
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
                try: os.unlink(p)
                except OSError: pass
        if ref_path and ref_path not in avatar_cache.values():
            try: os.unlink(ref_path)
            except OSError: pass

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
                try: os.unlink(p)
                except OSError: pass

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
        except:
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

def _generate_narration_audio(text: str, voice_id: str, stability: float, similarity: float, style_val: float) -> bytes:
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
    audio_gen = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        voice_settings=voice_settings,
    )
    audio_bytes = b""
    for chunk in audio_gen:
        audio_bytes += chunk
    return audio_bytes


def _run_narration_background(tenant_id: str, project_id: str, voice_id: str, stability: float, similarity: float, style_val: float):
    """Background: generate narration for each scene and save to project."""
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        lang = project.get("language", "pt")

        _update_project_field(tenant_id, project_id, {
            "narration_status": {"phase": "generating_script", "done": 0, "total": len(scenes)},
        })

        # Generate narration scripts via Claude
        narration_system = f"""You are a NARRATOR for cinematic storytelling. Given scenes, write compelling narration text for EACH scene.
Rules:
- Each scene narration is MAX 25 words (fits 12 seconds)
- Be dramatic, evocative, emotional
- Use the scene dialogue and description as basis
- Language: {lang}
- Output ONLY valid JSON array: [{{"scene_number": 1, "narration": "text..."}}]"""

        scene_summaries = "\n".join([
            f"Scene {s.get('scene_number', i+1)}: {s.get('title','')} — {s.get('description','')} — Dialogue: {s.get('dialogue','')}"
            for i, s in enumerate(scenes)
        ])

        script_result = _call_claude_sync(narration_system, f"Scenes:\n{scene_summaries}")

        # Parse narration scripts
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

        # Generate audio for each scene
        narration_outputs = []
        for i, narr in enumerate(narrations):
            scene_num = narr.get("scene_number", i + 1)
            text = narr.get("narration", "")
            if not text.strip():
                narration_outputs.append({"scene_number": scene_num, "text": "", "audio_url": None})
                continue
            try:
                audio_bytes = _generate_narration_audio(text, voice_id, stability, similarity, style_val)
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

    avg = lambda lst: round(sum(lst) / len(lst)) if lst else 0

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
        if error_rate > 30:
            recs.append({"type": "critical", "text": f"Taxa de erro alta: {error_rate:.0f}%. Verificar estabilidade da conexão Claude/Sora 2."})

    agent_times = [p["agent_seconds"] for p in productions if p["agent_seconds"]]
    if agent_times and max(agent_times) > 120:
        recs.append({"type": "warning", "text": f"Agentes lentos (máx {max(agent_times)}s). Pipeline v3 com equipas paralelas reduz para ~15s."})

    video_times = [p["video_seconds"] for p in productions if p["video_seconds"]]
    if video_times and max(video_times) > 600:
        recs.append({"type": "info", "text": f"Sora 2 é o gargalo principal (máx {max(video_times)//60}min). Considerar reduzir duração de 12s→8s para cenas simples."})

    v3_count = len([p for p in productions if p["pipeline_version"] == "v3"])
    if v3_count == 0:
        recs.append({"type": "info", "text": "Nenhuma produção v3 concluída ainda. Pipeline paralelo reduzirá tempo ~60%."})

    if not recs:
        recs.append({"type": "success", "text": "Pipeline optimizado. Todas as produções estão eficientes."})
    return recs
