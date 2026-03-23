# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts, Lucide Icons
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) — tenants.settings JSONB
- **AI**: Claude Sonnet 4.5 (cinema agents + screenwriter), Sora 2 (video gen), Gemini (image gen), Whisper (voice)
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
  - Interactive Screenwriter Chat (background thread + polling, K8s proxy safe)
  - Character & Avatar Management:
    - Edit character inline (name, description, age, role) + persist to backend
    - Copy character prompt to clipboard (execCommand fallback for iframes)
    - Avatar preview with zoom (modal)
    - AI Edit avatar (create new version via overlay)
    - Edit avatar (open editor)
    - Create new avatar button
  - Multi-Scene Production Pipeline (3 Cinema Agents per scene + Sora 2)
  - FFmpeg video concatenation into complete film
  - Results Viewer with download
  - Project History with auto-resume
  - E2E tested: Abraham & Isaac story (3 scenes, 36s film)

## Key API Endpoints
- POST /api/studio/chat — Screenwriter (background + polling)
- GET /api/studio/projects/{id}/status — Poll status (includes chat_status, chat_history)
- POST /api/studio/projects/{id}/update-characters — Update characters
- POST /api/studio/start-production — Start multi-scene production
- GET /api/studio/projects — List projects
- DELETE /api/studio/projects/{id} — Delete project

## Upcoming Tasks (P1)
- ElevenLabs voice generation for scene narration
- Whisper speech-to-text input
- Story templates (Biblical, Commercial, Documentary, Fiction)

## Future Tasks (P2-P4)
- Phase 8: Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Stripe payment gateway
- Refactor PipelineView.jsx (3000+ lines)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
