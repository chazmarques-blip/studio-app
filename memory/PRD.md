# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images), OpenAI gpt-4o-mini (text), Kling AI v3 (video + V2A + Lip Sync), Sora 2 (video + native lip sync), ElevenLabs (voice TTS)

## PIPELINE SEPARATION (2026-04-14)

### KLING PIPELINE (30 storyboard frames → video)
1. **Dialogue Generation** (GPT-4o-mini): 30 frames x character dialogue
2. **Auto-assign Voices** (ElevenLabs)
3. **30 Parallel I2V Clips** (Kling v3, 6s each)
4. **Kling Lip Sync**: For each clip → TTS → identify_face → lip_sync API → download
5. **FFmpeg Concat** (preserves lip-synced audio)
6. **V2A Sonoplastia** (Kling V2A: BGM at 15% volume)
7. **Multi-format Export** (YouTube 16:9, TikTok 9:16, Instagram 1:1)
8. **Upload + Compression** (CRF 28 if >48MB)

### SORA 2 PIPELINE (prompt-based with native lip sync)
1. **Dialogue in Prompt**: `dialogue_timeline` with timing included in Sora 2 prompt
2. **Sora 2 Video Generation**: Native lip sync from prompt (12s clips)
3. **TTS Audio Overlay**: ElevenLabs voices matched to scenes
4. **V2A Sonoplastia**: Background music via Kling V2A
5. **Multi-format Export**

### KEY SEPARATION RULES
- Kling pipeline does NOT use Sora 2 prompts
- Sora 2 pipeline does NOT use Kling lip sync API
- Audio overlay (_generate_audio_overlay_background) ONLY for Sora 2
- Kling handles its own audio inside _sora_render (lip sync + TTS + V2A)
- dialogue_locked field prevents regeneration of approved dialogues

## Bug Fixes (2026-04-14)

### Company Creation Lost by Cache
- **Root cause**: ProjectCache._flush_tenant overwrote settings with stale cache after company creation
- **Fix**: Drop cache entry (without flush) after direct DB writes in companies.py

## Test Credentials
- Email: test@studiox.com / Password: studiox123

## Pending/Backlog
- P1: Visual continuity (Modo Cinema as default)
- P1: Voice selection UI (choose ElevenLabs voices per character)
- P2: Custom Video Editor UI
- P2: Modularize DirectedStudio.jsx
