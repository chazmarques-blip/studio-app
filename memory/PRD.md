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
│   ├── constants.py, deps.py, models.py, utils.py
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
- Added Dashboard/Home as first tab in bottom navigation
- Fixed profile button with dropdown (Edit Profile, Billing, Sign Out)
- Fixed Account in Settings with inline profile editing
- All 15 tests passed (iteration_12: 100%)

### Phase 5: Dynamic Dashboard - Mar 12 2026
- **KPI Cards**: Messages Today, Resolution Rate, Active Leads (with total), Revenue
- **Messages Chart**: Recharts AreaChart showing last 7 days volume
- **CRM Pipeline**: Colored bar visualization (New, Qualified, Proposal, Won)
- **Recent Conversations**: Last 5 with channel icons, status badges, time ago
- **Agent Performance**: Per-agent metrics (conversations, resolved)
- **Credit Counter**: Dynamic counter in header showing remaining credits (clickable → /pricing)
- **Quick Actions**: 3-button grid (Create Agent, View Inbox, View CRM)
- **Plan & Usage**: Dual progress bars (messages + agents) with upgrade button
- **Greeting**: Time-based (Bom dia/Boa tarde/Boa noite)
- **Backend**: Enriched /api/dashboard/stats with messages_by_day, recent_conversations, agents, crm_pipeline, channel_stats
- All 14 backend + all frontend tests passed (iteration_13: 100%)

## Testing (ALL 100%)
- Iterations 2-13: All passed

## Upcoming Tasks
1. **Agente Pessoal** — Agent type "personal" for daily tasks
2. **Phase 6: Google Calendar/Sheets** — Real-time sync
3. **Phase 7: Lead Nurturing** — Automated follow-up campaigns

## Later/Backlog
- Phase 8: Omnichannel Integrations (WhatsApp live, SMS Twilio, Instagram, Facebook, Telegram)
- Final Testing & Adjustments

## Test Credentials
- Email: test@agentflow.com / Password: password123
