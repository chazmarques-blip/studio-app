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

### Completed This Session
- [x] Agent Details Drawer Modal (rich profiles with animated skill bars)
- [x] Company Management in AI Studio (primary/secondary, persist localStorage)
- [x] Default briefing mode: Guided Questionnaire
- [x] Video audio duplication fix (pause bg videos when lightbox opens)
- [x] Website URL as AI content source (context + contact info)
- [x] **Fix narration cutoff** — TTS audio checked via ffprobe, auto-sped up with atempo if > 19s; Ridley prompt tightened to 40-50 words max
- [x] **Video Mode Selector** — 3 options: Sem Video / Narracao / Apresentador (replaces old toggle)
- [x] **Avatar/Presenter System** — Upload photo or generate AI avatar (Nano Banana), saved with company, displayed in cards
- [x] **Presenter Video Infrastructure** — Backend endpoint for fal.ai Kling Avatar v2 lip-sync, graceful 503 fallback when FAL_KEY not set
- [x] Fixed HTML nesting (button inside button) in company cards

### Previously Completed
- [x] Audio duplication fix, per-channel templates, image/video toggle
- [x] Smart music selection, FFmpeg text escaping, recovery optimization
- [x] Video variant generation, skip video, clip2 retry + fallback
- [x] Rich agent profiles (25+ agents), Google Calendar/Sheets integration

### Known Issues
- Presenter video (lip-sync) requires FAL_KEY — infrastructure ready, awaiting API key
- FFmpeg logo overlay sometimes fails (low priority)
- Cloned videos 12s bug fix implemented but not fully verified

### Upcoming Tasks (Priority Order)
1. P1: Configure FAL_KEY for presenter video lip-sync
2. P1: Verify 12-second cloned video bug fix
3. P1: Agent renaming feature
4. P2: Universal Agent Sandbox
5. P2: Landing/Login Page Redesign
6. P3: WhatsApp MVP (Evolution API)

### Future/Backlog
- AutoFlow Workflow Builder
- Full Meta/WhatsApp Integration
- Unified Inbox
- Social Media Publishing
- Payment Gateway (Stripe)
- Admin Management System
- pipeline.py refactoring (3500+ lines)

## Campaign Cost Analysis
| Component | Cost Estimate |
|-----------|--------------|
| Claude Sonnet 4.5 (3-4 calls) | ~$0.10-0.15 |
| Gemini 2.0 Flash (4 calls) | ~$0.002 |
| Gemini Nano Banana (3 images) | ~$0.10-0.15 |
| OpenAI TTS-HD (narration) | ~$0.01-0.02 |
| Sora 2 (2-3 video clips) | ~$1.00-2.00 |
| **Total with video** | **~$1.20-2.50** |
| **Total without video** | **~$0.20-0.35** |
| Presenter video (fal.ai Kling) | ~$1.35 (24s) |

## Video Modes
| Mode | Description | Cost |
|------|-------------|------|
| Sem Video | Images only, fastest | $0.20-0.35 |
| Narracao | TTS voice + Sora 2 scenes | $1.20-2.50 |
| Apresentador | Avatar lip-sync (fal.ai) | ~$1.50 |

## Test Reports
- /app/test_reports/iteration_40.json (Agent Details Drawer)
- /app/test_reports/iteration_41.json (Company management + defaults)
- /app/test_reports/iteration_42.json (Avatar + Video Mode + Presenter)
