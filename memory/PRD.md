# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a no-code SaaS platform for SMBs to deploy AI agents on social channels. Mobile-first, designed for non-technical users.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, FFmpeg, PIL/Pillow
- **Auth**: Supabase Auth (token key: `agentzz_token`)

## AI Studio Agents
| Step ID | Agent | Role | Model |
|---------|-------|------|-------|
| sofia_copy | David | Copywriter | Claude Sonnet 4.5 |
| ana_review_copy | Lee | Creative Director | Gemini Flash |
| lucas_design | Stefan | Visual Designer | Claude Sonnet 4.5 |
| rafael_review_design | George | Art Director | Gemini Flash |
| marcos_video | Ridley | Video Director | Claude Sonnet 4.5 |
| rafael_review_video | Roger | Video Reviewer | Gemini Flash |
| pedro_publish | Gary | Campaign Validator | Gemini Flash |

## Traffic Hub Agents
| Agent | Role | Channels |
|-------|------|----------|
| James | Chief Traffic Manager | All |
| Emily | Meta Ads Specialist | Instagram, Facebook |
| Ryan | TikTok Ads Specialist | TikTok |
| Sarah | Messaging Specialist | WhatsApp, Telegram, SMS |
| Mike | Google & Email Specialist | Google Ads, Email |

---

## ROADMAP COMPLETO (Mar 15, 2026)

### FASE ATUAL — AI Studio + Traffic Hub (CONCLUIDA)
- [x] Pipeline multi-agente com 7 agentes especializados
- [x] Geracao de copy (3 variacoes), imagens (3 + variantes por canal), video (Sora 2)
- [x] Midia adaptativa: 1:1, 9:16, 16:9 para 8 canais
- [x] VideoLightbox para expandir videos em fullscreen
- [x] Enforcement de idioma reforcado
- [x] Auto-recovery de pipelines orfaos
- [x] Traffic Hub v2 — centro de comando de performance com metricas simuladas
- [x] Edicao de campanhas — editar copy text inline com save/cancel
- [x] Regenerar imagens — pedir ajuste com feedback especifico
- [x] Clonar campanha em outro idioma — botao com 6 idiomas (PT/EN/ES/FR/DE/IT)

### FASE 1 — WhatsApp-First Strategy (PROXIMA)
- [ ] 1.1 WhatsApp Business API (Evolution API / Meta Cloud API)
- [ ] 1.2 Conversational Commerce Engine (catalogo, botoes, PDF, pagamentos)
- [ ] 1.3 WhatsApp Broadcast & Nurturing (sequencias automaticas)
- [ ] 1.4 WhatsApp CRM Sync (bidirecional)

### FASE 2 — Conversacao IA com Qualificacao Profunda
- [ ] 2.1 Conversation Engine Avancado
- [ ] 2.2 Framework BANT Adaptado
- [ ] 2.3 Multi-Channel DM Dispatcher
- [ ] 2.4 Meeting Scheduler

### FASE 3 — Social Listening Light (APIs Oficiais)
- [ ] 3.1 Stream Listener via APIs Oficiais
- [ ] 3.2 Intent Detection Engine (NLP com Claude)
- [ ] 3.3 Action Trigger System
- [ ] 3.4 Keyword & Topic Manager

### FASE 4 — Rede de Agentes Colaborativos
- [ ] 4.1 Agente Analista
- [ ] 4.2 Agente Comunicador
- [ ] 4.3 Agente Closer
- [ ] 4.4 Orquestrador Central

### FASE 5 — Suporte
- [ ] Admin, Stripe, Creative Gallery, Mobile App, Legal, Refatorar pipeline.py

---

## API Endpoints (Campaign Editing - NEW)
- `PUT /api/campaigns/pipeline/{id}/update-copy` — Atualiza texto do copy
- `POST /api/campaigns/pipeline/{id}/regenerate-image` — Regenera imagem com feedback
- `POST /api/campaigns/pipeline/{id}/clone-language` — Clona pipeline em outro idioma

## Test Campaigns
- "Therapeutic & Relaxing Massage" (EN) — Pipeline 93501df9, Campaign 8e238aa0
- "Therapeutic & Relaxing Massage (Portuguese)" — Pipeline 7babc3c8 (clonado automaticamente)

## Test Reports
- iteration_31-34.json (all 100% pass)

## Credentials
- Email: test@agentflow.com | Password: password123
