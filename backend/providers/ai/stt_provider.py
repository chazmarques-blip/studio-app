"""STT Provider — Whisper speech-to-text implementation."""
import asyncio
import logging
from .base import STTProvider
from core.config import EMERGENT_LLM_KEY

logger = logging.getLogger(__name__)


class WhisperProvider(STTProvider):
    """OpenAI Whisper via emergent integrations."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or EMERGENT_LLM_KEY

    async def transcribe(self, audio_path: str, language: str = None) -> str:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        stt = OpenAISpeechToText(api_key=self.api_key)

        with open(audio_path, "rb") as f:
            kwargs = {"file": f, "model": "whisper-1", "response_format": "json"}
            if language:
                kwargs["language"] = language
            result = await stt.transcribe(**kwargs)
        return result
