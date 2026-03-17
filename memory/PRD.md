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
- Backend: FastAPI (Python), Supabase (PostgreSQL)
- 3rd Party: Sora 2, Claude/Gemini, GPT Image 1, OpenAI TTS, FFmpeg, litellm, fal.ai Kling Avatar v2

## Data Architecture
- **ALL data** stored in **Supabase** (user's paid account connected via GitHub)
- Companies & Avatars: `tenants.settings` JSONB → `studio_companies` and `studio_avatars`
- CRUD endpoints: `/api/data/companies`, `/api/data/avatars`

## What's Implemented
- Full i18n (EN, PT, ES)
- **Dual Upload for Avatar Creation** (photo required + video optional for maximum accuracy)
- **Multi-image identity analysis**: Gemini Vision analyzes photo + multiple video frames
- **Enhanced `_describe_person_from_video`**: dedicated multi-frame description function
- **Image Accuracy Agent** (Scanner → Artist → Critic) with visual timeline, up to 3 iterations
- Default "Company Uniform" outfit (white polo + logo + black pants + white sneakers)
- Data persistence in Supabase (companies & avatars survive cache clear)
- Photo/Video selector in avatar frame
- Avatar naming, editing, cloning
- Voice Mastering, Voice Bank (TTS), Custom Recording, Video-extracted voice
- Avatar Video Preview (5s lip-sync via fal.ai Kling Avatar v2)
- Automatic 360° generation
- Sora-based Presenter Mode
- Dashboard, Agent Marketplace, Google Calendar/Sheets integration

## Completed - March 2026
- [x] Voice Mastering, Avatar Video Preview, Auto 360°, Avatar Naming
- [x] Image Accuracy Agent with visual Agent Timeline
- [x] Default "Company Uniform" outfit
- [x] Data persistence migrated from localStorage to Supabase
- [x] **Dual Upload (Photo + Video)** for enhanced identity accuracy
- [x] Multi-frame video analysis with `_describe_person_from_video`
- [x] `extract-from-video` now returns `extra_frame_urls`
- [x] `generate-avatar-with-accuracy` accepts `video_frame_urls`
- [x] Photo/Video selector, Clear All Avatars, 5 clothing styles

## Backlog

### P1 - Stabilization & Foundation
- [ ] Refactor pipeline.py (>4700 lines) into modules
- [ ] Refactor PipelineView.jsx (~3100 lines) into components
- [ ] Allow renaming pipeline agents
- [ ] Redesign Landing/Login page

### P2 - CRM & Communication
- [ ] CRM / Lead Database, Kanban, Unified Inbox
- [ ] WhatsApp MVP (Evolution API), Omnichannel integrations

### P3 - Intelligent Agents
- [ ] Agent Tester, Chat Supervisor, Kanban Manager

### P4 - Campaigns & Automation
- [ ] Campaigns for Leads, AutoFlow, Social Publishing

### P5 - Monetization & Scale
- [ ] Stripe, Admin System, Analytics, Legal
