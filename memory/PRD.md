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
- `/app/backend/routers/studio/` — 11 modules:
  - `_shared.py`, `projects.py`, `storyboard.py`, `dialogues.py`, `smart_edit.py`,
    `continuity.py`, `book.py`, `screenwriter.py`, `production.py`, `narration.py`, `post_production.py`

#### Frontend: PipelineView.jsx Split
- 3095 → 1807 lines. Extracted: `ActivePipelineView.jsx`, `CompanyModal.jsx`, `AvatarModal.jsx`

#### Voice Preview Endpoint
- `POST /api/studio/voice-preview` — ElevenLabs TTS audio sample generation

#### Continuity Director Architecture (Storyboard)
Major upgrade to storyboard generation pipeline:

1. **Character Identity Cards** (`_analyze_avatars_with_vision()` upgraded):
   - Claude Vision analyzes each avatar image → structured Identity Card
   - Includes: species, body_type (BIPEDAL/QUADRUPED), locomotion, anatomy, immutable_traits, prohibitions
   - Stored in project's `production_design.identity_cards`

2. **Shot Director** (new `_generate_shot_briefs()`):
   - Claude pre-plans 6 frames per scene with spatial continuity
   - Each frame has: camera angle, character positioning, actions, expressions, continuity notes, prohibitions
   - Receives context from previous/next scenes for cross-scene continuity

3. **Identity-First Prompts** (new `_build_identity_prompt()`):
   - BLOCK 1: Character Identity (IMMUTABLE — highest weight)
   - BLOCK 2: Scene Instruction (can vary per frame)
   - BLOCK 3: Style & Rules
   - Per-character prohibitions inline (e.g., "NEVER show on four legs")

4. **Increased Parallelism**:
   - Scene semaphore: 2 → 4 concurrent scenes
   - Frame semaphore: 3 → 6 (all frames in parallel per scene)
   - Shot brief semaphore: 8 concurrent Claude calls
   - Total: up to 24 concurrent Gemini calls

## Backlog (Prioritized)

### P1 - High
- Test Continuity Director with real storyboard generation (visual validation)
- Progressive Storyboard Pipeline (keyframe blitz → lazy expansion)

### P2 - Medium
- AI Marketing Studio (Phase 7.1/7.2) — Enterprise plan
- Phase 8: Omnichannel Integrations (WhatsApp, SMS, Instagram, Telegram)
- Admin Management System, Stripe Payment Gateway

### P3 - Low
- Native App packaging (Capacitor iOS/Android)
- Legal & Publication

## Test Credentials
- Email: test@agentflow.com
- Password: password123
