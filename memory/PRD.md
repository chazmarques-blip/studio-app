# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio for generating full campaigns (copy, images, video) using multimodal AI, with a premium "dark luxury" theme.

## Core Architecture
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI (Python), Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude 3.5 Sonnet, OpenAI Whisper, Sora 2, ElevenLabs (TTS + Music Generation), Google APIs, Gemini (image gen)
- **Design**: Dark luxury monochrome theme (black/gold/white/gray)

## What's Been Implemented
- Full navigation, Dashboard with recharts, Agent Management (CRUD + config)
- Agent Marketplace with plan-gating (Personal Agents = Pro)
- Google Calendar/Sheets integration in AgentConfig
- AI Marketing Studio: Full pipeline (David Copy -> Lee Review -> Stefan Design -> George Review -> Dylan Sound -> Ridley Video -> Roger Review -> Gary Publish)
- Campaign management with 8-channel distribution
- Video generation with Sora 2 + ElevenLabs narration + FFmpeg cinematic audio mix
- AI Music generation with ElevenLabs music_v1 API
- Create Art tab with 15 style filters
- 3D Avatar generation with photo reference support (Gemini multimodal)
- Avatar 360° View with style-aware prompts (preserves 3D/Pixar style)
- Landing Page V2 with i18n (EN/PT/ES) — now the main landing page at `/`
- Login page with 2-column pricing layout
- CRM with Kanban board
- Audio Pre-Approval step in video pipeline (marcos_video pauses before Sora 2)

## Completed (March 21, 2026 — Session 3)

### Bug Fix: Avatar 360° View Ignoring 3D Style
- Root cause: `_run_batch_360` and `generate_avatar_variant` always used photorealistic prompts
- Fix: Added `avatar_style` parameter to `AvatarBatch360Request` and `AvatarVariantRequest` models
- When avatar_style is '3d_cartoon' or '3d_pixar', prompts now explicitly say "do NOT make it photorealistic"
- Frontend `startAuto360`, `generateAngle`, and `tempAvatar` all pass/store the correct style
- Verified: iteration_77.json (21/21 tests passed)

### P0: 3D Avatar Photo Reference Fix
- Fixed `generate_avatar_from_prompt` to use `_gemini_edit_image` (litellm multimodal) instead of `UserMessage(images=[...])`
- Added `_describe_person()` call for likeness preservation

### P1a: Landing Page V2 Swap
- Route `/` now serves `LandingV2`, removed temporary `/v2` route

### P1b: Audio Pre-Approval in Video Pipeline
- After marcos_video AI generates script, pipeline pauses at `waiting_audio_approval`
- TTS audio preview auto-generated, shown in `AudioApprovalPanel` component
- Endpoint: `POST /api/campaigns/pipeline/{id}/approve-audio`
- Approve → video generation starts; Reject with feedback → script revision

## Test Credentials
- Email: test@agentflow.com / Password: password123

## P1 - Upcoming
- Activate live omnichannel integrations (WhatsApp, SMS, etc.)
- CRM Kanban improvements

## P2 - Future/Backlog
- Admin Management System
- Payment Gateway Integration
- Legal & Publication (Terms, Privacy)
- Scalability hardening
- PipelineView.jsx refactoring (2600+ lines)
