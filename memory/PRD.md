# AgentZZ — Product Requirements Document

## Original Problem Statement
Build "AgentZZ" — a no-code SaaS with AI agents + "Directed Studio Mode" for animated film production. Storyboard-First workflow with editable panels, exports (PDF + Interactive Animated Book).

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Directed Studio Mode — 5-Step Pipeline
`Roteiro -> Personagens -> Storyboard -> Producao -> Resultado`

### Storyboard Editavel
- 6 individual frames per scene (Storybook Pages: Abertura, Tensao, Acao, Reacao, Consequencia, Encerramento)
- Gallery/Filmstrip layout with page numbers
- Visible toolbar (inpaint + regen) — no overlay on images
- AI Facilitator Chat (Claude)

### Preview Animado + MP4 Export
- Browser slideshow + ElevenLabs TTS + FFmpeg MP4

### Edicao de Elemento (Inpainting)
- Consistent h-8 sizing for mic button + edit button
- VoiceInput with Whisper STT (via emergentintegrations)

### Exportar Livro (NEW - Phase complete)
- **Gerar Capa + Titulo**: Gemini generates cover image with all characters + Claude generates creative title
- **PDF Storybook Export**: Full PDF with cover + all illustrated pages (sorted chronologically)
- **Livro Animado Interativo**: Standalone page at `/book/:projectId`
  - Page-turn animations (CSS flip)
  - Auto-narration TTS (ElevenLabs) on page turn
  - Toggle "Leia para mim" vs silent reading
  - Keyboard nav (arrows), touch/swipe for mobile
  - Progress bar, page counter
  - Cover page, story pages, "Fim" end page

### Hot-Reload Recovery
- Startup cleanup resets orphaned generating statuses

---

## Code Architecture
```
/app/backend/core/
  storyboard.py           # 6 storybook pages per scene
  storyboard_inpaint.py   # Element editing (Gemini)
  preview_generator.py    # MP4 (FFmpeg + ElevenLabs)
  book_generator.py       # NEW: PDF + cover + interactive book data
  llm.py                  # Whisper STT via emergentintegrations
/app/backend/routers/
  studio.py               # All endpoints including book export
/app/frontend/src/
  pages/InteractiveBook.jsx  # NEW: Standalone animated book reader
  components/StoryboardEditor.jsx  # Book export UI section
```

## Key API Endpoints (Book)
- `POST /api/studio/projects/{id}/book/generate-cover` — Gemini cover + Claude title
- `GET /api/studio/projects/{id}/book/pdf` — Download PDF storybook
- `GET /api/studio/projects/{id}/book/interactive-data` — JSON for animated reader
- `POST /api/studio/projects/{id}/book/tts-page` — ElevenLabs TTS per page

## Backlog
- P0: Agente de conversao e revisao de idioma (user requested post-first-edition)
- P1: Agente Editor Inteligente de Imagens (scene analysis + targeted editing)
- P1: Refactor studio.py (4500+ lines)
- P2: Storyboard -> Video (Sora 2)
- P3: Omnichannel, Admin + Stripe

## Test Reports
- 110: Individual frames + toolbar (100%)
- 111: Whisper fix + storybook pages (100%)
- 112: Book export + Interactive book (100%)
