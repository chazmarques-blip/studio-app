# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform that allows users (small and medium business owners) to deploy and configure pre-built AI agents on various social media channels and produce AI-powered video content through a Directed Studio.

## Core Features Implemented
- **Directed Studio**: Full video/storybook production pipeline with AI-powered screenwriting, storyboarding, character management, voice narration, and production
- **Character/Avatar System**: Project-isolated character management with global library, context-aware editing, incremental layer editing, 360-degree views
- **Scene Character Editing**: Users can edit which characters appear in each scene via toggle chips in the Roteiro (Step 1)
- **Agent Management**: Agent marketplace, customization, Google Calendar/Sheets integration
- **Omnichannel**: Unified inbox structure (WhatsApp, Instagram, Facebook, Telegram, SMS - mocked)
- **CRM**: Built-in CRM with visual Kanban board
- **Multi-language**: UI support for English, Portuguese, Spanish
- **Dark Luxury Theme**: Premium monochrome gold/black/white/gray design

## Recent Bug Fixes (March 28, 2026)

### Fix 1 - "Input should be a valid string" on Character Edit
- **Root Cause**: `AvatarModal.jsx` line 663 sent `base_url: null` when in Directed Mode. Pydantic's `EditAvatarRequest` model requires `str`, not `None`.
- **Fix (Frontend)**: Changed `null` to `""` in `AvatarModal.jsx`
- **Fix (Backend)**: Added `field_validator` on `EditAvatarRequest.base_url` in `config.py` to coerce `None` to `""`
- **Files**: `AvatarModal.jsx:663`, `config.py:972-981`

### Fix 2 - "Objects are not valid as a React child" Toast Crash  
- **Root Cause**: Pydantic 422 validation errors (arrays of objects) passed directly to `toast.error()`, crashing React rendering
- **Fix**: Created `getErrorMsg()` utility, applied across 20+ files (40+ occurrences)
- **Files**: `utils/getErrorMsg.js` (new), all major components and pages

### Feature - Scene Character Editing
- Backend `update-scene` endpoint accepts `characters_in_scene`
- Frontend shows toggle chips in scene edit form (Step 1)
- Testing: iteration_124.json - 100% pass rate

## Pending Verification
- 360-degree view clothing fix (company_uniform -> keep_original)

## Backlog (P0-P3)
### P1 - AI Marketing Studio (Phase 7.1 & 7.2)
### P2 - Omnichannel Integrations (Phase 8)
### P2 - Admin Management System & Stripe
### P3 - Native App Packaging (Capacitor)

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion 11.18.2, recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Anthropic Claude 3.5, OpenAI Whisper, Gemini (Image/Vision), ElevenLabs (TTS), Google APIs

## Key Credentials
- Email: test@agentflow.com / Password: password123
