# PLANO DE ENGENHARIA DE SISTEMAS — AgentZZ
## Reorganização Completa para Produção, Manutenção e Escalabilidade
### Data: 27/03/2026

---

## 1. DIAGNÓSTICO DE ARQUITETURA ATUAL

### 1.1 Mapa de Dependências Atual (O Problema)

```
┌──────────────────────────────────────────────────────────┐
│                    studio.py (5.268 linhas)               │
│                                                           │
│  ┌─ Projetos CRUD ──────────────────────────────────────┐ │
│  │  Tudo lê/escreve em tenant.settings["studio_projects"]│ │
│  │  = 1 campo JSONB com TODOS os projetos do usuário    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─ IA ─────────────────────────────────────────────────┐ │
│  │  litellm.completion("anthropic/claude-sonnet...")     │ │  ← Modelo HARDCODED
│  │  GeminiImageGeneration(api_key=...)                   │ │  ← Provider HARDCODED
│  │  ElevenLabs(api_key=...)                              │ │  ← Provider HARDCODED
│  │  DirectSora2Client(api_key=...)                       │ │  ← Provider HARDCODED
│  │  OpenAI(api_key=...) # whisper                        │ │  ← Provider HARDCODED
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─ Negócio ────────────────────────────────────────────┐ │
│  │  Storyboard + Produção + Pós-Produção + Livro +      │ │
│  │  Continuidade + Idioma + Smart Editor + Legendas +    │ │
│  │  Narração + Analytics + Preview                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─ Infraestrutura ────────────────────────────────────┐  │
│  │  FFmpeg inline + Upload Supabase + Thread pools ad-hoc│ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**Problemas fundamentais:**
1. **Arquivo monolítico** — 5.268 linhas num único ficheiro. Qualquer programador novo precisa de horas para entender.
2. **Dados num JSONB** — Todos os projetos (52+) guardados num único campo JSON do tenant. Não escala.
3. **IA acoplada** — Nome do modelo Claude hardcoded em 12+ locais. Trocar para GPT-5 exige editar dezenas de linhas.
4. **Sem camada de serviço** — A lógica de negócio está misturada com rotas HTTP e chamadas de banco.
5. **Frontend monolítico** — PipelineView tem 76 estados e 3.094 linhas. Impossível manter.

---

## 2. ARQUITETURA ALVO

### 2.1 Backend — Separação de Camadas

```
/app/backend/
│
├── server.py                          # App startup + middleware (slim)
├── .env                               # Todas as credenciais
│
├── api/                               # CAMADA 1: Rotas HTTP (recebe/responde)
│   ├── __init__.py
│   ├── v1/                            # Versionamento
│   │   ├── __init__.py                # Monta todos os sub-routers
│   │   ├── auth.py                    # Login, registro
│   │   ├── agents.py                  # CRUD de agentes
│   │   ├── studio/                    # Sub-módulo Studio
│   │   │   ├── __init__.py            # Agrupa sub-routers do studio
│   │   │   ├── projects.py            # CRUD projetos (~150 linhas)
│   │   │   ├── storyboard.py          # Storyboard endpoints (~200 linhas)
│   │   │   ├── production.py          # Produção de vídeo (~200 linhas)
│   │   │   ├── post_production.py     # Pós-produção/áudio (~150 linhas)
│   │   │   ├── continuity.py          # Diretor de continuidade (~100 linhas)
│   │   │   ├── book_export.py         # PDF + Livro interativo (~80 linhas)
│   │   │   ├── language.py            # Agente de idioma (~100 linhas)
│   │   │   ├── smart_editor.py        # Editor inteligente (~100 linhas)
│   │   │   ├── localization.py        # Dublagem + legendas (~150 linhas)
│   │   │   └── analytics.py           # Métricas (~80 linhas)
│   │   ├── campaigns.py
│   │   ├── conversations.py
│   │   ├── leads.py
│   │   ├── channels.py
│   │   └── google.py
│   └── schemas/                       # TODOS os Pydantic models (request/response)
│       ├── __init__.py
│       ├── auth.py
│       ├── agents.py
│       ├── studio.py                  # Todos os schemas do Studio
│       ├── campaigns.py
│       └── common.py                  # Schemas compartilhados
│
├── services/                          # CAMADA 2: Lógica de Negócio (regras)
│   ├── __init__.py
│   ├── studio/
│   │   ├── __init__.py
│   │   ├── project_service.py         # Criar, buscar, deletar projetos
│   │   ├── storyboard_service.py      # Gerar, editar, aprovar storyboard
│   │   ├── production_service.py      # Pipeline de produção de vídeo
│   │   ├── post_production_service.py # Mixagem de áudio
│   │   ├── continuity_service.py      # Análise de continuidade
│   │   └── export_service.py          # PDF, Livro, MP4
│   ├── agent_service.py
│   ├── campaign_service.py
│   └── auth_service.py
│
├── providers/                         # CAMADA 3: Integrações Externas (ISOLADAS)
│   ├── __init__.py
│   ├── ai/                            # ABSTRAÇÃO DE IA
│   │   ├── __init__.py
│   │   ├── base.py                    # Interface/Contrato
│   │   ├── text_provider.py           # Trocar Claude↔GPT↔Gemini em 1 config
│   │   ├── image_provider.py          # Trocar Gemini↔DALL-E em 1 config
│   │   ├── video_provider.py          # Trocar Sora↔Runway em 1 config
│   │   ├── voice_provider.py          # Trocar ElevenLabs↔OpenAI TTS em 1 config
│   │   └── stt_provider.py            # Trocar Whisper↔Deepgram em 1 config
│   ├── storage/
│   │   ├── __init__.py
│   │   └── supabase_storage.py        # Upload/download isolado
│   └── external/
│       ├── ffmpeg.py                  # Wrapper FFmpeg
│       ├── google_api.py              # Google Calendar/Sheets
│       └── messaging.py               # WhatsApp, Telegram, SMS
│
├── db/                                # CAMADA 4: Acesso a Dados (ISOLADO)
│   ├── __init__.py
│   ├── supabase_client.py             # Singleton do client Supabase
│   ├── mongo_client.py                # Singleton do client MongoDB
│   └── repositories/                  # Padrão Repository
│       ├── __init__.py
│       ├── user_repo.py               # CRUD users
│       ├── tenant_repo.py             # CRUD tenants
│       ├── agent_repo.py              # CRUD agents
│       ├── project_repo.py            # CRUD studio projects (NOVA TABELA)
│       ├── lead_repo.py               # CRUD leads
│       └── conversation_repo.py       # CRUD conversations
│
├── core/                              # Utilitários compartilhados
│   ├── __init__.py
│   ├── config.py                      # Todas as variáveis de ambiente
│   ├── auth.py                        # JWT, hashing
│   ├── cache.py                       # Sistema de cache (já existe, bom)
│   ├── middleware.py                   # Rate limit, logging, compression
│   ├── exceptions.py                  # Exceções customizadas
│   └── constants.py                   # Constantes globais
│
└── tests/                             # Reorganizado por domínio
    ├── test_auth.py
    ├── test_agents.py
    ├── studio/
    │   ├── test_projects.py
    │   ├── test_storyboard.py
    │   ├── test_production.py
    │   └── test_continuity.py
    └── test_campaigns.py
```

### 2.2 Frontend — Componentes Modulares

```
/app/frontend/src/
│
├── api/                               # CAMADA API (todas as chamadas HTTP isoladas)
│   ├── client.js                      # Axios instance configurado + interceptors
│   ├── studioApi.js                   # Todas as chamadas do Studio
│   ├── agentsApi.js                   # Todas as chamadas de Agentes
│   ├── authApi.js                     # Login, registro
│   └── campaignsApi.js                # Chamadas de Campanhas
│
├── hooks/                             # Custom hooks (lógica reutilizável)
│   ├── useProjectCache.js             # Já existe (bom)
│   ├── useStudioProject.js            # Estado de 1 projeto
│   ├── useStoryboard.js               # Estado do storyboard
│   ├── useCompanies.js                # CRUD empresas
│   ├── usePolling.js                  # Hook genérico de polling
│   └── useAbortController.js          # Cancelamento de requests
│
├── components/
│   ├── studio/                        # Módulo Studio (auto-contido)
│   │   ├── PipelineView.jsx           # Orquestrador (~200 linhas)
│   │   ├── CampaignTypeSelector.jsx   # Selector de tipo
│   │   ├── CompanySelector.jsx        # Empresa ativa
│   │   ├── ProjectList.jsx            # Lista + busca
│   │   ├── ProjectCard.jsx            # Card individual
│   │   ├── NewProjectForm.jsx         # Formulário
│   │   ├── BriefingWizard.jsx         # Questionário guiado
│   │   ├── StoryboardEditor/
│   │   │   ├── index.jsx              # Orquestrador
│   │   │   ├── PanelCard.jsx          # Card expandível
│   │   │   ├── Filmstrip.jsx          # Galeria de frames
│   │   │   ├── InpaintEditor.jsx      # Editor de elementos
│   │   │   └── FacilitatorChat.jsx    # Chat AI
│   │   ├── DirectedStudio/
│   │   │   ├── index.jsx              # Orquestrador Step 5
│   │   │   ├── HeroCard.jsx           # Filme Final
│   │   │   ├── DeliverableGrid.jsx    # Bento grid
│   │   │   └── SceneStrip.jsx         # Scroll horizontal
│   │   └── PostProduction/
│   │       ├── index.jsx
│   │       ├── AudioUploader.jsx
│   │       └── ModeSelector.jsx
│   ├── layout/                        # Já existe (bom)
│   ├── pipeline/                      # Já existe (bom)
│   └── ui/                            # shadcn (já existe)
│
├── contexts/                          # Já existe
├── pages/                             # Páginas (apenas routing + layout)
└── utils/                             # Utilitários
```

---

## 3. ABSTRAÇÃO DE IA — Trocar Provider sem Alterar Código

### 3.1 O Problema Atual

O nome do modelo está espalhado em **12+ lugares**:
```python
# studio.py linha 224, 251, 376, 617, etc.
model="anthropic/claude-sonnet-4-5-20250929"  # HARDCODED!
```

Para trocar de Claude para GPT-5, precisa editar **cada um** desses locais. Risco alto de esquecer algum.

### 3.2 A Solução: Provider Pattern

```python
# /app/backend/providers/ai/base.py
from abc import ABC, abstractmethod

class TextProvider(ABC):
    """Contrato: qualquer provider de texto deve implementar estes métodos."""

    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 4000) -> str: ...

    @abstractmethod
    async def complete_with_images(self, system: str, user: str, images: list[bytes]) -> str: ...

    @abstractmethod
    async def chat(self, system: str, messages: list[dict]) -> str: ...


class ImageProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, reference_image: bytes = None) -> bytes: ...


class VideoProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, reference_image: bytes = None,
                       size: str = "1280x720", duration: int = 12) -> bytes: ...


class VoiceProvider(ABC):
    @abstractmethod
    async def text_to_speech(self, text: str, voice_id: str) -> bytes: ...

    @abstractmethod
    async def list_voices(self) -> list[dict]: ...


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: str, language: str = None) -> str: ...
```

```python
# /app/backend/providers/ai/text_provider.py
import litellm
from .base import TextProvider

class ClaudeProvider(TextProvider):
    MODEL = "anthropic/claude-sonnet-4-5-20250929"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        response = await litellm.acompletion(
            model=self.MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            api_key=self.api_key, max_tokens=max_tokens, timeout=120,
        )
        return response.choices[0].message.content

class GPT5Provider(TextProvider):
    MODEL = "openai/gpt-5"
    # ... mesma interface, diferente implementação


# /app/backend/core/config.py
AI_TEXT_PROVIDER = "claude"  # Trocar aqui = troca em TODO o sistema
AI_IMAGE_PROVIDER = "gemini"
AI_VIDEO_PROVIDER = "sora2"
AI_VOICE_PROVIDER = "elevenlabs"
AI_STT_PROVIDER = "whisper"
```

```python
# /app/backend/providers/ai/__init__.py — Factory
from core.config import AI_TEXT_PROVIDER, AI_IMAGE_PROVIDER, ...

def get_text_provider() -> TextProvider:
    if AI_TEXT_PROVIDER == "claude":
        return ClaudeProvider(api_key=ANTHROPIC_API_KEY)
    elif AI_TEXT_PROVIDER == "gpt5":
        return GPT5Provider(api_key=OPENAI_API_KEY)
    # ... etc

def get_image_provider() -> ImageProvider: ...
def get_video_provider() -> VideoProvider: ...
def get_voice_provider() -> VoiceProvider: ...
```

**Resultado:** Para trocar Claude por GPT-5, basta mudar 1 variável:
```env
AI_TEXT_PROVIDER=gpt5
```

---

## 4. BANCO DE DADOS — Migração de JSONB para Tabelas

### 4.1 O Problema Atual

```
tenant.settings.studio_projects = [
  { id: "abc", name: "...", scenes: [...], storyboard_panels: [...],
    character_avatars: {...}, outputs: {...}, post_production_status: {...},
    ... (pode ter 100+ campos por projeto)
  },
  { ... },  // projeto 2
  { ... },  // projeto 3
  ... // 52 projetos, cada um com MEGABYTES de dados
]
```

**Tudo num ÚNICO campo JSONB.** Cada operação:
1. Busca o JSON inteiro (todos os 52 projetos)
2. Modifica 1 campo de 1 projeto
3. Reescreve o JSON inteiro de volta

Com 100 usuários, cada um com 50 projetos de 500KB: o sistema colapsa.

### 4.2 Schema Proposto (Tabelas Dedicadas)

```sql
-- TABELA: studio_projects (migrar de JSONB para tabela real)
CREATE TABLE studio_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'draft',  -- draft, script, storyboard, production, complete
    animation_style TEXT,
    animation_sub TEXT,
    visual_style JSONB DEFAULT '{}',
    lang TEXT DEFAULT 'pt',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_projects_tenant ON studio_projects(tenant_id);
CREATE INDEX idx_projects_status ON studio_projects(status);

-- TABELA: project_scenes (1 projeto → N cenas)
CREATE TABLE project_scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES studio_projects(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    title TEXT,
    description TEXT,
    dialogue TEXT,
    narration TEXT,
    characters_in_scene TEXT[] DEFAULT '{}',
    duration_seconds FLOAT DEFAULT 8,
    camera_angle TEXT,
    emotion TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_scenes_project ON project_scenes(project_id);

-- TABELA: storyboard_panels (1 cena → 1 painel com N frames)
CREATE TABLE storyboard_panels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES studio_projects(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, generating, done, error
    image_url TEXT,
    frames JSONB DEFAULT '[]',     -- [{frame_number, image_url, label}]
    approved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_panels_project ON storyboard_panels(project_id);

-- TABELA: project_characters (1 projeto → N personagens)
CREATE TABLE project_characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES studio_projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    avatar_url TEXT,
    avatar_analysis TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_chars_project ON project_characters(project_id);

-- TABELA: project_outputs (vídeos, PDFs, livros gerados)
CREATE TABLE project_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES studio_projects(id) ON DELETE CASCADE,
    type TEXT NOT NULL,  -- 'scene_video', 'final_video', 'pdf', 'book', 'narration'
    scene_number INTEGER,
    url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_outputs_project ON project_outputs(project_id);
```

### 4.3 Impacto da Migração

| Operação | Antes (JSONB) | Depois (Tabelas) |
|----------|---------------|-------------------|
| Listar projetos | Busca TODO o settings JSON | `SELECT * FROM studio_projects WHERE tenant_id=? LIMIT 20` |
| Abrir 1 projeto | Busca todos os 52 projetos, filtra no Python | `SELECT * FROM studio_projects WHERE id=?` |
| Atualizar 1 cena | Reescreve o JSON inteiro | `UPDATE project_scenes SET dialogue=? WHERE id=?` |
| Buscar painéis | Busca todos os projetos → filtra 1 → busca painéis | `SELECT * FROM storyboard_panels WHERE project_id=?` |
| Deletar projeto | Busca JSON, filtra array, reescreve | `DELETE FROM studio_projects WHERE id=?` (cascade) |

**Resultado:** De O(N) para O(1) em todas as operações. Com índices, suporta 100.000+ projetos.

---

## 5. FRONTEND — CAMADA API ISOLADA

### 5.1 O Problema Atual

Cada componente faz `axios.get`/`axios.post` diretamente com URL hardcoded:
```javascript
// StoryboardEditor.jsx linha 90
const r = await axios.get(`${API}/studio/projects/${projectId}/storyboard`);
// StoryboardEditor.jsx linha 109
await axios.post(`${API}/studio/projects/${projectId}/generate-storyboard`);
// ...43 chamadas espalhadas em PipelineView.jsx sozinho
```

Se a URL da API muda, se precisa adicionar headers, retry logic, ou trocar axios por fetch — precisa editar CADA componente.

### 5.2 A Solução: API Layer

```javascript
// /app/frontend/src/api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  timeout: 120000,
});

// Interceptor: adiciona token automaticamente
api.interceptors.request.use(config => {
  const token = localStorage.getItem('agentzz_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Interceptor: trata erros globalmente
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('agentzz_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

```javascript
// /app/frontend/src/api/studioApi.js
import api from './client';

export const studioApi = {
  // Projetos
  listProjects: () => api.get('/studio/projects'),
  getProject: (id) => api.get(`/studio/projects/${id}/status`),
  createProject: (data) => api.post('/studio/projects', data),
  deleteProject: (id) => api.delete(`/studio/projects/${id}`),

  // Storyboard
  getStoryboard: (projectId) => api.get(`/studio/projects/${projectId}/storyboard`),
  generateStoryboard: (projectId) => api.post(`/studio/projects/${projectId}/generate-storyboard`),
  regeneratePanel: (projectId, data) => api.post(`/studio/projects/${projectId}/storyboard/regenerate-panel`, data),
  editPanel: (projectId, data) => api.patch(`/studio/projects/${projectId}/storyboard/edit-panel`, data),
  approveStoryboard: (projectId) => api.patch(`/studio/projects/${projectId}/storyboard/approve`, { approved: true }),

  // Produção
  startProduction: (projectId, data) => api.post(`/studio/projects/${projectId}/production/start`, data),
  getProductionStatus: (projectId) => api.get(`/studio/projects/${projectId}/production/status`),

  // ... etc
};
```

**Resultado:** Componentes chamam `studioApi.getStoryboard(id)` em vez de montar URL + headers manualmente. Mudar a API = mudar 1 ficheiro.

---

## 6. PLANO DE EXECUÇÃO — FASES INCREMENTAIS

### Princípio: Cada fase é independente e testável. Nenhuma quebra funcionalidade existente.

### FASE 0: Preparação (1h)
- [ ] Fix do build de produção (`@/lib/i18n`)
- [ ] Criar branch de trabalho
- [ ] Backup dos dados atuais
- **Validação:** `npm run build` sem erros

### FASE 1: Segurança + Middleware (2h)
- [ ] Auth nos endpoints abertos
- [ ] CORS explícito
- [ ] GZip middleware
- [ ] Rate limiting (slowapi)
- **Validação:** Curl testa auth. Responses comprimidas.

### FASE 2: Abstração de IA (3-4h)
- [ ] Criar `/providers/ai/base.py` (interfaces)
- [ ] Implementar `ClaudeProvider`, `GeminiImageProvider`, `Sora2Provider`, `ElevenLabsProvider`
- [ ] Criar factory `get_text_provider()` etc.
- [ ] Criar `/core/config.py` com variáveis AI_*_PROVIDER
- [ ] Substituir chamadas hardcoded em studio.py pelos providers
- **Validação:** Gerar storyboard funciona igual. Trocar config = troca provider.

### FASE 3: Backend Modular (4-6h)
- [ ] Criar estrutura `/api/v1/studio/` com sub-routers
- [ ] Mover endpoints de studio.py para módulos (~10 ficheiros)
- [ ] Criar `/api/schemas/studio.py` com todos os Pydantic models
- [ ] Extrair helpers para `/services/studio/`
- [ ] Atualizar server.py para montar os novos routers
- [ ] Mover scripts mortos para `/scripts/`
- **Validação:** Todos os endpoints respondem igual. Testes existentes passam.

### FASE 4: Migração de Banco de Dados (3-4h)
- [ ] Criar tabelas no Supabase (projects, scenes, panels, characters, outputs)
- [ ] Criar `/db/repositories/project_repo.py`
- [ ] Script de migração: ler JSONB → inserir nas tabelas
- [ ] Atualizar services para usar repositories
- [ ] Manter compatibilidade retroativa (ler de ambos durante migração)
- **Validação:** Projetos existentes aparecem. CRUD funciona. Dados intactos.

### FASE 5: Performance Frontend (3-4h)
- [ ] Code splitting (React.lazy em todas as rotas)
- [ ] `loading="lazy"` em todas as `<img>`
- [ ] Error Boundary global
- [ ] Storyboard com painéis expandíveis
- [ ] PWA (manifest + service worker)
- **Validação:** Lighthouse > 70. Storyboard fluido. App instalável.

### FASE 6: Frontend Modular (4-6h)
- [ ] Criar `/api/client.js` + `studioApi.js`
- [ ] Split PipelineView.jsx em 6-8 componentes
- [ ] Split StoryboardEditor.jsx em 4-5 componentes
- [ ] Split DirectedStudio.jsx em 3-4 componentes
- [ ] Custom hooks (useStudioProject, useStoryboard, usePolling)
- [ ] AbortController nos hooks
- **Validação:** Todos os fluxos funcionam. Nenhuma regressão.

### FASE 7: Otimização de Backend (2-3h)
- [ ] Dashboard query otimizado (8 → 2 queries)
- [ ] Global ThreadPool
- [ ] Cache headers em assets
- [ ] Paginação em listagens
- **Validação:** Dashboard < 1s. 100 requests concorrentes sem falha.

---

## 7. ORDEM DE EXECUÇÃO E DEPENDÊNCIAS

```
FASE 0 (Fix Build)
  ↓
FASE 1 (Segurança)
  ↓
FASE 2 (Abstração IA) ←── Independente, pode começar em paralelo com Fase 5
  ↓
FASE 3 (Backend Modular) ←── Depende de Fase 2 (usa providers)
  ↓
FASE 4 (Banco de Dados) ←── Depende de Fase 3 (usa repositories)
  ↓
FASE 5 (Performance Frontend) ←── Independente do backend
  ↓
FASE 6 (Frontend Modular) ←── Depende de Fase 5
  ↓
FASE 7 (Otimização Backend) ←── Final
```

**Caminho crítico:** 0 → 1 → 2 → 3 → 4 (backend) + 5 → 6 (frontend em paralelo) → 7

---

## 8. REGRAS DE MIGRAÇÃO (Não Quebrar Nada)

1. **Endpoints mantêm mesma URL** — Frontend não precisa mudar até Fase 6
2. **Migração de dados incremental** — Novo código lê de tabelas, fallback para JSONB
3. **Feature flags** — Novas features ligam/desligam por config
4. **Testes em cada fase** — Rodar suite existente (1.299 testes) após cada mudança
5. **Rollback plan** — Cada fase tem script de reversão

---

## 9. RESULTADO FINAL

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Manutenibilidade | 1 arquivo de 5.268 linhas | 30+ módulos de <200 linhas |
| Trocar IA | Editar 12+ locais | Mudar 1 variável de config |
| Novo programador entende | 4-8 horas | 30 minutos (pastas auto-explicativas) |
| Query de 1 projeto | Busca TODOS os projetos | Busca só 1 por ID |
| 100 usuários simultâneos | Servidor bloqueia | Responde normalmente |
| Bundle inicial | 15 MB | ~400 KB (gzip) |
| Instalar como app | Impossível | PWA instalável |
| Adicionar novo provider | Copiar/colar código | Implementar 1 interface |
| Testes | 99 arquivos sem organização | Por domínio, fácil encontrar |
