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
- **Pipeline v5 (Pre-Production Intelligence)**:
  - NEW: Pre-production phase with Claude Vision avatar analysis
  - NEW: Production Design Document (ONE Claude call for style, locations, continuity, music, voice)
  - NEW: Composite avatar images for multi-character scenes
  - PHASE A: Scene Directors use Production Design Bible for canonical character descriptions
  - PHASE B: Sora 2 queue with 5 concurrent slots + composite avatar reference
  - FFmpeg concat + compression
- Per-scene retry, edit, visual style selection
- Character avatar persistence with auto-resize to video dimensions
- Screenwriter enforces character type (animal/human) from briefing

### Previous Pipeline Versions
- **v4**: Decoupled parallel directors + queued Sora renders
- **v3**: Per-scene parallel teams
- **v2**: Batched pipeline
- **v1**: Sequential pipeline

## Pipeline v5 Architecture
```
PRE-PRODUCTION (2 Claude calls):
├─ Avatar Analyzer (Claude Vision) — ONE call, all avatars → canonical descriptions
└─ Production Designer (Claude) — ONE call → style_anchors, character_bible, location_bible, 
                                              scene_directions, color_palette, music_plan, voice_plan

PHASE A (Directors — N parallel calls, token-efficient):
├─ Scene Director 1 (uses PD bible) ─┐
├─ Scene Director 2 (uses PD bible) ─┤  ALL PARALLEL → N Sora prompts
└─ Scene Director N (uses PD bible) ─┘

PHASE B (Sora 2 — 5 concurrent slots):
├─ Sora Queue → [1..5] → [6..10] → [11..15]
└─ Each scene gets COMPOSITE avatar image (collage of all characters)

POST-PRODUCTION:
└─ FFmpeg concat + compression → Final upload
```

## Token Optimization (v5 vs v4)
- v4: ~30,000 input tokens (N×2000 per director + music call)
- v5: ~18,000 input tokens (2×3000 pre-prod + N×800 per director) — ~40% reduction
- Music planning absorbed into Production Design (saves 1 Claude call)

## Pending Issues
- **P1**: FFmpeg disappears on container restarts (auto-install workaround in place)
- **P1**: Supabase 413 Payload Too Large for large final videos (compression workaround)

## Upcoming Tasks
- **P0**: Run a full production test with the new Pipeline v5 to verify continuity improvements
- **P1**: Add Quality Supervisor agent (optional review of all prompts before Sora 2)
- **P2**: Phase 8 Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- **P3**: Admin Management System & Stripe payment
- **P4**: Refactor PipelineView.jsx (3000+ lines)

## Key Files
- `/app/backend/routers/studio.py` — Core pipeline logic, pre-production, scene direction
- `/app/backend/core/llm.py` — All AI client integrations
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI
- `/app/frontend/src/components/StudioProductionBanner.jsx` — Production progress banner
- `/app/frontend/src/components/PipelineView.jsx` — Pipeline visualization

## Credentials
- Test: test@agentflow.com / password123
- API keys in /app/backend/.env (Anthropic, OpenAI, Gemini)
