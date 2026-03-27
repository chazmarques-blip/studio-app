# RELATÓRIO DE AUDITORIA TÉCNICA — AgentZZ
## Data: 27/03/2026 | Versão: 0.4.0

---

## RESUMO EXECUTIVO

| Métrica | Valor |
|---------|-------|
| Linhas de código backend | ~20.185 |
| Linhas de código frontend | ~20.370 |
| Endpoints API | 59 (só em studio.py) + ~40 em outros routers |
| Arquivos de teste | 99 (1.299 testes coletados) |
| Componentes React | ~35 páginas/componentes |
| Integrações 3rd party | 6 ativas (Supabase, Claude, Gemini, Whisper, ElevenLabs, Google API) |

**Score Geral de Saúde: 5.5/10**
- Funcionalidade: 8/10 (tudo funciona)
- Escalabilidade: 3/10 (gargalos sérios)
- Segurança: 4/10 (falhas críticas)
- Manutenibilidade: 3/10 (arquivos gigantes)
- Performance Frontend: 4/10 (sem lazy loading, sem code splitting)
- Performance Backend: 5/10 (cache bom, mas funções bloqueantes)

---

## 1. PROBLEMAS CRÍTICOS (P0) — Corrigir Imediatamente

### 1.1 SEGURANÇA — Endpoints sem Autenticação
**Risco: ALTO | Impacto: Exposição de dados / manipulação**

```
GET  /api/studio/cache/stats     → SEM AUTH (expõe métricas internas)
POST /api/studio/cache/flush     → SEM AUTH (qualquer pessoa pode limpar o cache!)
```

**Correção:** Adicionar `Depends(get_current_tenant)` nesses endpoints.

### 1.2 SEGURANÇA — CORS Wildcard em Produção
**Risco: ALTO | Impacto: Qualquer site pode fazer requests à API**

```python
# server.py:210
allow_origins=os.environ.get('CORS_ORIGINS', '*').split(',')
```

O fallback `'*'` permite que qualquer domínio faça requisições autenticadas (com `allow_credentials=True`). Isso é um **vetor de ataque CSRF/XSS**.

**Correção:** Definir `CORS_ORIGINS` explicitamente no `.env` com os domínios permitidos. Remover o fallback `'*'`.

### 1.3 SEGURANÇA — Token JWT no localStorage
**Risco: MÉDIO-ALTO | Impacto: Roubo de sessão via XSS**

```javascript
// AuthContext.jsx
localStorage.setItem('agentzz_token', data.access_token);
```

Encontrado em 10+ arquivos. `localStorage` é acessível por qualquer script JavaScript na página. Se houver uma vulnerabilidade XSS, o token é comprometido.

**Mitigação:** Migrar para `httpOnly` cookies no futuro. Por agora, adicionar `Content-Security-Policy` headers.

### 1.4 SEGURANÇA — Sem Rate Limiting
**Risco: ALTO | Impacto: DDoS, abuso de API de IA, custos descontrolados**

Nenhum endpoint tem rate limiting. Um atacante pode:
- Fazer centenas de chamadas ao Claude/Gemini, gerando custos
- Gerar milhares de imagens/vídeos
- Sobrecarregar o Supabase

**Correção:** Implementar `slowapi` ou middleware customizado com limites por IP/usuário.

---

## 2. PROBLEMAS DE ESCALABILIDADE (P1)

### 2.1 BACKEND — Arquivo Monolítico `studio.py` (5.268 linhas)
**Impacto: Impossível manter, testar e escalar**

Um único arquivo contém:
- 59 endpoints
- 34 funções síncronas
- Modelos Pydantic
- Lógica de negócio (produção de vídeo, storyboard, continuidade, livro, pós-produção)
- Chamadas a APIs externas
- Manipulação de arquivos/FFmpeg

```
Linha 1-165:    Helpers + Cache + FFmpeg
Linha 166-330:  Upload + LLM sync calls
Linha 330-750:  Pre-Production Intelligence + Continuity Engine
Linha 750-815:  Pydantic Models
Linha 816-963:  Projects CRUD
Linha 963-1330: Storyboard (generate, edit, chat, approve)
Linha 1330-1560: Preview + Language Agent
Linha 1560-1945: Smart Editor + Continuity Director
Linha 1945-2020: Book Export
Linha 2020-4165: Production (screenwriter, video generation, narration)
Linha 4165-4727: Post-Production (audio engineering)
Linha 4727-5026: Multi-Language Localization
Linha 5026-5268: Scene Re-edit + Subtitles
```

**Refatoração Proposta:**
```
/app/backend/routers/
  studio/
    __init__.py          → Router principal (import sub-routers)
    projects.py          → CRUD de projetos (~150 linhas)
    storyboard.py        → Storyboard endpoints (~400 linhas)
    production.py        → Vídeo production (~500 linhas)
    post_production.py   → Audio engineering (~600 linhas)
    continuity.py        → Continuity director (~250 linhas)
    book.py              → Book/PDF export (~100 linhas)
    language.py          → Language agent (~200 linhas)
    smart_editor.py      → Smart image editing (~200 linhas)
    localization.py      → Dubbing/subtitles (~300 linhas)
    analytics.py         → Performance stats (~150 linhas)
    models.py            → Todos os Pydantic models
    helpers.py           → Funções utilitárias compartilhadas
```

### 2.2 BACKEND — Funções Síncronas Bloqueando Event Loop
**Impacto: Requests paralelos ficam enfileirados**

```python
# 34 funções def (síncronas) vs 61 async def
def _call_claude_sync(...)        # BLOQUEIA o event loop!
def _generate_scene_keyframe(...) # BLOQUEIA
def _build_production_design(...) # BLOQUEIA
def _validate_scene_continuity(...)# BLOQUEIA
```

Quando uma função síncrona é chamada dentro de um endpoint async, ela bloqueia a thread principal do FastAPI. Com 10 usuários simultâneos, o servidor para de responder.

**Correção:** Usar `asyncio.to_thread()` ou `run_in_executor()` para todas as funções CPU/IO-bound.

### 2.3 BACKEND — ThreadPoolExecutor Criado Ad-hoc
**Impacto: Thread leaking, overhead de criação/destruição**

```python
# Encontrado 6x em core/ e 5x em studio.py:
with ThreadPoolExecutor(max_workers=total) as executor:  # Novo pool a cada chamada!
```

**Correção:** Criar UM pool global compartilhado no startup da aplicação.

### 2.4 BACKEND — Dados de Projeto no JSONB do Tenant
**Impacto: Single point of failure, crescimento ilimitado**

Todos os projetos são armazenados em `tenant.settings.studio_projects[]` — um campo JSONB único. Com 52 projetos (cada um com storyboard, cenas, avatares), esse campo pode crescer para MBs, causando:
- Leituras lentas (busca o JSON inteiro para qualquer operação)
- Conflitos de escrita concorrente
- Risco de corrupção de dados

**Correção:** Migrar projetos para uma tabela dedicada `studio_projects` no Supabase, ou usar MongoDB.

### 2.5 BACKEND — Sem Paginação
**Impacto: Endpoints retornam TODOS os dados de uma vez**

```python
# server.py:72 — Busca TODOS os agentes
agents_data = supabase.table("agents").select("*").eq("tenant_id", tid).execute().data
# server.py:75 — Busca TODOS os leads
leads_data = supabase.table("leads").select("*").eq("tenant_id", tid).execute().data
# server.py:83 — Busca TODAS as conversas
all_convos = supabase.table("conversations").select("*").eq("tenant_id", tid).execute().data
```

Com 1.000+ leads ou conversas, o Dashboard vai demorar 5-10 segundos para carregar.

**Correção:** Implementar paginação cursor-based em todos os endpoints de listagem.

### 2.6 BACKEND — Sem Response Models
**Impacto: Nenhuma validação de saída, risco de vazamento de dados**

```python
# 0 endpoints usam response_model
@router.get("/projects")  # Retorna tudo sem filtro
async def list_projects(tenant=Depends(get_current_tenant)):
```

**Correção:** Definir response_model Pydantic para cada endpoint.

---

## 3. PROBLEMAS DE PERFORMANCE FRONTEND (P1)

### 3.1 PipelineView.jsx — Componente Monstruoso
**Impacto: Re-renders massivos, UX lenta**

| Métrica | Valor | Ideal |
|---------|-------|-------|
| Linhas | 3.094 | <200 |
| useState hooks | 76 | <15 |
| Inline functions no JSX | 85 | 0 |
| useMemo/useCallback | 2 | 30+ |
| Axios calls | 43 | Com cancellation |
| useEffects sem cleanup | 5 | 0 |

Cada mudança de estado causa re-render de 3.094 linhas. Com 76 estados, qualquer interação dispara dezenas de re-renders.

**Refatoração Proposta:**
```
components/studio/
  PipelineView.jsx        → Orquestrador (~200 linhas)
  CampaignTypeSelector.jsx → Seletor de tipo (~100 linhas)
  CompanySelector.jsx      → Empresa ativa (~150 linhas)
  ProjectList.jsx          → Lista de projetos (~200 linhas)
  ProjectCard.jsx          → Card individual (~100 linhas)
  NewProjectForm.jsx       → Formulário de criação (~300 linhas)
  BriefingForm.jsx         → Questionário guiado (~200 linhas)
  hooks/
    usePipelineState.js    → Custom hook para estado
    useProjectPolling.js   → Polling de status
    useCompanies.js        → CRUD de empresas
```

### 3.2 ZERO Lazy Loading de Imagens
**Impacto: Storyboard com 20 cenas x 6 frames = 120 imagens carregadas simultaneamente**

```jsx
// StoryboardEditor.jsx — Nenhum loading="lazy"
<img src={resolveImageUrl(frame.image_url)} className="..." />
```

**Correção imediata:**
```jsx
<img src={resolveImageUrl(frame.image_url)} loading="lazy" className="..." />
```

### 3.3 ZERO Code Splitting
**Impacto: Bundle inicial carrega TUDO, mesmo páginas nunca visitadas**

```javascript
// App.js — Imports estáticos
import Marketing from './pages/Marketing';      // 2.422 linhas
import MarketingStudio from './pages/MarketingStudio';
import InteractiveBook from './pages/InteractiveBook';
```

**Correção:**
```javascript
const Marketing = React.lazy(() => import('./pages/Marketing'));
const MarketingStudio = React.lazy(() => import('./pages/MarketingStudio'));
```

### 3.4 ZERO Error Boundaries
**Impacto: Um erro em qualquer componente crasha a aplicação inteira**

Nenhum `ErrorBoundary` encontrado em todo o frontend. Se um componente falhar (ex: dados inesperados da API), a tela fica branca.

### 3.5 StoryboardEditor — Sem Virtualização/Lazy Panels
**Impacto: 20+ painéis renderizados com todas as imagens, filmstrips e toolbars**

Conforme reportado pelo usuário, o storyboard fica pesado. Solução: implementar expansão sob demanda (já discutido).

### 3.6 Sem AbortController em Chamadas API
**Impacto: Memory leaks, requests órfãos**

```javascript
// 43 chamadas axios, 0 AbortController
// Se o usuário navega para outra página durante uma chamada,
// o callback tenta fazer setState em componente desmontado
```

---

## 4. PROBLEMAS DE MANUTENIBILIDADE (P2)

### 4.1 Scripts Mortos no Backend
**Impacto: 45KB de código não utilizado, confusão**

```
generate_24s_commercial.py   (8.232 bytes)
generate_24s_pro.py          (9.093 bytes)
generate_cargo_van_video.py  (2.697 bytes)
generate_new_commercial.py   (5.509 bytes)
generate_video_demo.py       (3.713 bytes)
compare_models.py            (5.000 bytes)
migrate_storage.py           (3.624 bytes)
reprocess_video.py           (7.457 bytes)
```

**Correção:** Mover para `/app/backend/scripts/` ou deletar.

### 4.2 Testes com Erros de Coleta
**Impacto: 2 arquivos de teste não executam**

```
ERROR tests/test_iteration103_subtitles_regen.py
ERROR tests/test_music_library_iteration28.py
```

### 4.3 99 Arquivos de Teste — Nomenclatura Inconsistente
Nomes como `test_iteration43_...`, `test_iteration84_...` são úteis para rastrear iterações mas dificultam encontrar testes por funcionalidade.

**Sugestão:** Reorganizar em:
```
tests/
  test_projects.py
  test_storyboard.py
  test_production.py
  test_continuity.py
  test_auth.py
  ...
```

---

## 5. ARQUITETURA — Pontos de Atenção

### 5.1 Banco de Dados Híbrido (Supabase + MongoDB)
**Complexidade:** Alta. Dois sistemas de banco para manter, duas lógicas de conexão.

MongoDB é usado apenas para marketing (`routers/marketing.py`). Supabase para todo o resto.

**Recomendação:** Avaliar se vale consolidar em um único banco.

### 5.2 Sem WebSocket para Updates em Tempo Real
Toda a comunicação de status (geração de storyboard, produção de vídeo) usa **polling HTTP** com `setTimeout`. Isso gera:
- Até 120 requests por operação (polling a cada 4s por 8 min)
- Latência de até 4s entre o término real e a atualização na UI

**Correção futura:** WebSocket ou Server-Sent Events (SSE) para updates de progresso.

### 5.3 Sem API Versioning
Nenhum `/v1/` ou `/v2/` nos endpoints. Mudanças breaking vão afetar todos os clientes simultaneamente.

### 5.4 Middleware Insuficiente
Apenas 1 middleware (CORS). Faltam:
- Request logging (tempo de resposta por endpoint)
- Error handling global
- Rate limiting
- Request ID tracking
- Compression (gzip)

---

## 6. PLANO DE AÇÃO PRIORIZADO

### FASE 1 — Segurança (1-2 dias)
| # | Ação | Esforço |
|---|------|---------|
| 1 | Adicionar auth nos endpoints de cache | 10 min |
| 2 | Configurar CORS_ORIGINS explícito | 10 min |
| 3 | Implementar rate limiting (slowapi) | 2h |
| 4 | Adicionar Content-Security-Policy headers | 30 min |
| 5 | Validar upload file sizes | 30 min |

### FASE 2 — Performance Frontend (2-3 dias)
| # | Ação | Esforço |
|---|------|---------|
| 1 | Lazy loading de imagens (loading="lazy") | 30 min |
| 2 | Storyboard panels expandíveis (lazy expand) | 2h |
| 3 | Code splitting com React.lazy | 1h |
| 4 | Error Boundaries | 1h |
| 5 | AbortController em chamadas axios | 2h |
| 6 | useMemo/useCallback em componentes críticos | 3h |

### FASE 3 — Refatoração Backend (3-5 dias)
| # | Ação | Esforço |
|---|------|---------|
| 1 | Split studio.py em 10+ módulos | 1 dia |
| 2 | Converter funções sync → async | 4h |
| 3 | ThreadPoolExecutor global | 1h |
| 4 | Response models Pydantic | 4h |
| 5 | Paginação em endpoints de listagem | 2h |
| 6 | Limpar scripts mortos | 30 min |

### FASE 4 — Refatoração Frontend (3-5 dias)
| # | Ação | Esforço |
|---|------|---------|
| 1 | Split PipelineView.jsx | 1 dia |
| 2 | Split DirectedStudio.jsx | 1 dia |
| 3 | Custom hooks para estado compartilhado | 4h |
| 4 | Virtualização de listas (react-window) | 2h |
| 5 | Reorganizar testes por funcionalidade | 2h |

### FASE 5 — Arquitetura (Futuro)
| # | Ação | Esforço |
|---|------|---------|
| 1 | Migrar projetos de JSONB para tabela dedicada | 1 dia |
| 2 | WebSocket/SSE para updates de progresso | 1 dia |
| 3 | API versioning (v1/) | 2h |
| 4 | Middleware stack completo | 4h |
| 5 | Consolidar estratégia de banco (Supabase vs MongoDB) | Análise |

---

## 7. MÉTRICAS DE MONITORAMENTO SUGERIDAS

Para acompanhar a saúde do sistema após as melhorias:

1. **Tempo de resposta P95** por endpoint
2. **Taxa de erro** (4xx, 5xx) por hora
3. **Uso de memória** do processo FastAPI
4. **Custo de API** (Claude, Gemini, ElevenLabs) por dia
5. **Bundle size** do frontend (target: <500KB gzipped)
6. **Largest Contentful Paint** (target: <2.5s)
7. **Time to Interactive** (target: <3.5s)

---

## 8. PONTOS FORTES DO SISTEMA

1. **Cache System (4 camadas):** Bem arquitetado com ImageCache, ProjectCache, LLMCache e Frontend SWR
2. **Tratamento de erros no backend:** 89 HTTPException, 132 log statements em studio.py
3. **Sem bare except:** Nenhum `except:` genérico encontrado — boas práticas
4. **Cleanup de storyboards stale:** Recuperação automática no startup
5. **Flush on shutdown:** Cache persistido antes do servidor desligar
6. **Design System consistente:** Tema dark luxury bem aplicado em toda a UI
7. **Testes extensivos:** 1.299 testes coletados (mesmo que precisem reorganização)
8. **Feature completeness:** Pipeline completo de produção (roteiro → vídeo final)

---

*Relatório gerado por análise estática e dinâmica do codebase AgentZZ v0.4.0*
