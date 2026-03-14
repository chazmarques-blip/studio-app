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
- Auth, Dashboard, Marketplace (20+ agents), Agent Config, Chat Omnichannel (mock), CRM Kanban, Leads, Analytics, Settings, Pricing, Multi-language (PT/EN/ES)

### Phase 6: Google Integration (COMPLETE)
- Google OAuth, Calendar/Sheets selection per agent

### Phase 7: AI Marketing Studio (COMPLETE)
- **Simplified Flow**: No Manual/Pipeline tabs - direct "Nova Campanha" flow
- **Pipeline**: Sofia (Claude) -> Ana (Gemini Flash) -> Lucas (Gemini Flash + Nano Banana) -> Ana -> Pedro
- **Guided Questionnaire**: 8-question professional questionnaire as alternative to free briefing
- **Campaign Language Selector**: Generate content in any language (PT, EN, ES, FR, Haitian Creole, custom)
- **i18n Support**: All studio labels/buttons follow user's language setting
- **Image Generation**: Nano Banana with 3x retry and clean prompts (no logo embedding)
- **Final Preview**: Channel-specific mockups (WhatsApp, Instagram, Facebook) with dynamic brand name/logo
- **Text Editing**: Edit campaign text before publishing with save/cancel
- **Custom Image Upload**: Upload own images alongside AI-generated ones
- **Campaign Publishing**: Real backend endpoint creates/updates campaign in DB, redirects to dashboard
- **Pipeline Management**: Archive old pipelines, campaign name as first field

### Campaign Dashboard (COMPLETE)
- Enhanced campaign cards with dates, channel badges, CPL
- Campaign Detail modal with 3 tabs (Overview, Content, Results)
- Clean text display (no raw markdown labels)

## Key Files
- /app/backend/routers/pipeline.py - Pipeline logic, AI agents, publish, archive
- /app/frontend/src/components/PipelineView.jsx - Pipeline creation with questionnaire + language
- /app/frontend/src/components/FinalPreview.jsx - Channel mockups, text edit, image upload, publish
- /app/frontend/src/pages/MarketingStudio.jsx - Simplified studio (direct to pipeline)
- /app/frontend/src/pages/Marketing.jsx - Campaign dashboard

## Credentials
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Backlog
- P1: Add TikTok channel (mockup + platform option)
- P1: Video creator agent with Sora 2 integration
- P2: Phase 8 Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram, TikTok)
- P2: Admin Dashboard, Payment Gateway (Stripe), Legal pages
- P3: Refactor PipelineView.jsx (1000+ lines) and pipeline.py (800+ lines) into smaller modules
- P3: Real analytics, A/B Testing

## Notes
- Campaign CPL values are simulated for demo
- Channel integrations are mocked
- Mockups are visual previews (not connected to real channel APIs)
- AI cannot embed real logos into generated images - logos are shown in mockup chrome instead
