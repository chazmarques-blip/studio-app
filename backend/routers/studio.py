"""Directed Studio router — Background processing with polling for K8s proxy compatibility."""
import uuid
import base64
import os
import urllib.request
import litellm
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
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

def _upload_to_storage(file_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
    supabase.storage.from_(STORAGE_BUCKET).upload(
        filename, file_bytes,
        file_options={"content-type": content_type, "upsert": "true"}
    )
    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Call Claude via emergentintegrations."""
    import asyncio
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    async def _run():
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"studio-{uuid.uuid4().hex[:6]}",
            system_message=system_prompt
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        response = await chat.send_message(UserMessage(text=user_prompt))
        return response.text if hasattr(response, 'text') else str(response)

    return asyncio.run(_run())


# ── Models ──

class StudioProject(BaseModel):
    id: Optional[str] = None
    name: str = ""
    scene_type: str = "single_image"
    briefing: str = ""
    avatar_urls: list = []
    asset_urls: list = []
    voice_config: Optional[dict] = None
    music_config: Optional[dict] = None
    language: str = "pt"

class StartProductionRequest(BaseModel):
    project_id: str
    scene_prompt: str = ""
    video_duration: int = 8


# ── Projects CRUD ──

@router.post("/projects")
async def create_project(req: StudioProject, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    now = datetime.now(timezone.utc).isoformat()

    project = {
        "id": req.id or uuid.uuid4().hex[:12],
        "name": req.name or f"Studio {datetime.now(timezone.utc).strftime('%d/%m %H:%M')}",
        "scene_type": req.scene_type,
        "briefing": req.briefing,
        "avatar_urls": req.avatar_urls,
        "asset_urls": req.asset_urls,
        "voice_config": req.voice_config or {},
        "music_config": req.music_config or {},
        "language": req.language,
        "outputs": [],
        "agents_output": {},
        "agent_status": {},
        "status": "draft",
        "error": None,
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
    """Poll endpoint — returns current production status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": project.get("status"),
        "agent_status": project.get("agent_status", {}),
        "agents_output": project.get("agents_output", {}),
        "outputs": project.get("outputs", []),
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


# ── Background Production Pipeline ──

def _update_project_field(tenant_id: str, project_id: str, updates: dict):
    """Safely update specific fields on a project in Supabase."""
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


def _run_production_pipeline(tenant_id: str, project_id: str, briefing: str,
                              avatar_urls: list, lang: str, video_duration: int):
    """Background thread: runs 4 agents then generates video."""
    import json as json_mod

    def _parse_json(text):
        if '{' in text:
            try:
                return json_mod.loads(text[text.index('{'):text.rindex('}') + 1])
            except:
                pass
        return None

    try:
        avatar_count = len(avatar_urls)

        # ── Agent 1: Photography Director ──
        _update_project_field(tenant_id, project_id, {
            "status": "running_agents",
            "agent_status": {"photography": "running"}
        })

        photo_system = f"""You are a DIRECTOR OF PHOTOGRAPHY for cinema. Analyze the scene and define visual composition.
Output ONLY valid JSON: {{"visual_direction": "...", "camera_angle": "...", "lighting": "...", "color_palette": "...", "composition_notes": "...", "sora_prompt": "single English paragraph for AI video generation"}}"""
        photo_result = _call_claude(photo_system, f"Scene: {briefing}\nCharacters: {avatar_count}")
        photo_data = _parse_json(photo_result) or {"visual_direction": photo_result, "sora_prompt": briefing}

        _update_project_field(tenant_id, project_id, {
            "agent_status": {"photography": "done", "screenwriter": "running"},
            "agents_output": {"photography_director": photo_data}
        })
        logger.info(f"Studio [{project_id}]: Photography Director done")

        # ── Agent 2: Screenwriter ──
        screen_system = f"""You are a SCREENWRITER and RESEARCHER. Write dialogue with ACCURATE real-world content.
If the scene involves religious, historical, or scientific topics, use REAL sources (biblical texts, historical facts, etc.).
Language: {lang}. Output ONLY valid JSON: {{"dialogues": [{{"character": "...", "line": "...", "emotion": "...", "timing": "0:00-0:05"}}], "narration": "...", "research_notes": "..."}}"""
        screen_result = _call_claude(screen_system, f"Scene: {briefing}\nCharacters: {avatar_count}")
        screen_data = _parse_json(screen_result) or {"dialogues": [], "narration": screen_result}

        _update_project_field(tenant_id, project_id, {
            "agent_status": {"photography": "done", "screenwriter": "done", "music": "running"},
            "agents_output": {"photography_director": photo_data, "screenwriter": screen_data}
        })
        logger.info(f"Studio [{project_id}]: Screenwriter done")

        # ── Agent 3: Music Director ──
        avail = ", ".join(MUSIC_LIBRARY.keys())
        music_system = f"""You are a MUSIC DIRECTOR. Define the musical atmosphere.
Categories: {avail}. Language: {lang}. Output ONLY valid JSON: {{"recommended_genre": "...", "tempo": "...", "mood": "...", "instruments": "...", "selected_category": "one of: {avail}"}}"""
        music_result = _call_claude(music_system, f"Scene: {briefing}\nVisual: {photo_data.get('visual_direction', '')[:200]}")
        music_data = _parse_json(music_result) or {"recommended_genre": "cinematic", "mood": music_result}

        _update_project_field(tenant_id, project_id, {
            "agent_status": {"photography": "done", "screenwriter": "done", "music": "done", "audio": "running"},
            "agents_output": {"photography_director": photo_data, "screenwriter": screen_data, "music_director": music_data}
        })
        logger.info(f"Studio [{project_id}]: Music Director done")

        # ── Agent 4: Audio Director ──
        voices_info = [{"name": v.get("name", ""), "style": v.get("labels", {}).get("accent", "")} for v in ELEVENLABS_VOICES[:10]]
        audio_system = f"""You are an AUDIO DIRECTOR. Assign voices to characters.
Voices: {voices_info[:8]}. Language: {lang}. Output ONLY valid JSON: {{"voice_assignments": [{{"character": "...", "recommended_voice": "...", "tone_direction": "..."}}], "sound_effects": ["..."]}}"""
        audio_result = _call_claude(audio_system, f"Scene: {briefing}\nDialogues: {screen_data.get('dialogues', [])}")
        audio_data = _parse_json(audio_result) or {"voice_assignments": [], "audio_notes": audio_result}

        agents_output = {
            "photography_director": photo_data,
            "screenwriter": screen_data,
            "music_director": music_data,
            "audio_director": audio_data,
        }
        _update_project_field(tenant_id, project_id, {
            "agent_status": {"photography": "done", "screenwriter": "done", "music": "done", "audio": "done", "video": "running"},
            "agents_output": agents_output,
            "status": "generating_video",
        })
        logger.info(f"Studio [{project_id}]: All agents done, generating video...")

        # ── Generate Video with Sora 2 ──
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

        sora_prompt = photo_data.get("sora_prompt", briefing)
        narration = screen_data.get("narration", "")
        if narration:
            sora_prompt += f" Context: {narration[:200]}"

        duration = video_duration if video_duration in [4, 8, 12] else 8

        video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
        video_bytes = video_gen.text_to_video(
            prompt=sora_prompt[:1000],
            model="sora-2",
            size="1280x720",
            duration=duration,
            max_wait_time=600,
        )

        if not video_bytes:
            raise Exception("Video generation returned empty")

        filename = f"studio/video_{uuid.uuid4().hex[:8]}.mp4"
        video_url = _upload_to_storage(video_bytes, filename, "video/mp4")

        output = {
            "id": uuid.uuid4().hex[:8],
            "type": "video",
            "url": video_url,
            "prompt": sora_prompt[:500],
            "duration": duration,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["outputs"] = project.get("outputs", []) + [output]
            project["status"] = "complete"
            project["agents_output"] = agents_output
            project["agent_status"] = {"photography": "done", "screenwriter": "done", "music": "done", "audio": "done", "video": "done"}
            _save_project(tenant_id, settings, projects)

        logger.info(f"Studio [{project_id}]: Video generated! URL: {video_url[:60]}")

    except Exception as e:
        logger.error(f"Studio [{project_id}] pipeline error: {e}")
        _update_project_field(tenant_id, project_id, {
            "status": "error",
            "error": str(e)[:500],
            "agent_status": {"video": "error"},
        })


@router.post("/start-production")
async def start_production(req: StartProductionRequest, tenant=Depends(get_current_tenant)):
    """Start the full production pipeline in background. Returns immediately."""
    settings, projects, project = _get_project(tenant["id"], req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    briefing = req.scene_prompt or project.get("briefing", "")
    avatar_urls = project.get("avatar_urls", [])
    lang = project.get("language", "pt")
    duration = req.video_duration if req.video_duration in [4, 8, 12] else 8

    # Update status to starting
    project["status"] = "starting"
    project["error"] = None
    project["agent_status"] = {"photography": "pending", "screenwriter": "pending", "music": "pending", "audio": "pending", "video": "pending"}
    _save_project(tenant["id"], settings, projects)

    # Start background thread
    thread = threading.Thread(
        target=_run_production_pipeline,
        args=(tenant["id"], req.project_id, briefing, avatar_urls, lang, duration),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "project_id": req.project_id}


# ── Image Generation (fallback) ──

@router.post("/generate-image")
async def generate_directed_image(req: StartProductionRequest, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    avatar_urls = project.get("avatar_urls", [])
    briefing = project.get("briefing", "")
    agents = project.get("agents_output", {})
    photo_dir = agents.get("photography_director", {})

    prompt_text = photo_dir.get("sora_prompt", "") or f"Create a professional marketing image. Briefing: {briefing}. Characters: {len(avatar_urls)}. Cinematic quality, 16:9."

    content = [{"type": "text", "text": prompt_text}]
    for url in avatar_urls[:4]:
        try:
            req_obj = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            img_data = urllib.request.urlopen(req_obj, timeout=15).read()
            b64 = base64.b64encode(img_data).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        except Exception as e:
            logger.warning(f"Could not fetch avatar: {e}")

    response = litellm.completion(
        model="gemini/gemini-3-pro-image-preview",
        messages=[
            {"role": "system", "content": "Professional marketing image creator."},
            {"role": "user", "content": content}
        ],
        api_key=EMERGENT_KEY,
        api_base=EMERGENT_PROXY_URL,
        custom_llm_provider="openai",
        modalities=["image", "text"],
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

    output = {"id": uuid.uuid4().hex[:8], "type": "image", "url": public_url, "prompt": briefing, "created_at": datetime.now(timezone.utc).isoformat()}
    project["outputs"] = project.get("outputs", []) + [output]
    project["status"] = "complete"
    _save_project(tenant["id"], settings, projects)

    return {"image_url": public_url, "project": project}


# ── Voice & Music Library ──

@router.get("/voices")
async def get_voices(user=Depends(get_current_user)):
    return {"voices": ELEVENLABS_VOICES}

@router.get("/music-library")
async def get_music_library(user=Depends(get_current_user)):
    tracks = [{"id": k, **v} for k, v in MUSIC_LIBRARY.items()]
    return {"tracks": tracks}
