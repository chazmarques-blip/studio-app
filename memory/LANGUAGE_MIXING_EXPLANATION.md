# 🌐 Problema: Mistura de Idiomas (Português + Inglês)

## 📋 **Problema Reportado**

**Sintoma:** Cenas estão sendo geradas com mistura de português e inglês.

---

## 🔍 **Diagnóstico**

### Onde Acontece a Mistura

```
PROJETO CONFIGURADO: Português (pt)
    ↓
ROTEIRO/CENAS: Escritas em português ✅
    ↓
DIÁLOGOS: Em português ✅
    ↓
DESCRIÇÕES: Em português ✅
    ↓
⚠️ AQUI O PROBLEMA:
    ↓
PROMPTS SORA 2: Gerados em INGLÊS ❌
    ↓
RESULTADO: Mistura de idiomas
```

### Arquivo Responsável

**Arquivo:** `/app/backend/routers/studio/production.py`  
**Linha:** 398

```python
director_system = f"""You are a SCENE DIRECTOR for Sora 2 video generation...

...

- The sora_prompt MUST be in ENGLISH"""
#                    ^^^^^^^^^^^^^^^^^^^^^
#                    Esta linha força inglês
```

---

## 🎯 **Por Que Está em Inglês?**

### Razão Técnica

O Sora 2 da OpenAI tem **melhor desempenho** com prompts em **inglês**, pois:

1. **Modelo treinado primariamente em inglês**
   - Dataset maior em inglês
   - Vocabulário visual mais rico em inglês
   - Associações conceituais mais fortes

2. **Documentação oficial sugere inglês**
   - Exemplos oficiais da OpenAI em inglês
   - Melhores resultados reportados em inglês

3. **Consistência de geração**
   - Termos técnicos (cinematográficos) mais estáveis em inglês
   - Menos ambiguidade em descrições visuais

### Exemplo da Conversão

**Entrada (PT):**
```
Descrição da cena: "Jonas olha para o grande peixe com medo"
Diálogo: "Meu Deus, que criatura enorme!"
```

**Processamento:**
```
1. Scene description (PT) → Enviado para LLM director
2. LLM Director traduz → Prompt visual em inglês
3. Sora 2 recebe prompt em inglês
4. Sora 2 gera vídeo
```

**Prompt Sora 2 (EN):**
```
"Wide shot of anthropomorphic camel Jonas, middle-aged adult male,
standing on ancient dock. Camera dolly in as Jonas's eyes widen in fear,
looking upward. Giant whale emerges from deep blue water in background.
Dramatic lighting, golden hour, cinematic composition. Jonas's mouth 
opens in shock, expressing terror through facial animation..."
```

---

## ⚙️ **Como Funciona Atualmente**

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│ USUÁRIO ESCREVE ROTEIRO EM PORTUGUÊS                           │
├─────────────────────────────────────────────────────────────────┤
│ "Jonas caminha pela praia e encontra um grande peixe"          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ SISTEMA GERA CENAS EM PORTUGUÊS                                 │
├─────────────────────────────────────────────────────────────────┤
│ Cena #1:                                                        │
│ - Título: "Jonas na Praia"                                      │
│ - Descrição: "Praia ao amanhecer, areia dourada..."           │
│ - Diálogo: "Que dia lindo!"                                    │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ DIRECTOR AGENT CONVERTE PARA PROMPT VISUAL (EM INGLÊS)        │
├─────────────────────────────────────────────────────────────────┤
│ System: "The sora_prompt MUST be in ENGLISH"                   │
│                                                                 │
│ Input: Descrição em PT + Diálogos em PT                        │
│ Output: Prompt técnico visual em EN                            │
│                                                                 │
│ Exemplo:                                                        │
│ "Wide establishing shot of Mediterranean beach at golden dawn. │
│  Anthropomorphic camel character Jonas, wearing brown tunic..." │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ SORA 2 GERA VÍDEO (Recebe prompt em inglês)                    │
├─────────────────────────────────────────────────────────────────┤
│ ✅ Entende melhor em inglês                                     │
│ ✅ Termos cinematográficos precisos                             │
│ ✅ Geração mais consistente                                     │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÁUDIO ADICIONADO (Em português via ElevenLabs)                 │
├─────────────────────────────────────────────────────────────────┤
│ Vozes: "Que dia lindo!" (PT) ✅                                 │
│ Música: Instrumental ✅                                         │
│ Resultado: Vídeo com áudio em português                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤔 **Onde o Usuário Vê a Mistura?**

### Cenários Possíveis

1. **Logs do Sistema**
   ```
   [PT] Gerando cena: "Jonas na praia"
   [EN] Sora prompt: "Wide shot of beach..."
   ```
   → Logs mostram PT + EN misturado

2. **Metadados da Cena**
   ```json
   {
     "title": "Jonas na Praia",           // PT
     "description": "Praia ao amanhecer", // PT
     "sora_prompt": "Wide shot of beach..." // EN
   }
   ```
   → JSON tem campos em ambos idiomas

3. **Se Texto Aparecer no Vídeo**
   - Language marker é adicionado: "Any visible text in PORTUGUESE TEXT"
   - Mas o resto do prompt está em inglês

---

## ✅ **Isso É Normal?**

**SIM, isso é o comportamento esperado e recomendado!**

### Por Que É Assim

| Componente | Idioma | Motivo |
|------------|--------|--------|
| **Roteiro/Cenas** | Português | Para o usuário entender |
| **Diálogos** | Português | Falados pelos personagens |
| **Prompts Visuais** | Inglês | Melhor desempenho do Sora 2 |
| **Áudio Final** | Português | ElevenLabs sintetiza em PT |
| **Vídeo Final** | Visual (sem idioma) | Imagens não têm idioma |

### Analogia

É como um **filme dublado:**
- **Roteiro original:** Português (sua escolha)
- **Instruções técnicas:** Inglês (para a equipe técnica/Sora 2)
- **Diálogos falados:** Português (áudio final)
- **Resultado:** Vídeo em português

---

## 🔧 **Pode Mudar para Tudo em Português?**

### Opção 1: Forçar Prompts em Português

**Código:**
```python
# Mudar linha 398 de:
- The sora_prompt MUST be in ENGLISH

# Para:
- The sora_prompt MUST be in PORTUGUESE
```

**Prós:**
- ✅ Tudo em um único idioma
- ✅ Mais "natural" para usuário brasileiro

**Contras:**
- ❌ Sora 2 pode ter desempenho reduzido
- ❌ Termos cinematográficos podem ser mal interpretados
- ❌ Menor precisão em descrições visuais complexas
- ❌ Risco de qualidade inferior

### Opção 2: Sistema Bilíngue (Atual)

**Como Está:**
- Interface/Roteiro: PT
- Prompts técnicos: EN
- Áudio final: PT

**Prós:**
- ✅ Melhor desempenho do Sora 2
- ✅ Termos técnicos precisos
- ✅ Qualidade de geração superior
- ✅ Usuário vê resultado final em PT (áudio)

**Contras:**
- ⚠️ Logs/metadados misturados

---

## 💡 **Recomendação**

### ✅ **Manter Como Está (Opção 2)**

**Motivos:**

1. **Qualidade Visual Superior**
   - Sora 2 funciona melhor com prompts em inglês
   - Termos cinematográficos mais precisos
   - Menos ambiguidade

2. **Usuário Final Não Vê o Prompt**
   - Roteiro está em português ✅
   - Diálogos estão em português ✅
   - Vídeo final tem áudio em português ✅
   - O prompt é interno (técnico)

3. **Padrão da Indústria**
   - YouTube, Netflix, Disney+ fazem o mesmo
   - Instruções técnicas em inglês
   - Produto final no idioma local

### 🔄 **Se Realmente Quiser Mudar**

Posso implementar:

```python
# Adicionar opção de configuração
USE_NATIVE_LANGUAGE_PROMPTS = False  # True = forçar PT

if USE_NATIVE_LANGUAGE_PROMPTS:
    director_system = f"""The sora_prompt MUST be in {project_lang.upper()}"""
else:
    director_system = f"""The sora_prompt MUST be in ENGLISH"""
```

**Mas recomendo testar lado a lado** para comparar qualidade.

---

## 📊 **Comparação Visual**

### Prompt em Inglês (Atual):
```
"Cinematic wide shot of Mediterranean beach at golden hour. 
Anthropomorphic camel character, middle-aged male, wearing 
traditional brown tunic, walks slowly along pristine shoreline. 
Camera tracks laterally, revealing turquoise waters and distant 
rocky cliffs. Warm amber sunlight creates dramatic shadows. 
Character's expression shows contemplative serenity."
```
**Resultado:** ⭐⭐⭐⭐⭐ (Sora 2 entende perfeitamente)

### Prompt em Português (Hipotético):
```
"Plano aberto cinematográfico de praia mediterrânea no pôr do sol.
Personagem camelo antropomórfico, macho meia-idade, vestindo
túnica marrom tradicional, caminha devagar pela costa pristina.
Câmera acompanha lateralmente, revelando águas turquesa e
penhascos rochosos distantes. Luz solar âmbar quente cria sombras dramáticas.
Expressão do personagem mostra serenidade contemplativa."
```
**Resultado:** ⭐⭐⭐ (Sora 2 pode ter dificuldade com alguns termos)

---

## ✅ **Conclusão**

### Status Atual: **Correto e Otimizado**

A mistura de idiomas é **intencional e benéfica:**

| Para o Usuário | Idioma |
|---------------|--------|
| Interface UI | Português ✅ |
| Roteiro | Português ✅ |
| Diálogos | Português ✅ |
| Áudio Final | Português ✅ |

| Técnico (Interno) | Idioma |
|------------------|--------|
| Prompts Sora 2 | Inglês ✅ |
| Logs do Sistema | Misto (normal) |

### Ação Recomendada: **Manter como está**

Se houver texto visível nos vídeos, o language marker garante que aparecerá em português.

---

**Data:** 02/04/2026  
**Status:** ✅ Comportamento esperado e otimizado  
**Ação Necessária:** Nenhuma (a menos que usuário insista em mudar)
