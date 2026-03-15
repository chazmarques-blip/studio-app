# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a mobile-first SaaS platform — an AI-powered marketing agency and customer service automation tool. Not just chatbot agents, but a complete solution: social media management, content creation, post automation, and omnichannel customer support. "Uma agencia de marketing e atendimento na palma da mao."

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Claude Sonnet 4.5, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, FFmpeg, PIL/Pillow
- **Auth**: Supabase Auth (token key: `agentzz_token`)

## AI Studio Agents (Campaign Creation Pipeline)
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

## ROADMAP COMPLETO (Atualizado Feb 2026)

### CONCLUIDO
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
- [x] Bug fix: Sora 2 resolucao vertical corrigida (720x1280)
- [x] Bug fix: Regeneracao de imagem e sincronizacao de dados

### FASE ATUAL — Agentes de Atendimento + Gerador IA
- [ ] 1.1 Gerador de Agentes IA com questionario guiado (segmento > objetivo > tom > info negocio > IA gera agente)
- [ ] 1.2 Melhorar 25 system prompts existentes (DNA rico por nicho)
- [ ] 1.3 Renomear agente direto na lista "Meus Agentes"
- [ ] 1.4 Sandbox universal (testar qualquer agente do marketplace sem deploy)

### FASE 2 — Redesign Landing + Identidade
- [ ] 2.1 Redesign pagina de Login/Landing — enfatizar: agencia de marketing + atendimento na palma da mao
- [ ] 2.2 Tres pilares visuais: Criar > Automatizar > Atender
- [ ] 2.3 Mostrar gestao de redes sociais, automacao de posts, criacao de conteudo IA

### FASE 3 — WhatsApp MVP (Validacao Real)
- [ ] 3.1 Conectar Evolution API (URL + API Key + Instancia + QR Code)
- [ ] 3.2 Webhook de mensagens (receber mensagens reais no inbox)
- [ ] 3.3 Auto-resposta IA (agente responde usando system prompt configurado)
- [ ] 3.4 Handoff para humano (operador assume conversa)

### FASE 4 — AutoFlow (Automacoes Visuais Mobile-First)
- [ ] 4.1 Motor de automacao backend (triggers, condicoes, acoes)
- [ ] 4.2 Builder visual mobile (cards verticais, timeline/storyboard)
- [ ] 4.3 Templates prontos por tipo de agente ("Agendar consulta", "Recuperar carrinho", "Pos-venda", "Qualificar lead")
- [ ] 4.4 Integracoes nativas (Google Calendar, Sheets, WhatsApp, CRM interno)
- Inspirado no n8n mas redesenhado para mobile-first (n8n nao e mobile-friendly)

### FASE 5 — Social Publishing + Conteudo
- [ ] 5.1 Publicacao social (agendar/publicar posts no Facebook e Instagram)
- [ ] 5.2 Calendario editorial (visao mensal dos posts agendados)
- [ ] 5.3 Automacao de posts (IA cria + agenda posts automaticamente)

### FASE 6 — WhatsApp Business Cloud API
- [ ] 6.1 Meta Tech Provider + Embedded Signup
- [ ] 6.2 Conversational Commerce Engine (catalogo, botoes, PDF, pagamentos)
- [ ] 6.3 WhatsApp Broadcast & Nurturing (sequencias automaticas)
- [ ] 6.4 WhatsApp CRM Sync bidirecional

### FASE 7 — Conversacao IA Avancada
- [ ] 7.1 Conversation Engine Avancado
- [ ] 7.2 Framework BANT Adaptado
- [ ] 7.3 Multi-Channel DM Dispatcher
- [ ] 7.4 Meeting Scheduler

### FASE 8 — Social Listening
- [ ] 8.1 Stream Listener via APIs Oficiais
- [ ] 8.2 Intent Detection Engine (NLP com Claude)
- [ ] 8.3 Action Trigger System
- [ ] 8.4 Keyword & Topic Manager

### FASE 9 — Rede de Agentes Colaborativos
- [ ] 9.1 Agente Analista
- [ ] 9.2 Agente Comunicador
- [ ] 9.3 Agente Closer
- [ ] 9.4 Orquestrador Central

### FASE 10 — Suporte e Infraestrutura
- [ ] 10.1 Admin Dashboard
- [ ] 10.2 Stripe (pagamentos e planos)
- [ ] 10.3 Creative Gallery
- [ ] 10.4 Mobile App (React Native / PWA)
- [ ] 10.5 Legal (termos de uso, privacidade)
- [ ] 10.6 Refatorar pipeline.py (~2700 linhas)
- [ ] 10.7 FFmpeg logo overlay intermitente (P2)

---

## Marketplace Agents (25 total)
- 22 business agents: Carol (sales), Roberto (support), Ana (scheduling), Lucas (SAC), Marina (onboarding), Sofia (e-commerce), Pedro (e-commerce support), Julia (real estate), Rafael (health scheduling), Camila (health support), Diego (restaurant), Isabela (beauty), Thiago (automotive), Fernanda (education), Gabriel (finance), Larissa (SaaS onboarding), Bruno (telecom), Valentina (travel), Mateus (logistics), Amanda (fitness), Ricardo (legal), Beatriz (events)
- 3 personal agents: Alex (productivity), Luna (wellness), Max (finance)

## Credentials
- Email: test@agentflow.com | Password: password123
