# AgentZZ - Product Requirements Document

## Original Problem Statement
A comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users to deploy and configure pre-built AI agents on social media channels. Features a Directed Studio Mode for AI video production pipelines.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB (flexible-schema features)
- **AI Stack**: Direct API keys for ALL providers (no proxy)
  - Claude Sonnet 4.5 (Anthropic) — text generation, chat, analysis
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

### Directed Studio Mode (DONE)
- **Pipeline v4 (Decoupled)**: 
  - PHASE A: ALL Scene Directors run in parallel (~16s for 15 scenes)
  - PHASE B: Sora 2 queue with 5 concurrent slots
  - FFmpeg concat + compression
- Per-scene retry, edit, visual style selection
- Character avatar persistence with auto-resize to video dimensions
- Chunked prompt generation for large projects

### Direct API Migration (DONE - 2026-03-24)
- ALL AI calls migrated from Emergent LLM Proxy to direct API keys
- Created central module `/app/backend/core/llm.py`
- Migrated ALL routers + ALL pipeline modules

### Sora 2 Client Fix (DONE - 2026-03-24)
- Fixed `reference_image` → `input_reference` (multipart)
- Fixed status polling: `succeeded` → `completed`
- Fixed download: `/videos/{id}/content` with streaming + retry
- Added auto-resize of reference images to match video dimensions
- Verified: 15/15 scenes completed, 0 errors, 14.1 min total

## Production Results (2026-03-24)
- Project "Abraão e Isaac" (15 scenes): 15/15 OK, 0 errors
- PHASE A: 16.5s for 15 directors
- PHASE B: ~11min for 15 Sora 2 renders
- Concat: 123MB → 15MB compressed
- Total: 14.1 minutes

## Pending Issues
- **P1**: FFmpeg disappears on container restarts (auto-install workaround in place)

## Upcoming Tasks
- **P1**: Upgrade AI agent prompts (Robert McKee narrative, Roger Deakins cinematography)
- **P1**: Add Quality Supervisor agent (review prompts before Sora 2)
- **P2**: Phase 8 Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- **P3**: Admin Management System & Stripe payment
- **P4**: Refactor PipelineView.jsx (3000+ lines)

## Credentials
- Test: test@agentflow.com / password123
- API keys in /app/backend/.env (Anthropic, OpenAI, Gemini)
