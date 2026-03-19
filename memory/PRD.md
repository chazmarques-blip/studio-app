# AgentZZ - PRD (Product Requirements Document)

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

## Completed - March 19, 2026 (Latest Session)

### Dylan Reed v2 - Cinematic Sound Director
- Complete rewrite of system prompt with world-class audio direction knowledge
- Walter Murch's invisible architecture doctrine, Hans Zimmer's emotional scoring
- 3-Act Audio Architecture: Hook (disruption) → Body (escalation) → Payoff (release)
- Whisper-to-authority arc technique with progressive stability
- Punctuation-as-instrument guide (... — ALL CAPS for ElevenLabs control)
- Murch Breathing Room Rule (15-20% silence in narration)
- Cinematic voice settings: stability 0.25-0.35 for dramatic (was 0.70)
- Platform-specific audio mastering rules (TikTok vs YouTube vs WhatsApp)
- Full narration script output with word count limit (65 words max)
- Validated in 3 end-to-end campaigns

### Cinematic Audio Mixing (FFmpeg)
- Sidechain compression: music auto-ducks when narration plays
- EQ carving: -8dB at 400Hz, -4dB at 2.5kHz (voice frequency space)
- Narration processing: highpass 80Hz, presence boost 3kHz, broadcast compressor
- Music processing: exponential fades, sidechain ducking ratio 8:1
- Fallback to basic mix if cinematic filter fails

### AI Image Director v2
- Robust parser with 4 regex patterns (handles Gemini format variations)
- Raw response logging for debugging
- Validated: 5/5 platforms parsed in campaign 3 (was 0 in campaign 2)

### Art Gallery UI
- Fixed player at top, scrollable grid below, 8 channel previews

## Backlog (Priority Order)
### P1
- [ ] Audio Preview in Dylan step
- [ ] Optimized Export Flow
- [ ] Refactor PipelineView.jsx

### P2
- [ ] HeyGen ultra-realistic avatars
- [ ] CRM Kanban, Login Social

### P3
- [ ] Omnichannel, Admin, Payment, Legal

## Credentials
- Email: test@agentflow.com / Password: password123
