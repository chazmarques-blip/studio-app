# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform that allows users (small and medium business owners) to deploy and configure pre-built AI agents on various social media channels and produce AI-powered video content through a Directed Studio.

## Core Features Implemented
- **Directed Studio**: Full video/storybook production pipeline with AI-powered screenwriting, storyboarding, character management, voice narration, and production
- **Character/Avatar System**: Project-isolated character management with global library, context-aware editing (AvatarModal adapts to directed mode), incremental layer editing, 360-degree views
- **Agent Management**: Agent marketplace, customization, Google Calendar/Sheets integration
- **Omnichannel**: Unified inbox structure (WhatsApp, Instagram, Facebook, Telegram, SMS - mocked)
- **CRM**: Built-in CRM with visual Kanban board
- **Multi-language**: UI support for English, Portuguese, Spanish
- **Dark Luxury Theme**: Premium monochrome gold/black/white/gray design

## Recent Changes (March 2026)

### Completed - Session Current
- **Scene Character Editing (Step 1 - Roteiro)**: Users can now edit which characters appear in each scene directly from the script editor. Toggle chips allow selecting/deselecting characters per scene. Characters are displayed as gold chips in view mode. Backend `update-scene` endpoint now accepts `characters_in_scene` field.
  - Files: `DirectedStudio.jsx` (lines 1385, 1427-1458, 1469-1480), `production.py` (line 1025)
  - Testing: iteration_124.json - 100% pass rate

### Completed - Previous Sessions
- Project-Specific Characters (project_avatars isolation)
- localStorage caching for avatar library
- Framer Motion downgrade to 11.18.2 (Safari fix)
- Edit flow fixes (setAiEditLoading, AvatarModal auto-prefill)
- DOM Flickering fix (React.memo, stopped polling in directed mode)
- Apply Default Background endpoint
- Context-Aware 360 Generation (keep_original for non-human chars)
- Incremental Layer Editing (edits apply to latest version)
- Front view + transparent background generation prompts
- Google Integration in Agent Config (Phase 6)

## Pending Verification
- 360-degree view clothing fix (company_uniform -> keep_original) - Code was applied in previous session but needs visual verification

## Backlog (P0-P3)
### P1 - AI Marketing Studio (Phase 7.1 & 7.2)
- Campaign generation UI, backend with MongoDB, campaign library, Enterprise plan gating
- Files: AiMarketingStudio.jsx, Marketing.jsx, marketing.py (all placeholders)

### P2 - Omnichannel Integrations (Phase 8)
- WhatsApp (Evolution API), SMS (Twilio), Instagram, Facebook, Telegram

### P2 - Admin Management System & Stripe
- Admin dashboard, payment gateway

### P3 - Native App Packaging
- Capacitor for iOS/Android

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion 11.18.2, recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB (for new features)
- **3rd Party**: Anthropic Claude 3.5, OpenAI Whisper, Gemini (Image/Vision), ElevenLabs (TTS), Google APIs

## Key Credentials
- Email: test@agentflow.com / Password: password123
- Test project: 1a0779dd0ce7 (ADAO E EVA BIBLIZOO - 15 scenes, 4 characters)
