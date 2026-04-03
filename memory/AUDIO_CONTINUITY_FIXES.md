# Correções de Áudio e Continuidade - StudioX
**Data**: 2026-04-03  
**Objetivo**: Corrigir problemas de idioma inconsistente, texto truncado e falta de continuidade

---

## 🎯 **PROBLEMAS IDENTIFICADOS**

### ❌ Problema 1: Idioma Inconsistente (EN/PT misturado)
**Causa**: ElevenLabs `language_code` era opcional, às vezes não era passado
**Sintoma**: Algumas cenas em inglês, outras em português no mesmo projeto

### ❌ Problema 2: Texto do Diálogo Modificado/Truncado
**Causa**: Modo NARRATED estava usando Claude para **reescrever** o diálogo ao invés de usar o texto aprovado
**Sintoma**: Áudio falava texto diferente do que estava escrito no script

### ❌ Problema 3: Falta de Continuidade
**Causa**: Módulos `dialogue_timeline.py` e `video_stitching.py` existem mas não estão integrados
**Sintoma**: Sem sincronização precisa entre cenas

---

## ✅ **CORREÇÕES IMPLEMENTADAS**

### 1. **ElevenLabs TTS - Idioma Sempre Obrigatório**
**Arquivo**: `/app/backend/routers/studio/narration.py` linha 615-651

**Antes**:
```python
lang_hint = LANG_HINTS.get(language_code, "")
kwargs = {...}
if lang_hint:
    kwargs["language_code"] = lang_hint  # ❌ Opcional!
```

**Depois**:
```python
lang_hint = LANG_HINTS.get(language_code, "pt")  # ✅ Default "pt"
kwargs = {
    ...
    "language_code": lang_hint,  # ✅ SEMPRE passado
}
logger.info(f"ElevenLabs TTS: lang={lang_hint}, voice={voice_id[:8]}, text_len={len(text)}")
```

**Resultado**: TODAS as chamadas ElevenLabs agora explicitamente especificam o idioma.

---

### 2. **Modo NARRATED - Usar Diálogo Exato (Sem Reescrever)**
**Arquivo**: `/app/backend/routers/studio/narration.py` linha 782-836

**Antes**:
```python
# ❌ Claude REESCREVE o diálogo
narration_system = """Write compelling narration for EACH scene..."""
script_result = _call_claude_sync(narration_system, f"Scenes:\n{scene_summaries}")
narrations = json.loads(script_result)  # Novo texto gerado!
```

**Depois**:
```python
# ✅ Usa EXATO texto do diálogo aprovado
for i, scene in enumerate(scenes):
    text = scene.get("dialogue", "")  # Texto original
    if not text.strip():
        text = scene.get("narrated_text", "")
    if not text.strip():
        text = scene.get("description", "")[:120]
    
    cleaned_text = _clean_narration_for_tts(text)  # Limpa mas preserva
    
    # Log comparação para debug
    logger.info(f"Scene {scene_num}: {len(text)} → {len(cleaned_text)} chars")
    logger.debug(f"Original: {text[:100]}...")
    logger.debug(f"Cleaned: {cleaned_text[:100]}...")
    
    audio_bytes = _generate_narration_audio(cleaned_text, voice_id, stability, similarity, style_val, lang)
```

**Resultado**: Áudio fala EXATAMENTE o que está escrito no diálogo aprovado.

---

### 3. **Modo DUBBED - Melhor Limpeza de Texto**
**Arquivo**: `/app/backend/routers/studio/narration.py` linha 728-742

**Antes**:
```python
text = ":".join(part.split(":")[1:]).strip().strip("'\"")
# ❌ Sem limpeza, marcadores podem ir para TTS
audio_bytes = _generate_narration_audio(text, matched_voice, ...)
```

**Depois**:
```python
text = ":".join(part.split(":")[1:]).strip().strip("'\"")

# ✅ Limpa texto antes de enviar para TTS
from pipeline.media import _clean_narration_for_tts
cleaned_text = _clean_narration_for_tts(text)
if not cleaned_text.strip():
    logger.warning(f"Scene {scene_num} part {pi} cleaned to empty, using original")
    cleaned_text = text

# Log detalhado com nome do personagem
logger.debug(f"Scene {scene_num} - {matched_char_name}: '{cleaned_text[:50]}...' (lang={lang})")
audio_bytes = _generate_narration_audio(cleaned_text, matched_voice, stability, similarity, style_val, lang)
```

**Resultado**: Remove marcadores `[pausa]`, `<emotion>`, etc. mas preserva diálogo.

---

### 4. **Pós-Produção - Mesma Correção**
**Arquivo**: `/app/backend/routers/studio/post_production.py` linha 100-157

**Mudança**: Aplicada mesma lógica (usar diálogo exato) no fluxo de pós-produção para consistência.

---

### 5. **_clean_narration_for_tts - Segurança Contra Over-Cleaning**
**Arquivo**: `/app/backend/pipeline/media.py` linha 771-865

**Antes**:
```python
# ❌ Se regex agressivo remover TUDO, retorna string vazia
return text
```

**Depois**:
```python
# ✅ Se limpeza remover TUDO, retorna original
if not text or len(text) < 5:
    # Tenta limpeza mínima
    text = raw_text
    text = re.sub(r'\[\d+\s*-\s*\d+s?\]\s*:?\s*', '', text)  # Remove timing
    text = re.sub(r'<[^>]+>', '', text)  # Remove angle brackets
    text = text.strip()
    
    if not text or len(text) < 5:
        # Ainda vazio? Retorna original raw
        return raw_text.strip()

return text
```

**Resultado**: Nunca perde diálogo por limpeza excessiva.

---

## 📊 **LOGS ADICIONADOS PARA DEBUG**

1. **ElevenLabs TTS Call**:
   ```
   INFO: ElevenLabs TTS: lang=pt, voice=VR6AewLT, text_len=145
   ```

2. **Texto Original vs Limpo**:
   ```
   INFO: Studio [abc123]: Scene 5 text cleaned: 180 → 145 chars
   DEBUG: Original: [0-4s]: Narrador: 'Era uma vez...'
   DEBUG: Cleaned: Era uma vez...
   ```

3. **Modo DUBBED - Personagem**:
   ```
   DEBUG: Studio [abc123]: Scene 8 - Lulu: 'Au au! Eu sou sincero!' (lang=pt)
   ```

---

## 🧪 **COMO TESTAR**

### Teste 1: Idioma Consistente
1. Criar projeto com `language: "pt"`
2. Gerar narração
3. Verificar logs: `grep "ElevenLabs TTS: lang=" /var/log/supervisor/backend.err.log`
4. ✅ Todos devem mostrar `lang=pt`

### Teste 2: Diálogo Exato
1. Abrir projeto existente
2. Verificar campo `scene.dialogue` no banco
3. Regenerar narração
4. Comparar logs: "Original:" vs "Cleaned:"
5. ✅ Cleaned deve ser igual ou muito similar ao Original (só sem marcadores)

### Teste 3: Modo DUBBED
1. Projeto com `audio_mode: "dubbed"`
2. Diálogo: `Narrador: 'Texto 1' / Lulu: 'Texto 2'`
3. Verificar logs mostram ambos personagens
4. ✅ Cada personagem usa voz diferente, lang consistente

---

## 🚀 **PRÓXIMOS PASSOS (Fase 2 - Continuidade)**

**NÃO IMPLEMENTADO AINDA** (aguardando feedback do usuário):

1. Integrar `dialogue_timeline.py`:
   - Gerar timeline precisa de beats de diálogo
   - Exemplo: `[0-2s: Narrador, 2-5s: Personagem A, 5-8s: Personagem B]`

2. Sincronização com vídeo:
   - Alinhar início de áudio com movimento de personagem
   - Adicionar pausas entre falas (0.3s)

3. Transições entre cenas:
   - Fade in/out de áudio
   - Cortes naturais em diálogos longos

---

## ⚠️ **BREAKING CHANGES**

**NENHUMA!** Todas as mudanças são backwards-compatible:
- Projetos antigos continuam funcionando
- API pública não mudou
- Apenas correção de bugs internos

---

## 📝 **CREDENCIAIS DE TESTE**

- Email: `test@studiox.com`
- Password: `studiox123`
- Projeto de teste: "Farofa: O Lulu da Pomerânia Sincero"

---

## 🔑 **CHAVES NECESSÁRIAS**

- ✅ `ELEVENLABS_API_KEY`: Configurada em `/app/backend/.env`
- ✅ `ANTHROPIC_API_KEY`: Configurada (para Claude)
- ✅ `OPENAI_API_KEY`: Configurada (para Sora 2)

---

**Status**: ✅ Fase 1 completa - Aguardando teste do usuário  
**Próxima etapa**: Testar com projeto real "Farofa" e validar correções
