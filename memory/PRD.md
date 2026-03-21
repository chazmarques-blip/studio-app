# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio for generating full campaigns (copy, images, video) using multimodal AI, with a premium "dark luxury" theme.

## Core Architecture
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI (Python), Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude 3.5 Sonnet, OpenAI Whisper, Sora 2, ElevenLabs (TTS + Music), Google APIs, Gemini (image gen), fal.ai (Kling lip-sync)
- **Design**: Dark luxury monochrome theme (black/gold/white/gray)

## What's Been Implemented
- Full navigation, Dashboard, Agent Management, Agent Marketplace
- Google Calendar/Sheets integration in AgentConfig
- AI Marketing Studio: Full 8-step pipeline with real-time polling
- Video generation with Sora 2 + ElevenLabs + FFmpeg cinematic audio mix
- AI Music generation with ElevenLabs music_v1 API
- Create Art tab with 15 style filters
- 3D Avatar generation with photo reference + style-aware 360° view
- Avatar lip-sync video preview (Kling via fal.ai)
- Landing Page V2 at `/` with i18n (EN/PT/ES)
- CRM with Kanban board
- Audio Pre-Approval step in video pipeline

## Completed (March 21, 2026 — Session 3)

### Bug Fix: Avatar 360° View Converting 3D to Realistic
- **Root cause**: `applyClothing` and `generateAngle` used `source_photo_url` (original real photo) as source for 360° generation, even for 3D/Pixar avatars
- **Fix**: Added `is3d` check — for 3D styles, always use `tempAvatar.url` (the generated Pixar avatar). Realistic avatars still use source_photo_url
- Also: `avatar_style` is now persisted in save/edit functions (`saveAvatarAndClose`, `saveAvatarAsNew`, `openAvatarForEdit`)

### Bug Fix: Download Button Not Working
- **Root cause**: Used `<a target="_blank">` which only opens in new tab
- **Fix**: Replaced with `fetch+blob` download pattern that actually saves the file

### Bug Fix: 3D Avatar Photo Reference Ignored
- Fixed `generate_avatar_from_prompt` to use `_gemini_edit_image` (litellm multimodal) instead of `UserMessage(images=[...])`

### P1a: Landing Page V2 Swap
- Route `/` now serves `LandingV2`, removed temporary `/v2` route

### P1b: Audio Pre-Approval in Video Pipeline
- Pipeline pauses at `waiting_audio_approval` after script generation, before Sora 2 video
- AudioApprovalPanel component with TTS preview, approve/reject buttons
- Endpoint: `POST /api/campaigns/pipeline/{id}/approve-audio`

## Test Credentials
- Email: test@agentflow.com / Password: password123

## Test Reports
- iteration_76.json: 30/30 passed (P0 avatar fix + P1a landing + P1b audio approval)
- iteration_77.json: 21/21 passed (avatar_style parameter in 360° endpoints)
- iteration_78.json: 30/30 passed (360° style persistence + download fix)

## P1 - Upcoming
- Activate live omnichannel integrations (WhatsApp, SMS, etc.)
- CRM Kanban improvements

## P2 - Future/Backlog
- Admin Management System
- Payment Gateway Integration
- Legal & Publication (Terms, Privacy)
- Scalability hardening
- PipelineView.jsx refactoring (2600+ lines)
