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

### Audio Mixing Fix (Critical Bug Fix)
- **Bug 1: Sidechain Inverted** - `[narr][music]sidechaincompress` was compressing NARRATION instead of MUSIC. Fixed to `[music][narr_sc]sidechaincompress` with `asplit` for dual-stream
- **Bug 2: -shortest flag** - Was cutting video prematurely when audio ended. Replaced with explicit `-t {duration}` for exact video length
- **Bug 3: apad=pad_dur** - Was adding X seconds of silence instead of padding TO X seconds. Fixed to `apad=whole_dur`
- **Bug 4: asplit missing** - sidechaincompress consumes its inputs, so narration needed duplication via `asplit=2[narr][narr_sc]`
- Applied to both `_combine_commercial_video()` and `_generate_presenter_video()`
- Added fallback basic mix when cinematic sidechain fails in presenter mode

### Avatar in Campaign Assets
- Backend: avatar_url and video_mode saved in campaign stats when pipeline completes
- Frontend: Avatar in CampaignCard (thumbnail + View Avatar button), CampaignDetail (section + lightbox), GlobalArtGallery (filter + badge)
- Backfill: Existing campaigns updated with avatar data
- Testing: 12/12 tests passed (iteration_74.json)

### New Campaign: "Agents - Super Heroi Apresentador"
- Pipeline: ab592fdc-df4f-41d6-bda5-2bf9d16ca544 (completed)
- Video regenerated with audio fix: 6316KB master + 3 platform variants
- Avatar: 3D superhero with AgentZZ cape
- Mode: presenter
- Platforms: Instagram Reels, TikTok, YouTube Shorts

## Previous Completions
- Dylan Reed v2 - Cinematic Sound Director
- Cinematic Audio Mixing (FFmpeg sidechain + EQ)
- AI Image Director v2 with robust parsing
- Art Gallery UI (fixed player + scrollable grid)

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
