# AgentZZ - Product Requirements Document

## Original Problem Statement
A comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users to deploy and configure pre-built AI agents on social media channels. Features a Directed Studio Mode for AI video production pipelines.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB (flexible-schema features)
- **AI Stack**: Direct API keys for ALL providers (no proxy)
  - Claude Sonnet 4.5 (Anthropic) — text, chat, Vision (avatar analysis)
  - Sora 2 (OpenAI) — video generation
  - Whisper (OpenAI) — STT | TTS (OpenAI) — text-to-speech
  - Gemini 2.5 Flash (Google) — image generation, vision
- **Central LLM Module**: `/app/backend/core/llm.py`

## Directed Studio Mode — Pipeline v5 (PRODUCTION VERIFIED - 2026-03-24)

### Architecture
```
PREVIEW BOARD (user approval step):
├─ POST /generate-preview → background task
│  ├─ Avatar Analyzer (Claude Vision) — 1 call, ALL avatars
│  └─ Production Designer (Claude) — 1 call → full design document
└─ GET /preview → PreviewBoard component (visual review)

PRODUCTION (after user approves):
├─ Pipeline detects existing production_design → SKIPS pre-production
├─ PHASE A: N Scene Directors (parallel, PD-guided, ~12s total)
├─ PHASE B: Sora 2 queue (5 concurrent, composite avatars)
└─ POST-PRODUCTION: FFmpeg concat + upload
```

### Production Run Results (2026-03-24)
- **Project**: "Abraão e Isaac - Preview v5 Test" (3 scenes, camel characters)
- **Preview**: Generated in 48s (Claude Vision + Production Design)
- **Direction**: 3 scenes directed in 12.1s (parallel, PD-guided)
- **Rendering**: 3 Sora 2 videos in 4.0min (all with composite avatars)
- **Total**: 4.2 minutes, 24MB final video, 0 errors
- **Video URL**: https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/studio/864f3e7e0464_final.mp4

### Key Features
- Preview Board: visual review of character bible, locations, style, music, scene flow
- Claude Vision avatar analysis → canonical character descriptions
- Composite avatar images for multi-character scenes
- Screenwriter enforces character type (animal/human)
- Pipeline skips pre-production when preview already approved
- PUT /character-avatars endpoint for avatar assignment

## Pending Issues
- **P1**: FFmpeg disappears on container restarts
- **P1**: Supabase 413 for very large videos (compression workaround active)

## Upcoming Tasks
- **P0**: Run full 15-scene production with Pipeline v5
- **P1**: Quality Supervisor agent (optional prompt review before Sora 2)
- **P2**: Phase 8 Omnichannel Integrations
- **P3**: Admin Dashboard & Stripe
- **P4**: Refactor PipelineView.jsx

## Key Files
- `/app/backend/routers/studio.py` — Pipeline v5, preview endpoints, scene direction
- `/app/backend/core/llm.py` — AI clients (Claude, Sora 2, Gemini, TTS)
- `/app/frontend/src/components/PreviewBoard.jsx` — Production Design visual review
- `/app/frontend/src/components/DirectedStudio.jsx` — Studio UI + Preview integration
- `/app/frontend/src/components/StudioProductionBanner.jsx` — Progress banner

## Credentials
- Test: test@agentflow.com / password123
- API keys in /app/backend/.env (Anthropic, OpenAI, Gemini)
