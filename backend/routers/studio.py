"""Directed Studio router — Projects stored in Supabase tenants.settings JSONB."""
import uuid
import base64
import urllib.request
import litellm
from io import BytesIO
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.deps import supabase, get_current_user, get_current_tenant, EMERGENT_KEY, logger
from pipeline.config import STORAGE_BUCKET, EMERGENT_PROXY_URL

router = APIRouter(prefix="/api/studio", tags=["studio"])


# ── Helpers ──

def _get_settings(tenant_id: str) -> dict:
    r = supabase.table("tenants").select("settings").eq("id", tenant_id).single().execute()
    return r.data.get("settings", {}) if r.data else {}

def _save_settings(tenant_id: str, settings: dict):
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("tenants").update({"settings": settings}).eq("id", tenant_id).execute()

def _upload_to_storage(file_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
    supabase.storage.from_(STORAGE_BUCKET).upload(
        filename, file_bytes,
        file_options={"content-type": content_type, "upsert": "true"}
    )
    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)


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

class GenerateSceneRequest(BaseModel):
    project_id: str
    scene_prompt: str = ""


# ── Projects CRUD (Supabase JSONB) ──

@router.post("/projects")
async def create_project(req: StudioProject, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    now = datetime.now(timezone.utc).isoformat()
    project_id = req.id or uuid.uuid4().hex[:12]

    project = {
        "id": project_id,
        "name": req.name or f"Studio {datetime.now(timezone.utc).strftime('%d/%m %H:%M')}",
        "scene_type": req.scene_type,
        "briefing": req.briefing,
        "avatar_urls": req.avatar_urls,
        "asset_urls": req.asset_urls,
        "voice_config": req.voice_config or {},
        "music_config": req.music_config or {},
        "language": req.language,
        "outputs": [],
        "status": "draft",
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


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    projects = [p for p in projects if p.get("id") != project_id]
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return {"status": "ok"}


# ── Image Generation (litellm + Gemini, same as pipeline) ──

@router.post("/generate-image")
async def generate_directed_image(req: GenerateSceneRequest, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    project = next((p for p in projects if p.get("id") == req.project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    avatar_urls = project.get("avatar_urls", [])
    briefing = project.get("briefing", "")
    scene_type = project.get("scene_type", "single_image")

    # Build multimodal prompt with avatar reference images
    prompt_text = f"""Create a professional marketing image for social media.
Scene type: {scene_type}
Number of characters: {len(avatar_urls)}
Briefing: {briefing}
{f'Additional scene direction: {req.scene_prompt}' if req.scene_prompt else ''}

RULES:
- Use the provided avatar image(s) as reference for the character(s) in the scene
- Maintain each character's visual identity (face, body, style)
- Create a dynamic, engaging composition
- Professional lighting and cinematic quality
- 16:9 aspect ratio for social media"""

    content = [{"type": "text", "text": prompt_text}]

    # Add avatar reference images
    for url in avatar_urls[:4]:
        try:
            req_obj = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            img_data = urllib.request.urlopen(req_obj, timeout=15).read()
            b64 = base64.b64encode(img_data).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"}
            })
        except Exception as e:
            logger.warning(f"Could not fetch avatar image: {e}")

    messages = [
        {"role": "system", "content": "You are a professional marketing image creator."},
        {"role": "user", "content": content}
    ]

    try:
        response = litellm.completion(
            model="gemini/gemini-3-pro-image-preview",
            messages=messages,
            api_key=EMERGENT_KEY,
            api_base=EMERGENT_PROXY_URL,
            custom_llm_provider="openai",
            modalities=["image", "text"],
        )

        images = []
        if response.choices and response.choices[0].message:
            msg = response.choices[0].message
            if hasattr(msg, 'images') and msg.images:
                for img_data in msg.images:
                    if 'image_url' in img_data and 'url' in img_data['image_url']:
                        data_url = img_data['image_url']['url']
                        if 'data:' in data_url and ';base64,' in data_url:
                            parts = data_url.split(';base64,', 1)
                            b64 = parts[1]
                            images.append(b64)

        if not images:
            raise HTTPException(status_code=500, detail="No image generated")

        # Upload first generated image to Supabase Storage
        img_bytes = base64.b64decode(images[0])
        filename = f"studio/scene_{uuid.uuid4().hex[:8]}.png"
        public_url = _upload_to_storage(img_bytes, filename)

        # Save output to project
        output = {
            "id": uuid.uuid4().hex[:8],
            "type": "image",
            "url": public_url,
            "prompt": req.scene_prompt or briefing,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        project["outputs"] = project.get("outputs", []) + [output]
        project["status"] = "generated"
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        settings["studio_projects"] = projects
        _save_settings(tenant["id"], settings)

        return {"image_url": public_url, "project": project}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Studio image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Voice & Music Library ──

@router.get("/voices")
async def get_voices(user=Depends(get_current_user)):
    from pipeline.config import ELEVENLABS_VOICES
    return {"voices": ELEVENLABS_VOICES}


@router.get("/music-library")
async def get_music_library(user=Depends(get_current_user)):
    from pipeline.config import MUSIC_LIBRARY
    tracks = [{"id": k, **v} for k, v in MUSIC_LIBRARY.items()]
    return {"tracks": tracks}
