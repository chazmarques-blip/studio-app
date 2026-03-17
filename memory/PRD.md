# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Gemini 3 Pro (image), Gemini 2.5 Flash (vision/critic), OpenAI TTS, fal.ai Kling (lip-sync)
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
- **Manual Campaign Sharing** - Share Bar with image selector, text editor, and deep links for WhatsApp, Facebook, Telegram, Instagram, Email

## Completed - March 2026
- [x] Data persistence migrated from localStorage to Supabase
- [x] Dual Upload (Photo + Video) for enhanced identity accuracy
- [x] Image Accuracy Agent with visual Agent Timeline
- [x] Default "Company Uniform" outfit
- [x] Fixed Critic JSON parsing bug - regex-first score extraction
- [x] Lowered accuracy threshold from 8 to 7
- [x] Real logo compositing - company logo via PIL + numpy background removal
- [x] logo_url parameter added to all 3 avatar endpoints
- [x] EDIT-based generation prompt for better identity preservation (9/10 similarity)
- [x] **Share Bar** - "Compartilhar Agora" with image selector, editable text, copy button, and 5 platform share buttons

## Backlog (Priority Order)
### P1 - Technical Debt
- [ ] Refactor pipeline.py (>4800 lines) into modules: avatar.py, video.py, audio.py, steps.py
- [ ] Refactor PipelineView.jsx (~3100 lines) into smaller components

### P2 - Features
- [ ] Rename AI agents in pipeline
- [ ] Redesign Landing/Login page
- [ ] AI Marketing Studio campaigns (Phase 7)
- [ ] Automated campaign sharing (scheduling)

### P3 - Future
- [ ] CRM with Kanban board
- [ ] Omnichannel integrations (WhatsApp, Instagram, Facebook, Telegram, SMS)
- [ ] Admin Management System
- [ ] Payment gateway (Stripe)
- [ ] Legal pages (Terms, Privacy)

## Key API Endpoints
- POST /api/campaigns/pipeline/generate-avatar-with-accuracy (logo_url, video_frame_urls)
- GET /api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id}
- POST /api/campaigns/pipeline/generate-avatar-variant (logo_url)
- POST /api/campaigns/pipeline/generate-avatar-360 (logo_url)
- GET/POST /api/data/companies
- GET/POST /api/data/avatars
- GET /api/campaigns
- GET /api/dashboard/stats

## Credentials
- Email: test@agentflow.com / Password: password123
