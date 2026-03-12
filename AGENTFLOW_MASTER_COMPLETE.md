# 🚀 AGENTFLOW - PLANEJAMENTO COMPLETO E DEFINITIVO
## Produto Final | 75 Dias | Todas APIs e Sistemas

---

## 📋 ÍNDICE

1. [Resumo Executivo](#resumo-executivo)
2. [Stack Técnica Completa](#stack-técnica)
3. [APIs e Serviços Externos](#apis-externas)
4. [Credenciais Necessárias](#credenciais)
5. [Arquitetura do Sistema](#arquitetura)
6. [Schemas de Banco de Dados](#schemas)
7. [Cronograma Completo (75 dias)](#cronograma)
8. [Custos Estimados](#custos)
9. [Checklist de Pré-Requisitos](#checklist)
10. [Guia de Setup de Cada Serviço](#guia-setup)

---

## 🎯 RESUMO EXECUTIVO

### **AgentFlow — Plataforma Completa de IA Omnichannel com CRM**

**Tempo total:** 75 dias (10 semanas + 5 dias)  
**Produto:** Completo (não MVP)  
**Equipe:** 1 desenvolvedor full-stack  
**Deploy:** Vercel (frontend) + Railway (backend + serviços)

### **Features do Produto Final:**

| # | Feature | Status |
|---|---------|--------|
| 1 | Multi-idiomas (176 idiomas) | ✅ Completo |
| 2 | Omnichannel (WhatsApp + Instagram + Facebook + Telegram) | ✅ Completo |
| 3 | IA Multimodal (texto + voz + imagem) | ✅ Completo |
| 4 | Multi-agente inteligente (20+ templates) | ✅ Completo |
| 5 | Handoff humano automático | ✅ Completo |
| 6 | CRM Kanban com IA | ✅ Completo |
| 7 | Sincronização tempo real (agendas + produtos) | ✅ Completo |
| 8 | Nutrição de leads (campanhas) | ✅ Completo |
| 9 | Edição em tempo real (hot reload) | ✅ Completo |
| 10 | Dashboard mobile-first + Analytics | ✅ Completo |

---

## 🛠️ STACK TÉCNICA COMPLETA

### **Frontend**
```yaml
Framework: React 19.0.0
Build Tool: Create React App (CRA) 5.0.1
Linguagem: JavaScript (ES6+)
CSS Framework: Tailwind CSS 3.4.17
UI Components: shadcn/ui (Radix UI)
Ícones: Lucide React (2px stroke)
State Management: React Context + Hooks
Routing: React Router DOM 7.5.1
Forms: React Hook Form 7.56.2 + Zod 3.24.4
HTTP Client: Axios 1.8.4
Real-time: Supabase JS Client
Drag & Drop: @dnd-kit/core (para Kanban)
Charts: Recharts 3.6.0
Date Handling: date-fns 4.1.0
Notifications: Sonner 2.0.3
```

### **Backend**
```yaml
Framework: FastAPI 0.110.1
Linguagem: Python 3.11+
ASGI Server: Uvicorn 0.25.0
Banco de Dados: MongoDB 6.0+ (Motor 3.3.1)
Cache: Redis 7.0+
Task Queue: APScheduler 3.10.4 (cron jobs)
Auth: Supabase Auth (delegado)
Environment: python-dotenv 1.0.1
Validation: Pydantic 2.6.4
HTTP Client: requests 2.31.0
```

### **IA e ML**
```yaml
LLM Principal: Claude 3.5 Sonnet (Anthropic)
  - SDK: anthropic 0.34.0
  - Modelo: claude-3-5-sonnet-20250514
  - Uso: Conversação, análise, decisões

Transcrição de Voz: OpenAI Whisper
  - SDK: openai 1.54.0
  - Modelo: whisper-1
  - Uso: Áudio → Texto (30+ idiomas)

Visão Computacional: Claude Vision (incluso no SDK Anthropic)
  - Uso: OCR, reconhecimento de objetos

Detecção de Idioma: FastText
  - Biblioteca: fasttext 0.9.2
  - Modelo: lid.176.bin (176 idiomas)
  - Fallback: langdetect 1.0.9
```

### **Integrações de Canais**
```yaml
WhatsApp: Evolution API v2
  - Deployment: Docker no Railway
  - Protocolo: Baileys (WebSocket)
  - Features: Texto, áudio, imagem, vídeo

Instagram DM: Meta Graph API v21.0
  - OAuth: Facebook Login
  - Webhooks: Mensagens, reações
  - Features: Texto, imagem, story replies

Facebook Messenger: Meta Graph API v21.0
  - OAuth: Facebook Login
  - Webhooks: Mensagens, postbacks
  - Features: Texto, imagem, quick replies

Telegram: Bot API
  - SDK: python-telegram-bot 21.0
  - Webhooks: Updates
  - Features: Texto, foto, áudio, document
```

### **Integrações de Produtividade**
```yaml
Google Calendar:
  - SDK: google-api-python-client 2.100.0
  - OAuth 2.0: google-auth 2.23.0
  - Uso: Consultar agenda, criar eventos

Google Sheets:
  - SDK: gspread 5.12.0
  - Auth: Service Account
  - Uso: Catálogo de produtos, estoque

APIs Personalizadas:
  - requests 2.31.0
  - Suporta: REST, GraphQL
  - Auth: API Key, Bearer Token, OAuth
```

### **Infraestrutura**
```yaml
Frontend Host: Vercel
  - Framework Detection: React (auto)
  - Build Command: yarn build
  - Output: build/
  - Domains: Custom domain suportado
  - SSL: Automático (Let's Encrypt)

Backend Host: Railway
  - Runtime: Python 3.11
  - Ports: 8001 (backend), 8080 (Evolution)
  - Volumes: Persistente (Redis, uploads)
  - Env Variables: Suportado
  - Auto Deploy: GitHub integration

Database (MongoDB):
  - Opção 1: MongoDB Atlas (cloud, grátis até 512MB)
  - Opção 2: Railway MongoDB (deploy próprio)
  - Driver: Motor (async)

Cache (Redis):
  - Railway Redis (64MB grátis)
  - Uso: Queue, cache de configs, rate limiting

Auth & Realtime:
  - Supabase (500MB grátis)
  - Features: Auth JWT, Realtime subscriptions, Storage
```

### **DevOps**
```yaml
Version Control: Git + GitHub
CI/CD: GitHub Actions
  - Frontend: Auto-deploy Vercel em push
  - Backend: Auto-deploy Railway em push

Monitoring:
  - Logs: Railway Logs + Vercel Logs
  - Errors: Supabase Logs
  - Metrics: Custom (via API)

Testing:
  - Backend: pytest 8.0.0
  - Frontend: React Testing Library
  - E2E: Playwright (opcional)
```

---

## 🔌 APIS E SERVIÇOS EXTERNOS

### **1. ANTHROPIC CLAUDE API**

**Uso:** LLM principal (conversação, análise, decisões)

**Documentação:** https://docs.anthropic.com/  
**Pricing:** https://www.anthropic.com/pricing  
**Console:** https://console.anthropic.com/

**Modelos:**
- `claude-3-5-sonnet-20250514` (recomendado)
  - Input: $3.00 / 1M tokens
  - Output: $15.00 / 1M tokens
  - Context: 200k tokens

**Credenciais necessárias:**
```bash
ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**Como obter:**
1. Criar conta em https://console.anthropic.com/
2. Adicionar método de pagamento
3. Gerar API key em Settings > API Keys
4. Copiar chave (começa com `sk-ant-api03-`)

**Estimativa de custo (1000 conversas/mês):**
- Input: ~500k tokens × $3/1M = $1.50
- Output: ~200k tokens × $15/1M = $3.00
- **Total: ~$4.50/mês**

---

### **2. OPENAI API (WHISPER)**

**Uso:** Transcrição de áudio (voz → texto)

**Documentação:** https://platform.openai.com/docs/api-reference/audio  
**Pricing:** https://openai.com/api/pricing/  
**Console:** https://platform.openai.com/

**Modelo:**
- `whisper-1`
  - Preço: $0.006 / minuto de áudio
  - Idiomas: 30+ (auto-detect)
  - Formato: mp3, mp4, mpeg, mpga, m4a, wav, webm

**Credenciais necessárias:**
```bash
OPENAI_API_KEY="sk-proj-..."
```

**Como obter:**
1. Criar conta em https://platform.openai.com/signup
2. Adicionar créditos (mínimo $5)
3. Gerar API key em API Keys
4. Copiar chave (começa com `sk-proj-`)

**Estimativa de custo (1000 áudios/mês de ~30s cada):**
- 1000 × 0.5 min × $0.006 = **$3.00/mês**

---

### **3. META GRAPH API (INSTAGRAM + FACEBOOK)**

**Uso:** Integração com Instagram DM e Facebook Messenger

**Documentação:** https://developers.facebook.com/docs/graph-api/  
**Messenger:** https://developers.facebook.com/docs/messenger-platform/  
**Instagram:** https://developers.facebook.com/docs/messenger-platform/instagram/  
**Console:** https://developers.facebook.com/apps/

**Versão:** v21.0 (atual em 2025)

**Endpoints principais:**
- **Receber mensagens:** Webhooks
- **Enviar mensagens:** `POST /{page-id}/messages`
- **Perfil usuário:** `GET /{user-id}`

**Credenciais necessárias:**
```bash
# Para cada tenant (criado no onboarding)
META_APP_ID="123456789012345"
META_APP_SECRET="abc123def456..."
META_PAGE_ACCESS_TOKEN="EAABsbCS1iHgBO..."  # Por página conectada
```

**Como obter:**

1. **Criar App no Meta for Developers:**
   - Acesse https://developers.facebook.com/apps/
   - Clique "Create App"
   - Tipo: "Business"
   - Nome: "AgentFlow"

2. **Configurar produtos:**
   - Adicionar "Messenger" + "Instagram"
   - Em Settings > Basic:
     - Copiar `App ID` e `App Secret`

3. **Configurar Webhooks:**
   - Em Messenger > Settings:
     - Callback URL: `https://seu-backend.railway.app/api/webhooks/meta`
     - Verify Token: criar um token secreto (ex: `agentflow_webhook_2025`)
     - Subscribe to: `messages`, `messaging_postbacks`

4. **Obter Page Access Token:**
   - Usuário precisa conectar sua página Facebook/Instagram
   - Fluxo OAuth:
     ```
     https://www.facebook.com/v21.0/dialog/oauth?
       client_id={app-id}&
       redirect_uri={redirect-uri}&
       scope=pages_messaging,instagram_basic,instagram_manage_messages
     ```
   - Após aprovação, obter `page_access_token`

**Custo:** Grátis (Meta não cobra por mensagens via API)

**Rate Limits:**
- 200 mensagens/hora por usuário (Instagram)
- Sem limite (Messenger)

---

### **4. TELEGRAM BOT API**

**Uso:** Integração com Telegram

**Documentação:** https://core.telegram.org/bots/api  
**Bot Father:** https://t.me/botfather

**Credenciais necessárias:**
```bash
TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
```

**Como obter:**

1. **Criar Bot:**
   - Abrir Telegram
   - Buscar @BotFather
   - Enviar `/newbot`
   - Seguir instruções (nome + username)
   - Copiar token HTTP API

2. **Configurar Webhook:**
   ```bash
   curl -X POST https://api.telegram.org/bot{TOKEN}/setWebhook \
     -d url=https://seu-backend.railway.app/api/webhooks/telegram
   ```

**Custo:** Grátis

**Rate Limits:**
- 30 mensagens/segundo por bot

---

### **5. EVOLUTION API V2 (WHATSAPP)**

**Uso:** Conexão com WhatsApp via protocolo Baileys

**Repositório:** https://github.com/EvolutionAPI/evolution-api  
**Documentação:** https://doc.evolution-api.com/  
**Docker Hub:** https://hub.docker.com/r/atendai/evolution-api

**Deployment:** Docker no Railway

**Portas:**
- 8080: API HTTP
- 8081: Websocket (opcional)

**Variáveis de ambiente:**
```bash
# docker-compose.yml ou Railway env
SERVER_URL=https://evolution.seu-dominio.com
AUTHENTICATION_API_KEY="your-secure-key-here"
DATABASE_ENABLED=true
DATABASE_PROVIDER=mongodb
DATABASE_CONNECTION_URI=mongodb://localhost:27017/evolution
WEBHOOK_GLOBAL_URL=https://seu-backend.railway.app/api/webhooks/evolution
```

**Como obter:**

1. **Deploy no Railway:**
   - Criar novo projeto
   - Add Service > Docker Image
   - Image: `atendai/evolution-api:v2.1.1`
   - Add variáveis acima
   - Deploy

2. **Conectar WhatsApp:**
   - POST `/instance/create`
     ```json
     {
       "instanceName": "agentflow-tenant-123",
       "qrcode": true,
       "webhookUrl": "https://seu-backend.railway.app/api/webhooks/evolution"
     }
     ```
   - GET `/instance/connect/{instanceName}`
   - Retorna QR Code (base64)
   - Escanear com WhatsApp

**Custo:**
- Railway: ~$5-10/mês (256MB RAM suficiente)

**Rate Limits:**
- WhatsApp Business API: sem limites oficiais
- Recomendado: max 100 msgs/segundo

---

### **6. SUPABASE**

**Uso:** Auth JWT + Realtime subscriptions + Storage

**Documentação:** https://supabase.com/docs  
**Pricing:** https://supabase.com/pricing  
**Console:** https://app.supabase.com/

**Plano Free:**
- 500MB database
- 1GB file storage
- 2GB bandwidth/mês
- Unlimited API requests
- Realtime: 200 conexões simultâneas

**Credenciais necessárias:**
```bash
# Frontend (.env)
REACT_APP_SUPABASE_URL="https://xxxx.supabase.co"
REACT_APP_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Backend (.env)
SUPABASE_URL="https://xxxx.supabase.co"
SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Secret key
```

**Como obter:**

1. **Criar projeto:**
   - Acesse https://app.supabase.com/
   - "New project"
   - Nome: "agentflow"
   - Database password: (guardar!)
   - Region: South America (São Paulo)

2. **Obter credenciais:**
   - Settings > API
   - Copiar:
     - Project URL
     - `anon` `public` key (frontend)
     - `service_role` `secret` key (backend)

3. **Configurar Auth:**
   - Authentication > Providers
   - Habilitar: Email, Google (opcional)
   - Configure redirect URLs

4. **Criar tabelas (Realtime):**
   ```sql
   -- Tabela para eventos em tempo real
   CREATE TABLE agent_updates (
     id SERIAL PRIMARY KEY,
     agent_id UUID NOT NULL,
     updated_fields JSONB,
     timestamp TIMESTAMPTZ DEFAULT NOW()
   );

   CREATE TABLE lead_updates (
     id SERIAL PRIMARY KEY,
     lead_id UUID NOT NULL,
     event TEXT,  -- 'created', 'stage_changed', etc
     from_stage TEXT,
     to_stage TEXT,
     moved_by TEXT,
     timestamp TIMESTAMPTZ DEFAULT NOW()
   );

   CREATE TABLE conversation_updates (
     id SERIAL PRIMARY KEY,
     conversation_id UUID NOT NULL,
     event_type TEXT,
     timestamp TIMESTAMPTZ DEFAULT NOW()
   );
   ```

5. **Habilitar Realtime:**
   - Database > Replication
   - Enable replication em tabelas acima

**Custo:** Grátis (plano Free suficiente para MVP)

---

### **7. GOOGLE CLOUD APIS**

**Uso:** Calendar + Sheets + OAuth

**Console:** https://console.cloud.google.com/  
**Pricing:** Grátis até limites generosos

#### **Google Calendar API**

**Documentação:** https://developers.google.com/calendar/api/guides/overview

**Quota grátis:**
- 1.000.000 requisições/dia
- 100 requisições/segundo

**Setup:**

1. **Criar projeto:**
   - https://console.cloud.google.com/
   - "New Project" > "AgentFlow"

2. **Habilitar APIs:**
   - APIs & Services > Library
   - Buscar "Google Calendar API"
   - Enable

3. **Criar credenciais:**
   - APIs & Services > Credentials
   - Create Credentials > OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URIs:
     ```
     https://seu-frontend.vercel.app/auth/google/callback
     ```
   - Copiar `Client ID` e `Client Secret`

4. **OAuth Consent Screen:**
   - User Type: External
   - Scopes: `https://www.googleapis.com/auth/calendar`

**Credenciais:**
```bash
GOOGLE_CLIENT_ID="123456-abc.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="GOCSPX-..."
```

**Fluxo OAuth (por tenant):**
1. Usuário clica "Conectar Google Calendar"
2. Redirect para Google OAuth
3. Usuário autoriza
4. Callback retorna `access_token` + `refresh_token`
5. Salvar tokens no banco (criptografados)

#### **Google Sheets API**

**Documentação:** https://developers.google.com/sheets/api/guides/concepts

**Setup:**

1. **Habilitar API:**
   - Mesmo projeto acima
   - Enable "Google Sheets API"

2. **Service Account (recomendado para leitura/escrita):**
   - Credentials > Create Credentials > Service Account
   - Role: Editor
   - Download JSON key

**Credenciais:**
```bash
# Armazenar JSON completo no banco (por tenant)
GOOGLE_SERVICE_ACCOUNT_JSON='{
  "type": "service_account",
  "project_id": "agentflow-...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "agentflow@agentflow-....iam.gserviceaccount.com",
  ...
}'
```

**Uso:**
- Tenant compartilha planilha com `client_email` do service account
- Backend lê/escreve via gspread

---

### **8. FASTTEXT (DETECÇÃO DE IDIOMA)**

**Uso:** Detectar idioma automaticamente

**Repositório:** https://github.com/facebookresearch/fastText  
**Modelos:** https://fasttext.cc/docs/en/language-identification.html

**Modelo recomendado:**
- `lid.176.bin` (176 idiomas, 95%+ accuracy)
- Tamanho: 131MB
- Download: https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin

**Instalação:**
```bash
pip install fasttext==0.9.2
```

**Uso:**
```python
import fasttext

model = fasttext.load_model('models/lid.176.bin')
predictions = model.predict("Hello, how are you?", k=3)

# Output:
# (('__label__en', '__label__id', '__label__so'), 
#  array([0.98, 0.01, 0.00]))
```

**Custo:** Grátis (modelo open-source)

---

### **9. MONGODB ATLAS (OPCIONAL)**

**Uso:** Banco de dados (alternativa ao Railway MongoDB)

**Documentação:** https://www.mongodb.com/docs/atlas/  
**Pricing:** https://www.mongodb.com/pricing  
**Console:** https://cloud.mongodb.com/

**Plano Free (M0):**
- 512MB storage
- Shared CPU
- Grátis para sempre

**Como obter:**

1. **Criar cluster:**
   - https://cloud.mongodb.com/
   - Build a Database > Free (M0)
   - Provider: AWS
   - Region: São Paulo (sa-east-1)

2. **Configurar acesso:**
   - Database Access > Add New User
   - Username/Password (guardar!)
   - Network Access > Add IP Address
   - Allow access from anywhere: `0.0.0.0/0` (ou IP do Railway)

3. **Obter connection string:**
   - Database > Connect > Connect your application
   - Driver: Python
   - Copiar: `mongodb+srv://user:pass@cluster.mongodb.net/`

**Credenciais:**
```bash
MONGO_URL="mongodb+srv://agentflow:senha@cluster.abc123.mongodb.net/agentflow?retryWrites=true&w=majority"
DB_NAME="agentflow"
```

**Custo:** Grátis (M0 suficiente para ~10k leads)

---

### **10. VERCEL**

**Uso:** Deploy do frontend

**Documentação:** https://vercel.com/docs  
**Pricing:** https://vercel.com/pricing  
**Console:** https://vercel.com/dashboard

**Plano Hobby (Free):**
- Unlimited deploys
- 100GB bandwidth/mês
- Automatic HTTPS
- Custom domain (1 grátis)

**Como obter:**

1. **Criar conta:**
   - https://vercel.com/signup
   - Login com GitHub (recomendado)

2. **Importar projeto:**
   - New Project
   - Import Git Repository
   - Selecionar repo do AgentFlow
   - Framework Preset: Create React App
   - Root Directory: `frontend/`

3. **Configurar variáveis:**
   - Settings > Environment Variables
   - Adicionar:
     ```
     REACT_APP_BACKEND_URL=https://agentflow-api.up.railway.app
     REACT_APP_SUPABASE_URL=https://xxx.supabase.co
     REACT_APP_SUPABASE_ANON_KEY=eyJ...
     ```

4. **Deploy:**
   - Automático a cada push no `main`
   - Preview em cada Pull Request

**Custo:** Grátis

---

### **11. RAILWAY**

**Uso:** Deploy backend + Evolution API + Redis

**Documentação:** https://docs.railway.app/  
**Pricing:** https://railway.app/pricing  
**Console:** https://railway.app/dashboard

**Plano Free (Trial):**
- $5 de crédito/mês (500 horas de execução)
- Após trial: $5/mês base + uso

**Como obter:**

1. **Criar conta:**
   - https://railway.app/
   - Login com GitHub

2. **Criar projeto:**
   - New Project > Deploy from GitHub repo
   - Selecionar repo do AgentFlow
   - Root directory: `backend/`

3. **Adicionar serviços:**
   - Add Service > Database > Redis
   - Add Service > Docker Image > `atendai/evolution-api:v2.1.1`

4. **Configurar variáveis:**
   - Backend:
     ```bash
     MONGO_URL=${{mongodb.MONGO_URL}}  # Se usar Railway MongoDB
     REDIS_URL=${{redis.REDIS_URL}}
     ANTHROPIC_API_KEY=sk-ant-...
     OPENAI_API_KEY=sk-proj-...
     SUPABASE_URL=https://xxx.supabase.co
     SUPABASE_SERVICE_KEY=eyJ...
     CORS_ORIGINS=https://agentflow.vercel.app
     ```

5. **Expor portas:**
   - Backend: Port 8001
   - Evolution API: Port 8080

6. **Domínio:**
   - Settings > Networking > Generate Domain
   - Copiar: `agentflow-api.up.railway.app`

**Custo estimado:**
- Backend (256MB): ~$5/mês
- Redis (64MB): ~$2/mês
- Evolution API (256MB): ~$5/mês
- **Total: ~$12/mês**

---

## 🔑 CREDENCIAIS NECESSÁRIAS (CHECKLIST)

### **Essenciais para Desenvolvimento:**

```bash
# === IA & ML ===
ANTHROPIC_API_KEY="sk-ant-api03-..."                    # Obrigatório
OPENAI_API_KEY="sk-proj-..."                            # Obrigatório (Whisper)

# === Banco de Dados ===
MONGO_URL="mongodb://localhost:27017"                   # Dev local
# ou
MONGO_URL="mongodb+srv://user:pass@cluster.mongodb.net" # Atlas
DB_NAME="agentflow"

# === Cache & Queue ===
REDIS_URL="redis://localhost:6379"                      # Dev local
# ou
REDIS_URL="redis://default:pass@redis.railway.internal:6379"  # Railway

# === Auth & Realtime ===
SUPABASE_URL="https://xxxx.supabase.co"                 # Obrigatório
SUPABASE_ANON_KEY="eyJhbGciOiJI..."                     # Frontend
SUPABASE_SERVICE_KEY="eyJhbGciOiJI..."                  # Backend (secret)

# === WhatsApp ===
EVOLUTION_API_URL="http://localhost:8080"               # Dev local
# ou
EVOLUTION_API_URL="https://evolution.railway.app"       # Production
EVOLUTION_API_KEY="your-secure-key"

# === Meta (Instagram + Facebook) ===
META_APP_ID="123456789012345"
META_APP_SECRET="abc123..."
# Tokens por tenant (salvos no banco após OAuth)

# === Telegram ===
TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."                  # Por tenant

# === Google APIs ===
GOOGLE_CLIENT_ID="xxx.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="GOCSPX-..."
# Service Account JSON por tenant (salvo no banco)

# === Backend ===
CORS_ORIGINS="http://localhost:3000,https://agentflow.vercel.app"
PORT=8001

# === Frontend ===
REACT_APP_BACKEND_URL="http://localhost:8001"           # Dev
# ou
REACT_APP_BACKEND_URL="https://agentflow-api.railway.app"  # Prod
```

### **Opcionais (Futuro):**

```bash
# Pagamentos
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."

# Email
SENDGRID_API_KEY="SG...."
RESEND_API_KEY="re_..."

# SMS
TWILIO_ACCOUNT_SID="AC..."
TWILIO_AUTH_TOKEN="..."

# Monitoramento
SENTRY_DSN="https://...@sentry.io/..."
```

---

## 🏗️ ARQUITETURA DO SISTEMA

### **Diagrama de Alto Nível:**

```
┌──────────────────────────────────────────────────────────────┐
│                    USUÁRIO FINAL                             │
│              (Cliente no WhatsApp/Instagram)                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │   CANAIS (Message Gateways)        │
        ├────────────────────────────────────┤
        │  • WhatsApp (Evolution API)        │
        │  • Instagram (Meta Graph API)      │
        │  • Facebook (Meta Graph API)       │
        │  • Telegram (Bot API)              │
        └────────────────┬───────────────────┘
                         │ Webhooks
                         ▼
┌────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI)                             │
│                 Railway: 8001                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         MESSAGE ROUTER & NORMALIZER                   │ │
│  │  • Recebe webhooks de todos os canais                │ │
│  │  • Normaliza formato (schema unificado)              │ │
│  │  • Detecta idioma (FastText)                         │ │
│  └──────────────────┬───────────────────────────────────┘ │
│                     │                                      │
│                     ▼                                      │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              REDIS QUEUE                             │ │
│  │  • Fila de mensagens (evita duplicação)             │ │
│  │  • Rate limiting                                     │ │
│  └──────────────────┬───────────────────────────────────┘ │
│                     │                                      │
│                     ▼                                      │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          AGENT PROCESSOR (Worker)                    │ │
│  │  ┌────────────────────────────────────────────────┐ │ │
│  │  │ 1. Busca contexto (MongoDB)                    │ │ │
│  │  │ 2. Identifica agente atual                     │ │ │
│  │  │ 3. Monta prompt com histórico                  │ │ │
│  │  │ 4. Chama Claude API (+ Tool Use)               │ │ │
│  │  │ 5. Processa resposta:                          │ │ │
│  │  │    • Texto → Enviar                            │ │ │
│  │  │    • Voz → Whisper → Processar                 │ │ │
│  │  │    • Imagem → Claude Vision → Processar        │ │ │
│  │  │    • Tool Use → Executar ação                  │ │ │
│  │  │ 6. Atualiza banco                              │ │ │
│  │  │ 7. Envia resposta via canal                    │ │ │
│  │  └────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │               CRM MANAGER                            │ │
│  │  • Avalia se conversa → Lead                        │ │
│  │  • Calcula score (0-100)                            │ │
│  │  • Move leads pelo pipeline                         │ │
│  │  • Tool Use: create_lead, move_lead_stage           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          CAMPAIGN MANAGER (APScheduler)              │ │
│  │  • Cron job: roda a cada hora                       │ │
│  │  • Verifica regras de campanhas                     │ │
│  │  • Dispara nutrição de leads                        │ │
│  │  • Follow-up automático                             │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              INTEGRATION HUB                         │ │
│  │  • Google Calendar (consultar/agendar)              │ │
│  │  • Google Sheets (produtos/estoque)                 │ │
│  │  • APIs personalizadas                              │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      MONGODB (Banco Principal)      │
        │  • conversations                    │
        │  • messages                         │
        │  • agents                           │
        │  • leads                            │
        │  • campaigns                        │
        │  • tenants                          │
        │  • integrations                     │
        └────────────────────────────────────┘
                         ▲
                         │
        ┌────────────────────────────────────┐
        │    SUPABASE (Auth + Realtime)      │
        │  • Authentication (JWT)             │
        │  • agent_updates (realtime)         │
        │  • lead_updates (realtime)          │
        │  • conversation_updates             │
        └────────────────────────────────────┘
                         ▲
                         │
┌────────────────────────────────────────────────────────────┐
│                  FRONTEND (React)                          │
│                  Vercel: 3000                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         BOTTOM NAVIGATION (4 TABS)                   │ │
│  │  • 💬 Chat (Unified Inbox)                           │ │
│  │  • 🤖 Agentes (Marketplace + CRUD)                   │ │
│  │  • 🎯 CRM (Kanban Board)                             │ │
│  │  • 📊 Analytics (Dashboard)                          │ │
│  │  • ⚙️ Config (Settings)                              │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         REALTIME SUBSCRIPTIONS                       │ │
│  │  • Supabase listener → agent_updates                │ │
│  │  • Supabase listener → lead_updates                 │ │
│  │  • Auto-refresh UI sem polling                      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   OPERADOR    │
                 │   (Humano)    │
                 └───────────────┘
```

---

## 📊 SCHEMAS DE BANCO DE DADOS (MONGODB)

### **Collection: tenants**
```javascript
{
  _id: ObjectId("..."),
  id: "uuid",
  name: "Boutique da Maria",
  slug: "boutique-maria",
  
  owner: {
    user_id: "supabase_user_uuid",
    email: "maria@boutique.com",
    name: "Maria Silva"
  },
  
  settings: {
    language: "pt-BR",
    timezone: "America/Sao_Paulo",
    business_hours: {
      monday: { start: "09:00", end: "18:00" },
      // ... outros dias
    }
  },
  
  subscription: {
    plan: "starter" | "pro" | "enterprise",
    status: "active" | "trial" | "canceled",
    current_period_start: ISODate("2025-03-01"),
    current_period_end: ISODate("2025-04-01"),
    monthly_message_limit: 10000,
    messages_used_this_month: 4532
  },
  
  created_at: ISODate("2025-03-01"),
  updated_at: ISODate("2025-03-15")
}
```

### **Collection: conversations**
```javascript
{
  _id: ObjectId("..."),
  id: "uuid",
  tenant_id: "uuid",
  
  // Canal e identificação
  channel: "whatsapp" | "instagram" | "facebook" | "telegram",
  channel_user_id: "+5511987654321",  // Identificador único no canal
  
  // Cliente
  customer_name: "João Silva",
  customer_email: "joao@email.com",
  customer_phone: "+5511987654321",
  customer_metadata: {
    avatar_url: "https://...",
    username: "@joaosilva"
  },
  
  // Estado da conversa
  status: "active" | "waiting" | "resolved" | "archived",
  language: "pt",  // Auto-detected
  language_detection_method: "auto" | "manual",
  
  // Agente atual
  current_agent_id: "uuid",
  current_agent_name: "Carol",
  agent_history: [
    {
      agent_id: "uuid",
      agent_name: "Roberto",
      started_at: ISODate("..."),
      ended_at: ISODate("..."),
      reason: "Cliente quer comprar → Vendas"
    }
  ],
  
  // Handoff humano
  assigned_to: null | "user_uuid",  // Operador humano
  handler_type: "bot" | "human",
  is_typing: false,  // Cliente está digitando
  
  // Contexto coletado
  context: {
    customer_intent: "compra",
    pain_points: ["Gasta muito tempo em mensagens"],
    interests: ["Automação de vendas"],
    budget: "R$ 50-100/mês",
    cart: {
      items: [],
      total: 0,
      abandoned_at: null
    },
    custom_fields: {}
  },
  
  // Lead tracking
  lead_id: null | "uuid",  // Se virou lead no CRM
  
  // Timestamps
  created_at: ISODate("..."),
  updated_at: ISODate("..."),
  last_message_at: ISODate("..."),
  resolved_at: null | ISODate("...")
}
```

### **Collection: messages**
```javascript
{
  _id: ObjectId("..."),
  id: "uuid",
  conversation_id: "uuid",
  tenant_id: "uuid",
  
  // Metadados do canal
  channel: "whatsapp",
  channel_message_id: "WAM_abc123",
  
  // Direção e sender
  direction: "inbound" | "outbound",
  sender: {
    type: "customer" | "agent" | "human",
    id: "uuid_or_phone",
    name: "João Silva"
  },
  
  // Conteúdo
  content: {
    type: "text" | "audio" | "image" | "video" | "document",
    text: "Olá, quero comprar um vestido",
    
    // Se áudio
    audio_url: "https://...",
    audio_duration_seconds: 15,
    transcription: "Olá, quero comprar um vestido",  // Whisper
    
    // Se imagem
    image_url: "https://...",
    image_caption: "Esse vestido",
    ai_image_analysis: "Vestido floral branco e rosa, modelo verão",  // Claude Vision
    
    // Se vídeo/documento
    media_url: "https://...",
    media_type: "image/jpeg",
    media_size_bytes: 245678
  },
  
  // Metadados
  is_system_message: false,  // Mensagem de transição entre agentes
  reply_to_message_id: null | "uuid",
  
  // IA metadata (se outbound de bot)
  ai_metadata: {
    model: "claude-3-5-sonnet-20250514",
    tokens_input: 450,
    tokens_output: 120,
    cost_usd: 0.00285,
    latency_ms: 1240,
    tool_use: [
      {
        name: "update_context",
        input: { key: "customer_name", value: "João Silva" }
      }
    ]
  },
  
  // Status de envio
  status: "sent" | "delivered" | "read" | "failed",
  delivered_at: ISODate("..."),
  read_at: ISODate("..."),
  
  // Timestamps
  timestamp: ISODate("..."),
  created_at: ISODate("...")
}
```

### **Collection: agents**
```javascript
{
  _id: ObjectId("..."),
  id: "uuid",
  tenant_id: "uuid",
  
  // Identificação
  name: "Carol",
  type: "vendas" | "sac" | "suporte" | "agendamento" | "custom",
  description: "Assistente de vendas especializada em e-commerce",
  avatar_url: "https://...",
  
  // Status
  status: "active" | "inactive" | "paused",
  
  // Configuração de IA
  ai_config: {
    model: "claude-3-5-sonnet-20250514",
    system_prompt: `Você é Carol, assistente de vendas da Boutique da Maria.
    Sua função é: mostrar produtos, calcular frete, processar pedidos.
    Tom: amigável, consultivo, não insistente.
    Contexto coletado: {context}`,
    
    parameters: {
      temperature: 0.7,
      max_tokens: 500,
      top_p: 1.0
    },
    
    tools_enabled: [
      "escalate_to_human",
      "switch_agent",
      "update_context",
      "search_integration"
    ]
  },
  
  // Personalidade
  personality: {
    tone: 0.6,  // 0=formal, 1=casual
    verbosity: 0.4,  // 0=conciso, 1=detalhado
    emoji_usage: 0.5,  // 0=nunca, 1=sempre
    response_speed: "fast"  // fast | balanced | thoughtful
  },
  
  // Regras de handoff
  handoff_rules: {
    enabled: true,
    conditions: [
      "Cliente usa palavras: 'urgente', 'reclamação', 'processo'",
      "Cliente pede explicitamente: 'quero falar com humano'",
      "Não resolveu em 3 tentativas",
      "Cliente quer negociar preço/desconto"
    ]
  },
  
  // Integrações
  integrations: [
    {
      id: "uuid",
      type: "google_sheets",
      purpose: "product_catalog",
      config: {
        sheet_id: "1abc123...",
        sheet_name: "Produtos"
      },
      status: "active"
    }
  ],
  
  // Estatísticas
  stats: {
    total_conversations: 1247,
    total_messages: 8934,
    resolution_rate: 0.78,  // 78%
    handoff_rate: 0.12,  // 12%
    avg_response_time_seconds: 3.2,
    total_cost_usd: 45.67,
    last_active_at: ISODate("...")
  },
  
  // Timestamps
  created_at: ISODate("..."),
  updated_at: ISODate("..."),
  created_by: "user_uuid"
}
```

### **Collection: leads**
```javascript
{
  _id: ObjectId("..."),
  id: "uuid",
  tenant_id: "uuid",
  
  // Dados básicos
  name: "Maria Silva",
  email: "maria@example.com",
  phone: "+5511987654321",
  company: "Boutique da Maria",
  job_title: "Proprietária",
  
  // Pipeline
  stage: "new" | "qualified" | "proposal" | "won" | "lost",
  stage_history: [
    {
      stage: "new",
      entered_at: ISODate("..."),
      exited_at: ISODate("..."),
      moved_by: "ai" | "user_uuid",
      reason: "Score atingiu 60"
    }
  ],
  
  // Valor e score
  value: 2500.00,  // R$
  currency: "BRL",
  probability: 0.65,  // 65% de chance de fechar
  score: 65,  // 0-100
  score_factors: [
    { factor: "decision_maker", points: 20 },
    { factor: "budget_declared", points: 15 },
    { factor: "high_engagement", points: 10 }
  ],
  
  // Origem
  source: {
    channel: "whatsapp",
    agent_id: "uuid",
    agent_name: "Carol",
    conversation_id: "uuid",
    first_message: "Quero automatizar meu WhatsApp",
    created_at: ISODate("...")
  },
  
  // Contexto coletado
  context: {
    pain_points: [
      "Gasta 4h/dia em mensagens repetitivas",
      "Sobrecarga"
    ],
    interests: [
      "Automação de vendas",
      "Economia de tempo"
    ],
    budget: "R$ 50-100/mês",
    urgency: "high",  // low | medium | high
    decision_maker: true,
    competitors_mentioned: ["ManyChat"],
    timeline: "Black Friday (60 dias)",
    objections: []
  },
  
  // Análise da IA
  ai_analysis: {
    qualification_reason: "Dor clara, orçamento alinhado, decisora, urgência real",
    suggested_actions: [
      "Enviar demo personalizada",
      "Mencionar setup em 3min",
      "Oferecer trial até Black Friday"
    ],
    deal_breakers: [],
    winning_factors: [
      "É decisora",
      "Conhece concorrente",
      "Urgência"
    ],
    next_best_action: "send_proposal",
    confidence: 0.85
  },
  
  // Atribuição
  assigned_to: null | "user_uuid",
  current_handler: "agent_id" | "user_uuid",
  handler_type: "bot" | "human",
  
  // Timestamps
  created_at: ISODate("..."),
  updated_at: ISODate("..."),
  last_activity_at: ISODate("..."),
  won_at: null | ISODate("..."),
  lost_at: null | ISODate("..."),
  
  // Motivo de perda
  lost_reason: null | "price" | "competitor" | "timing" | "not_interested" | "other",
  lost_notes: null | "Cliente achou caro demais"
}
```

### **Collection: campaigns**
```javascript
{
  _id: ObjectId("..."),
  id: "uuid",
  tenant_id: "uuid",
  
  name: "Recuperação Carrinho Abandonado",
  type: "abandoned_cart" | "inactive_lead" | "follow_up" | "birthday" | "custom",
  status: "active" | "paused" | "completed",
  
  // Trigger
  trigger: {
    event: "cart_abandoned",
    conditions: {
      time_elapsed_hours: 24,
      cart_value_min: 50,
      customer_segment: "engaged"
    }
  },
  
  // Sequência de mensagens
  messages: [
    {
      delay_hours: 1,
      template: "Oi {{name}}! Vi que você deixou itens no carrinho. Quer finalizar a compra? 😊",
      variables: ["name", "cart_total", "cart_items"]
    },
    {
      delay_hours: 24,
      template: "{{name}}, preparei um desconto especial de 10% pra você! Use: VOLTA10",
      variables: ["name"]
    }
  ],
  
  // Estatísticas
  statistics: {
    triggered: 145,
    sent: 290,  // 145 × 2 mensagens
    replied: 67,
    converted: 23,
    conversion_rate: 0.16,
    revenue_generated: 12450.00
  },
  
  created_at: ISODate("..."),
  updated_at: ISODate("...")
}
```

---

## 📅 CRONOGRAMA COMPLETO (75 DIAS)

### **OVERVIEW:**

| Fase | Descrição | Dias | Dia Início | Dia Fim |
|------|-----------|------|------------|---------|
| 0 | Fundação + Setup | 5 | 1 | 5 |
| 1 | WhatsApp + Multi-idioma | 8 | 6 | 13 |
| 2 | IA Multimodal + Multi-agente | 15 | 14 | 28 |
| 3 | Omnichannel (Instagram, Facebook, Telegram) | 15 | 29 | 43 |
| 4 | CRM Kanban com IA | 12 | 44 | 55 |
| 5 | Dashboard + Analytics | 8 | 56 | 63 |
| 6 | Sincronização (Calendar + Sheets) | 5 | 64 | 68 |
| 7 | Nutrição de Leads | 5 | 69 | 73 |
| 8 | Testes + Ajustes Finais | 2 | 74 | 75 |

**TOTAL: 75 dias (10 semanas + 5 dias)**

---

### **FASE 0: FUNDAÇÃO + SETUP (Dia 1-5)**

**Objetivo:** Projeto rodando localmente, banco configurado, autenticação funcionando

**Tarefas:**

**Dia 1: Setup do Projeto**
- [ ] Criar repositório GitHub
- [ ] Clonar estrutura base (já fornecida em /app)
- [ ] Configurar `.gitignore`
- [ ] Instalar dependências:
  ```bash
  cd /app/frontend && yarn install
  cd /app/backend && pip install -r requirements.txt
  ```

**Dia 2: Banco de Dados**
- [ ] Setup MongoDB (Atlas ou Railway)
- [ ] Criar database `agentflow`
- [ ] Criar collections:
  - `tenants`
  - `conversations`
  - `messages`
  - `agents`
  - `leads`
  - `campaigns`
  - `pipeline_stages`
  - `integrations`
- [ ] Adicionar índices:
  ```javascript
  db.conversations.createIndex({ "tenant_id": 1, "channel_user_id": 1 })
  db.messages.createIndex({ "conversation_id": 1, "timestamp": -1 })
  db.leads.createIndex({ "tenant_id": 1, "stage": 1 })
  ```

**Dia 3: Supabase + Auth**
- [ ] Criar projeto Supabase
- [ ] Configurar Authentication (email + Google)
- [ ] Criar tabelas Realtime:
  ```sql
  CREATE TABLE agent_updates (...);
  CREATE TABLE lead_updates (...);
  CREATE TABLE conversation_updates (...);
  ```
- [ ] Habilitar Replication
- [ ] Testar auth no frontend

**Dia 4: Redis + Backend Base**
- [ ] Setup Redis (local ou Railway)
- [ ] Configurar FastAPI:
  - CORS
  - MongoDB connection
  - Redis connection
  - Routers (/api prefix)
- [ ] Criar endpoints básicos:
  - `GET /api/health`
  - `POST /api/auth/register`
  - `GET /api/auth/me`

**Dia 5: Frontend Base + Deploy**
- [ ] Configurar Tailwind + shadcn/ui
- [ ] Criar layout base (Bottom Navigation)
- [ ] Criar página de login/cadastro
- [ ] Testar fluxo: cadastro → login → dashboard
- [ ] Deploy inicial:
  - Frontend: Vercel
  - Backend: Railway

**Entregável:** App rodando em dev + prod, auth funcionando

---

### **FASE 1: WHATSAPP + MULTI-IDIOMA (Dia 6-13)**

**Objetivo:** Mensagens do WhatsApp entrando e sendo salvas no banco

**Dia 6-7: Evolution API**
- [ ] Deploy Evolution API no Railway
- [ ] Configurar variáveis de ambiente
- [ ] Criar instância WhatsApp (QR Code)
- [ ] Testar envio/recebimento

**Dia 8-9: Webhook Handler**
- [ ] Endpoint `POST /api/webhooks/evolution`
- [ ] Parsear eventos:
  - `MESSAGES_UPSERT`
  - `TYPING_INDICATOR`
  - `MESSAGE_STATUS_UPDATE`
- [ ] Salvar em `conversations` + `messages`
- [ ] Normalizar schema

**Dia 10-11: Multi-idioma**
- [ ] Baixar modelo FastText (`lid.176.bin`)
- [ ] Implementar `detect_language()`
- [ ] Salvar idioma em `conversations.language`
- [ ] Criar endpoint `POST /api/conversations/:id/language` (manual override)
- [ ] Frontend: LanguageSwitcher component

**Dia 12-13: Frontend - Inbox**
- [ ] Página `/chat`
- [ ] Lista de conversas (ConversationList)
- [ ] Tela de chat individual (ChatView)
- [ ] Realtime subscription (Supabase)
- [ ] Testar end-to-end

**Entregável:** Mensagem WhatsApp → Aparece no app em < 2s

---

### **FASE 2: IA MULTIMODAL + MULTI-AGENTE (Dia 14-28)**

**Objetivo:** Claude respondendo com voz + imagem + multi-agente

**Dia 14-15: Claude SDK + Agent Processor**
- [ ] Instalar `anthropic` SDK
- [ ] Criar `AgentProcessor` class
- [ ] Implementar `process_message()`
- [ ] Tool Use: `escalate_to_human`, `update_context`
- [ ] Testar resposta básica (só texto)

**Dia 16-17: Redis Queue + Worker**
- [ ] Implementar fila Redis (lpush/rpop)
- [ ] Worker processa fila continuamente
- [ ] Rate limiting (100 msg/min)
- [ ] Error handling + retry

**Dia 18-19: Marketplace de Agentes**
- [ ] Criar 5 agentes base (SAC, Vendas, Suporte, Agendamento, Custom)
- [ ] Seed data em `agents` collection
- [ ] Endpoint `GET /api/agents/marketplace`
- [ ] Frontend: Marketplace page

**Dia 20-21: Multi-agente (Orquestração)**
- [ ] Tool Use: `switch_agent`
- [ ] Handler de transição
- [ ] Preservar contexto
- [ ] Histórico em `agent_history`
- [ ] Testar: SAC → Vendas → Suporte

**Dia 22-23: Voz (Whisper)**
- [ ] Instalar `openai` SDK
- [ ] `TranscriptionService` class
- [ ] Webhook handler para `audioMessage`
- [ ] Download áudio → Whisper → Texto
- [ ] Processar como mensagem normal
- [ ] Salvar transcrição em `content.transcription`

**Dia 24-25: Imagem (Claude Vision)**
- [ ] `VisionService` class
- [ ] Webhook handler para `imageMessage`
- [ ] Download imagem → Base64 → Claude Vision
- [ ] OCR + Reconhecimento
- [ ] Salvar análise em `content.ai_image_analysis`

**Dia 26-27: Handoff Humano**
- [ ] Tool Use: `escalate_to_human`
- [ ] Atualizar `conversations.status` → `waiting`
- [ ] Notificação Realtime (Supabase)
- [ ] Frontend: HandoffBanner component
- [ ] Botão "Assumir" → muda `handler_type` → `human`
- [ ] Bot pausa enquanto humano atende

**Dia 28: Frontend - AgentBuilder**
- [ ] Wizard de criação (4 steps)
- [ ] Personalizar agente (nome, tom, prompt)
- [ ] Sandbox de teste
- [ ] CRUD completo

**Entregável:** Claude respondendo texto + voz + imagem + multi-agente + handoff

---

### **FASE 3: OMNICHANNEL (Dia 29-43)**

**Objetivo:** Instagram, Facebook, Telegram funcionando

**Dia 29-32: Instagram DM**
- [ ] Criar app no Meta for Developers
- [ ] Configurar produtos (Instagram)
- [ ] Implementar OAuth flow
- [ ] Configurar webhooks
- [ ] `InstagramConnector` class
- [ ] Webhook handler `POST /api/webhooks/instagram`
- [ ] Normalizar mensagens
- [ ] Testar envio/recebimento

**Dia 33-36: Facebook Messenger**
- [ ] Configurar produto Messenger no mesmo app Meta
- [ ] `FacebookMessengerConnector` class
- [ ] Webhook handler `POST /api/webhooks/facebook`
- [ ] Normalizar mensagens
- [ ] Testar

**Dia 37-40: Telegram**
- [ ] Criar bot via @BotFather
- [ ] `TelegramConnector` class
- [ ] Configurar webhook
- [ ] Webhook handler `POST /api/webhooks/telegram`
- [ ] Normalizar mensagens
- [ ] Testar

**Dia 41-43: Message Router + Unified Inbox**
- [ ] `MessageRouter` class
- [ ] `route_inbound()` → normaliza qualquer canal
- [ ] `route_outbound()` → envia pelo canal correto
- [ ] Frontend: Unified Inbox
  - Ícones por canal
  - Filtro por canal
  - Status unificado
- [ ] Testar todos os canais juntos

**Entregável:** 4 canais funcionando + unified inbox

---

### **FASE 4: CRM KANBAN COM IA (Dia 44-55)**

**Objetivo:** CRM completo com leads e IA

**Dia 44-45: Schema CRM**
- [ ] Collection `leads` criada
- [ ] Collection `pipeline_stages` criada
- [ ] Seed data (stages padrão)
- [ ] Endpoints CRUD:
  - `GET /api/leads`
  - `POST /api/leads`
  - `PATCH /api/leads/:id`
  - `DELETE /api/leads/:id`

**Dia 46-47: CRM Manager (IA cria leads)**
- [ ] `CRMManager` class
- [ ] `evaluate_conversation_for_lead()`
- [ ] `should_create_lead()` (Claude decide)
- [ ] `create_lead_from_conversation()`
- [ ] Extração de dados (nome, email, etc)
- [ ] Testar: conversa → lead criado

**Dia 48-49: Lead Scoring + Stage Movement**
- [ ] `calculate_lead_score()` (0-100)
- [ ] `evaluate_stage_transition()`
- [ ] Tool Use: `move_lead_stage`
- [ ] Regras configuráveis por stage
- [ ] Histórico em `stage_history`

**Dia 50-52: Frontend - Kanban Board**
- [ ] Instalar `@dnd-kit/core`
- [ ] `KanbanBoard` component
- [ ] `KanbanColumn` component
- [ ] `LeadCard` component
- [ ] Drag and drop manual
- [ ] Realtime updates (Supabase)

**Dia 53-54: Lead Detail View**
- [ ] Página `/crm/leads/:id`
- [ ] Timeline de atividades
- [ ] Análise da IA
- [ ] Botões de ação (mover, assumir, perder)
- [ ] Link para conversa original

**Dia 55: Pipeline Config**
- [ ] Página `/crm/pipeline/config`
- [ ] CRUD de stages
- [ ] Configurar regras automáticas
- [ ] Preview de automações

**Entregável:** CRM completo funcionando

---

### **FASE 5: DASHBOARD + ANALYTICS (Dia 56-63)**

**Objetivo:** UI completa e analytics

**Dia 56-57: Bottom Navigation**
- [ ] Layout com tabs
- [ ] 💬 Chat (já feito)
- [ ] 🤖 Agentes (já feito)
- [ ] 🎯 CRM (já feito)
- [ ] 📊 Analytics (novo)
- [ ] ⚙️ Config (novo)
- [ ] Badges com contadores

**Dia 58-59: Analytics Overview**
- [ ] Página `/analytics`
- [ ] Cards de métricas:
  - Mensagens hoje
  - Taxa de resolução bot
  - Handoffs
  - Custo (tokens × $)
- [ ] Gráfico (últimos 7 dias)
- [ ] Top 5 intenções
- [ ] Por canal
- [ ] Por agente

**Dia 60-61: Configurações - Canais**
- [ ] Página `/settings/channels`
- [ ] Conectar WhatsApp (QR Code)
- [ ] Conectar Instagram (OAuth)
- [ ] Conectar Facebook (OAuth)
- [ ] Conectar Telegram (Bot Token)
- [ ] Status de cada canal
- [ ] Desconectar

**Dia 62: Configurações - Conta**
- [ ] Página `/settings/account`
- [ ] Editar perfil
- [ ] Alterar senha
- [ ] Dados da empresa
- [ ] Plano e pagamento (view only por enquanto)

**Dia 63: PWA (Opcional)**
- [ ] Configurar `manifest.json`
- [ ] Service Worker
- [ ] Instalável no celular
- [ ] Push notifications (handoff)

**Entregável:** Dashboard completo mobile-first

---

### **FASE 6: SINCRONIZAÇÃO (Dia 64-68)**

**Objetivo:** Google Calendar + Sheets

**Dia 64-65: Google Calendar**
- [ ] Configurar OAuth no Google Cloud
- [ ] `GoogleCalendarIntegration` class
- [ ] `get_available_slots()`
- [ ] `book_appointment()`
- [ ] Tool Use: `check_availability`, `book_appointment`
- [ ] Frontend: Conectar calendar no onboarding

**Dia 66-67: Google Sheets**
- [ ] Configurar Service Account
- [ ] `GoogleSheetsIntegration` class
- [ ] `get_products()` (lê planilha)
- [ ] `search_products(query)`
- [ ] Tool Use: `search_products`, `check_stock`
- [ ] Frontend: Conectar sheets no onboarding

**Dia 68: Integrations Hub**
- [ ] Página `/settings/integrations`
- [ ] Lista de integrações disponíveis
- [ ] Status (conectado/desconectado)
- [ ] Configurar cada uma
- [ ] Logs de uso

**Entregável:** Agentes consultam agenda e produtos em tempo real

---

### **FASE 7: NUTRIÇÃO DE LEADS (Dia 69-73)**

**Objetivo:** Campanhas automáticas

**Dia 69-70: Campaign Manager**
- [ ] `CampaignManager` class (APScheduler)
- [ ] Cron job (roda a cada hora)
- [ ] `process_campaigns()`
- [ ] `handle_abandoned_cart()`
- [ ] `handle_inactive_lead()`
- [ ] `handle_follow_up()`

**Dia 71: Campaign Executor**
- [ ] `send_scheduled_messages()` (roda a cada 5min)
- [ ] Enfileirar mensagens
- [ ] Enviar via `MessageRouter`
- [ ] Cancelar se cliente respondeu
- [ ] Atualizar estatísticas

**Dia 72: Frontend - Campaign Builder**
- [ ] Página `/crm/campaigns`
- [ ] Lista de campanhas
- [ ] Wizard de criação:
  - Tipo
  - Trigger (quando disparar)
  - Sequência de mensagens
  - Variáveis
- [ ] Preview
- [ ] Ativar/pausar

**Dia 73: Campaign Analytics**
- [ ] Estatísticas por campanha:
  - Triggered
  - Sent
  - Replied
  - Converted
  - ROI
- [ ] Gráficos
- [ ] Exportar relatório

**Entregável:** Campanhas automáticas funcionando

---

### **FASE 8: TESTES + AJUSTES (Dia 74-75)**

**Objetivo:** Produto estável e polido

**Dia 74: Testes E2E**
- [ ] Testar onboarding completo
- [ ] Testar todos os canais
- [ ] Testar multi-agente
- [ ] Testar handoff
- [ ] Testar CRM (criar lead, mover, ganhar/perder)
- [ ] Testar campanhas
- [ ] Testar integrações
- [ ] Documentar bugs

**Dia 75: Ajustes Finais**
- [ ] Corrigir bugs críticos
- [ ] Polir UI (espaçamentos, cores)
- [ ] Otimizar performance (cache, lazy load)
- [ ] Verificar logs
- [ ] Atualizar README
- [ ] Deploy final

**Entregável:** Produto completo e pronto para uso

---

## 💰 CUSTOS ESTIMADOS

### **DESENVOLVIMENTO (3 meses):**

| Item | Custo/mês | Total (3 meses) |
|------|-----------|-----------------|
| Claude API (dev/test) | $30 | $90 |
| OpenAI API (Whisper dev) | $10 | $30 |
| Railway (backend + Evolution + Redis) | $12 | $36 |
| MongoDB Atlas (M0 Free) | $0 | $0 |
| Supabase (Free) | $0 | $0 |
| Vercel (Free) | $0 | $0 |
| Google Cloud APIs (Free) | $0 | $0 |
| **TOTAL** | **$52/mês** | **$156** |

### **PRODUÇÃO (por mês, 1000 conversas):**

| Item | Cálculo | Custo/mês |
|------|---------|-----------|
| Claude API | 500k input + 200k output | $4.50 |
| Whisper | 500 áudios × 30s × $0.006/min | $1.50 |
| Railway Backend | 256MB 24/7 | $5 |
| Railway Evolution | 256MB 24/7 | $5 |
| Railway Redis | 64MB | $2 |
| MongoDB Atlas | M0 Free | $0 |
| Supabase | Free tier | $0 |
| Vercel | Hobby plan | $0 |
| **TOTAL** | | **$18/mês** |

**Margem (Plano Starter $49/mês):**
- Receita: $49
- Custo: $18
- **Lucro: $31/mês (63% margem)**

---

## ✅ CHECKLIST DE PRÉ-REQUISITOS

### **Antes de Começar o Desenvolvimento:**

**Contas criadas:**
- [ ] GitHub (repo criado)
- [ ] Anthropic (Claude API key)
- [ ] OpenAI (Whisper API key)
- [ ] Supabase (projeto criado)
- [ ] Railway (conta criada)
- [ ] Vercel (conta criada)
- [ ] MongoDB Atlas (cluster criado) OU Railway MongoDB
- [ ] Google Cloud (projeto criado)
- [ ] Meta for Developers (app criado)

**Credenciais obtidas:**
- [ ] `ANTHROPIC_API_KEY`
- [ ] `OPENAI_API_KEY`
- [ ] `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_SERVICE_KEY`
- [ ] `MONGO_URL`
- [ ] `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET`
- [ ] `META_APP_ID` + `META_APP_SECRET`

**Ambiente local configurado:**
- [ ] Node.js 18+ instalado
- [ ] Python 3.11+ instalado
- [ ] MongoDB rodando local (ou Atlas)
- [ ] Redis rodando local (ou Railway)
- [ ] Git configurado
- [ ] VS Code (ou IDE preferida)

**Conhecimentos necessários:**
- [ ] React (hooks, context, routing)
- [ ] Python (async/await, FastAPI)
- [ ] MongoDB (queries, aggregations)
- [ ] REST APIs (endpoints, auth, webhooks)
- [ ] Git (branches, commits, push)

---

## 🔧 GUIA DE SETUP DE CADA SERVIÇO

### **1. SUPABASE (15 min)**

```bash
# 1. Criar projeto
- Acesse: https://app.supabase.com/
- "New project"
- Nome: agentflow
- Database password: (guardar!)
- Region: South America

# 2. Obter credenciais
- Settings > API
- Copiar:
  - Project URL
  - anon public key (frontend)
  - service_role secret key (backend)

# 3. Criar tabelas Realtime
- SQL Editor > New query
- Colar e executar:

CREATE TABLE agent_updates (
  id SERIAL PRIMARY KEY,
  agent_id UUID NOT NULL,
  updated_fields JSONB,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lead_updates (
  id SERIAL PRIMARY KEY,
  lead_id UUID NOT NULL,
  event TEXT,
  from_stage TEXT,
  to_stage TEXT,
  moved_by TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE conversation_updates (
  id SERIAL PRIMARY KEY,
  conversation_id UUID NOT NULL,
  event_type TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

# 4. Habilitar Realtime
- Database > Replication
- Enable replication nas 3 tabelas acima

# 5. Configurar Auth
- Authentication > Providers
- Enable: Email
- Optional: Google OAuth

# 6. Configurar URLs (depois do deploy)
- Authentication > URL Configuration
- Site URL: https://agentflow.vercel.app
- Redirect URLs: https://agentflow.vercel.app/**
```

---

### **2. RAILWAY (20 min)**

```bash
# 1. Criar conta
- https://railway.app/
- Login com GitHub

# 2. Criar projeto
- "New Project"
- Nome: agentflow

# 3. Deploy Backend
- "New Service" > "GitHub Repo"
- Selecionar: seu-usuario/agentflow
- Root directory: backend/
- Add variáveis (Settings > Variables):

MONGO_URL=mongodb://...
REDIS_URL=redis://...
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=eyJ...
CORS_ORIGINS=https://agentflow.vercel.app
PORT=8001

- Deploy

# 4. Adicionar Redis
- "New Service" > "Database" > "Redis"
- Auto-conecta (variável ${{REDIS_URL}})

# 5. Adicionar MongoDB (opcional)
- "New Service" > "Database" > "MongoDB"
- Auto-conecta (variável ${{MONGODB_URL}})

# 6. Deploy Evolution API
- "New Service" > "Docker Image"
- Image: atendai/evolution-api:v2.1.1
- Add variáveis:

SERVER_URL=https://evolution-agentflow.up.railway.app
AUTHENTICATION_API_KEY=seu-token-secreto-aqui
DATABASE_ENABLED=true
DATABASE_PROVIDER=mongodb
DATABASE_CONNECTION_URI=${{MONGODB_URL}}
WEBHOOK_GLOBAL_URL=https://agentflow-api.up.railway.app/api/webhooks/evolution

- Port: 8080
- Deploy

# 7. Obter URLs
- Backend: Settings > Networking > Generate Domain
  - Exemplo: agentflow-api.up.railway.app
- Evolution: idem
  - Exemplo: evolution-agentflow.up.railway.app

# 8. Configurar domains no frontend
- Atualizar REACT_APP_BACKEND_URL no Vercel
```

---

### **3. VERCEL (10 min)**

```bash
# 1. Criar conta
- https://vercel.com/signup
- Login com GitHub

# 2. Importar projeto
- "New Project"
- "Import Git Repository"
- Selecionar: seu-usuario/agentflow
- Framework Preset: Create React App
- Root Directory: frontend/
- Build Command: yarn build
- Output Directory: build/

# 3. Configurar variáveis
- Settings > Environment Variables
- Add:

REACT_APP_BACKEND_URL=https://agentflow-api.up.railway.app
REACT_APP_SUPABASE_URL=https://xxx.supabase.co
REACT_APP_SUPABASE_ANON_KEY=eyJ...

# 4. Deploy
- "Deploy"
- Aguardar build (2-3 min)

# 5. Obter URL
- Copiar: https://agentflow.vercel.app
- (ou configurar domínio custom)

# 6. Configurar no Supabase
- Supabase > Authentication > URL Configuration
- Site URL: https://agentflow.vercel.app
- Redirect URLs: https://agentflow.vercel.app/**

# 7. Auto-deploy
- Cada push no main → deploy automático
- Cada PR → preview deploy
```

---

### **4. ANTHROPIC CLAUDE (5 min)**

```bash
# 1. Criar conta
- https://console.anthropic.com/
- Sign up

# 2. Adicionar pagamento
- Settings > Billing
- Add payment method (cartão)

# 3. Gerar API key
- Settings > API Keys
- "Create Key"
- Nome: agentflow-production
- Copiar: sk-ant-api03-...
- GUARDAR (não aparece novamente)

# 4. Testar
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20250514",
    "max_tokens": 100,
    "messages": [
      {"role": "user", "content": "Olá!"}
    ]
  }'

# 5. Adicionar ao Railway
- Railway > Backend > Variables
- ANTHROPIC_API_KEY=sk-ant-...
- Redeploy
```

---

### **5. OPENAI (WHISPER) (5 min)**

```bash
# 1. Criar conta
- https://platform.openai.com/signup

# 2. Adicionar créditos
- Settings > Billing
- Add payment method
- Add credits (mínimo $5)

# 3. Gerar API key
- API keys > Create new secret key
- Nome: agentflow-whisper
- Copiar: sk-proj-...
- GUARDAR

# 4. Testar
curl https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F model="whisper-1" \
  -F file="@audio.mp3"

# 5. Adicionar ao Railway
- Railway > Backend > Variables
- OPENAI_API_KEY=sk-proj-...
- Redeploy
```

---

### **6. META FOR DEVELOPERS (Instagram + Facebook) (30 min)**

```bash
# 1. Criar conta
- https://developers.facebook.com/
- Login com Facebook pessoal

# 2. Criar App
- "My Apps" > "Create App"
- Use case: "Business"
- App name: AgentFlow
- Contact email: seu-email

# 3. Adicionar produtos
- Dashboard > Add Product
- Adicionar: "Messenger" + "Instagram"

# 4. Obter credenciais
- Settings > Basic
- Copiar:
  - App ID: 123456789
  - App Secret: abc123... (Show)

# 5. Configurar webhooks (Messenger)
- Messenger > Settings > Webhooks
- Callback URL: https://agentflow-api.railway.app/api/webhooks/meta
- Verify Token: criar um token secreto (ex: agentflow_2025)
- Subscribe to: messages, messaging_postbacks
- Save

# 6. Configurar webhooks (Instagram)
- Instagram > Settings > Webhooks
- Mesmas configs acima

# 7. OAuth Flow (implementar no backend)
- Usuário conecta página via:
https://www.facebook.com/v21.0/dialog/oauth?
  client_id=123456789&
  redirect_uri=https://agentflow.vercel.app/auth/meta/callback&
  scope=pages_messaging,instagram_basic,instagram_manage_messages&
  response_type=code

- Trocar code por access_token (backend)
- Salvar token no banco (criptografado)

# 8. Testar
- Enviar mensagem na página Facebook
- Verificar webhook recebendo
```

---

### **7. TELEGRAM BOT (10 min)**

```bash
# 1. Criar bot
- Abrir Telegram
- Buscar: @BotFather
- Enviar: /newbot
- Nome: AgentFlow Bot
- Username: agentflow_bot (único)
- Copiar token: 123456:ABC-DEF...

# 2. Configurar webhook
curl -X POST https://api.telegram.org/bot123456:ABC-DEF.../setWebhook \
  -d url=https://agentflow-api.railway.app/api/webhooks/telegram

# 3. Verificar
curl https://api.telegram.org/bot123456:ABC-DEF.../getWebhookInfo

# 4. Testar
- Enviar mensagem para @agentflow_bot
- Verificar webhook recebendo

# 5. Salvar token
- Cada tenant conecta seu próprio bot
- Token salvo em integrations collection
```

---

## 🎉 CONCLUSÃO

Você agora tem:
- ✅ Planejamento completo (75 dias)
- ✅ Todas as APIs e serviços mapeados
- ✅ Credenciais necessárias listadas
- ✅ Arquitetura detalhada
- ✅ Schemas de banco definidos
- ✅ Guia de setup passo a passo
- ✅ Custos estimados

**Próximo passo:** Obter todas as credenciais e começar FASE 0! 🚀

**Tem alguma dúvida sobre alguma API ou serviço?**
