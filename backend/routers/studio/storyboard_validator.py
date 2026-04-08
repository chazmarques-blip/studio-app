"""
Storyboard Validation & Auto-Regeneration System
Validates storyboard frames and automatically regenerates problematic ones
"""
from ._shared import *
from typing import List, Dict, Tuple
import asyncio

# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION THRESHOLDS
# ══════════════════════════════════════════════════════════════════════════════

VALIDATION_THRESHOLD = 0.90  # 90% of frames must be valid
MAX_REGENERATION_ATTEMPTS = 3  # Max attempts to regenerate a single frame

# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

async def validate_and_fix_storyboard(
    tenant_id: str,
    project_id: str,
    scene_number: int,
    frames: List[Dict],
    director_notes: Dict,
    character_bible: Dict
) -> Tuple[List[Dict], Dict]:
    """
    Validates storyboard frames and auto-regenerates problematic ones
    
    Args:
        tenant_id: Tenant ID
        project_id: Project ID
        scene_number: Scene number
        frames: List of 30 storyboard frames
        director_notes: Director's notes for the scene
        character_bible: Character reference data
    
    Returns:
        Tuple of (validated_frames, report)
    """
    logger.info(f"StoryboardValidator [{project_id}]: Scene {scene_number} - Validating {len(frames)} frames")
    
    iteration = 0
    max_iterations = 10  # Prevent infinite loop
    
    while iteration < max_iterations:
        iteration += 1
        logger.info(f"StoryboardValidator [{project_id}]: Iteration {iteration}")
        
        # Validate all frames
        validation_result = await _validate_frames(
            frames, 
            director_notes, 
            character_bible
        )
        
        valid_count = len(validation_result["valid_frames"])
        total_count = len(frames)
        score = valid_count / total_count
        
        logger.info(f"StoryboardValidator [{project_id}]: Score: {valid_count}/{total_count} ({score:.1%})")
        
        # Check if we met threshold
        if score >= VALIDATION_THRESHOLD:
            logger.info(f"StoryboardValidator [{project_id}]: ✅ PASSED validation ({score:.1%} ≥ {VALIDATION_THRESHOLD:.0%})")
            
            report = {
                "status": "passed",
                "score": score,
                "valid_frames": valid_count,
                "total_frames": total_count,
                "iterations": iteration
            }
            
            return frames, report
        
        # Identify problematic frames
        problematic_frames = validation_result["problematic_frames"]
        
        if not problematic_frames:
            # No specific frames identified as problematic, but score is low
            # This shouldn't happen, but handle gracefully
            logger.warning(f"StoryboardValidator [{project_id}]: Low score but no problematic frames identified")
            break
        
        logger.info(f"StoryboardValidator [{project_id}]: 🔄 Regenerating {len(problematic_frames)} problematic frames")
        
        # Regenerate problematic frames
        for frame_num in problematic_frames:
            frame_idx = frame_num - 1  # Convert to 0-indexed
            
            if frame_idx < 0 or frame_idx >= len(frames):
                continue
            
            logger.info(f"StoryboardValidator [{project_id}]: Regenerating frame {frame_num}")
            
            # Get context from neighboring frames
            prev_frame = frames[frame_idx - 1] if frame_idx > 0 else None
            next_frame = frames[frame_idx + 1] if frame_idx < len(frames) - 1 else None
            
            # Regenerate this frame
            new_frame = await _regenerate_frame(
                tenant_id=tenant_id,
                project_id=project_id,
                frame_number=frame_num,
                prev_frame=prev_frame,
                next_frame=next_frame,
                director_notes=director_notes,
                character_bible=character_bible,
                issue=validation_result["issues"].get(frame_num, "")
            )
            
            if new_frame:
                frames[frame_idx] = new_frame
                logger.info(f"StoryboardValidator [{project_id}]: ✅ Frame {frame_num} regenerated")
            else:
                logger.error(f"StoryboardValidator [{project_id}]: ❌ Failed to regenerate frame {frame_num}")
    
    # If we exit the loop without reaching threshold, return what we have
    logger.warning(f"StoryboardValidator [{project_id}]: Reached max iterations ({max_iterations}) with score {score:.1%}")
    
    report = {
        "status": "incomplete",
        "score": score,
        "valid_frames": valid_count,
        "total_frames": total_count,
        "iterations": iteration,
        "warning": f"Could not reach {VALIDATION_THRESHOLD:.0%} threshold after {iteration} iterations"
    }
    
    return frames, report


async def _validate_frames(
    frames: List[Dict],
    director_notes: Dict,
    character_bible: Dict
) -> Dict:
    """
    Validate storyboard frames using Vision AI
    
    Returns:
        {
            "valid_frames": [1, 2, 3, ...],
            "problematic_frames": [5, 12, 22],
            "issues": {
                5: "Character appearance inconsistent",
                12: "Camera angle doesn't match direction"
            }
        }
    """
    # TODO: Implement actual Vision AI validation
    # For now, simulate validation
    
    # Placeholder: Assume 85% of frames are valid initially
    import random
    random.seed(42)  # Deterministic for testing
    
    valid_frames = []
    problematic_frames = []
    issues = {}
    
    for i, frame in enumerate(frames):
        frame_num = i + 1
        
        # Simulate validation (replace with actual Vision AI)
        is_valid = random.random() > 0.15  # 85% pass rate
        
        if is_valid:
            valid_frames.append(frame_num)
        else:
            problematic_frames.append(frame_num)
            issues[frame_num] = "Simulated validation failure (replace with real Vision AI)"
    
    return {
        "valid_frames": valid_frames,
        "problematic_frames": problematic_frames,
        "issues": issues
    }


async def _regenerate_frame(
    tenant_id: str,
    project_id: str,
    frame_number: int,
    prev_frame: Dict,
    next_frame: Dict,
    director_notes: Dict,
    character_bible: Dict,
    issue: str
) -> Dict:
    """
    Regenerate a single problematic frame using neighboring frames as reference
    
    Args:
        frame_number: Frame number to regenerate
        prev_frame: Previous frame (for continuity)
        next_frame: Next frame (for continuity)
        director_notes: Director's notes
        character_bible: Character reference
        issue: Description of the problem
    
    Returns:
        Regenerated frame dict or None if failed
    """
    from .storyboard import _generate_storyboard_frame_async
    
    # Build context prompt emphasizing continuity
    context = f"Frame {frame_number} needs regeneration due to: {issue}\n\n"
    
    if prev_frame:
        context += f"PREVIOUS FRAME (Frame {frame_number - 1}):\n"
        context += f"Prompt: {prev_frame.get('prompt', '')}\n"
        context += f"Image: {prev_frame.get('image_url', '')}\n\n"
    
    if next_frame:
        context += f"NEXT FRAME (Frame {frame_number + 1}):\n"
        context += f"Prompt: {next_frame.get('prompt', '')}\n"
        context += f"Image: {next_frame.get('image_url', '')}\n\n"
    
    context += "Generate Frame {frame_number} that provides smooth visual transition "
    context += "maintaining character consistency and following director's vision."
    
    try:
        # Call storyboard generator with enhanced prompt
        new_frame = await _generate_storyboard_frame_async(
            tenant_id=tenant_id,
            project_id=project_id,
            frame_number=frame_number,
            scene_description=director_notes.get("sora_prompt", ""),
            timestamp=f"{(frame_number-1)*10}s-{frame_number*10}s",
            character_bible=character_bible,
            additional_context=context
        )
        
        return new_frame
        
    except Exception as e:
        logger.error(f"Frame regeneration failed: {e}")
        return None
