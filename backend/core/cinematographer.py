"""
Director of Photography (DoP) Agent
Plans camera shots, movements, and multi-format composition for video production.

The DoP is part of the initial creative committee and runs AFTER:
- Screenwriter (scenes + structure)
- Production Designer (visual style)
- Dialogue Writer (character dialogue)

And BEFORE:
- Storyboard generation (uses DoP's camera plan)
- Video production (uses DoP's camera movements)
"""
import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def generate_camera_plan(
    project_id: str,
    scenes: list,
    characters: list,
    production_design: dict,
    format_strategy: str = "safe_zone",  # "safe_zone" | "dual_generation" | "multi_format"
    formats_requested: list = None,  # ["16:9", "9:16", "4:5", "1:1"]
    lang: str = "pt"
) -> dict:
    """
    DoP Agent plans camera shots for entire project considering multi-format delivery.
    
    Args:
        project_id: Project ID for logging
        scenes: List of scene dicts with dialogue, description, emotion
        characters: List of character dicts
        production_design: Production design document with style, locations, etc
        format_strategy: Strategy for multi-format (safe_zone, dual, multi)
        formats_requested: List of aspect ratios needed
        lang: Language code
    
    Returns:
        Camera plan dict:
        {
            "format_strategy": "safe_zone",
            "formats_requested": ["16:9", "9:16"],
            "camera_shot_list": [
                {
                    "scene_number": 1,
                    "cinematography_notes": "...",
                    "shots": [...]
                }
            ],
            "safe_zone_rules": {...},
            "overall_cinematography_style": "..."
        }
    """
    if formats_requested is None:
        formats_requested = ["16:9"]  # Default to horizontal only
    
    # Build scene summary (first 10 for context)
    scene_summary = ""
    for i, s in enumerate(scenes[:10]):
        scene_num = s.get("scene_number", i+1)
        title = s.get("title", "")
        desc = s.get("description", "")[:120]
        emotion = s.get("emotion", "neutral")
        chars = ", ".join(s.get("characters_in_scene", []))
        
        scene_summary += f"\nScene {scene_num}: {title}\n"
        scene_summary += f"  Characters: {chars}\n"
        scene_summary += f"  Emotion: {emotion}\n"
        scene_summary += f"  Description: {desc}...\n"
    
    # Build character summary
    char_summary = ""
    for ch in characters[:10]:
        name = ch.get("name", "")
        role = ch.get("role", "")
        char_summary += f"- {name}: {role}\n"
    
    # Strategy instructions
    strategy_instructions = {
        "safe_zone": """FORMAT STRATEGY: SAFE ZONE (Single video with multi-format crop capability)
- Plan camera shots where ALL important elements fit in the CENTER 60% of frame (safe for 9:16 crop)
- Main characters MUST be centered vertically and horizontally
- Avoid placing characters or key actions on far left/right edges
- Use depth composition (characters front/back) instead of side-by-side
- Suggest camera movements that work in both horizontal and vertical crops
- Example: Instead of "two characters side-by-side", use "main character center, second character slightly behind"

CRITICAL: Your composition MUST work when cropped from 16:9 to 9:16 vertical.""",
        
        "dual_generation": """FORMAT STRATEGY: DUAL GENERATION (Separate videos for horizontal + vertical)
- Plan TWO different sets of camera movements:
  * HORIZONTAL (16:9): Wide pans, lateral tracking, landscape reveals
  * VERTICAL (9:16): Tilts, vertical dolly, portrait framing
- Horizontal version can use full width for dramatic reveals
- Vertical version focuses on character close-ups and vertical movement
- Each version is shot natively for its format

CRITICAL: Provide DIFFERENT camera plans for each format.""",
        
        "multi_format": f"""FORMAT STRATEGY: MULTI-FORMAT (Native versions for all requested formats)
Requested formats: {', '.join(formats_requested)}
- Plan optimized camera movements for EACH format
- 16:9: Horizontal pans, wide establishing shots
- 9:16: Vertical tilts, portrait close-ups
- 4:5: Balanced framing, medium shots
- 1:1: Centered composition, symmetrical framing

CRITICAL: Each format gets its own camera plan."""
    }
    
    # Get production design style
    style_dna = production_design.get("style_anchors", "Cinematic 3D animation") if production_design else "Cinematic"
    
    system_prompt = f"""You are an ELITE DIRECTOR OF PHOTOGRAPHY (DoP) with awards from ASC, BAFTA, and Oscars.

Your cinematography combines the mastery of:
- Roger Deakins (lighting, composition)
- Emmanuel Lubezki (movement, natural light)
- Janusz Kamiński (dramatic emotion)
- Hoyte van Hoytema (IMAX scale)

YOUR ROLE: Plan camera shots for this animated project considering multi-format delivery.

{strategy_instructions.get(format_strategy, strategy_instructions["safe_zone"])}

CAMERA MOVEMENT VOCABULARY:
- PAN: Camera rotates horizontally (left/right)
- TILT: Camera rotates vertically (up/down)
- DOLLY: Camera moves physically toward/away from subject
- TRACKING: Camera follows subject's movement
- ORBIT: Camera circles around subject
- CRANE: Camera moves vertically (up/down) on crane
- ZOOM: Lens zooms in/out (digital, not physical movement)
- STATIC: Camera does not move

SHOT SIZES:
- EXTREME WIDE: Shows entire environment, characters small
- WIDE: Shows full character + environment context
- MEDIUM: Shows character from waist up
- CLOSE-UP: Shows face/head only
- EXTREME CLOSE-UP: Shows detail (eyes, hands, object)

COMPOSITION RULES FOR ANIMATION:
1. SAFE ZONE (if strategy is safe_zone):
   - Main subjects in center 60% of frame
   - Never place characters on far edges
   - Use depth (front/back) not width (left/right)

2. STORYTELLING THROUGH MOVEMENT:
   - Dolly IN = create intimacy, increase tension
   - Dolly OUT = reveal context, show scale
   - Pan REVEAL = discover new information
   - Static shot = let acting/dialogue breathe

3. EMOTIONAL PACING:
   - Exciting scenes: Faster movements, dynamic angles
   - Sad scenes: Slower movements, static shots
   - Tense scenes: Slow push-ins, handheld feel

4. SHOT VARIETY (12-second scenes):
   - Vary shot sizes: Wide → Medium → Close-up
   - Mix static and movement
   - Match camera to emotion

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{{
  "format_strategy": "{format_strategy}",
  "formats_requested": {formats_requested},
  "overall_cinematography_style": "Brief description of overall visual approach",
  "safe_zone_rules": {{
    "character_positioning": "Guidelines for character placement",
    "action_area": "Safe area for important actions",
    "forbidden_compositions": ["List of compositions to avoid"]
  }},
  "camera_shot_list": [
    {{
      "scene_number": 1,
      "scene_title": "Scene title",
      "cinematography_notes": "Overall approach for this scene",
      "primary_format": "16:9",
      "shots": [
        {{
          "timing": "0-4s",
          "shot_type": "wide_shot",
          "camera_movement": "slow dolly in",
          "framing": "Character centered, beach environment visible",
          "composition_notes": "Safe zone: character in center 60%",
          "lighting_mood": "Golden hour backlight, warm",
          "rationale": "Establishes location and character"
        }}
      ]
    }}
  ]
}}"""

    user_prompt = f"""PROJECT: {project_id}
TOTAL SCENES: {len(scenes)}
FORMAT STRATEGY: {format_strategy}
FORMATS NEEDED: {', '.join(formats_requested)}

VISUAL STYLE:
{style_dna}

CHARACTERS:
{char_summary}

FIRST 10 SCENES (representative sample):
{scene_summary}

Plan camera shots for ALL {len(scenes)} scenes. For each scene:
1. Define overall cinematography approach
2. Break 12-second scene into 2-4 camera shots (each 3-6 seconds)
3. Specify camera movement, framing, composition
4. Consider format strategy (safe zones or format-specific)
5. Match camera movement to scene emotion

Return ONLY valid JSON with complete camera_shot_list for all {len(scenes)} scenes."""

    try:
        import litellm
        
        response = litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_key=ANTHROPIC_API_KEY,
            max_tokens=16000,  # Large project needs high token count
            timeout=240  # 4 minutes for large projects
        )
        
        result = response.choices[0].message.content
        
        # Parse JSON
        try:
            camera_plan = json.loads(result)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown
            import re
            match = re.search(r'\{[\s\S]*\}', result)
            if match:
                camera_plan = json.loads(match.group())
            else:
                logger.error(f"DoP [{project_id}]: Failed to parse JSON response")
                return _fallback_camera_plan(scenes, format_strategy, formats_requested)
        
        if not isinstance(camera_plan, dict):
            logger.error(f"DoP [{project_id}]: Response is not a dict")
            return _fallback_camera_plan(scenes, format_strategy, formats_requested)
        
        # Validate structure
        if "camera_shot_list" not in camera_plan:
            logger.warning(f"DoP [{project_id}]: Missing camera_shot_list, using fallback")
            return _fallback_camera_plan(scenes, format_strategy, formats_requested)
        
        shot_list = camera_plan.get("camera_shot_list", [])
        logger.info(f"DoP [{project_id}]: Camera plan generated for {len(shot_list)} scenes")
        
        return camera_plan
        
    except Exception as e:
        logger.error(f"DoP [{project_id}]: Camera planning failed: {e}")
        return _fallback_camera_plan(scenes, format_strategy, formats_requested)


def _fallback_camera_plan(scenes: list, format_strategy: str, formats_requested: list) -> dict:
    """
    Simple fallback camera plan when Claude fails.
    """
    camera_shot_list = []
    
    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i+1)
        title = scene.get("title", "")
        
        # Simple 3-shot structure for 12s scene
        camera_shot_list.append({
            "scene_number": scene_num,
            "scene_title": title,
            "cinematography_notes": "Standard 3-shot structure: establish, develop, conclude",
            "primary_format": "16:9",
            "shots": [
                {
                    "timing": "0-4s",
                    "shot_type": "wide_shot",
                    "camera_movement": "static",
                    "framing": "Establishing shot showing environment and characters",
                    "composition_notes": "Characters centered for safe zone",
                    "lighting_mood": "Natural, matching time of day",
                    "rationale": "Establishes scene context"
                },
                {
                    "timing": "4-8s",
                    "shot_type": "medium_shot",
                    "camera_movement": "slow dolly in",
                    "framing": "Characters from waist up, showing dialogue",
                    "composition_notes": "Main character centered",
                    "lighting_mood": "Focused on characters",
                    "rationale": "Shows character action/dialogue"
                },
                {
                    "timing": "8-12s",
                    "shot_type": "close_up",
                    "camera_movement": "static",
                    "framing": "Character's face showing emotion",
                    "composition_notes": "Face centered, emotional focus",
                    "lighting_mood": "Dramatic, emphasizing expression",
                    "rationale": "Captures emotional beat"
                }
            ]
        })
    
    return {
        "format_strategy": format_strategy,
        "formats_requested": formats_requested,
        "overall_cinematography_style": "Standard cinematic coverage with safe zone composition",
        "safe_zone_rules": {
            "character_positioning": "Always center-frame",
            "action_area": "Center 60% of frame",
            "forbidden_compositions": ["Characters on far edges", "Side-by-side layout"]
        },
        "camera_shot_list": camera_shot_list,
        "note": "Fallback camera plan (Claude failed)"
    }
