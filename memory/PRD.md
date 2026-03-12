# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES), Framer Motion, Recharts
- **Backend**: FastAPI (Python) — Modular: core/ + routers/ + server.py
- **Database**: Supabase (PostgreSQL via REST API)
- **AI**: Claude 3.5 Sonnet + Claude Vision + OpenAI Whisper (Emergent LLM Key)

## Architecture
```
/app/backend/
├── server.py          (entry point + dashboard/billing routes)
├── core/
│   ├── constants.py   (MARKETPLACE_AGENTS + PERSONAL_AGENTS + types)
│   ├── deps.py, models.py, utils.py
├── routers/
│   ├── auth.py, agents.py, conversations.py, leads.py
│   ├── ai.py, whatsapp.py, channels.py, telegram.py
└── requirements.txt
```

## Completed Phases

### Phase 0-2: Foundation, Messaging, AI & Multimodal
### Landing Page (Multiple Revisions) - Feb/Mar 2026
### Backend Refactoring v0.4.0 - Feb 2026
### Phase 4: CRM Kanban with AI - Mar 2026
### Enhanced Agent Configuration - Mar 2026
### Pricing & Billing In-App Page - Mar 2026

### P0 Navigation Bug Fixes - Mar 12 2026
- Dashboard/Home in bottom nav, profile dropdown, Account in Settings

### Phase 5: Dynamic Dashboard v2 - Mar 12 2026
- KPIs, Recharts area chart, CRM Pipeline, Recent Conversations with channel SVGs
- AI Insights widget placeholder, Credit Counter, Quick Actions
- Full gold/black/gray/white color palette (no colored elements)

### Personal Agent Feature - Mar 12 2026
- 3 personal agents: Alex (productivity), Luna (wellness), Max (finance)
- Plan restriction: only Pro+ plans can deploy personal agents
- Backend: 403 error on deploy attempt for free/starter plans
- Frontend: Lock icon, "Upgrade to Pro" button, PRO+ badge, Crown filter
- Marketplace returns 25 agents (22 business + 3 personal)
- iteration_14: 100% backend (14/14) + 100% frontend

### Chat Gold Palette - Mar 12 2026
- Channel SVG icons (WhatsApp, Instagram, Telegram, Facebook, SMS) in gold
- All colored elements replaced with gold/gray tones

## Testing
- Iterations 2-14: All passed (100%)

## Plan Configuration
- Free: 1 agent, 200 msgs/mo, 1 channel, NO personal agent
- Starter: 3 agents, 1500 msgs/mo, 5 channels, NO personal agent
- Pro: 5 agents, 5000 msgs/mo, 5 channels, YES personal agent
- Enterprise: 10 agents, 10000 msgs/mo, 5 channels, YES personal agent

## Upcoming Tasks
1. **Phase 6: Google Calendar/Sheets** — Real-time sync integration
2. **Phase 7: Lead Nurturing** — Automated follow-up campaigns
3. **Phase 8: Integrações Omnichannel** — WhatsApp live, SMS Twilio, Instagram, Facebook, Telegram
4. **Avatar Customizável** — Foto/logo da empresa no perfil

## Later/Backlog
- AI Insights dinâmicos (Claude analysis)
- Analytics page with detailed charts
- Final Testing & Adjustments

## Test Credentials
- Email: test@agentflow.com / Password: password123
