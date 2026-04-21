"""Book Editable — Exposes book as editable JSON spreads + quality gate.

Fluxo:
  1. Após ilustrações geradas → auto-audit Glen Keane
  2. Se score < 90 → bloqueia PDF final, retorna lista de spreads problemáticos
  3. Endpoints editáveis permitem ao usuário:
     - Ver todas as páginas como JSON estruturado (imagem + blocos de texto)
     - Editar texto de um bloco
     - Substituir imagem (upload ou regeneração)
     - Redimensionar/reposicionar imagens e textos
     - Regenerar PDF do estado editado
"""
from ._shared import *
from .agents_registry import resolve_agent_prompt
from pydantic import BaseModel
from typing import List as _List, Optional as _Opt
from datetime import datetime
import json as _json


# ─── Quality Gate ─────────────────────────────────────────────
MIN_QUALITY_SCORE = 90


@router.get("/book/projects/{project_id}/quality-gate")
async def book_quality_gate_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Check if book passes quality gate (Glen Keane score >= 90).
    Returns pass/fail + problematic spreads for regeneration.
    """
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = project.get("book_continuity_report") or {}
    score = report.get("score")

    if score is None:
        return {
            "passed": False,
            "status": "never_audited",
            "score": None,
            "min_required": MIN_QUALITY_SCORE,
            "message": "Auditoria Glen Keane ainda não executada. Execute antes de prosseguir para edição/PDF.",
            "problematic_spread_ids": [],
        }

    passed = score >= MIN_QUALITY_SCORE

    # Gather spread_ids from critical + medium issues (below 90 = regenerate)
    problematic = set()
    for bucket in ("critical_issues", "medium_issues"):
        for issue in report.get(bucket, []):
            for sid in (issue.get("spread_ids") or []):
                problematic.add(sid)

    return {
        "passed": passed,
        "status": "approved" if passed else "needs_revision",
        "score": score,
        "min_required": MIN_QUALITY_SCORE,
        "message": (
            f"Aprovado! Score {score} ≥ {MIN_QUALITY_SCORE}"
            if passed else
            f"Score {score} abaixo do mínimo {MIN_QUALITY_SCORE}. {len(problematic)} spreads precisam de regeneração."
        ),
        "problematic_spread_ids": sorted(problematic),
        "audited_at": report.get("audited_at"),
    }


# ─── Editable Spreads ─────────────────────────────────────────
@router.get("/book/projects/{project_id}/editable-spreads")
async def get_editable_spreads(project_id: str, tenant=Depends(get_current_tenant)):
    """Return editable JSON representation of all book spreads.

    Each spread has:
      - id (stable page_number)
      - chapter_index, chapter_title
      - image: {url, width_pct, height_pct, x_pct, y_pct, fit: 'cover'|'contain'|'full-bleed'}
      - text_overlays: [{id, content, x_pct, y_pct, width_pct, height_pct, font_size_pt, font_family, color, gradient: {direction, from, to, opacity}, alignment}]
      - background_color
      - metadata (description, characters, location — read-only)
    """
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    plan = book_bible.get("illustration_plan") or []
    chapters = book_bible.get("chapters") or {}

    # If editable state already exists → return it (preserves user edits)
    existing = book_bible.get("editable_spreads")
    if existing:
        return {"spreads": existing, "source": "user_edited"}

    # Build initial editable state from illustration_plan + chapters
    spreads = []
    format_preset = (book_bible.get("brief") or {}).get("format_preset", "infantil_ilustrado")
    is_picturebook = format_preset in ("infantil_ilustrado", "picturebook")

    for item in plan:
        page_num = item.get("page_number")
        chapter_idx = item.get("chapter")
        chapter = chapters.get(str(chapter_idx), {}) if chapter_idx else {}
        prose_preview = ""
        if chapter.get("prose"):
            # Pull a reasonable text chunk for this spread
            paragraphs = [p.strip() for p in chapter["prose"].split("\n\n") if p.strip()]
            if paragraphs:
                # Assign paragraph based on page_number offset
                prose_preview = paragraphs[page_num % len(paragraphs)][:500]

        # Build default text overlay (Disney-style when picturebook)
        if is_picturebook and prose_preview:
            text_overlay = {
                "id": f"text_{page_num}_0",
                "content": prose_preview,
                "x_pct": 8,
                "y_pct": 65,   # bottom third
                "width_pct": 84,
                "height_pct": 28,
                "font_size_pt": 16,
                "font_family": "'Source Serif Pro', Georgia, serif",
                "color": "#FFFFFF",
                "gradient": {
                    "direction": "to top",
                    "from": "rgba(0,0,0,0.85)",
                    "to":   "rgba(0,0,0,0)",
                    "opacity": 1.0,
                },
                "alignment": "left",
                "editable": True,
            }
        elif prose_preview:
            text_overlay = {
                "id": f"text_{page_num}_0",
                "content": prose_preview,
                "x_pct": 12, "y_pct": 10, "width_pct": 76, "height_pct": 80,
                "font_size_pt": 12,
                "font_family": "'EB Garamond', Garamond, serif",
                "color": "#111111",
                "gradient": None,
                "alignment": "justify",
                "editable": True,
            }
        else:
            text_overlay = None

        image_config = {
            "url": item.get("image_url") or item.get("url") or "",
            "x_pct": 0, "y_pct": 0, "width_pct": 100, "height_pct": 100,
            "fit": "cover" if is_picturebook else "contain",
            "regen_prompt": item.get("description", ""),
            "editable": True,
        }

        spreads.append({
            "id": page_num,
            "chapter_index": chapter_idx,
            "chapter_title": chapter.get("title", ""),
            "image": image_config,
            "text_overlays": [text_overlay] if text_overlay else [],
            "background_color": "#FFFFFF",
            "metadata": {
                "description": item.get("description", ""),
                "characters": item.get("characters_in_page", []),
                "type": item.get("type", "full"),
            },
        })

    # Persist initial state for future edits
    book_bible["editable_spreads"] = spreads
    _update_project_field(tenant["id"], project_id, {
        "project_bible": {**(project.get("project_bible") or {}), "book_bible": book_bible}
    }, flush_now=True)

    return {"spreads": spreads, "source": "initial_build"}


class SpreadUpdate(BaseModel):
    image: _Opt[dict] = None
    text_overlays: _Opt[list] = None
    background_color: _Opt[str] = None


@router.put("/book/projects/{project_id}/editable-spreads/{spread_id}")
async def update_editable_spread(
    project_id: str, spread_id: int, body: SpreadUpdate,
    tenant=Depends(get_current_tenant)
):
    """Update ONE spread's editable state (image, text_overlays, background)."""
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_bible = project.get("project_bible") or {}
    book_bible = project_bible.get("book_bible") or {}
    spreads = book_bible.get("editable_spreads") or []

    # Ensure initial state exists
    if not spreads:
        await get_editable_spreads(project_id, tenant)  # lazy-init
        _, _, project = _get_project(tenant["id"], project_id)
        book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
        spreads = book_bible.get("editable_spreads") or []

    updated = False
    for sp in spreads:
        if sp.get("id") == spread_id:
            if body.image is not None:
                sp["image"] = {**sp.get("image", {}), **body.image}
            if body.text_overlays is not None:
                sp["text_overlays"] = body.text_overlays
            if body.background_color is not None:
                sp["background_color"] = body.background_color
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Spread {spread_id} not found")

    book_bible["editable_spreads"] = spreads
    book_bible["last_edited_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    project_bible["book_bible"] = book_bible
    _update_project_field(tenant["id"], project_id, {"project_bible": project_bible}, flush_now=True)

    return {"status": "updated", "spread_id": spread_id}


@router.post("/book/projects/{project_id}/editable-spreads/{spread_id}/regenerate-image")
async def regenerate_spread_image(
    project_id: str, spread_id: int, body: dict = Body(default={}),
    tenant=Depends(get_current_tenant)
):
    """Regenerate the image for a spread using the current regen_prompt (or a custom prompt)."""
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    spreads = book_bible.get("editable_spreads") or []
    spread = next((s for s in spreads if s.get("id") == spread_id), None)
    if not spread:
        raise HTTPException(status_code=404, detail=f"Spread {spread_id} not found")

    prompt = body.get("prompt") or spread.get("image", {}).get("regen_prompt") or spread.get("metadata", {}).get("description", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt available for regeneration")

    # Use existing image generation infrastructure
    try:
        from core.llm import generate_image_gemini_sync
        image_bytes = await asyncio.to_thread(
            generate_image_gemini_sync,
            prompt,
            "9:16",  # default aspect ratio — TODO: honor book trim
        )
        if not image_bytes:
            raise RuntimeError("Empty image from generator")

        image_url = _upload_to_storage(
            image_bytes,
            f"books/{project_id}/spread_{spread_id}_{int(datetime.utcnow().timestamp())}.png",
            "image/png",
        )

        # Update spread
        spread["image"]["url"] = image_url
        spread["image"]["regen_prompt"] = prompt
        spread["image"]["regenerated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        book_bible["editable_spreads"] = spreads
        project_bible = project.get("project_bible") or {}
        project_bible["book_bible"] = book_bible
        _update_project_field(tenant["id"], project_id, {"project_bible": project_bible}, flush_now=True)

        return {"status": "regenerated", "image_url": image_url, "spread_id": spread_id}
    except Exception as e:
        logger.error(f"regenerate_spread_image [{project_id}/{spread_id}]: {e}")
        raise HTTPException(status_code=500, detail=f"Image regeneration failed: {str(e)[:200]}")


@router.get("/book/projects/{project_id}/editable-preview")
async def get_editable_preview_html(project_id: str, tenant=Depends(get_current_tenant)):
    """Return an HTML preview of current editable state (live — reflects latest edits).
    Frontend can iframe this for preview before PDF export.
    """
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible") or {}).get("book_bible") or {}
    spreads = book_bible.get("editable_spreads") or []
    if not spreads:
        raise HTTPException(status_code=400, detail="No editable spreads yet. Call GET /editable-spreads first.")

    # Build HTML
    pages = []
    for sp in spreads:
        img = sp.get("image", {}) or {}
        img_url = img.get("url", "")
        fit = img.get("fit", "cover")
        text_html = ""
        for t in sp.get("text_overlays", []) or []:
            grad = t.get("gradient") or {}
            grad_bg = (
                f"background: linear-gradient({grad.get('direction','to top')}, "
                f"{grad.get('from','rgba(0,0,0,0.85)')}, {grad.get('to','rgba(0,0,0,0)')});"
                if grad else ""
            )
            text_html += (
                f'<div style="position:absolute;'
                f'left:{t.get("x_pct",10)}%;top:{t.get("y_pct",70)}%;'
                f'width:{t.get("width_pct",80)}%;height:{t.get("height_pct",25)}%;'
                f'padding:16px;{grad_bg}'
                f'color:{t.get("color","#fff")};'
                f'font-family:{t.get("font_family","serif")};'
                f'font-size:{t.get("font_size_pt",16)}pt;'
                f'text-align:{t.get("alignment","left")};'
                f'display:flex;align-items:flex-end;">'
                f'<p style="margin:0;">{t.get("content","").replace(chr(10),"<br/>")}</p>'
                f'</div>'
            )
        pages.append(
            f'<section style="position:relative;width:100%;aspect-ratio:3/4;background:{sp.get("background_color","#fff")};overflow:hidden;margin:20px auto;max-width:800px;box-shadow:0 4px 20px rgba(0,0,0,0.15);">'
            + (f'<img src="{img_url}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:{fit};"/>' if img_url else "")
            + text_html
            + f'<div style="position:absolute;bottom:4px;right:8px;font-family:monospace;color:rgba(255,255,255,0.6);font-size:10px;">p.{sp.get("id","?")}</div>'
            + '</section>'
        )

    html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Preview</title>'
        '<style>body{margin:0;background:#1a1a2e;padding:20px;font-family:system-ui;}</style>'
        '</head><body>'
        + "".join(pages)
        + '</body></html>'
    )
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)
