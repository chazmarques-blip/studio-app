"""
Cost Estimator for StudioX Production
Calculates estimated costs for video production
"""
from ._shared import *
from typing import Dict

# ── Cost Constants ──

SORA_2_COST_PER_5S = 2.50  # USD per 5-second scene
ELEVENLABS_COST_PER_MIN = 0.30  # USD per minute of voice generation
CLAUDE_SONNET_COST_FIXED = 1.50  # Fixed cost for LLM calls in loop

def calculate_production_cost(bible: Dict) -> Dict:
    """
    Calculate estimated production cost based on Project Bible
    
    Returns:
    {
        "total_usd": float,
        "breakdown": {
            "sora_2": float,
            "voices": float,
            "llm": float
        },
        "details": {
            "num_scenes": int,
            "total_duration_seconds": int,
            "voice_duration_minutes": float
        }
    }
    """
    metadata = bible.get("production_metadata", {})
    
    # Scene count
    num_scenes = metadata.get("total_scenes_planned", 0)
    if num_scenes == 0:
        # Fallback: count from screenplay
        screenplay = bible.get("screenplay", {})
        scenes = screenplay.get("scenes", [])
        num_scenes = len(scenes)
    
    # Duration
    total_duration_seconds = metadata.get("estimated_duration_seconds", 180)  # default 3min
    
    # Calculate costs
    sora_cost = num_scenes * SORA_2_COST_PER_5S
    
    # Voice cost (assume 60% of video has voice-over/dialogue)
    voice_duration_minutes = (total_duration_seconds * 0.6) / 60
    voice_cost = voice_duration_minutes * ELEVENLABS_COST_PER_MIN
    
    # LLM cost (fixed for autonomous loop)
    llm_cost = CLAUDE_SONNET_COST_FIXED
    
    total_cost = sora_cost + voice_cost + llm_cost
    
    return {
        "total_usd": round(total_cost, 2),
        "breakdown": {
            "sora_2": round(sora_cost, 2),
            "voices": round(voice_cost, 2),
            "llm": round(llm_cost, 2)
        },
        "details": {
            "num_scenes": num_scenes,
            "total_duration_seconds": total_duration_seconds,
            "voice_duration_minutes": round(voice_duration_minutes, 2)
        }
    }


@router.get("/projects/{project_id}/cost-estimate")
async def get_cost_estimate(
    project_id: str,
    tenant=Depends(get_current_tenant)
):
    """Get production cost estimate for a project"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    bible = project.get("project_bible")
    if not bible:
        raise HTTPException(status_code=404, detail="Project Bible not created yet")
    
    cost_estimate = calculate_production_cost(bible)
    
    return {
        "project_id": project_id,
        "estimate": cost_estimate,
        "currency": "USD",
        "disclaimer": "Estimated costs may vary based on actual usage"
    }
