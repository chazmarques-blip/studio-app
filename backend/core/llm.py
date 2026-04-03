"""Direct LLM integration — all providers use user's API keys directly.
No Emergent proxy. Faster, cheaper, independent.
"""
import os
import asyncio
import base64
import logging
import litellm

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

DEFAULT_MODEL = "anthropic/claude-sonnet-4-5-20250929"
DEFAULT_GEMINI_MODEL = "gemini/gemini-2.5-flash"


def _api_key_for_model(model: str) -> str:
    if "anthropic" in model or "claude" in model:
        return ANTHROPIC_API_KEY
    elif "gemini" in model:
        return GEMINI_API_KEY
    else:
        return OPENAI_API_KEY


class DirectChat:
    """Session-based chat — drop-in replacement for LlmChat from emergentintegrations."""

    def __init__(self, system_message: str, model: str = DEFAULT_MODEL):
        self.model = model
        self.api_key = _api_key_for_model(model)
        self.messages = [{"role": "system", "content": system_message}]

    async def send_message(self, text: str, images: list = None) -> str:
        if images:
            content = [{"type": "text", "text": text}]
            for img_b64 in images:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
            self.messages.append({"role": "user", "content": content})
        else:
            self.messages.append({"role": "user", "content": text})

        response = await litellm.acompletion(
            model=self.model,
            messages=self.messages,
            api_key=self.api_key,
            max_tokens=4000,
            timeout=120,
        )
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply


async def direct_completion(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4000,
    images: list = None,
) -> str:
    """Single-shot completion — no session state."""
    api_key = _api_key_for_model(model)

    messages = [{"role": "system", "content": system_prompt}]
    if images:
        content = [{"type": "text", "text": user_message}]
        for img_b64 in images:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": user_message})

    response = await litellm.acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
        max_tokens=max_tokens,
        timeout=120,
    )
    return response.choices[0].message.content


async def multi_turn_completion(
    system_prompt: str,
    messages_history: list,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4000,
) -> str:
    """Multi-turn completion with pre-built message history list."""
    api_key = _api_key_for_model(model)
    messages = [{"role": "system", "content": system_prompt}] + messages_history

    response = await litellm.acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
        max_tokens=max_tokens,
        timeout=120,
    )
    return response.choices[0].message.content


async def speech_to_text(file_path: str, language: str = None, response_format: str = "json"):
    """Transcribe audio using OpenAI Whisper via emergentintegrations."""
    from emergentintegrations.llm.openai import OpenAISpeechToText

    api_key = os.environ.get("EMERGENT_LLM_KEY", "")
    stt = OpenAISpeechToText(api_key=api_key)

    with open(file_path, "rb") as f:
        kwargs = {"file": f, "model": "whisper-1", "response_format": response_format}
        if language:
            kwargs["language"] = language
        result = await stt.transcribe(**kwargs)
    return result


async def generate_image_gemini(prompt: str, input_image_bytes: bytes = None) -> bytes:
    """Generate/edit image using Gemini direct API. Returns image bytes."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents = []
    if input_image_bytes:
        contents.append(types.Part.from_bytes(data=input_image_bytes, mime_type="image/png"))
    contents.append(prompt)

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    # Safety check: validate response structure
    if not response or not response.candidates or len(response.candidates) == 0:
        logger.error("Gemini returned empty response (no candidates)")
        return None
    
    candidate = response.candidates[0]
    if not candidate or not candidate.content or not candidate.content.parts:
        logger.error("Gemini response missing content or parts")
        return None

    for part in candidate.content.parts:
        if part.inline_data:
            return part.inline_data.data

    logger.warning("No inline_data found in Gemini response parts")
    return None


def generate_image_gemini_sync(prompt: str, input_image_bytes: bytes = None) -> bytes:
    """Sync version of Gemini image generation for use in threads."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents = []
    if input_image_bytes:
        contents.append(types.Part.from_bytes(data=input_image_bytes, mime_type="image/png"))
    contents.append(prompt)

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

    return None


def text_to_speech_sync(text: str, voice: str = "alloy", model: str = "tts-1") -> bytes:
    """Generate speech using OpenAI TTS directly. Returns mp3 bytes."""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.audio.speech.create(model=model, voice=voice, input=text)
    return response.content


class DirectSora2Client:
    """Direct OpenAI Sora 2 video generation — based on official API docs (2025)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"

    def text_to_video(self, prompt: str, model: str = "sora-2", size: str = "1280x720",
                      duration: int = 12, max_wait_time: int = 600, image_path: str = None) -> bytes:
        import requests
        import time as _time

        auth_header = {"Authorization": f"Bearer {self.api_key}"}

        # --- Start render job ---
        if image_path and os.path.exists(image_path):
            # Resize reference image to match video dimensions (required by Sora 2 API)
            from PIL import Image as _PILImage
            import io as _io
            _img = _PILImage.open(image_path)
            w, h = [int(x) for x in size.split("x")]
            if _img.size != (w, h):
                canvas = _PILImage.new("RGB", (w, h), (0, 0, 0))
                ratio = min(w / _img.width, h / _img.height)
                nw, nh = int(_img.width * ratio), int(_img.height * ratio)
                resized = _img.resize((nw, nh), _PILImage.LANCZOS)
                canvas.paste(resized, ((w - nw) // 2, (h - nh) // 2))
                buf = _io.BytesIO()
                canvas.save(buf, format="PNG")
                buf.seek(0)
                img_data = buf
                img_name, img_mime = "reference.png", "image/png"
            else:
                img_data = open(image_path, "rb")
                img_name = os.path.basename(image_path)
                img_mime = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

            files = {"input_reference": (img_name, img_data, img_mime)}
            data = {"model": model, "prompt": prompt, "size": size, "seconds": str(duration)}
            resp = requests.post(f"{self.base_url}/videos", headers=auth_header, data=data, files=files, timeout=60)
            if hasattr(img_data, 'close'):
                img_data.close()

            if resp.status_code == 400:
                err_text = resp.text.lower()
                logger.warning(f"Sora 2: 400 error body: {resp.text[:300]}")
                if "face" in err_text or "moderation" in err_text or "inpaint" in err_text:
                    logger.warning(f"Sora 2: Image ref rejected ({resp.text[:80]}). Text-only fallback.")
                    resp = requests.post(
                        f"{self.base_url}/videos",
                        headers={**auth_header, "Content-Type": "application/json"},
                        json={"model": model, "prompt": prompt, "size": size, "seconds": str(duration)},
                        timeout=60,
                    )
        else:
            resp = requests.post(
                f"{self.base_url}/videos",
                headers={**auth_header, "Content-Type": "application/json"},
                json={"model": model, "prompt": prompt, "size": size, "seconds": str(duration)},
                timeout=60,
            )

        resp.raise_for_status()
        job = resp.json()
        video_id = job.get("id")
        if not video_id:
            raise Exception(f"No video ID in response: {job}")

        logger.info(f"Sora 2 job created: {video_id} (status={job.get('status')}, model={model})")

        # --- Poll until completed/failed ---
        start = _time.time()
        last_log = 0
        while _time.time() - start < max_wait_time:
            _time.sleep(10)
            poll = requests.get(f"{self.base_url}/videos/{video_id}", headers=auth_header, timeout=30)
            if poll.status_code != 200:
                continue

            pdata = poll.json()
            status = pdata.get("status", "")
            progress = pdata.get("progress", 0)

            if _time.time() - last_log > 30:
                logger.info(f"Sora 2 [{video_id[:20]}]: {status} ({progress}%)")
                last_log = _time.time()

            if status == "completed":
                for dl_try in range(3):
                    try:
                        dl = requests.get(f"{self.base_url}/videos/{video_id}/content", headers=auth_header, timeout=300, stream=True)
                        dl.raise_for_status()
                        chunks = []
                        for chunk in dl.iter_content(chunk_size=1024*1024):
                            chunks.append(chunk)
                        video_bytes = b"".join(chunks)
                        logger.info(f"Sora 2 [{video_id[:20]}]: Downloaded {len(video_bytes)//1024}KB")
                        return video_bytes
                    except Exception as dl_err:
                        logger.warning(f"Sora 2 [{video_id[:20]}]: Download attempt {dl_try+1}/3 failed: {dl_err}")
                        if dl_try < 2:
                            _time.sleep(5)
                raise Exception("Sora 2 download failed after 3 attempts")

            elif status == "failed":
                error = pdata.get("error", {})
                msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                raise Exception(f"Sora 2 failed: {msg}")

        raise Exception(f"Sora 2 timeout after {max_wait_time}s")
