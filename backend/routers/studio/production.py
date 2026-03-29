"""Auto-generated module from studio.py split."""
from ._shared import *
from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

# ── STEP 3: Multi-Scene Production Pipeline (v3 — Per-Scene Parallel Teams) ──

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
        agent_status.update({
            "current_scene": scene_num, "total_scenes": total,
            "phase": status if status in ("directing", "generating_video", "concatenating") else agent_status.get("phase", "running"),
            "scene_status": scene_status,
            "videos_done": videos_done,
        })
        project["agent_status"] = agent_status
        _save_project(tenant_id, settings, projects)
    except Exception:
        pass


# Thread-safe lock for saving scene videos (prevents race conditions in parallel mode)
_save_video_lock = threading.Lock()


def _save_scene_video(tenant_id: str, project_id: str, scene_num: int, video_url: str, total: int):
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
            _add_milestone(project, f"video_scene_{scene_num}", f"Vídeo cena {scene_num} gerado")
            _save_project(tenant_id, settings, projects)
        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
    except Exception as e:
        logger.warning(f"_save_scene_video scene {scene_num}: {e}")


def _run_multi_scene_production(tenant_id: str, project_id: str, character_avatars: dict = None):
    """v4 — Decoupled Pipeline: ALL Directors first (parallel) → ALL Sora jobs queued.

    Architecture:
    PHASE A (Preparation — ~5s):
    ┌─ Director(Claude) Scene 1  ─┐
    ├─ Director(Claude) Scene 2  ─┤  ALL PARALLEL → 15 Sora prompts ready
    ├─ Director(Claude) Scene N  ─┤
    └─ MusicDirector              ┘

    PHASE B (Production — priority queue):
    Sora Queue → [1,2,3,4,5] → [6,7,8,9,10] → [11,12,13,14,15]
                  5 slots simultaneous

    → FFmpeg concat → Complete
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

        # ── Resume support — find already completed videos ──
        _, _, proj_check = _get_project(tenant_id, project_id)
        existing_outputs = proj_check.get("outputs", []) if proj_check else []
        completed_videos = {}
        for o in existing_outputs:
            sn = o.get("scene_number")
            if sn and o.get("url") and o.get("type") == "video" and sn > 0:
                completed_videos[sn] = o["url"]
        if completed_videos:
            logger.info(f"Studio [{project_id}]: Resuming — {len(completed_videos)} scenes already cached: {sorted(completed_videos.keys())}")

        # ══ PRE-PRODUCTION: Avatar Analysis + Production Design Document ══
        # Check if pre-production was already done via Preview Board
        existing_pd = project.get("agents_output", {}).get("production_design")
        existing_ad = project.get("agents_output", {}).get("avatar_descriptions")

        if existing_pd and isinstance(existing_pd, dict) and existing_pd.get("character_bible"):
            logger.info(f"Studio [{project_id}]: PRE-PRODUCTION already done via Preview Board — skipping")
            production_design = existing_pd
            avatar_descriptions = existing_ad or {}
        else:
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "pre_production",
                                 "scene_status": {str(i+1): "queued" for i in range(total)}}
            })
            logger.info(f"Studio [{project_id}]: PRE-PRODUCTION — Analyzing avatars and building production design")

            # Step 1: Analyze avatars with Claude Vision (ONE call for all avatars)
            avatar_descriptions = _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id)

            # Step 2: Build Production Design Document (ONE call — replaces music, style, location, continuity planning)
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
            logger.info(f"Studio [{project_id}]: CONTINUITY ENGINE ON — Style DNA injected ({len(style_dna)} chars)")
        pd_chars = production_design.get("character_bible", {})
        pd_locations = production_design.get("location_bible", {})
        pd_scene_dirs = {d.get("scene", 0): d for d in production_design.get("scene_directions", [])}
        pd_color = production_design.get("color_palette", {})
        pd_music = production_design.get("music_plan", [])

        t_preproduction = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: PRE-PRODUCTION complete in {t_preproduction:.1f}s — {len(pd_chars)} characters, {len(pd_locations)} locations")

        _add_milestone(project, "preproduction_done", f"Pré-produção — {t_preproduction:.0f}s")
        _update_project_field(tenant_id, project_id, {
            "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "pre_production_done",
                             "scene_status": {str(i+1): "queued" for i in range(total)}}
        })

        # ── Rate limiter for Sora 2 ──
        sora_semaphore = threading.Semaphore(5)

        # Use direct OpenAI key for Sora 2
        video_gen = OpenAIVideoGeneration(api_key=OPENAI_API_KEY)
        logger.info(f"Studio [{project_id}]: Using DIRECT OpenAI key for Sora 2")

        # Track budget state across threads
        budget_exhausted = threading.Event()

        def _scene_director(scene, scene_num):
            """PHASE A — Scene Director: generates Sora prompt using Production Design Bible.
            Uses pre-computed character_bible, location_bible, and style_anchors for consistency.
            Token-efficient: creative decisions pre-made by Production Designer.
            """
            if scene_num in completed_videos:
                return {"scene_number": scene_num, "sora_prompt": None, "cached": True}

            chars_in_scene = scene.get("characters_in_scene", [])

            # Canonical character descriptions from Production Design Bible
            char_descs = "\n".join([
                f"- {name}: {pd_chars.get(name, next((ch.get('description','') for ch in characters if ch.get('name')==name), 'Unknown character'))}"
                for name in chars_in_scene
            ])

            # Scene-specific direction from Production Design
            scene_dir = pd_scene_dirs.get(scene_num, {})
            loc_key = scene_dir.get("location_key", "")
            loc_desc = pd_locations.get(loc_key, "")
            time_day = scene_dir.get("time_of_day", "afternoon")
            time_light = pd_color.get(time_day, pd_color.get("global", ""))
            cam_flow = scene_dir.get("camera_flow", scene.get("camera", ""))
            trans_note = scene_dir.get("transition_note", "")

            director_system = f"""You are a SCENE DIRECTOR for Sora 2 video generation. Convert scene descriptions into detailed visual prompts.

MANDATORY STYLE (include VERBATIM at the start of your prompt): {pd_style}

Return ONLY JSON: {{"sora_prompt": "ONE detailed English paragraph for Sora 2, max 300 words"}}

CRITICAL RULES:
- START your prompt with the exact mandatory style text above — copy it word for word
- Describe EVERY character by their EXACT PHYSICAL APPEARANCE from the character descriptions below — these descriptions come from analyzing the actual avatar images, so they are the ABSOLUTE SOURCE OF TRUTH
- For EACH character appearing in the scene, copy their FULL character_bible description into the prompt — DO NOT summarize or abbreviate
- SPECIES LOCK: If a character is described as an "anthropomorphic camel", they are ALWAYS a camel in EVERY scene — NEVER a lion, bear, or any other animal
- POSTURE LOCK: If a character is described as "bipedal/standing upright", they MUST be shown standing on two legs — NEVER as a quadruped walking on four legs
- NEVER add extra animals or characters that are NOT in the CHARACTER IDENTITY SHEET below — if only Abraão and Isaac are in the scene, ONLY those two characters appear
- NEVER use character names in the prompt — only physical descriptions
- If a scene describes a "birth" or "baby", the young character MUST be a tiny newborn infant of the SAME SPECIES as the parents — NOT a teenager or adult
- If a scene says "child" or "young", the character must be visibly SMALL and childlike — NOT adult-sized
- Include: specific environment details, lighting matching the time of day, atmospheric elements, character actions/expressions, camera movement
- Each scene must look like it belongs to the SAME FILM — same art technique, same 3D rendering quality, same color grading
- The sora_prompt MUST be in ENGLISH"""

            director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}

CHARACTER IDENTITY SHEET (from avatar image analysis — ABSOLUTE SOURCE OF TRUTH, DO NOT DEVIATE):
{char_descs}

AGE/LIFE STAGE CONTEXT FOR THIS SCENE: Based on the scene description above, determine the correct age of each character.
- If the scene describes a "birth" or "newborn", the baby character is a TINY INFANT of the same species — small enough to be held in arms.
- If the scene describes "growing up" or "childhood", the young character is a SMALL CHILD — about half the height of the adults.

LOCATION: {loc_desc}
TIME OF DAY: {time_day} — Light/Colors: {time_light}
CAMERA: {cam_flow}
CONTINUITY WITH PREVIOUS SCENE: {trans_note}"""

            _update_scene_status(tenant_id, project_id, scene_num, "directing", total)
            try:
                t_p = _time.time()
                result_text = _call_claude_sync(director_system, director_prompt, max_tokens=1000)
                data = _parse_json(result_text) or {}
                sora_prompt = data.get("sora_prompt", scene.get("description", ""))
                elapsed = _time.time() - t_p
                logger.info(f"Studio [{project_id}]: Scene {scene_num} directed in {elapsed:.1f}s")
                return {"scene_number": scene_num, "sora_prompt": sora_prompt, "cached": False}
            except Exception as e:
                logger.warning(f"Studio [{project_id}]: Scene {scene_num} director error: {e}")
                # Fallback: construct prompt directly from production design elements
                char_desc_text = ". ".join([pd_chars.get(n, '') for n in chars_in_scene if pd_chars.get(n)])
                fallback = f"{pd_style}. {loc_desc}. {time_day}, {time_light}. {char_desc_text}. {scene.get('description', '')}."
                return {"scene_number": scene_num, "sora_prompt": fallback[:1000], "cached": False}

        def _sora_render(directed_scene, scene):
            """PHASE B — Sora 2 video render with retries, budget awareness, and continuity anchoring."""
            scene_num = directed_scene["scene_number"]

            if directed_scene.get("cached"):
                _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                return {"scene_number": scene_num, "url": completed_videos[scene_num], "type": "video", "duration": 12}

            if budget_exhausted.is_set():
                _update_scene_status(tenant_id, project_id, scene_num, "error", total)
                return {"scene_number": scene_num, "url": None, "type": "video", "error": "budget_exhausted"}

            sora_prompt = directed_scene["sora_prompt"]
            chars_in_scene = scene.get("characters_in_scene", [])

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
                        gen_kwargs = {"prompt": sora_prompt[:1000], "model": "sora-2", "size": "1280x720", "duration": 12, "max_wait_time": 600}
                        if ref_path:
                            gen_kwargs["image_path"] = ref_path

                        logger.info(f"Studio [{project_id}]: Scene {scene_num} Sora 2 attempt {attempt+1}/{max_retries} (avatar={'Y' if ref_path else 'N'})")
                        video_bytes = video_gen.text_to_video(**gen_kwargs)
                        elapsed = _time.time() - t_v

                        if video_bytes and len(video_bytes) > 1000:
                            filename = f"studio/{project_id}_scene_{scene_num}.mp4"
                            video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                            logger.info(f"Studio [{project_id}]: Scene {scene_num} DONE {elapsed:.0f}s ({len(video_bytes)//1024}KB)")
                            _save_scene_video(tenant_id, project_id, scene_num, video_url, total)
                            return {"scene_number": scene_num, "url": video_url, "type": "video", "duration": 12}
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

        # ══ PHASE A: ALL DIRECTORS IN PARALLEL (Production-Design-guided) ══
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger.info(f"Studio [{project_id}]: PHASE A — Launching {total} Scene Directors (parallel, PD-guided)")

        directed_scenes = []
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
        logger.info(f"Studio [{project_id}]: PHASE A complete in {t_phase_a:.1f}s — {len(directed_scenes)} prompts ready")

        # Sort by scene number for ordered Sora queue
        directed_scenes.sort(key=lambda x: x["scene_number"])

        # ══ PHASE B: SORA RENDERS ══
        # Both modes now use parallel rendering (semaphore controls Sora 2 concurrency)
        # Continuity mode: generates keyframes first (parallel), then renders in parallel
        # Normal mode: renders directly in parallel
        scene_videos = []
        scene_map = {s.get("scene_number", i+1): s for i, s in enumerate(scenes)}

        if continuity_mode:
            logger.info(f"Studio [{project_id}]: PHASE B (CONTINUITY PARALLEL) — Keyframe generation + parallel rendering")

            # B1: Generate ALL keyframes in parallel (Gemini, 5 concurrent)
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
                    logger.warning(f"Studio [{project_id}]: Keyframe FAILED all retries for scene {sn} — using avatar fallback")
                return ds

            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_keyframes",
                                 "videos_done": 0, "scene_status": {str(ds["scene_number"]): "queued" for ds in directed_scenes}}
            })

            with ThreadPoolExecutor(max_workers=5) as executor:
                kf_futures = {executor.submit(_generate_keyframe_for_scene, ds): ds["scene_number"] for ds in directed_scenes}
                for future in as_completed(kf_futures):
                    sn = kf_futures[future]
                    future.result()  # ensures exceptions propagate
                    logger.info(f"Studio [{project_id}]: Keyframe {sn}/{total} ready")

            logger.info(f"Studio [{project_id}]: All {total} keyframes ready — launching parallel Sora 2 renders")

            # B2: Render ALL videos in parallel (Sora 2, controlled by sora_semaphore=5)
            _update_project_field(tenant_id, project_id, {
                "agent_status": {"current_scene": 0, "total_scenes": total, "phase": "generating_video",
                                 "videos_done": 0, "scene_status": {str(ds["scene_number"]): "waiting_sora" for ds in directed_scenes}}
            })

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
            logger.info(f"Studio [{project_id}]: PHASE B — Queueing {total} Sora 2 renders (5 slots, parallel)")

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
        logger.info(f"Studio [{project_id}]: ALL SCENES done in {t_prod:.0f}s ({t_prod/60:.1f}min) — {successful}/{total} OK, {budget_errors} budget errors")

        # Save production data
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["agents_output"] = {**project.get("agents_output", {}),
                                        "music_director": music_data,
                                        "production_design": production_design,
                                        "avatar_descriptions": avatar_descriptions}
            _add_milestone(project, "preproduction_complete", f"Pré-produção inteligente — {t_preproduction:.0f}s")
            _add_milestone(project, "agents_complete", f"Produção paralela — {t_prod:.0f}s")
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
                final_url = _concatenate_videos(successful_videos, project_id)
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
            _add_milestone(project, "videos_generated", f"Vídeos gerados — {len(successful_videos)} cenas")
            if final_url:
                _add_milestone(project, "film_complete", f"Filme completo — {len(successful_videos)*12}s")
            _save_project(tenant_id, settings, projects)

        t_total = _time.time() - t_start
        logger.info(f"Studio [{project_id}]: COMPLETE! {len(successful_videos)} videos in {t_total:.0f}s ({t_total/60:.1f}min)")

    except Exception as e:
        logger.error(f"Studio [{project_id}] pipeline error: {e}")
        _update_project_field(tenant_id, project_id, {
            "status": "error", "error": str(e)[:500],
        })


def _concatenate_videos(scene_videos: list, project_id: str) -> str:
    """Download scene videos, concatenate with FFmpeg, compress for upload, upload result."""
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

    # Create concat file
    concat_file = f"{tmpdir}/concat.txt"
    with open(concat_file, 'w') as f:
        for fp in files:
            f.write(f"file '{fp}'\n")

    output_path = f"{tmpdir}/final_{project_id}.mp4"

    # Calculate total input size to decide compression strategy
    total_input_size = sum(os.path.getsize(fp) for fp in files)
    total_input_mb = total_input_size / (1024 * 1024)
    num_scenes = len(files)
    logger.info(f"Studio [{project_id}]: Concat {num_scenes} scenes, total input {total_input_mb:.1f}MB")

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
        subprocess.run(cmd_reencode, capture_output=True, timeout=600)

    # Check file size — if > 45MB, apply aggressive compression
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

    # Persist character avatars and visual style to project
    if req.character_avatars:
        project["character_avatars"] = req.character_avatars
    if req.visual_style:
        project["visual_style"] = req.visual_style

    project["status"] = "starting"
    project["error"] = None
    total = len(project.get("scenes", []))
    project["agent_status"] = {"current_scene": 0, "total_scenes": total, "phase": "starting"}
    _add_milestone(project, "production_started", f"Produção iniciada — {total} cenas")
    if req.character_avatars:
        _add_milestone(project, "avatars_linked", f"Avatares vinculados — {len(req.character_avatars)} personagens")
    _save_project(tenant["id"], settings, projects)

    # Use saved character_avatars (merge request + saved)
    char_avatars = {**project.get("character_avatars", {}), **req.character_avatars}

    thread = threading.Thread(
        target=_run_multi_scene_production,
        args=(tenant["id"], req.project_id, char_avatars),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "project_id": req.project_id, "total_scenes": total}


# ── Per-Scene Regeneration ──

def _regenerate_single_scene(tenant_id: str, project_id: str, scene_num: int, custom_prompt: str = None):
    """Regenerate a single scene video using the same pipeline logic."""
    import time as _time
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        characters = project.get("characters", [])
        char_avatars = project.get("character_avatars", {})
        visual_style = project.get("visual_style", "animation")
        total = len(scenes)

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

        # Use custom prompt or generate via Claude with Production Design
        if custom_prompt:
            sora_prompt = custom_prompt
        else:
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
Return ONLY JSON: {{"sora_prompt": "ONE detailed English paragraph for Sora 2, max 250 words"}}
RULES: Describe characters by EXACT PHYSICAL APPEARANCE, NEVER by name. Include environment, lighting, atmosphere, actions, camera."""

                director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')}
CHARACTERS (by appearance): {char_descs}
LOCATION: {loc_desc}
TIME: {time_day} — {time_light}
CAMERA: {scene_dir.get('camera_flow', scene.get('camera', ''))}"""
            else:
                # Fallback: no production design available
                scene_chars = "; ".join([f"{ch['name']}: {ch.get('description','')}" for ch in characters if ch.get("name") in chars_in_scene])
                director_system = f"""You are a SCENE DIRECTOR for Sora 2. {style_hint}
Return ONLY JSON: {{"sora_prompt": "Detailed English paragraph for Sora 2. Max 250 words."}}"""
                director_prompt = f"""Scene {scene_num}/{total}: "{scene.get('title','')}"
Description: {scene.get('description','')}
Dialogue: {scene.get('dialogue','')}
Emotion: {scene.get('emotion','')} | Camera: {scene.get('camera','')}
Characters: {scene_chars}
Story: {briefing[:300]}"""

            try:
                result_text = _call_claude_sync(director_system, director_prompt, max_tokens=1000)
                data = _parse_json(result_text) or {}
                sora_prompt = data.get("sora_prompt", scene.get("description", ""))
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
        _update_scene_status(tenant_id, project_id, scene_num, "generating_video", total)

        video_gen = OpenAIVideoGeneration(api_key=OPENAI_API_KEY)

        for attempt in range(3):
            try:
                gen_kwargs = {"prompt": sora_prompt[:1000], "model": "sora-2", "size": "1280x720", "duration": 12, "max_wait_time": 600}
                if ref_path:
                    gen_kwargs["image_path"] = ref_path

                logger.info(f"Studio [{project_id}]: Regen scene {scene_num} attempt {attempt+1}/3")
                video_bytes = video_gen.text_to_video(**gen_kwargs)
                if video_bytes and len(video_bytes) > 1000:
                    filename = f"studio/{project_id}_scene_{scene_num}.mp4"
                    video_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                    logger.info(f"Studio [{project_id}]: Regen scene {scene_num} DONE ({len(video_bytes)//1024}KB)")

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
                        _update_scene_status(tenant_id, project_id, scene_num, "done", total)
                        _add_milestone(project, f"regen_scene_{scene_num}", f"Cena {scene_num} regenerada")
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
    _save_project(tenant["id"], settings, projects)
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
    """Update a single scene's description, dialogue, etc."""
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
        context_parts.append(f"CENA ANTERIOR ({prev_scene['scene_number']}): {prev_scene.get('title','')} — {prev_scene.get('description','')}")
    if next_scene:
        context_parts.append(f"CENA SEGUINTE ({next_scene['scene_number']}): {next_scene.get('title','')} — {next_scene.get('description','')}")
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
}}"""

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
        avatar_descriptions = _analyze_avatars_with_vision(characters, char_avatars, avatar_cache, project_id)

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


