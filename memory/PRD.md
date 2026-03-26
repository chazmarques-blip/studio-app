# AgentZZ — Product Requirements Document

## Original Problem Statement
Build "AgentZZ" — a no-code SaaS with AI agents + "Directed Studio Mode" for animated film production. Pivoting to **Storyboard-First** workflow to fix video generation inconsistencies.

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Directed Studio Mode — 5-Step Pipeline
`Roteiro -> Personagens -> Storyboard -> Producao -> Resultado`

### Storyboard Editavel
- **6 individual frames per scene** (6 separate Gemini calls — NO grid slicing)
- Frame types: Plano Geral, Close-up, Acao, Reacao, Angulo Dramatico, Transicao
- **Gallery/Filmstrip layout**: Large main display + horizontal thumbnails strip
- Click thumbnail -> becomes main display; edits apply to selected frame
- **Visible toolbar** below filmstrip (expand, inpaint, regen) — NOT overlay on image
- AI Facilitator Chat (Claude) for natural language editing
- Approve Storyboard -> unlock video production

### Preview Animado
- Interactive browser slideshow with Ken Burns, subtitles, controls
- MP4 Export with ElevenLabs narration + FFmpeg

### Edicao de Elemento (Inpainting IA)
- Paintbrush icon -> describe change -> Gemini edits only that element
- **Visible microphone button** (VoiceInput h-7 w-7) in inpainting input

### Comando de Voz (Whisper STT)
- VoiceInput.jsx mic button in Facilitator chat + Inpainting input

### Hot-Reload Recovery (P1)
- Startup cleanup: `_cleanup_stale_storyboards()` resets orphaned "starting"/"generating" statuses
- Prevents UI from getting stuck when background threads die during hot-reload

### UI
- FilmSpinner (Film icon, 1.5s), fixed double spinner, panel hover 3 icons
- Editing toolbar always visible below image (not overlay)
- Dark luxury theme (black/gold/white)

---

## Code Architecture
```
/app/backend/core/
  storyboard.py           # Individual frame generation (6 per scene) + AI Facilitator
  storyboard_inpaint.py   # Element editing (Gemini)
  preview_generator.py    # MP4 (FFmpeg + ElevenLabs)
/app/backend/routers/
  studio.py               # Main router (4500+ lines)
/app/backend/server.py    # FastAPI app + startup cleanup
/app/frontend/src/components/
  DirectedStudio.jsx      # 5-step pipeline
  StoryboardEditor.jsx    # Gallery/filmstrip + editing + voice + visible toolbar
  StoryboardPreview.jsx   # Animated slideshow
  VoiceInput.jsx          # Universal mic button
```

## Backlog
- P1: Refactor studio.py (4500+ lines), Storybook Export, Storyboard->Video (Sora 2)
- P2: Omnichannel, Admin + Stripe
- P3: Legal, Scalability

## Test Reports
- 105: Storyboard endpoints (92%) | 106: Preview+MP4 (92%) | 107: Inpaint+Voice (100%) | 108: 6-frame (100%) | 109: Gallery/filmstrip (100%) | 110: Individual frame gen + UI toolbar fix (100%)
