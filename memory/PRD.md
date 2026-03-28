# AgentZZ - Product Requirements Document

## Original Problem Statement
AgentZZ is a comprehensive, mobile-first, no-code SaaS platform that allows users (small and medium business owners) to deploy and configure pre-built AI agents on various social media channels and produce AI-powered video content through a Directed Studio.

## Core Features Implemented
- **Directed Studio**: Full video/storybook production pipeline with AI-powered screenwriting, storyboarding, character management, voice narration, and production
- **Character/Avatar System**: Project-isolated character management with global library, context-aware editing, incremental layer editing, 360-degree views
- **Scene Character Editing**: Users can edit which characters appear in each scene via toggle chips in the Roteiro (Step 1)
- **Agent Management**: Agent marketplace, customization, Google Calendar/Sheets integration
- **Omnichannel**: Unified inbox structure (WhatsApp, Instagram, Facebook, Telegram, SMS - mocked)
- **CRM**: Built-in CRM with visual Kanban board
- **Multi-language**: UI support for English, Portuguese, Spanish
- **Dark Luxury Theme**: Premium monochrome gold/black/white/gray design

## Recent Changes (March 2026)

### Bug Fix - Toast Error Crash (Session Current)
- **Root Cause**: `toast.error(err.response?.data?.detail)` was passing Pydantic validation error arrays (objects with keys `{type, loc, msg, input, url}`) directly to React/Sonner, causing "Objects are not valid as a React child" crash
- **Fix**: Created `/app/frontend/src/utils/getErrorMsg.js` utility that safely extracts string messages from API error responses. Applied across ALL files (20+ files, 40+ occurrences)
- **Files fixed**: DirectedStudio.jsx, StoryboardEditor.jsx, PipelineView.jsx, AvatarModal.jsx, Login.jsx, Marketing.jsx, Chat.jsx, Profile.jsx, Pricing.jsx, Agents.jsx, AgentBuilder.jsx, ChannelConnection.jsx, UpsellScreen.jsx, AvatarPicker.jsx, AvatarLibraryModal.jsx, ImageLightbox.jsx, CompletedSummary.jsx, ActivePipelineView.jsx, PostProduction.jsx

### Scene Character Editing (Session Current)
- Backend `update-scene` endpoint now accepts `characters_in_scene` field
- Frontend shows toggle chips in scene edit form (Step 1 - Roteiro)
- View mode displays characters as gold chips with Users icon
- Testing: iteration_124.json - 100% pass rate

### Previous Session Completed
- Project-Specific Characters, localStorage caching, Framer Motion fix
- Edit flow fixes, DOM Flickering fix, Apply Default Background
- Context-Aware 360 Generation, Incremental Layer Editing
- Front view + transparent background prompts
- Google Integration in Agent Config (Phase 6)

## Pending Verification
- 360-degree view clothing fix (company_uniform -> keep_original) - needs visual verification

## Backlog (P0-P3)
### P1 - AI Marketing Studio (Phase 7.1 & 7.2)
- Campaign generation UI, backend with MongoDB, Enterprise plan gating

### P2 - Omnichannel Integrations (Phase 8)
- WhatsApp (Evolution API), SMS (Twilio), Instagram, Facebook, Telegram

### P2 - Admin Management System & Stripe

### P3 - Native App Packaging (Capacitor)

## Tech Stack
- **Frontend**: React, Tailwind CSS, shadcn-ui, Lucide Icons, Framer Motion 11.18.2, recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Anthropic Claude 3.5, OpenAI Whisper, Gemini (Image/Vision), ElevenLabs (TTS), Google APIs

## Key Credentials
- Email: test@agentflow.com / Password: password123
- Test project: 1a0779dd0ce7 (ADAO E EVA BIBLIZOO - 15 scenes, 4 characters)
