# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a comprehensive, mobile-first, no-code SaaS platform for SMBs to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Features include an AI Marketing Studio with multi-agent video/image generation pipeline, a Traffic Hub for campaign distribution, omnichannel inbox, CRM, and admin system.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Lucide Icons + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB for flexible-schema features
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, Google APIs, FFmpeg, PIL/Pillow
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage

## AI Agent Architecture

### AI Studio Agents (Campaign Creation)
| Step ID | Agent | Role | Model |
|---------|-------|------|-------|
| sofia_copy | **David** | Copywriter | Claude Sonnet 4.5 |
| ana_review_copy | **Lee** | Creative Director | Gemini Flash |
| lucas_design | **Stefan** | Visual Designer | Claude Sonnet 4.5 |
| rafael_review_design | **George** | Art Director | Gemini Flash |
| marcos_video | **Ridley** | Video Director | Claude Sonnet 4.5 |
| rafael_review_video | **Roger** | Video Reviewer | Gemini Flash |
| pedro_publish | **Gary** | Campaign Validator | Gemini Flash |

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
- Landing page, auth system, dashboard with recharts analytics
- Agent management with marketplace, configuration, Google Calendar/Sheets integration
- CRM with Kanban board, multi-language support (EN/PT/ES)
- Dark luxury theme (monochrome gold/black/white)

### AI Marketing Studio (Phase 7) - COMPLETE
- Multi-agent pipeline: David -> Lee -> Stefan -> George -> Ridley -> Roger -> Gary
- Optimized revision loop: Max 1 revision, reviews use Gemini Flash (~5x faster)
- Post-video validation by Roger with revision loop to Ridley
- Adaptive media formats: PIL resizes for TikTok (9:16), Google Ads (16:9)
- Gary validates campaigns as "Created" (not published) - ready for Traffic Hub
- 25 real royalty-free music tracks, enhanced questionnaire
- Full i18n (EN/PT/ES)

### Traffic Hub (Phase 7.3) - NEW (March 15, 2026)
- New page at `/traffic-hub` with 5 specialized traffic management agents
- Agent cards with profile, skills, online status
- Campaign filtering by agent channels and status (Todas/Criadas/Ativas/Rascunho)
- Activate/Pause campaigns directly from Traffic Hub
- Button in Marketing header for Enterprise users

## Prioritized Backlog

### P0 (Critical)
- Verify language mismatch fix in generated images (testing pending)
- Video fullscreen button verification

### P1 (High)
- Traffic Hub AI integration (agents use LLM to generate channel-specific strategies)
- Phase 8: Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System

### P2 (Medium)
- Payment Gateway Integration (Stripe)
- Creative Gallery (browse/reuse generated assets)
- Refactor pipeline.py (~2400 lines -> smaller modules)

### P3 (Low)
- Advanced Video AI (Runway Gen-3, Google Veo)
- Mobile App (Capacitor)
- Terms of Use / Privacy Policy

## Test Reports
- /app/test_reports/iteration_31.json (pipeline review + platform variants - 100%)
- /app/test_reports/iteration_32.json (agent renaming + Traffic Hub - 100%)

## Credentials
- Email: test@agentflow.com
- Password: password123
