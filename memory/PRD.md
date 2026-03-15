# AgentZZ - Product Requirements Document

## Original Problem Statement
Build "AgentZZ," a mobile-first SaaS platform — an AI-powered marketing agency and customer service automation tool. "Uma agencia de marketing e atendimento na palma da mao."

## Architecture
- Frontend: React + Tailwind CSS + shadcn-ui + Framer Motion + recharts
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) + MongoDB
- 3rd Party: Claude Sonnet 4.5, Gemini Flash, Gemini Nano Banana, Sora 2, OpenAI TTS, FFmpeg
- Auth: Supabase Auth (token: agentzz_token)

## COMPLETED
- [x] Pipeline multi-agente (7 agentes) para criacao de campanhas
- [x] Geracao copy/imagens/video com midia adaptativa 8 canais
- [x] Traffic Hub v2, edicao campanhas, regenerar imagens, clonar idioma
- [x] Gerador de Agentes IA com questionario guiado (6 secoes: Identidade, Mentalidade, Negocio, Idioma, Comportamento, Escopo, Integracoes)
- [x] Backend assincrono para geracao (polling evita timeout proxy)
- [x] **25 avatares humanoides cyberpunk** meio humano/robo, multiracial
- [x] **Nomes americanos**: Sarah, James, Emily, Ryan, Olivia, Emma, Daniel, Madison, Michael, Ashley, Carlos, Nicole, Tyler, Jessica, Marcus, Chloe, Kevin, Sophia, Ethan, Jasmine, David, Megan + Alex, Luna, Max (pessoais)
- [x] **System prompts ricos** com frameworks profissionais (SPIN, HEART, etc.)
- [x] **Cards compactos** com avatares 36px, botoes menores, layout otimizado
- [x] **Botao Criar Agente com avatar** em vez de icone
- [x] **Marketing na barra de navegacao** (Megaphone entre Agents e CRM)
- [x] **Audio fix**: Corrigido amix com apad/aloop infinito, usando dropout_transition=0 e normalize=0, merge com -map explicito e -shortest

## ROADMAP

### FASE 1 (Atual) — Finalizar Agentes
- [x] 1.1-1.3 Gerador IA, avatares cyberpunk, redesign pagina
- [ ] 1.4 Melhorar 25 system prompts (DNA rico por nicho) — PARCIALMENTE FEITO
- [ ] 1.5 Renomear agente direto na lista
- [ ] 1.6 Sandbox universal (testar qualquer agente sem deploy)

### FASE 2 — Redesign Landing + Identidade
- [ ] 2.1 Redesign Login/Landing — agencia marketing + atendimento
- [ ] 2.2 Tres pilares: Criar > Automatizar > Atender

### FASE 3 — WhatsApp MVP
- [ ] 3.1 Conectar Evolution API (QR Code)
- [ ] 3.2 Webhook mensagens reais
- [ ] 3.3 Auto-resposta IA
- [ ] 3.4 Handoff humano

### FASE 4 — AutoFlow (Automacoes Mobile-First)
- [ ] 4.1 Motor automacao (triggers, condicoes, acoes)
- [ ] 4.2 Builder visual mobile (cards verticais)
- [ ] 4.3 Templates por tipo agente
- [ ] 4.4 Integracoes nativas

### FASE 5+ — Avancado
- Social Publishing, WhatsApp Business Cloud, Inbox Unificado, BANT, Social Listening, Rede Agentes, Admin, Stripe, Mobile App, Legal

## Credentials
- Email: test@agentflow.com | Password: password123
