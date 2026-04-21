"""
StudioX — Agent Activity Tracker
Records which agent is currently "thinking" (running) for a given project, so
the UI can surface real-time visual feedback ("Aaron Sorkin está escrevendo…").

Design: ADDITIVE. Zero breakage — if this module fails silently, pipelines keep
running. Writes to `project.active_agent` and appends to `project.agent_timeline`
(capped to the most recent 20 entries).
"""
from ._shared import *
from .agents_registry import _resolve_agent_path, _load_agent_file
from datetime import datetime, timezone
from typing import Optional as Opt

# Cap timeline to avoid unbounded growth
_TIMELINE_CAP = 20


def _enrich_agent_meta(agent_id: str) -> dict:
    """Look up agent registry metadata (name + master_reference)."""
    try:
        path = _resolve_agent_path(agent_id)
        if not path:
            return {"id": agent_id, "name": agent_id, "master_reference": None}
        data = _load_agent_file(path) or {}
        return {
            "id": agent_id,
            "name": data.get("name") or agent_id,
            "master_reference": data.get("master_reference"),
            "phase": data.get("phase"),
        }
    except Exception:
        return {"id": agent_id, "name": agent_id, "master_reference": None}


def set_active_agent(
    tenant_id: str,
    project_id: str,
    agent_id: str,
    action: str = "thinking",
    meta: Opt[dict] = None,
) -> None:
    """
    Mark an agent as currently active on a project. Safe to call in background
    tasks — all errors are swallowed to avoid breaking pipelines.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        enriched = _enrich_agent_meta(agent_id)
        active = {
            "agent_id": agent_id,
            "name": enriched["name"],
            "master_reference": enriched.get("master_reference"),
            "action": action,
            "started_at": now,
            **(meta or {}),
        }

        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        project["active_agent"] = active

        # Append to timeline (dedupe consecutive identical entries)
        timeline = project.get("agent_timeline") or []
        if not timeline or timeline[-1].get("agent_id") != agent_id or timeline[-1].get("action") != action:
            timeline.append({
                "agent_id": agent_id,
                "name": enriched["name"],
                "master_reference": enriched.get("master_reference"),
                "action": action,
                "at": now,
            })
            # Cap
            if len(timeline) > _TIMELINE_CAP:
                timeline = timeline[-_TIMELINE_CAP:]
            project["agent_timeline"] = timeline

        project["updated_at"] = now
        _save_project(tenant_id, settings, projects, flush_now=True)
    except Exception as e:
        logger.warning(f"set_active_agent({agent_id}) failed silently: {e}")


def clear_active_agent(tenant_id: str, project_id: str) -> None:
    """Clear the active agent marker — call when a pipeline phase completes."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        if project.get("active_agent"):
            project["active_agent"] = None
            project["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_project(tenant_id, settings, projects, flush_now=True)
    except Exception as e:
        logger.warning(f"clear_active_agent failed silently: {e}")


@router.get("/projects/{project_id}/active-agent")
async def get_active_agent(project_id: str, user=Depends(get_current_user)):
    """
    Returns the agent currently "thinking" on this project (if any), plus the
    last 20 activity entries. Polled by the frontend every ~2s.
    """
    tenant_id = user["tenant_id"]
    _, _, project = _get_project(tenant_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    active = project.get("active_agent")
    timeline = project.get("agent_timeline") or []

    # Auto-expire active_agent if stale (>10 minutes) — safety net in case a
    # background task crashed without clearing.
    if active:
        try:
            started = datetime.fromisoformat(active.get("started_at"))
            age_seconds = (datetime.now(timezone.utc) - started).total_seconds()
            if age_seconds > 600:
                active = None
        except Exception:
            pass

    return {
        "active_agent": active,
        "timeline": timeline[-10:],  # last 10 only
    }
