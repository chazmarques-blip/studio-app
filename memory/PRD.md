# AgentFlow - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentFlow" that allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL via REST API)
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key (emergentintegrations)
- **Authentication**: Custom JWT + Supabase storage

## Database Schema (Supabase) - 7 tables
- **users**: id, email, password_hash, full_name, ui_language, company_name, onboarding_completed
- **tenants**: id, owner_id, name, slug, plan, limits (JSONB), usage (JSONB)
- **agents**: id, tenant_id, name, type, description, system_prompt, personality, ai_config
- **channels**: id, tenant_id, type, status, config (JSONB)
- **conversations**: id, tenant_id, channel_id, agent_id, contact_name, contact_phone, channel_type, status, is_handoff, language, last_message_at
- **messages**: id, conversation_id, sender, content, message_type, metadata
- **leads**: id, tenant_id, conversation_id, name, phone, email, company, stage, score, value, ai_analysis

## API Endpoints (ALL working - 24+ endpoints)
### Auth: POST signup, POST login, GET me, PUT profile
### Tenants: POST create, GET get
### Agents: GET marketplace (22), POST create, GET list, GET/PUT/DELETE by id
### Conversations: GET list (with filters), POST create, GET detail, GET/POST messages
### AI: POST /sandbox/chat (real Claude Sonnet), DELETE /sandbox/{id}, POST /conversations/{id}/ai-reply
### Channels: GET/POST channels, PUT status, DELETE
### Leads/CRM: GET/POST leads, GET/PUT/DELETE by id
### Webhook: POST/GET /webhook/whatsapp
### Dashboard: GET /dashboard/stats

## What's Been Implemented

### Phase 0: Foundation (COMPLETE)
- Full scaffolding, dark luxury theme, 18 pages, 22 agents, JWT auth, Supabase migration

### Phase 1: Messaging, AI & i18n (COMPLETE) - March 2026
- **i18n**: EN, PT, ES with language sync on login/profile
- **Messaging**: Conversations, messages, channels CRUD (Supabase)
- **Chat/Inbox**: Real conversations, message detail, send messages, channel filters
- **AI Sandbox**: Real Claude Sonnet conversation, multi-turn context, debug panel (time, tokens, language, model)
- **AI Auto-Reply**: Generate AI responses in conversations
- **CRM Kanban**: Real leads from Supabase in 5-stage pipeline
- **Dashboard**: Real stats from API
- **WhatsApp Webhook**: Endpoint ready for Evolution API

### Testing Results
- iteration_2: Supabase migration 17/17 (100%)
- iteration_3: Messaging infrastructure 16/16 (100%)
- iteration_4: AI Sandbox + Reply 8/8 (100%), Frontend 100%

## Pending / Next Steps
- Connect real Evolution API for WhatsApp
- Agent deployment from marketplace to tenant
- Advanced language detection in messages

## Upcoming Phases
- **Phase 2**: Multimodal AI (Claude Vision, Whisper voice) & Multi-agent Orchestration
- **Phase 3**: Omnichannel (Instagram, Facebook, Telegram)
- **Phase 4**: CRM Kanban with AI (auto-classify leads)
- **Phase 5**: Dashboard & Analytics (charts, reports)
- **Phase 6**: Real-time Sync (Google Calendar/Sheets)
- **Phase 7**: Lead Nurturing (automated campaigns)
- **Phase 8**: Final Testing

## Test Credentials
- Email: test@agentflow.com / Password: password123

## 18 Pages
Landing, Login, Onboarding, OnboardingAgentLang, Dashboard, Chat, Agents, AgentBuilder, AgentSandbox, CRM, LeadDetail, CampaignBuilder, Analytics, Settings, ChannelConnection, HandoffHuman, UpsellScreen, Pricing
