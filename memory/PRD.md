# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Gemini 3 Pro (image), Gemini 2.5 Flash (vision/critic), OpenAI TTS, fal.ai Kling (lip-sync), ElevenLabs TTS
- Video: Sora 2 (via Emergent Integrations) - CURRENTLY DOWN
- Storage: Supabase Storage (pipeline-assets bucket)

## Code Architecture (Post-Refactoring)

### Backend Pipeline Package (`/app/backend/pipeline/`)
| Module | Lines | Responsibility |
|--------|-------|----------------|
| `config.py` | 636 | Constants, Pydantic models, configuration |
| `utils.py` | 413 | Storage, text parsing, AI utilities |
| `prompts.py` | 461 | AI agent prompt construction |
| `media.py` | 1251 | Image and video generation/processing |
| `engine.py` | 568 | Step execution, recovery, state management |
| `avatar_routes.py` | 880 | Avatar-related API endpoints |
| `routes.py` | 1348 | Core pipeline API endpoints |
| `router.py` | 4 | Shared FastAPI router instance |
| `__init__.py` | 18 | Package init, imports route modules |

### Frontend Pipeline Components (`/app/frontend/src/components/pipeline/`)
| Component | Lines | Purpose |
|-----------|-------|---------|
| `constants.js` | 44 | STEP_META, STEP_ORDER, PLATFORMS, cleanDisplayText |
| `ProgressTimer.jsx` | 32 | Pipeline step progress indicator |
| `ImageLightbox.jsx` | 83 | Image preview lightbox |
| `StepCard.jsx` | 214 | Pipeline step display card + content |
| `ApprovalCards.jsx` | 133 | Copy, Design, Video approval UIs |
| `CompletedSummary.jsx` | 213 | Campaign completion summary |
| `HistoryCard.jsx` | 54 | Pipeline history list item |
| `AssetUploader.jsx` | 128 | File upload component |
| `PipelineView.jsx` | 2346 | Main studio component (down from 3178) |

## Key Features Implemented
- Dashboard with recharts analytics
- Agent Marketplace with plan-gating
- Google Calendar/Sheets integration in Agent Config
- Data persistence in Supabase
- Dual-source avatar generation (photo + video)
- Iterative AI Accuracy Agent
- Real company logo compositing via PIL
- Agent Timeline UI for generation progress
- Voice Mastering, Voice Bank (TTS), Custom Recording
- Avatar Video Preview (5s lip-sync via fal.ai)
- Automatic 360 generation
- Multi-language support (EN, PT, ES)
- Unified Share Area
- ElevenLabs TTS Integration for video narration
- **ElevenLabs Premium Voices for Avatars** (backend + frontend complete)
- Scale-to-fit + padding for image/video format conversion
- Two-tab campaign detail (Content | Results)
- Per-platform video variants (8 platforms)
- 14 Image Generation Styles
- Edit Image Text (change headline without regenerating)
- Pipeline auto-recovery for stuck steps

## Completed - March 18, 2026 (Current Session)
### Refactoring
- [x] Backend: pipeline.py (5306 lines) decomposed into 9 modules in `/app/backend/pipeline/`
- [x] Frontend: PipelineView.jsx (3178 lines) decomposed, extracting 8 sub-components to `/app/frontend/src/components/pipeline/`
- [x] All 37 backend routes preserved and tested (iteration_69)
- [x] Avatar audio fix for older avatars (missing `language` field) verified working

## Completed - March 19, 2026
### ElevenLabs Premium Voices for Avatars
- [x] Backend: `/elevenlabs-voices` endpoint, `voice-preview` with `voice_type` param (openai/elevenlabs)
- [x] Backend: Route order fix in `pipeline/__init__.py` (avatar_routes before routes)
- [x] Frontend: 3 voice sub-tabs (Voice Bank, Premium ElevenLabs, Custom Recording)
- [x] Frontend: ElevenLabs voice selection, preview playback, visual indicators (Crown icon)
- [x] Frontend: Avatar edit auto-selects correct voice tab based on saved voice type
- [x] All tested and verified (iteration_70: 10/10 backend tests passed)

## Known Issues
- **Sora 2 Video Generation API** - Was down, now reported stable (needs re-verification)
- **Pipeline steps can get stuck** - Auto-recovery added (GET/LIST triggers)

## Backlog (Priority Order)
### P0
- [ ] Verify video branding once Sora 2 is back
- [ ] Test full campaign with working video generation

### P1 - Features
- [ ] Automated campaign sharing
- [ ] Redesign Landing/Login page

### P2 - Features
- [ ] Ultra-Realistic Avatar (HeyGen)
- [ ] CRM with Kanban board

### P3 - Future
- [ ] Omnichannel integrations (WhatsApp, SMS, etc.)
- [ ] Admin Management System
- [ ] Payment gateway
- [ ] Legal pages

## Credentials
- Email: test@agentflow.com / Password: password123
