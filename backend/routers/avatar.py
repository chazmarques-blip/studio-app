import os
import uuid
import base64
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from core.deps import supabase, get_current_user

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/avatar", tags=["avatar"])

DEFAULT_AVATAR = "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/36152c5b792ad0e3a5369214cbd423ca6b327833cf834f94d65f76c7c348c7a7.png"

AVATAR_PROMPT = """Transform this person's photo into a futuristic premium 3D humanoid avatar portrait.
CRITICAL: The avatar MUST face directly forward, looking straight at the camera. Front-facing portrait only.
Style requirements:
- Frontal face view, eyes looking directly at the viewer
- Golden metallic skin tones with subtle reflections
- Sleek dark background (#0A0A0A)
- Soft professional studio lighting with golden accent lights
- High-end 3D rendered quality
- The avatar should clearly resemble the person in the photo but stylized as a futuristic humanoid
- Premium luxury aesthetic with gold and black color palette
- Head and upper shoulders, centered in frame
- Clean, sharp details suitable for a circular profile picture
- No sunglasses, no accessories covering the face"""


class GenerateAvatarRequest(BaseModel):
    photo_base64: str
    custom_prompt: Optional[str] = None


def _get_tenant(user_id: str):
    r = supabase.table("tenants").select("*").eq("owner_id", user_id).execute()
    return r.data[0] if r.data else None


def _save_avatar_url(user_id: str, avatar_url: str):
    tenant = _get_tenant(user_id)
    if tenant:
        settings = tenant.get("settings", {}) or {}
        settings["avatar_url"] = avatar_url
        supabase.table("tenants").update({"settings": settings}).eq("id", tenant["id"]).execute()


def get_avatar_url(user_id: str):
    tenant = _get_tenant(user_id)
    if tenant:
        settings = tenant.get("settings", {}) or {}
        return settings.get("avatar_url")
    return None


@router.get("/me")
async def get_my_avatar(user=Depends(get_current_user)):
    url = get_avatar_url(user["id"])
    return {"avatar_url": url or DEFAULT_AVATAR}


@router.post("/generate")
async def generate_avatar(req: GenerateAvatarRequest, user=Depends(get_current_user)):
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM key not configured")

        photo_b64 = req.photo_base64
        if "," in photo_b64:
            photo_b64 = photo_b64.split(",", 1)[1]

        session_id = f"avatar-gen-{user['id']}-{uuid.uuid4().hex[:8]}"
        chat = LlmChat(api_key=api_key, session_id=session_id, system_message="You are a professional avatar artist.")
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])

        prompt = req.custom_prompt or AVATAR_PROMPT

        msg = UserMessage(
            text=prompt,
            file_contents=[ImageContent(photo_b64)]
        )

        text, images = await chat.send_message_multimodal_response(msg)

        if not images:
            raise HTTPException(status_code=500, detail="Failed to generate avatar image")

        img_data = images[0]
        image_bytes = base64.b64decode(img_data["data"])

        filename = f"user_avatar_{user['id']}_{uuid.uuid4().hex[:8]}.png"
        filepath = f"/app/frontend/public/avatars/{filename}"

        os.makedirs("/app/frontend/public/avatars", exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        avatar_url = f"/avatars/{filename}"

        _save_avatar_url(user["id"], avatar_url)

        return {"avatar_url": avatar_url, "status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Avatar generation failed: {str(e)}")


@router.post("/set-default")
async def set_default_avatar(user=Depends(get_current_user)):
    _save_avatar_url(user["id"], DEFAULT_AVATAR)
    return {"avatar_url": DEFAULT_AVATAR, "status": "ok"}
