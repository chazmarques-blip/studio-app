# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, Lucide Icons
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) — tenants.settings JSONB
- AI: Claude Sonnet 4.5 (3x retry), Sora 2 (video gen with avatar image_path), Gemini (image gen)
- Voice: ElevenLabs (24 voices, eleven_multilingual_v2)
- Video: FFmpeg for multi-scene concatenation

## Completed Features
- Landing, Auth, Onboarding, Dashboard, Agent Management, CRM, Google Integration, Avatar Generator, Settings
- Marketing AI Studio (auto pipeline: image, video, carousel, avatar)
- **Directed Studio v2**:
  - Step 0: Project Management — create/resume/list/DELETE projects with milestones
  - Step 1: Interactive Screenwriter — background + polling, 3x retry
  - Step 2: Characters & Avatars — edit, copy prompt, AI edit, create + **Voice Narration (ElevenLabs)** with 24-voice selector
  - Step 3: Multi-Scene Production — **parallel video generation (3 at a time via ThreadPoolExecutor)**, segmented progress bar, **real-time scene video preview**, time estimation
  - Step 4: Results — watch/download complete film + individual scenes
  - **Background Production** — StudioProductionContext persists polling across all pages + floating StudioProductionBanner with progress/minimize/navigate
  - Resume production button for error/incomplete projects
  - Delete projects from UI

## Key API Endpoints
- POST/GET/DELETE /api/studio/projects
- POST /api/studio/chat — Screenwriter (background)
- GET /api/studio/projects/{id}/status — Poll with scene_status + milestones + narrations
- POST /api/studio/start-production — with character_avatars (parallel 3x)
- POST /api/studio/projects/{id}/generate-narration — ElevenLabs narration (background)
- GET /api/studio/projects/{id}/narrations
- GET /api/studio/voices — 24 ElevenLabs voices
- GET /api/google/connect — Dynamic redirect_uri OAuth

## Upcoming
- Merge narration audio with final video output (FFmpeg audio overlay)
- Voice preview/sample playback before selecting
- Story templates for quick screenwriter start

## Future
- Phase 8: Omnichannel (WhatsApp, Telegram, etc.)
- Admin System
- Stripe payments
- Refactor PipelineView.jsx (3000+ lines)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
