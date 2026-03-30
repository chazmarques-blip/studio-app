"""Auto-generated module from studio.py split."""
from ._shared import *

# ── STEP 1: Screenwriter Chat ──

SCREENWRITER_SYSTEM_PHASE1 = """You are a MASTER SCREENWRITER and WORLD-BUILDER. You create RICH, DETAILED screenplays that honor the source material.

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
- There is NO LIMIT on the number of scenes or characters. Generate as many as the story NEEDS to be rich and faithful
- Generate up to 10 scenes per response. Set "total_scenes" to the FULL number the story needs. If more than 10, I will ask you to continue
- EVERY KEY NARRATIVE MOMENT deserves its OWN dedicated scene. NEVER compress multiple important events into a single scene
- Describe characters PHYSICALLY in detail with species-accurate features
- CRITICAL: If the story uses animals as characters, ALL descriptions MUST use animal features (fur, feathers, hooves, tails, snouts, paws). NEVER describe animal characters with human features (hands, fingers, human skin)
- Characters MUST maintain visually consistent appearance across ALL scenes — same colors, same clothing, same distinguishing marks
- Create as many UNIQUE characters as the story calls for — each with distinct visual identity. Secondary characters, crowds, and background characters ALL deserve proper names and descriptions
- Every scene description MUST include: specific location, time of day, atmosphere, background elements
- Be faithful to source material (bible, history, etc.). Cover the FULL arc of the story — beginning, development, climax, and resolution — with sufficient detail
- **LANGUAGE RULE (MANDATORY)**: ALL text content — title, scene titles, descriptions, dialogue, narration, research_notes — MUST be written ENTIRELY in {lang_name} ({lang}). Do NOT write in English unless the language IS English. This is NON-NEGOTIABLE.

RICHNESS GUIDELINES:
- A simple story (1-2 key events) → 5-8 scenes
- A medium story (3-5 key events) → 8-15 scenes
- A rich/epic story (biblical, historical, mythological) → 15-30+ scenes
- Each emotional beat, each location change, each character introduction = a new scene
- If in doubt, MORE scenes is better than fewer. The user wants depth, not summaries."""

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
- There is NO limit on new scenes or characters — generate as many as needed to enrich the story
- If the user asks to expand a specific part, create MULTIPLE detailed scenes for it
- Return ONLY JSON with "scenes" array containing the NEW scenes (continuation only)
- Also return "characters" array with any NEW characters introduced (or empty array if none)
- Return "total_scenes" as the total number of NEW scenes in this batch
- ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}"""
        else:
            user_prompt = f"""Previous conversation:
{history_text}

Current request: {message}
{audio_instruction}

Create the screenplay. Generate as many scenes and characters as the story NEEDS to be rich and complete — there is NO limit. If the story needs more than 10 scenes, generate the first 10 and set "total_scenes" to the full amount. Return ONLY valid JSON."""

        # Phase 1: Get first batch of scenes (up to 10)
        result = _call_claude_sync(system, user_prompt, max_tokens=8000)
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

            # Phase 2: Aggressive continuation loop — generate ALL remaining scenes
            max_continuation_rounds = 10  # Safety limit (10 rounds × 10 scenes = 100 scenes max)
            round_num = 0
            while total_needed > len(all_scenes) and round_num < max_continuation_rounds:
                round_num += 1
                remaining = total_needed - len(all_scenes)
                try:
                    scene_summary = '\n'.join(
                        f"Scene {s.get('scene_number')}: {s.get('title')}"
                        for s in all_scenes
                    )
                    char_names = ', '.join(c.get('name', '') for c in all_characters)

                    continuation_prompt = f"""Continue the screenplay. Generate scenes {len(all_scenes) + 1} to {total_needed}.

SCENES ALREADY WRITTEN ({len(all_scenes)} of {total_needed}):
{scene_summary}

Characters so far: {char_names}
Story: {message}

IMPORTANT:
- Generate up to 10 scenes in this batch
- Scene numbers start from {len(all_scenes) + 1}
- Time starts from {all_scenes[-1].get('time_end', '0:00')} (each scene = 12 seconds)
- Keep the same visual style, characters, and narrative tone
- Introduce NEW characters when the story calls for them — there is NO character limit
- If the story needs more key moments, add them. Be RICH and DETAILED
- ALL text (titles, descriptions, dialogue) MUST be in {LANG_FULL_NAMES.get(lang, lang)}
- Return ONLY JSON with "scenes" array and optionally "characters" array for NEW characters introduced"""

                    cont_result = _call_claude_sync(system, continuation_prompt, max_tokens=8000)
                    cont_parsed = _parse_json(cont_result)
                    if not cont_parsed:
                        import re
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', cont_result)
                        if json_match:
                            cont_parsed = _parse_json(json_match.group(1))

                    if cont_parsed and cont_parsed.get("scenes"):
                        new_scenes = cont_parsed["scenes"]
                        all_scenes.extend(new_scenes)
                        if cont_parsed.get("characters"):
                            existing_names = {c["name"] for c in all_characters}
                            for c in cont_parsed["characters"]:
                                if c.get("name") not in existing_names:
                                    all_characters.append(c)
                        # Update total_needed if Claude indicates more are needed
                        if cont_parsed.get("total_scenes") and cont_parsed["total_scenes"] > total_needed:
                            total_needed = cont_parsed["total_scenes"]
                        logger.info(f"Studio [{project_id}]: Continuation round {round_num} added {len(new_scenes)} scenes (total: {len(all_scenes)}/{total_needed})")
                    else:
                        logger.warning(f"Studio [{project_id}]: Continuation round {round_num} returned no scenes. Stopping.")
                        break
                except Exception as e2:
                    logger.warning(f"Studio [{project_id}]: Continuation round {round_num} failed: {e2}. Using {len(all_scenes)} scenes.")
                    break

            if round_num > 0:
                logger.info(f"Studio [{project_id}]: Screenplay complete — {len(all_scenes)} scenes, {len(all_characters)} characters after {round_num} continuation rounds")

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

    # Start background thread - USE PARALLEL GENERATION
    from .parallel_agents import generate_screenplay_parallel
    
    def _parallel_screenplay_wrapper():
        try:
            audio_mode = project.get("audio_mode", "narrated")
            result = generate_screenplay_parallel(
                tenant_id=tenant["id"],
                project_id=project["id"],
                user_prompt=req.message,
                lang=lang,
                audio_mode=audio_mode,
                max_scenes=50,
                batch_size=10,
                max_workers=3
            )
            _merge_screenplay_results(tenant["id"], project["id"], result)
        except Exception as e:
            logger.error(f"Parallel screenplay error: {e}, falling back")
            _run_screenwriter_background(tenant["id"], project["id"], req.message, lang)
    
    thread = threading.Thread(
        target=_parallel_screenplay_wrapper,
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


def _merge_screenplay_results(tenant_id: str, project_id: str, result: dict):
    """Merge parallel generation results"""
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        return
    
    existing_scenes = project.get("scenes", [])
    new_scenes = result.get("scenes", [])
    
    if existing_scenes:
        last_num = max(s.get("scene_number", 0) for s in existing_scenes)
        for ns in new_scenes:
            ns["scene_number"] = last_num + 1
            last_num += 1
        existing_scenes.extend(new_scenes)
    else:
        existing_scenes = new_scenes
    
    existing_chars = project.get("characters", [])
    existing_names = {c.get("name") for c in existing_chars}
    for new_char in result.get("characters", []):
        if new_char.get("name") not in existing_names:
            existing_chars.append(new_char)
    
    project["scenes"] = existing_scenes
    project["characters"] = existing_chars
    project["title"] = result.get("title", project.get("title", "Untitled"))
    
    chat_history = project.get("chat_history", [])
    chat_history.append({"role": "agent", "text": f"✅ {len(new_scenes)} cenas geradas!"})
    project["chat_history"] = chat_history[-20:]
    project["chat_status"] = "idle"
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    _save_project(tenant_id, settings, projects)



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



