"""AI Provider Factory — Single point to get any AI provider.
Change provider globally by setting AI_*_PROVIDER env vars.
Circuit breaker handles automatic failover.
"""
import logging
from core.config import (
    AI_TEXT_PROVIDER, AI_IMAGE_PROVIDER, AI_VIDEO_PROVIDER,
    AI_VOICE_PROVIDER, AI_STT_PROVIDER, is_enabled,
)
from .text_provider import ClaudeProvider, GeminiTextProvider
from .image_provider import GeminiImageProvider
from .video_provider import Sora2Provider
from .voice_provider import ElevenLabsProvider, OpenAITTSProvider
from .stt_provider import WhisperProvider
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

# ── Singleton instances ──
_text_cb = None
_image_provider = None
_video_provider = None
_voice_cb = None
_stt_provider = None


def get_text_provider():
    """Get text provider with circuit breaker (Claude primary, Gemini fallback)."""
    global _text_cb
    if _text_cb is None:
        primary = ClaudeProvider()
        fallback = GeminiTextProvider()
        if is_enabled("enable_circuit_breaker"):
            _text_cb = CircuitBreaker(primary, fallback, name="TextAI")
        else:
            _text_cb = primary
    return _text_cb


def get_image_provider() -> GeminiImageProvider:
    """Get image generation provider."""
    global _image_provider
    if _image_provider is None:
        _image_provider = GeminiImageProvider()
    return _image_provider


def get_video_provider() -> Sora2Provider:
    """Get video generation provider."""
    global _video_provider
    if _video_provider is None:
        _video_provider = Sora2Provider()
    return _video_provider


def get_voice_provider():
    """Get voice provider with circuit breaker (ElevenLabs primary, OpenAI fallback)."""
    global _voice_cb
    if _voice_cb is None:
        primary = ElevenLabsProvider()
        fallback = OpenAITTSProvider()
        if is_enabled("enable_circuit_breaker"):
            _voice_cb = CircuitBreaker(primary, fallback, name="VoiceAI")
        else:
            _voice_cb = primary
    return _voice_cb


def get_stt_provider() -> WhisperProvider:
    """Get speech-to-text provider."""
    global _stt_provider
    if _stt_provider is None:
        _stt_provider = WhisperProvider()
    return _stt_provider


def get_provider_status() -> dict:
    """Get health status of all AI providers (for deep health check)."""
    status = {}
    for name, instance in [("text", _text_cb), ("image", _image_provider),
                           ("video", _video_provider), ("voice", _voice_cb),
                           ("stt", _stt_provider)]:
        if instance is None:
            status[name] = {"state": "not_initialized"}
        elif isinstance(instance, CircuitBreaker):
            status[name] = instance.status
        else:
            status[name] = {"state": "active", "provider": instance.__class__.__name__}
    return status
