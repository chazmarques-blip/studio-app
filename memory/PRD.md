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
- Generate all panels via Gemini Nano Banana
- **6-frame grid per scene** (1 Gemini call → 2x3 grid → Pillow split into 6 frames)
- Frame types: Plano Geral, Close-up, Ação, Reação, Ângulo Dramático, Transição
- Frontend: 3-column grid within each panel card, fallback to single image for legacy panels
- AI Facilitator Chat (Claude) for natural language panel editing
- Approve Storyboard → unlock video production

### Preview Animado (Phase 7.5) ✅
- Interactive Browser Slideshow with Ken Burns CSS, fade transitions, subtitles, controls
- MP4 Export with ElevenLabs narration + cinematic music via FFmpeg
- Rendered via React createPortal

### Edição de Elemento (Inpainting IA) ✅
- Paintbrush icon on panel hover → "Editar Elemento" input
- Gemini edits only the specified element, preserving everything else
- Module: `/app/backend/core/storyboard_inpaint.py`

### Comando de Voz (Whisper STT) ✅
- `VoiceInput.jsx` — universal mic component
- Integrated in: Facilitator IA chat, Inpainting input
- Uses `/api/ai/transcribe` with auth

### UI Improvements ✅
- FilmSpinner component (Film icon, 1.5s animation)
- Fixed double spinner bug
- Panel hover: 3 icons (expand, paintbrush, film reel)

### Earlier Features (Complete)
- Claude screenwriter, character avatars, parallel Sora 2 + Gemini generation
- Multi-voice dubbed mode (ElevenLabs), post-production audio mixing
- Google Calendar/Sheets integration, Agent marketplace, CRM

---

## Code Architecture
```
/app/backend/core/
├── storyboard.py           # Panel gen + 6-frame split + AI Facilitator
├── storyboard_inpaint.py   # Element-specific image editing (Gemini)
├── preview_generator.py    # MP4 preview (FFmpeg + ElevenLabs)
/app/frontend/src/components/
├── DirectedStudio.jsx      # 5-step pipeline UI
├── StoryboardEditor.jsx    # Panel editing + 6-frame grid + Inpainting + Voice
├── StoryboardPreview.jsx   # Animated slideshow player
├── VoiceInput.jsx          # Universal voice command button
```

---

## Prioritized Backlog

### P1
- Storybook Export (PDF/image book from approved storyboard)
- Storyboard→Video (feed approved frames to Sora 2)
- Refactor studio.py (~4500 lines)
- Fix hot-reload killing background tasks

### P2
- Omnichannel (WhatsApp, SMS, Instagram, Telegram)
- Admin Dashboard + Stripe

### P3
- Legal, Scalability, App store

---

## Test Reports
- iteration_105: Storyboard endpoints (92%)
- iteration_106: Preview + MP4 (92%)
- iteration_107: Inpainting + Voice + FilmSpinner (100%)
- iteration_108: 6-frame grid (100%, 13/13 backend + code review)
