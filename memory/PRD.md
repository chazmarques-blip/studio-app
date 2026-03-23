# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, Lucide Icons
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) — tenants.settings JSONB
- AI: Claude Sonnet 4.5 (3x retry), Sora 2 (video gen with avatar image_path), Gemini (image gen)
- Video: FFmpeg for multi-scene concatenation

## Completed Features
- Landing, Auth, Onboarding, Dashboard, Agent Management, CRM, Google Integration, Avatar Generator, Settings
- Marketing AI Studio (auto pipeline: image, video, carousel, avatar)
- **Directed Studio v2**:
  - Step 0: Project Management — create/resume/list 39+ projects with milestones
  - Step 1: Interactive Screenwriter — background + polling, 3x retry
  - Step 2: Characters & Avatars — edit, copy prompt, AI edit, create
  - Step 3: Multi-Scene Production — segmented progress bar per scene, real-time scene_status tracking, immediate per-video save to DB
  - Step 4: Results — watch/download complete film + individual scenes
  - Milestones: project_created → screenplay_created → characters_updated → avatars_linked → production_started → agents_complete → video_scene_N → videos_generated → film_complete
  - Fix stuck projects endpoint
  - Auto-resume (30 min window)

## Key API Endpoints
- POST /api/studio/projects — Create project
- POST /api/studio/chat — Screenwriter (background)
- GET /api/studio/projects/{id}/status — Poll with scene_status + milestones
- POST /api/studio/projects/{id}/update-characters
- POST /api/studio/projects/{id}/fix-stuck
- POST /api/studio/start-production — with character_avatars
- GET /api/studio/projects — List all
- DELETE /api/studio/projects/{id}

## Upcoming
- Resume production from last completed scene
- ElevenLabs voice narration
- Delete projects from UI
- Story templates

## Future
- Phase 8: Omnichannel
- Admin System
- Stripe payments
- Refactor PipelineView.jsx

## Test Credentials
- Email: test@agentflow.com
- Password: password123
