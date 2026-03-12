# AgentFlow - PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentFlow". The platform allows small and medium business owners to easily deploy and configure pre-built AI agents on various social media channels (WhatsApp, Instagram, Facebook, Telegram).

## User Persona
- Small and medium business owners
- Non-technical users (no-code platform)
- Need AI chatbot automation across social channels
- Language: System base in English, UI multilingual (Portuguese priority)

## Core Requirements

### 1. Omnichannel AI Agents
- Deploy AI chatbot agents on WhatsApp, Instagram, Facebook Messenger, Telegram
- Unified inbox for all channels
- Pre-built agent marketplace (20+ templates)

### 2. AI Capabilities (Multimodal)
- Text: Claude Sonnet for conversational AI
- Voice: OpenAI Whisper for voice transcription
- Images: Claude Vision for image analysis

### 3. Multi-Agent Orchestration
- Intelligently switch between specialized agents in a conversation
- Agent types: Sales, Support, Scheduling, SAC, Custom

### 4. Multi-Language Support
- System base language: English
- User selects UI language during onboarding
- Agent language: fixed or auto-detect (FastText)

### 5. Freemium Business Model
- FREE: 1 agent, 50 messages/week, 1 channel
- STARTER ($49/mo): 5 agents, 10k messages/month, all channels
- ENTERPRISE: Custom pricing, unlimited

### 6. Integrated CRM
- Visual Kanban board
- AI-powered lead creation and scoring
- Automated stage movement

### 7. Real-Time Sync
- Google Calendar integration
- Google Sheets integration

### 8. Lead Nurturing
- Automated follow-up campaigns
- Abandoned cart recovery

### 9. Design Theme
- "Dark Luxury" - blacks (#0A0A0A), grays (#1A1A1A), gold (#C9A84C)
- Premium, sophisticated UI
- Mobile-first responsive design

## Tech Stack
- Frontend: React, Tailwind CSS, shadcn/ui, Lucide Icons
- Backend: FastAPI (Python), Motor (MongoDB async)
- Database: MongoDB
- AI: Claude Sonnet (Emergent LLM Key), OpenAI Whisper (Emergent LLM Key)
- Auth: JWT-based (to be determined)
- Channels: Evolution API (WhatsApp), Meta Graph API, Telegram Bot API

## Development Phases (75 days)
- Phase 0: Foundation & Setup (5 days)
- Phase 1: WhatsApp + Multi-language (8 days)
- Phase 2: Multimodal AI + Multi-agent (15 days)
- Phase 3: Omnichannel (15 days)
- Phase 4: CRM Kanban with AI (12 days)
- Phase 5: Dashboard + Analytics (8 days)
- Phase 6: Real-time Sync (5 days)
- Phase 7: Lead Nurturing (5 days)
- Phase 8: Final Testing (2 days)

## What's Been Implemented
- [2025-02] Planning documents created (AGENTFLOW_MASTER_COMPLETE.md + supporting docs)
- [2025-02] ASCII mockups created
- [2025-02] Visual mockups v1 generated (superseded)
- [2025-02] Visual mockups v2 generated (dark luxury theme - 8 screens)
- [2025-02] Master plan updated with Freemium model and Multi-language system
- [2025-02] Design System defined (colors, typography, components)

## Current Status
- Phase: Pre-development / Design approval pending
- No functional code developed yet (only boilerplate)
- Waiting for user approval of mockups and updated plan to start Phase 0

## Mockup URLs (Dark Luxury Theme v2)
1. Landing Page: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/b5e73ae160804f6c5d1a0f6d8597d80b4a227f2de04997edb2b64f599a29ab81.png
2. Login/Onboarding: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/54c9be7375014a6752f65b823a070f68b80e211b77c5f895facb272851a83cca.png
3. Dashboard: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/8342fbffd825a36c7704c78242b6f66c4d6caf8929256e6d8e961eb9a92cb52a.png
4. Chat/Inbox: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/fb07afadc2729d95164de59e45f4e8a9a91eecb17173275afc854e8692e1b8e5.png
5. CRM Kanban: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/f85ef003e7d54872542466b127b9da654b29d6d503a3b88b53d048c69524481f.png
6. Marketplace: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/dfef02a96b9bd6e9d248ec50d19b0dff02fb12f632d1990ea500c2b42f246150.png
7. Pricing: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/595c2d153efa15171101b208f8352dd4851b2e5d6272b44a69152e517188f5ab.png
8. Settings/Agent Editor: https://static.prod-images.emergentagent.com/jobs/a2a47944-581c-44db-bd6c-71f836ad88fa/images/dc9a843dbccb56a4821512959dc7544611629fb269bda8e39d65610924e309d7.png

## Prioritized Backlog
- P0: User approval of design + start Phase 0
- P1: Phase 1 (WhatsApp + Multi-language)
- P2: Phase 2 (AI Multimodal + Multi-agent)
- P3+: Phases 3-8
