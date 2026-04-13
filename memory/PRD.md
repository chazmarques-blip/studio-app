# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform. Users create animated videos from scripts to final production.

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini API (image gen), OpenAI gpt-4o-mini (text), Kling AI (video), ElevenLabs (voice)

## What's Been Implemented

### Kling AI Strategy B — Parallel I2V Production (2026-04-13)
- **Replaced** sequential video extension (2.5h) with parallel I2V clips + FFmpeg concat (~5 min)
- Each clip uses `image` (start frame) + `image_tail` (end frame) for smooth AI-interpolated transitions
- Model: `kling-v3/std` — supports image_tail in standard mode (cheapest)
- 30 clips × 6s = 180s (3 minutes), generated in ~2 min parallel
- FFmpeg concatenation with re-encoding for compatibility
- Progress callbacks update UI in real-time during generation

### Frame Dialogue Display + Inline Editing (2026-04-12)
- Backend: `dialogue_text` field in LLM prompt + PATCH endpoint for editing
- Frontend: Dialogue snippets below each frame + editable zoom modal (image_prompt, kling_prompt, dialogue_text)

### Video Engine Selection Fix (2026-04-12)
- Frontend now sends `video_engine` in production request
- Labels dynamically show "Kling AI" or "Sora 2"
- Old outputs cleared on re-production

### Previously Completed
- 30-frame async storyboard generation with Gemini multimodal
- Cache-busting, write-behind persistence with flush_now
- Kling JWT authentication, inline frame regeneration
- LLM switch from Claude to OpenAI gpt-4o-mini

## Pending Tasks
- P1: Audio overlay — sync dialogue TTS + background music with video clips
- P1: System of Layers Phase 2 — Custom Video Editor UI
- P2: "Seed Oficial" for new tenants
- P2: Modularize large frontend components
- P2: Project Deletion UI verification

## API Endpoints
- `POST /api/studio/start-production` — Starts production (accepts video_engine: "kling" or "sora")
- `PATCH /api/studio/projects/{id}/kling-storyboards/update-frame` — Edit frame fields
- `GET /api/studio/projects/{id}/kling-storyboards` — Get storyboard with frames
- `POST /api/studio/projects/{id}/kling-storyboards/generate` — Generate 30 frames async

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project ID: 06c877c953a3
