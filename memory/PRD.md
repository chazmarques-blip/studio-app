# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated content (Pixar/DreamWorks quality).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL
- **AI Services**: OpenAI GPT-4o-mini (text) + Sora 2 (video), Claude Sonnet 4.5 (scene direction/review), Gemini (keyframes), ElevenLabs (TTS), Kling AI (V2A sonoplastia)

## SORA 2 PIPELINE (Cinema Sequential Mode)
1. **Dialogue Unified**: `dubbed_text` = `dialogue` (single source of truth)
2. **Scene Directors SEQUENTIAL**: Each receives prev_scene context + Edge Mirroring + personality
3. **Keyframe**: Only scene 1 gets Gemini keyframe; scenes 2+ use last frame
4. **Sora 2 Video**: Full prompt (dialogue FIRST, no truncation), native audio kept
5. **Cinema Sequential**: Each clip sequential, last frame extracted for next
6. **FFmpeg Crossfade**: 1s xfade + acrossfade between clips
7. **V2A Sonoplastia**: BGM + SFX added ON TOP of native Sora 2 audio (12% vol)

## Agent Intelligence (Current Rules)

### Scene Director
- DYNAMICS: Characters constantly moving, expressions change every 2s, physical comedy
- EDGE MIRRORING: ENTRY 0-1s → ACTION 1-11s → EXIT 11-12s
- ENVIRONMENT TRANSITIONS: Motivated movement (character walks through door), camera follows, gradual lighting shift
- PERSONALITY: Gestures/expressions match character personality

### Screenwriter  
- Dialogue: 35-40 words/scene (~9-10s speech), 3 characters interact in every scene
- Last dialogue line connects to next scene's topic
- Continuity fields: transition_from, transition_to, music_mood, sfx_notes
- Environment transitions: EXIT dialogue motivates move, descriptions show journey

### Character Personality System
- Field `personality` on each character (temperament, humor, catchphrases)
- Injected into Screenwriter prompts → dialogue with personality
- Injected into Scene Director → visual expressions/gestures match

## Features Implemented
- Cinema Sequential Mode with Edge Mirroring
- Character Bible from Claude Vision (analyzes real avatar images)
- Dialogue unification (dubbed_text = dialogue)
- Custom instruction field for scene regeneration
- Scene editing in zoom modal (title, description, dialogue)
- Auto-advance Screenwriter → Director Review
- Director Review in background (no 502 timeout)
- Rebuild Film button (re-concatenate after scene regeneration)
- Auto-fix stuck storyboard panels (>5 min generating)
- Cache-buster on regenerated storyboard images
- max_scenes parameter for partial production
- V2A sonoplastia using scene music_mood/sfx_notes

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project Pulmeranea 2: ae9c7307ac53

## Backlog
- P1: Create new project from scratch with all improvements active
- P1: Personality field UI (textarea in character editor)
- P2: Custom Video Editor UI (timeline)
- P2: Modularize DirectedStudio.jsx (~4700 lines)
