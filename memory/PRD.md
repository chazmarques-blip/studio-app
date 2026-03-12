# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES), Framer Motion
- **Backend**: FastAPI (Python) — Modular: core/ + routers/ + server.py
- **Database**: Supabase (PostgreSQL via REST API)
- **AI**: Claude Sonnet 4.5 + Claude Vision + OpenAI Whisper (Emergent LLM Key)

## Architecture (Post-Refactoring v0.4.0)
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

### Phase 0: Foundation
### Phase 1: Messaging, AI & Agent Config
### Phase 2: Multimodal + WhatsApp + Orchestration
### Landing Page Redesign - Feb 2026
- Centered hero with content above chat demo
- Live chat demo (Sofia agent auto-responds)
- Channel orbit visualization
- Agent showcase, Features grid, Pricing, CTA
- Social media SVG icons throughout

### Backend Refactoring v0.4.0 - Feb 2026
- Monolithic server.py (~1400 lines) split into 7 modular routers
- Core utilities extracted to core/utils.py
- Models updated with missing fields (language_mode, fixed_language, etc.)
- All 12+ API endpoints verified working (iteration_9: 100%)

### Landing Page v2 - Mar 2026
- Compacted layout, all icons in gold (#C9A84C) only
- Removed orbit animation, horizontal channel grid
- Hero image (person + AI robot) + chat demo side by side
- Palette: gold, black, white only

### Phase 4: CRM Kanban with AI - Mar 2026
- 5-column drag-and-drop Kanban board (new/qualified/proposal/won/lost)
- Lead creation modal with form fields
- Dynamic lead detail page with stage dropdown
- AI lead scoring via Claude (score 0-100, analysis, next_action)
- Mark as Won/Lost quick actions, Delete lead
- All tests passed (iteration_10: 100%)

### Testing (ALL 100%)
- iterations 2-9: All passed

## Upcoming Tasks
1. **Phase 5: Dashboard & Analytics** — Data visualization, metrics, charts
2. **Phase 6: Google Calendar/Sheets** — Real-time sync
3. **Phase 7: Lead Nurturing** — Automated follow-up campaigns

## Later (End)
- Phase 8: Omnichannel Integrations (WhatsApp live, SMS Twilio, Instagram, Facebook, Telegram)
- Final Testing & Adjustments

## Test Credentials
- Email: test@agentflow.com / Password: password123
