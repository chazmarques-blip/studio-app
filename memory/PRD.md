# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + Supabase Storage (pipeline-assets bucket)
- **AI Models:**
  - Sofia, Ana, Lucas, Rafael: Claude Sonnet 4.5 (with Gemini Flash fallback)
  - Pedro (scheduling): Gemini 2.0 Flash (primary)
  - Image Generation: Gemini Nano Banana (gemini-3-pro-image-preview)
  - All via emergentintegrations + Emergent LLM Key
- **Auth:** JWT-based custom auth

## Supported Platforms (8 total)
WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS

## AI Agent Pipeline
1. **Sofia** — Claude → Copy (3 variations) + IMAGE BRIEFING + Google Ads expertise
2. **Ana** — Claude → Reviews copy + briefing alignment
3. **Lucas** — Claude → Translates briefing into Nano Banana prompts
4. **Rafael** — Claude → Reviews images (7 criteria)
5. **Pedro** — Gemini Flash → Schedule + Google Ads strategy + LATAM timing + KPIs
- asyncio.wait_for timeout 120s per attempt + Gemini fallback for Claude steps

## Implemented Features

### AI Marketing Studio (Phase 7) - COMPLETE
- Multi-Agent Pipeline with revision loops
- Guided Briefing (questionnaire + free-form), i18n (PT/EN/ES)
- Platform Mockups: Instagram, Facebook, WhatsApp, TikTok, Google Ads (Search + Display)
- Final Preview with style-based regeneration
- Unified "Criar com AI Studio" button
- Delete with inline confirmation

### File Storage - PERSISTENT
- Supabase Storage bucket: `pipeline-assets`
- 67 files migrated, all campaigns/pipelines updated

### Core Platform
- Dynamic Dashboard, Agent Management, Google Calendar/Sheets
- Omnichannel UI, Multi-language (PT/EN/ES), Dark luxury theme

## Backlog (Prioritized)
### P1
- Capacitor mobile app (iOS + Android) for store publishing
- **Programa de Referral / Embaixador AgentZZ:**
  - Todo novo usuário recebe uma campanha pronta da AgentZZ (pré-criada, profissional) pronta para publicar
  - Cada campanha tem uma **tag única do usuário** (link de referral rastreável)
  - Quando o usuário publica a campanha e traz novos assinantes pagantes, ele **ganha créditos** na plataforma
  - Modelo: campanha viral auto-propagável — cada cliente vira promotor da AgentZZ
  - Necessita: sistema de tracking de referral, dashboard de créditos, campanha template da AgentZZ

### P2
- Video generation agent (Sora 2)
- Activate live channel integrations

### P3
- Admin Management System
- Payment gateway (Stripe)
- Terms of Use / Privacy Policy

### P4
- Refactor large files
- Scalability hardening

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
