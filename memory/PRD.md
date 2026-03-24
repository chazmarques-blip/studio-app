# AgentZZ - Product Requirements Document

## Original Problem Statement
A comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users to deploy and configure pre-built AI agents on social media channels. Features a Directed Studio Mode for AI video production pipelines.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB (flexible-schema features)
- **AI Stack**: Direct API keys for ALL providers (no proxy)
  - Claude Sonnet 4.5 (Anthropic) — text generation, chat, analysis, **Vision (avatar analysis)**
  - Sora 2 (OpenAI) — video generation (with 1280x720 image resize)
  - Whisper (OpenAI) — speech-to-text
  - TTS (OpenAI) — text-to-speech
  - Gemini 2.5 Flash (Google) — image generation, agent generation, vision
- **Central LLM Module**: `/app/backend/core/llm.py` — all AI calls routed through here

## What's Been Implemented

### Phase 1-5: Core Platform (DONE)
- Auth, Dashboard, Agent Management, CRM, Conversations, Lead Scoring
- Agent Marketplace with plan gating
- Multi-language UI (EN, PT, ES)

### Phase 6: Google Integration (DONE)
- Google Calendar/Sheets integration in Agent Config

### Directed Studio Mode — Pipeline v5 (DONE - 2026-03-24)
- **Pre-Production Intelligence** (2 Claude calls total):
  - Avatar Analyzer: Claude Vision analyzes ALL character avatars in ONE call → canonical descriptions
  - Production Designer: ONE call → style_anchors, character_bible, location_bible, scene_directions, color_palette, music_plan, voice_plan
  - Composite avatar images for multi-character scenes (Pillow collage)
- **Preview Board** (NEW - 2026-03-24):
  - `POST /api/studio/projects/{id}/generate-preview` — runs pre-production in background
  - `GET /api/studio/projects/{id}/preview` — returns production design document
  - Visual frontend component showing: style anchors, color palette, character bible with avatar comparison, locations, scene flow timeline, music plan, voice direction
  - "Approve & Produce" or "Regenerate Preview" options
  - Pipeline automatically skips pre-production if preview was already approved
- **Scene Directors**: Use Production Design Bible for canonical character descriptions (40% token reduction)
- **Sora 2**: Composite avatar reference images, 5 concurrent slots, auto-resize
- **Screenwriter**: Enforces character type (animal/human) from briefing
- **Post-Production**: FFmpeg concat + compression

### Pipeline v5 Architecture
```
USER ACTION: "Preview Design" button
├─ POST /generate-preview (background)
│  ├─ Avatar Analyzer (Claude Vision) — 1 call
│  └─ Production Designer (Claude) — 1 call
└─ GET /preview → PreviewBoard component

USER ACTION: "Approve & Produce" button  
├─ Pipeline detects existing production_design → SKIPS pre-production
├─ PHASE A: N Scene Directors (parallel, PD-guided, token-efficient)
├─ PHASE B: Sora 2 queue (5 concurrent)
└─ POST-PRODUCTION: FFmpeg concat + compress + upload
```

## Pending Issues
- **P1**: FFmpeg disappears on container restarts (auto-install workaround in place)
- **P1**: Supabase 413 Payload Too Large for large final videos (compression workaround)

## Upcoming Tasks
- **P0**: Run a full production test with Pipeline v5 + Preview Board to verify continuity improvements
- **P1**: Add Quality Supervisor agent (optional review of all prompts before Sora 2)
- **P2**: Phase 8 Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- **P3**: Admin Management System & Stripe payment
- **P4**: Refactor PipelineView.jsx (3000+ lines)

## Key Files
- `/app/backend/routers/studio.py` — Core pipeline logic, pre-production, preview endpoints, scene direction
- `/app/backend/core/llm.py` — All AI client integrations
- `/app/frontend/src/components/PreviewBoard.jsx` — Production Design visual review component
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI with Preview Board integration
- `/app/frontend/src/components/StudioProductionBanner.jsx` — Production progress banner

## Credentials
- Test: test@agentflow.com / password123
- API keys in /app/backend/.env (Anthropic, OpenAI, Gemini)
