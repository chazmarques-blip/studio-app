# AgentZZ — Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy AI agents on social channels (WhatsApp, Instagram, Facebook, Telegram, SMS) and produce creative content via a Directed Studio Mode.

## Architecture
- **Frontend:** React + Tailwind CSS + shadcn/ui + Framer Motion + recharts
- **Backend:** FastAPI (Python) + Supabase (PostgreSQL) + MongoDB
- **3rd Party:** Anthropic Claude 3.5 Sonnet, OpenAI Whisper, Gemini (Image Gen), ElevenLabs (TTS), Google APIs
- **PWA:** Service Worker + Manifest configured

## What's Been Implemented

### Core Platform
- Authentication (Supabase Auth)
- Multi-language UI (EN, PT, ES)
- Dark luxury theme (gold/black/white)
- Dashboard with recharts analytics
- Agent Marketplace with plan-gating
- Agent Configuration with Google Calendar/Sheets integration

### Directed Studio (Video/Book Production Pipeline)
- 7-step pipeline: Config → Script → Characters → Storyboard → Dialogues → Production → Results
- Screenwriter chat (Claude AI)
- Character avatar generation with AI accuracy loop
- Storyboard editor with expandable/collapsible panels
- **Dialogue Editor (Step 4):** Visual Book Tab for text positioning + Audio Preview button
- Production pipeline with multi-scene generation
- Post-production, localization, subtitles
- Final preview with publish flow

### Infrastructure (Completed Audit)
- Rate limiting (slowapi)
- GZip/Observability middleware
- Circuit breakers for AI providers
- Idempotency layer
- React Code Splitting + Lazy Loading
- PWA (manifest + service worker)

### Recent Refactoring (Feb 2026)
- **Backend:** `studio.py` (5514 lines) → split into modular package `/app/backend/routers/studio/` with 11 modules:
  - `_shared.py`, `projects.py`, `storyboard.py`, `dialogues.py`, `smart_edit.py`, `continuity.py`, `book.py`, `screenwriter.py`, `production.py`, `narration.py`, `post_production.py`
- **Frontend:** `PipelineView.jsx` (3095 lines → 1807 lines) by extracting:
  - `ActivePipelineView.jsx`, `CompanyModal.jsx`, `AvatarModal.jsx` into `/pipeline/`
- **New Endpoint:** `POST /api/studio/voice-preview` for TTS audio sample generation (ElevenLabs)

## Backlog (Prioritized)

### P1 - High
- AI Marketing Studio (Phase 7.1 & 7.2) - Enterprise plan exclusive
- Complete DialogueEditor visual Book Tab testing

### P2 - Medium  
- Phase 8: Omnichannel Integrations (WhatsApp, SMS, Instagram, Telegram)
- Admin Management System
- Stripe Payment Gateway Integration

### P3 - Low
- Native App packaging (Capacitor iOS/Android)
- Legal & Publication (Terms of Use, Privacy Policy)
- Scalability hardening

## Known Issues
- `react-scripts` vs `@craco/craco` mismatch in package.json scripts (minor, bypassed)
- Omnichannel integrations are mocked
- AI Insights dashboard widget is static placeholder

## Test Credentials
- Email: test@agentflow.com
- Password: password123
