"""AI Provider Interfaces — Abstract base classes.
Any AI provider must implement these contracts.
Allows swapping Claude<->GPT, Gemini<->DALL-E, etc. with zero code changes.
"""
from abc import ABC, abstractmethod
from typing import Optional


class TextProvider(ABC):
    """Contract for text generation providers (Claude, GPT, Gemini)."""

    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        """Single-shot completion."""
        ...

    @abstractmethod
    def complete_sync(self, system: str, user: str, max_tokens: int = 4000) -> str:
        """Synchronous completion for use in threads."""
        ...

    @abstractmethod
    async def complete_with_images(self, system: str, user: str, images_b64: list, max_tokens: int = 4000) -> str:
        """Completion with image inputs (vision)."""
        ...


class ImageProvider(ABC):
    """Contract for image generation providers (Gemini, DALL-E)."""

    @abstractmethod
    async def generate(self, prompt: str, reference_image: bytes = None) -> bytes:
        """Generate an image. Optionally use a reference image for editing."""
        ...

    @abstractmethod
    def generate_sync(self, prompt: str, reference_image: bytes = None) -> bytes:
        """Synchronous version for use in thread pools."""
        ...


class VideoProvider(ABC):
    """Contract for video generation providers (Sora 2, Runway)."""

    @abstractmethod
    def generate(self, prompt: str, reference_image_path: str = None,
                 size: str = "1280x720", duration: int = 12) -> bytes:
        """Generate a video from prompt. Returns video bytes."""
        ...


class VoiceProvider(ABC):
    """Contract for text-to-speech providers (ElevenLabs, OpenAI TTS)."""

    @abstractmethod
    async def text_to_speech(self, text: str, voice_id: str, **kwargs) -> bytes:
        """Convert text to speech audio. Returns audio bytes."""
        ...

    @abstractmethod
    def text_to_speech_sync(self, text: str, voice_id: str, **kwargs) -> bytes:
        """Synchronous TTS for use in threads."""
        ...


class STTProvider(ABC):
    """Contract for speech-to-text providers (Whisper, Deepgram)."""

    @abstractmethod
    async def transcribe(self, audio_path: str, language: str = None) -> str:
        """Transcribe audio file to text."""
        ...
