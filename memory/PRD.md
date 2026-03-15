# AgentZZ - Product Requirements Document

## Problem Statement
No-code SaaS platform for SMB owners to deploy AI agents on social media (WhatsApp, Instagram, Facebook, Telegram, SMS) with integrated AI marketing campaign generation.

## Core Features
1. AI Agent Marketplace (25+ agents with cyberpunk avatars)
2. AI Agent Generator (guided questionnaire - BLOCKED by LLM budget)
3. AI Marketing Studio - Campaign creation with video, image, text
4. Omnichannel templates (per-channel format mockups)
5. CRM integration
6. Dark luxury theme (monochrome gold/black/white)

## Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Claude, OpenAI Whisper, Gemini Nano Banana, Sora 2, Google APIs

## Credentials
- Email: test@agentflow.com | Password: password123

## Current Status (March 15, 2026)

### Completed This Session
- [x] Agent Details Drawer Modal — Premium full-screen drawer showing rich agent profiles (mentality, skills with animated bars, background, methodologies, personality, strengths, interaction style, inspirations) with Deploy button
- [x] Fixed Deploy button z-index overlap with bottom nav bar (pb-20 fix)

### Previously Completed
- [x] Audio duplication fix — Music reduced from 0dB to -22dB, all 10 existing videos remixed
- [x] Per-channel templates — 8 mockups (WhatsApp 1:1, TikTok 9:16, Facebook 16:9, Google Ads 1.91:1, Telegram 16:9, Email 16:9, SMS 9:16)
- [x] Image/Video toggle per channel mockup
- [x] Smart music selection (30+ industry moods)
- [x] FFmpeg text escaping fix (special chars in CTA)
- [x] Recovery optimization (reuse AI scripts on video failure)
- [x] Remix API endpoints (individual + batch)
- [x] Video variant generation per platform (crop/resize from master)
- [x] Skip video flag — Campaign creation without video (faster)
- [x] Clip2 retry + fallback — No more 12-second videos on clip2 failure
- [x] Rafael review now checks format compatibility and text readability
- [x] Format size labels under each channel mockup
- [x] Full UI redesign with dark luxury theme
- [x] Agent marketplace with 25 cyberpunk avatars
- [x] AI Marketing Studio pipeline (7-step AI agent workflow)
- [x] Video generation with Sora 2
- [x] Google Calendar/Sheets integration in Agent Config
- [x] Rich agent profiles in constants.py (mentality, skills, methodologies, inspirations for all 25+ agents)

### Known Issues
- LLM Key budget exceeded (blocks AI Agent Generator and all AI generation) — User informed, needs to add balance
- FFmpeg logo overlay sometimes fails (low priority)
- Cloned videos 12s bug fix implemented but not verified

### Upcoming Tasks (Priority Order)
1. P1: Verify 12-second cloned video bug fix
2. P1: Agent renaming feature
3. P2: Universal Agent Sandbox
4. P2: Landing/Login Page Redesign
5. P3: WhatsApp MVP (Evolution API)
6. P4: AutoFlow Workflow Builder

### Future/Backlog
- Full Meta/WhatsApp Integration
- Unified Inbox
- Social Media Publishing
- Payment Gateway (Stripe)
- Admin Management System
- Legal & Publication (Terms, Privacy)
- pipeline.py refactoring (3200+ lines, needs modularization)

## Key API Endpoints
- POST /api/auth/login
- GET /api/campaigns
- POST /api/campaigns/pipeline (accepts skip_video:true)
- GET /api/campaigns/pipeline/{id}
- POST /api/campaigns/pipeline/{id}/remix-audio
- POST /api/campaigns/pipeline/remix-all-videos
- GET /api/agents/marketplace (returns agents with rich profile data)
- POST /api/agents/deploy
- POST /api/agents/generate (BLOCKED)

## Video Format Per Channel
| Channel | Image Format | Video Format |
|---------|-------------|-------------|
| WhatsApp | 1:1 720x720 | 1:1 720x720 |
| Instagram | 1:1 1080x1080 | 1:1 1080x1080 |
| Facebook | 16:9 1280x720 | 16:9 1280x720 |
| TikTok | 9:16 720x1280 | 9:16 720x1280 |
| Google Ads | 16:9 1344x768 | 16:9 1280x720 |
| Telegram | 16:9 1280x720 | 16:9 1280x720 |
| Email | 16:9 1280x720 | 16:9 1280x720 |
| SMS | 9:16 720x1280 | 9:16 720x1280 |

## Test Reports
- /app/test_reports/iteration_38.json (Channel templates)
- /app/test_reports/iteration_39.json (Skip video + format verification)
- /app/test_reports/iteration_40.json (Agent Details Drawer - 95% -> 100% after fix)
