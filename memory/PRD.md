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
- Multi-agent pipeline: Sofia → Ana → Lucas → Rafael → Marcos → Pedro
- Text (Claude Sonnet 4.5), Image (Nano Banana), Video (Sora 2 + TTS + FFmpeg)

### Video Pipeline V6 (Mar 14, 2026)
- 2x 12s Sora 2 clips with crossfade transition (23s total)
- Energetic TTS narration (Nova voice, 1.08x, ends ~14s before video end)
- Background music by mood (upbeat/energetic/emotional/cinematic/corporate)
- Audio resampled to 44100Hz stereo before mixing (fixed buzzing issue)
- Brand logo overlay: fully opaque black background (1.0), logo 240px centered
- Tagline + contact CTA positioned below logo
- Narration cleaned of [SILENCE] stage directions

### P0: Company Info Fields (Mar 14, 2026)
- Added Address field to Contact Data section (Phone, Website, Email, Address)
- Contact info (including address) passed to agent pipeline for CTA personalization
- Backend PipelineCreate model updated to accept address in contact_info

### P1: Adaptive Media Formats (Mar 14, 2026)
- Platform definitions include imgRatio, vidRatio, imgSize, vidSize per channel
- Formats: 9:16 (TikTok/Instagram/WhatsApp), 16:9 (Google Ads/Facebook/Telegram), 1:1 (Facebook/WhatsApp)
- media_formats dict sent to backend and stored in pipeline result
- Format instructions injected into Sofia, Lucas, and Marcos agent prompts

### P2: Music Library by Mood (Mar 14, 2026)
- 5 mood-categorized tracks in /app/backend/assets/music/
- Mood mapping: upbeat, energetic, emotional, cinematic, corporate
- Sofia specifies mood in VIDEO BRIEF → Marcos confirms → _combine_commercial_video selects track

### i18n Full Translation (Mar 14, 2026)
- Marketing.jsx: L(lang) function with EN/PT/ES for 50+ labels
- PipelineView.jsx: t() with studio.* keys for all UI text
- FinalPreview.jsx: t() for publish/edit/back labels
- Locale files updated with 70+ studio keys across 3 languages

## Current Test User
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Upcoming Tasks

### User Verification Pending
- Verify V6 video quality (music, logo, narration)
- URL: https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/videos/new_v6_commercial.mp4

## Future Tasks
- Creative Gallery for asset reuse
- Affiliate Program / Viral Loop
- Evaluate advanced video AI (Runway Gen-3, Google Veo, Kling via fal.ai)
- Mobile app (Capacitor)
- Admin Management System
- Payment gateway (Stripe)
- Omnichannel live integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- pipeline.py refactoring (~1900 lines → smaller modules)

## Key Files
- `/app/backend/routers/pipeline.py` - Core AI pipeline (~1900 lines)
- `/app/frontend/src/pages/Marketing.jsx` - Campaign hub with i18n
- `/app/frontend/src/components/PipelineView.jsx` - AI Studio UI
- `/app/frontend/src/components/FinalPreview.jsx` - Campaign publish preview
- `/app/backend/assets/brand_logo.png` - My Truck logo
- `/app/backend/assets/music/` - 5 mood-categorized music tracks

## Test Reports
- /app/test_reports/iteration_25.json
- /app/test_reports/iteration_26.json
- /app/test_reports/iteration_27.json (100% pass)
