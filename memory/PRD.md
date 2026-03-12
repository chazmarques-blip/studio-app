# AgentFlow - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentFlow" that allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram).

## Core Requirements
1. **Omnichannel Inbox**: Unified inbox for WhatsApp, Instagram, Facebook Messenger, Telegram
2. **AI Capabilities**: Text (Claude Sonnet), Voice (OpenAI Whisper), Images (Claude Vision)
3. **Multi-Agent Orchestration**: Switch between specialized agents in conversation
4. **Multi-Language**: UI language selection + agent auto-detect language
5. **Agent Marketplace**: 22+ pre-built agents (DONE)
6. **Real-Time Agent Editing**: Hot reload for agent config
7. **Real-Time Sync**: Google Calendar, Google Sheets
8. **Lead Nurturing**: Automated follow-up campaigns
9. **Integrated CRM**: Kanban board, AI-managed leads
10. **Design**: Dark luxury theme (blacks, grays, golds) (DONE)
11. **Pricing**: Freemium (1 agent, 50 msgs/week) + Starter ($49/mo) + Enterprise

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL via REST API)
- **Authentication**: Custom JWT + Supabase storage
- **User Language**: Portuguese (primary user)

## Architecture
```
Frontend (React:3000) -> /api prefix -> Backend (FastAPI:8001) -> Supabase REST API
```

## Database Schema (Supabase)
- **users**: id (UUID), email, password_hash, full_name, ui_language, company_name, onboarding_completed
- **tenants**: id (UUID), owner_id (FK), name, slug, plan, limits (JSONB), usage (JSONB)
- **agents**: id (UUID), tenant_id (FK), name, type, description, system_prompt, personality (JSONB), ai_config (JSONB)

## API Endpoints
- `POST /api/auth/signup` - Register user
- `POST /api/auth/login` - Login, returns JWT
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update profile
- `POST /api/tenants` - Create tenant
- `GET /api/tenants` - Get user's tenant
- `GET /api/agents/marketplace` - Get 22 marketplace agents
- `POST /api/agents` - Create agent
- `GET /api/agents` - List user's agents
- `GET /api/agents/{id}` - Get specific agent
- `PUT /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent
- `GET /api/dashboard/stats` - Dashboard statistics

## What's Been Implemented

### Phase 0: Foundation (COMPLETE) - March 2026
- Full project scaffolding (React + FastAPI)
- Dark luxury UI theme across all pages
- 18 placeholder pages with routing
- 22 pre-built marketplace agents
- i18next framework with EN/PT translations
- Custom JWT authentication
- **Supabase migration COMPLETE** (was MongoDB, now Supabase REST API)

### Testing Status
- Backend: 17/17 tests pass (100%)
- Frontend: All flows working (100%)
- Test report: /app/test_reports/iteration_2.json

## Pending Issues
- **i18n incomplete**: Only Dashboard fully translated to Portuguese; other pages still show English text
- Bottom navigation labels in English

## Upcoming Phases
- **Phase 1**: WhatsApp Integration & Advanced Multi-language (8 days)
- **Phase 2**: Multimodal AI & Multi-agent Orchestration (15 days)
- **Phase 3**: Omnichannel (Instagram, Facebook, Telegram) (15 days)
- **Phase 4**: CRM Kanban with AI (12 days)
- **Phase 5**: Dashboard & Analytics (8 days)
- **Phase 6**: Real-time Sync (Google Calendar/Sheets) (5 days)
- **Phase 7**: Lead Nurturing (5 days)
- **Phase 8**: Final Testing & Adjustments (2 days)

## Test Credentials
- Email: test@agentflow.com
- Password: password123

## 18 Pages
1. Landing, 2. Login, 3. Onboarding, 4. OnboardingAgentLang, 5. Dashboard, 6. Chat, 7. Agents, 8. AgentBuilder, 9. AgentSandbox, 10. CRM, 11. LeadDetail, 12. CampaignBuilder, 13. Analytics, 14. Settings, 15. ChannelConnection, 16. HandoffHuman, 17. UpsellScreen, 18. Pricing
