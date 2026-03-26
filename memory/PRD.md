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
- 6 individual frames per scene (Storybook Pages)
- Gallery/Filmstrip layout with page numbers
- Visible toolbar (inpaint + regen) — no overlay

### Smart Image Editor
- Scene Analysis: Gemini Vision scans image → structured map
- Clickable Scene Map: Elements listed in UI
- Smart Edit: 2-step pipeline — analyze then edit
- Toggle: Smart mode vs basic inpaint

### Language Agent
- Convert: Translate to 10 languages
- Review: AI quality review + text improvement
- Batched processing (5 scenes per call)

### Continuity Director Agent
- Holistic Analysis: ALL 6 FRAMES of each scene analyzed
- Uses AVATAR IMAGES as primary visual reference (not text descriptions)
- Character Consistency Check: species, clothing, colors, proportions
- Age Accuracy, Irrelevant Element Detection, Visual Quality Check
- Auto-Correction: fixes high/medium issues using inpainting
- Batched: 1 scene per LLM call (11 avatars + 6 frames)
- Endpoints: POST /continuity/analyze, GET /continuity/status, POST /continuity/auto-correct

### 4-Layer Cache System (NEW — 2026-03-26)
- **Layer 1 — ImageCache**: Disk-persistent (SHA256), in-memory hot layer (50 items), pre-warming, deduplication
- **Layer 2 — ProjectCache**: Read-through (5min TTL), write-behind batching (3s flush interval), dirty tracking, per-tenant locks
- **Layer 3 — LLMCache**: Content-addressable (prompt + image hashes), 1hr TTL, auto-invalidation
- **Layer 4 — Frontend SWR**: Stale-while-revalidate (30s stale, 5min max), image preloading, optimistic updates
- Endpoints: GET /cache/stats, POST /cache/flush
- Shutdown hook: auto-flushes dirty data to DB
- Integrated in: continuity_director, smart_editor, storyboard_inpaint, studio router

### Exports
- PDF Storybook: Cover + all illustrated pages
- Interactive Animated Book: `/book/:projectId`
- Cover Generation: Gemini + Claude creative title

### Preview Animado + MP4 Export
- Browser slideshow + ElevenLabs TTS + FFmpeg

### Voice Commands (Whisper STT)
- Via emergentintegrations

---

## Code Architecture
```
/app/backend/core/
  cache.py                # 4-layer cache system (ImageCache, ProjectCache, LLMCache)
  continuity_director.py  # Continuity analysis + auto-correction (cached)
  smart_editor.py         # Scene analysis + editing (cached)
  storyboard_inpaint.py   # Image editing (cached)
  storyboard.py           # Frame generation
  language_agent.py       # Translation + review
  book_generator.py       # PDF + cover + interactive
  preview_generator.py    # MP4
  llm.py                  # Whisper STT
/app/backend/routers/
  studio.py               # All endpoints (~5200 lines)
/app/frontend/src/
  hooks/useProjectCache.js # Frontend SWR cache + image preloader
  pages/InteractiveBook.jsx
  components/StoryboardEditor.jsx
  components/VoiceInput.jsx
```

## Backlog
- P1: Refactor studio.py (5200+ lines)
- P2: Storyboard -> Video (Sora 2)
- P3: Omnichannel, Admin + Stripe

## Test Reports
- 110-113: All features (100%)
- 114: Continuity Director Agent (100%) — 29/29
- 115: 4-Layer Cache System (100%) — 32/32
