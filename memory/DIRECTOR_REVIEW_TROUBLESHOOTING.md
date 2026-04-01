# Director Review - Análise Profunda e Correções

## 🔍 Problemas Identificados e Resolvidos

### Problema 1: Erro de Sintaxe Python (CRÍTICO) ✅ RESOLVIDO
**Sintoma:** `SyntaxError: expected 'except' or 'finally' block`

**Causa Raiz:**
- Quando adicionei o retry loop, sobrou uma string de documentação no meio do código (linha 174)
- Isso quebrou a estrutura do try-except

**Código Problemático:**
```python
                return fallback
    """Same as _review_scene_batch but updates progress in real-time with WATCHDOG timestamps."""
    from datetime import datetime, timezone
```

**Correção Aplicada:**
```python
                return fallback
    
    # Should never reach here
    return []


async def _review_scene_batch_with_progress(...):
    """Same as _review_scene_batch but updates progress in real-time with WATCHDOG timestamps."""
    from datetime import datetime, timezone
```

---

### Problema 2: Função Não Definida (CRÍTICO) ✅ RESOLVIDO
**Sintoma:** `name '_review_scene_batch_with_progress' is not defined`

**Causa Raiz:**
- A string de documentação no meio do código fez o Python pensar que a função anterior ainda não havia terminado
- Isso impediu que `_review_scene_batch_with_progress` fosse definida como uma função separada

**Correção:** Separação correta das funções com quebras de linha adequadas

---

### Problema 3: Retry Logic Incompleto ⚠️ PARCIALMENTE RESOLVIDO

**Issues Identificados:**
1. **Exponential Backoff OK**: 2s → 4s → 8s → 16s → 32s ✅
2. **Max Retries OK**: 5 tentativas por batch ✅
3. **Fallback OK**: Retorna score 50 em caso de falha total ✅
4. **MAS**: Anthropic API pode ter rate limits que causam falhas intermitentes

**Recomendações Adicionais:**
- Adicionar jitter ao exponential backoff para evitar thundering herd
- Implementar circuit breaker se >50% dos batches falharem
- Monitorar rate limits do Anthropic API

---

## 🛠️ Arquitetura Atual do Sistema

```
┌──────────────────────────────────────────────────────┐
│  Frontend: DirectorPreview.jsx                       │
│  - Polling a cada 5s                                 │
│  - Watchdog: Auto-resume após 90s sem progresso     │
│  - Botão manual "Retomar"                           │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│  Backend: director.py                                │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ _review_scene_batch(...)                    │   │
│  │  - Retry loop (5x com exponential backoff) │   │
│  │  - Anthropic Claude API call                │   │
│  │  - JSON validation                          │   │
│  │  - Fallback on total failure                │   │
│  └─────────────────────────────────────────────┘   │
│                 │                                    │
│                 ▼                                    │
│  ┌─────────────────────────────────────────────┐   │
│  │ _review_scene_batch_with_progress(...)      │   │
│  │  - Wraps _review_scene_batch                │   │
│  │  - Updates MongoDB progress                 │   │
│  │  - Timestamps (last_update) for watchdog    │   │
│  └─────────────────────────────────────────────┘   │
│                 │                                    │
│                 ▼                                    │
│  ┌─────────────────────────────────────────────┐   │
│  │ director_review(...)                        │   │
│  │  - Creates batches of 4 scenes              │   │
│  │  - Processes 2 batches in parallel          │   │
│  │  - Aggregates results                       │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ /resume endpoint                            │   │
│  │  - Detects stuck reviews (5min timeout)     │   │
│  │  - Resumes from last completed batch        │   │
│  │  - Merges old + new reviews                 │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
                 │
                 ▼
         [MongoDB Progress State]
```

---

## 📊 Fluxo de Dados

### Normal Flow (Sucesso):
```
1. User clica "Iniciar Revisão"
2. Backend cria batches [1,2,3]
3. Processa batch 1-2 em paralelo
   └─ Cada batch: 5 tentativas max
   └─ Cada tentativa: exponential backoff se falhar
4. Atualiza progress em MongoDB (current_batch, scenes_processed, last_update)
5. Frontend poll detecta progresso
6. Batch 3 processa
7. Finaliza: salva review completo em MongoDB
```

### Error Flow (com Watchdog):
```
1. User clica "Iniciar Revisão"
2. Backend processa batch 1 OK
3. Batch 2 trava (API timeout)
   └─ Retry 1: falha
   └─ Retry 2: falha
   └─ Retry 3: falha
   └─ Retry 4: falha
   └─ Retry 5: falha
   └─ Retorna fallback (score 50)
4. Progress para de atualizar
5. Frontend watchdog detecta (90s sem mudança)
6. Chama POST /resume automaticamente
7. Resume continua do batch 3
8. Finaliza com merge de resultados
```

---

## 🔧 Configurações Críticas

### Timeouts e Limits:
```python
BATCH_SIZE = 4  # Scenes per batch
MAX_RETRIES = 5  # Per batch
ANTHROPIC_TIMEOUT = 300  # 5 minutes
PARALLEL_BATCHES = 2  # Process 2 at a time
FRONTEND_POLL_INTERVAL = 5000  # 5 seconds
FRONTEND_WATCHDOG_TIMEOUT = 90  # 90 seconds
BACKEND_WATCHDOG_TIMEOUT = 300  # 5 minutes
```

### Exponential Backoff:
```python
wait_time = 2 ** (attempt + 1)
# Attempt 1: 2^1 = 2s
# Attempt 2: 2^2 = 4s
# Attempt 3: 2^3 = 8s
# Attempt 4: 2^4 = 16s
# Attempt 5: 2^5 = 32s
```

---

## 🧪 Como Testar

### Teste 1: Sucesso Normal
```bash
# No frontend:
1. Ir para Step 5 (Diálogos)
2. Clicar "Director's Preview"
3. Clicar "Iniciar Revisão"
4. Aguardar conclusão (monitorar progress bar)
```

### Teste 2: Watchdog Automático
```bash
# Simular travamento:
1. Durante a revisão, matar temporariamente o processo (CTRL+C no backend)
2. Frontend deve detectar após 90s
3. Toast: "Revisão travada detectada. Retomando..."
4. Restartar backend
5. Sistema deve retomar automaticamente
```

### Teste 3: Retomada Manual
```bash
1. Durante revisão, observar progress
2. Se parar, clicar botão "Retomar" (amarelo)
3. Deve continuar de onde parou
```

---

## 📝 Logs Importantes

### Sucesso:
```
INFO - Batch 1: Attempt 1/5
INFO - Batch 1: ✅ Reviewed 4 scenes successfully
INFO - Processing batches 1-2/3...
INFO - ✅ Director review complete: Score 85%
```

### Retry:
```
ERROR - Batch 2: Attempt 1 failed: timeout
INFO - Batch 2: Retrying in 2s...
ERROR - Batch 2: Attempt 2 failed: timeout
INFO - Batch 2: Retrying in 4s...
INFO - Batch 2: ✅ Reviewed 4 scenes successfully  # Success on retry!
```

### Watchdog:
```
WARN - ⚠️ WATCHDOG TRIGGERED for project_id
INFO - Resuming from batch 2/3, 4 scenes already done
INFO - RESUME: Processing batches 2-3/3...
INFO - ✅ WATCHDOG RESUME COMPLETE: Score 82%
```

---

## ⚠️ Problemas Conhecidos e Limitações

### 1. Anthropic API Rate Limits
**Sintoma:** Falhas intermitentes mesmo com retry
**Mitigação:** Exponential backoff + fallback scores
**Solução Futura:** Implementar rate limit tracking

### 2. Muito Polling
**Sintoma:** Frontend faz muitas requisições GET /progress
**Mitigação:** Intervalo de 5s (era 2s)
**Solução Futura:** WebSockets para push updates

### 3. Fallback Scores Podem Distorcer Média
**Sintoma:** Se muitos batches falharem, score final fica artificialmente em 50%
**Mitigação:** Fallback só após 5 tentativas
**Solução Futura:** Permitir skip de cenas problemáticas

---

## 🚀 Melhorias Futuras Sugeridas

1. **Circuit Breaker**: Se >50% batches falharem, pausar e alertar
2. **Jitter no Backoff**: Adicionar randomização para evitar thundering herd
3. **WebSockets**: Substituir polling por push updates
4. **Rate Limit Tracking**: Monitorar e respeitar limites da Anthropic API
5. **Persistent Queue**: Usar Redis/Celery para jobs de longa duração
6. **Detailed Metrics**: Dashboard com tempo médio, taxa de sucesso, retries

---

**Status:** ✅ Sistema operacional após correções de sintaxe
**Última Atualização:** 2026-04-01 22:15 UTC
**Versão:** 2.0 (com Watchdog)
