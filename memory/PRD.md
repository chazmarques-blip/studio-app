# AgentZZ - PRD

## Original Problem Statement
SaaS platform "AgentZZ" for SMBs to deploy AI agents on social media. AI Marketing Studio with full campaign generation.

## Core Architecture
- **Frontend**: React, Tailwind, shadcn-ui, Framer Motion, recharts, react-i18next
- **Backend**: FastAPI, Supabase (PostgreSQL), MongoDB
- **3rd Party**: Claude, OpenAI Whisper, Sora 2, ElevenLabs, Google APIs, Gemini, fal.ai

## Completed (March 21, 2026 — Session 3)

### Art Style Generator in Gallery Modal
- ArtGalleryModal now has inline style generator with 14 styles
- Styles: Minimalist, Vibrant, Luxury, Corporate, Playful, Bold, Organic, Tech, Cartoon, Illustration, Watercolor, Neon, Retro, Flat Design
- Uses same campaign prompt + chosen style variable
- New images added to gallery in real-time
- Backend: POST /api/campaigns/pipeline/regenerate-single-image

### Video Quality Overhaul
- CRF 23→16 throughout, preset fast→slow
- Normalization forces exact resolution (scale+crop, no black bars)
- Audio bitrate 192k→256k/320k

### Audio Pre-Approval Pipeline
- marcos_video pauses at `waiting_audio_approval` before Sora 2

### Avatar 360° View (3D Style Preservation)
- Style-aware prompts, auto-trigger, persistence

### Other: Landing V2, Download fix, Photo reference fix

## Test Reports
- iteration_76-81: All passed (30+21+30+32+22+16 = 151 tests total)

## Credentials
- Email: test@agentflow.com / Password: password123

## P1 - Upcoming
- Omnichannel integrations, CRM improvements

## P2 - Future/Backlog
- Admin System, Payment Gateway, Terms/Privacy, PipelineView refactoring
