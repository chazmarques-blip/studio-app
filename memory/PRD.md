# AgentZZ - Product Requirements Document

## Original Problem Statement
Comprehensive, mobile-first, no-code SaaS platform "AgentZZ" for deploying AI agents on social media. Features Directed Studio Mode for AI video production with Pipeline v5 architecture.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB
- **AI Stack**: Claude Sonnet (text/vision), Sora 2 (video), Gemini (images), ElevenLabs (multilingual voice), OpenAI TTS/Whisper

## Directed Studio — Full Production Pipeline

### Pipeline v5 + Audio Engineer + Localization
```
PREVIEW BOARD → Production Design Bible (Claude Vision + Production Designer)
PRODUCTION → N Scene Directors (parallel) + Sora 2 (5 concurrent)
POST-PRODUCTION → Narrations (Claude script + ElevenLabs) + Music (auto from music_plan) + Fade Transitions + FFmpeg Mix
LOCALIZATION → Translate (Claude) + Re-voice (ElevenLabs multilingual) + Re-mix (same video)
```

### Production Run Results

**15-Scene "Abraão e Isaac sobem ao monte" (2026-03-25):**
| Language | Duration | Narration | Music | Size |
|----------|----------|-----------|-------|------|
| PT 🇧🇷 | 183s (3:03) | ✅ Bill | ✅ Cinematic (auto) | 41.4MB |
| EN 🇺🇸 | 183s (3:03) | ✅ Roger | ✅ Cinematic | 42.9MB |
| ES 🇪🇸 | 183s (3:03) | ✅ Lily | ✅ Cinematic | 42.8MB |

**3-Scene Test Project (previously validated):**
| PT | 36.6s | ✅ | ✅ Emotional | ~10MB |
| EN | 36.6s | ✅ | ✅ Emotional | ~10MB |

## Completed Features

### Session 2026-03-25 (Current)
- **P0: 15-Scene Full Production** — Post-production + EN + ES localization complete
- **Phase A: Post-Production (Audio Engineer)** — Narration + music + fade transitions
- **Phase B: Multi-Language Localization** — Translation + re-voice + re-mix
- **P0: Language Selector** — Inline picker in Settings
- **P0: Project List** — Search/filter + loading state
- **P1: FFmpeg Auto-Install** — Module-level startup check
- **P1: Supabase Upload** — REST API retry for large files
- **Supabase Retry** — `_save_settings` and `_get_settings` with 3-attempt retry

### Previous Sessions
- Pipeline v5 (Production Design Bible + Preview Board)
- Google Integration in Agent Config
- Agent Marketplace, CRM, Dashboard
- Deployment readiness validated

## Key Files
- `/app/backend/routers/studio.py` — Full pipeline + post-production + localization
- `/app/frontend/src/components/PostProduction.jsx` — Audio + localization UI
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI + search/filter
- `/app/frontend/src/components/PreviewBoard.jsx` — Production Design review
- `/app/frontend/src/pages/Settings.jsx` — Inline language picker

## Key API Endpoints
- `POST /api/studio/projects/{id}/post-produce` — Start post-production
- `GET /api/studio/projects/{id}/post-production-status` — Progress polling
- `POST /api/studio/projects/{id}/localize` — Start localization
- `GET /api/studio/projects/{id}/localizations` — All localizations + statuses

## Upcoming Tasks
- **P1**: Audio Engineer improvements (scene-specific music segments based on mood)
- **P2**: Kling AI model integration as alternative to Sora 2
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe
- **P4**: Refactor DirectedStudio.jsx

## Credentials
- Test: test@agentflow.com / password123
