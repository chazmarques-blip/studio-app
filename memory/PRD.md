# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform for deploying AI agents and producing AI-powered video content through a Directed Studio.

## Core Features Implemented

### Sound Design Agent (Agente de Sonoplastia IA) — DONE 2026-03-29
- Claude analyzes each character's species, personality, age, role → writes optimal voice description
- ElevenLabs Voice Design API generates 3 unique voice previews per character
- User listens and selects the best voice; saved permanently via `text_to_voice.create`
- Dual mode: "Catálogo" (24 stock voices) + "Sonoplastia IA" (custom designed)
- Per-character "Design" button + bulk "Sonoplastia IA" button

### AI Voice Assignment System — DONE 2026-03-29
- Claude assigns best stock voice per character from ElevenLabs catalog
- Voice map persisted per project; used by narration generation and dialogue editor
- Replaced hardcoded biblical name mapping with intelligent AI analysis
- DialogueEditor now uses voice_map instead of hardcoded fallback

### Dialogue Editor Improvements — DONE 2026-03-29
- Fixed dubbed mode showing narration text instead of character dialogues
- Added alert "31 cenas sem diálogos dublados" with "Gerar Diálogos" CTA
- getTextField() no longer falls back to narration text in dubbed mode
- Backend GET /dialogues returns scenes_needing_dubbed count and has_voice_map flag

### Directed Studio - Scene Management
- Drag-and-Drop reordering (@dnd-kit/sortable) — DONE 2026-03-28
- Incremental add/delete/reorder scenes
- Storyboard Sync

### Continuity Director V2 (Claude Vision) — DONE 2026-03-28

## Key API Endpoints
- `POST /api/studio/projects/{id}/design-character-voice` — Sound Agent single
- `POST /api/studio/projects/{id}/design-all-voices` — Sound Agent all
- `POST /api/studio/projects/{id}/select-designed-voice` — Save designed voice
- `POST /api/studio/projects/{id}/auto-assign-voices` — Catalog assignment
- `GET/POST /api/studio/projects/{id}/voice-map` — Voice assignments
- `GET /api/studio/projects/{id}/dialogues` — Dialogue data with voice_map
- `POST /api/studio/projects/{id}/dialogues/generate` — AI dialogue generation

## Backlog
- P1: AI Marketing Studio (Phase 7.1 & 7.2)
- P2: Omnichannel Integrations
- P2: Admin System & Stripe
- P3: Native App (Capacitor)

## Credentials
- Email: test@agentflow.com / Password: password123
- Test project: d27afb0e79ff (ADÃO E EVA - BIBLIZOO 2, 31 scenes, 17 characters)
