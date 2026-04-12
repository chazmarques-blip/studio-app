# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform. Users create animated videos from scripts to final production, using AI-powered storyboards, character avatars, dialogues, and video generation.

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (NOT MongoDB)
- **Storage**: Supabase Storage (pipeline-assets bucket)
- **AI Services**: Gemini API (image gen), Claude/Anthropic (text/prompts), ElevenLabs (voice), Kling (video)
- **Cache Layer**: 3-tier caching (ImageCache, ProjectCache write-behind, LLMCache)

## Key Data Model
- Projects stored in `tenants.settings.studio_projects` (JSONB field)
- Each project contains: scenes, characters, character_avatars, dialogues, kling_storyboards, visual_style, target_audience
- Kling storyboards: array of scene objects, each with `frames[]` (30 frames for 5-min video)
- Each frame now includes: frame_number, time_start, time_end, dialogue_text, image_prompt, kling_prompt, characters_present, camera_movement, key_action, emotion, lighting

## What's Been Implemented

### P0: Frame Dialogue Display + Inline Editing (2026-04-12)
- **Backend**: Modified LLM prompt in `kling_storyboard.py` to generate `dialogue_text` field for each frame
- **Backend**: Created PATCH endpoint `/api/studio/projects/{id}/kling-storyboards/update-frame` for editing frame fields (image_prompt, kling_prompt, dialogue_text)
- **Frontend**: Grid view now shows dialogue_text snippet below each frame
- **Frontend**: Zoom modal now has 3 editable sections: Texto/Dialogo, Prompt de Imagem, Prompt Kling
- **Frontend**: Edit/Save/Cancel buttons in zoom modal for inline editing
- **Test Result**: Backend 100% (8/8 tests), Frontend code verified
- **Files Modified**: `kling_storyboard.py`, `StoryboardEditor.jsx`

### P0 Fix: Kling Storyboard DB Save (2026-04-10)
- **Root Cause**: `_update_project_field` used write-behind cache. 30 frames saved to in-memory cache but flush to Supabase failed silently (5MB+ payload).
- **Fix Applied**: `flush_now=True` + verification step + fallback direct DB save
- **Files Modified**: `_shared.py`, `kling_storyboard.py`, `cache.py`, `StoryboardEditor.jsx`

### Previously Completed (from earlier forks)
- Character avatar generation with multimodal Gemini inputs
- Target audience age-adaptation for dialogues
- Director's Preview unblocking
- Inline 2-click regeneration UI with progress overlay
- Cache-busting for regenerated images
- Async background generation with frontend polling
- LLM engine switch from Claude (quota exceeded) to OpenAI gpt-4o-mini
- Kling Authentication rewrite (PyJWT)

## Pending Tasks
- P1 (BLOCKED): Kling AI Video Generation - User account balance empty
- P1: System of Layers Phase 2 - Custom Video Editor UI
- P2: "Seed Oficial" System for New Tenants
- P2: Modularize large frontend components (StoryboardEditor ~2200 lines)
- P2: Migrate Avatar states to useAvatarManager.js hook
- P2: Project Deletion UI verification

## API Endpoints
- `POST /api/studio/projects/{id}/kling-storyboards/generate` - Start async 30-frame generation
- `GET /api/studio/projects/{id}/kling-storyboards` - Get storyboards with status
- `POST /api/studio/projects/{id}/kling-storyboards/regenerate-frame` - Regenerate single frame image
- `PATCH /api/studio/projects/{id}/kling-storyboards/update-frame` - Edit frame text fields
- `DELETE /api/studio/projects/{id}/kling-storyboards` - Delete all storyboards

## Test Credentials
- Email: test@studiox.com
- Password: studiox123
- Project with 30 frames: 06c877c953a3
