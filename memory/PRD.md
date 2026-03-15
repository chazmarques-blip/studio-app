# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a comprehensive, mobile-first, no-code SaaS platform for SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio with multi-agent video/image generation pipeline, omnichannel inbox, CRM, and admin system.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Lucide Icons + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB for flexible-schema features
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana, Sora 2, OpenAI TTS, Google APIs, FFmpeg
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage

## What's Been Implemented

### Core Platform
- Landing page with pricing, auth system, dashboard with recharts analytics
- Agent management with marketplace, configuration, Google Calendar/Sheets integration
- CRM with Kanban board, multi-language support (EN/PT/ES)
- Dark luxury theme (monochrome gold/black/white)

### AI Marketing Studio (Phase 7) - COMPLETE
- Multi-agent pipeline: Sofia (Copy) -> Ana (Reviewer) -> Lucas (Design) -> Rafael (Ad Manager) -> Marcos (Video) -> Pedro (Publisher)
- **Revision Loop**: When Ana or Rafael detect critical errors (wrong language, quality issues), pipeline loops BACK to Sofia/Lucas for correction (max 2 revision rounds)
- Robust review detection: Explicit DECISION tags + implicit signals (PROBLEMA CRITICO, WRONG LANGUAGE, low scores)
- Image generation via Gemini Nano Banana with MANDATORY LANGUAGE RULE enforcement
- Video generation via Sora 2 (2 clips x 12s = 23s with crossfade) + TTS narration + FFmpeg mixing
- Logo overlay with brand info in final video frame
- Background music library: 25 tracks in 9 categories with genre tab selector + scrollable UI
- Enhanced questionnaire: Gender, Age Range, Social Class, Lifestyle (12 tags), Pain Points, Visual Style (8 options)
- Campaign Content tab with video player, format badges per channel, Generate Video button
- Full internationalization (EN/PT/ES) including all UI text and Google Ads/Facebook previews
- Company contact info fields (phone, email, website, address)
- Adaptive media formats per channel (1:1, 9:16, 16:9, 1.91:1 badges)

### Recent Updates (March 15, 2026)
- Agent revision loop with robust detection of implicit rejection signals
- Enhanced questionnaire with 10 questions + selectable fields (gender, age, social class, lifestyle, pain points, visual style)
- Music library expanded to 25 tracks in 9 categories with compact genre-tab UI + scroll
- Video duration fixed (12s -> 23s), FFmpeg logo overlay fixed
- Format badges per channel in Content tab
- i18n fixes for all hardcoded Portuguese text

## Prioritized Backlog

### P0 (Critical)
- Replace synthetic music tracks with real royalty-free audio files (20 tracks still synthetic)
- Video post-review step (Rafael validates video after Marcos generates it)

### P1 (High)
- Phase 8: Omnichannel Integrations (WhatsApp Evolution API, SMS Twilio, Instagram, Facebook, Telegram)
- Admin Management System (full admin dashboard)
- Payment Gateway Integration (Stripe)

### P2 (Medium)
- Creative Gallery (browse/reuse generated assets)
- Channel-specific image/video generation (different aspect ratios per channel)
- Refactor pipeline.py (~2100 lines -> smaller modules)

### P3 (Low)
- Mobile App (Capacitor)
- Terms of Use / Privacy Policy
- Scalability hardening
- A/B testing automation for campaigns

## Test Reports
- /app/test_reports/iteration_29.json (questionnaire + music + content tab - 100% pass)
- /app/test_reports/iteration_30.json (revision loop + genre tabs + scroll - 100% pass)

## Credentials
- Email: test@agentflow.com
- Password: password123
