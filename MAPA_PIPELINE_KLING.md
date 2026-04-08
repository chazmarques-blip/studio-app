# 🎬 MAPA VISUAL DO PIPELINE KLING vs SORA 2

## 📊 VISÃO GERAL DO PIPELINE

```
┌─────────────────────────────────────────────────────────────────┐
│  PROJETO CRIADO                                                 │
│  ✅ video_engine: "kling"                                       │
│  ✅ target_duration: 10 minutos                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ETAPA 1: ROTEIRO (Screenwriter)                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Arquivo: screenwriter.py + parallel_agents.py            │  │
│  │ Status: ✅ LÊ video_engine                               │  │
│  │                                                            │  │
│  │ Lógica:                                                    │  │
│  │   if video_engine == "kling":                             │  │
│  │       num_scenes = target_duration // 5                   │  │
│  │       scene_duration = "5 minutos"                        │  │
│  │   else:                                                    │  │
│  │       num_scenes = (target_duration * 60) // 12           │  │
│  │       scene_duration = "12 segundos"                      │  │
│  │                                                            │  │
│  │ Resultado Esperado:                                        │  │
│  │   ✅ Kling 10min → 2 cenas (0:00-5:00, 5:00-10:00)       │  │
│  │   ❌ Se gerar 50 cenas → BUG! Não está lendo o engine    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ETAPA 2: PERSONAGENS (Character Library)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Status: ⚪ NÃO DEPENDE de video_engine                   │  │
│  │ Funciona igual para Kling e Sora                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ETAPA 3: DIÁLOGOS (Dialogue)                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Arquivo: Não encontrado (dialogue.py missing)             │  │
│  │ Status: ⚠️ DESCONHECIDO                                   │  │
│  │                                                            │  │
│  │ ⚠️ POSSÍVEL PROBLEMA AQUI!                                │  │
│  │ Se diálogos não leem video_engine, podem estar           │  │
│  │ gerando para 12 segundos em vez de 5 minutos             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ETAPA 4: DIRECTOR REVIEW                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Arquivo: director.py                                       │  │
│  │ Status: ❌ NÃO LÊ video_engine                            │  │
│  │                                                            │  │
│  │ ❌ PROBLEMA CRÍTICO ENCONTRADO!                           │  │
│  │ Director não adapta review baseado no engine              │  │
│  │ Pode estar revisando com critérios de Sora (12s)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ETAPA 5: STORYBOARD                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Arquivo: storyboard.py                                     │  │
│  │ Status: ✅ LÊ video_engine                                │  │
│  │                                                            │  │
│  │ Lógica:                                                    │  │
│  │   if video_engine == "kling":                             │  │
│  │       frames_to_generate = 30  # 30 frames para 5min     │  │
│  │   else:                                                    │  │
│  │       frames_to_generate = 6   # 6 frames para 12s       │  │
│  │                                                            │  │
│  │ ✅ Funcionando corretamente                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ETAPA 6: PRODUÇÃO (Video Generation)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Arquivo: production.py                                     │  │
│  │ Status: ✅ LÊ video_engine                                │  │
│  │                                                            │  │
│  │ Lógica:                                                    │  │
│  │   video_engine = project.get("video_engine", "sora")      │  │
│  │   video_duration = 300 if video_engine == "kling" else 12│  │
│  │                                                            │  │
│  │   if video_engine == "kling":                             │  │
│  │       # Usa Kling API                                      │  │
│  │       # Chama Cinematographer                             │  │
│  │       # Gera vídeo de 5 minutos                           │  │
│  │   else:                                                    │  │
│  │       # Usa Sora 2 API                                     │  │
│  │       # Gera vídeo de 12 segundos                         │  │
│  │                                                            │  │
│  │ ✅ Funcionando corretamente                               │  │
│  │ ⚠️ MAS depende dos timestamps do roteiro!                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔴 PROBLEMAS IDENTIFICADOS

### **1. Director Review (director.py)**
```
❌ CRÍTICO: Não lê video_engine
❌ Não adapta critérios de revisão
```

**Impacto:**
- Director pode estar revisando cenas de 5min com critérios de 12s
- Pode estar dando scores errados
- Pode estar aplicando correções inadequadas

**Localização:** `/app/backend/routers/studio/director.py`

---

### **2. Diálogos (dialogue.py)**
```
⚠️ DESCONHECIDO: Arquivo não encontrado na auditoria
```

**Impacto:**
- Diálogos podem estar sendo gerados para 12s
- Em cena de 5min, diálogos curtos demais
- Ou pode estar em outro arquivo

**Precisa verificar:** Onde os diálogos são gerados

---

## ✅ PONTOS QUE FUNCIONAM CORRETAMENTE

### **1. Roteiro (screenwriter.py + parallel_agents.py)**
```
✅ Lê video_engine
✅ Calcula cenas corretamente
✅ Define timestamps corretos
```

### **2. Storyboard (storyboard.py)**
```
✅ Lê video_engine
✅ Gera 30 frames para Kling (vs 6 para Sora)
✅ Funcionando corretamente
```

### **3. Produção (production.py)**
```
✅ Lê video_engine
✅ Chama API correta (Kling vs Sora)
✅ Define duração correta (300s vs 12s)
```

---

## 🎯 DIAGNÓSTICO

### **Por que tudo parece Sora?**

Existem 3 possibilidades:

**Possibilidade 1: Roteiro gerado antes da correção**
- Você criou o projeto e gerou o roteiro ANTES da correção
- Roteiro tem timestamps errados (12s)
- Todas as etapas seguintes usam esses timestamps
- Solução: Regenerar roteiro

**Possibilidade 2: Director Review está aplicando critérios Sora**
- Director não lê video_engine
- Pode estar dando feedback baseado em 12s
- Pode estar alterando descrições das cenas
- Solução: Corrigir director.py

**Possibilidade 3: Diálogos estão sendo gerados para 12s**
- Se diálogos são muito curtos
- Cena de 5min fica estranha com 3 frases
- Solução: Corrigir geração de diálogos

---

## 🔧 CHECKLIST DE VERIFICAÇÃO

Use este checklist para identificar onde está o problema:

### **Após gerar roteiro:**
```
[ ] Quantas cenas foram geradas?
    ✅ 2 cenas (Kling 10min) = CORRETO
    ❌ 50 cenas (Sora 10min) = ROTEIRO ERRADO

[ ] Timestamps das cenas:
    ✅ 0:00-5:00, 5:00-10:00 = CORRETO
    ❌ 0:00-0:12, 0:12-0:24... = ROTEIRO ERRADO
```

### **Após gerar diálogos:**
```
[ ] Quantidade de diálogo por cena:
    ✅ 20-30 falas (5min) = CORRETO
    ❌ 3-5 falas (12s) = DIÁLOGOS ERRADOS

[ ] Duração total do áudio:
    ✅ ~4-5 minutos = CORRETO
    ❌ ~10 segundos = DIÁLOGOS ERRADOS
```

### **Após Director Review:**
```
[ ] Feedback do Director:
    ✅ Menciona cenas longas/detalhadas = CORRETO
    ❌ Menciona cenas curtas/rápidas = DIRECTOR ERRADO
```

### **Antes da produção:**
```
[ ] Timestamps na tela de produção:
    ✅ 0:00-5:00, 5:00-10:00 = PRONTO PARA PRODUÇÃO
    ❌ 0:00-0:12, 0:12-0:24... = NÃO INICIAR!
```

---

## 📊 MATRIZ DE STATUS

| Etapa | Lê video_engine? | Status | Ação Necessária |
|---|---|---|---|
| Projeto | ✅ Salva | ✅ OK | Nenhuma |
| Roteiro | ✅ Sim | ✅ OK | Nenhuma |
| Personagens | ⚪ N/A | ✅ OK | Nenhuma |
| Diálogos | ❓ ? | ⚠️ Verificar | Localizar código |
| Director | ❌ Não | ❌ BUG | Adicionar leitura |
| Storyboard | ✅ Sim | ✅ OK | Nenhuma |
| Produção | ✅ Sim | ✅ OK | Nenhuma |

---

## 🎯 PRÓXIMOS PASSOS

1. **Verificar projeto atual:**
   - Quantas cenas foram geradas?
   - Qual o timestamp da primeira cena?

2. **Se timestamps errados:**
   - Regenerar roteiro (correção já aplicada)

3. **Corrigir Director Review:**
   - Adicionar leitura de video_engine
   - Adaptar prompts de revisão

4. **Verificar Diálogos:**
   - Localizar código de geração
   - Verificar se adapta para Kling

---

**Criado:** 2026-04-08  
**Auditoria:** Completa  
**Arquivos:** 6 verificados
