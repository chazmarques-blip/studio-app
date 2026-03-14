# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + Supabase Storage (pipeline-assets bucket)
- **AI Models:**
  - Sofia, Ana, Lucas, Rafael, Marcos: Claude Sonnet 4.5 (with Gemini Flash fallback)
  - Pedro (scheduling): Gemini 2.0 Flash (primary)
  - Image Generation: Gemini Nano Banana
  - Video Generation: Sora 2 (12s max, 1280x720 or 720x1280 only)
  - All via emergentintegrations + Emergent LLM Key
- **Auth:** JWT-based custom auth

## AI Agent Pipeline (6 agents)
1. **Sofia** → Copy (3 variations) + IMAGE BRIEFING with explicit language enforcement
2. **Ana** → Reviews copy + briefing alignment + language consistency
3. **Lucas** → Image prompts + Nano Banana generation + CRITICAL LANGUAGE RULE enforced
4. **Rafael** → Reviews images (7 criteria) + AUTOMATIC REJECTION on language mismatch
5. **Marcos** → Video concept (Claude) + Sora 2 generation (12s commercial)
6. **Pedro** → Schedule + strategy (Gemini Flash)

## Language Enforcement (Bug Fix - Mar 14, 2026)
- Sofia: Headlines must be "in the EXACT SAME language as the copy"
- Lucas: CRITICAL LANGUAGE RULE added + lang_instruction injected
- Rafael: Criterion 4 is AUTOMATIC FAIL if headline language != copy language
- Prompt builder: lang_instruction now passed to Lucas and Rafael

## Sora 2 Video Configuration
- Sizes: 1280x720 (landscape), 720x1280 (portrait) — ONLY supported sizes
- Durations: 4, 8, or 12 seconds (12 is max)
- Model: sora-2 (standard)
- Auto-format: vertical for TikTok/Instagram/WhatsApp, horizontal for Google Ads/Facebook

## Implemented Features
- AI Marketing Studio (6-agent pipeline, complete)
- Video Generation (Marcos/Sora 2, complete)
- Dashboard Quick Actions at top of page
- Persistent Supabase Storage for all assets
- 8 platforms: WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS
- Dark luxury theme (monochrome gold)
- Multi-language UI (PT/EN/ES)

## Backlog (Prioritized)
### P1
- Galeria de Criativos (imagens + vídeos)
- Programa de Referral/Embaixador AgentZZ
- App Mobile (Capacitor iOS + Android)

### P2
- Activate live channel integrations
- Refactor pipeline.py into modules

### P3
- Admin Management System
- Payment gateway (Stripe)
- Terms of Use / Privacy Policy

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
