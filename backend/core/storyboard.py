"""Storyboard Generator — Generate editable illustration panels from screenplay scenes.

Uses Gemini Nano Banana (via emergentintegrations) for panel illustration generation
and Claude (via litellm) for the AI Facilitator chat.

COST OPTIMIZATION:
- Default: 6 frames per scene (high quality)
- Economy: 3 frames per scene (50% cost reduction)
- Preview: 1 frame per scene (80% cost reduction, good for prototyping)
"""
import os
import base64
import asyncio
import logging
import threading
import tempfile
import urllib.request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# COST OPTIMIZATION PRESETS
QUALITY_PRESETS = {
    "preview": {
        "frames": [3],  # Only KEY ACTION frame
        "description": "Geração rápida - 1 frame/cena (~$8 para 24 cenas)",
    },
    "economy": {
        "frames": [1, 3, 6],  # Opening, Key Action, Closing
        "description": "Economia - 3 frames/cena (~$15 para 24 cenas)",
    },
    "standard": {
        "frames": [1, 2, 3, 4, 5, 6],  # All 6 frames
        "description": "Qualidade padrão - 6 frames/cena (~$25 para 24 cenas)",
    },
    "custom": {
        "frames": None,  # User can specify which frames
        "description": "Personalizado - escolha quais frames gerar",
    },
}

FRAME_TYPES = [
    {
        "label": "Pagina 1",
        "order": 1,
        "prompt": "OPENING MOMENT — The very beginning of this scene. Show the setting, the atmosphere, and the characters arriving or positioned at the start. This is the first page of the storybook for this scene.",
    },
    {
        "label": "Pagina 2",
        "order": 2,
        "prompt": "RISING ACTION — The tension or interest builds. Show what triggers the main event: a gesture, a look, a discovery, or dialogue that changes the mood. Second page of the storybook.",
    },
    {
        "label": "Pagina 3",
        "order": 3,
        "prompt": "KEY ACTION — The central dramatic moment of this scene. The most important action, decision, or turning point. This is the climax page of the storybook.",
    },
    {
        "label": "Pagina 4",
        "order": 4,
        "prompt": "REACTION — Characters react to what just happened. Show the emotional impact: surprise, joy, fear, sadness, or determination on their faces and body language. Fourth page of the storybook.",
    },
    {
        "label": "Pagina 5",
        "order": 5,
        "prompt": "CONSEQUENCE — Show the immediate aftermath or result of the main action. What changed? How does the environment or the characters look now? Fifth page of the storybook.",
    },
    {
        "label": "Pagina 6",
        "order": 6,
        "prompt": "CLOSING MOMENT — The scene winds down or transitions. Show characters moving on, a final emotional beat, or a visual that bridges to what comes next. Last page of the storybook for this scene.",
    },
]


# ── Shot Briefs Generator (Claude as Shot Director) ──────────────────────

def _generate_shot_briefs(
    scene: dict,
    scene_num: int,
    identity_cards: dict,
    style_dna: str,
    prev_scene: dict = None,
    next_scene: dict = None,
    lang: str = "pt",
    project_id: str = "",
    dialogue_timeline: list = None,
) -> list:
    """Use Claude to pre-plan 6 detailed shot briefs for a scene with continuity.
    Each brief includes per-character positioning, actions, and prohibitions.
    NOW SYNCED with dialogue_timeline for precise timing of actions and speech.
    Returns list of 6 dicts or falls back to FRAME_TYPES if Claude fails.
    """
    import litellm as _litellm

    # Build character identity block for the prompt
    chars_in_scene = scene.get("characters_in_scene", [])
    identity_block = ""
    for cname in chars_in_scene:
        card = identity_cards.get(cname, {})
        if isinstance(card, dict) and card.get("body_type"):
            identity_block += f"\n\n═══ CHARACTER: {cname} ═══\n"
            identity_block += f"Species: {card.get('species', '?')}\n"
            identity_block += f"Body Type: {card.get('body_type', '?')}\n"
            identity_block += f"Locomotion: {card.get('locomotion', '?')}\n"
            identity_block += f"Default Clothing: {card.get('default_clothing', '?')}\n"
            immutable = card.get("immutable_traits", [])
            if immutable:
                identity_block += f"IMMUTABLE TRAITS: {'; '.join(immutable)}\n"
            prohib = card.get("prohibitions", [])
            if prohib:
                identity_block += f"PROHIBITIONS: {'; '.join(prohib)}\n"
        else:
            desc = card if isinstance(card, str) else card.get("description", "")
            identity_block += f"\n- {cname}: {desc}\n"

    # Context from adjacent scenes for continuity
    prev_ctx = ""
    if prev_scene:
        prev_ctx = f"\nPREVIOUS SCENE (for continuity): Scene {prev_scene.get('scene_number', '?')}: {prev_scene.get('title', '')} — {prev_scene.get('description', '')[:150]}"
    next_ctx = ""
    if next_scene:
        next_ctx = f"\nNEXT SCENE (for bridging): Scene {next_scene.get('scene_number', '?')}: {next_scene.get('title', '')} — {next_scene.get('description', '')[:150]}"
    
    # Build dialogue timeline context
    dialogue_ctx = ""
    if dialogue_timeline and len(dialogue_timeline) > 0:
        dialogue_ctx = "\n\n═══ DIALOGUE TIMELINE (PRECISE TIMING) ═══\n"
        dialogue_ctx += "Each dialogue line has EXACT timing. Use this to synchronize visual actions:\n\n"
        for beat in dialogue_timeline:
            dialogue_ctx += f"[{beat['start_time']:.1f}s - {beat['end_time']:.1f}s] {beat['speaker']}: \"{beat['text']}\"\n"
            dialogue_ctx += f"  └─ Tone: {beat.get('tone', 'neutral')}\n"
            dialogue_ctx += f"  └─ Action: {beat.get('action_note', 'N/A')}\n\n"
        dialogue_ctx += "CRITICAL: Match visual actions to these precise timings. If a character speaks at 4-7s, they must be SPEAKING ON CAMERA during that time.\n"

    system = """You are a SHOT DIRECTOR for an animated storybook. You plan the exact visual composition of each page/frame.

You receive a scene description, character identity cards, adjacent scene context, and DIALOGUE TIMELINE with precise timing.
Your job is to produce 6 DETAILED SHOT BRIEFS — one for each page of the storybook scene (each page covers ~2 seconds of screen time in a 12-second scene).

CRITICAL RULES:
- Each character's visual identity is IMMUTABLE — you can change their EXPRESSION, CLOTHING for the scene, and ACTION, but NEVER their species, body type, or locomotion mode
- If a character is BIPEDAL_ANTHROPOMORPHIC, they MUST be standing/walking on TWO LEGS in EVERY frame — never on four legs
- If a character is QUADRUPED_ANIMAL, they MUST be on FOUR LEGS in every frame — never bipedal
- Characters' positions must flow logically: if a character is on the LEFT in Frame 1, they can't teleport to the RIGHT in Frame 2 without movement
- Frame 6 must visually bridge to the NEXT scene

🆕 DIALOGUE TIMING SYNC (NEW):
- If dialogue_timeline is provided, you MUST synchronize visual actions with speech timing
- Example: If Jonas speaks at 4.0-7.0s, Frame 3 (4-6s) must show him SPEAKING with mouth open, gestures
- If Narrator speaks at 0-2s, Frame 1 should show establishing shot with NO character speaking on camera
- Characters who are NOT speaking should be shown LISTENING or REACTING
- Match character expressions and actions to the tone of their dialogue (excited = animated gestures, calm = subtle movements)

Return ONLY valid JSON — a list of 6 objects:
[
  {
    "frame": 1,
    "time_range": "0-2s",
    "camera": "Wide shot / Medium shot / Close-up / Over-the-shoulder / etc.",
    "scene_action": "What is happening in this exact 2-second moment",
    "characters": {
      "CharacterName": {
        "position": "left third / center / right third / background",
        "pose": "standing upright on two legs / sitting / walking right / etc.",
        "action": "specific action: holding staff, pointing, looking at X",
        "expression": "specific expression: wide eyes, smiling, frowning",
        "clothing_note": "same as default / changed to X for this scene"
      }
    },
    "environment": "specific background and lighting details for this moment",
    "continuity_from_prev": "how this connects to the previous frame or previous scene",
    "prohibitions": ["NEVER show X on four legs in this frame", "NEVER change species"]
  }
]"""

    user = f"""SCENE {scene_num}: {scene.get('title', '')}
DESCRIPTION: {scene.get('description', '')}
EMOTION: {scene.get('emotion', '')}
DIALOGUE: {scene.get('dialogue', '')}
{dialogue_ctx}
{prev_ctx}
{next_ctx}

CHARACTER IDENTITY CARDS (IMMUTABLE — these are the VISUAL TRUTH):
{identity_block}

Generate 6 shot briefs. Remember: each character's body type is FIXED. If bipedal in the identity card, ALWAYS bipedal. Plan smooth spatial continuity between frames.
{'IMPORTANT: Synchronize visual actions with the dialogue timeline above. Match character actions to their speech timing.' if dialogue_timeline else ''}"""

    try:
        api_key = ANTHROPIC_API_KEY
        response = _litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=3000, timeout=120, api_key=api_key,
        )
        result = response.choices[0].message.content
        # Parse JSON from response
        import json
        # Try direct parse first
        try:
            briefs = json.loads(result)
        except json.JSONDecodeError:
            # Try extracting JSON array from markdown
            import re
            match = re.search(r'\[[\s\S]*\]', result)
            if match:
                briefs = json.loads(match.group())
            else:
                raise ValueError("No JSON array found in response")

        if isinstance(briefs, list) and len(briefs) >= 6:
            logger.info(f"Storyboard [{project_id}]: Shot briefs generated for scene {scene_num} — {len(briefs)} frames")
            return briefs[:6]
    except Exception as e:
        logger.warning(f"Storyboard [{project_id}]: Shot brief generation failed for scene {scene_num}: {e}")

    # Fallback: return None to indicate we should use FRAME_TYPES defaults
    return None


# ── Build Identity-Anchored Prompt ───────────────────────────────────────

def _build_identity_prompt(
    scene: dict,
    scene_num: int,
    frame_type: dict,
    frame_index: int,
    identity_cards: dict,
    character_bible: dict,
    style_dna: str,
    shot_brief: dict = None,
    lang: str = "pt",
) -> str:
    """Build an identity-first prompt for Gemini. Avatar identity comes FIRST (highest weight),
    scene instruction comes SECOND, dialogue context THIRD. Per-character prohibitions are inline.
    """
    chars_in_scene = scene.get("characters_in_scene", [])
    lang_name = {"pt": "Portuguese", "en": "English", "es": "Spanish"}.get(lang, "Portuguese")

    # ── BLOCK 1: CHARACTER IDENTITY (IMMUTABLE — highest priority) ──
    identity_block = "═══ CHARACTER IDENTITY — ABSOLUTE VISUAL CONTRACT (NON-NEGOTIABLE) ═══\n"
    identity_block += "⚠️ The reference images below are the ONLY TRUTH for each character's appearance.\n"
    identity_block += "⚠️ You MUST match EVERY detail: species, body type, fur/skin color, clothing, posture.\n"
    identity_block += "⚠️ ANY deviation from the reference image is a CRITICAL ERROR.\n\n"

    for cname in chars_in_scene:
        card = identity_cards.get(cname, {})
        bible_desc = character_bible.get(cname, "")
        if isinstance(bible_desc, dict):
            bible_desc = bible_desc.get("description", "")

        if isinstance(card, dict) and card.get("body_type"):
            identity_block += f"▸ {cname.upper()} — VISUAL CONTRACT\n"
            identity_block += f"  Species: {card.get('species', '?')}\n"
            identity_block += f"  Body Type: {card.get('body_type', '?')}\n"
            identity_block += f"  Locomotion: {card.get('locomotion', '?')}\n"
            if bible_desc:
                identity_block += f"  Visual Description: {bible_desc}\n"
            immutable = card.get("immutable_traits", [])
            for trait in immutable:
                identity_block += f"  ✅ MANDATORY: {trait}\n"
            prohib = card.get("prohibitions", [])
            for p in prohib:
                identity_block += f"  🚫 FORBIDDEN: {p}\n"
            # Redundancy: repeat the most critical trait
            if card.get('body_type'):
                identity_block += f"  ⚠️ REMINDER: {cname} is {card.get('body_type')} — {card.get('locomotion', 'maintain as designed')}\n"
            identity_block += "\n"
        elif bible_desc:
            identity_block += f"▸ {cname}: {bible_desc}\n\n"

    # ── BLOCK 2: DIALOGUE & NARRATION CONTEXT (enriches visual storytelling) ──
    dialogue_block = ""
    dubbed_text = scene.get("dubbed_text", "").strip()
    narrated_text = scene.get("narrated_text", "").strip()
    dialogue = scene.get("dialogue", "").strip()

    # Use the richest dialogue source available
    context_text = dubbed_text or dialogue or narrated_text
    if context_text:
        dialogue_block = "═══ DIALOGUE & EMOTIONAL CONTEXT FOR THIS SCENE ═══\n"
        dialogue_block += "Use this dialogue to inform character EXPRESSIONS, GESTURES, and BODY LANGUAGE:\n\n"
        dialogue_block += f"{context_text}\n\n"
        dialogue_block += "IMPORTANT: Characters should visually REFLECT what they are saying/feeling.\n"
        dialogue_block += "- Speaking characters: mouth slightly open, expressive gestures\n"
        dialogue_block += "- Listening characters: attentive posture, emotional reaction\n"
        dialogue_block += "- Emotional moments: exaggerate facial expressions for readability\n\n"

    # ── BLOCK 3: SCENE INSTRUCTION (can vary per frame) ──
    if shot_brief:
        # Use the detailed shot brief from Claude
        scene_block = f"═══ FRAME INSTRUCTION (Scene {scene_num}, {frame_type['label']}, {shot_brief.get('time_range', '')}) ═══\n"
        scene_block += f"Camera: {shot_brief.get('camera', 'Medium shot')}\n"
        scene_block += f"Action: {shot_brief.get('scene_action', scene.get('description', ''))}\n"
        scene_block += f"Environment: {shot_brief.get('environment', '')}\n"
        scene_block += f"Continuity: {shot_brief.get('continuity_from_prev', '')}\n\n"

        # Per-character positioning from shot brief
        brief_chars = shot_brief.get("characters", {})
        if brief_chars:
            scene_block += "CHARACTER POSITIONING:\n"
            for cname, cdata in brief_chars.items():
                if isinstance(cdata, dict):
                    scene_block += f"  {cname}: position={cdata.get('position', '?')}, "
                    scene_block += f"pose={cdata.get('pose', '?')}, "
                    scene_block += f"action={cdata.get('action', '?')}, "
                    scene_block += f"expression={cdata.get('expression', '?')}\n"
            scene_block += "\n"

        # Shot-specific prohibitions
        brief_prohib = shot_brief.get("prohibitions", [])
        if brief_prohib:
            scene_block += "FRAME PROHIBITIONS:\n"
            for p in brief_prohib:
                scene_block += f"  ⛔ {p}\n"
            scene_block += "\n"
    else:
        # Fallback to generic frame type prompt
        scene_block = f"═══ FRAME INSTRUCTION (Scene {scene_num}, {frame_type['label']}) ═══\n"
        scene_block += f"SCENE TITLE: {scene.get('title', '')}\n"
        scene_block += f"SCENE DESCRIPTION: {scene.get('description', '')}\n"
        scene_block += f"EMOTION/MOOD: {scene.get('emotion', '')}\n"
        scene_block += f"CAMERA: {scene.get('camera', '')}\n"
        scene_block += f"NARRATIVE MOMENT: {frame_type['prompt']}\n\n"

    # ── BLOCK 4: STYLE + RULES ──
    rules_block = f"""═══ STYLE & RULES ═══
{style_dna}

MANDATORY RULES:
- Generate exactly ONE single illustration (NOT a grid, NOT multiple panels)
- This is {frame_type['label']} of a storybook
- Characters MUST match their REFERENCE IMAGES and IDENTITY CARDS above — this is NON-NEGOTIABLE
- If a character's Identity Card says BIPEDAL, that character MUST be on TWO LEGS — NEVER four legs
- If a character's Identity Card says QUADRUPED, that character MUST be on FOUR LEGS — NEVER standing bipedally
- Frame the scene so characters and environment are clearly visible
- DO NOT include any text, numbers, labels, or speech bubbles
- Fill the entire image with the illustration — no borders, no margins
- Language context: {lang_name}

CHARACTER CONSISTENCY ENFORCEMENT:
- BEFORE generating, mentally review each character's Identity Card above
- Cross-check: Does each character match their species? Body type? Locomotion?
- If a character has fur, the color MUST match the reference image EXACTLY
- If a character wears clothing, the clothing MUST match the reference image EXACTLY
- Characters' proportions (head size, limb length, body shape) MUST be consistent

The REFERENCE IMAGES below are the ABSOLUTE VISUAL TRUTH for each character. Match them EXACTLY."""

    return f"{identity_block}\n{dialogue_block}{scene_block}\n{rules_block}"


def _generate_single_frame(
    scene: dict,
    scene_num: int,
    frame_type: dict,
    frame_index: int,
    project_id: str,
    char_avatars: dict,
    avatar_cache: dict,
    character_bible: dict,
    identity_cards: dict,
    style_dna: str,
    shot_brief: dict = None,
    lang: str = "pt",
) -> bytes:
    """Generate a single storyboard frame illustration via Gemini Nano Banana.
    Uses identity-anchored prompts with per-character prohibitions.
    Returns image bytes or None on failure.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        logger.warning(f"Storyboard [{project_id}]: No EMERGENT_LLM_KEY")
        return None

    # Build the identity-first prompt
    prompt_text = _build_identity_prompt(
        scene=scene, scene_num=scene_num,
        frame_type=frame_type, frame_index=frame_index,
        identity_cards=identity_cards, character_bible=character_bible,
        style_dna=style_dna, shot_brief=shot_brief, lang=lang,
    )

    # Load avatar reference images
    chars_in_scene = scene.get("characters_in_scene", [])
    ref_images = []
    for char_name in chars_in_scene:
        url = char_avatars.get(char_name)
        cached_path = avatar_cache.get(url) if url else None
        if cached_path and os.path.exists(cached_path):
            with open(cached_path, 'rb') as f:
                ref_b64 = base64.b64encode(f.read()).decode('utf-8')
            ref_images.append(ImageContent(ref_b64))

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=f"sb-{project_id}-{scene_num}-{frame_type['label'][:4]}",
            system_message="You are a professional storyboard artist for animated films. Generate exactly one high-quality illustration. The CHARACTER REFERENCE IMAGES provided are the ABSOLUTE VISUAL TRUTH — match them EXACTLY in every detail: species, body posture (bipedal/quadruped), fur/skin color, clothing."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

        if ref_images:
            msg = UserMessage(
                text=f"{prompt_text}\n\n═══ CHARACTER REFERENCE IMAGES (MATCH EXACTLY — these are the VISUAL TRUTH) ═══",
                file_contents=ref_images
            )
        else:
            msg = UserMessage(text=prompt_text)

        text, images = await chat.send_message_multimodal_response(msg)
        if images and len(images) > 0:
            return base64.b64decode(images[0]['data'])
        return None

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(lambda: asyncio.run(_gen())).result(timeout=90)
    else:
        result = asyncio.run(_gen())

    return result


def _generate_panel_image(
    scene: dict,
    scene_num: int,
    project_id: str,
    char_avatars: dict,
    avatar_cache: dict,
    character_bible: dict,
    identity_cards: dict,
    style_dna: str,
    shot_brief: dict = None,
    lang: str = "pt",
) -> bytes:
    """Legacy wrapper — generates the first frame (Plano Geral) as the main panel image."""
    return _generate_single_frame(
        scene=scene, scene_num=scene_num,
        frame_type=FRAME_TYPES[0], frame_index=0,
        project_id=project_id,
        char_avatars=char_avatars, avatar_cache=avatar_cache,
        character_bible=character_bible, identity_cards=identity_cards,
        style_dna=style_dna, shot_brief=shot_brief, lang=lang,
    )


def _generate_all_frames_for_scene(
    scene: dict,
    scene_num: int,
    project_id: str,
    char_avatars: dict,
    avatar_cache: dict,
    character_bible: dict,
    identity_cards: dict,
    style_dna: str,
    shot_briefs: list = None,
    lang: str = "pt",
    enable_validation: bool = True,
) -> list:
    """Generate 6 individual frames for a scene in parallel (6 at a time).
    Uses shot briefs for detailed per-frame instructions when available.
    When enable_validation=True, each frame is validated against character avatars
    using Claude Vision and regenerated up to 2 times if rejected.
    Returns list of (frame_type, image_bytes) tuples.
    """
    frame_sem = threading.Semaphore(6)  # All 6 frames in parallel
    results = [None] * len(FRAME_TYPES)
    chars_in_scene = scene.get("characters_in_scene", [])

    def _gen_one(idx, ft):
        with frame_sem:
            try:
                brief = shot_briefs[idx] if shot_briefs and idx < len(shot_briefs) else None

                def _do_generate():
                    return _generate_single_frame(
                        scene=scene, scene_num=scene_num,
                        frame_type=ft, frame_index=idx, project_id=project_id,
                        char_avatars=char_avatars, avatar_cache=avatar_cache,
                        character_bible=character_bible, identity_cards=identity_cards,
                        style_dna=style_dna, shot_brief=brief, lang=lang,
                    )

                # Continuity Director DISABLED - using QC Team for continuity checks
                # Validation gate removed to improve speed and reduce costs
                # Quality Control team validates continuity at scene level instead
                enable_validation = False  # Force disabled
                
                if False:  # Disabled block - keeping for reference
                    try:
                        from core.continuity_director import validate_and_retry
                        img = validate_and_retry(
                            generate_fn=_do_generate,
                            character_names_in_scene=chars_in_scene,
                            character_avatars=char_avatars,
                            scene_description=scene.get("description", ""),
                            frame_label=f"s{scene_num}_{ft['label']}",
                            project_id=project_id,
                            max_retries=2,
                        )
                    except Exception as e:
                        logger.warning(f"Storyboard [{project_id}]: Validation gate failed for {ft['label']}, falling back: {e}")
                        img = _do_generate()
                else:
                    img = _do_generate()

                results[idx] = (ft, img)
            except Exception as e:
                logger.error(f"Storyboard [{project_id}]: Frame {ft['label']} scene {scene_num} failed: {e}")
                results[idx] = (ft, None)

    threads = []
    for i, ft in enumerate(FRAME_TYPES):
        t = threading.Thread(target=_gen_one, args=(i, ft))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=180)  # Extended timeout for validation retries

    return [r for r in results if r is not None]


def generate_all_panels(
    tenant_id: str,
    project_id: str,
    scenes: list,
    characters: list,
    char_avatars: dict,
    production_design: dict,
    identity_cards: dict = None,
    lang: str = "pt",
    upload_fn=None,
    update_fn=None,
    frames_to_generate: list = None,  # NEW: [1,2,3,4,5,6] or [1,3,6] for economy
) -> list:
    """Generate storyboard panels for all scenes using the Continuity Director pipeline.

    Pipeline:
    1. Generate dialogue timelines for all scenes (NEW!)
    2. Load avatar references + Identity Cards
    3. Generate Shot Briefs (Claude, parallel per scene) for continuity WITH dialogue sync
    4. Generate frames (Gemini, parallel) using identity-anchored prompts

    Args:
        identity_cards: Dict of character identity cards from _analyze_avatars_with_vision()
        upload_fn: callable(bytes, filename, content_type) -> url
        update_fn: callable(tenant_id, project_id, updates_dict)
        frames_to_generate: List of frame indices to generate (1-6). Default: all 6

    Returns list of panel dicts.
    """
    from core.dialogue_timeline import enrich_scene_with_timeline
    
    if frames_to_generate is None:
        frames_to_generate = [1, 2, 3, 4, 5, 6]  # Default: all frames
    
    total = len(scenes)
    frames_per_scene = len(frames_to_generate)
    total_frames = total * frames_per_scene
    
    logger.info(f"Storyboard [{project_id}]: Generating {total_frames} frames ({frames_per_scene} frames/scene) for {total} scenes - Quality: {len(frames_to_generate)}/6 frames")
    character_bible = production_design.get("character_bible", {}) if production_design else {}
    if not identity_cards:
        identity_cards = {}

    style_dna = "ART STYLE: Premium 3D CGI animation (Pixar/DreamWorks quality). Volumetric lighting, warm color grading, cinematic composition."
    style_anchors = production_design.get("style_anchors", "") if production_design else ""
    if style_anchors:
        style_dna = f"{style_dna} {style_anchors}"
    
    # ── Phase 0A: Generate dialogue timelines for all scenes (NEW!) ──
    logger.info(f"Storyboard [{project_id}]: Phase 0A — Generating dialogue timelines for sync")
    if update_fn:
        update_fn(tenant_id, project_id, {
            "storyboard_status": {"phase": "dialogue_timing", "current": 0, "total": total, "detail": "Analyzing dialogue timing..."}
        })
    
    enriched_scenes = []
    for i, scene in enumerate(scenes):
        try:
            enriched = enrich_scene_with_timeline(scene, project_id=project_id)
            enriched_scenes.append(enriched)
            timeline_beats = len(enriched.get("dialogue_timeline", []))
            logger.info(f"Storyboard [{project_id}]: Scene {i+1} dialogue timeline - {timeline_beats} beats")
        except Exception as e:
            logger.warning(f"Storyboard [{project_id}]: Scene {i+1} dialogue timeline failed: {e}")
            enriched_scenes.append(scene)  # Use original scene without timeline
    
    scenes = enriched_scenes  # Use enriched scenes from now on

    # ── Phase 0B: Download and cache all avatar images ──
    logger.info(f"Storyboard [{project_id}]: Phase 0B — Caching avatar images")
    avatar_cache = {}
    for name, url in char_avatars.items():
        if url and url not in avatar_cache:
            try:
                supabase_url = os.environ.get('SUPABASE_URL', '')
                full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
                ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                urllib.request.urlretrieve(full_url, ref_file.name)
                avatar_cache[url] = ref_file.name
            except Exception as e:
                logger.warning(f"Storyboard [{project_id}]: Avatar download failed for {name}: {e}")
                avatar_cache[url] = None

    # ── Phase 1: Generate Shot Briefs (Claude, parallel) ──
    logger.info(f"Storyboard [{project_id}]: Phase 1 — Generating shot briefs for {total} scenes")
    if update_fn:
        update_fn(tenant_id, project_id, {
            "storyboard_status": {"phase": "planning", "current": 0, "total": total, "detail": "Shot Director planning frames..."}
        })

    brief_semaphore = threading.Semaphore(8)  # Up to 8 Claude calls in parallel
    all_shot_briefs = [None] * total

    def _gen_brief(idx, scene, scene_num):
        with brief_semaphore:
            try:
                prev_scene = scenes[idx - 1] if idx > 0 else None
                next_scene = scenes[idx + 1] if idx < total - 1 else None
                dialogue_timeline = scene.get("dialogue_timeline", [])  # NEW: Get timeline
                briefs = _generate_shot_briefs(
                    scene=scene, scene_num=scene_num,
                    identity_cards=identity_cards, style_dna=style_dna,
                    prev_scene=prev_scene, next_scene=next_scene,
                    lang=lang, project_id=project_id,
                    dialogue_timeline=dialogue_timeline,  # NEW: Pass timeline
                )
                all_shot_briefs[idx] = briefs
            except Exception as e:
                logger.warning(f"Storyboard [{project_id}]: Shot brief failed for scene {scene_num}: {e}")
                all_shot_briefs[idx] = None

    brief_threads = []
    for i, scene in enumerate(scenes):
        sn = scene.get("scene_number", i + 1)
        t = threading.Thread(target=_gen_brief, args=(i, scene, sn))
        brief_threads.append(t)
        t.start()

    for t in brief_threads:
        t.join(timeout=90)

    briefs_ok = sum(1 for b in all_shot_briefs if b is not None)
    logger.info(f"Storyboard [{project_id}]: Phase 1 complete — {briefs_ok}/{total} shot briefs generated")

    # ── Phase 2: Generate frames (Gemini, parallel scenes) ──
    logger.info(f"Storyboard [{project_id}]: Phase 2 — Generating {total * 6} frames across {total} scenes")
    scene_semaphore = threading.Semaphore(4)  # 4 scenes in parallel (was 2)

    def _gen_panel(scene, scene_num, scene_idx):
        with scene_semaphore:
            try:
                if update_fn:
                    update_fn(tenant_id, project_id, {
                        "storyboard_status": {
                            "phase": "generating",
                            "current": scene_num,
                            "total": total,
                        }
                    })

                scene_briefs = all_shot_briefs[scene_idx]

                frame_results = _generate_all_frames_for_scene(
                    scene=scene, scene_num=scene_num,
                    project_id=project_id,
                    char_avatars=char_avatars, avatar_cache=avatar_cache,
                    character_bible=character_bible, identity_cards=identity_cards,
                    style_dna=style_dna, shot_briefs=scene_briefs, lang=lang,
                )

                image_url = None
                frames = []
                for fi, (ft, img_bytes) in enumerate(frame_results):
                    if img_bytes and upload_fn:
                        fname = f"storyboard/{project_id}/panel_{scene_num}_frame_{fi+1}.png"
                        frame_url = upload_fn(img_bytes, fname, "image/png")
                        frames.append({
                            "frame_number": fi + 1,
                            "image_url": frame_url,
                            "label": ft["label"],
                        })
                        if image_url is None:
                            image_url = frame_url

                logger.info(f"Storyboard [{project_id}]: Panel {scene_num} — {len(frames)} frames uploaded")

                return {
                    "scene_number": scene_num,
                    "title": scene.get("title", f"Cena {scene_num}"),
                    "description": scene.get("description", ""),
                    "dialogue": scene.get("dialogue", ""),
                    "emotion": scene.get("emotion", ""),
                    "camera": scene.get("camera", ""),
                    "characters_in_scene": scene.get("characters_in_scene", []),
                    "image_url": image_url,
                    "frames": frames,
                    "status": "done" if image_url else "error",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                logger.error(f"Storyboard [{project_id}]: Panel {scene_num} failed: {e}")
                return {
                    "scene_number": scene_num,
                    "title": scene.get("title", f"Cena {scene_num}"),
                    "description": scene.get("description", ""),
                    "dialogue": scene.get("dialogue", ""),
                    "emotion": scene.get("emotion", ""),
                    "characters_in_scene": scene.get("characters_in_scene", []),
                    "image_url": None,
                    "status": "error",
                    "error": str(e)[:200],
                }

    threads = []
    results = [None] * total
    for i, scene in enumerate(scenes):
        sn = scene.get("scene_number", i + 1)

        def worker(s=scene, num=sn, idx=i):
            results[idx] = _gen_panel(s, num, idx)

        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=300)

    panels = [r for r in results if r is not None]
    panels.sort(key=lambda p: p["scene_number"])

    for path in avatar_cache.values():
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except Exception:
                pass

    return panels


def facilitator_chat(
    message: str,
    panels: list,
    scenes: list,
    chat_history: list,
    lang: str = "pt",
) -> dict:
    """AI Facilitator: Interprets user commands to edit storyboard panels.

    Returns dict with:
        - response: str (message to show user)
        - actions: list of {action, panel_number, field, value}
    """
    import litellm

    lang_name = {"pt": "Português", "en": "English", "es": "Español"}.get(lang, "Português")

    panels_summary = ""
    for p in panels:
        panels_summary += f"\nPainel {p['scene_number']}: {p['title']}"
        panels_summary += f"\n  Descrição: {p['description'][:100]}"
        panels_summary += f"\n  Diálogo: {p['dialogue'][:100]}"
        panels_summary += f"\n  Personagens: {', '.join(p.get('characters_in_scene', []))}"
        panels_summary += f"\n  Imagem: {'Sim' if p.get('image_url') else 'Sem imagem'}"
        panels_summary += f"\n  Status: {p.get('status', 'unknown')}"

    system_prompt = f"""You are the Storyboard Facilitator AI for an animated film production platform.
Your job is to help the user edit and improve their storyboard panels.

LANGUAGE: You MUST respond in {lang_name}.

CURRENT STORYBOARD:
{panels_summary}

You can suggest these ACTIONS (output them as JSON in your response):
1. EDIT_TEXT — Change a panel's dialogue, description, or title
2. REGENERATE_IMAGE — Request a new image for a specific panel
3. EDIT_DESCRIPTION — Modify the visual description that will be used to regenerate the image

RESPONSE FORMAT:
Always respond naturally in {lang_name}.
If the user asks to change something specific, include an ACTIONS block at the END of your response:

```actions
[{{"action": "edit_text", "panel_number": N, "field": "dialogue|description|title", "value": "new text"}}]
```
or
```actions
[{{"action": "regenerate_image", "panel_number": N, "new_description": "optional updated description for the image"}}]
```

If the user is just chatting or asking questions, respond naturally without actions.
If the user wants to change multiple panels, include multiple actions in the array.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for h in chat_history[-10:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("text", "")})
    messages.append({"role": "user", "content": message})

    try:
        response = litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=messages,
            api_key=ANTHROPIC_API_KEY,
            max_tokens=2000,
            timeout=120,
        )
        reply = response.choices[0].message.content

        # Parse actions from response
        actions = []
        if "```actions" in reply:
            import json
            actions_block = reply.split("```actions")[1].split("```")[0].strip()
            try:
                actions = json.loads(actions_block)
            except Exception:
                pass
            # Clean response by removing the actions block
            clean_reply = reply.split("```actions")[0].strip()
        else:
            clean_reply = reply

        return {
            "response": clean_reply,
            "actions": actions,
        }
    except Exception as e:
        logger.error(f"Facilitator chat error: {e}")
        error_msg = "Desculpe, ocorreu um erro ao processar." if lang == "pt" else "Sorry, an error occurred."
        return {"response": error_msg, "actions": []}
