# StudioX Changelog

## 2026-04-19 (Session 5 — Bugfix: Pipeline + Cover + UI chapter-flow + Download proxy + Regerar ilustrações)

### Fix 5: Regerar ilustração individual no fluxo chapter + prompt reforçado
**Problema do usuário:** Algumas ilustrações saíam fora do padrão Pixar 3D (pg.6 cartoon bichinho, pg.10 vector flat, pg.13 múltiplos cachorros random). Não havia botão para regenerar individualmente no fluxo chapter.

**Fix Backend (`book_generate_illustration`):**
- Agora sempre passa **todos os personagens do projeto** (até 5) como refs multimodais (prioriza `characters_in_page`), não só os na cena.
- Inclui `char_descriptions` no prompt com nome + descrição curta de cada personagem.
- Prompt reescrito com regras HARD: "NO LETTERS", "NO extra characters/dogs", "DO NOT switch art style" (explicita que não pode mudar de 3D Pixar pra flat/cartoon/pixel).
- Reforço do `style_rules` + `palette` do Art Director como obrigatórios.

**Fix Frontend (`BookStudio.jsx`):**
- No grid do fluxo chapter, cada card de ilustração agora tem 2 botões:
  - 🔄 **Regerar** — usa o plano original (rápido, corrige drift).
  - ✨ **Custom** — abre prompt para o usuário escrever instruções extras (estilo, personagens, excluir elementos).
- Botão **Regerar todas** no header (para refazer o lote inteiro após ajustar Art Director).
- Pré-preenche o prompt Custom com um template pronto sobre estilo Pixar 3D + Ash/Snow, que o usuário pode editar.
- Banner de dica roxo explicando o uso do botão Custom.

**Validação:** pg.6 regerada — saiu de cartoon flat para Pixar 3D com volumetric lighting, soft shadows, detailed fur, Ash corretamente identificado por tag.



### Fix 3: PDF download bloqueado (`ERR_BLOCKED_BY_CLIENT`)
**Bug:** O botão "Baixar PDF" apontava direto para o domínio `*.supabase.co`. Ad-blockers do usuário (uBlock/Chrome) bloqueiam esse domínio → download falha silenciosamente.

**Fix:**
- Novo endpoint `GET /api/studio/projects/{id}/book/download-pdf` (`book_factory.py`): faz stream do PDF pelo domínio da própria app com `Content-Disposition: attachment; filename="{título}.pdf"`.
- Frontend (`BookStudio.jsx`): nova função `downloadPdf()` faz fetch com auth + blob + click sintético. Botão "Baixar PDF" agora usa proxy. "Abrir em nova aba" ainda mantém link direto como fallback.

**Validação:** Curl do proxy retornou HTTP 200, 12.4 MB, `Content-Disposition: attachment`, PDF válido 64 páginas.

### Fix 4: UI BookStudio em branco no fluxo chapter (`infantil_ilustrado`)
**Bug:** Outline, Ilustrações e Render tinham layout exclusivo para `spreads` do picturebook. No fluxo chapter, `spreads` é sempre vazio → painéis mostravam zero conteúdo mesmo com 8 capítulos escritos e 16 ilustrações geradas.

**Fix em `BookStudio.jsx`:**
- Detecta `formatPreset` via `bookState.brief.format_preset` e flag `isPicturebook`.
- Outline panel: quando chapter flow, renderiza `outlineChapters` com badge "✓ N palavras" (verde) ou "pendente" (cinza) + accordion `<details>` mostrando a prosa escrita (`chapters[idx].prose`).
- Ilustrações panel: quando chapter flow, renderiza `illustration_plan` (grid com `pg.N • Cap X • tipo`).
- `renderPDF()` agora escolhe endpoint: `render-picturebook` para picturebook ou `render-pdf` para chapter flow.
- `loadState` detecta step correto em ambos os fluxos (verifica `illustration_plan[].illustration_url` além de `spreads[].illustration_url`).

**Validação visual:** Página do projeto Ash (`017f57ef8ecd`) mostra título "Cuidando do Meu Pulmerânea: Dicas do Ash", blurb mencionando Ash/Snow/Brenda, todos os 8 capítulos com word counts (664, 644, 645, 703, 674, 614, 716, 714), 16 ilustrações em grid com Ash cinza + Snow branco + Brenda visíveis.



### Fix 1: Auto-Run Pipeline falhava em `format_preset != 'picturebook'`
**Bug:** Projeto "Manual do Pulmeranea" (Ash, `infantil_ilustrado`) falhava com `400: No spreads to render` porque o background task `_run_book_pipeline_background` assumia sempre fluxo picturebook (spreads → `render-picturebook`), mas `generate-outline` só salva `spreads` quando `format_preset == "picturebook"`. Para outros formatos gera `chapters`.

**Fix:** `_run_book_pipeline_background` agora detecta `format_preset` e roteia:
- `picturebook` → outline (spreads) → art-direct → meeting-room → illustrate-spreads → cover → `render-picturebook` → preflight
- `infantil_ilustrado` / `romance_adulto` / `tecnico_historico` → outline (chapters) → art-direct → generate-chapter (loop) → plan-illustrations → generate-illustration (loop) → cover → `render-pdf` → preflight

`pipeline_error` e `pipeline_finished_at` agora são resetados ao iniciar nova corrida.

**Validação E2E (projeto `017f57ef8ecd`):** 8 capítulos escritos, 16 ilustrações geradas, capa gerada, PDF 64 páginas renderizado, preflight passou. Pipeline `step=done` com sucesso.

### Fix 2: Capa cortada lateralmente (Snow desaparecendo)
**Bug:** Gemini 3 Image retorna PNG `1024×1024` (aspect 1.0), mas trim 6×9 + bleed é `158.4×234.6 mm` (aspect 0.675 — portrait). Template usa `background-size: cover`, que força o preenchimento do container portrait escalando a imagem quadrada até `234.6×234.6 mm` — cortando ~15% de cada lado. Personagens nas laterais (Snow na capa do Ash) sumiam.

**Fix:** Em `book_generate_cover_v2`, **após** o Gemini, a imagem é padded server-side via PIL para o aspect exato do trim+bleed. Cor de fundo = `palette.primary` (extraída pela Art Director). O resultado (1024×1517 para 6×9) bate perfeitamente com o container do template — zero crop.

**Validação visual:** Capa do Ash regenerada — Ash + Shadow (cinza) + Snow (branco) todos totalmente visíveis e centrados. Confirmado por análise de imagem.

### Arquivos alterados
- `/app/backend/routers/studio/book_factory.py` (pad aspect + branching + reset flags)

---


## 2026-04-19 (Session 4 — BookFactory P0+P1 completo)

### P0 — UI BookStudio (nova rota `/studio/book/:projectId`)
Nova página React (`/app/frontend/src/pages/BookStudio.jsx`, ~560 linhas) com wizard de 7 passos navegável:

1. **Briefing** — formulário com todos os campos (name, title, author, idioma, briefing, format picturebook/chapter/romance/técnico, trim 6x9/5x8/A4/A5, target_spreads, audience, visual track, modo autoria, herdar personagens de outro projeto via `source_project_id`, reference_work quando public_domain).
2. **Outline** — exibe title, subtitle, blurb, badges dos RAG sources (Bíblia), lista de spreads com texto + scene description + characters + botão rewrite individual.
3. **Arte** — editor visual de tema: inputs de fonte (título e corpo), tamanho pt, 5 color pickers ao vivo (page_bg, text_box_bg, title_color, body_color, accent) + preview da fonte renderizado na hora. PATCH direto para `/book/theme`.
4. **Revisão (Meeting Room)** — mostra consistency_score em destaque, overall_assessment, lista colorida de issues por severity (critical vermelho, major âmbar, minor cinza), botão "Aplicar fixes críticos".
5. **Ilustrações** — grid responsivo com thumbnails, botão "Gerar todas faltantes" em lote, botão regenerar por spread.
6. **Capa** — preview com overlay de título + lombada calculada, botões regenerar e "Renderizar PDF final".
7. **PDF** — tela "Livro Pronto!" com page_count, preflight status verde/amber, botão Baixar PDF.

Auto-detecta o passo correto ao carregar projeto existente (usa `pdf_url`, `cover`, spreads com `illustration_url`, `meeting_room_review`, `theme`, `outline` pra decidir).

Botão "📖 Livro" adicionado no header do `StudioPage.jsx` com `data-testid="nav-bookfactory"`.

### P1 — Extensões backend

**Novas composições no `agent_compositions.json`**:
- `book_picturebook_user_author`
- `book_picturebook_public_domain` (lidera com Pesquisador + RAG)
- `book_picturebook_free` (lidera com Art Director)

**Novos endpoints em `book_factory.py`**:
- `PATCH /api/studio/projects/{id}/book/theme` — merge partial de theme/palette/style_rules; permite UI editar fontes/cores.
- `POST /book/rewrite-spread` — Author Agent reescreve UM spread via Claude preservando `illustration_url`.
- `POST /book/apply-review-fixes` — varre `meeting_room_review.issues` e auto-aplica critical/major via rewrite-spread; retorna `{applied, skipped, total_applied}`.

### Testing
- Testing agent iteration 138: **18/20 backend (90%) + 100% frontend UI verificada**.
- 2 issues minor: intermittent 500 em criação rápida (Supabase race) + React warning de `<span>` dentro de `<option>` — ambos LOW priority.
- Smoke test visual via Playwright: tela de briefing + tela de render carregam corretamente no preview environment.

### Arquitetura agora
Agentes **ativos** no fluxo picturebook: Orchestrator + Author + Art Director Editorial + Illustrator Interior + Cover Designer + Book Editor + Proofreader + Layout Designer + Preflight (8 agentes). Meeting Room em loop de debate simples via Editor review + apply-fixes. RAG Bíblia PT-BR com 5 passagens ARA (Gênesis 12, 21, 22 + Hebreus 11).


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
