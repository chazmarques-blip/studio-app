# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Core Requirements
1. **Omnichannel Inbox** - Unified inbox for WhatsApp, Instagram, Facebook Messenger, Telegram, SMS
2. **AI Capabilities** - Claude 3.5 Sonnet (text), OpenAI Whisper (voice), Claude Vision (images)
3. **Multi-Agent Orchestration** - Switch between specialized agents within conversations
4. **Multi-Language** - UI in English, Portuguese, Spanish
5. **Agent Marketplace** - 20+ pre-built, editable agents
6. **Advanced Agent Config** - Personality, knowledge base, post-conversation rules
7. **Real-Time Sync** - Google Calendar & Sheets integration
8. **Lead Nurturing & AI Campaigns** - Automated follow-ups + AI campaign generator (Enterprise)
9. **Integrated CRM** - Visual Kanban board
10. **Dark Luxury Theme** - Monochrome gold, black, white, gray
11. **Freemium Pricing** - Plan-gated features
12. **Admin Dashboard** - Full administrative backend

## Tech Stack
- **Frontend:** React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) for all data
- **3rd Party:** Google API, Anthropic Claude, OpenAI Whisper (via Emergent LLM Key)

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

### Phase 7: AI Marketing Studio (COMPLETE - Feb 2026)
- **Marketing Campaign Hub** (`/marketing`): Full CRUD for campaigns, stats dashboard, templates, filters
- **AI Marketing Studio** (`/marketing/studio`): 4 specialized AI agents (Sofia Copywriter, Lucas Designer, Ana Reviewer, Pedro Publisher) powered by Claude AI
- **Enterprise Plan Gating**: Studio restricted to Enterprise plan users
- **Creatives Library**: Save/manage AI-generated content
- **Seed Data**: Demo campaigns for AgentZZ company
- **Database**: All stored in Supabase (campaigns + creatives tables with JSONB metrics)

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
- **campaigns** - Marketing campaigns (JSONB metrics for stats/messages/schedule)
- **creatives** - AI-generated marketing content

## Credentials
- Email: test@agentflow.com / Password: password123
- Plan: Enterprise (upgraded)

## Backlog (P1/P2)
- **Phase 8**: Omnichannel Integrations (WhatsApp Evolution API, Twilio SMS, Instagram, Facebook, Telegram)
- **Admin Dashboard**: Platform management system
- **Payment Gateway**: Stripe/payment integration
- **Legal**: Terms of Use, Privacy Policy
- **Scalability**: Architecture optimization for high-volume
