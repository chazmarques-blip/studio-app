"""Directed Studio API — Separate from the main pipeline.
Handles directed scene generation with multiple avatars, voices, and music."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger, mongo_db

router = APIRouter(prefix="/api/studio", tags=["studio"])

EMERGENT_PROXY_URL = "https://integrations.emergentagent.com/llm"
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")


# ─── Models ───
class StudioProject(BaseModel):
    name: str = ""
    scene_type: str = "single_image"  # single_image | multi_avatar_image | video_scene
    briefing: str = ""
    avatar_urls: List[str] = []
    asset_urls: List[str] = []
    voice_config: Optional[dict] = None  # {avatar_index: {voice_id, voice_name}}
    music_config: Optional[dict] = None  # {track_id, volume}
    language: str = "pt"

class GenerateSceneRequest(BaseModel):
    project_id: str
    scene_prompt: str = ""

class VoiceGenerateRequest(BaseModel):
    text: str
    voice_id: str
    language: str = "pt"


# ─── ElevenLabs Voices Catalog ───
from pipeline.config import ELEVENLABS_VOICES


# ─── Endpoints ───

@router.get("/voices")
async def list_voices(gender: str = "", user=Depends(get_current_user)):
    """Return available ElevenLabs voices."""
    voices = ELEVENLABS_VOICES
    if gender:
        voices = [v for v in voices if gender.lower() in v["gender"].lower()]
    return {"voices": voices}


@router.post("/projects")
async def create_project(req: StudioProject, user=Depends(get_current_user)):
    """Create a new studio project."""
    project = {
        "user_id": user["id"],
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = mongo_db["studio_projects"].insert_one(project)
    project["id"] = str(result.inserted_id)
    del project["_id"]
    return project


@router.get("/projects")
async def list_projects(user=Depends(get_current_user)):
    """List all studio projects for the user."""
    projects = list(mongo_db["studio_projects"].find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50))
    return {"projects": projects}


@router.post("/generate-image")
async def generate_directed_image(req: GenerateSceneRequest, user=Depends(get_current_user)):
    """Generate a directed image scene with avatar(s) and context."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    project = mongo_db["studio_projects"].find_one({"id": req.project_id, "user_id": user["id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build the generation prompt
    avatar_count = len(project.get("avatar_urls", []))
    base_prompt = f"""Create a professional marketing image for social media.

SCENE DESCRIPTION: {req.scene_prompt or project.get('briefing', 'Professional business scene')}

RULES:
- The image must be photorealistic, cinematic quality, 8K resolution
- Professional lighting with dramatic shadows
- Dark, sophisticated background (#0A0A0A to #1A1A1A)
- The scene should feel premium and modern
"""
    if avatar_count > 1:
        base_prompt += f"\n- Show {avatar_count} people interacting in the scene"
        base_prompt += "\n- Position them naturally, facing each other or the camera"

    # Build message with avatar images as reference
    contents = [ImageContent(type="text", text=base_prompt)]
    for url in project.get("avatar_urls", []):
        contents.append(ImageContent(type="image_url", url=url))
    for url in project.get("asset_urls", []):
        contents.append(ImageContent(type="image_url", url=url))

    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            model="gemini-2.0-flash-preview-image-generation",
            base_url=EMERGENT_PROXY_URL,
        )
        response = await chat.send_image_generation_message(
            messages=[UserMessage(content=contents)],
            config={"response_modalities": ["image", "text"]},
        )

        image_url = None
        if response and response.image_parts:
            img_data = response.image_parts[0]

            import base64
            img_bytes = base64.b64decode(img_data.data)
            fname = f"studio/{uuid.uuid4().hex[:8]}.png"

            from pipeline.utils import _upload_to_storage
            image_url = _upload_to_storage(img_bytes, fname, "image/png")

        if not image_url:
            raise HTTPException(status_code=500, detail="Image generation failed")

        # Save output to project
        output = {
            "id": uuid.uuid4().hex[:8],
            "type": "image",
            "url": image_url,
            "prompt": req.scene_prompt,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mongo_db["studio_projects"].update_one(
            {"id": req.project_id},
            {"$push": {"outputs": output}, "$set": {"status": "generated"}}
        )

        return {"output": output}

    except Exception as e:
        logger.error(f"Studio image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-voice")
async def generate_voice(req: VoiceGenerateRequest, user=Depends(get_current_user)):
    """Generate voice audio using ElevenLabs."""
    import requests

    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=400, detail="ElevenLabs API key not configured")

    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{req.voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": req.text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.5,
                }
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Voice generation failed")

        audio_bytes = response.content
        filename = f"studio/{uuid.uuid4().hex[:8]}.mp3"

        from pipeline.utils import _upload_to_storage
        audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")

        return {"audio_url": audio_url, "voice_id": req.voice_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/music-library")
async def get_music_library(user=Depends(get_current_user)):
    """Return available background music tracks."""
    from pipeline.config import MUSIC_LIBRARY
    return {"tracks": MUSIC_LIBRARY}
