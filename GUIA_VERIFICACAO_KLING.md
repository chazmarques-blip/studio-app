# ✅ GUIA DE VERIFICAÇÃO: Projeto Kling

## 🎯 OBJETIVO
Garantir que cada etapa está correta ANTES de avançar para a próxima.

---

## 📋 CHECKLIST COMPLETO

### **PASSO 1: Criar Projeto** ✓
**Configurações obrigatórias:**
- ✅ Nome: "TESTE Kling" (ou qualquer nome)
- ✅ Video Engine: **KLING** (não Sora 2)
- ✅ Duração: **10 minutos** (para facilitar teste)
- ✅ Idioma: Português
- ✅ Modo áudio: Narrated ou Dubbed

**VERIFICAR ANTES DE AVANÇAR:**
- Confirmar que selecionou KLING (não Sora)
- Confirmar que duração está em 10 minutos

---

### **PASSO 2: Gerar Roteiro** 🔴 CRÍTICO
**Ação:** Gerar roteiro com história simples (ex: "Uma breve jornada")

**✅ VERIFICAÇÃO OBRIGATÓRIA:**

Após o roteiro ser gerado, VERIFIQUE os timestamps:

**CORRETO (Kling):**
```
✅ Cena 1: 0:00-5:00    (5 minutos)
✅ Cena 2: 5:00-10:00   (5 minutos)
```

**ERRADO (Sora):**
```
❌ Cena 1: 0:00-0:12    (12 segundos)
❌ Cena 2: 0:12-0:24    (12 segundos)
❌ Cena 3: 0:24-0:36    (12 segundos)
... (50 cenas)
```

**SE OS TIMESTAMPS ESTIVEREM ERRADOS:**
- ⚠️ NÃO AVANCE! Algo está errado
- Avisar imediatamente
- Não perder tempo com as próximas etapas

**SE OS TIMESTAMPS ESTIVEREM CORRETOS:**
- ✅ Pode avançar para Personagens

---

### **PASSO 3: Personagens**
**Verificação simples:**
- Personagens foram criados/sincronizados?
- ✅ Se sim, avançar

---

### **PASSO 4: Diálogos**
**Verificação simples:**
- Diálogos foram gerados?
- ✅ Se sim, avançar

---

### **PASSO 5: Director Preview**
**Verificação:**
- Score >= 80%?
- ✅ Se sim, avançar

---

### **PASSO 6: Storyboard**
**Verificação:**
- Imagens foram geradas?
- ✅ Se sim, avançar para Produção

---

### **PASSO 7: Produção** 🔴 VERIFICAÇÃO FINAL

**ANTES de clicar em "Iniciar Produção Completa":**

**Verificar timestamps novamente:**

**CORRETO:**
```
✅ Cena 1: 0:00-5:00
✅ Cena 2: 5:00-10:00
✅ Total: 2 cenas × 5min = 10 minutos
```

**Se estiver assim, pode iniciar produção!**

**ERRADO:**
```
❌ 50+ cenas de 12 segundos
❌ NÃO INICIAR! Vai gerar 50 vídeos de 5min cada!
```

---

## 🚨 PONTOS CRÍTICOS DE VERIFICAÇÃO

### **🔴 CHECKPOINT 1: Logo Após Gerar Roteiro**
```
Esperado para 10 minutos + Kling:
- 2 cenas
- Cena 1: 0:00-5:00
- Cena 2: 5:00-10:00
```

Se estiver diferente = PARAR E AVISAR

### **🔴 CHECKPOINT 2: Antes da Produção**
```
Confirmar novamente os timestamps na aba PRODUÇÃO
Se estiver correto = Pode iniciar produção
```

---

## 📊 TABELA DE REFERÊNCIA RÁPIDA

| Duração Config | Engine | Cenas Esperadas | Duração/Cena | Exemplo Timestamps |
|---|---|---|---|---|
| 5 min | Kling | 1 | 5:00 | 0:00-5:00 |
| 10 min | Kling | 2 | 5:00 | 0:00-5:00, 5:00-10:00 |
| 15 min | Kling | 3 | 5:00 | 0:00-5:00, 5:00-10:00, 10:00-15:00 |
| 5 min | Sora | 25 | 0:12 | 0:00-0:12, 0:12-0:24, ... |

---

## ✅ CONFIRMAÇÃO DE CORREÇÃO

**Código verificado:**

1. ✅ `/app/backend/routers/studio/screenwriter.py` linha 282-284:
   ```python
   scene_duration_seconds = 300 if video_engine == "kling" else 12
   scene_duration_label = "5 minutos" if video_engine == "kling" else "12 segundos"
   ```

2. ✅ `/app/backend/routers/studio/parallel_agents.py` linha 59-72:
   ```python
   if video_engine == "kling":
       num_scenes_needed = target_duration_minutes // 5
       scene_duration = "5 minutos"
   ```

3. ✅ Backend reiniciado: PID 14116

**Correção aplicada e funcionando no código.**

---

## 🎯 RESUMO EXECUTIVO

**Para ter certeza:**
1. ✅ Criar projeto com Kling + 10min
2. 🔴 Gerar roteiro
3. 🔴 **VERIFICAR TIMESTAMPS IMEDIATAMENTE**
4. ✅ Se correto (0:00-5:00, 5:00-10:00) → Continuar
5. ❌ Se errado (0:00-0:12, 0:12-0:24...) → PARAR E AVISAR

**Tempo de verificação:** 30 segundos após gerar roteiro
**Evita:** Perder horas de trabalho

---

## 📞 SE ALGO DER ERRADO

**Avisar com:**
- Screenshot dos timestamps
- Configurações do projeto (Engine + Duração)
- Não avançar para próximas etapas

---

**Data:** 2026-04-08  
**Backend:** PID 14116  
**Correção:** Aplicada e verificada
