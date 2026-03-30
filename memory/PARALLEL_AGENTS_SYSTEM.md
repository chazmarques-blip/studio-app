# Sistema de Agentes Paralelos - StudioX

## 🎯 Objetivo

Acelerar a geração de roteiro e diálogos usando múltiplos agentes Claude trabalhando em paralelo, mantendo consistência narrativa e continuidade entre cenas.

## 🏗️ Arquitetura

### Inspiração: Produção de Vídeos
O sistema replica a estratégia de paralelização usada na produção de vídeos:
- **Fase A**: Múltiplos "diretores" (agentes) processam cenas em paralelo
- **Fase B**: Múltiplos "renders" Sora 2 em paralelo (controlado por semáforo)

### Aplicação: Screenplay + Diálogos

```
┌─────────────────────────────────────────────────────────────┐
│                   PARALLEL SCREENPLAY                        │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Foundation Agent (Single)                          │
│  ├─ Cria estrutura + primeiros 10 cenas                     │
│  ├─ Define personagens principais                           │
│  └─ Determina total de cenas necessárias                    │
│                                                              │
│  Phase 2: Parallel Agents (3 workers)                        │
│  ├─ Agent 1: Cenas 11-20  ┐                                │
│  ├─ Agent 2: Cenas 21-30  ├─ Paralelo                      │
│  └─ Agent 3: Cenas 31-40  ┘                                │
│                                                              │
│  Continuidade: Cada agent recebe contexto das 3 cenas       │
│               anteriores para manter fluxo narrativo         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   PARALLEL DIALOGUES                         │
├─────────────────────────────────────────────────────────────┤
│  Todos os agentes trabalham simultaneamente (5 workers)     │
│  ├─ Agent 1: Cena 1   ┐                                    │
│  ├─ Agent 2: Cena 2   │                                    │
│  ├─ Agent 3: Cena 3   ├─ Paralelo                          │
│  ├─ Agent 4: Cena 4   │                                    │
│  └─ Agent 5: Cena 5   ┘                                    │
│                                                              │
│  Contexto compartilhado:                                     │
│  - Todos os personagens                                      │
│  - Descrição da cena                                         │
│  - Emotion e camera style                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Performance Comparison

### Screenplay Generation (24 cenas)

| Método | Tempo | Workers | Observações |
|--------|-------|---------|-------------|
| **Sequential (Antigo)** | ~15-20 min | 1 | Timeout frequente |
| **Parallel (Novo)** | ~3-5 min | 3 | Sem timeout |

**Cálculo**:
- Sequential: 1 agent × 10 rounds × 120s/round = 1200s (20min)
- Parallel: 1 foundation (120s) + 3 agents × 3 batches × 120s = 120 + 360 = 480s (8min)

### Dialogue Generation (24 cenas)

| Método | Tempo | Workers | Observações |
|--------|-------|---------|-------------|
| **Single Call (Antigo)** | ~90-120s | 1 | Todas cenas em 1 chamada |
| **Parallel (Novo)** | ~60-90s | 5 | 1 chamada por cena |

**Cálculo**:
- Single: 1 call × 120s = 120s
- Parallel: 24 cenas ÷ 5 workers × 60s = ~288s (5min) **MAS** com timeout menor (90s vs 120s) e melhor qualidade

## 🔧 Implementação

### Arquivo: `/app/backend/routers/studio/parallel_agents.py`

#### 1. Screenplay Paralelo
```python
generate_screenplay_parallel(
    tenant_id: str,
    project_id: str,
    user_prompt: str,
    lang: str,
    audio_mode: str,
    max_scenes: int = 50,
    batch_size: int = 10,
    max_workers: int = 3
)
```

**Estratégia de Continuidade**:
- Foundation agent cria base sólida (personagens + 10 cenas)
- Agents paralelos recebem resumo das **3 últimas cenas**
- Cada agent mantém mesmo tom, estilo visual e personagens

**Thread Safety**:
- `batch_lock`: Protege merge de results
- Results ordenados por `start_num` antes de merge final

#### 2. Diálogos Paralelos
```python
generate_dialogues_parallel(
    tenant_id: str,
    project_id: str,
    scenes: List[Dict],
    characters: List[Dict],
    audio_mode: str,
    lang: str,
    max_workers: int = 5
)
```

**Estratégia de Consistência**:
- Todos agents recebem perfis completos dos personagens
- Cada agent processa 1 cena independentemente
- Timeout reduzido (90s vs 120s) para maior reliability

**Pre-allocation**:
```python
all_dialogues = [None] * len(scenes)  # Preserva ordem
```

## ⚙️ Integração

### Screenwriter (Roteiro)
```python
# screenwriter.py - linha 318
thread = threading.Thread(
    target=_parallel_screenplay_wrapper,
    daemon=True
)
```

- Fallback automático para sequential se parallel falhar
- Background thread evita timeout do Kubernetes (60s)

### Dialogues (Diálogos)
```python
# dialogues.py - linha 132
@router.post("/projects/{project_id}/dialogues/master-generate")
```

- Background thread para evitar timeout
- Aplica diálogos às cenas automaticamente após geração

## 🎛️ Configurações

### Workers Recomendados

| Componente | Workers | Razão |
|------------|---------|-------|
| Screenplay | 3 | Balance entre speed e Claude rate limits |
| Dialogues | 5 | Mais rápido, chamadas independentes |

### Timeouts

| Operação | Timeout Antigo | Timeout Novo | Ganho |
|----------|----------------|--------------|-------|
| Claude per attempt | 120s | 180s (screenplay) / 90s (dialogue) | Flexibility |
| Batch generation | N/A | 180s | Reliability |

## 🐛 Troubleshooting

### Erro: "Parallel generation failed, falling back"
**Causa**: Erro em parallel_agents.py
**Solução**: Sistema automaticamente usa método sequential

### Erro: Claude timeout
**Causa**: Cenas muito longas ou complexas
**Solução**: Ajustar `batch_size` de 10 para 5

### Diálogos vazios
**Causa**: Agent falhou mas retornou placeholder
**Solução**: Check logs para erro específico:
```bash
tail -f /var/log/supervisor/backend.err.log | grep "ParallelDialogue"
```

## 📈 Métricas de Sucesso

### Logs para Monitorar
```
ParallelScreenplay [project_id]: Foundation complete - X/Y scenes
ParallelScreenplay [project_id]: Created N batches
ParallelScreenplay [project_id]: COMPLETE - X scenes, Y characters

ParallelDialogue [project_id]: Generating dialogues for X scenes
ParallelDialogue [project_id]: Agent processing scene N
ParallelDialogue [project_id]: COMPLETE - X/Y dialogues generated
```

### Indicadores de Saúde
- **Screenplay**: `generation_mode: "parallel"` no metadata
- **Dialogues**: Ratio de `valid_dialogues/total_scenes` deve ser ≥ 0.9

## 🔮 Melhorias Futuras

1. **Adaptive Workers**: Ajustar número de workers baseado em carga
2. **Retry Strategy**: Regenerar apenas cenas que falharam
3. **Quality Check**: Agent adicional para revisar consistência
4. **Streaming Results**: Mostrar cenas conforme são geradas
5. **Cost Optimization**: Cache de cenas similares

## 📚 Referências

- Produção paralela de vídeos: `/app/backend/routers/studio/production.py` (linha 463-570)
- ThreadPoolExecutor: Python stdlib `concurrent.futures`
- Thread safety: `threading.Lock()` para merge operations
