# AgentZZ — Product Requirements Document

## Original Problem Statement
Build "AgentZZ" — a no-code SaaS with AI agents + "Directed Studio Mode" for animated film production. Storyboard-First workflow with editable panels, intelligent editing, multilingual support, and exports (PDF + Interactive Book).

## Credentials
- Test: test@agentflow.com / password123

---

## Implemented Features

### Directed Studio Mode — 5-Step Pipeline
`Roteiro -> Personagens -> Storyboard -> Producao -> Resultado`

### UX Redesign (2026-03-26)
- **Pipeline Navigation**: Minimal timeline with gold active node, white done nodes, dark gray future nodes, connecting track
- **Step 5 — Deliverables Showcase**:
  - Hero Card: "O Filme Completo" (full video with download)
  - Bento Grid: 4 product cards (Livro Animado, Storyboard PDF, Pós-Produção, Analytics)
  - Horizontal Scroll: Individual scene videos with hover-to-play
  - PostProduction moved to drawer/modal for cleaner layout
- **Typography**: Cormorant Garamond (serif headings), Manrope (sans body), JetBrains Mono (labels/badges)
- **Design System**: Enhanced with serif hierarchy, tracking-wide labels, inset glow hover effects

### Media Preview System (2026-03-26)
- **Video Player Modal**: Full-screen video player with native controls, scene navigation buttons, download
- **Image Gallery Modal**: Lightbox with left/right navigation, thumbnail strip, keyboard arrows support
- **Book Preview Modal**: Embedded iframe of Interactive Book with "Tela cheia" link
- **PDF Preview Modal**: Grid view of all storyboard illustrations (84 frames), click-to-expand, "Baixar PDF Completo" button
- **Keyboard Support**: Escape closes, Arrow keys navigate gallery

### Final Video Hero Card & Post-Production Improvements (2026-03-26)
- **Hero Card "Filme Final"**: Displays post-produced video at top of Step 5 with FILME FINAL, DUBLADO, TRILHA SONORA badges, metadata (duration, file size, language), click-to-preview, download button
- **Narration Mode Selector**: 3 modes — IA (ElevenLabs), Áudio Manual (upload), Misto (IA + uploads)
- **Per-Scene Audio Upload**: Upload custom narration/dubbing per scene with audio player, delete, and status indicators (Manual/IA)
- **Backend**: POST /api/studio/projects/{id}/upload-narration/{scene_number}, DELETE /api/studio/projects/{id}/narration/{scene_number}
- **Pós-Produção Card**: Shows completion status with green checkmark and "CONCLUÍDO — RECONFIGURAR" text

### Storyboard Editavel
- 6 individual frames per scene (Storybook Pages)
- Gallery/Filmstrip layout with page numbers

### Smart Image Editor
- Scene Analysis + Clickable Scene Map + Smart Edit

### Language Agent
- Convert (10 languages) + Review (AI quality)

### Continuity Director Agent
- ALL 6 FRAMES per scene analyzed against avatar images
- Auto-Correction of high/medium issues

### 4-Layer Cache System
- ImageCache (disk + memory), ProjectCache (read-through + write-behind), LLMCache (content-addressable), Frontend SWR

### Exports
- PDF Storybook, Interactive Animated Book, MP4 Preview

### Voice Commands (Whisper STT)

---

## Code Architecture
```
/app/backend/core/
  cache.py, continuity_director.py, smart_editor.py,
  storyboard_inpaint.py, storyboard.py, language_agent.py,
  book_generator.py, preview_generator.py, llm.py
/app/backend/routers/studio.py (~5200 lines)
/app/frontend/src/
  hooks/useProjectCache.js
  components/DirectedStudio.jsx (Redesigned Step 5 + Navigation)
  components/StoryboardEditor.jsx
  components/PostProduction.jsx
  components/FinalPreview.jsx
  pages/InteractiveBook.jsx
```

## Backlog
- P1: Refactor studio.py (5200+ lines)
- P2: Storyboard -> Video (Sora 2)
- P3: Omnichannel, Admin + Stripe

## Test Reports
- 110-113: Core features (100%)
- 114: Continuity Director (100%)
- 115: Cache System (100%)
- 116: UX Redesign Step 5 + Navigation (100%)
- 117: Media Preview Modal System (100%) — Book, PDF, Video, Gallery all tested
- 118: Hero Card Filme Final + Post-Production Upload (Backend 100%, Frontend 95%)
