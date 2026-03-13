# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES), Framer Motion, Recharts
- **Backend**: FastAPI (Python), google-api-python-client, google-auth-oauthlib
- **Database**: Supabase (PostgreSQL via REST API)
- **AI**: Claude 3.5 Sonnet + Claude Vision + OpenAI Whisper (Emergent LLM Key)
- **Google**: Calendar API, Sheets API, Drive API (OAuth2)

## Completed Phases
- Phase 0-2: Foundation, Messaging, AI & Multimodal
- Landing Page, Backend Refactoring, CRM Kanban, Agent Config, Pricing/Billing
- P0 Navigation Fixes, Dashboard v2 (dynamic), Personal Agents (Pro+)
- Chat gold palette, Agent detail modal, Name edit + Reset

### Phase 6: Google Integration — Mar 13 2026
- OAuth2 flow (connect/disconnect/status)
- Google Calendar: list events, create event, delete event
- Google Sheets: read, write, append, list spreadsheets
- Export Leads to Google Sheets (auto-creates spreadsheet)
- Google Drive: list files (readonly)
- Frontend: /settings/google page with connection management, Calendar/Sheets tabs
- Settings updated with Google menu item
- iteration_15: 100% backend (14/14) + 100% frontend

## Plan Configuration
- Free: 1 agent, 200 msgs/mo, NO personal agent
- Starter: 3 agents, 1500 msgs/mo, NO personal agent
- Pro: 5 agents, 5000 msgs/mo, YES personal agent
- Enterprise: 10 agents, 10000 msgs/mo, YES personal + Marketing AI Studio

## Upcoming Tasks
1. **Phase 7.1**: Lead Nurturing Engine (Pro+) — drip campaigns, segmentation, templates
2. **Phase 7.2**: Marketing AI Studio (Enterprise) — 4 AI agents (Copywriter, Designer, Reviewer, Publisher)
3. **Phase 8**: Integrações Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
4. **Phase 9**: Gateway de Pagamento (Stripe)
5. **Phase 10**: Painel Administrativo
6. **Phase 11**: Multi-tenancy & Escalabilidade
7. **Phase 12**: Compliance & App Store (Termos, LGPD, GDPR, Apple/Google requirements)
8. **Phase 13**: IA Avançada (AI Insights dinâmicos, análise sentimento, auto-treinamento)
9. **Phase 14**: Melhorias UX (avatar, onboarding wizard, analytics page, PWA)

## Test Credentials
- Email: test@agentflow.com / Password: password123
