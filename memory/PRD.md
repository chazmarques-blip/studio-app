# AgentZZ - Product Requirements Document

## Problem Statement
No-code SaaS platform for SMB owners to deploy AI agents on social media (WhatsApp, Instagram, Facebook, Telegram, SMS) with integrated AI marketing campaign generation.

## Core Features
1. AI Agent Marketplace (25+ agents with cyberpunk avatars + rich detail profiles)
2. AI Agent Generator (guided questionnaire - requires LLM key balance)
3. AI Marketing Studio - Campaign creation with video, image, text
4. Omnichannel templates (per-channel format mockups)
5. Company management in AI Studio (primary + secondary companies)
6. CRM integration
7. Dark luxury theme (monochrome gold/black/white)

## Architecture
- Frontend: React + Tailwind + shadcn-ui + Lucide Icons + tailwindcss-animate
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Claude Sonnet 4.5, OpenAI Whisper, Gemini Nano Banana, Sora 2, Google APIs

## Credentials
- Email: test@agentflow.com | Password: password123

## Current Status (March 16, 2026)

### Completed This Session
- [x] Agent Details Drawer Modal — Premium full-screen drawer with rich profiles (mentality, animated skill bars, background, methodologies, personality, strengths, interaction style, inspirations)
- [x] Fixed Deploy button z-index overlap with bottom nav bar
- [x] Company Management in AI Studio — "Empresa Anunciante" section above Campaign Name with primary/secondary companies (name, phone, WhatsApp flag, website URL), persisted in localStorage
- [x] Default briefing mode changed from "Free Briefing" to "Guided Questionnaire"
- [x] Video audio duplication fix — Background videos now pause when lightbox expands
- [x] Backend updated to include website_url and is_whatsapp in AI pipeline context
- [x] All features tested 100% pass rate (iteration_40, iteration_41)

### Previously Completed
- [x] Audio duplication fix — Music reduced from 0dB to -22dB, all 10 existing videos remixed
- [x] Per-channel templates — 8 mockups (WhatsApp 1:1, TikTok 9:16, Facebook 16:9, etc.)
- [x] Image/Video toggle per channel mockup
- [x] Smart music selection (30+ industry moods)
- [x] FFmpeg text escaping fix
- [x] Recovery optimization (reuse AI scripts on video failure)
- [x] Remix API endpoints (individual + batch)
- [x] Video variant generation per platform
- [x] Skip video flag
- [x] Clip2 retry + fallback
- [x] Rich agent profiles in constants.py (all 25+ agents)
- [x] Google Calendar/Sheets integration in Agent Config

### Known Issues
- LLM Key budget status — User confirmed they have credit
- FFmpeg logo overlay sometimes fails (low priority)
- Cloned videos 12s bug fix implemented but not verified

### Upcoming Tasks (Priority Order)
1. P1: Verify 12-second cloned video bug fix
2. P1: Agent renaming feature
3. P1: Evaluate video generation cost reduction (fal.ai/Kling vs Sora 2)
4. P2: Universal Agent Sandbox
5. P2: Landing/Login Page Redesign
6. P3: WhatsApp MVP (Evolution API)
7. P4: AutoFlow Workflow Builder

### Future/Backlog
- Full Meta/WhatsApp Integration
- Unified Inbox
- Social Media Publishing
- Payment Gateway (Stripe)
- Admin Management System
- Legal & Publication (Terms, Privacy)
- pipeline.py refactoring (3200+ lines, needs modularization)

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

## Key API Endpoints
- POST /api/auth/login
- GET /api/campaigns
- POST /api/campaigns/pipeline (accepts skip_video, context.company, context.website_url, contact_info.is_whatsapp)
- GET /api/agents/marketplace (returns agents with rich profile data)

## Test Reports
- /app/test_reports/iteration_38.json (Channel templates)
- /app/test_reports/iteration_39.json (Skip video + format verification)
- /app/test_reports/iteration_40.json (Agent Details Drawer)
- /app/test_reports/iteration_41.json (Company management + briefing default + video fix)
