"""Auto-generated module from studio.py split."""
from ._shared import *

# ══ SMART IMAGE EDITOR ENDPOINTS ══

@router.post("/projects/{project_id}/storyboard/analyze-scene")
async def analyze_storyboard_scene(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Analyze a storyboard panel image and return structured scene map."""
    from core.smart_editor import analyze_scene
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panel_number = payload.get("panel_number", 1)
    frame_index = payload.get("frame_index", 0)

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == panel_number), None)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    # Get the image to analyze
    frames = panel.get("frames", [])
    if frames and 0 <= frame_index < len(frames):
        image_url = frames[frame_index].get("image_url", panel.get("image_url"))
    else:
        image_url = panel.get("image_url")

    if not image_url:
        raise HTTPException(status_code=400, detail="No image to analyze")

    scene_context = {
        "title": panel.get("title", ""),
        "description": panel.get("description", ""),
        "characters_in_scene": panel.get("characters_in_scene", []),
        "emotion": panel.get("emotion", ""),
    }

    analysis = analyze_scene(
        image_url=image_url,
        project_id=project_id,
        panel_number=panel_number,
        scene_context=scene_context,
    )

    # Cache analysis in panel
    for p in panels:
        if p.get("scene_number") == panel_number:
            p_frames = p.get("frames", [])
            if p_frames and 0 <= frame_index < len(p_frames):
                p_frames[frame_index]["scene_analysis"] = analysis
            else:
                p["scene_analysis"] = analysis
    _save_project(tenant["id"], settings, projects)

    return analysis


@router.post("/projects/{project_id}/storyboard/smart-edit")
async def smart_edit_panel(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Edit a panel using scene-aware intelligence."""
    from core.smart_editor import analyze_scene, smart_edit
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panel_number = payload.get("panel_number", 1)
    frame_index = payload.get("frame_index", 0)
    edit_instruction = payload.get("edit_instruction", "")
    if not edit_instruction:
        raise HTTPException(status_code=400, detail="No edit instruction")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == panel_number), None)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    frames = panel.get("frames", [])
    if frames and 0 <= frame_index < len(frames):
        image_url = frames[frame_index].get("image_url", panel.get("image_url"))
        cached_analysis = frames[frame_index].get("scene_analysis")
    else:
        image_url = panel.get("image_url")
        cached_analysis = panel.get("scene_analysis")

    if not image_url:
        raise HTTPException(status_code=400, detail="No image to edit")

    # Mark as editing
    for p in panels:
        if p.get("scene_number") == panel_number:
            p["status"] = "generating"
    _save_project(tenant["id"], settings, projects)

    def _bg_smart_edit():
        try:
            # Step 1: Get or create scene analysis
            analysis = cached_analysis
            if not analysis or "error" in analysis:
                analysis = analyze_scene(
                    image_url=image_url,
                    project_id=project_id,
                    panel_number=panel_number,
                    scene_context={
                        "title": panel.get("title", ""),
                        "description": panel.get("description", ""),
                        "characters_in_scene": panel.get("characters_in_scene", []),
                        "emotion": panel.get("emotion", ""),
                    },
                )

            # Step 2: Smart edit with analysis context
            result_bytes = smart_edit(
                image_url=image_url,
                edit_instruction=edit_instruction,
                scene_analysis=analysis,
                project_id=project_id,
                panel_number=panel_number,
                lang=project.get("language", "pt"),
            )

            if result_bytes:
                fname = f"storyboard/{project_id}/panel_{panel_number}_frame_{frame_index + 1}_smart.png"
                new_url = _upload_to_storage(result_bytes, fname, "image/png")
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == panel_number:
                            p_frames = p.get("frames", [])
                            if p_frames and 0 <= frame_index < len(p_frames):
                                p_frames[frame_index]["image_url"] = new_url
                                p_frames[frame_index]["scene_analysis"] = analysis
                            if frame_index == 0 or not p_frames:
                                p["image_url"] = new_url
                            p["status"] = "done"
                            p["last_edit"] = f"[Smart] {edit_instruction}"
                            p["generated_at"] = datetime.now(timezone.utc).isoformat()
                    _save_project(tenant["id"], _s, _p)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == panel_number:
                            p["status"] = "error"
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"SmartEdit [{project_id}]: Panel {panel_number} failed: {e}")

    thread = threading.Thread(target=_bg_smart_edit, daemon=True)
    thread.start()

    return {"status": "editing", "panel_number": panel_number, "mode": "smart"}



