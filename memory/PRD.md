# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform for deploying AI agents and producing AI-powered video content through a Directed Studio.

## Core Features Implemented

### Directed Studio - Scene Management
- Add scenes at any position (manual + AI-assisted with Claude)
- Delete scenes (removes storyboard/audio, renumbers)
- Reorder scenes (up/down buttons)
- **Storyboard Sync** - auto-creates placeholder panels for new scenes, generates storyboard frames in background
- `POST /api/studio/projects/{id}/storyboard/sync-panels` - creates & generates missing panels
- `regenerate-panel` auto-creates panel if scene exists but panel doesn't
- Frontend alert banner: "X cena(s) sem storyboard" with "Gerar Faltantes" button
- Character selection per scene via toggle chips

### Error Handling
- `getErrorMsg()` utility prevents Pydantic validation arrays from crashing React
- `EditAvatarRequest.base_url` field_validator coerces None→""

### Other Features
- Agent Management, Omnichannel (mocked), CRM, Multi-language, Dark luxury theme

## Key Endpoints
- `POST /api/studio/projects/{id}/add-scene`
- `POST /api/studio/projects/{id}/delete-scene`
- `POST /api/studio/projects/{id}/reorder-scenes`
- `POST /api/studio/projects/{id}/generate-scene-ai`
- `POST /api/studio/projects/{id}/storyboard/sync-panels` (NEW)

## Backlog
- P1: Drag-and-drop scene reordering (user requested)
- P1: AI Marketing Studio (Phase 7.1 & 7.2)
- P2: Omnichannel Integrations
- P2: Admin System & Stripe
- P3: Native App (Capacitor)

## Credentials
- Email: test@agentflow.com / Password: password123
