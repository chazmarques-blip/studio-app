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
- Frontend: React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion, recharts, react-i18next
- Backend: FastAPI (Python), Supabase (PostgreSQL), MongoDB
- 3rd Party: Sora 2, Claude/Gemini, GPT Image 1, OpenAI TTS, FFmpeg, litellm, fal.ai Kling Avatar v2

## What's Implemented
- Full i18n (EN, PT, ES)
- Company and Avatar creation modals
- Advanced Avatar Studio (photo/video source, clothing, 360 angles, voice bank, recording, video-extracted voice)
- Avatar editing and cloning
- Voice Mastering via FFmpeg
- Avatar Video Preview (5s lip-sync via fal.ai Kling Avatar v2 with async polling)
- Automatic 360 generation (all 4 angles auto-generated after avatar creation or clothing change)
- Sora-based Presenter Mode (avatar in scene)
- Brand Data toggle for campaigns
- Multi-LLM fallback (Claude -> Gemini)
- Dashboard with recharts
- Agent Marketplace with plan gating
- Google Calendar/Sheets integration
- Image Accuracy Agent (Gemini Vision comparison loop, up to 3 iterations)
- Photo/Video selector in avatar frame
- Avatar naming and video_url persistence

## Completed - March 2026
- [x] Voice Mastering endpoint - FFmpeg audio enhancement
- [x] Avatar Video Preview with async polling - Sora 2, then migrated to fal.ai Kling Avatar v2
- [x] "Voz Original" label for extracted voices
- [x] Fixed blob URL handling in masterize flow
- [x] Fixed Sora 2 video sizes (720x1280)
- [x] Fixed voice URL consistency
- [x] BUG FIX: UserMessage images kwarg - Fixed ImageContent/UserMessage API
- [x] UI: Video tab first (left) with "Best" badge, Photo second (dimmed)
- [x] UI: Added specs for video and photo uploads
- [x] BUG FIX: Avatar zoom z-index (z-[80] above modal)
- [x] BUG FIX: Avatar identity preservation - _gemini_edit_image sends text+image in SAME multimodal message via litellm
- [x] Auto 360 generation: batch endpoint with polling, auto-triggered after avatar creation and clothing changes
- [x] Progress bar for 360 generation
- [x] Avatar Naming feature
- [x] Lip-Sync Preview via fal.ai Kling Avatar v2 with language selector (PT/EN/ES)
- [x] Image Accuracy Agent: Gemini Vision comparison loop (up to 3 iterations) for avatar quality validation
- [x] Photo/Video selector in avatar preview frame (toggle between photo and video in same area)
- [x] Video URL persistence: preview videos saved with avatar data
- [x] Preview texts shortened to ~5 seconds for quicker test videos
- [x] Robust JSON parsing for accuracy comparison with regex fallback

## Backlog

### P1 - Stabilization & Foundation
- [ ] Refactor pipeline.py (>4600 lines) into modules (avatar.py, video.py, audio.py, steps.py)
- [ ] Refactor PipelineView.jsx (~2900 lines) into components
- [ ] Allow renaming pipeline agents
- [ ] Redesign Landing/Login page
- [ ] Fix FFmpeg logo overlay (low priority)

### P2 - CRM & Communication
- [ ] CRM / Lead Database
- [ ] Kanban Visual board
- [ ] Unified Inbox
- [ ] WhatsApp MVP (Evolution API)
- [ ] Omnichannel integrations

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
