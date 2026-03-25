# AgentZZ - Product Requirements Document

## Original Problem Statement
Comprehensive, mobile-first, no-code SaaS platform "AgentZZ" for deploying AI agents on social media. Features Directed Studio Mode for AI video production with Pipeline v5 and Continuity Engine v3 (Keyframe-First).

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB
- **AI Stack**: Claude Sonnet (text/vision), Sora 2 (video), Gemini (images/keyframes), ElevenLabs (multilingual voice)

## Continuity Engine v3 — Keyframe-First Pipeline

### Architecture
```
PRE-PRODUCTION:
  1. Avatar Analysis (Claude Vision) -> character descriptions
  2. Production Design Bible (Claude) -> style anchors, color palette
  3. Scene Directors (Claude, parallel) -> Sora prompts

PRODUCTION (Continuity Mode):
  For each scene (SEQUENTIAL):
    1. Generate Keyframe Image (Gemini)
    2. Render Video (Sora 2, using keyframe as reference)
    3. Upload to Supabase Storage

POST-PRODUCTION:
  1. Narration scripts (Claude)
  2. Voice synthesis (ElevenLabs, ISO 639-1 codes)
  3. Music segmentation
  4. Color grading + extended crossfades (1.5s, FFmpeg)
  5. Final mix + upload
```

## Screenplay Approval Flow (COMPLETED - 2026-03-25)
- PATCH `/api/studio/projects/{id}/settings` endpoint - saves screenplay_approved, audio_mode, visual_style, etc.
- Frontend "Aprovar Roteiro" button locks scene edits and unlocks "Personagens" step
- Status endpoint returns screenplay_approved and audio_mode fields

## Scene Merge on Continuation (COMPLETED - 2026-03-25)
- When user sends continuation message, backend detects existing scenes
- Prompt instructs Claude to start from last_scene_num + 1
- Smart merge: non-overlapping scene numbers are appended (continuation), overlapping numbers replace (rewrite)
- Characters are also merged (new characters added, duplicates skipped)

## Bug Fixes
- **Scene merge**: Fixed scenes being replaced instead of merged on continuation messages
- **Screenplay approval**: Added PATCH /settings endpoint for persisting screenplay_approved state
- **Status endpoint**: Added screenplay_approved and audio_mode to GET /status response
- **ElevenLabs Language Codes**: Fixed `pt-BR` -> `pt` (ISO 639-1) for `eleven_multilingual_v2`
- **Python Lint**: All errors in studio.py fixed

## Key Files
- `/app/backend/routers/studio.py` — Pipeline + continuity engine + keyframe gen + post-prod + settings
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI + scene editor + approval flow
- `/app/frontend/src/components/PostProduction.jsx` — Audio + localization + subtitles UI

## Upcoming Tasks
- **P1**: Refactor `studio.py` (3700+ lines) -> `core/media.py`, `core/generators.py`
- **P1**: Refactor `DirectedStudio.jsx` (1800+ lines) -> smaller components
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe

## Credentials
- Test: test@agentflow.com / password123
