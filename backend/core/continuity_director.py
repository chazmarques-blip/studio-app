"""Continuity Director Agent — Holistic storyboard consistency analysis and auto-correction.

Uses CHARACTER AVATAR IMAGES as the primary visual reference (not text descriptions).
Analyzes all frames across a storyboard project to ensure:
1. Characters match their avatar reference images (species, appearance, style)
2. Removal of irrelevant/out-of-context elements
3. Chronological coherence between scenes
4. Auto-correction via the existing inpainting pipeline
"""
import os
import base64
import asyncio
import json
import logging
import tempfile
import urllib.request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


def _download_image(url: str) -> bytes:
    """Download image from URL or Supabase path."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        urllib.request.urlretrieve(full_url, tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def _run_vision_analysis(images_b64: list, prompt: str, session_id: str) -> str:
    """Run Gemini Vision analysis with multiple images."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        raise ValueError("No EMERGENT_LLM_KEY")

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message="You are an expert continuity director for animated productions. You ensure characters match their AVATAR REFERENCE IMAGES exactly. The avatars define the canonical look — species, style, colors, proportions."
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
            return pool.submit(lambda: asyncio.run(_gen())).result(timeout=120)
    else:
        return asyncio.run(_gen())


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
    """Download all avatar images and return as {name: base64_string}."""
    avatars_b64 = {}
    for name, url in character_avatars.items():
        if not url:
            continue
        try:
            img_bytes = _download_image(url)
            if img_bytes:
                avatars_b64[name] = base64.b64encode(img_bytes).decode("utf-8")
                logger.info(f"Continuity: Loaded avatar for '{name}' ({len(img_bytes)//1024}KB)")
        except Exception as e:
            logger.warning(f"Continuity: Failed to load avatar for '{name}': {e}")
    return avatars_b64


def analyze_continuity(
    project_id: str,
    panels: list,
    scenes: list,
    characters: list,
    character_avatars: dict,
    progress_callback=None,
) -> dict:
    """Analyze the entire storyboard for continuity issues.

    CRITICAL: Uses avatar IMAGES as the primary visual reference.
    The avatars define the canonical look of each character (species, style, etc).
    Text descriptions are secondary context only.

    Processes scenes in batches of 2 (with avatars, payloads are larger).
    """
    # Step 1: Load all avatar images as base64
    logger.info(f"Continuity [{project_id}]: Loading {len(character_avatars)} avatar reference images...")
    avatars_b64 = _load_avatar_images(character_avatars)

    if not avatars_b64:
        logger.warning(f"Continuity [{project_id}]: No avatars loaded, analysis may be less accurate")

    # Build avatar image list and mapping for the prompt
    avatar_images = []
    avatar_prompt_block = "AVATAR REFERENCE IMAGES (these define the CANONICAL look of each character):\n"
    for name, b64 in avatars_b64.items():
        avatar_images.append(b64)
        idx = len(avatar_images)
        avatar_prompt_block += f"  AVATAR IMAGE {idx} = \"{name}\"\n"

    # Build text reference as secondary info
    char_text_block = "\nCHARACTER TEXT CONTEXT (secondary — avatars above are the visual truth):\n"
    for ch in characters:
        name = ch.get("name", "Unknown")
        age = ch.get("age", "")
        char_text_block += f"  - {name} (age: {age})\n"

    all_issues = []
    total_panels = len(panels)
    # Smaller batches because we also send avatar images
    batch_size = 2

    for batch_start in range(0, total_panels, batch_size):
        batch = panels[batch_start:batch_start + batch_size]
        scene_images = []
        batch_context = ""

        for panel in batch:
            sn = panel.get("scene_number", 0)
            frames = panel.get("frames", [])
            image_url = None
            if frames:
                image_url = frames[0].get("image_url")
            if not image_url:
                image_url = panel.get("image_url")
            if not image_url:
                continue

            try:
                img_bytes = _download_image(image_url)
                if img_bytes:
                    scene_images.append(base64.b64encode(img_bytes).decode("utf-8"))
                    expected_chars = panel.get("characters_in_scene", [])
                    scene_img_idx = len(avatar_images) + len(scene_images)
                    batch_context += f"\n\nSCENE IMAGE {scene_img_idx} = Scene {sn}: \"{panel.get('title', '')}\"\n"
                    batch_context += f"  Expected characters: {', '.join(expected_chars)}\n"
                    batch_context += f"  Description: {panel.get('description', '')[:200]}\n"
                    batch_context += f"  Emotion: {panel.get('emotion', '')}\n"
            except Exception as e:
                logger.warning(f"Continuity [{project_id}]: Failed to download scene {sn}: {e}")

        if not scene_images:
            if progress_callback:
                progress_callback(min(batch_start + batch_size, total_panels), total_panels, 0)
            continue

        # Combine: avatars first, then scene images
        all_images = avatar_images + scene_images

        prompt = f"""CONTINUITY ANALYSIS — You are reviewing storyboard frames against CHARACTER AVATAR REFERENCES.

{avatar_prompt_block}
{char_text_block}

SCENE FRAMES TO ANALYZE:
{batch_context}

CRITICAL RULES:
- The AVATAR IMAGES above are the DEFINITIVE visual reference for each character
- Characters may be animals, anthropomorphic creatures, fantasy beings — whatever their avatar shows IS their correct appearance
- Do NOT flag characters as "wrong" because they look like animals/creatures — if the avatar shows an animal, the character IS that animal
- DO NOT suggest changing a character's species, body type, or visual style — the avatar IS the truth
- Focus ONLY on: consistency WITH the avatar (colors, proportions, clothing style), irrelevant objects, quality defects, and scene coherence

For EACH scene image, check:
1. **Avatar Match**: Does each character visually match their avatar reference image? (same species, same style, same color palette, same clothing style)
2. **Irrelevant Elements**: Objects, characters, or elements that DON'T belong in this scene
3. **Visual Quality**: Deformations, extra limbs, merged characters, AI artifacts
4. **Scene Coherence**: Does the setting match the scene description?

DO NOT report issues about:
- Characters being animals/creatures (that's their design if the avatar shows it)
- Characters not looking "human enough" (follow the avatar)
- Age descriptions that contradict the visual style (avatar is truth)

Return JSON:
{{
  "issues": [
    {{
      "scene_number": N,
      "severity": "high|medium|low",
      "category": "avatar_mismatch|irrelevant_element|quality_defect|scene_coherence",
      "element": "what is wrong",
      "description": "detailed description — reference which avatar it should match",
      "correction": "specific instruction to fix (must preserve the character's species/style from avatar)"
    }}
  ],
  "scenes_ok": [list of scene numbers with no issues],
  "summary": "brief overall assessment"
}}

Return ONLY valid JSON."""

        try:
            result_text = _run_vision_analysis(
                all_images, prompt,
                f"continuity-v2-{project_id}-b{batch_start}"
            )
            parsed = _parse_json(result_text)
            batch_issues = parsed.get("issues", [])
            all_issues.extend(batch_issues)

            if progress_callback:
                progress_callback(
                    min(batch_start + batch_size, total_panels),
                    total_panels,
                    len(batch_issues),
                )

            logger.info(
                f"Continuity [{project_id}]: Batch {batch_start}-{batch_start+len(batch)}: "
                f"{len(batch_issues)} issues found"
            )
        except Exception as e:
            logger.error(f"Continuity [{project_id}]: Batch {batch_start} analysis failed: {e}")
            if progress_callback:
                progress_callback(
                    min(batch_start + batch_size, total_panels),
                    total_panels,
                    0,
                )

    # Sort issues by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))

    report = {
        "total_scenes_analyzed": total_panels,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "high_count": sum(1 for i in all_issues if i.get("severity") == "high"),
        "medium_count": sum(1 for i in all_issues if i.get("severity") == "medium"),
        "low_count": sum(1 for i in all_issues if i.get("severity") == "low"),
        "avatars_used": list(avatars_b64.keys()),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Continuity [{project_id}]: Analysis complete — "
        f"{report['total_issues']} issues ({report['high_count']}H, {report['medium_count']}M, {report['low_count']}L) "
        f"using {len(avatars_b64)} avatar references"
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

    return inpaint_element(
        image_url=image_url,
        edit_instruction=correction_instruction,
        project_id=project_id,
        panel_number=panel_number,
        lang="pt",
    )
