# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" for managing AI-powered chatbot agents on social media channels with an integrated AI Marketing Studio and Directed Video Production Studio.

## Core Requirements
1. Omnichannel AI chatbot management platform
2. Multi-language support (EN, PT, ES)
3. Agent Marketplace with 20+ pre-built agents
4. Integrated CRM with Kanban board
5. Premium "dark luxury" design (glass-morphism, gold accents)
6. Freemium pricing model with plan-gated features
7. AI Avatar Generator (Cyborg half-human/half-machine)
8. Real-time Google Calendar/Sheets integration
9. AI Marketing Studio with auto pipeline + directed studio mode
10. Directed Video Production Studio with 4 AI Cinema Agents + Multi-Scene Generation

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) for ALL data (tenants.settings JSONB)
- **AI**: Gemini (image gen), Claude Sonnet 4.5 (cinema agents + screenwriter), OpenAI Sora 2 (video gen), OpenAI Whisper (voice)
- **Video**: FFmpeg for multi-scene video concatenation
- **Design**: .glass-card, .btn-gold, dark luxury monochrome theme

## Architecture
- Studio projects stored in `tenants.settings.studio_projects` (Supabase JSONB)
- Background processing with polling for long-running tasks (K8s proxy-safe)
- 4 Cinema Agents run sequentially via Claude, saving progress to Supabase after each
- Video generation via Sora 2 runs as background thread with status polling
- Multi-scene: Each 12s scene gets its own Sora 2 video, then FFmpeg concatenates all

## Completed Features
- Landing page with premium design
- Auth flow (login/signup) with extended profile fields
- Onboarding with language selection + AI Avatar generation
- Dashboard with Quick Actions grid
- Agent Management (marketplace, config, sandbox)
- CRM with Kanban pipeline
- Google Calendar/Sheets integration in Agent Config
- AI Avatar Generator (Gemini cyborg, gallery, download with watermark)
- Settings page with profile management
- Marketing AI Studio - Auto Pipeline (image, video, carousel, avatar modes)
- **Directed Studio Mode v2** — COMPLETE:
  - Interactive Screenwriter Chat (Step 1) - Conversational AI that researches and creates multi-scene screenplays
  - Character & Avatar Management (Step 2) - Link existing avatars to screenplay characters
  - Multi-Scene Production Pipeline (Step 3) - 3 AI Cinema Agents per scene + Sora 2 video generation
    - Dir. Fotografia: visual composition, camera, lighting, Sora 2 prompts
    - Dir. Musical: mood, genre, instruments (once for all scenes)
    - Dir. Audio: sound design per scene
  - Video Concatenation with FFmpeg - Stitches all 12s scene videos into one complete film
  - Results Viewer (Step 4) - Watch complete film + individual scenes with download
  - Project History with auto-resume for in-progress productions
  - Real-time progress tracking (scene-by-scene status with phase indicators)
- Avatar creation/editing tools shared between Auto Pipeline and Directed Studio

## In Progress
- Voice generation with ElevenLabs (needs API key)
- Speech-to-text input via Whisper

## Upcoming Tasks (P1)
- Complete ElevenLabs voice generation integration
- Add speech-to-text (Whisper) for briefing/description input
- Dedicated voice generation area with research agent

## Future Tasks (P2-P4)
- Phase 8: Omnichannel integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Payment Gateway Integration
- Refactor PipelineView.jsx (3000+ lines)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
