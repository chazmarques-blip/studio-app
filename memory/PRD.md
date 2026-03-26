# AgentZZ — Product Requirements Document

## Original Problem Statement
Build "AgentZZ" — a no-code SaaS with AI agents + "Directed Studio Mode" for animated film production. Storyboard-First workflow with editable panels, intelligent editing, multilingual support, and exports (PDF + Interactive Book).

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Directed Studio Mode — 5-Step Pipeline
`Roteiro -> Personagens -> Storyboard -> Producao -> Resultado`

### Storyboard Editavel
- 6 individual frames per scene (Storybook Pages: Abertura, Tensao, Acao, Reacao, Consequencia, Encerramento)
- Gallery/Filmstrip layout with page numbers
- Visible toolbar (inpaint + regen) — no overlay

### Smart Image Editor
- **Scene Analysis**: Gemini Vision scans image → structured map of characters, objects, background, quality issues
- **Clickable Scene Map**: Elements listed in UI, click to select for editing
- **Smart Edit**: 2-step pipeline — analyze scene first, then edit with full context → preserves unrelated elements
- **Toggle**: Smart mode (Zap icon) vs basic inpaint

### Language Agent
- **Convert**: Translate all scenes to 10 languages (pt, en, es, fr, it, de, ja, ko, zh, ar)
- **Review**: AI quality review + text improvement (8/10 for test project)
- Batched processing (5 scenes per Claude call to avoid timeouts)
- Background tasks with polling status

### Continuity Director Agent (NEW — 2026-03-26)
- **Holistic Analysis**: Analyzes ALL frames across the entire storyboard for visual consistency
- **Character Consistency Check**: Verifies each character matches their reference description (clothing, hair, skin, proportions, age)
- **Age Accuracy**: Validates characters shown at correct age for each scene
- **Irrelevant Element Detection**: Finds objects/characters that don't belong in the scene
- **Visual Quality Check**: Detects deformations, extra limbs, AI artifacts
- **Auto-Correction**: Automatically fixes high/medium severity issues using existing inpainting pipeline
- **Batched Processing**: Analyzes scenes in batches of 3 to avoid API timeouts
- **Background Tasks**: Both analysis and correction run as background threads with polling
- Endpoints: POST /continuity/analyze, GET /continuity/status, POST /continuity/auto-correct

### Exports
- **PDF Storybook**: Cover + all illustrated pages
- **Interactive Animated Book**: `/book/:projectId` with page-turn animation, TTS narration, swipe/keyboard nav
- **Cover Generation**: Gemini creates cover with all characters + Claude generates creative title

### Preview Animado + MP4 Export
- Browser slideshow + ElevenLabs TTS + FFmpeg

### Voice Commands (Whisper STT)
- Via emergentintegrations (fixed quota issue)

---

## Code Architecture
```
/app/backend/core/
  storyboard.py           # 6 storybook pages per scene
  storyboard_inpaint.py   # Basic element editing
  smart_editor.py         # Scene analysis + targeted editing
  language_agent.py       # Translation + review (batched)
  continuity_director.py  # NEW: Holistic consistency analysis + auto-correction
  book_generator.py       # PDF + cover + interactive book data
  preview_generator.py    # MP4 (FFmpeg + ElevenLabs)
  llm.py                  # Whisper STT
/app/backend/routers/
  studio.py               # All endpoints (5200+ lines)
/app/frontend/src/
  pages/InteractiveBook.jsx  # Animated book reader
  components/StoryboardEditor.jsx  # Full editor UI with all agents
  components/VoiceInput.jsx  # Universal mic button
```

## Key API Endpoints
- `POST /api/studio/projects/{id}/storyboard/analyze-scene` — Gemini Vision scene map
- `POST /api/studio/projects/{id}/storyboard/smart-edit` — AI-aware editing
- `POST /api/studio/projects/{id}/language/convert` — Translate to target lang
- `POST /api/studio/projects/{id}/language/review` — Quality review
- `GET /api/studio/projects/{id}/language/status` — Poll language status
- `POST /api/studio/projects/{id}/continuity/analyze` — Start continuity analysis (NEW)
- `GET /api/studio/projects/{id}/continuity/status` — Poll continuity status (NEW)
- `POST /api/studio/projects/{id}/continuity/auto-correct` — Auto-correct issues (NEW)
- `POST /api/studio/projects/{id}/book/generate-cover` — Cover + title
- `GET /api/studio/projects/{id}/book/pdf` — Download PDF
- `GET /api/studio/projects/{id}/book/interactive-data` — Book JSON
- `POST /api/studio/projects/{id}/book/tts-page` — TTS per page

## Backlog
- P1: Refactor studio.py (5200+ lines)
- P2: Storyboard -> Video (Sora 2)
- P3: Omnichannel, Admin + Stripe

## Test Reports
- 110: Individual frames + toolbar (100%) | 111: Whisper + storybook pages (100%)
- 112: Book export + Interactive book (100%) | 113: Language Agent + Smart Editor (100%)
- 114: Continuity Director Agent (100%) — 29/29 tests passed
