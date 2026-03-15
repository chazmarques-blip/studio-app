# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a mobile-first SaaS platform — an AI-powered marketing agency and customer service automation tool. Complete solution: social media management, content creation, post automation, and omnichannel customer support. "Uma agencia de marketing e atendimento na palma da mao."

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) + MongoDB
- **3rd Party**: Claude Sonnet 4.5, Gemini Flash, Gemini Nano Banana (images), Sora 2 (video), OpenAI TTS, FFmpeg
- **Auth**: Supabase Auth (token key: `agentzz_token`)

## COMPLETED
- [x] Pipeline multi-agente (7 agentes) para criacao de campanhas
- [x] Geracao de copy (3 variacoes), imagens (3 + variantes), video (Sora 2)
- [x] Midia adaptativa: 1:1, 9:16, 16:9 para 8 canais
- [x] Traffic Hub v2 com metricas simuladas e recomendacoes IA
- [x] Edicao de campanhas, regenerar imagens, clonar idioma
- [x] Bug fixes: Sora 2 resolucao, regeneracao de imagem
- [x] **Gerador de Agentes IA com questionario guiado** — 6 secoes colapsaveis: Identidade, Mentalidade, Negocio, Idioma, Comportamento, Escopo, Integracoes
- [x] **Backend assincrono** para geracao (polling pattern evita timeout do proxy)
- [x] **25 avatares humanoides cyberpunk** — meio humano, meio robo, multiracial, futuristas
- [x] **Pagina Agents redesenhada** — Marketplace com grid 2 colunas, filtros, busca, tabs, avatares
- [x] **Icone Marketing na barra de navegacao** — Megaphone entre Agents e CRM

## ROADMAP

### FASE 1 (Atual) — Finalizar Agentes
- [x] 1.1 Gerador de Agentes IA com questionario guiado
- [x] 1.2 Avatares humanoides cyberpunk para 25 agentes
- [x] 1.3 Redesign pagina Agents com avatares e visual high-tech
- [ ] 1.4 Melhorar 25 system prompts (DNA rico por nicho)
- [ ] 1.5 Renomear agente direto na lista
- [ ] 1.6 Sandbox universal (testar qualquer agente sem deploy)

### FASE 2 — Redesign Landing + Identidade
- [ ] 2.1 Redesign pagina Login/Landing — enfatizar agencia marketing + atendimento
- [ ] 2.2 Tres pilares: Criar > Automatizar > Atender
- [ ] 2.3 Gestao de redes sociais, automacao de posts, criacao conteudo IA

### FASE 3 — WhatsApp MVP (Validacao Real)
- [ ] 3.1 Conectar Evolution API (URL + Key + QR Code)
- [ ] 3.2 Webhook de mensagens reais no inbox
- [ ] 3.3 Auto-resposta IA usando system prompt
- [ ] 3.4 Handoff para humano

### FASE 4 — AutoFlow (Automacoes Visuais Mobile-First)
- [ ] 4.1 Motor de automacao backend (triggers, condicoes, acoes)
- [ ] 4.2 Builder visual mobile (cards verticais, timeline)
- [ ] 4.3 Templates prontos por tipo de agente
- [ ] 4.4 Integracoes nativas (Calendar, Sheets, WhatsApp, CRM)

### FASE 5 — Social Publishing
- [ ] 5.1 Publicar/agendar posts Facebook e Instagram
- [ ] 5.2 Calendario editorial mensal
- [ ] 5.3 Automacao de posts com IA

### FASE 6+ — Avancado
- WhatsApp Business Cloud API (Meta Tech Provider)
- Inbox Unificado com WebSockets
- Conversacao IA Avancada (BANT)
- Social Listening
- Rede de Agentes Colaborativos
- Admin Dashboard, Stripe, Mobile App, Legal

## Marketplace Agents (25)
22 business + 3 personal, todos com avatares cyberpunk humanoides

## Credentials
- Email: test@agentflow.com | Password: password123
