# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMB owners to deploy and configure pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS).

## Tech Stack
- **Frontend**: React, TailwindCSS, shadcn/ui, Lucide Icons, i18next (EN/PT/ES)
- **Backend**: FastAPI (Python) — Modular structure: core/ + routers/ + server.py
- **Database**: Supabase (PostgreSQL via REST API) - 9 tables
- **AI**: Claude Sonnet 4.5 + Claude Vision + OpenAI Whisper (via Emergent LLM Key)

## Code Architecture
```
backend/
  server.py          (1403 lines - API routes)
  core/
    deps.py          (62 lines - Supabase, Auth, JWT, helpers)
    models.py        (140 lines - All Pydantic models)
    constants.py     (36 lines - 22 marketplace agents + categories)
  routers/           (ready for future extraction)
  tests/
frontend/src/
  pages/ (19 pages)
  components/layout/ (AppLayout, BottomNav)
  contexts/ (AuthContext)
  locales/ (en.json, pt.json, es.json)
```

## Completed Phases

### Phase 0: Foundation ✅
### Phase 1: Messaging, AI & Agent Config ✅
### Phase 2: Multimodal + WhatsApp + Orchestration ✅ - March 2026
- WhatsApp (Evolution API), Multimodal UI (Vision + Whisper), Multi-Agent Orchestration
- 22 Agent Prompts with professional protocols
- Rebranding AgentFlow → AgentZZ with custom logo
- Social media SVG icons in gold, "Made with Emergent" badge removed
- Backend refactoring: extracted core/deps.py, core/models.py, core/constants.py

### Testing (ALL 100%)
- iteration_2-8: All passed 100%

## Upcoming Tasks (Inverted Planning)
1. **Phase 3: Omnichannel** (Instagram, Facebook, Telegram)
2. **Phase 4: CRM Kanban with AI**
3. **Phase 5: Dashboard & Analytics**
4. **Phase 6: Google Calendar/Sheets**
5. **Phase 7: Lead Nurturing**

## Later (End)
- SMS Integration (Twilio)
- WhatsApp Real Connection (when domain available)
- Final Testing

## Test Credentials
- Email: test@agentflow.com / Password: password123
