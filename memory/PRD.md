# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + MongoDB
- **AI Models:**
  - Copy/Art Direction: Claude Sonnet 4.5
  - Speed tasks (reviews, scheduling): Gemini 2.0 Flash
  - Image Generation: **GPT Image 1** (OpenAI) - upgraded from Gemini Nano Banana
  - Prompt Engineering: Gemini 2.0 Flash
- **Auth:** JWT-based custom auth

## Implemented Features

### AI Marketing Studio (Phase 7) - COMPLETE
- **Multi-Agent Pipeline:** Sofia (Copy) → Ana (Copy Review) → Lucas (Design) → Rafael (Art Director) → Pedro (Publisher)
- **Rafael Art Director:** World-class art direction agent with mindsets from Lee Clow, Marcello Serpa, David Droga, George Lois, Helmut Krone, Rob Reilly
- **Revision Loop:** Ana and Rafael can request up to 2 revisions from creators before approving
- **GPT Image 1 Integration:** High-quality image generation with strong instruction following (no text/logos/placeholders)
- **Campaign-Aware Prompts:** Briefing context injected throughout the entire prompt chain for maximum relevance
- **Guided Briefing:** Dual-mode (questionnaire + free-form), i18n (PT/EN/ES)
- **Campaign Language Selector:** Independent of UI language
- **Final Preview:** Realistic mockups for WhatsApp/Instagram/Facebook, text editing, custom image upload, style-based regeneration (8 styles)
- **Asset Management:** Logo gallery, previous briefings, reference images
- **Plan Gating:** Enterprise plan exclusive

### Core Platform
- Dynamic Dashboard with recharts
- Agent Management & Marketplace
- Google Calendar/Sheets Integration (Phase 6)
- Omnichannel UI (mocked integrations)
- Multi-language UI (PT/EN/ES)
- Dark luxury theme (monochrome gold/black/white)

## Current Status
- **Working:** All features above are functional
- **Known Issue:** File uploads use ephemeral storage (/app/backend/uploads/)

## Backlog (Prioritized)
### P1 - Critical
- Migrate file uploads to persistent storage (Supabase Storage)

### P2 - High
- Add TikTok as channel
- Video generation agent (Sora 2)

### P3 - Medium
- Activate live channel integrations (WhatsApp, SMS, Telegram, Instagram, Facebook)
- Admin Management System
- Payment gateway integration

### P4 - Low
- Refactor PipelineView.jsx (1300+ lines) and pipeline.py (1200+ lines)
- Terms of Use / Privacy Policy
- Scalability hardening

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
