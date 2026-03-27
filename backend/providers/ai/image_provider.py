"""Image Provider — Gemini image generation implementation."""
import asyncio
import logging
from .base import ImageProvider
from core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)


class GeminiImageProvider(ImageProvider):
    """Google Gemini image generation."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY

    async def generate(self, prompt: str, reference_image: bytes = None) -> bytes:
        return await asyncio.to_thread(self.generate_sync, prompt, reference_image)

    def generate_sync(self, prompt: str, reference_image: bytes = None) -> bytes:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        contents = []
        if reference_image:
            contents.append(types.Part.from_bytes(data=reference_image, mime_type="image/png"))
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


class GeminiVisionProvider(ImageProvider):
    """Gemini for image analysis/editing via emergent integrations."""

    def __init__(self, api_key: str = None):
        from core.config import EMERGENT_LLM_KEY
        self.api_key = api_key or EMERGENT_LLM_KEY

    async def generate(self, prompt: str, reference_image: bytes = None) -> bytes:
        return await asyncio.to_thread(self.generate_sync, prompt, reference_image)

    def generate_sync(self, prompt: str, reference_image: bytes = None) -> bytes:
        from emergentintegrations.llm.gemeni.image_generation import GeminiImageGeneration
        gen = GeminiImageGeneration(api_key=self.api_key)
        result = gen.generate_image(prompt=prompt)
        if result and hasattr(result, 'image_bytes'):
            return result.image_bytes
        return None
