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
- Frame types: **Storybook Pages** in chronological order:
  - Pagina 1: Opening Moment (inicio da cena)
  - Pagina 2: Rising Action (tensao/interesse cresce)
  - Pagina 3: Key Action (momento central dramatico)
  - Pagina 4: Reaction (reacao dos personagens)
  - Pagina 5: Consequence (consequencia da acao)
  - Pagina 6: Closing Moment (encerramento/transicao)
- Each frame = full storybook page with narrative action (no zoom/close-ups)
- **Gallery/Filmstrip layout**: Large main display + horizontal thumbnails with page numbers
- **Visible toolbar** below filmstrip (inpaint + regen only, no expand/zoom)
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
- **Uses emergentintegrations.llm.openai.OpenAISpeechToText** (not direct OpenAI SDK)

### Hot-Reload Recovery
- Startup cleanup: `_cleanup_stale_storyboards()` resets orphaned statuses

### UI
- Dark luxury theme (black/gold/white)
- FilmSpinner, page numbers on filmstrip thumbnails
- Toolbar shows "Pag X/Y" format

---

## Code Architecture
```
/app/backend/core/
  storyboard.py           # Individual frame generation (6 storybook pages per scene)
  storyboard_inpaint.py   # Element editing (Gemini)
  preview_generator.py    # MP4 (FFmpeg + ElevenLabs)
  llm.py                  # Whisper STT via emergentintegrations
/app/backend/routers/
  studio.py               # Main router (4500+ lines)
  ai.py                   # Transcription endpoint
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
- 105-109: Previous iterations
- 110: Individual frame gen + toolbar fix (100%)
- 111: Whisper fix + storybook pages + zoom removal (100%)
