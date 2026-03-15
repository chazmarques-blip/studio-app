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

### Language Mismatch Fix
- Root: `_generate_design_images` read wrong path for campaign_language (was `None` → fallback `pt`)
- Root: Lee's prompt didn't receive `lang_instruction` → confused briefing language with target language
- Fix: Corrected field path to `result.campaign_language`, added explicit lang instruction to ALL agent prompts
- Verified: PT briefing + EN campaign → ALL output in English ✅

### Video Generation Fix  
- Root: FFmpeg at `/usr/bin/ffmpeg` doesn't exist, real path via `imageio_ffmpeg.get_ffmpeg_exe()`
- Root: `text_to_video()` failed silently, split into 3 phases (generate→poll→download) with logging
- Root: FFmpeg shell quotes corrupted filter expressions, converted to subprocess list args
- Root: Invalid Sora 2 size `720x1280` → corrected to `1024x1792`
- Verified: Full video generation pipeline working (9515KB commercial) ✅

### Gary Validator Role Fix
- Changed Gary from Publisher (scheduling) to Campaign Validator (quality gate)
- Updated `_build_prompt` to request validation report + traffic team recommendations

## What's Implemented
- Full AI Studio pipeline (7 agents) with robust revision loops (max 1)
- Adaptive media formats: PIL resizes for TikTok (9:16), Google Ads (16:9)
- Traffic Hub with 5 specialized agents
- Orphan pipeline recovery on server restart
- 25 real music tracks, enhanced questionnaire
- Full i18n (EN/PT/ES), dark luxury theme

## Prioritized Backlog
### P0: Integrate AI in Traffic Hub agents
### P1: Omnichannel integrations, Admin system, Stripe
### P2: Creative gallery, Refactor pipeline.py (~2500 lines)
### P3: Mobile app, Legal pages

## Test Reports
- /app/test_reports/iteration_31.json, iteration_32.json (100% pass)

## Credentials
- Email: test@agentflow.com | Password: password123
