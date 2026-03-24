# AgentZZ - Product Requirements Document

## Original Problem Statement
Mobile-first SaaS platform "AgentZZ" for managing AI chatbot agents + Directed Video Production Studio.

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn-ui, Lucide Icons
- Backend: FastAPI (Python), Supabase (PostgreSQL)
- AI: Claude Sonnet (Scene Director), Sora 2 (video gen), Gemini (image gen)
- Voice: ElevenLabs (24 voices, eleven_multilingual_v2)
- Video: FFmpeg for concatenation

## Directed Studio v3 Pipeline Architecture
```
Per-scene parallel teams (not sequential phases):
┌─ Scene 1: SceneDirector(Claude) → Sora 2 ─┐
├─ Scene 2: SceneDirector(Claude) → Sora 2 ─┤  ALL SIMULTANEOUS
├─ Scene N: SceneDirector(Claude) → Sora 2 ─┤  (Sora max 5 concurrent)
└─ MusicDirector (1 global call)             ┘
→ FFmpeg concat → Complete
```

### Optimizations Applied:
- 3 agents merged into 1 "Scene Director" (1 Claude call not 3)
- Video gen starts per-scene as soon as prompt ready
- Avatars cached once globally (not per scene)
- Sora 2 rate-limited by threading.Semaphore(5)
- Per-scene status: queued → directing → waiting_sora → generating_video → done/error
- Real-time video preview per scene
- Background production with global banner across all pages
- Estimated time: ~8-9min regardless of scene count (limited by Sora 2)

## Key API Endpoints
- POST/GET/DELETE /api/studio/projects
- POST /api/studio/chat (background screenwriter)
- GET /api/studio/projects/{id}/status (poll with per-scene status)
- POST /api/studio/start-production (launches parallel teams)
- POST /api/studio/projects/{id}/generate-narration (ElevenLabs)
- GET /api/studio/projects/{id}/narrations
- GET /api/studio/voices (24 voices)

## Upcoming
- Merge narration audio with video (FFmpeg overlay)
- Voice preview before selecting
- Story templates

## Future
- Phase 8: Omnichannel (WhatsApp, Telegram, etc.)
- Admin System & Stripe payments
- Refactor PipelineView.jsx (3000+ lines)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
