# AgentZZ - Product Requirements Document

## Original Problem Statement
Comprehensive, mobile-first, no-code SaaS platform "AgentZZ" for deploying AI agents on social media. Features Directed Studio Mode for AI video production with Pipeline v5 architecture and Continuity Engine.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB
- **AI Stack**: Claude Sonnet (text/vision), Sora 2 (video), Gemini (images), ElevenLabs (multilingual voice), OpenAI TTS/Whisper

## Directed Studio — Full Production Pipeline

### Pipeline v5 + Continuity Engine + Post-Production
```
PRE-PRODUCTION -> Avatar Analysis (Claude Vision) + Production Design Bible (Claude)
CONTINUITY ENGINE (NEW):
  - Style DNA injection (rigid visual identity per art style)
  - Reference Image Anchoring (last frame → next scene)
  - Continuity Validator (Claude Vision inter-scene check)
  - Enhanced Color Grading (FFmpeg uniform tone)
  - Extended Crossfades (1.5s fade transitions)
PRODUCTION:
  - Continuity Mode: Sequential rendering with frame anchoring
  - Normal Mode: Parallel rendering (5 concurrent Sora 2 slots)
POST-PRODUCTION -> Narrations (Claude script + ElevenLabs) + Segmented Music + FFmpeg Mix
LOCALIZATION -> Translate + Re-voice + Re-mix (EN, ES)
SUBTITLES -> SRT generation for all languages
SCENE RE-EDIT -> Single scene regeneration
```

## Continuity Engine v1 (Implemented 2026-03-25)

### 5 Strategies:
1. **P0.1 Reference Image Anchoring** — Extract last frame of scene N → use as Sora 2 reference for scene N+1
2. **P0.2 Style DNA** — Rigid art-style descriptions injected verbatim into every scene prompt (439+ chars). Includes color temp, rendering technique, lighting specifics per style (pixar_3d, cartoon_3d, cartoon_2d, anime_2d, realistic, watercolor)
3. **P1.3 Enhanced Director Prompts** — Stronger visual consistency instructions, character appearance emphasis
4. **P1.4 Color Grading + Extended Crossfades** — Uniform color grading (contrast 1.05, saturation 1.1, warm color balance) + 1.5s crossfade transitions
5. **P2.5 Continuity Validator** — Claude Vision compares first frame of scene N with last frame of scene N-1, reports consistency/issues/severity

### Test Results (Project: Continuity Test - 3 Cenas):
| Scene | Duration | Size | Method |
|-------|----------|------|--------|
| 1 | 12s | 7.9MB | Sora 2 + avatar reference |
| 2 | 12s | 8.5MB | Sora 2 + prev frame anchor |
| 3 | 12s | 9.9MB | Sora 2 + prev frame anchor |
| Final (PT narration) | 36.6s | 9MB | Post-prod + color grading |

## Bug Fix: ElevenLabs Language Code
- `eleven_multilingual_v2` requires ISO 639-1 codes: `pt`, `en`, `es`
- Previously used `pt-BR`, `en-US`, `es-ES` which are unsupported
- Fixed in `_generate_narration_audio()` LANG_HINTS mapping

## Completed Features (All Sessions)

### Session 2026-03-25 (Latest)
- **Continuity Engine v1** — All 5 strategies implemented
- **ElevenLabs Language Fix** — ISO 639-1 codes (pt, en, es)
- **Subtitles UI** — PostProduction.jsx "Gerar Legendas" button + download links
- **Lint Cleanup** — 27 Python lint errors fixed in studio.py
- **Continuity Toggle** — Frontend toggle in project creation form
- **Test Project Generated** — 3 scenes "Abraão e Isaac" with PT narration

### Previous Sessions
- Pipeline v5 (Production Design Bible + Preview Board)
- 15-Scene Full Production + EN + ES localization
- Post-Production (Narration + Music + FFmpeg Transitions)
- Multi-Language Localization
- Google Integration in Agent Config
- Agent Marketplace, CRM, Dashboard

## Key Files
- `/app/backend/routers/studio.py` — Pipeline + continuity engine + post-prod (3550+ lines)
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI + continuity toggle
- `/app/frontend/src/components/PostProduction.jsx` — Audio + localization + subtitles UI

## Key API Endpoints
- `POST /api/studio/projects` — Create project (with continuity_mode flag)
- `POST /api/studio/start-production` — Start production (respects continuity_mode)
- `POST /api/studio/projects/{id}/post-produce` — Post-production with narration
- `POST /api/studio/projects/{id}/localize` — Multi-language localization
- `POST /api/studio/projects/{id}/generate-subtitles` — SRT subtitles
- `POST /api/studio/projects/{id}/regen-scene/{scene_num}` — Re-edit single scene

## Upcoming Tasks
- **P1**: Refactor `studio.py` (3550+ lines) -> separate media logic into `core/media.py`
- **P1**: Refactor `DirectedStudio.jsx` (1750+ lines) -> smaller components
- **P2**: Character Sheet generation via Gemini (pre-production phase)
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe

## Credentials
- Test: test@agentflow.com / password123
