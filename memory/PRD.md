# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform. Users create animated videos from scripts to final production.

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini API (image gen), OpenAI gpt-4o-mini (text), Kling AI v3 (video), ElevenLabs (voice TTS)

## What's Been Implemented

### Audio Overlay — Dubbed Dialogue + Merge (2026-04-13)
- **New endpoint**: `POST /api/studio/projects/{id}/kling-storyboards/generate-dialogues` — LLM generates dialogue_text for all 30 frames
- **New endpoint**: `POST /api/studio/projects/{id}/kling-storyboards/generate-audio` — Generates TTS per frame via ElevenLabs, pads to 6s each, concatenates, merges with Kling video via FFmpeg
- **Voice assignment**: Auto-assigns ElevenLabs voices to characters (Bill→Abraão, Sarah→Sara, Gigi→Isaac, Rachel→Anjo)
- **Result**: 30-frame dubbed audio generated in ~30s, merged with 3-min video

### Kling AI Strategy B — Parallel I2V Production (2026-04-13)
- Replaced sequential video extension (2.5h) with parallel I2V clips + FFmpeg concat (~5 min)
- Each clip uses `image` (start frame) + `image_tail` (end frame) for smooth AI transitions
- Model: `kling-v3/std`, 30 clips × 6s = 180s (3 minutes)

### Frame Dialogue Display + Inline Editing (2026-04-12)
- Backend: `dialogue_text` field in LLM prompt + PATCH endpoint for editing
- Frontend: Dialogue snippets below each frame + editable zoom modal

### Video Engine Selection Fix (2026-04-12)
- Frontend now sends `video_engine` correctly, labels dynamic

### Previously Completed
- 30-frame async storyboard generation with Gemini multimodal
- Cache-busting, write-behind persistence, Kling JWT auth
- LLM switch from Claude to OpenAI gpt-4o-mini

## Pending Tasks
- P1: Add background music overlay (in addition to dialogue)
- P1: Frontend button to trigger dialogue generation + audio overlay from UI
- P1: System of Layers Phase 2 — Custom Video Editor UI
- P2: "Seed Oficial" for new tenants
- P2: Modularize large frontend components

## Key API Endpoints
- `POST /api/studio/start-production` — Produces video (kling parallel I2V or sora)
- `POST /api/studio/projects/{id}/kling-storyboards/generate-dialogues` — Generate dialogue_text for all frames via LLM
- `POST /api/studio/projects/{id}/kling-storyboards/generate-audio` — Generate TTS audio + merge with video
- `PATCH /api/studio/projects/{id}/kling-storyboards/update-frame` — Edit frame text fields
- `POST /api/studio/projects/{id}/auto-assign-voices` — Auto-assign ElevenLabs voices to characters

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project ID: 06c877c953a3
