# AgentZZ — Product Requirements Document

## Original Problem Statement
Build "AgentZZ" — a no-code SaaS with AI agents + "Directed Studio Mode" for animated film production. Pivoting to **Storyboard-First** workflow to fix video generation inconsistencies.

## Core Architecture
- **Frontend:** React + Tailwind CSS + shadcn-ui + Lucide Icons + Framer Motion
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL)
- **3rd Party:** Claude (Emergent LLM Key), Sora 2, Gemini Nano Banana (Emergent LLM Key), ElevenLabs TTS, OpenAI Whisper

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Directed Studio Mode — 5-Step Pipeline
`Roteiro → Personagens → Storyboard → Produção → Resultado`

### Storyboard Editável (Phase 7) ✅
- Generate all panels via Gemini Nano Banana (1 image per scene)
- 2-column grid with images + dialogue + character tags
- Inline editing (title, description, dialogue)
- AI Facilitator Chat (Claude) for natural language panel editing
- Approve Storyboard → unlock video production

### Preview Animado (Phase 7.5) ✅
- **Interactive Browser Slideshow** with Ken Burns CSS animations, fade transitions, synchronized subtitles, play/pause/skip, fullscreen, keyboard shortcuts
- **MP4 Export** with ElevenLabs narration + cinematic background music via FFmpeg
- Rendered via React createPortal for z-index isolation

### Edição de Elemento (Inpainting IA) ✅ — 2026-03-26
- Click paintbrush icon on panel → "Editar Elemento" input appears
- Describe what to change: "Remover a corcova do Isaque"
- Gemini edits ONLY that element, preserving everything else
- Backend: `POST /api/studio/projects/{id}/storyboard/edit-element`
- Module: `/app/backend/core/storyboard_inpaint.py`

### Comando de Voz (Whisper STT) ✅ — 2026-03-26
- `VoiceInput.jsx` — universal microphone component
- Integrated in: Facilitator IA chat, Inpainting edit input
- Uses existing `/api/ai/transcribe` endpoint with auth
- Records via MediaRecorder API, transcribes via Whisper

### UI Fixes ✅ — 2026-03-26
- **Film reel icon** (Film from lucide) replaces RefreshCw for all film-related loading
- **FilmSpinner** component with 1.5s animation for generation states
- **Fixed double spinner** — regenerating panels show single centered FilmSpinner only
- Panel hover overlay: 3 icons (expand, paintbrush/inpaint, film reel/regenerate)

### Earlier Features (Complete)
- Claude-powered screenwriter chat
- Character avatar system
- Parallel generation pipeline (Sora 2 + Gemini)
- Multi-voice dubbed mode (ElevenLabs)
- Post-production audio mixing
- Google Calendar/Sheets integration
- Agent marketplace, CRM, omnichannel UI

---

## Code Architecture
```
/app/backend/
├── core/
│   ├── storyboard.py          # Panel generation + AI Facilitator
│   ├── storyboard_inpaint.py  # Element-specific image editing (Gemini)
│   ├── preview_generator.py   # MP4 preview (FFmpeg + ElevenLabs)
│   ├── llm.py
├── routers/
│   ├── studio.py              # ~4500 lines - main studio logic
│   ├── ai.py                  # Whisper transcription endpoint
/app/frontend/src/
├── components/
│   ├── DirectedStudio.jsx     # 5-step pipeline UI
│   ├── StoryboardEditor.jsx   # Panel editing + AI Facilitator + Inpainting
│   ├── StoryboardPreview.jsx  # Animated slideshow player
│   ├── VoiceInput.jsx         # Universal voice command button
```

---

## Prioritized Backlog

### P1
- Grid 6 frames per scene (generate single 2x3 image, split into 6 frames)
- Storybook Export (static PDF/image book)
- Storyboard→Video (feed approved panels to Sora 2)
- Refactor `studio.py` into modular services
- Fix hot-reload killing background tasks

### P2
- Omnichannel live integrations (WhatsApp, SMS, Instagram, Telegram)
- Admin Management System + Stripe

### P3
- Legal & publication, Scalability hardening

---

## Test Reports
- iteration_105.json — Storyboard endpoints (92%)
- iteration_106.json — Preview Animado + MP4 (92%)
- iteration_107.json — Inpainting + VoiceInput + FilmSpinner (100%)

## Known Issues
- Hot-reload kills background production threads (P1)
- `studio.py` ~4500 lines needs refactoring (P1)
