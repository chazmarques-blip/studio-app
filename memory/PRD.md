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
- Visual Agent Timeline (Scanner -> Artist -> Critic) with robot icons during generation
- Photo/Video selector in avatar frame
- Avatar naming and video_url persistence
- Default "Company Uniform" outfit (white polo + logo + black pants + white sneakers)
- Clear All Avatars button to fix cache issues

## Completed - March 2026
- [x] Voice Mastering endpoint
- [x] Avatar Video Preview (fal.ai Kling Avatar v2)
- [x] Avatar identity preservation (gemini-3-pro-image-preview)
- [x] Automatic 360° View Generation
- [x] Avatar Naming & Lip-Sync Preview with language selector
- [x] Image Accuracy Agent: Gemini Vision comparison loop (up to 3 iterations)
- [x] Photo/Video selector in avatar preview frame
- [x] Video URL persistence with avatar data
- [x] Preview texts shortened to ~5 seconds
- [x] Visual Agent Timeline (Scanner/Artist/Critic) with animated icons during generation
- [x] Default "Company Uniform" outfit (white polo, company logo, black pants, white sneakers)
- [x] Clear All Avatars button to eliminate cache bug
- [x] Updated CLOTHING_MAP with 5 styles: company_uniform, business_formal, casual, streetwear, creative

## Backlog

### P1 - Stabilization & Foundation
- [ ] Refactor pipeline.py (>4600 lines) into modules (avatar.py, video.py, audio.py, steps.py)
- [ ] Refactor PipelineView.jsx (~3000 lines) into components
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
