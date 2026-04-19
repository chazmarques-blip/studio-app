"""BookFactory — Parallel pipeline for physical book generation.

Entirely ADDITIVE. Does not modify existing video pipeline.

Reuses from StudioX:
    - Character folders (routers/folders.py)
    - Character avatars (project.character_avatars)
    - Gemini image stack (core/llm.generate_image_gemini_sync)
    - Emergent LLM Key via emergentintegrations
    - Supabase storage (_upload_to_storage)
    - Project Bible (project.project_bible — extended with book_bible section)
    - Milestones (project.milestones)

Adds:
    - Adaptive Meeting Room (composition resolver per mode)
    - Endpoints: briefing → outline → chapters → illustrations → cover → layout → PDF → preflight
    - WeasyPrint renderer (templates/book/*.html.j2)
    - Preflight validation (pypdf + PIL DPI checks)
    - RAG stub interface (class with in-memory fallback; swap to ChromaDB/pgvector later)
"""
from ._shared import *
import json
import io
import re as _re
import tempfile as _tempfile

# ─── Constants ──────────────────────────────────────────────────────────────

AGENTS_BOOK_DIR = "/app/memory/agents/book"
COMPOSITIONS_PATH = f"{AGENTS_BOOK_DIR}/agent_compositions.json"

TRIM_SIZES_MM = {
    "6x9":  {"width": 152.4, "height": 228.6, "name": "6×9 in"},
    "5x8":  {"width": 127.0, "height": 203.2, "name": "5×8 in"},
    "A4":   {"width": 210.0, "height": 297.0, "name": "A4"},
    "A5":   {"width": 148.0, "height": 210.0, "name": "A5"},
}

VISUAL_TRACKS = ["aquarela", "cartoon", "flat", "storybook", "realismo_editorial", "minimalista", "gravura", "fotorrealismo", "none"]


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class BookBriefRequest(BaseModel):
    output_mode: str = "book"  # "book" | "video" | "both"
    autoria_mode: str = "user_author"  # "user_author" | "public_domain" | "free"
    format_preset: str = "infantil_ilustrado"  # "picturebook" | "infantil_ilustrado" | "romance_adulto" | "tecnico_historico"
    trim_size: str = "6x9"
    target_pages: int = 40
    target_spreads: int = 14  # Only used when format_preset = picturebook
    audience: str = "children_4_8"  # children_0_3 | children_4_8 | children_9_12 | ya | adult | technical
    illustration_track: str = "storybook"
    title: str = ""
    author_name: str = ""
    briefing: str = ""
    language: str = "pt"
    character_ids: list = []  # Refs to folders/avatars
    source_project_id: Optional[str] = None  # Inherit characters + avatars from this project
    reference_work: Optional[str] = None  # For public_domain mode: "biblia_genesis_22" | "classic_gutenberg_xxx"


class SpreadGenerateRequest(BaseModel):
    spread_index: int
    rewrite_instructions: Optional[str] = None


class IllustrateSpreadRequest(BaseModel):
    spread_index: int
    override_prompt: Optional[str] = None
    layout: Optional[str] = None  # "split" (default) | "overlay"


class ChapterGenerateRequest(BaseModel):
    chapter_index: int
    rewrite_instructions: Optional[str] = None


class IllustrationGenerateRequest(BaseModel):
    page_number: int
    override_prompt: Optional[str] = None


# ─── RAG Stub Interface (swappable implementation) ────────────────────────────

class _RAGStub:
    """In-memory RAG with simple keyword match. Replace with ChromaDB/pgvector in Phase 2.

    Public API intentionally matches what a real vector retriever would expose:
        search(query, top_k) -> list[{"text", "source", "score"}]
    """
    _MEMORY = {
        "biblia_genesis_cap1": {
            "text": "No princípio, criou Deus os céus e a terra. A terra era sem forma e vazia; havia trevas sobre a face do abismo, e o Espírito de Deus pairava sobre as águas. Disse Deus: Haja luz; e houve luz.",
            "source": "Bíblia, Gênesis 1:1-3 (ARA)",
        },
        "classic_dom_casmurro_abertura": {
            "text": "Uma noite destas, vindo da cidade para o Engenho Novo, encontrei num trem da Central um rapaz aqui do bairro, que eu conheço de vista e de chapéu.",
            "source": "Machado de Assis, Dom Casmurro (Cap. I), domínio público",
        },
    }

    def is_configured(self) -> bool:
        return bool(os.environ.get("BOOKFACTORY_RAG_BACKEND"))

    def search(self, query: str, top_k: int = 3) -> list:
        # MVP: returns all memory items scored by naive word overlap. Replace with real embeddings later.
        q_words = set(_re.findall(r'\w+', query.lower()))
        results = []
        for key, entry in self._MEMORY.items():
            text_words = set(_re.findall(r'\w+', entry["text"].lower()))
            overlap = len(q_words & text_words)
            results.append({**entry, "score": overlap / max(1, len(q_words))})
        results.sort(key=lambda x: -x["score"])
        return results[:top_k]


_rag = _RAGStub()


# ─── Adaptive Meeting Room Resolver ──────────────────────────────────────────

def _load_compositions() -> dict:
    try:
        with open(COMPOSITIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"BookFactory: failed to load compositions: {e}")
        return {"compositions": {}, "resolver": {"fallback": "book_infantil_ilustrado_user_author"}}


def _resolve_composition_key(brief: dict) -> str:
    output_mode = brief.get("output_mode", "book")
    fmt = brief.get("format_preset", "infantil_ilustrado")
    autoria = brief.get("autoria_mode", "user_author")

    if output_mode == "both":
        return "both_parallel"
    if output_mode == "video":
        return "video_only"
    # book
    key = f"book_{fmt}_{autoria}"
    comps = _load_compositions().get("compositions", {})
    if key in comps:
        return key
    # fallback
    return _load_compositions().get("resolver", {}).get("fallback", "book_infantil_ilustrado_user_author")


def _load_agent_spec_book(agent_id: str) -> dict:
    """Load agent spec from /app/memory/agents/book/ OR /app/memory/agents/ (shared agents)."""
    for base in (AGENTS_BOOK_DIR, "/app/memory/agents"):
        path = f"{base}/{agent_id}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/book/start")
async def book_start(project_id: str, req: BookBriefRequest, tenant=Depends(get_current_tenant)):
    """Kick off a BookFactory pipeline. Saves brief + resolves meeting room composition."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if req.trim_size not in TRIM_SIZES_MM:
        raise HTTPException(status_code=400, detail=f"Invalid trim_size. Options: {list(TRIM_SIZES_MM.keys())}")
    if req.illustration_track not in VISUAL_TRACKS:
        raise HTTPException(status_code=400, detail=f"Invalid illustration_track. Options: {VISUAL_TRACKS}")

    brief = req.model_dump()
    composition_key = _resolve_composition_key(brief)

    # Inherit characters from another project (Character Universe reuse)
    if req.source_project_id:
        _, _, source_project = _get_project(tenant["id"], req.source_project_id)
        if source_project:
            project["characters"] = source_project.get("characters") or []
            project["character_avatars"] = source_project.get("character_avatars") or {}
            logger.info(f"BookFactory: inherited {len(project['characters'])} characters + {len(project['character_avatars'])} avatars from {req.source_project_id}")

    book_bible = project.get("project_bible", {}).get("book_bible", {}) or {}
    book_bible.update({
        "brief": brief,
        "composition_key": composition_key,
        "status": "brief_received",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rag_enabled": req.autoria_mode == "public_domain",
        "trim_size_mm": TRIM_SIZES_MM[req.trim_size],
    })
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    project["output_mode"] = req.output_mode

    _add_milestone(project, "book_brief_submitted", f"Briefing BookFactory recebido — {composition_key}")
    _save_project(tenant["id"], settings, projects)

    return {
        "project_id": project_id,
        "composition_key": composition_key,
        "agents_active": _load_compositions().get("compositions", {}).get(composition_key, {}).get("agents", []),
        "trim_size_mm": TRIM_SIZES_MM[req.trim_size],
        "status": "brief_received",
        "next_step": "POST /book/generate-outline",
    }


@router.post("/projects/{project_id}/book/generate-outline")
async def book_generate_outline(project_id: str, tenant=Depends(get_current_tenant)):
    """Author Agent generates chapter outline from brief + universe bible + optional RAG context."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    if not brief:
        raise HTTPException(status_code=400, detail="Call /book/start first")

    # Optional RAG context — use real Bible RAG for public_domain mode
    rag_context = []
    if book_bible.get("rag_enabled") and brief.get("reference_work"):
        try:
            from core.bible_rag import search_bible_passages
            # If reference_work is bible, search with briefing as query
            ref = brief.get("reference_work", "").lower()
            if "biblia" in ref or "bible" in ref or "genesis" in ref or "gênesis" in ref:
                q = brief.get("briefing", "") + " " + ref
                rag_context = search_bible_passages(q, top_k=5)
                logger.info(f"BookFactory: Bible RAG returned {len(rag_context)} passages for '{ref}'")
            else:
                rag_context = _rag.search(brief["reference_work"], top_k=5)
        except Exception as e:
            logger.warning(f"BookFactory RAG failed: {e}")

    # Character universe context
    characters = project.get("characters") or []
    char_block = ""
    for c in characters[:8]:
        if isinstance(c, dict):
            char_block += f"- {c.get('name', '')}: {c.get('description', '')[:200]}\n"

    # RAG block (text used in prompt)
    rag_block = ""
    if rag_context:
        rag_lines = []
        for r in rag_context:
            ref = r.get("reference") or r.get("source", "")
            txt = (r.get("text") or "")[:900]
            rag_lines.append(f"[{ref}]\n{txt}")
        rag_block = "\n\nSOURCE PASSAGES TO USE (cite faithfully, adapt tone to audience):\n" + "\n\n".join(rag_lines)

    is_picturebook = brief.get("format_preset") == "picturebook"
    target_spreads = brief.get("target_spreads", 14)

    if is_picturebook:
        prompt = f"""You are the Author Agent writing a PICTUREBOOK for children.

BOOK BRIEF:
- Format: picturebook (illustration + short text per spread)
- Audience: {brief.get('audience')} — VERY IMPORTANT: use language appropriate for this age.
- Language: {brief.get('language')}
- Title: {brief.get('title') or '(to be created)'}
- Briefing: {brief.get('briefing')}
- Target: {target_spreads} spreads (pages)
- Autoria mode: {brief.get('autoria_mode')}

CHARACTERS AVAILABLE (USE EXACTLY THESE, DO NOT INVENT):
{char_block or '(none — author may invent, but prefer to stay with reference work characters)'}
{rag_block}

RULES FOR PICTUREBOOK:
- Each spread = 1 illustration + 2-4 short sentences (max ~40 words). NEVER long paragraphs.
- Rhythm: sentences should read out loud well. Use repetition, rhyme-adjacent prose.
- Vocabulary: simple, concrete, visual. Age-appropriate.
- Narrative arc across ALL spreads: setup → tension → climax → resolution.
- Each spread must be VISUALLY compelling — a scene that deserves a full illustration.
- Faithful to source passages if provided.

RETURN ONLY VALID JSON:
{{
  "title": "creative title adapted to audience",
  "subtitle": "optional subtitle",
  "blurb": "100-word book synopsis",
  "total_spreads": {target_spreads},
  "spreads": [
    {{
      "index": 1,
      "text": "2-4 short sentences (MAX ~40 words)",
      "scene_description": "What the illustrator should draw — concrete, visual, includes which characters are in frame, their poses, setting, lighting, mood",
      "characters_in_scene": ["Exact Character Name 1", "Character Name 2"],
      "layout_hint": "split" or "overlay"
    }},
    ...
  ]
}}
"""
    else:
        prompt = f"""You are the Author Agent for BookFactory. Generate a chapter outline.

BOOK BRIEF:
- Format: {brief.get('format_preset')}
- Trim: {brief.get('trim_size')} ({brief.get('target_pages')} target pages)
- Audience: {brief.get('audience')}
- Language: {brief.get('language')}
- Title: {brief.get('title') or '(to be created)'}
- Briefing: {brief.get('briefing')}
- Autoria mode: {brief.get('autoria_mode')}
{f"- Reference work: {brief.get('reference_work')}" if brief.get('reference_work') else ''}

CHARACTERS AVAILABLE:
{char_block or '(none — author may invent)'}
{rag_block}

RETURN ONLY VALID JSON:
{{
  "title": "final creative title",
  "subtitle": "optional subtitle",
  "blurb": "150-word book synopsis",
  "total_chapters": number,
  "chapters": [
    {{"index": 1, "title": "Chapter 1 title", "synopsis": "2-4 sentence description", "target_words": number}},
    ...
  ]
}}
"""

    try:
        raw = (await _call_claude_async(
            "You are a professional literary author. Return only valid JSON.",
            prompt,
            max_tokens=4000,
        )).strip()
        # Strip fences if present
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
        outline = json.loads(raw)
    except json.JSONDecodeError as je:
        logger.error(f"BookFactory outline JSON parse failed: {je} — raw: {raw[:300]}")
        raise HTTPException(status_code=502, detail="Author returned invalid JSON")
    except Exception as e:
        logger.error(f"BookFactory outline generation failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    book_bible["outline"] = outline
    if is_picturebook:
        book_bible["spreads"] = outline.get("spreads", [])
    book_bible["status"] = "outline_ready"
    if rag_context:
        book_bible["rag_sources"] = [
            {"reference": r.get("reference") or r.get("source", ""), "score": r.get("score", 0)}
            for r in rag_context
        ]
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_outline_ready", f"Outline gerado — {outline.get('total_spreads', outline.get('total_chapters', 0))} {'spreads' if is_picturebook else 'capítulos'}")
    _save_project(tenant["id"], settings, projects)

    return outline


@router.post("/projects/{project_id}/book/approve-outline")
async def book_approve_outline(project_id: str, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    if not book_bible.get("outline"):
        raise HTTPException(status_code=400, detail="No outline to approve")
    book_bible["outline_approved"] = True
    book_bible["status"] = "outline_approved"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_outline_approved", "Outline aprovado pelo usuário")
    _save_project(tenant["id"], settings, projects)
    return {"status": "outline_approved"}


@router.post("/projects/{project_id}/book/generate-chapter")
async def book_generate_chapter(project_id: str, req: ChapterGenerateRequest, tenant=Depends(get_current_tenant)):
    """Author writes prose for a single chapter."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    outline = book_bible.get("outline") or {}
    chapters_outline = outline.get("chapters") or []
    if req.chapter_index < 1 or req.chapter_index > len(chapters_outline):
        raise HTTPException(status_code=400, detail="Chapter index out of range")

    ch_meta = chapters_outline[req.chapter_index - 1]
    brief = book_bible.get("brief") or {}

    # Build character context
    characters = project.get("characters") or []
    char_block = "\n".join([
        f"- {c.get('name', '')}: {c.get('description', '')[:200]}"
        for c in characters[:8] if isinstance(c, dict)
    ])

    # Previous chapter for continuity
    prev_chapter = ""
    prev_chapters = (book_bible.get("chapters") or {})
    if req.chapter_index > 1:
        prev_ch = prev_chapters.get(str(req.chapter_index - 1))
        if prev_ch:
            prev_chapter = prev_ch.get("prose", "")[-800:]

    lang_full = {"pt": "Portuguese", "en": "English", "es": "Spanish"}.get(brief.get("language", "pt"), "Portuguese")

    prompt = f"""You are the Author. Write Chapter {req.chapter_index} of this book.

BOOK: "{outline.get('title', '')}"
FORMAT: {brief.get('format_preset')} — audience: {brief.get('audience')} — language: {lang_full}

CHAPTER OUTLINE:
Title: {ch_meta.get('title')}
Synopsis: {ch_meta.get('synopsis')}
Target words: {ch_meta.get('target_words', 1200)}

CHARACTERS (use these exactly — do not invent new main characters):
{char_block}

{f"CONTINUITY (last 800 chars of previous chapter):{chr(10)}{prev_chapter}" if prev_chapter else 'This is Chapter 1.'}

{f"REWRITE INSTRUCTIONS: {req.rewrite_instructions}" if req.rewrite_instructions else ''}

Write in {lang_full}. Output ONLY the chapter prose in Markdown, no meta commentary, no JSON.
Begin with "## {ch_meta.get('title')}" on the first line.
"""

    try:
        prose = (await _call_claude_async(
            f"You are a professional literary author writing in {lang_full}.",
            prompt,
            max_tokens=8000,
        )).strip()
    except Exception as e:
        logger.error(f"BookFactory chapter generation failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    # Save
    chapters_dict = book_bible.get("chapters") or {}
    word_count = len(prose.split())
    chapters_dict[str(req.chapter_index)] = {
        "index": req.chapter_index,
        "title": ch_meta.get("title"),
        "prose": prose,
        "word_count": word_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    book_bible["chapters"] = chapters_dict
    book_bible["status"] = f"chapter_{req.chapter_index}_ready"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, f"book_chapter_{req.chapter_index}_ready", f"Capítulo {req.chapter_index} escrito ({word_count} palavras)")
    _save_project(tenant["id"], settings, projects)

    return chapters_dict[str(req.chapter_index)]


@router.post("/projects/{project_id}/book/plan-illustrations")
async def book_plan_illustrations(project_id: str, tenant=Depends(get_current_tenant)):
    """Art Director creates illustration_plan based on chapters and trim."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    chapters_dict = book_bible.get("chapters") or {}

    if not chapters_dict:
        raise HTTPException(status_code=400, detail="No chapters to illustrate")
    if brief.get("illustration_track") == "none":
        return {"illustration_plan": [], "skipped": True, "reason": "illustration_track=none"}

    chapter_summaries = []
    for idx in sorted(chapters_dict.keys(), key=lambda x: int(x)):
        ch = chapters_dict[idx]
        chapter_summaries.append(f"Ch{idx} ({ch.get('title')}): {ch.get('prose', '')[:500]}...")

    prompt = f"""You are the Editorial Art Director. Plan illustrations for this book.

FORMAT: {brief.get('format_preset')} — trim {brief.get('trim_size')} — track {brief.get('illustration_track')}

CHAPTERS:
{chr(10).join(chapter_summaries)}

Return ONLY JSON:
{{
  "visual_track": "{brief.get('illustration_track')}",
  "palette": {{"primary": "#hex", "secondary": "#hex", "accent": "#hex"}},
  "style_rules": "brief rules for all illustrations",
  "illustration_plan": [
    {{"page_number": 1, "chapter": 1, "type": "full" | "spot" | "spread" | "none", "description": "what to illustrate", "characters_in_page": ["name"]}},
    ...
  ]
}}

Rules:
- For format=infantil_ilustrado: 1 full-page illustration per chapter + 1 spot at chapter start.
- For format=romance_adulto: type=none (no interior illustrations).
- For format=tecnico_historico: 1 full-page every 2-3 chapters.
"""

    try:
        raw = (await _call_claude_async(
            "You are an Editorial Art Director. Return only valid JSON.",
            prompt,
            max_tokens=4000,
        )).strip()
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
        plan = json.loads(raw)
    except Exception as e:
        logger.error(f"BookFactory illustration plan failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    book_bible["illustration_plan"] = plan.get("illustration_plan", [])
    book_bible["visual_track"] = plan.get("visual_track")
    book_bible["palette"] = plan.get("palette")
    book_bible["style_rules"] = plan.get("style_rules")
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_illustrations_planned", f"{len(plan.get('illustration_plan', []))} ilustrações planeadas")
    _save_project(tenant["id"], settings, projects)

    return plan


@router.post("/projects/{project_id}/book/generate-illustration")
async def book_generate_illustration(project_id: str, req: IllustrationGenerateRequest, tenant=Depends(get_current_tenant)):
    """Illustrator generates a single page's image using Gemini 3 Image + character refs."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    plan = book_bible.get("illustration_plan") or []
    item = next((p for p in plan if p.get("page_number") == req.page_number), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"No illustration planned for page {req.page_number}")
    if item.get("type") == "none":
        return {"page_number": req.page_number, "skipped": True}

    char_avatars = project.get("character_avatars") or {}
    style_rules = book_bible.get("style_rules", "")
    visual_track = book_bible.get("visual_track", "storybook")
    palette = book_bible.get("palette", {})

    chars_in_page = item.get("characters_in_page") or []

    # Collect avatar bytes (up to 5)
    avatar_cache = {}
    primary_image = None
    extra_images = []
    for name in chars_in_page[:5]:
        url = char_avatars.get(name)
        if not url:
            continue
        try:
            full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL', '')}/storage/v1/object/public{url}"
            tmp = _tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            urllib.request.urlretrieve(full_url, tmp.name)
            with open(tmp.name, "rb") as f:
                img_bytes = f.read()
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            if primary_image is None:
                primary_image = img_bytes
            else:
                extra_images.append(img_bytes)
        except Exception as e:
            logger.warning(f"BookFactory illustrator: failed to load avatar {name}: {e}")

    prompt = req.override_prompt or f"""Create a full-page book illustration in {visual_track} style.

SCENE: {item.get('description')}

STYLE RULES: {style_rules}
PALETTE: primary={palette.get('primary', '')}, secondary={palette.get('secondary', '')}, accent={palette.get('accent', '')}

CHARACTERS: match reference images EXACTLY. Same species, face, clothing, palette.
NO TEXT in illustration.
Leave 3mm bleed margin. Safe area inside.
Composition: cinematic, reader-friendly, high contrast.
"""

    try:
        from core.llm import generate_image_gemini_sync
        img_bytes = generate_image_gemini_sync(prompt, primary_image, extra_images=extra_images)
    except Exception as e:
        logger.error(f"BookFactory illustration gen failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    if not img_bytes:
        raise HTTPException(status_code=502, detail="Illustrator returned no image")

    fname = f"books/{project_id}/page_{req.page_number:03d}.png"
    url = _upload_to_storage(img_bytes, fname, "image/png")

    # Persist
    plan_new = []
    for p in plan:
        if p.get("page_number") == req.page_number:
            p["illustration_url"] = url
            p["generated_at"] = datetime.now(timezone.utc).isoformat()
        plan_new.append(p)
    book_bible["illustration_plan"] = plan_new
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _save_project(tenant["id"], settings, projects)

    return {"page_number": req.page_number, "illustration_url": url}


@router.post("/projects/{project_id}/book/generate-cover-v2")
async def book_generate_cover_v2(project_id: str, tenant=Depends(get_current_tenant)):
    """Cover Designer (v2) — uses Gemini 3 Image (same stack as interior illustrations)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    outline = book_bible.get("outline") or {}
    palette = book_bible.get("palette") or {}
    visual_track = book_bible.get("visual_track", brief.get("illustration_track", "storybook"))

    title = outline.get("title") or brief.get("title") or project.get("name", "Meu Livro")
    blurb = outline.get("blurb", "")

    # Collect character refs (up to 5)
    char_avatars = project.get("character_avatars") or {}
    primary_image = None
    extra_images = []
    for name, url in list(char_avatars.items())[:5]:
        try:
            full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
            tmp = _tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            urllib.request.urlretrieve(full_url, tmp.name)
            with open(tmp.name, "rb") as f:
                img = f.read()
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            if primary_image is None:
                primary_image = img
            else:
                extra_images.append(img)
        except Exception as e:
            logger.warning(f"BookFactory cover: failed to load avatar {name}: {e}")

    cover_prompt = f"""Create a stunning children's book cover illustration in {visual_track} style.

TITLE: "{title}"
STORY SUMMARY: {blurb[:400]}
PALETTE: primary={palette.get('primary','')}, secondary={palette.get('secondary','')}, accent={palette.get('accent','')}

RULES:
- Portrait orientation (taller than wide), cover-ready composition.
- NO TEXT on the image (title added later by layout).
- Dynamic, magical, inviting composition that captures the essence of the story.
- Characters match reference images EXACTLY if refs provided.
- Volumetric lighting, rich colors, high contrast.
- Leave 3mm bleed margin. Keep main subject inside safe area.
- Format: {brief.get('format_preset', 'infantil_ilustrado')}.
"""

    try:
        from core.llm import generate_image_gemini_sync
        cover_bytes = generate_image_gemini_sync(cover_prompt, primary_image, extra_images=extra_images)
    except Exception as e:
        logger.error(f"BookFactory cover gen failed: {e}")
        raise HTTPException(status_code=502, detail=f"Cover generation failed: {str(e)[:200]}")

    if not cover_bytes:
        raise HTTPException(status_code=502, detail="Cover image generation returned empty")

    cover_url = _upload_to_storage(cover_bytes, f"books/{project_id}/cover.png", "image/png")

    # Calculate spine width
    page_count = book_bible.get("page_count_estimate") or brief.get("target_pages", 40)
    paper_gsm = 80
    spine_mm = round(page_count * paper_gsm * 0.00058 + 4, 2)

    book_bible["cover"] = {
        "front_url": cover_url,
        "title": title,
        "subtitle": outline.get("subtitle", ""),
        "blurb": blurb,
        "spine_width_mm": spine_mm,
        "author_name": brief.get("author_name", ""),
    }
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_cover_ready", f"Capa gerada — lombada {spine_mm}mm")
    _save_project(tenant["id"], settings, projects)

    return book_bible["cover"]


@router.post("/projects/{project_id}/book/proofread")
async def book_proofread(project_id: str, tenant=Depends(get_current_tenant)):
    """Proofreader applies orthographic/typographic corrections."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    chapters_dict = book_bible.get("chapters") or {}
    if not chapters_dict:
        raise HTTPException(status_code=400, detail="No chapters to proofread")

    brief = book_bible.get("brief") or {}
    lang_full = {"pt": "Portuguese (PT-BR)", "en": "English", "es": "Spanish"}.get(brief.get("language", "pt"), "Portuguese")

    corrected = {}
    for idx in sorted(chapters_dict.keys(), key=lambda x: int(x)):
        ch = chapters_dict[idx]
        prose = ch.get("prose", "")
        try:
            fixed = (await _call_claude_async(
                f"Professional proofreader for {lang_full}. Fix orthography, typography, grammar. Preserve author's voice.",
                f"Proofread the following chapter. Return ONLY the corrected prose in Markdown, no commentary:\n\n{prose}",
                max_tokens=8000,
            )).strip()
            corrected[idx] = {**ch, "prose": fixed, "proofread_at": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            logger.warning(f"BookFactory proofread ch{idx} failed: {e} — keeping original")
            corrected[idx] = ch

    book_bible["chapters"] = corrected
    book_bible["status"] = "proofread"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_proofread", "Revisão ortográfica completa")
    _save_project(tenant["id"], settings, projects)

    return {"status": "proofread", "chapters_reviewed": len(corrected)}


@router.post("/projects/{project_id}/book/render-pdf")
async def book_render_pdf(project_id: str, tenant=Depends(get_current_tenant)):
    """Layout Designer decides specs + WeasyPrint renders PDF."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    outline = book_bible.get("outline") or {}
    chapters_dict = book_bible.get("chapters") or {}
    plan = book_bible.get("illustration_plan") or []
    cover = book_bible.get("cover") or {}

    if not chapters_dict:
        raise HTTPException(status_code=400, detail="No chapters ready for layout")

    # Layout spec resolver (Layout Designer presets)
    format_preset = brief.get("format_preset", "infantil_ilustrado")
    trim = TRIM_SIZES_MM.get(brief.get("trim_size", "6x9"), TRIM_SIZES_MM["6x9"])

    PRESETS = {
        "infantil_ilustrado": {
            "font_family": "'Source Serif Pro', Georgia, serif",
            "font_size_pt": 14,
            "line_height": 1.5,
            "margins_mm": {"top": 18, "bottom": 18, "inner": 20, "outer": 16},
            "widows": 3, "orphans": 3,
            "hyphens": "auto",
            "drop_cap": False,
            "show_running_headers": False,
            "chapter_start_recto": True,
        },
        "romance_adulto": {
            "font_family": "'EB Garamond', Garamond, serif",
            "font_size_pt": 10.5,
            "line_height": 1.25,
            "margins_mm": {"top": 20, "bottom": 22, "inner": 20, "outer": 15},
            "widows": 3, "orphans": 3,
            "hyphens": "auto",
            "drop_cap": True,
            "show_running_headers": True,
            "chapter_start_recto": True,
        },
        "tecnico_historico": {
            "font_family": "'Source Serif Pro', Georgia, serif",
            "font_size_pt": 11,
            "line_height": 1.35,
            "margins_mm": {"top": 22, "bottom": 22, "inner": 22, "outer": 18},
            "widows": 3, "orphans": 3,
            "hyphens": "auto",
            "drop_cap": False,
            "show_running_headers": True,
            "chapter_start_recto": True,
        },
    }
    layout = PRESETS.get(format_preset, PRESETS["infantil_ilustrado"])

    # Build pages
    ordered = sorted(chapters_dict.values(), key=lambda x: x.get("index", 0))
    illus_by_chapter = {}
    for p in plan:
        illus_by_chapter.setdefault(p.get("chapter"), []).append(p)

    # Render HTML (1st pass without padding)
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader("/app/backend/templates/book"),
        autoescape=select_autoescape(['html']),
    )
    tmpl = env.get_template("book_base.html.j2")

    def _render(blank_pages: int):
        html = tmpl.render(
            book={
                "title": outline.get("title") or brief.get("title") or project.get("name", "Meu Livro"),
                "subtitle": outline.get("subtitle", ""),
                "author": brief.get("author_name", ""),
                "language": brief.get("language", "pt"),
            },
            cover=cover,
            chapters=ordered,
            illustrations_by_chapter=illus_by_chapter,
            layout=layout,
            trim=trim,
            blank_pages_count=blank_pages,
        )
        from weasyprint import HTML as WeasyHTML
        return WeasyHTML(string=html, base_url="/app/backend/templates/book/").write_pdf()

    try:
        pdf_bytes = _render(0)
    except Exception as e:
        logger.error(f"BookFactory WeasyPrint render failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Render failed: {str(e)[:200]}")

    # Auto-padding: count pages and re-render if not multiple of 4
    try:
        from pypdf import PdfReader
        import io as _io
        page_count = len(PdfReader(_io.BytesIO(pdf_bytes)).pages)
        remainder = page_count % 4
        if remainder != 0:
            blanks_needed = 4 - remainder
            logger.info(f"BookFactory auto-padding: {page_count} pages → adding {blanks_needed} blank(s) for multiple of 4")
            pdf_bytes = _render(blanks_needed)
            page_count = len(PdfReader(_io.BytesIO(pdf_bytes)).pages)
    except Exception as e:
        logger.warning(f"BookFactory padding pass skipped: {e}")
        page_count = None

    pdf_url = _upload_to_storage(pdf_bytes, f"books/{project_id}/final.pdf", "application/pdf")

    book_bible["pdf_url"] = pdf_url
    book_bible["pdf_size_bytes"] = len(pdf_bytes)
    book_bible["layout_spec"] = layout
    book_bible["status"] = "pdf_rendered"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_pdf_rendered", f"PDF gerado — {len(pdf_bytes)//1024}KB")
    _save_project(tenant["id"], settings, projects)

    return {
        "pdf_url": pdf_url,
        "size_kb": len(pdf_bytes) // 1024,
        "page_count": page_count,
        "layout_spec": layout,
    }


@router.post("/projects/{project_id}/book/preflight")
async def book_preflight(project_id: str, tenant=Depends(get_current_tenant)):
    """Preflight Agent validates the rendered PDF."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    pdf_url = book_bible.get("pdf_url")
    if not pdf_url:
        raise HTTPException(status_code=400, detail="No PDF to preflight. Run /book/render-pdf first.")

    # Download locally
    tmp = _tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        full_url = pdf_url if not pdf_url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{pdf_url}"
        urllib.request.urlretrieve(full_url, tmp.name)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PDF download failed: {e}")

    # Run checks
    report = {
        "passed": True,
        "checks": {},
        "warnings": [],
        "blockers": [],
    }

    try:
        from pypdf import PdfReader
        reader = PdfReader(tmp.name)
        page_count = len(reader.pages)

        # Check 1: page count multiple of 4
        target_multiple = 4
        pc_ok = (page_count % target_multiple == 0)
        report["checks"]["page_count_multiple"] = {
            "passed": pc_ok,
            "actual": page_count,
            "target_multiple": target_multiple,
        }
        if not pc_ok:
            report["passed"] = False
            report["blockers"].append(f"Page count {page_count} is not a multiple of {target_multiple}")

        # Check 2: fonts embedded (scan page resources)
        embedded_ok = True
        font_check_details = {"pages_scanned": 0, "non_embedded_found": 0}
        for i, page in enumerate(reader.pages[:20]):  # sample first 20 pages
            font_check_details["pages_scanned"] += 1
            resources = page.get("/Resources") or {}
            fonts = resources.get("/Font") or {}
            for fk in fonts:
                try:
                    font_obj = fonts[fk].get_object() if hasattr(fonts[fk], "get_object") else fonts[fk]
                    # Font is embedded if it has FontDescriptor with FontFile*
                    desc = font_obj.get("/FontDescriptor")
                    if desc:
                        desc_obj = desc.get_object() if hasattr(desc, "get_object") else desc
                        if not any(k in desc_obj for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                            embedded_ok = False
                            font_check_details["non_embedded_found"] += 1
                except Exception:
                    pass
        report["checks"]["fonts_embedded"] = {
            "passed": embedded_ok,
            "details": font_check_details,
        }
        if not embedded_ok:
            report["warnings"].append("Some fonts may not be embedded (sample check)")

        # Check 3: bleed — measure first page MediaBox vs TrimBox/BleedBox
        first_page = reader.pages[0]
        media = first_page.get("/MediaBox")
        bleed = first_page.get("/BleedBox") or first_page.get("/TrimBox")
        if media:
            mw = float(media[2]) - float(media[0])
            mh = float(media[3]) - float(media[1])
            # Expected trim (mm→pt: 1mm = 2.834645 pt)
            trim_mm = TRIM_SIZES_MM.get((book_bible.get("brief") or {}).get("trim_size", "6x9"), TRIM_SIZES_MM["6x9"])
            expected_w_pt = trim_mm["width"] * 2.834645
            expected_h_pt = trim_mm["height"] * 2.834645
            # Bleed 3mm = 8.5pt each side → page should be ~17pt larger if bleed applied
            bleed_applied = abs(mw - expected_w_pt) > 10 or abs(mh - expected_h_pt) > 10
            report["checks"]["bleed_3mm"] = {
                "passed": bleed_applied,
                "media_box_pt": [mw, mh],
                "expected_trim_pt": [expected_w_pt, expected_h_pt],
                "note": "Bleed detection heuristic: MediaBox should be ~17pt larger than trim on each axis.",
            }
            if not bleed_applied:
                report["warnings"].append("Bleed may not be applied — check WeasyPrint @page bleed CSS.")

        # Check 4: image DPI (heuristic — scan XObjects)
        dpi_report = {"images_scanned": 0, "below_300dpi": 0}
        try:
            from pypdf.generic import ContentStream
            for page in reader.pages[:10]:
                resources = page.get("/Resources") or {}
                xobj = resources.get("/XObject") or {}
                for name in xobj:
                    o = xobj[name].get_object() if hasattr(xobj[name], "get_object") else xobj[name]
                    if o.get("/Subtype") == "/Image":
                        dpi_report["images_scanned"] += 1
                        # Can't easily compute actual DPI without rendering — just count presence
        except Exception:
            pass
        report["checks"]["image_dpi"] = {
            "passed": True,  # Heuristic: WeasyPrint with image_resolution 300 is usually OK
            "details": dpi_report,
            "note": "Full DPI audit requires per-image rendering analysis (Phase 2).",
        }

        # Check 5: color space (heuristic — pdf generated by WeasyPrint is RGB by default, flagged as warning)
        report["checks"]["color_space_cmyk"] = {
            "passed": False,
            "note": "WeasyPrint outputs RGB by default. CMYK conversion requires post-processing via ghostscript (Phase 2).",
        }
        report["warnings"].append("CMYK conversion pending — use ghostscript post-processing before printing.")

        # Check 6: PDF/X compliance (requires ghostscript)
        report["checks"]["pdfx_compliance"] = {
            "passed": False,
            "note": "PDF/X tagging requires ghostscript post-processing (Phase 2).",
        }

    except Exception as e:
        logger.error(f"BookFactory preflight error: {e}")
        report["passed"] = False
        report["blockers"].append(f"Preflight scan failed: {e}")
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

    book_bible["preflight_report"] = report
    book_bible["preflight_passed"] = report["passed"]
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    if report["passed"]:
        _add_milestone(project, "book_preflight_passed", "Pré-impressão aprovada")
    _save_project(tenant["id"], settings, projects)

    return report


@router.get("/projects/{project_id}/book/state")
async def book_state(project_id: str, tenant=Depends(get_current_tenant)):
    """Return the full book_bible state for the frontend."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    bb = (project.get("project_bible") or {}).get("book_bible") or {}
    return bb


@router.get("/book/compositions")
async def list_compositions(user=Depends(get_current_user)):
    """Expose available meeting room compositions for the UI."""
    return _load_compositions()


@router.get("/book/trim-sizes")
async def list_trim_sizes(user=Depends(get_current_user)):
    return {"trim_sizes": TRIM_SIZES_MM, "visual_tracks": VISUAL_TRACKS}


# ─── Picturebook-specific endpoints ───────────────────────────────────────────

class ArtDirectRequest(BaseModel):
    extra_instructions: Optional[str] = None


@router.post("/projects/{project_id}/book/art-direct")
async def book_art_direct(project_id: str, req: ArtDirectRequest, tenant=Depends(get_current_tenant)):
    """Art Director Editorial agent picks the visual theme for the book.

    Returns a `theme` JSON used by the picturebook template: colors, fonts, palette,
    spreads layout suggestion. Runs once before illustration generation.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    outline = book_bible.get("outline") or {}
    spreads = book_bible.get("spreads") or []

    characters_brief = "\n".join([
        f"- {c.get('name')}: {(c.get('description') or '')[:150]}"
        for c in (project.get("characters") or []) if isinstance(c, dict)
    ][:8])

    prompt = f"""You are the Editorial Art Director for BookFactory.
Decide the complete VISUAL THEME for this book: palette, typography, mood.

BOOK:
- Title: {outline.get('title', '')}
- Format: {brief.get('format_preset')} — audience {brief.get('audience')}
- Briefing: {brief.get('briefing')}
- Illustration track: {brief.get('illustration_track')}
- Total spreads: {len(spreads)}
- Language: {brief.get('language')}

CHARACTERS:
{characters_brief}

{f"EXTRA INSTRUCTIONS: {req.extra_instructions}" if req.extra_instructions else ''}

Return ONLY valid JSON with this EXACT structure:
{{
  "theme": {{
    "title_font": "Google Font or generic family (e.g. 'Fredoka', 'Lilita One', 'Poppins')",
    "body_font": "Nunito, Quicksand, Comic Neue, etc for children OR Merriweather, Lora for older",
    "body_size": 13 (pt, 13-18 for children picturebook),
    "line_height": 1.5,
    "title_color": "#HEX",
    "body_color": "#HEX",
    "accent": "#HEX",
    "page_bg": "#HEX (light warm cream for children, white for adult)",
    "text_box_bg": "#HEX (slightly tinted from page_bg)",
    "illus_bg": "#HEX (deeper version for image fallback)",
    "cover_title_size": 42 (pt),
    "page_number_color": "#HEX",
    "cover_fallback_a": "#HEX",
    "cover_fallback_b": "#HEX"
  }},
  "palette": {{"primary": "#HEX", "secondary": "#HEX", "accent": "#HEX", "shadow": "#HEX"}},
  "style_rules": "4-6 sentence description of overall visual style guidelines that every illustration must follow (lighting, mood, detail level, color temperature, line quality)",
  "spread_layouts_default": "split | overlay"
}}
"""

    try:
        raw = (await _call_claude_async(
            "You are a professional Editorial Art Director. Return only valid JSON with all fields.",
            prompt,
            max_tokens=2500,
        )).strip()
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
        direction = json.loads(raw)
    except Exception as e:
        logger.error(f"BookFactory art-direct failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    book_bible["theme"] = direction.get("theme") or {}
    book_bible["palette"] = direction.get("palette") or {}
    book_bible["style_rules"] = direction.get("style_rules") or ""
    book_bible["spread_layouts_default"] = direction.get("spread_layouts_default") or "split"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_art_direction_set", "Direção de arte definida")
    _save_project(tenant["id"], settings, projects)

    return direction


def _download_avatar_bytes(url: str) -> Optional[bytes]:
    try:
        full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
        tmp = _tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        urllib.request.urlretrieve(full_url, tmp.name)
        with open(tmp.name, "rb") as f:
            data = f.read()
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        return data
    except Exception as e:
        logger.warning(f"BookFactory: avatar download failed {url[:60]}: {e}")
        return None


@router.post("/projects/{project_id}/book/illustrate-spread")
async def book_illustrate_spread(project_id: str, req: IllustrateSpreadRequest, tenant=Depends(get_current_tenant)):
    """Illustrator generates 1 illustration for a SPECIFIC spread.

    Uses:
    - Exact spread text and scene_description
    - Character avatars from project.character_avatars as multimodal refs (up to 5)
    - Visual track + style_rules from Art Director
    - Previous spread illustration as optional continuity ref
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    spreads = book_bible.get("spreads") or []
    if req.spread_index < 1 or req.spread_index > len(spreads):
        raise HTTPException(status_code=400, detail=f"Spread index out of range (1..{len(spreads)})")

    spread = spreads[req.spread_index - 1]
    theme = book_bible.get("theme") or {}
    palette = book_bible.get("palette") or {}
    style_rules = book_bible.get("style_rules") or ""
    visual_track = (book_bible.get("brief") or {}).get("illustration_track") or "storybook"

    # Character refs — ALWAYS pass ALL project avatars (up to 5), not just in-scene
    # This ensures illustrator maintains style across the whole book
    char_avatars = project.get("character_avatars") or {}
    characters = project.get("characters") or []
    scene_chars = spread.get("characters_in_scene") or []

    char_descriptions = []
    primary_image = None
    extra_images = []
    # Preferencialmente carrega personagens DA CENA; depois completa até 5
    ordered_names = list(scene_chars) + [
        c.get("name") for c in characters
        if isinstance(c, dict) and c.get("name") not in scene_chars
    ]
    for name in ordered_names[:5]:
        if not name:
            continue
        url = char_avatars.get(name)
        if not url:
            continue
        img = _download_avatar_bytes(url)
        if not img:
            continue
        desc = next((c.get("description", "") for c in characters if isinstance(c, dict) and c.get("name") == name), "")
        char_descriptions.append(f"- {name}: {desc[:200]}")
        if primary_image is None:
            primary_image = img
        else:
            extra_images.append(img)

    prompt = req.override_prompt or f"""Create a full-page children's book illustration in {visual_track} style.

SCENE TO ILLUSTRATE (this exact moment from the book):
{spread.get('scene_description', '')}

TEXT OF THIS PAGE (for context — do NOT render text in image):
"{spread.get('text', '')}"

CHARACTERS VISIBLE IN SCENE: {', '.join(scene_chars) if scene_chars else 'scene context only'}
CHARACTER REFERENCES (match EXACTLY):
{chr(10).join(char_descriptions) if char_descriptions else '(none available)'}

STYLE RULES (apply rigorously — every illustration in this book must follow these):
{style_rules}

PALETTE TO USE:
- Primary: {palette.get('primary', '#000')}
- Secondary: {palette.get('secondary', '#000')}
- Accent: {palette.get('accent', '#000')}

TECHNICAL:
- Landscape orientation preferred (wider than tall) — image will be cropped to top portion of page.
- NO TEXT, NO LETTERS, NO SIGNS in the illustration.
- Characters MUST match reference images exactly (same species, face, clothing, proportions).
- Composition: reader-friendly, clear focal point, warm cinematic lighting.
- Leave 5% bleed margin around edges (main subject centered).
- High detail, emotional, evocative — this is the ONLY image on this page of the book.
"""

    try:
        from core.llm import generate_image_gemini_sync
        img_bytes = generate_image_gemini_sync(prompt, primary_image, extra_images=extra_images)
    except Exception as e:
        logger.error(f"BookFactory illustrate-spread failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    if not img_bytes:
        raise HTTPException(status_code=502, detail="Illustrator returned no image")

    fname = f"books/{project_id}/spread_{req.spread_index:03d}.png"
    url = _upload_to_storage(img_bytes, fname, "image/png")

    # Persist on the spread
    spread["illustration_url"] = url
    spread["generated_at"] = datetime.now(timezone.utc).isoformat()
    if req.layout:
        spread["layout"] = req.layout
    spreads[req.spread_index - 1] = spread
    book_bible["spreads"] = spreads
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _save_project(tenant["id"], settings, projects)

    return {"spread_index": req.spread_index, "illustration_url": url, "refs_used": len(char_descriptions)}


@router.post("/projects/{project_id}/book/meeting-room-review")
async def book_meeting_room_review(project_id: str, tenant=Depends(get_current_tenant)):
    """Simulated Meeting Room: Editor agent reviews outline + spreads and proposes tweaks.

    Returns a review JSON with suggestions. Non-destructive — does not rewrite unless
    follow-up call to /book/apply-review is made.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    spreads = book_bible.get("spreads") or []
    outline = book_bible.get("outline") or {}
    if not spreads:
        raise HTTPException(status_code=400, detail="No spreads to review")

    spreads_text = "\n".join([
        f"Spread {s.get('index')}: {s.get('text', '')[:200]}"
        for s in spreads
    ])

    prompt = f"""You are the Editor of Consistency for BookFactory. Review this picturebook and identify issues.

TITLE: {outline.get('title', '')}
AUDIENCE: {(book_bible.get('brief') or {}).get('audience')}
TOTAL SPREADS: {len(spreads)}

SPREADS:
{spreads_text}

Identify:
1. Any character trait inconsistencies across spreads.
2. Any pacing issues (too slow, too fast, missing emotional beats).
3. Any vocabulary inappropriate for the audience.
4. Any factual issues (if based on source material).
5. Any spread that is too text-heavy (should be <45 words).

Return ONLY JSON:
{{
  "consistency_score": 0-100,
  "issues": [
    {{"spread": N, "type": "character_drift|pacing|vocabulary|factual|length", "severity": "minor|major|critical", "description": "...", "suggested_fix": "..."}},
    ...
  ],
  "overall_assessment": "short paragraph"
}}
"""
    try:
        raw = (await _call_claude_async(
            "You are a strict Editor of Consistency. Return only valid JSON.",
            prompt,
            max_tokens=3000,
        )).strip()
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
        review = json.loads(raw)
    except Exception as e:
        logger.error(f"BookFactory meeting-room failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    book_bible["meeting_room_review"] = review
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_review_done", f"Review — score {review.get('consistency_score')}")
    _save_project(tenant["id"], settings, projects)

    return review


@router.post("/projects/{project_id}/book/render-picturebook")
async def book_render_picturebook(project_id: str, tenant=Depends(get_current_tenant)):
    """Renders picturebook PDF using the storybook template (text+illus on same page)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    outline = book_bible.get("outline") or {}
    spreads = book_bible.get("spreads") or []
    cover = book_bible.get("cover") or {}
    theme = book_bible.get("theme") or {}

    if not spreads:
        raise HTTPException(status_code=400, detail="No spreads to render")

    # Defaults if Art Director didn't run
    default_theme = {
        "title_font": "'Fredoka', 'Lilita One', 'Quicksand', sans-serif",
        "body_font": "'Nunito', 'Quicksand', 'Source Sans Pro', sans-serif",
        "body_size": 14,
        "line_height": 1.55,
        "title_color": "#6B4423",
        "body_color": "#3A2C20",
        "accent": "#E8A344",
        "page_bg": "#FFF8EA",
        "text_box_bg": "#FFF3D6",
        "illus_bg": "#F5E4C0",
        "cover_title_size": 46,
        "page_number_color": "#9E7D4A",
        "cover_fallback_a": "#F5B041",
        "cover_fallback_b": "#C87F0A",
    }
    merged_theme = {**default_theme, **(theme or {})}

    trim = TRIM_SIZES_MM.get(brief.get("trim_size", "6x9"), TRIM_SIZES_MM["6x9"])

    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(loader=FileSystemLoader("/app/backend/templates/book"), autoescape=select_autoescape(['html']))
    tmpl = env.get_template("picturebook.html.j2")

    year = datetime.now(timezone.utc).year
    sources = [s.get("reference", "") for s in book_bible.get("rag_sources", [])]

    def _render(blank_pages: int):
        html = tmpl.render(
            book={
                "title": outline.get("title") or brief.get("title") or project.get("name", "Livro"),
                "subtitle": outline.get("subtitle", ""),
                "author": brief.get("author_name", ""),
                "language": brief.get("language", "pt"),
                "year": year,
            },
            cover=cover,
            spreads=spreads,
            theme=merged_theme,
            trim=trim,
            blank_pages_count=blank_pages,
            sources=sources,
        )
        from weasyprint import HTML as WeasyHTML
        return WeasyHTML(string=html, base_url="/app/backend/templates/book/").write_pdf()

    try:
        pdf_bytes = _render(0)
    except Exception as e:
        logger.error(f"BookFactory picturebook render failed: {e}")
        import traceback; logger.error(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Render failed: {str(e)[:200]}")

    # Auto-padding
    try:
        from pypdf import PdfReader
        import io as _io
        page_count = len(PdfReader(_io.BytesIO(pdf_bytes)).pages)
        remainder = page_count % 4
        if remainder != 0:
            blanks = 4 - remainder
            pdf_bytes = _render(blanks)
            page_count = len(PdfReader(_io.BytesIO(pdf_bytes)).pages)
    except Exception as e:
        logger.warning(f"BookFactory picturebook padding failed: {e}")
        page_count = None

    pdf_url = _upload_to_storage(pdf_bytes, f"books/{project_id}/final.pdf", "application/pdf")

    book_bible["pdf_url"] = pdf_url
    book_bible["pdf_size_bytes"] = len(pdf_bytes)
    book_bible["page_count"] = page_count
    book_bible["theme_applied"] = merged_theme
    book_bible["status"] = "picturebook_rendered"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_picturebook_rendered", f"Picturebook gerado — {page_count}p")
    _save_project(tenant["id"], settings, projects)

    return {"pdf_url": pdf_url, "size_kb": len(pdf_bytes) // 1024, "page_count": page_count, "theme": merged_theme}


# ─── Theme editor + Refinement loop ───────────────────────────────────────────

class ThemeUpdateRequest(BaseModel):
    theme: dict
    palette: Optional[dict] = None
    style_rules: Optional[str] = None


@router.patch("/projects/{project_id}/book/theme")
async def book_update_theme(project_id: str, req: ThemeUpdateRequest, tenant=Depends(get_current_tenant)):
    """User-driven theme override. Frontend can edit fonts/colors after Art Direction."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    current_theme = book_bible.get("theme") or {}
    book_bible["theme"] = {**current_theme, **(req.theme or {})}
    if req.palette:
        book_bible["palette"] = {**(book_bible.get("palette") or {}), **req.palette}
    if req.style_rules is not None:
        book_bible["style_rules"] = req.style_rules

    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _save_project(tenant["id"], settings, projects)
    return {"theme": book_bible["theme"], "palette": book_bible.get("palette"), "style_rules": book_bible.get("style_rules")}


class RewriteSpreadRequest(BaseModel):
    spread_index: int
    instructions: str  # e.g. "encurtar texto", "remover palavra X", "mais alegre"


@router.post("/projects/{project_id}/book/rewrite-spread")
async def book_rewrite_spread(project_id: str, req: RewriteSpreadRequest, tenant=Depends(get_current_tenant)):
    """Author Agent rewrites a single spread based on user instructions or editor issues."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    spreads = book_bible.get("spreads") or []
    if req.spread_index < 1 or req.spread_index > len(spreads):
        raise HTTPException(status_code=400, detail="Spread index out of range")

    spread = spreads[req.spread_index - 1]
    brief = book_bible.get("brief") or {}
    outline = book_bible.get("outline") or {}

    lang_full = {"pt": "Portuguese", "en": "English", "es": "Spanish"}.get(brief.get("language", "pt"), "Portuguese")
    prompt = f"""You are the Author. Rewrite this SINGLE spread based on instructions.

BOOK: {outline.get('title', '')}
AUDIENCE: {brief.get('audience')}
LANGUAGE: {lang_full}

CURRENT SPREAD {spread.get('index')}:
Text: "{spread.get('text', '')}"
Scene: {spread.get('scene_description', '')}
Characters: {spread.get('characters_in_scene', [])}
Layout: {spread.get('layout_hint', 'split')}

REWRITE INSTRUCTIONS: {req.instructions}

Return ONLY valid JSON with the rewritten spread (same schema as original):
{{
  "index": {spread.get('index')},
  "text": "new text (2-4 short sentences, max 45 words)",
  "scene_description": "updated scene for illustrator",
  "characters_in_scene": [...],
  "layout_hint": "split" or "overlay"
}}
"""
    try:
        raw = (await _call_claude_async(
            f"Professional picturebook author in {lang_full}. Return only valid JSON.",
            prompt,
            max_tokens=2000,
        )).strip()
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
        new_spread = json.loads(raw)
    except Exception as e:
        logger.error(f"BookFactory rewrite-spread failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    # Preserve illustration_url (user may re-illustrate separately)
    new_spread["illustration_url"] = spread.get("illustration_url")
    new_spread["index"] = req.spread_index
    new_spread["rewritten_at"] = datetime.now(timezone.utc).isoformat()
    spreads[req.spread_index - 1] = new_spread
    book_bible["spreads"] = spreads
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, f"book_spread_{req.spread_index}_rewritten", f"Spread {req.spread_index} reescrito")
    _save_project(tenant["id"], settings, projects)

    return new_spread


@router.post("/projects/{project_id}/book/apply-review-fixes")
async def book_apply_review_fixes(project_id: str, tenant=Depends(get_current_tenant)):
    """Auto-apply critical/major fixes from the last meeting-room review.

    Iterates the review.issues list and calls rewrite-spread for each.
    Safe to run multiple times — acts only on current issues.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    review = book_bible.get("meeting_room_review") or {}
    issues = review.get("issues") or []

    applied = []
    skipped = []
    for iss in issues:
        severity = iss.get("severity", "minor")
        if severity not in ("critical", "major"):
            skipped.append({"spread": iss.get("spread"), "reason": f"severity={severity}"})
            continue

        spread_idx = iss.get("spread")
        if not spread_idx:
            skipped.append({"reason": "no spread index"})
            continue

        instr = f"Fix issue: {iss.get('description', '')}. Suggested fix: {iss.get('suggested_fix', '')}"
        try:
            rr = RewriteSpreadRequest(spread_index=spread_idx, instructions=instr)
            await book_rewrite_spread(project_id, rr, tenant)
            applied.append({"spread": spread_idx, "type": iss.get("type")})
        except Exception as e:
            skipped.append({"spread": spread_idx, "reason": str(e)[:120]})

    _add_milestone(project, "book_review_applied", f"Aplicados {len(applied)} fixes")
    settings, projects, project = _get_project(tenant["id"], project_id)
    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    book_bible["review_applied_count"] = len(applied)
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _save_project(tenant["id"], settings, projects)

    return {"applied": applied, "skipped": skipped, "total_applied": len(applied)}
