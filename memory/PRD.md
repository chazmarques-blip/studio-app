# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform for deploying AI agents and producing AI-powered video content through a Directed Studio.

## Core Features Implemented

### Directed Studio - Scene Management
- Add/delete/reorder scenes incrementally
- **Drag-and-Drop scene reordering** (@dnd-kit/sortable) — DONE 2026-03-28
- Storyboard Sync — auto-creates missing panels
- Character selection per scene

### Sound Design Agent (Agente de Sonoplastia IA) — DONE 2026-03-29
- **Dual mode**: "Catálogo" (24 stock ElevenLabs voices) + "Sonoplastia IA" (custom AI-designed voices)
- **Claude analysis**: Deeply analyzes each character's species, personality, age, role → writes optimal voice description
- **ElevenLabs Voice Design**: Generates 3 unique voice previews per character via `create_previews` API
- **Audio preview**: Users can listen to each option and select the best one
- **Permanent save**: Selected voice preview is saved as permanent ElevenLabs voice via `text_to_voice.create`
- **Per-character controls**: Individual "Design" button per character + bulk "Sonoplastia IA" button
- Endpoints: `POST /design-character-voice`, `POST /design-all-voices`, `POST /select-designed-voice`

### AI Voice Assignment (Catalog Mode) — DONE 2026-03-29
- Claude assigns best stock voice per character from 24 ElevenLabs voices
- Manual override via dropdown
- Endpoints: `POST /auto-assign-voices`, `GET/POST /voice-map`

### Continuity Director V2 (Claude Vision) — DONE 2026-03-28
- Strict anatomical/visual consistency checks via claude-sonnet-4-5-20250929

### Other Features
- Agent Management, Omnichannel (mocked), CRM, Multi-language, Dark luxury theme
- Google Integration, recharts Dashboard

## Key API Endpoints
- `POST /api/studio/projects/{id}/design-character-voice` — Sound Agent single char
- `POST /api/studio/projects/{id}/design-all-voices` — Sound Agent all chars
- `POST /api/studio/projects/{id}/select-designed-voice` — Save designed voice
- `POST /api/studio/projects/{id}/auto-assign-voices` — Catalog voice assignment
- `GET /api/studio/projects/{id}/voice-map` — Get voice assignments
- `POST /api/studio/projects/{id}/voice-map` — Update voice assignments

## Backlog
- P1: AI Marketing Studio (Phase 7.1 & 7.2)
- P2: Omnichannel Integrations
- P2: Admin System & Stripe
- P3: Native App (Capacitor)

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn-ui, @dnd-kit, Framer Motion, recharts
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Anthropic Claude, ElevenLabs (TTS + Voice Design), OpenAI Whisper, Google APIs, Gemini

## Credentials
- Email: test@agentflow.com / Password: password123
- Test project: d27afb0e79ff (ADÃO E EVA - BIBLIZOO 2, 31 scenes, 17 characters)
