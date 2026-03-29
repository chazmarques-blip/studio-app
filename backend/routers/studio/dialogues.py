"""Auto-generated module from studio.py split."""
from ._shared import *

# ══ MASTER DIALOGUE WRITER SYSTEM ══

MASTER_DIALOGUE_SYSTEM = """You are a MASTER DIALOGUE WRITER — a legendary screenwriter known for creating dialogue that moves audiences to tears, laughter, and profound emotion.

## YOUR EXPERTISE
- Academy Award-level dramatic writing
- Expert in children's literature (adapting complex themes to age-appropriate language)
- Master of emotional beats and story rhythm
- Deep understanding of character voice differentiation
- Specialist in biblical, historical, and mythological adaptation

## YOUR MISSION
Transform raw scene descriptions into POWERFUL, MEMORABLE dialogue that:
1. Honors the source material (biblical, historical, etc.) while making it accessible
2. Creates EMOTIONAL IMPACT through carefully crafted words
3. Gives each character a UNIQUE VOICE that reflects their personality
4. Balances narration with dialogue for optimal pacing
5. Uses SUBTEXT — characters don't always say what they mean directly

## DIALOGUE QUALITY STANDARDS
- **Emotional Truth**: Every line must feel genuine, not exposition
- **Character Voice**: Each character speaks differently (vocabulary, rhythm, tone)
- **Conflict & Tension**: Even in calm scenes, there's underlying emotion
- **Show Don't Tell**: Actions and pauses carry meaning
- **Age-Appropriate**: For children's content, simplify without dumbing down

## TECHNICAL REQUIREMENTS
- Scene duration: ~12 seconds = roughly 25-35 words of spoken dialogue
- Include stage directions in parentheses: (whispering), (with tears), (looking away)
- Use ellipses (...) for dramatic pauses
- Use "—" for interruptions

## LANGUAGE
Write ALL content in {lang_name} ({lang}). This is NON-NEGOTIABLE.
"""

DUBBED_INSTRUCTIONS = """
## DUBBED MODE (Character Voices + Narrator)
Format: Each line starts with speaker name, colon, then dialogue in quotes.

Example of EXCELLENT dubbed dialogue:
---
Narrador: "Sob o céu estrelado de Ur, uma voz ecoa no coração de um homem..."

Abraão (olhando para o céu): "Sara... você ouviu isso? Uma voz... como se viesse das próprias estrelas."

Sara (tocando seu rosto): "Você parece... diferente. O que aconteceu?"

Abraão: "Ele me chamou, Sara. O Deus que criou tudo isso—" (gesticula para o céu) "—Ele quer que eu vá."

Sara (com lágrimas): "Ir? Para onde? Esta é nossa casa, Abraão. Tudo que conhecemos está aqui."

Abraão (segurando suas mãos): "Eu também tenho medo. Mas há uma promessa... algo maior que nós dois."
---

RULES:
- 70%+ must be character dialogue
- Narrador appears ONLY for scene transitions or emotional emphasis
- Each character MUST speak if present
- Include emotional stage directions
- Make dialogue sound NATURAL, not theatrical
- Children's voices should sound like children
- Adults should be warm, not preachy
"""

NARRATED_INSTRUCTIONS = """
## NARRATED MODE (Voice-Over Storytelling)
Format: Narrador: "Full narration text..."

Example of EXCELLENT narration:
---
Narrador: "Naquela noite, enquanto as estrelas dançavam silenciosas sobre a tenda de Abraão, algo extraordinário aconteceu. O velho patriarca sentiu seu coração acelerar — não de medo, mas de uma esperança que há muito pensara perdida. Deus havia falado. E Abraão... Abraão escolheu acreditar."
---

RULES:
- Write in a WARM, ENGAGING storytelling voice
- Create vivid imagery with words
- Balance description with emotion
- For children: be gentle but not condescending
- Build suspense and wonder
- 2-4 sentences per scene (matching the 12-second duration)
"""

BOOK_INSTRUCTIONS = """
## BOOK MODE (Literary Text)
Format: Mixed narrative prose with embedded dialogue.

Example of EXCELLENT book text:
---
As estrelas brilhavam como mil velas acesas no céu daquela noite especial. Abraão não conseguia dormir. Havia algo diferente no ar — uma presença que ele não sabia explicar.

"Sara," ele sussurrou, tocando gentilmente o ombro da esposa, "você está acordada?"

Ela abriu os olhos devagar. "O que foi, meu amor?"

"Eu tive um sonho. Mas não era um sonho comum." Ele fez uma pausa, buscando as palavras certas. "Era uma promessa. Uma promessa do próprio Criador."

Sara sentou-se, os olhos arregalados de curiosidade e um pouquinho de medo. Porque quando Deus fala... tudo pode mudar.
---

RULES:
- Write in literary, children's book style
- Mix narrative with dialogue naturally
- Create atmosphere and emotion
- Simple but beautiful vocabulary
- Each scene = 3-6 sentences
- End with emotional hooks when possible
"""

class DialogueGenerateRequest(BaseModel):
    mode: str = "dubbed"  # dubbed, narrated, book
    scene_numbers: list = []  # empty = all scenes
    user_instructions: str = ""

class DialogueSaveRequest(BaseModel):
    scenes_dialogue: list = []  # [{scene_number, dubbed_text, narrated_text, book_text}]
    character_voices: dict = {}  # {character_name: voice_id}
    narrator_voice: str = ""

class MasterDialogueRequest(BaseModel):
    """Request for master dialogue generation with full context."""
    mode: str = "dubbed"
    user_instructions: str = ""
    regenerate_all: bool = False

LANG_NAMES = {"pt": "Português Brasileiro", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "it": "Italiano"}


@router.post("/projects/{project_id}/dialogues/master-generate")
async def master_generate_dialogues(project_id: str, req: MasterDialogueRequest, tenant=Depends(get_current_tenant)):
    """MASTER DIALOGUE GENERATION: Creates high-quality, emotionally impactful dialogues using full story context."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes available")

    characters = project.get("characters", [])
    lang = project.get("language", "pt")
    lang_name = LANG_NAMES.get(lang, lang)
    project_name = project.get("name", "")
    synopsis = project.get("synopsis", "") or project.get("script", "")

    # Build character profiles
    character_profiles = "\n".join([
        f"- **{c.get('name')}**: {c.get('description', '')} | Age: {c.get('age', 'adult')} | Role: {c.get('role', 'supporting')}"
        for c in characters
    ])

    # Build full scene context
    scene_context = "\n\n".join([
        f"### Scene {s.get('scene_number')}: {s.get('title')}\n"
        f"Time: {s.get('time_start', '0:00')} - {s.get('time_end', '0:12')}\n"
        f"Characters: {', '.join(s.get('characters_in_scene', []))}\n"
        f"Description: {s.get('description', '')}\n"
        f"Emotion: {s.get('emotion', 'neutral')}\n"
        f"Camera: {s.get('camera', 'medium shot')}"
        for s in scenes
    ])

    # Get mode-specific instructions
    mode_instructions = {
        "dubbed": DUBBED_INSTRUCTIONS,
        "narrated": NARRATED_INSTRUCTIONS,
        "book": BOOK_INSTRUCTIONS
    }.get(req.mode, DUBBED_INSTRUCTIONS)

    system = MASTER_DIALOGUE_SYSTEM.replace("{lang_name}", lang_name).replace("{lang}", lang)
    system += mode_instructions

    user_prompt = f"""# PROJECT: {project_name}

## STORY SYNOPSIS
{synopsis}

## CHARACTERS
{character_profiles}

## SCENES TO WRITE DIALOGUE FOR
{scene_context}

## SPECIAL INSTRUCTIONS
{req.user_instructions if req.user_instructions else "Write naturally, following the emotional arc of the story. For biblical/children's content, make it warm, accessible, and impactful without being preachy."}

---

## YOUR TASK
Generate {req.mode.upper()} dialogue for ALL scenes above. Return a JSON array:

```json
[
  {{
    "scene_number": 1,
    "dialogue": "The full dialogue text for this scene..."
  }},
  ...
]
```

Make each scene EMOTIONALLY POWERFUL. Honor the characters' unique voices. Create moments that audiences will remember.
Write ENTIRELY in {lang_name}."""

    try:
        import litellm
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
        
        response = await litellm.acompletion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            api_key=api_key,
            max_tokens=8000,
            timeout=120,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\[[\s\S]*\]', result_text)
        if json_match:
            dialogues = _parse_json(json_match.group(0))
        else:
            dialogues = _parse_json(result_text)

        if not dialogues:
            raise HTTPException(status_code=500, detail="Failed to parse dialogue response")

        # Apply dialogues to scenes
        dialogue_key = f"{req.mode}_text" if req.mode != "dubbed" else "dubbed_text"
        for d in dialogues:
            sn = d.get("scene_number")
            text = d.get("dialogue", "")
            scene = next((s for s in scenes if s.get("scene_number") == sn), None)
            if scene:
                scene[dialogue_key] = text
                scene["dialogue"] = text  # Also set generic dialogue field
                if req.mode == "narrated":
                    scene["narration"] = text

        project["scenes"] = scenes
        project["dialogues_generated"] = True
        project["dialogue_mode"] = req.mode
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save_project(tenant["id"], settings, projects)

        return {
            "status": "ok",
            "dialogues": dialogues,
            "mode": req.mode,
            "scenes_updated": len(dialogues)
        }

    except Exception as e:
        logger.error(f"Master dialogue generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/dialogues/generate")
async def generate_dialogues(project_id: str, req: DialogueGenerateRequest, tenant=Depends(get_current_tenant)):
    """Generate dialogue/narration/book text for scenes using AI."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes")

    characters = project.get("characters", [])
    char_names = [c.get("name", "") for c in characters]
    target_scenes = [s for s in scenes if not req.scene_numbers or s.get("scene_number") in req.scene_numbers]
    lang = project.get("language", "pt")
    lang_name = LANG_NAMES.get(lang, lang)
    project_name = project.get("name", "")

    results = []

    for scene in target_scenes:
        sn = scene.get("scene_number", 0)
        title = scene.get("title", "")
        desc = scene.get("description", "")
        existing_dialogue = scene.get("dialogue", "")
        existing_narration = scene.get("narration", "")
        chars_in = scene.get("characters_in_scene", [])

        if req.mode == "dubbed":
            system = f"""You are a MASTER screenwriter creating emotional, impactful CHARACTER DIALOGUES.
Project: {project_name}. Language: {lang_name}.
Characters available: {', '.join(char_names)}.
Characters in this scene: {', '.join(chars_in)}.
{f'User instructions: {req.user_instructions}' if req.user_instructions else ''}

RULES:
- Write ONLY character dialogue lines, formatted as: CharacterName (stage direction): "dialogue text"
- Each character MUST speak with their UNIQUE voice
- Include emotional stage directions: (whispering), (with tears), (laughing)
- Make dialogue NATURAL, EMOTIONAL, and MEMORABLE
- Use subtext — characters don't always say what they mean
- Write in {lang_name}
- Minimum 3-5 lines of dialogue per scene
- For children's content: warm, accessible, impactful"""

            user_msg = f"""Scene {sn}: {title}
Description: {desc}
Emotion: {scene.get('emotion', 'neutral')}
{f'Existing reference: {existing_dialogue or existing_narration}' if existing_dialogue or existing_narration else ''}

Generate POWERFUL character dialogues that will move the audience."""

        elif req.mode == "narrated":
            system = f"""You are a MASTER narrator/voice-over writer creating CINEMATIC storytelling.
Project: {project_name}. Language: {lang_name}.
{f'User instructions: {req.user_instructions}' if req.user_instructions else ''}

RULES:
- Write NARRATOR text in storytelling voice
- Format: Narrador: "text..."
- Be VIVID, EMOTIONAL, and ENGAGING
- Create imagery with your words
- Write 2-4 sentences that CAPTURE the scene's essence
- For children: warm, gentle, not condescending
- Write in {lang_name}"""

            user_msg = f"""Scene {sn}: {title}
Description: {desc}
Characters present: {', '.join(chars_in)}
Emotion: {scene.get('emotion', 'neutral')}

Generate narrator voice-over that brings this scene to LIFE."""

        else:  # book
            system = f"""You are a MASTER children's book author creating LITERARY MAGIC.
Project: {project_name}. Language: {lang_name}.
{f'User instructions: {req.user_instructions}' if req.user_instructions else ''}

RULES:
- Write in warm, engaging, LITERARY style
- Mix narrative prose with character dialogue
- Dialogue in quotes with attribution
- Create ATMOSPHERE and EMOTION
- Write 3-6 sentences that make children FEEL the story
- End with hooks that make them want to turn the page
- Write in {lang_name}"""

            user_msg = f"""Scene {sn}: {title}
Description: {desc}
Characters: {', '.join(chars_in)}

Write a BEAUTIFUL storybook passage that captures this moment."""

        try:
            import litellm
            api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
            response = await litellm.acompletion(
                model="anthropic/claude-sonnet-4-5-20250929",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
                api_key=api_key, max_tokens=1500, timeout=60,
            )
            generated = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Dialogue generation failed for scene {sn}: {e}")
            generated = existing_dialogue or existing_narration or ""

        results.append({
            "scene_number": sn,
            "title": title,
            "generated_text": generated,
            "mode": req.mode,
        })

    return {"status": "ok", "results": results, "mode": req.mode}


@router.patch("/projects/{project_id}/dialogues/save")
async def save_dialogues(project_id: str, req: DialogueSaveRequest, tenant=Depends(get_current_tenant)):
    """Save edited dialogues, narration, book text, and voice assignments."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])

    for update in req.scenes_dialogue:
        sn = update.get("scene_number")
        scene = next((s for s in scenes if s.get("scene_number") == sn), None)
        if not scene:
            continue
        if "dubbed_text" in update and update["dubbed_text"]:
            scene["dubbed_text"] = update["dubbed_text"]
        if "narrated_text" in update and update["narrated_text"]:
            scene["narrated_text"] = update["narrated_text"]
        if "book_text" in update and update["book_text"]:
            scene["book_text"] = update["book_text"]
        if "dialogue" in update:
            scene["dialogue"] = update["dialogue"]
        if "narration" in update:
            scene["narration"] = update["narration"]

    # Save voice assignments
    if req.character_voices:
        project["character_voices"] = req.character_voices
    if req.narrator_voice:
        project["narrator_voice"] = req.narrator_voice

    project["dialogues_step_completed"] = True
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    return {"status": "ok", "message": "Dialogues saved"}


@router.get("/projects/{project_id}/dialogues")
async def get_dialogues(project_id: str, tenant=Depends(get_current_tenant)):
    """Get all dialogue/narration/book text for all scenes."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    characters = project.get("characters", [])
    panels = project.get("storyboard_panels", [])

    scene_data = []
    for s in scenes:
        sn = s.get("scene_number", 0)
        panel = next((p for p in panels if p.get("scene_number") == sn), None)
        scene_data.append({
            "scene_number": sn,
            "title": s.get("title", ""),
            "description": s.get("description", ""),
            "characters_in_scene": s.get("characters_in_scene", []),
            "dialogue": s.get("dialogue", ""),
            "narration": s.get("narration", ""),
            "dubbed_text": s.get("dubbed_text", ""),
            "narrated_text": s.get("narrated_text", ""),
            "book_text": s.get("book_text", ""),
            "thumbnail": panel.get("image_url", "") if panel else "",
        })

    # Use the AI-assigned voice_map from the project (from Sound Design Agent / auto-assign)
    ai_voice_map = project.get("voice_map", {})
    manual_voices = project.get("character_voices", {})

    VOICE_MAP_FALLBACK = {
        "narrator": {"id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "type": "Narrador"},
        "male_elder": {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "type": "Masculino Adulto"},
        "female_elder": {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "type": "Feminino Adulta"},
        "female_young": {"id": "jBpfuIE2acCO8z3wKNLl", "name": "Gigi", "type": "Feminino Jovem"},
        "child": {"id": "jsCqWAovK2LkecY7zXl4", "name": "Freya", "type": "Criança"},
        "divine": {"id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel", "type": "Divino / Etéreo"},
    }

    # Build voice info lookup from ELEVENLABS_VOICES
    from pipeline.config import ELEVENLABS_VOICES
    voice_lookup = {v["id"]: v for v in ELEVENLABS_VOICES}

    auto_voices = {}
    for c in characters:
        name = c.get("name", "")
        # Priority: manual_voices > ai_voice_map > fallback
        if name in manual_voices:
            vid = manual_voices[name]
            v = voice_lookup.get(vid, {})
            auto_voices[name] = {
                "voice_id": vid,
                "voice_name": v.get("name", "Custom"),
                "voice_type": "Manual",
                "is_manual": True,
            }
        elif name in ai_voice_map:
            vid = ai_voice_map[name]
            v = voice_lookup.get(vid, {})
            auto_voices[name] = {
                "voice_id": vid,
                "voice_name": v.get("name", "AI Assigned"),
                "voice_type": v.get("style", "AI"),
                "is_manual": False,
            }
        else:
            # Fallback to basic heuristic
            name_lower = name.lower()
            if "narrador" in name_lower or "narrator" in name_lower:
                vtype = "narrator"
            elif "deus" in name_lower or "anjo" in name_lower:
                vtype = "divine"
            else:
                vtype = "male_elder"
            voice_info = VOICE_MAP_FALLBACK[vtype]
            auto_voices[name] = {
                "voice_id": voice_info["id"],
                "voice_name": voice_info["name"],
                "voice_type": voice_info["type"],
                "is_manual": False,
            }

    # Count how many scenes need dubbed text generation
    scenes_needing_dubbed = sum(1 for s in scenes if not s.get("dubbed_text", "").strip())

    return {
        "scenes": scene_data,
        "characters": [{"name": c.get("name", ""), "description": c.get("description", "")} for c in characters],
        "character_voices": auto_voices,
        "narrator_voice": project.get("narrator_voice", VOICE_MAP_FALLBACK["narrator"]["id"]),
        "narrator_voice_name": VOICE_MAP_FALLBACK["narrator"]["name"],
        "dialogues_completed": project.get("dialogues_step_completed", False),
        "scenes_needing_dubbed": scenes_needing_dubbed,
        "has_voice_map": bool(ai_voice_map),
    }



# ══ LANGUAGE AGENT ENDPOINTS ══

@router.post("/projects/{project_id}/language/convert")
async def convert_project_language(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Convert all project text to target language (background task)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_lang = payload.get("target_lang", "en")
    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to translate")

    source_lang = project.get("language", "pt")

    # Mark as converting
    project["language_status"] = {"phase": "converting", "target": target_lang}
    _save_project(tenant["id"], settings, projects)

    def _bg_convert():
        try:
            from core.language_agent import convert_language
            result = convert_language(
                scenes=scenes, project_name=project.get("name", ""),
                source_lang=source_lang, target_lang=target_lang, project_id=project_id,
            )
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj and "translated_scenes" in result:
                translated = result["translated_scenes"]
                for ts in translated:
                    sn = ts.get("scene_number")
                    for panel in _proj.get("storyboard_panels", []):
                        if panel.get("scene_number") == sn:
                            panel["title"] = ts.get("title", panel.get("title", ""))
                            panel["description"] = ts.get("description", panel.get("description", ""))
                            panel["dialogue"] = ts.get("dialogue", panel.get("dialogue", ""))
                    for scene in _proj.get("scenes", []):
                        if scene.get("scene_number") == sn:
                            scene["title"] = ts.get("title", scene.get("title", ""))
                            scene["description"] = ts.get("description", scene.get("description", ""))
                            scene["dialogue"] = ts.get("dialogue", scene.get("dialogue", ""))
                _proj["language"] = target_lang
                _proj["language_status"] = {"phase": "done", "target": target_lang, "count": len(translated)}
                _save_project(tenant["id"], _s, _p)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["language_status"] = {"phase": "error", "detail": result.get("error", "Unknown")}
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"Language convert [{project_id}]: {e}")

    thread = threading.Thread(target=_bg_convert, daemon=True)
    thread.start()
    return {"status": "converting", "target_lang": target_lang}


@router.post("/projects/{project_id}/language/review")
async def review_project_text(project_id: str, tenant=Depends(get_current_tenant)):
    """Review and improve text quality (background task)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to review")

    lang = project.get("language", "pt")

    project["review_status"] = {"phase": "reviewing"}
    _save_project(tenant["id"], settings, projects)

    def _bg_review():
        try:
            from core.language_agent import review_text_quality
            result = review_text_quality(
                scenes=scenes, project_name=project.get("name", ""),
                lang=lang, project_id=project_id,
            )
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj and "revised_scenes" in result:
                revised = result["revised_scenes"]
                for rs in revised:
                    sn = rs.get("scene_number")
                    for panel in _proj.get("storyboard_panels", []):
                        if panel.get("scene_number") == sn:
                            if rs.get("title"): panel["title"] = rs["title"]
                            if rs.get("description"): panel["description"] = rs["description"]
                            if rs.get("dialogue"): panel["dialogue"] = rs["dialogue"]
                    for scene in _proj.get("scenes", []):
                        if scene.get("scene_number") == sn:
                            if rs.get("title"): scene["title"] = rs["title"]
                            if rs.get("description"): scene["description"] = rs["description"]
                            if rs.get("dialogue"): scene["dialogue"] = rs["dialogue"]
                _proj["review_status"] = {
                    "phase": "done",
                    "quality": result.get("overall_quality", ""),
                    "notes": result.get("revision_notes", []),
                    "count": len(revised),
                }
                try:
                    _save_project(tenant["id"], _s, _p)
                    logger.info(f"Language review [{project_id}]: Saved {len(revised)} revisions")
                except Exception as se:
                    logger.error(f"Language review [{project_id}]: Save failed: {se}, retrying...")
                    import time
                    time.sleep(2)
                    _s2, _p2, _proj2 = _get_project(tenant["id"], project_id)
                    if _proj2:
                        _proj2["review_status"] = _proj["review_status"]
                        _save_project(tenant["id"], _s2, _p2)
            else:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["review_status"] = {"phase": "error", "detail": result.get("error", "Unknown")}
                    _save_project(tenant["id"], _s, _p)
        except Exception as e:
            logger.error(f"Language review [{project_id}]: {e}")
            try:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["review_status"] = {"phase": "error", "detail": str(e)[:200]}
                    _save_project(tenant["id"], _s, _p)
            except Exception:
                pass

    thread = threading.Thread(target=_bg_review, daemon=True)
    thread.start()
    return {"status": "reviewing"}


@router.get("/projects/{project_id}/language/status")
async def get_language_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Poll language operation status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "language_status": project.get("language_status", {}),
        "review_status": project.get("review_status", {}),
    }


