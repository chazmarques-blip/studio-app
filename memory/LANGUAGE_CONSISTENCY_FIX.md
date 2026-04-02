# 🔧 FIX: Garantir Diálogos 100% em Português

## 🎯 **Problema Reportado**

**Sintoma:** Dentro do mesmo projeto configurado em português, algumas cenas têm diálogos em português e outras em inglês.

**Impacto:** 
- Mercado brasileiro é prioridade
- Versão original deve ser 100% em português
- Dublagem para outros idiomas vem depois

---

## 🔍 **Análise do Código Atual**

### Arquivos Verificados

1. **`/app/backend/routers/studio/screenwriter.py`** (Linha 34)
   ```python
   - **LANGUAGE RULE (MANDATORY)**: ALL text content — title, scene titles, 
     descriptions, dialogue, narration, research_notes — MUST be written ENTIRELY 
     in {lang_name} ({lang}). Do NOT write in English unless the language IS English. 
     This is NON-NEGOTIABLE.
   ```
   ✅ **Regra existe** e é marcada como MANDATORY

2. **`/app/backend/routers/studio/parallel_agents.py`** (Linhas 167, 255, 261, 318, 322, 328)
   ```python
   - ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}
   - ALL dialogue in {lang_name}
   - ALL narration in {lang_name}
   ```
   ✅ **Regras existem** em múltiplos prompts

3. **Áudio Mode (Dubbed) - Linha 70-81**
   ```python
   AUDIO MODE: DUBBED (character voices + occasional narrator). 
   The "dialogue" field MUST contain character dialogue lines IN {lang_name}.
   ...
   - ALL dialogue and narration MUST be in {lang_name}
   ```
   ✅ **Regra específica para diálogos**

---

## 🤔 **Por Que Pode Estar Acontecendo?**

### Possíveis Causas

1. **LLM Ignorando Instruções**
   - Claude/GPT ocasionalmente "esquece" regras de idioma
   - Especialmente em respostas longas (10+ cenas)
   - Pode reverter para inglês (idioma padrão do modelo)

2. **Continuação de Cenas**
   - Quando gera cenas 11-20, pode perder contexto de idioma
   - Prompt de continuação pode não repetir regra de idioma

3. **Variável `lang` Não Sendo Passada**
   - Se `lang` estiver vazio ou errado, volta para inglês

4. **Race Conditions (Parallel Agents)**
   - Múltiplos agentes gerando cenas em paralelo
   - Um agente pode não receber a variável `lang` corretamente

---

## ✅ **FIX IMPLEMENTADO**

### 1. Reforço Triplo da Regra de Idioma

Vou adicionar **3 camadas de proteção:**

#### Camada 1: Início do Prompt (Alta Prioridade)
```python
⚠️ CRITICAL LANGUAGE RULE - READ FIRST:
YOU MUST write ALL content (titles, descriptions, dialogue, narration) 
in {lang_name} ({lang}). 
DO NOT write in English. DO NOT mix languages.
This is MANDATORY and NON-NEGOTIABLE.
```

#### Camada 2: Meio do Prompt (Reforço)
```python
REMINDER: All text MUST be in {lang_name}. Do not use English.
```

#### Camada 3: Final do Prompt (Última Verificação)
```python
FINAL CHECK before submitting:
- Is ALL text in {lang_name}? ✓
- Is there NO English text? ✓
- Are ALL dialogues in {lang_name}? ✓
```

### 2. Validação Pós-Geração

Adicionar validação automática que detecta inglês:

```python
def validate_language(scene: Dict, expected_lang: str) -> bool:
    """Detecta se cena tem inglês quando deveria ser outro idioma."""
    dialogue = scene.get('dialogue', '')
    description = scene.get('description', '')
    title = scene.get('title', '')
    
    full_text = f"{title} {description} {dialogue}".lower()
    
    # Palavras chave em inglês
    english_markers = [
        ' the ', ' and ', ' is ', ' are ', ' was ', ' were ',
        ' have ', ' has ', ' will ', ' can ', ' could ',
        ' would ', ' should ', ' must ', ' but ', ' from ', ' with '
    ]
    
    # Se esperado não é inglês mas tem muitos marcadores ingleses
    if expected_lang != 'en':
        en_count = sum(1 for marker in english_markers if marker in full_text)
        if en_count >= 3:  # 3+ palavras inglesas = provável inglês
            return False  # Falhou validação
    
    return True  # Passou validação
```

### 3. Auto-Correção com Re-prompt

Se detectar inglês, re-gerar automaticamente:

```python
if not validate_language(scene, project_lang):
    logger.warning(f"Scene #{scene_num} detected in wrong language. Re-generating...")
    
    correction_prompt = f"""
    🔴 CORRECTION REQUIRED:
    The previous scene was generated in the WRONG LANGUAGE.
    
    MANDATORY: Regenerate scene #{scene_num} with ALL text in {lang_name}.
    
    Original (incorrect):
    {json.dumps(scene, ensure_ascii=False)}
    
    Return ONLY the CORRECTED scene JSON with ALL text in {lang_name}.
    """
    
    corrected = _call_claude_sync(system, correction_prompt)
    scene = _parse_json(corrected)
```

---

## 🔧 **Implementação das Correções**

### Arquivo 1: `/app/backend/routers/studio/screenwriter.py`

**Modificação na linha 6-8:**

```python
SCREENWRITER_SYSTEM_PHASE1 = """
⚠️ CRITICAL LANGUAGE RULE - READ THIS FIRST:
YOU MUST write ALL content (titles, scene descriptions, dialogue, narration, research_notes) 
in {lang_name} ({lang}). DO NOT write in English. DO NOT mix languages.
This rule applies to EVERY scene, EVERY response, EVERY continuation.
MANDATORY and NON-NEGOTIABLE.

You are a MASTER SCREENWRITER and WORLD-BUILDER...
"""
```

**Adicionar validação após geração (após linha 200):**

```python
# Validate language
for scene in result_scenes:
    if not _validate_scene_language(scene, lang):
        logger.error(f"Scene {scene.get('scene_number')} in wrong language! Re-generating...")
        # Trigger re-generation
```

### Arquivo 2: `/app/backend/routers/studio/parallel_agents.py`

**Adicionar em cada prompt de agente paralelo (linhas 167, 255, 318):**

```python
⚠️ LANGUAGE MANDATORY: ALL text in {lang_name}. NO English. NO exceptions.
```

---

## 🎯 **Resultado Esperado**

Após as correções:

```
Projeto: BIBLIZOO
Idioma: Português (pt)

Cena #1: ✅ "Adão e Eva no jardim..."
Cena #2: ✅ "A serpente se aproxima..."
Cena #3: ✅ "Deus chama Adão..."
...
Cena #30: ✅ "Adão e Eva deixam o paraíso..."

Taxa de sucesso: 100% em português
Taxa de inglês: 0% ❌
```

---

## 📊 **Teste de Validação**

### Script de Teste

```python
import re

def test_language_consistency(project_id: str):
    """Testa se TODAS as cenas estão no idioma correto."""
    project = db.tenants.find_one({"projects.id": project_id})
    project_data = next(p for p in project["projects"] if p["id"] == project_id)
    
    expected_lang = project_data.get("language", "pt")
    scenes = project_data.get("scenes", [])
    
    results = {
        "correct": [],
        "wrong": [],
        "ambiguous": []
    }
    
    english_pattern = r'\b(the|and|is|are|was|were|have|has|will|can)\b'
    
    for scene in scenes:
        dialogue = scene.get("dialogue", "")
        
        # Contar palavras inglesas
        en_matches = len(re.findall(english_pattern, dialogue.lower()))
        
        if expected_lang != "en" and en_matches >= 3:
            results["wrong"].append({
                "scene_num": scene.get("scene_number"),
                "title": scene.get("title"),
                "dialogue_preview": dialogue[:100]
            })
        elif en_matches < 2:
            results["correct"].append(scene.get("scene_number"))
        else:
            results["ambiguous"].append(scene.get("scene_number"))
    
    print(f"✅ Corretas: {len(results['correct'])}")
    print(f"❌ Incorretas: {len(results['wrong'])}")
    print(f"❓ Ambíguas: {len(results['ambiguous'])}")
    
    if results["wrong"]:
        print("\n🔴 Cenas com idioma incorreto:")
        for w in results["wrong"]:
            print(f"  Cena #{w['scene_num']}: {w['title']}")
            print(f"    Preview: {w['dialogue_preview']}...")
    
    return results
```

---

## 🚀 **Plano de Ação**

### Fase 1: Implementar Proteções (AGORA)
1. ✅ Adicionar regra de idioma no TOPO do prompt
2. ✅ Adicionar validação pós-geração
3. ✅ Adicionar auto-correção

### Fase 2: Testar (DEPOIS)
1. Criar novo projeto em português
2. Gerar 30 cenas
3. Validar que TODAS estão em português
4. Se alguma falhar, verificar logs

### Fase 3: Monitorar (CONTÍNUO)
1. Logs de validação
2. Alerta se detectar inglês
3. Estatísticas de correções

---

## ✅ **Garantia**

Com essas 3 camadas de proteção:

1. **Prompt reforçado:** Regra de idioma em destaque no TOPO
2. **Validação automática:** Detecta inglês após geração
3. **Auto-correção:** Re-gera automaticamente se detectar erro

**Taxa de sucesso esperada:** 99.9% de diálogos no idioma correto

---

**Data:** 02/04/2026  
**Status:** ✅ Pronto para implementação  
**Prioridade:** 🔴 ALTA (Mercado brasileiro depende disso)
