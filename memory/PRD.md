# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform that allows users to deploy AI agents and produce AI-powered video content through a Directed Studio.

## Core Features Implemented

### Directed Studio
- Full video/storybook production pipeline (6 steps: Roteiro → Personagens → Storyboard → Diálogos → Produção → Resultado)
- **Scene Management (NEW - March 28, 2026)**:
  - Add scenes at any position (beginning, between, end)
  - Manual creation or AI-assisted generation (Claude generates scene with context from neighboring scenes)
  - Delete scenes with automatic removal of associated storyboard/audio
  - Reorder scenes with up/down buttons
  - Auto-renumbering of all scenes and storyboard panels
  - Auto-storyboard generation for new scenes when storyboard already exists
  - Character selection per scene via toggle chips
- Character/Avatar System with project isolation, context-aware editing, 360° views
- AI screenwriting, storyboarding, voice narration, production

### Other Features
- Agent Management with marketplace and Google Calendar/Sheets integration
- Omnichannel inbox structure (mocked)
- CRM with Kanban board
- Multi-language (EN/PT/ES)
- Dark luxury theme

## Recent Changes (March 28, 2026)
1. **Scene Management** - Add/Delete/Reorder/AI-Generate scenes in Roteiro (iteration_125 - 92% backend, 100% frontend)
2. **Scene Character Editing** - Toggle chips per scene (iteration_124 - 100%)
3. **Toast Error Crash Fix** - getErrorMsg utility across 20+ files
4. **Character Edit Fix** - base_url null→"" in AvatarModal

## Key Endpoints
- `POST /api/studio/projects/{id}/add-scene` - Add scene at position
- `POST /api/studio/projects/{id}/delete-scene` - Delete scene + storyboard
- `POST /api/studio/projects/{id}/reorder-scenes` - Reorder by order array
- `POST /api/studio/projects/{id}/generate-scene-ai` - AI scene generation

## Backlog
- P1: AI Marketing Studio (Phase 7.1 & 7.2)
- P2: Omnichannel Integrations (Phase 8)
- P2: Admin System & Stripe
- P3: Native App (Capacitor)

## Tech Stack
- Frontend: React, Tailwind, shadcn-ui, Framer Motion 11.18.2, recharts
- Backend: FastAPI (Python)
- DB: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Claude 3.5, OpenAI Whisper, Gemini, ElevenLabs, Google APIs

## Credentials
- Email: test@agentflow.com / Password: password123
