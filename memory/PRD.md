# Agents - PRD (Product Requirements Document)

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying AI agents on social channels. Key feature: AI Marketing Studio with avatar generation, campaign creation, and multi-format video with AI avatars.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- AI: Gemini 3 Pro (image), Gemini 2.5 Flash (vision/critic), Gemini 2.0 Flash (AI Director + Dylan), OpenAI TTS, fal.ai Kling (lip-sync), ElevenLabs TTS
- Video: Sora 2 (via Emergent Integrations)
- Audio: FFmpeg 7.0.2 (sidechaincompress, EQ, broadcast compressor)
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

## Completed - March 20, 2026

### Avatar in Campaign Assets
- Backend: avatar_url and video_mode now saved in campaign stats when pipeline completes (engine.py)
- Frontend: Avatar displayed in CampaignCard with mini-thumbnail and View Avatar button
- Frontend: Avatar section in CampaignDetail with Presenter badge, View Avatar + Download buttons
- Frontend: Avatar lightbox modal for full-size preview with Copy/Download actions
- Frontend: GlobalArtGallery now includes avatar as asset type with dedicated "Avatares" filter
- Frontend: Avatar badge overlay on gallery thumbnails and player
- Backfill: Existing campaigns updated with avatar data from their pipelines
- i18n: Avatar labels added for PT, EN, ES
- Testing: 12/12 tests passed (iteration_74.json)

### Agents Superhero Campaign (Pipeline ed678011)
- Full pipeline completed: copy, review, design, audio (Dylan), video generation
- 3 images generated with Nano Banana + platform variants
- Avatar: 3D superhero with AgentZZ logo and cape
- Video: Sora 2 clips generated in presenter mode (some retries due to timeouts)
- Campaign saved to DB with avatar_url and video_mode=presenter

## Previous Completions

### Dylan Reed v2 - Cinematic Sound Director
- Complete rewrite of system prompt with world-class audio direction knowledge
- 3-Act Audio Architecture: Hook -> Body -> Payoff
- Cinematic voice settings: stability 0.25-0.35 for dramatic
- Platform-specific audio mastering rules
- Validated in 3+ end-to-end campaigns

### Cinematic Audio Mixing (FFmpeg)
- Sidechain compression: music auto-ducks when narration plays
- EQ carving: -8dB at 400Hz, -4dB at 2.5kHz
- Narration processing: highpass 80Hz, presence boost 3kHz, broadcast compressor

### AI Image Director v2
- Robust parser with 4 regex patterns
- Raw response logging for debugging

### Art Gallery UI
- Fixed player at top, scrollable grid below, channel previews

## Backlog (Priority Order)
### P1
- [ ] Audio Preview in Dylan step (pre-approve before Sora generation)
- [ ] Optimized Export Flow
- [ ] Refactor PipelineView.jsx (break into smaller components)

### P2
- [ ] HeyGen ultra-realistic avatars
- [ ] CRM Kanban, Login Social

### P3
- [ ] Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- [ ] Admin Dashboard
- [ ] Payment Gateway
- [ ] Legal (Terms of Use, Privacy Policy)

## Credentials
- Email: test@agentflow.com / Password: password123
