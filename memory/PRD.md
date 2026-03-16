# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users (small and medium business owners) to easily deploy and configure pre-built AI agents on various social media channels. The platform includes an AI Marketing Studio for generating full marketing campaigns with AI-written copy, AI-generated images, and AI avatar-based video commercials.

## Core Requirements
1. **AI Marketing Studio** - Full pipeline to generate marketing campaigns from a brief
2. **Advanced Avatar Creation** - Generate realistic avatars from photos/videos with customization
3. **Voice Features** - Voice bank (TTS), custom recording, video-extracted voice, voice mastering
4. **Video Generation** - Sora 2 based commercial videos with avatar in scene
5. **Omnichannel** - WhatsApp, Instagram, Facebook, Telegram, SMS
6. **CRM** - Built-in with Kanban board
7. **Multi-Language** - EN, PT, ES via i18n
8. **Dark Luxury Theme** - Monochrome gold/black/white/gray

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion, recharts, react-i18next
- **Backend:** FastAPI (Python), Supabase (PostgreSQL), MongoDB
- **3rd Party:** Sora 2, Claude/Gemini, GPT Image 1, OpenAI TTS, FFmpeg

## What's Implemented
- Full i18n (EN, PT, ES)
- Company and Avatar creation modals
- Advanced Avatar Studio (photo/video source, clothing, 360 angles, voice bank, recording, video-extracted voice)
- Avatar editing and cloning
- Voice Mastering via FFmpeg (noise reduction, EQ, compression, normalization)
- Avatar Video Preview (4s Sora 2 clip with async polling pattern)
- Sora-based Presenter Mode (avatar in scene)
- Brand Data toggle for campaigns
- Multi-LLM fallback (Claude -> Gemini)
- Dashboard with recharts
- Agent Marketplace with plan gating
- Google Calendar/Sheets integration

## Completed - March 2026
- [x] Voice Mastering endpoint (`/master-voice`) - FFmpeg audio enhancement
- [x] Avatar Video Preview with async polling (`/avatar-video-preview`) - Sora 2, 720x1280
- [x] "Voz Original" label for extracted voices
- [x] Fixed blob URL handling in masterize flow (auto-uploads before mastering)
- [x] Fixed Sora 2 video sizes from invalid 1024x1792 to valid 720x1280 (3 places)
- [x] Fixed voice URL consistency (recording_url -> url)
- [x] Proxy timeout handled via async polling pattern
- [x] All tests passing (iteration_54.json - 13/13 backend, 7/7 frontend)

## Backlog

### P1 - Stabilization & Foundation
- [ ] Refactor `pipeline.py` (>4000 lines) into modules (video.py, audio.py, avatar.py, etc.)
- [ ] Refactor `PipelineView.jsx` (~2700 lines) into smaller components
- [ ] Allow renaming pipeline agents ("Sofia", "Gary")
- [ ] Redesign Landing/Login page
- [ ] Fix FFmpeg logo overlay (low priority)

### P2 - CRM & Communication
- [ ] CRM / Lead Database
- [ ] Kanban Visual board
- [ ] Unified Inbox
- [ ] WhatsApp MVP (Evolution API)
- [ ] Omnichannel (Instagram, Facebook, Telegram, SMS)

### P3 - Intelligent Agents
- [ ] Agent Tester (Sandbox)
- [ ] Chat Supervisor Agent
- [ ] Kanban Manager Agent

### P4 - Campaigns & Automation
- [ ] Campaigns for Leads
- [ ] AutoFlow visual workflow builder
- [ ] Social Publishing

### P5 - Monetization & Scale
- [ ] Stripe Integration
- [ ] Admin System
- [ ] Analytics Dashboard
- [ ] Legal & Compliance
