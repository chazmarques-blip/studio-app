# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform for businesses to deploy AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features omnichannel inbox, AI-powered marketing campaigns, CRM, and multi-language support.

## Core Architecture
- **Frontend:** React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + MongoDB (flexible-schema features)
- **AI Models:** Claude Sonnet 4.5 (text), Gemini Nano Banana (image), Sora 2 (video), OpenAI TTS HD (narration)
- **Video Processing:** FFmpeg (crossfade, audio mixing, logo overlay)

## Implemented Features

### Phase 1-5: Core Platform (Complete)
- User auth, Dashboard, Agent Management, Marketplace
- Agent Configuration with Google Calendar/Sheets integration
- CRM with Kanban board
- Multi-language UI (EN, PT, ES) via i18next

### Phase 6: Google Integration (Complete)
- Google account connection, Calendar/Sheets selection per agent

### Phase 7: AI Marketing Studio (Complete)
- Multi-agent pipeline: Sofia (copy) → Ana (review) → Lucas (design) → Rafael (QA) → Marcos (video) → Pedro (publish)
- Text generation (Claude Sonnet 4.5)
- Image generation (Gemini Nano Banana)
- Video generation (Sora 2 + TTS + FFmpeg)

### Video Pipeline V5 (Complete - Mar 14, 2026)
- 2x 12s Sora 2 clips with crossfade transition
- Energetic TTS narration (Nova voice, 1.08x speed)
- Background music mixing (30% volume)
- Brand logo overlay in last 4 seconds
- Narration timing: ends by ~19s, last 4s = music + logo only
- Narration cleaned of stage directions (SILENCE markers)

### i18n Full Translation (Complete - Mar 14, 2026)
- Marketing.jsx: L(lang) function with EN/PT/ES for all labels
- PipelineView.jsx: t() with studio.* keys for all UI text
- FinalPreview.jsx: t() for publish/edit/back labels
- Locale files (en.json, pt.json, es.json) updated with 40+ studio keys
- No Portuguese hardcoded text remaining when English selected

## Current Test User
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Upcoming Tasks (Prioritized)

### P0: Company Info Fields
- Add website, phone, email, address to campaign creation flow
- Pass to agent pipeline for CTA personalization

### P1: Adaptive Media Formats
- Generate images/videos in correct aspect ratios per channel
- 9:16 for TikTok/Reels, 16:9 for Google Ads, 1:1 for Facebook

### P2: Music Library by Mood
- Expand /app/backend/assets/music/ with categorized tracks
- Sofia selects mood → Marcos picks track

## Future Tasks
- Creative Gallery for asset reuse
- Affiliate Program / Viral Loop
- Evaluate advanced video AI (Runway Gen-3, Google Veo, Kling)
- Mobile app (Capacitor)
- Admin Management System
- Payment gateway (Stripe)
- Omnichannel live integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)

## Key Files
- `/app/backend/routers/pipeline.py` - Core AI pipeline (~1800 lines)
- `/app/frontend/src/pages/Marketing.jsx` - Campaign hub with i18n
- `/app/frontend/src/components/PipelineView.jsx` - AI Studio UI
- `/app/frontend/src/components/FinalPreview.jsx` - Campaign publish preview
- `/app/backend/assets/brand_logo.png` - My Truck logo (13134x13321px)
- `/app/backend/assets/music/upbeat.mp3` - Background music track

## Areas Needing Refactoring
- pipeline.py is ~1800 lines - needs breakdown into modules
- MongoDB client centralization
