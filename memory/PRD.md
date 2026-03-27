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

### Infrastructure
- Rate limiting (slowapi), GZip/Observability middleware, Circuit breakers
- React Code Splitting + Lazy Loading, PWA

### Recent Changes (Feb 27, 2026)

#### Backend: studio.py Split into Modular Package
`/app/backend/routers/studio/` — 11 modules

#### Frontend: PipelineView.jsx Split
3095 → 1807 lines. Extracted: ActivePipelineView, CompanyModal, AvatarModal

#### Voice Preview Endpoint
`POST /api/studio/voice-preview` — ElevenLabs TTS audio sample generation

#### Continuity Director Architecture (Storyboard)
1. **Character Identity Cards**: Claude Vision analyzes avatars → structured card with body_type, immutable_traits, prohibitions
2. **Shot Director**: Claude pre-plans 6 frames/scene with spatial continuity
3. **Identity-First Prompts**: Identity FIRST (highest weight), scene SECOND, per-character prohibitions inline
4. **Parallelism**: 4 scenes × 6 frames = 24 concurrent (was 6)

#### Unlimited Screenwriter (Script Generation)
- Removed 8-scene limit — story generates as many scenes as needed (10 per batch, auto-continuation loop up to 100)
- Removed character limit — more characters = richer story
- Added richness guidelines: simple stories 5-8 scenes, rich/epic stories 15-30+
- Aggressive auto-continuation: loop generates ALL scenes until complete
- Instruction: "Every key narrative moment deserves its OWN scene — never compress"

## Backlog

### P1
- Visual validation of Continuity Director + Unlimited Screenwriter with real project
- Progressive Storyboard Pipeline (keyframe blitz → lazy expansion)

### P2
- AI Marketing Studio (Phase 7), Omnichannel Integrations, Admin System, Stripe

### P3
- Native App packaging (Capacitor), Legal & Publication

## Test Credentials
- Email: test@agentflow.com / Password: password123
