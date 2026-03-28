# AgentZZ — Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for deploying AI agents on social channels and producing creative content via a Directed Studio Mode.

## Architecture
- **Frontend:** React + Tailwind CSS + shadcn/ui + Framer Motion + recharts
- **Backend:** FastAPI (Python) + Supabase (PostgreSQL) + MongoDB
- **3rd Party:** Anthropic Claude 4.5 Sonnet, OpenAI Whisper, Gemini Nano Banana, ElevenLabs (TTS), Google APIs
- **PWA:** Service Worker + Manifest configured

## What's Been Implemented

### Core Platform
- Authentication (Supabase Auth), Multi-language UI (EN/PT/ES), Dark luxury theme
- Dashboard with recharts analytics, Agent Marketplace with plan-gating
- Agent Configuration with Google Calendar/Sheets integration

### Directed Studio (Video/Book Production Pipeline)
- 7-step pipeline: Config → Script → Characters → Storyboard → Dialogues → Production → Results
- Screenwriter chat (Claude AI), Character avatar generation with accuracy loop
- Storyboard editor with expandable/collapsible panels
- Dialogue Editor (Step 4): Visual Book Tab + Audio Preview
- Production pipeline, Post-production, localization, subtitles

### Project-Scoped Avatar System (Mar 28, 2026)
- **Project Avatars**: Each project has its own `project_avatars[]` array (isolated from other projects)
- **Global Library**: `studio_avatars[]` in tenant settings serves as the shared avatar repository
- **New Project Flow**: Projects start with zero avatars. Users can "Criar" (create new) or "Acervo" (import from library)
- **AvatarLibraryModal**: Search/filter global library, select multiple, import to project
- **Backend Endpoints**:
  - `GET /api/studio/projects/{id}/project-avatars` — project-scoped avatars
  - `POST /api/studio/projects/{id}/project-avatars` — add to project + optionally to library
  - `POST /api/studio/projects/{id}/project-avatars/import` — import from library
  - `DELETE /api/studio/projects/{id}/project-avatars/{avatar_id}` — remove from project only
- **Cache Unification**: `data.py` and `studio/` now share the same ProjectCache for consistency

### Infrastructure
- Rate limiting (slowapi), GZip/Observability middleware, Circuit breakers
- React Code Splitting + Lazy Loading, PWA

### Backend: studio.py Split into Modular Package
`/app/backend/routers/studio/` — 11 modules

### Frontend: PipelineView.jsx Split
3095 → 1807 lines. Extracted: ActivePipelineView, CompanyModal, AvatarModal

### Continuity Director Architecture (Storyboard)
1. **Character Identity Cards**: Claude Vision analyzes avatars → structured card
2. **Shot Director**: Claude pre-plans 6 frames/scene with spatial continuity
3. **Identity-First Prompts**: Identity FIRST, scene SECOND, per-character prohibitions

### Unlimited Screenwriter
- Removed 8-scene limit — auto-continuation loop up to 100 scenes
- Rich narrative guidelines: simple stories 5-8 scenes, epic stories 15-30+

## Backlog

### P1
- AI Marketing Studio (Phase 7.1 & 7.2) — campaign generation, enterprise gating
- Visual validation of Continuity Director with real projects

### P2
- Omnichannel Integrations (WhatsApp, SMS, Instagram, Telegram)
- Admin Management System, Stripe Integration

### P3
- Native App packaging (Capacitor iOS/Android)
- Legal & Publication (Terms, Privacy Policy)

## Test Credentials
- Email: test@agentflow.com / Password: password123
