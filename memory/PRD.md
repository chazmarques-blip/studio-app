# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Gemini 3 Pro (image), Gemini 2.5 Flash (vision/critic), Gemini 2.0 Flash (AI Director), OpenAI TTS, fal.ai Kling (lip-sync), ElevenLabs TTS
- Video: Sora 2 (via Emergent Integrations)
- Storage: Supabase Storage (pipeline-assets bucket)

## Code Architecture (Post-Refactoring)

### Backend Pipeline Package (`/app/backend/pipeline/`)
| Module | Lines | Responsibility |
|--------|-------|----------------|
| `config.py` | 636 | Constants, Pydantic models, configuration |
| `utils.py` | 413 | Storage, text parsing, AI utilities |
| `prompts.py` | 461 | AI agent prompt construction |
| `media.py` | ~1450 | Image/video generation, AI Director, variants |
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
| `PipelineView.jsx` | 2346 | Main studio component |

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
- ElevenLabs Premium Voices for Avatars
- Scale-to-fit + padding for image/video format conversion
- Two-tab campaign detail (Content | Results)
- Per-platform video variants (8 platforms)
- 14 Image Generation Styles
- Edit Image Text (change headline without regenerating)
- Pipeline auto-recovery for stuck steps
- **Art Gallery with Fixed Player + Scrollable Grid** (NEW)
- **AI Image Director** for smart video cropping per platform (NEW)

## Completed - March 19, 2026 (Latest Session)

### Art Gallery UI Rearchitecture
- [x] Redesigned GlobalArtGallery component in Marketing.jsx
- [x] Fixed player area at top: shows selected asset with full channel preview
- [x] 8 channel preview tabs: Original, IG Feed, IG Reels, TikTok, Facebook, YouTube, WhatsApp, Stories
- [x] Device mockups (phone 9:16, feed 4:5, widescreen 16:9) with UI overlays
- [x] Action bar: Download, Share, Use in Campaign, Close
- [x] Scrollable thumbnail grid below (6 columns) with gold selection indicator
- [x] Placeholder prompt when no asset selected
- [x] Tested: 15/15 frontend tests (iteration_72)

### AI Image Director (Backend)
- [x] New `_ai_analyze_video_for_crops()` function in pipeline/media.py
- [x] Uses Gemini 2.0 Flash with vision to analyze 3 keyframes from master video
- [x] Generates optimal crop regions per platform (maintains aspect ratio, centers subjects)
- [x] Updated `_create_video_variants()` to use AI-directed crops when available
- [x] Graceful fallback to generic scale+pad when AI analysis fails
- [x] Tested: 15/15 backend tests (iteration_72)

### Previous Session Completions
- [x] ElevenLabs Premium Voices for Avatars (backend + frontend)
- [x] Global Art Gallery: unified view of all images/videos
- [x] Art Gallery Channel Preview with device mockups
- [x] Avatar Creator Enhancement (3 modes: Photo, Prompt, 3D Animated)
- [x] Video Format & Branding Update (8+ platforms with exact dimensions)
- [x] Test Campaign: AgentZZ Super Hero (full end-to-end)
- [x] Backend refactoring: pipeline.py decomposed into 9 modules
- [x] Frontend refactoring: PipelineView.jsx decomposed, 8 sub-components

## Known Issues
- **Sora 2 Video Generation API** - Reported stable (needs re-verification)
- **Pipeline steps can get stuck** - Auto-recovery added (GET/LIST triggers)

## Backlog (Priority Order)
### P0
- [ ] Verify video branding once Sora 2 is back
- [ ] Test full campaign with AI Director video variants

### P1 - Features
- [ ] Optimized Export Flow (decouple video variant creation from pipeline)
- [ ] Refactor PipelineView.jsx (reduce complexity ~2500 lines)
- [ ] Automated campaign sharing
- [ ] Redesign Landing/Login page

### P2 - Features
- [ ] Ultra-Realistic Avatar (HeyGen)
- [ ] CRM with Kanban board
- [ ] Login Social / Google Auth

### P3 - Future
- [ ] Omnichannel integrations (WhatsApp, SMS, etc.)
- [ ] Admin Management System
- [ ] Payment gateway
- [ ] Legal pages

## Credentials
- Email: test@agentflow.com / Password: password123
