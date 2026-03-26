# AgentZZ — Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users to deploy AI agents on social media channels, AND a "Directed Studio Mode" for generating AI-powered animated films with visual/narrative consistency.

## Core Architecture
- **Frontend:** React + Tailwind CSS + shadcn-ui + Lucide Icons + Framer Motion + recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) for core data
- **3rd Party:** Anthropic Claude (Emergent LLM Key), OpenAI Sora 2, Gemini Nano Banana (Emergent LLM Key), ElevenLabs TTS, Google APIs

## Key Routes
- `/marketing/studio` — Marketing AI Studio (includes Directed Studio Mode)
- `/dashboard` — Main dashboard
- `/agents` — Agent management

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Phase 1-5: Core Platform (Complete)
- User auth, agent marketplace, dashboard, CRM, omnichannel UI
- Agent configuration with knowledge base, personality, integrations
- Google Calendar/Sheets integration in agent config

### Phase 6: Google Integration (Complete)
- Backend endpoints for Google Calendar/Sheets listing
- Dynamic connection status in AgentConfig
- Agent integrations_config persistence

### Directed Studio Mode (Core Pipeline - Complete)
- 5-step pipeline: Roteiro → Personagens → **Storyboard** → Produção → Resultado
- Claude-powered screenwriter chat
- Character avatar system with AI generation
- Production design (character bible, style DNA)
- Parallel generation pipeline (ThreadPool + Semaphores for Sora 2 + Gemini)
- Multi-voice dubbed mode (ElevenLabs voices per character)
- Post-production audio mixing
- Scene recovery ("Unificar Roteiro")

### Phase 7: Editable Storyboard Pipeline (Complete - 2026-03-26)
- **New Step 3 — Storyboard** inserted between Characters and Production
- `StoryboardEditor.jsx` component with:
  - Generate all panels button (Gemini Nano Banana images)
  - 2-column panel grid with image + dialogue + character tags
  - Inline panel editing (title, description, dialogue)
  - "Save & Regenerate" per-panel
  - Expand panel for detailed view
- **AI Facilitator Chat** — sidebar chat powered by Claude that interprets natural language commands to edit panels
- **Approve Storyboard** flow — must approve before proceeding to video production
- Backend module: `/app/backend/core/storyboard.py` (generate_all_panels, facilitator_chat)
- 6 new endpoints in `/app/backend/routers/studio.py`:
  - POST /generate-storyboard
  - GET /storyboard
  - POST /storyboard/regenerate-panel
  - PATCH /storyboard/edit-panel
  - PATCH /storyboard/approve
  - POST /storyboard/chat

---

## Prioritized Backlog

### P0 (Next)
- None currently

### P1
- Storybook Export (export storyboard as static PDF/image book)
- Storyboard-to-Video integration (feed approved panels to Sora 2)
- Refactor `studio.py` (~4000 lines) into modular services
- Fix hot-reload killing background tasks

### P2
- Phase 8: Omnichannel live integrations (WhatsApp Evolution API, Twilio SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Stripe payment integration

### P3
- Legal & publication (Terms, Privacy Policy)
- Scalability hardening
- App store submission

---

## Known Issues
- Hot-reload kills background production threads (P1)
- `studio.py` is ~4300 lines and needs refactoring (P1)
- Supabase intermittent connection issues (mitigated with retry logic)

## Project Health
- **Running:** Core platform, Directed Studio, Storyboard pipeline, parallel generation, dubbed mode
- **Mocked:** External channel integrations (WhatsApp, Telegram, etc.)
