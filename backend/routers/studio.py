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

from core.deps import supabase, get_current_user, get_current_tenant, EMERGENT_KEY, logger
from pipeline.config import STORAGE_BUCKET, EMERGENT_PROXY_URL, ELEVENLABS_VOICES, MUSIC_LIBRARY

router = APIRouter(prefix="/api/studio", tags=["studio"])

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


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
    """Call Claude via emergentintegrations (async — for API endpoints). Retries on transient errors."""
    import time as _time
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    for attempt in range(3):
        try:
            chat = LlmChat(
                api_key=EMERGENT_KEY,
                session_id=f"studio-{uuid.uuid4().hex[:6]}",
                system_message=system_prompt
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            response = await chat.send_message(UserMessage(text=user_prompt))
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            if attempt < 2 and any(code in str(e) for code in ["502", "503", "529", "timeout", "disconnected"]):
                logger.warning(f"Claude attempt {attempt+1} failed: {e}. Retrying...")
                await asyncio.sleep(5 * (attempt + 1))
                continue
            raise


def _call_claude_sync(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
    """Call Claude via emergentintegrations (sync — for background threads). Retries on transient errors."""
    import asyncio
    import time as _time
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    async def _run():
        for attempt in range(3):
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"studio-{uuid.uuid4().hex[:6]}",
                    system_message=system_prompt
                ).with_model("anthropic", "claude-sonnet-4-5-20250929")
                response = await chat.send_message(UserMessage(text=user_prompt))
                return response.text if hasattr(response, 'text') else str(response)
            except Exception as e:
                if attempt < 2 and any(code in str(e) for code in ["502", "503", "529", "timeout", "disconnected"]):
                    logger.warning(f"Claude sync attempt {attempt+1} failed: {e}. Retrying...")
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                raise

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


def _parse_json(text):
    import json
    if '{' in text:
        try:
            start = text.index('{')
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{': depth += 1
                elif text[i] == '}': depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
            return json.loads(text[start:text.rindex('}')+1])
        except:
            pass
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

class ChatMessage(BaseModel):
    project_id: Optional[str] = None
    message: str = ""
    language: str = "pt"

class StartProductionRequest(BaseModel):
    project_id: str
    video_duration: int = 12
    character_avatars: dict = {}  # {character_name: avatar_url}

class GenerateAvatarRequest(BaseModel):
    character_name: str
    character_description: str
    style: str = "cinematic"


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
        "chat_history": [],
        "agents_output": {},
        "agent_status": {},
        "outputs": [],
        "milestones": [{"key": "project_created", "label": "Projecto criado", "done": True, "at": now}],
        "status": "draft",
        "error": None,
        "language": req.language,
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
        "outputs": project.get("outputs", []),
        "milestones": project.get("milestones", []),
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


# ── STEP 1: Screenwriter Chat ──

SCREENWRITER_SYSTEM = """You are a MASTER SCREENWRITER and RESEARCHER for cinema and advertising.

YOUR ROLE:
1. When the user describes a story, you DEEPLY RESEARCH the topic using your knowledge
2. For biblical stories: use EXACT biblical passages, real names, real events
3. For historical stories: use real historical facts
4. Create a COMPLETE screenplay divided into scenes of EXACTLY 12 seconds each

OUTPUT FORMAT — You MUST return valid JSON:
{{
  "title": "Story Title",
  "total_scenes": N,
  "characters": [
    {{"name": "Character Name", "description": "Physical appearance for avatar generation", "age": "young/adult/old", "role": "protagonist/supporting"}}
  ],
  "scenes": [
    {{
      "scene_number": 1,
      "time_start": "0:00",
      "time_end": "0:12",
      "title": "Scene Title",
      "description": "Visual description of what happens",
      "dialogue": "Character dialogue for this scene",
      "characters_in_scene": ["Character1", "Character2"],
      "emotion": "dramatic/joyful/tense/peaceful",
      "camera": "wide shot/close up/medium shot",
      "transition": "fade/cut/dissolve"
    }}
  ],
  "research_notes": "Sources and references used",
  "narration": "Brief narrator text for context"
}}

RULES:
- Each scene is EXACTLY 12 seconds
- Plan smooth transitions between scenes
- Describe characters physically so avatars can be generated
- Be faithful to source material (bible, history, etc.)
- Language: {lang}"""


def _run_screenwriter_background(tenant_id: str, project_id: str, message: str, lang: str):
    """Background thread: call Claude screenwriter and save result."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        chat_history = project.get("chat_history", [])

        history_text = "\n".join([
            f"{'USER' if m['role']=='user' else 'SCREENWRITER'}: {m['text'][:500]}"
            for m in chat_history[-6:]
        ])

        system = SCREENWRITER_SYSTEM.replace("{lang}", lang)
        user_prompt = f"""Previous conversation:
{history_text}

Current request: {message}

Create or update the screenplay based on this conversation. Return the complete screenplay as JSON."""

        result = _call_claude_sync(system, user_prompt)
        parsed = _parse_json(result)

        # Re-read project (may have changed)
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        chat_history = project.get("chat_history", [])

        if parsed:
            project["scenes"] = parsed.get("scenes", [])
            project["characters"] = parsed.get("characters", [])
            project["agents_output"] = project.get("agents_output", {})
            project["agents_output"]["screenwriter"] = {
                "title": parsed.get("title", ""),
                "research_notes": parsed.get("research_notes", ""),
                "narration": parsed.get("narration", ""),
            }
            assistant_text = f"**{parsed.get('title', 'Roteiro')}** — {parsed.get('total_scenes', len(parsed.get('scenes',[])))} cenas\n\n"
            for s in parsed.get("scenes", []):
                assistant_text += f"**CENA {s.get('scene_number','')}** ({s.get('time_start','')}-{s.get('time_end','')}) — {s.get('title','')}\n"
                assistant_text += f"_{s.get('description','')}_\n"
                if s.get('dialogue'):
                    assistant_text += f'"{s["dialogue"]}"\n'
                assistant_text += f"Personagens: {', '.join(s.get('characters_in_scene',[]))}\n\n"
            assistant_text += f"\n**Personagens identificados:** {', '.join(c.get('name','') for c in parsed.get('characters',[]))}"
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

        logger.info(f"Studio [{project_id}]: Screenwriter done — {len(project.get('scenes',[]))} scenes")

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


# ── STEP 3: Multi-Scene Production Pipeline ──

def _run_multi_scene_production(tenant_id: str, project_id: str, character_avatars: dict = None):
    """Background: run 3 agents per scene, then generate videos.
    character_avatars: dict mapping character name -> avatar URL (from frontend)
    """
    import json as json_mod
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        characters = project.get("characters", [])
        lang = project.get("language", "pt")
        total = len(scenes)
        char_avatars = character_avatars or {}

        if total == 0:
            _update_project_field(tenant_id, project_id, {"status": "error", "error": "No scenes to produce"})
            return

        _update_project_field(tenant_id, project_id, {
            "status": "running_agents",
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "photography"}
        })

        scene_prompts = []

        for i, scene in enumerate(scenes):
            scene_num = i + 1
            logger.info(f"Studio [{project_id}]: Processing scene {scene_num}/{total}")

            # ── Photography Director ──
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": scene_num, "total_scenes": total, "phase": "photography"}
            })

            photo_system = """You are a DIRECTOR OF PHOTOGRAPHY. Create the visual composition for this scene.

IMPORTANT RULES:
1. If characters have AVATAR REFERENCES, describe the characters EXACTLY matching their avatar appearance
2. Maintain VISUAL CONSISTENCY across all scenes — same characters must look identical
3. Include the art style specified (cartoon, realistic, anime, etc.)
4. The sora_prompt must be a SINGLE detailed English paragraph for Sora 2 video generation

Output ONLY valid JSON: {"visual_direction": "...", "camera_angle": "...", "lighting": "...", "art_style": "...", "sora_prompt": "single detailed English paragraph describing the exact visual scene with character appearances matching their avatars"}"""

            chars_in_scene = scene.get("characters_in_scene", [])
            char_descriptions = []
            for ch in characters:
                if ch.get("name") in chars_in_scene:
                    desc = f"{ch['name']}: {ch.get('description','')}"
                    if ch.get("name") in char_avatars:
                        desc += " [HAS AVATAR REFERENCE IMAGE — maintain this exact visual appearance]"
                    char_descriptions.append(desc)

            # Detect art style from briefing
            briefing = project.get("briefing", "")
            style_hint = ""
            briefing_lower = briefing.lower()
            if any(w in briefing_lower for w in ["cartoon", "desenho", "animado", "criança", "infantil", "kids"]):
                style_hint = "\nART STYLE: Colorful cartoon/animated style for children. Warm, friendly, vibrant colors."
            elif any(w in briefing_lower for w in ["anime", "mangá"]):
                style_hint = "\nART STYLE: Japanese anime style with expressive characters."
            elif any(w in briefing_lower for w in ["realistic", "realista", "cinema"]):
                style_hint = "\nART STYLE: Cinematic photorealistic style."

            photo_prompt = f"""Scene {scene_num}: {scene.get('title','')}
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}
Camera: {scene.get('camera','')}
Characters: {'; '.join(char_descriptions)}{style_hint}
Transition to next: {scene.get('transition','')}"""

            photo_result = _call_claude_sync(photo_system, photo_prompt)
            photo_data = _parse_json(photo_result) or {"sora_prompt": scene.get("description", "")}

            # ── Music Director (once for all scenes) ──
            if i == 0:
                _update_project_field(tenant_id, project_id, {
                    "agent_status": {"current_scene": scene_num, "total_scenes": total, "phase": "music"}
                })
                avail = ", ".join(MUSIC_LIBRARY.keys())
                music_system = f"""You are a MUSIC DIRECTOR. Define the musical atmosphere for this story.
Output ONLY JSON: {{"mood": "...", "recommended_genre": "...", "tempo": "...", "selected_category": "one of: {avail}"}}"""
                music_result = _call_claude_sync(music_system, f"Story: {project.get('briefing','')}\nScenes: {total}\nTone: {scene.get('emotion','')}")
                music_data = _parse_json(music_result) or {"mood": "cinematic"}

                _update_project_field(tenant_id, project_id, {
                    "agents_output": {
                        **project.get("agents_output", {}),
                        "music_director": music_data,
                    }
                })

            # ── Audio Director ──
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": scene_num, "total_scenes": total, "phase": "audio"}
            })

            audio_system = """You are an AUDIO DIRECTOR. Define sound design for this scene.
Output ONLY JSON: {"sound_effects": ["..."], "voice_tone": "...", "ambient": "..."}"""
            audio_result = _call_claude_sync(audio_system, photo_prompt)
            audio_data = _parse_json(audio_result) or {"sound_effects": []}

            # Save the Sora prompt for this scene + identify reference avatar
            sora_prompt = photo_data.get("sora_prompt", scene.get("description", ""))

            # Find the best reference avatar for this scene (first character with avatar)
            reference_avatar_url = None
            for ch_name in chars_in_scene:
                if ch_name in char_avatars and char_avatars[ch_name]:
                    reference_avatar_url = char_avatars[ch_name]
                    break

            scene_prompts.append({
                "scene_number": scene_num,
                "sora_prompt": sora_prompt,
                "photography": photo_data,
                "audio": audio_data,
                "transition": scene.get("transition", "cut"),
                "reference_avatar_url": reference_avatar_url,
            })

        # Save all scene analysis
        _update_project_field(tenant_id, project_id, {
            "agents_output": {
                **project.get("agents_output", {}),
                "scene_prompts": scene_prompts,
            },
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_videos"}
        })

        logger.info(f"Studio [{project_id}]: All agents done. Generating {total} videos...")

        # Add milestone for agents completion
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            _add_milestone(project, "agents_complete", f"Agentes de cinema concluídos — {total} cenas processadas")
            _save_project(tenant_id, settings, projects)

        # ── Generate Videos (one per scene) ──
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

        video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
        scene_videos = []

        for i, sp in enumerate(scene_prompts):
            scene_num = sp["scene_number"]
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": scene_num, "total_scenes": total, "phase": "generating_video",
                                 "videos_done": len(scene_videos)}
            })

            logger.info(f"Studio [{project_id}]: Generating video for scene {scene_num}/{total}")

            try:
                # Download reference avatar if available
                ref_image_path = None
                if sp.get("reference_avatar_url"):
                    try:
                        avatar_url = sp["reference_avatar_url"]
                        # Resolve relative URLs
                        if avatar_url.startswith("/"):
                            supa_url = os.environ.get("SUPABASE_URL", "")
                            avatar_url = f"{supa_url}/storage/v1/object/public{avatar_url}"
                        ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        urllib.request.urlretrieve(avatar_url, ref_file.name)
                        ref_image_path = ref_file.name
                        logger.info(f"Studio [{project_id}]: Scene {scene_num} using avatar reference image")
                    except Exception as ae:
                        logger.warning(f"Studio [{project_id}]: Could not download avatar reference: {ae}")
                        ref_image_path = None

                gen_kwargs = {
                    "prompt": sp["sora_prompt"][:1000],
                    "model": "sora-2",
                    "size": "1280x720",
                    "duration": 12,
                    "max_wait_time": 600,
                }
                if ref_image_path:
                    gen_kwargs["image_path"] = ref_image_path

                video_bytes = video_gen.text_to_video(**gen_kwargs)
                if video_bytes:
                    filename = f"studio/{project_id}_scene_{scene_num}.mp4"
                    video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                    scene_videos.append({
                        "scene_number": scene_num,
                        "url": video_url,
                        "type": "video",
                        "duration": 12,
                    })
                    logger.info(f"Studio [{project_id}]: Scene {scene_num} video uploaded")
                else:
                    logger.warning(f"Studio [{project_id}]: Scene {scene_num} returned empty video")
                    scene_videos.append({"scene_number": scene_num, "url": None, "type": "video", "error": "empty"})
            except Exception as ve:
                logger.error(f"Studio [{project_id}]: Scene {scene_num} video error: {ve}")
                scene_videos.append({"scene_number": scene_num, "url": None, "type": "video", "error": str(ve)[:200]})
            finally:
                # Cleanup temp avatar file
                if ref_image_path:
                    try:
                        os.unlink(ref_image_path)
                    except OSError:
                        pass

        # ── Concatenate Videos ──
        successful_videos = [sv for sv in scene_videos if sv.get("url")]
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
                logger.error(f"Studio [{project_id}]: Concatenation error: {ce}")
        elif len(successful_videos) == 1:
            final_url = successful_videos[0]["url"]

        # ── Save Results ──
        outputs = []
        for sv in scene_videos:
            if sv.get("url"):
                outputs.append({
                    "id": uuid.uuid4().hex[:8],
                    "type": "video",
                    "url": sv["url"],
                    "scene_number": sv["scene_number"],
                    "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        if final_url and len(successful_videos) > 1:
            outputs.insert(0, {
                "id": uuid.uuid4().hex[:8],
                "type": "video",
                "url": final_url,
                "scene_number": 0,
                "label": "complete",
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
                "videos_done": len(successful_videos)
            }
            _save_project(tenant_id, settings, projects)

        logger.info(f"Studio [{project_id}]: COMPLETE! {len(successful_videos)} videos, final={final_url}")

        # Final milestones
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            _add_milestone(project, "videos_generated", f"Vídeos gerados — {len(successful_videos)} cenas")
            if final_url:
                _add_milestone(project, "film_complete", f"Filme completo — {len(successful_videos) * 12}s concatenado")
            _save_project(tenant_id, settings, projects)

    except Exception as e:
        logger.error(f"Studio [{project_id}] pipeline error: {e}")
        _update_project_field(tenant_id, project_id, {
            "status": "error",
            "error": str(e)[:500],
        })


def _concatenate_videos(scene_videos: list, project_id: str) -> str:
    """Download scene videos, concatenate with FFmpeg, upload result."""
    import tempfile
    tmpdir = tempfile.mkdtemp()
    files = []

    for i, sv in enumerate(scene_videos):
        local_path = f"{tmpdir}/scene_{i:03d}.mp4"
        urllib.request.urlretrieve(sv["url"], local_path)
        files.append(local_path)

    # Create concat file
    concat_file = f"{tmpdir}/concat.txt"
    with open(concat_file, 'w') as f:
        for fp in files:
            f.write(f"file '{fp}'\n")

    output_path = f"{tmpdir}/final_{project_id}.mp4"

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
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        subprocess.run(cmd_reencode, capture_output=True, timeout=300)

    with open(output_path, 'rb') as f:
        video_bytes = f.read()

    filename = f"studio/{project_id}_final.mp4"
    url = _upload_to_storage(video_bytes, filename, "video/mp4")

    # Cleanup
    import shutil
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

    project["status"] = "starting"
    project["error"] = None
    project["outputs"] = []
    total = len(project.get("scenes", []))
    project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "starting"}
    _add_milestone(project, "production_started", f"Produção iniciada — {total} cenas")
    if req.character_avatars:
        _add_milestone(project, "avatars_linked", f"Avatares vinculados — {len(req.character_avatars)} personagens")
    _save_project(tenant["id"], settings, projects)

    thread = threading.Thread(
        target=_run_multi_scene_production,
        args=(tenant["id"], req.project_id, req.character_avatars),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "project_id": req.project_id, "total_scenes": total}


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
        model="gemini/gemini-3-pro-image-preview",
        messages=[{"role": "user", "content": content}],
        api_key=EMERGENT_KEY, api_base=EMERGENT_PROXY_URL,
        custom_llm_provider="openai", modalities=["image", "text"],
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
