# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn-ui, Lucide Icons
- **Backend:** FastAPI (Python) with background threading
- **Database:** Supabase (PostgreSQL)
- **3rd Party:** Google API, Anthropic Claude, Gemini Flash, Gemini Nano Banana (via Emergent LLM Key)

## What's Been Implemented

### Phase 1-5: Core Platform (COMPLETE)
- Auth, Dashboard, Marketplace (20+ agents), Agent Config, Chat Omnichannel (mock), CRM Kanban, Leads, Analytics, Settings, Pricing, Multi-language (PT/EN/ES)

### Phase 6: Google Integration (COMPLETE)
- Google OAuth, Calendar/Sheets selection per agent

### Phase 7: AI Marketing Studio (COMPLETE - Mar 2026)
- **Manual Mode**: Chat with 4 AI agents (Sofia, Lucas, Ana, Pedro)
- **Pipeline Mode**: Autonomous multi-agent workflow (Sofia → Ana → Lucas → Ana → Pedro)
- **Real Image Generation**: Gemini Nano Banana with brand identity integration
- **Background Threading**: Long AI tasks in threads to prevent timeouts
- **Multi-Model AI**: Claude (creative), Gemini Flash (reviews), Nano Banana (images)
- **Enterprise Plan Gating**: Paywall at final publish step

### Phase 7.3: Pipeline Enhancements v2 (COMPLETE - Mar 2026)
- **Brand & Reference Image Upload**: Logo and reference images in pipeline briefing
- **Contact Info Fields**: Phone, website, email included in campaign prompts
- **Brand in Image Generation**: Lucas now passes brand name, logo context, and company info to Nano Banana image prompts
- **Image Lightbox**: Full-size image viewer with thumbnails navigation
- **Pedir Ajuste (Request Adjustment)**: Users can request specific changes to any generated design, which regenerates the image via background thread
- **Regenerate Design Endpoint**: POST /api/campaigns/pipeline/{id}/regenerate-design
- **Progress Timer**: Each step shows estimated time remaining with animated progress bar
- **Campaign Auto-Save**: Completed pipelines automatically create a campaign in the campaigns table
- **Preview Completo Tab**: CompletedSummary shows text + images + schedule together in one view
- **Improved Pipeline History**: Cards with thumbnails, status, dates, platforms

## Database Schema
- **campaigns**: id, tenant_id, name, type (ai_pipeline), status, messages, schedule, stats (images array)
- **pipelines**: id, tenant_id, briefing, mode, platforms, status, current_step, steps (JSONB), result (JSONB with context, contact_info, uploaded_assets)
- **creatives**: id, campaign_id, type, content

## Key API Endpoints
- POST /api/campaigns/pipeline - Create pipeline with contact_info, uploaded_assets
- POST /api/campaigns/pipeline/upload - Upload brand logo / reference images
- POST /api/campaigns/pipeline/{id}/regenerate-design - Regenerate with feedback
- POST /api/campaigns/pipeline/{id}/approve - Approve step
- POST /api/campaigns/pipeline/{id}/retry - Retry failed step
- GET /api/campaigns/pipeline/list - List pipelines
- GET /api/campaigns/pipeline/{id} - Get pipeline details

## Credentials
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise

## Backlog
- **P1**: Post-generation text editing, bulk download, duplicate pipeline
- **P2**: Phase 8 Omnichannel (WhatsApp, SMS, Instagram, Facebook, Telegram)
- **P2**: Admin Dashboard, Payment Gateway (Stripe), Legal pages
- **P3**: Scalability, A/B Testing automation
