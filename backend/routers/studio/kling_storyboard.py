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
    Generate ultra-detailed storyboards for ALL scenes in project
    Processes 5 scenes at a time in parallel for efficiency
    Each scene gets storyboards based on its duration (1 per 10 seconds)
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes available")
    
    # Get project metadata
    characters = project.get("characters", [])
    dialogues_data = project.get("dialogues", {}).get("scenes", [])
    target_audience = project.get("target_audience", "all")
    lang = project.get("language", "pt")
    
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
                tenant["id"],
                project_id
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
            raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")
    
    # Save all storyboards to project
    _update_project_field(tenant["id"], project_id, {
        "kling_storyboards": all_scene_storyboards,
        "kling_storyboards_generated_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Calculate totals
    total_frames = sum(len(s.get("frames", [])) for s in all_scene_storyboards)
    
    logger.info(f"KlingStoryboard [{project_id}]: ✅ Generated {total_frames} frames across {len(scenes)} scenes")
    
    return {
        "status": "success",
        "total_scenes": len(scenes),
        "total_frames": total_frames,
        "scenes": all_scene_storyboards
    }


async def _generate_storyboards_for_single_scene(
    scene: Dict,
    dialogue: Optional[Dict],
    characters: List[Dict],
    target_audience: str,
    lang: str,
    tenant_id: str,
    project_id: str
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
            duration_secs
        )
    except Exception as e:
        logger.error(f"Scene {scene_num} prompt generation failed: {e}")
        raise
    
    # Step 2: Generate images in parallel
    try:
        frames_with_images = await _generate_images_parallel(frames_data, tenant_id, project_id)
    except Exception as e:
        logger.error(f"Scene {scene_num} image generation failed: {e}")
        # Continue with frames but without images
        frames_with_images = frames_data
    
    return {
        "scene_number": scene_num,
        "scene_title": scene_title,
        "duration_seconds": duration_secs,
        "frames": frames_with_images
    }


async def _generate_frame_prompts_for_scene(
    scene: Dict,
    dialogue: Optional[Dict],
    characters: List[Dict],
    target_audience: str,
    lang: str,
    num_frames: int,
    duration_secs: int
) -> List[Dict]:
    """
    Generate frame structures with detailed prompts for a single scene
    Uses mini-batch approach: generates 5 frames at a time for better reliability
    """
    
    # Build character context
    scene_characters = scene.get("characters_in_scene", [])
    char_descriptions = "\n".join([
        f"- {c.get('name', 'Unknown')}: {c.get('description', 'No description')} (Role: {c.get('role', 'supporting')})"
        for c in characters
    ])
    
    # Get dialogue text if available
    dialogue_text = ""
    if dialogue:
        dialogue_text = dialogue.get("dialogue", "")
    
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
        
        # Build prompt for this mini-batch
        system_prompt = f"""You are an ELITE CINEMATOGRAPHER creating detailed storyboard frames.

TARGET AUDIENCE: {target_audience}
{audience_guide}

TASK: Generate {frames_in_batch} consecutive frames (frames {batch_start+1} to {batch_end} of {num_frames} total).
Each frame = 10 seconds of video.

CRITICAL RULES:
1. image_prompt: Visual description including character appearance
2. kling_prompt: Action description (character names only, NO physical descriptions)
3. Ensure CONTINUITY from previous frame
4. Return ONLY valid JSON array

Language: {"Portuguese" if lang == "pt" else "English"}"""
        
        user_prompt = f"""SCENE: {scene.get('title', 'Untitled')}
Description: {scene.get('description', '')}
Duration: {duration_secs}s (frames {batch_start+1}-{batch_end} out of {num_frames} total)

CHARACTERS:
{char_descriptions}

MAIN CHARACTERS IN SCENE: {', '.join(scene_characters)}

DIALOGUE SNIPPET (for timing reference):
{dialogue_text[:500] if dialogue_text else "No dialogue"}...

PREVIOUS FRAME CONTEXT:
{last_frame_context}

Generate {frames_in_batch} frames. Each frame must have:
- frame_number: {batch_start+1} to {batch_end}
- time_start & time_end (format "M:SS")
- image_prompt: Detailed visual description
- kling_prompt: Detailed 10-second action description
- characters_present: List of character names
- camera_movement: e.g., "dolly forward", "static", "pan right"
- key_action: Brief description
- emotion: Emotional tone
- lighting: Lighting description

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
    """Call Claude for a mini-batch of frames"""
    import litellm
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
    
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        max_tokens=8000,  # Enough for 5 frames
        timeout=120,
        api_key=api_key
    )
    
    return response.choices[0].message.content


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


async def _generate_images_parallel(frames: List[Dict], tenant_id: str, project_id: str) -> List[Dict]:
    """Generate images for all frames in parallel batches"""
    
    # Process in 3 batches of 10 frames each
    BATCH_SIZE = 10
    batches = [frames[i:i+BATCH_SIZE] for i in range(0, len(frames), BATCH_SIZE)]
    
    all_results = []
    
    for batch_num, batch in enumerate(batches, 1):
        logger.info(f"KlingStoryboard: Processing batch {batch_num}/3 ({len(batch)} frames)...")
        
        # Generate images in parallel for this batch
        tasks = [
            _generate_single_frame_image(frame, tenant_id, project_id)
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


async def _generate_single_frame_image(frame: Dict, tenant_id: str, project_id: str) -> str:
    """Generate image for a single frame using Nano Banana"""
    
    image_prompt = frame.get("image_prompt", "")
    frame_num = frame.get("frame_number", 0)
    
    # Call Nano Banana (Gemini 2.5 Flash Image)
    try:
        emergent_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not emergent_key:
            raise Exception("EMERGENT_LLM_KEY not found")
        
        import litellm
        
        response = await litellm.aimage_generation(
            model="gemini/gemini-2.0-flash-exp",
            prompt=image_prompt,
            api_key=emergent_key,
            timeout=60
        )
        
        # Get image URL from response
        if hasattr(response, 'data') and len(response.data) > 0:
            image_url = response.data[0].url
            logger.info(f"Frame {frame_num}: Image generated")
            return image_url
        else:
            raise Exception("No image URL in response")
            
    except Exception as e:
        logger.error(f"Frame {frame_num} image generation failed: {e}")
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
    """Get generated Kling storyboards"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    storyboards = project.get("kling_storyboards", [])
    
    return {
        "has_storyboards": len(storyboards) > 0,
        "total_frames": len(storyboards),
        "frames": storyboards,
        "generated_at": project.get("kling_storyboards_generated_at")
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
            })
            logger.info(f"  Batch complete. Progress: {total_generated} generated, {total_failed} failed")
    
    logger.info(f"RegenerateImages [{project_id}]: Complete! {total_generated} generated, {total_failed} failed")
    
    return {
        "status": "success",
        "total_generated": total_generated,
        "total_failed": total_failed,
        "storyboards": storyboards
    }


async def _generate_frame_image_with_tool(frame: Dict, project_id: str) -> str:
    """
    Generate image for a frame using the system image generation tool
    This uses the proper tool interface instead of direct API calls
    """
    image_prompt = frame.get("image_prompt", "")
    frame_num = frame.get("frame_number", 0)
    
    if not image_prompt:
        raise Exception("No image_prompt available")
    
    # Simplify prompt for better results (keep under 500 chars)
    simplified_prompt = image_prompt[:500] if len(image_prompt) > 500 else image_prompt
    
    logger.info(f"      Generating image for frame {frame_num}...")
    
    # Use the system's image generation (will use Nano Banana via Emergent key)
    # This is more reliable than direct litellm calls
    try:
        # Import the image generation utility
        import subprocess
        import json
        import tempfile
        
        # Create a request payload
        payload = {
            "prompts": [
                {
                    "slug_name": f"frame_{frame_num}",
                    "prompt": simplified_prompt,
                    "size": "1024x1024",
                    "quality": "low",  # Use low for faster generation
                    "output_format": "png"
                }
            ]
        }
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(payload, f)
            temp_file = f.name
        
        # Call image generation via curl (more reliable)
        result = subprocess.run([
            'curl', '-s', '-X', 'POST',
            'https://api.emergent.ag/v1/image/generate',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {os.environ.get("EMERGENT_LLM_KEY", "")}',
            '-d', f'@{temp_file}'
        ], capture_output=True, text=True, timeout=120)
        
        # Clean up
        os.unlink(temp_file)
        
        if result.returncode != 0:
            raise Exception(f"Image generation failed: {result.stderr}")
        
        response_data = json.loads(result.stdout)
        
        # Extract URL from response
        if 'images' in response_data and len(response_data['images']) > 0:
            return response_data['images'][0]['url']
        else:
            raise Exception(f"No image URL in response: {response_data}")
            
    except Exception as e:
        logger.error(f"      Image generation error: {e}")
        raise
