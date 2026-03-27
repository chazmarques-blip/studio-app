"""Continuity Director Agent — Holistic storyboard consistency analysis and auto-correction.

Uses CHARACTER AVATAR IMAGES as the primary visual reference (not text descriptions).
Analyzes ALL 6 FRAMES of each scene to ensure:
1. Characters match their avatar reference images (species, appearance, style)
2. Removal of irrelevant/out-of-context elements
3. Visual quality across all frames
4. Auto-correction via the existing inpainting pipeline
"""
import os
import base64
import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


def _download_image(url: str) -> bytes:
    """Download image with cache."""
    from core.cache import image_cache
    return image_cache.download(url)


def _run_vision_analysis(images_b64: list, prompt: str, session_id: str) -> str:
    """Run Gemini Vision analysis with LLM cache."""
    from core.cache import llm_cache
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        raise ValueError("No EMERGENT_LLM_KEY")

    # Check LLM cache
    img_hashes = [llm_cache.hash_image(base64.b64decode(b)) for b in images_b64[:3]]
    prompt_hash = [prompt[:200]]
    cached = llm_cache.get(prompt[:500], img_hashes + prompt_hash)
    if cached:
        logger.info(f"LLM cache HIT for session {session_id}")
        return cached

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message="You are an expert continuity director for animated productions. You ensure characters match their AVATAR REFERENCE IMAGES exactly across ALL frames. The avatars define the canonical look — species, style, colors, proportions."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["text"])
        msg = UserMessage(
            text=prompt,
            file_contents=[ImageContent(img) for img in images_b64]
        )
        text, _ = await chat.send_message_multimodal_response(msg)
        return text

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(lambda: asyncio.run(_gen())).result(timeout=120)
    else:
        result = asyncio.run(_gen())

    # Store in LLM cache
    llm_cache.put(prompt[:500], img_hashes + prompt_hash, result)
    return result


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response text."""
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return {"items": json.loads(text[start:end])}
        except json.JSONDecodeError:
            pass
    return {}


def _load_avatar_images(character_avatars: dict) -> dict:
    """Download all avatar images using cache with pre-warming."""
    from core.cache import image_cache
    urls = [url for url in character_avatars.values() if url]
    image_cache.prewarm(urls)

    avatars_b64 = {}
    for name, url in character_avatars.items():
        if not url:
            continue
        try:
            img_bytes = image_cache.download(url)
            if img_bytes:
                avatars_b64[name] = base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"Continuity: Failed to load avatar for '{name}': {e}")
    logger.info(f"Continuity: Loaded {len(avatars_b64)} avatar references (cached)")
    return avatars_b64


def analyze_continuity(
    project_id: str,
    panels: list,
    scenes: list,
    characters: list,
    character_avatars: dict,
    user_notes: str = "",
    progress_callback=None,
) -> dict:
    """Analyze ALL frames of every scene for continuity issues.

    Processes ONE scene at a time (11 avatars + 6 frames = 17 images per call).
    Each frame is individually evaluated against the avatar references.
    """
    # Step 1: Load all avatar images (pre-warmed from cache)
    avatars_b64 = _load_avatar_images(character_avatars)

    # Pre-warm ALL frame images for all panels
    from core.cache import image_cache
    all_frame_urls = []
    for panel in panels:
        for frame in panel.get("frames", []):
            url = frame.get("image_url")
            if url:
                all_frame_urls.append(url)
    if all_frame_urls:
        image_cache.prewarm(all_frame_urls)

    # Build avatar image list and prompt mapping
    avatar_images = []
    avatar_prompt_block = "AVATAR REFERENCE IMAGES (the CANONICAL look of each character):\n"
    for name, b64 in avatars_b64.items():
        avatar_images.append(b64)
        avatar_prompt_block += f"  AVATAR IMAGE {len(avatar_images)} = \"{name}\"\n"

    # Secondary text context
    char_text_block = "\nCHARACTER NAMES & AGES (secondary context only — avatars are the visual truth):\n"
    for ch in characters:
        char_text_block += f"  - {ch.get('name', '?')} (age: {ch.get('age', '?')})\n"

    all_issues = []
    total_panels = len(panels)
    total_frames_analyzed = 0

    # Process ONE scene at a time (6 frames + avatars)
    for panel_idx, panel in enumerate(panels):
        sn = panel.get("scene_number", 0)
        frames = panel.get("frames", [])
        expected_chars = panel.get("characters_in_scene", [])

        if not frames:
            if progress_callback:
                progress_callback(panel_idx + 1, total_panels, 0)
            continue

        # Download all 6 frames of this scene (from cache)
        frame_images = []
        frame_labels = []
        for fi, frame in enumerate(frames):
            url = frame.get("image_url")
            if not url:
                continue
            try:
                img_bytes = _download_image(url)
                if img_bytes:
                    frame_images.append(base64.b64encode(img_bytes).decode("utf-8"))
                    label = frame.get("label", f"Frame {fi+1}")
                    frame_labels.append((fi, label))
            except Exception as e:
                logger.warning(f"Continuity [{project_id}]: Scene {sn} frame {fi} download failed: {e}")

        if not frame_images:
            if progress_callback:
                progress_callback(panel_idx + 1, total_panels, 0)
            continue

        # Build frame listing for prompt
        frames_block = f"\nSCENE {sn} FRAMES TO ANALYZE: \"{panel.get('title', '')}\"\n"
        frames_block += f"  Expected characters: {', '.join(expected_chars)}\n"
        frames_block += f"  Description: {panel.get('description', '')[:200]}\n"
        frames_block += f"  Emotion: {panel.get('emotion', '')}\n"
        for i, (fi, label) in enumerate(frame_labels):
            img_num = len(avatar_images) + i + 1
            frames_block += f"  FRAME IMAGE {img_num} = Frame {fi} \"{label}\"\n"

        # Combine: avatars first, then all 6 frames
        all_images = avatar_images + frame_images

        prompt = f"""CONTINUITY ANALYSIS — Review ALL {len(frame_images)} frames of Scene {sn} against the avatar references.

{avatar_prompt_block}
{char_text_block}
{frames_block}

CRITICAL RULES:
- The AVATAR IMAGES are the DEFINITIVE visual reference for each character
- Characters may be animals, anthropomorphic creatures, fantasy beings — the avatar IS their correct appearance
- Do NOT flag characters as wrong for being animals/creatures if their avatar shows that
- Do NOT suggest changing a character's species or visual style
- Check EVERY FRAME individually — each may have different issues
{f'''
USER NOTES (PRIORITY — the director specifically asked to check these):
{user_notes}
''' if user_notes.strip() else ''}
For EACH of the {len(frame_images)} frames, check:
1. **Avatar Match**: Does each character visually match their avatar? (species, style, colors, clothing)
2. **Cross-Frame Consistency**: Are characters consistent across all 6 frames of this scene?
3. **Irrelevant Elements**: Objects or characters that don't belong
4. **Visual Quality**: Deformations, extra limbs, merged characters, AI artifacts
5. **Scene Coherence**: Does the setting match the description?

Return JSON:
{{
  "issues": [
    {{
      "scene_number": {sn},
      "frame_index": 0-5,
      "frame_label": "frame label",
      "severity": "high|medium|low",
      "category": "avatar_mismatch|cross_frame_inconsistency|irrelevant_element|quality_defect|scene_coherence",
      "element": "what is wrong",
      "description": "detailed description — reference which avatar it should match",
      "correction": "specific fix instruction (must preserve character species/style from avatar)"
    }}
  ],
  "frames_ok": [list of frame indices with no issues],
  "summary": "brief assessment of this scene"
}}

Return ONLY valid JSON."""

        try:
            result_text = _run_vision_analysis(
                all_images, prompt,
                f"continuity-v3-{project_id}-s{sn}"
            )
            parsed = _parse_json(result_text)
            scene_issues = parsed.get("issues", [])
            all_issues.extend(scene_issues)
            total_frames_analyzed += len(frame_images)

            if progress_callback:
                progress_callback(panel_idx + 1, total_panels, len(scene_issues))

            logger.info(
                f"Continuity [{project_id}]: Scene {sn} ({len(frame_images)} frames): "
                f"{len(scene_issues)} issues"
            )
        except Exception as e:
            logger.error(f"Continuity [{project_id}]: Scene {sn} analysis failed: {e}")
            if progress_callback:
                progress_callback(panel_idx + 1, total_panels, 0)

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: (x.get("scene_number", 0), severity_order.get(x.get("severity", "low"), 2)))

    report = {
        "total_scenes_analyzed": total_panels,
        "total_frames_analyzed": total_frames_analyzed,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "high_count": sum(1 for i in all_issues if i.get("severity") == "high"),
        "medium_count": sum(1 for i in all_issues if i.get("severity") == "medium"),
        "low_count": sum(1 for i in all_issues if i.get("severity") == "low"),
        "avatars_used": list(avatars_b64.keys()),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Continuity [{project_id}]: Complete — {total_frames_analyzed} frames, "
        f"{report['total_issues']} issues ({report['high_count']}H, {report['medium_count']}M, {report['low_count']}L)"
    )
    return report


def auto_correct_issue(
    image_url: str,
    correction_instruction: str,
    project_id: str,
    panel_number: int,
    frame_index: int = 0,
) -> bytes:
    """Apply a single auto-correction to a frame using the existing inpainting pipeline."""
    from core.storyboard_inpaint import inpaint_element
    from core.cache import image_cache

    result = inpaint_element(
        image_url=image_url,
        edit_instruction=correction_instruction,
        project_id=project_id,
        panel_number=panel_number,
        lang="pt",
    )

    # Invalidate the old image from cache since it was replaced
    if result:
        image_cache.invalidate(image_url)

    return result
