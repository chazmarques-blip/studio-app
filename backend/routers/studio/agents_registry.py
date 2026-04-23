"""
StudioX Agents Registry
Single source of truth for all AI agent prompts across Video / Book / Audio pipelines.

Folder structure:
  /app/memory/agents/             → Video pipeline agents (+ shared)
  /app/memory/agents/book/        → Book pipeline agents
"""
from ._shared import *
from typing import Dict, Optional as Opt
import os
import json
from datetime import datetime

AGENTS_DIR = "/app/memory/agents"
BOOK_AGENTS_DIR = "/app/memory/agents/book"
MINDSETS_FILE = "/app/memory/agents/_mindsets.json"

# ─── Category map ─────────────────────────────────────────────
# Explicit mapping — keeps UI deterministic even if folders change
VIDEO_AGENTS = {
    "orchestrator_agent", "researcher_agent", "screenwriter_agent",
    "dialogue_writer_agent", "narrator_agent", "visual_researcher_agent",
    "consistency_checker_agent", "quality_validator_agent",
}
AUDIO_AGENTS = {"sound_designer_agent"}
# Anything in /book/ subfolder = book category (dynamic)


def _load_agent_file(path: str) -> Opt[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"AgentsRegistry: Failed to load {path}: {e}")
        return None


def _resolve_agent_path(agent_id: str) -> Opt[str]:
    """Find an agent JSON in either the root or book/ folder."""
    root_path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
    if os.path.exists(root_path):
        return root_path
    book_path = os.path.join(BOOK_AGENTS_DIR, f"{agent_id}.json")
    if os.path.exists(book_path):
        return book_path
    return None


def _categorize(agent_id: str, file_path: str) -> str:
    if BOOK_AGENTS_DIR in file_path:
        return "book"
    if agent_id in AUDIO_AGENTS:
        return "audio"
    return "video"


@router.get("/agents/registry")
async def list_studio_agents(user=Depends(get_current_user)):
    """List all StudioX AI agents across all pipelines."""
    agents = []

    # Scan root folder
    if os.path.isdir(AGENTS_DIR):
        for fname in sorted(os.listdir(AGENTS_DIR)):
            if not fname.endswith(".json"):
                continue
            # Skip meta/index files (mindsets, compositions)
            if fname.startswith("_") or fname in ("agent_compositions.json",):
                continue
            fpath = os.path.join(AGENTS_DIR, fname)
            data = _load_agent_file(fpath)
            if not data:
                continue
            agent_id = data.get("id") or fname.replace(".json", "")
            agents.append({
                "id": agent_id,
                "name": data.get("name"),
                "phase": data.get("phase"),
                "version": data.get("version"),
                "description": data.get("description"),
                "category": _categorize(agent_id, fpath),
                "active": data.get("active", True),
                "updated_at": data.get("updated_at"),
                "model": data.get("model", "claude-sonnet-4-5"),
                "master_reference": data.get("master_reference"),
            })

    # Scan book subfolder
    if os.path.isdir(BOOK_AGENTS_DIR):
        for fname in sorted(os.listdir(BOOK_AGENTS_DIR)):
            if not fname.endswith(".json"):
                continue
            # Skip compositions/index files that aren't actual agents
            if fname in ("agent_compositions.json",):
                continue
            fpath = os.path.join(BOOK_AGENTS_DIR, fname)
            data = _load_agent_file(fpath)
            if not data or not data.get("name"):
                continue
            agent_id = data.get("id") or fname.replace(".json", "")
            agents.append({
                "id": agent_id,
                "name": data.get("name"),
                "phase": data.get("phase"),
                "version": data.get("version"),
                "description": data.get("description"),
                "category": "book",
                "active": data.get("active", True),
                "updated_at": data.get("updated_at"),
                "model": data.get("model", "claude-sonnet-4-5"),
                "master_reference": data.get("master_reference"),
            })

    # Sort: category (video → book → audio) then phase then name
    cat_order = {"video": 1, "book": 2, "audio": 3}
    phase_order = {"research": 1, "consensus": 2, "production": 3, "validation": 4, "execution": 5}
    agents.sort(key=lambda a: (
        cat_order.get(a.get("category") or "", 99),
        phase_order.get(a.get("phase") or "", 99),
        a.get("name") or "",
    ))

    return {"agents": agents, "total": len(agents)}


@router.get("/agents/registry/{agent_id}")
async def get_studio_agent(agent_id: str, user=Depends(get_current_user)):
    """Get full specification of an agent."""
    path = _resolve_agent_path(agent_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    data = _load_agent_file(path)
    if not data:
        raise HTTPException(status_code=500, detail=f"Failed to read agent: {agent_id}")
    data["category"] = _categorize(agent_id, path)
    return {"agent": data}


@router.put("/agents/registry/{agent_id}")
async def update_studio_agent(
    agent_id: str,
    agent_data: Dict,
    user=Depends(get_current_user)
):
    """Update agent specification. Appends previous version to edit_history for rollback."""
    path = _resolve_agent_path(agent_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    prev = _load_agent_file(path) or {}
    history = prev.get("edit_history", [])
    # Keep only editable fields in history snapshot to avoid bloat
    history.append({
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "by": (user.get("email") if isinstance(user, dict) else getattr(user, "email", None)) or "unknown",
        "system_prompt": prev.get("system_prompt"),
        "temperature": prev.get("temperature"),
        "min_quality_score": prev.get("min_quality_score"),
    })
    # Keep last 20 entries
    history = history[-20:]

    # Merge: new data wins, but preserve id / category / history
    merged = {**prev, **agent_data}
    merged["id"] = prev.get("id", agent_id)
    merged["edit_history"] = history
    merged["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info(f"AgentsRegistry: Updated {agent_id} (history={len(history)})")
    return {"status": "updated", "agent_id": agent_id, "history_size": len(history)}


@router.post("/agents/registry/{agent_id}/rollback")
async def rollback_agent(agent_id: str, body: Dict = Body(default={}), user=Depends(get_current_user)):
    """Rollback to a previous version from edit_history. index=0 is oldest."""
    path = _resolve_agent_path(agent_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    data = _load_agent_file(path) or {}
    history = data.get("edit_history", [])
    if not history:
        raise HTTPException(status_code=400, detail="No history available")

    idx = int(body.get("index", len(history) - 1))
    if idx < 0 or idx >= len(history):
        raise HTTPException(status_code=400, detail=f"Invalid history index {idx}")
    target = history[idx]

    # Restore
    data["system_prompt"] = target.get("system_prompt", data.get("system_prompt"))
    if target.get("temperature") is not None:
        data["temperature"] = target.get("temperature")
    if target.get("min_quality_score") is not None:
        data["min_quality_score"] = target.get("min_quality_score")
    # Append the restoration as a new history entry
    history.append({
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "by": (user.get("email") if isinstance(user, dict) else getattr(user, "email", None)) or "unknown",
        "note": f"rollback to index {idx}",
        "system_prompt": data.get("system_prompt"),
    })
    data["edit_history"] = history[-20:]
    data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"status": "rolled_back", "agent_id": agent_id, "index": idx}


# ─── Runtime helper for pipeline routers ──────────────────────
def _load_mindsets() -> dict:
    try:
        if not os.path.exists(MINDSETS_FILE):
            return {}
        with open(MINDSETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f) or {}
    except Exception as e:
        logger.warning(f"mindsets load failed: {e}")
        return {}


def _save_mindsets(mindsets: dict) -> None:
    try:
        os.makedirs(os.path.dirname(MINDSETS_FILE), exist_ok=True)
        with open(MINDSETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(mindsets or {}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"mindsets save failed: {e}")


def _get_agent_category(agent_id: str) -> Opt[str]:
    path = _resolve_agent_path(agent_id)
    if not path:
        return None
    return _categorize(agent_id, path)


def resolve_category_mindset(category: str) -> Opt[str]:
    """Returns the global mindset system_prompt for a category if active, else None."""
    try:
        mindsets = _load_mindsets()
        m = mindsets.get(category) or {}
        if m.get("active") and isinstance(m.get("system_prompt"), str) and m["system_prompt"].strip():
            return m["system_prompt"]
    except Exception as e:
        logger.warning(f"resolve_category_mindset({category}) failed: {e}")
    return None


def resolve_agent_prompt(agent_id: str, fallback: str, lang: Opt[str] = None) -> str:
    """
    Returns the final system prompt to feed the LLM, combining (in this order):
      0. Output-language directive (if `lang` is provided — e.g. "pt", "en", "es")
      1. Category Mindset (if active)
      2. Agent's custom system_prompt (if active) OR the hardcoded fallback

    All layers are optional — the function is defensive and ALWAYS returns a non-empty
    string (fallback at minimum), ensuring pipeline never breaks.

    The language directive is short and explicit so even strong creative prompts stay
    in the requested language (Claude/GPT tend to default to English otherwise).

    Usage in pipeline routers:
        from .agents_registry import resolve_agent_prompt
        HARDCODED = "Você é um roteirista..."
        prompt = resolve_agent_prompt("screenwriter_agent", fallback=HARDCODED, lang="pt")
    """
    try:
        # Layer 1: resolve the agent's own prompt
        agent_prompt = fallback
        path = _resolve_agent_path(agent_id)
        if path:
            data = _load_agent_file(path)
            if data and data.get("active") is True:
                p = data.get("system_prompt")
                if isinstance(p, str) and p.strip():
                    agent_prompt = p

        # Layer 2: prepend category mindset if active
        category = _get_agent_category(agent_id) or "video"
        mindset = resolve_category_mindset(category)
        combined = f"{mindset}\n\n---\n\n{agent_prompt}" if mindset else agent_prompt

        # Layer 0: prepend language directive
        if lang:
            lang_name = {
                "pt": "Portuguese (Brazilian)",
                "pt-br": "Portuguese (Brazilian)",
                "en": "English",
                "es": "Spanish",
                "fr": "French",
                "it": "Italian",
                "de": "German",
                "ja": "Japanese",
            }.get(lang.lower(), lang)
            lang_header = (
                f"## OUTPUT LANGUAGE: {lang_name}\n"
                f"ALL narrative text, dialogue, scene descriptions, and any written output "
                f"MUST be in {lang_name}. Technical JSON field names stay in English, but "
                f"VALUES (descriptions, dialogue, notes) must be in {lang_name}.\n\n"
            )
            return lang_header + combined

        return combined
    except Exception as e:
        logger.warning(f"resolve_agent_prompt({agent_id}) failed, using fallback: {e}")
        return fallback


# ─── Mindsets endpoints ───────────────────────────────────────
@router.get("/agents/mindsets")
async def list_mindsets(user=Depends(get_current_user)):
    """List all category mindsets (video / book / audio)."""
    mindsets = _load_mindsets()
    return {"mindsets": mindsets, "categories": list(mindsets.keys())}


@router.get("/agents/mindsets/{category}")
async def get_mindset(category: str, user=Depends(get_current_user)):
    mindsets = _load_mindsets()
    m = mindsets.get(category)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mindset not found: {category}")
    return {"mindset": m}


@router.put("/agents/mindsets/{category}")
async def update_mindset(
    category: str,
    body: Dict,
    user=Depends(get_current_user)
):
    """Update a category mindset. Appends previous state to edit_history."""
    mindsets = _load_mindsets()
    if category not in mindsets:
        raise HTTPException(status_code=404, detail=f"Mindset not found: {category}")

    prev = mindsets[category]
    history = prev.get("edit_history", [])
    history.append({
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "by": (user.get("email") if isinstance(user, dict) else getattr(user, "email", None)) or "unknown",
        "system_prompt": prev.get("system_prompt"),
        "temperature": prev.get("temperature"),
    })
    history = history[-20:]

    merged = {**prev, **body}
    merged["id"] = prev.get("id", f"mindset_{category}")
    merged["category"] = category
    merged["edit_history"] = history
    merged["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
    mindsets[category] = merged

    with open(MINDSETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(mindsets, f, indent=2, ensure_ascii=False)

    logger.info(f"Mindsets: Updated {category}")
    return {"status": "updated", "category": category, "history_size": len(history)}


# ─── Playground endpoint ──────────────────────────────────────
class PlaygroundRequest(BaseModel):
    agent_id: str
    system_prompt: Opt[str] = None  # user's unsaved system prompt to test
    user_input: str
    temperature: Opt[float] = 0.7
    include_mindset: Opt[bool] = True
    mindset_prompt: Opt[str] = None  # if provided, overrides saved mindset for preview


@router.post("/agents/playground")
async def playground_test(req: PlaygroundRequest, user=Depends(get_current_user)):
    """
    Quick test of an agent prompt WITHOUT saving it.
    Returns the LLM output using the provided (unsaved) system_prompt + user_input.
    Uses Emergent LLM Key infrastructure.
    """
    if not req.user_input or not req.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input is required")

    # Resolve the full prompt: custom mindset (or saved) + custom agent prompt (or saved)
    category = _get_agent_category(req.agent_id) or "video"
    agent_prompt = req.system_prompt
    if not agent_prompt:
        # Fallback to saved prompt
        path = _resolve_agent_path(req.agent_id)
        if path:
            data = _load_agent_file(path) or {}
            agent_prompt = data.get("system_prompt", "")
    agent_prompt = agent_prompt or "You are a helpful assistant."

    final_prompt = agent_prompt
    if req.include_mindset:
        mindset = req.mindset_prompt
        if not mindset:
            mindset = resolve_category_mindset(category) or ""
            if not mindset:
                # Even if not active, use saved mindset for preview
                m = _load_mindsets().get(category) or {}
                mindset = m.get("system_prompt", "")
        if mindset and mindset.strip():
            final_prompt = f"{mindset}\n\n---\n\n{agent_prompt}"

    # Call Claude via emergentintegrations (already used in _shared)
    try:
        output = await asyncio.to_thread(
            _call_claude_sync,
            final_prompt,
            req.user_input,
            3000  # max_tokens for playground (keep snappy)
        )
        return {
            "output": output or "",
            "agent_id": req.agent_id,
            "category": category,
            "prompt_length": len(final_prompt),
            "mindset_applied": bool(req.include_mindset and (req.mindset_prompt or resolve_category_mindset(category))),
        }
    except Exception as e:
        logger.error(f"Playground error for {req.agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)[:200]}")




# ─── Mindset Templates (Dream Team bundles) ──────────────────
MINDSET_TEMPLATES_FILE = "/app/memory/agents/_mindset_templates.json"


def _load_mindset_templates() -> list:
    try:
        if not os.path.exists(MINDSET_TEMPLATES_FILE):
            return []
        with open(MINDSET_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f) or {}
        return data.get("templates", [])
    except Exception as e:
        logger.warning(f"mindset_templates load failed: {e}")
        return []


@router.get("/agents/mindset-templates")
async def list_mindset_templates(user=Depends(get_current_user)):
    """List all available mindset templates (Dream Team bundles)."""
    templates = _load_mindset_templates()
    # Attach which template is currently active per category (if any)
    mindsets = _load_mindsets()
    active_by_category = {}
    for cat, m in (mindsets or {}).items():
        if m and m.get("active") and m.get("template_id"):
            active_by_category[cat] = m.get("template_id")
    return {
        "templates": templates,
        "active_by_category": active_by_category,
        "count": len(templates),
    }


class ApplyTemplateRequest(BaseModel):
    template_id: str
    category: Opt[str] = "video"
    apply_to_agents: Opt[bool] = True  # also update master_reference + temperature on each agent
    overwrite_system_prompt: Opt[bool] = False  # stronger mode (not default for safety)


@router.post("/agents/mindset-templates/apply")
async def apply_mindset_template(req: ApplyTemplateRequest, user=Depends(get_current_user)):
    """
    Apply a mindset template (Dream Team) to:
      - The category mindset (system_prompt + temperature + activate it)
      - Each listed agent: master_reference + temperature (and optionally system_prompt)
    All changes are appended to `edit_history` for rollback.
    """
    templates = _load_mindset_templates()
    tpl = next((t for t in templates if t.get("id") == req.template_id), None)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template not found: {req.template_id}")

    category = req.category or tpl.get("category") or "video"
    user_email = (user.get("email") if isinstance(user, dict) else getattr(user, "email", None)) or "unknown"
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # ─── 1. Apply mindset prompt to category ───
    mindsets = _load_mindsets()
    prev_mindset = mindsets.get(category) or {}
    history = list(prev_mindset.get("edit_history", []))
    history.append({
        "timestamp": ts,
        "by": user_email,
        "system_prompt": prev_mindset.get("system_prompt"),
        "temperature": prev_mindset.get("temperature"),
        "source": f"template_apply:{req.template_id}",
    })
    history = history[-20:]

    mindsets[category] = {
        **prev_mindset,
        "id": prev_mindset.get("id", f"mindset_{category}"),
        "category": category,
        "title": prev_mindset.get("title") or f"Mentalidade Global · {category}",
        "master_reference": tpl.get("name"),
        "active": True,
        "template_id": req.template_id,
        "system_prompt": tpl.get("mindset_prompt", ""),
        "temperature": tpl.get("mindset_temperature", 0.7),
        "edit_history": history,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    _save_mindsets(mindsets)

    # ─── 2. Apply per-agent overrides ───
    agent_updates = []
    if req.apply_to_agents:
        for a_cfg in tpl.get("agents") or []:
            aid = a_cfg.get("agent_id")
            if not aid:
                continue
            path = _resolve_agent_path(aid)
            if not path:
                logger.warning(f"apply_template: agent not found: {aid}")
                continue
            data = _load_agent_file(path) or {}

            # Backup to agent's edit_history
            a_history = list(data.get("edit_history", []))
            a_history.append({
                "timestamp": ts,
                "by": user_email,
                "master_reference": data.get("master_reference"),
                "temperature": data.get("temperature"),
                "system_prompt": data.get("system_prompt") if req.overwrite_system_prompt else None,
                "source": f"template_apply:{req.template_id}",
            })
            a_history = a_history[-20:]

            data["master_reference"] = a_cfg.get("master_reference") or data.get("master_reference")
            if a_cfg.get("temperature") is not None:
                data["temperature"] = a_cfg.get("temperature")
            if req.overwrite_system_prompt and a_cfg.get("system_prompt"):
                data["system_prompt"] = a_cfg["system_prompt"]
            data["edit_history"] = a_history
            data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")

            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                agent_updates.append({
                    "agent_id": aid,
                    "master_reference": data["master_reference"],
                    "temperature": data.get("temperature"),
                })
            except Exception as e:
                logger.error(f"apply_template: failed to save agent {aid}: {e}")

    logger.info(
        f"MindsetTemplates: applied '{req.template_id}' to category '{category}' "
        f"(agents updated: {len(agent_updates)}, by: {user_email})"
    )
    return {
        "status": "applied",
        "template_id": req.template_id,
        "template_name": tpl.get("name"),
        "category": category,
        "mindset_activated": True,
        "agents_updated": agent_updates,
        "production_quality": tpl.get("production_quality"),
        "visual_style": tpl.get("visual_style"),
    }


@router.post("/agents/mindset-templates/deactivate")
async def deactivate_mindset_template(category: str = "video", user=Depends(get_current_user)):
    """Deactivate the current category mindset (does not restore agent overrides)."""
    mindsets = _load_mindsets()
    m = mindsets.get(category)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mindset not found: {category}")
    m["active"] = False
    m["template_id"] = None
    m["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
    mindsets[category] = m
    _save_mindsets(mindsets)
    return {"status": "deactivated", "category": category}


# ─── Export / Import (Dream Team backup & share) ──────────────
@router.get("/agents/export")
async def export_agents_config(user=Depends(get_current_user)):
    """
    Export the FULL agents registry (all agents + mindsets) as a single JSON
    payload. Useful for backups, sharing a "Dream Team", or migrating between
    environments.
    """
    agents_out = []

    def _scan(folder: str):
        if not os.path.isdir(folder):
            return
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".json"):
                continue
            if fname.startswith("_") or fname in ("agent_compositions.json",):
                continue
            fpath = os.path.join(folder, fname)
            data = _load_agent_file(fpath)
            if not data:
                continue
            agent_id = data.get("id") or fname.replace(".json", "")
            # Strip edit_history to keep export small & portable
            clean = {k: v for k, v in data.items() if k != "edit_history"}
            clean["id"] = agent_id
            clean["_category"] = _categorize(agent_id, fpath)
            agents_out.append(clean)

    _scan(AGENTS_DIR)
    _scan(BOOK_AGENTS_DIR)

    mindsets = _load_mindsets()

    return {
        "format_version": 1,
        "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "studiox_version": "1.0",
        "agents": agents_out,
        "mindsets": mindsets,
        "counts": {"agents": len(agents_out), "mindsets": len(mindsets or {})},
    }


class ImportPayload(BaseModel):
    format_version: Opt[int] = 1
    agents: Opt[list] = None
    mindsets: Opt[dict] = None
    overwrite: Opt[bool] = False  # if True, replace existing; else only add missing


@router.post("/agents/import")
async def import_agents_config(
    payload: ImportPayload = Body(...),
    user=Depends(get_current_user),
):
    """
    Import an agents registry bundle. By default only ADDS agents/mindsets that
    don't already exist — pass overwrite=true to replace everything.
    Returns counts of imported / skipped / errors.
    """
    if payload.format_version and payload.format_version != 1:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format_version: {payload.format_version}",
        )

    imported = 0
    skipped = 0
    errors = []

    for a in (payload.agents or []):
        try:
            agent_id = a.get("id")
            if not agent_id:
                errors.append({"reason": "missing id", "agent": (a.get("name") or "?")})
                continue

            category = a.get("_category") or _categorize(agent_id, "")
            target_folder = BOOK_AGENTS_DIR if category == "book" else AGENTS_DIR
            os.makedirs(target_folder, exist_ok=True)
            target_path = os.path.join(target_folder, f"{agent_id}.json")

            if os.path.exists(target_path) and not payload.overwrite:
                skipped += 1
                continue

            # Clean out internal-only fields
            clean = {k: v for k, v in a.items() if not k.startswith("_")}
            clean["id"] = agent_id
            clean["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(clean, f, indent=2, ensure_ascii=False)
            imported += 1
        except Exception as e:
            errors.append({"agent_id": a.get("id"), "error": str(e)[:200]})

    # Import mindsets
    mindsets_imported = 0
    if payload.mindsets:
        try:
            current = _load_mindsets()
            for category, m in (payload.mindsets or {}).items():
                if category in current and not payload.overwrite:
                    continue
                current[category] = m
                mindsets_imported += 1
            _save_mindsets(current)
        except Exception as e:
            errors.append({"mindsets_error": str(e)[:200]})

    logger.info(
        f"AgentsRegistry import: {imported} agents + {mindsets_imported} mindsets "
        f"(skipped={skipped}, errors={len(errors)}, overwrite={payload.overwrite})"
    )
    return {
        "status": "ok",
        "imported_agents": imported,
        "imported_mindsets": mindsets_imported,
        "skipped": skipped,
        "errors": errors,
    }
