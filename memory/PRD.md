# AgentFlow - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentFlow" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES)
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL via REST API) - 9 tables
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key
- **Authentication**: Custom JWT + Supabase storage

## Database Schema (Supabase) - 9 tables
- **users**: id, email, password_hash, full_name, ui_language, company_name, onboarding_completed
- **tenants**: id, owner_id, name, slug, plan, limits, usage
- **agents**: id, tenant_id, name, type, description, system_prompt, personality, ai_config, tone, emoji_level, verbosity_level, escalation_rules, follow_up_config, knowledge_instructions, is_deployed, marketplace_template_id
- **agent_knowledge**: id, agent_id, type, title, content
- **follow_up_rules**: id, agent_id, trigger_type, delay_hours, message_template, is_active
- **channels**: id, tenant_id, type, status, config
- **conversations**: id, tenant_id, channel_id, agent_id, contact_name, contact_phone, channel_type, status, is_handoff, language, last_message_at
- **messages**: id, conversation_id, sender, content, message_type, metadata
- **leads**: id, tenant_id, conversation_id, name, phone, email, company, stage, score, value, ai_analysis

## API Endpoints (30+ working)
### Auth: POST signup, POST login, GET me, PUT profile
### Tenants: POST create, GET get
### Agents: GET marketplace (22), POST deploy, POST create, GET list, GET/PUT/DELETE by id
### Agent Knowledge: GET/POST/DELETE /agents/{id}/knowledge
### Follow-up Rules: GET/POST/DELETE /agents/{id}/follow-up-rules
### AI: POST /sandbox/chat, DELETE /sandbox/{id}, POST /conversations/{id}/ai-reply
### Conversations: GET/POST, GET detail, GET/POST messages
### Channels: GET/POST, PUT status, DELETE
### Leads/CRM: GET/POST, GET/PUT/DELETE by id
### Webhook: POST /webhook/whatsapp (auto-reply + escalation)
### Dashboard: GET /dashboard/stats

## What's Been Implemented

### Phase 0: Foundation (COMPLETE)
- Scaffolding, dark luxury theme, 19 pages, 22 agents, JWT auth, Supabase migration

### Phase 1: Messaging, AI & Agent Config (COMPLETE) - March 2026
- **i18n**: EN, PT, ES with auto sync on login
- **AI Sandbox**: Real Claude Sonnet conversation, multi-turn, debug panel
- **AI Auto-Reply**: Webhook receives message → knowledge base lookup → AI responds → escalation detection
- **Agent Deployment**: Deploy from marketplace → auto-configure → start responding
- **Agent Personality**: 5 tones (Professional, Friendly, Empathetic, Direct, Consultive), emoji/verbosity sliders
- **Knowledge Base**: CRUD for FAQs, products, policies, hours, custom
- **Follow-up/Reactivation**: Post-service automation rules (after close, inactive 24h/48h, post-sale, cart abandoned)
- **Escalation**: Keyword detection → handoff to human → operator takes over
- **CRM**: Real leads in 5-stage Kanban
- **Chat/Inbox**: Real conversations with AI Reply button

### Testing (ALL 100%)
- iteration_2: Supabase 17/17
- iteration_3: Messaging 16/16
- iteration_4: AI Sandbox 8/8
- iteration_5: Agent Config 15/15

## 19 Pages
Landing, Login, Onboarding, OnboardingAgentLang, Dashboard, Chat, Agents, AgentBuilder, AgentSandbox, AgentConfig, CRM, LeadDetail, CampaignBuilder, Analytics, Settings, ChannelConnection, HandoffHuman, UpsellScreen, Pricing

## Upcoming Phases
- **Phase 2**: Multimodal AI (Claude Vision for images, Whisper for voice)
- **Phase 3**: Omnichannel (Instagram, Facebook, Telegram)
- **Phase 4**: CRM with AI (auto-classify leads, AI analysis)
- **Phase 5**: Dashboard & Analytics (charts, reports)
- **Phase 6**: Google Calendar/Sheets integration
- **Phase 7**: Lead Nurturing campaigns
- **Phase 8**: Final Testing

## Test Credentials
- Email: test@agentflow.com / Password: password123
