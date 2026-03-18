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
- **Unified Share Area** - Select media (images + video), edit text, share as FILE (blob) via Web Share API to WhatsApp, Instagram, Facebook, Telegram, Email

## Completed - March 2026
- [x] Avatar generation fix (JSON parsing, threshold 7, EDIT-based prompt, 9/10 similarity)
- [x] Real logo compositing via PIL + numpy background removal
- [x] **Unified Share Area** replacing old separate sections:
  - Selectable media gallery (images + video) with gold check indicator
  - Editable text area with copy button
  - 5 platform share buttons using Web Share API with file blobs for native mobile sharing
  - Fallback to deep links on desktop
- [x] **Fix: Image regeneration language enforcement** — Strengthened language instructions in all image generation/regeneration prompts. Language instruction now appears as FIRST/DOMINANT rule in the prompt, preventing AI from defaulting to English when campaign is in Spanish/Portuguese/etc. Fixed in: `/regenerate-single-image`, `/{pipeline_id}/regenerate-image`, and `_generate_design_images`.
- [x] **Fix: i18n for FinalPreview** — Replaced all hardcoded Portuguese labels ("IMAGEM:", "GERAR NOVA IMAGEM COM ESTILO", "Minimalista", "Vibrante", etc.) with i18n translation keys. Now correctly displays in EN/PT/ES based on user's platform language setting.
- [x] **Layout Redesign: Campaign Detail Modal** — Eliminated the 3-tab layout (Overview/Content/Results). Overview KPIs are now a compact inline strip in the header. Content and Results are displayed side-by-side in a split-panel layout. Schedule and Message Flow moved to the Results panel. Modal widened to max-w-5xl for the two-column view.
- [x] **Fix: Video format per channel** — Videos now display correctly per channel format (WhatsApp 1:1, Instagram 1:1, Facebook 16:9, TikTok 9:16) using `object-contain` instead of `object-cover` (which was cropping). Backend `regenerate-video` endpoint now also creates per-platform video variants.
- [x] **P0: Video Adjustments UI** — Added "VIDEO ADJUSTMENTS" section with textarea for user feedback and "Regenerate Video" button. Also added "Update Formats" button for campaigns missing video_variants.
- [x] **Fix: i18n for all Campaign Detail labels** — Replaced all remaining hardcoded PT labels (Imagem, Video, Curtir, Comentar, Compartilhar, Selecionar Midia, Copiar) with i18n labels in EN/PT/ES.
- [x] **ElevenLabs TTS Integration** — Integrated ElevenLabs as primary TTS engine for video narration with OpenAI TTS as fallback. Features: multilingual v2 model, voice selection (6 voice types), tone control (energetic/calm/warm/dramatic), stability/style parameters auto-configured by AI director "Ridley". Added `===NARRATION TONE===` section to Ridley's output format.
- [x] **Fix: Image/Video format scaling** — Changed from crop-based resizing to scale-to-fit + black padding for both images (PIL) and videos (FFmpeg). All content is now preserved without cropping when converting between aspect ratios (1:1, 9:16, 16:9).
- [x] **Fix: Video variants on regeneration** — The `regenerate-video` endpoint now creates per-platform video variants (was only saving master URL before).
- [x] **All 8 platforms selected by default** — New campaigns now default to all platforms (WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS).

## Backlog (Priority Order)
### P1 - Technical Debt
- [ ] Refactor pipeline.py (>4800 lines) into modules
- [ ] Refactor PipelineView.jsx (~3100 lines) into smaller components

### P2 - Features
- [ ] Automated campaign sharing (scheduling)
- [ ] Rename AI agents in pipeline
- [ ] Redesign Landing/Login page

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
- GET/POST /api/data/companies
- GET/POST /api/data/avatars
- GET /api/campaigns
- GET /api/dashboard/stats

## Credentials
- Email: test@agentflow.com / Password: password123
