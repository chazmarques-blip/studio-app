# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images), OpenAI gpt-4o-mini (text), Kling AI v3 (video + V2A + Lip Sync), ElevenLabs (voice TTS)

## Production Pipeline (5 Phases)

### PHASE 1: Dialogue Generation
- GPT-4o-mini generates clean character dialogue from script
- Stage direction filter (13+ markers) removes non-spoken text
- Format: "CharacterName: 'spoken words'" or "(silêncio)"
- Distributes dialogue evenly across 30 frames (aim: 20+ with dialogue)

### PHASE 2: Video Generation (Kling AI)
- **Modo Rápido**: 30 parallel I2V clips + xfade crossfade (~8 min)
- **Modo Cinema**: Sequential clips using last real frame extraction (~20 min)

### PHASE 2.5: Lip Sync (NEW - 2026-04-14)
- For each clip with dialogue: identify_face → lip_sync with TTS audio
- Uploads clip + audio to Supabase for Kling API access
- ~90-100s per clip, ~30 min total for 21 dialogue clips
- Graceful fallback: clips without detected faces keep original video
- Result: 12/21 clips lip-synced in first production

### PHASE 3: Audio Production
- ElevenLabs TTS with character-specific voices (voice_map)
- Padded to 6s per frame, concatenated into full audio track

### PHASE 4: Final Mix + Multi-format Export
- FFmpeg merge: video + dialogue track (+ optional V2A BGM)
- Video compression (CRF 28) when >48MB
- Export: YouTube 16:9, TikTok 9:16, Instagram 1:1

## Recent Changes

### Lip Sync Integration (2026-04-14)
- Integrated Kling identify_face + lip_sync API into production pipeline
- Runs after clip generation, before FFmpeg concat
- Each dialogue clip: upload → face detect → TTS → lip sync → download
- Fallback for animal characters or missing faces

### Dialogue + Audio Fixes (2026-04-14)
- Dialogue prompt rewritten: ONLY spoken words, no stage directions
- Stage direction filter with 13 markers
- Video compression for Supabase upload (55MB→31MB)
- Upload before tmpdir cleanup (fixed 0 outputs bug)
- V2A sonoplastia: 20s sample + loop to video length

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project IDs: 06c877c953a3, 0295f93baf6e

## Pending/Backlog
- P1: Improve dialogue distribution (frames 16-24 still silent)
- P2: Custom Video Editor UI
- P2: "Seed Oficial" for new tenants
- P2: Modularize DirectedStudio.jsx
