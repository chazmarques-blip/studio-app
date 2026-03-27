# AgentZZ — Product Requirements Document
## Version: 1.0.0 | Updated: 2026-03-27

---

## Original Problem Statement
Comprehensive, mobile-first, no-code SaaS platform "AgentZZ" for deploying AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS) with a Directed Studio for animated content production.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + shadcn/ui + Framer Motion
- **Backend:** FastAPI (Python) + Supabase (PostgreSQL) + MongoDB
- **AI Providers:** Claude 3.5 Sonnet, Gemini (Image/Vision), OpenAI Whisper, ElevenLabs, Sora 2
- **Build:** Craco (CRA with @/ alias support)

## Credentials
- Email: test@agentflow.com | Password: password123

---

## What's Been Implemented

### Core Platform
- Multi-tenant auth system (JWT)
- Agent management (CRUD, marketplace, sandbox)
- Dashboard with recharts analytics
- CRM with Kanban board
- Multi-language UI (PT, EN, ES)
- Dark luxury theme (monochrome gold)
- Bottom navigation with Movie shortcut

### Directed Studio (Complete Pipeline — 6 Steps)
- 6-step production pipeline: Briefing -> Characters -> Storyboard -> **Dialogues** -> Production -> Results
- AI-powered storyboard generation with multi-frame panels
- **Storyboard expandable panels** (collapsed by default, lazy loading)
- **Step 4 — Dialogues/Script Polish (NEW):**
  - Tab DUBLADO: Edit character dialogues per scene + AI generation
  - Tab NARRADO: Edit narrator text per scene + voice selection
  - Tab LIVRO: Edit literary text per scene
  - Character voice assignment per character
  - Auto-save and per-scene AI regeneration
- Continuity Director with user notes
- Smart Editor (inpainting)
- Character avatar system (upload, analyze, zoom)
- Video production (Sora 2)
- Narration (ElevenLabs TTS)
- Post-production audio engineering
- Multi-language dubbing + subtitles
- Export: PDF, Interactive Book (iframe), MP4 video
- Media preview system (Video Modal, PDF Lightbox, Book iframe, Image Gallery)

### Google Integration (Phase 6)
- Google account connection
- Calendar/Sheets selection per agent
- Dynamic connection status

### Infrastructure Refactoring (2026-03-27) - PHASE COMPLETE
- **Error Boundary:** Global catch for component crashes
- **Code Splitting:** React.lazy on ALL 20+ page routes
- **Lazy Loading:** loading="lazy" on ALL img tags across 3 main components
- **PWA:** manifest.json + service-worker.js + SW registration
- **GZip Compression:** FastAPI GZipMiddleware
- **Observability:** Request tracing (X-Request-Id, X-Response-Time)
- **Rate Limiting:** slowapi middleware
- **Auth on Cache Endpoints:** /cache/stats and /cache/flush now require auth
- **Deep Health Check:** /api/health/deep checks Supabase, AI keys, disk, cache
- **Circuit Breaker:** Auto-failover for AI providers (Claude->Gemini)
- **Idempotency Guard:** Prevents duplicate expensive operations
- **Provider Pattern:** Swap AI providers via config (text, image, video, voice, STT)
- **Centralized Config:** /core/config.py with all env vars
- **Error Taxonomy:** Standardized error responses (Stripe-style)
- **API Layer:** Frontend api/client.js + api/studioApi.js
- **Touch Targets:** CSS media query for 44px min (mobile)
- **Storyboard Expandable Panels:** Collapsed by default, expand on click
- **Scripts Cleanup:** 8 dead scripts moved to /scripts/
- **Movie Nav Shortcut:** BottomNav -> /marketing/studio?mode=directed auto-selects Estudio

---

## Backlog (Prioritized)

### P0 — Next Up
- Complete frontend split: PipelineView.jsx (3094 lines -> 6-8 components)
- Complete backend split: studio.py (5268 lines -> 10+ modules)
- Database migration: JSONB -> dedicated tables

### P1 — Important
- Offline Queue (PWA write operations)
- Image optimization (WebP via Supabase transforms)
- Dashboard query optimization (8 -> 2 queries)
- WebSocket/SSE for real-time progress updates

### P2 — Future
- Phase 8: Omnichannel (WhatsApp, SMS, Instagram, Telegram)
- Admin Management System
- Stripe Payment Integration
- Legal & Publication pages
- Capacitor wrapper for App Store/Google Play

---

## Test Reports
- 110-118: Previous iterations (all passed)
- 119: Infrastructure audit (Backend 100%, Frontend 100%)
- 120: Dialogues Step + Expandable Panels (Backend 100%, Frontend 100%)

---

## Technical Debt
- studio.py: 5268 lines (needs splitting)
- PipelineView.jsx: 3094 lines, 76 useState (needs splitting)
- DirectedStudio.jsx: 2531 lines (needs splitting)
- Recharts chart sizing warning (minor)
