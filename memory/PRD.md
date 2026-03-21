# AgentZZ - PRD

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Includes AI Marketing Studio for multimodal campaign generation.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion + recharts
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Claude Sonnet 4.5, Gemini Flash, Gemini Nano Banana (images), Sora 2 (video), ElevenLabs (voice/music)
- Auth: Supabase Auth
- Pipeline: Multi-agent AI directors (Sofia, Lee, Ana, Lucas, Rafael, George, Stefan, Dylan, Roger, Marcos, Pedro)

## Implemented Features (Completed)
- Dashboard with recharts analytics
- Agent Management + Marketplace
- Agent Configuration with Google Calendar/Sheets integration
- AI Marketing Studio with full pipeline
- Campaign Gallery with Art Style Generator (14 styles)
- Avatar 3D Creator with 360-degree views
- Video generation pipeline (Sora 2 + FFmpeg)
- Audio Pre-Approval (pipeline pauses before video)
- FFmpeg quality: CRF 16, scale+crop, 256k/320k audio
- Landing Page V2
- Multi-language support (PT/EN/ES)

## Completed This Session (2026-03-21)
- BUG FIX: Campaign gallery image selection now updates the channel mockup preview (was always showing first image)
- BUG FIX: Router ordering conflict resolved (pipeline_router before campaigns_router in server.py)
- P0 FEATURE: ElevenLabs voice catalog expanded from 10 to 24 verified premade voices with rich metadata
  - All voices support multilingual (PT/ES/EN/28+ languages)
  - Includes female (11), male (12), non-binary (1) voices
  - Hardcoded catalog (API key lacks voices_read permission)
  - Dylan's prompt now includes detailed voice descriptions for context-aware selection
  - _generate_voice_alternatives() updated to use hardcoded catalog

## Backlog
### P1
- Omnichannel integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- CRM Kanban board

### P2
- Admin Management System
- Payment Gateway
- Terms of Use / Privacy Policy

### P3
- Refactor PipelineView.jsx (>2700 lines)
- Scalability hardening

## Known Issues
- Sora 2 video generation returning "insufficient_balance" - user needs to add balance via Profile > Universal Key > Add Balance
- ElevenLabs API key lacks voices_read permission (mitigated with hardcoded catalog)
- Live social channel integrations are mocked

## Test Credentials
- Email: test@agentflow.com
- Password: password123
