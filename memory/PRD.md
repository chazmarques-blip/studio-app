# AgentFlow - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentFlow" that allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram).

## Core Requirements
1. **Omnichannel Inbox**: Unified inbox for WhatsApp, Instagram, Facebook Messenger, Telegram
2. **AI Capabilities**: Text (Claude Sonnet), Voice (OpenAI Whisper), Images (Claude Vision)
3. **Multi-Agent Orchestration**: Switch between specialized agents in conversation
4. **Multi-Language**: UI in EN/PT/ES + agent auto-detect language
5. **Agent Marketplace**: 22+ pre-built agents (DONE)
6. **Real-Time Agent Editing**: Hot reload for agent config
7. **Real-Time Sync**: Google Calendar, Google Sheets
8. **Lead Nurturing**: Automated follow-up campaigns
9. **Integrated CRM**: Kanban board, AI-managed leads (DONE - basic)
10. **Design**: Dark luxury theme (blacks, grays, golds) (DONE)
11. **Pricing**: Freemium (1 agent, 50 msgs/week) + Starter ($49/mo) + Enterprise

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL via REST API)
- **Authentication**: Custom JWT + Supabase storage
- **User Language**: Portuguese (primary user)

## Database Schema (Supabase)
- **users**: id, email, password_hash, full_name, ui_language, company_name, onboarding_completed
- **tenants**: id, owner_id, name, slug, plan, limits (JSONB), usage (JSONB)
- **agents**: id, tenant_id, name, type, description, system_prompt, personality, ai_config
- **channels**: id, tenant_id, type, status, config (JSONB)
- **conversations**: id, tenant_id, channel_id, agent_id, contact_name, contact_phone, channel_type, status, is_handoff, language, last_message_at
- **messages**: id, conversation_id, sender, content, message_type, metadata
- **leads**: id, tenant_id, conversation_id, name, phone, email, company, stage, score, value, ai_analysis

## API Endpoints (ALL working)
### Auth
- POST /api/auth/signup, POST /api/auth/login, GET /api/auth/me, PUT /api/auth/profile
### Tenants
- POST /api/tenants, GET /api/tenants
### Agents
- GET /api/agents/marketplace (22 agents), POST /api/agents, GET /api/agents, GET/PUT/DELETE /api/agents/{id}
### Conversations & Messages
- GET/POST /api/conversations, GET /api/conversations/{id}, GET/POST /api/conversations/{id}/messages
### Channels
- GET/POST /api/channels, PUT /api/channels/{id}/status, DELETE /api/channels/{id}
### Leads/CRM
- GET/POST /api/leads, GET/PUT/DELETE /api/leads/{id}
### Webhook
- POST /api/webhook/whatsapp (Evolution API ready)
### Dashboard
- GET /api/dashboard/stats

## What's Been Implemented

### Phase 0: Foundation (COMPLETE) - March 2026
- Full scaffolding, dark luxury theme, 18 pages, 22 agents, JWT auth, Supabase migration

### Phase 1: Messaging & i18n (IN PROGRESS) - March 2026
- i18n complete: EN, PT, ES with language sync on login
- Messaging infrastructure: conversations, messages, channels, leads tables in Supabase
- Full CRUD APIs for all entities
- Chat/Inbox with real conversations, message detail, send messages
- CRM Kanban with real leads from API
- Dashboard with real stats from API
- WhatsApp webhook endpoint ready for Evolution API
- Channel management API

### Testing: iteration_3.json - Backend 100% (16/16), Frontend 95%

## Pending Issues
- WhatsApp webhook is built but no real Evolution API connected (MOCKED)

## Upcoming Phases
- **Phase 1 remaining**: Connect real Evolution API for WhatsApp, AI agent responses
- **Phase 2**: Multimodal AI & Multi-agent Orchestration (15 days)
- **Phase 3**: Omnichannel (Instagram, Facebook, Telegram) (15 days)
- **Phase 4**: CRM Kanban with AI (12 days)
- **Phase 5**: Dashboard & Analytics (8 days)
- **Phase 6**: Real-time Sync (Google Calendar/Sheets) (5 days)
- **Phase 7**: Lead Nurturing (5 days)
- **Phase 8**: Final Testing (2 days)

## Test Credentials
- Email: test@agentflow.com / Password: password123

## 18 Pages
Landing, Login, Onboarding, OnboardingAgentLang, Dashboard, Chat, Agents, AgentBuilder, AgentSandbox, CRM, LeadDetail, CampaignBuilder, Analytics, Settings, ChannelConnection, HandoffHuman, UpsellScreen, Pricing
