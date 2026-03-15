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
- VERIFIED: PT briefing + EN campaign → ALL output in English, images show "FRESH ROASTED. SERIOUSLY GOOD."

### Video Generation (FIXED & VERIFIED)
- Root: FFmpeg at `/usr/bin/ffmpeg` doesn't exist → use `imageio_ffmpeg.get_ffmpeg_exe()`
- Root: `text_to_video()` failed silently → split into 3 phases with detailed logging
- Root: FFmpeg shell quotes corrupted filters → converted to subprocess list args
- Root: Invalid Sora 2 size `720x1280` → corrected to `1024x1792`
- VERIFIED: Full video pipeline working (Clip1 6789KB + Clip2 6051KB = 9515KB commercial)

### Pipeline UI Approval Flow (FIXED)
- Added VideoApproval component for `rafael_review_video` step
- Added auto-expand for `rafael_review_video` in waiting_approval state
- Pipeline retry now handles `generating_images` and `generating_video` stuck states
- Orphan pipeline recovery on server restart

### Gary Validator Role (FIXED)
- Changed from Publisher (scheduling) to Campaign Validator (quality gate)
- Updated `_build_prompt` to output validation report + traffic team recommendations

## Full Pipeline Test: "Bean and Brew Coffee"
- Briefing: Portuguese | Campaign Language: English
- David (51s) → Lee (6s) → Stefan (215s) → George (47s) → Ridley (281s) → Roger (13s) → Gary (93s)
- 3 images with English text, video with narration, platform variants for Instagram (1:1) and Google Ads (16:9)
- STATUS: COMPLETED SUCCESSFULLY

## Prioritized Backlog
### P0: Integrate AI in Traffic Hub agents (James/Emily/Ryan/Sarah/Mike)
### P1: Omnichannel integrations, Admin system, Stripe
### P2: Creative gallery, Refactor pipeline.py (~2500 lines), Logo overlay in video
### P3: Mobile app, Legal pages

## Test Reports
- /app/test_reports/iteration_31.json, iteration_32.json (100% pass)

## Credentials
- Email: test@agentflow.com | Password: password123
