"""Language Agent — Translation, adaptation, and quality revision for storybook content.

Uses Claude for high-quality translation and text revision while
preserving narrative tone, cultural nuances, and character voice.
"""
import os
import asyncio
import logging
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

SUPPORTED_LANGS = {
    "pt": "Portugues Brasileiro",
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "it": "Italiano",
    "de": "Deutsch",
    "ja": "Japonese",
    "ko": "Coreano",
    "zh": "Chines Mandarim",
    "ar": "Arabe",
}


def _run_claude(system: str, prompt: str, session_id: str) -> str:
    """Run a Claude completion and return the text response."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        raise ValueError("No EMERGENT_LLM_KEY")

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system,
        )
        chat.with_model("anthropic", "claude-sonnet-4-20250514")
        resp = await chat.send_message(UserMessage(text=prompt))
        return resp.strip()

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


def convert_language(
    scenes: list,
    project_name: str,
    source_lang: str,
    target_lang: str,
    project_id: str,
) -> dict:
    """Convert all storybook text content to target language (in batches of 5).

    Returns dict with translated scenes and metadata.
    """
    src_name = SUPPORTED_LANGS.get(source_lang, source_lang)
    tgt_name = SUPPORTED_LANGS.get(target_lang, target_lang)

    all_translated = []
    batch_size = 5

    for batch_start in range(0, len(scenes), batch_size):
        batch = scenes[batch_start:batch_start + batch_size]

        scenes_text = ""
        for s in batch:
            sn = s.get("scene_number", "?")
            scenes_text += f"\n---\nSCENE {sn}:\n"
            scenes_text += f"title: {s.get('title', '')}\n"
            scenes_text += f"description: {s.get('description', '')}\n"
            scenes_text += f"dialogue: {s.get('dialogue', '')}\n"
            scenes_text += f"emotion: {s.get('emotion', '')}\n"

        system = f"""You are an expert literary translator specializing in children's stories.
Translate from {src_name} to {tgt_name}.

RULES:
- Preserve the narrative tone, emotion, and style
- Adapt cultural references naturally for the target audience
- Keep character names unchanged (they are proper nouns)
- The translation must feel like it was ORIGINALLY written in {tgt_name}
- Return ONLY valid JSON, no extra text"""

        prompt = f"""Translate this storybook batch from {src_name} to {tgt_name}:

PROJECT: {project_name}

{scenes_text}

Return JSON array:
[{{"scene_number": N, "title": "...", "description": "...", "dialogue": "...", "emotion": "..."}}]"""

        result_text = _run_claude(system, prompt, f"lang-{project_id}-{target_lang}-b{batch_start}")

        try:
            start = result_text.find("[")
            end = result_text.rfind("]") + 1
            if start >= 0 and end > start:
                translated = json.loads(result_text[start:end])
                all_translated.extend(translated)
            else:
                logger.warning(f"Language [{project_id}]: No JSON in batch {batch_start}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Language [{project_id}]: Parse error in batch {batch_start}: {e}")

    logger.info(f"Language [{project_id}]: Translated {len(all_translated)} scenes from {src_name} to {tgt_name}")

    return {
        "translated_scenes": all_translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "translated_at": datetime.now(timezone.utc).isoformat(),
    }


def review_text_quality(
    scenes: list,
    project_name: str,
    lang: str,
    project_id: str,
) -> dict:
    """Review and improve text quality for all scenes (processes in batches of 5).

    Returns dict with improved scenes and revision notes.
    """
    lang_name = SUPPORTED_LANGS.get(lang, lang)
    all_revised = []
    all_notes = []
    overall_quality = ""

    # Process in batches of 5 scenes
    batch_size = 5
    for batch_start in range(0, len(scenes), batch_size):
        batch = scenes[batch_start:batch_start + batch_size]

        scenes_text = ""
        for s in batch:
            sn = s.get("scene_number", "?")
            scenes_text += f"\n---\nSCENE {sn}:\n"
            scenes_text += f"title: {s.get('title', '')}\n"
            scenes_text += f"description: {s.get('description', '')}\n"
            scenes_text += f"dialogue: {s.get('dialogue', '')}\n"

        system = f"""You are a senior children's book editor reviewing a storybook in {lang_name}.

Your job:
1. Fix grammar, spelling, and punctuation errors
2. Improve narrative flow and readability
3. Ensure age-appropriate language (5-10 years old)
4. Enhance descriptive passages for visual storytelling
5. Ensure emotional consistency

Return ONLY valid JSON."""

        prompt = f"""Review and improve this storybook batch:

PROJECT: {project_name}

{scenes_text}

Return JSON:
{{
  "revised_scenes": [{{"scene_number": N, "title": "...", "description": "...", "dialogue": "..."}}],
  "revision_notes": [{{"scene_number": N, "changes": "brief description"}}],
  "overall_quality": "score 1-10 with brief assessment"
}}"""

        result_text = _run_claude(system, prompt, f"review-{project_id}-b{batch_start}")

        try:
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if start >= 0 and end > start:
                review = json.loads(result_text[start:end])
                all_revised.extend(review.get("revised_scenes", []))
                all_notes.extend(review.get("revision_notes", []))
                overall_quality = review.get("overall_quality", overall_quality)
            else:
                logger.warning(f"Review [{project_id}]: No JSON in batch {batch_start}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Review [{project_id}]: Parse error in batch {batch_start}: {e}")

    logger.info(f"Review [{project_id}]: Reviewed {len(all_revised)} scenes, quality: {overall_quality}")

    return {
        "revised_scenes": all_revised,
        "revision_notes": all_notes,
        "overall_quality": overall_quality,
        "lang": lang,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
