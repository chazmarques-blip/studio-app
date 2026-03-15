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
- Multi-agent pipeline: Sofia (Copy) → Ana (Reviewer) → Lucas (Design) → Rafael (Ad Manager) → Marcos (Video) → Pedro (Publisher)
- Image generation via Gemini Nano Banana with language-enforced prompts
- Video generation via Sora 2 (2 clips × 12s = 23s with crossfade) + TTS narration + FFmpeg mixing
- Background music library: 25 royalty-free tracks in 9 categories (General, Pop, Hip-Hop, Electronic, Latin, Rock, Jazz, Ambient, Other)
- Enhanced questionnaire with selectable fields: Gender, Age Range, Social Class, Lifestyle, Pain Points, Visual Style
- Campaign Content tab with video player, format badges per channel, and "Generate Video" button for retry
- Full internationalization (EN/PT/ES) including all UI text, agent prompts, and Google Ads previews
- Company contact info fields (phone, email, website, address)
- Adaptive media formats per channel

### Recent Fixes (March 14, 2026)
- Fixed video not appearing in campaign Content tab (auto-link to campaign after generation)
- Fixed FFmpeg not found (installed + absolute path /usr/bin/ffmpeg)
- Fixed video duration (12s → 23s, crossfade combining was silently failing)
- Fixed logo overlay (relative URL → absolute URL for download)
- Fixed hardcoded Portuguese text in Google Ads and Facebook previews (Patrocinado → Sponsored)
- Added CSS fullscreen fix for video player in modals
- Strengthened language enforcement in ALL agent prompts (MANDATORY LANGUAGE RULE)
- Added format badges per channel (WhatsApp 1:1, TikTok 9:16, Facebook 16:9, Google Ads 1.91:1)
- Created PUT /api/campaigns/{id}/video endpoint for manual video linking
- Created POST /api/campaigns/pipeline/{id}/regenerate-video endpoint

## Prioritized Backlog

### P0 (Critical)
- None currently

### P1 (High)
- Phase 8: Omnichannel Integrations (WhatsApp Evolution API, SMS Twilio, Instagram, Facebook, Telegram)
- Admin Management System (full admin dashboard)
- Payment Gateway Integration (Stripe)

### P2 (Medium)
- Creative Gallery (browse/reuse generated assets)
- Advanced Video AI Evaluation (Runway Gen-3, Google Veo, Kling)
- Refactor pipeline.py (~2000 lines → smaller modules)

### P3 (Low)
- Mobile App (Capacitor)
- Terms of Use / Privacy Policy
- Scalability hardening

## Key API Endpoints
- POST /api/pipeline/create - Start campaign generation
- GET /api/campaigns/pipeline/music-library - List 25 music tracks
- GET /api/campaigns/pipeline/music-preview/{track_id} - Preview music
- PUT /api/campaigns/{id}/video - Link video to campaign
- POST /api/campaigns/pipeline/{id}/regenerate-video - Regenerate video
- GET /api/campaigns - List all campaigns
- GET /api/campaigns/{id} - Get campaign detail

## Test Reports
- /app/test_reports/iteration_28.json (i18n + music library - 100% pass)
- /app/test_reports/iteration_29.json (questionnaire + music + content tab - 100% pass)

## Credentials
- Email: test@agentflow.com
- Password: password123
