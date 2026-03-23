# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, Lucide Icons
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) — tenants.settings JSONB
- **AI**: Claude Sonnet 4.5 (cinema agents + screenwriter), Sora 2 (video gen with avatar image_path reference), Gemini (image gen), Whisper (voice)
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
  - Interactive Screenwriter Chat (background + polling)
  - Character & Avatar Management (edit inline, copy prompt, preview zoom, AI edit, create new)
  - Multi-Scene Production Pipeline:
    - Dir. Fotografia with auto art-style detection (cartoon/anime/realistic)
    - Avatar reference images sent to Sora 2 via image_path
    - Dir. Musical + Dir. Audio per scene
  - FFmpeg video concatenation
  - Results Viewer with download
  - Project History with auto-resume

## Key API Endpoints
- POST /api/studio/chat — Screenwriter (background + polling)
- GET /api/studio/projects/{id}/status — Poll status
- POST /api/studio/projects/{id}/update-characters — Update characters
- POST /api/studio/start-production — Start production (accepts character_avatars dict)
- GET /api/studio/projects — List projects
- DELETE /api/studio/projects/{id} — Delete project

## Upcoming Tasks (P1)
- ElevenLabs voice generation for scene narration
- Story templates (Biblical, Commercial, Documentary, Fiction)
- Retry logic for empty Sora 2 video responses

## Future Tasks (P2-P4)
- Phase 8: Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Stripe payment gateway
- Refactor PipelineView.jsx (3000+ lines)

## Known Issues
- Universal Key budget can be exceeded during multi-scene generation (10+ scenes)
- User needs to add balance: Profile → Universal Key → Add Balance

## Test Credentials
- Email: test@agentflow.com
- Password: password123
