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
    """Generate storyboard panels in 2 phases using parallel ordered generation.
    
    PHASE 1: Create panel structure with prompts (instant)
    PHASE 2: Generate images in ordered batches (parallel, 5 workers)
    
    Quality presets:
    - preview: 1 frame/scene (~$8 for 24 scenes) - apenas momento-chave
    - economy: 3 frames/scene (~$15 for 24 scenes) - abertura, ação, fechamento  
    - standard: 6 frames/scene (~$25 for 24 scenes) - cobertura completa
    - custom: frames personalizados (especificar em custom_frames)
    """
    from core.storyboard import QUALITY_PRESETS, FRAME_TYPES
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
    
    # **NEW:** Detect video engine and adjust frame count
    video_engine = project.get("video_engine", "sora")
    
    if video_engine == "kling":
        # Kling: 30 frames per 5-minute scene (1 frame every 10s)
        from core.storyboard import FRAME_TYPES_KLING
        frames_to_generate = list(range(1, 31))  # All 30 frames
        logger.info(f"Storyboard [{project_id}]: Kling engine detected - generating 30 frames per scene")
    else:
        # Sora: 6 frames per 12s scene (default)
        logger.info(f"Storyboard [{project_id}]: Sora engine - generating {len(frames_to_generate)} frames per scene")
    
    # Store quality choice in project
    project["storyboard_quality"] = quality
    if quality == "custom":
        project["storyboard_custom_frames"] = req.custom_frames

    # ═══ PHASE 1: Create panel structure with prompts ═══
    logger.info(f"Storyboard [{project_id}]: PHASE 1 - Creating structure for {len(scenes)} scenes")
    
    panels = []
    for scene_idx, scene in enumerate(scenes, 1):
        # Build basic prompt for this scene
        scene_num = scene.get("scene_number", scene_idx)
        title = scene.get("title", f"Cena {scene_num}")
        description = scene.get("description", "")
        characters = scene.get("characters_in_scene", [])
        
        # Create panel structure
        panel = {
            "panel_number": scene_idx,
            "scene_number": scene_num,
            "title": title,
            "description": description,
            "characters": characters,
            "prompt": f"Scene {scene_num}: {title}. {description}",  # Will be enriched in Phase 2
            "status": "pending",  # pending → generating → done | error
            "image_url": None,
            "frames": [],  # Will store multiple frames for this panel
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        panels.append(panel)
    
    # Save panel structure to DB
    project["storyboard_panels"] = panels
    project["storyboard_progress"] = {
        "status": "generating",
        "phase": "structure_created",
        "total": len(panels),
        "completed": 0,
        "current_panel": 0,
    }
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    
    logger.info(f"Storyboard [{project_id}]: Structure created - {len(panels)} panels ready")
    
    # ═══ PHASE 2: Generate images in ordered batches (parallel) ═══
    # Launch background thread
    thread = threading.Thread(
        target=_generate_panels_ordered_parallel,
        args=(tenant["id"], project_id, quality, frames_to_generate, video_engine),
        daemon=True,
    )
    thread.start()
    
    return {
        "status": "started",
        "total_panels": len(panels),
        "quality": quality,
        "video_engine": video_engine,
        "frames_per_scene": len(frames_to_generate) if isinstance(frames_to_generate, list) else "variable",
        "message": f"Estrutura criada! Gerando {len(panels)} painéis em paralelo..."
    }


def _generate_panels_ordered_parallel(tenant_id: str, project_id: str, quality: str, frames_to_generate: list, video_engine: str = "sora"):
    """PHASE 2: Generate panel images in ordered batches using 5 workers.
    
    Worker distribution for sequential visual progression:
    - Worker 1: Panels [1, 6, 11, 16, 21, 26, 31, 36, ...]
    - Worker 2: Panels [2, 7, 12, 17, 22, 27, 32, 37, ...]
    - Worker 3: Panels [3, 8, 13, 18, 23, 28, 33, 38, ...]
    - Worker 4: Panels [4, 9, 14, 19, 24, 29, 34, ...]
    - Worker 5: Panels [5, 10, 15, 20, 25, 30, 35, ...]
    
    This ensures panels become ready in sequence: 1→2→3→4→5→6→...
    """
    from concurrent.futures import ThreadPoolExecutor
    from core.storyboard import _generate_all_frames_for_scene, _generate_shot_briefs
    import tempfile
    import urllib.request
    
    MAX_WORKERS = 5
    
    try:
        # Get project data
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            logger.error(f"Storyboard [{project_id}]: Project not found in Phase 2")
            return
        
        panels = project.get("storyboard_panels", [])
        scenes = project.get("scenes", [])
        characters = project.get("characters", [])
        char_avatars = project.get("character_avatars", {})
        
        if not panels:
            logger.error(f"Storyboard [{project_id}]: No panels to generate")
            return
        
        logger.info(f"Storyboard [{project_id}]: PHASE 2 - Starting parallel generation with {MAX_WORKERS} workers for {len(panels)} panels")
        
        # Extract identity cards and style DNA
        pd = project.get("agents_output", {}).get("production_design", {})
        identity_cards = pd.get("identity_cards", {})
        style_dna = pd.get("style_dna", "")
        character_bible = pd.get("character_bible", {})
        
        # Download avatar cache (for character references)
        avatar_cache = {}
        supabase_url = os.environ.get('SUPABASE_URL', '')
        for name, url in char_avatars.items():
            if url:
                try:
                    full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                except Exception as e:
                    logger.warning(f"Failed to download avatar {name}: {e}")
                    avatar_cache[url] = None
        
        def generate_worker_batch(worker_id: int):
            """Each worker generates its assigned panels in sequence."""
            # Get panels for this worker: worker_id, worker_id+N, worker_id+2N, ...
            worker_panels_indices = [i for i in range(len(panels)) if i % MAX_WORKERS == worker_id]
            worker_panels = [panels[i] for i in worker_panels_indices]
            
            panel_numbers = [p['panel_number'] for p in worker_panels]
            logger.info(f"🤖 Worker {worker_id + 1}/{MAX_WORKERS} INICIADO: {len(worker_panels)} painéis {panel_numbers}")
            
            for idx, panel in enumerate(worker_panels, 1):
                try:
                    panel_num = panel["panel_number"]
                    scene_num = panel["scene_number"]
                    
                    logger.info(f"🎨 Worker {worker_id + 1}: Painel {panel_num}/{len(panels)} ({idx}/{len(worker_panels)} do worker) - Cena {scene_num}")
                    
                    # Find corresponding scene
                    scene = next((s for s in scenes if s.get("scene_number") == scene_num), None)
                    if not scene:
                        logger.error(f"Worker {worker_id}: Scene {scene_num} not found for panel {panel_num}")
                        panel["status"] = "error"
                        panel["error"] = f"Scene {scene_num} not found"
                        _update_panel_status(tenant_id, project_id, panel)
                        continue
                    
                    # Update status to generating
                    panel["status"] = "generating"
                    _update_panel_status(tenant_id, project_id, panel)
                    logger.info(f"Worker {worker_id}: Generating panel {panel_num} (Scene {scene_num})")
                    
                    # Generate shot briefs for this scene
                    shot_briefs = _generate_shot_briefs(
                        scene=scene,
                        scene_num=scene_num,
                        identity_cards=identity_cards,
                        style_dna=style_dna,
                        lang=project.get("language", "pt"),
                        project_id=project_id,
                    )
                    
                    # Generate all frames for this panel
                    # Use Kling frames (30) or Sora frames (6) based on engine
                    from core.storyboard import FRAME_TYPES_KLING, FRAME_TYPES
                    frame_types_to_use = FRAME_TYPES_KLING if video_engine == "kling" else FRAME_TYPES
                    
                    frames_data = _generate_all_frames_for_scene(
                        scene=scene,
                        scene_num=scene_num,
                        project_id=project_id,
                        char_avatars=char_avatars,
                        avatar_cache=avatar_cache,
                        character_bible=character_bible,
                        identity_cards=identity_cards,
                        style_dna=style_dna,
                        shot_briefs=shot_briefs,
                        lang=project.get("language", "pt"),
                        enable_validation=True,
                        frame_types=frame_types_to_use,  # Pass correct frame types
                    )
                    
                    # Upload frames to Supabase and build frame URLs
                    panel["frames"] = []
                    
                    for frame_type, image_bytes in frames_data:
                        if image_bytes:
                            try:
                                # Use _upload_to_storage helper
                                frame_filename = f"storyboard/{project_id}/scene_{scene_num:03d}_{frame_type['label']}.png"
                                frame_url = _upload_to_storage(
                                    file_bytes=image_bytes,
                                    filename=frame_filename,
                                    content_type="image/png"
                                )
                                panel["frames"].append({
                                    "label": frame_type["label"],
                                    "order": frame_type["order"],
                                    "image_url": frame_url
                                })
                            except Exception as e:
                                logger.error(f"Worker {worker_id}: Failed to upload frame {frame_type['label']}: {e}")
                    
                    # Set main image_url to first frame
                    if panel["frames"]:
                        panel["image_url"] = panel["frames"][0]["image_url"]
                    
                    # Mark as done
                    panel["status"] = "done"
                    panel["completed_at"] = datetime.now(timezone.utc).isoformat()
                    _update_panel_status(tenant_id, project_id, panel)
                    
                    logger.info(f"✅ Worker {worker_id + 1}: Painel {panel_num} COMPLETO ({len(panel['frames'])} frames) | Progresso worker: {idx}/{len(worker_panels)}")
                    
                except Exception as e:
                    logger.error(f"❌ Worker {worker_id + 1}: Painel {panel.get('panel_number')} FALHOU: {e}", exc_info=True)
                    panel["status"] = "error"
                    panel["error"] = str(e)[:200]
                    _update_panel_status(tenant_id, project_id, panel)
        
        # Launch workers
        logger.info(f"🚀 Lançando {MAX_WORKERS} workers paralelos para gerar {len(panels)} painéis...")
        logger.info(f"📊 Distribuição: Worker 1→{[p['panel_number'] for i, p in enumerate(panels) if i % MAX_WORKERS == 0]}")
        logger.info(f"📊 Distribuição: Worker 2→{[p['panel_number'] for i, p in enumerate(panels) if i % MAX_WORKERS == 1]}")
        logger.info(f"📊 Distribuição: Worker 3→{[p['panel_number'] for i, p in enumerate(panels) if i % MAX_WORKERS == 2]}")
        logger.info(f"📊 Distribuição: Worker 4→{[p['panel_number'] for i, p in enumerate(panels) if i % MAX_WORKERS == 3]}")
        logger.info(f"📊 Distribuição: Worker 5→{[p['panel_number'] for i, p in enumerate(panels) if i % MAX_WORKERS == 4]}")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for worker_id in range(MAX_WORKERS):
                future = executor.submit(generate_worker_batch, worker_id)
                futures.append(future)
            
            # Wait for all workers to complete
            for future in futures:
                future.result()
        
        # Clean up avatar cache
        for path in avatar_cache.values():
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass
        
        # Mark as complete
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["storyboard_progress"]["status"] = "complete"
            project["storyboard_progress"]["phase"] = "done"
            project["storyboard_progress"]["completed"] = len(panels)
            project["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_project(tenant_id, settings, projects)
            logger.info(f"Storyboard [{project_id}]: ✅ All {len(panels)} panels complete!")
        
    except Exception as e:
        logger.error(f"Storyboard [{project_id}]: PHASE 2 failed: {e}", exc_info=True)
        # Update project with error
        try:
            settings, projects, project = _get_project(tenant_id, project_id)
            if project:
                project["storyboard_progress"]["status"] = "error"
                project["storyboard_progress"]["error"] = str(e)[:300]
                _save_project(tenant_id, settings, projects)
        except:
            pass


def _update_panel_status(tenant_id: str, project_id: str, panel: dict):
    """Update a single panel's status in the database."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        
        panels = project.get("storyboard_panels", [])
        panel_num = panel["panel_number"]
        
        # Find and update panel
        for i, p in enumerate(panels):
            if p["panel_number"] == panel_num:
                panels[i] = panel
                break
        
        # Update completed count
        completed = len([p for p in panels if p["status"] == "done"])
        project["storyboard_progress"]["completed"] = completed
        project["storyboard_progress"]["current_panel"] = panel_num
        
        _save_project(tenant_id, settings, projects)
        
    except Exception as e:
        logger.error(f"Failed to update panel {panel.get('panel_number')}: {e}")


@router.get("/projects/{project_id}/storyboard/progress")
async def get_storyboard_progress(project_id: str, tenant=Depends(get_current_tenant)):
    """Get real-time progress of storyboard generation."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    progress = project.get("storyboard_progress", {})
    panels = project.get("storyboard_panels", [])
    
    return {
        "in_progress": progress.get("status") == "generating",
        "progress": progress,
        "panels": panels  # Full panel data for frontend to render
    }


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
        MAX_RETRIES = 3
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                import tempfile
                import time
                from core.storyboard import _generate_all_frames_for_scene, _generate_shot_briefs, FRAME_TYPES
                
                if attempt > 0:
                    wait_time = 2 ** attempt  # 2s, 4s, 8s
                    logger.info(f"Panel {req.panel_number}: Retry attempt {attempt + 1}/{MAX_RETRIES} after {wait_time}s wait...")
                    time.sleep(wait_time)
                
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

                logger.info(f"Panel {req.panel_number}: Generating frames (attempt {attempt + 1}/{MAX_RETRIES})...")
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
                        
                        # CRITICAL: Update outputs too!
                        outputs = _proj.get("outputs", [])
                        outputs = [o for o in outputs if not (o.get("type") == "storyboard" and o.get("scene_number") == req.panel_number)]
                        outputs.append({
                            "type": "storyboard",
                            "scene_number": req.panel_number,
                            "url": image_url,
                            "status": "done",
                            "frames": frames,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })
                        _proj["outputs"] = outputs
                        
                        _save_project(tenant["id"], _s, _p)
                        logger.info(f"✅ Panel {req.panel_number}: SUCCESS on attempt {attempt + 1}! ({len(frames)} frames)")
                else:
                    raise Exception("No frames generated")

                # Cleanup
                for path in avatar_cache.values():
                    if path and os.path.exists(path):
                        try:
                            os.unlink(path)
                        except Exception:
                            pass
                
                # SUCCESS - break retry loop
                return
                
            except Exception as e:
                last_error = e
                logger.error(f"Panel {req.panel_number}: Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    # Will retry
                    continue
                else:
                    # All retries exhausted
                    logger.error(f"❌ Panel {req.panel_number}: ALL {MAX_RETRIES} ATTEMPTS FAILED! Last error: {last_error}")
                    _s, _p, _proj = _get_project(tenant["id"], project_id)
                    if _proj:
                        for p in _proj.get("storyboard_panels", []):
                            if p.get("scene_number") == req.panel_number:
                                p["status"] = "error"
                                p["error"] = str(last_error)[:200]
                        _save_project(tenant["id"], _s, _p)

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




