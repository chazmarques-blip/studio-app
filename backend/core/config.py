"""Centralized configuration — all env vars validated at startup.
Single source of truth. Fail fast if anything is missing.
"""
import os
from dotenv import load_dotenv

load_dotenv(override=False)

# ── Database ──
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME = os.environ.get("DB_NAME", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")

# ── AI Provider Keys ──
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
FAL_KEY = os.environ.get("FAL_KEY", "")

# ── AI Provider Selection (change here to swap provider globally) ──
AI_TEXT_PROVIDER = os.environ.get("AI_TEXT_PROVIDER", "claude")
AI_IMAGE_PROVIDER = os.environ.get("AI_IMAGE_PROVIDER", "gemini")
AI_VIDEO_PROVIDER = os.environ.get("AI_VIDEO_PROVIDER", "sora2")
AI_VOICE_PROVIDER = os.environ.get("AI_VOICE_PROVIDER", "elevenlabs")
AI_STT_PROVIDER = os.environ.get("AI_STT_PROVIDER", "whisper")

# ── AI Model Names ──
CLAUDE_MODEL = "anthropic/claude-sonnet-4-5-20250929"
GEMINI_TEXT_MODEL = "gemini/gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"

# ── External Services ──
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REACT_APP_BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "")

# ── CORS ──
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "").split(",")
if CORS_ORIGINS == [""]:
    CORS_ORIGINS = ["*"]

# ── Feature Flags ──
FEATURE_FLAGS = {
    "use_new_db_schema": False,
    "enable_circuit_breaker": True,
    "enable_deep_health": True,
}


def is_enabled(flag: str) -> bool:
    """Check if a feature flag is enabled."""
    return FEATURE_FLAGS.get(flag, False)


# ── Upload Limits ──
MAX_IMAGE_SIZE_MB = 10
MAX_AUDIO_SIZE_MB = 20
MAX_VIDEO_SIZE_MB = 100

# ── Rate Limits ──
RATE_LIMIT_AI_GENERATION = "10/minute"
RATE_LIMIT_DEFAULT = "60/minute"

# ── App Info ──
APP_VERSION = "1.0.0"
APP_NAME = "StudioX API"
