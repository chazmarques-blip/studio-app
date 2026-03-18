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
- Iterative AI Accuracy Agent
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
- 14 Image Generation Styles (Minimalist, Vibrant, Luxury, Corporate, Playful, Bold, Organic, Tech, Cartoon, Illustration, Watercolor, Neon, Retro, Flat Design)
- Edit Image Text (change headline without regenerating entire image)
- Pipeline auto-recovery for stuck steps

## Completed - March 18, 2026 (Current Session)
### Bug Fixes
- [x] Campaign auto-save failure — Removed `language` column from INSERT
- [x] Image language regression — Language-specific prompt templates (PT/ES/EN)
- [x] FinalPreview i18n key — `studio.video_generating` → `studio.generating_video`
- [x] Publish uses all images — `image_urls` → `images` (includes regenerated)
- [x] Avatar language not loading — Added `language` field to AvatarIn model + load on edit
- [x] Avatar audio not loading — Restored `recordedAudioUrl` from `av.voice.url` on edit
- [x] Button nesting HTML fix — Changed outer `<button>` to `<div>` in campaign image grid

### New Features
- [x] 14 Style Filters (6 new: Cartoon, Illustration, Watercolor, Neon, Retro, Flat Design)
- [x] Edit Image Text endpoint (`POST /api/campaigns/pipeline/edit-image-text`)
- [x] Language from Campaign (not user UI language)
- [x] Pipeline Auto-Recovery in GET + LIST endpoints
- [x] New campaign "Amigas na luta" (a3165a97) with Portuguese content
- [x] Avatar data includes language field (saved + loaded on edit)

## Known Issues
- **Sora 2 Video Generation API DOWN** — Returns 500 Server Error. External issue.
- **Pipeline steps can get stuck** — Auto-recovery added (GET/LIST triggers)

## Backlog (Priority Order)
### P0
- [ ] Verify video branding once Sora 2 is back
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

## Credentials
- Email: test@agentflow.com / Password: password123
