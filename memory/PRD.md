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

### Phase 2: Multimodal AI & WhatsApp + Agent Prompts (COMPLETE) - March 2026
- **WhatsApp (Evolution API)**: 6 backend endpoints, QR code flow, outbound messaging, auto-reply
- **Multimodal UI**: Image upload + Audio recording/upload in Chat.jsx and AgentSandbox.jsx
- **Vision**: Claude Vision analysis integrated in Chat and Sandbox
- **Whisper**: Audio transcription integrated in Chat and Sandbox
- **Multi-Agent Orchestration**: Route button in Chat header + AI-powered agent routing
- **22 Agent Prompts**: Professional system prompts (500-770 chars each) with specific protocols, methodologies, escalation rules per category
- **Rebranding**: AgentFlow → AgentZZ with custom logo
- **Social Media Icons**: Official SVG icons in gold on Landing page

### Testing (ALL 100%)
- iteration_2-5: Supabase, Messaging, AI, Agent Config
- iteration_6: WhatsApp Integration 8/8
- iteration_7: Multimodal UI + Rebranding 7/7
- iteration_8: Agent Prompts + Orchestration + Icons 7/7

## Upcoming Tasks (Priority Order)
1. **SMS Integration (Twilio)**: Full send/receive SMS via Twilio
2. **Backend Refactoring**: Split server.py (1600+ lines) into APIRouter modules
3. **WhatsApp Real Connection**: When domain is available

## Future Phases (Backlog)
- Phase 3: Omnichannel (Instagram, Facebook, Telegram)
- Phase 4: CRM Kanban with AI
- Phase 5: Dashboard & Analytics
- Phase 6: Google Calendar/Sheets
- Phase 7: Lead Nurturing
- Phase 8: Final Testing

## Test Credentials
- Email: test@agentflow.com / Password: password123
