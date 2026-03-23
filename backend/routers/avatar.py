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

IDENTITY PRESERVATION (NEVER BREAK):
1. The face MUST be the EXACT same person - identical face shape, jawline, nose, lips, eyes, skin tone, hair style and color
2. Keep ALL accessories from the photo: glasses, earrings, beard, piercings, necklaces, chains — EVERYTHING preserved exactly
3. The person's expression MUST match the photo (smiling if smiling, serious if serious)

POSE & FRAMING:
- Face MUST be perfectly FRONTAL, looking DIRECTLY at the camera — correct any angle from the source photo
- Head straight and level, both eyes at same horizontal line
- Frame from above the head to mid-chest — leave 15% empty space above the head
- Shoulders and upper chest visible — NOT a tight face crop
- Background: solid very dark, almost black (#0A0A0A)

MECHANICAL AUGMENTATION DESIGN (FOLLOW THIS EXACT STYLE):
- Metallic jaw frame: a sleek brushed-steel guard that wraps around the lower jaw and chin, with subtle ventilation slits and clean panel lines
- Carbon fiber neck armor: a fitted neckpiece in matte black carbon fiber texture, covering the neck and upper chest, with small integrated amber/orange LED strip lights
- Ear mechanism: a compact, intricate metallic device attached to one or both ears, suggesting advanced auditory augmentation
- Forehead band: a thin, minimalist metallic visor/band across the forehead with tiny amber indicator lights
- All mechanical parts must be brushed steel / matte silver color — NOT gold, NOT chrome, NOT black metal
- Small amber/orange LED accent lights integrated into mechanical pieces for visual continuity
- Mechanical parts must seamlessly blend with skin at the borders — smooth organic-to-metal transitions

SKIN & TEXTURE:
- Skin must be SMOOTH — reduced visible pores, no wrinkles, no blemishes
- Slight synthetic sheen on the skin surface — like high-quality silicone or bioengineered tissue
- Skin tone slightly cooled with a subtle steel/blue undertone — less organic, more artificial
- Subsurface scattering still present for realism — skin should glow slightly from within
- The overall feel: a real human who has been enhanced — smooth, polished, slightly artificial skin

LIGHTING (CRITICAL FOR CONSISTENCY):
- Strong key light from upper left — warm, casting defined highlights on the left side of face
- Cool blue/teal fill light from the right — subtle, creating contrast with warm skin tones
- Amber/orange glow from the LED elements on mechanical parts
- High contrast between light and shadow — dramatic, cinematic portrait lighting
- Realistic shadow depth without obscuring facial details

QUALITY:
- Hyper-photorealistic 3D render — must look like a cinematic still, NOT a painting or cartoon
- 8K resolution detail with subtle film grain
- Material contrast: soft organic skin vs hard brushed metal vs textured carbon fiber
- The result must feel like a real augmented human — sophisticated, advanced, not a cheap robot costume"""

STYLE_VARIATIONS = [
    """CYBORG MIX STYLE A - Classic Half Split:
- Left half of face is fully HUMAN (photo-identical, untouched)
- Right half transitions into exposed titanium/carbon-fiber endoskeleton
- Glowing cyan/teal micro-circuits visible in the seams between skin and metal
- Right eye: cybernetic lens with blue-white glow, mechanical iris rings
- Mechanical jaw and cheekbone plates with brushed titanium finish
- Transition zone: skin gradually peeling away to reveal tech beneath
- Blue LED pinpoints along the mechanical seam lines""",

    """CYBORG MIX STYLE B - Subdermal Circuits:
- Face remains 90% human (photo-identical)
- Bioluminescent circuit patterns glow BENEATH the skin like electric veins
- Circuits spread from right temple across cheek and down neck in branching patterns
- Both eyes natural but with subtle cyan glow ring deep in the iris
- Small brushed-chrome implant plates at both temples (sleek, flush with skin)
- The circuits pulse with teal light, visible through translucent skin
- Neck area shows denser circuit patterns converging at the spine""",

    """CYBORG MIX STYLE C - Combat Armor Integration:
- Face fully human (photo-identical) with chrome/titanium armor additions
- Tactical armor plates attached along jawline (like Iron Man partial faceplate)
- Forehead: slim chrome neural-interface band with amber status LED
- One cheek has armored plate with micro-ventilation slits
- Ear replaced with advanced tactical audio module (chrome finish)
- Neck protected by segmented carbon-fiber collar with orange accent lights
- Military-grade cybernetic aesthetic, battle-ready look""",

    """CYBORG MIX STYLE D - Damaged Reveal (Terminator):
- Face mostly human (photo-identical) with realistic battle damage
- Skin realistically torn/scraped on one cheek revealing chrome skull and red-glowing servo eye
- The damage looks organic - not clean cuts, but realistic wounds showing metal beneath
- Endoskeleton visible at temple: pistons, servos, chrome bone structure
- One eye fully cybernetic with glowing red scanner lens
- Rest of face perfectly natural and photo-realistic
- Dramatic contrast between vulnerable flesh and indestructible metal""",

    """CYBORG MIX STYLE E - Holographic Neural Interface:
- Face fully human (photo-identical) - most subtle and elegant variation
- Sleek chrome neural-link device behind right ear with holographic projector
- Floating holographic HUD elements: data readouts, scan lines near the eyes
- Eyes show holographic targeting interface overlay (subtle blue grid in iris)
- Tiny floating holographic particles around the temples
- Minimal physical modifications - emphasis on projected tech
- The most futuristic and clean variation""",
]


class GenerateAvatarRequest(BaseModel):
    photo_base64: str
    variation_index: Optional[int] = None


class SelectAvatarRequest(BaseModel):
    avatar_url: str


class DownloadAvatarRequest(BaseModel):
    avatar_url: str


def _get_tenant(user_id: str):
    r = supabase.table("tenants").select("*").eq("owner_id", user_id).execute()
    return r.data[0] if r.data else None


def _get_settings(user_id: str):
    tenant = _get_tenant(user_id)
    if tenant:
        return tenant.get("settings", {}) or {}, tenant["id"]
    return {}, None


def _save_settings(tenant_id: str, settings: dict):
    supabase.table("tenants").update({"settings": settings}).eq("id", tenant_id).execute()


@router.get("/me")
async def get_my_avatar(user=Depends(get_current_user)):
    settings, _ = _get_settings(user["id"])
    return {
        "avatar_url": settings.get("avatar_url") or DEFAULT_AVATAR,
        "gallery": settings.get("avatar_gallery", [])
    }


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

        # Save to gallery in DB
        settings, tenant_id = _get_settings(user["id"])
        if tenant_id:
            gallery = settings.get("avatar_gallery", [])
            gallery.append({"url": avatar_url, "variation": idx, "style": ["Classic Split", "Subdermal Circuits", "Combat Armor", "Terminator", "Holographic"][idx]})
            settings["avatar_gallery"] = gallery
            _save_settings(tenant_id, settings)

        return {"avatar_url": avatar_url, "variation": idx, "status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Avatar generation failed: {str(e)}")


@router.post("/select")
async def select_avatar(req: SelectAvatarRequest, user=Depends(get_current_user)):
    settings, tenant_id = _get_settings(user["id"])
    if tenant_id:
        settings["avatar_url"] = req.avatar_url
        _save_settings(tenant_id, settings)
    return {"avatar_url": req.avatar_url, "status": "ok"}


@router.post("/download")
async def download_avatar(req: DownloadAvatarRequest, user=Depends(get_current_user)):
    return _build_download(req.avatar_url)


@router.get("/download-file")
async def download_avatar_get(avatar_url: str, token: str):
    from jose import jwt
    secret = os.environ.get("JWT_SECRET", "agentzz-secret-key-2025")
    try:
        jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    return _build_download(avatar_url)


def _build_download(avatar_url: str):
    try:
        from PIL import Image, ImageDraw

        avatar_path = None
        if avatar_url.startswith("/avatars/"):
            avatar_path = f"/app/frontend/public{avatar_url}"
        elif avatar_url.startswith("http"):
            import urllib.request
            tmp_path = f"/tmp/avatar_dl_{uuid.uuid4().hex[:8]}.png"
            urllib.request.urlretrieve(avatar_url, tmp_path)
            avatar_path = tmp_path

        if not avatar_path or not os.path.exists(avatar_path):
            raise HTTPException(status_code=404, detail="Avatar not found")

        img = Image.open(avatar_path).convert("RGBA")
        w, h = img.size

        bar_height = max(50, int(h * 0.07))
        result = Image.new("RGBA", (w, h + bar_height), (10, 10, 10, 255))
        result.paste(img, (0, 0))

        draw = ImageDraw.Draw(result)
        draw.rectangle([(0, h), (w, h + bar_height)], fill=(10, 10, 10, 255))

        logo_path = "/app/frontend/public/logo-agentzz.png"
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_h = int(bar_height * 0.55)
            logo_w = int(logo.width * (logo_h / logo.height))
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
            lx = (w - logo_w) // 2
            ly = h + (bar_height - logo_h) // 2
            result.paste(logo, (lx, ly), logo)

        result_rgb = result.convert("RGB")
        buf = BytesIO()
        result_rgb.save(buf, format="PNG")
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
    settings, tenant_id = _get_settings(user["id"])
    if tenant_id:
        settings["avatar_url"] = DEFAULT_AVATAR
        _save_settings(tenant_id, settings)
    return {"avatar_url": DEFAULT_AVATAR, "status": "ok"}
