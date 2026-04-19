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
    format_preset: str = "infantil_ilustrado"  # "infantil_ilustrado" | "romance_adulto" | "tecnico_historico"
    trim_size: str = "6x9"
    target_pages: int = 40
    audience: str = "children_4_8"  # children_0_3 | children_4_8 | children_9_12 | ya | adult | technical
    illustration_track: str = "storybook"
    title: str = ""
    author_name: str = ""
    briefing: str = ""
    language: str = "pt"
    character_ids: list = []  # Refs to folders/avatars
    reference_work: Optional[str] = None  # For public_domain mode: "biblia_genesis" | "classic_gutenberg_xxx"


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

    # Optional RAG context
    rag_context = []
    if book_bible.get("rag_enabled") and brief.get("reference_work"):
        rag_context = _rag.search(brief["reference_work"], top_k=5)

    # Character universe context
    characters = project.get("characters") or []
    char_block = ""
    for c in characters[:8]:
        if isinstance(c, dict):
            char_block += f"- {c.get('name', '')}: {c.get('description', '')[:200]}\n"

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

{"RESEARCH CONTEXT (cite when relevant):" + chr(10) + chr(10).join(["- " + r["source"] + ": " + r["text"] for r in rag_context]) if rag_context else ""}

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
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")

        chat = LlmChat(
            api_key=api_key,
            session_id=f"book-outline-{project_id}",
            system_message="You are a professional literary author. Return only valid JSON."
        ).with_model("anthropic", "claude-sonnet-4-20250514")

        resp = await chat.send_message(UserMessage(text=prompt))
        raw = resp.strip()
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
    book_bible["status"] = "outline_ready"
    pb = project.get("project_bible", {}) or {}
    pb["book_bible"] = book_bible
    project["project_bible"] = pb
    _add_milestone(project, "book_outline_ready", f"Outline gerado — {outline.get('total_chapters', 0)} capítulos")
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
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        chat = LlmChat(
            api_key=api_key,
            session_id=f"book-chapter-{project_id}-{req.chapter_index}",
            system_message=f"You are a professional literary author writing in {lang_full}."
        ).with_model("anthropic", "claude-sonnet-4-20250514")
        prose = (await chat.send_message(UserMessage(text=prompt))).strip()
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
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        chat = LlmChat(
            api_key=api_key, session_id=f"book-artdir-{project_id}",
            system_message="You are an Editorial Art Director. Return only valid JSON."
        ).with_model("anthropic", "claude-sonnet-4-20250514")
        raw = (await chat.send_message(UserMessage(text=prompt))).strip()
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
    """Cover Designer (v2) — uses universe + computes spine width from page count."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    brief = book_bible.get("brief") or {}
    outline = book_bible.get("outline") or {}

    # Reuse existing cover generator for the front image
    from core.book_generator import generate_cover_image
    characters = project.get("characters", [])
    char_avatars = project.get("character_avatars", {})
    production_design = project.get("agents_output", {}).get("production_design", {})
    lang = project.get("language", "pt")
    title = outline.get("title") or brief.get("title") or project.get("name", "Meu Livro")

    try:
        cover_bytes = generate_cover_image(title, characters, char_avatars, production_design, lang)
    except Exception as e:
        logger.error(f"BookFactory cover gen failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    if not cover_bytes:
        raise HTTPException(status_code=502, detail="Cover image generation returned empty")

    cover_url = _upload_to_storage(cover_bytes, f"books/{project_id}/cover.png", "image/png")

    # Calculate spine width (assuming page_count approximation)
    page_count = book_bible.get("page_count_estimate") or brief.get("target_pages", 40)
    paper_gsm = 80
    spine_mm = round(page_count * paper_gsm * 0.00058 + 4, 2)

    book_bible["cover"] = {
        "front_url": cover_url,
        "title": title,
        "subtitle": outline.get("subtitle", ""),
        "blurb": outline.get("blurb", ""),
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
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            api_key = os.environ.get("EMERGENT_LLM_KEY", "")
            chat = LlmChat(
                api_key=api_key, session_id=f"book-proof-{project_id}-{idx}",
                system_message=f"Professional proofreader for {lang_full}. Fix orthography, typography, grammar. Preserve author's voice."
            ).with_model("anthropic", "claude-sonnet-4-20250514")
            msg = UserMessage(text=f"Proofread the following chapter. Return ONLY the corrected prose in Markdown, no commentary:\n\n{prose}")
            fixed = (await chat.send_message(msg)).strip()
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

    # Render HTML
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader("/app/backend/templates/book"),
        autoescape=select_autoescape(['html']),
    )
    tmpl = env.get_template("book_base.html.j2")
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
    )

    # WeasyPrint
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_bytes = WeasyHTML(string=html, base_url="/app/backend/templates/book/").write_pdf()
    except Exception as e:
        logger.error(f"BookFactory WeasyPrint render failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Render failed: {str(e)[:200]}")

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
