"""Continuity Audit — On-demand continuity validation for video and book projects.

Endpoints:
    POST /api/studio/projects/{project_id}/continuity-audit  → video (Thelma Schoonmaker)
    POST /api/studio/book/projects/{project_id}/visual-continuity-audit → book (Glen Keane)
    GET  /api/studio/projects/{project_id}/continuity-report
    GET  /api/studio/book/projects/{project_id}/visual-continuity-report

Design: ADDITIVE. Uses resolve_agent_prompt (customizable via /agents UI).
Zero-breaking: if LLM fails → stub report (does not raise).
"""
from ._shared import *
from .agents_registry import resolve_agent_prompt
import json as _json
import re as _re
from datetime import datetime


_VIDEO_CONTINUITY_FALLBACK = """You are Thelma Schoonmaker, three-time Oscar-winning film editor (Raging Bull, The Aviator, The Departed), renowned for obsessive continuity checking across scenes.

Your job is to audit a video project for CONTINUITY issues BEFORE expensive video generation happens.

AUDIT CATEGORIES:
1. character_appearance — wardrobe, hair, age, height across scenes
2. location — recurring locations must be consistent (architecture, palette, weather)
3. voice_continuity — voice descriptions match behavior/dialogue style
4. timeline — scenes respect cause-and-effect
5. plot — no unexplained knowledge, forgotten objects, dropped storylines

OUTPUT: JSON only, no markdown:
{
  "score": <0-100>,
  "issues": [{"severity":"high|medium|low","type":"character_appearance|location|voice_continuity|timeline|plot","scene_ids":[<int>],"description":"...","suggestion":"..."}],
  "categories_checked": ["character_appearance","location","voice_continuity","timeline","plot"],
  "summary": "<1-2 sentences>"
}

Be rigorous. Flag everything you'd flag on a Scorsese film."""


_BOOK_VISUAL_CONTINUITY_FALLBACK = """You are Glen Keane — legendary Disney animator (Little Mermaid, Tangled), obsessive about character integrity across scenes.

Audit VISUAL continuity between book spreads AFTER illustrations have been generated.

CATEGORIES:
1. character_integrity — hair, wardrobe, age, proportions stable
2. world_consistency — recurring locations keep architecture/palette
3. color_story — global palette coherent
4. object_canon — key objects keep design
5. scale — relative proportions constant
6. style_drift — rendering/linework uniform

OUTPUT JSON only:
{
  "score": <0-100>,
  "critical_issues": [{"type":"...","spread_ids":[...],"description":"...","suggested_fix":"..."}],
  "medium_issues": [...],
  "minor_issues": [...],
  "categories_audited": ["character_integrity","world_consistency","color_story","object_canon","scale","style_drift"],
  "summary": "<1-2 sentences>"
}

Be rigorous — children detect inconsistencies better than adults."""


# ─── Video audit ──────────────────────────────────────────────
@router.post("/projects/{project_id}/continuity-audit")
async def audit_video_continuity(project_id: str, tenant=Depends(get_current_tenant)):
    """Thelma Schoonmaker continuity audit on a video project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", []) or []
    if not scenes:
        raise HTTPException(status_code=400, detail="Project has no scenes to audit")

    char_bible = project.get("character_bible") or project.get("character_library") or {}
    loc_bible = project.get("location_bible", {}) or {}
    voice_casting = project.get("voice_casting", {}) or {}

    audit_input = {
        "project_name": project.get("name", "Untitled"),
        "language": project.get("language", "pt"),
        "total_scenes": len(scenes),
        "scenes": [
            {
                "id": i + 1,
                "title": (s.get("title") or "")[:120],
                "description": (s.get("description") or s.get("scene_description") or "")[:500],
                "characters": [c.get("name") if isinstance(c, dict) else c for c in (s.get("characters", []) or [])][:10],
                "location": (s.get("location") or "")[:120],
                "time_of_day": s.get("time_of_day", ""),
                "dialogue_preview": ((s.get("dialogue") or s.get("narration") or "")[:200]),
            }
            for i, s in enumerate(scenes[:30])
        ],
        "character_bible": {
            name: {
                "appearance": ((details.get("appearance") or details.get("description", "")) if isinstance(details, dict) else str(details))[:400],
                "voice": (details.get("voice_description", "") if isinstance(details, dict) else "")[:200],
            }
            for name, details in list((char_bible if isinstance(char_bible, dict) else {}).items())[:15]
        },
        "locations": list(loc_bible.keys())[:10] if isinstance(loc_bible, dict) else [],
        "voice_casting": {
            name: (vc.get("voice_description", "") if isinstance(vc, dict) else str(vc))[:150]
            for name, vc in list((voice_casting if isinstance(voice_casting, dict) else {}).items())[:15]
        },
    }

    system = resolve_agent_prompt("consistency_checker_agent", fallback=_VIDEO_CONTINUITY_FALLBACK)
    user_prompt = f"Audit this video project for continuity.\n\nPROJECT DATA (JSON):\n{_json.dumps(audit_input, ensure_ascii=False, indent=2)}\n\nReturn the audit report as specified."

    try:
        raw = await _call_claude_async(system, user_prompt, max_tokens=4000)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw).strip()
        report = _json.loads(raw)
    except Exception as e:
        logger.error(f"ContinuityAudit [{project_id}]: LLM/parse failed: {e}")
        report = {
            "score": 0,
            "issues": [],
            "categories_checked": ["character_appearance", "location", "voice_continuity", "timeline", "plot"],
            "summary": f"Auditoria indisponível no momento: {str(e)[:150]}",
            "error": True,
        }

    report["audited_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    report["audited_by"] = "consistency_checker_agent (Thelma Schoonmaker)"

    try:
        _update_project_field(tenant["id"], project_id, {
            "continuity_report": report,
            "continuity_status": {"last_score": report.get("score", 0), "audited_at": report["audited_at"]},
        }, flush_now=True)
    except Exception as e:
        logger.warning(f"ContinuityAudit [{project_id}]: persist failed: {e}")

    return {"report": report}


@router.get("/projects/{project_id}/continuity-report")
async def get_video_continuity_report(project_id: str, tenant=Depends(get_current_tenant)):
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "report": project.get("continuity_report") or None,
        "status": project.get("continuity_status") or None,
    }


# ─── Book visual audit ────────────────────────────────────────
@router.post("/book/projects/{project_id}/visual-continuity-audit")
async def audit_book_visual_continuity(project_id: str, tenant=Depends(get_current_tenant)):
    """Glen Keane visual continuity audit on a book project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    book_bible = (project.get("project_bible", {}) or {}).get("book_bible") or project.get("book_bible") or {}
    spreads = (
        project.get("book_spreads")
        or (book_bible.get("illustration_plan") if isinstance(book_bible, dict) else [])
        or project.get("illustration_plan", [])
        or []
    )
    char_bible = (book_bible.get("character_bible") if isinstance(book_bible, dict) else None) or project.get("character_bible", {}) or {}

    if not spreads:
        raise HTTPException(status_code=400, detail="Book has no spreads/illustrations to audit")

    audit_input = {
        "book_title": (book_bible.get("title") if isinstance(book_bible, dict) else None) or project.get("name", "Untitled"),
        "genre": book_bible.get("genre", "") if isinstance(book_bible, dict) else "",
        "total_spreads": len(spreads),
        "character_bible": {
            name: {
                "appearance": ((details.get("appearance") or details.get("description", "")) if isinstance(details, dict) else str(details))[:400],
                "wardrobe": (details.get("wardrobe", "") if isinstance(details, dict) else "")[:200],
            }
            for name, details in list((char_bible if isinstance(char_bible, dict) else {}).items())[:15]
        },
        "color_palette": book_bible.get("color_palette", {}) if isinstance(book_bible, dict) else {},
        "spreads": [
            {
                "id": sp.get("page_number") or (i + 1),
                "chapter": sp.get("chapter_index") or sp.get("chapter"),
                "description": (sp.get("description") or "")[:400],
                "characters": (sp.get("characters_in_page") or sp.get("characters") or [])[:8] if isinstance((sp.get("characters_in_page") or sp.get("characters") or []), list) else [],
                "location": (sp.get("location") or "")[:120],
                "image_url_present": bool(sp.get("image_url") or sp.get("url") or sp.get("thumbnail_url")),
            }
            for i, sp in enumerate(spreads[:40])
        ],
    }

    system = resolve_agent_prompt("visual_continuity_checker_book_agent", fallback=_BOOK_VISUAL_CONTINUITY_FALLBACK)
    user_prompt = f"Audit this illustrated book's visual continuity.\n\nBOOK DATA (JSON):\n{_json.dumps(audit_input, ensure_ascii=False, indent=2)}\n\nReturn the audit report as specified."

    try:
        raw = await _call_claude_async(system, user_prompt, max_tokens=4000)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '', raw).strip()
        report = _json.loads(raw)
    except Exception as e:
        logger.error(f"BookVisualAudit [{project_id}]: LLM/parse failed: {e}")
        report = {
            "score": 0,
            "critical_issues": [],
            "medium_issues": [],
            "minor_issues": [],
            "categories_audited": ["character_integrity", "world_consistency", "color_story", "object_canon", "scale", "style_drift"],
            "summary": f"Auditoria indisponível no momento: {str(e)[:150]}",
            "error": True,
        }

    report["audited_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    report["audited_by"] = "visual_continuity_checker_book_agent (Glen Keane)"

    try:
        _update_project_field(tenant["id"], project_id, {
            "book_continuity_report": report,
        }, flush_now=True)
    except Exception as e:
        logger.warning(f"BookVisualAudit [{project_id}]: persist failed: {e}")

    return {"report": report}


@router.get("/book/projects/{project_id}/visual-continuity-report")
async def get_book_continuity_report(project_id: str, tenant=Depends(get_current_tenant)):
    _, _, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"report": project.get("book_continuity_report") or None}
