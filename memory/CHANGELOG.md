# StudioX Changelog

## 2026-04-18 → 2026-04-19 (Session 4 — BookFactory MVP)

### BookFactory — Pipeline Paralela de Livros Físicos (NEW)

**Objetivo**: Criar uma segunda pipeline ao lado do gerador de vídeos para produzir **livros físicos prontos para impressão** (PDF com sangria, fontes embutidas, layout profissional), reusando a Character Universe, Project Bible e agentes já existentes do StudioX.

**Decisões arquiteturais aprovadas pelo usuário**:
- Motor de diagramação: **WeasyPrint** (Python puro, CSS Paged Media) — descartado LaTeX por limitação de disco (2.2 GB livres vs ~1.5 GB do TeX Live)
- RAG: **stub in-memory** com interface pronta (Bíblia + Machado de Assis) — ChromaDB/pgvector em Fase 2
- 3 formatos via templates: **6×9** (infantil/romance), **5×8** (romance), **A4** (técnico/histórico) + A5 bonus
- Universo compartilhado: usuário escolhe no briefing entre `book` | `video` | `both` (meeting room adaptativa)
- Branding: **BookFactory**

**O que foi implementado**:

1. **8 novos agent specs** em `/app/memory/agents/book/`:
   - `author_agent` (Autor Profissional)
   - `art_director_editorial_agent`
   - `illustrator_interior_agent`
   - `cover_designer_agent`
   - `book_editor_agent` (consistência narrativa)
   - `proofreader_agent`
   - `layout_designer_agent` (decide tipografia/grid)
   - `preflight_agent` (valida PDF final)

2. **Meeting Room adaptativa**: `agent_compositions.json` com 7 composições dinâmicas resolvidas por `(output_mode, format_preset, autoria_mode)`. Modo `video_only` preservado idêntico ao fluxo atual.

3. **Novo módulo backend**: `/app/backend/routers/studio/book_factory.py` (~540 linhas) com 10 endpoints sob `/api/studio/`:
   - `GET /book/trim-sizes`, `GET /book/compositions`
   - `POST /projects/{id}/book/start` (grava brief + resolve composition)
   - `POST /book/generate-outline` (Autor — Claude)
   - `POST /book/approve-outline`
   - `POST /book/generate-chapter` (Autor — Claude, com continuidade)
   - `POST /book/plan-illustrations` (Art Director)
   - `POST /book/generate-illustration` (Ilustrador — Gemini 3 Image com character refs)
   - `POST /book/generate-cover-v2` (Designer de Capa, calcula lombada pelo page count)
   - `POST /book/proofread` (Revisor)
   - `POST /book/render-pdf` (Diagramador + WeasyPrint)
   - `POST /book/preflight` (Preflight Agent — pypdf)
   - `GET /book/state`

4. **Template Jinja2 + CSS Paged Media** em `/app/backend/templates/book/book_base.html.j2`:
   - `@page` com `bleed: 3mm` e `marks: crop cross`
   - Running headers, footer com número de página
   - Drop cap (opcional por preset)
   - Capítulo começa em página ímpar (recto) quando preset pede
   - `widows: 3, orphans: 3, hyphens: auto, text-align: justify`
   - 3 presets: infantil_ilustrado / romance_adulto / tecnico_historico

5. **RAG stub**: classe `_RAGStub` com API idêntica a um retriever real (`.search(query, top_k)`). Interface pronta para trocar por ChromaDB/pgvector sem mexer no resto.

6. **LLM integration**: usa o pattern oficial do projeto — `_call_claude_async` em `_shared.py` (litellm + `anthropic/claude-sonnet-4-5-20250929`). Migrei de `emergentintegrations.LlmChat` (que tem bug reportado pelo testing agent) para o padrão que já funciona no pipeline de vídeo.

**Testing**:
- Testing Agent v3 rodou 26 testes (21 passaram, 5 bloqueados pelo bug da emergentintegrations).
- Depois de migrar para `_call_claude_async`, rodei **fluxo end-to-end real** via curl: criou livro "A Raposinha Generosa" com 8 capítulos, escreveu capítulo 1 em português (200 palavras), renderizou PDF de 17KB, preflight passou com 0 blockers.
- Backward compat: pipeline de vídeo 100% preservado (endpoints antigos continuam funcionando).

**Pendente para próxima sessão** (UI):
- Componente `BookStudio.jsx` (nova rota `/studio/book/:id`)
- Page-flip preview com PDF.js
- Editor de outline inline (drag-reorder de capítulos)
- Preview de ilustrações por página
- Botão unificado "Criar Livro" na home do Studio X

**Fase 2 (roadmap)**:
- Substituir RAG stub por ChromaDB com ingestão real (Bíblia PT, Gutenberg)
- Pós-processamento CMYK + PDF/X via ghostscript
- Integração Amazon KDP, Uiclap, Lulu APIs
- Book+Video paralelo (Universe Bible bifurcando)
- Multi-language (EN/ES no template)


## 2026-04-18 (Session 4 — continuação)

### Video Quality Upgrade — Sprints P0+P1 completos
**Problema identificado**: Prompts Sora 2 estavam 10x maiores que o recomendado pelo guia oficial OpenAI 2026 (>5000 chars, guia pede <150 palavras). Sora ignorava silenciosamente metade do prompt.

**Implementado**:

1. **Toggle Production Quality** (`fast` vs `cinema`)
   - Campo novo `production_quality` em `StudioProject` (default `fast` para backward compat).
   - UI: radio no modal de novo projeto (só aparece quando `videoEngine=sora`). Badge visual "⚡ Rápida" vs "🎬 Cinema".
   - `fast`: Sora 2 @ 1280×720, prompt legacy (longo), FFmpeg CRF 23 / AAC 128k — comportamento anterior.
   - `cinema`: Sora 2 Pro @ 1792×1024 HD, prompt compacto (<200 palavras) cinema-style, FFmpeg CRF 18 / preset medium / AAC 256k.

2. **Prompt Sora cinema-style (P0)**
   - Prompt novo em formato `[SHOT] / [ACTION] / [DIALOGUE] / [STYLE] / [VOICES] / [TEXT]`.
   - Identidade visual movida integralmente para o `input_reference` (keyframe Gemini).
   - Só ativa quando `production_quality=cinema`. Modo `fast` mantém o prompt longo original.

3. **Sora 2 Pro @ 1792×1024 (P0)**
   - `_generate_video_with_openai_direct` e `_generate_video_unified` agora aceitam `model` e `sora_model` parâmetros.
   - Auto-seleciona `sora-2-pro` + `1792x1024` quando `production_quality=cinema`.

4. **Gemini 3 Pro Image (Nano Banana Pro) via env var (P0)**
   - `core/llm.py` agora lê `GEMINI_IMAGE_MODEL` (default `gemini-2.5-flash-image`).
   - Para ativar consistência de personagens top-tier, basta setar `GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview` no `.env`.

5. **FFmpeg cinema preset (P1)**
   - `_concatenate_videos` agora aceita `cinema_quality: bool`.
   - Cinema: `-crf 18 -preset medium -c:a aac -b:a 256k -pix_fmt yuv420p`.

6. **Emotion markers no diálogo (P1)**
   - `dialogue_timeline` beats agora suportam campo opcional `emotion` que é injetado como `[whispers]`, `[laughing]`, `[tense]` etc. no prompt Sora.

**Backward compatibility**: Todas as mudanças são condicionais. Projetos existentes sem `production_quality` rodam em modo `fast` e se comportam exatamente como antes.

**Testing**: 13/13 testes backend passaram via testing_agent_v3_fork (iteration_136.json).


## 2026-04-18 (Session 4)

### Sora 2 Character Voice Lock (NEW)
- **Problem**: Sora 2 generates a different voice for each scene even for the same character (stochastic sampling).
- **Solution**: Integrated OpenAI's official Sora 2 Characters API (`POST /v1/sora/characters`) that creates a reusable `character_id` from an anchor scene. Reusing the ID in subsequent generations locks **voice + appearance** natively.
- New module: `/app/backend/routers/studio/sora_characters.py`
- Auto-detects first rendered scene per character to use as voice anchor.
- Supports Sora 2 2-character-per-generation limit (March 2026).
- Endpoints:
  - `POST /api/studio/projects/{id}/auto-register-sora-characters` (auto, idempotent)
  - `POST /api/studio/projects/{id}/register-sora-character` (manual with specific scene)
  - `GET  /api/studio/projects/{id}/sora-characters`
  - `DELETE /api/studio/projects/{id}/sora-characters/{character_name}`
- `production.py`: `_generate_video_with_openai_direct` and `_generate_video_unified` accept optional `sora_character_ids`. Character lookup is per-scene from `project.characters[].sora_character_id`.
- **Backward compatible**: zero impact on existing/in-flight projects (fallback is empty list → payload identical to before).
- UI: "🎤 Travar Vozes" button on the Vídeos tab of `DirectedStudio.jsx` + badge showing locked characters count.


## 2026-04-17 (Session 3)

### ElevenLabs Music - Children's Song Generator
- Integrated ElevenLabs Music API (`client.music.compose()`) for generating original children's songs
- LLM (Claude) generates lyrics based on story briefing + scenes + characters
- Music style adapts to age range: 0-3 (lullaby), 3-5 (Galinha Pintadinha), 5-8 (Disney Junior), 8-12 (Disney/Pixar)
- Lyrics in project language (Portuguese by default)
- Endpoint: `POST /api/studio/projects/{id}/generate-music`
- UI card "Música Cantada" added to RESULTADO tab with lyrics display
- Song saved to project as `generated_song` field

### Film Rebuild for Large Projects
- Fixed: Previous rebuild of 26 scenes crashed silently (FFmpeg crossfade memory exhaustion)
- Reduced crossfade scene limit: 30 → 15 scenes
- V2A sonoplastia now non-blocking in rebuild
- Successfully rebuilt "Jonas e o Peixe Grande" (32 scenes, 276MB → 17MB)

### Folder System Improvements
- Fixed: Delete folder button not working (replaced `window.confirm` with inline two-click)
- Fixed: Stale avatar IDs auto-cleanup was deleting valid avatars (REMOVED auto-cleanup)
- Hierarchical folders: parent_id support with expand/collapse (no modal reload)
- Compact sidebar: smaller fonts, narrower width
- Chevron arrow moved after folder name for alignment
- `useTransition` for smooth folder switching (no flash)
- New endpoint: `PUT /api/folders/bulk-update` for atomic folder operations
- New endpoint: `PUT /api/folders/update-avatars` for replacing folder avatar IDs

### Audio Pipeline Upgraded (Sora 2)
- Primary: ElevenLabs Music generates original soundtrack matching story
- Fallback: Kling V2A for BGM + SFX if ElevenLabs fails
- Mix: native Sora 2 audio (100%) + music (15% volume)

## 2026-04-15 (Session 2)
[... previous entries unchanged ...]
