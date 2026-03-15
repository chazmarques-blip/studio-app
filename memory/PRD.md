# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a comprehensive, mobile-first, no-code SaaS platform for SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio with multi-agent video/image generation pipeline, omnichannel inbox, CRM, and admin system.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Lucide Icons + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB for flexible-schema features
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, Google APIs, FFmpeg, PIL/Pillow
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage

## What's Been Implemented

### Core Platform
- Landing page with pricing, auth system, dashboard with recharts analytics
- Agent management with marketplace, configuration, Google Calendar/Sheets integration
- CRM with Kanban board, multi-language support (EN/PT/ES)
- Dark luxury theme (monochrome gold/black/white)

### AI Marketing Studio (Phase 7) - COMPLETE
- Multi-agent pipeline: Sofia (Copy) -> Ana (Review) -> Lucas (Design) -> Rafael (Review Design) -> Marcos (Video) -> Rafael (Review Video) -> Pedro (Publisher)
- **Optimized Revision Loop**: Max 1 revision per review step (was 2). Review agents use Gemini Flash for speed (~10s vs ~60s). Creative agents use Claude Sonnet 4.5 for quality.
- **Post-Video Validation**: Rafael reviews video script after Marcos generates it. Can reject and loop back to Marcos.
- **Adaptive Media Formats**: PIL-based image resizing creates platform-specific variants:
  - TikTok: 9:16 (768x1344)
  - Google Ads: 16:9 (1344x768)
  - Instagram/WhatsApp/Facebook: 1:1 (1024x1024)
- Robust review detection: Explicit DECISION tags + implicit rejection signals
- Image generation via Gemini Nano Banana with MANDATORY LANGUAGE RULE enforcement
- Video generation via Sora 2 (2 clips x 12s = 23s with crossfade) + TTS narration + FFmpeg mixing
- Background music library: 25 real royalty-free tracks in 9 categories
- Enhanced questionnaire: Gender, Age Range, Social Class, Lifestyle, Pain Points, Visual Style
- Campaign Content tab with channel-specific mockups using platform variants
- Full internationalization (EN/PT/ES)

### Updates (March 15, 2026 - Current Session)
- Optimized review loop: Reviews use Gemini Flash, max 1 revision, ~5x faster
- Post-video validation by Rafael with revision loop to Marcos
- Adaptive media formats: PIL resizes base images for TikTok (9:16), Google Ads (16:9)
- Platform variants stored in campaign metrics and used in frontend mockups
- Frontend PipelineView shows all 7 steps including rafael_review_video
- Platform variant badges displayed in PipelineView after image generation

## Prioritized Backlog

### P0 (Critical)
- Verify language mismatch fix in generated images (testing pending with new generation)
- Video fullscreen button verification

### P1 (High)
- Phase 8: Omnichannel Integrations (WhatsApp Evolution API, SMS Twilio, Instagram, Facebook, Telegram)
- Admin Management System (full admin dashboard)
- Payment Gateway Integration (Stripe)

### P2 (Medium)
- Creative Gallery (browse/reuse generated assets)
- Refactor pipeline.py (~2400 lines -> smaller modules)
- Advanced Video AI Evaluation (Runway Gen-3, Google Veo, Kling)

### P3 (Low)
- Mobile App (Capacitor)
- Terms of Use / Privacy Policy
- Scalability hardening
- A/B testing automation for campaigns

## Test Reports
- /app/test_reports/iteration_29.json (questionnaire + music + content tab - 100% pass)
- /app/test_reports/iteration_30.json (revision loop + genre tabs + scroll - 100% pass)
- /app/test_reports/iteration_31.json (pipeline review system + platform variants - 100% pass)

## Credentials
- Email: test@agentflow.com
- Password: password123
