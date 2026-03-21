# AgentZZ - PRD

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Includes AI Marketing Studio for multimodal campaign generation.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion + recharts
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
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

### Bug Fixes
- Campaign gallery image selection now updates channel mockup preview (was always first image)
- Router ordering conflict resolved (pipeline_router before campaigns_router)
- Voice ID parser rewritten (was sending "Lily" instead of "pFZP5JQG7iQjIQuC4Bku")
- ElevenLabs Music generation double-read bug fixed (response iterator consumed twice → 0 bytes)
- Alternative voices now use correct voice_ids with type="elevenlabs" flag
- Dylan override no longer overwrites alternative voice_id during pre-approval generation

### Audio Quality Overhaul
- Removed aecho reverb filter from narration (was making voices sound robotic)
- Increased music bed level from 0.22 to 0.35 (was nearly inaudible)
- Reduced sidechain compression ratio from 6 to 4 (less aggressive ducking)
- Installed Montserrat Bold font for brand overlay (replaced FreeSansBold)

### Dylan Rewrite (19,856 chars) — World-Class Audio Director
- Complete voice personality profiles for all 24 voices (each described as if Dylan has cast them hundreds of times)
- 10 music genre deep-dives with instruments, BPM, mood progressions
- Music composition mastery for ElevenLabs Music API prompt engineering
- Voice entonation via punctuation techniques (v2 model)
- Platform-specific audio mastering (TikTok, Instagram, YouTube, etc.)
- Dynamic voice settings by campaign type (dramatic, energetic, corporate, intimate)
- Dylan's music prompt now passed to video generation for custom AI music

### Ridley Rewrite (6,458 chars) — Intelligent Sora 2 Transitions
- Removed dependency on character continuity between clips (impossible in Sora 2)
- Introduced 5 transition techniques: Threshold, Reveal, Time-Lapse, Reflection, Material
- Focus on environment + product instead of specific human faces
- Uses hands, silhouettes, back-of-head shots for human elements
- Prompts optimized at 60-90 words (Sora produces better with focused prompts)

### Tests Verified
- Voice parser: 4 formats tested (name+id, id-only, name-only lookup) ✅
- Pipeline test: Dylan selected George (British Artisan) for cervejaria premium ✅
- Narration generated with correct voice_id JBFqnCBsd6RMkjVDRZzb ✅
- Alternative voice Will (bIHbv24MWmeRgasZH58o) generated correctly ✅

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

## Test Credentials
- Email: test@agentflow.com
- Password: password123
