# AgentZZ — Product Requirements Document

## Original Problem Statement
Build "AgentZZ" — a no-code SaaS with AI agents + "Directed Studio Mode" for animated film production. Pivoting to **Storyboard-First** workflow to fix video generation inconsistencies.

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Directed Studio Mode — 5-Step Pipeline
`Roteiro → Personagens → Storyboard → Produção → Resultado`

### Storyboard Editável ✅
- 6 frames per scene (1 Gemini call → 2x3 grid → Pillow split)
- **Gallery/Filmstrip layout**: Large main display + horizontal thumbnails strip
- Click thumbnail → becomes main display; edits apply to selected frame
- Frame types: Plano Geral, Close-up, Ação, Reação, Ângulo Dramático, Transição
- AI Facilitator Chat (Claude) for natural language editing
- Approve Storyboard → unlock video production

### Preview Animado ✅
- Interactive browser slideshow with Ken Burns, subtitles, controls
- MP4 Export with ElevenLabs narration + FFmpeg

### Edição de Elemento (Inpainting IA) ✅
- Paintbrush icon → describe change → Gemini edits only that element

### Comando de Voz (Whisper STT) ✅
- VoiceInput.jsx mic button in Facilitator chat + Inpainting input

### UI ✅
- FilmSpinner (Film icon, 1.5s), fixed double spinner, panel hover 3 icons

---

## Code Architecture
```
/app/backend/core/
├── storyboard.py           # 6-frame generation + split + AI Facilitator
├── storyboard_inpaint.py   # Element editing (Gemini)
├── preview_generator.py    # MP4 (FFmpeg + ElevenLabs)
/app/frontend/src/components/
├── DirectedStudio.jsx      # 5-step pipeline
├── StoryboardEditor.jsx    # Gallery/filmstrip + editing + voice
├── StoryboardPreview.jsx   # Animated slideshow
├── VoiceInput.jsx          # Universal mic button
```

## Backlog
- P1: Storybook Export, Storyboard→Video (Sora 2), Refactor studio.py, Fix hot-reload
- P2: Omnichannel, Admin + Stripe
- P3: Legal, Scalability

## Test Reports
- 105: Storyboard endpoints (92%) | 106: Preview+MP4 (92%) | 107: Inpaint+Voice (100%) | 108: 6-frame (100%) | 109: Gallery/filmstrip (100%)
