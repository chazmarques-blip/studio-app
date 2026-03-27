"""Voice Provider — ElevenLabs and OpenAI TTS implementations."""
import asyncio
import logging
from .base import VoiceProvider
from core.config import ELEVENLABS_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)


class ElevenLabsProvider(VoiceProvider):
    """ElevenLabs TTS provider."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ELEVENLABS_API_KEY

    async def text_to_speech(self, text: str, voice_id: str, **kwargs) -> bytes:
        return await asyncio.to_thread(self.text_to_speech_sync, text, voice_id, **kwargs)

    def text_to_speech_sync(self, text: str, voice_id: str, **kwargs) -> bytes:
        from elevenlabs import ElevenLabs as ELClient, VoiceSettings
        client = ELClient(api_key=self.api_key)
        stability = kwargs.get("stability", 0.5)
        similarity = kwargs.get("similarity_boost", 0.8)

        audio_gen = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(stability=stability, similarity_boost=similarity),
        )
        chunks = []
        for chunk in audio_gen:
            chunks.append(chunk)
        return b"".join(chunks)


class OpenAITTSProvider(VoiceProvider):
    """OpenAI TTS provider (fallback)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENAI_API_KEY

    async def text_to_speech(self, text: str, voice_id: str, **kwargs) -> bytes:
        return await asyncio.to_thread(self.text_to_speech_sync, text, voice_id, **kwargs)

    def text_to_speech_sync(self, text: str, voice_id: str, **kwargs) -> bytes:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        voice = voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "alloy"
        response = client.audio.speech.create(model="tts-1", voice=voice, input=text)
        return response.content
