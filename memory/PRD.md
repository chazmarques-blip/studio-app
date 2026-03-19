# AgentZZ - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Gemini 3 Pro (image), Gemini 2.5 Flash (vision/critic), Gemini 2.0 Flash (AI Director + Dylan), OpenAI TTS, fal.ai Kling (lip-sync), ElevenLabs TTS
- Video: Sora 2 (via Emergent Integrations)
- Storage: Supabase Storage (pipeline-assets bucket)

## Pipeline Agents (8-step creative pipeline)
| # | Step Key | Agent | Role | Model | Description |
|---|----------|-------|------|-------|-------------|
| 1 | sofia_copy | David | Copywriter | Claude Sonnet 4.5 | Writes campaign copy and video brief |
| 2 | ana_review_copy | Lee | Creative Director | Gemini 2.0 Flash | Reviews and approves copy |
| 3 | lucas_design | Stefan | Visual Designer | Claude Sonnet 4.5 | Generates marketing images |
| 4 | rafael_review_design | George | Art Director | Gemini 2.0 Flash | Reviews and approves design |
| 5 | **dylan_sound** | **Dylan** | **Sound Director** | **Gemini 2.0 Flash** | **Selects voice, music, narration delivery** |
| 6 | marcos_video | Ridley | Video Director | Claude Sonnet 4.5 | Creates video script + generates video |
| 7 | rafael_review_video | Roger | Video Reviewer | Gemini 2.0 Flash | Reviews video quality |
| 8 | pedro_publish | Gary | Campaign Validator | Gemini 2.0 Flash | Final campaign validation |

## Key Features Implemented
- Dashboard with recharts analytics
- Agent Marketplace with plan-gating
- Google Calendar/Sheets integration in Agent Config
- Dual-source avatar generation (photo + video)
- Iterative AI Accuracy Agent
- Real company logo compositing via PIL
- Agent Timeline UI for generation progress
- Voice Mastering, Voice Bank (TTS), Custom Recording
- Avatar Video Preview (5s lip-sync via fal.ai)
- ElevenLabs TTS Integration for video narration
- Per-platform video variants (8+ platforms)
- 14 Image Generation Styles
- Edit Image Text (change headline without regenerating)
- Pipeline auto-recovery for stuck steps
- Art Gallery with Fixed Player + Scrollable Grid
- AI Image Director for smart video cropping per platform
- **Dylan Reed - Sound Director Agent** (NEW)

## Completed - March 19, 2026 (Latest Session)

### Art Gallery UI Rearchitecture
- Redesigned GlobalArtGallery: fixed player top + scrollable thumbnail grid
- 8 channel preview tabs with device mockups
- Action bar: Download, Share, Use in Campaign, Close
- Tested: 15/15 frontend + 15/15 backend (iteration_72)

### AI Image Director (Backend)
- `_ai_analyze_video_for_crops()` using Gemini 2.0 Flash vision
- Smart crop regions per platform from keyframe analysis
- Integrated into `_create_video_variants()` with fallback
- Tested: iteration_72

### Dylan Reed - Sound Director Agent
- New pipeline step: `dylan_sound` (between George and Ridley)
- System prompt with complete ElevenLabs voice catalog (10 voices with characteristics)
- System prompt with complete music library (25 tracks by mood/genre)
- Voice psychology rules (voice type → brand matching)
- Music-brand matching rules (industry → genre)
- Platform-specific audio guidelines (TikTok/IG/YouTube/etc.)
- Structured output: Voice Selection, Voice Settings, Narration Delivery, Music Selection, Music Mix
- `_parse_dylan_audio()` parser in engine.py extracts all settings
- Dylan's output injected into Ridley's prompt as AUDIO DIRECTION
- `_generate_narration()` updated to accept precise voice settings (stability, similarity, style_val, speed)
- Frontend: Headphones icon, #E91E63 color, dynamic timeline rendering
- Tested: 21/21 backend + 5/5 frontend (iteration_73)

## Backlog (Priority Order)
### P0
- [ ] Run full end-to-end campaign to verify Dylan's audio integration
- [ ] Test AI Director with real Sora 2 video generation

### P1 - Features
- [ ] Optimized Export Flow (decouple variant creation)
- [ ] Refactor PipelineView.jsx (~2500 lines)
- [ ] Automated campaign sharing
- [ ] Redesign Landing/Login page

### P2 - Features
- [ ] Ultra-Realistic Avatar (HeyGen)
- [ ] CRM with Kanban board
- [ ] Login Social / Google Auth

### P3 - Future
- [ ] Omnichannel integrations (WhatsApp, SMS, etc.)
- [ ] Admin Management System
- [ ] Payment gateway
- [ ] Legal pages

## Credentials
- Email: test@agentflow.com / Password: password123
