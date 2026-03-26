"""Storyboard Inpainting — Edit specific elements in panel images using Gemini.

Uses Gemini Nano Banana image editing to modify specific elements while preserving
the rest of the image. The original image is sent as reference and the AI generates
an edited version based on text instructions.
"""
import os
import base64
import asyncio
import logging
import tempfile
import urllib.request

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


def _download_image(url: str) -> bytes:
    """Download image from URL or Supabase path."""
    supabase_url = os.environ.get('SUPABASE_URL', '')
    full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        urllib.request.urlretrieve(full_url, tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def inpaint_element(
    image_url: str,
    edit_instruction: str,
    project_id: str,
    panel_number: int,
    lang: str = "pt",
) -> bytes:
    """Edit a specific element in a storyboard panel image.

    Sends the original image to Gemini with instructions to modify only the
    specified element while preserving everything else exactly as-is.

    Returns edited image bytes or None.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        logger.warning(f"Inpaint [{project_id}]: No EMERGENT_LLM_KEY")
        return None

    # Download original image
    original_bytes = _download_image(image_url)
    if not original_bytes:
        logger.error(f"Inpaint [{project_id}]: Failed to download original image")
        return None

    original_b64 = base64.b64encode(original_bytes).decode('utf-8')

    lang_name = {"pt": "Português", "en": "English", "es": "Español"}.get(lang, "Português")

    prompt = f"""EDIT THIS IMAGE following these EXACT instructions:

EDIT INSTRUCTION: {edit_instruction}

CRITICAL RULES:
- You MUST keep the ENTIRE image exactly the same — same background, same lighting, same colors, same style, same composition
- ONLY modify the specific element mentioned in the instruction
- The edit should look natural and seamless, as if the original image was always this way
- Maintain the same 3D CGI Pixar/DreamWorks art style
- Maintain the same camera angle and perspective
- Maintain the same characters in their same positions (except for the specific edit)
- DO NOT add any text, labels, or watermarks
- DO NOT change the aspect ratio or resolution
- The result must be a SINGLE image that looks identical to the original except for the requested change

Language context: {lang_name}"""

    async def _edit():
        chat = LlmChat(
            api_key=api_key,
            session_id=f"inpaint-{project_id}-{panel_number}",
            system_message="You are a professional image editor. Edit the provided image following the exact instructions while preserving everything else unchanged."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

        msg = UserMessage(
            text=prompt,
            file_contents=[ImageContent(original_b64)]
        )

        text, images = await chat.send_message_multimodal_response(msg)
        if images and len(images) > 0:
            return base64.b64decode(images[0]['data'])
        return None

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(lambda: asyncio.run(_edit())).result(timeout=90)
    else:
        result = asyncio.run(_edit())

    if result:
        logger.info(f"Inpaint [{project_id}]: Panel {panel_number} edited ({len(result)//1024}KB)")
    return result
