# AgentZZ - Product Requirements Document

## Original Problem Statement
A comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows users to deploy and configure pre-built AI agents on social media channels. Features a Directed Studio Mode for AI video production pipelines.

## Core Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python) + LiteLLM
- **Database**: Supabase (PostgreSQL) + MongoDB (flexible-schema features)
- **AI Stack**: Direct API keys for ALL providers (no proxy)
  - Claude Sonnet 4.5 (Anthropic) — text generation, chat, analysis
  - Sora 2 (OpenAI) — video generation
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
- Pipeline v3: Screenwriter → Scene Director → Video Generator
- Per-scene retry, edit, visual style selection
- Character avatar persistence
- Chunked prompt generation for large projects

### Direct API Migration (DONE - 2026-03-24)
- **ALL** AI calls migrated from Emergent LLM Proxy to direct API keys
- Created central module `/app/backend/core/llm.py` with:
  - DirectChat (session-based, replaces LlmChat)
  - direct_completion (single-shot)
  - multi_turn_completion (with history)
  - speech_to_text (Whisper)
  - text_to_speech_sync (OpenAI TTS)
  - generate_image_gemini / generate_image_gemini_sync
  - DirectSora2Client (Sora 2 video gen)
- Migrated routers: ai.py, conversations.py, leads.py, campaigns.py, agent_generator.py, telegram.py, whatsapp.py, avatar.py, studio.py
- Migrated pipeline: utils.py, engine.py, media.py, avatar_routes.py, routes.py
- Test results: 94% backend, 100% frontend (iteration_98)

## Pending Issues
- **P0**: Supabase 413 Payload Too Large on final video concatenation (>48MB uploads fail)
- **P1**: FFmpeg disappears on container restarts

## Upcoming Tasks
- **P1**: Implement chunked/resumable upload for large concatenated videos
- **P2**: Phase 8 Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- **P3**: Admin Management System & Stripe payment
- **P4**: Refactor PipelineView.jsx (3000+ lines)

## Credentials
- Test: test@agentflow.com / password123
- API keys in /app/backend/.env (Anthropic, OpenAI, Gemini)
