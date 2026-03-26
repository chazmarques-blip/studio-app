"""Smart Image Editor — Scene analysis + targeted element editing.

Uses Gemini Vision for scene understanding and generates a structured map
of all elements (characters, objects, background) before editing.
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
    """Download image with cache."""
    from core.cache import image_cache
    return image_cache.download(url)


def analyze_scene(
    image_url: str,
    project_id: str,
    panel_number: int,
    scene_context: dict = None,
) -> dict:
    """Analyze a storyboard image and return a structured scene map.

    Returns JSON with detected characters, objects, background, and composition.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        return {"error": "No EMERGENT_LLM_KEY"}

    img_bytes = _download_image(image_url)
    if not img_bytes:
        return {"error": "Failed to download image"}

    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

    context_block = ""
    if scene_context:
        context_block = f"""
SCENE CONTEXT:
- Title: {scene_context.get('title', '')}
- Description: {scene_context.get('description', '')}
- Characters expected: {', '.join(scene_context.get('characters_in_scene', []))}
- Emotion: {scene_context.get('emotion', '')}"""

    prompt = f"""Analyze this storyboard illustration in COMPLETE DETAIL.
{context_block}

Identify EVERY element and return a structured JSON map:

{{
  "characters": [
    {{
      "name": "character name or description",
      "position": "left|center|right|background",
      "posture": "standing|sitting|walking|etc",
      "expression": "happy|sad|surprised|etc",
      "clothing": "description of clothes",
      "details": "any notable details, accessories, features",
      "issues": "any visual problems: wrong proportions, missing limbs, deformation, etc"
    }}
  ],
  "objects": [
    {{
      "name": "object name",
      "position": "where in the scene",
      "details": "description",
      "issues": "any visual problems"
    }}
  ],
  "background": {{
    "setting": "indoor|outdoor|abstract",
    "description": "detailed description of the environment",
    "lighting": "type of lighting",
    "time_of_day": "morning|afternoon|sunset|night",
    "issues": "any visual problems"
  }},
  "composition": {{
    "camera_angle": "wide|medium|close-up|low-angle|high-angle",
    "focal_point": "what draws the eye first",
    "mood": "overall emotional tone of the image"
  }},
  "quality_issues": [
    "list any artifacts, deformations, inconsistencies, or areas that need fixing"
  ]
}}

Be thorough and precise. Report ALL visual issues.
Return ONLY valid JSON."""

    async def _analyze():
        chat = LlmChat(
            api_key=api_key,
            session_id=f"analyze-{project_id}-{panel_number}",
            system_message="You are an expert visual analyst and storyboard reviewer. Analyze images with extreme precision and attention to detail."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["text"])

        msg = UserMessage(
            text=prompt,
            file_contents=[ImageContent(img_b64)]
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
            result_text = pool.submit(lambda: asyncio.run(_analyze())).result(timeout=60)
    else:
        result_text = asyncio.run(_analyze())

    if not result_text:
        return {"error": "No analysis returned"}

    try:
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        if start >= 0 and end > start:
            analysis = json.loads(result_text[start:end])
        else:
            raise ValueError("No JSON found in response")
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"SceneAnalysis [{project_id}]: Parse error: {e}")
        return {"error": f"Parse error: {e}", "raw": result_text[:500]}

    analysis["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    analysis["panel_number"] = panel_number
    logger.info(f"SceneAnalysis [{project_id}]: Panel {panel_number} — {len(analysis.get('characters', []))} chars, {len(analysis.get('objects', []))} objects")
    return analysis


def smart_edit(
    image_url: str,
    edit_instruction: str,
    scene_analysis: dict,
    project_id: str,
    panel_number: int,
    lang: str = "pt",
) -> bytes:
    """Perform targeted image editing using scene analysis context.

    Uses the scene map to generate ultra-precise edit instructions
    that preserve all unrelated elements.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        return None

    img_bytes = _download_image(image_url)
    if not img_bytes:
        return None

    img_b64 = base64.b64encode(img_bytes).decode('utf-8')

    # Build preservation list from analysis
    chars = scene_analysis.get("characters", [])
    objects = scene_analysis.get("objects", [])
    bg = scene_analysis.get("background", {})

    preserve_block = "ELEMENTS TO PRESERVE EXACTLY (do NOT change these):\n"
    for c in chars:
        preserve_block += f"- CHARACTER '{c.get('name', '?')}' at {c.get('position', '?')}: {c.get('posture', '')}, wearing {c.get('clothing', '')}, expression {c.get('expression', '')}\n"
    for o in objects:
        preserve_block += f"- OBJECT '{o.get('name', '?')}' at {o.get('position', '?')}: {o.get('details', '')}\n"
    preserve_block += f"- BACKGROUND: {bg.get('description', 'preserve as-is')}\n"
    preserve_block += f"- LIGHTING: {bg.get('lighting', 'preserve as-is')}\n"

    lang_name = {"pt": "Portugues", "en": "English", "es": "Espanol"}.get(lang, "Portugues")

    prompt = f"""SMART EDIT — You have DETAILED knowledge of this scene. Edit ONLY what is requested.

USER REQUEST: {edit_instruction}

SCENE MAP (what the image contains):
{preserve_block}

EDIT RULES:
1. Modify ONLY what the user explicitly asked to change
2. PRESERVE every other element in its EXACT position, color, pose, expression
3. The edit must be seamless — the result should look like the original was always this way
4. Maintain the same 3D CGI Pixar/DreamWorks art style
5. Maintain the same camera angle, lighting, and composition
6. DO NOT add text, labels, or watermarks
7. DO NOT change the aspect ratio

Language context: {lang_name}"""

    async def _edit():
        chat = LlmChat(
            api_key=api_key,
            session_id=f"smart-edit-{project_id}-{panel_number}",
            system_message="You are a precision image editor with deep scene understanding. You know exactly what every element in the image is and you edit ONLY what is requested."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

        msg = UserMessage(
            text=prompt,
            file_contents=[ImageContent(img_b64)]
        )
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
            result = pool.submit(lambda: asyncio.run(_edit())).result(timeout=90)
    else:
        result = asyncio.run(_edit())

    if result:
        logger.info(f"SmartEdit [{project_id}]: Panel {panel_number} edited ({len(result)//1024}KB) — {edit_instruction[:50]}")
    return result
