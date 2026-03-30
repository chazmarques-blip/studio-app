# 🎵 Sound Design Agent - Sistema Inteligente de Atribuição de Vozes

## 🎯 Visão Geral

O **Sound Design Agent** é um agente especialista em sonoplastia que trabalha automaticamente com o criador de personagens para atribuir vozes perfeitas baseadas em:

- **Espécie/Tipo** (pássaro, leão, golfinho, humano, etc.)
- **Características Físicas** (tamanho, build)
- **Idade** (criança, adulto, idoso)
- **Personalidade** (brincalhão, sábio, enérgico, sério)
- **Papel narrativo** (protagonista, vilão, alívio cômico)

## 🧠 Inteligência do Sistema

### Expertise do Agente

O Sound Designer Agent possui conhecimento profundo de:

1. **Bioacústica de Espécies**
   - Pássaros: Pitch alto, tom leve, tempo rápido
   - Mamíferos predadores: Grave, autoritário, ressonante
   - Mamíferos herbívoros: Suave, quente, pitch médio-alto
   - Aquáticos: Fluido, misterioso, variado
   - Répteis: Suave, calculado, sibilante

2. **Mapeamento Idade → Voz**
   - Criança (0-12): Alto, brincalhão, inocente
   - Adolescente (13-17): Médio-alto, entusiasmado
   - Jovem adulto (18-35): Claro, confiante, dinâmico
   - Adulto (36-60): Rico, autoritário, experiente
   - Idoso (60+): Grave, sábio, tempo lento

3. **Personalidade → Características Vocais**
   - Brincalhão: Tempo rápido, pitch variado, tom leve
   - Sábio: Tempo lento, pitch grave, tom calmo
   - Enérgico: Tempo rápido, tom brilhante, pitch variado
   - Sério: Tempo estável, pitch controlado, tom forte
   - Vilão: Agudo ou muito grave, ameaçador, calculado

## 🎬 Exemplos Práticos

### Caso 1: Pomba da Paz

**Entrada do Personagem:**
```json
{
  "name": "Pomba da Paz",
  "description": "Uma pomba gentil e serena que espalha harmonia",
  "age": "young adult",
  "role": "supporting"
}
```

**Análise do Sound Designer:**
```json
{
  "character_type": "bird - dove",
  "recommended_voice": {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "voice_name": "Rachel",
    "confidence_score": 95
  },
  "reasoning": "Rachel's soft, gentle tone perfectly matches a dove's peaceful nature. Her medium-high pitch suits a small bird, and her calm delivery reflects the character's serene personality.",
  "voice_characteristics_needed": {
    "pitch": "medium-high",
    "tone": "soft, gentle, warm",
    "tempo": "calm, measured",
    "timbre": "light, airy"
  }
}
```

### Caso 2: Leão Rei

**Entrada do Personagem:**
```json
{
  "name": "Leão Rei",
  "description": "Líder majestoso da savana, forte e protetor",
  "age": "adult",
  "role": "protagonist"
}
```

**Análise do Sound Designer:**
```json
{
  "character_type": "mammal - lion",
  "recommended_voice": {
    "voice_id": "N2lVS1w4EtoT3dr4eOWO",
    "voice_name": "Callum",
    "confidence_score": 98
  },
  "reasoning": "Callum's deep, authoritative voice perfectly captures the lion's majestic power. His rich bass tone matches the physical size and commanding presence, while maintaining warmth for a heroic protagonist.",
  "voice_characteristics_needed": {
    "pitch": "deep bass",
    "tone": "powerful, authoritative, warm",
    "tempo": "measured, confident",
    "timbre": "rich, resonant"
  }
}
```

### Caso 3: Golfinho Alegre

**Entrada do Personagem:**
```json
{
  "name": "Dolly",
  "description": "Golfinho jovem e brincalhão que adora fazer novos amigos",
  "age": "child",
  "role": "comic relief"
}
```

**Análise do Sound Designer:**
```json
{
  "character_type": "aquatic - dolphin",
  "recommended_voice": {
    "voice_id": "pNInz6obpgDQGcFmaJgB",
    "voice_name": "Adam",
    "confidence_score": 93
  },
  "reasoning": "Adam's playful, intelligent voice matches a young dolphin's friendly nature. His medium-high pitch and expressive delivery capture the character's energetic and social personality perfectly.",
  "voice_characteristics_needed": {
    "pitch": "medium-high",
    "tone": "playful, friendly, intelligent",
    "tempo": "quick, animated",
    "timbre": "bright, fluid"
  }
}
```

## 🔧 Implementação Técnica

### Arquivo Principal
`/app/backend/routers/studio/sound_design_agent.py`

### Fluxo de Funcionamento

```
1. Criação de Personagens
   └─> Gera imagens (Gemini)
   └─> Envia para Sound Designer Agent
   
2. Sound Designer Agent (Paralelo)
   ├─> Analisa cada personagem
   ├─> Identifica espécie/tipo
   ├─> Determina características vocais ideais
   ├─> Consulta biblioteca ElevenLabs
   ├─> Seleciona voz primária + alternativa
   └─> Retorna reasoning detalhado
   
3. Merge Inteligente
   ├─> Verifica duplicatas
   ├─> Usa alternativa se voz já usada
   └─> Garante distintividade
   
4. Salva no Projeto
   └─> voice_map: {character_name: voice_id}
   └─> detailed_assignments: reasoning completo
```

### Endpoints

#### 1. Auto-Atribuição Inteligente
```http
POST /api/studio/projects/{project_id}/auto-assign-voices
```

**Response:**
```json
{
  "voice_map": {
    "Pomba da Paz": "21m00Tcm4TlvDq8ikWAM",
    "Leão Rei": "N2lVS1w4EtoT3dr4eOWO",
    "Dolly": "pNInz6obpgDQGcFmaJgB"
  },
  "assignments": [
    {
      "character": "Pomba da Paz",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "voice_name": "Rachel",
      "confidence": 95,
      "reasoning": "Rachel's soft, gentle tone...",
      "characteristics": {
        "pitch": "medium-high",
        "tone": "soft, gentle, warm"
      },
      "status": "recommended"
    }
  ],
  "stats": {
    "total_characters": 24,
    "unique_voices_used": 22,
    "fallbacks": 0,
    "alternatives": 2
  }
}
```

#### 2. Integração Automática na Geração de Personagens

Quando `POST /api/studio/projects/{project_id}/characters/generate-all` é chamado:

1. Gera imagens dos personagens
2. **Automaticamente** chama Sound Designer Agent
3. Atribui vozes a todos os personagens
4. Salva voice_map no projeto

**Response Estendido:**
```json
{
  "total": 24,
  "generated": 18,
  "reused": 6,
  "failed": 0,
  "voice_assignments": {
    "assigned": 24,
    "details": [
      {
        "character_name": "Pomba da Paz",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "confidence": 95,
        "reasoning": "..."
      }
    ]
  }
}
```

## 📊 Regras de Distintividade

O sistema garante que cada personagem tenha voz única:

1. **Detecção de Duplicatas**: Monitora vozes já atribuídas
2. **Uso de Alternativas**: Se voz recomendada já foi usada, usa alternativa
3. **Fallback Inteligente**: Se necessário, busca próxima melhor opção
4. **Score de Confiança**: Indica qualidade do match (0-100)

## 🎨 Características Vocais Mapeadas

### Pitch (Tom)
- **Ultra-alto**: Insetos, pássaros muito pequenos
- **Alto**: Crianças, pássaros pequenos/médios
- **Médio-alto**: Jovens, golfinhos, herbívoros pequenos
- **Médio**: Adultos humanos, mamíferos médios
- **Grave**: Adultos idosos, predadores grandes
- **Ultra-grave**: Elefantes, baleias, criaturas míticas

### Tempo
- **Muito rápido**: Personagens hiperativos, insetos
- **Rápido**: Jovens enérgicos, personagens cômicos
- **Médio**: Adultos normais
- **Lento**: Sábios, idosos, criaturas grandes
- **Muito lento**: Seres ancestrais, montanhas, árvores mágicas

### Tom (Mood)
- **Brilhante**: Alegres, otimistas
- **Suave**: Gentis, calmos
- **Forte**: Heróicos, autoritários
- **Escuro**: Vilões, misteriosos
- **Fluido**: Aquáticos, etéreos

## 🧪 Testes

### Teste Manual
```bash
# 1. Criar projeto com personagens diversos
# 2. Gerar personagens automaticamente
# 3. Verificar voice_map no projeto
# 4. Validar que cada voz é apropriada
```

### Validação de Qualidade

Critérios de sucesso:
- ✅ Cada personagem tem voz atribuída
- ✅ Vozes são distintas (duplicatas < 10%)
- ✅ Confidence score médio ≥ 85%
- ✅ Espécies têm vozes apropriadas (pássaros agudos, leões graves)
- ✅ Idades são respeitadas (crianças agudas, idosos graves)

## 🔮 Próximas Evoluções

### Fase 2: Voice Design (Criar Vozes Customizadas)
```python
# Usar ElevenLabs Voice Design API para criar vozes únicas
voice_design_prompt = f"""
Create a voice for:
- Species: {species}
- Age: {age}
- Personality: {personality}
- Gender: {gender}
"""

custom_voice = elevenlabs.voice_design.create(
    text=voice_design_prompt,
    gender=gender,
    age=age
)
```

### Fase 3: Voice Cloning
Para personagens específicos, clonar vozes reais:
```python
cloned_voice = elevenlabs.voices.clone(
    name=character_name,
    files=[sample1.mp3, sample2.mp3],
    description=character_description
)
```

### Fase 4: Ajuste Fino de Parâmetros
```python
voice_settings = {
    "stability": 0.7,     # Consistência
    "similarity_boost": 0.8,  # Fidelidade ao original
    "style": 0.6,         # Expressividade
    "use_speaker_boost": True  # Clareza
}
```

## 📝 Notas Importantes

1. **Biblioteca ElevenLabs**: 50+ vozes pré-configuradas em `ELEVENLABS_VOICES`
2. **Multilingual**: Todas as vozes suportam `eleven_multilingual_v2`
3. **Fallback**: Sistema sempre tem voz padrão (Rachel) como backup
4. **Parallel Processing**: Análise de personagens em paralelo para velocidade
5. **Idempotência**: Pode ser re-executado sem problemas

## 🎓 Referências

- ElevenLabs Voice Library: https://elevenlabs.io/voice-library
- Bioacústica: Princípios de vocalização animal
- Disney/Pixar Casting Guidelines: Matching voice to character archetype
