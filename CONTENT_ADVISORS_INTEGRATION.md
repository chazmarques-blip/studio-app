# 🎭 Content Advisors System - Documentação Completa

## 📋 Visão Geral

O **Content Advisors System** (Fase 2 do Pipeline Roadmap) permite adaptar automaticamente o conteúdo do roteiro para diferentes públicos e formatos sem quebrar o pipeline genérico.

### ✅ Status: **IMPLEMENTADO**
- ✅ Backend completo
- ✅ 3 Advisors funcionais
- ✅ Sistema de chain modular
- ✅ API endpoints criados
- ⏸ Frontend UI (pendente)

---

## 🎯 O Que São Content Advisors?

Content Advisors são **agentes especializados** que modificam o roteiro após a criação pelo Screenwriter, adaptando-o para:
- **Faixa etária específica** (ex: 2-5 anos)
- **Formato de apresentação** (música, narração dramatizada)
- **Estilo de narração** (tons e pausas)

### Princípios:
1. **Modular**: Cada advisor é independente
2. **Opt-in**: Todos desabilitados por padrão
3. **Não-destrutivo**: Roteiro original sempre preservado
4. **Escalável**: Fácil adicionar novos advisors

---

## 🧩 Advisors Disponíveis

### 1️⃣ **Toddler Content Advisor** (`toddler_content`)
**Objetivo**: Adaptar conteúdo para crianças de 2-5 anos

**Características**:
- Vocabulário simples (200-500 palavras básicas)
- Frases curtas (máximo 6-8 palavras)
- Repetição para fixação ("Quem é...? ... é...!")
- Perguntas retóricas para engajamento
- Conceitos concretos (evita abstrações)
- Ritmo e musicalidade

**Exemplo de transformação**:
```
Original: "Abraão era um homem de grande fé que confiava plenamente em Deus"

Adaptado: "Quem é Abraão? Abraão é papai!
Abraão ama Deus muito muito!
Deus fala: 'Oi Abraão!'
Abraão escuta Deus.
Abraão é feliz!"
```

**Configuração**:
```json
{
  "toddler_content": {
    "enabled": true,
    "vocabulary_level": "simple",
    "repetition_frequency": "high"
  }
}
```

---

### 2️⃣ **Musical Composer Advisor** (`musical_composer`)
**Objetivo**: Transformar história em música infantil chiclete

**Características**:
- Estrutura: Refrão → Verso 1 → Refrão → Verso 2 → Refrão
- Refrão cativante e repetitivo (4-6 linhas)
- Versos simples contando a história
- Rimas naturais
- Sons onomatopaicos (la la, na na)
- Letra + estilo musical para ElevenLabs Music API

**Exemplo de transformação**:
```
Original: "Noé construiu uma grande arca e salvou os animais do dilúvio"

Adaptado:
[Refrão]
♪ Noé, Noé, construiu um barco grande!
♪ Chuva, chuva, água por todo lugar!
♪ Animais, animais, todos vão entrar!
♪ Lalala lalala, Noé vai nos salvar! ♪

[Verso 1]
Noé trabalha, martelando o barco
Dois por dois, os bichinhos chegando
Leão e leoa, elefante e passarinho
Todos juntos cantando bem baixinho!
```

**Configuração**:
```json
{
  "musical_composer": {
    "enabled": true,
    "music_style": "chiclete",
    "duration_target": "2-3min"
  }
}
```

**Retorno**:
```json
{
  "lyrics": "...",
  "style": "upbeat children's music, chiclete, catchy chorus, xylophone, tambourine...",
  "duration": 180,
  "structure": "chorus-verse-chorus-verse-chorus"
}
```

---

### 3️⃣ **Narration Style Advisor** (`narration_style`)
**Objetivo**: Adicionar marcações de estilo para síntese de voz

**Marcações disponíveis**:
- `[PAUSA]` - Pausa dramática (1-2 segundos)
- `[ENFASE: palavra]` - Enfatizar palavra específica
- `[TOM: tipo]` - Mudar tom (entusiasmado, calmo, misterioso, suave, animado)
- `[VELOCIDADE: tipo]` - Ritmo (rápido, normal, lento)

**Exemplo de transformação**:
```
Original: "Abraão olhou para o céu. Deus falou com ele. 'Abraão, você confia em mim?'"

Adaptado: "[TOM: calmo] Abraão olhou para o [ENFASE: céu]. [PAUSA] [TOM: misterioso] Deus falou com ele. [PAUSA] [TOM: suave] 'Abraão, você [ENFASE: confia] em mim?'"
```

**Configuração**:
```json
{
  "narration_style": {
    "enabled": true,
    "tone": "enthusiastic",
    "voice_guidance": true
  }
}
```

---

## 🔄 Como o Sistema Funciona

### Fluxo Completo

```
1. Screenwriter gera roteiro
   ↓
2. Sistema verifica: has_active_advisors(project)?
   ↓ SIM
3. AdvisorChain processa em sequência:
   - Toddler (se enabled) → adapta linguagem
   - Musical (se enabled) → transforma em música
   - Narration (se enabled) → adiciona marcações
   ↓
4. Resultados salvos em project.agents_output.content_advisors
   ↓
5. Frontend exibe indicador de advisors aplicados
```

### Arquitetura

```
/app/backend/
├── services/
│   ├── content_advisors.py      # 3 classes de advisors
│   └── advisor_chain.py          # Sistema de chain e helpers
├── routers/studio/
│   ├── screenwriter.py           # Integração no pipeline
│   └── projects.py               # API endpoints de configuração
└── core/
    └── llm.py                    # get_claude_client helper
```

---

## 🛠️ API Endpoints

### 1. **Configurar Content Advisors**
```http
POST /api/studio/projects/{project_id}/content-advisors
Content-Type: application/json

{
  "content_advisors": {
    "toddler_content": {
      "enabled": true,
      "vocabulary_level": "simple",
      "repetition_frequency": "high"
    },
    "musical_composer": {
      "enabled": false
    },
    "narration_style": {
      "enabled": true,
      "tone": "enthusiastic",
      "voice_guidance": true
    }
  }
}
```

**Resposta**:
```json
{
  "status": "ok",
  "enabled_advisors": ["toddler_content", "narration_style"],
  "config": { ... }
}
```

---

### 2. **Obter Configuração Atual**
```http
GET /api/studio/projects/{project_id}/content-advisors
```

**Resposta**:
```json
{
  "current_config": { ... },
  "default_configs": {
    "toddler": { ... },
    "musical": { ... },
    "narrated": { ... },
    "default": { ... }
  }
}
```

---

## 📦 Configurações Pré-definidas

### Projeto Tipo "Toddler" (2-5 anos)
```json
{
  "toddler_content": { "enabled": true, "vocabulary_level": "simple", "repetition_frequency": "high" },
  "musical_composer": { "enabled": false },
  "narration_style": { "enabled": true, "tone": "enthusiastic", "voice_guidance": true }
}
```

### Projeto Tipo "Musical"
```json
{
  "toddler_content": { "enabled": false },
  "musical_composer": { "enabled": true, "music_style": "chiclete", "duration_target": "2-3min" },
  "narration_style": { "enabled": false }
}
```

### Projeto Tipo "Narrated" (apenas narração)
```json
{
  "toddler_content": { "enabled": false },
  "musical_composer": { "enabled": false },
  "narration_style": { "enabled": true, "tone": "calm", "voice_guidance": true }
}
```

---

## 🧪 Como Testar

### 1. Configurar um projeto
```bash
curl -X POST "$API_URL/api/studio/projects/{project_id}/content-advisors" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_advisors": {
      "toddler_content": {
        "enabled": true,
        "vocabulary_level": "simple",
        "repetition_frequency": "high"
      }
    }
  }'
```

### 2. Criar roteiro via Screenwriter
- O sistema automaticamente detectará que `toddler_content` está habilitado
- Aplicará a adaptação após gerar o roteiro

### 3. Verificar resultado
```bash
curl -X GET "$API_URL/api/studio/projects/{project_id}" \
  -H "Authorization: Bearer $TOKEN"
```

Procure por:
```json
{
  "agents_output": {
    "content_advisors": {
      "applied": ["toddler_content"],
      "stages": {
        "toddler_content": "Adaptação aplicada..."
      },
      "final_length": 1234
    }
  }
}
```

---

## 🎨 Frontend Pendente

### UI Necessária:

1. **Modal de Seleção de Tipo de Conteúdo** (ao iniciar Redator)
   - História narrada + diálogos (padrão)
   - História 100% narrada (com entonação)
   - Música infantil (chiclete)

2. **Badge de Advisors Ativos** (na UI do projeto)
   ```jsx
   {project.content_advisors && (
     <span className="badge">
       ✨ {enabledAdvisors.join(", ")}
     </span>
   )}
   ```

3. **Configuração Avançada** (settings do projeto)
   - Toggles para habilitar/desabilitar cada advisor
   - Sliders para configurações (repetition_frequency, tone, etc.)

---

## 🔮 Próximos Passos

### Fase 3: Pipeline Visual Tracker
- Server-Sent Events (SSE) para mostrar progresso
- UI mostrando: "Carregando personagens..." → "Criando história..." → "Adaptando para 2-5 anos..." → "Finalizado"

### Fase 4: Music Integration Frontend
- Botão "Gerar Música" na UI
- Player de áudio com a música gerada
- Download da música MP3

### Fase 5: Company Configuration
- Configurações default por empresa
- Herança automática para novos projetos

---

## 📝 Notas Técnicas

### Execução Síncrona vs Assíncrona
O `_run_screenwriter_background` roda em thread separada (não async), então usamos:
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
advisor_results = loop.run_until_complete(chain.process(screenplay_text, project))
loop.close()
```

### Error Handling
Se um advisor falhar, o sistema continua sem ele:
```python
try:
    processed = await advisor.refine(current_content, advisor_config)
except Exception as e:
    logger.error(f"Advisor {advisor.name} failed: {e}")
    # Continue com próximo advisor
```

### Performance
- Cada advisor adiciona ~5-10 segundos ao tempo de geração
- Advisors rodam sequencialmente (não em paralelo)
- Tokens adicionais consumidos: ~1000-2000 por advisor

---

## ✅ Checklist de Implementação

- [x] Criar classes de advisors (`content_advisors.py`)
- [x] Criar sistema de chain (`advisor_chain.py`)
- [x] Integrar no screenwriter (`screenwriter.py`)
- [x] Criar endpoints de configuração (`projects.py`)
- [x] Adicionar helper `get_claude_client` (`llm.py`)
- [x] Testar backend funcionando
- [ ] Criar UI de seleção de tipo de conteúdo
- [ ] Criar badge de advisors ativos
- [ ] Criar página de configuração avançada
- [ ] Testing completo com testing agent

---

## 🎉 Conclusão

O **Content Advisors System** está **100% funcional no backend**. Agora é possível:
1. Configurar advisors via API
2. Gerar roteiros automaticamente adaptados
3. Salvar múltiplas versões (original + adaptadas)
4. Expandir facilmente com novos advisors

**Próximo passo**: Implementar a UI frontend ou prosseguir para Fase 3 (Pipeline Visual Tracker).
