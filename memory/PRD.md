# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + Supabase Storage (pipeline-assets bucket)
- **AI Models:**
  - Copy/Art Direction: Claude Sonnet 4.5
  - Speed tasks (reviews, scheduling): Gemini 2.0 Flash
  - Image Generation: **Gemini Nano Banana (gemini-3-pro-image-preview)** — replaced GPT Image 1
  - All via emergentintegrations library with Emergent LLM Key
- **Auth:** JWT-based custom auth

## AI Agent Pipeline (Updated 2026-03-14)

### Agent Roles & Flow
1. **Sofia (Copywriter + Visual Strategist)** — Claude Sonnet → Creates copy (3 variations) AND a detailed IMAGE BRIEFING with visual concepts, headline, color direction, mood
2. **Ana (Creative Director)** — Gemini Flash → Reviews copy quality + image briefing alignment. New: anti-cliché check, CTA per platform, briefing notes
3. **Lucas (Visual Production Director)** — Gemini Flash → Receives Sofia's image briefing, translates into optimized Nano Banana prompts (80-120 words each, with headline text embedded)
4. **Rafael (Art Director)** — Claude Sonnet → Reviews generated images. New: HEADLINE INTEGRATION criterion (readability, impact, language correctness). 7 criteria now (was 6)
5. **Pedro (Publisher)** — Gemini Flash → Creates publishing schedule. New: LATAM regional timing (Brazil, Mexico, Colombia, Argentina, US Hispanic), KPI targets per platform

### Key Changes (2026-03-14)
- Sofia now creates IMAGE BRIEFING alongside copy — no more separate prompt extraction step
- Lucas is a "translator" of Sofia's visual vision into technical prompts
- Removed intermediate Gemini Flash prompt extraction step (was redundant with Lucas's new role)
- Rafael now evaluates headline text quality in images (7th criterion)
- Pedro now has regional LATAM timing data

## File Storage
- **Supabase Storage** bucket: `pipeline-assets` (PUBLIC)
- All images (generated + uploaded) stored persistently
- Frontend uses `resolveImageUrl()` helper for backward compatibility
- Legacy local mount at `/api/uploads` still exists as fallback

## Implemented Features

### AI Marketing Studio (Phase 7) - COMPLETE
- Multi-Agent Pipeline with revision loops
- Guided Briefing (questionnaire + free-form), i18n (PT/EN/ES)
- Platform Mockups for Instagram, WhatsApp, Facebook
- Final Preview with style-based regeneration
- Asset Management (logos, references)
- Plan Gating (Enterprise exclusive)

### Core Platform
- Dynamic Dashboard with recharts
- Agent Management & Marketplace
- Google Calendar/Sheets Integration
- Omnichannel UI (mocked integrations)
- Multi-language UI (PT/EN/ES)
- Dark luxury theme

## Current Status
- **Working:** All features functional. Delete button with inline confirmation.
- **Image Model:** Nano Banana (gemini-3-pro-image-preview) — quality 8-9/10
- **Storage:** Supabase Storage (persistent) — 67 files migrated

## Backlog (Prioritized)
### P2 - High
- Add TikTok as channel
- Video generation agent (Sora 2)

### P3 - Medium
- Activate live channel integrations
- Admin Management System
- Payment gateway

### P4 - Low
- Refactor large files (PipelineView.jsx, pipeline.py)
- Terms of Use / Privacy Policy

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
