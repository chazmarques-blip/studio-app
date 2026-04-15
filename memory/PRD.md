# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images), OpenAI gpt-4o-mini (text), Kling AI v3 (video + V2A + Lip Sync), Sora 2 (video + native lip sync), ElevenLabs (voice TTS)

## PIPELINE SEPARATION (2026-04-14)

### KLING PIPELINE (30 storyboard frames -> video)
1. **Dialogue Generation** (GPT-4o-mini): 30 frames x character dialogue
2. **Auto-assign Voices** (ElevenLabs)
3. **30 Parallel I2V Clips** (Kling v3, 6s each)
4. **Kling Lip Sync**: For each clip -> TTS -> identify_face -> lip_sync API -> download
5. **FFmpeg Concat** (preserves lip-synced audio)
6. **V2A Sonoplastia** (Kling V2A: BGM at 15% volume)
7. **Multi-format Export** (YouTube 16:9, TikTok 9:16, Instagram 1:1)
8. **Upload + Compression** (CRF 28 if >48MB)

### SORA 2 PIPELINE (prompt-based with native lip sync)
1. **Dialogue in Prompt**: `dialogue_timeline` with timing included in Sora 2 prompt
2. **Sora 2 Video Generation**: Native lip sync from prompt (12s clips)
3. **Cinema Sequential Mode** (DEFAULT): Scene 1 gets Gemini keyframe, scenes 2+ use last frame from previous clip for visual continuity
4. **Character Bible Injection**: pd_chars from production_design injected into scene director prompts for character consistency
5. **TTS Audio Overlay**: ElevenLabs voices matched to scenes via `_generate_sora2_audio_overlay` (12s segments, timed beats)
6. **V2A Sonoplastia**: Background music via Kling V2A
7. **Multi-format Export**

### KEY SEPARATION RULES
- Kling pipeline does NOT use Sora 2 prompts
- Sora 2 pipeline does NOT use Kling lip sync API
- Audio overlay (`_generate_sora2_audio_overlay`) ONLY for Sora 2
- Kling handles its own audio inside `_sora_render` (lip sync + TTS + V2A)
- `dialogue_locked` field prevents regeneration of approved dialogues
- `full-production` endpoint validates based on `video_engine`: Sora 2 needs scenes, Kling needs storyboards

## Bug Fixes (2026-04-15)

### Backend Syntax Error (P0) - FIXED
- **Root cause**: Stray `)` in f-string at line 536 + dead code with unclosed f-string at lines 591-601
- **Fix**: Removed stray parenthesis, deleted dead code block after `return` statement

### full-production Sora 2 Validation (P0) - FIXED
- **Root cause**: Endpoint required `kling_storyboards` for ALL projects, blocking Sora 2
- **Fix**: Validation now checks `video_engine`: Kling requires storyboards, Sora 2 only needs scenes

### lang Variable Undefined (P1) - FIXED
- **Root cause**: `lang` used in `_scene_director` but not defined in scope
- **Fix**: Changed to `project_lang` (closure variable from line 306)

### Cinema Sequential Optimization (P1) - DONE
- **Root cause**: ALL keyframes were generated in parallel (wasting API calls for scenes 2+)
- **Fix**: For Sora 2 Cinema Sequential, only scene 1 gets Gemini keyframe; scenes 2+ use last frame from previous clip

### Sora 2 Audio Overlay (P1) - DONE
- **New function**: `_generate_sora2_audio_overlay` reads `dialogue_timeline` from scenes (12s each)
- Generates TTS per character beat with correct timing
- Mixes dialogue + V2A sonoplastia onto video

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Test Project (Sora 2): 5a12e7f93f6f

## Pending/Backlog
- P1: End-to-end test of Sora 2 pipeline (requires API keys with available budget)
- P2: Custom Video Editor UI (timeline/editor)
- P2: Modularize DirectedStudio.jsx (~4600 lines)
- P2: Migrate Avatar states to useAvatarManager.js
- P2: Voice selection UI (choose ElevenLabs voices per character)
