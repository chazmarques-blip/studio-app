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
- Parallel LLM calls generate Sora/Kling prompts

### PHASE B: Video Generation (existing, enhanced)
- **Modo Rápido**: 30 parallel I2V clips with start+end frame → xfade crossfade (5 min)
- **Modo Cinema**: Sequential clips using last real frame extraction → perfect continuity (20 min)
- Both use `kling-v3/std` with `image_tail` for smooth transitions

### PHASE C: Audio Production (new, integrated)
- C1: Dialogue alignment (LLM generates `dialogue_text` per frame matching visual action)
- C2: Emotion TTS (ElevenLabs with emotion→params mapping: joy/sad/tense/etc.)
- C3: Audio padded to 6s per frame, concatenated into full dialogue track

### PHASE D: Final Mix + Export (new)
- D1: FFmpeg merge video + dialogue track (H264 baseline + AAC stereo)
- D2: Multi-format export: YouTube 16:9, TikTok 9:16, Instagram 1:1

## What's Been Implemented

### Dual Production Mode + Full Audio Pipeline (2026-04-13)
- `kling_client.py`: Added `generate_sequential_clips()`, `video_to_audio()`, `identify_face()`, `lip_sync()`
- `production.py`: Both modes (fast/cinema) + inline PHASE C+D audio pipeline + multi-format export
- Frontend: Mode selector (Rápido/Cinema), "Gerar Diálogos" and "Gerar Áudio" buttons

### Previous implementations
- Parallel I2V Strategy B (30 clips in 2 min)
- Frame dialogue display + inline editing
- Video engine selection fix
- 30-frame async storyboard generation

## Pending Tasks
- P1: Kling Lip-Sync integration (identify-face + advanced-lip-sync per clip)
- P1: Kling Video-to-Audio sonoplastia (SFX + BGM per clip, parallel)
- P1: Frontend progress tracking for PHASE C+D
- P2: "Seed Oficial" for new tenants
- P2: Modularize large frontend components

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project ID: 06c877c953a3
