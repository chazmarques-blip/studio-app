# AgentZZ - Product Requirements Document

## Original Problem Statement
A comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users to deploy and configure pre-built AI agents on social media channels. Features a Directed Studio Mode for AI video production with Pipeline v5 architecture.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB (flexible-schema features)
- **AI Stack**: Direct API keys for ALL providers
  - Claude Sonnet 4.5 (Anthropic) — text, vision
  - OpenAI Sora 2 — video generation
  - OpenAI TTS/Whisper — speech
  - Google Gemini — image generation
  - ElevenLabs — multilingual voice synthesis (eleven_multilingual_v2)

## Directed Studio Mode — Pipeline v5 + Audio Engineer

### Video Production Pipeline
```
PREVIEW BOARD (approval step):
|- POST /generate-preview → Avatar Analyzer + Production Designer
+- GET /preview → PreviewBoard component

PRODUCTION (after approval):
|- N Scene Directors (parallel, PD-guided)
|- Sora 2 queue (5 concurrent, composite avatars)
+- FFmpeg concat

POST-PRODUCTION (Phase A - NEW):
|- POST /post-produce → Background task
|  |- Generate narrations (Claude script + ElevenLabs audio)
|  |- Download scene videos
|  |- Apply fade transitions (FFmpeg)
|  |- Select background music (auto from music_plan or manual)
|  |- Mix: video + narration + music → final video
+- Upload final video with full audio

LOCALIZATION (Phase B - NEW):
|- POST /localize → Background task
|  |- Translate narration scripts (Claude)
|  |- Generate audio in target language (ElevenLabs)
|  |- Re-mix: same video + new narration + same music
+- Upload localized video
```

### Validated Production Results
- **Post-Production (PT)**: 36.6s video with narration + emotional soundtrack ✅
- **Localization (EN)**: Same video with English narration ✅
- Both uploaded to Supabase Storage successfully

## Completed Features

### Session 2025-03-25
- **Phase A: Post-Production (Audio Engineer)**
  - Narration generation via Claude (script) + ElevenLabs (audio)
  - Background music auto-selection from Production Design music_plan
  - Fade transitions between scenes via FFmpeg
  - Audio mixing: narration (full) + music (15% volume) with fade in/out
  - Adaptive compression for large files (target bitrate encoding)
  - New endpoints: POST /post-produce, GET /post-production-status

- **Phase B: Multi-Language Localization**
  - Translation via Claude (preserves dramatic tone, 25-word limit)
  - Audio generation in target language via ElevenLabs multilingual v2
  - Video re-mix with new narration + same background music
  - Supports: EN, ES, FR, DE, IT (from PT original)
  - New endpoints: POST /localize, GET /localizations

- **P0: Language Selector** — Inline picker in Settings (6 languages)
- **P0: Project List Bug** — Search/filter, loading state, less aggressive auto-resume
- **P1: FFmpeg Auto-Install** — Module-level check at startup
- **P1: Supabase Upload** — REST API with retry for files >45MB

### Previous Sessions
- Pipeline v5 (Production Design Bible + Preview Board)
- Google Integration in Agent Config
- Agent Marketplace, CRM, Dashboard
- Deployment readiness validated

## Key Files
- `/app/backend/routers/studio.py` — Full pipeline + post-production + localization
- `/app/frontend/src/components/PostProduction.jsx` — Audio + localization UI
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI
- `/app/frontend/src/components/PreviewBoard.jsx` — Production Design review
- `/app/frontend/src/pages/Settings.jsx` — Inline language picker
- `/app/backend/core/llm.py` — AI clients

## Upcoming Tasks
- **P0**: Run full 15-scene "Abraão e Isaac" production with Pipeline v5
- **P1**: Audio Engineer improvements (scene-specific music segments)
- **P2**: Kling AI model integration
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe
- **P4**: Refactor DirectedStudio.jsx

## Credentials
- Test: test@agentflow.com / password123
- API keys in /app/backend/.env
