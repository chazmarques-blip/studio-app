# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio for generating full campaigns (copy, images, video) using multimodal AI, with a premium "dark luxury" theme.

## Core Architecture
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI (Python), Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude 3.5 Sonnet, OpenAI Whisper, Sora 2, ElevenLabs TTS, Google APIs
- **Design**: Dark luxury monochrome theme (black/gold/white/gray)

## What's Been Implemented
- Full navigation, Dashboard with recharts, Agent Management (CRUD + config)
- Agent Marketplace with plan-gating (Personal Agents = Pro)
- Google Calendar/Sheets integration in AgentConfig
- AI Marketing Studio: Full pipeline (Sofia Copy → Ana Review → Lucas Design → Stefan Retouch → George Creative → Dylan Sound → Ridley Video → Rafael Review → Pedro Publish)
- Campaign management with 8-channel distribution (WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS)
- Video generation with Sora 2 + ElevenLabs narration + FFmpeg cinematic audio mix
- Create Art tab with 15 style filters
- Landing Page V2 with i18n (EN/PT/ES), multi-platform campaign carousel
- Login page with 2-column pricing layout
- CRM with Kanban board

## Completed (March 21, 2026)
- **Fixed AI Narration**: Added `_clean_narration_for_tts()` — centralized function removing ALL non-spoken content (ANTES:, DEPOIS:, [Direction:], <<<>>>, [HOOK], framework tags, emojis, timing marks)
- **Added ===CLEAN TTS TEXT=== section**: New prompt section for Dylan and Marcos that outputs ONLY the spoken text for TTS, no markup
- **Fixed Copy Display**: Updated `cleanCampaignText()` in Marketing.jsx and `cleanDisplayText()` in constants.js to strip framework tags from displayed copy
- **Cinema-Quality Audio**: ElevenLabs settings upgraded (stability=0.30, style=0.55), narration gets presence EQ boost (3kHz), broadcast compressor, cinematic room reverb (aecho)
- **Music Files Fixed**: Replaced 20 placeholder music files (~361KB) with proper copies of 5 real tracks mapped by mood
- **Full HD Video**: Default resolution upgraded from 1280x720 to 1920x1080
- **Audio Encoding**: AAC 320kbps at 48kHz for broadcast quality
- **Campaign Auto-Update Fixed**: `_find_campaign_for_pipeline()` helper now correctly looks up `metrics.schedule.pipeline_id` and `_update_campaign_stats()` writes to `metrics.stats`
- **Video URL Preservation**: Regeneration failures no longer clear existing video URL

## Test Credentials
- Email: test@agentflow.com / Password: password123

## P0 - Next Actions
- Audio Pre-Approval step in video pipeline (user approves script/voice before burning video credits)

## P1 - Upcoming
- Replace landing page `/` with `/v2` version
- Activate live omnichannel integrations (WhatsApp, SMS, etc.)

## P2 - Future/Backlog
- Admin Management System
- Payment Gateway Integration
- CRM Kanban improvements
- Legal & Publication (Terms, Privacy)
- Scalability hardening
