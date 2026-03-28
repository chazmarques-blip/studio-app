"""Continuity Director v2 — Expert character consistency enforcer using Claude Vision.

ARCHITECTURE:
1. PREVENTIVE GATE: validate_frame() is called AFTER every image generation, BEFORE saving.
   If the frame fails validation, it is regenerated (max 2 retries).
2. POST-HOC ANALYSIS: analyze_continuity() runs a full audit of all frames.
3. AUTO-CORRECTION: auto_correct_issue() fixes detected issues via inpainting.

Uses CLAUDE VISION (not Gemini) for superior anatomical/species understanding.
"""
import os
import base64
import asyncio
import json
import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


# ══════════════════════════════════════════
# IMAGE UTILITIES
# ══════════════════════════════════════════

def _download_image_bytes(url: str) -> bytes:
    """Download image with robust fallback."""
    import urllib.request
    # Try cache first, fall back to direct download
    try:
        from core.cache import image_cache
        result = image_cache.download(url)
        if result:
            return result
    except Exception:
        pass
    # Direct fallback
    try:
        supabase_url = os.environ.get("SUPABASE_URL", "")
        full_url = url if url.startswith("http") else f"{supabase_url}/storage/v1/object/public{url}"
        with urllib.request.urlopen(full_url, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        logger.warning(f"ContinuityV2: Download failed for {url[:80]}: {e}")
        return b""


def _image_to_b64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")


def _load_avatar_references(character_avatars: dict) -> dict:
    """Download all character avatars, return {name: b64_string}."""
    try:
        from core.cache import image_cache
        urls = [u for u in character_avatars.values() if u]
        image_cache.prewarm(urls)
    except ImportError:
        pass

    refs = {}
    for name, url in character_avatars.items():
        if not url:
            continue
        try:
            img = _download_image_bytes(url)
            if img:
                refs[name] = _image_to_b64(img)
        except Exception as e:
            logger.warning(f"ContinuityV2: Failed to load avatar '{name}': {e}")
    return refs


# ══════════════════════════════════════════
# CLAUDE VISION CALLS
# ══════════════════════════════════════════

def _call_claude_vision(images_b64: list, prompt: str, session_id: str, max_tokens: int = 2000) -> str:
    """Call Claude Vision via emergentintegrations for image analysis."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY not set")

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=(
                "You are the world's most rigorous CONTINUITY DIRECTOR for animated productions. "
                "Your SOLE MISSION is to ensure every generated frame matches the CHARACTER REFERENCE IMAGES exactly. "
                "The reference images are the ABSOLUTE TRUTH — species, body type (biped/quadruped), colors, proportions, "
                "clothing, accessories. You NEVER accept deviations. "
                "If a character is a bipedal animal in the reference, it MUST be bipedal in EVERY frame. "
                "If a character is quadrupedal, it MUST remain quadrupedal. "
                "You detect even SUBTLE inconsistencies: wrong number of legs, wrong posture (standing vs crawling), "
                "wrong colors, wrong species, merged characters, extra limbs, missing features."
            )
        )
        chat.with_model("anthropic", "claude-sonnet-4-5-20250929").with_params(max_tokens=max_tokens)
        msg = UserMessage(
            text=prompt,
            file_contents=[ImageContent(img) for img in images_b64]
        )
        response = await chat.send_message(msg)
        return response

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(_gen())).result(timeout=120)
    else:
        return asyncio.run(_gen())


def _parse_json(text: str) -> dict:
    if not text:
        return {}
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        end = text.rfind(end_char) + 1
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start:end])
                return parsed if isinstance(parsed, dict) else {"items": parsed}
            except json.JSONDecodeError:
                continue
    return {}


# ══════════════════════════════════════════
# PREVENTIVE VALIDATION GATE
# ══════════════════════════════════════════

def validate_frame(
    frame_bytes: bytes,
    character_names_in_scene: list,
    character_avatars: dict,
    scene_description: str = "",
    frame_label: str = "",
    project_id: str = "",
) -> dict:
    """PREVENTIVE GATE — Validate a generated frame BEFORE saving it.

    Compares the frame against character avatar references using Claude Vision.

    Returns:
        {
            "approved": True/False,
            "confidence": 0-100,
            "issues": [...],
            "rejection_reason": "..." or None
        }
    """
    if not character_names_in_scene or not character_avatars:
        return {"approved": True, "confidence": 100, "issues": [], "rejection_reason": None}

    # Load only the relevant character avatars
    images_b64 = []
    avatar_legend = []

    for char_name in character_names_in_scene:
        url = character_avatars.get(char_name)
        if not url:
            continue
        try:
            img = _download_image_bytes(url)
            if img:
                images_b64.append(_image_to_b64(img))
                avatar_legend.append(f"IMAGE {len(images_b64)}: Reference for \"{char_name}\"")
        except Exception:
            continue

    if not images_b64:
        return {"approved": True, "confidence": 50, "issues": [], "rejection_reason": None}

    # Add the frame to validate as the last image
    images_b64.append(_image_to_b64(frame_bytes))
    frame_img_num = len(images_b64)

    prompt = f"""FRAME VALIDATION — Compare the GENERATED FRAME against CHARACTER REFERENCES.

CHARACTER REFERENCES:
{chr(10).join(avatar_legend)}

GENERATED FRAME TO VALIDATE:
IMAGE {frame_img_num}: Generated frame "{frame_label}" — Scene: "{scene_description[:200]}"

STRICT VALIDATION CHECKLIST — Check EACH character that should appear in this frame:

1. **SPECIES & BODY TYPE**: Is each character the SAME species as their reference? 
   - If reference shows BIPED (walks on 2 legs) → frame MUST show biped
   - If reference shows QUADRUPED (walks on 4 legs) → frame MUST show quadruped
   - If reference shows ANIMAL → frame must NOT show human
   - If reference shows HUMAN → frame must NOT show animal

2. **ANATOMY**: Correct number of limbs? Correct posture? Correct body proportions?

3. **COLORS**: Skin/fur/scale colors match reference? Hair/feather colors correct?

4. **DISTINGUISHING FEATURES**: Horns, tails, wings, ears, spots, stripes — all must match reference.

5. **CLOTHING/ACCESSORIES**: If the reference shows specific clothing, the frame should be consistent.

Return ONLY valid JSON:
{{
    "approved": true/false,
    "confidence": 0-100,
    "characters_checked": [
        {{
            "name": "character name",
            "found_in_frame": true/false,
            "species_match": true/false,
            "body_type_match": true/false,
            "color_match": true/false,
            "overall_match": true/false,
            "issue": "description of mismatch or null"
        }}
    ],
    "rejection_reason": "specific reason for rejection or null",
    "issues": ["list of all issues found"]
}}"""

    try:
        result = _call_claude_vision(images_b64, prompt, f"validate-{project_id}-{frame_label[:20]}", max_tokens=1000)
        parsed = _parse_json(result)
        return {
            "approved": parsed.get("approved", True),
            "confidence": parsed.get("confidence", 50),
            "issues": parsed.get("issues", []),
            "rejection_reason": parsed.get("rejection_reason"),
            "characters_checked": parsed.get("characters_checked", []),
        }
    except Exception as e:
        logger.error(f"ContinuityV2 [{project_id}]: Validation failed: {e}")
        # On error, approve to avoid blocking the pipeline
        return {"approved": True, "confidence": 0, "issues": [f"Validation error: {str(e)[:100]}"], "rejection_reason": None}


def validate_and_retry(
    generate_fn,
    character_names_in_scene: list,
    character_avatars: dict,
    scene_description: str = "",
    frame_label: str = "",
    project_id: str = "",
    max_retries: int = 2,
) -> bytes:
    """Generate a frame with automatic validation and retry.

    Args:
        generate_fn: Callable that returns image bytes. Called on each attempt.
        max_retries: Max regeneration attempts on validation failure.

    Returns: The best frame bytes (approved or best attempt after retries).
    """
    best_frame = None
    best_confidence = -1

    for attempt in range(1 + max_retries):
        frame_bytes = generate_fn()
        if not frame_bytes:
            continue

        validation = validate_frame(
            frame_bytes=frame_bytes,
            character_names_in_scene=character_names_in_scene,
            character_avatars=character_avatars,
            scene_description=scene_description,
            frame_label=f"{frame_label}_attempt{attempt+1}",
            project_id=project_id,
        )

        confidence = validation.get("confidence", 0)
        if confidence > best_confidence:
            best_frame = frame_bytes
            best_confidence = confidence

        if validation.get("approved", False):
            if attempt > 0:
                logger.info(f"ContinuityV2 [{project_id}]: {frame_label} approved on attempt {attempt+1}")
            return frame_bytes
        else:
            reason = validation.get("rejection_reason", "unknown")
            logger.warning(
                f"ContinuityV2 [{project_id}]: {frame_label} REJECTED (attempt {attempt+1}/{1+max_retries}): {reason}"
            )

    # Return best attempt even if none was approved
    logger.warning(f"ContinuityV2 [{project_id}]: {frame_label} — returning best attempt (confidence={best_confidence})")
    return best_frame


# ══════════════════════════════════════════
# POST-HOC FULL ANALYSIS
# ══════════════════════════════════════════

def analyze_continuity(
    project_id: str,
    panels: list,
    scenes: list,
    characters: list,
    character_avatars: dict,
    user_notes: str = "",
    progress_callback=None,
) -> dict:
    """Full post-hoc analysis of ALL frames across ALL scenes using Claude Vision."""

    avatar_refs = _load_avatar_references(character_avatars)

    # Pre-warm frame images
    try:
        from core.cache import image_cache
        all_urls = [f.get("image_url") for p in panels for f in p.get("frames", []) if f.get("image_url")]
        if all_urls:
            image_cache.prewarm(all_urls)
    except ImportError:
        pass

    # Build avatar images list
    avatar_images = list(avatar_refs.values())
    avatar_prompt = "CHARACTER REFERENCE IMAGES (ABSOLUTE VISUAL TRUTH):\n"
    for idx, name in enumerate(avatar_refs.keys()):
        avatar_prompt += f"  IMAGE {idx+1}: \"{name}\" — This is the DEFINITIVE look. Species, body type, colors, proportions.\n"

    char_text = "\nCHARACTERS:\n"
    for ch in characters:
        char_text += f"  - {ch.get('name', '?')} (age: {ch.get('age', '?')}, desc: {ch.get('description', '')[:100]})\n"

    all_issues = []
    total_panels = len(panels)
    total_frames = 0

    for pi, panel in enumerate(panels):
        sn = panel.get("scene_number", 0)
        frames = panel.get("frames", [])

        # Get chars expected in this scene from the scenes list
        scene_data = next((s for s in scenes if s.get("scene_number") == sn), {})
        expected_chars = scene_data.get("characters_in_scene", []) or panel.get("characters_in_scene", [])

        if not frames:
            if progress_callback:
                progress_callback(pi + 1, total_panels, 0)
            continue

        # Only load avatars for characters in THIS scene (not all 15+)
        scene_avatar_images = []
        scene_avatar_names = []
        if expected_chars:
            for cname in expected_chars:
                if cname in avatar_refs:
                    scene_avatar_images.append(avatar_refs[cname])
                    scene_avatar_names.append(cname)
        else:
            # If no chars specified, use max 5 most common avatars
            for cname, b64 in list(avatar_refs.items())[:5]:
                scene_avatar_images.append(b64)
                scene_avatar_names.append(cname)

        # Download frames (max 6)
        frame_images = []
        frame_labels = []
        for fi, frame in enumerate(frames[:6]):
            url = frame.get("image_url")
            if not url:
                continue
            try:
                img = _download_image_bytes(url)
                if img and len(img) > 100:
                    frame_images.append(_image_to_b64(img))
                    frame_labels.append((fi, frame.get("frame_type", {}).get("label", f"Frame {fi+1}") if isinstance(frame.get("frame_type"), dict) else frame.get("label", f"Frame {fi+1}")))
            except Exception as e:
                logger.warning(f"ContinuityV2 [{project_id}]: Scene {sn} frame {fi} download failed: {e}")

        if not frame_images:
            if progress_callback:
                progress_callback(pi + 1, total_panels, 0)
            continue

        # Build prompt with only relevant avatars
        avatar_prompt_block = "CHARACTER REFERENCE IMAGES (ABSOLUTE VISUAL TRUTH):\n"
        for idx, name in enumerate(scene_avatar_names):
            avatar_prompt_block += f"  IMAGE {idx+1}: \"{name}\" — DEFINITIVE reference for species, body type, colors, proportions.\n"

        frames_block = f"\nSCENE {sn}: \"{scene_data.get('title', panel.get('title', ''))}\"\n"
        frames_block += f"  Expected characters: {', '.join(expected_chars) if expected_chars else 'not specified'}\n"
        frames_block += f"  Description: {scene_data.get('description', panel.get('description', ''))[:300]}\n"
        for i, (fi, label) in enumerate(frame_labels):
            img_num = len(scene_avatar_images) + i + 1
            frames_block += f"  IMAGE {img_num}: Frame {fi+1} \"{label}\"\n"

        all_images = scene_avatar_images + frame_images

        prompt = f"""FULL CONTINUITY AUDIT — Analyze ALL {len(frame_images)} frames of Scene {sn}.

{avatar_prompt_block}
{char_text}
{frames_block}

{f'DIRECTOR NOTES (HIGH PRIORITY): {user_notes}' if user_notes.strip() else ''}

STRICT RULES — You are IMPECCABLE. Zero tolerance for:
1. **SPECIES CHANGE**: A biped character appearing as quadruped or vice-versa is a CRITICAL error
2. **ANATOMY DRIFT**: Wrong number of legs, arms, tails, wings between frames
3. **COLOR SHIFT**: Character colors must be consistent with reference AND across all frames
4. **POSTURE CHANGE**: If character is bipedal in reference, they cannot crawl on all fours
5. **FEATURE LOSS**: Missing horns, tails, wings, ears that exist in reference
6. **CROSS-FRAME DRIFT**: Character looks different between Frame 1 and Frame 6 of SAME scene
7. **IRRELEVANT ELEMENTS**: Characters or objects that don't belong in this scene

For EACH frame, compare EVERY visible character against their reference image.
Flag ANY deviation, no matter how subtle.

Return ONLY valid JSON:
{{
    "issues": [
        {{
            "scene_number": {sn},
            "frame_index": 0-5,
            "frame_label": "label",
            "severity": "critical|high|medium|low",
            "category": "species_change|anatomy_drift|color_shift|posture_change|feature_loss|cross_frame_drift|irrelevant_element|quality_defect",
            "character": "character name",
            "element": "what is wrong",
            "description": "detailed description comparing to reference",
            "correction": "specific fix instruction preserving character design from reference"
        }}
    ],
    "frames_ok": [frame indices with no issues],
    "scene_score": 0-100,
    "summary": "brief assessment"
}}"""

        try:
            result_text = _call_claude_vision(all_images, prompt, f"audit-v2-{project_id}-s{sn}")
            parsed = _parse_json(result_text)
            scene_issues = parsed.get("issues", [])
            all_issues.extend(scene_issues)
            total_frames += len(frame_images)

            if progress_callback:
                progress_callback(pi + 1, total_panels, len(scene_issues))

            logger.info(f"ContinuityV2 [{project_id}]: Scene {sn}: {len(scene_issues)} issues (score: {parsed.get('scene_score', '?')})")
        except Exception as e:
            logger.error(f"ContinuityV2 [{project_id}]: Scene {sn} analysis failed: {e}")
            if progress_callback:
                progress_callback(pi + 1, total_panels, 0)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_issues.sort(key=lambda x: (x.get("scene_number", 0), severity_order.get(x.get("severity", "low"), 3)))

    report = {
        "total_scenes_analyzed": total_panels,
        "total_frames_analyzed": total_frames,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "critical_count": sum(1 for i in all_issues if i.get("severity") == "critical"),
        "high_count": sum(1 for i in all_issues if i.get("severity") == "high"),
        "medium_count": sum(1 for i in all_issues if i.get("severity") == "medium"),
        "low_count": sum(1 for i in all_issues if i.get("severity") == "low"),
        "avatars_used": list(avatar_refs.keys()),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "engine": "claude-vision-v2",
    }

    logger.info(
        f"ContinuityV2 [{project_id}]: Complete — {total_frames} frames, "
        f"{report['total_issues']} issues (C:{report['critical_count']} H:{report['high_count']} M:{report['medium_count']} L:{report['low_count']})"
    )
    return report


# ══════════════════════════════════════════
# AUTO-CORRECTION
# ══════════════════════════════════════════

def auto_correct_issue(
    image_url: str,
    correction_instruction: str,
    project_id: str,
    panel_number: int,
    frame_index: int = 0,
) -> bytes:
    """Apply a single auto-correction to a frame using inpainting."""
    from core.storyboard_inpaint import inpaint_element

    result = inpaint_element(
        image_url=image_url,
        edit_instruction=correction_instruction,
        project_id=project_id,
        panel_number=panel_number,
        lang="pt",
    )

    if result:
        try:
            from core.cache import image_cache
            image_cache.invalidate(image_url)
        except ImportError:
            pass

    return result
