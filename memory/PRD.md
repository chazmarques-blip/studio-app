# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a comprehensive, mobile-first, no-code SaaS platform for SMBs to deploy and configure pre-built AI agents on social media channels. Features include an AI Marketing Studio with multi-agent pipeline, a Traffic Hub for campaign distribution with channel-specialized agents, omnichannel inbox, CRM, and admin system.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Lucide Icons + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, Google APIs, FFmpeg, PIL/Pillow
- **Auth**: Supabase Auth (token key: `agentzz_token`)

## AI Agent Architecture

### AI Studio Agents (Campaign Creation)
| Step ID | Agent | Role | Model |
|---------|-------|------|-------|
| sofia_copy | **David** | Copywriter (Ogilvy) | Claude Sonnet 4.5 |
| ana_review_copy | **Lee** | Creative Director (Clow) | Gemini Flash |
| lucas_design | **Stefan** | Visual Designer (Sagmeister) | Claude Sonnet 4.5 |
| rafael_review_design | **George** | Art Director (Lois) | Gemini Flash |
| marcos_video | **Ridley** | Video Director (Scott) | Claude Sonnet 4.5 |
| rafael_review_video | **Roger** | Video Reviewer (Deakins) | Gemini Flash |
| pedro_publish | **Gary** | Campaign Validator (Vaynerchuk) | Gemini Flash |

### Traffic Hub Agents (Campaign Distribution)
| Agent | Role | Channels |
|-------|------|----------|
| **James** | Chief Traffic Manager | All channels |
| **Emily** | Meta Ads Manager | Instagram, Facebook |
| **Ryan** | TikTok Ads Manager | TikTok |
| **Sarah** | Messaging Manager | WhatsApp, Telegram, SMS |
| **Mike** | Google Ads Manager | Google Ads, Email |

## What's Been Implemented

### Core Platform
- Landing page, auth, dashboard, agent management, CRM, multi-language (EN/PT/ES)
- Dark luxury theme (monochrome gold/black/white)

### AI Marketing Studio (Phase 7) - COMPLETE
- 7-step pipeline: David → Lee → Stefan → George → Ridley → Roger → Gary
- Optimized revision: Max 1 revision, reviews via Gemini Flash (~5x faster)
- Adaptive media: PIL resizes for TikTok (9:16), Google Ads (16:9), Instagram (1:1)
- Gary validates as "Campaign Validator" (not publisher)
- Orphan pipeline recovery on server restart
- Fixed Sora 2 video sizes: `1024x1792` (vertical), `1280x720` (horizontal)
- 25 real music tracks, enhanced questionnaire, full i18n

### Traffic Hub (Phase 7.3) - COMPLETE
- `/traffic-hub` with 5 specialized traffic agents
- Campaign filtering by agent channels and status
- Activate/Pause/View campaigns
- Agent profiles with skills, online status
- Correct token handling (`agentzz_token`)

## Prioritized Backlog

### P0 (Critical)
- Traffic Hub AI integration (agents generate channel strategies via LLM)
- Sora 2 video generation returning empty - investigate API quota/limits

### P1 (High)
- Phase 8: Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Payment Gateway (Stripe)

### P2 (Medium)
- Creative Gallery
- Refactor pipeline.py (~2500 lines)
- Language mismatch verification in images

### P3 (Low)
- Advanced Video AI (Runway Gen-3, Veo)
- Mobile App (Capacitor)
- Terms/Privacy Policy

## Test Reports
- /app/test_reports/iteration_31.json (platform variants - 100%)
- /app/test_reports/iteration_32.json (agent renaming + Traffic Hub - 100%)

## Credentials
- Email: test@agentflow.com
- Password: password123
