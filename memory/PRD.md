# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images/keyframes), OpenAI gpt-4o-mini (text), Claude Sonnet 4.5 (scene direction), Kling AI v3 (video + V2A + Lip Sync), Sora 2 (video + native lip sync), ElevenLabs (voice TTS)

## PIPELINE SEPARATION

### KLING PIPELINE (30 storyboard frames -> video)
1. Dialogue Generation (GPT-4o-mini): 30 frames x character dialogue
2. Auto-assign Voices (ElevenLabs)
3. 30 Parallel I2V Clips (Kling v3, 6s each)
4. Kling Lip Sync: For each clip -> TTS -> identify_face -> lip_sync API -> download
5. FFmpeg Concat (preserves lip-synced audio)
6. V2A Sonoplastia (Kling V2A: BGM at 15% volume)
7. Multi-format Export

### SORA 2 PIPELINE (Cinema Sequential Mode)
1. Dialogue Unified: `dubbed_text` = canonical source, copied to `dialogue`
2. Scene Directors SEQUENTIAL: Each director receives prev_scene context (transition_from, transition_to, music_mood, sfx_notes)
3. Keyframe Generation: Only scene 1 gets Gemini keyframe; scenes 2+ use last frame from previous clip
4. Sora 2 Video Generation: Full prompt (no truncation) with dialogue FIRST, then characters, direction, style
5. Cinema Sequential Rendering: Each clip generated sequentially, last frame extracted via FFmpeg for next
6. FFmpeg Crossfade Concatenation: 1s crossfade between clips
7. TTS Audio Overlay: ElevenLabs voices per character beat with correct timing (12s/scene)
8. V2A Sonoplastia: BGM + SFX via Kling V2A using scene music_mood and sfx_notes
9. Final Mix: TTS dialogue (vol 1.0) + V2A (vol 0.15) onto video

### KEY RULES
- Kling pipeline does NOT use Sora 2 prompts
- Sora 2 pipeline does NOT use Kling lip sync API
- `dialogue` field = `dubbed_text` (single source of truth)
- Prompt order: Dialogue FIRST -> Characters -> Direction -> Style (never truncated)
- `max_scenes` parameter limits both video production AND audio overlay
- `full-production` validates by engine: Sora 2 needs scenes, Kling needs storyboards

## Scene Continuity System (NEW - 2026-04-15)

### Layer 1: Screenwriter
New fields per scene: `transition_from`, `transition_to`, `music_mood`, `sfx_notes`
- transition_from: How scene visually connects FROM previous
- transition_to: How scene ENDS leading into next
- music_mood: Music atmosphere for V2A
- sfx_notes: Sound effects for V2A

### Layer 2: Scene Director
- Directors run SEQUENTIALLY for Sora 2 (each gets prev_scene context)
- Continuity context injected: previous scene title, description ending, last dialogue, transition notes
- Audio atmosphere (music_mood, sfx_notes) reflected in visual direction
- First 2 seconds of each scene must connect to previous scene's ending

### Layer 3: Post-Production
- FFmpeg xfade filter: 1s crossfade between clips (video + audio)
- Fallback to simple concat if crossfade fails or >30 scenes

## Bug Fixes (2026-04-15)

### Backend Syntax Error (P0) - FIXED
- Stray `)` in f-string + dead code with unclosed f-string

### full-production Sora 2 Validation (P0) - FIXED
- Now validates by engine: Kling requires storyboards, Sora 2 only needs scenes

### Dialogue Not Reaching Sora 2 (P0) - FIXED
- Root cause: prompt truncated to 2500 chars, dialogue at end = cut completely
- Fix: Removed truncation, reordered prompt (dialogue first)
- Also: dialogue_timeline Narrator beats were filtered out; now falls through to scene_dialogue

### Two Different Dialogues (P1) - FIXED
- Root cause: `dialogue` and `dubbed_text` were different versions
- Fix: Unified `dialogue = dubbed_text` in screenwriter, parallel_agents, and existing data
- Frontend now shows `dubbed_text || dialogue`

### Crossfade concat_file Error (P1) - FIXED
- Simple concat code ran even when crossfade succeeded, using undefined `concat_file`
- Fix: Simple concat only runs when `use_crossfade = False`

### Audio Overlay Processing All Scenes (P1) - FIXED
- `_generate_sora2_audio_overlay` now respects `max_scenes` limit

### lang Variable Undefined (P1) - FIXED
- Changed to `project_lang` in `_scene_director`

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Test Project (Sora 2): 5a12e7f93f6f

## Pending/Backlog
- P1: Test with new shorter project for better continuity
- P1: Voice selection UI (choose ElevenLabs voices per character)
- P2: Custom Video Editor UI (timeline/editor)
- P2: Modularize DirectedStudio.jsx (~4600 lines)
- P2: Migrate Avatar states to useAvatarManager.js
