"""Auto-generated module from studio.py split."""
from ._shared import *

@router.get("/cache/stats")
async def get_cache_stats(tenant=Depends(get_current_tenant)):
    """Get statistics from all cache layers. Requires auth."""
    from core.cache import get_cache_stats
    return get_cache_stats()

@router.post("/cache/flush")
async def flush_cache(tenant=Depends(get_current_tenant)):
    """Force flush all dirty project data to DB. Requires auth."""
    from core.cache import project_cache, image_cache, llm_cache
    project_cache.force_flush()
    image_cache.cleanup()
    llm_cache.cleanup()
    return {"status": "flushed"}



# ── Projects CRUD ──

@router.post("/projects")
async def create_project(req: StudioProject, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    now = datetime.now(timezone.utc).isoformat()
    project = {
        "id": req.id or uuid.uuid4().hex[:12],
        "name": req.name or f"Studio {datetime.now(timezone.utc).strftime('%d/%m %H:%M')}",
        "scene_type": "multi_scene",
        "briefing": req.briefing,
        "avatar_urls": req.avatar_urls,
        "scenes": [],
        "characters": [],
        "character_avatars": {},
        "project_avatars": [],
        "chat_history": [],
        "agents_output": {},
        "agent_status": {},
        "outputs": [],
        "milestones": [{"key": "project_created", "label": "Projecto criado", "done": True, "at": now}],
        "status": "draft",
        "error": None,
        "language": req.language,
        "visual_style": req.visual_style or "animation",
        "audio_mode": req.audio_mode or "narrated",
        "animation_sub": req.animation_sub or "pixar_3d",
        "continuity_mode": req.continuity_mode,
        "created_at": now,
        "updated_at": now,
    }
    projects.insert(0, project)
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return project

@router.get("/projects")
async def list_projects(tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    return {"projects": settings.get("studio_projects", [])}

@router.get("/projects/{project_id}")
async def get_project(project_id: str, tenant=Depends(get_current_tenant)):
    """Get complete project data - same as /status"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.get("id"),
        "name": project.get("name", ""),
        "synopsis": project.get("synopsis", ""),
        "briefing": project.get("briefing", ""),
        "script": project.get("script", ""),
        "status": project.get("status"),
        "chat_status": project.get("chat_status"),
        "chat_history": project.get("chat_history", []),
        "chat_messages": project.get("chat_messages", []),
        "agent_status": project.get("agent_status", {}),
        "agents_output": project.get("agents_output", {}),
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
        "character_avatars": project.get("character_avatars", {}),
        "project_avatars": project.get("project_avatars", []),
        "outputs": project.get("outputs", []),
        "milestones": project.get("milestones", []),
        "narrations": project.get("narrations", []),
        "narration_status": project.get("narration_status", {}),
        "voice_config": project.get("voice_config", {}),
        "visual_style": project.get("visual_style", "animation"),
        "animation_sub": project.get("animation_sub", "pixar_3d"),
        "continuity_mode": project.get("continuity_mode", True),
        "language": project.get("language", "pt"),
        "subtitles": project.get("subtitles", {}),
        "screenplay_approved": project.get("screenplay_approved", False),
        "audio_mode": project.get("audio_mode", "narrated"),
        "storyboard_panels": project.get("storyboard_panels", []),
        "storyboard_status": project.get("storyboard_status", {}),
        "storyboard_approved": project.get("storyboard_approved", False),
        "storyboard_chat_history": project.get("storyboard_chat_history", []),
        "continuity_status": project.get("continuity_status", {}),
        "continuity_report": project.get("continuity_report", {}),
        "error": project.get("error"),
    }

@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.get("id"),
        "name": project.get("name", ""),
        "synopsis": project.get("synopsis", ""),
        "script": project.get("script", ""),
        "status": project.get("status"),
        "chat_status": project.get("chat_status"),
        "chat_history": project.get("chat_history", []),
        "chat_messages": project.get("chat_messages", []),
        "agent_status": project.get("agent_status", {}),
        "agents_output": project.get("agents_output", {}),
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
        "character_avatars": project.get("character_avatars", {}),
        "project_avatars": project.get("project_avatars", []),
        "outputs": project.get("outputs", []),
        "milestones": project.get("milestones", []),
        "narrations": project.get("narrations", []),
        "narration_status": project.get("narration_status", {}),
        "voice_config": project.get("voice_config", {}),
        "visual_style": project.get("visual_style", "animation"),
        "animation_sub": project.get("animation_sub", "pixar_3d"),
        "continuity_mode": project.get("continuity_mode", True),
        "language": project.get("language", "pt"),
        "subtitles": project.get("subtitles", {}),
        "screenplay_approved": project.get("screenplay_approved", False),
        "audio_mode": project.get("audio_mode", "narrated"),
        "storyboard_panels": project.get("storyboard_panels", []),
        "storyboard_status": project.get("storyboard_status", {}),
        "storyboard_approved": project.get("storyboard_approved", False),
        "storyboard_chat_history": project.get("storyboard_chat_history", []),
        "continuity_status": project.get("continuity_status", {}),
        "continuity_report": project.get("continuity_report", {}),
        "error": project.get("error"),
    }

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])
    projects = [p for p in projects if p.get("id") != project_id]
    settings["studio_projects"] = projects
    _save_settings(tenant["id"], settings)
    return {"status": "ok"}


@router.post("/projects/{project_id}/fix-stuck")
async def fix_stuck_project(project_id: str, tenant=Depends(get_current_tenant)):
    """Fix a stuck project by marking it as error or complete."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    outputs = project.get("outputs", [])
    if any(o.get("url") for o in outputs):
        project["status"] = "complete"
        _add_milestone(project, "fixed_stuck", "Projecto recuperado automaticamente")
    else:
        project["status"] = "scripting"
        project["error"] = None
        # Reset agent status so UI shows ready to restart
        total = len(project.get("scenes", []))
        project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "idle", "videos_done": 0, "scene_status": {}}
        _add_milestone(project, "fixed_stuck", "Produção interrompida — pronto para reiniciar")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": project["status"], "scenes": len(project.get("scenes", []))}



@router.post("/projects/{project_id}/update-characters")
async def update_characters(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update characters list for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["characters"] = payload.get("characters", [])
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _add_milestone(project, "characters_updated", f"Personagens editados — {len(payload.get('characters', []))} personagens")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.put("/projects/{project_id}/character-avatars")
async def update_character_avatars(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update character avatar URLs for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["character_avatars"] = payload.get("character_avatars", {})
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "avatars": len(project["character_avatars"])}


@router.patch("/projects/{project_id}/settings")
async def update_project_settings(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update project-level settings (screenplay_approved, audio_mode, etc.)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    allowed_keys = {"screenplay_approved", "audio_mode", "visual_style", "animation_sub", "continuity_mode", "language"}
    for k, v in payload.items():
        if k in allowed_keys:
            project[k] = v
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    if payload.get("screenplay_approved"):
        _add_milestone(project, "screenplay_approved", "Roteiro aprovado pelo usuário")
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.patch("/projects/{project_id}")
async def update_project(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update project basic info (name, etc.)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update allowed fields
    if "name" in payload:
        project["name"] = payload["name"]
    if "genre" in payload:
        project["genre"] = payload["genre"]
    if "duration_minutes" in payload:
        project["duration_minutes"] = payload["duration_minutes"]
    
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "project": project}


# ── Project-scoped Avatars ──

@router.get("/projects/{project_id}/project-avatars")
async def get_project_avatars(project_id: str, tenant=Depends(get_current_tenant)):
    """Get avatars that belong to this specific project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"avatars": project.get("project_avatars", [])}


@router.post("/projects/{project_id}/project-avatars")
async def add_project_avatar(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Add/update an avatar in this project's local pool."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    avatar = payload.get("avatar", {})
    if not avatar.get("id"):
        avatar["id"] = uuid.uuid4().hex[:12]
    avatar["added_at"] = datetime.now(timezone.utc).isoformat()

    project_avatars = project.get("project_avatars", [])
    existing_idx = next((i for i, a in enumerate(project_avatars) if a.get("id") == avatar["id"]), None)
    if existing_idx is not None:
        project_avatars[existing_idx] = {**project_avatars[existing_idx], **avatar}
    else:
        project_avatars.append(avatar)

    project["project_avatars"] = project_avatars
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    # Also persist to global library if save_to_library flag is set
    if payload.get("save_to_library", True):
        global_avatars = settings.get("studio_avatars", [])
        g_idx = next((i for i, a in enumerate(global_avatars) if a.get("id") == avatar["id"]), None)
        lib_doc = {k: v for k, v in avatar.items() if k != "added_at"}
        lib_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        if g_idx is not None:
            lib_doc["created_at"] = global_avatars[g_idx].get("created_at", lib_doc["updated_at"])
            global_avatars[g_idx] = lib_doc
        else:
            lib_doc["created_at"] = lib_doc["updated_at"]
            global_avatars.append(lib_doc)
        settings["studio_avatars"] = global_avatars
        _save_settings(tenant["id"], settings)

    return {"status": "ok", "avatar": avatar}


@router.post("/projects/{project_id}/project-avatars/import")
async def import_avatar_from_library(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Import one or more avatars from the global library into a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    avatar_ids = payload.get("avatar_ids", [])
    if not avatar_ids:
        raise HTTPException(status_code=400, detail="No avatar_ids provided")

    global_avatars = settings.get("studio_avatars", [])
    project_avatars = project.get("project_avatars", [])
    existing_ids = {a["id"] for a in project_avatars}
    imported = 0

    for aid in avatar_ids:
        if aid in existing_ids:
            continue
        source = next((a for a in global_avatars if a.get("id") == aid), None)
        if source:
            copy = {**source, "added_at": datetime.now(timezone.utc).isoformat()}
            project_avatars.append(copy)
            imported += 1

    project["project_avatars"] = project_avatars
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "imported": imported, "total": len(project_avatars)}


@router.delete("/projects/{project_id}/project-avatars/{avatar_id}")
async def remove_project_avatar(project_id: str, avatar_id: str, tenant=Depends(get_current_tenant)):
    """Remove an avatar from a project (does NOT delete from global library)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_avatars = project.get("project_avatars", [])
    project["project_avatars"] = [a for a in project_avatars if a.get("id") != avatar_id]

    # Also unlink from character_avatars if the removed avatar was linked
    removed_av = next((a for a in project_avatars if a.get("id") == avatar_id), None)
    if removed_av:
        char_avatars = project.get("character_avatars", {})
        project["character_avatars"] = {k: v for k, v in char_avatars.items() if v != removed_av.get("url")}

    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.post("/projects/{project_id}/characters/generate-all")
async def generate_all_character_images(project_id: str, tenant=Depends(get_current_tenant)):
    """
    Auto-generate images for ALL characters that don't have avatars yet.
    - Checks global library first for reuse (same character name)
    - Generates missing ones using Gemini Nano Banana (gemini-3.1-flash-image-preview)
    - Returns progress + results
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", [])
    character_avatars = project.get("character_avatars", {})
    visual_style = project.get("animation_sub", "pixar_3d")
    global_avatars = settings.get("studio_avatars", [])
    project_avatars = project.get("project_avatars", [])

    # Map style to prompt hints
    STYLE_MAP = {
        "pixar_3d": "Pixar 3D animation style, high quality CGI render",
        "cartoon_3d": "Stylized 3D cartoon with cel-shading",
        "cartoon_2d": "Classic 2D hand-drawn animation style",
        "anime_2d": "Japanese anime art style (Makoto Shinkai quality)",
        "realistic": "Photorealistic rendering",
    }
    style_hint = STYLE_MAP.get(visual_style, "High quality animation style")

    results = {
        "total": len(characters),
        "generated": 0,
        "reused": 0,
        "failed": 0,
        "characters": []
    }

    try:
        import base64
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise Exception("EMERGENT_LLM_KEY not found in environment")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation unavailable: {str(e)}")

    for char in characters:
        char_name = char.get("name", "")
        char_desc = char.get("description", "")
        
        # Skip if already has avatar
        if character_avatars.get(char_name):
            results["characters"].append({
                "name": char_name,
                "status": "skipped",
                "reason": "already_has_avatar"
            })
            continue

        # 1. Check global library for reuse (same name)
        existing_global = next((a for a in global_avatars if a.get("name", "").lower() == char_name.lower()), None)
        
        if existing_global:
            # Reuse from library
            avatar_copy = {**existing_global, "added_at": datetime.now(timezone.utc).isoformat()}
            avatar_copy["id"] = uuid.uuid4().hex[:12]  # New ID for project scope
            project_avatars.append(avatar_copy)
            character_avatars[char_name] = avatar_copy["url"]
            results["reused"] += 1
            results["characters"].append({
                "name": char_name,
                "status": "reused",
                "avatar_url": avatar_copy["url"],
                "avatar_id": avatar_copy["id"]
            })
            logger.info(f"Reused avatar for '{char_name}' from global library")
            continue

        # 2. Generate new image
        try:
            prompt = f"""{char_desc}

{style_hint}

CRITICAL REQUIREMENTS:
- Character facing FRONT (looking directly at camera)
- TRANSPARENT background (no background elements)
- Full body portrait visible
- Character reference sheet quality
- Sharp details, well-lit, neutral standing pose"""

            logger.info(f"Generating image for character '{char_name}'")
            
            # Use LlmChat for Gemini image generation
            chat = LlmChat(
                api_key=api_key, 
                session_id=f"char-gen-{uuid.uuid4().hex[:8]}",
                system_message="You are an expert AI image generator for animation character design."
            )
            chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
            
            msg = UserMessage(text=prompt)
            text_response, images = await chat.send_message_multimodal_response(msg)

            if not images or len(images) == 0:
                raise Exception("No image generated")

            # Decode base64 image
            image_data = images[0]['data']
            image_bytes = base64.b64decode(image_data)

            # Upload to Supabase Storage
            file_name = f"character_{uuid.uuid4().hex[:12]}.png"
            
            try:
                upload_res = supabase.storage.from_("pipeline-assets").upload(
                    path=file_name,
                    file=image_bytes,
                    file_options={"content-type": "image/png"}
                )
                public_url = supabase.storage.from_("pipeline-assets").get_public_url(file_name)
            except Exception as upload_err:
                logger.error(f"Supabase upload failed for {char_name}: {upload_err}")
                raise Exception(f"Upload failed: {str(upload_err)}")

            # Create avatar record
            new_avatar = {
                "id": uuid.uuid4().hex[:12],
                "name": char_name,
                "url": public_url,
                "prompt": prompt,
                "description": char_desc,
                "visual_style": visual_style,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Add to project avatars
            project_avatars.append(new_avatar)
            character_avatars[char_name] = public_url
            
            # Also save to global library for future reuse
            global_avatars.append({k: v for k, v in new_avatar.items() if k != "added_at"})

            results["generated"] += 1
            results["characters"].append({
                "name": char_name,
                "status": "generated",
                "avatar_url": public_url,
                "avatar_id": new_avatar["id"]
            })
            logger.info(f"Successfully generated avatar for '{char_name}'")

        except Exception as gen_err:
            logger.error(f"Failed to generate avatar for '{char_name}': {gen_err}")
            results["failed"] += 1
            results["characters"].append({
                "name": char_name,
                "status": "failed",
                "error": str(gen_err)
            })

    # Save everything
    project["project_avatars"] = project_avatars
    project["character_avatars"] = character_avatars
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    settings["studio_avatars"] = global_avatars
    _save_project(tenant["id"], settings, projects)
    _save_settings(tenant["id"], settings)
    
    # ═══ AUTO-ASSIGN VOICES using Sound Designer Agent ═══
    logger.info(f"CharacterGen [{project_id}]: Triggering Sound Designer Agent for voice assignment")
    try:
        from .sound_design_agent import auto_assign_voices_with_sound_designer
        from pipeline.config import ELEVENLABS_VOICES
        
        voice_result = await auto_assign_voices_with_sound_designer(
            project_id=project_id,
            tenant_id=tenant["id"],  # FIX: tenant["id"] instead of undefined tenant_id
            available_voices=ELEVENLABS_VOICES
        )
        
        # Save voice assignments to project
        voice_map = voice_result["voice_map"]
        project["voice_map"] = voice_map
        _save_project(tenant["id"], settings, projects)  # FIX: tenant["id"]
        
        logger.info(f"CharacterGen [{project_id}]: Voice assignment complete - {len(voice_map)} characters")
        
        results["voice_assignments"] = {
            "assigned": len(voice_map),
            "details": voice_result["detailed_assignments"][:5]  # First 5 for preview
        }
        
    except Exception as voice_err:
        logger.warning(f"CharacterGen [{project_id}]: Voice assignment failed, skipping - {voice_err}")
        results["voice_assignments"] = {"assigned": 0, "error": str(voice_err)}

    return results


@router.post("/projects/{project_id}/characters/{character_name}/generate")
async def generate_single_character_image(
    project_id: str,
    character_name: str,
    tenant=Depends(get_current_tenant)
):
    """
    Generate image for a single specific character.
    Checks global library first, generates if not found.
    """
    # CRITICAL FIX: Decode URL-encoded characters (spaces, accents like ã, ó, etc.)
    from urllib.parse import unquote
    character_name = unquote(character_name)
    
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", [])
    character = next((c for c in characters if c.get("name") == character_name), None)
    
    if not character:
        raise HTTPException(status_code=404, detail=f"Character '{character_name}' not found")

    character_avatars = project.get("character_avatars", {})
    visual_style = project.get("animation_sub", "pixar_3d")
    global_avatars = settings.get("studio_avatars", [])
    project_avatars = project.get("project_avatars", [])

    # Check if already has avatar
    if character_avatars.get(character_name):
        return {
            "status": "skipped",
            "message": f"'{character_name}' already has an avatar",
            "avatar_url": character_avatars[character_name]
        }

    STYLE_MAP = {
        "pixar_3d": "Pixar 3D animation style, high quality CGI render",
        "cartoon_3d": "Stylized 3D cartoon with cel-shading",
        "cartoon_2d": "Classic 2D hand-drawn animation style",
        "anime_2d": "Japanese anime art style (Makoto Shinkai quality)",
        "realistic": "Photorealistic rendering",
    }
    style_hint = STYLE_MAP.get(visual_style, "High quality animation style")

    try:
        import base64
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not api_key:
            raise Exception("EMERGENT_LLM_KEY not found in environment")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation unavailable: {str(e)}")

    char_name = character.get("name", "")
    char_desc = character.get("description", "")

    # 1. Check global library for reuse
    existing_global = next((a for a in global_avatars if a.get("name", "").lower() == char_name.lower()), None)
    
    if existing_global:
        avatar_copy = {**existing_global, "added_at": datetime.now(timezone.utc).isoformat()}
        avatar_copy["id"] = uuid.uuid4().hex[:12]
        project_avatars.append(avatar_copy)
        character_avatars[char_name] = avatar_copy["url"]
        
        project["project_avatars"] = project_avatars
        project["character_avatars"] = character_avatars
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save_project(tenant["id"], settings, projects)
        
        logger.info(f"Reused avatar for '{char_name}' from global library")
        return {
            "status": "reused",
            "character_name": char_name,
            "avatar_url": avatar_copy["url"],
            "avatar_id": avatar_copy["id"]
        }

    # 2. Generate new image
    try:
        prompt = f"""{char_desc}

{style_hint}

CRITICAL REQUIREMENTS:
- Character facing FRONT (looking directly at camera)
- TRANSPARENT background (no background elements)
- Full body portrait visible
- Character reference sheet quality
- Sharp details, well-lit, neutral standing pose"""

        logger.info(f"Generating image for character '{char_name}'")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"char-gen-{uuid.uuid4().hex[:8]}",
            system_message="You are an expert AI image generator for animation character design."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=prompt)
        text_response, images = await chat.send_message_multimodal_response(msg)

        if not images or len(images) == 0:
            raise Exception("No image generated")

        # Decode base64 image
        image_data = images[0]['data']
        image_bytes = base64.b64decode(image_data)

        # Upload to Supabase
        file_name = f"character_{uuid.uuid4().hex[:12]}.png"
        
        try:
            upload_res = supabase.storage.from_("pipeline-assets").upload(
                path=file_name,
                file=image_bytes,
                file_options={"content-type": "image/png"}
            )
            public_url = supabase.storage.from_("pipeline-assets").get_public_url(file_name)
        except Exception as upload_err:
            logger.error(f"Supabase upload failed for {char_name}: {upload_err}")
            raise Exception(f"Upload failed: {str(upload_err)}")

        # Create avatar record
        new_avatar = {
            "id": uuid.uuid4().hex[:12],
            "name": char_name,
            "url": public_url,
            "prompt": prompt,
            "description": char_desc,
            "visual_style": visual_style,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add to project and global library
        project_avatars.append(new_avatar)
        character_avatars[char_name] = public_url
        global_avatars.append({k: v for k, v in new_avatar.items() if k != "added_at"})

        project["project_avatars"] = project_avatars
        project["character_avatars"] = character_avatars
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        settings["studio_avatars"] = global_avatars
        
        _save_project(tenant["id"], settings, projects)
        _save_settings(tenant["id"], settings)
        
        logger.info(f"Successfully generated avatar for '{char_name}'")
        
        return {
            "status": "generated",
            "character_name": char_name,
            "avatar_url": public_url,
            "avatar_id": new_avatar["id"]
        }

    except Exception as gen_err:
        logger.error(f"Failed to generate avatar for '{char_name}': {gen_err}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(gen_err)}")

