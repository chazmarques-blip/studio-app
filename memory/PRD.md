# AgentZZ - PRD

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Includes AI Marketing Studio for multimodal campaign generation.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion + recharts
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) — ALL data stored in Supabase (no MongoDB)
- AI: Claude Sonnet 4.5, Gemini Flash, Gemini Nano Banana (images), Sora 2 (video), ElevenLabs (voice/music)
- Auth: Supabase Auth
- Pipeline: Multi-agent AI directors (Sofia, Lee, Ana, Lucas, Rafael, George, Stefan, Dylan, Roger, Marcos, Pedro)

## Implemented Features (Completed)
- Dashboard with recharts analytics
- Agent Management + Marketplace
- Agent Configuration with Google Calendar/Sheets integration
- AI Marketing Studio with full pipeline
- Campaign Gallery with Art Style Generator (14 styles)
- Avatar 3D Creator with 360-degree views
- Video generation pipeline (Sora 2 + FFmpeg)
- Audio Pre-Approval (pipeline pauses before video)
- FFmpeg quality: CRF 16, scale+crop, 256k/320k audio
- Landing Page V2
- Multi-language support (PT/EN/ES)

## Completed This Session (2026-03-21)

### Bug Fix: Art Gallery Images Disappearing
- Root cause: Field name inconsistency — engine.py saved images as `image_urls` while regenerate-single-image and edit-image-text read from `images` (empty field)
- Fix: Normalized all backend code to use `images` with fallback to `image_urls` for legacy pipelines
- Frontend: ArtGalleryModal now fetches fresh campaign data on mount (useEffect)
- Frontend: Gallery/Detail modal close now triggers loadData() to refresh campaign list
- Files fixed: pipeline/engine.py, pipeline/routes.py, Marketing.jsx
- Verified: 11/11 backend + 6/6 frontend tests passed (iteration_82)

### Database Verification
- Confirmed: ALL data is stored in Supabase (campaigns, pipelines, creatives, storage)
- No MongoDB usage in production code
- Tables: campaigns, pipelines, tenants, agents, creatives, leads, conversations

## Backlog
### P0 (In Progress)
- Presenter mode: lip-sync integration (avatar talks in video) — needs API like HeyGen/D-ID/Sync Labs
- Color grading via FFmpeg (contrast + saturation + warmth)
- Fade-in/out suaves, dissolve transitions

### P1
- Omnichannel integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- CRM Kanban board

### P2
- Admin Management System
- Payment Gateway
- Terms of Use / Privacy Policy

### P3
- Refactor PipelineView.jsx (>2700 lines)
- Scalability hardening

## Known Issues
- `_extract_dylan_voice_settings` fails with UUID error for "_preview" suffixed pipeline IDs (non-critical)
- Live social channel integrations are mocked
- Legacy pipelines have mismatch between `images` and `image_urls` fields (handled by fallback)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
