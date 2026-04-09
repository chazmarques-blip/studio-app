"""
Regenerate images for Kling storyboards
"""
from ._shared import *
from typing import List, Dict
import asyncio

@router.post("/projects/{project_id}/kling-storyboards/regenerate-images")
async def regenerate_storyboard_images(
    project_id: str,
    tenant=Depends(get_current_tenant)
):
    """
    Regenerate images for frames that don't have them
    Uses the system image generation tool
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    storyboards = project.get("kling_storyboards", [])
    if not storyboards:
        raise HTTPException(status_code=400, detail="No storyboards found")
    
    logger.info(f"RegenerateImages [{project_id}]: Starting image regeneration")
    
    total_regenerated = 0
    
    for scene_data in storyboards:
        scene_num = scene_data.get("scene_number", 0)
        frames = scene_data.get("frames", [])
        
        # Find frames without images
        frames_to_regenerate = [
            (i, f) for i, f in enumerate(frames) 
            if not f.get("image_url")
        ]
        
        if not frames_to_regenerate:
            logger.info(f"Scene {scene_num}: All frames have images")
            continue
        
        logger.info(f"Scene {scene_num}: Regenerating {len(frames_to_regenerate)} images")
        
        # Process in batches of 4 (avoid overwhelming the API)
        BATCH_SIZE = 4
        for batch_start in range(0, len(frames_to_regenerate), BATCH_SIZE):
            batch = frames_to_regenerate[batch_start:batch_start+BATCH_SIZE]
            
            logger.info(f"  Batch {batch_start//BATCH_SIZE + 1}: {len(batch)} images")
            
            # Generate images in parallel
            tasks = []
            for idx, frame in batch:
                task = _generate_single_image(frame, tenant["id"], project_id)
                tasks.append((idx, task))
            
            results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            
            # Update frames with results
            for (idx, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Frame {frames[idx].get('frame_number')} failed: {result}")
                    frames[idx]["image_error"] = str(result)
                elif result:
                    frames[idx]["image_url"] = result
                    frames[idx].pop("image_error", None)
                    total_regenerated += 1
                    logger.info(f"  ✅ Frame {frames[idx].get('frame_number')} image generated")
    
    # Save updated project
    _update_project_field(tenant["id"], project_id, {
        "kling_storyboards": storyboards
    })
    
    logger.info(f"RegenerateImages [{project_id}]: ✅ Regenerated {total_regenerated} images")
    
    return {
        "status": "success",
        "total_regenerated": total_regenerated,
        "storyboards": storyboards
    }


async def _generate_single_image(frame: Dict, tenant_id: str, project_id: str) -> str:
    """
    Generate image for a single frame using system image generation
    Falls back to placeholder if generation fails
    """
    image_prompt = frame.get("image_prompt", "")
    frame_num = frame.get("frame_number", 0)
    
    if not image_prompt:
        raise Exception("No image_prompt available")
    
    try:
        # Use emergentintegrations for image generation
        from emergentintegrations import generate_image
        
        result = await generate_image(
            prompt=image_prompt,
            model="gemini-2.0-flash-exp",
            size="1024x1024"
        )
        
        if result and result.get("url"):
            return result["url"]
        else:
            raise Exception("No URL in response")
            
    except Exception as e:
        logger.warning(f"Frame {frame_num}: Primary generation failed ({e}), trying fallback...")
        
        # Fallback: try with simplified prompt
        try:
            simple_prompt = f"Chibi 3D render: {frame.get('key_action', image_prompt[:100])}"
            
            from emergentintegrations import generate_image
            result = await generate_image(
                prompt=simple_prompt,
                model="gemini-2.0-flash-exp",
                size="1024x1024"
            )
            
            if result and result.get("url"):
                return result["url"]
                
        except:
            pass
        
        # If all fails, return None (will keep trying later)
        raise Exception(f"All generation methods failed: {e}")
