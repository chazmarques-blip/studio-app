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
PREVIEW BOARD -> Production Design Bible (Claude Vision + Production Designer)
PRODUCTION -> N Scene Directors (parallel) + Sora 2 (5 concurrent)
POST-PRODUCTION -> Narrations (Claude script + ElevenLabs) + Music (auto from music_plan) + Fade Transitions + FFmpeg Mix
LOCALIZATION -> Translate (Claude) + Re-voice (ElevenLabs multilingual) + Re-mix (same video)
SUBTITLES -> SRT generation from narrations (all languages)
SCENE RE-EDIT -> Single scene regeneration via Sora 2 (without full project rebuild)
```

### Production Run Results

**15-Scene "Abraao e Isaac sobem ao monte" (2026-03-25):**
| Language | Duration | Narration | Music | Size |
|----------|----------|-----------|-------|------|
| PT | 183s (3:03) | Bill | Cinematic (auto) | 41.4MB |
| EN | 183s (3:03) | Roger | Cinematic | 42.9MB |
| ES | 183s (3:03) | Lily | Cinematic | 42.8MB |

## Completed Features

### Session 2026-03-25 (Latest)
- **P0: Python Lint Cleanup** — Fixed all 27 lint errors in studio.py (E701/E702/F841/E722/E731/E741)
- **P1: Subtitles Backend** — `/api/studio/projects/{id}/generate-subtitles` endpoint generates SRT files for all languages
- **P1: Subtitles UI** — PostProduction.jsx has "Gerar Legendas" button with download links per language
- **P1: Scene Re-edit Backend** — `/api/studio/projects/{id}/regen-scene/{scene_number}` endpoint for single-scene regeneration
- **P1: API Response Updates** — Both `/status` and `/post-production-status` endpoints now include `subtitles` field
- **Bug Fix: RegenSceneRequest** — Removed redundant `scene_number` from body (already in URL path), made body optional

### Previous Sessions
- **P0: 15-Scene Full Production** — Post-production + EN + ES localization complete
- **Phase A: Post-Production (Audio Engineer)** — Narration + music + fade transitions
- **Phase B: Multi-Language Localization** — Translation + re-voice + re-mix
- **P0: Language Selector** — Inline picker in Settings
- **P0: Project List** — Search/filter + loading state
- **P1: FFmpeg Auto-Install** — Module-level startup check
- **P1: Supabase Upload** — REST API retry for large files
- Pipeline v5 (Production Design Bible + Preview Board)
- Google Integration in Agent Config
- Agent Marketplace, CRM, Dashboard
- Deployment readiness validated

## Key Files
- `/app/backend/routers/studio.py` — Full pipeline + post-production + localization + subtitles + scene re-edit
- `/app/frontend/src/components/PostProduction.jsx` — Audio + localization + subtitles UI
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI + search/filter + scene regen buttons
- `/app/frontend/src/components/PreviewBoard.jsx` — Production Design review
- `/app/frontend/src/pages/Settings.jsx` — Inline language picker

## Key API Endpoints
- `POST /api/studio/projects/{id}/post-produce` — Start post-production
- `GET /api/studio/projects/{id}/post-production-status` — Progress polling (includes subtitles)
- `POST /api/studio/projects/{id}/localize` — Start localization
- `GET /api/studio/projects/{id}/localizations` — All localizations + statuses
- `POST /api/studio/projects/{id}/generate-subtitles` — Generate SRT subtitles for all languages
- `POST /api/studio/projects/{id}/regen-scene/{scene_number}` — Regenerate single scene
- `GET /api/studio/projects/{id}/status` — Full project status (includes subtitles)

## Upcoming Tasks
- **P1**: Refactor `studio.py` (3300+ lines) -> separate media logic into `core/media.py`
- **P1**: Refactor `DirectedStudio.jsx` (1733 lines) -> smaller components
- **P2**: Kling AI model integration as alternative to Sora 2
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe
- **P4**: Legal & Publication

## Credentials
- Test: test@agentflow.com / password123
