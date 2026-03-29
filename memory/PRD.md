# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is a standalone AI-powered video studio platform focused on end-to-end video production with AI.

## Core Features Implemented

### Pipeline Reordering — DONE 2026-03-29
- New order: Roteiro → Personagens → **Diálogos** → **Storyboard** → Produção → Resultado
- Dialogues/narration generated BEFORE storyboard for richer visual context
- DialogueEditor navigation updated: "Voltar aos Personagens" / "Continuar para Storyboard"

### Enriched Storyboard Prompts — DONE 2026-03-29
- Dialogue/emotional context block added to storyboard generation prompt
- Character identity section enhanced with NON-NEGOTIABLE markers, MANDATORY/FORBIDDEN traits
- Redundant consistency enforcement (body type + locomotion reminders per character)
- Characters' expressions and gestures now reflect their dialogue

### Voice Remix — DONE 2026-03-29
- Endpoint: `POST /api/studio/projects/{id}/remix-voice`
- Adjusts existing voice characteristics (pitch, accent, tone) via ElevenLabs remix API
- Parameters: voice_description, prompt_strength (0-1)
- UI: Remix button per character → form with description input + intensity slider → 3 preview options

### Sound Design Agent (Sonoplastia IA) — DONE 2026-03-29
- Claude analyzes characters → ElevenLabs Voice Design generates 3 custom voice options
- Dual mode: Catálogo (stock) + Sonoplastia IA (custom designed)

### AI Voice Assignment — DONE 2026-03-29
- Replaced hardcoded biblical name mapping with Claude-powered intelligent assignment
- DialogueEditor uses voice_map; alerts when dubbed_text is missing

### Scene Management — DONE 2026-03-28
- Drag-and-Drop (@dnd-kit), Incremental add/delete, Storyboard Sync, Continuity Director V2

## Key API Endpoints
- `POST /api/studio/projects/{id}/remix-voice` — Voice Remix
- `POST /api/studio/projects/{id}/design-character-voice` — Sound Agent single
- `POST /api/studio/projects/{id}/design-all-voices` — Sound Agent all
- `POST /api/studio/projects/{id}/select-designed-voice` — Save designed voice
- `POST /api/studio/projects/{id}/auto-assign-voices` — Catalog assignment
- `GET/POST /api/studio/projects/{id}/voice-map` — Voice assignments
- `GET /api/studio/projects/{id}/dialogues` — Dialogue data with voice_map

## Backlog
- P1: AI Marketing Studio (Phase 7.1 & 7.2)
- P2: Omnichannel Integrations
- P2: Admin System & Stripe
- P3: Native App (Capacitor)

## Credentials
- Email: test@agentflow.com / Password: password123
- Test project: d27afb0e79ff (ADÃO E EVA - BIBLIZOO 2, 31 scenes, 17 characters)
