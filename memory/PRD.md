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

### Completed
- [x] Full UI redesign with dark luxury theme
- [x] Agent marketplace with 25 cyberpunk avatars
- [x] AI Marketing Studio pipeline (7-step AI agent workflow)
- [x] Video generation with Sora 2
- [x] Audio mixing fix (music volume corrected, batch remix for all videos)
- [x] Per-channel content templates (WhatsApp 1:1, TikTok 9:16, Facebook 16:9, etc.)
- [x] Image/Video toggle per channel mockup
- [x] FFmpeg text escaping fix (special chars in CTA)
- [x] Recovery optimization (reuse AI scripts on video failure)
- [x] Smart music selection (30+ mood options by industry)
- [x] Rafael review agent now checks audio quality
- [x] remix-audio and remix-all-videos API endpoints
- [x] Video variant generation per platform (crop/resize from master)
- [x] Google Calendar/Sheets integration in Agent Config

### Known Issues
- LLM Key budget exceeded (blocks AI Agent Generator and all AI generation)
- Audio fix for previously generated videos applied but user should verify quality
- FFmpeg logo overlay sometimes fails (low priority)

### Upcoming Tasks (Priority Order)
1. P0: Contact Management System in Marketing Studio
2. P1: Detailed Agent Profiles + Details Modal
3. P1: Agent renaming + Universal Sandbox
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

## Key API Endpoints
- POST /api/auth/login
- GET /api/campaigns
- POST /api/campaigns/pipeline/start
- GET /api/campaigns/pipeline/{id}
- POST /api/campaigns/pipeline/{id}/remix-audio
- POST /api/campaigns/pipeline/remix-all-videos
- GET /api/agents/marketplace
- POST /api/agents/generate (BLOCKED)

## Key Files
- /app/frontend/src/pages/Marketing.jsx - Marketing page with channel mockups
- /app/backend/routers/pipeline.py - Video pipeline with audio mixing
- /app/backend/routers/campaigns.py - Campaign CRUD
- /app/backend/core/constants.py - Agent marketplace data
- /app/frontend/src/pages/Agents.jsx - Agent marketplace UI
