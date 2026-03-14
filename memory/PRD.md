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
- CRM with Kanban board, Multi-language UI (EN, PT, ES)

### Phase 6: Google Integration (Complete)

### Phase 7: AI Marketing Studio (Complete)
- Multi-agent pipeline: Sofia → Ana → Lucas → Rafael → Marcos → Pedro

### Video Pipeline V7 (Mar 14, 2026)
- 2x 12s Sora 2 clips with crossfade (23s total)
- TTS narration (Nova voice, 1.08x) — cleaned of [SILENCE] stage directions
- REAL background music (royalty-free from Pixabay CDN, resampled 44100Hz stereo)
- Brand logo overlay: fully opaque black bg, logo 240px centered
- Contact: (321) 960-2080 | mytruckflorida.com

### P0: Company Info Fields (Complete)
- 4 fields: Phone, Website, Email, Address
- Passed to agent pipeline for CTA personalization

### P1: Adaptive Media Formats (Complete)
- 8 platforms with imgRatio/vidRatio/imgSize/vidSize
- 9:16 (TikTok/Instagram), 16:9 (Google Ads), 1:1 (Facebook)
- media_formats sent to backend → injected in agent prompts

### P2: Music Library (Complete)
- 5 real tracks: Upbeat, Energetic, Emotional, Cinematic, Corporate
- UI: Selectable list with play/pause preview buttons
- API: GET /api/campaigns/pipeline/music-library (list tracks)
- API: GET /api/campaigns/pipeline/music-preview/{id} (stream audio)
- Pipeline: selected_music field → overrides AI mood selection
- Mood mapping in _combine_commercial_video for auto-selection

### i18n Full Translation (Complete)
- Marketing.jsx: L(lang) with EN/PT/ES
- PipelineView.jsx: t() with 70+ studio.* keys
- FinalPreview.jsx: t() for all buttons

## Test User
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## User Verification Pending
- V7 Video: https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/videos/new_v7_commercial.mp4

## Future Tasks
- Creative Gallery for asset reuse
- Affiliate Program / Viral Loop
- Evaluate advanced video AI (Runway Gen-3, Google Veo, Kling)
- Mobile app (Capacitor)
- Admin Management System
- Payment gateway (Stripe)
- Omnichannel live integrations
- pipeline.py refactoring (~2000 lines → modules)

## Key Files
- /app/backend/routers/pipeline.py - Core AI pipeline
- /app/frontend/src/pages/Marketing.jsx - Campaign hub
- /app/frontend/src/components/PipelineView.jsx - AI Studio UI
- /app/backend/assets/music/ - 5 music tracks
- /app/backend/assets/brand_logo.png - My Truck logo

## Test Reports
- /app/test_reports/iteration_27.json (100% pass)
- /app/test_reports/iteration_28.json (100% pass - music library verified)
