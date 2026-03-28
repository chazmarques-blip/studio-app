"""Auto-generated module from studio.py split."""
from ._shared import *

@router.get("/cache/stats")
async def get_cache_stats(tenant=Depends(get_current_tenant)):
    """Get statistics from all cache layers. Requires auth."""
    from core.cache import get_cache_stats
    return get_cache_stats()

@router.post("/cache/flush")
async def flush_cache(tenant=Depends(get_current_tenant)):
    """Force flush all dirty project data to DB. Requires auth."""
    from core.cache import project_cache, image_cache, llm_cache
    project_cache.force_flush()
    image_cache.cleanup()
    llm_cache.cleanup()
    return {"status": "flushed"}



# ── Projects CRUD ──

@router.post("/projects")
async def create_project(req: StudioProject, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    now = datetime.now(timezone.utc).isoformat()
    project = {
        "id": req.id or uuid.uuid4().hex[:12],
        "name": req.name or f"Studio {datetime.now(timezone.utc).strftime('%d/%m %H:%M')}",
        "scene_type": "multi_scene",
        "briefing": req.briefing,
        "avatar_urls": req.avatar_urls,
        "scenes": [],
        "characters": [],
        "character_avatars": {},
        "project_avatars": [],
        "chat_history": [],
        "agents_output": {},
        "agent_status": {},
        "outputs": [],
        "milestones": [{"key": "project_created", "label": "Projecto criado", "done": True, "at": now}],
        "status": "draft",
        "error": None,
        "language": req.language,
        "visual_style": req.visual_style or "animation",
        "audio_mode": req.audio_mode or "narrated",
        "animation_sub": req.animation_sub or "pixar_3d",
        "continuity_mode": req.continuity_mode,
        "created_at": now,
        "updated_at": now,
    }
    projects.insert(0, project)
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return project

@router.get("/projects")
async def list_projects(tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    return {"projects": settings.get("studio_projects", [])}

@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": project.get("status"),
        "chat_status": project.get("chat_status"),
        "chat_history": project.get("chat_history", []),
        "agent_status": project.get("agent_status", {}),
        "agents_output": project.get("agents_output", {}),
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
        "character_avatars": project.get("character_avatars", {}),
        "project_avatars": project.get("project_avatars", []),
        "outputs": project.get("outputs", []),
        "milestones": project.get("milestones", []),
        "narrations": project.get("narrations", []),
        "narration_status": project.get("narration_status", {}),
        "voice_config": project.get("voice_config", {}),
        "visual_style": project.get("visual_style", "animation"),
        "language": project.get("language", "pt"),
        "subtitles": project.get("subtitles", {}),
        "screenplay_approved": project.get("screenplay_approved", False),
        "audio_mode": project.get("audio_mode", "narrated"),
        "storyboard_panels": project.get("storyboard_panels", []),
        "storyboard_status": project.get("storyboard_status", {}),
        "storyboard_approved": project.get("storyboard_approved", False),
        "storyboard_chat_history": project.get("storyboard_chat_history", []),
        "continuity_status": project.get("continuity_status", {}),
        "continuity_report": project.get("continuity_report", {}),
        "error": project.get("error"),
    }

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    projects = [p for p in projects if p.get("id") != project_id]
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return {"status": "ok"}


@router.post("/projects/{project_id}/fix-stuck")
async def fix_stuck_project(project_id: str, tenant=Depends(get_current_tenant)):
    """Fix a stuck project by marking it as error or complete."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    outputs = project.get("outputs", [])
    if any(o.get("url") for o in outputs):
        project["status"] = "complete"
        _add_milestone(project, "fixed_stuck", "Projecto recuperado automaticamente")
    else:
        project["status"] = "scripting"
        project["error"] = None
        # Reset agent status so UI shows ready to restart
        total = len(project.get("scenes", []))
        project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "idle", "videos_done": 0, "scene_status": {}}
        _add_milestone(project, "fixed_stuck", "Produção interrompida — pronto para reiniciar")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": project["status"], "scenes": len(project.get("scenes", []))}



@router.post("/projects/{project_id}/update-characters")
async def update_characters(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update characters list for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["characters"] = payload.get("characters", [])
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _add_milestone(project, "characters_updated", f"Personagens editados — {len(payload.get('characters', []))} personagens")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.put("/projects/{project_id}/character-avatars")
async def update_character_avatars(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update character avatar URLs for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["character_avatars"] = payload.get("character_avatars", {})
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "avatars": len(project["character_avatars"])}


@router.patch("/projects/{project_id}/settings")
async def update_project_settings(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update project-level settings (screenplay_approved, audio_mode, etc.)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    allowed_keys = {"screenplay_approved", "audio_mode", "visual_style", "animation_sub", "continuity_mode", "language"}
    for k, v in payload.items():
        if k in allowed_keys:
            project[k] = v
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    if payload.get("screenplay_approved"):
        _add_milestone(project, "screenplay_approved", "Roteiro aprovado pelo usuário")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}




# ── Project-scoped Avatars ──

@router.get("/projects/{project_id}/project-avatars")
async def get_project_avatars(project_id: str, tenant=Depends(get_current_tenant)):
    """Get avatars that belong to this specific project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"avatars": project.get("project_avatars", [])}


@router.post("/projects/{project_id}/project-avatars")
async def add_project_avatar(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Add/update an avatar in this project's local pool."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    avatar = payload.get("avatar", {})
    if not avatar.get("id"):
        avatar["id"] = uuid.uuid4().hex[:12]
    avatar["added_at"] = datetime.now(timezone.utc).isoformat()

    project_avatars = project.get("project_avatars", [])
    existing_idx = next((i for i, a in enumerate(project_avatars) if a.get("id") == avatar["id"]), None)
    if existing_idx is not None:
        project_avatars[existing_idx] = {**project_avatars[existing_idx], **avatar}
    else:
        project_avatars.append(avatar)

    project["project_avatars"] = project_avatars
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    # Also persist to global library if save_to_library flag is set
    if payload.get("save_to_library", True):
        global_avatars = settings.get("studio_avatars", [])
        g_idx = next((i for i, a in enumerate(global_avatars) if a.get("id") == avatar["id"]), None)
        lib_doc = {k: v for k, v in avatar.items() if k != "added_at"}
        lib_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        if g_idx is not None:
            lib_doc["created_at"] = global_avatars[g_idx].get("created_at", lib_doc["updated_at"])
            global_avatars[g_idx] = lib_doc
        else:
            lib_doc["created_at"] = lib_doc["updated_at"]
            global_avatars.append(lib_doc)
        settings["studio_avatars"] = global_avatars
        _save_settings(tenant["id"], settings)

    return {"status": "ok", "avatar": avatar}


@router.post("/projects/{project_id}/project-avatars/import")
async def import_avatar_from_library(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Import one or more avatars from the global library into a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    avatar_ids = payload.get("avatar_ids", [])
    if not avatar_ids:
        raise HTTPException(status_code=400, detail="No avatar_ids provided")

    global_avatars = settings.get("studio_avatars", [])
    project_avatars = project.get("project_avatars", [])
    existing_ids = {a["id"] for a in project_avatars}
    imported = 0

    for aid in avatar_ids:
        if aid in existing_ids:
            continue
        source = next((a for a in global_avatars if a.get("id") == aid), None)
        if source:
            copy = {**source, "added_at": datetime.now(timezone.utc).isoformat()}
            project_avatars.append(copy)
            imported += 1

    project["project_avatars"] = project_avatars
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "imported": imported, "total": len(project_avatars)}


@router.delete("/projects/{project_id}/project-avatars/{avatar_id}")
async def remove_project_avatar(project_id: str, avatar_id: str, tenant=Depends(get_current_tenant)):
    """Remove an avatar from a project (does NOT delete from global library)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_avatars = project.get("project_avatars", [])
    project["project_avatars"] = [a for a in project_avatars if a.get("id") != avatar_id]

    # Also unlink from character_avatars if the removed avatar was linked
    removed_av = next((a for a in project_avatars if a.get("id") == avatar_id), None)
    if removed_av:
        char_avatars = project.get("character_avatars", {})
        project["character_avatars"] = {k: v for k, v in char_avatars.items() if v != removed_av.get("url")}

    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}
