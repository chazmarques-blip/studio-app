# 🤖 AGENTFLOW - PLANEJAMENTO EXECUTIVO MVP
## Redetalhamento Pragmático e Executável

---

## 📋 VISÃO GERAL

**O que é:** SaaS mobile-first de agentes de IA para atendimento no WhatsApp com orquestração multi-agente e handoff humano.

**Stack Definitiva (Adaptada):**
- ✅ **Frontend:** React 19 + CRA + Tailwind CSS + shadcn/ui (já configurado)
- ✅ **Backend:** FastAPI + Python (já configurado)
- ✅ **Banco Principal:** MongoDB (já rodando local)
- 🆕 **Supabase:** Auth + Realtime subscriptions + Storage de arquivos
- 🆕 **Railway:** Evolution API v2 + Redis (fila de mensagens) + n8n (orquestração)
- 🆕 **IA:** Anthropic Claude 3.5 Sonnet (via SDK Python)
- 🆕 **Deploy:** Vercel (frontend) + Railway (backend + serviços)

**Diferencial do Original:**
- Mantém React CRA ao invés de migrar para Next.js (menos complexidade)
- MongoDB continua como banco principal (dados já modelados)
- Supabase complementa: auth + realtime (websockets)
- Arquitetura híbrida: melhor dos dois mundos

---

## 🎯 FASES DE EXECUÇÃO (4 FASES - ~40 dias)

### **FASE 1: FUNDAÇÃO + WHATSAPP CONECTADO (7-10 dias)**
**Meta:** Receber mensagens do WhatsApp e salvar no banco

**Componentes:**
1. **Schema MongoDB atualizado:**
   ```
   - tenants (empresas)
   - conversations (conversas do WhatsApp)
   - messages (mensagens individuais)
   - agents (configuração dos agentes IA)
   - handovers (transferências para humano)
   ```

2. **Evolution API v2 no Railway:**
   - Deploy via Docker no Railway
   - Conectar WhatsApp via QR Code
   - Configurar webhook para receber mensagens
   - Endpoint: POST /webhook/evolution → salva no MongoDB

3. **Backend FastAPI:**
   - Endpoint `/api/webhooks/evolution` (recebe mensagens)
   - Endpoint `/api/conversations` (lista conversas)
   - Endpoint `/api/messages/:id` (mensagens de uma conversa)
   - Modelos Pydantic para validação

4. **Frontend básico:**
   - Página de login (Supabase Auth)
   - Lista de conversas (inbox)
   - Visualização de chat simples

**Entregável:** Mensagem enviada no WhatsApp aparece no app web em tempo real.

**Critério de Sucesso:** 
✅ WhatsApp conectado  
✅ Webhook recebendo mensagens  
✅ Conversas aparecem no frontend  

---

### **FASE 2: INTELIGÊNCIA ARTIFICIAL (10-12 dias)**
**Meta:** Claude respondendo automaticamente no WhatsApp

**Componentes:**
1. **Integração Claude API:**
   - SDK Anthropic no backend
   - Wrapper para chamadas (retry, error handling)
   - Sistema de prompts configurável
   - Tool Use: `escalate_to_human`, `update_context`

2. **Agent Processor (FastAPI):**
   ```python
   POST /api/agents/process
   - Recebe message_id
   - Busca histórico (últimas 10 msgs)
   - Monta prompt com contexto
   - Chama Claude API
   - Salva resposta no banco
   - Envia via Evolution API
   ```

3. **3 Agentes Pré-configurados:**
   - **SAC (Triagem):** Acolhe, coleta nome, identifica intenção
   - **Vendas:** Recomenda produtos, contorna objeções
   - **Suporte:** Resolve problemas técnicos

4. **Redis + Fila:**
   - Mensagens entram em fila (evita processamento duplicado)
   - Worker processa fila → chama Agent Processor

5. **Frontend - AgentBuilder:**
   - Form para criar/editar agente
   - Campos: nome, tipo, prompt_sistema, temperature
   - Toggle ativo/inativo

**Entregável:** Cliente envia mensagem → Agente IA responde em < 5s.

**Critério de Sucesso:**
✅ Claude respondendo corretamente  
✅ Contexto preservado (cliente não repete dados)  
✅ Custo por mensagem rastreado  

---

### **FASE 3: ORQUESTRAÇÃO + HANDOFF HUMANO (10-12 dias)**
**Meta:** Multi-agente + transferência para atendente humano

**Componentes:**
1. **Orquestração Multi-Agente:**
   - Campo `current_agent_id` em conversations
   - Tool Use: `switch_agent(agent_type, reason)`
   - Transições: SAC → Vendas → Suporte → Humano
   - Contexto preservado entre transições

2. **Handoff para Humano:**
   - Tool Use: `escalate_to_human(reason, priority)`
   - Status: `bot` | `waiting` | `human` | `resolved`
   - Notificação para operador (Supabase Realtime)

3. **Supabase Realtime:**
   - Subscriptions em `conversations` e `messages`
   - Frontend atualiza em tempo real (sem polling)
   - Operador vê digitação do cliente instantaneamente

4. **Detecção de Digitação:**
   - Evolution API emite `TYPING_INDICATOR` webhook
   - Salva `is_typing: true` no banco
   - **PAUSA fila do agente IA** enquanto humano digita
   - Frontend mostra "digitando..." no chat

5. **Frontend - HandoffBanner:**
   ```jsx
   // Banner vermelho no topo quando status = 'waiting'
   <HandoffBanner>
     Cliente aguardando atendimento humano
     [Assumir Conversa] [Devolver ao Bot]
   </HandoffBanner>
   ```

6. **Frontend - Inbox Operador:**
   - Lista conversas ativas vs aguardando
   - Filtros: bot | humano | urgente
   - Badge com contador de mensagens não lidas

**Entregável:** Agente identifica urgência → escala para humano → operador assume em tempo real.

**Critério de Sucesso:**
✅ Transição entre agentes funciona  
✅ Handoff notifica operador  
✅ Operador responde e bot pausa  
✅ Realtime sem delay perceptível  

---

### **FASE 4: DASHBOARD MOBILE + ANALYTICS (8-10 dias)**
**Meta:** Interface mobile completa e métricas de uso

**Componentes:**
1. **Bottom Navigation (4 tabs):**
   - 💬 **Chat:** Inbox de conversas (badge com contador)
   - 🤖 **Agentes:** Gestão de agentes (criar, editar, ativar)
   - 📊 **Analytics:** Métricas e gráficos
   - ⚙️ **Config:** Conta, integrações, plano

2. **Tela /chat:**
   - ConversationList: avatar, status dot, preview msg, timestamp
   - ChatView: bubbles coloridos (user/agent/human)
   - TypingIndicator: 3 pontos animados
   - HandoffBanner integrado
   - Input com Send button

3. **Tela /agents:**
   - AgentCard: nome, tipo, status, msgs hoje
   - AgentBuilder: wizard de 4 steps
     1. Info básica (nome, tipo)
     2. Prompt do sistema (templates)
     3. Parâmetros (temperature, max_tokens)
     4. Teste ao vivo (sandbox)
   - AgentOrchestrator: visual de pipeline (opcional)

4. **Tela /analytics:**
   - Cards: Mensagens Hoje, Taxa Resolução Bot, Handoffs, Custo $
   - Gráfico de barras (últimos 7 dias)
   - Top 5 intenções detectadas
   - Custo acumulado (tokens × $0.003/1k Claude)

5. **Tela /settings:**
   - Conectar WhatsApp (QR Code do Evolution API)
   - Gerenciar integrações (futuro: Sheets, CRM)
   - Plano atual + uso do mês
   - Dados do tenant (nome, logo)

6. **PWA (Opcional):**
   - Manifest.json + Service Worker
   - Push Notifications (handoff criado)
   - Instalável no celular

**Entregável:** App mobile completo, instalável e com métricas.

**Critério de Sucesso:**
✅ Bottom nav funcionando  
✅ Todas as 4 telas operacionais  
✅ Analytics mostrando dados reais  
✅ PWA instalável (bônus)  

---

## 🏗️ ARQUITETURA DETALHADA

### **Fluxo de Mensagem (End-to-End):**
```
WhatsApp → Evolution API → Webhook FastAPI → Redis Queue
                                                    ↓
                                          [Worker processa]
                                                    ↓
                    ← Evolution API ← Salva resposta ← Claude API
                                                           ↑
                                              [Agent Processor busca contexto]
                                                           ↑
                                                      MongoDB
```

### **Stack de Cada Camada:**
| Camada | Tecnologia | Onde Roda | Função |
|--------|-----------|-----------|--------|
| Frontend | React + Tailwind | Vercel | Interface mobile-first |
| Backend | FastAPI + Python | Railway | APIs + lógica de negócio |
| Banco | MongoDB | Railway/Atlas | Dados principais |
| Auth | Supabase Auth | Supabase Cloud | Login/cadastro |
| Realtime | Supabase Realtime | Supabase Cloud | Websockets |
| WhatsApp | Evolution API v2 | Railway Docker | Conexão WhatsApp |
| Fila | Redis | Railway | Queue de mensagens |
| Orquestração | n8n (opcional) | Railway | Automações |
| IA | Claude 3.5 Sonnet | Anthropic API | Inteligência |

---

## 📊 DESIGN SYSTEM MOBILE-FIRST

### **Cores:**
```css
--background: #F8F9FA (cinza claro)
--primary: #6366F1 (indigo)
--success: #10B981 (verde)
--warning: #F59E0B (laranja)
--error: #EF4444 (vermelho)
--text: #1F2937 (cinza escuro)
```

### **Tipografia:**
- Fonte: Inter (Google Fonts)
- Headings: bold (font-weight: 700)
- Body: regular (font-weight: 400)

### **Componentes Chave:**
1. **ChatBubble:**
   - User: bg-gray-100 (esquerda)
   - Agent: bg-indigo-100 (direita)
   - Human: bg-green-100 (direita)

2. **TypingIndicator:**
   ```jsx
   <div className="typing-indicator">
     <span></span><span></span><span></span>
   </div>
   ```
   Animação CSS: 3 pontos pulsando (0.6s loop)

3. **StatusDot:**
   - Verde pulsante: agente ativo
   - Cinza: inativo
   - Vermelho: erro

4. **HandoffBanner:**
   - bg-red-50, border-l-4 border-red-500
   - Ícone de alerta + texto + botões

---

## 🚀 ESTRATÉGIA DE DEPLOY

### **Railway (Backend + Serviços):**
```yaml
services:
  - backend-api (FastAPI)
  - evolution-api (Docker)
  - redis (database)
  - mongodb (database)
  - n8n (opcional - fase 2+)
```

### **Vercel (Frontend):**
- Branch `main` → Produção
- Pull Requests → Preview deploys
- Environment variables automáticas

### **Supabase:**
- Project criado manualmente
- Migrations via Supabase CLI
- RLS (Row Level Security) ativado

---

## ✅ CHECKLIST DE DEPENDÊNCIAS

**Você precisa fornecer:**
- [ ] Chave API Claude (Anthropic)
- [ ] URL do projeto Supabase + anon key + service key
- [ ] URL do Railway (após deploy dos serviços)

**Eu vou criar:**
- [ ] Schema MongoDB completo
- [ ] Modelos FastAPI (Pydantic)
- [ ] Integração Evolution API
- [ ] Sistema de agentes + Claude
- [ ] Frontend completo mobile-first
- [ ] Deploy scripts (Railway + Vercel)

---

## 🎯 MVP MÍNIMO VIÁVEL (O QUE REALMENTE IMPORTA)

Se precisar priorizar, o **核心 (núcleo)** é:

1. ✅ **WhatsApp conectado** (mensagens entrando)
2. ✅ **Claude respondendo** (single agent)
3. ✅ **Handoff humano** (operador assume)
4. ✅ **Chat em tempo real** (Supabase Realtime)
5. ✅ **Dashboard básico** (lista conversas + chat view)

**Funcionalidades "nice to have" (podem esperar):**
- Multi-agente complexo (começa com 1 agente genérico)
- Analytics avançado (começa com contador simples)
- PWA + push notifications
- Integrações externas (Sheets, CRM)
- Agent Orchestrator visual

---

## 📝 PRÓXIMOS PASSOS

**Agora você precisa me dizer:**

1. ✅ **Aprovar este plano?** (ou ajustar algo)

2. 🔑 **Fornecer credenciais:**
   - Chave API Claude (Anthropic)
   - Dados do Supabase (URL + keys)
   - Você quer que eu configure o Railway ou você faz manual?

3. 🚦 **Decidir o começo:**
   - Executar **FASE 1 completa** agora?
   - Ou fazer parte por parte com sua aprovação?

**Minha recomendação:**  
Vamos executar **FASE 1** completa (fundação + WhatsApp). Ao final você testa, aprova, e partimos para FASE 2 (IA). Isso garante validação incremental.

**Você está de acordo? Tem alguma mudança no plano?** 🚀
