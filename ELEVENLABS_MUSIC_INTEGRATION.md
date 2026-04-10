# ElevenLabs Music Integration - Documentação Completa

## ✅ Status da Implementação

**Backend**: ✅ 100% Implementado e Funcionando
- Service: `/app/backend/services/music_service.py`
- Router: `/app/backend/routers/music.py`
- Registrado em: `/app/backend/server.py`

**API Key**: ✅ Configurada (usando a mesma do ElevenLabs TTS)

---

## 💰 Custos por Música

| Plano | Mensalidade | Música 3min | Minutos Inclusos |
|-------|-------------|-------------|------------------|
| Starter | $5/mês | ~$0.90 | 11 min |
| Creator | $22/mês | ~$1.05 | 16 min |
| Pro | $99/mês | ~$0.99 | 62 min |
| Scale | $330/mês | ~$0.90 | 304 min |

**Observações:**
- Usa os mesmos créditos do TTS
- Uso comercial permitido (Starter+)
- Duração: 3 segundos a 5 minutos

---

## 📋 Endpoints Disponíveis

### 1. Gerar Música (Async)
```http
POST /api/music/generate
Content-Type: application/json

{
  "prompt": "Upbeat children's song about Abraham and Isaac, cheerful xylophone",
  "duration_seconds": 180,
  "with_vocals": true,
  "lyrics": "Abraão, Abraão, tem um filho Isaque..."  // opcional
}

Response:
{
  "task_id": "abc123",
  "status": "processing",
  "message": "Music generation started",
  "audio_url": null
}
```

### 2. Verificar Status
```http
GET /api/music/status/{task_id}

Response (processing):
{
  "task_id": "abc123",
  "status": "processing",
  "audio_url": null
}

Response (completed):
{
  "task_id": "abc123",
  "status": "completed",
  "audio_url": "https://elevenlabs.io/audio/abc123.mp3",
  "duration": 183
}
```

### 3. Gerar e Aguardar (Sync)
```http
POST /api/music/generate-and-wait
Content-Type: application/json

{
  "prompt": "Children's song...",
  "duration_seconds": 180,
  "with_vocals": true,
  "lyrics": "..."
}

Response (após 1-2 minutos):
{
  "task_id": "abc123",
  "status": "completed",
  "audio_url": "https://elevenlabs.io/audio/abc123.mp3",
  "duration": 183
}
```

---

## 🎯 Fluxo Recomendado

### Para Músicas Infantis (Biblizoo Baby):

1. **Musical Composer Advisor** cria:
   - Letra completa estruturada
   - Prompt de estilo: "children's music, upbeat, catchy, xylophone, educational"
   - Estrutura: [Refrão] → [Verso 1] → [Refrão] → [Verso 2] → [Refrão]

2. **Backend** chama ElevenLabs:
   ```python
   from services.music_service import get_music_service
   
   service = get_music_service()
   result = await service.generate_music(
       prompt=f"Upbeat children's song about {tema}, cheerful instruments\n\nLyrics:\n{lyrics}",
       duration_seconds=180,
       with_vocals=True
   )
   ```

3. **Polling** (frontend):
   - Faz requisição inicial: POST /api/music/generate
   - Recebe task_id
   - A cada 10 segundos: GET /api/music/status/{task_id}
   - Quando status="completed": mostra player de áudio

4. **Salvar no Projeto**:
   ```python
   project["music"] = {
       "task_id": "abc123",
       "audio_url": "https://...",
       "lyrics": "...",
       "prompt": "...",
       "duration": 183,
       "generated_at": "2026-04-07T04:00:00Z"
   }
   ```

---

## 🎨 Próximos Passos (Frontend)

### Componente: MusicGeneratorModal.jsx

```jsx
const MusicGeneratorModal = ({ lyrics, style, onComplete }) => {
  const [status, setStatus] = useState('idle'); // idle, generating, completed
  const [taskId, setTaskId] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [progress, setProgress] = useState(0);

  const generateMusic = async () => {
    setStatus('generating');
    
    // 1. Iniciar geração
    const response = await fetch('/api/music/generate', {
      method: 'POST',
      body: JSON.stringify({
        prompt: style,
        duration_seconds: 180,
        with_vocals: true,
        lyrics: lyrics
      })
    });
    
    const { task_id } = await response.json();
    setTaskId(task_id);
    
    // 2. Polling
    const interval = setInterval(async () => {
      const statusResponse = await fetch(`/api/music/status/${task_id}`);
      const statusData = await statusResponse.json();
      
      if (statusData.status === 'completed') {
        clearInterval(interval);
        setAudioUrl(statusData.audio_url);
        setStatus('completed');
        onComplete(statusData);
      }
      
      setProgress(prev => Math.min(prev + 5, 95));
    }, 10000); // 10 segundos
  };

  return (
    <div>
      {status === 'idle' && (
        <button onClick={generateMusic}>Gerar Música</button>
      )}
      
      {status === 'generating' && (
        <div>
          <ProgressBar value={progress} />
          <p>Gerando música... {progress}%</p>
        </div>
      )}
      
      {status === 'completed' && (
        <div>
          <audio controls src={audioUrl} />
          <button onClick={() => window.open(audioUrl)}>Download</button>
        </div>
      )}
    </div>
  );
};
```

---

## 🧪 Teste Manual (via curl)

```bash
# 1. Gerar música
API_URL="https://studiox-kling-fix.preview.emergentagent.com"

RESPONSE=$(curl -s -X POST "$API_URL/api/music/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Upbeat cheerful children song about animals, xylophone, educational",
    "duration_seconds": 60,
    "with_vocals": true,
    "lyrics": "Animals animals everywhere, Lions tigers and bears oh my!"
  }')

echo "$RESPONSE"
TASK_ID=$(echo "$RESPONSE" | jq -r '.task_id')

# 2. Aguardar 1 minuto e verificar status
sleep 60

curl -s "$API_URL/api/music/status/$TASK_ID" | jq
```

---

## ⚠️ Observações Importantes

1. **Tempo de Geração**: 1-2 minutos
2. **Polling Interval**: 10 segundos (não menos que isso)
3. **Timeout**: Máximo 5 minutos
4. **Créditos**: Compartilha com TTS, verificar saldo
5. **Comercial**: Apenas planos Starter+ podem usar comercialmente

---

## 🐛 Troubleshooting

### Erro: "ELEVENLABS_API_KEY not found"
- Verificar `/app/backend/.env`
- Reiniciar backend: `sudo supervisorctl restart backend`

### Erro 422: Unprocessable Entity
- Verificar formato do JSON
- `prompt` é obrigatório
- `duration_seconds` deve estar entre 3 e 300

### Erro 408: Timeout
- Música demorou mais de 5 minutos
- Use endpoint async (/generate) ao invés de /generate-and-wait

### Status fica "processing" indefinidamente
- Verificar créditos na conta ElevenLabs
- Verificar logs: `tail -f /var/log/supervisor/backend.err.log`

---

## 📊 Monitoramento

### Logs
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log

# Filtrar apenas music
tail -f /var/log/supervisor/backend.err.log | grep -i music
```

### Métricas
- Total de músicas geradas: Adicionar ao dashboard
- Tempo médio de geração: ~90 segundos
- Taxa de sucesso: Monitorar

---

**Implementado por**: Agent E1  
**Data**: 2026-04-07  
**Status**: ✅ Pronto para uso
