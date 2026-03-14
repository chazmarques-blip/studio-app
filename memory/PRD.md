# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL)
- **AI Models:**
  - Copy/Art Direction: Claude Sonnet 4.5
  - Speed tasks (reviews, scheduling): Gemini 2.0 Flash
  - Image Generation: **GPT Image 1** (OpenAI)
  - Prompt Engineering: Gemini 2.0 Flash
- **Auth:** JWT-based custom auth

## Implemented Features

### AI Marketing Studio (Phase 7) - COMPLETE
- **Multi-Agent Pipeline:** Sofia (Copy) -> Ana (Copy Review) -> Lucas (Design) -> Rafael (Art Director) -> Pedro (Publisher)
- **Rafael Art Director:** World-class art direction agent
- **Revision Loop:** Ana and Rafael can request up to 2 revisions
- **GPT Image 1:** High-quality images with impactful headlines (3-7 words), language-aware (PT/EN/ES)
- **Platform Mockups:** Content tab shows campaign as it appears on each network
- **Guided Briefing:** Dual-mode (questionnaire + free-form), i18n (PT/EN/ES)
- **Campaign Language Selector:** Headlines and copy respect the selected language
- **Final Preview:** Realistic mockups, text editing, custom image upload, style-based regeneration
- **Asset Management:** Logo gallery, previous briefings, reference images
- **Plan Gating:** Enterprise plan exclusive

### Core Platform
- Dynamic Dashboard with recharts
- Agent Management & Marketplace
- Google Calendar/Sheets Integration (Phase 6)
- Omnichannel UI (mocked integrations)
- Multi-language UI (PT/EN/ES)
- Dark luxury theme (monochrome gold/black/white)

### Bug Fixes (2026-03-14)
- **Delete button fix (FINAL):** Replaced `window.confirm()` (blocked by browser) with inline confirmation UI (checkmark/X buttons). Button now gray by default, red only on hover. Verified working via screenshot testing - campaign successfully deleted with toast notification.

### Campaigns Created
- **My Truck Brokers - Campana Espanol:** Created via full AI pipeline with 3 images, Spanish copy, targeting WhatsApp/Instagram/Facebook.

## Current Status
- **Working:** All features functional. Delete button confirmed working with inline confirmation.
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
- Refactor PipelineView.jsx (1400+ lines) and pipeline.py (1300+ lines)
- Terms of Use / Privacy Policy
- Scalability hardening

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
