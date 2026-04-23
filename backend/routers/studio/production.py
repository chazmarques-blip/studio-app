"""Auto-generated module from studio.py split."""
from ._shared import *
import asyncio
import requests
from fastapi import BackgroundTasks
from openai import OpenAI
import base64
import sys
import os

# Add backend root to path for kling_client import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.kling_client import KlingClient
from .sora_characters import _sora_character_ids_for_scene

def _run_async_in_thread(coro):
    """Execute async function in sync thread context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def _generate_video_with_openai_direct(client: OpenAI, prompt: str, size: str = "1280x720", duration: int = 12, image_path: str = None, max_wait: int = 600, sora_character_ids: Optional[list] = None, model: str = "sora-2") -> bytes:
    """Generate video using OpenAI SDK directly (not emergentintegrations).
    
    Args:
        client: OpenAI client instance
        prompt: Text description for the video
        size: Video resolution (1280x720, 1792x1024, 1024x1792, 1024x1024)
        duration: Video length in seconds (4, 8, or 12)
        image_path: Optional path to reference image (from Project Bible or keyframe)
        max_wait: Maximum time to wait for generation (seconds)
        sora_character_ids: Optional list of pre-registered Sora character_ids
            (POST /v1/sora/characters) to lock voice+appearance across scenes.
            Max 2 per Sora 2 limit. Safe when empty/None.
        model: "sora-2" (default, 720p) or "sora-2-pro" (1792x1024 HD support).
    
    Returns:
        Video bytes if successful, empty bytes if failed
    """
    import time
    import os
    
    img_file_handle = None
    try:
        # Prepare generation parameters
        gen_params = {
            "model": model,
            "prompt": prompt,  # Full prompt - dialogue + characters + direction
            "size": size,
            "seconds": duration
        }
        
        logger.info(f"Sora 2: Prompt length={len(prompt)} chars. First 200: {prompt[:200]}")
        
        # CHARACTER LOCK (aditive, safe): If pre-registered character_ids are provided,
        # pass them to Sora 2 so voice + appearance stay consistent across scenes.
        # Max 2 per Sora 2 limit (March 2026). Skipped when list is empty.
        if sora_character_ids:
            ids = [cid for cid in sora_character_ids if cid][:2]
            if ids:
                gen_params["characters"] = [{"id": cid} for cid in ids]
                logger.info(f"Sora 2: Character lock active — {len(ids)} character_id(s): {ids}")
        
        # Use input_reference if image path provided (Project Bible keyframe or character reference)
        # CRITICAL FIX (2026-04-03): Resize image to match video dimensions to avoid 400 error
        if image_path and os.path.exists(image_path):
            try:
                from PIL import Image
                # Parse target dimensions from size string (e.g., "1280x720")
                target_width, target_height = map(int, size.split('x'))
                
                # Resize image to match video dimensions
                img = Image.open(image_path)
                if img.size != (target_width, target_height):
                    logger.info(f"Sora 2: Resizing input_reference from {img.size} to {target_width}x{target_height}")
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    
                    # Save resized image to temp file
                    import tempfile
                    resized_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                    img.save(resized_path, format="PNG")
                    image_path = resized_path
                
                # OpenAI SDK expects a file handle, not base64 string
                img_file_handle = open(image_path, "rb")
                gen_params["input_reference"] = img_file_handle
                logger.info(f"Sora 2: Using input_reference from {image_path[:50]}... ({target_width}x{target_height})")
            except Exception as e:
                logger.warning(f"Sora 2: Failed to load/resize input_reference: {e}")
        
        # Create video generation request
        start = time.time()
        video = client.videos.create(**gen_params)
        
        # Poll for completion
        video_id = video.id
        while (time.time() - start) < max_wait:
            video_status = client.videos.retrieve(video_id)
            
            if video_status.status == "completed":
                # Download video content
                content = client.videos.download_content(video_id)
                # content is a file-like object
                video_bytes = content.read()
                return video_bytes
            
            elif video_status.status == "failed":
                error_msg = getattr(video_status, 'error', 'Unknown error')
                logger.error(f"Sora 2 generation failed: {error_msg}")
                return b""
            
            # Still processing (queued or in_progress)
            progress = getattr(video_status, 'progress', 'N/A')
            if progress != 'N/A':
                logger.debug(f"Sora 2 video {video_id[:8]} progress: {progress}%")
            time.sleep(10)  # Poll every 10 seconds
        
        # Timeout
        logger.warning(f"Sora 2 generation timeout after {max_wait}s")
        return b""
        
    except Exception as e:
        logger.error(f"Sora 2 direct generation error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return b""
    finally:
        # Clean up file handle
        if img_file_handle:
            try:
                img_file_handle.close()
            except:
                pass

def _generate_video_unified(
    prompt: str,
    engine: str = "sora",
    size: str = "1280x720",
    duration: int = 12,
    image_path: str = None,
    max_wait: int = 600,
    openai_client: Optional[OpenAI] = None,
    kling_client: Optional[KlingClient] = None,
    sora_character_ids: Optional[list] = None,
    sora_model: str = "sora-2"
) -> bytes:
    """Unified video generation supporting both Sora 2 and Kling AI
    
    Args:
        prompt: Text description for video generation
        engine: "sora" or "kling" (default: "sora")
        size: Video resolution
        duration: Video duration in seconds
        image_path: Optional reference image
        max_wait: Maximum wait time in seconds
        openai_client: OpenAI client instance (required if engine="sora")
        kling_client: Kling client instance (required if engine="kling")
        sora_character_ids: Optional list of Sora 2 character_ids for voice lock
            (Sora engine only; ignored for Kling). Max 2.
        
    Returns:
        Video bytes if successful, empty bytes if failed
    """
    if engine == "kling":
        if not kling_client:
            logger.error("Kling engine selected but kling_client not provided")
            return b""
        
        # Kling supports max 10s clips - use 10s for best quality
        kling_duration = min(duration, 10)
        logger.info(f"[FILM] Using KLING AI engine (duration={kling_duration}s)")
        return kling_client.text_to_video(
            prompt=prompt,
            image_path=image_path,
            duration=float(kling_duration),
            resolution=size,
            model="kling-v2-master",
            max_wait=max_wait
        )
    
    else:  # Default: Sora 2
        if not openai_client:
            logger.error("Sora engine selected but openai_client not provided")
            return b""
        
        logger.info(f"[FILM] Using SORA 2 engine (duration={duration}s)")
        return _generate_video_with_openai_direct(
            client=openai_client,
            prompt=prompt,
            size=size,
            duration=duration,
            image_path=image_path,
            max_wait=max_wait,
            sora_character_ids=sora_character_ids,
            model=sora_model,
        )

# ── STEP 3: Multi-Scene Production Pipeline (v3 - Per-Scene Parallel Teams) ──

def _update_scene_status(tenant_id: str, project_id: str, scene_num: int, status: str, total: int):
    """Thread-safe scene status update. Reads current state, merges, writes."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        agent_status = project.get("agent_status", {})
        scene_status = agent_status.get("scene_status", {})
        scene_status[str(scene_num)] = status
        videos_done = sum(1 for v in scene_status.values() if v == "done")
        # Progress percent: 95% during generation (last 5% reserved for concat+upload)
        progress_pct = int(min(95, round((videos_done / total) * 95))) if total else 0
        # Human-readable phase detail
        phase_map = {
            "directing": "Diretor planejando",
            "generating_video": f"Gerando vídeo da cena {scene_num}",
            "concatenating": "Concatenando filme final",
            "done": f"Cena {scene_num} pronta",
            "error": f"Erro na cena {scene_num}",
        }
        phase_detail = phase_map.get(status, status)
        agent_status.update({
            "current_scene": scene_num, "total_scenes": total,
            "phase": status if status in ("directing", "generating_video", "concatenating") else agent_status.get("phase", "running"),
            "scene_status": scene_status,
            "videos_done": videos_done,
            "progress_percent": progress_pct,
            "phase_detail": phase_detail,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        project["agent_status"] = agent_status
        _save_project(tenant_id, settings, projects)
    except Exception:
        pass


# Thread-safe lock for saving scene videos (prevents race conditions in parallel mode)
_save_video_lock = threading.Lock()


def _save_scene_video(tenant_id: str, project_id: str, scene_num: int, video_url: str, total: int, sora_prompt: str = None, keyframe_url: str = None):
    """Save a completed scene video immediately for real-time preview (thread-safe)."""
    try:
        with _save_video_lock:
            settings, projects, project = _get_project(tenant_id, project_id)
            if not project:
                return
            outputs = project.get("outputs", [])
            if not any(o.get("scene_number") == scene_num for o in outputs):
                outputs.append({
                    "id": uuid.uuid4().hex[:8], "type": "video", "url": video_url,
                    "scene_number": scene_num, "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            project["outputs"] = outputs
            
            # Also save to scene data for frontend access
            for scene in project.get("scenes", []):
                if scene.get("scene_number") == scene_num:
                    scene["video_url"] = video_url
                    if sora_prompt:
                        scene["sora_prompt"] = sora_prompt
                    if keyframe_url:
                        scene["keyframe_url"] = keyframe_url
                    break
            
            _add_milestone(project, f"video_scene_{scene_num}", f"Vídeo cena {scene_num} gerado")
            _save_project(tenant_id, settings, projects, flush_now=True)
        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
    except Exception as e:
        logger.warning(f"_save_scene_video scene {scene_num}: {e}")


def _run_multi_scene_production(tenant_id: str, project_id: str, character_avatars: dict = None):
    """v4 - Decoupled Pipeline: ALL Directors first (parallel) -> ALL Sora jobs queued.

    Architecture:
    PHASE A (Preparation - ~5s):
    ┌─ Director(Claude) Scene 1  ─┐
    ├─ Director(Claude) Scene 2  ─┤  ALL PARALLEL -> 15 Sora prompts ready
    ├─ Director(Claude) Scene N  ─┤
    └─ MusicDirector              ┘

    PHASE B (Production - priority queue):
    Sora Queue -> [1,2,3,4,5] -> [6,7,8,9,10] -> [11,12,13,14,15]
                  5 slots simultaneous

    -> FFmpeg concat -> Complete
    """
    import json as json_mod
    import tempfile
    import time as _time

    try:
        t_start = _time.time()
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        # Limit scenes if max_scenes is set
        max_scenes = project.get("max_scenes")
        if max_scenes and max_scenes > 0:
            scenes = scenes[:max_scenes]
            logger.info(f"Studio [{project_id}]: Limiting production to {len(scenes)}/{len(project.get('scenes', []))} scenes (max_scenes={max_scenes})")
        characters = project.get("characters", [])
        total = len(scenes)
        char_avatars = character_avatars or project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")

        if total == 0:
            _update_project_field(tenant_id, project_id, {"status": "error", "error": "No scenes"})
            return

        _update_project_field(tenant_id, project_id, {
            "status": "running_agents",
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "starting_teams",
                             "scene_status": {str(i+1): "queued" for i in range(total)}}
        })

        # ── Visual Style Mapping ──
        STYLE_PROMPTS = {
            "animation": "ART STYLE: High-quality 3D animation like Pixar/DreamWorks. Colorful, warm, expressive characters with large eyes. Smooth cinematic camera movements. Rich detailed environments.",
            "cartoon": "ART STYLE: Vibrant 2D cartoon style. Bold outlines, saturated colors, exaggerated expressions. Playful and fun atmosphere.",
            "anime": "ART STYLE: Japanese anime style. Detailed backgrounds, expressive eyes, dramatic lighting. Fluid motion.",
            "realistic": "ART STYLE: Cinematic photorealistic live-action. Film grain, natural lighting, professional cinematography.",
            "watercolor": "ART STYLE: Watercolor painting style. Soft edges, pastel tones, dreamy ethereal atmosphere.",
        }
        # Use animation_sub for more specific style
        animation_sub = project.get("animation_sub", "pixar_3d")
        ANIMATION_SUB_PROMPTS = {
            "pixar_3d": "ART STYLE: Premium 3D CGI animation identical to Pixar/DreamWorks (Toy Story, Shrek quality). Subsurface scattering on skin/fur, global illumination, cinematic depth of field, warm color grading. Characters with large expressive eyes, smooth rounded features. MUST maintain consistent 3D rendering across ALL scenes.",
            "cartoon_3d": "ART STYLE: Stylized 3D cartoon animation (similar to Paw Patrol, Cocomelon). Bright saturated colors, simplified shapes, thick outlines on 3D models, flat shading with cel-shading effect. Playful and vibrant. MUST maintain consistent style across ALL scenes.",
            "cartoon_2d": "ART STYLE: Classic 2D hand-drawn animation (Disney Renaissance, Studio Ghibli). Clean line art, watercolor-like coloring, fluid character animation, painted backgrounds. MUST maintain consistent 2D art style across ALL scenes.",
            "anime_2d": "ART STYLE: Japanese anime (Studio Ghibli, Makoto Shinkai quality). Detailed backgrounds with atmospheric perspective, dramatic lighting, speed lines for action, large expressive eyes. MUST maintain consistent anime style across ALL scenes.",
            "realistic": "ART STYLE: Cinematic photorealistic live-action. Shallow depth of field, film grain, natural lighting, 35mm anamorphic lens look. Professional cinematography with handheld camera feel. MUST maintain consistent photorealistic style.",
            "watercolor": "ART STYLE: Watercolor painting animation. Visible brush strokes, bleeding edges, soft pastel tones, paper texture overlay. Dreamy ethereal atmosphere. MUST maintain consistent painted style across ALL scenes.",
        }
        style_hint = ANIMATION_SUB_PROMPTS.get(animation_sub, STYLE_PROMPTS.get(visual_style, STYLE_PROMPTS["animation"]))

        # ── Shared context ──
        briefing = project.get("briefing", "")
        
        # ── Language enforcement for text in videos ──
        project_lang = project.get("language", "pt")
        LANGUAGE_MARKERS = {
            "pt": "PORTUGUESE TEXT",
            "en": "ENGLISH TEXT", 
            "es": "SPANISH TEXT",
            "fr": "FRENCH TEXT",
            "de": "GERMAN TEXT",
            "it": "ITALIAN TEXT",
            "ja": "JAPANESE TEXT",
            "zh": "CHINESE TEXT",
            "ar": "ARABIC TEXT",
            "ru": "RUSSIAN TEXT",
            "hi": "HINDI TEXT"
        }
        language_marker = LANGUAGE_MARKERS.get(project_lang, f"{project_lang.upper()} TEXT")
        logger.info(f"Studio [{project_id}]: Language enforcement: {language_marker}")

        # ── Pre-download avatars ONCE ──
        avatar_cache = {}
        for name, url in char_avatars.items():
            if url and url not in avatar_cache:
                try:
                    full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                    logger.info(f"Studio [{project_id}]: Avatar cached for {name}")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Avatar download failed for {name}: {e}")
                    avatar_cache[url] = None

        # ── Resume support - find already completed videos ──
        _, _, proj_check = _get_project(tenant_id, project_id)
        existing_outputs = proj_check.get("outputs", []) if proj_check else []
        completed_videos = {}
        for o in existing_outputs:
            sn = o.get("scene_number")
            if sn and o.get("url") and o.get("type") == "video" and sn > 0:
                completed_videos[sn] = o["url"]
        if completed_videos:
            logger.info(f"Studio [{project_id}]: Resuming - {len(completed_videos)} scenes already cached: {sorted(completed_videos.keys())}")

        # ══ PRE-PRODUCTION: Avatar Analysis + Production Design Document ══
        # Check if pre-production was already done via Preview Board
        existing_pd = project.get("agents_output", {}).get("production_design")
        existing_ad = project.get("agents_output", {}).get("avatar_descriptions")

        if existing_pd and isinstance(existing_pd, dict) and existing_pd.get("character_bible"):
            logger.info(f"Studio [{project_id}]: PRE-PRODUCTION already done via Preview Board - skipping")
            production_design = existing_pd
            avatar_descriptions = existing_ad or {}
        else:
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "pre_production",
                                 "scene_status": {str(i+1): "queued" for i in range(total)}}
            })
            logger.info(f"Studio [{project_id}]: PRE-PRODUCTION - Analyzing avatars and building production design")

            # Step 1: Analyze avatars with Claude Vision (ONE call for all avatars)
            avatar_descriptions = _run_async_in_thread(
                _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id)
            )

            # Step 2: Build Production Design Document (ONE call - replaces music, style, location, continuity planning)
            production_design = _build_production_design(
                briefing, characters, scenes, avatar_descriptions, visual_style,
                project.get("language", "pt"), project_id
            )

            _update_project_field(tenant_id, project_id, {
                "agents_output": {**project.get("agents_output", {}),
                                  "production_design": production_design,
                                  "avatar_descriptions": avatar_descriptions},
            })

        # Extract production design elements for efficient access by directors
        pd_style = production_design.get("style_anchors", style_hint)
        # ── CONTINUITY ENGINE: Build rigid Style DNA ──
        continuity_mode = project.get("continuity_mode", True)
        if continuity_mode:
            style_dna = _build_style_dna(animation_sub, production_design)
            pd_style = f"{style_dna} {pd_style}"
            logger.info(f"Studio [{project_id}]: CONTINUITY ENGINE ON - Style DNA injected ({len(style_dna)} chars)")
        pd_chars = production_design.get("character_bible", {})
        pd_locations = production_design.get("location_bible", {})
        pd_scene_dirs = {d.get("scene", 0): d for d in production_design.get("scene_directions", [])}
        pd_color = production_design.get("color_palette", {})
        pd_music = production_design.get("music_plan", [])

        t_preproduction = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: PRE-PRODUCTION complete in {t_preproduction:.1f}s - {len(pd_chars)} characters, {len(pd_locations)} locations")

        _add_milestone(project, "preproduction_done", f"Pré-produção - {t_preproduction:.0f}s")
        _update_project_field(tenant_id, project_id, {
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "pre_production_done",
                             "scene_status": {str(i+1): "queued" for i in range(total)}}
        })
        
        # ── DIALOGUE TIMELINE: Ensure all scenes have timing sync ──
        scenes_without_timeline = [s for s in scenes if not s.get("dialogue_timeline")]
        if scenes_without_timeline:
            logger.info(f"Studio [{project_id}]: {len(scenes_without_timeline)} scenes missing dialogue timeline, generating now...")
            from core.dialogue_timeline import enrich_scene_with_timeline
            
            for i, scene in enumerate(scenes):
                if not scene.get("dialogue_timeline"):
                    try:
                        enriched = enrich_scene_with_timeline(scene, project_id=project_id)
                        scenes[i] = enriched
                        beats = len(enriched.get("dialogue_timeline", []))
                        logger.info(f"Studio [{project_id}]: Scene {scene.get('scene_number')} timeline generated ({beats} beats)")
                    except Exception as e:
                        logger.warning(f"Studio [{project_id}]: Scene {scene.get('scene_number')} timeline failed: {e}")
            
            # Update project with enriched scenes
            project["scenes"] = scenes
            _save_project(tenant_id, settings, projects)
            logger.info(f"Studio [{project_id}]: Dialogue timelines generated for production sync")

        # ── Rate limiter for video generation ──
        sora_semaphore = threading.Semaphore(5)

        # ── Initialize video generation engines ──
        # Check which engine to use (default: Sora 2)
        video_engine = project.get("video_engine", "sora")  # "sora" or "kling"
        
        openai_client = None
        kling_client = None
        
        if video_engine == "kling":
            kling_client = KlingClient()
            logger.info(f"Studio [{project_id}]: Using KLING AI engine (v3)")
        else:
            # Default: Sora 2
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info(f"Studio [{project_id}]: Using SORA 2 engine (OpenAI SDK)")

        # Track budget state across threads
        budget_exhausted = threading.Event()

        def _scene_director(scene, scene_num, prev_scene=None):
            """PHASE A - Scene Director: generates Sora prompt using Production Design Bible.
            
            NEW ARCHITECTURE: The prompt is built in layers:
            1. FIXED: Style DNA (never changes)
            2. FIXED: Character identity prompts (from avatar analysis - never changes)
            3. FIXED: Original dialogue with lip sync instruction (from scene data - never changes)
            4. CONTINUITY: Previous scene context (transition_from, last dialogue)
            5. VARIABLE: Visual scene direction (camera, lighting, action) ← only this comes from Director
            """
            if scene_num in completed_videos:
                return {"scene_number": scene_num, "sora_prompt": None, "cached": True}

            chars_in_scene = scene.get("characters_in_scene", [])

            # ── LAYER 1: FIXED CHARACTER PROMPTS (from avatar analysis) ──
            # These are IMMUTABLE identity cards that NEVER change between scenes
            char_identity_blocks = []
            for name in chars_in_scene:
                # Priority: production_design character_bible > avatar_descriptions > character description
                identity = pd_chars.get(name, "")
                if not identity and avatar_descriptions:
                    av_desc = avatar_descriptions.get(name, {})
                    if isinstance(av_desc, dict):
                        identity = av_desc.get("description", "")
                        immutable = av_desc.get("immutable_traits", [])
                        if immutable:
                            identity += " IMMUTABLE TRAITS: " + ", ".join(immutable)
                    elif isinstance(av_desc, str):
                        identity = av_desc
                if not identity:
                    identity = next((ch.get('description','') for ch in characters if ch.get('name')==name), 'Unknown')
                char_identity_blocks.append(f"CHARACTER [{name}]: {identity}")
            
            char_identity_text = "\n".join(char_identity_blocks)

            # ── LAYER 2: FIXED DIALOGUE WITH LIP SYNC (from scene data) ──
            dialogue_timeline = scene.get("dialogue_timeline", [])
            # Prefer dubbed_text (richest) > dialogue (original)
            scene_dialogue = (scene.get("dubbed_text") or scene.get("dialogue", "")).strip()
            lang_full = {"pt": "Portuguese", "en": "English", "es": "Spanish"}.get(project_lang, project_lang)
            
            fixed_dialogue_block = ""
            if dialogue_timeline and len(dialogue_timeline) > 0:
                character_beats = [b for b in dialogue_timeline if b.get('speaker','').lower() not in ('narrador','narrator')]
                if character_beats:
                    timing_parts = []
                    for beat in character_beats:
                        # Optional emotion marker (e.g. [whispers], [tense]) from beat.emotion
                        emotion_tag = f"[{beat['emotion']}] " if beat.get('emotion') else ""
                        timing_parts.append(f"[{beat['start_time']:.1f}s-{beat['end_time']:.1f}s] The character [{beat['speaker']}] says: '{emotion_tag}{beat['text']}' - speaking with perfectly synchronized lip movements")
                    fixed_dialogue_block = f"\n\nDIALOGUE LIP-SYNC TIMING (ORIGINAL {lang_full.upper()} - DO NOT TRANSLATE):\n" + "\n".join(timing_parts)
            
            if not fixed_dialogue_block and scene_dialogue:
                # Parse character dialogue from dubbed_text or dialogue field
                import re as _re
                # Split by | (dubbed_text separator) or newlines
                raw_lines = scene_dialogue.replace('|', '\n').split('\n')
                lines = [l.strip() for l in raw_lines if l.strip()]
                lip_parts = []
                for line in lines[:6]:  # Max 6 dialogue lines per 12s scene
                    # Remove stage directions in parentheses/brackets at start
                    clean = _re.sub(r'^\[.*?\]\s*', '', line).strip()
                    if ':' in clean:
                        char_name = clean.split(':')[0].strip()
                        # Remove parenthetical actions from character name
                        char_name = _re.sub(r'\s*\(.*?\)\s*', '', char_name).strip()
                        speech = clean.split(':', 1)[1].strip().strip("'\"")
                        # Remove inline stage directions from speech
                        speech = _re.sub(r'\[.*?\]', '', speech).strip()
                        speech = _re.sub(r'\(.*?\)', '', speech).strip()
                        if speech and len(speech) > 2 and len(char_name) < 30:
                            lip_parts.append(f"The character [{char_name}] says: '{speech}' - speaking with perfectly synchronized lip movements")
                    elif clean and len(clean) > 5 and not clean.startswith('[') and not clean.startswith('('):
                        lip_parts.append(f"A character says: '{clean}' - speaking with perfectly synchronized lip movements")
                if lip_parts:
                    fixed_dialogue_block = f"\n\nDIALOGUE LIP-SYNC (ORIGINAL {lang_full.upper()} - DO NOT TRANSLATE):\n" + "\n".join(lip_parts)

            # ── LAYER 3: Scene-specific direction from Production Design ──
            scene_dir = pd_scene_dirs.get(scene_num, {})
            loc_key = scene_dir.get("location_key", "")
            loc_desc = pd_locations.get(loc_key, "")
            time_day = scene_dir.get("time_of_day", "afternoon")
            time_light = pd_color.get(time_day, pd_color.get("global", ""))
            cam_flow = scene_dir.get("camera_flow", scene.get("camera", ""))
            trans_note = scene_dir.get("transition_note", "")

            # ── LAYER 4: Director generates ONLY the visual action description ──
            # Build continuity context from previous scene
            continuity_ctx = ""
            if prev_scene:
                prev_title = prev_scene.get("title", "")
                prev_desc_end = prev_scene.get("description", "")[-200:]
                prev_dialogue_end = prev_scene.get("dialogue", "").strip().split("\n")[-1] if prev_scene.get("dialogue") else ""
                prev_transition_to = prev_scene.get("transition_to", "")
                transition_from = scene.get("transition_from", "")
                prev_camera = prev_scene.get("camera", "")
                # Get the visual_direction from prev scene if available (has EXIT ZONE info)
                prev_visual = prev_scene.get("_visual_direction", "")
                prev_exit = ""
                if prev_visual:
                    # Extract the 10-12s segment (EXIT ZONE)
                    import re as _re
                    exit_match = _re.search(r'10-12s?:(.+?)(?:\.|$)', prev_visual)
                    if exit_match:
                        prev_exit = exit_match.group(1).strip()
                
                continuity_ctx = f"""
[CONTINUITY FROM PREVIOUS SCENE - EDGE MIRRORING]
Previous scene ({prev_scene.get('scene_number', '?')}): "{prev_title}"
How it ended visually: {prev_desc_end}
EXIT ZONE action (last 2s): {prev_exit or prev_transition_to or 'Characters in resting position'}
Last dialogue line: {prev_dialogue_end}
Previous camera angle: {prev_camera}
How this scene connects: {transition_from}

YOUR ENTRY ZONE (0-2s) MUST:
- Show characters in the EXACT same positions as the EXIT ZONE above
- Use the SAME camera angle as previous scene ended
- Same lighting, same environment
- Characters complete the gesture/look that was starting in the EXIT ZONE
- Then SMOOTHLY transition into this scene's new action (2-4s onward)"""

            # Build audio/sfx context
            music_mood = scene.get("music_mood", "")
            sfx_notes = scene.get("sfx_notes", "")
            audio_ctx = ""
            if music_mood or sfx_notes:
                audio_ctx = f"\n[AUDIO ATMOSPHERE] Music: {music_mood}. SFX: {sfx_notes}. Reflect this mood in the visual direction."

            director_system = f"""You are a VISUAL SCENE DIRECTOR for a continuous animated film (Pixar/DreamWorks quality). Your ONLY job is to describe the VISUAL ACTION of each 12-second scene.

[RULES]
- DO NOT describe character appearances - they are already defined in CHARACTER IDENTITY blocks
- DO NOT write dialogue - it is already defined in DIALOGUE LIP-SYNC blocks  
- DO NOT modify, translate, or paraphrase the dialogue text
- ONLY describe: camera movement, lighting, character positioning, gestures, expressions, environment details, timing of actions

[DYNAMICS RULE - CRITICAL FOR ENGAGEMENT]
Every scene MUST be visually dynamic and full of life:
- Characters must be CONSTANTLY MOVING: shifting weight, tilting heads, wagging tails, fidgeting, gesturing
- At least ONE physical comedy moment per scene (stumble, slip, exaggerated reaction, double-take)
- Facial expressions change EVERY 2 seconds (surprise, joy, concern, mischief)
- Camera NEVER stays static — always subtle dolly, pan, or zoom during dialogue
- Background elements should have life too (curtain moving, light shifting, toys wobbling)
- Characters REACT to each other physically (nudge, lean in, step back, point)

[EDGE MIRRORING RULE - CRITICAL FOR SCENE CONTINUITY]
This is a CONTINUOUS FILM. Scenes must flow like one uninterrupted take:

ENTRY ZONE (0-1s): If CONTINUITY context is provided:
- SAME ENVIRONMENT: Start with EXACTLY the same character positions as the previous scene ended
- ENVIRONMENT CHANGE: Use a MOTIVATED transition — character walks through a door, camera follows character from one room to another, or a visual element (window, doorway, path) connects both spaces. NEVER hard-cut to a completely different location.

ACTION ZONE (1-11s): The main scene action with constant movement and interaction

EXIT ZONE (11-12s): Describe a CLEAR transition action:
- A character looks toward something, starts walking, or reaches for an object
- Camera begins a slow movement toward the next scene's focus
- The LAST LINE of dialogue should naturally LEAD INTO the next scene's topic
- If the NEXT SCENE is in a DIFFERENT location: character starts walking toward the exit/door/path, camera follows them, creating a natural visual bridge

[ENVIRONMENT TRANSITION RULES]
When scenes change location:
- The EXIT of scene N must MOTIVATE the move (character says "let's go outside!", stands up, walks toward door)
- The ENTRY of scene N+1 must show the CHARACTER ARRIVING (walking through door, stepping outside, entering room)
- The camera must FOLLOW the character through the transition — never just cut to a new place
- Lighting should shift GRADUALLY to match new environment (indoor warm → outdoor bright should take 2-3s)
- At least ONE visual element should be shared between both scenes (same character, same prop being carried, same clothing)

FORBIDDEN BETWEEN SCENES:
- NEVER teleport characters to new positions or locations
- NEVER hard-cut to a completely different environment without motivated movement
- NEVER change lighting abruptly

OUTPUT: Return ONLY JSON: {{"visual_direction": "Visual action description in English, max 250 words"}}

TIMING FORMAT (2-second intervals — EVERY interval must have CHARACTER MOVEMENT):
"0-1s: [ENTRY - connect to previous, characters in motion]. 1-3s: [action + reaction]. 3-5s: [physical comedy beat]. 5-7s: [interaction + gesture]. 7-9s: [dynamic action]. 9-11s: [climax of scene]. 11-12s: [EXIT - prepare transition]."

LOCATION: {loc_desc or 'As described in scene'}
TIME OF DAY: {time_day}
LIGHTING: {time_light or 'Match scene emotion'}
CAMERA: {cam_flow or 'Medium shot with gentle tracking movement'}
TRANSITION: {trans_note or 'Smooth cut'}
{continuity_ctx}{audio_ctx}
"""

            # Build personality context for visual direction
            personality_visual = ""
            for cname in chars_in_scene:
                char_data = next((c for c in characters if c.get("name") == cname), None)
                if char_data and char_data.get("personality"):
                    personality_visual += f"\n- {cname}: {char_data['personality']}"
            if personality_visual:
                personality_visual = f"\n[CHARACTER PERSONALITIES - reflect in gestures, expressions, body language]{personality_visual}\n"

            director_user = f"""SCENE {scene_num}: "{scene.get('title', '')}"
DESCRIPTION: {scene.get('description', '')}
EMOTION: {scene.get('emotion', 'neutral')}
CHARACTERS IN SCENE: {', '.join(chars_in_scene)}
{personality_visual}
Describe ONLY the visual action and camera work for this scene. Do NOT describe characters or dialogue. Make it DYNAMIC and EXPRESSIVE - characters should move, react, and show personality through body language."""

            try:
                from litellm import completion
                resp = completion(
                    model="claude-sonnet-4-5-20250929",
                    messages=[
                        {"role": "system", "content": director_system},
                        {"role": "user", "content": director_user}
                    ],
                    temperature=0.5, max_tokens=600
                )
                raw = resp.choices[0].message.content.strip()
                
                import json as _json
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                
                visual_direction = _json.loads(raw).get("visual_direction", raw)
                
            except Exception as e:
                logger.warning(f"Studio [{project_id}]: Director failed for scene {scene_num}: {e}")
                visual_direction = f"Camera slowly reveals the scene. Characters interact naturally. {cam_flow or ''}"

            # Save visual_direction on the scene so the NEXT scene's director can read the EXIT ZONE
            scene["_visual_direction"] = visual_direction

            # ══ ASSEMBLE FINAL SORA PROMPT (Layered Architecture) ══
            continuity_prompt = ""
            if prev_scene:
                transition_from = scene.get("transition_from", "")
                prev_exit = prev_scene.get("_visual_direction", "")
                import re as _re2
                exit_match = _re2.search(r'10-12s?:(.+?)(?:\.|$)', prev_exit) if prev_exit else None
                exit_text = exit_match.group(1).strip() if exit_match else ""
                
                continuity_prompt = f"""
[SCENE CONTINUITY - EDGE MIRRORING]
This scene continues DIRECTLY from the previous. The first 2 seconds must match the last 2 seconds of the previous scene.
Previous scene EXIT action: {exit_text or transition_from or 'Characters in resting position'}
Visual bridge: {transition_from}
RULE: Same character positions, same camera angle, same lighting. NO visual jumps."""

            voice_prompt = "\n[VOICE CONSISTENCY] Each character has a FIXED voice throughout the entire film. Lip movements must match the same speaking style, pace, and mouth movement pattern in every scene.\n"

            # ── LAYER 6: Cinema-style prompt (SHORT, <200 words) vs Legacy (long, all-in-one) ──
            # Official OpenAI Sora 2 guide (Feb 2026): Sora 2 ignores half of prompts >150 words.
            # When `production_quality=cinema`, we emit a compressed prompt and rely on the
            # keyframe image + Sora character_id for identity/style. Long prompt is kept for
            # backward compatibility when quality=fast (default = legacy to avoid breaking
            # existing projects mid-production).
            prod_quality = project.get("production_quality", "fast")  # "fast" (legacy) | "cinema" (compressed)

            if prod_quality == "cinema":
                # Extract only the lighting/mood line from pd_style (first sentence typically)
                pd_style_short = (pd_style.split(".")[0] + ".") if pd_style else ""
                pd_style_short = pd_style_short[:220]
                visual_short = visual_direction[:600]  # cap at ~100 words
                continuity_short = ""
                if prev_scene:
                    exit_match2 = _re2.search(r'10-12s?:(.+?)(?:\.|$)', prev_scene.get("_visual_direction", "") or "") if prev_scene.get("_visual_direction") else None
                    if exit_match2:
                        continuity_short = f"\n[CONTINUITY] First 2s match previous scene's final pose: {exit_match2.group(1).strip()[:120]}."

                sora_prompt = f"""[SHOT] Cinematic scene, 12 seconds.
[ACTION] {visual_short}{continuity_short}
{fixed_dialogue_block}
[STYLE] {pd_style_short}
[VOICES] Same character voices as previous scenes.
[TEXT] All visible text in {language_marker}."""
            else:
                sora_prompt = f"""{fixed_dialogue_block}

{char_identity_text}
{continuity_prompt}{voice_prompt}
VISUAL DIRECTION: {visual_direction}

{pd_style}

[CRITICAL: All visible text, signs, letters, and written words must be in {language_marker}]
"""

            logger.info(f"Studio [{project_id}]: Scene {scene_num} prompt assembled [{prod_quality}] - total={len(sora_prompt)} chars, style={len(pd_style)} chars, identity={len(char_identity_text)} chars, direction={len(visual_direction)} chars, dialogue={len(fixed_dialogue_block)} chars")

            return {
                "scene_number": scene_num,
                "title": scene.get("title", ""),
                "sora_prompt": sora_prompt.strip(),
                "cached": False
            }

        def _sora_render(directed_scene, scene):
            """PHASE B - Video render with Sora 2 or Kling AI.
            
            For KLING AI (5-minute scenes):
            - Calls Cinematographer to generate ultra-detailed 5-minute description
            - Uses 30 storyboard frames as visual anchors
            - Integrates dialogue timeline
            - Duration: 300 seconds
            
            For SORA 2 (12-second scenes):
            - Uses directed scene prompt directly
            - Duration: 12 seconds
            """
            scene_num = directed_scene["scene_number"]

            if directed_scene.get("cached"):
                _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                return {"scene_number": scene_num, "url": completed_videos[scene_num], "type": "video", "duration": 12}

            if budget_exhausted.is_set():
                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

            sora_prompt = directed_scene["sora_prompt"]
            chars_in_scene = scene.get("characters_in_scene", [])
            
            # ══════════════════════════════════════════════════════════════
            # KLING AI: Dual Mode - Rápido (paralelo) ou Cinema (sequencial)
            # + Audio Pipeline completa (TTS + Sonoplastia + Lip-Sync + Mix)
            # ══════════════════════════════════════════════════════════════
            if video_engine == "kling":
                production_mode = project.get("production_mode", "fast")  # "fast" or "cinema"
                logger.info(f"Studio [{project_id}]: KLING [{production_mode.upper()}] - Scene {scene_num}")
                
                # Get all storyboard frames
                kling_storyboards = project.get("kling_storyboards", [])
                all_frames = []
                for sb_scene in kling_storyboards:
                    all_frames.extend(sb_scene.get("frames", []))
                
                if not all_frames:
                    _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                    return {"scene_number": scene_num, "url": None, "error": "no_storyboard_frames"}
                
                _update_scene_status(tenant_id, project_id, scene_num, "generating_video", total)
                
                # ── STEP 1: Download all frame images as base64 ──
                _update_project_field(tenant_id, project_id, {
                    "progress_message": f"Kling AI - Baixando {len(all_frames)} imagens...",
                    "agent_status": {"phase": "generating_video", "videos_done": 0,
                                     "total_scenes": total, "total_frames": len(all_frames),
                                     "scene_status": {str(scene_num): "generating_video"}}
                })
                frame_images = {}
                for frame in all_frames:
                    fn = frame.get("frame_number", 0)
                    img_url = frame.get("image_url", "")
                    if img_url:
                        try:
                            img_resp = requests.get(img_url.split('?')[0], timeout=30)
                            if img_resp.status_code == 200:
                                frame_images[fn] = base64.b64encode(img_resp.content).decode()
                        except Exception as e:
                            logger.warning(f"  Frame {fn}: Image download failed: {e}")
                
                if len(frame_images) < 2:
                    _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                    return {"scene_number": scene_num, "url": None, "error": "insufficient_images"}
                
                def progress_cb(done, total_clips, msg):
                    _update_project_field(tenant_id, project_id, {
                        "agent_status": {"phase": "generating_video", "videos_done": done,
                                         "total_scenes": total, "total_frames": total_clips,
                                         "scene_status": {str(scene_num): "generating_video"}},
                        "progress_message": msg
                    })
                
                # ── STEP 2: Generate clips (Fast or Cinema mode) ──
                t_v = _time.time()
                if production_mode == "cinema":
                    clips = kling_client.generate_sequential_clips(
                        frames=all_frames, frame_images=frame_images,
                        clip_duration=6, model="kling-v3", mode="std",
                        max_wait=600, progress_callback=progress_cb
                    )
                else:
                    clips = kling_client.generate_parallel_clips(
                        frames=all_frames, frame_images=frame_images,
                        clip_duration=6, model="kling-v3", mode="std",
                        max_wait=600, max_concurrent=5, progress_callback=progress_cb
                    )
                
                if not clips:
                    _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                    return {"scene_number": scene_num, "url": None, "error": "no_clips_generated"}
                
                # ══════════════════════════════════════════════════════════════
                # STEP 2.5: LIP SYNC + TTS - Character voices with lip movement
                # Architecture: For each clip WITH dialogue ->
                #   1. Generate TTS audio (ElevenLabs, character voice)
                #   2. Upload clip + audio to Supabase (Kling API needs public URLs)
                #   3. Identify face -> Apply lip sync (audio baked into video)
                #   4. Download lip-synced clip (REPLACES original)
                # For clips WITHOUT dialogue -> keep original silent clip
                # After this step: lip-synced clips ALREADY HAVE dialogue audio
                # ══════════════════════════════════════════════════════════════
                import subprocess as _sp
                import tempfile as _tf
                
                voice_map = project.get("voice_map", {})
                lang = project.get("language", "pt")
                has_lip_sync = False
                
                # Stage direction markers (text with these = silence)
                STAGE_MARKERS = ["silêncio", "beat", "câmera", "camera", "olhar", "pausa",
                                 "movimento", "plano", "corte", "fade", "zoom", "som de"]
                
                if voice_map and any(f.get("dialogue_text") for f in all_frames):
                    _update_project_field(tenant_id, project_id, {
                        "progress_message": "Lip Sync - Gerando vozes e sincronizando lábios..."
                    })
                    
                    lip_synced = 0
                    lip_failed = 0
                    
                    try:
                        from .narration import _generate_narration_audio
                        
                        for clip_info in clips:
                            fn = clip_info["frame_number"]
                            clip_path = clip_info["clip_path"]
                            
                            frame = next((f for f in all_frames if f.get("frame_number") == fn), None)
                            if not frame:
                                continue
                            
                            dialogue = (frame.get("dialogue_text") or "").strip()
                            
                            # Skip non-dialogue frames
                            is_silence = (
                                not dialogue or dialogue.startswith("(") or dialogue == "..."
                                or dialogue.upper().startswith("SILÊNCIO") or dialogue.upper().startswith("BEAT")
                            )
                            if not is_silence and ":" not in dialogue:
                                if any(m in dialogue.lower() for m in STAGE_MARKERS):
                                    is_silence = True
                            if is_silence:
                                continue
                            
                            # Parse character name + clean text
                            char_name, text = "Narrador", dialogue
                            if ":" in dialogue:
                                parts = dialogue.split(":", 1)
                                if len(parts[0].strip()) < 30:
                                    char_name = parts[0].strip()
                                    text = parts[1].strip().strip("'\"")
                            
                            import re as _re
                            text = _re.sub(r'\([^)]*\)', '', text).strip()
                            text = _re.sub(r'\[.*?\]', '', text).strip()
                            if not text or len(text) < 2:
                                continue
                            
                            # Find character voice
                            matched_voice = None
                            for cname, vid in voice_map.items():
                                if char_name.lower() in cname.lower() or cname.lower() in char_name.lower():
                                    matched_voice = vid
                                    break
                            if not matched_voice:
                                matched_voice = list(voice_map.values())[0] if voice_map else None
                            if not matched_voice:
                                continue
                            
                            _update_project_field(tenant_id, project_id, {
                                "progress_message": f"Lip Sync - Frame {fn}/{len(clips)} ({char_name})"
                            })
                            
                            try:
                                # 1. Generate TTS audio
                                audio_bytes = _generate_narration_audio(
                                    text=text, voice_id=matched_voice,
                                    stability=0.5, similarity=0.75, style_val=0.0,
                                    language_code=lang
                                )
                                
                                # Get audio duration
                                audio_tmp = f"/tmp/lipsync_audio_{project_id}_{fn}.mp3"
                                with open(audio_tmp, "wb") as f:
                                    f.write(audio_bytes)
                                probe = _sp.run([
                                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "default=noprint_wrappers=1:nokey=1", audio_tmp
                                ], capture_output=True, text=True, timeout=5)
                                audio_dur_ms = int(float(probe.stdout.strip()) * 1000) if probe.returncode == 0 else 5000
                                
                                # 2. Upload clip + audio to get public URLs
                                with open(clip_path, 'rb') as f:
                                    clip_bytes = f.read()
                                clip_url = _upload_to_storage(clip_bytes, f"studio/{project_id}_ls_clip_{fn:03d}.mp4", "video/mp4")
                                audio_url = _upload_to_storage(audio_bytes, f"studio/{project_id}_ls_audio_{fn:03d}.mp3", "audio/mpeg")
                                
                                # 3. Identify face
                                face_result = kling_client.identify_face(video_url=clip_url, max_wait=60)
                                
                                if not face_result or not face_result.get("faces"):
                                    logger.info(f"  LipSync F{fn}: No faces, adding TTS as audio track instead")
                                    # Fallback: overlay TTS audio on clip via FFmpeg
                                    ls_clip = f"/tmp/lipsync_clip_{project_id}_{fn}.mp4"
                                    _sp.run([
                                        "ffmpeg", "-y", "-i", clip_path, "-i", audio_tmp,
                                        "-map", "0:v:0", "-map", "1:a:0",
                                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                                        "-shortest", "-movflags", "+faststart", ls_clip
                                    ], capture_output=True, timeout=30)
                                    if os.path.exists(ls_clip) and os.path.getsize(ls_clip) > 1000:
                                        clip_info["clip_path"] = ls_clip
                                        clip_info["has_audio"] = True
                                        lip_synced += 1
                                    else:
                                        lip_failed += 1
                                    try: os.remove(audio_tmp)
                                    except: pass
                                    continue
                                
                                session_id = face_result["session_id"]
                                face_id = face_result["faces"][0].get("face_id", "")
                                
                                # 4. Apply lip sync (audio baked into video)
                                ls_result = kling_client.lip_sync(
                                    session_id=session_id,
                                    face_id=face_id,
                                    audio_url=audio_url,
                                    sound_start_time=0,
                                    sound_end_time=min(audio_dur_ms, 6000),
                                    sound_insert_time=0,
                                    sound_volume=1.5,
                                    original_audio_volume=0.0,
                                    max_wait=180
                                )
                                
                                if ls_result and ls_result.get("video_url"):
                                    # 5. Download lip-synced clip to /tmp (NOT a tmpdir that gets deleted)
                                    ls_resp = requests.get(ls_result["video_url"], timeout=60)
                                    ls_resp.raise_for_status()
                                    ls_clip = f"/tmp/lipsync_clip_{project_id}_{fn}.mp4"
                                    with open(ls_clip, "wb") as f:
                                        f.write(ls_resp.content)
                                    clip_info["clip_path"] = ls_clip
                                    clip_info["has_audio"] = True
                                    lip_synced += 1
                                    logger.info(f"  LipSync F{fn}: SUCCESS ({len(ls_resp.content)//1024}KB)")
                                else:
                                    # Fallback: FFmpeg audio overlay
                                    ls_clip = f"/tmp/lipsync_clip_{project_id}_{fn}.mp4"
                                    _sp.run([
                                        "ffmpeg", "-y", "-i", clip_path, "-i", audio_tmp,
                                        "-map", "0:v:0", "-map", "1:a:0",
                                        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                                        "-shortest", "-movflags", "+faststart", ls_clip
                                    ], capture_output=True, timeout=30)
                                    if os.path.exists(ls_clip) and os.path.getsize(ls_clip) > 1000:
                                        clip_info["clip_path"] = ls_clip
                                        clip_info["has_audio"] = True
                                        lip_synced += 1
                                        logger.info(f"  LipSync F{fn}: Fallback FFmpeg overlay OK")
                                    else:
                                        lip_failed += 1
                                
                                try: os.remove(audio_tmp)
                                except: pass
                                    
                            except Exception as ls_err:
                                logger.warning(f"  LipSync F{fn}: Error ({ls_err}), keeping original")
                                lip_failed += 1
                        
                        has_lip_sync = lip_synced > 0
                        logger.info(f"Studio [{project_id}]: LIP SYNC complete - {lip_synced} synced, {lip_failed} failed")
                        
                    except Exception as e:
                        logger.error(f"Studio [{project_id}]: Lip sync phase error: {e}")
                        import traceback; logger.error(traceback.format_exc())
                
                # ══════════════════════════════════════════════════════════════
                # STEP 3: FFmpeg concat - Join all clips
                # When lip sync is active: use simple concat to PRESERVE audio
                # When no lip sync: can use xfade for smooth video transitions
                # ══════════════════════════════════════════════════════════════
                _update_project_field(tenant_id, project_id, {
                    "progress_message": f"Concatenando {len(clips)} clips..."
                })
                
                output_path = f"/tmp/kling_final_{project_id}.mp4"
                clip_paths = [c["clip_path"] for c in clips]
                
                # ALWAYS use simple concat (preserves audio from lip-synced clips)
                concat_list = f"/tmp/kling_concat_{project_id}.txt"
                with open(concat_list, 'w') as f:
                    for cp in clip_paths:
                        f.write(f"file '{cp}'\n")
                
                concat_result = _sp.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart", output_path
                ], capture_output=True, timeout=300)
                
                try: os.remove(concat_list)
                except: pass
                
                if concat_result.returncode != 0:
                    logger.error(f"Studio [{project_id}]: Concat failed: {concat_result.stderr.decode()[:200]}")
                
                if not os.path.exists(output_path):
                    _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                    return {"scene_number": scene_num, "url": None, "error": "concat_failed"}
                
                logger.info(f"Studio [{project_id}]: Video concatenated ({os.path.getsize(output_path)//1024}KB, lip_sync={has_lip_sync})")
                
                # ══════════════════════════════════════════════════════════════
                # STEP 4: SONOPLASTIA - Background music + SFX via Kling V2A
                # If lip sync was used: clips ALREADY have dialogue audio
                #   -> only add V2A BGM at low volume
                # If NO lip sync: generate TTS dialogue track + V2A BGM
                # ══════════════════════════════════════════════════════════════
                voice_map = project.get("voice_map", {})
                lang = project.get("language", "pt")
                
                if voice_map and any(f.get("dialogue_text") for f in all_frames):
                    import tempfile as _tf
                    tmpdir = _tf.mkdtemp(prefix="kling_audio_")
                    
                    try:
                        # ── If NO lip sync: generate TTS dialogue track ──
                        if not has_lip_sync:
                            _update_project_field(tenant_id, project_id, {
                                "progress_message": "Gerando vozes dos personagens (TTS)..."
                            })
                            
                            from .narration import _generate_narration_audio
                            STAGE_MARKERS_A = ["silêncio", "beat", "câmera", "camera", "olhar", "pausa", "movimento", "plano"]
                            clip_dur = 6.0
                            audio_segments = []
                            
                            for idx, frame in enumerate(all_frames):
                                fn = frame.get("frame_number", idx + 1)
                                dialogue = (frame.get("dialogue_text") or "").strip()
                                
                                is_silence = (
                                    not dialogue or dialogue.startswith("(") or dialogue == "..."
                                    or dialogue.upper().startswith("SILÊNCIO") or dialogue.upper().startswith("BEAT")
                                )
                                if not is_silence and ":" not in dialogue:
                                    if any(m in dialogue.lower() for m in STAGE_MARKERS_A):
                                        is_silence = True
                                
                                if is_silence:
                                    sil_path = f"{tmpdir}/frame_{fn:03d}.mp3"
                                    _sp.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                                             f"anullsrc=r=44100:cl=stereo", "-t", str(clip_dur),
                                             "-q:a", "9", "-acodec", "libmp3lame", sil_path],
                                            capture_output=True, timeout=10)
                                    audio_segments.append(sil_path)
                                    continue
                                
                                char_name, text = "Narrador", dialogue
                                if ":" in dialogue:
                                    parts = dialogue.split(":", 1)
                                    if len(parts[0]) < 30:
                                        char_name, text = parts[0].strip(), parts[1].strip().strip("'\"")
                                
                                import re as _re
                                text = _re.sub(r'\([^)]*\)', '', text).strip()
                                text = _re.sub(r'\[.*?\]', '', text).strip()
                                
                                if not text or len(text) < 2:
                                    sil_path = f"{tmpdir}/frame_{fn:03d}.mp3"
                                    _sp.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                                             f"anullsrc=r=44100:cl=stereo", "-t", str(clip_dur),
                                             "-q:a", "9", "-acodec", "libmp3lame", sil_path],
                                            capture_output=True, timeout=10)
                                    audio_segments.append(sil_path)
                                    continue
                                
                                voice_id = None
                                for cn, vid in voice_map.items():
                                    if char_name.lower() in cn.lower() or cn.lower() in char_name.lower():
                                        voice_id = vid
                                        break
                                if not voice_id:
                                    voice_id = list(voice_map.values())[0]
                                
                                try:
                                    audio_bytes = _generate_narration_audio(
                                        text=text, voice_id=voice_id,
                                        stability=0.5, similarity=0.75, style_val=0.0,
                                        language_code=lang
                                    )
                                    raw = f"{tmpdir}/frame_{fn:03d}_raw.mp3"
                                    with open(raw, "wb") as f:
                                        f.write(audio_bytes)
                                    padded = f"{tmpdir}/frame_{fn:03d}.mp3"
                                    _sp.run(["ffmpeg", "-y", "-i", raw,
                                             "-af", f"apad=whole_dur={clip_dur}", "-t", str(clip_dur),
                                             "-acodec", "libmp3lame", "-q:a", "4", padded],
                                            capture_output=True, timeout=15)
                                    audio_segments.append(padded)
                                except Exception as e:
                                    logger.warning(f"  Frame {fn} TTS error: {e}")
                                    sil_path = f"{tmpdir}/frame_{fn:03d}.mp3"
                                    _sp.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                                             f"anullsrc=r=44100:cl=stereo", "-t", str(clip_dur),
                                             "-q:a", "9", "-acodec", "libmp3lame", sil_path],
                                            capture_output=True, timeout=10)
                                    audio_segments.append(sil_path)
                            
                            # Concat TTS segments into dialogue track
                            dialogue_track = f"{tmpdir}/dialogue_full.mp3"
                            alist = f"{tmpdir}/audio_concat.txt"
                            with open(alist, 'w') as f:
                                for ap in audio_segments:
                                    f.write(f"file '{ap}'\n")
                            _sp.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist,
                                     "-c", "copy", dialogue_track], capture_output=True, timeout=60)
                            
                            logger.info(f"Studio [{project_id}]: TTS Dialogue track ready ({os.path.getsize(dialogue_track)//1024}KB)")
                            
                            # Mix dialogue into video
                            dubbed_path = f"{tmpdir}/dubbed.mp4"
                            _sp.run([
                                "ffmpeg", "-y", "-i", output_path, "-i", dialogue_track,
                                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                                "-profile:v", "baseline", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                                "-map", "0:v:0", "-map", "1:a:0", "-shortest",
                                "-movflags", "+faststart", dubbed_path
                            ], capture_output=True, timeout=180)
                            
                            if os.path.exists(dubbed_path) and os.path.getsize(dubbed_path) > 1000:
                                output_path = dubbed_path
                                logger.info(f"Studio [{project_id}]: Dubbed video ready ({os.path.getsize(dubbed_path)//1024}KB)")
                        else:
                            logger.info(f"Studio [{project_id}]: Lip sync active - skipping TTS overlay (audio already in clips)")
                        
                        # ── SONOPLASTIA: V2A Background Music + SFX ──
                        _update_project_field(tenant_id, project_id, {
                            "progress_message": "Gerando sonoplastia (música + efeitos) via Kling V2A..."
                        })
                        
                        bgm_added = False
                        try:
                            from core.kling_client import KlingClient
                            kling_v2a = KlingClient()
                            
                            # Extract 15s sample for V2A
                            v2a_sample = f"{tmpdir}/v2a_sample.mp4"
                            _sp.run([
                                "ffmpeg", "-y", "-i", output_path,
                                "-t", "15", "-an", "-c:v", "copy", v2a_sample
                            ], capture_output=True, timeout=15)
                            
                            if os.path.exists(v2a_sample) and os.path.getsize(v2a_sample) > 1000:
                                with open(v2a_sample, 'rb') as f:
                                    sample_bytes = f.read()
                                sample_url = _upload_to_storage(sample_bytes, f"studio/{project_id}_v2a_sample.mp4", "video/mp4")
                                
                                scenes = project.get("scenes", [])
                                scene_desc = (scenes[0].get("description", "") if scenes else "")[:150]
                                
                                v2a_result = kling_v2a.video_to_audio(
                                    video_url=sample_url,
                                    sfx_prompt=scene_desc or "nature sounds, gentle footsteps, birds chirping",
                                    bgm_prompt="gentle orchestral music, Pixar animation style, warm emotional, children cartoon",
                                    max_wait=180
                                )
                                
                                if v2a_result and v2a_result.get("audio_mp3_url"):
                                    sfx_resp = requests.get(v2a_result["audio_mp3_url"], timeout=60)
                                    if sfx_resp.status_code == 200 and len(sfx_resp.content) > 1000:
                                        # Save V2A audio and loop to video length
                                        v2a_short = f"{tmpdir}/v2a_short.mp3"
                                        with open(v2a_short, "wb") as f:
                                            f.write(sfx_resp.content)
                                        
                                        probe = _sp.run([
                                            "ffprobe", "-v", "error", "-show_entries", "format=duration",
                                            "-of", "default=noprint_wrappers=1:nokey=1", output_path
                                        ], capture_output=True, text=True, timeout=10)
                                        vid_dur = float(probe.stdout.strip()) if probe.returncode == 0 else 180.0
                                        
                                        v2a_full = f"{tmpdir}/v2a_looped.mp3"
                                        _sp.run([
                                            "ffmpeg", "-y", "-stream_loop", "-1", "-i", v2a_short,
                                            "-t", str(vid_dur), "-acodec", "libmp3lame", "-q:a", "4",
                                            v2a_full
                                        ], capture_output=True, timeout=30)
                                        
                                        if os.path.exists(v2a_full) and os.path.getsize(v2a_full) > 1000:
                                            # Mix BGM at low volume with existing audio
                                            bgm_mixed = f"{tmpdir}/final_with_bgm.mp4"
                                            _sp.run([
                                                "ffmpeg", "-y", "-i", output_path, "-i", v2a_full,
                                                "-filter_complex",
                                                "[0:a]volume=1.0[dialogue];[1:a]volume=0.15[bgm];[dialogue][bgm]amix=inputs=2:duration=shortest[out]",
                                                "-map", "0:v:0", "-map", "[out]",
                                                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                                                "-movflags", "+faststart", bgm_mixed
                                            ], capture_output=True, timeout=120)
                                            
                                            if os.path.exists(bgm_mixed) and os.path.getsize(bgm_mixed) > 1000:
                                                output_path = bgm_mixed
                                                bgm_added = True
                                                logger.info(f"Studio [{project_id}]: BGM mixed! ({os.path.getsize(bgm_mixed)//1024}KB)")
                                            else:
                                                logger.warning(f"Studio [{project_id}]: BGM mix FFmpeg failed")
                                else:
                                    logger.warning(f"Studio [{project_id}]: V2A returned no audio")
                        except Exception as v2a_err:
                            logger.warning(f"Studio [{project_id}]: V2A sonoplastia failed (non-fatal): {v2a_err}")
                        
                        logger.info(f"Studio [{project_id}]: Audio complete - lip_sync={has_lip_sync}, bgm={bgm_added}")
                        
                        # ── STEP 5: Multi-format export ──
                        _update_project_field(tenant_id, project_id, {
                            "progress_message": "Exportando multi-formato (YouTube, TikTok, Instagram)..."
                        })
                        
                        multi_outputs = {}
                        formats = {
                            "youtube_16x9": {"vf": "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2", "label": "YouTube 16:9"},
                            "tiktok_9x16": {"vf": "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2", "label": "TikTok 9:16"},
                            "instagram_1x1": {"vf": "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2", "label": "Instagram 1:1"},
                        }
                        
                        for fmt_key, fmt_cfg in formats.items():
                            fmt_path = f"{tmpdir}/{fmt_key}.mp4"
                            try:
                                _sp.run([
                                    "ffmpeg", "-y", "-i", output_path,
                                    "-vf", fmt_cfg["vf"],
                                    "-c:v", "libx264", "-preset", "fast", "-crf", "26",
                                    "-profile:v", "baseline", "-pix_fmt", "yuv420p",
                                    "-c:a", "aac", "-b:a", "96k", "-ac", "2",
                                    "-movflags", "+faststart", fmt_path
                                ], capture_output=True, timeout=180)
                                
                                if os.path.exists(fmt_path) and os.path.getsize(fmt_path) > 1000:
                                    with open(fmt_path, 'rb') as f:
                                        fmt_bytes = f.read()
                                    if len(fmt_bytes) < 50 * 1024 * 1024:
                                        fmt_url = _upload_to_storage(fmt_bytes, f"studio/{project_id}_{fmt_key}.mp4", "video/mp4")
                                        multi_outputs[fmt_key] = {"url": fmt_url, "label": fmt_cfg["label"]}
                                        logger.info(f"  {fmt_key}: {len(fmt_bytes)//1024}KB uploaded")
                            except Exception as e:
                                logger.warning(f"  {fmt_key} export failed: {e}")
                        
                        # ── STEP 6: Upload final video ──
                        _update_project_field(tenant_id, project_id, {
                            "progress_message": "Fazendo upload do vídeo final..."
                        })
                        
                        video_url = None
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                            file_size = os.path.getsize(output_path)
                            
                            if file_size > 48 * 1024 * 1024:
                                logger.info(f"Studio [{project_id}]: Video too large ({file_size//1024}KB), compressing...")
                                compressed_path = f"{tmpdir}/compressed_main.mp4"
                                _sp.run([
                                    "ffmpeg", "-y", "-i", output_path,
                                    "-c:v", "libx264", "-preset", "fast", "-crf", "28",
                                    "-profile:v", "baseline", "-pix_fmt", "yuv420p",
                                    "-c:a", "aac", "-b:a", "96k", "-ac", "2",
                                    "-movflags", "+faststart", compressed_path
                                ], capture_output=True, timeout=180)
                                if os.path.exists(compressed_path) and os.path.getsize(compressed_path) > 1000:
                                    output_path = compressed_path
                                    logger.info(f"Studio [{project_id}]: Compressed to {os.path.getsize(compressed_path)//1024}KB")
                            
                            with open(output_path, 'rb') as f:
                                final_video_bytes = f.read()
                            
                            final_duration = sum(c.get("duration", 6) for c in clips)
                            elapsed = _time.time() - t_v
                            
                            try:
                                filename = f"studio/{project_id}_scene_{scene_num}_kling.mp4"
                                video_url = _upload_to_storage(final_video_bytes, filename, "video/mp4")
                                logger.info(f"Studio [{project_id}]: KLING DONE - {len(clips)} clips, lip_sync={has_lip_sync}, bgm={bgm_added}, ~{final_duration:.0f}s, {elapsed:.0f}s ({len(final_video_bytes)//1024}KB)")
                            except Exception as upload_err:
                                logger.warning(f"Studio [{project_id}]: Upload failed ({len(final_video_bytes)//1024}KB): {upload_err}")
                                if multi_outputs.get("youtube_16x9", {}).get("url"):
                                    video_url = multi_outputs["youtube_16x9"]["url"]
                        
                        # Cleanup
                        import shutil
                        try: shutil.rmtree(tmpdir)
                        except: pass
                        for c in clips:
                            try: os.remove(c["clip_path"])
                            except: pass
                        
                        if video_url:
                            _save_scene_video(tenant_id, project_id, scene_num, video_url, total, sora_prompt=sora_prompt)
                            _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                            result = {"scene_number": scene_num, "url": video_url, "type": "video",
                                      "duration": final_duration, "has_audio": True,
                                      "has_lip_sync": has_lip_sync, "has_bgm": bgm_added}
                            if multi_outputs:
                                result["multi_format"] = multi_outputs
                                _update_project_field(tenant_id, project_id, {"multi_format_urls": multi_outputs})
                            return result
                        elif multi_outputs.get("youtube_16x9", {}).get("url"):
                            yt_url = multi_outputs["youtube_16x9"]["url"]
                            _save_scene_video(tenant_id, project_id, scene_num, yt_url, total, sora_prompt=sora_prompt)
                            _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                            _update_project_field(tenant_id, project_id, {"multi_format_urls": multi_outputs})
                            return {"scene_number": scene_num, "url": yt_url, "type": "video",
                                    "has_audio": True, "multi_format": multi_outputs}
                        else:
                            _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                            return {"scene_number": scene_num, "url": None, "error": "upload_failed"}
                        
                    except Exception as audio_err:
                        logger.error(f"Studio [{project_id}]: Audio/Export pipeline error: {audio_err}")
                        import traceback; logger.error(traceback.format_exc())
                        import shutil
                        try: shutil.rmtree(tmpdir)
                        except: pass
                
                # ── Fallback: No voice_map -> upload video without audio ──
                if os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        final_video_bytes = f.read()
                    
                    final_duration = sum(c.get("duration", 6) for c in clips)
                    filename = f"studio/{project_id}_scene_{scene_num}_kling.mp4"
                    video_url = _upload_to_storage(final_video_bytes, filename, "video/mp4")
                    
                    for c in clips:
                        try: os.remove(c["clip_path"])
                        except: pass
                    try: os.remove(output_path)
                    except: pass
                    
                    _save_scene_video(tenant_id, project_id, scene_num, video_url, total, sora_prompt=sora_prompt)
                    _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                    return {"scene_number": scene_num, "url": video_url, "type": "video",
                            "duration": final_duration, "has_audio": False}
                else:
                    _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                    return {"scene_number": scene_num, "url": None, "error": "output_missing"}
            
            # ══════════════════════════════════════════════════════════════
            # SORA 2: Standard 12-second video generation
            # ══════════════════════════════════════════════════════════════
            video_duration = 12

            # KEYFRAME-FIRST: If continuity mode, generate a Gemini keyframe first
            # This forces correct character identity that Sora 2 can't override
            keyframe_path = directed_scene.get("_keyframe_path")
            char_ref = _create_composite_avatar(chars_in_scene, char_avatars, avatar_cache)
            # Prefer keyframe > avatar composite
            ref_path = keyframe_path if (keyframe_path and os.path.exists(keyframe_path)) else char_ref

            _update_scene_status(tenant_id, project_id, scene_num, "waiting_sora", total)

            max_retries = 3
            last_error = None

            with sora_semaphore:
                for attempt in range(max_retries):
                    if budget_exhausted.is_set():
                        _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                        return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

                    _update_scene_status(tenant_id, project_id, scene_num, "generating_video", total)
                    t_v = _time.time()
                    try:
                        engine_name = video_engine.upper()
                        logger.info(f"Studio [{project_id}]: Scene {scene_num} {engine_name} attempt {attempt+1}/{max_retries} (dur={video_duration}s, ref_image={'Y' if ref_path else 'N'})")
                        
                        # Sora 2 Character Lock: pick up to 2 registered character_ids for this scene
                        _sora_char_ids = []
                        _sora_model = "sora-2"
                        _sora_size = "1280x720"
                        if video_engine == "sora":
                            try:
                                from .sora_characters import _sora_character_ids_for_scene
                                _sora_char_ids = _sora_character_ids_for_scene(project, scene, max_refs=2)
                                if _sora_char_ids:
                                    logger.info(f"Studio [{project_id}]: Scene {scene_num} using Sora character_ids: {_sora_char_ids}")
                            except Exception as _ce:
                                logger.warning(f"Studio [{project_id}]: character_ids lookup failed (non-fatal): {_ce}")

                            # Cinema quality → Sora 2 Pro HD (1792x1024)
                            # Default: ON for films >= 3 scenes (unless user explicitly set "fast")
                            _prod_q = project.get("production_quality")
                            if not _prod_q:
                                _prod_q = "cinema" if total >= 3 else "fast"
                            if _prod_q == "cinema":
                                _sora_model = "sora-2-pro"
                                _sora_size = "1792x1024"
                                logger.info(f"Studio [{project_id}]: Scene {scene_num} CINEMA quality → sora-2-pro @ 1792x1024")
                        
                        # Unified video generation supporting Sora 2 and Kling AI
                        video_bytes = _generate_video_unified(
                            prompt=sora_prompt,  # No truncation - dialogue must reach Sora 2 intact
                            engine=video_engine,
                            size=_sora_size if video_engine == "sora" else "1280x720",
                            duration=video_duration,  # 12s for Sora, 300s for Kling
                            image_path=ref_path,
                            max_wait=600,
                            openai_client=openai_client,
                            kling_client=kling_client,
                            sora_character_ids=_sora_char_ids or None,
                            sora_model=_sora_model,
                        )
                        elapsed = _time.time() - t_v

                        if video_bytes and len(video_bytes) > 1000:
                            filename = f"studio/{project_id}_scene_{scene_num}.mp4"
                            video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                            logger.info(f"Studio [{project_id}]: Scene {scene_num} DONE {elapsed:.0f}s ({len(video_bytes)//1024}KB)")
                            
                            # Upload keyframe to storage for reference
                            keyframe_url = None
                            if ref_path and os.path.exists(ref_path):
                                try:
                                    with open(ref_path, 'rb') as kf:
                                        keyframe_bytes = kf.read()
                                    keyframe_filename = f"studio/{project_id}_keyframe_{scene_num}.png"
                                    keyframe_url = _upload_to_storage(keyframe_bytes, keyframe_filename, "image/png")
                                except Exception:
                                    pass
                            
                            _save_scene_video(tenant_id, project_id, scene_num, video_url, total, sora_prompt=sora_prompt, keyframe_url=keyframe_url)
                            return {"scene_number": scene_num, "url": video_url, "type": "video", "duration": video_duration}
                        else:
                            sz = len(video_bytes) if video_bytes else 0
                            if elapsed < 30:
                                logger.error(f"Studio [{project_id}]: Scene {scene_num} BUDGET EXHAUSTED ({sz}B in {elapsed:.0f}s)")
                                budget_exhausted.set()
                                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                                return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}
                            else:
                                last_error = f"empty_video_{sz}B"
                                logger.warning(f"Studio [{project_id}]: Scene {scene_num} attempt {attempt+1} empty ({sz}B in {elapsed:.0f}s)")
                                if attempt < max_retries - 1:
                                    _time.sleep(10)

                    except Exception as ve:
                        err_str = str(ve).lower()
                        elapsed = _time.time() - t_v
                        if "budget" in err_str or "exceeded" in err_str or "insufficient" in err_str:
                            logger.error(f"Studio [{project_id}]: Scene {scene_num} BUDGET ERROR: {ve}")
                            budget_exhausted.set()
                            _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                            return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

                        last_error = str(ve)[:200]
                        is_retryable = any(k in err_str for k in ["disconnect", "server", "timeout", "connection", "reset", "eof"])
                        if is_retryable and attempt < max_retries - 1:
                            wait = 15 * (attempt + 1)
                            logger.warning(f"Studio [{project_id}]: Scene {scene_num} Sora attempt {attempt+1} FAIL: {ve}. Retry in {wait}s...")
                            _time.sleep(wait)
                            continue
                        else:
                            logger.warning(f"Studio [{project_id}]: Scene {scene_num} Sora FAIL after {attempt+1} attempts: {ve}")

                # All retries exhausted
                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                return {"scene_number": scene_num, "url": None, "type": "video", "error": last_error or "unknown"}

        # ══ PHASE A: DIRECTORS (Production-Design-guided) ══
        from concurrent.futures import ThreadPoolExecutor, as_completed

        directed_scenes = []
        scene_map = {s.get("scene_number", i+1): s for i, s in enumerate(scenes)}

        if video_engine == "sora" and continuity_mode:
            # SORA 2 CINEMA: Directors run SEQUENTIALLY so each gets prev_scene context
            logger.info(f"Studio [{project_id}]: PHASE A - Launching {total} Scene Directors SEQUENTIALLY (continuity mode)")
            sorted_scenes = sorted(scenes, key=lambda s: s.get("scene_number", 0))
            prev_s = None
            for s in sorted_scenes:
                sn = s.get("scene_number", 0)
                result = _scene_director(s, sn, prev_scene=prev_s)
                directed_scenes.append(result)
                cached = result.get("cached", False)
                logger.info(f"Studio [{project_id}]: Director {result['scene_number']}/{total} done {'(CACHED)' if cached else ''}")
                prev_s = s  # Current scene becomes prev for next iteration
        else:
            # KLING / Non-continuity: Directors run in PARALLEL (no prev_scene needed)
            logger.info(f"Studio [{project_id}]: PHASE A - Launching {total} Scene Directors (parallel, PD-guided)")
            with ThreadPoolExecutor(max_workers=total) as executor:
                director_futures = {
                    executor.submit(_scene_director, s, s.get("scene_number", i+1)): (i, s)
                    for i, s in enumerate(scenes)
                }
                for future in as_completed(director_futures):
                    result = future.result()
                    directed_scenes.append(result)
                    cached = result.get("cached", False)
                    logger.info(f"Studio [{project_id}]: Director {result['scene_number']}/{total} done {'(CACHED)' if cached else ''}")

        music_data = {"plan": pd_music, "mood": "cinematic"}

        t_phase_a = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: PHASE A complete in {t_phase_a:.1f}s - {len(directed_scenes)} prompts ready")

        # Sort by scene number for ordered Sora queue
        directed_scenes.sort(key=lambda x: x["scene_number"])

        # ══ PHASE B: SORA RENDERS ══
        # Both modes now use parallel rendering (semaphore controls Sora 2 concurrency)
        # Continuity mode: generates keyframes first (parallel), then renders in parallel
        # Normal mode: renders directly in parallel
        scene_videos = []
        scene_map = {s.get("scene_number", i+1): s for i, s in enumerate(scenes)}

        if continuity_mode:
            logger.info(f"Studio [{project_id}]: PHASE B (CONTINUITY) - Keyframe + rendering")

            # B1: Generate keyframes
            keyframe_paths = []

            def _generate_keyframe_for_scene(ds):
                """Generate keyframe for a single scene (thread-safe)."""
                sn = ds["scene_number"]
                if ds.get("cached"):
                    return ds
                sd = scene_map.get(sn, scenes[0])
                chars_in = sd.get("characters_in_scene", [])
                kf_path = None
                for kf_attempt in range(3):
                    kf_path = _generate_scene_keyframe(
                        ds["sora_prompt"], char_avatars, avatar_cache,
                        chars_in, project_id, sn,
                        character_bible=pd_chars
                    )
                    if kf_path:
                        break
                    logger.warning(f"Studio [{project_id}]: Keyframe retry {kf_attempt+1}/3 for scene {sn}")
                    _time.sleep(2)
                if kf_path:
                    ds["_keyframe_path"] = kf_path
                    keyframe_paths.append(kf_path)
                else:
                    logger.warning(f"Studio [{project_id}]: Keyframe FAILED all retries for scene {sn} - using avatar fallback")
                return ds

            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_keyframes",
                                 "videos_done": 0, "scene_status": {str(ds["scene_number"]): "queued" for ds in directed_scenes}}
            })

            if video_engine == "sora":
                # SORA 2 CINEMA SEQUENTIAL: Only generate keyframe for scene 1
                # Scenes 2+ will use the last frame from the previous clip
                first_ds = next((ds for ds in sorted(directed_scenes, key=lambda x: x["scene_number"]) if not ds.get("cached")), None)
                if first_ds:
                    logger.info(f"Studio [{project_id}]: Cinema Sequential - generating keyframe for scene {first_ds['scene_number']} only")
                    _generate_keyframe_for_scene(first_ds)
                    logger.info(f"Studio [{project_id}]: Scene 1 keyframe ready - starting sequential pipeline")
                else:
                    logger.info(f"Studio [{project_id}]: All scenes cached, skipping keyframe generation")
            else:
                # KLING: Generate ALL keyframes in parallel (Gemini, 5 concurrent)
                with ThreadPoolExecutor(max_workers=5) as executor:
                    kf_futures = {executor.submit(_generate_keyframe_for_scene, ds): ds["scene_number"] for ds in directed_scenes}
                    for future in as_completed(kf_futures):
                        sn = kf_futures[future]
                        future.result()
                        logger.info(f"Studio [{project_id}]: Keyframe {sn}/{total} ready")
                logger.info(f"Studio [{project_id}]: All {total} keyframes ready")

            # B2: Render videos
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_video",
                                 "videos_done": 0, "scene_status": {str(ds["scene_number"]): "waiting_sora" for ds in directed_scenes}}
            })
            
            if video_engine == "sora":
                # SEQUENTIAL rendering for Sora 2 Cinema Mode
                logger.info(f"Studio [{project_id}]: SORA 2 CINEMA MODE - Rendering {total} scenes SEQUENTIALLY for continuity")
                last_frame_path = None
                
                # Check which scenes already have videos (for "produce missing" mode)
                existing_videos = {o["scene_number"]: o for o in project.get("outputs", []) 
                                   if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")}
                
                for ds in sorted(directed_scenes, key=lambda x: x["scene_number"]):
                    sn = ds["scene_number"]
                    sc = scene_map.get(sn, scenes[0])
                    
                    # Skip scenes that already have a video (reuse existing)
                    if sn in existing_videos:
                        existing = existing_videos[sn]
                        scene_videos.append({"scene_number": sn, "url": existing["url"]})
                        logger.info(f"Studio [{project_id}]: Scene {sn} CACHED (already has video)")
                        
                        # Extract last frame from existing video for continuity
                        try:
                            import tempfile as _tf
                            vid_resp = requests.get(existing["url"], timeout=60)
                            if vid_resp.status_code == 200:
                                tmp_vid = _tf.mktemp(suffix=".mp4")
                                with open(tmp_vid, 'wb') as f:
                                    f.write(vid_resp.content)
                                last_frame_path = f"/tmp/cinema_lastframe_{project_id}_{sn}.jpg"
                                import subprocess as _sp
                                _sp.run([
                                    "ffmpeg", "-y", "-sseof", "-0.1", "-i", tmp_vid,
                                    "-frames:v", "1", "-q:v", "2", last_frame_path
                                ], capture_output=True, timeout=15)
                                try: os.remove(tmp_vid)
                                except: pass
                        except Exception as e:
                            logger.warning(f"Studio [{project_id}]: Failed to extract last frame from cached scene {sn}: {e}")
                        
                        _update_scene_status(tenant_id, project_id, sn, "done", total)
                        videos_done += 1
                        continue
                    
                    # Override keyframe with last frame from previous clip (Cinema continuity)
                    if last_frame_path and os.path.exists(last_frame_path):
                        ds["_keyframe_path"] = last_frame_path
                        logger.info(f"Studio [{project_id}]: Scene {sn} using last frame from scene {sn-1} for continuity")
                    
                    _update_project_field(tenant_id, project_id, {
                        "progress_message": f"Cinema Mode - Gerando cena {sn}/{total}..."
                    })
                    
                    result = _sora_render(ds, sc)
                    scene_videos.append(result)
                    
                    # Extract last frame from generated video for next scene
                    if result.get("url"):
                        try:
                            import tempfile as _tf
                            vid_resp = requests.get(result["url"], timeout=60)
                            if vid_resp.status_code == 200:
                                tmp_vid = _tf.mktemp(suffix=".mp4")
                                with open(tmp_vid, 'wb') as f:
                                    f.write(vid_resp.content)
                                
                                last_frame_path = f"/tmp/cinema_lastframe_{project_id}_{sn}.jpg"
                                import subprocess as _sp
                                _sp.run([
                                    "ffmpeg", "-y", "-sseof", "-0.1", "-i", tmp_vid,
                                    "-frames:v", "1", "-q:v", "2", last_frame_path
                                ], capture_output=True, timeout=15)
                                
                                try: os.remove(tmp_vid)
                                except: pass
                                
                                if os.path.exists(last_frame_path) and os.path.getsize(last_frame_path) > 1000:
                                    logger.info(f"Studio [{project_id}]: Extracted last frame from scene {sn} ({os.path.getsize(last_frame_path)//1024}KB)")
                                else:
                                    last_frame_path = None
                        except Exception as e:
                            logger.warning(f"Studio [{project_id}]: Failed to extract last frame from scene {sn}: {e}")
                            last_frame_path = None
                    
                    done = len([v for v in scene_videos if v.get("url")])
                    _update_project_field(tenant_id, project_id, {
                        "agent_status": {"current_scene": sn, "total_scenes": total,
                                         "phase": "generating_video", "videos_done": done,
                                         "scene_status": {str(v["scene_number"]): ("done" if v.get("url") else "error") for v in scene_videos}}
                    })
                    logger.info(f"Studio [{project_id}]: Cinema Progress {done}/{total} (scene {sn})")
                
                # Cleanup cinema frames
                for i in range(1, total + 1):
                    try: os.remove(f"/tmp/cinema_lastframe_{project_id}_{i}.jpg")
                    except: pass
            else:
                # PARALLEL rendering for Kling (no continuity needed)
                with ThreadPoolExecutor(max_workers=total) as executor:
                    sora_futures = {
                        executor.submit(_sora_render, ds, scene_map.get(ds["scene_number"], scenes[0])): ds["scene_number"]
                        for ds in directed_scenes
                    }
                    for future in as_completed(sora_futures):
                        result = future.result()
                        scene_videos.append(result)
                        done = len([v for v in scene_videos if v.get("url")])
                        _update_project_field(tenant_id, project_id, {
                            "agent_status": {"current_scene": result["scene_number"], "total_scenes": total,
                                             "phase": "generating_video", "videos_done": done,
                                             "scene_status": {str(v["scene_number"]): ("done" if v.get("url") else "error") for v in scene_videos}}
                        })
                        logger.info(f"Studio [{project_id}]: Progress {done}/{total} (scene {result['scene_number']})")

            # Cleanup keyframe files
            for kf in keyframe_paths:
                try:
                    os.unlink(kf)
                except OSError:
                    pass
        else:
            logger.info(f"Studio [{project_id}]: PHASE B - Queueing {total} Sora 2 renders (5 slots, parallel)")

            with ThreadPoolExecutor(max_workers=total) as executor:
                sora_futures = {
                    executor.submit(_sora_render, ds, scene_map.get(ds["scene_number"], scenes[0])): ds["scene_number"]
                    for ds in directed_scenes
                }

                for future in as_completed(sora_futures):
                    result = future.result()
                    scene_videos.append(result)
                    done = len([v for v in scene_videos if v.get("url")])
                    sn = result.get("scene_number", "?")
                    if result.get("url"):
                        logger.info(f"Studio [{project_id}]: Progress {done}/{total} (scene {sn} OK)")
                    elif result.get("error"):
                        logger.warning(f"Studio [{project_id}]: Scene {sn} FAILED: {result.get('error','')}")

        t_prod = _time.time() - t_start
        successful = len([v for v in scene_videos if v.get("url")])
        budget_errors = len([v for v in scene_videos if "budget" in (v.get("error") or "")])
        logger.info(f"Studio [{project_id}]: ALL SCENES done in {t_prod:.0f}s ({t_prod/60:.1f}min) - {successful}/{total} OK, {budget_errors} budget errors")

        # Save production data
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["agents_output"] = {**project.get("agents_output", {}),
                                        "music_director": music_data,
                                        "production_design": production_design,
                                        "avatar_descriptions": avatar_descriptions}
            _add_milestone(project, "preproduction_complete", f"Pré-produção inteligente - {t_preproduction:.0f}s")
            _add_milestone(project, "agents_complete", f"Produção paralela - {t_prod:.0f}s")
            _save_project(tenant_id, settings, projects)

        # Cleanup avatars
        for path in avatar_cache.values():
            if path:
                try:
                    os.unlink(path)
                except OSError:
                    pass

        # ── Concatenate Videos ──
        successful_videos = sorted(
            [sv for sv in scene_videos if sv.get("url")],
            key=lambda x: x["scene_number"]
        )
        final_url = None

        if len(successful_videos) > 1:
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "concatenating",
                                 "videos_done": len(successful_videos)}
            })
            logger.info(f"Studio [{project_id}]: Concatenating {len(successful_videos)} videos...")
            try:
                # Default: cinema ON for films >= 3 scenes (unless user explicitly set "fast")
                _quality = project.get("production_quality")
                if not _quality:
                    _quality = "cinema" if len(successful_videos) >= 3 else "fast"
                _cinema = _quality == "cinema"
                final_url = _concatenate_videos(successful_videos, project_id, cinema_quality=_cinema)
            except Exception as ce:
                logger.error(f"Studio [{project_id}]: Concat error: {ce}")
        elif len(successful_videos) == 1:
            final_url = successful_videos[0]["url"]

        # ── Save Final Results ──
        outputs = []
        for sv in sorted(scene_videos, key=lambda x: x.get("scene_number", 0)):
            if sv.get("url"):
                outputs.append({
                    "id": uuid.uuid4().hex[:8], "type": "video", "url": sv["url"],
                    "scene_number": sv["scene_number"], "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        if final_url and len(successful_videos) > 1:
            outputs.insert(0, {
                "id": uuid.uuid4().hex[:8], "type": "video", "url": final_url,
                "scene_number": 0, "label": "complete",
                "duration": len(successful_videos) * 12,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["outputs"] = outputs
            project["scene_videos"] = scene_videos
            project["status"] = "complete"
            project["agent_status"] = {
                "current_scene": total, "total_scenes": total, "phase": "complete",
                "videos_done": len(successful_videos),
                "scene_status": {str(sv["scene_number"]): ("done" if sv.get("url") else "error") for sv in scene_videos},
            }
            _add_milestone(project, "videos_generated", f"Vídeos gerados - {len(successful_videos)} cenas")
            if final_url:
                _add_milestone(project, "film_complete", f"Filme completo - {len(successful_videos)*12}s")
            _save_project(tenant_id, settings, projects)

        t_total = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: COMPLETE! {len(successful_videos)} videos in {t_total:.0f}s ({t_total/60:.1f}min)")

    except Exception as e:
        logger.error(f"Studio [{project_id}] pipeline error: {e}")
        _update_project_field(tenant_id, project_id, {
            "status": "error", "error": str(e)[:500],
        })


def _concatenate_videos(scene_videos: list, project_id: str, crossfade_duration: float = 1.0, cinema_quality: bool = False) -> str:
    """Download scene videos, concatenate with FFmpeg crossfade, compress for upload, upload result.
    
    Args:
        scene_videos: List of {scene_number, url} dicts
        project_id: Project ID for logging
        crossfade_duration: Seconds of crossfade between clips (0 = hard cut)
    """
    import tempfile

    # Ensure FFmpeg is available
    if not _ensure_ffmpeg():
        logger.error(f"Studio [{project_id}]: FFmpeg unavailable, cannot concatenate")
        return None

    tmpdir = tempfile.mkdtemp()
    files = []

    for i, sv in enumerate(scene_videos):
        local_path = f"{tmpdir}/scene_{i:03d}.mp4"
        urllib.request.urlretrieve(sv["url"], local_path)
        files.append(local_path)
        logger.info(f"Studio [{project_id}]: Downloaded scene {sv.get('scene_number')} ({os.path.getsize(local_path)//1024}KB)")

    output_path = f"{tmpdir}/final_{project_id}.mp4"

    # Calculate total input size to decide compression strategy
    total_input_size = sum(os.path.getsize(fp) for fp in files)
    total_input_mb = total_input_size / (1024 * 1024)
    num_scenes = len(files)
    logger.info(f"Studio [{project_id}]: Concat {num_scenes} scenes, total input {total_input_mb:.1f}MB, crossfade={crossfade_duration}s")

    # ── CROSSFADE CONCATENATION ──
    # Uses xfade filter for smooth video transitions + acrossfade for audio
    use_crossfade = crossfade_duration > 0 and num_scenes >= 2 and num_scenes <= 15
    
    if use_crossfade:
        try:
            # Get duration of each clip
            clip_durations = []
            for fp in files:
                probe = subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", fp
                ], capture_output=True, text=True, timeout=10)
                dur = float(probe.stdout.strip()) if probe.returncode == 0 else 12.0
                clip_durations.append(dur)
            
            # Build xfade filter chain
            # For N clips: N-1 xfade transitions
            # Each transition: offset = sum of previous durations - (crossfade_count * crossfade_duration)
            inputs = []
            for fp in files:
                inputs.extend(["-i", fp])
            
            # Video xfade + audio crossfade (keeps Sora 2 native audio)
            v_filters = []
            a_filters = []
            cumulative_offset = 0
            
            for i in range(num_scenes - 1):
                cumulative_offset += clip_durations[i] - crossfade_duration
                
                if i == 0:
                    v_in = "[0:v]"
                    a_in = "[0:a]"
                else:
                    v_in = f"[vx{i-1}]"
                    a_in = f"[ax{i-1}]"
                
                v_out = f"[vx{i}]" if i < num_scenes - 2 else "[vout]"
                a_out = f"[ax{i}]" if i < num_scenes - 2 else "[aout]"
                
                v_filters.append(f"{v_in}[{i+1}:v]xfade=transition=fade:duration={crossfade_duration}:offset={cumulative_offset:.2f}{v_out}")
                a_filters.append(f"{a_in}[{i+1}:a]acrossfade=d={crossfade_duration}:c1=tri:c2=tri{a_out}")
            
            filter_complex = ";".join(v_filters + a_filters)
            
            # Cinema preset: CRF 18, medium preset, 256k audio (vs fast CRF 23, 128k)
            _crf = "18" if cinema_quality else "23"
            _preset = "medium" if cinema_quality else "fast"
            _abr = "256k" if cinema_quality else "128k"
            # Loudness normalization (broadcast standard -16 LUFS, true peak -1.5 dBTP)
            _af_loudnorm = "loudnorm=I=-16:TP=-1.5:LRA=11"

            cmd_xfade = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", filter_complex,
                "-map", "[vout]", "-map", "[aout]",
                "-af", _af_loudnorm,
                "-c:v", "libx264", "-preset", _preset, "-crf", _crf,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", _abr,
                "-movflags", "+faststart",
                output_path
            ]
            
            result = subprocess.run(cmd_xfade, capture_output=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"Studio [{project_id}]: Crossfade concat successful ({num_scenes - 1} transitions)")
            else:
                logger.warning(f"Studio [{project_id}]: Crossfade failed, falling back to simple concat. Error: {result.stderr.decode()[:200]}")
                use_crossfade = False
        except Exception as e:
            logger.warning(f"Studio [{project_id}]: Crossfade error: {e}, falling back to simple concat")
            use_crossfade = False
    
    if not use_crossfade:
        # ── SIMPLE CONCATENATION (fallback or >30 scenes) ──
        concat_file = f"{tmpdir}/concat.txt"
        with open(concat_file, 'w') as f:
            for fp in files:
                f.write(f"file '{fp}'\n")

        # For small total inputs (<40MB), try stream copy first
        if total_input_mb < 40:
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-movflags", "+faststart",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=120)

            if result.returncode != 0:
                cmd_reencode = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", concat_file,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "28",
                    "-c:a", "aac", "-b:a", "128k",
                    "-movflags", "+faststart",
                    output_path
                ]
                subprocess.run(cmd_reencode, capture_output=True, timeout=300)
        else:
            # For large inputs, re-encode with adaptive CRF based on scene count
            crf = min(35, 26 + num_scenes)  # More scenes = more compression
            resolution = "1280:720" if num_scenes <= 10 else "960:540"
            audio_bitrate = "128k" if num_scenes <= 10 else "96k"
            cmd_reencode = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                "-vf", f"scale={resolution}",
                "-c:a", "aac", "-b:a", audio_bitrate,
                "-movflags", "+faststart",
                output_path
            ]
            subprocess.run(cmd_reencode, capture_output=True, timeout=900)

    # Check file size - if > 45MB, apply aggressive compression
    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    logger.info(f"Studio [{project_id}]: Concatenated video size: {file_size//1024//1024}MB ({file_size//1024}KB)")

    if file_size > 45 * 1024 * 1024:
        compressed_path = f"{tmpdir}/final_{project_id}_compressed.mp4"
        # Calculate target bitrate for ~40MB output
        try:
            probe = subprocess.run(
                ["ffmpeg", "-i", output_path, "-f", "null", "-"],
                capture_output=True, timeout=60
            )
            duration_match = None
            for line in probe.stderr.decode().split('\n'):
                if 'Duration:' in line:
                    parts = line.split('Duration:')[1].split(',')[0].strip().split(':')
                    duration_match = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    break
        except Exception:
            duration_match = num_scenes * 12  # estimate 12s per scene

        if duration_match and duration_match > 0:
            target_bitrate = int((40 * 8 * 1024) / duration_match)  # kbps for 40MB
            cmd_compress = [
                "ffmpeg", "-y", "-i", output_path,
                "-c:v", "libx264", "-preset", "medium",
                "-b:v", f"{target_bitrate}k", "-maxrate", f"{int(target_bitrate*1.5)}k",
                "-bufsize", f"{target_bitrate*2}k",
                "-vf", "scale=960:540",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                compressed_path
            ]
        else:
            cmd_compress = [
                "ffmpeg", "-y", "-i", output_path,
                "-c:v", "libx264", "-preset", "medium", "-crf", "35",
                "-vf", "scale=960:540",
                "-c:a", "aac", "-b:a", "96k",
                "-movflags", "+faststart",
                compressed_path
            ]
        result = subprocess.run(cmd_compress, capture_output=True, timeout=600)
        if result.returncode == 0 and os.path.exists(compressed_path):
            new_size = os.path.getsize(compressed_path)
            logger.info(f"Studio [{project_id}]: Compressed {file_size//1024//1024}MB -> {new_size//1024//1024}MB")
            output_path = compressed_path
            file_size = new_size

    # If still too large (> 90MB), skip upload and return None
    if file_size > 90 * 1024 * 1024:
        logger.warning(f"Studio [{project_id}]: Final video still too large ({file_size//1024//1024}MB), skipping concat upload")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    with open(output_path, 'rb') as f:
        video_bytes = f.read()

    filename = f"studio/{project_id}_final.mp4"
    try:
        url = _upload_to_storage(video_bytes, filename, "video/mp4")
    except Exception as e:
        logger.error(f"Studio [{project_id}]: Upload failed: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)

    return url


@router.post("/start-production")
async def start_production(req: StartProductionRequest, tenant=Depends(get_current_tenant)):
    """Start multi-scene production pipeline in background."""
    settings, projects, project = _get_project(tenant["id"], req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.get("scenes"):
        raise HTTPException(status_code=400, detail="No scenes defined. Use the Screenwriter first.")

    # Persist character avatars, visual style, and video engine
    if req.character_avatars:
        project["character_avatars"] = req.character_avatars
    if req.visual_style:
        project["visual_style"] = req.visual_style
    project["video_engine"] = req.video_engine  # Save engine choice
    if req.max_scenes:
        project["max_scenes"] = req.max_scenes
    logger.info(f"Studio [{req.project_id}]: start_production - video_engine='{req.video_engine}', max_scenes={req.max_scenes} (from request)")

    project["status"] = "starting"
    project["error"] = None
    total = len(project.get("scenes", []))
    project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "starting"}
    _add_milestone(project, "production_started", f"Produção iniciada - {total} cenas")
    if req.character_avatars:
        _add_milestone(project, "avatars_linked", f"Avatares vinculados - {len(req.character_avatars)} personagens")
    
    # When re-producing, clear previous outputs so engine generates fresh
    if project.get("outputs"):
        logger.info(f"Studio [{req.project_id}]: Clearing {len(project.get('outputs', []))} previous outputs for fresh production")
        project["outputs"] = []
    
    _save_project(tenant["id"], settings, projects, flush_now=True)
    
    # Invalidate cache to ensure background thread reads fresh data
    try:
        from core.cache import project_cache
        project_cache.invalidate(tenant["id"])
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")

    # Use saved character_avatars (merge request + saved)
    char_avatars = {**project.get("character_avatars", {}), **req.character_avatars}

    thread = threading.Thread(
        target=_run_multi_scene_production,
        args=(tenant["id"], req.project_id, char_avatars),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "project_id": req.project_id, "total_scenes": total}



@router.post("/projects/{project_id}/full-production")
async def full_production(
    project_id: str,
    background_tasks: BackgroundTasks,
    tenant=Depends(get_current_tenant),
    max_scenes: int = None
):
    """One-click full production: Dialogues -> Video (Kling) -> Audio (TTS) -> Multi-format export.
    
    Orchestrates all phases automatically in background.
    Optional: ?max_scenes=15 to limit number of scenes produced.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.get("scenes"):
        raise HTTPException(status_code=400, detail="No scenes defined")
    
    video_engine = project.get("video_engine", "kling")
    
    # Validate based on engine
    if video_engine == "kling":
        storyboards = project.get("kling_storyboards", [])
        all_frames = []
        for sb in storyboards:
            all_frames.extend(sb.get("frames", []))
        if not all_frames:
            raise HTTPException(status_code=400, detail="No storyboard frames. Generate storyboard first.")
    else:
        # Sora 2: only needs scenes
        if not project.get("scenes"):
            raise HTTPException(status_code=400, detail="No scenes defined. Use the Screenwriter first.")
    
    # Save max_scenes limit if provided
    if max_scenes and max_scenes > 0:
        project["max_scenes"] = max_scenes
        logger.info(f"Studio [{project_id}]: full-production limited to {max_scenes} scenes")
    else:
        project.pop("max_scenes", None)  # Remove limit if not specified
    
    project["full_production_status"] = "starting"
    project["progress_message"] = "Iniciando produção completa..."
    _save_project(tenant["id"], settings, projects, flush_now=True)
    
    background_tasks.add_task(
        _run_full_production_pipeline,
        tenant["id"], project_id
    )
    
    return {"status": "started", "message": "Full production pipeline started"}


def _run_full_production_pipeline(tenant_id: str, project_id: str):
    """Background: Dialogues -> Video -> Audio -> Export
    
    PIPELINE SEPARATION:
    - KLING: Storyboard frames -> 30 parallel I2V clips -> Kling Lip Sync -> TTS -> V2A BGM -> Concat -> Export
    - SORA 2: Dialogue in prompt -> Sora 2 generates video WITH native lip sync -> TTS audio overlay -> V2A BGM -> Export
    These pipelines MUST NOT interfere with each other.
    """
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        
        voice_map = project.get("voice_map", {})
        video_engine = project.get("video_engine", "kling")
        production_mode = project.get("production_mode", "fast")
        
        logger.info(f"FullProd [{project_id}]: Starting pipeline - engine={video_engine}, mode={production_mode}")
        
        # ══════════════════════════════════════════════════════════════
        # KLING PIPELINE: Storyboard-based production
        # ══════════════════════════════════════════════════════════════
        if video_engine == "kling":
            # ── PHASE 1: Generate frame dialogues for TTS + Lip Sync ──
            storyboards = project.get("kling_storyboards", [])
            all_frames = []
            for sb in storyboards:
                all_frames.extend(sb.get("frames", []))
            
            # Only regenerate dialogues if not locked
            dialogue_locked = project.get("dialogue_locked", False)
            has_dialogues = any(f.get("dialogue_text") and ":" in f.get("dialogue_text", "") for f in all_frames)
            
            if not dialogue_locked or not has_dialogues:
                logger.info(f"FullProd [{project_id}]: PHASE 1 - Generating clean character dialogues...")
                _update_project_field(tenant_id, project_id, {
                    "full_production_status": "dialogues",
                    "progress_message": "Fase 1/4 - Gerando diálogos dos personagens..."
                })
                _generate_kling_dialogues(tenant_id, project_id, project, all_frames, storyboards)
            else:
                logger.info(f"FullProd [{project_id}]: PHASE 1 - Dialogues locked, skipping regeneration")
            
            # ── PHASE 2: Auto-assign voices ──
            if not voice_map:
                _auto_assign_voices(tenant_id, project_id, project)
                settings, projects, project = _get_project(tenant_id, project_id)
                voice_map = project.get("voice_map", {})
            
            # ── PHASE 3: Video Production (Kling clips + Lip Sync + Concat + V2A + Export) ──
            logger.info(f"FullProd [{project_id}]: PHASE 3 - Starting Kling video production ({production_mode})...")
            _update_project_field(tenant_id, project_id, {
                "full_production_status": "video",
                "progress_message": f"Fase 2/4 - Produzindo vídeo Kling ({production_mode})..."
            })
            
            project["video_engine"] = "kling"
            project["production_mode"] = production_mode
            project["status"] = "starting"
            project["error"] = None
            project["outputs"] = []
            _save_project(tenant_id, settings, projects, flush_now=True)
            from core.cache import project_cache
            project_cache.invalidate(tenant_id)
            
            character_avatars = project.get("character_avatars", {})
            _run_multi_scene_production(tenant_id, project_id, character_avatars)
            
            # Kling pipeline handles its own audio (Lip Sync + TTS + V2A + Multi-format) inside _sora_render
            # No need for separate audio overlay phase
            
        # ══════════════════════════════════════════════════════════════
        # SORA 2 PIPELINE: Prompt-based production with native lip sync
        # ══════════════════════════════════════════════════════════════
        else:
            # ── PHASE 1: Sora 2 uses dialogue_timeline in the prompt for native lip sync ──
            # Dialogues are part of scene data (dialogue, dialogue_timeline)
            # NOT from kling_storyboards - Sora 2 has its own prompt system
            logger.info(f"FullProd [{project_id}]: PHASE 1 - Sora 2 pipeline (lip sync via prompt)...")
            _update_project_field(tenant_id, project_id, {
                "full_production_status": "dialogues",
                "progress_message": "Fase 1/3 - Preparando diálogos para Sora 2 (lip sync nativo)..."
            })
            
            # ── PHASE 2: Auto-assign voices for TTS audio track ──
            if not voice_map:
                _auto_assign_voices(tenant_id, project_id, project)
                settings, projects, project = _get_project(tenant_id, project_id)
                voice_map = project.get("voice_map", {})
            
            # ── PHASE 3: Video Production (Sora 2 with native lip sync in prompt) ──
            logger.info(f"FullProd [{project_id}]: PHASE 2 - Starting Sora 2 video production...")
            _update_project_field(tenant_id, project_id, {
                "full_production_status": "video",
                "progress_message": "Fase 2/3 - Sora 2 gerando vídeo com lip sync nativo..."
            })
            
            project["video_engine"] = "sora"
            project["status"] = "starting"
            project["error"] = None
            project["outputs"] = []
            _save_project(tenant_id, settings, projects, flush_now=True)
            from core.cache import project_cache
            project_cache.invalidate(tenant_id)
            
            character_avatars = project.get("character_avatars", {})
            _run_multi_scene_production(tenant_id, project_id, character_avatars)
            
            # ── PHASE 4: Audio overlay (TTS voices + V2A BGM) ──
            # Sora 2 generates video with visual lip sync but NO actual audio
            # We need TTS audio for the spoken words + V2A for background music
            settings, projects, project = _get_project(tenant_id, project_id)
            if not project:
                return
            
            outputs = project.get("outputs", [])
            has_video = any(o.get("type") == "video" and o.get("url") for o in outputs)
            
            if has_video and voice_map:
                logger.info(f"FullProd [{project_id}]: PHASE 3 - Generating Sora 2 audio overlay (TTS + V2A)...")
                _update_project_field(tenant_id, project_id, {
                    "full_production_status": "audio",
                    "progress_message": "Fase 3/3 - Gerando audio (vozes + sonoplastia)..."
                })
                
                _generate_sora2_audio_overlay(tenant_id, project_id)
                
                logger.info(f"FullProd [{project_id}]: Audio overlay complete")
        
        # ══ DONE ══
        _update_project_field(tenant_id, project_id, {
            "full_production_status": "complete",
            "progress_message": "Produção completa finalizada!"
        }, flush_now=True)
        
        logger.info(f"FullProd [{project_id}]: ALL PHASES COMPLETE!")
        
    except Exception as e:
        logger.error(f"FullProd [{project_id}]: Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        _update_project_field(tenant_id, project_id, {
            "full_production_status": "error",
            "progress_message": f"Erro na produção: {str(e)[:100]}"
        })



def _generate_sora2_audio_overlay(tenant_id: str, project_id: str):
    """Add background music on top of Sora 2 native audio.
    
    Uses ElevenLabs Music API to generate an original soundtrack matching the story,
    then mixes it at low volume with the native Sora 2 audio (voices + lip sync).
    Falls back to Kling V2A if ElevenLabs Music fails.
    """
    import subprocess
    import tempfile
    import shutil
    
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        
        scenes = project.get("scenes", [])
        max_scenes = project.get("max_scenes")
        if max_scenes and max_scenes > 0:
            scenes = scenes[:max_scenes]
        
        outputs = project.get("outputs", [])
        video_output = next((o for o in outputs if o.get("type") == "video" and o.get("scene_number", -1) == 0), None)
        if not video_output:
            video_output = next((o for o in outputs if o.get("type") == "video" and o.get("url")), None)
        if not video_output or not video_output.get("url"):
            logger.warning(f"Sora2Audio [{project_id}]: No video output found, skipping")
            return
        
        video_url = video_output["url"]
        logger.info(f"Sora2Audio [{project_id}]: Adding music overlay to native Sora 2 audio — {len(scenes)} scenes")
        
        tmpdir = tempfile.mkdtemp(prefix="sora2_audio_")
        
        try:
            # Download video (already has native Sora 2 audio)
            _update_project_field(tenant_id, project_id, {
                "progress_message": "Baixando vídeo para adicionar trilha sonora..."
            })
            video_path = f"{tmpdir}/video.mp4"
            vid_resp = requests.get(video_url, timeout=120)
            vid_resp.raise_for_status()
            with open(video_path, "wb") as f:
                f.write(vid_resp.content)
            
            # Get video duration
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ], capture_output=True, text=True, timeout=10)
            vid_dur = float(probe.stdout.strip()) if probe.returncode == 0 else len(scenes) * 12.0
            logger.info(f"Sora2Audio [{project_id}]: Video duration: {vid_dur:.1f}s")
            
            # ══ STEP 1: Generate original soundtrack via ElevenLabs Music ══
            music_track = None
            try:
                _update_project_field(tenant_id, project_id, {
                    "progress_message": "Compondo trilha sonora original (ElevenLabs Music)..."
                })
                
                # Build music prompt from project context
                briefing = project.get("briefing", "")[:200]
                all_moods = [s.get("music_mood", "") for s in scenes if s.get("music_mood")]
                mood_text = ", ".join(set(all_moods))[:100] if all_moods else "warm, hopeful, adventurous"
                lang = project.get("language", "pt")
                
                music_prompt = (
                    f"Instrumental orchestral soundtrack for a children's animated story (Pixar/DreamWorks quality). "
                    f"Story: {briefing}. "
                    f"Mood: {mood_text}. "
                    f"Style: Warm orchestral with playful woodwinds, gentle strings, soft percussion. "
                    f"For ages 3-8. No vocals, no lyrics. Cinematic, emotional, family-friendly."
                )
                
                # ElevenLabs Music: max 5 minutes (300000ms)
                music_length_ms = min(int(vid_dur * 1000), 300000)
                # Minimum 3 seconds
                music_length_ms = max(music_length_ms, 3000)
                
                logger.info(f"Sora2Audio [{project_id}]: ElevenLabs Music — generating {music_length_ms//1000}s track")
                logger.info(f"Sora2Audio [{project_id}]: Music prompt: {music_prompt[:150]}...")
                
                from elevenlabs import ElevenLabs as ElevenLabsClient
                el_client = ElevenLabsClient(api_key=ELEVENLABS_API_KEY)
                
                track_stream = el_client.music.compose(
                    prompt=music_prompt,
                    music_length_ms=music_length_ms
                )
                
                music_data = b""
                for chunk in track_stream:
                    music_data += chunk
                
                if len(music_data) > 1000:
                    music_track = f"{tmpdir}/elevenlabs_music.mp3"
                    with open(music_track, "wb") as f:
                        f.write(music_data)
                    logger.info(f"Sora2Audio [{project_id}]: ElevenLabs Music generated — {len(music_data)//1024}KB")
                else:
                    logger.warning(f"Sora2Audio [{project_id}]: ElevenLabs Music returned empty audio")
                    
            except Exception as e:
                logger.warning(f"Sora2Audio [{project_id}]: ElevenLabs Music failed: {e}")
            
            # ══ STEP 1b: Fallback to Kling V2A if ElevenLabs Music failed ══
            if not music_track:
                try:
                    _update_project_field(tenant_id, project_id, {
                        "progress_message": "Gerando sonoplastia (V2A fallback)..."
                    })
                    kling = KlingClient()
                    v2a_sample = f"{tmpdir}/v2a_sample.mp4"
                    subprocess.run([
                        "ffmpeg", "-y", "-i", video_path,
                        "-t", "20", "-c", "copy", v2a_sample
                    ], capture_output=True, timeout=15)
                    
                    if os.path.exists(v2a_sample) and os.path.getsize(v2a_sample) > 1000:
                        with open(v2a_sample, 'rb') as f:
                            sample_bytes = f.read()
                        sample_url = _upload_to_storage(sample_bytes, f"studio/{project_id}_sora_v2a_sample.mp4", "video/mp4")
                        
                        all_sfx = [s.get("sfx_notes", "") for s in scenes[:5] if s.get("sfx_notes")]
                        sfx_prompt = "; ".join(all_sfx)[:150] if all_sfx else "ambient sounds, gentle atmosphere"
                        bgm_prompt = f"Music mood: {mood_text}. Pixar-style orchestral, warm emotional, children animation"
                        
                        v2a_result = kling.video_to_audio(
                            video_url=sample_url, sfx_prompt=sfx_prompt,
                            bgm_prompt=bgm_prompt, max_wait=180
                        )
                        
                        if v2a_result and v2a_result.get("audio_mp3_url"):
                            sfx_resp = requests.get(v2a_result["audio_mp3_url"], timeout=60)
                            if sfx_resp.status_code == 200:
                                v2a_short = f"{tmpdir}/sfx_bgm_short.mp3"
                                with open(v2a_short, "wb") as f:
                                    f.write(sfx_resp.content)
                                
                                music_track = f"{tmpdir}/v2a_looped.mp3"
                                subprocess.run([
                                    "ffmpeg", "-y", "-stream_loop", "-1", "-i", v2a_short,
                                    "-t", str(vid_dur), "-acodec", "libmp3lame", "-q:a", "4",
                                    music_track
                                ], capture_output=True, timeout=30)
                                
                                if not (os.path.exists(music_track) and os.path.getsize(music_track) > 1000):
                                    music_track = None
                                else:
                                    logger.info(f"Sora2Audio [{project_id}]: V2A fallback track ready ({os.path.getsize(music_track)//1024}KB)")
                except Exception as e:
                    logger.warning(f"Sora2Audio [{project_id}]: V2A fallback also failed: {e}")
            
            # ══ STEP 2: Mix music with native Sora 2 audio ══
            if music_track and os.path.exists(music_track):
                _update_project_field(tenant_id, project_id, {
                    "progress_message": "Mixando trilha sonora com áudio do vídeo..."
                })
                final_path = f"{tmpdir}/final_mixed.mp4"
                
                merge_cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path, "-i", music_track,
                    "-filter_complex",
                    "[0:a]volume=1.0[native];[1:a]volume=0.15[bgm];[native][bgm]amix=inputs=2:duration=shortest[aout]",
                    "-c:v", "copy", "-map", "0:v:0", "-map", "[aout]",
                    "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-movflags", "+faststart", final_path
                ]
                
                merge_result = subprocess.run(merge_cmd, capture_output=True, timeout=120)
                
                if merge_result.returncode != 0:
                    logger.error(f"Sora2Audio: Music mix failed: {merge_result.stderr.decode()[:200]}")
                    _update_project_field(tenant_id, project_id, {
                        "audio_generation_status": "complete",
                        "progress_message": "Vídeo pronto (sem trilha sonora extra)"
                    })
                    return
                
                # Upload final
                with open(final_path, "rb") as f:
                    final_bytes = f.read()
                
                filename = f"studio/{project_id}_sora2_final.mp4"
                final_url = _upload_to_storage(final_bytes, filename, "video/mp4")
                
                logger.info(f"Sora2Audio [{project_id}]: DONE — {len(final_bytes)//1024}KB (native audio + music)")
                
                for o in outputs:
                    if o.get("type") == "video":
                        o["url"] = final_url
                        o["has_audio"] = True
                        o["has_music"] = True
                        break
                
                _update_project_field(tenant_id, project_id, {
                    "outputs": outputs,
                    "audio_generation_status": "complete",
                    "progress_message": "Trilha sonora original aplicada ao filme!"
                }, flush_now=True)
            else:
                logger.info(f"Sora2Audio [{project_id}]: No music track generated — keeping native Sora 2 audio only")
                _update_project_field(tenant_id, project_id, {
                    "audio_generation_status": "complete",
                    "progress_message": "Vídeo pronto com áudio nativo Sora 2!"
                })
            
        finally:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass
    
    except Exception as e:
        logger.error(f"Sora2Audio [{project_id}]: Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        _update_project_field(tenant_id, project_id, {
            "audio_generation_status": "error",
            "progress_message": f"Erro audio: {str(e)[:100]}"
        })
        

def _generate_kling_dialogues(tenant_id, project_id, project, all_frames, storyboards):
    """Generate clean character dialogues for Kling storyboard frames."""
    try:
        scenes = project.get("scenes", [])
        scene_dialogue = scenes[0].get("dialogue", "") if scenes else ""
        synopsis = project.get("synopsis", project.get("briefing", ""))
        characters = project.get("characters", [])
        char_names = [c.get("name", "") for c in characters]
        lang = project.get("language", "pt")
        
        frame_context = []
        for f in all_frames:
            frame_context.append(f"Frame {f.get('frame_number')}: {f.get('time_start','')}-{f.get('time_end','')}: {f.get('key_action', f.get('image_prompt','')[:80])}")
        
        prompt = f"""You are a professional dialogue writer for an animated video for children (Pixar-style).

SYNOPSIS: {synopsis[:500]}
CHARACTERS: {', '.join(char_names)}
ORIGINAL SCRIPT (distribute ALL of this dialogue across ALL 30 frames):
{scene_dialogue[:3000]}

STORYBOARD FRAMES (30 frames x 6 seconds = 3 minutes):
{chr(10).join(frame_context)}

CRITICAL RULES:
1. EVERY SINGLE FRAME MUST have spoken dialogue - NO silent frames allowed
2. Format EVERY line as: "CharacterName: 'What they say'" - ALWAYS include character name
3. NEVER include stage directions, camera notes, descriptions, or actions
4. NEVER write "(silêncio)" - every frame needs a character speaking
5. DISTRIBUTE the original script across ALL 30 frames evenly
6. Each frame: SHORT dialogue (max 2 sentences, ~5 seconds of speech)
7. Characters: {', '.join(char_names)} - alternate between them naturally
8. Language: {lang}
9. ALL 30 frames MUST have dialogue - if the script runs out, add natural reactions, comments, or transitions
10. Frames 1-3: Introduction/greeting from characters
11. Frames 4-27: Main content from the script
12. Frames 28-30: Goodbye/conclusion from characters

MANDATORY FORMAT for EVERY frame:
"CharacterName: 'spoken words here'"

Return ONLY a JSON array with EXACTLY 30 items:
[{{"frame_number": 1, "dialogue_text": "Ash: 'Oi pessoal!'"}}]"""

        from litellm import completion
        resp = completion(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.5, max_tokens=6000)
        result_text = resp.choices[0].message.content.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        import json as _json
        dialogues = _json.loads(result_text)
        dialogue_map = {d["frame_number"]: d["dialogue_text"] for d in dialogues if "frame_number" in d}
        
        # Clean up stage directions
        STAGE_DIRECTION_MARKERS = [
            "SILÊNCIO", "BEAT", "câmera", "Camera", "CAMERA", "olhar", "pausa",
            "movimento", "plano", "corte", "fade", "close-up", "wide shot",
            "slow motion", "enquadramento", "travelling", "zoom"
        ]
        
        cleaned_count = 0
        for fn, text in list(dialogue_map.items()):
            has_char_prefix = ":" in text and len(text.split(":")[0]) < 30
            is_stage_direction = any(marker.lower() in text.lower() for marker in STAGE_DIRECTION_MARKERS)
            is_silence = text.startswith("(") or not text.strip()
            
            if is_stage_direction and not has_char_prefix:
                dialogue_map[fn] = "(silêncio)"
                cleaned_count += 1
            elif not has_char_prefix and not is_silence and text.strip():
                default_char = char_names[fn % len(char_names)] if char_names else "Narrador"
                dialogue_map[fn] = f"{default_char}: '{text.strip()}'"
                cleaned_count += 1
        
        # Fill missing frames
        missing_frames = [fn for fn in range(1, 31) if not dialogue_map.get(fn, "") or dialogue_map.get(fn, "").startswith("(")]
        if missing_frames and char_names:
            transition_lines = [
                "Que divertido, não é?", "Vamos continuar!", "Olha só isso!",
                "Incrível, né?", "Adoro isso!", "Que legal!",
                "Pessoal, prestem atenção!", "Essa é boa!", "Concordo totalmente!",
            ]
            for idx, fn_miss in enumerate(missing_frames):
                char = char_names[idx % len(char_names)]
                line = transition_lines[idx % len(transition_lines)]
                dialogue_map[fn_miss] = f"{char}: '{line}'"
        
        for sb in storyboards:
            for frame in sb.get("frames", []):
                fn = frame.get("frame_number")
                if fn in dialogue_map:
                    frame["dialogue_text"] = dialogue_map[fn]
        
        _update_project_field(tenant_id, project_id, {"kling_storyboards": storyboards}, flush_now=True)
        with_dialogue = sum(1 for fn in range(1, 31) if dialogue_map.get(fn, "").strip() and not dialogue_map.get(fn, "").startswith("("))
        logger.info(f"FullProd [{project_id}]: Dialogues: {with_dialogue}/30 with speech, {cleaned_count} cleaned/filled")
    except Exception as e:
        logger.error(f"FullProd [{project_id}]: Dialogue generation failed: {e}")


def _auto_assign_voices(tenant_id, project_id, project):
    """Auto-assign ElevenLabs voices to characters."""
    logger.info(f"FullProd [{project_id}]: Auto-assigning voices...")
    _update_project_field(tenant_id, project_id, {"progress_message": "Atribuindo vozes aos personagens..."})
    try:
        from pipeline.config import ELEVENLABS_VOICES
        characters = project.get("characters", [])
        auto_map = {}
        for i, char in enumerate(characters):
            if i < len(ELEVENLABS_VOICES):
                auto_map[char.get("name", f"Char{i}")] = ELEVENLABS_VOICES[i]["id"]
        if auto_map:
            _update_project_field(tenant_id, project_id, {"voice_map": auto_map}, flush_now=True)
            logger.info(f"FullProd [{project_id}]: Auto-assigned {len(auto_map)} voices")
    except Exception as e:
        logger.error(f"FullProd [{project_id}]: Voice assignment failed: {e}")
        _update_project_field(tenant_id, project_id, {
            "full_production_status": "error",
            "progress_message": f"Erro: {str(e)[:100]}"
        })



@router.post("/projects/{project_id}/stop-production")
async def stop_production(project_id: str, tenant=Depends(get_current_tenant)):
    """Stop ongoing production and reset to storyboard step.
    
    This allows users to review storyboards before continuing to production.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Stop production by resetting status
    previous_status = project.get("status", "unknown")
    project["status"] = "scripting"  # Reset to pre-production state
    project["agent_status"] = {}
    project["error"] = None
    
    _add_milestone(project, "production_stopped", f"Produção parada pelo usuário (estava: {previous_status})")
    _save_project(tenant["id"], settings, projects)
    
    logger.info(f"Studio [{project_id}]: Production STOPPED by user (was: {previous_status})")
    
    return {
        "status": "stopped",
        "message": "Production stopped. You can now review storyboards.",
        "previous_status": previous_status
    }


# ── Per-Scene Regeneration ──

def _regenerate_single_scene(tenant_id: str, project_id: str, scene_num: int, custom_prompt: str = None):
    """Regenerate a single scene video using the same pipeline logic."""
    import time as _time
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        # Get scenes FIRST before using it
        scenes = project.get("scenes", [])
        characters = project.get("characters", [])
        char_avatars = project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")
        outputs = project.get("outputs", [])  # CRITICAL FIX: Get outputs from project
        total = len(scenes)

        # REMOVED: Concurrency check (now in endpoint before thread creation)
        
        # CRITICAL FIX (2026-04-04): Use TOTAL scenes in project, not just 1
        # This ensures progress bar shows correctly (e.g., "1 of 6" not "1 of 1")
        total_scenes = len(scenes)
        _update_scene_status(tenant_id, project_id, scene_num, "directing", total=total_scenes)
        
        # Add detailed progress message
        _update_project_field(tenant_id, project_id, {
            "progress_message": f"Cena {scene_num}: Claude Director analisando e refinando prompt..."
        })
        
        logger.info(f"Studio [{project_id}]: Scene {scene_num} regeneration started - status set to 'directing' ({scene_num}/{total_scenes})")

        scene = next((s for s in scenes if s.get("scene_number") == scene_num), None)
        if not scene:
            logger.error(f"Studio [{project_id}]: Scene {scene_num} not found for regeneration")
            return

        _update_scene_status(tenant_id, project_id, scene_num, "directing", total)

        # Load Production Design from project (if available from previous production)
        agents_output = project.get("agents_output", {})
        production_design = agents_output.get("production_design", {})
        pd_chars = production_design.get("character_bible", {})
        pd_locations = production_design.get("location_bible", {})
        pd_style = production_design.get("style_anchors", "")
        pd_color = production_design.get("color_palette", {})
        pd_scene_dirs = {d.get("scene", 0): d for d in production_design.get("scene_directions", [])}

        STYLE_PROMPTS = {
            "animation": "ART STYLE: High-quality 3D animation like Pixar/DreamWorks. Colorful, warm, expressive characters with large eyes. Smooth cinematic camera movements. Rich detailed environments.",
            "cartoon": "ART STYLE: Vibrant 2D cartoon style. Bold outlines, saturated colors, exaggerated expressions.",
            "anime": "ART STYLE: Japanese anime style. Detailed backgrounds, expressive eyes, dramatic lighting.",
            "realistic": "ART STYLE: Cinematic photorealistic live-action. Film grain, natural lighting.",
            "watercolor": "ART STYLE: Watercolor painting style. Soft edges, pastel tones, dreamy atmosphere.",
        }
        style_hint = pd_style or STYLE_PROMPTS.get(visual_style, STYLE_PROMPTS["animation"])

        briefing = project.get("briefing", "")
        
        # ── Language enforcement for text in videos ──
        project_lang = project.get("language", "pt")
        LANGUAGE_MARKERS = {
            "pt": "PORTUGUESE TEXT",
            "en": "ENGLISH TEXT", 
            "es": "SPANISH TEXT",
            "fr": "FRENCH TEXT",
            "de": "GERMAN TEXT",
            "it": "ITALIAN TEXT",
            "ja": "JAPANESE TEXT",
            "zh": "CHINESE TEXT",
            "ar": "ARABIC TEXT",
            "ru": "RUSSIAN TEXT",
            "hi": "HINDI TEXT"
        }
        language_marker = LANGUAGE_MARKERS.get(project_lang, f"{project_lang.upper()} TEXT")

        # Use custom prompt instruction if provided (injected into scene, not replacement)
        if custom_prompt:
            scene = {**scene, "description": f"{scene.get('description', '')}\n\n[USER INSTRUCTION - MUST FOLLOW]: {custom_prompt}"}
            logger.info(f"Studio [{project_id}]: Scene {scene_num} regen with instruction: {custom_prompt[:100]}")

        chars_in_scene = scene.get("characters_in_scene", [])

        # Use canonical descriptions from Production Design if available
        if pd_chars:
            char_descs = "\n".join([
                f"- {name}: {pd_chars.get(name, next((ch.get('description','') for ch in characters if ch.get('name')==name), ''))}"
                for name in chars_in_scene
            ])
            scene_dir = pd_scene_dirs.get(scene_num, {})
            loc_key = scene_dir.get("location_key", "")
            loc_desc = pd_locations.get(loc_key, "")
            time_day = scene_dir.get("time_of_day", "afternoon")
            time_light = pd_color.get(time_day, pd_color.get("global", ""))

            director_system = f"""You are a SCENE DIRECTOR for Sora 2 video generation.
MANDATORY STYLE (include VERBATIM): {style_hint}

[RULE] ABSOLUTE RULE - DO NOT MODIFY APPROVED CONTENT:
- The DESCRIPTION, DIALOGUE, and EMOTION below were APPROVED by the content creator
- PRESERVE the EXACT story, meaning, actions, and dialogue - do NOT rewrite or reinterpret
- Your job is ONLY to add VISUAL details (camera, lighting, character appearance, timing)
- NEVER change what happens - only describe HOW it looks visually
- The DIALOGUE must appear WORD FOR WORD in the lip-sync instruction

[FILM] CRITICAL LIP-SYNC INSTRUCTION:
- If the scene has DIALOGUE, you MUST include the EXACT dialogue text in the sora_prompt
- Format: "The [character description] says: '[exact dialogue text]' - speaking with perfectly synchronized lip movements, mouth moving naturally with each word"
- This ensures Sora 2 generates video WITH audio AND lip-sync matching the spoken text

[LANG] LANGUAGE MARKER:
- At the END of your sora_prompt, add: "Any visible text in {language_marker}."

[WARNING] DIALOGUE LANGUAGE: Visual descriptions in ENGLISH, but DIALOGUE TEXT in lip-sync instructions MUST stay in ORIGINAL LANGUAGE ({language_marker}) - do NOT translate dialogue.

Return ONLY JSON: {{"sora_prompt": "ONE detailed English paragraph for Sora 2, max 250 words"}}
RULES: Describe characters by EXACT PHYSICAL APPEARANCE, NEVER by name. Include environment, lighting, atmosphere, actions, camera. ALWAYS include exact dialogue (in original language) with lip-sync instruction."""

            director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}
CHARACTERS (by appearance): {char_descs}
LOCATION: {loc_desc}
TIME: {time_day} - {time_light}
CAMERA: {scene_dir.get('camera_flow', scene.get('camera', ''))}
"""
        else:
            # Fallback: no production design available
            scene_chars = "; ".join([f"{ch['name']}: {ch.get('description','')}" for ch in characters if ch.get("name") in chars_in_scene])
            director_system = f"""You are a SCENE DIRECTOR for Sora 2. {style_hint}

[RULE] ABSOLUTE RULE - DO NOT MODIFY APPROVED CONTENT:
- The DESCRIPTION, DIALOGUE, and EMOTION below were APPROVED by the content creator
- PRESERVE the EXACT story, meaning, actions, and dialogue - do NOT rewrite or reinterpret
- Your job is ONLY to add VISUAL details (camera, lighting, character appearance, timing)
- NEVER change what happens - only describe HOW it looks visually

[FILM] CRITICAL LIP-SYNC INSTRUCTION:
- If the scene has DIALOGUE, you MUST include the EXACT dialogue text in the sora_prompt
- Format: "The [character description] says: '[exact dialogue text]' - speaking with perfectly synchronized lip movements, mouth moving naturally with each word"
- This ensures Sora 2 generates video WITH audio AND lip-sync matching the spoken text

[LANG] LANGUAGE MARKER:
- At the END of your sora_prompt, add: "Any visible text in {language_marker}."

[WARNING] DIALOGUE LANGUAGE: Visual descriptions in ENGLISH, but DIALOGUE TEXT in lip-sync instructions MUST stay in ORIGINAL LANGUAGE ({language_marker}) - do NOT translate dialogue.

Return ONLY JSON: {{"sora_prompt": "Detailed English paragraph for Sora 2. Max 250 words. ALWAYS include exact dialogue (in original language) with lip-sync instruction."}}
"""
            director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')} | Camera: {scene.get('camera','')}
Characters: {scene_chars}
Story: {briefing[:300]}
"""

        try:
            result_text = _call_claude_sync(director_system, director_prompt, max_tokens=1000)
            data = _parse_json(result_text) or {}
            sora_prompt_base = data.get("sora_prompt", scene.get("description", ""))
            
            dialogue_timeline = scene.get("dialogue_timeline", [])
            logger.info(f"Studio [{project_id}]: DEBUG - dialogue_timeline beats: {len(dialogue_timeline)}")
            
            if dialogue_timeline and len(dialogue_timeline) > 0:
                character_beats = [beat for beat in dialogue_timeline if beat.get('speaker', '').lower() not in ('narrador', 'narrator')]
                
                if character_beats:
                    import re as _re
                    clean_base = _re.sub(r"The .{5,80} says: '[^']*'[^.]*\.", "", sora_prompt_base).strip()
                    clean_base = _re.sub(r"DIALOGUE TIMING:.*$", "", clean_base).strip()
                    
                    timing_text = ""
                    for beat in character_beats:
                        speaker = beat.get('speaker', 'Character')
                        text = beat.get('text', '')
                        start = beat.get('start_time', 0)
                        end = beat.get('end_time', 0)
                        timing_text += f"[{start:.1f}s-{end:.1f}s] {speaker} says: '{text}' - "
                    
                    sora_prompt = f"{clean_base} DIALOGUE TIMING (ORIGINAL LANGUAGE - DO NOT TRANSLATE): {timing_text}speaking with perfectly synchronized lip movements, mouth moving naturally and expressively with each word matching the exact timing above, clear articulation."
                    logger.info(f"Studio [{project_id}]: INJECTED original-language dialogue_timeline with {len(character_beats)} character beats")
                else:
                    sora_prompt = sora_prompt_base
                    logger.info(f"Studio [{project_id}]: dialogue_timeline only has narrator - using dubbed_text fallback")
            
            if not dialogue_timeline or (dialogue_timeline and not [b for b in dialogue_timeline if b.get('speaker','').lower() not in ('narrador','narrator')]):
                # Fallback: use dubbed_text/dialogue field
                dialogue_text = (scene.get("dubbed_text") or scene.get("dialogue", "")).strip()
                if dialogue_text:
                    import re as _re
                    clean_base = _re.sub(r"The .{5,80} says: '[^']*'[^.]*\.", "", sora_prompt_base).strip()
                    
                    lines = dialogue_text.replace('|', '\n').split('\n')
                    lip_parts = []
                    for line in [l.strip() for l in lines if l.strip()][:6]:
                        clean = _re.sub(r'^\[.*?\]\s*', '', line).strip()
                        if ':' in clean:
                            char_name = _re.sub(r'\s*\(.*?\)\s*', '', clean.split(':')[0].strip()).strip()
                            speech = _re.sub(r'\[.*?\]', '', _re.sub(r'\(.*?\)', '', clean.split(':', 1)[1].strip().strip("'\""))).strip()
                            if speech and len(speech) > 2 and len(char_name) < 30:
                                lip_parts.append(f"The character [{char_name}] says: '{speech}' - speaking with perfectly synchronized lip movements")
                    
                    if lip_parts:
                        sora_prompt = f"{clean_base}\nDIALOGUE LIP-SYNC (ORIGINAL LANGUAGE - DO NOT TRANSLATE):\n" + "\n".join(lip_parts)
                    else:
                        sora_prompt = sora_prompt_base
                elif 'sora_prompt' not in dir():
                    sora_prompt = sora_prompt_base
            
            logger.info(f"Studio [{project_id}]: Scene {scene_num} FINAL Sora prompt LENGTH: {len(sora_prompt)} chars")
            
        except Exception as e:
            logger.warning(f"Studio [{project_id}]: Scene {scene_num} regen director error: {e}")
            sora_prompt = f"{style_hint} {scene.get('description', '')}"

        # Build composite avatar for all characters in scene
        chars_in_scene = scene.get("characters_in_scene", [])
        avatar_cache = {}
        for ch_name in chars_in_scene:
            url = char_avatars.get(ch_name)
            if url and url not in avatar_cache:
                try:
                    full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                except Exception:
                    avatar_cache[url] = None

        ref_path = _create_composite_avatar(chars_in_scene, char_avatars, avatar_cache)

        # Generate video with Sora 2 (3 retries)
        _update_scene_status(tenant_id, project_id, scene_num, "waiting_sora", total)
        _update_project_field(tenant_id, project_id, {
            "progress_message": f"Cena {scene_num}: Enviando para Sora 2..."
        })

        openai_client = OpenAI(api_key=OPENAI_API_KEY)

        for attempt in range(3):
            try:
                logger.info(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1}/3")
                
                _update_scene_status(tenant_id, project_id, scene_num, "generating_video", total)
                _update_project_field(tenant_id, project_id, {
                    "progress_message": f"Cena {scene_num}: Sora 2 gerando vídeo ({attempt+1}/3)... ~3-5 min"
                })
                
                # Cinema quality → Sora 2 Pro HD
                _regen_q = project.get("production_quality", "fast")
                _regen_model = "sora-2-pro" if _regen_q == "cinema" else "sora-2"
                _regen_size = "1792x1024" if _regen_q == "cinema" else "1280x720"

                video_bytes = _generate_video_with_openai_direct(
                    client=openai_client,
                    prompt=sora_prompt,
                    size=_regen_size,
                    duration=12,
                    image_path=ref_path,
                    max_wait=600,
                    sora_character_ids=(
                        _sora_character_ids_for_scene(project, scene, max_refs=2)
                        if True else None
                    ),
                    model=_regen_model,
                )
                if video_bytes and len(video_bytes) > 1000:
                    # Video generated successfully - Sora 2 includes audio with lip-sync!
                    filename = f"studio/{project_id}_scene_{scene_num}_final.mp4"
                    video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                    logger.info(f"Studio [{project_id}]: Regen scene {scene_num} video WITH audio and lip-sync DONE ({len(video_bytes)//1024}KB)")

                    # CRITICAL CHANGE (2026-04-03): Sora 2 now generates audio WITH lip-sync natively
                    # No need for separate ElevenLabs audio generation + FFmpeg merge
                    # The director prompt now includes exact dialogue text, so Sora 2 generates:
                    # - Video with character mouth movements
                    # - Synchronized audio of character speaking the exact text
                    # - Perfect lip-sync automatically
                    
                    # Update output in project data
                    existing_out = next((o for o in outputs if o.get("scene_number") == scene_num and o.get("type") == "video"), None)
                    if existing_out:
                        existing_out["url"] = video_url
                        existing_out["timestamp"] = datetime.now(timezone.utc).isoformat()
                    else:
                        outputs.append({
                            "scene_number": scene_num,
                            "type": "video",
                            "url": video_url,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    
                    # CRITICAL CHANGE (2026-04-03): Sora 2 generates complete video with audio and lip-sync
                    # Skip separate ElevenLabs audio generation and FFmpeg merge
                    # The Claude director now instructs to include exact dialogue in Sora prompt
                    
                    # Save scene data and mark as complete
                    scene["video_url"] = video_url
                    scene["regenerated_at"] = datetime.now(timezone.utc).isoformat()
                    
                    # Update project with new output
                    _save_project(tenant_id, settings, projects)
                    _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                    
                    # Clear progress message
                    _update_project_field(tenant_id, project_id, {
                        "progress_message": f"Cena {scene_num}: Concluída! ✓"
                    })
                    
                    logger.info(f"Studio [{project_id}]: Scene {scene_num} regenerated WITH Sora 2 native audio and lip-sync")
                    return video_url
                    dialogue_text = scene.get("dialogue", "")
                    if dialogue_text and dialogue_text.strip():
                        try:
                            logger.info(f"Studio [{project_id}]: Generating audio for regen scene {scene_num}")
                            
                            # Import narration generation function
                            from .narration import _generate_narration_audio
                            from pipeline.media import _clean_narration_for_tts
                            
                            # Get audio mode and voice configuration
                            audio_mode = project.get("audio_mode", "narrated")
                            voice_map = project.get("voice_map", {})
                            lang = project.get("language", "pt")
                            
                            logger.info(f"Studio [{project_id}]: Audio mode={audio_mode}, voice_map={len(voice_map)} voices, lang={lang}")
                            
                            if audio_mode == "dubbed" and voice_map:
                                # DUBBED MODE: Multiple character voices
                                # Parse dialogue: "Narrador: '...' / Farofa: '...'"
                                parts = [p.strip() for p in dialogue_text.split(" / ")]
                                audio_clips = []
                                
                                # Note: tempfile already imported globally via _shared.py
                                tmpdir = tempfile.mkdtemp()
                                
                                try:
                                    for pi, part in enumerate(parts):
                                        if ":" in part:
                                            char_name_raw = part.split(":")[0].strip()
                                            text = ":".join(part.split(":")[1:]).strip().strip("'\"")
                                        else:
                                            char_name_raw = "Narrador"
                                            text = part.strip().strip("'\"")
                                        
                                        if not text:
                                            continue
                                        
                                        # Clean text for TTS
                                        cleaned_text = _clean_narration_for_tts(text)
                                        if not cleaned_text.strip():
                                            cleaned_text = text
                                        
                                        # Find matching voice from voice_map
                                        matched_voice = None
                                        for cname, vid in voice_map.items():
                                            if char_name_raw.lower() in cname.lower() or cname.lower() in char_name_raw.lower():
                                                matched_voice = vid
                                                break
                                        
                                        if not matched_voice:
                                            logger.warning(f"Studio [{project_id}]: No voice found for '{char_name_raw}', skipping")
                                            continue
                                        
                                        # Generate audio for this character line
                                        logger.info(f"Studio [{project_id}]: Generating '{char_name_raw}' voice ({matched_voice[:8]}...): {cleaned_text[:50]}...")
                                        audio_bytes = _generate_narration_audio(
                                            text=cleaned_text,
                                            voice_id=matched_voice,
                                            stability=0.5,
                                            similarity=0.75,
                                            style_val=0.0,
                                            language_code=lang
                                        )
                                        
                                        # Save clip
                                        clip_path = f"{tmpdir}/clip_{pi}.mp3"
                                        with open(clip_path, "wb") as f:
                                            f.write(audio_bytes)
                                        audio_clips.append(clip_path)
                                        
                                        # Add 0.3s silence between characters
                                        if pi < len(parts) - 1:
                                            silence_path = f"{tmpdir}/silence_{pi}.mp3"
                                            subprocess.run([
                                                "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                                                "-t", "0.3", "-q:a", "9", "-acodec", "libmp3lame", silence_path
                                            ], capture_output=True, timeout=5)
                                            audio_clips.append(silence_path)
                                    
                                    if audio_clips:
                                        # Concatenate all clips
                                        concat_list = f"{tmpdir}/concat_list.txt"
                                        with open(concat_list, "w") as f:
                                            for clip in audio_clips:
                                                f.write(f"file '{clip}'\n")
                                        
                                        final_audio = f"{tmpdir}/final.mp3"
                                        result = subprocess.run([
                                            "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_list,
                                            "-c", "copy", final_audio
                                        ], capture_output=True, timeout=30)
                                        
                                        if result.returncode == 0 and os.path.exists(final_audio):
                                            with open(final_audio, "rb") as f:
                                                audio_bytes = f.read()
                                            audio_filename = f"studio/{project_id}_scene_{scene_num}_audio.mp3"
                                            narration_url = _upload_to_storage(audio_bytes, audio_filename, "audio/mpeg")
                                            logger.info(f"Studio [{project_id}]: Regen scene {scene_num} DUBBED audio DONE ({len(audio_bytes)//1024}KB)")
                                        else:
                                            logger.error(f"Studio [{project_id}]: FFmpeg concat failed: {result.stderr[:200]}")
                                finally:
                                    # Cleanup
                                    import shutil
                                    try:
                                        shutil.rmtree(tmpdir)
                                    except:
                                        pass
                            
                            else:
                                # NARRATED MODE: Single narrator voice
                                # CRITICAL FIX (2026-04-03): Try multiple sources for narrator voice
                                narrator_voice = None
                                
                                # 1. Try voice_config (primary)
                                voice_config = project.get("voice_config", {})
                                narrator_voice = voice_config.get("voice_id")
                                
                                # 2. Try voice_map for "Narrador" or "Narrator"
                                if not narrator_voice and voice_map:
                                    narrator_voice = voice_map.get("Narrador") or voice_map.get("Narrator") or voice_map.get("narrador")
                                
                                # 3. Use first voice from voice_map as fallback
                                if not narrator_voice and voice_map:
                                    narrator_voice = list(voice_map.values())[0]
                                    logger.warning(f"Studio [{project_id}]: Using first voice from voice_map as narrator fallback")
                                
                                # 4. Final fallback: use ElevenLabs default voice
                                if not narrator_voice:
                                    narrator_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel (always available)
                                    logger.warning(f"Studio [{project_id}]: No narrator configured, using ElevenLabs default voice")
                                
                                cleaned_text = _clean_narration_for_tts(dialogue_text)
                                logger.info(f"Studio [{project_id}]: NARRATED mode - voice={narrator_voice[:8]}..., text_len={len(cleaned_text)}")
                                
                                audio_bytes = _generate_narration_audio(
                                    text=cleaned_text,
                                    voice_id=narrator_voice,
                                    stability=0.5,
                                    similarity=0.75,
                                    style_val=0.0,
                                    language_code=lang
                                )
                                audio_filename = f"studio/{project_id}_scene_{scene_num}_audio.mp3"
                                narration_url = _upload_to_storage(audio_bytes, audio_filename, "audio/mpeg")
                                logger.info(f"Studio [{project_id}]: Regen scene {scene_num} NARRATED audio DONE ({len(audio_bytes)//1024}KB)")
                            
                            # Merge audio + video using FFmpeg
                            # Note: subprocess and tempfile already imported globally via _shared.py
                            
                            # Download video and audio to temp files
                            video_temp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                            audio_temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
                            merged_temp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                            
                            urllib.request.urlretrieve(video_url, video_temp)
                            urllib.request.urlretrieve(narration_url, audio_temp)
                            
                            # Merge with FFmpeg (overlay audio on existing video audio track)
                            cmd = [
                                "ffmpeg", "-i", video_temp, "-i", audio_temp,
                                "-filter_complex", "[0:a]volume=0.3[bg];[1:a]volume=1.0[voice];[bg][voice]amix=inputs=2:duration=first[a]",
                                "-map", "0:v", "-map", "[a]",
                                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                                "-y", merged_temp
                            ]
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                            
                            if result.returncode == 0 and os.path.exists(merged_temp) and os.path.getsize(merged_temp) > 1000:
                                # Upload merged video
                                with open(merged_temp, "rb") as f:
                                    merged_bytes = f.read()
                                merged_filename = f"studio/{project_id}_scene_{scene_num}_final.mp4"
                                video_url = _upload_to_storage(merged_bytes, merged_filename, "video/mp4")
                                logger.info(f"Studio [{project_id}]: Regen scene {scene_num} audio+video merged ({len(merged_bytes)//1024}KB)")
                            else:
                                logger.warning(f"Studio [{project_id}]: Regen scene {scene_num} FFmpeg merge failed: {result.stderr[:200]}")
                            
                            # Cleanup temp files
                            for tmp in [video_temp, audio_temp, merged_temp]:
                                try:
                                    os.unlink(tmp)
                                except:
                                    pass
                                    
                        except Exception as audio_err:
                            logger.error(f"Studio [{project_id}]: Regen scene {scene_num} audio generation failed: {audio_err}")
                            # Continue with video-only if audio fails

                    # Update project outputs
                    settings, projects, project = _get_project(tenant_id, project_id)
                    if project:
                        outputs = project.get("outputs", [])
                        # Remove old output for this scene
                        outputs = [o for o in outputs if o.get("scene_number") != scene_num]
                        outputs.append({
                            "id": uuid.uuid4().hex[:8], "type": "video", "url": video_url,
                            "scene_number": scene_num, "duration": 12,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })
                        project["outputs"] = outputs
                        
                        # CRITICAL FIX (2026-04-03): Update scene status to "done" after successful regeneration
                        if narration_url:
                            logger.info(f"Studio [{project_id}]: Scene {scene_num} regenerated WITH audio")
                        else:
                            logger.info(f"Studio [{project_id}]: Scene {scene_num} regenerated (video only, no dialogue)")
                        
                        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                        _add_milestone(project, f"regen_scene_{scene_num}", f"Cena {scene_num} regenerada com sucesso")
                        _save_project(tenant_id, settings, projects)

                    # Cleanup temp files
                    for p in avatar_cache.values():
                        if p:
                            try:
                                os.unlink(p)
                            except OSError:
                                pass
                    if ref_path and ref_path not in avatar_cache.values():
                        try:
                            os.unlink(ref_path)
                        except OSError:
                            pass
                    return

                else:
                    logger.warning(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1} empty video")
                    if attempt < 2:
                        _time.sleep(10)
                        continue

            except Exception as ve:
                err_str = str(ve).lower()
                is_retryable = any(k in err_str for k in ["disconnect", "server", "timeout", "connection"])
                if is_retryable and attempt < 2:
                    logger.warning(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1} error: {ve}. Retrying...")
                    _time.sleep(15 * (attempt + 1))
                    continue
                logger.error(f"Studio [{project_id}]: Regen scene {scene_num} FAILED: {ve}")
                break

        # All retries failed
        _update_scene_status(tenant_id, project_id, scene_num, "error", total)
        for p in avatar_cache.values():
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass
        if ref_path and ref_path not in avatar_cache.values():
            try:
                os.unlink(ref_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Regen scene {scene_num} error: {e}")
        _update_scene_status(tenant_id, project_id, scene_num, "error", len(project.get("scenes", [])) if project else 0)


@router.post("/projects/{project_id}/regenerate-scene")
async def regenerate_scene(project_id: str, req: RegenerateSceneRequest, tenant=Depends(get_current_tenant)):
    """Regenerate a single scene video."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scene = next((s for s in project.get("scenes", []) if s.get("scene_number") == req.scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {req.scene_number} not found")

    thread = threading.Thread(
        target=_regenerate_single_scene,
        args=(tenant["id"], project_id, req.scene_number, req.custom_prompt),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "scene_number": req.scene_number}


@router.post("/projects/{project_id}/save-character-avatars")
async def save_character_avatars(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Persist character avatar links to the project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["character_avatars"] = payload.get("character_avatars", {})
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects, flush_now=True)
    
    # Force cache drop to prevent stale data overwrite
    from core.cache import project_cache
    lock = project_cache._get_lock(tenant["id"])
    with lock:
        project_cache._cache.pop(tenant["id"], None)
        project_cache._dirty_tenants.discard(tenant["id"])
    
    logger.info(f"Studio [{project_id}]: Saved character avatars: {list(payload.get('character_avatars', {}).keys())}")
    return {"status": "ok"}


@router.post("/projects/{project_id}/update-visual-style")
async def update_visual_style(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update visual style for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["visual_style"] = payload.get("visual_style", "animation")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.post("/projects/{project_id}/update-language")
async def update_language(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update language for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["language"] = payload.get("language", "pt")
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}


@router.post("/projects/{project_id}/update-scene")
async def update_scene(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update a single scene description, dialogue, etc."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    scene_num = payload.get("scene_number")
    scenes = project.get("scenes", [])
    for s in scenes:
        if s.get("scene_number") == scene_num:
            for key in ["title", "description", "dialogue", "emotion", "camera", "transition", "characters_in_scene"]:
                if key in payload:
                    s[key] = payload[key]
            break
    project["scenes"] = scenes
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok"}



# ── Scene Management (Add, Delete, Reorder, AI Generate) ──

@router.post("/projects/{project_id}/add-scene")
async def add_scene(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Add a new scene at a given position. Auto-renumbers subsequent scenes."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    position = payload.get("position")  # 1-based insert position
    scene_data = payload.get("scene", {})
    scenes = project.get("scenes", [])

    if position is None or position < 1:
        position = len(scenes) + 1
    position = min(position, len(scenes) + 1)

    new_scene = {
        "scene_number": position,
        "title": scene_data.get("title", f"Cena {position}"),
        "description": scene_data.get("description", ""),
        "dialogue": scene_data.get("dialogue", ""),
        "emotion": scene_data.get("emotion", ""),
        "camera": scene_data.get("camera", ""),
        "characters_in_scene": scene_data.get("characters_in_scene", []),
        "transition": scene_data.get("transition", ""),
    }

    # Renumber scenes at and after the insertion point
    for s in scenes:
        if s.get("scene_number", 0) >= position:
            s["scene_number"] = s["scene_number"] + 1

    # Also renumber storyboard panels
    panels = project.get("storyboard_panels", [])
    for p in panels:
        if p.get("scene_number", 0) >= position:
            p["scene_number"] = p["scene_number"] + 1

    scenes.append(new_scene)
    scenes.sort(key=lambda x: x.get("scene_number", 0))

    # Create placeholder storyboard panel for the new scene if storyboard exists
    has_storyboard = len(panels) > 0
    if has_storyboard:
        new_panel = {
            "scene_number": position,
            "status": "pending",
            "image_url": None,
            "frames": [],
            "description": scene_data.get("description", ""),
        }
        panels.append(new_panel)
        panels.sort(key=lambda x: x.get("scene_number", 0))

    project["scenes"] = scenes
    project["storyboard_panels"] = panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    return {"status": "ok", "scene": new_scene, "total_scenes": len(scenes), "auto_storyboard": has_storyboard}


@router.post("/projects/{project_id}/delete-scene")
async def delete_scene(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Delete a scene and its associated storyboard panel. Renumbers remaining scenes."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scene_num = payload.get("scene_number")
    if scene_num is None:
        raise HTTPException(status_code=400, detail="scene_number is required")

    scenes = project.get("scenes", [])
    panels = project.get("storyboard_panels", [])

    # Remove the scene
    scenes = [s for s in scenes if s.get("scene_number") != scene_num]
    # Remove its storyboard panel
    panels = [p for p in panels if p.get("scene_number") != scene_num]

    # Renumber everything after the deleted scene
    for s in scenes:
        if s.get("scene_number", 0) > scene_num:
            s["scene_number"] = s["scene_number"] - 1
    for p in panels:
        if p.get("scene_number", 0) > scene_num:
            p["scene_number"] = p["scene_number"] - 1

    project["scenes"] = scenes
    project["storyboard_panels"] = panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "total_scenes": len(scenes)}


@router.post("/projects/{project_id}/reorder-scenes")
async def reorder_scenes(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Reorder scenes by providing the new order as a list of scene_numbers."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_order = payload.get("order", [])  # List of scene_numbers in new order
    scenes = project.get("scenes", [])
    panels = project.get("storyboard_panels", [])

    # Build lookup maps
    scene_map = {s["scene_number"]: s for s in scenes}
    panel_map = {p["scene_number"]: p for p in panels}

    # Reassign scene_numbers based on new order
    reordered_scenes = []
    reordered_panels = []
    for new_num, old_num in enumerate(new_order, start=1):
        if old_num in scene_map:
            s = scene_map[old_num]
            s["scene_number"] = new_num
            reordered_scenes.append(s)
        if old_num in panel_map:
            p = panel_map[old_num]
            p["scene_number"] = new_num
            reordered_panels.append(p)

    project["scenes"] = reordered_scenes
    project["storyboard_panels"] = reordered_panels
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "total_scenes": len(reordered_scenes)}


@router.post("/projects/{project_id}/generate-scene-ai")
async def generate_scene_ai(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Generate a new scene using AI based on context from neighboring scenes."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_hint = payload.get("hint", "")
    position = payload.get("position", len(project.get("scenes", [])) + 1)
    scenes = project.get("scenes", [])
    characters = project.get("characters", [])
    lang = project.get("language", "pt")

    # Get neighboring scenes for context
    prev_scene = next((s for s in scenes if s.get("scene_number") == position - 1), None)
    next_scene = next((s for s in scenes if s.get("scene_number") == position), None)

    context_parts = []
    if prev_scene:
        context_parts.append(f"CENA ANTERIOR ({prev_scene['scene_number']}): {prev_scene.get('title','')} - {prev_scene.get('description','')}")
    if next_scene:
        context_parts.append(f"CENA SEGUINTE ({next_scene['scene_number']}): {next_scene.get('title','')} - {next_scene.get('description','')}")
    if characters:
        char_names = [c.get("name", "") for c in characters]
        context_parts.append(f"PERSONAGENS DISPONÍVEIS: {', '.join(char_names)}")

    lang_instruction = {
        "pt": "Responda em português.",
        "en": "Respond in English.",
        "es": "Responda en español.",
    }.get(lang, "Responda em português.")

    prompt = f"""Você é um roteirista profissional. Crie UMA nova cena que se encaixe perfeitamente na narrativa.

{chr(10).join(context_parts)}

INSTRUÇÃO DO USUÁRIO: {user_hint if user_hint else 'Crie uma cena que faça sentido como continuação natural da história.'}

{lang_instruction}

Retorne APENAS JSON válido:
{{
  "title": "Título da cena",
  "description": "Descrição visual detalhada da cena",
  "dialogue": "Narração ou diálogo",
  "emotion": "emoção dominante",
  "camera": "tipo de câmera (ex: close-up, wide shot)",
  "characters_in_scene": ["nomes dos personagens presentes"]
}}
"""

    try:
        system = "Você é um roteirista profissional especializado em criar cenas narrativas detalhadas."
        result = _call_claude_sync(system, prompt, max_tokens=1000)
        parsed = _parse_json(result)
        if not parsed:
            raise HTTPException(status_code=500, detail="AI did not return valid scene data")
        return {"status": "ok", "scene": parsed}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)[:200]}")



# ── Production Preview (Pre-Production Only) ──

def _generate_preview_task(tenant_id, project_id):
    """Background task: runs ONLY avatar analysis + production design."""
    import time as _time
    import tempfile
    t0 = _time.time()
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        characters = project.get("characters", [])
        scenes = project.get("scenes", [])
        char_avatars = project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")
        briefing = project.get("briefing", "")

        # Download avatars
        avatar_cache = {}
        for name, url in char_avatars.items():
            if url and url not in avatar_cache:
                try:
                    full_url = url if not url.startswith("/") else f"{os.environ.get('SUPABASE_URL','')}/storage/v1/object/public{url}"
                    ref_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    urllib.request.urlretrieve(full_url, ref_file.name)
                    avatar_cache[url] = ref_file.name
                except Exception:
                    avatar_cache[url] = None

        # Step 1: Avatar analysis with Claude Vision
        avatar_descriptions = _run_async_in_thread(_analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id))

        # Step 2: Production Design Document
        production_design = _build_production_design(
            briefing, characters, scenes, avatar_descriptions, visual_style,
            project.get("language", "pt"), project_id
        )

        # Cleanup
        for p in avatar_cache.values():
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass

        # Save
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["agents_output"] = {
                **project.get("agents_output", {}),
                "production_design": production_design,
                "avatar_descriptions": avatar_descriptions,
            }
            project["preview_status"] = "complete"
            project["preview_time"] = round(_time.time() - t0, 1)
            _save_project(tenant_id, settings, projects)
            logger.info(f"Studio [{project_id}]: Preview generated in {project['preview_time']}s")

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Preview generation failed: {e}")
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["preview_status"] = "error"
            project["preview_error"] = str(e)
            _save_project(tenant_id, settings, projects)


@router.post("/projects/{project_id}/generate-preview")
async def generate_production_preview(project_id: str, tenant=Depends(get_current_tenant)):
    """Start pre-production preview: avatar analysis + production design document."""
    tenant_id = tenant["id"]
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not project.get("scenes"):
        raise HTTPException(400, "No scenes available")

    project["preview_status"] = "generating"
    _save_project(tenant_id, settings, projects)

    thread = threading.Thread(target=_generate_preview_task, args=(tenant_id, project_id), daemon=True)
    thread.start()

    return {"status": "generating", "message": "Pre-production preview started"}


@router.get("/projects/{project_id}/preview")
async def get_production_preview(project_id: str, tenant=Depends(get_current_tenant)):
    """Get pre-production preview data (production design document)."""
    tenant_id = tenant["id"]
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    agents_output = project.get("agents_output", {})
    return {
        "preview_status": project.get("preview_status", "none"),
        "preview_time": project.get("preview_time"),
        "production_design": agents_output.get("production_design"),
        "avatar_descriptions": agents_output.get("avatar_descriptions"),
    }


# ── Image Generation (for scene thumbnails or fallback) ──

@router.post("/generate-image")
async def generate_directed_image(req: StartProductionRequest, tenant=Depends(get_current_tenant)):
    settings, projects, project = _get_project(tenant["id"], req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    briefing = project.get("briefing", "")
    avatar_urls = project.get("avatar_urls", [])

    prompt_text = f"Create a professional cinematic image. Briefing: {briefing}. Characters: {len(avatar_urls)}. 16:9 aspect ratio."

    content = [{"type": "text", "text": prompt_text}]
    for url in avatar_urls[:4]:
        try:
            req_obj = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            img_data = urllib.request.urlopen(req_obj, timeout=15).read()
            b64 = base64.b64encode(img_data).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        except Exception:
            pass

    response = await litellm.acompletion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": content}],
        api_key=GEMINI_API_KEY,
    )
    images = []
    if response.choices and response.choices[0].message:
        msg = response.choices[0].message
        if hasattr(msg, 'images') and msg.images:
            for img_d in msg.images:
                if 'image_url' in img_d and 'url' in img_d['image_url']:
                    data_url = img_d['image_url']['url']
                    if ';base64,' in data_url:
                        images.append(data_url.split(';base64,', 1)[1])
    if not images:
        raise HTTPException(status_code=500, detail="No image generated")
    img_bytes = base64.b64decode(images[0])
    filename = f"studio/scene_{uuid.uuid4().hex[:8]}.png"
    public_url = _upload_to_storage(img_bytes, filename)
    return {"image_url": public_url}




@router.post("/projects/{project_id}/rebuild-film")
async def rebuild_film(project_id: str, tenant=Depends(get_current_tenant)):
    """Re-concatenate all scene videos into final film with crossfade.
    Used after regenerating individual scenes to update the complete film."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    outputs = project.get("outputs", [])
    scene_videos = sorted(
        [o for o in outputs if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")],
        key=lambda x: x["scene_number"]
    )
    
    if len(scene_videos) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 scene videos to rebuild film")
    
    _update_project_field(tenant["id"], project_id, {
        "full_production_status": "rebuilding",
        "progress_message": f"Re-concatenando {len(scene_videos)} cenas com crossfade..."
    })
    
    import threading
    thread = threading.Thread(
        target=_rebuild_film_background,
        args=(tenant["id"], project_id),
        daemon=True
    )
    thread.start()
    
    return {"status": "started", "message": f"Rebuilding film with {len(scene_videos)} scenes"}


def _rebuild_film_background(tenant_id: str, project_id: str):
    """Background task to re-concatenate all scene videos."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        outputs = project.get("outputs", [])
        
        scene_videos = sorted(
            [o for o in outputs if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")],
            key=lambda x: x["scene_number"]
        )
        
        logger.info(f"RebuildFilm [{project_id}]: Concatenating {len(scene_videos)} scenes with crossfade")
        
        # Default: cinema ON for films >= 3 scenes (unless user explicitly set "fast")
        _quality = project.get("production_quality")
        if not _quality:
            _quality = "cinema" if len(scene_videos) >= 3 else "fast"
        _cinema = _quality == "cinema"
        final_url = _concatenate_videos(scene_videos, project_id, crossfade_duration=1.0, cinema_quality=_cinema)
        
        if final_url:
            # Update or create the main video output (scene_number=0)
            main_output = next((o for o in outputs if o.get("type") == "video" and o.get("scene_number", -1) == 0), None)
            if main_output:
                main_output["url"] = final_url
                main_output["has_audio"] = True
            else:
                outputs.append({"type": "video", "scene_number": 0, "url": final_url, "has_audio": True})
            
            # Save film immediately (before V2A attempt)
            _update_project_field(tenant_id, project_id, {
                "outputs": outputs,
                "progress_message": "Filme concatenado! Adicionando sonoplastia..."
            }, flush_now=True)
            
            # V2A sonoplastia is optional - don't let it block the film
            try:
                _generate_sora2_audio_overlay(tenant_id, project_id)
                logger.info(f"RebuildFilm [{project_id}]: V2A overlay applied successfully")
            except Exception as v2a_err:
                logger.warning(f"RebuildFilm [{project_id}]: V2A overlay failed (non-blocking): {v2a_err}")
            
            _update_project_field(tenant_id, project_id, {
                "full_production_status": "complete",
                "progress_message": "Filme atualizado com sucesso!"
            }, flush_now=True)
            
            logger.info(f"RebuildFilm [{project_id}]: COMPLETE - film updated")
        else:
            _update_project_field(tenant_id, project_id, {
                "full_production_status": "error",
                "progress_message": "Erro ao re-concatenar o filme"
            })
            logger.error(f"RebuildFilm [{project_id}]: Concatenation failed")
    
    except Exception as e:
        logger.error(f"RebuildFilm [{project_id}]: Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        _update_project_field(tenant_id, project_id, {
            "full_production_status": "error",
            "progress_message": f"Erro: {str(e)[:100]}"
        })
