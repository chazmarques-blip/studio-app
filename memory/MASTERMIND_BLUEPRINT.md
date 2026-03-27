# MASTERMIND ENGINEERING BLUEPRINT — AgentZZ
## Protocolo de Engenharia de Software de Classe Mundial
### Revisão Final | 27/03/2026

---

## PAINEL DE ESPECIALISTAS CONSULTADOS

| Princípio | Fonte | Aplicação no AgentZZ |
|-----------|-------|---------------------|
| **Clean Architecture** | Robert C. Martin (Uncle Bob) | 4 camadas independentes |
| **Domain-Driven Design** | Eric Evans | Bounded contexts por domínio |
| **12-Factor App** | Heroku/Adam Wiggins | Config, logs, processos |
| **Site Reliability Engineering** | Google SRE | Observability, error budgets |
| **Circuit Breaker** | Michael Nygard (Release It!) | Resiliência de providers AI |
| **API-First Design** | Stripe Engineering | Idempotência, error taxonomy |
| **Mobile-First Architecture** | Google/Apple HIG | Touch targets, offline-first |
| **CQRS** | Greg Young | Separação leitura/escrita |
| **Repository Pattern** | Martin Fowler | Abstração total do banco |
| **Provider/Adapter Pattern** | Gang of Four | Troca de IA sem alterar código |

---

## O QUE FALTAVA NO PLANO ANTERIOR

Após análise mastermind, identifiquei **9 lacunas críticas** que separam um sistema "bom" de um sistema de classe mundial:

### 1. CIRCUIT BREAKER PARA PROVIDERS DE IA
**Por que é crítico:** O AgentZZ depende de 5 providers externos (Claude, Gemini, Sora, ElevenLabs, Whisper). Se UM falhar, a feature inteira morre. Sem circuit breaker, o sistema fica fazendo requests para um serviço morto, acumulando timeouts de 120s cada.

**O que o mastermind recomenda:**
```python
# providers/ai/circuit_breaker.py
class CircuitBreaker:
    """Se um provider falha 3x seguidas, ativa o circuito.
    Tenta fallback automático. Testa recovery a cada 60s."""

    CLOSED = "closed"      # Funcionando normal
    OPEN = "open"          # Provider morto, usando fallback
    HALF_OPEN = "half_open" # Testando se voltou

    def __init__(self, primary, fallback, failure_threshold=3, recovery_timeout=60):
        self.primary = primary
        self.fallback = fallback
        self.state = self.CLOSED
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None

    async def call(self, method, *args, **kwargs):
        if self.state == self.OPEN:
            if self._should_attempt_recovery():
                self.state = self.HALF_OPEN
            else:
                return await getattr(self.fallback, method)(*args, **kwargs)

        try:
            result = await getattr(self.primary, method)(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            logger.warning(f"Circuit breaker: {self.primary.__class__.__name__} failed ({self.failures}/{self.failure_threshold}): {e}")
            return await getattr(self.fallback, method)(*args, **kwargs)
```

**Impacto:** Se Claude cair, o sistema automaticamente usa Gemini para texto. Sem downtime para o usuário.

### 2. IDEMPOTÊNCIA PARA OPERAÇÕES CARAS
**Por que é crítico:** Gerar vídeo com Sora custa US$0.50+. Se o usuário clica 2x no botão, ou a rede falha e o frontend retenta, o sistema gera 2 vídeos idênticos. Dinheiro jogado fora.

**O que o mastermind recomenda:**
```python
# core/idempotency.py
class IdempotencyGuard:
    """Previne operações duplicadas usando chave única."""

    _active_operations = {}  # operation_key -> result

    @classmethod
    async def execute(cls, key: str, operation_fn, ttl=3600):
        if key in cls._active_operations:
            return cls._active_operations[key]  # Retorna resultado anterior

        result = await operation_fn()
        cls._active_operations[key] = result

        # Limpar após TTL
        asyncio.get_event_loop().call_later(ttl, lambda: cls._active_operations.pop(key, None))
        return result
```

```python
# Uso no endpoint:
@router.post("/projects/{id}/production/start")
async def start_production(id: str, request: StartProductionRequest):
    key = f"production:{id}:{request.hash()}"
    return await IdempotencyGuard.execute(key, lambda: _do_production(id, request))
```

### 3. OBSERVABILIDADE (Structured Logging + Request Tracing)
**Por que é crítico:** Hoje, se um usuário reporta "o vídeo não gerou", não há como rastrear o que aconteceu. Os logs são texto plano sem correlação. Impossível debugar em produção com 100+ usuários.

**O que o mastermind recomenda:**
```python
# core/middleware.py
import uuid, time

class ObservabilityMiddleware:
    """Cada request recebe um ID único. Logs estruturados em JSON."""

    async def __call__(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        logger.info({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000),
            "user_id": getattr(request.state, "user_id", None),
        })

        response.headers["X-Request-Id"] = request_id
        return response
```

**Impacto:** Cada request é rastreável. Podemos medir: qual endpoint é mais lento, qual provider de IA falha mais, quanto tempo cada operação demora.

### 4. ERROR TAXONOMY (Erros Padronizados)
**Por que é crítico:** Hoje, cada endpoint retorna erros em formato diferente. O frontend não sabe se é erro do usuário (400), do servidor (500), ou do provider (502). Impossível mostrar mensagens úteis.

**O que o mastermind recomenda (padrão Stripe):**
```python
# core/exceptions.py
class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        super().__init__(code="validation_error", message=message, status=422, details={"field": field})

class ProviderError(AppError):
    def __init__(self, provider: str, message: str):
        super().__init__(code="provider_error", message=f"{provider}: {message}", status=502)

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(code="not_found", message=f"{resource} {id} not found", status=404)

# Handler global
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(status_code=exc.status, content={
        "error": {"code": exc.code, "message": exc.message, "details": exc.details}
    })
```

**Resposta consistente:**
```json
{
  "error": {
    "code": "provider_error",
    "message": "ElevenLabs: rate limit exceeded",
    "details": {"provider": "elevenlabs", "retry_after": 60}
  }
}
```

### 5. HEALTH CHECK PROFUNDO
**Por que é crítico:** O health check atual retorna `{"status": "ok"}` mesmo se o Supabase estiver fora, se o Claude não responder, ou se o disco estiver cheio. Em Kubernetes, o pod seria considerado saudável mesmo quebrado.

**O que o mastermind recomenda:**
```python
@api_router.get("/health")
async def health():
    """Health raso — para load balancer (rápido)."""
    return {"status": "ok"}

@api_router.get("/health/deep")
async def deep_health():
    """Health profundo — para monitoring (verifica todas as dependências)."""
    checks = {}

    # Supabase
    try:
        supabase.table("tenants").select("id").limit(1).execute()
        checks["supabase"] = {"status": "ok"}
    except Exception as e:
        checks["supabase"] = {"status": "error", "detail": str(e)[:100]}

    # AI Providers
    for name, key_var in [("claude", "ANTHROPIC_API_KEY"), ("gemini", "GEMINI_API_KEY"),
                           ("elevenlabs", "ELEVENLABS_API_KEY"), ("openai", "OPENAI_API_KEY")]:
        checks[name] = {"status": "ok" if os.environ.get(key_var) else "missing_key"}

    # Disk
    import shutil
    disk = shutil.disk_usage("/tmp")
    checks["disk"] = {"status": "ok" if disk.free > 500_000_000 else "low", "free_gb": round(disk.free / 1e9, 1)}

    # Cache
    from core.cache import get_cache_stats
    checks["cache"] = get_cache_stats()

    overall = "ok" if all(c.get("status") == "ok" for c in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
```

### 6. OFFLINE-FIRST PWA COM SYNC QUEUE
**Por que é crítico para mobile:** Usuário no metrô edita um painel do storyboard. A conexão cai. Sem offline-first, a edição se perde. Com offline-first, ela é guardada localmente e sincronizada quando a conexão volta.

**O que o mastermind recomenda:**
```javascript
// service-worker.js — Estratégias por tipo de recurso
// App Shell: Cache First (instantâneo)
// API Data: Network First, fallback to cache
// Imagens: Cache First com revalidação
// Operações de escrita: Background Sync queue

// frontend/src/api/offlineQueue.js
class OfflineQueue {
  constructor() {
    this.queue = JSON.parse(localStorage.getItem('offline_queue') || '[]');
  }

  add(request) {
    this.queue.push({ ...request, timestamp: Date.now() });
    localStorage.setItem('offline_queue', JSON.stringify(this.queue));
  }

  async flush() {
    while (this.queue.length > 0) {
      const req = this.queue[0];
      try {
        await api[req.method](req.url, req.data);
        this.queue.shift();
        localStorage.setItem('offline_queue', JSON.stringify(this.queue));
      } catch {
        break; // Ainda offline, para de tentar
      }
    }
  }
}

// Detectar reconexão
window.addEventListener('online', () => offlineQueue.flush());
```

### 7. OTIMIZAÇÃO DE IMAGENS PARA MOBILE
**Por que é crítico:** 73 referências a `.png` no frontend. PNG é 3-5x maior que WebP. Em mobile com 4G, cada imagem extra de 500KB = 1s a mais de loading.

**O que o mastermind recomenda:**
```javascript
// utils/imageOptimizer.js
export function optimizedImageUrl(url, { width, quality = 75, format = 'webp' } = {}) {
  if (!url) return url;

  // Supabase Storage suporta transformações via URL
  if (url.includes('supabase')) {
    const params = new URLSearchParams();
    if (width) params.set('width', width);
    params.set('quality', quality);
    params.set('format', format);
    return `${url}?${params.toString()}`;
  }
  return url;
}

// Uso no componente:
<img
  src={optimizedImageUrl(frame.image_url, { width: 400 })}
  loading="lazy"
  decoding="async"
  alt={frame.label}
/>
```

### 8. TOUCH TARGETS PARA MOBILE (Apple/Google HIG)
**Por que é crítico:** Encontrei **8 botões de 24px (h-6)** no StoryboardEditor. Apple exige mínimo de **44px**. Google exige **48px**. Botões de 24px são impossíveis de clicar com o dedo no celular.

**O que o mastermind recomenda:**
```css
/* Regra global para mobile */
@media (pointer: coarse) {
  button, a, [role="button"] {
    min-height: 44px;
    min-width: 44px;
  }
}
```

### 9. FEATURE FLAGS PARA ROLLOUT SEGURO
**Por que é crítico:** Ao migrar o banco de JSONB para tabelas, se algo falhar em produção, precisa de rollback instantâneo. Feature flags permitem ligar/desligar a nova lógica sem deploy.

**O que o mastermind recomenda:**
```python
# core/feature_flags.py
FLAGS = {
    "use_new_db_schema": False,    # Migração de banco
    "enable_circuit_breaker": True,
    "enable_offline_sync": False,
    "enable_webp_optimization": True,
    "enable_deep_health": True,
}

def is_enabled(flag: str) -> bool:
    return FLAGS.get(flag, False)
```

```python
# Uso no service:
if is_enabled("use_new_db_schema"):
    project = await project_repo.get(project_id)  # Nova tabela
else:
    project = _get_project_from_jsonb(tenant_id, project_id)  # JSONB legado
```

---

## PLANO FINAL REVISADO — 8 FASES

### FASE 0: Foundation (1h)
- [ ] Fix build (`@/lib/i18n`)
- [ ] Criar `/core/config.py` centralizado (todas as env vars validadas no startup)
- [ ] Criar `/core/exceptions.py` (error taxonomy)
- **Teste:** Build OK. App inicia com config validada.

### FASE 1: Segurança + Observabilidade (2-3h)
- [ ] Auth em endpoints abertos
- [ ] CORS restritivo
- [ ] GZip middleware
- [ ] Rate limiting (slowapi) nos endpoints AI
- [ ] ObservabilityMiddleware (request_id + duração + structured logs)
- [ ] Deep health check (`/health/deep`)
- **Teste:** Logs estruturados no terminal. Health check mostra status de cada dependência.

### FASE 2: Provider Pattern + Circuit Breaker (4-5h)
- [ ] Criar interfaces base (`TextProvider`, `ImageProvider`, `VideoProvider`, `VoiceProvider`, `STTProvider`)
- [ ] Implementar `ClaudeProvider`, `GeminiProvider` (text)
- [ ] Implementar `GeminiImageProvider` (image)
- [ ] Implementar `Sora2Provider` (video)
- [ ] Implementar `ElevenLabsProvider`, `OpenAITTSProvider` (voice)
- [ ] Implementar `WhisperProvider` (STT)
- [ ] Circuit breaker com fallback automático (Claude → Gemini para texto)
- [ ] Factory (`get_text_provider()`) configurável via env
- [ ] Substituir todas as chamadas hardcoded em studio.py
- [ ] Idempotency guard para operações caras (vídeo, pós-produção)
- **Teste:** Gerar storyboard funciona. Simular falha do Claude → fallback para Gemini automático. Duplo-click não gera 2x.

### FASE 3: Backend Modular (4-6h)
- [ ] Criar estrutura `/api/v1/studio/` com sub-routers
- [ ] Mover endpoints para módulos (projects, storyboard, production, etc.)
- [ ] Criar `/api/schemas/` com request/response models separados
- [ ] Extrair lógica para `/services/studio/`
- [ ] Feature flags para controlar migração gradual
- [ ] Remover scripts mortos → `/scripts/`
- **Teste:** Todos os endpoints respondem igual. URLs não mudaram. Tests passam.

### FASE 4: Migração de Banco de Dados (3-4h)
- [ ] Criar tabelas no Supabase (projects, scenes, panels, characters, outputs)
- [ ] Criar `/db/repositories/` (project_repo, scene_repo, panel_repo)
- [ ] Script de migração: JSONB → tabelas (com validação de integridade)
- [ ] Feature flag `use_new_db_schema` para rollback instantâneo
- [ ] Compatibilidade retroativa (lê das tabelas, fallback para JSONB)
- **Teste:** Projetos existentes aparecem. CRUD funciona. Feature flag liga/desliga sem erro.

### FASE 5: Performance Frontend (3-4h)
- [ ] Code splitting (React.lazy em todas as rotas)
- [ ] `loading="lazy"` + `decoding="async"` em todas as `<img>`
- [ ] Image optimization (WebP via Supabase transform URLs)
- [ ] Error Boundary global
- [ ] Storyboard com painéis expandíveis (lazy expand)
- [ ] Touch targets ≥ 44px para mobile (media query `pointer: coarse`)
- **Teste:** Lighthouse > 70. Storyboard fluido. Botões clicáveis no celular.

### FASE 6: Frontend Modular + API Layer (4-6h)
- [ ] Criar `/api/client.js` (axios instance + interceptors)
- [ ] Criar `/api/studioApi.js` (todas as chamadas isoladas)
- [ ] Split PipelineView.jsx → 6-8 componentes
- [ ] Split StoryboardEditor.jsx → 4-5 componentes
- [ ] Split DirectedStudio.jsx → 3-4 componentes
- [ ] Custom hooks com AbortController
- [ ] Debounce em inputs de busca/chat
- **Teste:** Todos os fluxos funcionam. Componentes < 200 linhas cada.

### FASE 7: PWA + App Ready (3-4h)
- [ ] Criar `manifest.json` (nome, ícones, tema, orientation: portrait)
- [ ] Service Worker com estratégias por recurso (Cache First / Network First)
- [ ] Offline Queue para operações de escrita
- [ ] Splash screen e ícones (192px, 512px)
- [ ] Registrar SW no index.js
- [ ] Prefetching de dados da próxima tela provável
- **Teste:** App instalável no celular. Shell carrega offline. Edições offline sincronizam ao reconectar.

---

## COMPARAÇÃO: ANTES vs DEPOIS

| Dimensão | Antes | Depois (8 Fases) |
|----------|-------|-------------------|
| **Manutenibilidade** | 1 arquivo de 5.268 linhas | 40+ módulos de <200 linhas |
| **Trocar provider IA** | Editar 12+ locais, risco alto | Mudar 1 variável de config |
| **Provider IA cai** | Feature inteira morre | Circuit breaker → fallback automático |
| **Query de 1 projeto** | Busca TODOS os projetos do tenant | Query direto por ID (O(1)) |
| **Operação duplicada** | Gera 2 vídeos = $1.00 perdido | Idempotency guard bloqueia |
| **Debug em produção** | Logs texto plano, sem correlação | Request ID + structured JSON logs |
| **Error responses** | Formato diferente por endpoint | Padrão Stripe universal |
| **Build de produção** | Quebrado | Funcionando + CI-ready |
| **Bundle inicial** | ~15 MB | ~400 KB (gzip + code split) |
| **Primeiro load (4G)** | 8-12 segundos | 2-3 segundos |
| **Storyboard 20 cenas** | Trava / lento | Fluido (expand on demand) |
| **Botões no celular** | 24px (impossível clicar) | 44px+ (Apple/Google HIG) |
| **App mobile** | Impossível | PWA instalável + Capacitor ready |
| **Offline** | Perde dados | Fila local + sync automático |
| **Imagens** | PNG sem otimização | WebP + lazy load + responsive |
| **Novo dev entende** | 4-8 horas | 30 minutos |
| **Rollback seguro** | Sem mecanismo | Feature flags instantâneos |
| **100 usuários simultâneos** | Servidor bloqueia | Responde normalmente |
| **Health monitoring** | `{"status":"ok"}` sempre | Status de CADA dependência |

---

## STACK TECNOLÓGICA FINAL

### Backend
- **Framework:** FastAPI (async-first)
- **ORM/DB:** Supabase (PostgreSQL) via repositórios isolados
- **Cache:** 4 camadas (já existente, bom) + Redis (futuro)
- **Queue:** FastAPI BackgroundTasks (agora) → Celery + Redis (escala)
- **AI:** Provider Pattern com Circuit Breaker + Factory
- **Storage:** Supabase Storage com image transforms
- **Logging:** Structured JSON logs com request tracing
- **Security:** JWT + Rate Limiting + CORS + CSP

### Frontend
- **Framework:** React 19 com code splitting
- **State:** Custom hooks + Context (já existente)
- **Styling:** Tailwind CSS + shadcn/ui
- **API Layer:** Axios instance centralizada + interceptors
- **PWA:** Service Worker + Web App Manifest + Offline Queue
- **Images:** WebP + lazy loading + responsive
- **Mobile:** Touch targets 44px+ + pointer: coarse media queries

### Infraestrutura
- **Container:** Docker multi-stage build
- **Deploy:** Kubernetes (já existente via Emergent)
- **CDN:** Supabase Storage CDN para mídia
- **Monitoring:** Structured logs + deep health checks

---

## CONCLUSÃO DO MASTERMIND

Este plano segue os protocolos de:
- **SOLID** (Single Responsibility em cada módulo)
- **12-Factor App** (Config, Logs, Processos, Dependências)
- **Clean Architecture** (4 camadas independentes)
- **API-First** (Stripe patterns: idempotência, error taxonomy)
- **SRE** (Observabilidade, circuit breakers, health checks profundos)
- **Mobile-First** (PWA, offline-first, touch targets, image optimization)
- **DDD** (Bounded contexts por domínio: Studio, Agents, Campaigns)

**Nenhuma funcionalidade existente será removida.** Cada fase é incremental, testável e reversível via feature flags.

O resultado é um sistema que qualquer programador entende em 30 minutos, que aguenta 100+ usuários simultâneos, que funciona offline no celular, e que permite trocar qualquer provider de IA mudando 1 variável de configuração.
