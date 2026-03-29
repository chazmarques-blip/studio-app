"""
StudioX Project Bible Module
Manages the unified project context that all agents share and contribute to.
"""
from ._shared import *
import json
from datetime import datetime
from typing import Dict, List, Optional

# ── Project Bible Structure ──

class ProjectBible(BaseModel):
    """Unified project context shared by all agents"""
    project_id: str
    quality_score: int = 0  # 0-100
    iteration: int = 1
    approved_by_user: bool = False
    created_at: str = ""
    updated_at: str = ""
    
    # Core elements
    characters: List[Dict] = []
    visual_style: Dict = {}
    narrative_elements: Dict = {}
    production_metadata: Dict = {}
    
    # Production outputs
    screenplay: Optional[Dict] = None
    dialogues: List[Dict] = []
    narration: List[Dict] = []
    storyboard: List[Dict] = []
    voice_samples: List[Dict] = []
    
    # Quality tracking
    quality_breakdown: Dict = {}
    issues: List[str] = []
    recommendations: List[str] = []


@router.post("/projects/{project_id}/create-bible")
async def create_project_bible(
    project_id: str,
    tenant=Depends(get_current_tenant)
):
    """
    Initialize Project Bible structure for a project.
    This is called after user approves characters.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Initialize Bible structure
    characters = project.get("characters", [])
    if not characters:
        raise HTTPException(status_code=400, detail="No characters in project. User must approve characters first.")
    
    bible = ProjectBible(
        project_id=project_id,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        characters=[
            {
                "id": c.get("id", f"char_{i}"),
                "name": c.get("name", ""),
                "age": c.get("age", ""),
                "physical_description": c.get("description", ""),
                "clothing": c.get("clothing", ""),
                "personality": c.get("role", ""),
                "avatar_id": c.get("avatar_id", ""),
                "voice_profile": {
                    "voice_id": c.get("voice_id", ""),
                    "voice_name": "",
                    "voice_sample_url": "",
                    "consistency_hash": ""
                },
                "reference_image_url": c.get("avatar_url", "")
            }
            for i, c in enumerate(characters)
        ],
        visual_style={
            "art_style": project.get("animation_substyle", "pixar_3d"),
            "color_palette": [],
            "lighting": "",
            "camera_style": ""
        },
        narrative_elements={
            "tone": "",
            "period": "",
            "target_duration": "",
            "key_themes": []
        },
        production_metadata={
            "total_scenes_planned": 0,
            "estimated_cost_usd": 0.0,
            "estimated_duration_seconds": 0
        }
    )
    
    # Save Bible to project
    project["project_bible"] = bible.dict()
    await _save_project(tenant["id"], project)
    
    logger.info(f"Bible [{project_id}]: Created initial Project Bible with {len(characters)} characters")
    
    return {
        "status": "created",
        "bible": bible.dict()
    }


@router.get("/projects/{project_id}/bible")
async def get_project_bible(
    project_id: str,
    tenant=Depends(get_current_tenant)
):
    """Get current Project Bible for a project"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    bible = project.get("project_bible")
    if not bible:
        raise HTTPException(status_code=404, detail="Project Bible not created yet. Call /create-bible first.")
    
    return {"bible": bible}


@router.put("/projects/{project_id}/bible")
async def update_project_bible(
    project_id: str,
    bible_update: Dict,
    tenant=Depends(get_current_tenant)
):
    """Update Project Bible (used by agents during autonomous loop)"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    current_bible = project.get("project_bible", {})
    
    # Merge updates
    current_bible.update(bible_update)
    current_bible["updated_at"] = datetime.utcnow().isoformat()
    current_bible["iteration"] = current_bible.get("iteration", 1) + 1
    
    project["project_bible"] = current_bible
    await _save_project(tenant["id"], project)
    
    logger.info(f"Bible [{project_id}]: Updated (iteration {current_bible['iteration']})")
    
    return {
        "status": "updated",
        "iteration": current_bible["iteration"]
    }
