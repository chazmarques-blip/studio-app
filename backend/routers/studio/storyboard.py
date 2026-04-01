"""Auto-generated module from studio.py split."""
from ._shared import *

# ══ STORYBOARD ENDPOINTS ══

class StoryboardGenerateRequest(BaseModel):
    quality: str = "economy"  # preview | economy | standard | custom
    custom_frames: list = None  # For custom mode: [1, 3, 6] etc

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

@router.get("/storyboard/cost-estimate")
async def get_storyboard_cost_estimate():
    """Get cost estimates for different quality presets."""
    from core.storyboard import QUALITY_PRESETS
    
    # Base costs (approximate)
    COST_PER_FRAME = 0.35  # Gemini Nano Banana per frame
    COST_IDENTITY_CARDS = 2.5  # Claude Vision for identity cards (one-time)
    COST_PER_SCENE_PLANNING = 0.15  # Claude for shot briefs
    
    estimates = {}
    for preset_name, preset_data in QUALITY_PRESETS.items():
        if preset_name == "custom":
            continue
            
        frames = preset_data["frames"]
        num_frames = len(frames) if frames else 6
        
        # For 24 scenes
        cost_24 = (
            COST_IDENTITY_CARDS +  # One-time
            (COST_PER_SCENE_PLANNING * 24) +  # Shot planning per scene
            (COST_PER_FRAME * num_frames * 24)  # Frames
        )
        
        estimates[preset_name] = {
            "description": preset_data["description"],
            "frames_per_scene": num_frames,
            "cost_24_scenes": round(cost_24, 2),
            "cost_per_scene": round(cost_24 / 24, 2),
        }
    
    return {
        "presets": estimates,
        "recommendations": {
            "prototyping": "Use 'preview' para testar rapidamente (~$8)",
            "production": "Use 'economy' para equilibrar custo e qualidade (~$15)",
            "premium": "Use 'standard' para cobertura completa (~$25)",
        }
    }


class StoryboardApproveRequest(BaseModel):
    approved: bool = True


@router.post("/projects/{project_id}/generate-storyboard")
async def generate_storyboard(project_id: str, req: StoryboardGenerateRequest = None, tenant=Depends(get_current_tenant)):
    """Generate storyboard panels for scenes using Gemini Nano Banana.
    
    Quality presets:
    - preview: 1 frame/scene (~$8 for 24 scenes) - apenas momento-chave
    - economy: 3 frames/scene (~$15 for 24 scenes) - abertura, ação, fechamento  
    - standard: 6 frames/scene (~$25 for 24 scenes) - cobertura completa
    - custom: frames personalizados (especificar em custom_frames)
    """
    from core.storyboard import generate_all_panels, QUALITY_PRESETS
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to generate storyboard from")
    
    # Get quality settings
    if req is None:
        req = StoryboardGenerateRequest()
    
    quality = req.quality if req.quality in QUALITY_PRESETS else "economy"
    frames_to_generate = QUALITY_PRESETS[quality]["frames"]
    
    if quality == "custom" and req.custom_frames:
        frames_to_generate = req.custom_frames
    
    # Store quality choice in project
    project["storyboard_quality"] = quality
    if quality == "custom":
        project["storyboard_custom_frames"] = req.custom_frames

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

            # Extract identity cards from production_design (stored by _analyze_avatars_with_vision)
            pd = _project.get("agents_output", {}).get("production_design", {})
            identity_cards = pd.get("identity_cards", {})

            # If no identity cards yet, try to generate them from avatar analysis
            if not identity_cards:
                char_avatars_dict = _project.get("character_avatars", {})
                characters_list = _project.get("characters", [])
                if char_avatars_dict and characters_list:
                    # Download avatars temporarily to analyze
                    import tempfile, urllib.request
                    temp_cache = {}
                    supabase_url = os.environ.get('SUPABASE_URL', '')
                    for name, url in char_avatars_dict.items():
                        if url:
                            try:
                                full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
                                ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                                urllib.request.urlretrieve(full_url, ref_file.name)
                                temp_cache[url] = ref_file.name
                            except Exception:
                                temp_cache[url] = None

                    identity_cards = _run_async_in_thread(_analyze_avatars_with_vision(
                        characters_list, char_avatars_dict, temp_cache, project_id
                    ))

                    # Clean up temp files
                    for path in temp_cache.values():
                        if path and os.path.exists(path):
                            try: os.unlink(path)
                            except Exception: pass

                    # Store identity cards in the project for reuse
                    if identity_cards:
                        agents_output = _project.get("agents_output", {})
                        if "production_design" not in agents_output:
                            agents_output["production_design"] = {}
                        agents_output["production_design"]["identity_cards"] = identity_cards
                        _project["agents_output"] = agents_output
                        _save_project(tenant["id"], _settings, _projects)
                        logger.info(f"Storyboard [{project_id}]: Identity Cards generated and stored for {len(identity_cards)} characters")

            panels = generate_all_panels(
                tenant_id=tenant["id"],
                project_id=project_id,
                scenes=_project.get("scenes", []),
                characters=_project.get("characters", []),
                char_avatars=_project.get("character_avatars", {}),
                production_design=pd,
                identity_cards=identity_cards,
                lang=_project.get("language", "pt"),
                upload_fn=_upload_to_storage,
                update_fn=_update_project_field,
                frames_to_generate=frames_to_generate,  # NEW: selective frame generation
            )
            done_count = len([p for p in panels if p.get("image_url")])
            
            # CRITICAL FIX: Save to BOTH storyboard_panels AND outputs (for frontend compatibility)
            outputs = _project.get("outputs", [])
            
            # Remove old storyboard outputs
            outputs = [o for o in outputs if o.get("type") != "storyboard"]
            
            # Add new storyboard outputs
            for panel in panels:
                if panel.get("image_url"):  # Only add successful panels
                    outputs.append({
                        "type": "storyboard",
                        "scene_number": panel["scene_number"],
                        "url": panel["image_url"],
                        "status": panel.get("status", "done"),
                        "title": panel.get("title", ""),
                        "frames": panel.get("frames", []),
                        "created_at": panel.get("generated_at", datetime.now(timezone.utc).isoformat()),
                    })
            
            _update_project_field(tenant["id"], project_id, {
                "storyboard_panels": panels,
                "outputs": outputs,  # CRITICAL: Save to outputs too!
                "storyboard_status": {"phase": "complete", "current": len(panels), "total": len(panels), "panels_done": done_count},
                "storyboard_approved": False,
            })
            _add_milestone(_project, "storyboard_generated", f"Storyboard — {done_count}/{len(panels)} painéis")
            _save_project(tenant["id"], _settings, _projects)
            logger.info(f"Storyboard [{project_id}]: Complete — {done_count}/{len(panels)} panels | {len(outputs)} outputs saved")
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


@router.post("/projects/{project_id}/storyboard/sync-panels")
async def sync_storyboard_panels(project_id: str, tenant=Depends(get_current_tenant)):
    """Create placeholder panels for scenes missing storyboard, then regenerate them in background."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    panels = project.get("storyboard_panels", [])
    panel_nums = {p.get("scene_number") for p in panels}

    missing = [s for s in scenes if s.get("scene_number") not in panel_nums]
    if not missing:
        return {"status": "ok", "synced": 0, "message": "All scenes already have storyboard panels"}

    # Create placeholder panels for missing scenes
    for s in missing:
        panels.append({
            "scene_number": s["scene_number"],
            "status": "pending",
            "image_url": None,
            "frames": [],
            "description": s.get("description", ""),
        })
    panels.sort(key=lambda x: x.get("scene_number", 0))
    project["storyboard_panels"] = panels
    _save_project(tenant["id"], settings, projects)

    # Regenerate missing panels in background
    missing_nums = [s["scene_number"] for s in missing]

    def _bg_sync():
        for scene_num in missing_nums:
            try:
                _settings, _projects, _project = _get_project(tenant["id"], project_id)
                if not _project:
                    return
                _scene = next((s for s in _project.get("scenes", []) if s.get("scene_number") == scene_num), None)
                if not _scene:
                    continue

                import tempfile
                from core.storyboard import _generate_all_frames_for_scene, _generate_shot_briefs, FRAME_TYPES
                char_avatars = _project.get("character_avatars", {})
                pd = _project.get("agents_output", {}).get("production_design", {})
                character_bible = pd.get("character_bible", {})
                identity_cards = pd.get("identity_cards", {})

                avatar_cache = {}
                chars_in_scene = _scene.get("characters_in_scene", [])
                supabase_url = os.environ.get('SUPABASE_URL', '')
                for cname in chars_in_scene:
                    url = char_avatars.get(cname)
                    if url and url not in avatar_cache:
                        try:
                            full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
                            ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                            urllib.request.urlretrieve(full_url, ref_file.name)
                            avatar_cache[url] = ref_file.name
                        except Exception:
                            avatar_cache[url] = None

                style_dna = "ART STYLE: Premium 3D CGI animation (Pixar/DreamWorks quality). Volumetric lighting."
                style_anchors = pd.get("style_anchors", "")
                if style_anchors:
                    style_dna = f"{style_dna} {style_anchors}"

                scenes_list = _project.get("scenes", [])
                scene_idx = next((i for i, s in enumerate(scenes_list) if s.get("scene_number") == scene_num), 0)
                prev_scene = scenes_list[scene_idx - 1] if scene_idx > 0 else None
                next_scene = scenes_list[scene_idx + 1] if scene_idx < len(scenes_list) - 1 else None
                
                # Get dialogue timeline for this scene
                dialogue_timeline = _scene.get("dialogue_timeline", [])

                shot_briefs = None
                if identity_cards:
                    shot_briefs = _generate_shot_briefs(
                        scene=_scene, scene_num=scene_num,
                        identity_cards=identity_cards, style_dna=style_dna,
                        prev_scene=prev_scene, next_scene=next_scene,
                        lang=_project.get("language", "pt"), project_id=project_id,
                        dialogue_timeline=dialogue_timeline,
                    )

                frame_results = _generate_all_frames_for_scene(
                    scene=_scene, scene_num=scene_num, project_id=project_id,
                    char_avatars=char_avatars, avatar_cache=avatar_cache,
                    character_bible=character_bible, identity_cards=identity_cards,
                    style_dna=style_dna, shot_briefs=shot_briefs,
                    lang=_project.get("language", "pt"),
                )

                image_url = None
                frames = []
                for fi, (ft, img_bytes) in enumerate(frame_results):
                    if img_bytes:
                        frame_fname = f"storyboard/{project_id}/panel_{scene_num}_frame_{fi+1}.png"
                        frame_url = _upload_to_storage(img_bytes, frame_fname, "image/png")
                        frames.append({"frame_type": ft, "image_url": frame_url})
                        if not image_url:
                            image_url = frame_url

                # Update the panel
                _settings2, _projects2, _project2 = _get_project(tenant["id"], project_id)
                if _project2:
                    _panels = _project2.get("storyboard_panels", [])
                    _panel = next((p for p in _panels if p.get("scene_number") == scene_num), None)
                    if _panel:
                        _panel["status"] = "done"
                        _panel["image_url"] = image_url
                        _panel["frames"] = frames
                        _save_project(tenant["id"], _settings2, _projects2)
                        logger.info(f"Sync [{project_id}]: Panel {scene_num} generated ({len(frames)} frames)")

            except Exception as e:
                logger.error(f"Sync [{project_id}]: Failed to generate panel {scene_num}: {e}")
                # Mark as error
                try:
                    _s, _ps, _p = _get_project(tenant["id"], project_id)
                    if _p:
                        _pnl = next((p for p in _p.get("storyboard_panels", []) if p.get("scene_number") == scene_num), None)
                        if _pnl:
                            _pnl["status"] = "error"
                            _save_project(tenant["id"], _s, _ps)
                except Exception:
                    pass

    thread = threading.Thread(target=_bg_sync, daemon=True)
    thread.start()
    return {"status": "syncing", "synced": len(missing), "missing_scenes": missing_nums}



@router.post("/projects/{project_id}/storyboard/regenerate-panel")
async def regenerate_storyboard_panel(project_id: str, req: StoryboardRegeneratePanelRequest, tenant=Depends(get_current_tenant)):
    """Regenerate a single storyboard panel with 6 individual frames."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    panel = next((p for p in panels if p.get("scene_number") == req.panel_number), None)
    if not panel:
        # Auto-create panel for new scenes that don't have one yet
        scene_check = next((s for s in project.get("scenes", []) if s.get("scene_number") == req.panel_number), None)
        if not scene_check:
            raise HTTPException(status_code=404, detail="Scene not found")
        panel = {
            "scene_number": req.panel_number,
            "status": "pending",
            "image_url": None,
            "frames": [],
            "description": scene_check.get("description", ""),
        }
        panels.append(panel)
        panels.sort(key=lambda x: x.get("scene_number", 0))
        project["storyboard_panels"] = panels
        _save_project(tenant["id"], settings, projects)

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
            from core.storyboard import _generate_all_frames_for_scene, _generate_shot_briefs, FRAME_TYPES
            char_avatars = project.get("character_avatars", {})
            production_design = project.get("agents_output", {}).get("production_design", {})
            character_bible = production_design.get("character_bible", {})
            identity_cards = production_design.get("identity_cards", {})

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

            # Generate shot briefs for this single scene with continuity
            scenes_list = project.get("scenes", [])
            scene_idx = next((i for i, s in enumerate(scenes_list) if s.get("scene_number") == req.panel_number), 0)
            prev_scene = scenes_list[scene_idx - 1] if scene_idx > 0 else None
            next_scene = scenes_list[scene_idx + 1] if scene_idx < len(scenes_list) - 1 else None
            
            # Get dialogue timeline for this scene
            dialogue_timeline = scene.get("dialogue_timeline", [])

            shot_briefs = None
            if identity_cards:
                shot_briefs = _generate_shot_briefs(
                    scene=scene, scene_num=req.panel_number,
                    identity_cards=identity_cards, style_dna=style_dna,
                    prev_scene=prev_scene, next_scene=next_scene,
                    lang=project.get("language", "pt"), project_id=project_id,
                    dialogue_timeline=dialogue_timeline,
                )

            frame_results = _generate_all_frames_for_scene(
                scene=scene, scene_num=req.panel_number, project_id=project_id,
                char_avatars=char_avatars, avatar_cache=avatar_cache,
                character_bible=character_bible, identity_cards=identity_cards,
                style_dna=style_dna, shot_briefs=shot_briefs,
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




