# 📊 Pipeline Visual Tracker - Documentação

## 🎯 **O que é?**

Um **timeline visual em tempo real** que mostra todos os agentes trabalhando na produção do vídeo, exibindo:

- 📝 Qual agente está ativo no momento
- ⏱️ Progresso de cada agente (%)
- 🕐 Tempo decorrido e estimado restante
- ✅ Status: Aguardando, Processando, Concluído, Erro

---

## 🎨 **Design Implementado**

### **Versão 1: Inline (na área de chat)**

Quando o usuário está gerando roteiro, aparece um painel simplificado mostrando:

```
┌─────────────────────────────────────┐
│ ✨ Pipeline de Produção              │
├─────────────────────────────────────┤
│ [📝] Redator & Pesquisador  [⟳]     │  ← Ativo (rodando)
│ [🎬] Diretor de Cena       [🕐]     │  ← Aguardando
└─────────────────────────────────────┘
```

### **Versão 2: Completa (componente standalone)**

Arquivo: `/app/frontend/src/components/pipeline/PipelineVisualTracker.jsx`

Mostra **TODOS** os agentes do pipeline:

```
┌──────────────────────────────────────────────────┐
│ 🪄 Pipeline de Produção           75% completo   │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░          │
│ 3 de 4 agentes concluídos                        │
├──────────────────────────────────────────────────┤
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ [📝] Redator & Pesquisador      [✓ Concluído] │ │
│ │ Criando roteiro e pesquisando personagens     │ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100%          │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ [✨] Toddler Content Advisor  [⟳ Processando] │ │
│ │ Simplificando vocabulário...                  │ │
│ │ 27s decorrido              ~18s restante     │ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░ 60%            │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ [🎵] Musical Composer         [🕐 Aguardando] │ │
│ │ Transformando história em música chiclete     │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ [🎬] Diretor de Cena          [🕐 Aguardando] │ │
│ │ Criando prompts visuais com Identity Cards    │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## 🤖 **Agentes Suportados**

| Agente | Nome | Cor | Tempo Estimado |
|--------|------|-----|----------------|
| 📝 | Redator & Pesquisador | Roxo `#8B5CF6` | 2 min |
| 👥 | Biblioteca de Personagens | Azul `#3B82F6` | 10s |
| ✨ | Toddler Content Advisor | Laranja `#F59E0B` | 45s |
| 🎵 | Musical Composer | Rosa `#EC4899` | 1 min |
| 🎨 | Narration Style Advisor | Verde `#10B981` | 30s |
| 🎬 | Diretor de Cena | Índigo `#6366F1` | 3 min |
| 🎵 | Geração de Música | Roxo `#8B5CF6` | 2 min |
| 🎥 | Geração de Vídeo | Vermelho `#DC2626` | 10 min |

---

## 📡 **Como Funciona** (Backend → Frontend)

### **1. Backend atualiza status**

Durante a geração do roteiro, o backend atualiza o status via:

```python
# Em /app/backend/routers/studio/screenwriter.py
project["pipeline_status"] = {
    "researcher_screenwriter": {
        "status": "processing",
        "progress": 60,
        "elapsedTime": 72,
        "message": "Criando diálogos..."
    },
    "toddler_advisor": {
        "status": "waiting",
        "progress": 0,
        "elapsedTime": 0
    },
    ...
}
```

### **2. Frontend busca status**

Frontend faz polling a cada 2 segundos:

```javascript
useEffect(() => {
  const interval = setInterval(async () => {
    const res = await axios.get(`${API}/studio/projects/${projectId}`);
    setPipelineStatus(res.data.pipeline_status || {});
  }, 2000);
  return () => clearInterval(interval);
}, [projectId]);
```

### **3. Componente renderiza**

```jsx
<PipelineVisualTracker
  pipelineStatus={pipelineStatus}
  enabledAdvisors={['toddler_content', 'musical_composer']}
  currentAgent="researcher_screenwriter"
/>
```

---

## 🎨 **Estados Visuais**

### **Aguardando** `waiting`
```
┌────────────────────────────────┐
│ [🕐] Agente Name  [Aguardando] │
│ Descrição do agente            │
└────────────────────────────────┘
```
- Cor: Cinza `#6B7280`
- Sem barra de progresso
- Ícone: Relógio estático

### **Processando** `processing`
```
┌────────────────────────────────┐
│ [⟳] Agente Name  [Processando] │
│ Mensagem dinâmica...           │
│ 45s decorrido    ~30s restante │
│ ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░ 60%      │
└────────────────────────────────┘
```
- Cor: Roxo `#8B5CF6`
- Barra de progresso animada
- Ícone: Spinner girando
- Efeito shimmer no fundo

### **Concluído** `completed`
```
┌────────────────────────────────┐
│ [✓] Agente Name   [Concluído]  │
│ Descrição do agente            │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100%      │
└────────────────────────────────┘
```
- Cor: Verde `#10B981`
- Barra 100% preenchida
- Ícone: Check verde

### **Erro** `error`
```
┌────────────────────────────────┐
│ [!] Agente Name      [Erro]    │
│ Mensagem de erro...            │
└────────────────────────────────┘
```
- Cor: Vermelho `#EF4444`
- Sem barra de progresso
- Ícone: Alerta

### **Desabilitado** `skipped`
```
┌────────────────────────────────┐
│ Agente Name    [Desabilitado]  │
│ (opacidade 50%)                │
└────────────────────────────────┘
```
- Cor: Cinza escuro `#374151`
- Sem ícone de status
- Opacidade reduzida

---

## 🔧 **Uso no Código**

### **Versão Inline (já integrada)**

Já está funcionando em `/app/frontend/src/components/DirectedStudio.jsx`:

```jsx
{chatLoading && (
  <PipelineVisualTrackerInline 
    lang={lang}
    currentAgent="researcher_screenwriter"
  />
)}
```

### **Versão Completa (para usar em modais/páginas)**

```jsx
import { PipelineVisualTracker } from './pipeline/PipelineVisualTracker';

function MyComponent() {
  const [pipelineStatus, setPipelineStatus] = useState({});
  const enabledAdvisors = ['toddler_content', 'musical_composer'];
  
  return (
    <PipelineVisualTracker
      pipelineStatus={pipelineStatus}
      enabledAdvisors={enabledAdvisors}
      currentAgent="researcher_screenwriter"
      projectConfig={{}}
    />
  );
}
```

---

## ⚙️ **Configuração de Tempo**

Tempos estimados para cada agente (em segundos):

```javascript
const AGENT_DEFINITIONS = [
  { id: 'researcher_screenwriter', estimatedTime: 120 },  // 2 min
  { id: 'character_library', estimatedTime: 10 },         // 10s
  { id: 'toddler_advisor', estimatedTime: 45 },           // 45s
  { id: 'musical_advisor', estimatedTime: 60 },           // 1 min
  { id: 'narration_advisor', estimatedTime: 30 },         // 30s
  { id: 'director', estimatedTime: 180 },                 // 3 min
  { id: 'music_generation', estimatedTime: 120 },         // 2 min
  { id: 'video_generation', estimatedTime: 600 },         // 10 min
];
```

---

## 🎯 **Próximos Passos (Fase 3 Completa)**

### **Pendente para Fase 3:**

1. **Backend - Server-Sent Events (SSE)**
   - Streaming de updates em tempo real
   - Endpoint: `GET /api/studio/projects/{id}/pipeline-stream`
   - Elimina polling a cada 2s

2. **Frontend - EventSource**
   ```javascript
   const eventSource = new EventSource(
     `${API}/studio/projects/${projectId}/pipeline-stream`
   );
   eventSource.onmessage = (event) => {
     const data = JSON.parse(event.data);
     setPipelineStatus(data.pipeline_status);
   };
   ```

3. **Mensagens Dinâmicas**
   - Backend envia mensagens específicas:
     - "Identificando personagens na pasta master..."
     - "Abraão detectado, usando avatar 001..."
     - "Simplificando vocabulário para 2-5 anos..."
     - "Criando refrão cativante..."

4. **Sub-etapas de Progresso**
   - Screenwriter:
     - [25%] Pesquisando personagens
     - [50%] Criando estrutura do roteiro
     - [75%] Escrevendo diálogos
     - [100%] Finalizando narração

---

## 📊 **Status Atual da Implementação**

| Feature | Status | Arquivo |
|---------|--------|---------|
| Componente completo | ✅ Pronto | `PipelineVisualTracker.jsx` |
| Versão inline | ✅ Integrada | `DirectedStudio.jsx` |
| Backend status updates | ⏸ Pendente | Precisa adicionar em `screenwriter.py` |
| SSE streaming | ⏸ Pendente | Fase 3 |
| Mensagens dinâmicas | ⏸ Pendente | Fase 3 |
| Testing | ⏸ Pendente | Testing agent |

---

## 🎉 **Resultado**

Quando implementado completamente, o usuário verá:

✅ **Visibilidade total** do pipeline em tempo real
✅ **Progresso detalhado** de cada agente (%)
✅ **Tempo restante** estimado
✅ **Mensagens descritivas** do que está acontecendo
✅ **Design moderno** com cores, ícones e animações
✅ **Adaptável** - mostra apenas agentes habilitados

**Tempo total de implementação**: ~2 horas (frontend completo)
**Pendente**: Backend SSE + mensagens dinâmicas (~1-2 horas)
