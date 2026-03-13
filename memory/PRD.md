# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a mobile-first, no-code SaaS platform called "AgentZZ" for SMBs to deploy AI agents on social channels.

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn-ui, Lucide Icons
- Backend: FastAPI (Python) with background threading
- Database: Supabase (PostgreSQL)
- AI: Claude Sonnet, Gemini Flash, Gemini Nano Banana (via Emergent LLM Key)

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

### Phase 7.3: Pipeline Enhancements (COMPLETE)
- Brand/reference image upload, contact info fields
- Image lightbox + "Pedir Ajuste" regeneration
- Progress timer with estimated time per step
- Campaign auto-save on pipeline completion

### Phase 7.4: Campaign Dashboard (COMPLETE - Mar 2026)
- Enhanced Campaign Cards: dates, channel badges (colored), CPL, preview/detail
- Campaign Detail Modal: 3 tabs (Visao Geral, Conteudo, Resultados)
- Per-channel CPL with progress bars, message flow timeline

### Phase 7.5: Final Preview & Channel Mockups (COMPLETE - Mar 2026)
- **Channel Mockups**: WhatsApp (green chat bubble), Instagram (feed post), Facebook (sponsored post)
- **Channel Selector**: Switch between mockup views per platform
- **Image Selector**: Preview different generated images in each mockup
- **Publish Flow**: "Publicar Campanha" button at the end of the complete flow
- **Complete Pipeline Flow**: Briefing → Creation → Approval → Preview Final → Publish
- Component: /app/frontend/src/components/FinalPreview.jsx

## Key Files
- /app/backend/routers/pipeline.py - Pipeline logic, upload, regenerate
- /app/frontend/src/components/PipelineView.jsx - Pipeline UI
- /app/frontend/src/components/FinalPreview.jsx - Channel mockups
- /app/frontend/src/pages/Marketing.jsx - Campaign dashboard
- /app/frontend/src/pages/MarketingStudio.jsx - Studio page

## Credentials
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Backlog
- P1: Post-generation text editing, bulk download, duplicate pipeline
- P2: Phase 8 Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- P2: Admin Dashboard, Payment Gateway (Stripe), Legal pages
- P3: Real analytics integration, A/B Testing automation

## Notes
- Campaign CPL values are simulated for demo
- Channel integrations are mocked
- Mockups are visual previews (not connected to real channel APIs)
