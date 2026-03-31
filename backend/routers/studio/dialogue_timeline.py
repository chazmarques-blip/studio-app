"""Dialogue Timeline Endpoints for StudioX"""
from ._shared import *
from core.dialogue_timeline import generate_dialogue_timeline, enrich_scene_with_timeline, batch_enrich_scenes_with_timeline


class DialogueTimelineRequest(BaseModel):
    scene_numbers: list = None  # Optional: specific scenes to process, or None for all


@router.post("/projects/{project_id}/dialogue-timeline/generate")
async def generate_dialogue_timelines(
    project_id: str,
    req: DialogueTimelineRequest = None,
    tenant=Depends(get_current_tenant)
):
    """
    Generate or regenerate dialogue timelines for scenes.
    
    This creates precise timing for each dialogue line, which is used by:
    - Storyboard generation (to sync frames with dialogue)
    - Video production (to create accurate Sora 2 prompts)
    - Audio production (to sync voices)
    
    Args:
        scene_numbers: Optional list of scene numbers to process. If None, processes all scenes.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes found in project")
    
    # Determine which scenes to process
    if req and req.scene_numbers:
        scenes_to_process = [s for s in scenes if s.get("scene_number") in req.scene_numbers]
    else:
        scenes_to_process = scenes
    
    if not scenes_to_process:
        raise HTTPException(status_code=400, detail="No scenes to process")
    
    logger.info(f"DialogueTimeline [{project_id}]: Processing {len(scenes_to_process)} scenes")
    
    # Mark as processing
    project["dialogue_timeline_status"] = {
        "phase": "generating",
        "current": 0,
        "total": len(scenes_to_process)
    }
    _save_project(tenant["id"], settings, projects)
    
    # Process in background
    def _bg_generate():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return
            
            _scenes = _project.get("scenes", [])
            processed_count = 0
            
            for scene in _scenes:
                scene_num = scene.get("scene_number")
                
                # Skip if not in the list to process
                if req and req.scene_numbers and scene_num not in req.scene_numbers:
                    continue
                
                # Enrich this scene
                enriched_scene = enrich_scene_with_timeline(scene, project_id=project_id)
                
                # Update the scene in the project
                for i, s in enumerate(_scenes):
                    if s.get("scene_number") == scene_num:
                        _scenes[i] = enriched_scene
                        break
                
                processed_count += 1
                
                # Update progress
                _update_project_field(tenant["id"], project_id, {
                    "scenes": _scenes,
                    "dialogue_timeline_status": {
                        "phase": "generating",
                        "current": processed_count,
                        "total": len(scenes_to_process)
                    }
                })
            
            # Mark as complete
            _update_project_field(tenant["id"], project_id, {
                "dialogue_timeline_status": {
                    "phase": "complete",
                    "current": processed_count,
                    "total": processed_count
                },
                "dialogue_timeline_generated_at": datetime.now(timezone.utc).isoformat()
            })
            
            _add_milestone(_project, "dialogue_timeline_generated", f"Timeline gerada para {processed_count} cenas")
            _save_project(tenant["id"], _settings, _projects)
            
            logger.info(f"DialogueTimeline [{project_id}]: Complete - {processed_count} scenes enriched")
            
        except Exception as e:
            logger.error(f"DialogueTimeline [{project_id}]: Failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "dialogue_timeline_status": {
                    "phase": "error",
                    "error": str(e)[:200]
                }
            })
    
    import threading
    thread = threading.Thread(target=_bg_generate, daemon=True)
    thread.start()
    
    return {
        "status": "generating",
        "total_scenes": len(scenes_to_process),
        "message": "Dialogue timeline generation started"
    }


@router.get("/projects/{project_id}/dialogue-timeline/status")
async def get_dialogue_timeline_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get dialogue timeline generation status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "status": project.get("dialogue_timeline_status", {}),
        "generated_at": project.get("dialogue_timeline_generated_at"),
        "scenes_with_timeline": len([s for s in project.get("scenes", []) if s.get("dialogue_timeline")])
    }


@router.get("/projects/{project_id}/scenes/{scene_number}/dialogue-timeline")
async def get_scene_dialogue_timeline(
    project_id: str,
    scene_number: int,
    tenant=Depends(get_current_tenant)
):
    """Get dialogue timeline for a specific scene."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scene = next((s for s in project.get("scenes", []) if s.get("scene_number") == scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    timeline = scene.get("dialogue_timeline", [])
    
    return {
        "scene_number": scene_number,
        "scene_title": scene.get("title", ""),
        "scene_duration": scene.get("duration", 12.0),
        "dialogue": scene.get("dubbed_text") or scene.get("dialogue") or scene.get("narrated_text", ""),
        "timeline": timeline,
        "total_beats": len(timeline),
        "total_spoken_duration": max([b.get("end_time", 0) for b in timeline]) if timeline else 0
    }
