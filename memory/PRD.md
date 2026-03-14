# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + Supabase Storage (pipeline-assets bucket)
- **AI Models:**
  - Sofia, Ana, Lucas, Rafael: Claude Sonnet 4.5 (max quality)
  - Pedro (scheduling): Gemini 2.0 Flash (primary, reliable)
  - All creative steps: Claude with Gemini fallback if 502
  - Image Generation: Gemini Nano Banana (gemini-3-pro-image-preview)
  - All via emergentintegrations library with Emergent LLM Key
- **Auth:** JWT-based custom auth

## AI Agent Pipeline
1. **Sofia** — Claude Sonnet → Copy (3 variations) + IMAGE BRIEFING
2. **Ana** — Claude Sonnet → Reviews copy + briefing alignment
3. **Lucas** — Claude Sonnet → Translates Sofia's briefing into optimized Nano Banana prompts
4. **Rafael** — Claude Sonnet → Reviews images (7 criteria including headline integration)
5. **Pedro** — Gemini Flash → Publishing schedule with LATAM timing + KPIs
- All creative steps have asyncio.wait_for timeout (120s) + Gemini fallback

## File Storage
- Supabase Storage bucket: `pipeline-assets` (PUBLIC, persistent)
- Frontend uses `resolveImageUrl()` helper

## UI Updates (2026-03-14)
- Marketing page: Unified "Criar com AI Studio" button (was 2 separate buttons)
- Delete: Inline confirmation (checkmark/X, no window.confirm)

## Implemented Features
- AI Marketing Studio (Phase 7) — Complete
- Multi-Agent Pipeline with revision loops
- Guided Briefing, i18n, Platform Mockups
- Core Platform (Dashboard, Agents, Google Integration, Omnichannel UI)

## Backlog (Prioritized)
### P1 - High
- Add Google Ads as platform/channel
- Add TikTok as channel

### P2 - Medium
- Video generation agent (Sora 2)
- Activate live channel integrations
- Admin Management System

### P3 - Low
- Payment gateway
- Refactor large files
- Terms of Use / Privacy Policy

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
