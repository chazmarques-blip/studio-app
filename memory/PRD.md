# AgentZZ - Product Requirements Document

## Problem Statement
No-code SaaS platform for SMB owners to deploy AI agents on social media with integrated AI marketing campaign generation.

## Architecture
- Frontend: React + Tailwind + shadcn-ui + Lucide Icons
- Backend: FastAPI (Python), Database: Supabase + MongoDB
- 3rd Party: Claude Sonnet 4.5, OpenAI TTS, Gemini Nano Banana, Sora 2, Google APIs, fal.ai (planned)

## Credentials
- Email: test@agentflow.com | Password: password123

## Current Status (March 16, 2026)

### Completed This Session
- [x] Agent Details Drawer (rich profiles, animated skill bars)
- [x] Company Management (primary/secondary, localStorage persist)
- [x] Default: Guided Questionnaire, Website URL as AI source
- [x] Video audio duplication fix (pause bg on lightbox)
- [x] Narration cutoff fix (atempo speedup if > 19s)
- [x] Video Mode Selector (Sem Video / Narracao / Apresentador)
- [x] Avatar System (upload photo or AI generate via Nano Banana)
- [x] Presenter Video infrastructure (fal.ai Kling Avatar v2)
- [x] CRITICAL: Replaced ALL ffprobe calls with ffmpeg-based helpers (_ffprobe_duration, _ffprobe_dimensions)
- [x] CRITICAL: 12s video fix — clip2 fallback now concatenates clip1 twice for 24s
- [x] CRITICAL: Video variants were EMPTY — now generated correctly for all 8 channels
- [x] Regenerated variants for all existing campaigns
- [x] Created regenerate-video-variants endpoint
- [x] Clone now preserves skip_video, video_mode, avatar_url
- [x] Compact uploads: Logo + Reference side by side in a single row
- [x] Fixed button-in-button HTML nesting
- [x] **Avatar Studio UI Refactor (P0 COMPLETE)**: Dedicated "Avatar do Apresentador" section created outside the company form. Features: photo upload, AI-powered full-body avatar generation (Gemini), large preview, regenerate/remove controls. Backend uses GPT Image 1 via Emergent LLM Key. Tested: iteration_44 (100% pass)

### Known Issues
- Presenter video requires FAL_KEY (infrastructure ready)
- FFmpeg logo overlay sometimes fails (low priority)

### Upcoming Tasks
1. P1: Ask user for FAL_KEY to enable Presenter video mode
2. P1: Agent renaming
3. P2: Sandbox, Landing Page Redesign
4. P3: WhatsApp MVP

### Future
- AutoFlow, Unified Inbox, Social Publishing, Stripe, Admin, pipeline.py refactoring

## Test Reports
- iteration_40: Agent Details Drawer
- iteration_41: Company management + defaults
- iteration_42: Avatar + Video Mode
- iteration_43: Video bug fixes (ffprobe, 12s, variants)
- iteration_44: Avatar Studio UI Refactor (100% pass)
- iteration_43: Video variants + clone fix (100% pass)
