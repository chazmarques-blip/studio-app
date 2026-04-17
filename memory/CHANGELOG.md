# StudioX Changelog

## 2026-04-17 (Session 3)

### Film Rebuild - JONAS E O PEIXE GRANDE (32 scenes)
- FIXED: Previous rebuild attempt (26 scenes with crossfade) crashed silently due to FFmpeg memory exhaustion
- Reduced crossfade scene limit from 30 → 15 to prevent FFmpeg crashes on large projects
- Made V2A sonoplastia overlay non-blocking in rebuild (film saves even if V2A fails)
- Increased concat re-encode timeout 600s → 900s for large projects
- Successfully concatenated 32 scenes (276.8MB input → 17MB output at CRF 35, 960:540)
- V2A sonoplastia applied successfully (18.9MB final)
- Final movie URL: accessible and valid MP4

## 2026-04-15 (Session 2)

### Cinema Sequential Mode - Complete Pipeline
- Scene Directors run SEQUENTIALLY for Sora 2 (each receives prev_scene context)
- Keyframe only for scene 1; scenes 2+ use last frame from previous clip (FFmpeg extract)
- Character Bible (pd_chars) injected into all scene director prompts

### Dialogue Fix - Single Source of Truth
- FIXED: Prompt was truncated to 2500 chars, cutting dialogue completely
- Removed all truncation from Sora 2 prompt pipeline
- Reordered prompt: Dialogue FIRST, then characters, direction, style last
- FIXED: dialogue_timeline Narrator beats filtered out → now falls through to scene_dialogue
- Unified `dialogue = dubbed_text` across screenwriter, parallel_agents, frontend
- Frontend StoryboardEditor now shows `dubbed_text || dialogue`

### Scene Continuity System (3 Layers)
- Layer 1 (Screenwriter): New fields - transition_from, transition_to, music_mood, sfx_notes
- Layer 2 (Director): Sequential directors with prev_scene context, continuity instructions, audio atmosphere
- Layer 3 (Post-prod): FFmpeg xfade crossfade (1s) between clips

### Audio Pipeline (Sora 2)
- New `_generate_sora2_audio_overlay` function (separate from Kling's)
- Reads dialogue_timeline with timing per character beat
- V2A sonoplastia uses scene music_mood and sfx_notes
- Mix: TTS (vol 1.0) + V2A (vol 0.15) onto video
- Respects max_scenes limit

### Infrastructure Fixes
- Backend syntax error fixed (stray parenthesis + dead code)
- full-production endpoint: Sora 2 no longer requires kling_storyboards
- max_scenes parameter: limits video production AND audio overlay
- Crossfade concat bug fixed (concat_file undefined when xfade succeeds)

## 2026-04-14 (Session 1)
- Kling pipeline complete rewrite (30 parallel clips, lip sync, V2A, FFmpeg concat)
- Pipeline separation (Kling vs Sora 2)
- Director Preview consistency (DO NOT MODIFY APPROVED CONTENT rule)
- Sora 2 storyboard UI fix
- Company creation cache race condition fix
- Parallel screenwriter with scene_outline
- Auth 401 fix in DialogueEditor
- UI progress feedback improvements
