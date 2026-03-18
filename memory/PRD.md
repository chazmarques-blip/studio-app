# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Gemini 3 Pro (image), Gemini 2.5 Flash (vision/critic), OpenAI TTS, fal.ai Kling (lip-sync), ElevenLabs TTS
- Video: Sora 2 (via Emergent Integrations)
- Storage: Supabase Storage (pipeline-assets bucket)

## Key Features Implemented
- Dashboard with recharts analytics
- Agent Marketplace with plan-gating
- Google Calendar/Sheets integration in Agent Config
- Data persistence in Supabase (companies, avatars in tenants.settings JSONB)
- Dual-source avatar generation (photo + video)
- Iterative AI Accuracy Agent (Describer -> Artist -> Critic loop)
- EDIT-based generation prompt (identity preservation)
- Real company logo compositing via PIL (black background auto-removal with numpy)
- logo_url parameter on all 3 avatar endpoints (accuracy, variant, 360)
- Cache-busting for Supabase Storage URLs
- Agent Timeline UI for generation progress
- Default "Company Uniform" outfit
- Voice Mastering, Voice Bank (TTS), Custom Recording
- Avatar Video Preview (5s lip-sync via fal.ai)
- Automatic 360 generation
- Sora-based Presenter Mode
- Multi-language support (EN, PT, ES)
- Unified Share Area - Select media (images + video), edit text, share as FILE (blob)
- ElevenLabs TTS Integration for video narration
- Scale-to-fit + padding for image/video format conversion (no cropping)
- Two-tab campaign detail (Content | Results)
- Per-platform video variants (WhatsApp 1:1, Instagram 1:1, Facebook 16:9, TikTok 9:16)

## Completed - March 18, 2026 (Latest Session)
- [x] **Bug Fix: Campaign auto-save failure** — Removed `language` field from Supabase campaigns INSERT. The `language` column doesn't exist in the campaigns table schema, causing ALL auto-saves to fail silently. Campaign language is now correctly stored in `stats.campaign_language` (JSONB field).
- [x] **Bug Fix: Image regeneration language regression** — Replaced English-language prompt template ("Create a stunning marketing visual for:") with language-specific templates (PT/ES/EN). Now extracts headline from campaign copy and instructs the model to use it exactly. Tested: regenerated image correctly shows Portuguese text "Força e Fé: Dose diária de inspiração".
- [x] **Bug Fix: FinalPreview i18n key** — Fixed wrong i18n key `studio.video_generating` to correct `studio.generating_video` in FinalPreview.jsx.
- [x] **Published orphaned campaign** — The "Amigas na luta" pipeline (dea6ebbb) had no campaign entry due to the auto-save bug. Manually published to create campaign 068141ee with campaign_language: pt.
- [x] **Added campaign_language to publish endpoint stats** — Ensured the publish endpoint saves campaign_language in stats for future regenerations.

## Previous Session Completions
- Avatar generation fix (JSON parsing, threshold 7, EDIT-based prompt, 9/10 similarity)
- Real logo compositing via PIL + numpy background removal
- Unified Share Area with Web Share API
- Image regeneration language enforcement
- i18n for FinalPreview and Campaign Detail
- Layout Redesign: Campaign Detail Modal (2-tab)
- Video format per channel
- Video Adjustments UI
- ElevenLabs TTS Integration
- Image/Video format scaling (scale-to-fit + padding)
- Video variants on regeneration
- All 8 platforms selected by default
- Ridley prompt overhaul (narration vs visual separation)
- Narration cleanup hardened
- Audio speed cap reduced (1.15x max)
- Roger prompt enhanced (V2-V4 criteria)

## Known Issues
- **Sora 2 Video Generation API DOWN** — Returns 500 Server Error. External service issue, not our code. Videos cannot be generated until the API is restored.

## Backlog (Priority Order)
### P0 - Current
- [ ] Create new test campaign to validate full pipeline end-to-end (blocked by Sora 2 API)
- [ ] Verify video branding (logo/contact overlay) once Sora 2 API is back

### P1 - Technical Debt
- [ ] Refactor pipeline.py (>5100 lines) into modules
- [ ] Refactor PipelineView.jsx (~3100 lines) into smaller components

### P2 - Features
- [ ] Automated campaign sharing (scheduling)
- [ ] Rename AI agents in pipeline
- [ ] Redesign Landing/Login page
- [ ] Ultra-Realistic Avatar Integration (HeyGen)

### P3 - Future
- [ ] CRM with Kanban board
- [ ] Omnichannel integrations
- [ ] Admin Management System
- [ ] Payment gateway
- [ ] Legal pages

## Key API Endpoints
- POST /api/campaigns/pipeline/generate-avatar-with-accuracy
- POST /api/campaigns/pipeline/generate-avatar-variant
- POST /api/campaigns/pipeline/generate-avatar-360
- POST /api/campaigns/pipeline/regenerate-single-image
- POST /api/campaigns/pipeline/{id}/regenerate-video
- POST /api/campaigns/pipeline/{id}/publish
- GET/POST /api/data/companies
- GET/POST /api/data/avatars
- GET /api/campaigns
- GET /api/dashboard/stats

## Credentials
- Email: test@agentflow.com / Password: password123
