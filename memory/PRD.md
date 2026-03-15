# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a no-code SaaS platform for SMBs to deploy AI agents on social channels. Mobile-first, designed for non-technical users. Features: AI Marketing Studio, Traffic Hub, omnichannel inbox, CRM, admin system, and advanced AI-powered sales automation.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, FFmpeg (via imageio_ffmpeg), PIL/Pillow
- **Auth**: Supabase Auth (token key: `agentzz_token`)

## AI Studio Agents (Pipeline de Criacao de Campanhas)
| Step ID | Agent | Role | Model |
|---------|-------|------|-------|
| sofia_copy | David | Copywriter | Claude Sonnet 4.5 |
| ana_review_copy | Lee | Creative Director | Gemini Flash |
| lucas_design | Stefan | Visual Designer | Claude Sonnet 4.5 |
| rafael_review_design | George | Art Director | Gemini Flash |
| marcos_video | Ridley | Video Director | Claude Sonnet 4.5 |
| rafael_review_video | Roger | Video Reviewer | Gemini Flash |
| pedro_publish | Gary | Campaign Validator | Gemini Flash |

## Traffic Hub Agents (Centro de Comando)
| Agent | Role | Channels |
|-------|------|----------|
| James | Chief Traffic Manager | All |
| Emily | Meta Ads Specialist | Instagram, Facebook |
| Ryan | TikTok Ads Specialist | TikTok |
| Sarah | Messaging Specialist | WhatsApp, Telegram, SMS |
| Mike | Google & Email Specialist | Google Ads, Email |

---

## ROADMAP COMPLETO (Aprovado pelo usuario - Mar 15, 2026)

### FASE ATUAL — AI Studio + Traffic Hub (EM ANDAMENTO)
- [x] Pipeline multi-agente com 7 agentes especializados
- [x] Geracao de copy (3 variacoes), imagens (3 + variantes por canal), video (Sora 2)
- [x] Midia adaptativa: 1:1, 9:16, 16:9 para 8 canais
- [x] VideoLightbox para expandir videos em fullscreen
- [x] Enforcement de idioma reforcado (briefing PT -> campanha EN funciona)
- [x] Auto-recovery de pipelines orfaos
- [x] Traffic Hub v2 redesenhado como centro de comando de performance
- [x] Metricas simuladas por canal + recomendacoes IA por agente especialista
- [x] Botoes Ativar/Pausar funcionais no Traffic Hub
- [x] Filtros por status (Todas/Ativas/Prontas/Rascunho) + filtro por agente
- [ ] Edicao de campanhas ja criadas (ajustar textos/imagens)
- [ ] Clonar campanha em outro idioma

### FASE 1 — WhatsApp-First Strategy (PROXIMA)
**Prioridade: MAXIMA | Impacto: ALTISSIMO para LATAM**
- [ ] 1.1 WhatsApp Business API Integration (Evolution API / Meta Cloud API)
  - Conexao oficial, webhook tempo real, multiplos numeros
  - Templates pre-aprovados, mensagens de sessao (janela 24h)
  - Suporte a midia: imagens, videos, PDFs, audios, localizacao
- [ ] 1.2 Conversational Commerce Engine
  - Catalogo de produtos na conversa (carrossel)
  - Botoes interativos, listas de opcoes, CTAs com link
  - Envio de orcamentos/propostas como PDF dinamico
  - Link de pagamento (Stripe/Pix) direto na conversa
- [ ] 1.3 WhatsApp Broadcast & Nurturing
  - Broadcasts segmentados por tag/score/estagio do funil
  - Sequencias automaticas: Dia 1 (boas-vindas), Dia 3 (case), Dia 7 (oferta), Dia 14 (last call)
  - Gestao de opt-in/opt-out para compliance
  - Metricas: entregues, lidos, respondidos, convertidos
- [ ] 1.4 WhatsApp CRM Sync
  - Bidirecional: toda mensagem registrada na timeline do lead
  - Status (enviada/entregue/lida) em tempo real
  - Contato novo -> lead automatico no CRM
  - Mudanca de estagio no pipeline -> mensagem automatica

### FASE 2 — Conversacao IA com Qualificacao Profunda
**Prioridade: ALTA | Evolucao natural dos agentes existentes**
- [ ] 2.1 Conversation Engine Avancado (system prompt dinamico, memoria longo prazo)
- [ ] 2.2 Framework BANT Adaptado (Budget, Authority, Need, Timeline)
- [ ] 2.3 Multi-Channel DM Dispatcher (fila unificada, delay humanizado)
- [ ] 2.4 Meeting Scheduler (Google Calendar ja integrado)

### FASE 3 — Social Listening Light (APIs Oficiais)
**Prioridade: MEDIA | Versao segura sem scraping**
- [ ] 3.1 Stream Listener via APIs Oficiais (Meta Graph, Twitter/X)
- [ ] 3.2 Intent Detection Engine (NLP com Claude)
- [ ] 3.3 Action Trigger System (DMs automaticas baseadas em intencao)
- [ ] 3.4 Keyword & Topic Manager

### FASE 4 — Rede de Agentes Colaborativos (Sales Team IA)
**Prioridade: MEDIA | Reutiliza arquitetura do pipeline existente**
- [ ] 4.1 Agente Analista (lead scoring avancado)
- [ ] 4.2 Agente Comunicador (conversacao via Conversation Engine)
- [ ] 4.3 Agente Closer (persuasao etica, meeting scheduler)
- [ ] 4.4 Orquestrador Central (state machine, event bus)

### FASE 5 — Funcionalidades de Suporte
- [ ] Admin Management System
- [ ] Payment Gateway (Stripe)
- [ ] Creative Gallery (reuso de assets)
- [ ] Refatorar pipeline.py (~2500 linhas)
- [ ] Fix logo overlay FFmpeg no video
- [ ] Mobile App (Capacitor)
- [ ] Legal pages

### DESCARTADO
- ~~Prospeccao Ativa com Browser Agents~~ — Viola TOS das redes, risco de banimento, questoes LGPD/GDPR

---

## Recent Changes (March 15, 2026)
- Traffic Hub v2: Redesigned as performance command center with simulated metrics
- VideoLightbox: Fullscreen video viewing in Marketing and PipelineView
- Language enforcement: Double reinforcement in prompts (top + bottom)
- New campaign: "Therapeutic & Relaxing Massage" (Pipeline 93501df9, Campaign 8e238aa0, 9/10 APPROVED)

## Test Reports
- iteration_31.json, iteration_32.json, iteration_33.json (100% pass)

## Credentials
- Email: test@agentflow.com | Password: password123
