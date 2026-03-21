# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio for generating full campaigns (copy, images, video) using multimodal AI, with a premium "dark luxury" theme.

## Core Architecture
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI (Python), Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude 3.5 Sonnet, OpenAI Whisper, Sora 2, ElevenLabs (TTS + Music Generation), Google APIs
- **Design**: Dark luxury monochrome theme (black/gold/white/gray)

## What's Been Implemented
- Full navigation, Dashboard with recharts, Agent Management (CRUD + config)
- Agent Marketplace with plan-gating (Personal Agents = Pro)
- Google Calendar/Sheets integration in AgentConfig
- AI Marketing Studio: Full pipeline (Sofia Copy -> Ana Review -> Lucas Design -> Stefan Retouch -> George Creative -> Dylan Sound -> Ridley Video -> Rafael Review -> Pedro Publish)
- Campaign management with 8-channel distribution
- Video generation with Sora 2 + ElevenLabs narration + FFmpeg cinematic audio mix
- Create Art tab with 15 style filters
- Landing Page V2 with i18n (EN/PT/ES), multi-platform campaign carousel
- Login page with 2-column pricing layout
- CRM with Kanban board

## Completed (March 21, 2026 — Session 2)

### ElevenLabs Music Generation API
- Implemented `_generate_music_elevenlabs()` using ElevenLabs Compose API (`music_v1` model)
- `_build_music_prompt_from_dylan()` extracts music direction from pipeline output
- Prefers `===ELEVENLABS MUSIC PROMPT===` section, falls back to mood-based prompts
- Automatic retry with API prompt_suggestion on copyright violations
- Fallback to static music files if AI generation fails

### Dylan Sound Director — Full ElevenLabs Knowledge
- Updated prompt with complete ELEVENLABS MUSIC GENERATION documentation
- Music prompt engineering guidelines with 5 genre-specific examples
- New `===ELEVENLABS MUSIC PROMPT===` output section for custom music generation
- New `===CLEAN TTS TEXT===` section for pure spoken text output

### Narration Cleaning (TTS)
- Centralized `_clean_narration_for_tts()` removes ALL non-spoken content
- Tags removed: ANTES:, DEPOIS:, A PONTE:, [HOOK 0-4s], [Direction:], <<<>>>, emojis, [TOTAL WORD COUNT], etc.
- Applied to both commercial and presenter video pipelines
- Both cleanCampaignText() and cleanDisplayText() updated for UI display

### Cinema-Quality Audio
- ElevenLabs voice: stability=0.30, style=0.55, speaker_boost=True
- Dylan's voice settings (stability, similarity, style) auto-extracted and applied
- Narration: presence EQ (3kHz), broadcast compressor, cinematic reverb (aecho)
- AAC 320kbps at 48kHz encoding
- Music: sidechain ducking + EQ carving + exponential fades

### Avatar 3D — Photo Reference
- Added optional photo upload to "3D Animated" tab in Create Avatar modal
- Backend AvatarFromPromptRequest accepts `reference_photo_url`
- Photo sent to Gemini as image reference for 3D character generation

### Campaign Auto-Update Fix
- `_find_campaign_for_pipeline()` checks metrics.schedule.pipeline_id (primary) + metrics.stats.pipeline_id (legacy)
- `_update_campaign_stats()` correctly writes to metrics.stats
- Video URL preservation: regeneration failures no longer clear existing URLs
- All 10+ campaign lookup patterns refactored to use helper functions

### Music Files
- Replaced 20 placeholder music files (~361KB) with proper copies of 5 real tracks mapped by mood

## Test Credentials
- Email: test@agentflow.com / Password: password123

## P0 - Next Actions
- Audio Pre-Approval step in video pipeline (user approves script/voice before burning credits)

## P1 - Upcoming
- Replace landing page `/` with `/v2` version
- Activate live omnichannel integrations (WhatsApp, SMS, etc.)

## P2 - Future/Backlog
- Admin Management System
- Payment Gateway Integration
- CRM Kanban improvements
- Legal & Publication (Terms, Privacy)
- Scalability hardening
