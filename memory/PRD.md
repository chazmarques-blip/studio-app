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

## Traffic Hub Agents (Distribuicao de Campanhas)
| Agent | Role | Channels |
|-------|------|----------|
| James | Chief Traffic Manager | All |
| Emily | Meta Ads Manager | Instagram, Facebook |
| Ryan | TikTok Ads Manager | TikTok |
| Sarah | Messaging Manager | WhatsApp, Telegram, SMS |
| Mike | Google Ads Manager | Google Ads, Email |

---

## ROADMAP COMPLETO (Aprovado pelo usuario - Mar 15, 2026)

### FASE ATUAL — Funcionalidades do AI Studio (EM ANDAMENTO)
- [x] Pipeline multi-agente com 7 agentes especializados
- [x] Geracao de copy (3 variacoes), imagens (3 + variantes por canal), video (Sora 2)
- [x] Midia adaptativa: 1:1, 9:16, 16:9 para 8 canais
- [x] VideoLightbox para expandir videos em fullscreen
- [x] Enforcement de idioma reforcado (briefing PT -> campanha EN funciona)
- [x] Auto-recovery de pipelines orfaos
- [ ] Edicao de campanhas ja criadas (ajustar textos/imagens)
- [ ] Clonar campanha em outro idioma
- [ ] Traffic Hub funcional (botoes Ativar/Pausar + agentes com analise estrategica)

### FASE 1 — WhatsApp-First Strategy (PROXIMA)
**Prioridade: MAXIMA | Impacto: ALTISSIMO para LATAM**
- [ ] 1.1 WhatsApp Business API Integration (Evolution API / Meta Cloud API)
  - Conexao oficial, webhook tempo real, multiplos numeros
  - Templates pre-aprovados, mensagens de sessao (janela 24h)
  - Suporte a midia: imagens, videos, PDFs, audios, localizacao
- [ ] 1.2 Conversational Commerce Engine
  - Catalogo de produtos na conversa (carrossel)
  - Botoes interativos, listas de opcoes, CTAs com link
  - Menus de autoatendimento conversacional
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
- [ ] 2.1 Conversation Engine Avancado
  - System prompt dinamico: dados do lead + historico + produto + tom + idioma
  - Memoria de longo prazo por lead (todas interacoes, preferencias, objecoes)
  - Deteccao automatica de idioma e adaptacao (PT-BR, EN-US, ES)
  - Guardrails: nunca prometer precos, nunca fechar negocios, apenas qualificar
- [ ] 2.2 Framework BANT Adaptado
  - Budget: perguntas indiretas sobre faixa de investimento
  - Authority: identificar se e decisor
  - Need: mapear dor especifica e urgencia
  - Timeline: quando pretende decidir
  - Score 0-3 por dimensao, qualificado >= 8/12
- [ ] 2.3 Multi-Channel DM Dispatcher
  - Fila unificada de todas as conversas
  - Delay humanizado (30s a 5min, aleatorio)
  - Typing indicator antes da resposta
  - Fallback para humano com contexto completo
- [ ] 2.4 Meeting Scheduler
  - Google Calendar integrado (JA TEMOS a base)
  - Verificar disponibilidade em tempo real
  - Link de agendamento direto na DM
  - Lembretes automaticos 24h e 1h antes

### FASE 3 — Social Listening Light (APIs Oficiais)
**Prioridade: MEDIA | Versao segura sem scraping**
- [ ] 3.1 Stream Listener via APIs Oficiais
  - Meta Graph API (Instagram/Facebook posts publicos)
  - Twitter/X API para monitorar keywords
  - Google Alerts/Mentions como fonte complementar
  - Frequencia configuravel: 5min (premium), 15min (padrao), 1h (basico)
- [ ] 3.2 Intent Detection Engine (NLP com Claude)
  - Classificar: COMPRA_ATIVA, PESQUISA, DOR, RECOMENDACAO, IRRELEVANTE
  - Score de confianca 0-100, acionar acao se >= 70
  - Analise de sentimento + deteccao de girias regionais
  - Modelo customizavel por nicho
- [ ] 3.3 Action Trigger System
  - COMPRA_ATIVA -> DM personalizada imediata
  - PESQUISA -> Comentar com info util + DM follow-up 2h
  - DOR -> Comentar com empatia + solucao sutil via DM
  - Todas as acoes geram lead no CRM com fonte "social listening"
- [ ] 3.4 Keyword & Topic Manager
  - Keywords positivas e negativas
  - Combinacoes booleanas (AND/OR/NOT)
  - Sugestao automatica de novas keywords

### FASE 4 — Rede de Agentes Colaborativos (Sales Team IA)
**Prioridade: MEDIA | Reutiliza arquitetura do pipeline existente**
- [ ] 4.1 Agente Analista
  - Lead scoring avancado (1-10) com 15+ sinais
  - Define estrategia: canal, tom, gatilho da primeira mensagem
  - Segmenta leads em cohorts
- [ ] 4.2 Agente Comunicador
  - Executa conversacao completa via Conversation Engine (Fase 2)
  - Aplica framework BANT naturalmente
  - Transfere ao Closer quando qualificado
- [ ] 4.3 Agente Closer
  - Tecnicas de closing: urgencia, prova social, reciprocidade
  - Tratamento de objecoes
  - Meeting Scheduler integrado
- [ ] 4.4 Orquestrador Central
  - State machine por lead (em qual estagio, qual agente responsavel)
  - Balanceamento de carga entre agentes
  - Fallback para humano se IA nao resolver
  - Dashboard de monitoramento em tempo real

### FASE 5 — Funcionalidades de Suporte
- [ ] Admin Management System
- [ ] Payment Gateway (Stripe)
- [ ] Creative Gallery (reuso de assets)
- [ ] Refatorar pipeline.py (~2500 linhas)
- [ ] Fix logo overlay FFmpeg no video
- [ ] Mobile App (Capacitor)
- [ ] Legal pages (Termos de Uso, Politica de Privacidade)

### DESCARTADO (Risco muito alto)
- ~~Prospeccao Ativa com Browser Agents~~ — Viola TOS das redes, risco de banimento, questoes LGPD/GDPR

---

## Bug Fixes Historico (March 15, 2026)

### Language Mismatch (FIXED)
- lang_instruction movido para topo e fundo de todos os prompts

### Video Generation (FIXED)
- FFmpeg via imageio_ffmpeg, subprocess list args, Sora 2 sizes corrigidos

### Pipeline UI (FIXED)
- VideoApproval, auto-recovery, orphan pipelines

### Gary Validator (FIXED)
- Validador de qualidade (nao publicador)

## VideoLightbox (March 15, 2026 - IMPLEMENTED)
- Modal fullscreen em Marketing.jsx e PipelineView.jsx
- Maximize2 icon on hover, "Expandir" text link

## Test Campaigns
- "Therapeutic & Relaxing Massage" — Pipeline 93501df9, Campaign 8e238aa0 — 9/10 APPROVED

## Test Reports
- iteration_31.json, iteration_32.json, iteration_33.json (100% pass)

## Credentials
- Email: test@agentflow.com | Password: password123
