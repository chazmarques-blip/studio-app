# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for SMBs to deploy AI agents on social media. Features: AI Marketing Studio, omnichannel support, premium dark luxury theme.

## Core Architecture
- **Frontend**: React, Tailwind, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI, Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude 3.5 Sonnet, OpenAI Whisper, Sora 2, ElevenLabs, Google APIs, Gemini, fal.ai (Kling)

## Completed (March 21, 2026 — Session 3)

### Bug Fix: Avatar 360° View for 3D/Pixar Avatars (3 iterations of fixes)
1. **Style-aware prompts**: Backend `_run_batch_360` and `generate_avatar_variant` now detect `avatar_style` and use 3D-appropriate prompts ("do NOT make it photorealistic")
2. **Correct source URL**: `applyClothing` and `generateAngle` use `tempAvatar.url` (generated 3D avatar) for 3D styles, not `source_photo_url` (original photo)
3. **Style inference for old avatars**: `openAvatarForEdit` infers `avatar_style` from `creation_mode` for avatars saved before the fix
4. **Clear wrong angles**: Opens 3D avatars with fresh front angle if saved angles don't match
5. **Auto-trigger 360°**: Clicking "360° View" tab auto-starts generation if <4 angles loaded
6. **Regenerate All button**: New "Regenerate All 360°" button in 360° tab
7. **Persistence**: `avatar_style` and `creation_mode` now saved/restored in all avatar CRUD functions

### Bug Fix: Download Button
- Replaced `<a target=_blank>` with fetch+blob download pattern

### P0: 3D Avatar Photo Reference Fix
- `generate_avatar_from_prompt` uses `_gemini_edit_image` (litellm multimodal) for photo references

### P1a: Landing Page V2 at `/`
### P1b: Audio Pre-Approval in Video Pipeline

## Test Reports
- iteration_76: 30/30 | iteration_77: 21/21 | iteration_78: 30/30 | iteration_79: 32/32

## Test Credentials
- Email: test@agentflow.com / Password: password123

## P1 - Upcoming
- Activate live omnichannel integrations
- CRM Kanban improvements

## P2 - Future/Backlog
- Admin System, Payment Gateway, Terms/Privacy
- PipelineView.jsx refactoring (2700+ lines)
