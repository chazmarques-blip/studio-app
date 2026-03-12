# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES)
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL via REST API) - 9 tables
- **AI**: Claude Sonnet 4.5 via Emergent LLM Key + OpenAI Whisper + Claude Vision
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

## What's Been Implemented

### Phase 0: Foundation (COMPLETE)
- Dark luxury theme, 19 pages, 22 marketplace agents, JWT auth, Supabase migration

### Phase 1: Messaging, AI & Agent Config (COMPLETE)
- i18n (EN, PT, ES), AI Sandbox (Claude), AI Auto-Reply webhook, Agent Deployment
- Agent Personality, Knowledge Base CRUD, Follow-up/Reactivation rules
- Escalation detection, CRM leads in 5-stage Kanban, Chat/Inbox

### Phase 2: WhatsApp Integration via Evolution API (COMPLETE) - March 2026
- 6 new backend endpoints: create-instance, QR code, status, messaging, webhook, delete
- Frontend WhatsApp Setup: Config form → QR Code → Auto-polling → Connected state
- Outbound messaging: operator replies auto-sent via WhatsApp
- AI Auto-Reply via WhatsApp: incoming → AI responds → sends back via Evolution API
- Multimodal Backend: Claude Vision + Whisper endpoints ready

### Rebranding: AgentFlow → AgentZZ (COMPLETE) - March 2026
- Updated all references across frontend (Landing, Login, locales), backend (API service name), and localStorage keys
- Integrated user's custom logo with transparent background crop
- Added SMS as 5th channel badge on Landing page

### Testing (ALL 100%)
- iteration_2: Supabase 17/17
- iteration_3: Messaging 16/16
- iteration_4: AI Sandbox 8/8
- iteration_5: Agent Config 15/15
- iteration_6: WhatsApp Integration 8/8 + frontend 100%

## 19 Pages
Landing, Login, Onboarding, OnboardingAgentLang, Dashboard, Chat, Agents, AgentBuilder, AgentSandbox, AgentConfig, CRM, LeadDetail, CampaignBuilder, Analytics, Settings, ChannelConnection, HandoffHuman, UpsellScreen, Pricing

## Upcoming Phases (Priority Order)
1. **Multimodal UI in Chat/Sandbox** — Image/audio upload buttons connected to Vision/Whisper endpoints
2. **Multi-Agent Orchestration** — Frontend integration of route-agent endpoint
3. **SMS Integration (Twilio)** — Full send/receive SMS integration
4. **Backend Refactoring** — Split server.py into APIRouter modules
5. **WhatsApp Real Connection** — When domain is available, connect to Evolution API

## Future Phases (Backlog)
- Phase 3: Omnichannel (Instagram, Facebook, Telegram)
- Phase 4: CRM Kanban with AI
- Phase 5: Dashboard & Analytics
- Phase 6: Google Calendar/Sheets
- Phase 7: Lead Nurturing
- Phase 8: Final Testing

## Test Credentials
- Email: test@agentflow.com / Password: password123
