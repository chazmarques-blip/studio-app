# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Core Requirements
1. Omnichannel AI chatbot management platform
2. Multi-language support (EN, PT, ES)
3. Agent Marketplace with 20+ pre-built agents
4. Integrated CRM with Kanban board
5. Premium "dark luxury" design (glass-morphism, gold accents)
6. Freemium pricing model with plan-gated features
7. AI Avatar Generator (Cyborg half-human/half-machine)
8. Real-time Google Calendar/Sheets integration

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Framer Motion, recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **AI**: Gemini (image gen), Claude (text), OpenAI Whisper (voice)
- **Design**: .glass-card, .btn-gold, dark luxury monochrome theme

## Architecture
- Extended profile fields (birth_date, phone, preferred_contact) stored in tenant settings JSONB
- Avatar gallery stored in tenant settings JSONB
- MongoDB used for flexible-schema features (campaigns, creatives)

## Completed Features
- Landing page with premium design
- Auth flow (login/signup) with extended profile fields (birth_date, phone, preferred_contact)
- Onboarding with language selection + AI Avatar generation
- Dashboard with Quick Actions grid
- Agent Management (marketplace, config, sandbox)
- CRM with Kanban pipeline
- Google Calendar/Sheets integration in Agent Config
- AI Avatar Generator (Gemini cyborg generation, gallery, download with watermark)
- Global AppHeader with logo, credits, language selector
- Glass-morphism redesign across all internal pages
- Settings page with "Trocar Foto" overlay on profile photo
- Extended registration fields: birth date, phone, preferred communication (WhatsApp/SMS)

## Pending/In Progress
- Avatar Download button fix (needs verification)
- Avatar Gallery (save all generated avatars to profile) - partially implemented

## Upcoming Tasks (P1)
- Directed Studio Mode Workspace
- Presenter Mode / Lip-Sync (D-ID/HeyGen)

## Future Tasks (P2-P4)
- Phase 8: Omnichannel integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- Admin Management System
- Payment Gateway Integration
- Refactor PipelineView.jsx (3000+ lines)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
