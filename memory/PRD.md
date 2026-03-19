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
| # | Step Key | Agent | Role | Model |
|---|----------|-------|------|-------|
| 1 | sofia_copy | David | Copywriter | Claude Sonnet 4.5 |
| 2 | ana_review_copy | Lee | Creative Director | Gemini 2.0 Flash |
| 3 | lucas_design | Stefan | Visual Designer | Claude Sonnet 4.5 |
| 4 | rafael_review_design | George | Art Director | Gemini 2.0 Flash |
| 5 | dylan_sound | Dylan | Sound Director | Gemini 2.0 Flash |
| 6 | marcos_video | Ridley | Video Director | Claude Sonnet 4.5 |
| 7 | rafael_review_video | Roger | Video Reviewer | Gemini 2.0 Flash |
| 8 | pedro_publish | Gary | Campaign Validator | Gemini 2.0 Flash |

## Validated End-to-End (March 19, 2026)
Campaign "AgentZZ - IA que Vende" ran through all 8 steps:
- Dylan selected Liam (ElevenLabs TX3LPaxmHKxFdv7VOQHJ), stability 0.70, energetic music
- Ridley followed Dylan's direction exactly (same voice ID, music, narration script)
- ElevenLabs TTS generated 270KB narration with Liam voice
- Sora 2 generated 2 clips (5.2MB + 5.5MB)
- AI Director analyzed 3 keyframes → smart crops for 6 platforms
- 6 AI-directed video variants generated (all _ai.mp4 suffix)
- Pipeline ID: 4d7ac1f5-11ea-4ea5-b932-7704906a8243

## Key Features Implemented
- Dashboard with recharts analytics
- Agent Marketplace with plan-gating
- Google Calendar/Sheets integration
- Dual-source avatar generation (photo + video)
- Iterative AI Accuracy Agent
- Voice Mastering, Voice Bank, Custom Recording
- Avatar Video Preview (5s lip-sync via fal.ai)
- ElevenLabs TTS Integration
- Per-platform video variants (8+ platforms)
- 14 Image Generation Styles
- Pipeline auto-recovery
- Art Gallery with Fixed Player + Scrollable Grid
- AI Image Director (vision-based smart crops)
- Dylan Reed - Sound Director Agent

## Backlog (Priority Order)
### P1 - Features
- [ ] Optimized Export Flow (decouple variant creation)
- [ ] Audio Preview in Dylan step (hear voice+music before video generation)
- [ ] Refactor PipelineView.jsx (~2500 lines)
- [ ] Automated campaign sharing

### P2 - Features
- [ ] Ultra-Realistic Avatar (HeyGen)
- [ ] CRM with Kanban board
- [ ] Login Social / Google Auth
- [ ] Redesign Landing/Login page

### P3 - Future
- [ ] Omnichannel integrations (WhatsApp, SMS, etc.)
- [ ] Admin Management System
- [ ] Payment gateway
- [ ] Legal pages

## Credentials
- Email: test@agentflow.com / Password: password123
