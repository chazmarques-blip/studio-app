# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a mobile-first, no-code SaaS platform called "AgentZZ" for SMBs to deploy AI agents on social channels.

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn-ui, Lucide Icons
- **Backend:** FastAPI (Python) with background threading
- **Database:** Supabase (PostgreSQL)
- **AI:** Claude Sonnet, Gemini Flash, Gemini Nano Banana (via Emergent LLM Key)

## Implemented Features

### Phase 1-5: Core Platform (COMPLETE)
- Auth, Dashboard, Marketplace (20+ agents), Agent Config, Chat Omnichannel (mock), CRM Kanban, Leads, Analytics, Settings, Pricing, Multi-language

### Phase 6: Google Integration (COMPLETE)
- Google OAuth, Calendar/Sheets selection per agent

### Phase 7: AI Marketing Studio (COMPLETE)
- Manual Mode + Pipeline Mode (Sofia/Ana/Lucas/Ana/Pedro)
- Real Image Generation (Nano Banana) with brand identity
- Background Threading, Multi-Model AI Strategy
- Enterprise Plan Gating at publish step

### Phase 7.3: Pipeline Enhancements (COMPLETE - Mar 2026)
- Brand/reference image upload, contact info fields
- Image lightbox + "Pedir Ajuste" regeneration
- Progress timer with estimated time per step
- Campaign auto-save on pipeline completion
- Preview Completo tab (text + images + schedule)

### Phase 7.4: Campaign Dashboard Overhaul (COMPLETE - Mar 2026)
- **Enhanced Campaign Cards**: Thumbnail, dates (inicio/fim), channel badges (colored), CPL dynamic, preview/detail buttons
- **Campaign Detail Modal**: Full modal with 3 tabs:
  - **Visao Geral**: KPI grid (Enviadas, Entregues, Abertura, Conversao), CPL por Canal with progress bars, Fluxo de Mensagens timeline
  - **Conteudo**: Campaign arts with lightbox, message texts with copy button
  - **Resultados**: Metrics grid, Performance por Canal breakdown with CPL per channel
- **Preview Modal**: Quick view of campaign art + text
- **Channel Color System**: WhatsApp green, Instagram pink, Facebook blue, Telegram blue, Email gold, SMS orange

## Key API Endpoints
- POST /api/campaigns/pipeline - Create pipeline
- POST /api/campaigns/pipeline/upload - Upload assets
- POST /api/campaigns/pipeline/{id}/regenerate-design - Adjust design
- GET /api/campaigns - List campaigns
- GET /api/campaigns/pipeline/list - List pipelines

## Credentials
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Backlog
- **P1**: Post-generation text editing, bulk download, duplicate pipeline
- **P2**: Phase 8 Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- **P2**: Admin Dashboard, Payment Gateway (Stripe), Legal pages
- **P3**: Real analytics integration, A/B Testing automation

## Notes
- Campaign CPL values are currently simulated for demo purposes
- Channel integrations are mocked
- AI insights widget on dashboard is a static placeholder
