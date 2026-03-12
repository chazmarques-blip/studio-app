# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES), Framer Motion
- **Backend**: FastAPI (Python) — Modular: core/ + routers/ + server.py
- **Database**: Supabase (PostgreSQL via REST API)
- **AI**: Claude 3.5 Sonnet + Claude Vision + OpenAI Whisper (Emergent LLM Key)

## Architecture
```
/app/backend/
├── server.py          (~60 lines - slim entry point)
├── core/
│   ├── constants.py   (Marketplace agents, type descriptions)
│   ├── deps.py        (Supabase client, auth, JWT)
│   ├── models.py      (Pydantic models)
│   └── utils.py       (AI prompt builder, escalation, evo_request)
├── routers/
│   ├── auth.py        (signup, login, me, profile, tenants)
│   ├── agents.py      (CRUD, marketplace, deploy, knowledge, follow-ups)
│   ├── conversations.py (CRUD, messages, multimedia, AI reply)
│   ├── leads.py       (CRUD)
│   ├── ai.py          (sandbox, vision, whisper, agent routing)
│   ├── whatsapp.py    (Evolution API, webhooks)
│   └── channels.py    (CRUD)
└── requirements.txt
```

## Completed Phases

### Phase 0-2: Foundation, Messaging, AI & Multimodal
### Landing Page (Multiple Revisions) - Feb/Mar 2026
### Backend Refactoring v0.4.0 - Feb 2026
### Landing Page v2 - Mar 2026
### Phase 4: CRM Kanban with AI - Mar 2026
### Enhanced Agent Configuration - Mar 2026
### Pricing & Billing In-App Page - Mar 2026

### P0 Navigation Bug Fixes - Mar 12 2026
- Added Dashboard/Home as first tab in bottom navigation (BottomNav.jsx)
- Fixed profile button: gold avatar opens dropdown with Edit Profile, Billing & Plan, Sign Out
- Fixed Account in Settings: opens inline profile editing panel (name, company, email)
- Added i18n translations for profile keys (EN/PT/ES)
- All 15 frontend tests passed (iteration_12: 100%)

## Testing (ALL 100%)
- Iterations 2-12: All passed

## Upcoming Tasks
1. **Phase 5: Dashboard & Analytics** — Data visualization, metrics, charts
2. **Agente Pessoal** — Agent type "personal" for daily tasks
3. **Phase 6: Google Calendar/Sheets** — Real-time sync
4. **Phase 7: Lead Nurturing** — Automated follow-up campaigns

## Later/Backlog
- Phase 8: Omnichannel Integrations (WhatsApp live, SMS Twilio, Instagram, Facebook, Telegram)
- Final Testing & Adjustments

## Test Credentials
- Email: test@agentflow.com / Password: password123
