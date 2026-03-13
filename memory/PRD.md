# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Core Requirements
1. **Omnichannel Inbox** - Unified inbox for WhatsApp, Instagram, Facebook Messenger, Telegram, SMS
2. **AI Capabilities** - Claude 3.5 Sonnet (text), OpenAI Whisper (voice), Claude Vision (images), Gemini Nano Banana (image generation)
3. **Multi-Agent Orchestration** - Switch between specialized agents within conversations + Autonomous Campaign Pipeline
4. **Multi-Language** - UI in English, Portuguese, Spanish
5. **Agent Marketplace** - 20+ pre-built, editable agents
6. **Advanced Agent Config** - Personality, knowledge base, post-conversation rules
7. **Real-Time Sync** - Google Calendar & Sheets integration
8. **Lead Nurturing & AI Campaigns** - Automated follow-ups + AI campaign generator (Enterprise)
9. **Integrated CRM** - Visual Kanban board
10. **Dark Luxury Theme** - Monochrome gold, black, white, gray
11. **Freemium Pricing** - Plan-gated features (paywall at publish step)
12. **Admin Dashboard** - Full administrative backend

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn-ui, Lucide Icons
- **Backend:** FastAPI (Python) with background threading for long AI tasks
- **Database:** Supabase (PostgreSQL) for all data
- **3rd Party:** Google API, Anthropic Claude, Gemini Flash, Gemini Nano Banana (via Emergent LLM Key)

## What's Been Implemented

### Phase 1-5: Core Platform (COMPLETE)
- Auth system (JWT + Supabase)
- Onboarding flow
- Dashboard with recharts
- Agent Marketplace (20+ agents + personal agents)
- Agent Configuration (name, prompt, personality, knowledge base, follow-up rules)
- Omnichannel Chat (mocked channels)
- CRM with Kanban board
- Lead Management with AI scoring
- Analytics page
- Settings & Profile
- Pricing & Plan management
- Multi-language support (EN/PT/ES)

### Phase 6: Google Integration (COMPLETE)
- Google OAuth connection
- Calendar selection per agent
- Sheets selection per agent
- Dynamic connection status display

### Phase 7: AI Marketing Studio (COMPLETE - Feb/Mar 2026)
- **Manual Mode**: Chat with 4 specialized AI agents (Sofia, Lucas, Ana, Pedro)
- **Pipeline Mode**: Autonomous multi-agent workflow (Sofia -> Ana -> Lucas -> Ana -> Pedro)
- **Real Image Generation**: Gemini Nano Banana for campaign visuals
- **Background Threading**: Long AI tasks run in threads to prevent server timeouts
- **Multi-Model AI Strategy**: Claude for creative, Gemini Flash for reviews, Nano Banana for images
- **Enterprise Plan Gating**: Paywall at final publish step
- **Creatives Library**: Save/manage AI-generated content

### Phase 7.2: Pipeline Enhancements (COMPLETE - Mar 2026)
- **Brand & Reference Image Upload**: Upload logos and reference images in pipeline briefing
- **Contact Info Fields**: Phone, website, email included in campaign generation prompts
- **Completed Pipeline Summary**: Visual summary with tabs (Copy Final, Images, Schedule)
- **Improved Pipeline History**: Cards with thumbnails, status badges, dates, platform info
- **Download Support**: Direct image download from completed campaigns

## Database Schema
- **users** - Auth & profile data
- **tenants** - Multi-tenant with plan, limits, usage
- **agents** - AI agent configurations with JSONB personality/ai_config
- **agent_knowledge** - Knowledge base items per agent
- **follow_up_rules** - Post-conversation rules
- **conversations** - Chat conversations
- **messages** - Chat messages
- **leads** - CRM leads with AI scoring
- **channels** - Communication channels
- **campaigns** - Marketing campaigns (JSONB metrics)
- **creatives** - AI-generated marketing content
- **pipelines** - Autonomous campaign pipelines with JSONB steps/result

## Credentials
- Email: test@agentflow.com / Password: password123
- Plan: Enterprise (upgraded)

## Backlog (P1/P2)
- **P1: Post-generation editing** - Edit generated text before publishing
- **P1: Download assets** - Bulk download of campaign images and text
- **P1: Duplicate pipeline** - Reuse a briefing as base for new pipeline
- **P2: Phase 8 - Omnichannel** - WhatsApp Evolution API, Twilio SMS, Instagram, Facebook, Telegram
- **P2: Admin Dashboard** - Platform management system
- **P2: Payment Gateway** - Stripe/payment integration
- **P2: Legal** - Terms of Use, Privacy Policy
- **P2: Scalability** - Architecture optimization
