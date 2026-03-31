"""Migration endpoint to upgrade projects to V2 (with dialogue timeline + DoP)"""
from ._shared import *
from core.dialogue_timeline import batch_enrich_scenes_with_timeline
from core.cinematographer import generate_camera_plan


@router.post("/projects/{project_id}/migrate-to-v2")
async def migrate_project_to_v2(project_id: str, tenant=Depends(get_current_tenant)):
    """
    Migrates existing project to V2 with new features:
    - Dialogue timeline (timing sync)
    - Camera plan (DoP)
    - Format strategy
    
    This does NOT regenerate storyboards or videos.
    It only adds the new data structures for future generations.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="Project has no scenes to migrate")
    
    logger.info(f"Migration [{project_id}]: Starting V2 migration for {len(scenes)} scenes")
    
    # Mark as migrating
    project["migration_status"] = {
        "phase": "starting",
        "version": "v2",
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    _save_project(tenant["id"], settings, projects)
    
    # Run migration in background
    def _bg_migrate():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return
            
            _scenes = _project.get("scenes", [])
            characters = _project.get("characters", [])
            production_design = _project.get("agents_output", {}).get("production_design", {})
            
            # STEP 1: Generate dialogue timelines
            logger.info(f"Migration [{project_id}]: Step 1/2 - Generating dialogue timelines")
            _project["migration_status"]["phase"] = "dialogue_timelines"
            _save_project(tenant["id"], _settings, _projects)
            
            enriched_scenes = batch_enrich_scenes_with_timeline(_scenes, project_id=project_id)
            _project["scenes"] = enriched_scenes
            
            timeline_count = len([s for s in enriched_scenes if s.get("dialogue_timeline")])
            logger.info(f"Migration [{project_id}]: {timeline_count}/{len(_scenes)} scenes have timelines")
            
            # STEP 2: Generate camera plan
            logger.info(f"Migration [{project_id}]: Step 2/2 - Generating camera plan")
            _project["migration_status"]["phase"] = "camera_plan"
            _save_project(tenant["id"], _settings, _projects)
            
            # Default to safe_zone if not specified
            format_strategy = _project.get("format_strategy", "safe_zone")
            formats_requested = _project.get("formats_requested", ["16:9"])
            
            camera_plan = generate_camera_plan(
                project_id=project_id,
                scenes=enriched_scenes,
                characters=characters,
                production_design=production_design,
                format_strategy=format_strategy,
                formats_requested=formats_requested,
                lang=_project.get("language", "pt")
            )
            
            if "agents_output" not in _project:
                _project["agents_output"] = {}
            _project["agents_output"]["camera_plan"] = camera_plan
            
            # Mark as complete
            _project["migration_status"] = {
                "phase": "complete",
                "version": "v2",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "timelines_added": timeline_count,
                "camera_plan_added": True
            }
            _project["v2_migrated"] = True
            _project["v2_migrated_at"] = datetime.now(timezone.utc).isoformat()
            
            _add_milestone(_project, "v2_migration", f"Migrado para V2: {timeline_count} timelines + camera plan")
            _save_project(tenant["id"], _settings, _projects)
            
            logger.info(f"Migration [{project_id}]: Complete - V2 features added")
            
        except Exception as e:
            logger.error(f"Migration [{project_id}]: Failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "migration_status": {
                    "phase": "error",
                    "error": str(e)[:200]
                }
            })
    
    import threading
    thread = threading.Thread(target=_bg_migrate, daemon=True)
    thread.start()
    
    return {
        "status": "migrating",
        "message": "V2 migration started - adding dialogue timelines and camera plan",
        "total_scenes": len(scenes)
    }


@router.get("/projects/{project_id}/migration-status")
async def get_migration_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get V2 migration status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    is_v2 = project.get("v2_migrated", False)
    migration_status = project.get("migration_status", {})
    
    return {
        "is_v2": is_v2,
        "migrated_at": project.get("v2_migrated_at"),
        "migration_status": migration_status,
        "has_timelines": any(s.get("dialogue_timeline") for s in project.get("scenes", [])),
        "has_camera_plan": bool(project.get("agents_output", {}).get("camera_plan"))
    }
