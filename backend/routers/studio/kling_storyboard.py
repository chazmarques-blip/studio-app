"""
Kling Storyboard Generator - 30 Frames for 5-Minute Videos
Generates ultra-detailed storyboards with Kling-optimized prompts for continuity
"""
from ._shared import *
from typing import List, Dict
import asyncio
from datetime import datetime, timezone

# ══════════════════════════════════════════════════════════════════════════════
# KLING STORYBOARD SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

KLING_STORYBOARD_SYSTEM = """You are an ELITE CINEMATOGRAPHER specializing in creating frame-by-frame descriptions for AI video generation.

YOUR MISSION:
Generate 30 ultra-detailed storyboard frames for a 300-second (5-minute) video.
Each frame represents a 10-second segment.

CRITICAL REQUIREMENTS:

1. **VISUAL CONTINUITY**:
   - Each frame must flow naturally into the next
   - Characters maintain consistent appearance
   - Environment stays coherent throughout
   - Lighting progresses naturally (time of day, mood shifts)

2. **CHARACTER CONSISTENCY**:
   - Use character names ONLY
   - NEVER describe physical appearance (already defined in character sheets)
   - Focus on: actions, expressions, emotions, movements, poses

3. **KLING-OPTIMIZED DESCRIPTIONS**:
   Each frame needs TWO parts:
   
   A) **IMAGE PROMPT** (for visual reference):
      - Scene composition
      - Character positions and poses
      - Environment/setting details
      - Lighting and atmosphere
      - Camera angle and framing
      
   B) **KLING VIDEO PROMPT** (for 10-second video generation):
      - What HAPPENS in those 10 seconds
      - Character movements and actions
      - Camera movements (tracking, dolly, pan, tilt, static)
      - Dialogue timing and lip-sync cues
      - Environmental changes (wind, shadows, light shifts)
      - Transitions into next segment

4. **STRUCTURE FOR EACH FRAME**:
```json
{
  "frame_number": 1,
  "time_start": "0:00",
  "time_end": "0:10",
  
  "image_prompt": "Detailed visual description for reference image generation...",
  
  "kling_prompt": "Detailed 10-second action description for Kling video generation. Camera slowly dollies forward. Abraão walks from left to right, turning to face Isaac. Isaac reaches up with both hands. Wind gently moves their clothing. Warm golden light intensifies. [0:05] Abraão begins speaking...",
  
  "characters_present": ["Abraão", "Isaac", "Sara"],
  "camera_movement": "dolly forward + slight pan right",
  "key_action": "Father-son embrace begins",
  "emotion": "tenderness, warmth",
  "lighting": "golden hour, warm backlight",
  "continuity_note": "Sets up emotional peak in next frame"
}
```

5. **DIALOGUE INTEGRATION**:
   - Include exact timestamp within 10s window
   - Example: "[0:03] Abraão says 'Meu filho, precisamos conversar'"
   - Describe lip movement: "mouth moves naturally with speech"
   - Show listener reactions

6. **CAMERA CHOREOGRAPHY**:
   - Be specific: "Camera starts static, then slowly dollies in from medium shot to close-up over 7 seconds"
   - Coordinate with action: "Camera tilts up as character stands"
   - Create visual rhythm: alternate between static and moving shots

7. **ENVIRONMENT PROGRESSION**:
   - Time progression: sunrise → midday → sunset
   - Weather: clouds move, wind intensity changes
   - Light shifts: shadows lengthen, colors warm/cool
   - Ambient details: birds fly, leaves fall, dust particles

LANGUAGE: {language}
TARGET AUDIENCE: {target_audience}
{audience_guidelines}

Return ONLY valid JSON with all 30 frames.
"""


# ══════════════════════════════════════════════════════════════════════════════
# AUDIENCE ADAPTATION
# ══════════════════════════════════════════════════════════════════════════════

AUDIENCE_CINEMATOGRAPHY = {
    "pt": {
        "2-5": "Movimentos lentos e suaves. Ações simples e claras. Cores vibrantes. Close-ups frequentes nas expressões.",
        "3-6": "Ritmo moderado. Ações óbvias. Câmera estável com movimentos suaves. Evitar cortes rápidos.",
        "6-9": "Ritmo dinâmico. Ações variadas. Câmera pode ser mais ousada (zoom, giros suaves).",
        "10-13": "Ritmo cinematográfico. Sequências de ação complexas. Câmera criativa.",
        "14-17": "Estilo maduro. Movimentos de câmera sofisticados. Simbolismo visual.",
        "18-25": "Liberdade criativa total. Experimentação visual. Referências culturais.",
        "25+": "Cinematografia de autor. Narrativa visual complexa. Sem restrições.",
        "all": "Equilíbrio entre acessibilidade e sofisticação visual."
    },
    "en": {
        "2-5": "Slow, smooth movements. Simple, clear actions. Vibrant colors. Frequent close-ups on expressions.",
        "3-6": "Moderate pace. Obvious actions. Stable camera with smooth movements. Avoid quick cuts.",
        "6-9": "Dynamic pace. Varied actions. Camera can be bolder (zoom, smooth spins).",
        "10-13": "Cinematic pace. Complex action sequences. Creative camera.",
        "14-17": "Mature style. Sophisticated camera movements. Visual symbolism.",
        "18-25": "Full creative freedom. Visual experimentation. Cultural references.",
        "25+": "Auteur cinematography. Complex visual narrative. No restrictions.",
        "all": "Balance between accessibility and visual sophistication."
    }
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

class KlingStoryboardRequest(BaseModel):
    scene_id: Optional[str] = None  # If None, use first scene with 5-min duration


@router.post("/projects/{project_id}/kling-storyboards/generate")
async def generate_kling_storyboards(
    project_id: str, 
    req: KlingStoryboardRequest,
    tenant=Depends(get_current_tenant)
):
    """
    Generate ultra-detailed storyboards for 5-minute video (30 frames).
    Runs as a BACKGROUND TASK — returns immediately, frontend polls for completion.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Mark generation as started (so frontend knows to poll)
    _update_project_field(tenant["id"], project_id, {
        "kling_generation_status": {
            "phase": "generating",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "progress": 0,
            "total_expected": 30
        }
    }, flush_now=True)
    
    # Capture tenant info for background task
    tenant_id = tenant["id"]
    
    # Launch generation in background thread (won't be killed by HTTP disconnect)
    async def _run_generation_background():
        try:
            await _do_generate_kling_storyboards(project_id, tenant_id)
        except Exception as e:
            logger.error(f"KlingStoryboard [{project_id}]: Background generation failed: {e}")
            _update_project_field(tenant_id, project_id, {
                "kling_generation_status": {
                    "phase": "error",
                    "error": str(e)[:200],
                    "finished_at": datetime.now(timezone.utc).isoformat()
                }
            }, flush_now=True)
    
    asyncio.ensure_future(_run_generation_background())
    
    logger.info(f"KlingStoryboard [{project_id}]: Generation launched in background")
    
    return {
        "status": "generating",
        "message": "30-frame generation started in background. Poll GET /kling-storyboards for progress.",
        "total_expected": 30
    }


async def _do_generate_kling_storyboards(project_id: str, tenant_id: str):
    """
    Actual generation logic — runs in background, immune to HTTP timeouts.
    """
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        raise Exception("Project not found")
    
    scenes = project.get("scenes", [])
    
    # If no scenes or scenes are too short, create a virtual 5-minute scene
    if not scenes:
        logger.info(f"KlingStoryboard [{project_id}]: No scenes found, creating virtual 5-minute scene")
        scenes = [{
            "scene_number": 1,
            "title": project.get("title", "Cena Principal"),
            "description": project.get("description", "Cena do vídeo"),
            "time_start": "0:00",
            "time_end": "5:00",
            "duration_seconds": 300,
            "characters_in_scene": [c.get("name") for c in project.get("characters", [])],
            "emotion": "neutral"
        }]
    
    # Get project metadata
    characters = project.get("characters", [])
    character_avatars = project.get("character_avatars", {})  # Avatares já vinculados
    
    # NOVO: Se character_avatars estiver vazio, buscar da character_library automaticamente
    if not character_avatars or len(character_avatars) == 0:
        character_library = project.get("character_library")
        if character_library:
            library_characters = character_library.get("characters", [])
            logger.info(f"KlingStoryboard [{project_id}]: character_avatars vazio, buscando da library (pasta '{character_library.get('folder_name', 'Unknown')}')")
            
            # Mapear nomes de personagens para URLs dos avatares
            for char in characters:
                char_name = char.get("name", "")
                # Buscar na library pelo nome
                for lib_char in library_characters:
                    # Tentar match exato ou parcial
                    if lib_char.get("name") == char_name or lib_char.get("full_name") == char_name:
                        character_avatars[char_name] = lib_char.get("url")
                        logger.info(f"  ✅ Vinculado '{char_name}' → {lib_char.get('url')[:50]}...")
                        break
            
            # Salvar os avatares vinculados no projeto para próximas vezes
            if character_avatars:
                project["character_avatars"] = character_avatars
                _update_project_field(tenant_id, project_id, {
                    "character_avatars": character_avatars
                })
                logger.info(f"KlingStoryboard [{project_id}]: ✅ {len(character_avatars)} avatares vinculados da library e salvos no projeto")
    
    dialogues_data = project.get("dialogues", {}).get("scenes", [])
    target_audience = project.get("target_audience", "all")
    lang = project.get("language", "pt")
    
    # Calculate total duration
    total_duration = sum(
        _parse_time_to_seconds(s.get("time_end", "0:00")) - _parse_time_to_seconds(s.get("time_start", "0:00"))
        for s in scenes
    )
    
    # If total duration is less than 5 minutes, adjust the last scene to reach 300 seconds
    if total_duration < 300:
        logger.info(f"KlingStoryboard [{project_id}]: Total duration {total_duration}s < 300s, extending to 5 minutes")
        if len(scenes) == 1:
            scenes[0]["time_end"] = "5:00"
            scenes[0]["duration_seconds"] = 300
        else:
            # Extend last scene to reach 5 minutes total
            last_scene = scenes[-1]
            last_start = _parse_time_to_seconds(last_scene.get("time_start", "0:00"))
            needed_duration = 300 - (total_duration - (
                _parse_time_to_seconds(last_scene.get("time_end", "0:00")) - last_start
            ))
            last_scene["time_end"] = f"{(last_start + needed_duration)//60}:{(last_start + needed_duration)%60:02d}"
            last_scene["duration_seconds"] = needed_duration
    
    logger.info(f"KlingStoryboard [{project_id}]: Processing {len(scenes)} scenes with {len(characters)} characters")
    
    # Process scenes in batches of 5
    BATCH_SIZE = 5
    all_scene_storyboards = []
    
    for batch_start in range(0, len(scenes), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(scenes))
        batch_scenes = scenes[batch_start:batch_end]
        
        logger.info(f"KlingStoryboard [{project_id}]: Processing batch {batch_start//BATCH_SIZE + 1} (scenes {batch_start+1}-{batch_end})")
        
        # Process this batch in parallel
        tasks = []
        for scene in batch_scenes:
            # Find dialogue for this scene
            scene_num = scene.get("scene_number", 0)
            scene_dialogue = next(
                (d for d in dialogues_data if d.get("scene_number") == scene_num),
                None
            )
            
            # Create task for this scene
            task = _generate_storyboards_for_single_scene(
                scene,
                scene_dialogue,
                characters,
                target_audience,
                lang,
                tenant_id,
                project_id,
                project,  # projeto completo
                character_avatars  # NOVO: avatares selecionados
            )
            tasks.append(task)
        
        # Execute batch in parallel
        try:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Scene {batch_scenes[i].get('scene_number')} failed: {result}")
                    all_scene_storyboards.append({
                        "scene_number": batch_scenes[i].get("scene_number"),
                        "error": str(result),
                        "frames": []
                    })
                else:
                    all_scene_storyboards.append(result)
            
            logger.info(f"✅ Batch {batch_start//BATCH_SIZE + 1} complete")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise Exception(f"Batch processing failed: {str(e)}")
    
    # Calculate totals
    total_frames = sum(len(s.get("frames", [])) for s in all_scene_storyboards)
    
    logger.info(f"KlingStoryboard [{project_id}]: Saving {total_frames} frames to DB (flush_now=True)...")
    
    # Save all storyboards to project with IMMEDIATE flush to Supabase
    _update_project_field(tenant_id, project_id, {
        "kling_storyboards": all_scene_storyboards,
        "kling_storyboards_generated_at": datetime.now(timezone.utc).isoformat(),
        "kling_generation_status": {
            "phase": "complete",
            "total_frames": total_frames,
            "finished_at": datetime.now(timezone.utc).isoformat()
        }
    }, flush_now=True)
    
    # Verify the save actually persisted to DB
    verify_settings, _, verify_project = _get_project(tenant_id, project_id)
    saved_storyboards = verify_project.get("kling_storyboards", []) if verify_project else []
    saved_frames = sum(len(s.get("frames", [])) for s in saved_storyboards)
    
    if saved_frames == 0 and total_frames > 0:
        logger.error(f"KlingStoryboard [{project_id}]: CRITICAL — {total_frames} frames generated but 0 saved! Attempting direct DB save...")
        try:
            from core.deps import supabase as supa_client
            from core.cache import project_cache
            
            project_cache.invalidate(tenant_id)
            
            r = supa_client.table("tenants").select("settings").eq("id", tenant_id).single().execute()
            db_settings = r.data.get("settings", {}) if r.data else {}
            db_projects = db_settings.get("studio_projects", [])
            db_project = next((p for p in db_projects if p.get("id") == project_id), None)
            
            if db_project:
                db_project["kling_storyboards"] = all_scene_storyboards
                db_project["kling_storyboards_generated_at"] = datetime.now(timezone.utc).isoformat()
                db_project["updated_at"] = datetime.now(timezone.utc).isoformat()
                db_project["kling_generation_status"] = {"phase": "complete", "total_frames": total_frames, "finished_at": datetime.now(timezone.utc).isoformat()}
                db_settings["studio_projects"] = db_projects
                
                supa_client.table("tenants").update({"settings": db_settings}).eq("id", tenant_id).execute()
                logger.info(f"KlingStoryboard [{project_id}]: ✅ Direct DB save successful — {total_frames} frames persisted")
            else:
                logger.error(f"KlingStoryboard [{project_id}]: Project not found in DB for direct save!")
        except Exception as e:
            logger.error(f"KlingStoryboard [{project_id}]: Direct DB save also failed: {e}")
            raise
    else:
        logger.info(f"KlingStoryboard [{project_id}]: ✅ Verified {saved_frames} frames persisted to DB")



@router.delete("/projects/{project_id}/kling-storyboards")
async def delete_kling_storyboards(
    project_id: str,
    tenant=Depends(get_current_tenant)
):
    """
    Delete all Kling storyboards for a project
    Used before regenerating all frames
    """
    try:
        _update_project_field(tenant["id"], project_id, {
            "kling_storyboards": [],
            "kling_storyboards_generated_at": None
        }, flush_now=True)
        
        logger.info(f"KlingStoryboard [{project_id}]: Deleted all storyboards")
        
        return {
            "status": "success",
            "message": "All Kling storyboards deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting storyboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/kling-storyboards/regenerate-frame")
async def regenerate_single_frame(
    project_id: str,
    request: Dict,
    tenant=Depends(get_current_tenant)
):
    """
    Regenerate a single frame by frame_number WITH PROJECT CONTEXT
    """
    frame_number = request.get("frame_number")
    if not frame_number:
        raise HTTPException(status_code=400, detail="frame_number is required")
    
    try:
        settings, projects, project = _get_project(tenant["id"], project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        storyboards = project.get("kling_storyboards", [])
        if not storyboards:
            raise HTTPException(status_code=404, detail="No storyboards found")
        
        # Extract project context for regeneration
        visual_style = project.get("visual_style", "pixar_3d")
        target_audience = project.get("target_audience", "general")
        character_avatars = project.get("character_avatars", {})
        
        # character_avatars já contém {nome: URL} dos avatares
        # Vamos passar isso para a função que vai baixar e usar as imagens como referência
        
        if character_avatars:
            logger.info(f"🎨 Regenerando frame {frame_number} com {len(character_avatars)} avatares como referência visual")
            for char_name in character_avatars.keys():
                logger.info(f"  - {char_name}")
        else:
            logger.warning("⚠️ Nenhum character_avatar vinculado ao projeto")
        
        logger.info(f"📊 Context: style={visual_style}, audience={target_audience}, avatars={len(character_avatars)}")
        
        # Find the frame across all scenes
        frame_found = False
        for scene in storyboards:
            frames = scene.get("frames", [])
            for i, frame in enumerate(frames):
                if frame.get("frame_number") == frame_number:
                    # Generate new image for this frame WITH PROJECT CONTEXT
                    logger.info(f"Regenerating frame {frame_number}...")
                    
                    new_image_url = await _generate_frame_image_with_context(
                        frame, 
                        project_id,
                        visual_style,
                        character_avatars,  # Passar URLs dos avatares para download e uso como referência
                        target_audience
                    )
                    
                    # Update the frame with new image
                    frames[i]["image_url"] = new_image_url
                    frame_found = True
                    break
            
            if frame_found:
                break
        
        if not frame_found:
            raise HTTPException(status_code=404, detail=f"Frame {frame_number} not found")
        
        # Save updated storyboards with retry
        try:
            _update_project_field(tenant["id"], project_id, {
                "kling_storyboards": storyboards
            }, flush_now=True)
        except Exception as save_err:
            logger.warning(f"Primary save failed: {save_err}. Trying direct DB save...")
            # Fallback: direct Supabase save bypassing cache
            try:
                from core.deps import get_fresh_supabase
                from core.cache import project_cache
                import time as _time
                
                _time.sleep(2)
                project_cache.invalidate(tenant["id"])
                supa = get_fresh_supabase()
                r = supa.table("tenants").select("settings").eq("id", tenant["id"]).single().execute()
                db_settings = r.data.get("settings", {}) if r.data else {}
                db_project = next((p for p in db_settings.get("studio_projects", []) if p.get("id") == project_id), None)
                if db_project:
                    db_project["kling_storyboards"] = storyboards
                    supa.table("tenants").update({"settings": db_settings}).eq("id", tenant["id"]).execute()
                    logger.info(f"✅ Direct DB save successful for frame {frame_number}")
                else:
                    raise Exception("Project not found in DB")
            except Exception as e2:
                logger.error(f"Direct save also failed: {e2}")
                raise HTTPException(status_code=500, detail=f"Save failed: {e2}")
        
        logger.info(f"KlingStoryboard [{project_id}]: ✅ Regenerated frame {frame_number}")
        
        return {
            "status": "success",
            "frame_number": frame_number,
            "message": f"Frame {frame_number} regenerated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/projects/{project_id}/kling-storyboards/update-frame")
async def update_frame_fields(
    project_id: str,
    request: Dict,
    tenant=Depends(get_current_tenant)
):
    """
    Update editable fields of a single frame (image_prompt, kling_prompt, dialogue_text).
    Does NOT regenerate the image — just saves the text fields.
    """
    frame_number = request.get("frame_number")
    if not frame_number:
        raise HTTPException(status_code=400, detail="frame_number is required")

    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    storyboards = project.get("kling_storyboards", [])
    if not storyboards:
        raise HTTPException(status_code=404, detail="No storyboards found")

    # Allowed editable fields
    editable = {}
    for key in ("image_prompt", "kling_prompt", "dialogue_text"):
        if key in request:
            editable[key] = request[key]

    if not editable:
        raise HTTPException(status_code=400, detail="No editable fields provided (image_prompt, kling_prompt, dialogue_text)")

    # Find and update the frame
    frame_found = False
    for scene in storyboards:
        for frame in scene.get("frames", []):
            if frame.get("frame_number") == frame_number:
                frame.update(editable)
                frame_found = True
                break
        if frame_found:
            break

    if not frame_found:
        raise HTTPException(status_code=404, detail=f"Frame {frame_number} not found")

    # Persist
    _update_project_field(tenant["id"], project_id, {
        "kling_storyboards": storyboards
    }, flush_now=True)

    logger.info(f"KlingStoryboard [{project_id}]: Updated frame {frame_number} fields: {list(editable.keys())}")

    return {
        "status": "success",
        "frame_number": frame_number,
        "updated_fields": list(editable.keys())
    }


async def _generate_storyboards_for_single_scene(
    scene: Dict,
    dialogue: Optional[Dict],
    characters: List[Dict],
    target_audience: str,
    lang: str,
    tenant_id: str,
    project_id: str,
    project: Dict,  # projeto completo para acessar visual_style
    character_avatars: Dict[str, str]  # NOVO: {nome: avatar_url}
) -> Dict:
    """
    Generate storyboards for a single scene
    Number of frames based on scene duration (1 frame per 10 seconds)
    """
    # Calculate scene duration
    start_time = scene.get("time_start", "0:00")
    end_time = scene.get("time_end", "0:00")
    duration_secs = _parse_time_to_seconds(end_time) - _parse_time_to_seconds(start_time)
    
    # Calculate number of frames needed (1 per 10 seconds)
    num_frames = max(1, duration_secs // 10)
    
    scene_num = scene.get("scene_number", 0)
    scene_title = scene.get("title", f"Scene {scene_num}")
    
    logger.info(f"KlingStoryboard: Scene {scene_num} - {duration_secs}s → {num_frames} frames")
    
    # Step 1: Generate frame prompts
    try:
        frames_data = await _generate_frame_prompts_for_scene(
            scene,
            dialogue,
            characters,
            target_audience,
            lang,
            num_frames,
            duration_secs,
            project.get("visual_style", "pixar_3d"),  # estilo visual
            character_avatars  # NOVO: avatares
        )
    except Exception as e:
        logger.error(f"Scene {scene_num} prompt generation failed: {e}")
        raise
    
    # Step 2: Download character avatars ONCE for all frames (multimodal reference)
    avatar_images = await _download_avatar_images(character_avatars, project_id)
    
    # Step 3: Generate images in parallel WITH avatar references
    try:
        frames_with_images = await _generate_images_parallel(
            frames_data, tenant_id, project_id, 
            avatar_images=avatar_images,
            visual_style=project.get("visual_style", "pixar_3d"),
            target_audience=target_audience
        )
    except Exception as e:
        logger.error(f"Scene {scene_num} image generation failed: {e}")
        frames_with_images = frames_data
    
    return {
        "scene_number": scene_num,
        "scene_title": scene_title,
        "duration_seconds": duration_secs,
        "frames": frames_with_images
    }



def _extract_dialogue_for_timerange(dialogue_text: str, start_secs: int, end_secs: int) -> str:
    """Extract script/dialogue lines relevant to a specific time range.
    
    Handles multiple timestamp formats:
    - [0:00-1:00] or [ABERTURA - 0:00-1:00] 
    - [0:20-0:35]: 'text'
    - ABERTURA [0:20-0:35]: text
    """
    if not dialogue_text:
        return ""
    
    import re
    lines = dialogue_text.strip().split('\n')
    
    def parse_time(t: str) -> int:
        """Parse M:SS or MM:SS to seconds"""
        parts = t.strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    
    # Collect lines with their timestamps
    timed_blocks = []
    current_block = {"start": -1, "end": -1, "lines": []}
    
    for line in lines:
        # Match various timestamp patterns: [0:00-1:00], [TOPO - 4:00-4:45], ABERTURA [0:20-0:35]
        time_match = re.search(r'(\d+:\d+)\s*[-–]\s*(\d+:\d+)', line)
        
        if time_match:
            # Save previous block if any
            if current_block["lines"] and current_block["start"] >= 0:
                timed_blocks.append(current_block)
            
            block_start = parse_time(time_match.group(1))
            block_end = parse_time(time_match.group(2))
            current_block = {"start": block_start, "end": block_end, "lines": [line]}
        elif current_block["start"] >= 0:
            # Continue adding to current block
            if line.strip():
                current_block["lines"].append(line)
    
    # Don't forget the last block
    if current_block["lines"] and current_block["start"] >= 0:
        timed_blocks.append(current_block)
    
    # If we found timed blocks, extract those overlapping with the requested range
    if timed_blocks:
        relevant = []
        for block in timed_blocks:
            # Check if block overlaps with requested time range
            if block["end"] > start_secs and block["start"] < end_secs:
                relevant.extend(block["lines"])
        
        if relevant:
            return '\n'.join(relevant)
    
    # Fallback: proportional split
    total_lines = len([l for l in lines if l.strip()])
    if total_lines == 0:
        return ""
    
    total_duration = max(end_secs, 300)
    line_start = int((start_secs / total_duration) * total_lines)
    line_end = int((end_secs / total_duration) * total_lines)
    line_start = max(0, min(line_start, total_lines - 1))
    line_end = max(line_start + 1, min(line_end + 1, total_lines))
    
    non_empty = [l for l in lines if l.strip()]
    extracted = non_empty[line_start:line_end]
    return '\n'.join(extracted) if extracted else '\n'.join(non_empty[:5])


async def _generate_frame_prompts_for_scene(
    scene: Dict,
    dialogue: Optional[Dict],
    characters: List[Dict],
    target_audience: str,
    lang: str,
    num_frames: int,
    duration_secs: int,
    visual_style: str = "pixar_3d",  # estilo visual
    character_avatars: Dict[str, str] = None  # NOVO: {nome: avatar_url}
) -> List[Dict]:
    """
    Generate frame structures with detailed prompts for a single scene
    Uses mini-batch approach: generates 5 frames at a time for better reliability
    """
    
    # Build character context with DETAILED descriptions AND avatar references
    scene_characters = scene.get("characters_in_scene", [])
    character_avatars = character_avatars or {}
    
    char_descriptions = []
    for c in characters:
        char_name = c.get('name', 'Unknown')
        char_desc = c.get('description', 'No description')
        char_role = c.get('role', 'supporting')
        
        # Add avatar URL if available
        avatar_url = character_avatars.get(char_name)
        if avatar_url:
            char_descriptions.append(
                f"- {char_name}: {char_desc} (Role: {char_role})\n"
                f"  VISUAL REFERENCE: {avatar_url}\n"
                f"  IMPORTANT: Use this exact visual appearance in all frames!"
            )
        else:
            char_descriptions.append(f"- {char_name}: {char_desc} (Role: {char_role})")
    
    char_descriptions_text = "\n".join(char_descriptions)
    
    # Map visual style to description
    style_descriptions = {
        "pixar_3d": "Disney Pixar 3D animation style - cute, rounded characters, vibrant colors, cinematic lighting, high-quality CGI",
        "disney_2d": "Disney 2D hand-drawn animation style - classic animation, smooth lines, painted backgrounds",
        "anime": "Anime style - Japanese animation, expressive eyes, dynamic poses",
        "realistic": "Photorealistic live-action style - real people, natural lighting, cinematic",
        "cartoon": "Cartoon style - simplified, colorful, exaggerated features"
    }
    style_guide = style_descriptions.get(visual_style, style_descriptions["pixar_3d"])
    
    # Get dialogue text if available - use FULL script from dubbed_text, narrated_text, and description
    dialogue_text = ""
    if dialogue:
        dialogue_text = dialogue.get("dialogue", "")
    
    # Build COMPLETE SCRIPT from all scene sources (dubbed_text has the full timestamped dialogue)
    dubbed_text = scene.get("dubbed_text", "")
    narrated_text = scene.get("narrated_text", "")
    scene_description = scene.get("description", "")
    scene_camera = scene.get("camera", "")
    
    # The FULL SCRIPT is the combination of all these — dubbed_text is the primary source
    full_script = ""
    if dubbed_text:
        full_script += f"=== DIÁLOGO COMPLETO COM TIMESTAMPS ===\n{dubbed_text}\n\n"
    if narrated_text:
        full_script += f"=== NARRAÇÃO COM TIMESTAMPS ===\n{narrated_text}\n\n"
    if scene_description:
        full_script += f"=== DIREÇÃO DE CENA ===\n{scene_description}\n\n"
    if scene_camera:
        full_script += f"=== DIREÇÃO DE CÂMERA ===\n{scene_camera}\n\n"
    
    # Use full_script as primary source, fallback to dialogue_text
    if not full_script.strip():
        full_script = dialogue_text
    
    logger.info(f"KlingStoryboard: Full script assembled ({len(full_script)} chars from dubbed_text={len(dubbed_text)}, narrated={len(narrated_text)}, description={len(scene_description)})")
    
    # Get audience cinematography guidelines
    audience_guide = AUDIENCE_CINEMATOGRAPHY.get(lang, {}).get(target_audience, "")
    
    logger.info(f"Generating {num_frames} frames in mini-batches of 5...")
    
    all_frames = []
    last_frame_context = "Scene begins."
    
    # Generate in mini-batches of 5 frames
    MINI_BATCH_SIZE = 5
    for batch_start in range(0, num_frames, MINI_BATCH_SIZE):
        batch_end = min(batch_start + MINI_BATCH_SIZE, num_frames)
        frames_in_batch = batch_end - batch_start
        
        logger.info(f"  Mini-batch: frames {batch_start+1}-{batch_end} ({frames_in_batch} frames)")
        
        # Calculate time range for this batch to extract relevant dialogue
        batch_time_start_secs = batch_start * 10
        batch_time_end_secs = batch_end * 10
        batch_time_start_str = f"{batch_time_start_secs // 60}:{batch_time_start_secs % 60:02d}"
        batch_time_end_str = f"{batch_time_end_secs // 60}:{batch_time_end_secs % 60:02d}"
        
        # Extract the relevant part of the FULL SCRIPT for this time range
        relevant_script = _extract_dialogue_for_timerange(full_script, batch_time_start_secs, batch_time_end_secs)
        
        # Build prompt for this mini-batch
        system_prompt = f"""You are an ELITE CINEMATOGRAPHER creating storyboard frames for a children's animated video.

VISUAL STYLE: {style_guide}
TARGET AUDIENCE: {target_audience}
{audience_guide}

TASK: Generate exactly {frames_in_batch} frames (frames {batch_start+1} to {batch_end} of {num_frames} total).
Each frame covers exactly 10 seconds. Time range: {batch_time_start_str} to {batch_time_end_str}.

ABSOLUTE RULES FOR SCRIPT FIDELITY:
1. Each frame MUST show EXACTLY what the script says happens at that timestamp.
   - Read the script segment carefully for this time range
   - If at 0:00-0:10 Sara is singing a lullaby to Isaac, the frame MUST show Sara singing to baby Isaac
   - If at 4:40-4:50 an Angel appears with divine light, the frame MUST show the Angel appearing
   - NEVER invent actions not in the script. NEVER skip script actions.
2. The image_prompt MUST describe the SPECIFIC characters, their EXACT actions, emotions and positions as written in the script
3. Include dialogue/speech as visual context (who is speaking, their expression)
4. The kling_prompt should describe the 10-second movement/animation for that exact moment
5. Return ONLY a valid JSON array of {frames_in_batch} objects

JSON format per frame:
{{
  "frame_number": N,
  "time_start": "M:SS",
  "time_end": "M:SS",
  "dialogue_text": "[EXACT dialogue/narration text spoken during this 10-second window, copied verbatim from the script. If no speech, describe the sound/ambient]",
  "image_prompt": "[style]. [EXACT scene matching script]. [character positions, expressions, lighting]",
  "kling_prompt": "[10-second animation: character movements, camera moves matching script action]",
  "characters_present": ["name1", "name2"],
  "camera_movement": "type",
  "key_action": "brief action summary in Portuguese",
  "emotion": "primary emotion",
  "lighting": "lighting description"
}}

Language: {"Portuguese" if lang == "pt" else "English"}"""
        
        user_prompt = f"""SCENE: {scene.get('title', 'Untitled')}

===== SCRIPT PARA ESTE INTERVALO ({batch_time_start_str} a {batch_time_end_str}) =====
{relevant_script if relevant_script else '(Sem script específico para este intervalo — use o contexto geral)'}
===== FIM DO SCRIPT DO INTERVALO =====

SCRIPT COMPLETO (para contexto de continuidade):
{full_script[:4000]}

CHARACTERS:
{char_descriptions_text}

MAIN CHARACTERS IN SCENE: {', '.join(scene_characters)}

PREVIOUS FRAME CONTEXT:
{last_frame_context}

Generate {frames_in_batch} frames. Each frame must have:
- frame_number: {batch_start+1} to {batch_end}
- time_start & time_end (format "M:SS")
- dialogue_text: The EXACT spoken dialogue or narration text for this 10-second window (copy verbatim from script). If silence, describe the ambient sound.
- image_prompt: Detailed visual description
- kling_prompt: Detailed 10-second action description
- characters_present: List of character names
- camera_movement: e.g., "dolly forward", "static", "pan right"
- key_action: Brief description
- emotion: Emotional tone
- lighting: Lighting description

CRITICAL: dialogue_text must contain the EXACT words from the script for this time window. This is essential for syncing audio with visuals.

Return ONLY a JSON array of {frames_in_batch} frame objects. No markdown, no explanation."""
        
        try:
            # Call Claude for this mini-batch
            result = await _call_claude_for_mini_batch(system_prompt, user_prompt, frames_in_batch)
            
            # Parse result
            frames_batch = _parse_frames_response(result, frames_in_batch, batch_start)
            
            if not frames_batch:
                logger.warning(f"Mini-batch {batch_start+1}-{batch_end} failed, using fallback")
                frames_batch = _generate_fallback_frames(
                    scene, batch_start, frames_in_batch, duration_secs, scene_characters
                )
            
            all_frames.extend(frames_batch)
            
            # Update context for next batch
            if frames_batch:
                last_frame = frames_batch[-1]
                last_frame_context = f"Frame {last_frame.get('frame_number')} ended with: {last_frame.get('key_action', 'action continues')}. Camera at: {last_frame.get('camera_movement', 'static')}."
            
            logger.info(f"  ✅ Mini-batch {batch_start+1}-{batch_end} complete")
            
        except Exception as e:
            logger.error(f"Mini-batch {batch_start+1}-{batch_end} error: {e}")
            # Generate fallback frames
            frames_batch = _generate_fallback_frames(
                scene, batch_start, frames_in_batch, duration_secs, scene_characters
            )
            all_frames.extend(frames_batch)
    
    logger.info(f"✅ Generated {len(all_frames)} frames total")
    return all_frames


async def _call_claude_for_mini_batch(system: str, user: str, expected_frames: int) -> str:
    """Call LLM for a mini-batch of frames. Uses OpenAI as primary (Claude quota exhausted)."""
    import litellm
    
    # Try OpenAI first (Claude quota exhausted), then Claude as fallback
    models = [
        ("gpt-4o-mini", os.environ.get("OPENAI_API_KEY")),
        ("anthropic/claude-sonnet-4-20250514", os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")),
    ]
    
    for model_name, api_key in models:
        if not api_key:
            continue
        try:
            response = await litellm.acompletion(
                model=model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                max_tokens=8000,
                timeout=120,
                api_key=api_key
            )
            text = response.choices[0].message.content
            if text:
                logger.info(f"Mini-batch LLM [{model_name}]: OK ({len(text)} chars)")
                return text
        except Exception as e:
            logger.warning(f"Mini-batch LLM [{model_name}] failed: {str(e)[:100]}")
            continue
    
    raise Exception("All LLM models failed for mini-batch")


def _parse_frames_response(response: str, expected_count: int, start_index: int) -> List[Dict]:
    """Parse Claude response into frames array"""
    import json
    import re
    
    # Try direct JSON parse first
    try:
        data = json.loads(response)
        if isinstance(data, list) and len(data) > 0:
            return data
    except:
        pass
    
    # Try extracting JSON array with regex
    try:
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        # Find array
        array_match = re.search(r'\[[\s\S]*\]', cleaned)
        if array_match:
            data = json.loads(array_match.group(0))
            if isinstance(data, list):
                return data
    except Exception as e:
        logger.error(f"Regex extraction failed: {e}")
    
    # Try line-by-line object extraction (if Claude returned objects separated)
    try:
        objects = re.findall(r'\{[^}]+\}', response, re.DOTALL)
        frames = []
        for obj_str in objects:
            try:
                frame = json.loads(obj_str)
                if 'frame_number' in frame:
                    frames.append(frame)
            except:
                continue
        if len(frames) > 0:
            return frames
    except:
        pass
    
    return []


def _generate_fallback_frames(
    scene: Dict, 
    start_index: int, 
    count: int, 
    total_duration: int,
    characters: List[str]
) -> List[Dict]:
    """Generate simple fallback frames if AI generation fails"""
    frames = []
    for i in range(count):
        frame_num = start_index + i + 1
        start_sec = (frame_num - 1) * 10
        end_sec = min(start_sec + 10, total_duration)
        
        frames.append({
            "frame_number": frame_num,
            "time_start": f"{start_sec//60}:{start_sec%60:02d}",
            "time_end": f"{end_sec//60}:{end_sec%60:02d}",
            "dialogue_text": "(Sem diálogo específico para este intervalo)",
            "image_prompt": f"{scene.get('title', 'Scene')} - Frame {frame_num}. {scene.get('description', 'Scene continues.')}",
            "kling_prompt": f"[{start_sec//60}:{start_sec%60:02d}-{end_sec//60}:{end_sec%60:02d}] {scene.get('description', 'Action continues.')} Characters: {', '.join(characters)}. Camera static. Natural lighting.",
            "characters_present": characters,
            "camera_movement": "static",
            "key_action": "scene continues",
            "emotion": scene.get("emotion", "neutral"),
            "lighting": "natural"
        })
    
    return frames
async def _call_claude_for_frames(system: str, user: str) -> str:
    """Call Claude with large context for frame generation"""
    import litellm
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
    
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        max_tokens=16000,  # Need large output for 30 frames
        timeout=300,  # 5 minutes
        api_key=api_key
    )
    
    return response.choices[0].message.content


async def _download_avatar_images(character_avatars: Dict[str, str], project_id: str) -> List[Dict]:
    """
    Download character avatar images ONCE and convert to base64 for multimodal Gemini input.
    Returns list of {name, inline_data} dicts ready for Gemini API.
    """
    import httpx
    import base64
    
    avatar_images = []
    
    if not character_avatars:
        logger.info(f"KlingStoryboard [{project_id}]: No character avatars to download")
        return avatar_images
    
    logger.info(f"KlingStoryboard [{project_id}]: Downloading {len(character_avatars)} avatar images for visual reference...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for char_name, avatar_url in character_avatars.items():
            if not avatar_url:
                continue
            try:
                response = await client.get(avatar_url)
                if response.status_code == 200:
                    image_bytes = response.content
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Detect mime type
                    mime_type = "image/png"
                    if avatar_url.lower().endswith(".jpg") or avatar_url.lower().endswith(".jpeg"):
                        mime_type = "image/jpeg"
                    elif avatar_url.lower().endswith(".webp"):
                        mime_type = "image/webp"
                    
                    avatar_images.append({
                        "name": char_name,
                        "inline_data": {
                            "mimeType": mime_type,
                            "data": image_base64
                        }
                    })
                    logger.info(f"  ✅ {char_name}: Avatar downloaded ({len(image_bytes)} bytes)")
                else:
                    logger.warning(f"  ⚠️ {char_name}: Failed to download avatar (HTTP {response.status_code})")
            except Exception as e:
                logger.warning(f"  ⚠️ {char_name}: Error downloading avatar: {e}")
    
    logger.info(f"KlingStoryboard [{project_id}]: {len(avatar_images)}/{len(character_avatars)} avatars ready for multimodal input")
    return avatar_images


async def _generate_images_parallel(
    frames: List[Dict], tenant_id: str, project_id: str,
    avatar_images: List[Dict] = None,
    visual_style: str = "pixar_3d",
    target_audience: str = "general"
) -> List[Dict]:
    """Generate images for all frames in parallel batches WITH character avatar references"""
    
    avatar_images = avatar_images or []
    
    # Process in 3 batches of 10 frames each
    BATCH_SIZE = 10
    batches = [frames[i:i+BATCH_SIZE] for i in range(0, len(frames), BATCH_SIZE)]
    
    all_results = []
    
    for batch_num, batch in enumerate(batches, 1):
        logger.info(f"KlingStoryboard: Processing batch {batch_num}/3 ({len(batch)} frames)...")
        
        # Generate images in parallel for this batch
        tasks = [
            _generate_single_frame_image(
                frame, tenant_id, project_id,
                avatar_images=avatar_images,
                visual_style=visual_style,
                target_audience=target_audience
            )
            for frame in batch
        ]
        
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Frame {batch[i].get('frame_number')} failed: {result}")
                # Keep frame but mark as failed
                batch[i]["image_url"] = None
                batch[i]["image_error"] = str(result)
            else:
                batch[i]["image_url"] = result
        
        all_results.extend(batch)
        logger.info(f"✅ Batch {batch_num}/3 complete")
    
    return all_results


async def _generate_single_frame_image(
    frame: Dict, tenant_id: str, project_id: str,
    avatar_images: List[Dict] = None,
    visual_style: str = "pixar_3d",
    target_audience: str = "general"
) -> str:
    """
    Generate image for a single frame using Gemini with MULTIMODAL avatar references.
    Sends character avatar images alongside text prompt so Gemini replicates exact characters.
    """
    
    image_prompt = frame.get("image_prompt", "")
    frame_num = frame.get("frame_number", 0)
    avatar_images = avatar_images or []
    
    # Map visual style
    style_descriptions = {
        "pixar_3d": "Disney Pixar 3D animation style - cute, rounded characters, vibrant colors, cinematic lighting",
        "disney_2d": "Disney 2D hand-drawn animation style",
        "anime": "Anime style - Japanese animation",
        "realistic": "Photorealistic live-action style",
        "cartoon": "Cartoon style - simplified, colorful"
    }
    style_guide = style_descriptions.get(visual_style, style_descriptions["pixar_3d"])
    
    # Build audience context
    audience_context = ""
    if target_audience in ("baby", "0-2"):
        audience_context = "Para bebês (0-2 anos): formas arredondadas, alto contraste, cores primárias."
    elif target_audience in ("crianca", "3-6"):
        audience_context = "Para crianças (3-6 anos): visuais coloridos, personagens amigáveis."
    
    # Build character reference text
    char_refs = []
    for av in avatar_images:
        char_refs.append(f"PERSONAGEM {av['name']}: Use a aparência EXATA da imagem de referência acima.")
    char_ref_text = "\n".join(char_refs) if char_refs else ""
    
    # Build the full text prompt
    text_prompt = f"""ESTILO VISUAL: {style_guide}
{audience_context}

{f"REFERÊNCIAS DE PERSONAGENS (imagens acima):{chr(10)}{char_ref_text}{chr(10)}IMPORTANTE: Mantenha a aparência EXATA dos personagens mostrados nas imagens acima!" if char_refs else ""}

CENA:
{image_prompt[:1200]}

REQUISITOS:
1. DEVE usar o estilo {visual_style}
2. DEVE manter a aparência visual dos personagens das referências
3. NÃO criar novos designs - usar os personagens fornecidos"""

    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            raise Exception("GEMINI_API_KEY not found")
        
        import httpx
        import base64
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        headers = {
            "x-goog-api-key": gemini_key,
            "Content-Type": "application/json"
        }
        
        # Build MULTIMODAL parts: avatar images first, then text prompt
        parts = []
        
        # Add character avatar images as visual references
        for av in avatar_images:
            parts.append({"inlineData": av["inline_data"]})
        
        # Add text prompt
        parts.append({"text": text_prompt})
        
        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        
        if avatar_images:
            logger.info(f"Frame {frame_num}: Calling Gemini with {len(avatar_images)} avatar references (multimodal)")
        else:
            logger.info(f"Frame {frame_num}: Calling Gemini (text-only, no avatars)")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}: {response.text[:300]}")
            
            result = response.json()
            
            if "candidates" in result:
                for candidate in result["candidates"]:
                    if "content" in candidate:
                        resp_parts = candidate["content"].get("parts", [])
                        for part in resp_parts:
                            if "inlineData" in part:
                                image_base64 = part["inlineData"].get("data")
                                
                                if image_base64:
                                    image_url = await _upload_base64_to_supabase(
                                        image_base64, 
                                        tenant_id, 
                                        project_id, 
                                        f"storyboard_frame_{frame_num}.png"
                                    )
                                    
                                    logger.info(f"Frame {frame_num}: ✅ Image generated and uploaded")
                                    return image_url
            
            raise Exception(f"No image found in response: {result.keys()}")
            
    except Exception as e:
        logger.error(f"Frame {frame_num} image generation failed: {e}")
        raise


async def _upload_base64_to_supabase(
    base64_data: str, 
    tenant_id: str, 
    project_id: str, 
    filename: str
) -> str:
    """Upload base64 image to Supabase storage and return public URL with cache-busting"""
    import base64
    import time as _time
    from supabase import create_client
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not supabase_key:
        raise Exception("Supabase credentials not found")
    
    # Decode base64 to bytes
    image_bytes = base64.b64decode(base64_data)
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    # Add timestamp to filename to bust CDN/browser cache
    ts = int(_time.time())
    name_parts = filename.rsplit('.', 1)
    if len(name_parts) == 2:
        versioned_filename = f"{name_parts[0]}_{ts}.{name_parts[1]}"
    else:
        versioned_filename = f"{filename}_{ts}"
    
    storage_path = f"{tenant_id}/projects/{project_id}/storyboards/{versioned_filename}"
    
    try:
        response = supabase.storage.from_("pipeline-assets").upload(
            path=storage_path,
            file=image_bytes,
            file_options={"content-type": "image/png", "upsert": "true"}
        )
        
        public_url = supabase.storage.from_("pipeline-assets").get_public_url(storage_path)
        
        return public_url
        
    except Exception as e:
        logger.error(f"Supabase upload failed: {e}")
        raise


def _parse_time_to_seconds(time_str: str) -> int:
    """Parse time string like '0:00' or '5:00' to seconds"""
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    except:
        return 0


@router.get("/projects/{project_id}/kling-storyboards")
async def get_kling_storyboards(project_id: str, tenant=Depends(get_current_tenant)):
    """Get generated Kling storyboards with generation status"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    storyboards = project.get("kling_storyboards", [])
    generation_status = project.get("kling_generation_status", {})
    
    # Calculate total frames across all scenes (each scene has a "frames" array)
    total_frames = sum(len(s.get("frames", [])) for s in storyboards)
    
    return {
        "has_storyboards": len(storyboards) > 0,
        "total_scenes": len(storyboards),
        "total_frames": total_frames,
        "scenes": storyboards,
        "generated_at": project.get("kling_storyboards_generated_at"),
        "generation_status": generation_status
    }



@router.post("/projects/{project_id}/kling-storyboards/regenerate-images")
async def regenerate_images(project_id: str, tenant=Depends(get_current_tenant)):
    """
    Regenerate images for all frames using system image generation tool
    Processes in small batches (4 at a time) for reliability
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    storyboards = project.get("kling_storyboards", [])
    if not storyboards:
        raise HTTPException(status_code=400, detail="No storyboards found")
    
    logger.info(f"RegenerateImages [{project_id}]: Starting image generation for all frames")
    
    total_generated = 0
    total_failed = 0
    
    for scene_data in storyboards:
        scene_num = scene_data.get("scene_number", 0)
        frames = scene_data.get("frames", [])
        
        logger.info(f"Scene {scene_num}: Generating {len(frames)} images...")
        
        # Process in batches of 4 to avoid overwhelming the API
        BATCH_SIZE = 4
        for batch_start in range(0, len(frames), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(frames))
            batch = frames[batch_start:batch_end]
            
            logger.info(f"  Processing frames {batch_start+1}-{batch_end}...")
            
            # Generate images sequentially in this batch (more reliable)
            for frame in batch:
                frame_num = frame.get("frame_number", 0)
                
                # Skip if already has image
                if frame.get("image_url"):
                    logger.info(f"    Frame {frame_num}: Already has image, skipping")
                    continue
                
                try:
                    image_url = await _generate_frame_image_with_tool(frame, project_id)
                    frame["image_url"] = image_url
                    frame.pop("image_error", None)
                    total_generated += 1
                    logger.info(f"    Frame {frame_num}: ✅ Image generated")
                except Exception as e:
                    logger.error(f"    Frame {frame_num}: ❌ Failed - {e}")
                    frame["image_error"] = str(e)
                    total_failed += 1
            
            # Save progress after each batch
            _update_project_field(tenant["id"], project_id, {
                "kling_storyboards": storyboards
            }, flush_now=True)
            logger.info(f"  Batch complete. Progress: {total_generated} generated, {total_failed} failed")
    
    logger.info(f"RegenerateImages [{project_id}]: Complete! {total_generated} generated, {total_failed} failed")
    
    return {
        "status": "success",
        "total_generated": total_generated,
        "total_failed": total_failed,
        "storyboards": storyboards
    }


async def _generate_frame_image_with_context(
    frame: Dict, 
    project_id: str,
    visual_style: str = "pixar_3d",
    character_prompts: Dict[str, str] = None,  # Agora recebe URLs dos avatares, não prompts
    target_audience: str = "general"
) -> str:
    """
    Generate image for a frame using Gemini Nano Banana WITH PROJECT CONTEXT
    USA AS IMAGENS DOS AVATARES como referência visual (multimodal input)
    
    IMPORTANTE: Gemini suporta entrada multimodal - podemos passar as IMAGENS dos personagens
    junto com o texto para que o modelo use os avatares já criados como referência!
    """
    base_image_prompt = frame.get("image_prompt", "")
    frame_num = frame.get("frame_number", 0)
    
    if not base_image_prompt:
        raise Exception("No image_prompt available")
    
    # character_prompts na verdade contém as URLs dos avatares
    character_avatar_urls = character_prompts or {}
    
    # Map visual style to description
    style_descriptions = {
        "pixar_3d": "Disney Pixar 3D animation style - cute, rounded characters, vibrant colors, cinematic lighting, high-quality CGI",
        "disney_2d": "Disney 2D hand-drawn animation style - classic animation, smooth lines, painted backgrounds",
        "anime": "Anime style - Japanese animation, expressive eyes, dynamic poses",
        "realistic": "Photorealistic live-action style - real people, natural lighting, cinematic",
        "cartoon": "Cartoon style - simplified, colorful, exaggerated features"
    }
    style_guide = style_descriptions.get(visual_style, style_descriptions["pixar_3d"])
    
    # Build audience-specific context
    audience_context = ""
    if target_audience == "baby" or target_audience == "0-2":
        audience_context = "PÚBLICO-ALVO: Bebês (0-2 anos) - Usar formas extremamente simples e arredondadas, alto contraste, cores primárias brilhantes, objetos grandes, detalhes mínimos."
    elif target_audience == "crianca" or target_audience == "3-6":
        audience_context = "PÚBLICO-ALVO: Crianças (3-6 anos) - Usar visuais coloridos e envolventes com formas claras e personagens amigáveis."
    
    # Download avatar images and convert to base64 for multimodal input
    import httpx
    import base64
    
    character_images = []
    character_references = []
    
    if character_avatar_urls:
        logger.info(f"Frame {frame_num}: Baixando {len(character_avatar_urls)} imagens de avatares para referência visual...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for char_name, avatar_url in character_avatar_urls.items():
                try:
                    # Download avatar image
                    response = await client.get(avatar_url)
                    if response.status_code == 200:
                        # Convert to base64
                        image_bytes = response.content
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        # Add to multimodal parts
                        character_images.append({
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": image_base64
                            }
                        })
                        
                        character_references.append(
                            f"PERSONAGEM {char_name}: Use a aparência EXATA da imagem de referência acima. "
                            f"Sempre que {char_name} aparecer na cena, mantenha TODAS as características visuais desta imagem!"
                        )
                        
                        logger.info(f"  ✅ {char_name}: Imagem carregada ({len(image_bytes)} bytes)")
                    else:
                        logger.warning(f"  ⚠️ {char_name}: Erro ao baixar avatar (HTTP {response.status_code})")
                except Exception as e:
                    logger.warning(f"  ⚠️ {char_name}: Erro ao processar avatar: {e}")
    
    character_context = "\n\n".join(character_references) if character_references else ""
    
    # Build the text prompt
    text_prompt = f"""ESTILO VISUAL OBRIGATÓRIO: {style_guide}

{audience_context}

PERSONAGENS NA CENA:
As imagens acima mostram a aparência EXATA dos personagens. Use-as como referência visual obrigatória.
{character_context}

DESCRIÇÃO DA CENA:
{base_image_prompt}

REQUISITOS CRÍTICOS:
1. DEVE usar o estilo {visual_style} em todos os elementos
2. DEVE manter a aparência visual EXATA dos personagens mostrados nas imagens de referência acima
3. NÃO criar novos designs para os personagens - usar EXATAMENTE as imagens fornecidas
4. DEVE adaptar ao nível do público-alvo {target_audience}
5. NÃO misturar estilos ou alterar aparência dos personagens
"""
    
    logger.info(f"Frame {frame_num}: Gerando imagem com {len(character_images)} referências visuais de personagens")
    
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            raise Exception("GEMINI_API_KEY not found")
        
        from supabase import create_client
        
        # Gemini Nano Banana endpoint
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        headers = {
            "x-goog-api-key": gemini_key,
            "Content-Type": "application/json"
        }
        
        # Build multimodal parts: images first, then text prompt
        parts = []
        
        # Add character reference images
        for char_img in character_images:
            parts.append(char_img)
        
        # Add text prompt
        parts.append({"text": text_prompt})
        
        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract base64 image from response
            if "candidates" in result:
                for candidate in result["candidates"]:
                    if "content" in candidate:
                        parts_response = candidate["content"].get("parts", [])
                        for part in parts_response:
                            if "inlineData" in part:
                                image_base64 = part["inlineData"].get("data")
                                
                                if image_base64:
                                    # Decode base64 to bytes
                                    image_bytes = base64.b64decode(image_base64)
                                    
                                    # Upload to Supabase
                                    supabase_url = os.environ.get("SUPABASE_URL", "")
                                    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
                                    
                                    if not supabase_url or not supabase_key:
                                        raise Exception("Supabase credentials not found")
                                    
                                    supabase = create_client(supabase_url, supabase_key)
                                    
                                    # Storage path with timestamp to force cache refresh
                                    import time
                                    timestamp = int(time.time())
                                    storage_path = f"storyboards/{project_id}/frame_{frame_num}_{timestamp}.png"
                                    
                                    supabase.storage.from_("pipeline-assets").upload(
                                        path=storage_path,
                                        file=image_bytes,
                                        file_options={"content-type": "image/png", "upsert": "true"}
                                    )
                                    
                                    # Get public URL
                                    public_url = supabase.storage.from_("pipeline-assets").get_public_url(storage_path)
                                    
                                    logger.info(f"Frame {frame_num}: ✅ Imagem regenerada com referências visuais dos personagens")
                                    return public_url
            
            raise Exception("No image found in response")
            
    except Exception as e:
        logger.info(f"Image regeneration error: {e}")
        raise
    
    logger.info(f"Frame {frame_num}: Regenerating with context (style={visual_style}, audience={target_audience}, avatars={len(character_avatars)})")
    
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            raise Exception("GEMINI_API_KEY not found")
        
        import httpx
        import base64
        from supabase import create_client
        
        # Gemini Nano Banana endpoint
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        headers = {
            "x-goog-api-key": gemini_key,
            "Content-Type": "application/json"
        }
        
        # Limit prompt to 1500 chars for best results
        final_prompt = enriched_prompt[:1500] if len(enriched_prompt) > 1500 else enriched_prompt
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": final_prompt
                }]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract base64 image from response
            if "candidates" in result:
                for candidate in result["candidates"]:
                    if "content" in candidate:
                        parts = candidate["content"].get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                image_base64 = part["inlineData"].get("data")
                                
                                if image_base64:
                                    # Decode base64 to bytes
                                    image_bytes = base64.b64decode(image_base64)
                                    
                                    # Upload to Supabase
                                    supabase_url = os.environ.get("SUPABASE_URL", "")
                                    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
                                    
                                    if not supabase_url or not supabase_key:
                                        raise Exception("Supabase credentials not found")
                                    
                                    supabase = create_client(supabase_url, supabase_key)
                                    
                                    # Storage path with timestamp to force cache refresh
                                    import time
                                    timestamp = int(time.time())
                                    storage_path = f"storyboards/{project_id}/frame_{frame_num}_{timestamp}.png"
                                    
                                    supabase.storage.from_("pipeline-assets").upload(
                                        path=storage_path,
                                        file=image_bytes,
                                        file_options={"content-type": "image/png", "upsert": "true"}
                                    )
                                    
                                    # Get public URL
                                    public_url = supabase.storage.from_("pipeline-assets").get_public_url(storage_path)
                                    
                                    logger.info(f"Frame {frame_num}: ✅ Image regenerated with context")
                                    return public_url
            
            raise Exception("No image found in response")
            
    except Exception as e:
        logger.info(f"Image regeneration error: {e}")
        raise


async def _generate_frame_image_with_tool(frame: Dict, project_id: str) -> str:
    """
    Generate image for a frame using Gemini Nano Banana with native GEMINI_API_KEY
    """
    image_prompt = frame.get("image_prompt", "")
    frame_num = frame.get("frame_number", 0)
    
    if not image_prompt:
        raise Exception("No image_prompt available")
    
    logger.info(f"      Generating image for frame {frame_num}...")
    
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            raise Exception("GEMINI_API_KEY not found")
        
        import httpx
        import base64
        from supabase import create_client
        
        # Gemini Nano Banana endpoint
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        headers = {
            "x-goog-api-key": gemini_key,
            "Content-Type": "application/json"
        }
        
        # Simplify prompt for better results (keep under 1000 chars)
        simplified_prompt = image_prompt[:1000] if len(image_prompt) > 1000 else image_prompt
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": simplified_prompt
                }]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Extract base64 image from response
            if "candidates" in result:
                for candidate in result["candidates"]:
                    if "content" in candidate:
                        parts = candidate["content"].get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                image_base64 = part["inlineData"].get("data")
                                
                                if image_base64:
                                    # Decode base64 to bytes
                                    image_bytes = base64.b64decode(image_base64)
                                    
                                    # Upload to Supabase
                                    supabase_url = os.environ.get("SUPABASE_URL", "")
                                    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
                                    
                                    if not supabase_url or not supabase_key:
                                        raise Exception("Supabase credentials not found")
                                    
                                    supabase = create_client(supabase_url, supabase_key)
                                    
                                    # Get tenant ID from project
                                    storage_path = f"storyboards/{project_id}/frame_{frame_num}.png"
                                    
                                    supabase.storage.from_("pipeline-assets").upload(
                                        path=storage_path,
                                        file=image_bytes,
                                        file_options={"content-type": "image/png", "upsert": "true"}
                                    )
                                    
                                    # Get public URL
                                    public_url = supabase.storage.from_("pipeline-assets").get_public_url(storage_path)
                                    
                                    logger.info(f"      Frame {frame_num}: ✅ Image generated")
                                    return public_url
            
            raise Exception("No image found in response")
            
    except Exception as e:
        logger.info(f"      Image generation error: {e}")
        raise
