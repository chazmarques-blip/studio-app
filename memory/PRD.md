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
- Landing Page V2 with i18n (EN/PT/ES), multi-platform campaign carousel — now the main landing page at `/`
- Login page with 2-column pricing layout
- CRM with Kanban board
- Audio Pre-Approval step in video pipeline (marcos_video pauses for user review before Sora 2 generation)

## Completed (March 21, 2026 — Session 3)

### P0: 3D Avatar Photo Reference Fix
- Fixed `generate_avatar_from_prompt` in avatar_routes.py to use `_gemini_edit_image` (litellm multimodal) instead of `emergentintegrations LlmChat.UserMessage(images=[...])` which silently ignored images
- When `reference_photo_url` is provided for 3D styles, the image is now properly sent to Gemini alongside the prompt
- Added `_describe_person()` call for photo reference to capture likeness details

### P1a: Landing Page V2 Swap
- Route `/` now serves `LandingV2` component (was `Landing`)
- Removed the temporary `/v2` route
- Old `Landing` component no longer imported in App.js

### P1b: Audio Pre-Approval in Video Pipeline
- After `marcos_video` AI generates the script, pipeline pauses at `waiting_audio_approval` status
- TTS audio preview is automatically generated from the narration text
- New `AudioApprovalPanel` component in StepCard shows: narration text, audio player, approve/reject buttons
- New backend endpoint: `POST /api/campaigns/pipeline/{id}/approve-audio`
- Approve: triggers `_continue_video_after_approval()` which runs Sora 2 + music + FFmpeg mix in background
- Reject with feedback: reruns marcos_video step with revision feedback
- Purple theme for audio approval status in pipeline UI

## Previous Sessions Completed
- ElevenLabs Music Generation API (music_v1 model)
- Dylan Sound Director with full ElevenLabs knowledge
- Cinema-Quality FFmpeg audio mixing (sidechain ducking, reverb, loudnorm)
- Narration text cleaning (_clean_narration_for_tts)
- Campaign auto-update DB logic fix
- Music files replaced with proper tracks

## Test Credentials
- Email: test@agentflow.com / Password: password123

## P0 - Next Actions
- None currently

## P1 - Upcoming
- Activate live omnichannel integrations (WhatsApp, SMS, etc.)
- CRM Kanban improvements

## P2 - Future/Backlog
- Admin Management System
- Payment Gateway Integration
- Legal & Publication (Terms, Privacy)
- Scalability hardening
- PipelineView.jsx refactoring (2600+ lines — split into smaller components)
