# AgentZZ - Product Requirements Document

## Problem Statement
No-code SaaS platform for SMB owners to deploy AI agents on social media with integrated AI marketing campaign generation including text, images, and videos.

## Architecture
- Frontend: React + Tailwind + shadcn-ui + Lucide Icons
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Claude Sonnet 4.5, OpenAI Whisper/TTS, Gemini Nano Banana, Sora 2, Google APIs, fal.ai (planned)

## Credentials
- Email: test@agentflow.com | Password: password123

## Current Status (March 16, 2026)

### Completed This Session (3 rounds)

#### Round 1: Agent Details + Company Management
- [x] Agent Details Drawer Modal (rich profiles with animated skill bars)
- [x] Company Management in AI Studio (primary/secondary, persist localStorage)
- [x] Default briefing mode: Guided Questionnaire
- [x] Video audio duplication fix (pause bg videos when lightbox opens)
- [x] Website URL as AI content source

#### Round 2: Avatar + Video Mode + Narration Fix
- [x] Fix narration cutoff — TTS audio auto-sped up with atempo if > 19s; Ridley prompt tightened to 40-50 words
- [x] Video Mode Selector — 3 options: Sem Video / Narracao / Apresentador
- [x] Avatar/Presenter System — Upload photo or generate AI avatar (Nano Banana)
- [x] Presenter Video Infrastructure — Backend for fal.ai Kling Avatar v2 lip-sync

#### Round 3: Video Duration + Channel Formats (Critical Bug Fixes)
- [x] ROOT CAUSE: ffprobe binary does NOT exist in environment — ALL ffprobe calls silently failed
- [x] Created _ffprobe_duration() and _ffprobe_dimensions() helpers using ffmpeg stderr parsing
- [x] Replaced ALL ffprobe calls across pipeline.py (6 occurrences)
- [x] Fix 12-second video: clip2 fallback now concatenates clip1 twice (24s) instead of copying clip1 alone (12s)
- [x] Fixed BOTH crossfade and concat fallback paths to loop clip1 for 24s
- [x] Video variants were EMPTY for all campaigns (root cause: ffprobe missing) — NOW FIXED
- [x] Created regenerate-video-variants endpoint for existing campaigns
- [x] Regenerated 8 format variants for ALL existing campaigns with video
- [x] Clone endpoint now preserves skip_video, video_mode, avatar_url

### Previously Completed
- Audio fix, per-channel templates, image/video toggle, smart music, skip video, rich agent profiles, Google integration

### Known Issues
- Presenter video (lip-sync) requires FAL_KEY — infrastructure ready
- FFmpeg logo overlay sometimes fails (low priority)

### Upcoming Tasks (Priority Order)
1. P0: Configure FAL_KEY for presenter video lip-sync (fal.ai)
2. P1: Agent renaming feature
3. P2: Universal Agent Sandbox
4. P2: Landing/Login Page Redesign
5. P3: WhatsApp MVP (Evolution API)

### Future/Backlog
- AutoFlow, Unified Inbox, Social Publishing, Stripe, Admin, pipeline.py refactoring

## Video Format Per Channel
| Channel | Video Format | Size |
|---------|-------------|------|
| WhatsApp | 1:1 | 720x720 |
| Instagram | 1:1 | 1080x1080 |
| Facebook | 16:9 | 1280x720 |
| TikTok | 9:16 | 720x1280 |
| Google Ads | 16:9 | 1344x768 |
| Telegram | 16:9 | 1280x720 |
| Email | 16:9 | 1280x720 |
| SMS | 9:16 | 720x1280 |

## Test Reports
- /app/test_reports/iteration_40.json (Agent Details Drawer)
- /app/test_reports/iteration_41.json (Company management + defaults)
- /app/test_reports/iteration_42.json (Avatar + Video Mode + Presenter)
- /app/test_reports/iteration_43.json (Video variants + clone fix - 100% pass)
