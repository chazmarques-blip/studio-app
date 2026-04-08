# Criação de Personagens em Lote

## Visão Geral
Sistema para criar múltiplos personagens de uma vez através de prompts em lote.

## Como Funciona

### Interface do Usuário
1. No modal "Criar Personagem", clique em "Por Prompt"
2. Escolha entre **Individual** ou **Em Lote**
3. **Modo Em Lote**: 
   - Textarea grande para colar prompts (um por linha)
   - Contador automático de quantos personagens serão criados
   - Progress bar durante a geração

### Exemplo de Uso
```
Pescocinho Biblizoo Baby, girafa bebê fofa com pescoço longo
Jonas Biblizoo Baby, leão adolescente corajoso e forte
Maria Biblizoo Baby, elefante filhote sorridente e gentil
```

## Backend - Endpoint

**POST** `/api/data/avatars/batch`

### Request
```json
{
  "prompts": [
    "Pescocinho Biblizoo Baby, girafa bebê",
    "Jonas Biblizoo Baby, leão corajoso"
  ],
  "style": "custom",
  "gender": "female"
}
```

### Response
```json
{
  "created": [...avatars],
  "failed": [{
    "prompt": "...",
    "error": "..."
  }],
  "total": 10,
  "success": 8
}
```

## Funcionalidades Automáticas

### 1. Auto-Extração de Nome
- Extrai nome do personagem do início do prompt
- Exemplo: "Pescocinho Biblizoo Baby, descrição" → Nome: "Pescocinho Biblizoo Baby"

### 2. Auto-Assignment de Pastas
- Se o nome contém tags conhecidas (ex: "Biblizoo Baby"), o personagem é automaticamente atribuído à pasta correspondente
- Se a pasta não existe, é criada automaticamente

### 3. Limite de Segurança
- Máximo de 20 personagens por lote
- Delay de 0.5s entre cada geração para evitar rate limits

## Arquivos Modificados

### Frontend
- `/app/frontend/src/components/pipeline/AvatarModal.jsx`
  - Toggle Individual/Em Lote
  - UI de progress indicator
  - Textarea adaptativo

- `/app/frontend/src/components/PipelineView.jsx`
  - State: `promptBatchMode`, `batchProgress`
  - Função: `generateAvatarBatch()`

### Backend
- `/app/backend/routers/data.py`
  - Endpoint: `POST /api/data/avatars/batch`
  - Função auxiliar: `_extract_name_from_prompt()`

## Fluxo de Criação

```
1. Usuário cola prompts
   ↓
2. Frontend valida e envia para backend
   ↓
3. Backend processa cada prompt:
   - Gera imagem com Gemini
   - Extrai nome automaticamente
   - Detecta pasta baseada no nome
   - Salva no banco de dados
   ↓
4. Frontend atualiza lista de avatares
   ↓
5. Toast de sucesso com quantidade criada
```

## Limitações
- Máximo 20 personagens por lote
- Processamento sequencial (evita rate limits)
- Tempo aproximado: ~3-5s por personagem

## Próximas Melhorias Sugeridas
- [ ] Preview dos personagens antes de salvar
- [ ] Edição em lote (aplicar mudanças a todos)
- [ ] Export/Import de prompts (CSV, JSON)
- [ ] Templates de prompts pré-definidos
