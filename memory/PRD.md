# AgentFlow - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentFlow". The platform allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram).

## User Persona
- Small and medium business owners
- Non-technical users (no-code platform)
- Need AI chatbot automation across social channels
- Language: System base in English, UI multilingual (Portuguese priority)

## Core Requirements
1. **Omnichannel AI Agents** - Deploy AI chatbots on WhatsApp, Instagram, Facebook Messenger, Telegram
2. **AI Capabilities** - Text (Claude), Voice (Whisper), Images (Claude Vision)
3. **Multi-Agent Orchestration** - Switch between specialized agents mid-conversation
4. **Multi-Language Support** - Auto-detect or fixed language per agent
5. **Freemium Model** - FREE (1 agent, 50 msgs/week) / STARTER ($49/mo) / ENTERPRISE
6. **Integrated CRM** - Kanban board, AI-powered lead scoring
7. **Real-Time Sync** - Google Calendar & Sheets
8. **Lead Nurturing** - Automated follow-up campaigns
9. **Design** - Dark Luxury theme (blacks, grays, gold)

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn/ui, Lucide Icons
- Backend: FastAPI (Python), Motor (MongoDB async)
- Database: MongoDB
- Auth: JWT-based custom auth (Supabase planned for future when DNS resolves)
- AI: Claude Sonnet + OpenAI Whisper (via Emergent LLM Key - pending)

## What's Been Implemented

### Phase 0: Foundation & Setup - COMPLETED [2026-03-12]
**Backend:**
- FastAPI server with full REST API
- JWT authentication (signup, login, me, profile update)
- Tenant management (create, get) with free plan limits
- Agent CRUD (create, read, update, delete) with plan limit enforcement
- Agent Marketplace (5 pre-built agents: Carol, Roberto, Ana, Lucas, Marina)
- Dashboard stats endpoint
- MongoDB integration for all data

**Frontend:**
- Dark Luxury theme implemented (CSS variables, gold accents, glass-morphism)
- Landing page (hero, features grid, pricing, channel badges, footer)
- Login/Signup page (email/password auth)
- Onboarding page (language selection - 6 languages)
- Dashboard (stats cards, quick actions, empty agent state, plan status)
- Chat inbox page (channel filters, empty state)
- Agents marketplace page (loads 5 agents from API)
- CRM Kanban page (5 stage columns)
- Analytics page (placeholder stats/charts)
- Settings page (profile, channels, menu items, logout)
- Bottom navigation (5 tabs: Chat, Agents, CRM, Analytics, Settings)
- Protected/Public route guards

**Testing:**
- All 17 backend tests passed (100%)
- All frontend UI tests passed (100%)
- Test credentials: demo@agentflow.com / Demo123!

### Visual Mockups - COMPLETED [2026-03-12]
18 screens generated with Dark Luxury theme (see CHANGELOG.md for URLs)

## Current Status
- Phase 0: COMPLETED
- Phase 1: NOT STARTED

## Prioritized Backlog
- **P0**: Phase 1 - WhatsApp Integration + Multi-language (i18n)
- **P1**: Phase 2 - AI Multimodal + Multi-agent (Claude, Whisper)
- **P2**: Phase 3 - Omnichannel (Instagram, Facebook, Telegram)
- **P3**: Phase 4 - CRM Kanban with AI
- **P4**: Phase 5 - Dashboard + Analytics
- **P5**: Phase 6 - Real-time Sync (Google Calendar + Sheets)
- **P6**: Phase 7 - Lead Nurturing
- **P7**: Phase 8 - Final Testing

## Known Limitations
- Supabase project DNS doesn't resolve from container (using JWT + MongoDB instead)
- Supabase credentials are stored in .env but not actively used
- AI integration not yet implemented (Claude, Whisper)
- Channel integrations not yet functional (WhatsApp, Instagram, etc.)
