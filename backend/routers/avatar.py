import os
import uuid
import base64
import logging
import random
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

from core.deps import supabase, get_current_user

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/avatar", tags=["avatar"])

DEFAULT_AVATAR = "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png"

BASE_PROMPT = """Transform this person's photo into a CYBORG half-human half-machine portrait.

CRITICAL RULES - MUST FOLLOW:
- The avatar MUST be an exact likeness of the person in the photo
- Keep ALL accessories: if wearing glasses, avatar MUST have glasses. If has beard, keep beard. Earrings, hat, piercings - keep everything.
- Preserve the person's exact facial features, skin tone, hair color, hair style, and expression
- Front-facing portrait looking directly at camera

COMPOSITION:
- Head, neck, and upper chest visible - show from top of head to mid-chest
- Slightly zoomed out with breathing room around the head
- Centered, suitable for circular profile picture
- High-end 3D photorealistic render, 8K detail"""

STYLE_VARIATIONS = [
    """CYBORG STYLE - VARIANT A (Classic Split):
- Left side fully HUMAN and natural
- Right side transitions into ROBOTIC parts with exposed titanium plates
- Glowing blue/cyan circuit lines on the mechanical side
- Cybernetic eye with blue glow on right side
- Gradual organic transition between human and machine
LIGHTING: Dark background, cool blue rim light on mechanical side, warm light on human side""",

    """CYBORG STYLE - VARIANT B (Circuit Overlay):
- Full face remains mostly human/natural looking
- Subtle glowing circuit patterns visible BENEATH the skin on both sides
- Circuits glow in teal/cyan, visible like veins of light
- One eye has a subtle digital HUD overlay (holographic iris)
- Metallic accents only at temples and jawline
LIGHTING: Dark background, purple and teal accent lighting, subtle neon glow from circuits""",

    """CYBORG STYLE - VARIANT C (Battle-Worn):
- Face is mostly human but with visible cybernetic repairs
- Metallic plate on one cheekbone, like a healed wound replaced with tech
- One ear replaced with sleek mechanical audio implant
- Thin glowing orange/amber circuit scar running from temple to jaw
- Weathered, experienced look - like a veteran cyborg operative
LIGHTING: Dark moody background, warm amber accent light mixed with cool blue""",

    """CYBORG STYLE - VARIANT D (Sleek Chrome):
- Human face with chrome/silver metallic patches seamlessly integrated
- Smooth chrome temple implants on both sides (like premium headphones built into skull)
- One eye with chrome iris ring glowing white
- Neck has visible chrome vertebrae/spine implants
- Clean, elegant, luxury cyborg aesthetic - like a high-end android
LIGHTING: Dark background, clean white studio lighting with subtle blue reflections on chrome""",

    """CYBORG STYLE - VARIANT E (Bio-Luminescent):
- Face mostly natural but with bioluminescent patterns
- Glowing green/teal organic-looking patterns under the skin, like bioluminescent tattoos
- One side of the neck shows translucent skin revealing glowing mechanical parts beneath
- Eyes enhanced with subtle luminous ring around iris
- Futuristic but organic feeling, like biotech rather than hard metal
LIGHTING: Dark background, green/teal bioluminescent glow as primary light source, cinematic""",
]


class GenerateAvatarRequest(BaseModel):
    photo_base64: str
    variation_index: Optional[int] = None


class SaveAvatarRequest(BaseModel):
    avatar_url: str
    cleanup_urls: Optional[List[str]] = None


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

        idx = req.variation_index if req.variation_index is not None else random.randint(0, len(STYLE_VARIATIONS) - 1)
        idx = idx % len(STYLE_VARIATIONS)
        style = STYLE_VARIATIONS[idx]

        full_prompt = f"{BASE_PROMPT}\n\n{style}"

        session_id = f"avatar-gen-{user['id']}-{uuid.uuid4().hex[:8]}"
        chat = LlmChat(api_key=api_key, session_id=session_id, system_message="You are a professional avatar artist.")
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])

        msg = UserMessage(text=full_prompt, file_contents=[ImageContent(photo_b64)])
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

        return {"avatar_url": avatar_url, "variation": idx, "status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Avatar generation failed: {str(e)}")


@router.post("/save")
async def save_avatar(req: SaveAvatarRequest, user=Depends(get_current_user)):
    _save_avatar_url(user["id"], req.avatar_url)
    # Cleanup non-selected files
    if req.cleanup_urls:
        for url in req.cleanup_urls:
            if url.startswith("/avatars/") and url != req.avatar_url:
                filepath = f"/app/frontend/public{url}"
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
    return {"avatar_url": req.avatar_url, "status": "ok"}


@router.post("/set-default")
async def set_default_avatar(user=Depends(get_current_user)):
    _save_avatar_url(user["id"], DEFAULT_AVATAR)
    return {"avatar_url": DEFAULT_AVATAR, "status": "ok"}
