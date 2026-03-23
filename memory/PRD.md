# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, Lucide Icons
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) — tenants.settings JSONB
- **AI**: Claude Sonnet 4.5 (cinema agents + screenwriter, 3x retry), Sora 2 (video gen with avatar image_path), Gemini (image gen), Whisper (voice)
- **Video**: FFmpeg for multi-scene concatenation
- **Design**: Dark luxury monochrome + gold accents

## Completed Features
- Landing page, Auth, Onboarding, Dashboard
- Agent Management (marketplace, config, sandbox)
- CRM with Kanban pipeline
- Google Calendar/Sheets integration
- AI Avatar Generator (Gemini cyborg)
- Settings page
- Marketing AI Studio (auto pipeline: image, video, carousel, avatar)
- **Directed Studio v2** — COMPLETE:
  - **Step 0: Project Management** — List all projects with status, resume from any step, create new with name+description
  - **Step 1: Interactive Screenwriter** — Background thread + polling (K8s safe), 3x retry on 502/503
  - **Step 2: Characters & Avatars** — Edit inline, copy prompt, preview zoom, AI edit, create new
  - **Step 3: Multi-Scene Production** — 3 Cinema Agents per scene, avatar reference via image_path, art style auto-detection
  - **Step 4: Results** — Watch complete film + individual scenes with download
  - Auto-resume for in-progress productions
  - E2E tested: Abraham & Isaac (3 scenes, 36s film)

## Key API Endpoints
- POST /api/studio/projects — Create project (name + briefing)
- POST /api/studio/chat — Screenwriter (background + polling)
- GET /api/studio/projects/{id}/status — Poll status (chat_status, chat_history)
- POST /api/studio/projects/{id}/update-characters — Update characters
- POST /api/studio/start-production — Start production (with character_avatars)
- GET /api/studio/projects — List all projects
- DELETE /api/studio/projects/{id} — Delete project

## Upcoming Tasks (P1)
- ElevenLabs voice generation for scene narration
- Delete projects from UI
- Story templates (Biblical, Commercial, Documentary, Fiction)

## Future Tasks (P2-P4)
- Phase 8: Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Stripe payment gateway
- Refactor PipelineView.jsx (3000+ lines)

## Known Issues
- Universal Key budget may be exceeded during multi-scene generation
- User needs to add balance: Profile → Universal Key → Add Balance

## Test Credentials
- Email: test@agentflow.com
- Password: password123
