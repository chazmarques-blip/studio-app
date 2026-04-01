# 📚 ACERVO DE PERSONAGENS - Planejamento Refinado

## 🎯 **Objetivo**
Manter consistência de personagens históricos (Jonas, Adão, Eva, Noé, etc.) entre diferentes filmes do BIBLIZOO, eliminando recriação desnecessária e garantindo continuidade visual/narrativa.

---

## 🔄 **Workflow Automatizado**

### **PASSO 1: Roteiro Definido**
```
Usuário cria projeto → Define briefing/roteiro
```

### **PASSO 2: Criação Automática de Personagens**
```
Pesquisador + Roteirista analisam roteiro
   ↓
Para CADA personagem identificado:
   1. 🔍 CONSULTA ACERVO primeiro
   2. ✅ Personagem existe? → APLICA AUTOMATICAMENTE (sem aprovação)
   3. ✨ Personagem novo? → CRIA e aguarda aprovação
   ↓
Retorna: [Personagens do Acervo (aplicados)] + [Personagens Novos (aguardando)]
```

### **PASSO 3: Aprovação APENAS dos Novos**
```
UI mostra:
- 🏛️ Personagens Históricos (do acervo) - MARCADOS, JÁ APLICADOS
- ✨ Personagens Novos - AGUARDAM APROVAÇÃO

Usuário aprova apenas os novos
   ↓
Novos personagens aprovados → SALVOS NO ACERVO
   ↓
Pipeline autônomo continua
```

---

## 🏛️ **Marcação Visual: Personagens Históricos**

### **UI - Personagens do Acervo:**

```
┌──────────────────────────────────────────────────┐
│ 🤖 PERSONAGENS IDENTIFICADOS                     │
│                                                  │
│ 🏛️  Do Acervo (aplicados automaticamente) (2)    │
│ ┌──────────────────────────────────────────────┐ │
│ │ 🏛️ Jonas                                      │ │
│ │    PERSONAGEM HISTÓRICO                       │ │
│ │    Usado em 3 filmes anteriores               │ │
│ │    ✅ Aplicado automaticamente                │ │
│ │                                                │ │
│ │    Profeta hebreu, barba preta encaracolada,  │ │
│ │    túnica de linho bege, olhar penetrante...  │ │
│ │                                                │ │
│ │    [📚 Ver Histórico de Uso]                  │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ ┌──────────────────────────────────────────────┐ │
│ │ 🏛️ Rei de Nínive                              │ │
│ │    PERSONAGEM HISTÓRICO                       │ │
│ │    Usado em 1 filme anterior                  │ │
│ │    ✅ Aplicado automaticamente                │ │
│ │                                                │ │
│ │    [📚 Ver Histórico de Uso]                  │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ ✨ Novos Personagens (aguardam aprovação) (1)    │
│ ┌──────────────────────────────────────────────┐ │
│ │ ✨ Grande Baleia                               │ │
│ │    NOVO PERSONAGEM                            │ │
│ │    Será adicionado ao acervo após aprovação   │ │
│ │                                                │ │
│ │    Criatura gigante, enviada por Deus para    │ │
│ │    engolir Jonas. Olhos profundos, corpo...   │ │
│ │                                                │ │
│ │    [✏️ Editar] [❌ Remover]                    │ │
│ └──────────────────────────────────────────────┘ │
│                                                  │
│ [➕ Adicionar Personagem Manual]                 │
│                                                  │
│ [✅ APROVAR NOVOS E INICIAR PIPELINE]            │
└──────────────────────────────────────────────────┘
```

---

## 🔍 **Busca Inteligente no Acervo**

### **Como Funciona:**
```python
async def search_character_library(char_name, context, tenant_id):
    """
    Busca inteligente usando LLM + tags canônicas.
    """
    library = get_character_library(tenant_id)
    
    # 1. Busca exata por canonical_id (tags)
    canonical_match = library.get(f"biblical_{char_name.lower()}")
    if canonical_match:
        return canonical_match
    
    # 2. Busca fuzzy por nome + LLM
    prompt = f"""
    Analise se "{char_name}" no contexto "{context}" 
    corresponde a algum personagem do acervo:
    
    {json.dumps(library, indent=2)}
    
    Considere:
    - Nome similar (Jonas vs Jonah)
    - Contexto histórico (profeta hebreu)
    - Papel na narrativa
    
    Se SIM (>80% confiança), retorne canonical_id.
    Se NÃO, retorne null.
    
    JSON: {"match": "canonical_id" ou null, "confidence": 0-100}
    """
    
    result = await llm_call(prompt)
    
    if result["match"] and result["confidence"] > 80:
        return library[result["match"]]
    
    return None  # Personagem novo
```

---

## 💾 **Estrutura do Acervo (MongoDB)**

### **Collection: `character_library`**

```json
{
  "_id": "ObjectId(...)",
  "tenant_id": "user_abc123",
  "canonical_id": "biblical_jonas",
  "name": "Jonas",
  "description": "Profeta hebreu, 30 anos, barba preta encaracolada, túnica de linho bege, olhar penetrante mas relutante. Fisicamente forte mas espiritualmente fraco no início.",
  "avatar_url": "https://storage.../jonas_canonical.png",
  "personality": "Relutante, teimoso, mas compassivo quando confrontado. Foge de responsabilidades mas acaba obedecendo.",
  "role": "Protagonista/Profeta",
  "historical_context": "Livro de Jonas, Antigo Testamento, 8º século AC",
  "tags": ["profeta", "biblico", "antigo_testamento", "jonas"],
  "canonical_tags": ["biblical_jonas"],
  "first_created_at": "2026-01-15T10:30:00Z",
  "first_project_id": "project_abc123",
  "first_project_name": "Jonas e a Baleia",
  "usage_history": [
    {
      "project_id": "project_abc123",
      "project_name": "Jonas e a Baleia",
      "used_at": "2026-01-15T10:30:00Z"
    },
    {
      "project_id": "project_def456",
      "project_name": "Jonas em Nínive",
      "used_at": "2026-01-22T14:20:00Z"
    },
    {
      "project_id": "project_ghi789",
      "project_name": "Jonas e o Arrependimento",
      "used_at": "2026-02-01T09:15:00Z"
    }
  ],
  "usage_count": 3,
  "last_used_at": "2026-02-01T09:15:00Z",
  "approved": true,
  "created_by": "ai_agent",
  "approved_by": "user",
  "version": 1,
  "updated_at": "2026-02-01T09:15:00Z"
}
```

---

## 🎨 **Indicadores Visuais**

| Tipo | Badge | Cor | Ações Disponíveis |
|------|-------|-----|-------------------|
| 🏛️ Histórico (acervo) | "PERSONAGEM HISTÓRICO" | Azul | Ver Histórico |
| ✨ Novo | "NOVO PERSONAGEM" | Laranja | Editar, Remover |

---

## 🔄 **Fluxo Técnico Completo**

### **Backend:**

```python
@router.post("/projects/{project_id}/characters/auto-generate")
async def auto_generate_characters(project_id, tenant):
    """
    Gera personagens consultando acervo PRIMEIRO.
    Aplica automaticamente os do acervo.
    """
    project = get_project(project_id)
    briefing = project["briefing"]
    screenplay = project.get("screenplay", "")
    
    # 1. LLM identifica personagens necessários
    identified = await llm_identify_characters(screenplay, briefing)
    # Retorna: ["Jonas", "Baleia", "Marinheiros", "Rei de Nínive"]
    
    # 2. Consulta acervo para cada um
    characters = []
    for char_name in identified:
        canonical = await search_character_library(
            char_name, 
            briefing, 
            tenant["id"]
        )
        
        if canonical:
            # ✅ APLICAR DO ACERVO (automático, sem aprovação)
            char = {
                **canonical,
                "source": "library",
                "is_historical": True,
                "auto_applied": True,
                "needs_approval": False
            }
            
            # Atualizar histórico de uso
            await update_character_usage(
                tenant["id"],
                canonical["canonical_id"],
                project_id,
                project["name"]
            )
            
            logger.info(f"🏛️ Applied historical character: {char_name}")
        else:
            # ✨ CRIAR NOVO (precisa aprovação)
            char = await llm_create_character(char_name, briefing, screenplay)
            char.update({
                "source": "new",
                "is_historical": False,
                "auto_applied": False,
                "needs_approval": True,
                "canonical_id": generate_canonical_id(char_name)
            })
            
            logger.info(f"✨ Created new character: {char_name}")
        
        characters.append(char)
    
    # 3. Salvar no projeto
    _update_project_field(tenant["id"], project_id, {
        "characters": characters,
        "characters_status": "awaiting_new_approval"
    })
    
    return {
        "characters": characters,
        "historical": len([c for c in characters if c["is_historical"]]),
        "new": len([c for c in characters if not c["is_historical"]]),
        "auto_applied": len([c for c in characters if c.get("auto_applied")])
    }


@router.post("/projects/{project_id}/characters/approve-new")
async def approve_new_characters(project_id, payload, tenant):
    """
    Aprova APENAS personagens novos e os adiciona ao acervo.
    Personagens históricos já foram aplicados automaticamente.
    """
    project = get_project(project_id)
    characters = project["characters"]
    
    # Filtrar apenas personagens novos
    new_chars = [c for c in characters if not c.get("is_historical")]
    
    # Adicionar aprovados ao acervo
    for char in new_chars:
        if char["canonical_id"] in payload["approved_ids"]:
            await add_to_character_library(tenant["id"], char)
            logger.info(f"📚 Added to library: {char['name']}")
    
    # Atualizar status
    _update_project_field(tenant["id"], project_id, {
        "characters_approved": True,
        "pipeline_status": "running"
    })
    
    # Iniciar pipeline autônomo
    background_tasks.add_task(run_autonomous_pipeline, tenant["id"], project_id)
    
    return {"status": "approved", "pipeline_started": True}
```

---

## ✅ **Resumo das Mudanças**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Criação** | Todos os personagens criados do zero | Consulta acervo primeiro |
| **Aprovação** | Usuário aprova todos | Aprova APENAS novos |
| **Históricos** | Recriados a cada filme | Aplicados automaticamente |
| **Consistência** | ❌ Variações entre filmes | ✅ Idênticos entre filmes |
| **Marcação** | Sem distinção | 🏛️ vs ✨ |
| **Economia** | ❌ Tokens desperdiçados | ✅ Reutilização eficiente |

---

## 🚀 **Próximos Passos de Implementação**

1. ✅ Backend: Collection `character_library`
2. ✅ Backend: Busca inteligente com LLM
3. ✅ Backend: Auto-aplicação de históricos
4. ✅ Frontend: Marcação visual 🏛️ vs ✨
5. ✅ Frontend: Modal "Ver Histórico de Uso"
6. ✅ Integração: Pipeline autônomo após aprovação

---

**Implementação completa em ~90 minutos** 🎬
