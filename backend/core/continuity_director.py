"""Continuity Director Agent — Holistic storyboard consistency analysis and auto-correction.

Analyzes all frames across a storyboard project to ensure:
1. Character appearance consistency (clothing, features, age)
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
            system_message="You are an expert continuity director for animated productions. You analyze visual consistency across storyboard frames with extreme precision."
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
    # Try to find JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    # Try JSON array
    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return {"items": json.loads(text[start:end])}
        except json.JSONDecodeError:
            pass
    return {}


def build_character_reference(characters: list, character_avatars: dict) -> str:
    """Build a master character reference block from project data."""
    ref = ""
    for ch in characters:
        name = ch.get("name", "Unknown")
        age = ch.get("age", "")
        desc = ch.get("description", "")
        avatar_url = character_avatars.get(name, "")
        ref += f"\n--- CHARACTER: {name} ---\n"
        ref += f"Age category: {age}\n"
        ref += f"Description: {desc}\n"
        if avatar_url:
            ref += "Has reference avatar: YES\n"
    return ref


def analyze_continuity(
    project_id: str,
    panels: list,
    scenes: list,
    characters: list,
    character_avatars: dict,
    progress_callback=None,
) -> dict:
    """Analyze the entire storyboard for continuity issues.

    Processes scenes in batches of 3, analyzing the key frame (frame 0)
    of each scene against the character reference.

    Returns a structured report with all detected issues.
    """
    char_reference = build_character_reference(characters, character_avatars)

    # Build scene context mapping
    scene_map = {}
    for s in scenes:
        scene_map[s.get("scene_number")] = s

    all_issues = []
    total_panels = len(panels)
    batch_size = 3  # Analyze 3 scenes at a time to avoid timeouts

    for batch_start in range(0, total_panels, batch_size):
        batch = panels[batch_start:batch_start + batch_size]
        batch_images = []
        batch_context = ""

        for panel in batch:
            sn = panel.get("scene_number", 0)
            frames = panel.get("frames", [])
            # Use frame 0 (Abertura) as the representative frame
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
                    batch_images.append(base64.b64encode(img_bytes).decode("utf-8"))
                    expected_chars = panel.get("characters_in_scene", [])
                    batch_context += f"\n\nIMAGE {len(batch_images)} = Scene {sn}: \"{panel.get('title', '')}\"\n"
                    batch_context += f"Expected characters: {', '.join(expected_chars)}\n"
                    batch_context += f"Description: {panel.get('description', '')[:200]}\n"
                    batch_context += f"Emotion: {panel.get('emotion', '')}\n"
            except Exception as e:
                logger.warning(f"Continuity [{project_id}]: Failed to download scene {sn}: {e}")

        if not batch_images:
            continue

        prompt = f"""CONTINUITY ANALYSIS — Analyze these {len(batch_images)} storyboard frames for visual consistency issues.

CHARACTER REFERENCE (the definitive look of each character):
{char_reference}

SCENE DETAILS:
{batch_context}

For EACH image, check:
1. **Character Consistency**: Does each character match their reference description? Check clothing, hair, skin tone, body proportions, age
2. **Age Accuracy**: Are characters shown at the correct age for this scene? (e.g., "Abraao Jovem" should look 25, "Abraao Idoso" should look 100)
3. **Irrelevant Elements**: Are there objects, characters, or elements that DON'T belong in this scene's context?
4. **Visual Quality**: Any deformations, extra limbs, merged characters, or AI artifacts?
5. **Scene Coherence**: Does the setting/background match the scene description?

Return JSON:
{{
  "issues": [
    {{
      "scene_number": N,
      "severity": "high|medium|low",
      "category": "character_consistency|age_mismatch|irrelevant_element|quality_defect|scene_coherence",
      "element": "what is wrong (character name or object)",
      "description": "detailed description of the issue",
      "correction": "specific instruction to fix this (for an AI image editor)"
    }}
  ],
  "scenes_ok": [list of scene numbers that are fine],
  "summary": "brief overall assessment"
}}

Be strict and thorough. Report ALL issues, even minor ones. Return ONLY valid JSON."""

        try:
            result_text = _run_vision_analysis(
                batch_images, prompt,
                f"continuity-{project_id}-b{batch_start}"
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

    # Deduplicate and sort issues by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))

    report = {
        "total_scenes_analyzed": total_panels,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "high_count": sum(1 for i in all_issues if i.get("severity") == "high"),
        "medium_count": sum(1 for i in all_issues if i.get("severity") == "medium"),
        "low_count": sum(1 for i in all_issues if i.get("severity") == "low"),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Continuity [{project_id}]: Analysis complete — "
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

    return inpaint_element(
        image_url=image_url,
        edit_instruction=correction_instruction,
        project_id=project_id,
        panel_number=panel_number,
        lang="pt",
    )
