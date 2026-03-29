# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform for deploying AI agents and producing AI-powered video content through a Directed Studio. Target: small and medium business owners.

## Core Features Implemented

### Directed Studio - Scene Management
- Add scenes at any position (manual + AI-assisted with Claude)
- Delete scenes (removes storyboard/audio, renumbers)
- **Drag-and-Drop scene reordering** using @dnd-kit/sortable (replaced Up/Down buttons) — DONE 2026-03-28
- **Storyboard Sync** - auto-creates placeholder panels for new scenes
- Character selection per scene via toggle chips

### AI Voice Assignment System — DONE 2026-03-29
- **Intelligent voice auto-assignment**: Claude analyzes each character's name, description, role, species and assigns the most suitable ElevenLabs voice from 24 available voices
- **Manual override**: Users can change any character's voice via dropdown
- **Voice Map persistence**: Saved per project in Supabase
- **Dubbed mode integration**: `_run_narration_background` uses the AI-assigned voice_map instead of hardcoded biblical name mappings
- Endpoints: `POST /auto-assign-voices`, `GET /voice-map`, `POST /voice-map`

### Continuity Director V2 (Claude Vision) — DONE 2026-03-28
- Rewritten for `claude-sonnet-4-5-20250929` via Emergent LLM Key
- Preventive Gate + Post-hoc Analysis + Auto-correction
- Optimized to only send relevant character avatars per scene

### Error Handling
- `getErrorMsg()` utility prevents Pydantic validation arrays from crashing React
- `EditAvatarRequest.base_url` field_validator coerces None to ""

### Other Features
- Agent Management, Omnichannel (mocked), CRM, Multi-language, Dark luxury theme
- Google Integration in Agent Config (Phase 6 Complete)
- recharts Dashboard

## Key API Endpoints
- `POST /api/studio/projects/{id}/auto-assign-voices` — AI voice assignment
- `GET /api/studio/projects/{id}/voice-map` — Get voice assignments
- `POST /api/studio/projects/{id}/voice-map` — Update voice assignments
- `POST /api/studio/projects/{id}/add-scene`
- `POST /api/studio/projects/{id}/delete-scene`
- `POST /api/studio/projects/{id}/reorder-scenes`
- `POST /api/studio/projects/{id}/storyboard/sync-panels`
- `POST /api/studio/projects/{id}/continuity/analyze`
- `GET /api/studio/projects/{id}/continuity/status`

## Backlog
- P1: AI Marketing Studio (Phase 7.1 & 7.2)
- P2: Omnichannel Integrations (WhatsApp, SMS, Instagram, Telegram)
- P2: Admin System & Stripe
- P3: Native App (Capacitor)

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion, recharts, @dnd-kit
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Anthropic Claude, OpenAI Whisper, Google APIs, ElevenLabs, Gemini

## Credentials
- Email: test@agentflow.com / Password: password123
- Test project: d27afb0e79ff (ADÃO E EVA - BIBLIZOO 2, 31 scenes, 17 characters)
