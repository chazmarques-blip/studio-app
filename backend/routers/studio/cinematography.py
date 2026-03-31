"""Director of Photography & Quality Control Endpoints"""
from ._shared import *
from core.cinematographer import generate_camera_plan
from core.quality_control import (
    run_full_quality_control,
    design_scene_transitions,
    validate_storyboard_frame,
    check_scene_continuity,
    normalize_audio_continuity,
    analyze_color_consistency
)


class CameraPlanRequest(BaseModel):
    format_strategy: str = "safe_zone"  # safe_zone | dual_generation | multi_format
    formats_requested: list = ["16:9"]


class QCRequest(BaseModel):
    include_transitions: bool = True
    include_audio: bool = True
    include_color: bool = True


@router.post("/projects/{project_id}/cinematography/generate")
async def generate_cinematography_plan(
    project_id: str,
    req: CameraPlanRequest,
    tenant=Depends(get_current_tenant)
):
    """
    Generate camera plan with Director of Photography agent.
    
    This creates a complete cinematography plan including:
    - Camera movements per scene
    - Shot composition guidelines
    - Multi-format strategy (safe zones or format-specific)
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes found")
    
    characters = project.get("characters", [])
    production_design = project.get("agents_output", {}).get("production_design", {})
    
    logger.info(f"DoP [{project_id}]: Generating camera plan for {len(scenes)} scenes, strategy: {req.format_strategy}")
    
    # Mark as processing
    project["cinematography_status"] = {
        "phase": "generating",
        "format_strategy": req.format_strategy,
        "formats_requested": req.formats_requested
    }
    _save_project(tenant["id"], settings, projects)
    
    # Generate in background
    def _bg_generate():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return
            
            _scenes = _project.get("scenes", [])
            _characters = _project.get("characters", [])
            _production_design = _project.get("agents_output", {}).get("production_design", {})
            
            # Generate camera plan
            camera_plan = generate_camera_plan(
                project_id=project_id,
                scenes=_scenes,
                characters=_characters,
                production_design=_production_design,
                format_strategy=req.format_strategy,
                formats_requested=req.formats_requested,
                lang=_project.get("language", "pt")
            )
            
            # Save to project
            if "agents_output" not in _project:
                _project["agents_output"] = {}
            _project["agents_output"]["camera_plan"] = camera_plan
            _project["cinematography_status"] = {
                "phase": "complete",
                "format_strategy": req.format_strategy,
                "scenes_planned": len(camera_plan.get("camera_shot_list", []))
            }
            _project["cinematography_generated_at"] = datetime.now(timezone.utc).isoformat()
            
            _add_milestone(_project, "cinematography_generated", f"DoP planejou {len(_scenes)} cenas")
            _save_project(tenant["id"], _settings, _projects)
            
            logger.info(f"DoP [{project_id}]: Complete - camera plan generated")
            
        except Exception as e:
            logger.error(f"DoP [{project_id}]: Failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "cinematography_status": {
                    "phase": "error",
                    "error": str(e)[:200]
                }
            })
    
    import threading
    thread = threading.Thread(target=_bg_generate, daemon=True)
    thread.start()
    
    return {
        "status": "generating",
        "format_strategy": req.format_strategy,
        "total_scenes": len(scenes),
        "message": "Camera plan generation started"
    }


@router.get("/projects/{project_id}/cinematography/status")
async def get_cinematography_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get DoP camera plan generation status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    camera_plan = project.get("agents_output", {}).get("camera_plan", {})
    
    return {
        "status": project.get("cinematography_status", {}),
        "generated_at": project.get("cinematography_generated_at"),
        "format_strategy": camera_plan.get("format_strategy"),
        "scenes_planned": len(camera_plan.get("camera_shot_list", []))
    }


@router.get("/projects/{project_id}/cinematography/plan")
async def get_camera_plan(project_id: str, tenant=Depends(get_current_tenant)):
    """Get full camera plan."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    camera_plan = project.get("agents_output", {}).get("camera_plan", {})
    
    if not camera_plan:
        raise HTTPException(status_code=404, detail="Camera plan not generated yet")
    
    return camera_plan


@router.post("/projects/{project_id}/quality-control/run")
async def run_quality_control(
    project_id: str,
    req: QCRequest,
    tenant=Depends(get_current_tenant)
):
    """
    Run full quality control on completed production.
    
    Checks:
    - Transition design (smooth scene changes)
    - Audio continuity (volume normalization, crossfades)
    - Color grading (consistent palette)
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    outputs = project.get("outputs", [])
    production_design = project.get("agents_output", {}).get("production_design", {})
    
    # Separate video and audio outputs
    video_outputs = [o for o in outputs if o.get("type") == "video"]
    audio_outputs = [o for o in outputs if o.get("type") == "audio"]
    
    if not video_outputs:
        raise HTTPException(status_code=400, detail="No video outputs found for QC")
    
    logger.info(f"QC [{project_id}]: Starting quality control")
    
    # Run QC in background
    def _bg_qc():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return
            
            _scenes = _project.get("scenes", [])
            _outputs = _project.get("outputs", [])
            _video_outputs = [o for o in _outputs if o.get("type") == "video"]
            _audio_outputs = [o for o in _outputs if o.get("type") == "audio"]
            _production_design = _project.get("agents_output", {}).get("production_design", {})
            
            # Run full QC
            qc_report = run_full_quality_control(
                project_id=project_id,
                scenes=_scenes,
                video_outputs=_video_outputs,
                audio_outputs=_audio_outputs if req.include_audio else [],
                production_design=_production_design
            )
            
            # Save report
            if "agents_output" not in _project:
                _project["agents_output"] = {}
            _project["agents_output"]["quality_control"] = qc_report
            _project["qc_completed_at"] = datetime.now(timezone.utc).isoformat()
            
            _add_milestone(_project, "quality_control_complete", f"QC: {len(qc_report['checks_performed'])} checks")
            _save_project(tenant["id"], _settings, _projects)
            
            logger.info(f"QC [{project_id}]: Complete - {qc_report['overall_status']}")
            
        except Exception as e:
            logger.error(f"QC [{project_id}]: Failed: {e}")
    
    import threading
    thread = threading.Thread(target=_bg_qc, daemon=True)
    thread.start()
    
    return {
        "status": "running",
        "message": "Quality control started",
        "checks": {
            "transitions": req.include_transitions,
            "audio": req.include_audio,
            "color": req.include_color
        }
    }


@router.get("/projects/{project_id}/quality-control/report")
async def get_qc_report(project_id: str, tenant=Depends(get_current_tenant)):
    """Get quality control report."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    qc_report = project.get("agents_output", {}).get("quality_control", {})
    
    if not qc_report:
        raise HTTPException(status_code=404, detail="QC report not available yet")
    
    return qc_report
