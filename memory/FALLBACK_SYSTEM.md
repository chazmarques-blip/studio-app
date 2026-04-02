# 🔄 **Intelligent Fallback System - StudioX Character Generation**

## 📋 Overview

Sistema implementado para **recuperação automática de erros** na geração de personagens. Quando o Gemini Nano Banana retorna erro 502/503/timeout, o sistema automaticamente tenta estratégias alternativas.

---

## 🎯 Problema Resolvido

**Antes:**
```
❌ Erro 502 → Geração falha completamente
❌ Usuário precisa tentar manualmente várias vezes
❌ Sem estratégia de fallback
```

**Depois:**
```
✅ Erro 502 → Sistema tenta automaticamente 3 estratégias diferentes
✅ Exponential backoff + jitter para evitar sobrecarga
✅ Circuit breaker para proteger serviços
✅ Logs detalhados para debug
```

---

## 🔧 Arquitetura

### **Componentes:**

1. **FallbackAgent** (`/app/backend/core/fallback_agent.py`)
   - Gerencia retries inteligentes
   - Classifica tipos de erro (rate limit, server error, timeout, etc.)
   - Aplica exponential backoff com jitter
   - Implementa circuit breaker pattern

2. **FallbackStrategy**
   - Define estratégias alternativas com parâmetros customizáveis
   - Cada estratégia tem seus próprios retries e delays

3. **CircuitBreaker**
   - Evita sobrecarregar serviços que estão falhando
   - Estados: CLOSED → OPEN → HALF_OPEN
   - Auto-recuperação após timeout

---

## 📊 Estratégias de Fallback

### **Strategy 1: Full Detailed Prompt** (PRIMARY)
```python
- Descrição: Prompt completo e detalhado
- Retries: 2
- Base delay: 2s
- Quando usa: Primeira tentativa sempre
```

### **Strategy 2: Simplified Prompt** (502/503 FALLBACK)
```python
- Descrição: Prompt simplificado para reduzir carga
- Retries: 2  
- Base delay: 4s
- Quando usa: Após falha da Strategy 1
```

### **Strategy 3: Batch Delay + Minimal** (RATE LIMIT PROTECTION)
```python
- Descrição: Delay aleatório (3-8s) + prompt mínimo
- Retries: 1
- Base delay: 6s
- Quando usa: Última tentativa, proteção contra rate limit
```

---

## 🔬 Classificação de Erros

O sistema classifica automaticamente os erros para aplicar a estratégia correta:

| Tipo de Erro | Códigos | Retryable? | Delay Multiplier |
|---|---|---|---|
| **RATE_LIMIT** | 429, "rate limit", "quota" | ✅ Sim | 2x |
| **SERVER_ERROR** | 500, 502, 503, 504, "gateway" | ✅ Sim | 1.5x |
| **TIMEOUT** | "timeout", "timed out" | ✅ Sim | 1x |
| **AUTHENTICATION** | 401, 403, "unauthorized" | ❌ Não | N/A |
| **NOT_FOUND** | 404 | ❌ Não | N/A |
| **BAD_REQUEST** | 400, "bad request" | ❌ Não | N/A |

---

## 📈 Exponential Backoff com Jitter

**Fórmula:**
```
delay = min(base_delay * (2.0 ^ attempt), max_delay) * error_multiplier + jitter
jitter = random(0, delay * 0.3)
```

**Exemplo (Strategy 1, Server Error 502):**
```
Attempt 1: delay = 2.0s * 1.5 + jitter(0-0.9s) = ~2.5s
Attempt 2: delay = 4.0s * 1.5 + jitter(0-1.8s) = ~6.8s
Attempt 3: Fallback para Strategy 2
```

---

## 🛡️ Circuit Breaker

**Estados:**
```mermaid
CLOSED → (5 failures) → OPEN → (60s timeout) → HALF_OPEN → (success) → CLOSED
                                                    ↓ (failure)
                                                   OPEN
```

**Parâmetros:**
- Failure threshold: 5 falhas consecutivas
- Timeout duration: 180s para image generation
- Quando OPEN: Bloqueia tentativas para proteger o serviço
- Quando HALF_OPEN: Permite 1 tentativa de teste

---

## 🎬 Fluxo de Execução

```
1. Usuário clica em "Gerar Todos os Personagens"
   ↓
2. Para cada personagem sem avatar:
   ↓
3. Checa biblioteca global (reuso)
   ↓ (se não encontrado)
4. FallbackAgent inicia com Strategy 1
   ↓
5. Tenta Strategy 1 (2 retries com backoff)
   ↓ (se falha)
6. Tenta Strategy 2 (2 retries com backoff maior)
   ↓ (se falha)
7. Tenta Strategy 3 (1 retry com delay + minimal prompt)
   ↓ (se falha)
8. Retorna erro para o usuário
```

---

## 📝 Logs Gerados

```python
# Sucesso na Strategy 1
INFO: FallbackAgent: Full Detailed Prompt attempt 1/2
INFO: Strategy 1 (Full): Generating 'Abraão'
INFO: FallbackAgent: Full Detailed Prompt SUCCESS on attempt 1
INFO: Successfully generated avatar for 'Abraão' using fallback system ✅

# Falha na Strategy 1, sucesso na Strategy 2
WARNING: FallbackAgent: Full Detailed Prompt FAILED attempt 1 (type: server_error): 502 Bad Gateway
INFO: FallbackAgent: Waiting 3.2s before retry (error_type: server_error)
WARNING: FallbackAgent: Full Detailed Prompt FAILED attempt 2 (type: server_error): 502 Bad Gateway
INFO: FallbackAgent: Falling back to next strategy (2/3)
INFO: FallbackAgent: Trying strategy 2/3: Simplified Prompt (502/503 fallback)
INFO: Strategy 2 (Simplified): Generating 'Abraão'
INFO: FallbackAgent: Simplified Prompt (502/503 fallback) SUCCESS on attempt 1
INFO: Successfully generated avatar for 'Abraão' using fallback system ✅

# Circuit Breaker ativo
WARNING: CircuitBreaker: OPENED after 5 failures
ERROR: CircuitBreaker OPEN for Full Detailed Prompt — service temporarily unavailable
INFO: CircuitBreaker: Transitioning to HALF_OPEN (timeout passed)
```

---

## 🧪 Testing

**Teste Manual:**
1. Gerar personagens quando Gemini está sobrecarregado
2. Verificar logs no backend
3. Confirmar que strategies alternativas foram tentadas

**Teste Simulado:**
```python
# Simular erro 502 para testar fallback
from core.fallback_agent import create_image_generation_agent, FallbackStrategy

async def mock_502_error(**kwargs):
    raise Exception("502 Bad Gateway")

async def mock_success(**kwargs):
    return "success_data", "prompt"

agent = create_image_generation_agent()
strategies = [
    FallbackStrategy(name="Fail", func=mock_502_error, max_retries=1),
    FallbackStrategy(name="Success", func=mock_success, max_retries=1)
]

result = await agent.execute_with_fallback(strategies, context={})
# Deve retornar sucesso da Strategy 2
```

---

## 📊 Métricas de Sucesso

**Resposta do Endpoint:**
```json
{
  "total": 10,
  "generated": 8,
  "reused": 1,
  "failed": 1,
  "fallback_used": true,
  "strategies_tried": ["Abraão", "Ló", "Sara"],
  "characters": [
    {
      "name": "Abraão",
      "status": "generated",
      "avatar_url": "https://...",
      "avatar_id": "abc123"
    }
  ]
}
```

**Novos Campos:**
- `fallback_used`: Indica se o sistema de fallback foi acionado
- `strategies_tried`: Lista de personagens que usaram fallback

---

## 🚀 Próximos Passos

1. ✅ Implementado FallbackAgent
2. ✅ Integrado na geração de personagens (generate-all)
3. ⏳ **PENDENTE:** Integrar na geração individual (`/characters/{name}/generate`)
4. ⏳ **PENDENTE:** Adicionar métricas de fallback no Analytics
5. ⏳ **PENDENTE:** Dashboard para monitorar circuit breaker state

---

## 📄 Arquivos Modificados

- ✅ **CRIADO:** `/app/backend/core/fallback_agent.py` (380 linhas)
- ✅ **MODIFICADO:** `/app/backend/routers/studio/projects.py` (endpoint `generate-all`)

---

**Status:** ✅ Implementado e pronto para teste  
**Data:** 2026-04-02  
**Agent:** E1 Fork Agent
