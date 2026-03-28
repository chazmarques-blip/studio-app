# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform for deploying AI agents and producing AI-powered video content through a Directed Studio. The platform targets small and medium business owners who need to easily deploy and configure pre-built AI agents on social media channels.

## Core Features Implemented

### Directed Studio - Scene Management
- Add scenes at any position (manual + AI-assisted with Claude)
- Delete scenes (removes storyboard/audio, renumbers)
- **Drag-and-Drop scene reordering** using @dnd-kit/sortable (replaced old Up/Down buttons) - DONE 2026-03-28
- **Storyboard Sync** - auto-creates placeholder panels for new scenes, generates storyboard frames in background
- `POST /api/studio/projects/{id}/storyboard/sync-panels` - creates & generates missing panels
- `regenerate-panel` auto-creates panel if scene exists but panel doesn't
- Frontend alert banner: "X cena(s) sem storyboard" with "Gerar Faltantes" button
- Character selection per scene via toggle chips

### Continuity Director V2 (Claude Vision) - DONE 2026-03-28
- Completely rewritten to use `claude-sonnet-4-5-20250929` via Emergent LLM Key
- **Preventive Gate**: validate_frame() runs after every image generation, before saving
- **Post-hoc Analysis**: Full audit of all frames across all scenes
- **Auto-correction**: Fixes detected issues via inpainting
- Optimized to only send relevant character avatars per scene (prevents payload overflow)
- Analysis complete: 87 issues found (65 critical, 6 high, 13 medium, 3 low)

### Error Handling
- `getErrorMsg()` utility prevents Pydantic validation arrays from crashing React
- `EditAvatarRequest.base_url` field_validator coerces None to ""

### Other Features
- Agent Management, Omnichannel (mocked), CRM, Multi-language, Dark luxury theme
- Google Integration in Agent Config (Phase 6 Complete)
- recharts Dashboard

## Key Endpoints
- `POST /api/studio/projects/{id}/add-scene`
- `POST /api/studio/projects/{id}/delete-scene`
- `POST /api/studio/projects/{id}/reorder-scenes`
- `POST /api/studio/projects/{id}/generate-scene-ai`
- `POST /api/studio/projects/{id}/storyboard/sync-panels`
- `POST /api/studio/projects/{id}/continuity/analyze`
- `GET /api/studio/projects/{id}/continuity/status`
- `POST /api/studio/projects/{id}/continuity/auto-correct`

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
- Test project: d27afb0e79ff (ADÃO E EVA - BIBLIZOO 2, 31 scenes)
