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
- Channel Mockups: WhatsApp, Instagram, Facebook
- Channel Selector, Image Selector per mockup
- Complete Pipeline Flow: Briefing -> Creation -> Approval -> Preview Final -> Publish

### Phase 7.6: Publish Campaign Fix (COMPLETE - Mar 2026)
- **Bug Fix**: Campaign name field added as first step in pipeline creation
- **Bug Fix**: Fixed campaign auto-creation using correct Supabase columns (goal + metrics JSONB)
- **New Endpoint**: POST /api/campaigns/pipeline/{id}/publish - Creates or activates campaign
- **Frontend**: Publish button calls backend, shows loading state, redirects to /marketing
- **Campaign Name**: Displayed in pipeline header and FinalPreview title
- Test report: /app/test_reports/iteration_22.json (100% pass rate)

## Key Files
- /app/backend/routers/pipeline.py - Pipeline logic, upload, regenerate, publish
- /app/frontend/src/components/PipelineView.jsx - Pipeline UI with campaign name
- /app/frontend/src/components/FinalPreview.jsx - Channel mockups + publish
- /app/frontend/src/pages/Marketing.jsx - Campaign dashboard
- /app/frontend/src/pages/MarketingStudio.jsx - Studio page

## Credentials
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Backlog
- P1: Add TikTok channel (mockup + platform option)
- P1: Video creator agent with Sora 2 integration
- P1: Post-generation text editing, bulk download, duplicate pipeline
- P2: Phase 8 Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram, TikTok)
- P2: Admin Dashboard, Payment Gateway (Stripe), Legal pages
- P3: Real analytics integration, A/B Testing automation
- P3: Refactor PipelineView.jsx (1000+ lines) and pipeline.py (800+ lines) into smaller modules

## Notes
- Campaign CPL values are simulated for demo
- Channel integrations are mocked
- Mockups are visual previews (not connected to real channel APIs)
