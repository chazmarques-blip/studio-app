# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated children's content (Pixar-style).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL (Auth + Storage + DB)
- **AI Services**: Gemini (images), OpenAI gpt-4o-mini (text), Kling AI v3 (video + V2A), ElevenLabs (voice TTS)

## Production Pipeline (4 Phases)

### PHASE A: Scene Directors (existing)
### PHASE B: Video Generation — Dual Mode (existing)
- **Modo Rápido**: 30 parallel I2V clips + xfade crossfade (~5 min)
- **Modo Cinema**: Sequential clips using last real frame extraction (~20 min)

### PHASE C: Audio Production (improved 2026-04-14)
- Clean dialogue generation with character name prefixes
- Stage direction filtering (13+ markers detected and cleaned)
- Character-specific voice mapping via ElevenLabs TTS
- Silence generation for non-dialogue frames
- V2A sonoplastia with 20s video sample (looped to full length)

### PHASE D: Final Mix + Multi-format Export (fixed 2026-04-14)
- Video compression (CRF 28) when >48MB for Supabase upload
- YouTube 16:9, TikTok 9:16, Instagram 1:1
- Fallback to YouTube format URL if main upload fails

## Recent Changes

### Full Production Pipeline Fix (2026-04-14)
- **Bug Fix**: Video upload was failing because tmpdir was deleted before upload — moved upload BEFORE cleanup
- **Bug Fix**: Payload too large (55MB > 50MB Supabase limit) — added auto-compression with CRF 28
- **Bug Fix**: Storyboard "Gerar Storyboard" button required 2 clicks — fixed to 1-click for initial generation
- **Improvement**: Dialogue generation prompt completely rewritten — ONLY spoken words, no stage directions
- **Improvement**: Stage direction filter (13 markers: "SILÊNCIO", "câmera", etc.) removes non-dialogue text
- **Improvement**: Production timeline shows real-time progress from backend (progress_message, full_production_status)
- **Improvement**: V2A sonoplastia now extracts 20s sample (API limit) and loops audio to full video length
- **Improvement**: Multi-format URLs saved to project and displayed in results UI

### Pipeline Tracker Dynamic Progress (2026-04-13)
- Backend: Added `pipeline_phase` field updated at each stage
- Frontend: Production timeline shows 4-phase tracker (Dialogues → Video → Audio → Done)
- Frontend: Live progress message from backend displayed

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project IDs: 06c877c953a3, b5cbe7c320f6, 0295f93baf6e

## Pending Tasks

### P0 (Critical)
- None currently blocking

### P1 (Important)  
- Improve dialogue distribution across 30 frames (currently ~17/30 have dialogue)
- Lip sync integration using Kling Lip-Sync API

### P2 (Backlog)
- Custom Video Editor UI (Timeline/Layers)
- "Seed Oficial" System for new tenants
- Modularize DirectedStudio.jsx (~4600 lines)
- Migrate Avatar states to useAvatarManager.js hook
