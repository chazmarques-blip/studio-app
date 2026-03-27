"""Auto-generated module from studio.py split."""
from ._shared import *

# ── STEP 1: Screenwriter Chat ──

SCREENWRITER_SYSTEM_PHASE1 = """You are a MASTER SCREENWRITER and WORLD-BUILDER.

TASK: Create a screenplay structure. Return ONLY valid JSON:
{{
  "title": "Story Title",
  "total_scenes": N,
  "characters": [
    {{"name": "Name", "description": "DETAILED physical: species/type, body shape, size, colors, textures (fur/skin/feathers), clothing/accessories, unique features", "age": "young/adult/old", "role": "protagonist/supporting"}}
  ],
  "scenes": [SCENES_HERE],
  "research_notes": "Sources used",
  "narration": "Brief context"
}}

Each scene:
{{"scene_number": N, "time_start": "M:SS", "time_end": "M:SS", "title": "Title", "description": "RICH visual: WHERE (landscape, nature), WHEN (time of day, weather), WHAT (action), ATMOSPHERE (light, colors)", "dialogue": "Text or narration", "characters_in_scene": ["Name"], "emotion": "mood", "camera": "shot type", "transition": "fade/cut"}}

RULES:
- Each scene = EXACTLY 12 seconds
- Max 8 scenes per response (if more needed, note it)
- Describe characters PHYSICALLY in detail with species-accurate features
- CRITICAL: If the story uses animals as characters, ALL descriptions MUST use animal features (fur, feathers, hooves, tails, snouts, paws). NEVER describe animal characters with human features (hands, fingers, human skin)
- Characters MUST maintain visually consistent appearance across ALL scenes — same colors, same clothing, same distinguishing marks
- Every scene description MUST include: specific location, time of day, atmosphere, background elements
- Be faithful to source material (bible, history, etc.)
- **LANGUAGE RULE (MANDATORY)**: ALL text content — title, scene titles, descriptions, dialogue, narration, research_notes — MUST be written ENTIRELY in {lang_name} ({lang}). Do NOT write in English unless the language IS English. This is NON-NEGOTIABLE."""

LANG_FULL_NAMES = {"pt": "Português (Brazilian Portuguese)", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "it": "Italiano"}


def _run_screenwriter_background(tenant_id: str, project_id: str, message: str, lang: str):
    """Background thread: call Claude screenwriter and save result. Uses chunked approach for reliability."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        chat_history = project.get("chat_history", [])

        history_text = "\n".join([
            f"{'USER' if m['role']=='user' else 'SCREENWRITER'}: {m['text'][:500]}"
            for m in chat_history[-6:]
        ])

        audio_mode = project.get("audio_mode", "narrated")

        system = SCREENWRITER_SYSTEM_PHASE1.replace("{lang}", lang).replace("{lang_name}", LANG_FULL_NAMES.get(lang, lang))

        # Inject audio mode context into prompt
        audio_instruction = ""
        lang_name = LANG_FULL_NAMES.get(lang, lang)
        if audio_mode == "dubbed":
            audio_instruction = f"""

AUDIO MODE: DUBBED (character voices + occasional narrator). The "dialogue" field MUST contain character dialogue lines IN {lang_name}. A narrator may also appear when needed to bridge scenes, explain time passages, or add emotional context — but the MAJORITY of the text should be character dialogue.
Format EXACTLY like this:
"dialogue": "Narrador: 'Naquela noite, sob o manto de estrelas...' / Abraão: 'Meu filho, vamos subir o monte juntos.' / Isaac: 'Sim, pai! Mas onde está o cordeiro?' / Abraão: 'Deus proverá, meu filho.'"

RULES for DUBBED mode:
- Each speaker must be prefixed with their name (or "Narrador") followed by colon
- Separate different speakers with " / "
- Character dialogue should be the MAJORITY (70%+) of the text
- Use "Narrador:" sparingly — only to introduce a scene, mark time passing, or add emotional weight
- Every scene MUST have at least one character speaking
- Keep dialogue natural, emotional, and age-appropriate for each character
- ALL dialogue and narration MUST be in {lang_name}"""
        else:
            audio_instruction = f"""

AUDIO MODE: NARRATED (voice-over narrator). The "dialogue" field should contain narrator text IN {lang_name}.
Format: "dialogue": "Narrador: 'Descrição do que acontece nesta cena...'"
- Use a storytelling narrator voice
- Keep narration concise (2-3 sentences per scene)
- ALL narration MUST be in {lang_name}"""

        # Detect if project already has scenes (continuation vs new screenplay)
        existing_scenes = project.get("scenes", [])
        is_continuation = len(existing_scenes) > 0

        if is_continuation:
            existing_summary = "\n".join([
                f"Scene {s.get('scene_number')}: {s.get('title')} ({s.get('time_start')}-{s.get('time_end')})"
                for s in existing_scenes
            ])
            last_scene_num = max(s.get("scene_number", 0) for s in existing_scenes)
            last_time_end = existing_scenes[-1].get("time_end", "0:00") if existing_scenes else "0:00"
            user_prompt = f"""Previous conversation:
{history_text}

EXISTING SCREENPLAY (already written — DO NOT rewrite these, only ADD new scenes):
{existing_summary}

The user now says: {message}
{audio_instruction}

CONTINUATION RULES:
- Scene numbers MUST start from {last_scene_num + 1}
- Time starts from {last_time_end} (each scene = 12 seconds)
- Keep the same characters, visual style, and narrative tone
- Return ONLY JSON with "scenes" array containing the NEW scenes (continuation only)
- Also return "characters" array with any NEW characters introduced (or empty array if none)
- Return "total_scenes" as the total number of NEW scenes in this batch
- ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}"""
        else:
            user_prompt = f"""Previous conversation:
{history_text}

Current request: {message}
{audio_instruction}

Create the screenplay. If the story needs more than 8 scenes, generate the first 8 now. Return ONLY valid JSON."""

        # Phase 1: Get first batch of scenes (up to 8)
        result = _call_claude_sync(system, user_prompt, max_tokens=6000)
        parsed = _parse_json(result)

        if not parsed:
            # Try to extract from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result)
            if json_match:
                parsed = _parse_json(json_match.group(1))

        # Re-read project (may have changed)
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        chat_history = project.get("chat_history", [])

        if parsed:
            all_scenes = parsed.get("scenes", [])
            all_characters = parsed.get("characters", [])
            total_needed = parsed.get("total_scenes", len(all_scenes))

            # Phase 2: If more scenes needed, generate continuation
            if total_needed > len(all_scenes):
                try:
                    continuation_prompt = f"""Continue the screenplay from scene {len(all_scenes) + 1} to {total_needed}.

Previous scenes already written:
{', '.join(f'Scene {s.get("scene_number")}: {s.get("title")}' for s in all_scenes)}

Characters: {', '.join(c.get('name','') for c in all_characters)}
Story: {message}

ALL text (titles, descriptions, dialogue) MUST be in {LANG_FULL_NAMES.get(lang, lang)}.
Return ONLY JSON with a "scenes" array containing the remaining scenes (same format)."""

                    cont_result = _call_claude_sync(system, continuation_prompt, max_tokens=3000)
                    cont_parsed = _parse_json(cont_result)
                    if not cont_parsed:
                        import re
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', cont_result)
                        if json_match:
                            cont_parsed = _parse_json(json_match.group(1))

                    if cont_parsed and cont_parsed.get("scenes"):
                        all_scenes.extend(cont_parsed["scenes"])
                        if cont_parsed.get("characters"):
                            existing_names = {c["name"] for c in all_characters}
                            for c in cont_parsed["characters"]:
                                if c.get("name") not in existing_names:
                                    all_characters.append(c)
                        logger.info(f"Studio [{project_id}]: Phase 2 added {len(cont_parsed['scenes'])} more scenes (total: {len(all_scenes)})")
                except Exception as e2:
                    logger.warning(f"Studio [{project_id}]: Phase 2 continuation failed: {e2}. Using {len(all_scenes)} scenes.")

            # Re-read existing scenes (project may have been re-fetched)
            prev_scenes = project.get("scenes", [])
            prev_scene_nums = {s.get("scene_number") for s in prev_scenes}
            new_scene_nums = {s.get("scene_number") for s in all_scenes}

            # Smart merge: if new scenes don't overlap with existing, append (continuation)
            if prev_scenes and new_scene_nums and not prev_scene_nums.intersection(new_scene_nums):
                merged_scenes = prev_scenes + all_scenes
                merged_scenes.sort(key=lambda x: x.get("scene_number", 0))
                project["scenes"] = merged_scenes
                # Merge characters (add new ones only)
                existing_char_names = {c.get("name") for c in project.get("characters", [])}
                for c in all_characters:
                    if c.get("name") not in existing_char_names:
                        project.get("characters", []).append(c)
                logger.info(f"Studio [{project_id}]: Merged {len(all_scenes)} new scenes with {len(prev_scenes)} existing (total: {len(merged_scenes)})")
            else:
                # Fresh screenplay or overlap — replace
                project["scenes"] = all_scenes
                project["characters"] = all_characters

            final_scenes = project["scenes"]
            final_characters = project.get("characters", [])

            project["agents_output"] = project.get("agents_output", {})
            project["agents_output"]["screenwriter"] = {
                "title": parsed.get("title", ""),
                "research_notes": parsed.get("research_notes", ""),
                "narration": parsed.get("narration", ""),
            }
            assistant_text = f"**{parsed.get('title', 'Roteiro')}** — {len(all_scenes)} {'novas cenas' if prev_scenes and not prev_scene_nums.intersection(new_scene_nums) else 'cenas'} (total: {len(final_scenes)})\n\n"
            for s in all_scenes:
                assistant_text += f"**CENA {s.get('scene_number','')}** ({s.get('time_start','')}-{s.get('time_end','')}) — {s.get('title','')}\n"
                assistant_text += f"_{s.get('description','')}_\n"
                if s.get('dialogue'):
                    assistant_text += f'"{s["dialogue"]}"\n'
                assistant_text += f"Personagens: {', '.join(s.get('characters_in_scene',[]))}\n\n"
            assistant_text += f"\n**Personagens identificados:** {', '.join(c.get('name','') for c in final_characters)}"
            if parsed.get("research_notes"):
                assistant_text += f"\n\n**Pesquisa:** {parsed['research_notes'][:300]}"
        else:
            assistant_text = result

        chat_history.append({"role": "assistant", "text": assistant_text})
        project["chat_history"] = chat_history[-20:]
        project["status"] = "scripting"
        project["chat_status"] = "done"
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        n_scenes = len(project.get('scenes', []))
        n_chars = len(project.get('characters', []))
        _add_milestone(project, "screenplay_created", f"Roteiro criado — {n_scenes} cenas, {n_chars} personagens")
        _save_project(tenant_id, settings, projects)

        logger.info(f"Studio [{project_id}]: Screenwriter done — {n_scenes} scenes")

    except Exception as e:
        logger.error(f"Studio [{project_id}] screenwriter error: {e}")
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["chat_status"] = "error"
            project["error"] = str(e)[:300]
            _save_project(tenant_id, settings, projects)


@router.post("/chat")
async def screenwriter_chat(req: ChatMessage, tenant=Depends(get_current_tenant)):
    """Start screenwriter in background (avoids K8s 60s proxy timeout)."""
    lang = req.language or "pt"

    if req.project_id:
        settings, projects, project = _get_project(tenant["id"], req.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        settings = _get_settings(tenant["id"])
        projects = settings.get("studio_projects", [])
        now = datetime.now(timezone.utc).isoformat()
        project = {
            "id": uuid.uuid4().hex[:12],
            "name": req.message[:50],
            "scene_type": "multi_scene",
            "briefing": req.message,
            "scenes": [],
            "characters": [],
            "chat_history": [],
            "agents_output": {},
            "agent_status": {},
            "outputs": [],
            "status": "scripting",
            "chat_status": "thinking",
            "error": None,
            "language": lang,
            "created_at": now,
            "updated_at": now,
        }
        projects.insert(0, project)

    # Save user message and set thinking status
    chat_history = project.get("chat_history", [])
    chat_history.append({"role": "user", "text": req.message})
    project["chat_history"] = chat_history[-20:]
    project["chat_status"] = "thinking"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)

    # Start background thread
    thread = threading.Thread(
        target=_run_screenwriter_background,
        args=(tenant["id"], project["id"], req.message, lang),
        daemon=True,
    )
    thread.start()

    return {
        "project_id": project["id"],
        "status": "thinking",
        "message": None,
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
    }



@router.post("/projects/{project_id}/reset-chat")
async def reset_chat(project_id: str, tenant=Depends(get_current_tenant)):
    """Reset a stuck chat_status back to 'idle' so user can retry."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["chat_status"] = "idle"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "chat_status": "idle"}


@router.post("/projects/{project_id}/retry-chat")
async def retry_chat(project_id: str, tenant=Depends(get_current_tenant)):
    """Retry the last user message in the screenwriter chat."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_history = project.get("chat_history", [])
    last_user_msg = None
    for m in reversed(chat_history):
        if m["role"] == "user":
            last_user_msg = m["text"]
            break

    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message to retry")

    project["chat_status"] = "thinking"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)

    lang = project.get("language", "pt")
    thread = threading.Thread(
        target=_run_screenwriter_background,
        args=(tenant["id"], project_id, last_user_msg, lang),
        daemon=True,
    )
    thread.start()

    return {"status": "thinking", "message": last_user_msg}



