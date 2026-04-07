# 🎬 PLANEJAMENTO COMPLETO DO PIPELINE - StudioX

## 📊 VISÃO GERAL

Transformar o pipeline atual em um sistema inteligente que:
1. **Reutiliza personagens** existentes prioritariamente
2. **Especializa conteúdo** por faixa etária (ex: 2-5 anos)
3. **Gera múltiplos formatos**: narrado, dialogado, musical
4. **Transparência visual** do processo

---

## ✅ STATUS ATUAL (O que JÁ temos)

### Backend:
- ✅ Pipeline básico funcionando (Redator, Personagens, Diálogos, etc)
- ✅ Sistema de pastas de personagens (Avatar Folders)
- ✅ Integração ElevenLabs Music (backend completo)
- ✅ Galeria de avatares organizada
- ✅ Master Projects/Companies configurados

### Frontend:
- ✅ Interface de pipeline visual
- ✅ Galeria de avatares com pastas
- ✅ DirectedStudio completo
- ✅ NewProjectModal com Company selection

### Integrações:
- ✅ Claude Sonnet 4 (Redator & Pesquisador)
- ✅ Gemini Vision (análise de imagens)
- ✅ ElevenLabs TTS (vozes)
- ✅ ElevenLabs Music (músicas)
- ✅ Sora 2 (vídeos)

---

## 🎯 ARQUITETURA PLANEJADA

```
┌─────────────────────────────────────────────────────┐
│  PROJETO (Company: Biblizoo Baby)                   │
│  ─────────────────────────────────────────────────│
│  • target_audience: 2-5 anos                        │
│  • character_library: 27 personagens disponíveis    │
│  • content_advisors: Toddler + Musical ativados    │
└─────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  PIPELINE PRINCIPAL (genérico, não muda)            │
│  ─────────────────────────────────────────────────│
│                                                     │
│  1. Redator & Pesquisador                          │
│     + Consulta character_library                    │
│     + Usa personagens existentes prioritariamente   │
│     ↓                                               │
│  2. [OPCIONAL] Content Advisors                     │
│     • Toddler Content Advisor (2-5 anos)           │
│     • Musical Composer Advisor                      │
│     • Narration Style Advisor                       │
│     ↓                                               │
│  3. Personagens                                     │
│     + Cria apenas extras se necessário              │
│     + Atualiza character_library                    │
│     ↓                                               │
│  4. Diálogos                                        │
│     ↓                                               │
│  5. Director's Preview                              │
│     ↓                                               │
│  6. Storyboard                                      │
│     ↓                                               │
│  7. Produção (Vídeos)                              │
│     ↓                                               │
│  8. [OPCIONAL] Music Generation                     │
│     + Se Musical Advisor ativo                      │
│     + Gera MP3 completo                            │
└─────────────────────────────────────────────────────┘
```

---

## 📋 ROADMAP COMPLETO

### 🔴 FASE 1: CHARACTER LIBRARY SYSTEM (Prioridade Máxima)
**Objetivo**: Redator consulta personagens existentes ANTES de criar história

#### Task 1.1: Backend - Character Library Schema
**Arquivo**: Schema do projeto no Supabase
- [ ] Adicionar campo `character_library` no projeto:
  ```json
  {
    "folder_id": "uuid",
    "folder_name": "Biblizoo Baby",
    "last_synced": "timestamp",
    "total_characters": 27,
    "characters": [
      {
        "id": "uuid",
        "name": "Abraão",
        "animal": "Dromedário ancião",
        "traits": "Barba branca, keffiyeh turquesa...",
        "personality": "Sábio e nobre",
        "category": "principal"
      }
    ]
  }
  ```
**Estimativa**: 1-2 horas
**Arquivos**: Schema Supabase + backend model

---

#### Task 1.2: Backend - Sync Characters Endpoint
**Arquivo**: `/app/backend/routers/projects.py`
- [ ] Criar endpoint `POST /api/studio/projects/{project_id}/sync-characters`
- [ ] Buscar avatares da pasta associada ao projeto
- [ ] Processar e simplificar dados dos avatares
- [ ] Salvar em `project.character_library`
- [ ] Retornar lista de personagens

**Estimativa**: 2-3 horas
**Código exemplo**:
```python
@router.post("/{project_id}/sync-characters")
async def sync_characters(project_id: str, tenant = Depends(get_tenant)):
    # 1. Buscar projeto
    project = await get_project(project_id)
    
    # 2. Buscar folder_id do company/master project
    company = await get_company(project.company_id)
    folder_id = company.character_folder_id
    
    # 3. Buscar avatares da pasta
    avatars = await get_avatars_by_folder(folder_id)
    
    # 4. Processar e simplificar
    characters = [
        {
            "id": avatar.id,
            "name": extract_name(avatar.name),
            "animal": extract_animal(avatar.prompt),
            "traits": extract_traits(avatar.prompt),
            "personality": extract_personality(avatar.prompt)
        }
        for avatar in avatars
    ]
    
    # 5. Salvar no projeto
    project.character_library = {
        "folder_id": folder_id,
        "last_synced": datetime.now(),
        "characters": characters
    }
    
    return {"status": "ok", "total": len(characters)}
```

---

#### Task 1.3: Frontend - Sync Characters Button
**Arquivo**: `/app/frontend/src/pages/StudioPage.jsx`
- [ ] Adicionar botão "Carregar Personagens" no projeto
- [ ] Chamada ao endpoint `/sync-characters`
- [ ] Exibir lista de personagens carregados
- [ ] Badge mostrando "27 personagens disponíveis"

**Estimativa**: 2 horas
**UI proposta**:
```jsx
<div className="character-library-status">
  {project.character_library ? (
    <>
      <span>✅ {project.character_library.total_characters} personagens carregados</span>
      <button onClick={handleSyncCharacters}>🔄 Atualizar</button>
    </>
  ) : (
    <button onClick={handleSyncCharacters}>📚 Carregar Personagens</button>
  )}
</div>
```

---

#### Task 1.4: Backend - Modificar Redator & Pesquisador
**Arquivo**: `/app/backend/pipeline/agents/writer.py` (ou equivalente)
- [ ] Modificar prompt do Redator para incluir character_library
- [ ] Passar lista de personagens disponíveis
- [ ] Instruções claras: "USE PRIORITARIAMENTE esses personagens"
- [ ] Indicar quando criar novos: "NOVO PERSONAGEM: [nome]"

**Estimativa**: 3-4 horas
**Prompt exemplo**:
```python
def build_writer_prompt(user_input: str, character_library: dict):
    characters = character_library.get("characters", [])
    
    prompt = f"""
Você é um roteirista especializado em histórias bíblicas para crianças.

PERSONAGENS PRÉ-CRIADOS DISPONÍVEIS ({len(characters)} personagens):

PERSONAGENS PRINCIPAIS:
"""
    
    for char in characters:
        if char.get("category") == "principal":
            prompt += f"- {char['name']} ({char['animal']}): {char['traits']}\n"
    
    prompt += f"""

REGRAS IMPORTANTES:
1. USE PRIORITARIAMENTE os personagens listados acima
2. Crie novos personagens APENAS se absolutamente necessário para a história
3. Quando criar novo personagem, indique claramente: "NOVO PERSONAGEM: [nome] - [descrição]"
4. Mantenha consistência com as características dos personagens existentes

HISTÓRIA SOLICITADA:
{user_input}

Crie a história completa:
"""
    
    return prompt
```

---

#### Task 1.5: Sistema de Notificação de Mudanças
**Arquivo**: `/app/backend/routers/data.py`
- [ ] Quando avatar é adicionado/editado/deletado
- [ ] Verificar se pertence a alguma pasta de projeto ativo
- [ ] Trigger automático de `sync-characters`
- [ ] Notificar frontend via websocket (opcional)

**Estimativa**: 2-3 horas

---

### 🟡 FASE 2: CONTENT ADVISORS SYSTEM (Especialização) ✅ BACKEND COMPLETO

**Objetivo**: Adaptar conteúdo para faixa etária específica

**STATUS**: ✅ Backend 100% implementado | ⏸ Frontend pendente

#### Task 2.1: Backend - Content Advisors Schema ✅
**Arquivo**: Schema do projeto
- [x] Adicionar campo `content_advisors` no projeto
- [x] Sistema de configuração modular

**Status**: COMPLETO

---

#### Task 2.2: Backend - Toddler Content Advisor ✅
**Arquivo**: `/app/backend/services/content_advisors.py`
- [x] Criar agente especialista em conteúdo 2-5 anos
- [x] Recebe texto do Redator
- [x] Simplifica linguagem
- [x] Adiciona repetições ("Quem é forte? O leão é forte!")
- [x] Reduz vocabulário (200-500 palavras)
- [x] Retorna texto adaptado

**Status**: COMPLETO

---

#### Task 2.3: Backend - Musical Composer Advisor ✅
**Arquivo**: `/app/backend/services/content_advisors.py`
- [x] Criar agente compositor
- [x] Recebe roteiro
- [x] Transforma em estrutura musical
- [x] Cria letra (verso, refrão, ponte)
- [x] Define estilo ("children's music, upbeat, xylophone")
- [x] Retorna letra + prompt para ElevenLabs Music

**Status**: COMPLETO

---

#### Task 2.4: Backend - Narration Style Advisor ✅
**Arquivo**: `/app/backend/services/content_advisors.py`
- [x] Adiciona marcações de entonação
- [x] Define pausas dramáticas
- [x] Guia para síntese de voz
- [x] Tom (entusiasmado, calmo, misterioso)

**Status**: COMPLETO

---

#### Task 2.5: Backend - Advisor Chain System ✅
**Arquivo**: `/app/backend/services/advisor_chain.py`
- [x] Sistema que executa advisors em sequência
- [x] Configurável por projeto
- [x] Pipeline: Redator → Toddler → Musical → Narration
- [x] Salva cada versão (original, adaptada, musical)

**Status**: COMPLETO

**Implementação**:
```python
class AdvisorChain:
    """Executa múltiplos advisors em sequência"""
    
    async def process(self, content: str, project_config: dict) -> dict:
        results = {"original": content}
        current_content = content
        
        for advisor in self.advisors:
            if advisor.is_enabled(project_config):
                current_content = await advisor.refine(current_content, project_config)
                results[advisor.name] = current_content
        
        return results
```

**API Endpoints criados**:
- `POST /api/studio/projects/{project_id}/content-advisors` - Configurar advisors
- `GET /api/studio/projects/{project_id}/content-advisors` - Obter configuração

**Integração no Screenwriter**: ✅ Completa
- Detecta advisors habilitados após geração do roteiro
- Aplica transformações automaticamente
- Salva resultados em `project.agents_output.content_advisors`

**Documentação**: `/app/CONTENT_ADVISORS_INTEGRATION.md`

---

#### Task 2.6: Frontend - Content Type Selector ⏸
**Arquivo**: `/app/frontend/src/components/ContentTypeSelectorModal.jsx`
- [ ] Modal para escolher tipo de conteúdo ao iniciar Redator
- [ ] Opções:
  - História narrada + diálogos (padrão)
  - História 100% narrada (com entonação)
  - Música infantil (chiclete)
- [ ] Salva em `project.content_advisors`

**Status**: PENDENTE
**UI proposta**:
```jsx
<div className="content-type-selector">
  <h3>Que tipo de conteúdo você quer criar?</h3>
  
  <div className="option">
    <input type="radio" id="narrated-dialog" name="content-type" />
    <label>
      <h4>📖 História Narrada + Diálogos</h4>
      <p>Narrador conta a história + personagens conversam</p>
      <span>Ideal para: Engajamento e aprendizado</span>
    </label>
  </div>
  
  <div className="option">
    <input type="radio" id="full-narration" name="content-type" />
    <label>
      <h4>🎙️ História 100% Narrada</h4>
      <p>Apenas narrador com muita entonação dramática</p>
      <span>Ideal para: Hora de dormir, relaxamento</span>
    </label>
  </div>
  
  <div className="option">
    <input type="radio" id="musical" name="content-type" />
    <label>
      <h4>🎵 Música Infantil (Chiclete)</h4>
      <p>História transformada em música cativante</p>
      <span>Ideal para: Memorização, diversão</span>
    </label>
  </div>
  
  <button>Começar</button>
</div>
```

---

### 🟢 FASE 3: PIPELINE VISUAL INTERNO
**Objetivo**: Mostrar progresso das etapas em tempo real

#### Task 3.1: Backend - Progress Streaming
**Arquivo**: `/app/backend/pipeline/routes.py`
- [ ] Implementar Server-Sent Events (SSE)
- [ ] Emitir eventos a cada etapa:
  - `character_discovery_start`
  - `character_discovery_complete`
  - `story_creation_start`
  - `story_creation_complete`
  - `advisor_processing_start`
  - `advisor_processing_complete`
  - `music_generation_start`
  - `music_generation_complete`

**Estimativa**: 4-5 horas
**Código exemplo**:
```python
from fastapi.responses import StreamingResponse
import asyncio
import json

@router.post("/{project_id}/generate-story-stream")
async def generate_story_stream(project_id: str):
    async def event_generator():
        # 1. Character Discovery
        yield f"data: {json.dumps({'step': 'character_discovery', 'status': 'start'})}\n\n"
        characters = await load_character_library(project_id)
        yield f"data: {json.dumps({'step': 'character_discovery', 'status': 'complete', 'count': len(characters)})}\n\n"
        
        # 2. Story Creation
        yield f"data: {json.dumps({'step': 'story_creation', 'status': 'start'})}\n\n"
        story = await generate_story_with_characters(characters)
        yield f"data: {json.dumps({'step': 'story_creation', 'status': 'complete', 'length': len(story)})}\n\n"
        
        # 3. Advisor Processing
        if project.content_advisors.toddler_content.enabled:
            yield f"data: {json.dumps({'step': 'toddler_adaptation', 'status': 'start'})}\n\n"
            story = await toddler_advisor.refine(story)
            yield f"data: {json.dumps({'step': 'toddler_adaptation', 'status': 'complete'})}\n\n"
        
        # Final
        yield f"data: {json.dumps({'step': 'complete', 'story': story})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

#### Task 3.2: Frontend - PipelineProgressTracker Component
**Arquivo**: `/app/frontend/src/components/PipelineProgressTracker.jsx`
- [ ] Componente que escuta SSE
- [ ] Mostra cada etapa com status
- [ ] Animações suaves
- [ ] Progress bar
- [ ] Contador de tempo

**Estimativa**: 5-6 horas
**Código exemplo**:
```jsx
const PipelineProgressTracker = ({ projectId, onComplete }) => {
  const [steps, setSteps] = useState([
    { id: 'character_discovery', name: 'Carregando personagens', status: 'pending' },
    { id: 'story_creation', name: 'Criando história', status: 'pending' },
    { id: 'toddler_adaptation', name: 'Adaptando para 2-5 anos', status: 'pending' },
    { id: 'complete', name: 'Finalizado', status: 'pending' }
  ]);

  useEffect(() => {
    const eventSource = new EventSource(`/api/pipeline/${projectId}/generate-story-stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      setSteps(prev => prev.map(step => 
        step.id === data.step 
          ? { ...step, status: data.status, ...data }
          : step
      ));
      
      if (data.step === 'complete') {
        onComplete(data.story);
        eventSource.close();
      }
    };
    
    return () => eventSource.close();
  }, [projectId]);

  return (
    <div className="pipeline-progress">
      {steps.map(step => (
        <div key={step.id} className={`step step-${step.status}`}>
          <div className="step-icon">
            {step.status === 'pending' && '⏸'}
            {step.status === 'start' && '🔄'}
            {step.status === 'complete' && '✅'}
          </div>
          <div className="step-content">
            <h4>{step.name}</h4>
            {step.count && <p>{step.count} personagens encontrados</p>}
            {step.status === 'start' && <Spinner />}
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

### 🔵 FASE 4: INTEGRAÇÃO MUSIC GENERATION
**Objetivo**: Integrar geração de música ao pipeline

#### Task 4.1: Backend - Music Generation Step
**Arquivo**: `/app/backend/pipeline/steps/music_generation.py`
- [ ] Após Musical Composer Advisor criar letra
- [ ] Automaticamente chamar ElevenLabs Music API
- [ ] Polling para aguardar conclusão
- [ ] Salvar MP3 URL no projeto
- [ ] Emitir eventos de progresso

**Estimativa**: 3-4 horas

---

#### Task 4.2: Frontend - Music Player Component
**Arquivo**: `/app/frontend/src/components/MusicPlayer.jsx`
- [ ] Player de áudio customizado
- [ ] Controles: play, pause, seek, volume
- [ ] Download button
- [ ] Visualização de forma de onda (opcional)

**Estimativa**: 4-5 horas

---

#### Task 4.3: Frontend - Music Generation Modal
**Arquivo**: `/app/frontend/src/components/MusicGenerationModal.jsx`
- [ ] Modal que mostra progresso da geração
- [ ] Progress bar (0-100%)
- [ ] Tempo estimado restante
- [ ] Preview da letra enquanto gera
- [ ] Player quando concluído

**Estimativa**: 3-4 horas

---

### 🟣 FASE 5: CONFIGURAÇÃO POR PROJETO/EMPRESA
**Objetivo**: Cada empresa tem suas configurações default

#### Task 5.1: Backend - Company Configuration Schema
**Arquivo**: Schema da empresa (Supabase)
- [ ] Adicionar campos de configuração default:
  ```json
  {
    "company_id": "biblizoo-baby",
    "name": "Biblizoo Baby",
    "character_folder_id": "uuid",
    "default_config": {
      "target_audience": {
        "age_range": "2-5",
        "characteristics": "Pré-escolar, atenção curta"
      },
      "content_advisors": {
        "toddler_content": { "enabled": true },
        "musical_composer": { "enabled": true },
        "narration_style": { "enabled": true }
      }
    }
  }
  ```

**Estimativa**: 2 horas

---

#### Task 5.2: Frontend - Company Settings Page
**Arquivo**: `/app/frontend/src/pages/CompanySettingsPage.jsx`
- [ ] Página de configurações da empresa
- [ ] Editar target audience
- [ ] Ativar/desativar advisors
- [ ] Escolher pasta de personagens padrão
- [ ] Preview de como afeta novos projetos

**Estimativa**: 5-6 horas

---

#### Task 5.3: Backend - Auto-apply Company Config
**Arquivo**: `/app/backend/routers/projects.py`
- [ ] Ao criar novo projeto
- [ ] Herdar configurações da empresa
- [ ] Auto-sync character library
- [ ] Aplicar advisors default

**Estimativa**: 2-3 horas

---

## 📊 RESUMO DE ESTIMATIVAS

| Fase | Tarefas | Tempo Estimado | Prioridade |
|------|---------|----------------|------------|
| **Fase 1: Character Library** | 5 tarefas | 10-14 horas | 🔴 Máxima |
| **Fase 2: Content Advisors** | 6 tarefas | 18-23 horas | 🟡 Alta |
| **Fase 3: Pipeline Visual** | 2 tarefas | 9-11 horas | 🟢 Média |
| **Fase 4: Music Integration** | 3 tarefas | 10-13 horas | 🔵 Média |
| **Fase 5: Company Config** | 3 tarefas | 9-11 horas | 🟣 Baixa |
| **TOTAL** | **19 tarefas** | **56-72 horas** | (~7-9 dias) |

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

### Sprint 1 (2-3 dias): Character Library ✅
1. Task 1.1: Schema
2. Task 1.2: Backend sync endpoint
3. Task 1.3: Frontend button
4. Task 1.4: Modificar Redator prompt
5. Task 1.5: Notificações

**Resultado**: Redator usa personagens existentes

---

### Sprint 2 (3-4 dias): Content Advisors 🎭
1. Task 2.1: Schema
2. Task 2.2: Toddler Advisor
3. Task 2.3: Musical Composer
4. Task 2.4: Narration Advisor
5. Task 2.5: Advisor Chain
6. Task 2.6: Frontend selector

**Resultado**: Conteúdo especializado por idade

---

### Sprint 3 (2 dias): Pipeline Visual 📊
1. Task 3.1: SSE backend
2. Task 3.2: Frontend progress tracker

**Resultado**: Transparência do processo

---

### Sprint 4 (2 dias): Music Integration 🎵
1. Task 4.1: Backend integration
2. Task 4.2: Music player
3. Task 4.3: Generation modal

**Resultado**: Músicas geradas automaticamente

---

### Sprint 5 (1-2 dias): Company Config ⚙️
1. Task 5.1: Schema
2. Task 5.2: Settings page
3. Task 5.3: Auto-apply

**Resultado**: Configuração centralizada

---

## 🧪 TESTES NECESSÁRIOS

### Por Fase:
- [ ] **Fase 1**: Testar com 3 projetos diferentes, verificar personagens carregados
- [ ] **Fase 2**: Criar história genérica vs adaptada (2-5 anos) vs musical
- [ ] **Fase 3**: Verificar eventos SSE em tempo real
- [ ] **Fase 4**: Gerar música completa end-to-end
- [ ] **Fase 5**: Criar empresa nova com config e verificar herança

### Testes de Integração:
- [ ] História para 2-5 anos usando personagens existentes
- [ ] Música infantil gerada do zero até MP3
- [ ] Pipeline visual completo sem erros
- [ ] Multiple projets com configs diferentes

---

## 📝 NOTAS IMPORTANTES

### Decisões Arquiteturais:
1. **Modular**: Cada advisor é independente
2. **Opt-in**: Advisors são opcionais, não quebram conteúdo genérico
3. **Escalável**: Fácil adicionar novos advisors (adolescentes, adultos)
4. **Performance**: Character library em memória (não busca toda vez)

### Pontos de Atenção:
1. **Custos**: ElevenLabs Music (~$0.90 por música)
2. **Tempo**: Geração de música leva 1-2 minutos
3. **LLM Tokens**: Advisors aumentam uso de tokens
4. **Cache**: Implementar cache de character library

### Melhorias Futuras:
- [ ] Multiple music styles (rock, jazz, classical)
- [ ] Voice cloning para personagens
- [ ] A/B testing de advisors
- [ ] Analytics de qual tipo de conteúdo funciona melhor
- [ ] Export para outras plataformas (YouTube Kids, Spotify)

---

## 🚀 PRONTO PARA COMEÇAR?

**Próximo Passo**: Implementar **Fase 1 - Character Library System**

Começamos? 🎯
