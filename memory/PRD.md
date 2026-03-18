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

## Key Features Implemented
- Dashboard with recharts analytics
- Agent Marketplace with plan-gating
- Google Calendar/Sheets integration in Agent Config
- Data persistence in Supabase
- Dual-source avatar generation (photo + video)
- Iterative AI Accuracy Agent (Describer -> Artist -> Critic loop)
- EDIT-based generation prompt (identity preservation)
- Real company logo compositing via PIL
- Agent Timeline UI for generation progress
- Voice Mastering, Voice Bank (TTS), Custom Recording
- Avatar Video Preview (5s lip-sync via fal.ai)
- Automatic 360 generation
- Multi-language support (EN, PT, ES)
- Unified Share Area
- ElevenLabs TTS Integration for video narration
- Scale-to-fit + padding for image/video format conversion
- Two-tab campaign detail (Content | Results)
- Per-platform video variants (8 platforms)

## Completed - March 18, 2026 (Current Session)
- [x] **Bug Fix: Campaign auto-save failure** — Removed `language` column from campaigns INSERT
- [x] **Bug Fix: Image language regression** — Language-specific prompt templates (PT/ES/EN) instead of English-only
- [x] **Bug Fix: FinalPreview i18n key** — Fixed `studio.video_generating` → `studio.generating_video`
- [x] **Bug Fix: Publish uses all images** — Changed `image_urls` → `images` to include regenerated images
- [x] **Feature: 14 Style Filters** — Added 6 new: Cartoon, Illustration, Watercolor, Neon, Retro, Flat Design
- [x] **Feature: Edit Image Text** — New endpoint `/api/campaigns/pipeline/edit-image-text` to change text on existing image while keeping style
- [x] **Feature: Language from Campaign** — Frontend now uses `stats.campaign_language` (not user's UI language)
- [x] **Improvement: Pipeline Auto-Recovery** — Added stuck step detection in GET and LIST endpoints (handles pending + timeout scenarios)
- [x] **Campaign Recreation** — New "Amigas na luta" campaign created via pipeline (a3165a97) with Portuguese content

## Known Issues
- **Sora 2 Video Generation API DOWN** — Returns 500 Server Error. External service issue.
- **Pipeline steps can get stuck** — Auto-recovery added but depends on GET/LIST calls

## Backlog (Priority Order)
### P0 - Current
- [ ] Verify video branding once Sora 2 API is back
- [ ] Test full campaign with working video generation

### P1 - Technical Debt
- [ ] Refactor pipeline.py (>5300 lines) into modules
- [ ] Refactor PipelineView.jsx (~3100 lines)

### P2 - Features
- [ ] Automated campaign sharing
- [ ] Redesign Landing/Login page
- [ ] Ultra-Realistic Avatar (HeyGen)

### P3 - Future
- [ ] CRM with Kanban board
- [ ] Omnichannel integrations
- [ ] Admin Management System
- [ ] Payment gateway
- [ ] Legal pages

## Key API Endpoints
- POST /api/campaigns/pipeline/regenerate-single-image (14 styles)
- POST /api/campaigns/pipeline/edit-image-text (new)
- POST /api/campaigns/pipeline/{id}/publish
- POST /api/campaigns/pipeline/{id}/approve
- POST /api/campaigns/pipeline (create pipeline)
- GET /api/campaigns/pipeline/list (with auto-recovery)
- GET /api/campaigns/pipeline/{id} (with auto-recovery)
- GET /api/campaigns
- GET /api/dashboard/stats

## Credentials
- Email: test@agentflow.com / Password: password123
