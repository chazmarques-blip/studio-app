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
def resolve_agent_prompt(agent_id: str, fallback: str) -> str:
    """
    Returns the JSON-registry system_prompt if present AND active,
    otherwise returns the hardcoded fallback — ensuring zero breakage.

    Usage in any pipeline router:
        from .agents_registry import resolve_agent_prompt
        HARDCODED = "Você é um roteirista..."
        prompt = resolve_agent_prompt("screenwriter_agent", fallback=HARDCODED)
    """
    try:
        path = _resolve_agent_path(agent_id)
        if not path:
            return fallback
        data = _load_agent_file(path)
        if not data:
            return fallback
        if data.get("active") is False:
            return fallback
        prompt = data.get("system_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            return fallback
        return prompt
    except Exception as e:
        logger.warning(f"resolve_agent_prompt({agent_id}) failed, using fallback: {e}")
        return fallback
