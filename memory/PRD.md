# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES)
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL via REST API) - 9 tables
- **AI**: Claude Sonnet 4.5 + Claude Vision + OpenAI Whisper (via Emergent LLM Key)
- **Authentication**: Custom JWT + Supabase storage

## What's Been Implemented

### Phase 0: Foundation (COMPLETE)
- Dark luxury theme, 19 pages, 22 marketplace agents, JWT auth, Supabase migration

### Phase 1: Messaging, AI & Agent Config (COMPLETE)
- i18n (EN, PT, ES), AI Sandbox (Claude), AI Auto-Reply webhook, Agent Deployment
- Agent Personality, Knowledge Base CRUD, Follow-up/Reactivation rules
- Escalation detection, CRM leads, Chat/Inbox

### Phase 2: Multimodal AI & WhatsApp Integration (COMPLETE) - March 2026
- **WhatsApp (Evolution API)**: 6 backend endpoints, QR code flow, outbound messaging, auto-reply
- **Multimodal UI**: Image upload + Audio recording/upload in Chat.jsx and AgentSandbox.jsx
- **Vision**: Claude Vision analysis (image → text) integrated in both Chat and Sandbox
- **Whisper**: Audio transcription integrated in both Chat and Sandbox
- **Rebranding**: AgentFlow → AgentZZ with custom logo

### Testing (ALL 100%)
- iteration_2-5: Supabase, Messaging, AI, Agent Config
- iteration_6: WhatsApp Integration 8/8
- iteration_7: Multimodal UI + Rebranding 7/7

## Upcoming Phases (Priority Order)
1. **Agent Prompts**: Create system prompts for all 22 marketplace agents
2. **Multi-Agent Orchestration**: Frontend integration of route-agent endpoint
3. **SMS Integration (Twilio)**: Full send/receive SMS
4. **Backend Refactoring**: Split server.py into APIRouter modules
5. **WhatsApp Real Connection**: When domain is available

## Future Phases (Backlog)
- Phase 3: Omnichannel (Instagram, Facebook, Telegram)
- Phase 4: CRM Kanban with AI
- Phase 5: Dashboard & Analytics
- Phase 6: Google Calendar/Sheets
- Phase 7: Lead Nurturing
- Phase 8: Final Testing

## Test Credentials
- Email: test@agentflow.com / Password: password123
