# 🎬 Video Stitching Architecture - StudioX

## Problema
Sora 2 API limita vídeos a **12 segundos máximo**, mas cenas podem ter 30s, 45s, 60s ou mais.

## Solução: Frame Stitching + Audio Continuity

---

## 📋 Arquitetura Completa

### FASE 1: Geração de Áudio Completo 🔊

**Objetivo:** Gerar TODO o áudio da cena ANTES de dividir em clips visuais.

```
Entrada:
- Scene data
- dialogue_timeline (array de beats com timing)
- character_voices (mapeamento personagem → ElevenLabs voice)
- background_music (opcional)

Processo:
1. Para cada beat no dialogue_timeline:
   - Gerar fala com ElevenLabs
   - Posicionar no timestamp correto (start → end)
   
2. Mixar camadas de áudio:
   - Layer 1: Diálogos (posicionados no timeline)
   - Layer 2: Música de fundo (fade in/out)
   - Layer 3: Efeitos sonoros (SFX)
   
3. Exportar áudio master (AAC 128kbps)

Saída:
- full_scene_audio.aac (duração total da cena)
- Metadados: duration, has_dialogue, has_music
```

**Código:**
```python
from core.video_stitching import AudioSynchronizer

audio_result = AudioSynchronizer.generate_full_scene_audio(
    scene=scene,
    dialogue_timeline=scene['dialogue_timeline'],
    character_voices=character_voice_mapping,
    background_music_path="/path/to/music.mp3"
)

# audio_result = {
#   'audio_path': '/tmp/scene_5_audio.aac',
#   'duration': 28.0,
#   'has_dialogue': True,
#   'has_music': True
# }
```

---

### FASE 2: Planejamento de Clips 📐

**Objetivo:** Dividir a cena em clips de ≤12s em pontos naturais.

```
Entrada:
- Scene data
- dialogue_timeline

Análise:
1. Calcular duração total da cena (do último beat)
2. Se ≤12s: não precisa dividir
3. Se >12s: encontrar pontos de corte naturais

Pontos de Corte Prioritários:
1. ✅ Pausas/silêncios explícitos: [pausa], [silêncio]
2. ✅ Gaps entre falas (≥0.5s)
3. ✅ Final de frases completas
4. ✅ Mudanças de personagem
5. ❌ EVITAR: meio de palavras/frases

Exemplo:
Cena 28s → Dividir em:
- Clip 0: 0.0s - 11.0s (pausa dramática)
- Clip 1: 11.0s - 21.0s (silêncio)
- Clip 2: 21.0s - 28.0s (fim da cena)
```

**Código:**
```python
from core.video_stitching import VideoStitchingPlanner

planner = VideoStitchingPlanner(scene, dialogue_timeline)

if planner.needs_splitting():
    clips = planner.create_clip_plan()
    
    # clips = [
    #   {
    #     'clip_index': 0,
    #     'start_time': 0.0,
    #     'end_time': 11.0,
    #     'duration': 11.0,
    #     'needs_frame_reference': False,
    #     'dialogue_beats': [beat1, beat2, beat3],
    #     'description': 'Jonas, Narrador (0.0s-11.0s)'
    #   },
    #   { ... clip 1 ... },
    #   { ... clip 2 ... }
    # ]
```

---

### FASE 3: Geração de Vídeo com Frame Stitching 🎥

**Objetivo:** Gerar clips visuais mantendo continuidade entre eles.

```
Para Clip 0 (primeiro):
1. Gerar prompt completo da cena
2. Chamar Sora 2 API:
   - duration: 11.0s
   - prompt: [descrição completa]
   - NO frame_reference (é o primeiro)
3. Salvar vídeo: clip_0.mp4
4. Extrair último frame: clip_0_last_frame.jpg

Para Clip 1 (segundo):
1. Usar prompt + continuidade
2. Chamar Sora 2 API:
   - duration: 10.0s
   - prompt: [continuação da ação]
   - frame_reference: clip_0_last_frame.jpg  ← CONTINUIDADE!
3. Salvar vídeo: clip_1.mp4
4. Extrair último frame: clip_1_last_frame.jpg

Para Clip 2 (terceiro):
1. Usar prompt + continuidade
2. Chamar Sora 2 API:
   - duration: 7.0s
   - prompt: [final da cena]
   - frame_reference: clip_1_last_frame.jpg  ← CONTINUIDADE!
3. Salvar vídeo: clip_2.mp4
```

**Resultado:** 3 clips de vídeo com transição visual suave!

**Código:**
```python
from core.video_stitching import FrameStitcher

# Após gerar cada clip de vídeo
last_frame = FrameStitcher.extract_last_frame(
    video_path="clip_0.mp4",
    output_path="/tmp/clip_0_last_frame.jpg"
)

# Usar last_frame como referência para próximo clip
next_clip = sora_api.generate_video(
    prompt=next_prompt,
    duration=10.0,
    frame_reference=last_frame  # ← Continuidade visual!
)
```

---

### FASE 4: Sincronização Áudio + Vídeo 🎵

**Objetivo:** Extrair segmentos de áudio e sincronizar com clips de vídeo.

```
Para cada clip de vídeo:
1. Extrair segmento correspondente do áudio master
2. Sincronizar áudio com vídeo
3. Exportar clip final com áudio

Exemplo:
- Clip 0 (0-11s):
  - Video: clip_0.mp4 (sem áudio)
  - Audio: full_scene_audio.aac[0:11s]
  - Output: clip_0_with_audio.mp4
  
- Clip 1 (11-21s):
  - Video: clip_1.mp4 (sem áudio)
  - Audio: full_scene_audio.aac[11:21s]
  - Output: clip_1_with_audio.mp4
  
- Clip 2 (21-28s):
  - Video: clip_2.mp4 (sem áudio)
  - Audio: full_scene_audio.aac[21:28s]
  - Output: clip_2_with_audio.mp4
```

**Código:**
```python
from core.video_stitching import AudioSynchronizer

# Para cada clip
clip_audio = AudioSynchronizer.extract_clip_audio(
    full_audio_path="full_scene_audio.aac",
    start_time=clip['start_time'],
    end_time=clip['end_time'],
    output_path=f"/tmp/clip_{i}_audio.aac"
)

# Sincronizar com FFmpeg
ffmpeg -i clip_0.mp4 -i clip_0_audio.aac -c:v copy -c:a aac -shortest clip_0_with_audio.mp4
```

---

### FASE 5: Merge Final 🎬

**Objetivo:** Concatenar todos os clips em um vídeo único.

```
Entrada:
- clip_0_with_audio.mp4
- clip_1_with_audio.mp4
- clip_2_with_audio.mp4

Processo:
1. Criar arquivo concat.txt:
   file 'clip_0_with_audio.mp4'
   file 'clip_1_with_audio.mp4'
   file 'clip_2_with_audio.mp4'

2. FFmpeg concat demuxer:
   ffmpeg -f concat -safe 0 -i concat.txt -c copy final_scene.mp4

Saída:
- final_scene.mp4 (28s)
  - Continuidade visual ✅
  - Áudio sincronizado ✅
  - Música de fundo contínua ✅
  - Transições suaves ✅
```

**Código:**
```python
from core.video_stitching import FrameStitcher

final_video = FrameStitcher.merge_clips_with_audio(
    video_clips=["clip_0.mp4", "clip_1.mp4", "clip_2.mp4"],
    audio_clips=["clip_0_audio.aac", "clip_1_audio.aac", "clip_2_audio.aac"],
    output_path="/final/scene_5_complete.mp4"
)
```

---

## 🎯 Vantagens da Solução

### ✅ Continuidade Visual
- Frame stitching garante transição suave entre clips
- Sora 2 mantém personagens, cenário e lighting consistentes
- Sem cortes abruptos

### ✅ Continuidade de Áudio
- Áudio gerado UMA VEZ para toda a cena
- Música de fundo flui naturalmente
- Falas sincronizadas perfeitamente
- Sem "pulos" ou interrupções

### ✅ Pontos de Corte Inteligentes
- Corta em pausas naturais do diálogo
- Respeita estrutura narrativa
- Evita cortar frases no meio
- Mantém ritmo da cena

### ✅ Escalabilidade
- Cenas de qualquer duração (30s, 60s, 120s+)
- Múltiplos clips gerados em paralelo (futuro)
- Cache de áudio master para regenerações

---

## 🔧 Integração com StudioX Existente

### 1. Production Router (routers/studio/production.py)

**Modificar endpoint de geração de vídeo:**

```python
@router.post("/projects/{project_id}/generate-videos")
async def generate_videos(...):
    for scene in scenes:
        dialogue_timeline = scene.get('dialogue_timeline', [])
        
        # Verificar se precisa de stitching
        planner = VideoStitchingPlanner(scene, dialogue_timeline)
        
        if planner.needs_splitting():
            # NOVO FLUXO: Multiple clips com stitching
            clips = planner.create_clip_plan()
            
            # 1. Gerar áudio completo PRIMEIRO
            full_audio = AudioSynchronizer.generate_full_scene_audio(...)
            
            # 2. Gerar cada clip de vídeo com frame reference
            video_clips = []
            for i, clip_plan in enumerate(clips):
                # Gerar clip
                video = await generate_sora_clip(
                    scene=scene,
                    duration=clip_plan['duration'],
                    frame_reference=last_frame if i > 0 else None
                )
                video_clips.append(video)
                
                # Extrair último frame para próximo clip
                if i < len(clips) - 1:
                    last_frame = FrameStitcher.extract_last_frame(video)
            
            # 3. Sincronizar áudio com cada clip
            # 4. Merge final
            final_video = FrameStitcher.merge_clips_with_audio(...)
            
        else:
            # FLUXO EXISTENTE: Single clip ≤12s
            video = await generate_sora_clip(scene, duration=12)
```

### 2. Sound Design Agent (routers/studio/sound_design_agent.py)

**Já existe!** Apenas integrar:

```python
# Usar sound design agent para gerar áudio completo
from routers.studio.sound_design_agent import generate_scene_audio

full_audio = generate_scene_audio(
    scene=scene,
    dialogue_timeline=dialogue_timeline,
    character_voices=voices,
    background_music=music_track
)
```

### 3. Frontend (DirectedStudio.jsx)

**Adicionar indicador de stitching:**

```jsx
{scene.needs_stitching && (
  <div className="flex items-center gap-2 text-xs text-purple-400">
    <Scissors size={14} />
    <span>Cena longa: {scene.num_clips} clips com frame stitching</span>
  </div>
)}
```

---

## 📊 Exemplo Completo

### Cena: "Jonas e o Grande Peixe" (28 segundos)

**Dialogue Timeline:**
```json
[
  {"start": 0.0, "end": 5.5, "character": "Jonas", "text": "Olha o tamanho desse peixe!"},
  {"start": 6.0, "end": 10.0, "character": "Narrador", "text": "Jonas estava assustado"},
  {"start": 10.5, "end": 11.0, "character": null, "text": "[pausa dramática]"},
  {"start": 11.5, "end": 16.0, "character": "Peixe", "text": "Não tenha medo, pequeno"},
  {"start": 16.5, "end": 20.0, "character": "Jonas", "text": "Você... você fala?!"},
  {"start": 20.5, "end": 21.0, "character": null, "text": "[silêncio]"},
  {"start": 21.5, "end": 28.0, "character": "Peixe", "text": "Sim, tenho uma missão"}
]
```

**Plano de Stitching:**
```
Clip 0: 0.0s - 11.0s (11s)
  - Diálogo: Jonas + Narrador
  - Ponto de corte: Pausa dramática
  
Clip 1: 11.0s - 21.0s (10s)
  - Diálogo: Peixe + Jonas
  - Ponto de corte: Silêncio
  
Clip 2: 21.0s - 28.0s (7s)
  - Diálogo: Peixe (final)
  - Fim da cena
```

**Resultado Final:**
- ✅ Vídeo de 28s com transições suaves
- ✅ Música de fundo contínua
- ✅ Áudio sincronizado perfeitamente
- ✅ Cortes imperceptíveis nos pontos naturais

---

## 🚀 Próximos Passos

### Fase 1: Core Implementation (Esta Sessão)
- [x] Criar módulo `video_stitching.py`
- [ ] Integrar com `production.py`
- [ ] Testar com cena de 30s
- [ ] Validar continuidade visual e de áudio

### Fase 2: Audio Pipeline
- [ ] Integrar com ElevenLabs para geração de diálogos
- [ ] Implementar mixagem de áudio (diálogo + música + SFX)
- [ ] Adicionar fade in/out automático
- [ ] Cache de áudio master

### Fase 3: Otimizações
- [ ] Geração paralela de clips (quando não depende de frame anterior)
- [ ] Retry logic por clip individual
- [ ] Progress tracking detalhado
- [ ] Estimativa de custo (múltiplos clips)

### Fase 4: UI/UX
- [ ] Indicador visual de stitching
- [ ] Preview de pontos de corte
- [ ] Edição manual de cut points
- [ ] Timeline visual com clips

---

## ❓ FAQ

**Q: Frame stitching funciona bem?**
A: Sim! Sora 2 é treinado para manter continuidade quando recebe um frame de referência. A transição é suave.

**Q: E se a música não coincidir nos cortes?**
A: Não há problema! O áudio é gerado COMPLETO antes, então a música flui naturalmente através de todos os clips.

**Q: Posso ter cenas de 2 minutos?**
A: Sim! O sistema divide automaticamente em quantos clips de 12s forem necessários.

**Q: O custo aumenta?**
A: Sim, proporcionalmente. Cena de 24s = 2 clips = 2x o custo. Mas é a única forma de ter vídeos longos.

**Q: Posso editar os pontos de corte?**
A: Futuramente sim! Por enquanto, o sistema escolhe automaticamente os melhores pontos.

---

## 📚 Referências

- [Sora 2 API Documentation](https://platform.openai.com/docs/guides/sora)
- [FFmpeg Concat Demuxer](https://trac.ffmpeg.org/wiki/Concatenate)
- [ElevenLabs Voice Synthesis](https://elevenlabs.io/docs)
- StudioX Internal: `dialogue_timeline.py`, `sound_design_agent.py`
