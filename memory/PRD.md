# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
SaaS platform "AgentZZ" for SMBs to deploy AI agents on social media. AI Marketing Studio with full campaign generation (copy, images, video, audio).

## Core Architecture
- **Frontend**: React, Tailwind, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI, Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude 3.5 Sonnet, OpenAI Whisper, Sora 2, ElevenLabs, Google APIs, Gemini, fal.ai

## Completed (March 21, 2026 — Session 3)

### Video Quality Overhaul (Cinema Grade)
- **CRF 23→16** in ALL pipeline steps (normalization, crossfade, brand overlay, concat, final merge)
- **Preset fast→slow** for max quality throughout pipeline
- **Normalization** now forces exact target resolution: `scale=W:H:force_original_aspect_ratio=increase,crop=W:H` — eliminates black bars
- **Audio bitrate** upgraded from 192k to 256k/320k
- **Audio merge** now uses CRF 16 encoding instead of `-c:v copy`
- **Video variants** use CRF 18, preset slow, 256k audio for social platform formats

### Social Media Video Formats (Already Configured)
- TikTok: 1080x1920 (9:16)
- Instagram: 1080x1350 (4:5) + Reels 1080x1920
- Facebook: 1280x720 (16:9) + Stories 1080x1920
- WhatsApp: 1080x1920 (9:16)
- YouTube: 1920x1080 (16:9) + Shorts 1080x1920
- Google Ads: 1920x1080 (16:9)
- Telegram: 1280x720 (16:9)

### Audio Pre-Approval in Video Pipeline
- After marcos_video AI generates script, pipeline pauses at `waiting_audio_approval`
- TTS audio preview auto-generated
- Endpoint: POST /api/campaigns/pipeline/{id}/approve-audio
- Approve → Sora 2 video generation starts; Reject → script revision

### Avatar 360° View (3D Style Preservation)
- Style-aware prompts for 3D/Pixar avatars
- Auto-trigger 360° when switching to tab
- avatar_style persistence in all CRUD functions

### Other Fixes
- 3D Avatar photo reference: uses _gemini_edit_image (litellm multimodal)
- Landing Page V2 at `/`
- Download button: fetch+blob pattern

## Test Reports
- iteration_76: 30/30 | iteration_77: 21/21 | iteration_78: 30/30 | iteration_79: 32/32 | iteration_80: 22/22

## Test Credentials
- Email: test@agentflow.com / Password: password123

## P1 - Upcoming
- Activate live omnichannel integrations
- CRM Kanban improvements

## P2 - Future/Backlog
- Admin System, Payment Gateway, Terms/Privacy
- PipelineView.jsx refactoring (2700+ lines)
