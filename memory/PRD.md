# StudioX - Product Requirements Document

## Original Problem Statement
StudioX is an end-to-end autonomous video creation platform for animated content (Pixar/DreamWorks quality).

## Core Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI
- **Backend**: FastAPI + Python
- **Database**: Supabase PostgreSQL
- **AI Services**: OpenAI GPT-4o-mini (text) + Sora 2 (video), Claude Sonnet 4.5 (scene direction/review), Gemini (keyframes), ElevenLabs (TTS), Kling AI (V2A sonoplastia)

## SORA 2 PIPELINE (Cinema Sequential Mode)
1. **Dialogue Unified**: `dubbed_text` = `dialogue` (single source of truth)
2. **Scene Directors SEQUENTIAL**: Each receives prev_scene context + Edge Mirroring + personality
3. **Keyframe**: Only scene 1 gets Gemini keyframe; scenes 2+ use last frame
4. **Sora 2 Video**: Full prompt (dialogue FIRST, no truncation), native audio kept
5. **Cinema Sequential**: Each clip sequential, last frame extracted for next
6. **FFmpeg Crossfade**: 1s xfade + acrossfade between clips (max 15 scenes; >15 uses simple concat)
7. **V2A Sonoplastia**: BGM + SFX added ON TOP of native Sora 2 audio (12% vol)

## Agent Intelligence (Current Rules)

### Scene Director
- DYNAMICS: Characters constantly moving, expressions change every 2s, physical comedy
- EDGE MIRRORING: ENTRY 0-1s → ACTION 1-11s → EXIT 11-12s
- ENVIRONMENT TRANSITIONS: Motivated movement (character walks through door), camera follows, gradual lighting shift
- PERSONALITY: Gestures/expressions match character personality

### Screenwriter  
- Dialogue: 35-40 words/scene (~9-10s speech), 3 characters interact in every scene
- Last dialogue line connects to next scene's topic
- Continuity fields: transition_from, transition_to, music_mood, sfx_notes
- Environment transitions: EXIT dialogue motivates move, descriptions show journey

### Character Personality System
- Field `personality` on each character (temperament, humor, catchphrases)
- Injected into Screenwriter prompts → dialogue with personality
- Injected into Scene Director → visual expressions/gestures match

## Features Implemented
- Cinema Sequential Mode with Edge Mirroring
- Character Bible from Claude Vision (analyzes real avatar images)
- Dialogue unification (dubbed_text = dialogue)
- Custom instruction field for scene regeneration
- Scene editing in zoom modal (title, description, dialogue)
- Auto-advance Screenwriter → Director Review
- Director Review in background (no 502 timeout)
- Rebuild Film button (re-concatenate after scene regeneration)
- Auto-fix stuck storyboard panels (>5 min generating)
- Cache-buster on regenerated storyboard images
- max_scenes parameter for partial production
- V2A sonoplastia using scene music_mood/sfx_notes
- Produce Missing Scenes (skip cached scenes in full production)
- Large project support (32+ scenes concat with adaptive compression)
- Folder delete with inline two-click confirmation
- Hierarchical folder system (subpastas with parent_id)
- ElevenLabs Music API integration (original soundtrack generation per project)
- **BookFactory pipeline** (Session 5): 4-agent layout review (Revisor Literário, Plano, Curador Visual, Diagramador Master + Revisor Tipográfico)
- **Inline PDF viewer** with react-pdf + progress bar (Session 6)
- **Modal-based prose editor** replacing window.prompt (Session 6)
- **Project type filters** in Studio page: Tudo / Vídeos / Livros / Híbridos (Session 6)
- **Hybrid project navigation banner** — DirectedStudio shows "Ver livro" button for output_mode='both' (Session 6)
- **DirectedStudio Refactor Fase 1** (2026-04-21): Extracted PipelineTrackerInline + SortableSceneWrapper to `/app/frontend/src/components/pipeline/`; removed dead code `_calcProgress`; file reduced from 4987 → 4606 lines (−381 lines). 100% passing in iteration_141.
- **Active Agent Live Feedback** (2026-04-21): Real-time "thinking" indicator. Backend `agents_activity.py` + endpoint `GET /api/studio/projects/{id}/active-agent`. Frontend `ActiveAgentIndicator.jsx` (2s polling, animated Brain badge with master reference + thinking dots + elapsed timer). Instrumented: screenwriter, director, continuity video (Thelma Schoonmaker), continuity book (Glen Keane), book factory illustration plan (Mary Blair). 11/11 backend tests passing in iteration_142.
- **P2 Parcial — Métricas + Export/Import + Keyboard Nav** (2026-04-22): Backend `agents_metrics.py` (record_activation, GET metrics, POST reset). `GET /agents/export` + `POST /agents/import` com format_version=1. Frontend AgentsPage: 3 novos botões (Métricas, Exportar, Importar) + MetricsModal com tabela de ativações/custo/latência. Lightbox: Esc, ← → entre vídeos, Space play/pause. Testing Agent iteration_143: Backend 25/25, Frontend 100%.
- **P2 Parte 2 — Cleanup Legacy + Multi-Format Export** (2026-04-22): Removidos 13 pages frontend + 7 routers backend CRM/Marketing legacy. Novo `multi_format_export.py` com ffmpeg blurred backdrop (9:16/1:1/4:5/16:9). Novo `MultiFormatExport.jsx` em DirectedStudio step 7 com polling 5s. Testing Agent iteration_144: Backend 22/23 (1 flaky transient) + Frontend 90%.
- **P0 + P1 Crítico — Vídeos Perfeitos** (2026-04-23): (a) Continuity Auto-Fix Loop: POST `/continuity-auto-fix` + `_do_regenerate_scene` in-process helper; (b) Character Bible Enforcement no screenwriter prompt (🔒 IMMUTABLE rules); (c) Cinema + Sora 2 Pro default ON para films >= 3 scenes; (d) Token Tracking via ContextVar + `_llm_context()` context manager → auto-accumula input/output_tokens no active_agent; (e) Progress Granular: `progress_percent` + `phase_detail`; (f) Loudness Normalization `loudnorm=I=-16:TP=-1.5:LRA=11`; (g) Frontend Auto-Fix button em ContinuityAuditModal + global progress bar. Testing Agent iteration_145: Backend 13/13 + Frontend 100%, zero regressões.
- **P2 (3ª rodada) — Quality Dashboard + Multi-idioma + Cleanup** (2026-04-23): (a) GET `/api/studio/quality-dashboard` agrega videos/books/auto_fix/cost/hot_issues; (b) `QualityDashboardStrip.jsx` com 4 KPIs + hot issues banner + health score badges nos cards (🟢🟡🔴); (c) `resolve_agent_prompt` multi-idioma com OUTPUT LANGUAGE directive (pt, en, es, fr, etc.); (d) 33 naked `except:` → `except Exception:`. Testing Agent iteration_146: Backend 21/21 + Frontend 100%, zero regressões.
- **P0 Delete Bug + P2 Mindset Templates (Dream Teams)** (2026-04-23): (a) Bug do botão Excluir — adicionado **optimistic update** em `handleDeleteProject` (StudioPage.jsx L907-946): remove card da UI imediatamente, com rollback via `fetchProjects()` se API falhar; (b) **9 Mindset Templates pré-configurados** — seed `/app/memory/agents/_mindset_templates.json` com bundles (Cinema Arte, Blockbuster, Animação Pixar, Documentário, Noir/Suspense, Infantil/Picturebook + 3 customizados **Bibizoo 6-9**, **Bibizoo Baby 3-5**, **Petz Genius**); (c) 3 endpoints novos em `agents_registry.py`: `GET /agents/mindset-templates`, `POST /agents/mindset-templates/apply` (com `overwrite_system_prompt` opcional), `POST /agents/mindset-templates/deactivate`; (d) Frontend: novo `MindsetTemplatesPicker.jsx` (modal com grid de 9 cards, emojis, dream team, badge ATIVO) integrado em AgentsPage via botão "Dream Team" gradiente violet→fuchsia; (e) Toggle "Modo agressivo" para também sobrescrever system_prompts dos agentes. Todas mudanças criam backup em `edit_history` (rollback disponível). Testing Agent iteration_147: Backend 18/18 + Frontend 100% ✅.

## Test Credentials
- Email: test@studiox.com / Password: studiox123
- Project JONAS E O PEIXE GRANDE: 1f26f1649bcf (32 scenes, COMPLETE)
- Project Pulmeranea 2: ae9c7307ac53

## Active Projects
- **JONAS E O PEIXE GRANDE** (1f26f1649bcf): 32 scenes, all videos generated, final movie concatenated with V2A sonoplastia. Status: COMPLETE
- **Jonas e a Baleia** (fd7e965d42f8): 35 scenes, 0 videos generated

## 🎬 Current Focus
**Vídeos perfeitos** — toda a trilha de produção de vídeo é prioridade máxima (Sora 2 Pro + Nano Banana Pro + Cinema FFmpeg + Voice Consistency + Multi-Format Export).

## 📚 Books Track — PAUSED
Trilha de livros está em **manutenção**, não está sendo evoluída no momento.
Features continuam em produção (BookFactory, Quality Gate, BookEditorPage, Mary Blair + Glen Keane), mas **backlog de melhorias foi capturado em `/app/memory/BOOKS_BACKLOG.md`** com 15 itens identificados durante análise em tempo real (23/04/2026) do livro "Manual do Pulmeranea" (33 spreads, score 85/90).

**Principais itens a retomar depois** (ver BOOKS_BACKLOG.md para detalhes):
- P0: CMYK automático via ghostscript (hoje é warning, precisa ser step do pipeline)
- P0: Integrar Glen Keane Auditor ao fim do pipeline (hoje só é disponível via endpoint manual)
- P0: Popular `book_state.thumbnails` automaticamente
- P1: Live feedback com ActiveAgentIndicator durante geração do livro
- P1: Retry por spread (regerar UMA ilustração sem refazer livro todo — 10s vs 6min)
- P1: Quality Gate configurável por projeto + botão "Forçar aprovação"
- P1: Validar fluxo BookEditorPage end-to-end com livro real
- P2: Integração KDP/Lulu print-on-demand
- P3: Refactor arquitetural do `book_factory.py` (2933 linhas) + paralelização asyncio.gather

## Backlog
- P0 (non-blocking, observed): Backend worker saturation when video pipeline runs — `time.sleep` + sync `videos.retrieve` in Sora polling can queue requests. Production runs in thread pool so it's mitigated, but worth migrating to `asyncio.sleep` + `asyncio.to_thread()` for cleaner multiplexing.
- P1: Personality field UI (textarea in character editor)
- P1: BookFactory — implement REAL RAG in `/app/backend/core/bible_rag.py` (currently mock). Use ChromaDB or Supabase pgvector to ingest public-domain reference texts.
- P2: Custom Video Editor UI (timeline)
- P2: Modularize DirectedStudio.jsx Fase 2 — ainda ~4606 linhas após Fase 1. Próximo passo opcional: extrair render blocks dos steps 0-7 em subcomponentes (exige DirectedStudioContext para evitar prop drilling de ~100+ states).
- P2: Multi-format export
- P2: BookFactory → KDP/Lulu API integration for print-on-demand publishing
- P2: Cleanup 218 silent `except: pass` blocks in /app/backend/routers/
- P3: Voice selection UI per character
- P3: WebSocket for real-time progress
