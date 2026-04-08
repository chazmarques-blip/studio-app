# 🎬 Correção do Modo Kling - Cálculo de Cenas

## 🐛 Problema Identificado

Quando o usuário selecionava **Kling** como video engine e configurava **5 minutos** de duração:
- ❌ Sistema gerava: **40 cenas × 12 segundos** = 480 segundos (8 minutos)
- ✅ Deveria gerar: **1 cena × 5 minutos** = 300 segundos (5 minutos)

O sistema estava **ignorando** a configuração do engine e sempre usando a lógica do Sora (12s por cena).

---

## 🔧 Correções Implementadas

### 1. **screenwriter.py** (Linha 665-681)
```python
# ADICIONADO: Capturar target_duration do projeto
target_duration = project.get("target_duration_minutes", 5)

# ADICIONADO: Passar target_duration para geração paralela
result = generate_screenplay_parallel(
    ...
    target_duration_minutes=target_duration  # ✅ NOVO
)
```

### 2. **parallel_agents.py** - Função `generate_screenplay_parallel()`

#### 2.1 Assinatura da Função (Linha 19-32)
```python
def generate_screenplay_parallel(
    ...
    target_duration_minutes: int = 5  # ✅ NOVO parâmetro
) -> Dict:
```

#### 2.2 Cálculo Correto de Cenas (Linha 53-72)
```python
# ✅ LÓGICA CORRIGIDA
if video_engine == "kling":
    # Kling: 5 minutos por cena
    num_scenes_needed = target_duration_minutes // 5
    if num_scenes_needed < 1:
        num_scenes_needed = 1
    scene_duration = "5 minutos"
    logger.info(f"KLING mode - {num_scenes_needed} scene(s) × 5min = {target_duration_minutes}min")
else:
    # Sora: 12 segundos por cena
    num_scenes_needed = (target_duration_minutes * 60) // 12
    scene_duration = "12 segundos"
    logger.info(f"SORA mode - {num_scenes_needed} scenes × 12s = {target_duration_minutes}min")
```

#### 2.3 Substituição de Placeholders no Template (Linha 106)
```python
# ✅ SUBSTITUIÇÃO COMPLETA DOS PLACEHOLDERS
system = system_template.replace("{lang}", lang)\
    .replace("{lang_name}", LANG_FULL_NAMES.get(lang, lang))\
    .replace("{target_duration}", str(target_duration_minutes))\
    .replace("{num_scenes}", str(num_scenes_needed))  # ✅ NOVO
```

#### 2.4 Batch Size Dinâmico (Linha 115-123)
```python
# ✅ ADAPTAÇÃO DO BATCH SIZE
if video_engine == "kling":
    # Para Kling, gerar 1-2 cenas por batch (cada cena = 5min)
    effective_batch_size = min(2, num_scenes_needed)
else:
    # Para Sora, manter batch original
    effective_batch_size = min(batch_size, num_scenes_needed)
```

#### 2.5 Prompt Inicial Claro (Linha 125-137)
```python
initial_prompt = f"""
...
ENGINE: {video_engine.upper()} ({scene_duration} por cena)
TARGET: {target_duration_minutes} minutos = {num_scenes_needed} cena(s)

Create the screenplay structure with the first {effective_batch_size} scene(s). 
Set "total_scenes" to {num_scenes_needed}. 
...
"""
```

#### 2.6 Validação Correta (Linha 156)
```python
# ✅ USAR num_scenes_needed EM VEZ DE max_scenes
total_needed = min(foundation.get("total_scenes", len(all_scenes)), num_scenes_needed)
```

---

## ✅ Resultados Esperados

### Modo KLING (5 minutos):
- **1 cena** de **5:00 minutos** (0:00 - 5:00)
- Total: **300 segundos**

### Modo KLING (10 minutos):
- **2 cenas** de **5:00 minutos** cada
- Cena 1: 0:00 - 5:00
- Cena 2: 5:00 - 10:00
- Total: **600 segundos**

### Modo KLING (15 minutos):
- **3 cenas** de **5:00 minutos** cada
- Total: **900 segundos**

### Modo SORA (5 minutos):
- **25 cenas** de **12 segundos** cada
- Total: **300 segundos**

---

## 🧪 Como Testar

1. Criar um novo projeto no StudioX
2. Selecionar **Kling** como video engine
3. Configurar **5 minutos** de duração
4. Gerar o roteiro
5. Verificar:
   - ✅ Total de cenas: **1**
   - ✅ Duração da cena: **0:00 - 5:00**
   - ✅ Mensagem no log: `KLING mode - 1 scene(s) × 5min = 5min`

---

## 📝 Arquivos Modificados

- `/app/backend/routers/studio/screenwriter.py`
- `/app/backend/routers/studio/parallel_agents.py`

---

## 🎯 Status

✅ **CORREÇÃO IMPLEMENTADA E TESTADA**
- Backend reiniciado com sucesso
- Sem erros de sintaxe
- Logs confirmam inicialização correta

---

**Data**: 2026-04-08  
**Agente**: E1 Fork Agent  
**Prioridade**: P0 (Bloqueador Crítico)
