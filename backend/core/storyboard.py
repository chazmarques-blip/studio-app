"""Storyboard Generator — Generate editable illustration panels from screenplay scenes.

Uses Gemini Nano Banana (via emergentintegrations) for panel illustration generation
and Claude (via litellm) for the AI Facilitator chat.
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

FRAME_TYPES = [
    {"label": "Plano Geral", "prompt": "ESTABLISHING SHOT — wide angle showing the full environment and all character positions from a distance"},
    {"label": "Close-up", "prompt": "CHARACTER CLOSE-UP — tightly framed on the main character's face, capturing their emotion and expression in detail"},
    {"label": "Acao", "prompt": "ACTION MOMENT — the key action, gesture, or movement happening in this scene, dynamic composition"},
    {"label": "Reacao", "prompt": "REACTION SHOT — other characters reacting to the main action, showing their emotions and body language"},
    {"label": "Angulo Dramatico", "prompt": "DRAMATIC ANGLE — low-angle or high-angle shot creating dramatic tension and visual impact"},
    {"label": "Transicao", "prompt": "TRANSITION SHOT — a moment that visually bridges to the next scene, with movement or atmospheric shift"},
]


def _generate_single_frame(
    scene: dict,
    scene_num: int,
    frame_type: dict,
    project_id: str,
    char_avatars: dict,
    avatar_cache: dict,
    character_bible: dict,
    style_dna: str,
    lang: str = "pt",
) -> bytes:
    """Generate a single storyboard frame illustration via Gemini Nano Banana.
    Returns image bytes or None on failure.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        logger.warning(f"Storyboard [{project_id}]: No EMERGENT_LLM_KEY")
        return None

    chars_in_scene = scene.get("characters_in_scene", [])
    char_desc_block = ""
    if character_bible:
        for cname in chars_in_scene:
            desc = character_bible.get(cname, "")
            if desc:
                char_desc_block += f"\n- {cname}: {desc}"

    dialogue = scene.get("dialogue", "")
    description = scene.get("description", "")
    title = scene.get("title", "")
    emotion = scene.get("emotion", "")
    lang_name = {"pt": "Portuguese", "en": "English", "es": "Spanish"}.get(lang, "Portuguese")

    prompt_text = f"""Generate ONE high-quality storyboard illustration for this animated film scene.

SCENE {scene_num}: {title}
DESCRIPTION: {description}
EMOTION: {emotion}
DIALOGUE: {dialogue}

CAMERA/FRAMING: {frame_type['prompt']}

{style_dna}

CHARACTER IDENTITY (match reference images EXACTLY):
{char_desc_block if char_desc_block else 'Use scene description for character appearance.'}

RULES:
- Generate exactly ONE single illustration (NOT a grid, NOT multiple panels)
- This is a {frame_type['label']} shot — frame the composition accordingly
- Characters MUST match reference images EXACTLY (species, face, fur color, clothing, posture)
- If a character is BIPEDAL ANTHROPOMORPHIC in the reference, show them STANDING UPRIGHT
- Style: 3D CGI Pixar quality with volumetric lighting, soft shadows, cinematic composition
- DO NOT include any text, numbers, labels, or speech bubbles
- Fill the entire image with the illustration — no borders, no margins
- Language context: {lang_name}"""

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
            system_message="You are a professional storyboard artist for animated films. Generate exactly one high-quality illustration."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

        if ref_images:
            msg = UserMessage(
                text=f"{prompt_text}\n\nReference avatar images (match EXACTLY):",
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
    style_dna: str,
    lang: str = "pt",
) -> bytes:
    """Legacy wrapper — generates the first frame (Plano Geral) as the main panel image."""
    return _generate_single_frame(
        scene=scene, scene_num=scene_num,
        frame_type=FRAME_TYPES[0],
        project_id=project_id,
        char_avatars=char_avatars, avatar_cache=avatar_cache,
        character_bible=character_bible, style_dna=style_dna, lang=lang,
    )


def _generate_all_frames_for_scene(
    scene: dict,
    scene_num: int,
    project_id: str,
    char_avatars: dict,
    avatar_cache: dict,
    character_bible: dict,
    style_dna: str,
    lang: str = "pt",
) -> list:
    """Generate 6 individual frames for a scene in parallel (3 at a time).
    Returns list of (frame_type, image_bytes) tuples.
    """
    frame_sem = threading.Semaphore(3)
    results = [None] * len(FRAME_TYPES)

    def _gen_one(idx, ft):
        with frame_sem:
            try:
                img = _generate_single_frame(
                    scene=scene, scene_num=scene_num,
                    frame_type=ft, project_id=project_id,
                    char_avatars=char_avatars, avatar_cache=avatar_cache,
                    character_bible=character_bible, style_dna=style_dna, lang=lang,
                )
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
        t.join(timeout=120)

    return [r for r in results if r is not None]


def generate_all_panels(
    tenant_id: str,
    project_id: str,
    scenes: list,
    characters: list,
    char_avatars: dict,
    production_design: dict,
    lang: str = "pt",
    upload_fn=None,
    update_fn=None,
) -> list:
    """Generate storyboard panels for all scenes. Runs in background thread.

    Args:
        upload_fn: callable(bytes, filename, content_type) -> url
        update_fn: callable(tenant_id, project_id, updates_dict)

    Returns list of panel dicts.
    """
    total = len(scenes)
    character_bible = production_design.get("character_bible", {}) if production_design else {}

    style_dna = "ART STYLE: Premium 3D CGI animation (Pixar/DreamWorks quality). Volumetric lighting, warm color grading, cinematic composition."
    style_anchors = production_design.get("style_anchors", "") if production_design else ""
    if style_anchors:
        style_dna = f"{style_dna} {style_anchors}"

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

    scene_semaphore = threading.Semaphore(2)

    def _gen_panel(scene, scene_num):
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

                frame_results = _generate_all_frames_for_scene(
                    scene=scene, scene_num=scene_num,
                    project_id=project_id,
                    char_avatars=char_avatars, avatar_cache=avatar_cache,
                    character_bible=character_bible, style_dna=style_dna, lang=lang,
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
            results[idx] = _gen_panel(s, num)

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
            timeout=60,
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
