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

## What's Been Implemented

### P0 Fix: Kling Storyboard DB Save (2026-04-10)
- **Root Cause**: `_update_project_field` used write-behind cache (`flush_now=False`). 30 frames were saved to in-memory cache but the async flush to Supabase failed silently (5MB+ payload).
- **Fix Applied**:
  1. Added `flush_now` parameter to `_update_project_field` in `_shared.py`
  2. All kling storyboard saves now use `flush_now=True`
  3. Added verification step after save + fallback direct DB save
  4. Improved `_flush_tenant` logging with payload size tracking
  5. Frontend optimized: immediately loads storyboards after successful POST instead of polling
  6. Fixed `displayFrames` to flatten ALL scenes (was only showing `scenes[0]`)
  7. Fixed `doneCount` to count across all scenes
- **Files Modified**: `_shared.py`, `kling_storyboard.py`, `cache.py`, `StoryboardEditor.jsx`
- **Test Result**: Verified 30 frames persist through cache → Supabase → API → frontend

### Previously Completed (from earlier forks)
- Character avatar generation with multimodal Gemini inputs
- Target audience age-adaptation for dialogues
- Director's Preview unblocking
- Inline 2-click regeneration UI with progress overlay
- Cache-busting for regenerated images

## Pending Tasks
- P1: System of Layers Phase 2 - Custom Video Editor UI
- P2: "Seed Oficial" System for New Tenants
- P2: Modularize large frontend components (StoryboardEditor ~2000 lines)
- P2: Migrate Avatar states to useAvatarManager.js hook

## Test Credentials
- Email: test@studiox.com
- Password: studiox123
