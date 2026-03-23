import os
import uuid
import base64
import logging
import random
from io import BytesIO
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

from core.deps import supabase, get_current_user

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/avatar", tags=["avatar"])

DEFAULT_AVATAR = "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png"

BASE_PROMPT = """Transform this person's photo into a CYBORG half-human half-machine portrait.

ABSOLUTE RULES (NEVER BREAK THESE):
1. The face MUST be the EXACT same person from the photo - same face shape, jawline, nose, lips, eyes, skin tone, hair
2. Keep ALL accessories EXACTLY as in photo: glasses, earrings, beard, piercings, hat - everything
3. Camera angle MUST be FRONT-FACING, looking DIRECTLY at the camera - NO side angles, NO 3/4 view
4. The person's expression should match the photo (smiling if smiling, serious if serious)
5. Show head, neck and upper chest - NOT just the face
6. Background MUST be very dark, almost black (#0A0A0A)
7. 3D photorealistic render quality, 8K detail
8. The human parts must look EXACTLY like the real photo - same skin texture, same features"""

STYLE_VARIATIONS = [
    """CYBORG MIX STYLE A - Classic Half Split:
- Left half of face is fully HUMAN (identical to photo)
- Right half transitions into exposed titanium mechanical endoskeleton
- Glowing cyan/teal circuit lines on the mechanical half
- Right eye replaced with cybernetic lens glowing blue
- Mechanical jaw plates visible on right side
- Chrome and titanium metal parts with blue LED seams""",

    """CYBORG MIX STYLE B - Circuit Veins:
- Face remains 90% human (identical to photo)
- Glowing teal/cyan circuit patterns visible UNDER the skin like luminous veins
- Circuits spread from the right temple across cheek and down neck
- Both eyes natural but with subtle cyan glow ring in iris
- Small metallic implant plates at temples
- Neck shows circuits beneath translucent skin""",

    """CYBORG MIX STYLE C - Armored Plates:
- Face fully human (identical to photo) but with chrome armor additions
- Metallic armor plates attached to jawline and cheekbones (like Iron Man faceplate pieces)
- Forehead has a slim chrome band/implant
- Glowing orange/amber accent lights on armor pieces
- One ear has mechanical audio enhancement module
- Neck protected by segmented chrome collar armor""",

    """CYBORG MIX STYLE D - Terminator Style:
- Face mostly human (identical to photo) with DAMAGE revealing machine underneath
- Skin torn/peeled on one cheek showing chrome skull and red glowing eye beneath
- Metallic endoskeleton visible at temple and jaw
- One eye glowing red through the skin tear
- Rest of face perfectly human
- Dramatic contrast between flesh and metal""",

    """CYBORG MIX STYLE E - Holographic Tech:
- Face fully human (identical to photo)
- Holographic HUD overlay projected from a small temple device
- Floating holographic data particles around the head
- Eyes show holographic targeting/scan interface
- Subtle blue holographic grid pattern floating near the skin
- Small chrome neural-link device behind one ear
- The most subtle and elegant variation""",
]


class GenerateAvatarRequest(BaseModel):
    photo_base64: str
    variation_index: Optional[int] = None


class SaveAvatarRequest(BaseModel):
    avatar_url: str
    cleanup_urls: Optional[List[str]] = None


class DownloadAvatarRequest(BaseModel):
    avatar_url: str


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


@router.post("/download")
async def download_avatar(req: DownloadAvatarRequest, user=Depends(get_current_user)):
    try:
        from PIL import Image, ImageDraw, ImageFont

        avatar_path = None
        if req.avatar_url.startswith("/avatars/"):
            avatar_path = f"/app/frontend/public{req.avatar_url}"
        elif req.avatar_url.startswith("http"):
            import urllib.request
            tmp_path = f"/tmp/avatar_dl_{uuid.uuid4().hex[:8]}.png"
            urllib.request.urlretrieve(req.avatar_url, tmp_path)
            avatar_path = tmp_path

        if not avatar_path or not os.path.exists(avatar_path):
            raise HTTPException(status_code=404, detail="Avatar not found")

        img = Image.open(avatar_path).convert("RGBA")
        w, h = img.size

        bar_height = max(40, int(h * 0.06))
        result = Image.new("RGBA", (w, h + bar_height), (10, 10, 10, 255))
        result.paste(img, (0, 0))

        draw = ImageDraw.Draw(result)
        draw.rectangle([(0, h), (w, h + bar_height)], fill=(10, 10, 10, 255))

        logo_path = "/app/frontend/public/logo-agentzz.png"
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_h = int(bar_height * 0.6)
            logo_w = int(logo.width * (logo_h / logo.height))
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
            lx = (w - logo_w) // 2
            ly = h + (bar_height - logo_h) // 2
            result.paste(logo, (lx, ly), logo)
        else:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(bar_height * 0.4))
            except Exception:
                font = ImageFont.load_default()
            text = "agentZZ"
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (w - tw) // 2
            ty = h + (bar_height - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), text, fill=(201, 168, 76, 255), font=font)

        result_rgb = result.convert("RGB")
        buf = BytesIO()
        result_rgb.save(buf, format="PNG", quality=95)
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/png", headers={
            "Content-Disposition": f"attachment; filename=agentzz_avatar_{uuid.uuid4().hex[:6]}.png"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/set-default")
async def set_default_avatar(user=Depends(get_current_user)):
    _save_avatar_url(user["id"], DEFAULT_AVATAR)
    return {"avatar_url": DEFAULT_AVATAR, "status": "ok"}
