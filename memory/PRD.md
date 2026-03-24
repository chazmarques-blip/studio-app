# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform for managing AI-powered chatbot agents on social media channels. Includes a "Directed Studio Mode" for multi-agent video production using Sora 2.

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts
- **Backend**: FastAPI (Python), ThreadPoolExecutor for parallel processing
- **Database**: Supabase (PostgreSQL) + MongoDB for flexible-schema features
- **3rd Party**: Anthropic Claude 3.5 Sonnet, OpenAI Sora 2, ElevenLabs, Gemini, Google APIs

## Credentials
- Email: test@agentflow.com
- Password: password123

## What's Been Implemented

### Core Platform
- Landing page, Auth (Supabase), Dashboard with recharts
- Agent Management, Agent Marketplace, Agent Configuration
- Google Calendar/Sheets integration in Agent Config
- Multi-language UI (PT/EN/ES)
- Dark luxury monochrome theme (gold/black/white)

### Directed Studio Mode (Pipeline v3)
- Full parallel multi-agent video production pipeline
- One AI team per scene (Claude Director → Sora 2) running simultaneously
- ElevenLabs voice narration integration
- Global Background Processing UI (StudioProductionContext + floating banner)
- Real-time video previews per scene as they complete
- Analytics Dashboard for pipeline performance

### Phase 7 (Mar 24, 2026) — Studio Enhancements
- **Language Selection**: Dropdown (PT/EN/ES) when creating projects
- **Visual Style Selection**: 5 styles (Animation 3D/Cartoon 2D/Anime/Realistic/Watercolor) 
- **Character Avatar Persistence**: Avatars saved to project, restored on resume
- **Per-Scene Regeneration**: API + UI buttons to retry individual failed scenes
- **Per-Scene Editing**: Edit title/description/dialogue/emotion/camera inline
- **Enhanced Scene Director Prompt**: Rich environmental/atmospheric/cinematic details
- **Enhanced Screenwriter Prompt**: World-building with landscape/weather/atmosphere
- **Sora 2 Retry Logic**: 3 attempts with exponential backoff for disconnects/empty videos
- **FFmpeg Compression**: Auto-compress concat video if >45MB (CRF 28→32)
- **Failed Scenes Summary**: Results view shows which scenes failed with retry buttons

## Known Issues (P0/P1)
1. **Supabase 413 Payload Too Large**: Mitigated with FFmpeg compression, but very long videos (20+ scenes) may still exceed limit
2. **FFmpeg disappears on restart**: Added check before use, but ephemeral container issue persists
3. **Sora 2 API flakiness**: Mitigated with 3 retries, but budget exhaustion can still halt production

## Prioritized Backlog
- P2: Phase 8 Omnichannel Integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- P2: Dubbing in another language (ElevenLabs translation)
- P2: Subtitle/SRT generation and overlay
- P3: Admin Management System
- P3: Stripe payment gateway integration
- P4: Refactor PipelineView.jsx (3000+ lines)
