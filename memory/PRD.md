# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, Lucide Icons
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) — tenants.settings JSONB
- **AI**: Claude Sonnet 4.5 (3x retry), Sora 2 (video gen with avatar image_path), Gemini (image gen), Whisper (voice)
- **Video**: FFmpeg for multi-scene concatenation

## Completed Features
- Landing, Auth, Onboarding, Dashboard, Agent Management, CRM, Google Integration, Avatar Generator, Settings
- Marketing AI Studio (auto pipeline: image, video, carousel, avatar)
- **Directed Studio v2** — COMPLETE:
  - **Step 0: Project Management** — List all projects with milestones, create new (name+description), resume from any step, fix stuck projects
  - **Step 1: Interactive Screenwriter** — Background thread + polling, 3x retry on 502/503
  - **Step 2: Characters & Avatars** — Edit inline, copy prompt, preview zoom, AI edit, create new
  - **Step 3: Multi-Scene Production** — 3 Cinema Agents per scene, avatar reference via image_path, art style auto-detection (cartoon/anime/realistic)
  - **Step 4: Results** — Watch complete film + individual scenes with download
  - **Milestones System** — Tracks: project_created → screenplay_created → characters_updated → avatars_linked → production_started → agents_complete → videos_generated → film_complete
  - Auto-resume for in-progress productions (30 min window)

## Key API Endpoints
- POST /api/studio/projects — Create project
- POST /api/studio/chat — Screenwriter (background + polling)
- GET /api/studio/projects/{id}/status — Poll status with milestones
- POST /api/studio/projects/{id}/update-characters — Update characters
- POST /api/studio/projects/{id}/fix-stuck — Fix stuck projects
- POST /api/studio/start-production — Start production (with character_avatars)
- GET /api/studio/projects — List all projects
- DELETE /api/studio/projects/{id} — Delete project

## Upcoming Tasks (P1)
- ElevenLabs voice narration
- Delete projects from UI
- Story templates

## Future Tasks (P2-P4)
- Phase 8: Omnichannel
- Admin Management System
- Stripe payment
- Refactor PipelineView.jsx

## Test Credentials
- Email: test@agentflow.com
- Password: password123
