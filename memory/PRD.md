# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images), OpenAI gpt-4o-mini (text), Kling AI v3 (video), ElevenLabs (voice TTS)

## Production Pipeline (4 Phases)

### PHASE A: Scene Directors (existing)
### PHASE B: Video Generation — Dual Mode (existing)
- **Modo Rápido**: 30 parallel I2V clips + xfade crossfade (~5 min)
- **Modo Cinema**: Sequential clips using last real frame extraction (~20 min)

### PHASE C: Audio Production (new)
- Dialogue alignment, Emotion TTS, Audio padding + concatenation

### PHASE D: Final Mix + Multi-format Export (new)
- YouTube 16:9, TikTok 9:16, Instagram 1:1

## Recent Changes

### Pipeline Tracker Dynamic Progress (2026-04-13)
- Backend: Added `pipeline_phase` field updated at each stage (library_sync → researcher_screenwriter → done)
- Frontend: `PipelineVisualTrackerInline` now reads `pipeline_phase` + `character_library` + `agents_output` for real-time progress
- Frontend: `pollChatResult` now updates `currentProjectData` during polling so tracker refreshes every 3s
- Backend: `/status` endpoint now returns `character_library`, `director_review`, `director_progress`, `pipeline_phase`, `voice_map`, `dialogues`

### Dual Production Mode + Full Audio Pipeline (2026-04-13)
- Both fast/cinema modes implemented
- Frontend mode selector in production step
- Audio overlay with emotion-mapped TTS

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project IDs: 06c877c953a3, b5cbe7c320f6
