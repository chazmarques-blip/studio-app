"""Scene Reordering Endpoint"""
from ._shared import *


class ReorderScenesRequest(BaseModel):
    scene_order: list[int]  # New order of scene_numbers, e.g. [3, 1, 2, 5, 4]


@router.post("/projects/{project_id}/scenes/reorder")
async def reorder_scenes(
    project_id: str,
    req: ReorderScenesRequest,
    tenant=Depends(get_current_tenant)
):
    """
    Reorders scenes in the project and updates all references.
    
    This updates:
    - scene_number in each scene
    - Storyboard panel references
    - Screenplay act structure
    - Camera plan scene references
    
    Args:
        scene_order: New order of scene numbers
            Example: [3, 1, 2] means scene 3 becomes first, scene 1 becomes second, etc.
    
    Returns:
        Updated project with reordered scenes
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to reorder")
    
    # Validate scene_order
    if len(req.scene_order) != len(scenes):
        raise HTTPException(
            status_code=400,
            detail=f"scene_order length ({len(req.scene_order)}) must match number of scenes ({len(scenes)})"
        )
    
    # Validate all scene numbers exist
    existing_numbers = {s.get("scene_number") for s in scenes}
    requested_numbers = set(req.scene_order)
    if requested_numbers != existing_numbers:
        raise HTTPException(
            status_code=400,
            detail=f"scene_order contains invalid scene numbers. Expected: {sorted(existing_numbers)}, Got: {sorted(requested_numbers)}"
        )
    
    logger.info(f"SceneReorder [{project_id}]: Reordering {len(scenes)} scenes from {[s.get('scene_number') for s in scenes]} to {req.scene_order}")
    
    try:
        # Create mapping: old_number -> scene_data
        scene_map = {s.get("scene_number"): s for s in scenes}
        
        # Create new ordered list
        new_scenes = []
        for new_idx, old_scene_num in enumerate(req.scene_order):
            scene = scene_map[old_scene_num].copy()
            
            # Update scene_number to new position (1-indexed)
            old_num = scene.get("scene_number")
            new_num = new_idx + 1
            scene["scene_number"] = new_num
            
            logger.info(f"  Scene {old_num} → {new_num}: {scene.get('title', 'Untitled')}")
            
            new_scenes.append(scene)
        
        # Update project
        project["scenes"] = new_scenes
        
        # Update storyboard panels if they exist
        storyboard_panels = project.get("storyboard_panels", [])
        if storyboard_panels:
            # Create reverse mapping: old_number -> new_number
            num_mapping = {old: new_idx + 1 for new_idx, old in enumerate(req.scene_order)}
            
            for panel in storyboard_panels:
                old_panel_num = panel.get("panel_number")
                if old_panel_num in num_mapping:
                    panel["panel_number"] = num_mapping[old_panel_num]
            
            # Re-sort panels by new panel_number
            storyboard_panels.sort(key=lambda p: p.get("panel_number", 0))
            project["storyboard_panels"] = storyboard_panels
            
            logger.info(f"  Updated {len(storyboard_panels)} storyboard panels")
        
        # Update camera plan if it exists
        camera_plan = project.get("agents_output", {}).get("camera_plan", {})
        if camera_plan and "camera_shot_list" in camera_plan:
            num_mapping = {old: new_idx + 1 for new_idx, old in enumerate(req.scene_order)}
            
            for shot in camera_plan["camera_shot_list"]:
                old_scene_num = shot.get("scene_number")
                if old_scene_num in num_mapping:
                    shot["scene_number"] = num_mapping[old_scene_num]
            
            # Re-sort by new scene_number
            camera_plan["camera_shot_list"].sort(key=lambda s: s.get("scene_number", 0))
            
            if "agents_output" not in project:
                project["agents_output"] = {}
            project["agents_output"]["camera_plan"] = camera_plan
            
            logger.info(f"  Updated camera plan")
        
        # Update outputs (video/audio) if they reference scene numbers
        outputs = project.get("outputs", [])
        if outputs:
            num_mapping = {old: new_idx + 1 for new_idx, old in enumerate(req.scene_order)}
            
            for output in outputs:
                old_scene_num = output.get("scene_number")
                if old_scene_num in num_mapping:
                    output["scene_number"] = num_mapping[old_scene_num]
            
            # Re-sort by new scene_number
            outputs.sort(key=lambda o: o.get("scene_number", 0))
            project["outputs"] = outputs
            
            logger.info(f"  Updated {len(outputs)} outputs")
        
        # Add milestone
        _add_milestone(project, "scenes_reordered", f"Cenas reordenadas: {req.scene_order[:5]}...")
        
        # Update timestamp
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save project to database
        _save_project(tenant["id"], settings, projects, flush_now=True)
        
        logger.info(f"SceneReorder [{project_id}]: Complete - {len(new_scenes)} scenes reordered and SAVED to database")
        logger.info(f"SceneReorder [{project_id}]: New scene order: {[s.get('scene_number') for s in new_scenes]}")
        
        return {
            "status": "success",
            "message": "Scenes reordered successfully",
            "new_order": [s.get("scene_number") for s in new_scenes],
            "scenes_updated": len(new_scenes),
            "panels_updated": len(storyboard_panels) if storyboard_panels else 0,
            "camera_plan_updated": bool(camera_plan),
            "outputs_updated": len(outputs) if outputs else 0
        }
        
    except Exception as e:
        logger.error(f"SceneReorder [{project_id}]: Failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder scenes: {str(e)}")


@router.get("/projects/{project_id}/scenes/order")
async def get_scene_order(project_id: str, tenant=Depends(get_current_tenant)):
    """Get current scene order."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    
    return {
        "scene_order": [s.get("scene_number") for s in scenes],
        "scene_titles": [
            {
                "scene_number": s.get("scene_number"),
                "title": s.get("title", "Untitled")
            }
            for s in scenes
        ],
        "total_scenes": len(scenes)
    }
