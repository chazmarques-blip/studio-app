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
    Generate 30 ultra-detailed storyboards for Kling 5-minute video
    Each storyboard includes:
    - Reference image (generated via Nano Banana)
    - Kling-optimized prompt for 10-second video generation
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes available")
    
    # Find the 5-minute scene (or use specified scene)
    target_scene = None
    if req.scene_id:
        target_scene = next((s for s in scenes if s.get("id") == req.scene_id), None)
    else:
        # Find first scene with ~300s duration
        for scene in scenes:
            start = scene.get("time_start", "0:00")
            end = scene.get("time_end", "0:00")
            duration = _parse_time_to_seconds(end) - _parse_time_to_seconds(start)
            if 250 <= duration <= 350:  # Allow some flexibility
                target_scene = scene
                break
    
    if not target_scene:
        raise HTTPException(status_code=400, detail="No 5-minute scene found. Create a scene with ~300 seconds duration.")
    
    # Get project metadata
    characters = project.get("characters", [])
    dialogues = project.get("dialogues", {}).get("scenes", [])
    target_audience = project.get("target_audience", "all")
    lang = project.get("language", "pt")
    
    # Find dialogue for this scene
    scene_dialogue = next(
        (d for d in dialogues if d.get("scene_number") == target_scene.get("scene_number")),
        None
    )
    
    logger.info(f"KlingStoryboard [{project_id}]: Generating 30 frames for scene '{target_scene.get('title', 'Untitled')}'")
    
    # Step 1: Generate frame structure with prompts
    try:
        frames_data = await _generate_frame_prompts(
            target_scene,
            scene_dialogue,
            characters,
            target_audience,
            lang
        )
    except Exception as e:
        logger.error(f"KlingStoryboard ERROR generating prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate frame prompts: {str(e)}")
    
    # Step 2: Generate images in parallel (batches of 10)
    logger.info(f"KlingStoryboard [{project_id}]: Generating 30 images in 3 batches...")
    
    try:
        frames_with_images = await _generate_images_parallel(frames_data, tenant["id"], project_id)
    except Exception as e:
        logger.error(f"KlingStoryboard ERROR generating images: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate images: {str(e)}")
    
    # Step 3: Save to project
    _update_project_field(tenant["id"], project_id, {
        "kling_storyboards": frames_with_images,
        "kling_storyboards_generated_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"KlingStoryboard [{project_id}]: ✅ Generated 30 frames with images")
    
    return {
        "status": "success",
        "total_frames": len(frames_with_images),
        "scene_title": target_scene.get("title"),
        "frames": frames_with_images
    }


async def _generate_frame_prompts(
    scene: Dict,
    dialogue: Optional[Dict],
    characters: List[Dict],
    target_audience: str,
    lang: str
) -> List[Dict]:
    """Generate 30 frame structures with detailed prompts"""
    
    # Build character context
    char_names = [c.get("name", "") for c in characters if c.get("name")]
    char_descriptions = "\n".join([
        f"- {c.get('name', 'Unknown')}: {c.get('description', 'No description')}"
        for c in characters
    ])
    
    # Get dialogue text if available
    dialogue_text = ""
    if dialogue:
        dialogue_text = dialogue.get("dialogue", "")
    
    # Get audience cinematography guidelines
    audience_guide = AUDIENCE_CINEMATOGRAPHY.get(lang, {}).get(target_audience, "")
    
    # Build system prompt
    system_prompt = KLING_STORYBOARD_SYSTEM.format(
        language="Portuguese" if lang == "pt" else "English",
        target_audience=target_audience,
        audience_guidelines=audience_guide
    )
    
    # Build user prompt
    user_prompt = f"""
SCENE INFORMATION:
- Title: {scene.get('title', 'Untitled')}
- Description: {scene.get('description', '')}
- Emotion: {scene.get('emotion', 'neutral')}
- Camera: {scene.get('camera', 'varied')}
- Duration: 300 seconds (5 minutes)
- Target audience: {target_audience}

CHARACTERS (use ONLY these names):
{char_descriptions}

DIALOGUE TEXT (integrate at appropriate moments):
{dialogue_text if dialogue_text else "No dialogue for this scene"}

YOUR TASK:
Generate 30 frames covering 0:00 to 5:00 (300 seconds).
Each frame covers exactly 10 seconds.

Frame 1: 0:00-0:10
Frame 2: 0:10-0:20
...
Frame 30: 4:50-5:00

For each frame, provide:
1. image_prompt - Visual description for reference image
2. kling_prompt - Detailed 10-second action description for Kling
3. All metadata fields

Ensure VISUAL CONTINUITY between frames.
Character positions at end of Frame N should match start of Frame N+1.

Return as valid JSON array with 30 frame objects.
"""
    
    # Call Claude to generate structure
    logger.info("Calling Claude to generate 30 frame structures...")
    result = await _call_claude_for_frames(system_prompt, user_prompt)
    
    data = _parse_json(result)
    if not data or not isinstance(data, list):
        # Try to extract array from response
        if isinstance(data, dict) and "frames" in data:
            data = data["frames"]
        else:
            raise Exception("Invalid response format - expected array of 30 frames")
    
    if len(data) != 30:
        logger.warning(f"Expected 30 frames, got {len(data)}. Padding/trimming...")
        # Pad or trim to exactly 30
        while len(data) < 30:
            data.append({
                "frame_number": len(data) + 1,
                "time_start": f"0:{(len(data) * 10) // 60:02d}:{(len(data) * 10) % 60:02d}",
                "time_end": f"0:{((len(data) + 1) * 10) // 60:02d}:{((len(data) + 1) * 10) % 60:02d}",
                "image_prompt": scene.get("description", ""),
                "kling_prompt": scene.get("description", ""),
                "characters_present": char_names,
                "camera_movement": "static",
                "key_action": "scene continues",
                "emotion": scene.get("emotion", "neutral"),
                "lighting": "natural"
            })
        data = data[:30]
    
    logger.info(f"✅ Generated structure for {len(data)} frames")
    return data


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
