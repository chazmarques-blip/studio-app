# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images), OpenAI gpt-4o-mini (text), Kling AI v3 (video + V2A + Lip Sync), ElevenLabs (voice TTS)

## Production Pipeline (6 Steps)

### STEP 1: Dialogue Generation (GPT-4o-mini)
- Generates clean character dialogue from approved script
- Format: "CharacterName: 'spoken words'" or "(silêncio)"
- Stage direction filter removes 13+ non-spoken markers
- Distributes evenly across 30 frames (aim: 20+ with dialogue)

### STEP 2: Video Generation (Kling AI v3)
- 30 parallel I2V clips x 6 seconds each
- Image-to-Video from storyboard frames

### STEP 2.5: Lip Sync (Kling API + ElevenLabs TTS)
- For EACH clip with dialogue:
  1. Generate TTS audio (ElevenLabs, character-specific voice)
  2. Upload clip + audio to Supabase
  3. Identify face → apply lip sync (audio baked into video)
  4. Download lip-synced clip (replaces original)
- Fallback: If no face detected → FFmpeg overlays TTS audio on clip
- Result: 21/21 clips with audio (10 Kling lip sync + 11 FFmpeg TTS)
- Files saved to /tmp (NOT tmpdir) to avoid deletion before concat

### STEP 3: FFmpeg Concat
- Simple concat (preserves audio from lip-synced clips)
- No xfade when lip sync active (xfade strips audio tracks)

### STEP 4: Sonoplastia (Kling V2A)
- Extract 15s video sample (V2A API limit: 3-20s)
- Generate background music + SFX
- Loop V2A audio to video length
- Mix at 15% volume with existing dialogue audio
- If lip sync active: NO additional TTS overlay (audio already in clips)

### STEP 5: Multi-format Export
- YouTube 16:9, TikTok 9:16, Instagram 1:1
- Compression (CRF 28) if main video >48MB

### STEP 6: Upload + Cleanup

## Critical Bug Fixes (2026-04-14)

### BUG 1: Lip sync clips deleted before concat
- **Root cause**: `shutil.rmtree(lip_sync_tmpdir)` in `finally` block deleted lip-synced clips
- **Fix**: Save lip-synced clips to `/tmp/lipsync_clip_{project}_{frame}.mp4` (outside tmpdir)

### BUG 2: Double audio (TTS overlay on lip-synced clips)
- **Root cause**: STEP 4 generated ANOTHER TTS track and overlaid on already-dubbed video
- **Fix**: When `has_lip_sync=True`, skip TTS generation; only add V2A background music

### BUG 3: No fallback for faces not detected
- **Root cause**: Clips without faces skipped entirely (kept silent)
- **Fix**: FFmpeg overlays TTS audio directly when face detection fails

### BUG 4: No sonoplastia in final video
- **Root cause**: V2A audio generated but never mixed into final video
- **Fix**: FFmpeg amix with dialogue at 100% volume + BGM at 15% volume

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project IDs: 0295f93baf6e

## Verified Production Results (2026-04-14 02:07)
- 30/30 Kling clips ✅
- 21/21 lip sync (0 failures) ✅
- V2A sonoplastia + BGM mixed ✅
- 3 format exports ✅
- Total: 44 min, 35MB final video

## Pending/Backlog
- P1: Visual continuity between clips (characters changing appearance)
- P1: "Director rewriting dialogue" — ensure script is preserved exactly
- P2: Custom Video Editor UI
- P2: "Seed Oficial" for new tenants
- P2: Modularize DirectedStudio.jsx
