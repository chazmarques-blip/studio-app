"""
StudioX — Scene Regeneration Endpoint
Allows regenerating a specific scene's storyboard and video after production.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from routers.studio._shared import (
    _get_settings, _save_settings, _get_project, _save_project, _add_milestone
)

logger = logging.getLogger(__name__)
router = APIRouter()


class RegenerateSceneRequest(BaseModel):
    """Request to regenerate a specific scene"""
    new_description: Optional[str] = None
    new_dialogue: Optional[str] = None
    new_emotion: Optional[str] = None


@router.post("/projects/{project_id}/scenes/{scene_number}/regenerate")
async def regenerate_scene(
    project_id: str,
    scene_number: int,
    req: RegenerateSceneRequest,
    tenant=None  # Injected by middleware
):
    """
    Regenerate storyboard frames for a specific scene.
    Optionally updates scene description/dialogue before regenerating.
    
    Steps:
    1. Find the scene by scene_number
    2. Update description/dialogue if provided
    3. Regenerate storyboard frames for that scene only
    4. Update storyboard_panels
    5. Mark video outputs for that scene as 'needs_regeneration'
    6. Return updated scene data
    """
    logger.info(f"SceneRegenerate [{project_id}]: Regenerating scene {scene_number}")
    
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    project = _get_project(projects, project_id)
    
    if not project:
        raise HTTPException(404, "Project not found")
    
    scenes = project.get("scenes", [])
    
    # Find the scene
    target_scene = None
    scene_index = None
    for idx, scene in enumerate(scenes):
        if scene.get("scene_number") == scene_number:
            target_scene = scene
            scene_index = idx
            break
    
    if not target_scene:
        raise HTTPException(404, f"Scene {scene_number} not found in project")
    
    logger.info(f"SceneRegenerate [{project_id}]: Found scene '{target_scene.get('title', '')}'")
    
    # Update scene fields if provided
    if req.new_description:
        target_scene["description"] = req.new_description
        logger.info(f"SceneRegenerate [{project_id}]: Updated description")
    
    if req.new_dialogue:
        target_scene["dialogue"] = req.new_dialogue
        logger.info(f"SceneRegenerate [{project_id}]: Updated dialogue")
    
    if req.new_emotion:
        target_scene["emotion"] = req.new_emotion
        logger.info(f"SceneRegenerate [{project_id}]: Updated emotion")
    
    # Save updated scene
    scenes[scene_index] = target_scene
    project["scenes"] = scenes
    
    # Remove old storyboard panels for this scene
    old_panels = project.get("storyboard_panels", [])
    new_panels = [p for p in old_panels if p.get("scene_number") != scene_number]
    project["storyboard_panels"] = new_panels
    
    logger.info(f"SceneRegenerate [{project_id}]: Removed {len(old_panels) - len(new_panels)} old panels")
    
    # Regenerate storyboard for this scene only
    try:
        from core.storyboard import _generate_all_frames_for_scene
        
        characters = project.get("characters", [])
        char_avatars = {c["name"]: c.get("avatar_url") for c in characters if c.get("avatar_url")}
        character_bible = {c["name"]: c.get("description", "") for c in characters}
        identity_cards = project.get("identity_cards", {})
        style_dna = project.get("style_dna", "Pixar 3D animation style")
        lang = project.get("language", "pt")
        
        # Generate frames for this scene
        avatar_cache = {}
        frames = _generate_all_frames_for_scene(
            scene=target_scene,
            scene_num=scene_number,
            project_id=project_id,
            char_avatars=char_avatars,
            avatar_cache=avatar_cache,
            character_bible=character_bible,
            identity_cards=identity_cards,
            style_dna=style_dna,
            shot_briefs=None,  # Will be generated internally
            lang=lang,
            enable_validation=False  # Disabled for speed
        )
        
        logger.info(f"SceneRegenerate [{project_id}]: Generated {len(frames)} new frames")
        
        # Create new panel
        new_panel = {
            "scene_number": scene_number,
            "title": target_scene.get("title", ""),
            "description": target_scene.get("description", ""),
            "dialogue": target_scene.get("dialogue", ""),
            "emotion": target_scene.get("emotion", ""),
            "image_url": frames[0]["url"] if frames and frames[0].get("url") else None,
            "frames": frames,
            "status": "done" if frames else "error"
        }
        
        # Add to panels list
        project["storyboard_panels"].append(new_panel)
        
        # Sort panels by scene_number
        project["storyboard_panels"].sort(key=lambda x: x.get("scene_number", 0))
        
        # Mark video output for this scene as needing regeneration
        outputs = project.get("outputs", [])
        for output in outputs:
            if output.get("scene_number") == scene_number:
                output["needs_regeneration"] = True
                output["status"] = "pending"
        
        project["outputs"] = outputs
        
        # Add milestone
        _add_milestone(project, "scene_regenerated", f"Scene {scene_number} regenerated")
        
        # Save project
        _save_project(tenant["id"], settings, projects, flush_now=True)
        
        logger.info(f"SceneRegenerate [{project_id}]: Complete - scene {scene_number} regenerated")
        
        return {
            "status": "success",
            "message": f"Scene {scene_number} regenerated successfully",
            "scene_number": scene_number,
            "frames_generated": len(frames),
            "panel": new_panel,
            "video_marked_for_regen": True
        }
        
    except Exception as e:
        logger.error(f"SceneRegenerate [{project_id}]: Failed - {e}", exc_info=True)
        raise HTTPException(500, f"Failed to regenerate scene: {str(e)}")
