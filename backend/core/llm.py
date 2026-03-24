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
    """Transcribe audio using OpenAI Whisper directly."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    with open(file_path, "rb") as f:
        kwargs = {"model": "whisper-1", "file": f, "response_format": response_format}
        if language:
            kwargs["language"] = language
        result = client.audio.transcriptions.create(**kwargs)
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

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data

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
    """Direct OpenAI Sora 2 video generation — bypasses Emergent proxy."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def text_to_video(self, prompt: str, model: str = "sora-2", size: str = "1280x720",
                      duration: int = 12, max_wait_time: int = 600, image_path: str = None) -> bytes:
        import requests
        import time as _time

        payload = {"model": model, "prompt": prompt, "size": size, "seconds": str(duration)}

        if image_path:
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/jpeg" if image_path.endswith(".jpg") else "image/png"
            payload["reference_image"] = {"data": f"data:{mime};base64,{encoded}"}

        resp = requests.post(f"{self.base_url}/videos", headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        op_id = data.get("id") or data.get("operation_id") or data.get("generation_id")
        if not op_id:
            raise Exception(f"No operation ID: {data}")

        start = _time.time()
        while _time.time() - start < max_wait_time:
            _time.sleep(10)
            poll = requests.get(f"{self.base_url}/videos/{op_id}", headers=self.headers, timeout=30)
            if poll.status_code == 200:
                pdata = poll.json()
                status = pdata.get("status", "")
                if status == "succeeded":
                    video_url = pdata.get("video", {}).get("url") or pdata.get("url")
                    if not video_url:
                        outputs = pdata.get("outputs", [])
                        if outputs:
                            video_url = outputs[0].get("url")
                    if video_url:
                        vid_resp = requests.get(video_url, timeout=120)
                        vid_resp.raise_for_status()
                        return vid_resp.content
                    raise Exception(f"No video URL in response: {pdata}")
                elif status == "failed":
                    raise Exception(f"Sora 2 generation failed: {pdata.get('error', pdata)}")

        raise Exception(f"Sora 2 timeout after {max_wait_time}s")
