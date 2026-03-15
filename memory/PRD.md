# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a no-code SaaS platform for SMBs to deploy AI agents. Features: AI Marketing Studio with multi-agent pipeline, Traffic Hub for campaign distribution, omnichannel inbox, CRM, admin system.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, FFmpeg (via imageio_ffmpeg), PIL/Pillow
- **Auth**: Supabase Auth (token key: `agentzz_token`)

## AI Studio Agents
| Step ID | Agent | Role | Model |
|---------|-------|------|-------|
| sofia_copy | David | Copywriter | Claude Sonnet 4.5 |
| ana_review_copy | Lee | Creative Director | Gemini Flash |
| lucas_design | Stefan | Visual Designer | Claude Sonnet 4.5 |
| rafael_review_design | George | Art Director | Gemini Flash |
| marcos_video | Ridley | Video Director | Claude Sonnet 4.5 |
| rafael_review_video | Roger | Video Reviewer | Gemini Flash |
| pedro_publish | Gary | Campaign Validator | Gemini Flash |

## Traffic Hub Agents
| Agent | Role | Channels |
|-------|------|----------|
| James | Chief Traffic Manager | All |
| Emily | Meta Ads Manager | Instagram, Facebook |
| Ryan | TikTok Ads Manager | TikTok |
| Sarah | Messaging Manager | WhatsApp, Telegram, SMS |
| Mike | Google Ads Manager | Google Ads, Email |

## Major Bug Fixes (March 15, 2026)

### Language Mismatch (FIXED & VERIFIED)
- Root: `_generate_design_images` read wrong field path for campaign_language
- Root: Lee's prompt didn't receive `lang_instruction`
- Root: Lee confused briefing language with campaign target language
- Fix: All prompts now use `result.campaign_language`, Lee explicitly checks CAMPAIGN_LANGUAGE
- Further strengthened: lang_instruction moved to top of all prompts with double-reinforcement at bottom
- VERIFIED: PT briefing + EN campaign → ALL output in English

### Video Generation (FIXED & VERIFIED)
- Root: FFmpeg at `/usr/bin/ffmpeg` doesn't exist → use `imageio_ffmpeg.get_ffmpeg_exe()`
- Root: `text_to_video()` failed silently → split into 3 phases with detailed logging
- Root: FFmpeg shell quotes corrupted filters → converted to subprocess list args
- Root: Invalid Sora 2 size `720x1280` → corrected to `1024x1792`
- VERIFIED: Full video pipeline working

### Pipeline UI Approval Flow (FIXED)
- Added VideoApproval component for `rafael_review_video` step
- Added auto-expand for `rafael_review_video` in waiting_approval state
- Pipeline retry now handles `generating_images` and `generating_video` stuck states
- Orphan pipeline recovery on server restart

### Gary Validator Role (FIXED)
- Changed from Publisher (scheduling) to Campaign Validator (quality gate)
- Updated `_build_prompt` to output validation report + traffic team recommendations

## VideoLightbox Feature (March 15, 2026) - NEW
- Added VideoLightbox modal overlay to Marketing.jsx and PipelineView.jsx
- Expand button (Maximize2 icon) appears on hover over video containers
- "Expandir" text link also opens lightbox
- Lightbox features: close button, download link, fullscreen video player with autoplay
- Applied to: CampaignDetail content tab, PipelineView StepContent, CompletedSummary (preview & video tabs)

## Full Pipeline Test: "Therapeutic & Relaxing Massage"
- Pipeline ID: 93501df9-b090-455f-8bc5-603952ccfded
- Campaign ID: 8e238aa0-6ae6-4a7f-a044-7846f764a4e7
- Briefing: Portuguese | Campaign Language: English
- Platforms: All 8 (WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS)
- David (48.8s) → Lee (3.5s) → Stefan (21s) → George (4.1s) → Ridley (38s) → Roger (3.4s) → Gary (3.2s)
- 3 images with English text ("Expert Hands. Real Relief."), video with narration (24s horizontal)
- Platform variants: 1:1 (WhatsApp/Instagram/Facebook/Telegram/SMS), 9:16 (TikTok), 16:9 (Email/Google Ads)
- Validation Score: 9/10 - APPROVED
- STATUS: COMPLETED SUCCESSFULLY

## Prioritized Backlog
### P0: Campaign editing (adjust images/texts) + Multi-language cloning
### P1: Integrate AI in Traffic Hub agents (James/Emily/Ryan/Sarah/Mike)
### P2: Omnichannel integrations, Admin system, Stripe
### P3: Creative gallery, Refactor pipeline.py (~2500 lines), Logo overlay in video
### P4: Mobile app, Legal pages

## Test Reports
- /app/test_reports/iteration_31.json, iteration_32.json, iteration_33.json (100% pass)

## Credentials
- Email: test@agentflow.com | Password: password123
