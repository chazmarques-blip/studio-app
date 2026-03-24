# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform for managing AI-powered chatbot agents on social media channels. Includes a "Directed Studio Mode" for multi-agent video production using Sora 2.

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts
- **Backend**: FastAPI (Python), ThreadPoolExecutor for parallel processing
- **Database**: Supabase (PostgreSQL) + MongoDB for flexible-schema features

## API Keys Configuration
| Service | Key Type | Env Var | Status |
|---|---|---|---|
| Anthropic (Claude) | DIRECT | ANTHROPIC_API_KEY | Active - No proxy |
| OpenAI (Sora 2, GPT) | DIRECT | OPENAI_API_KEY | Active - No proxy |
| Google (Gemini) | DIRECT | GEMINI_API_KEY | Quota exceeded - needs billing |
| ElevenLabs (Voice) | DIRECT | ELEVENLABS_API_KEY | Active |
| Supabase (DB/Auth) | DIRECT | SUPABASE_URL + keys | Active |
| Google OAuth | DIRECT | GOOGLE_CLIENT_ID + SECRET | Active |
| Emergent (fallback) | PROXY | EMERGENT_LLM_KEY | Backup only |

## Credentials
- Email: test@agentflow.com
- Password: password123

## What's Been Implemented

### Core Platform
- Landing page, Auth (Supabase), Dashboard with recharts
- Agent Management, Agent Marketplace, Agent Configuration
- Google Calendar/Sheets integration in Agent Config
- Multi-language UI (PT/EN/ES), Dark luxury theme

### Directed Studio Mode (Pipeline v3)
- Full parallel multi-agent video production pipeline
- One AI team per scene (Claude Director → Sora 2) running simultaneously
- ElevenLabs voice narration, Global Background Processing UI
- Real-time video previews per scene, Analytics Dashboard

### Mar 24, 2026 — API Migration & Studio Enhancements
- **MIGRATED**: Claude from Emergent proxy → Anthropic API direct
- **MIGRATED**: Sora 2 from Emergent proxy → OpenAI API direct
- **CONFIGURED**: Gemini for direct Google API (needs billing activation)
- **Language Selection**: PT/EN/ES dropdown at project creation
- **Visual Style Selection**: Animation 3D / Cartoon 2D / Anime / Realistic / Watercolor
- **Character Avatar Persistence**: Saved to project, restored on resume
- **Per-Scene Regeneration**: Retry individual failed scenes via API + UI
- **Per-Scene Editing**: Edit title/description/dialogue inline
- **Chunked Screenwriter**: Phase 1 (8 scenes) + Phase 2 (continuation) for reliability
- **Enhanced Prompts**: Rich environmental/cinematic details in Scene Director
- **Sora 2 Retry Logic**: 3 attempts with exponential backoff
- **FFmpeg Compression**: Auto-compress concat video if >45MB
- **Reset/Retry Chat**: Unstick screenwriter with backend endpoints + UI button
- **JSON Repair**: Parser handles truncated JSON + markdown code blocks

## Known Issues
1. Gemini direct key needs billing activation (falls back to Emergent)
2. Sora 2 DirectSora2Client needs production testing (may need API format adjustments)
3. FFmpeg disappears on container restart (auto-install check added)

## Prioritized Backlog
- P1: Test full production pipeline with direct API keys
- P1: Dubbing in another language (ElevenLabs translation)
- P1: Subtitle/SRT generation and overlay
- P2: Phase 8 Omnichannel Integrations
- P3: Admin Management System & Stripe
- P4: Refactor PipelineView.jsx (3000+ lines)
