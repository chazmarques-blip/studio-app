"""Auto-generated module from studio.py split."""
from ._shared import *

# ══ STORYBOARD ENDPOINTS ══

class StoryboardGenerateRequest(BaseModel):
    pass

class StoryboardRegeneratePanelRequest(BaseModel):
    panel_number: int
    description: str = ""

class StoryboardEditPanelRequest(BaseModel):
    panel_number: int
    title: str = ""
    description: str = ""
    dialogue: str = ""

class StoryboardChatRequest(BaseModel):
    message: str

class StoryboardApproveRequest(BaseModel):
    approved: bool = True


@router.post("/projects/{project_id}/generate-storyboard")
async def generate_storyboard(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate storyboard panels for all scenes using Gemini Nano Banana."""
    from core.storyboard import generate_all_panels
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to generate storyboard from")

    # Mark as generating
    project["storyboard_status"] = {"phase": "starting", "current": 0, "total": len(scenes), "panels_done": 0}
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    # Run generation in background thread
    def _bg_gen():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return
            panels = generate_all_panels(
                tenant_id=tenant["id"],
                project_id=project_id,
                scenes=_project.get("scenes", []),
                characters=_project.get("characters", []),
                char_avatars=_project.get("character_avatars", {}),
                production_design=_project.get("agents_output", {}).get("production_design", {}),
                lang=_project.get("language", "pt"),
                upload_fn=_upload_to_storage,
                update_fn=_update_project_field,
            )
            done_count = len([p for p in panels if p.get("image_url")])
            _update_project_field(tenant["id"], project_id, {
                "storyboard_panels": panels,
                "storyboard_status": {"phase": "complete", "current": len(panels), "total": len(panels), "panels_done": done_count},
                "storyboard_approved": False,
            })
            _add_milestone(_project, "storyboard_generated", f"Storyboard — {done_count}/{len(panels)} painéis")
            _save_project(tenant["id"], _settings, _projects)
            logger.info(f"Storyboard [{project_id}]: Complete — {done_count}/{len(panels)} panels")
        except Exception as e:
            logger.error(f"Storyboard [{project_id}]: Generation failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "storyboard_status": {"phase": "error", "error": str(e)[:200]},
            })

    thread = threading.Thread(target=_bg_gen, daemon=True)
    thread.start()
    return {"status": "generating", "total_scenes": len(scenes)}


@router.get("/projects/{project_id}/storyboard")
async def get_storyboard(project_id: str, tenant=Depends(get_current_tenant)):
    """Get storyboard panels and status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "panels": project.get("storyboard_panels", []),
        "storyboard_status": project.get("storyboard_status", {}),
        "storyboard_approved": project.get("storyboard_approved", False),
        "storyboard_chat_history": project.get("storyboard_chat_history", []),
    }


@router.post("/projects/{project_id}/storyboard/regenerate-panel")
async def regenerate_storyboard_panel(project_id: str, req: StoryboardRegeneratePanelRequest, tenant=Depends(get_current_tenant)):
    """Regenerate a single storyboard panel with 6 individual frames."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == req.panel_number), None)
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    scene = next((s for s in project.get("scenes", []) if s.get("scene_number") == req.panel_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Use updated description if provided
    if req.description:
        scene = {**scene, "description": req.description}

    # Mark as generating
    panel["status"] = "generating"
    _save_project(tenant["id"], settings, projects)

    def _bg_regen():
        try:
            import tempfile
            from core.storyboard import _generate_all_frames_for_scene, FRAME_TYPES
            char_avatars = project.get("character_avatars", {})
            production_design = project.get("agents_output", {}).get("production_design", {})
            character_bible = production_design.get("character_bible", {})

            avatar_cache = {}
            chars_in_scene = scene.get("characters_in_scene", [])
            for cname in chars_in_scene:
                url = char_avatars.get(cname)
                if url and url not in avatar_cache:
                    try:
                        supabase_url = os.environ.get('SUPABASE_URL', '')
                        full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
                        ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        urllib.request.urlretrieve(full_url, ref_file.name)
                        avatar_cache[url] = ref_file.name
                    except Exception:
                        avatar_cache[url] = None

            style_dna = "ART STYLE: Premium 3D CGI animation (Pixar/DreamWorks quality). Volumetric lighting."
            style_anchors = production_design.get("style_anchors", "")
            if style_anchors:
                style_dna = f"{style_dna} {style_anchors}"

            frame_results = _generate_all_frames_for_scene(
                scene=scene, scene_num=req.panel_number, project_id=project_id,
                char_avatars=char_avatars, avatar_cache=avatar_cache,
                character_bible=character_bible, style_dna=style_dna,
                lang=project.get("language", "pt"),
            )

            image_url = None
            frames = []
            for fi, (ft, img_bytes) in enumerate(frame_results):
                if img_bytes:
                    frame_fname = f"storyboard/{project_id}/panel_{req.panel_number}_frame_{fi+1}.png"
                    frame_url = _upload_to_storage(img_bytes, frame_fname, "image/png")
                    frames.append({
                        "frame_number": fi + 1,
                        "image_url": frame_url,
                        "label": ft["label"],
                    })
                    if image_url is None:
                        image_url = frame_url

            if image_url:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            p["image_url"] = image_url
                            p["frames"] = frames
                            p["status"] = "done"
                            p["generated_at"] = datetime.now(timezone.utc).isoformat()
                    _save_project(tenant["id"], _s, _p)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            p["status"] = "error"
                    _save_project(tenant["id"], _s, _p)

            for path in avatar_cache.values():
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Storyboard [{project_id}]: Panel {req.panel_number} regen failed: {e}")

    thread = threading.Thread(target=_bg_regen, daemon=True)
    thread.start()
    return {"status": "regenerating", "panel_number": req.panel_number}


@router.patch("/projects/{project_id}/storyboard/edit-panel")
async def edit_storyboard_panel(project_id: str, req: StoryboardEditPanelRequest, tenant=Depends(get_current_tenant)):
    """Edit text fields of a storyboard panel."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    found = False
    for p in panels:
        if p.get("scene_number") == req.panel_number:
            if req.title:
                p["title"] = req.title
            if req.description:
                p["description"] = req.description
            if req.dialogue:
                p["dialogue"] = req.dialogue
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Panel not found")

    project["storyboard_panels"] = panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


class InpaintElementRequest(BaseModel):
    panel_number: int
    edit_instruction: str
    frame_index: int = 0  # Which frame to edit (0-based)


@router.post("/projects/{project_id}/storyboard/edit-element")
async def edit_element_inpaint(project_id: str, req: InpaintElementRequest, tenant=Depends(get_current_tenant)):
    """Edit a specific element in a storyboard panel using AI image editing (Gemini).

    The AI receives the original image + text instruction and generates an edited version
    that preserves everything except the requested change.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == req.panel_number), None)
    if not panel or not panel.get("image_url"):
        raise HTTPException(status_code=400, detail="Panel not found or has no image")

    # Determine which image to edit (selected frame or main image)
    frames = panel.get("frames", [])
    if frames and 0 <= req.frame_index < len(frames):
        source_image_url = frames[req.frame_index].get("image_url", panel["image_url"])
    else:
        source_image_url = panel["image_url"]

    # Mark as editing
    for p in panels:
        if p.get("scene_number") == req.panel_number:
            p["status"] = "generating"
    _save_project(tenant["id"], settings, projects)

    def _bg_inpaint():
        try:
            from core.storyboard_inpaint import inpaint_element
            result_bytes = inpaint_element(
                image_url=source_image_url,
                edit_instruction=req.edit_instruction,
                project_id=project_id,
                panel_number=req.panel_number,
                lang=project.get("language", "pt"),
            )
            if result_bytes:
                fname = f"storyboard/{project_id}/panel_{req.panel_number}_frame_{req.frame_index + 1}_edited.png"
                new_url = _upload_to_storage(result_bytes, fname, "image/png")
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            # Update the correct frame
                            p_frames = p.get("frames", [])
                            if p_frames and 0 <= req.frame_index < len(p_frames):
                                p_frames[req.frame_index]["image_url"] = new_url
                            # Also update main image_url if editing frame 0 or no frames
                            if req.frame_index == 0 or not p_frames:
                                p["image_url"] = new_url
                            p["status"] = "done"
                            p["last_edit"] = req.edit_instruction
                            p["generated_at"] = datetime.now(timezone.utc).isoformat()
                    _save_project(tenant["id"], _s, _p)
                logger.info(f"Inpaint [{project_id}]: Panel {req.panel_number} frame {req.frame_index} edited — {req.edit_instruction[:50]}")
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    for p in _proj.get("storyboard_panels", []):
                        if p.get("scene_number") == req.panel_number:
                            p["status"] = "error"
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"Inpaint [{project_id}]: Panel {req.panel_number} failed: {e}")
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                for p in _proj.get("storyboard_panels", []):
                    if p.get("scene_number") == req.panel_number:
                        p["status"] = "error"
                _save_project(tenant["id"], _s, _p)

    thread = threading.Thread(target=_bg_inpaint, daemon=True)
    thread.start()
    return {"status": "editing", "panel_number": req.panel_number}


@router.patch("/projects/{project_id}/storyboard/approve")
async def approve_storyboard(project_id: str, req: StoryboardApproveRequest, tenant=Depends(get_current_tenant)):
    """Approve or unapprove the storyboard."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["storyboard_approved"] = req.approved
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    if req.approved:
        _add_milestone(project, "storyboard_approved", "Storyboard aprovado pelo usuário")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "storyboard_approved": req.approved}


@router.post("/projects/{project_id}/storyboard/chat")
async def storyboard_facilitator_chat(project_id: str, req: StoryboardChatRequest, tenant=Depends(get_current_tenant)):
    """AI Facilitator chat for editing storyboard panels."""
    from core.storyboard import facilitator_chat
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    chat_history = project.get("storyboard_chat_history", [])

    result = facilitator_chat(
        message=req.message,
        panels=panels,
        scenes=project.get("scenes", []),
        chat_history=chat_history,
        lang=project.get("language", "pt"),
    )

    # Save chat history
    chat_history.append({"role": "user", "text": req.message})
    chat_history.append({"role": "assistant", "text": result["response"]})

    # Apply text edits from actions
    for action in result.get("actions", []):
        if action.get("action") == "edit_text" and action.get("panel_number"):
            for p in panels:
                if p.get("scene_number") == action["panel_number"]:
                    field = action.get("field", "dialogue")
                    if field in ("dialogue", "description", "title"):
                        p[field] = action.get("value", "")

    project["storyboard_chat_history"] = chat_history[-20:]  # Keep last 20 messages
    project["storyboard_panels"] = panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    # Handle regenerate_image actions asynchronously
    regen_panels = [a["panel_number"] for a in result.get("actions", []) if a.get("action") == "regenerate_image"]

    return {
        "response": result["response"],
        "actions": result.get("actions", []),
        "regenerating_panels": regen_panels,
    }


# ══ STORYBOARD PREVIEW ENDPOINTS ══

class PreviewGenerateRequest(BaseModel):
    voice_id: str = "onwK4e9ZLuTAKqWW03F9"  # Daniel (British, authoritative)
    music_track: str = ""


@router.post("/projects/{project_id}/storyboard/generate-preview")
async def generate_storyboard_preview(project_id: str, req: PreviewGenerateRequest, tenant=Depends(get_current_tenant)):
    """Generate an animated MP4 preview from storyboard panels with ElevenLabs narration."""
    from core.preview_generator import generate_preview_video
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    valid_panels = [p for p in panels if p.get("image_url")]
    if not valid_panels:
        raise HTTPException(status_code=400, detail="No storyboard panels with images")

    lang = project.get("language", "pt")

    # Find music file path if specified
    music_path = None
    if req.music_track:
        from pipeline.config import MUSIC_LIBRARY
        track_info = MUSIC_LIBRARY.get(req.music_track)
        if track_info:
            music_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline", "music")
            candidate = os.path.join(music_dir, track_info["file"])
            if os.path.exists(candidate):
                music_path = candidate

    # Mark as generating
    project["preview_status"] = {"phase": "starting", "current": 0, "total": len(valid_panels)}
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    def _bg_preview():
        try:
            url = generate_preview_video(
                project_id=project_id,
                panels=valid_panels,
                voice_id=req.voice_id,
                lang=lang,
                music_path=music_path,
                upload_fn=_upload_to_storage,
                update_fn=_update_project_field,
                tenant_id=tenant["id"],
            )
            _update_project_field(tenant["id"], project_id, {
                "preview_status": {"phase": "complete", "url": url},
                "preview_url": url,
            })
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                _add_milestone(_proj, "preview_generated", "Preview animado gerado")
                _save_project(tenant["id"], _s, _p)
            logger.info(f"Preview [{project_id}]: Complete — {url}")
        except Exception as e:
            logger.error(f"Preview [{project_id}]: Failed: {e}")
            _update_project_field(tenant["id"], project_id, {
                "preview_status": {"phase": "error", "error": str(e)[:200]},
            })

    thread = threading.Thread(target=_bg_preview, daemon=True)
    thread.start()
    return {"status": "generating", "total_panels": len(valid_panels)}


@router.get("/projects/{project_id}/storyboard/preview-status")
async def get_preview_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get preview generation status and URL."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "preview_status": project.get("preview_status", {}),
        "preview_url": project.get("preview_url"),
    }




