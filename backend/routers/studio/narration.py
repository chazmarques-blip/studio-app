"""Auto-generated module from studio.py split."""
from ._shared import *

# ── Voice & Music Library ──

@router.get("/voices")
async def get_voices(user=Depends(get_current_user)):
    return {"voices": ELEVENLABS_VOICES}


class VoicePreviewRequest(BaseModel):
    voice_id: str
    text: str = "Olá, esta é a minha voz."


@router.post("/voice-preview")
async def preview_voice(req: VoicePreviewRequest, user=Depends(get_current_user)):
    """Generate a short TTS sample for voice preview. Returns audio/mpeg blob."""
    from fastapi.responses import Response
    if not req.voice_id:
        raise HTTPException(status_code=400, detail="voice_id is required")
    sample_text = req.text[:200]  # limit to 200 chars for preview
    try:
        audio_bytes = _generate_narration_audio(
            text=sample_text,
            voice_id=req.voice_id,
            stability=0.5,
            similarity=0.8,
            style_val=0.5,
        )
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Voice preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice preview failed: {str(e)[:100]}")


@router.get("/music-library")
async def get_music_library(user=Depends(get_current_user)):
    tracks = [{"id": k, **v} for k, v in MUSIC_LIBRARY.items()]
    return {"tracks": tracks}


# ── Intelligent Voice Assignment (Claude) ──

class AutoAssignVoicesRequest(BaseModel):
    project_id: str


@router.post("/projects/{project_id}/auto-assign-voices")
async def auto_assign_voices(project_id: str, tenant=Depends(get_current_tenant)):
    """
    Use SOUND DESIGNER AGENT to intelligently assign voices based on:
    - Species/character type (bird, lion, dolphin, human, etc.)
    - Physical characteristics (size, build)
    - Age (child, adult, elder)
    - Personality (playful, wise, energetic, etc.)
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", [])
    if not characters:
        raise HTTPException(status_code=400, detail="No characters in project")

    logger.info(f"SoundDesigner [{project_id}]: Starting intelligent voice assignment for {len(characters)} characters")

    try:
        from .sound_design_agent import auto_assign_voices_with_sound_designer
        
        # Use Sound Designer Agent for intelligent assignment
        result = await auto_assign_voices_with_sound_designer(
            project_id=project_id,
            tenant_id=tenant["id"],
            available_voices=ELEVENLABS_VOICES
        )
        
        voice_map = result["voice_map"]
        detailed_assignments = result["detailed_assignments"]
        stats = result["stats"]
        
        # Save to project
        _update_project_field(tenant["id"], project_id, {"voice_map": voice_map})

        # Build detailed response
        voice_lookup = {v['id']: v for v in ELEVENLABS_VOICES}
        assignments_with_details = []
        
        for assignment in detailed_assignments:
            char_name = assignment["character_name"]
            voice_id = assignment["voice_id"]
            voice_info = voice_lookup.get(voice_id, {})
            
            assignments_with_details.append({
                "character": char_name,
                "voice_id": voice_id,
                "voice_name": voice_info.get("name", "Unknown"),
                "voice_gender": voice_info.get("gender", ""),
                "voice_accent": voice_info.get("accent", ""),
                "confidence": assignment["confidence"],
                "reasoning": assignment["reasoning"],
                "characteristics": assignment.get("voice_characteristics", {}),
                "status": assignment["status"]
            })

        logger.info(f"SoundDesigner [{project_id}]: Complete - {stats['unique_voices_used']} unique voices assigned")

        return {
            "voice_map": voice_map,
            "assignments": assignments_with_details,
            "stats": stats,
            "message": f"✅ {len(voice_map)} personagens receberam vozes inteligentes! "
                      f"({stats['unique_voices_used']} vozes únicas, "
                      f"{stats['fallbacks']} fallbacks)"
        }

    except Exception as e:
        logger.error(f"SoundDesigner error: {e}")
        # Fallback to old simple assignment
        logger.warning(f"Falling back to simple voice assignment")
        return await auto_assign_voices_simple(project_id, tenant)
            voice_details[char_name] = {
                "voice_id": vid,
                "voice_name": v.get("name", "Unknown"),
                "gender": v.get("gender", "?"),
                "accent": v.get("accent", "?"),
                "style": v.get("style", "?"),
            }

        logger.info(f"Studio [{project_id}]: AI Voice Assignment — {len(voice_map)} characters mapped")
        return {"voice_map": voice_map, "voice_details": voice_details}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Studio [{project_id}]: Auto-assign voices failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice assignment failed: {str(e)[:150]}")


async def auto_assign_voices_simple(project_id: str, tenant: dict):
    """Simple fallback voice assignment (old method)"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    characters = project.get("characters", [])
    
    # Simple rule-based assignment
    voice_map = {}
    for char in characters:
        name = char.get("name", "")
        desc = char.get("description", "").lower()
        
        # Simple heuristics
        if any(word in desc for word in ["bird", "pássaro", "ave"]):
            voice_map[name] = "pNInz6obpgDQGcFmaJgB"  # Adam - higher pitched
        elif any(word in desc for word in ["lion", "leão", "tiger"]):
            voice_map[name] = "N2lVS1w4EtoT3dr4eOWO"  # Callum - deep
        else:
            voice_map[name] = "21m00Tcm4TlvDq8ikWAM"  # Rachel - default
    
    _update_project_field(tenant["id"], project_id, {"voice_map": voice_map})
    
    return {"voice_map": voice_map, "message": "Simple assignment completed"}



class UpdateVoiceMapRequest(BaseModel):
    voice_map: dict  # {character_name: voice_id}


@router.post("/projects/{project_id}/voice-map")
async def update_voice_map(project_id: str, req: UpdateVoiceMapRequest, tenant=Depends(get_current_tenant)):
    """Manually update voice assignments for characters."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Merge with existing map
    existing = project.get("voice_map", {})
    existing.update(req.voice_map)
    _update_project_field(tenant["id"], project_id, {"voice_map": existing})

    # Build response with voice details
    voice_lookup = {v['id']: v for v in ELEVENLABS_VOICES}
    voice_details = {}
    for char_name, vid in existing.items():
        v = voice_lookup.get(vid, {})
        voice_details[char_name] = {
            "voice_id": vid,
            "voice_name": v.get("name", "Unknown"),
            "gender": v.get("gender", "?"),
            "accent": v.get("accent", "?"),
            "style": v.get("style", "?"),
        }

    return {"voice_map": existing, "voice_details": voice_details}


@router.get("/projects/{project_id}/voice-map")
async def get_voice_map(project_id: str, tenant=Depends(get_current_tenant)):
    """Get current voice assignments for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    voice_map = project.get("voice_map", {})
    voice_lookup = {v['id']: v for v in ELEVENLABS_VOICES}
    voice_details = {}
    for char_name, vid in voice_map.items():
        v = voice_lookup.get(vid, {})
        voice_details[char_name] = {
            "voice_id": vid,
            "voice_name": v.get("name", "Unknown"),
            "gender": v.get("gender", "?"),
            "accent": v.get("accent", "?"),
            "style": v.get("style", "?"),
        }

    return {"voice_map": voice_map, "voice_details": voice_details}


# ── Sound Design Agent (Agente de Sonoplastia IA) ──

class DesignCharacterVoiceRequest(BaseModel):
    character_name: str
    preview_text: str = ""  # optional custom preview text


@router.post("/projects/{project_id}/design-character-voice")
async def design_character_voice(project_id: str, req: DesignCharacterVoiceRequest, tenant=Depends(get_current_tenant)):
    """Sound Design Agent: Analyze a character and generate 3 custom voice previews using ElevenLabs Voice Design."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")

    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the character
    characters = project.get("characters", [])
    char = next((c for c in characters if c.get("name") == req.character_name), None)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{req.character_name}' not found")

    lang = project.get("language", "pt")
    LANG_NAMES = {"pt": "Portuguese", "en": "English", "es": "Spanish"}

    # Step 1: Claude analyzes the character and writes the ideal voice description
    system_prompt = """You are an elite SOUND DESIGN DIRECTOR for animated films. Your specialty is CASTING — finding the PERFECT voice for each character based on their visual appearance, personality, role, and species.

Given a character's details, write a VOICE DESIGN PROMPT (100-800 characters) that will be used to generate a custom AI voice. The prompt must describe the IDEAL vocal qualities for this character.

RULES:
1. Describe the voice in ENGLISH (the AI voice generator only understands English prompts)
2. Include: age range, gender, vocal texture, energy level, emotional tone, speaking style
3. For ANIMAL characters: describe how the animal's nature should influence the voice (e.g., a lion should have a deep resonant voice, a rabbit should be light and quick)
4. For CHILD/YOUNG characters: specify youthful, lighter vocal qualities
5. For VILLAIN/ANTAGONIST characters: add menacing, seductive, or unsettling qualities
6. For NARRATOR characters: warm, storytelling, authoritative
7. Be VERY specific about unique qualities that make this voice MEMORABLE and DISTINCT
8. The voice must feel like it BELONGS to this character — when people hear it, they should immediately picture the character

Return ONLY the voice description text, nothing else. No JSON, no labels."""

    char_info = f"""Character: {char.get('name', '?')}
Description: {char.get('description', 'No description')}
Role: {char.get('role', '?')}
Age: {char.get('age', '?')}
Story: {project.get('briefing', '')[:300]}
Language of the project: {LANG_NAMES.get(lang, lang)}"""

    try:
        voice_description = _call_claude_sync(system_prompt, char_info, max_tokens=500)
        voice_description = voice_description.strip().strip('"').strip("'")
        # Ensure it's within limits
        if len(voice_description) < 100:
            voice_description = voice_description + ". A distinctive, memorable voice with clear emotional range and natural expressiveness."
        if len(voice_description) > 1000:
            voice_description = voice_description[:997] + "..."

        logger.info(f"Studio [{project_id}]: Sound Agent voice description for {req.character_name}: {voice_description[:100]}...")

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Sound Agent Claude analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)[:150]}")

    # Step 2: Generate voice previews using ElevenLabs Voice Design
    try:
        from elevenlabs import ElevenLabs as ELClient
        client = ELClient(api_key=elevenlabs_key)

        # Use a sample dialogue line from the character, or a default
        preview_text = req.preview_text
        if not preview_text:
            # Find a dialogue line from the scenes for this character
            scenes = project.get("scenes", [])
            for s in scenes:
                dialogue = s.get("dialogue", "")
                if req.character_name.lower() in dialogue.lower() and ":" in dialogue:
                    parts = [p.strip() for p in dialogue.split(" / ")]
                    for part in parts:
                        if req.character_name.lower() in part.split(":")[0].lower():
                            text = ":".join(part.split(":")[1:]).strip().strip("'\"")
                            if len(text) > 10:
                                preview_text = text[:200]
                                break
                if preview_text:
                    break

        result = client.text_to_voice.create_previews(
            voice_description=voice_description,
            text=preview_text if preview_text else None,
            auto_generate_text=not bool(preview_text),
            loudness=0.0,
            quality=0.8,
            guidance_scale=0.5,
        )

        previews = []
        for p in result.previews:
            previews.append({
                "generated_voice_id": p.generated_voice_id,
                "audio_base64": p.audio_base_64,
                "duration_secs": p.duration_secs,
                "media_type": p.media_type,
            })

        logger.info(f"Studio [{project_id}]: Sound Agent generated {len(previews)} voice previews for {req.character_name}")

        # Save the voice description and previews for this character
        designed_voices = project.get("designed_voices", {})
        designed_voices[req.character_name] = {
            "voice_description": voice_description,
            "previews": [{"generated_voice_id": p["generated_voice_id"], "duration_secs": p["duration_secs"]} for p in previews],
        }
        _update_project_field(tenant["id"], project_id, {"designed_voices": designed_voices})

        return {
            "character_name": req.character_name,
            "voice_description": voice_description,
            "previews": previews,
            "preview_text": result.text,
        }

    except Exception as e:
        logger.error(f"Studio [{project_id}]: ElevenLabs Voice Design failed for {req.character_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Voice design failed: {str(e)[:200]}")


class SelectDesignedVoiceRequest(BaseModel):
    character_name: str
    generated_voice_id: str
    voice_name: str = ""  # optional name for the saved voice


@router.post("/projects/{project_id}/select-designed-voice")
async def select_designed_voice(project_id: str, req: SelectDesignedVoiceRequest, tenant=Depends(get_current_tenant)):
    """Save a designed voice preview as a permanent voice and assign it to the character."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")

    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        from elevenlabs import ElevenLabs as ELClient
        client = ELClient(api_key=elevenlabs_key)

        # Get the voice description from stored data
        designed = project.get("designed_voices", {}).get(req.character_name, {})
        voice_desc = designed.get("voice_description", req.character_name)
        voice_name = req.voice_name or f"AgentZZ_{req.character_name}"

        # Save the preview as a permanent voice
        voice = client.text_to_voice.create(
            voice_name=voice_name,
            voice_description=voice_desc[:500],
            generated_voice_id=req.generated_voice_id,
        )

        # Update the voice map with the new permanent voice ID
        voice_map = project.get("voice_map", {})
        voice_map[req.character_name] = voice.voice_id
        _update_project_field(tenant["id"], project_id, {"voice_map": voice_map})

        logger.info(f"Studio [{project_id}]: Saved designed voice for {req.character_name}: {voice.voice_id} ({voice_name})")

        return {
            "character_name": req.character_name,
            "voice_id": voice.voice_id,
            "voice_name": voice_name,
            "status": "saved",
        }

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Save designed voice failed: {e}")
        raise HTTPException(status_code=500, detail=f"Save voice failed: {str(e)[:200]}")


class RemixVoiceRequest(BaseModel):
    character_name: str
    voice_description: str  # What to change (e.g., "make it deeper", "add Brazilian accent")
    prompt_strength: float = 0.5  # 0 = minimal change, 1 = maximum change
    preview_text: str = ""


@router.post("/projects/{project_id}/remix-voice")
async def remix_voice(project_id: str, req: RemixVoiceRequest, tenant=Depends(get_current_tenant)):
    """Voice Remix: Adjust an existing voice's characteristics (pitch, accent, tone) without creating from scratch."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")

    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get the current voice for this character
    voice_map = project.get("voice_map", {})
    current_voice_id = voice_map.get(req.character_name)
    if not current_voice_id:
        raise HTTPException(status_code=400, detail=f"No voice assigned to '{req.character_name}'. Assign one first.")

    # Find a dialogue line for preview text
    preview_text = req.preview_text
    if not preview_text:
        scenes = project.get("scenes", [])
        for s in scenes:
            dialogue = s.get("dubbed_text", "") or s.get("dialogue", "")
            if req.character_name.lower() in dialogue.lower() and ":" in dialogue:
                parts = [p.strip() for p in dialogue.split(" / ")]
                for part in parts:
                    if req.character_name.lower() in part.split(":")[0].lower():
                        text = ":".join(part.split(":")[1:]).strip().strip("'\"")
                        if len(text) > 10:
                            preview_text = text[:200]
                            break
            if preview_text:
                break

    try:
        from elevenlabs import ElevenLabs as ELClient
        client = ELClient(api_key=elevenlabs_key)

        result = client.text_to_voice.remix(
            voice_id=current_voice_id,
            voice_description=req.voice_description,
            text=preview_text if preview_text else None,
            auto_generate_text=not bool(preview_text),
            prompt_strength=max(0.0, min(1.0, req.prompt_strength)),
            guidance_scale=2.0,
            loudness=0.0,
        )

        previews = []
        for p in result.previews:
            previews.append({
                "generated_voice_id": p.generated_voice_id,
                "audio_base64": p.audio_base_64,
                "duration_secs": p.duration_secs,
                "media_type": p.media_type,
            })

        logger.info(f"Studio [{project_id}]: Voice Remix for {req.character_name}: {len(previews)} previews ({req.voice_description[:60]})")

        return {
            "character_name": req.character_name,
            "original_voice_id": current_voice_id,
            "remix_description": req.voice_description,
            "prompt_strength": req.prompt_strength,
            "previews": previews,
            "preview_text": result.text,
        }

    except Exception as e:
        logger.error(f"Studio [{project_id}]: Voice Remix failed for {req.character_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Voice remix failed: {str(e)[:200]}")


@router.post("/projects/{project_id}/design-all-voices")
async def design_all_voices(project_id: str, tenant=Depends(get_current_tenant)):
    """Sound Design Agent: Run the full analysis for ALL characters and return voice previews for each."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")

    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", [])
    if not characters:
        raise HTTPException(status_code=400, detail="No characters in project")

    lang = project.get("language", "pt")
    LANG_NAMES = {"pt": "Portuguese", "en": "English", "es": "Spanish"}

    # Step 1: ONE Claude call to analyze ALL characters and write voice descriptions
    system_prompt = """You are an elite SOUND DESIGN DIRECTOR for animated films. Your specialty is VOICE CASTING — finding the PERFECT voice for each character.

For EACH character, write a VOICE DESIGN PROMPT (100-500 chars each) that will generate a custom AI voice. Prompts must be in ENGLISH.

RULES:
1. Each voice must be DISTINCT and MEMORABLE — no two characters should sound similar
2. For ANIMAL characters: the animal's nature MUST influence the voice (lion=deep, rabbit=quick/light, snake=breathy/sibilant)
3. Include: age, gender, vocal texture, energy, tone, speaking style, unique qualities
4. Consider the character's ROLE in the story (hero, villain, comic relief, wise mentor, etc.)
5. Think about CONTRAST between characters — if one is deep, make another high; if one is slow, make another fast
6. The voice should make the character INSTANTLY recognizable

Return ONLY valid JSON:
{"CharacterName": "voice description prompt in English", ...}"""

    char_list = "\n".join([
        f"- {c.get('name', '?')}: {c.get('description', 'No description')} | Role: {c.get('role', '?')} | Age: {c.get('age', '?')}"
        for c in characters
    ])

    user_prompt = f"""Project: {project.get('name', 'Untitled')}
Story: {project.get('briefing', '')[:400]}
Language: {LANG_NAMES.get(lang, lang)}

CHARACTERS TO CAST:
{char_list}

Design the PERFECT voice for each character. Make each voice UNIQUE and INSTANTLY recognizable."""

    try:
        result = _call_claude_sync(system_prompt, user_prompt, max_tokens=4000)
        import json as json_mod
        parsed = _parse_json(result)
        if not parsed:
            raise HTTPException(status_code=500, detail="Failed to parse voice descriptions")

        logger.info(f"Studio [{project_id}]: Sound Agent analyzed {len(parsed)} characters")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)[:150]}")

    # Step 2: Generate voice previews for each character
    from elevenlabs import ElevenLabs as ELClient
    client = ELClient(api_key=elevenlabs_key)
    scenes = project.get("scenes", [])

    all_results = {}
    designed_voices = project.get("designed_voices", {})

    for char in characters:
        name = char.get("name", "")
        desc = parsed.get(name, "")
        if not desc:
            # Try fuzzy match
            for k, v in parsed.items():
                if k.lower() in name.lower() or name.lower() in k.lower():
                    desc = v
                    break
        if not desc:
            continue

        # Ensure minimum length
        if len(desc) < 100:
            desc = desc + ". A distinctive, memorable voice with clear emotional range and natural expressiveness suitable for animation."

        # Find a dialogue line for preview
        preview_text = ""
        for s in scenes:
            dialogue = s.get("dialogue", "")
            if name.lower() in dialogue.lower() and ":" in dialogue:
                parts = [p.strip() for p in dialogue.split(" / ")]
                for part in parts:
                    if name.lower() in part.split(":")[0].lower():
                        text = ":".join(part.split(":")[1:]).strip().strip("'\"")
                        if len(text) > 10:
                            preview_text = text[:200]
                            break
            if preview_text:
                break

        try:
            result = client.text_to_voice.create_previews(
                voice_description=desc[:1000],
                text=preview_text if preview_text else None,
                auto_generate_text=not bool(preview_text),
                loudness=0.0,
                quality=0.8,
                guidance_scale=0.5,
            )

            previews = []
            for p in result.previews:
                previews.append({
                    "generated_voice_id": p.generated_voice_id,
                    "audio_base64": p.audio_base_64,
                    "duration_secs": p.duration_secs,
                    "media_type": p.media_type,
                })

            all_results[name] = {
                "voice_description": desc,
                "previews": previews,
                "preview_text": result.text,
            }

            designed_voices[name] = {
                "voice_description": desc,
                "previews": [{"generated_voice_id": p["generated_voice_id"], "duration_secs": p["duration_secs"]} for p in previews],
            }

            logger.info(f"Studio [{project_id}]: Sound Agent — {name}: {len(previews)} previews ({desc[:60]}...)")

        except Exception as e:
            logger.warning(f"Studio [{project_id}]: Voice Design failed for {name}: {e}")
            all_results[name] = {"voice_description": desc, "previews": [], "error": str(e)[:100]}

    # Save all designed voices
    _update_project_field(tenant["id"], project_id, {"designed_voices": designed_voices})

    return {
        "total_characters": len(characters),
        "designed": len([r for r in all_results.values() if r.get("previews")]),
        "results": all_results,
    }


# ── Narration Generation (ElevenLabs) ──

def _generate_narration_audio(text: str, voice_id: str, stability: float, similarity: float, style_val: float, language_code: str = "") -> bytes:
    """Generate narration audio using ElevenLabs TTS. Returns mp3 bytes."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise RuntimeError("ELEVENLABS_API_KEY not configured")

    from elevenlabs import ElevenLabs as ELClient, VoiceSettings

    client = ELClient(api_key=elevenlabs_key)
    voice_settings = VoiceSettings(
        stability=stability,
        similarity_boost=similarity,
        style=style_val,
        use_speaker_boost=True,
    )

    # Map language codes to ElevenLabs language hints (ISO 639-1 for multilingual_v2)
    LANG_HINTS = {
        "pt": "pt", "en": "en", "es": "es",
        "fr": "fr", "de": "de", "it": "it",
    }
    lang_hint = LANG_HINTS.get(language_code, "")

    kwargs = {
        "text": text,
        "voice_id": voice_id,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings,
    }
    if lang_hint:
        kwargs["language_code"] = lang_hint

    audio_gen = client.text_to_speech.convert(**kwargs)
    audio_bytes = b""
    for chunk in audio_gen:
        audio_bytes += chunk
    return audio_bytes


def _run_narration_background(tenant_id: str, project_id: str, voice_id: str, stability: float, similarity: float, style_val: float):
    """Background: generate narration for each scene and save to project.
    In 'dubbed' mode: parses character lines, uses different voices per character, and concatenates."""
    import tempfile

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        lang = project.get("language", "pt")
        audio_mode = project.get("audio_mode", "narrated")

        _update_project_field(tenant_id, project_id, {
            "narration_status": {"phase": "generating_script", "done": 0, "total": len(scenes)},
        })

        # ── DUBBED MODE: Use scene dialogues directly (already have character lines) ──
        if audio_mode == "dubbed":
            # Use the AI-assigned voice_map from the project (set by auto-assign-voices endpoint)
            voice_map = project.get("voice_map", {})

            # Fallback: if no voice_map exists, create basic one
            if not voice_map:
                DUBBED_VOICES = {
                    "narrator": voice_id,
                    "male_elder": "VR6AewLTigWG4xSOukaG",
                    "male_young": "pNInz6obpgDQGcFmaJgB",
                    "female_elder": "EXAVITQu4vr4xnSDxMaL",
                    "female_young": "jBpfuIE2acCO8z3wKNLl",
                    "child": "jsCqWAovK2LkecY7zXl4",
                    "angel": "onwK4e9ZLuTAKqWW03F9",
                }
                characters = project.get("characters", [])
                for c in characters:
                    name = c.get("name", "")
                    n = name.lower()
                    if "narrador" in n:
                        voice_map[name] = DUBBED_VOICES["narrator"]
                    elif any(k in n for k in ["anjo", "angel", "deus", "god"]):
                        voice_map[name] = DUBBED_VOICES["angel"]
                    elif any(k in n for k in ["criança", "bebê", "bebe", "child"]):
                        voice_map[name] = DUBBED_VOICES["child"]
                    else:
                        voice_map[name] = DUBBED_VOICES["male_elder"]
                voice_map["Narrador"] = DUBBED_VOICES["narrator"]
                voice_map["Deus"] = DUBBED_VOICES["angel"]

            logger.info(f"Studio [{project_id}]: DUBBED mode — {len(voice_map)} character voices mapped")

            narration_outputs = []
            for i, scene in enumerate(scenes):
                scene_num = scene.get("scene_number", i + 1)
                dialogue = scene.get("dialogue", "")
                if not dialogue.strip():
                    narration_outputs.append({"scene_number": scene_num, "narration": "", "audio_url": None})
                    continue

                try:
                    # Parse character lines: "Narrador: '...' / Abraão: '...' / Isaac: '...'"
                    parts = [p.strip() for p in dialogue.split(" / ")]
                    audio_clips = []

                    with tempfile.TemporaryDirectory() as tmpdir:
                        for pi, part in enumerate(parts):
                            # Extract character name and text
                            if ":" in part:
                                char_name_raw = part.split(":")[0].strip()
                                text = ":".join(part.split(":")[1:]).strip().strip("'\"")
                            else:
                                char_name_raw = "Narrador"
                                text = part.strip().strip("'\"")

                            if not text:
                                continue

                            # Find matching voice from voice_map
                            matched_voice = voice_id  # default narrator
                            for cname, vid in voice_map.items():
                                if char_name_raw.lower() in cname.lower() or cname.lower() in char_name_raw.lower():
                                    matched_voice = vid
                                    break

                            # Generate audio for this character line
                            audio_bytes = _generate_narration_audio(text, matched_voice, stability, similarity, style_val, lang)
                            clip_path = f"{tmpdir}/part_{pi:03d}.mp3"
                            with open(clip_path, 'wb') as f:
                                f.write(audio_bytes)
                            audio_clips.append(clip_path)

                        if len(audio_clips) == 1:
                            with open(audio_clips[0], 'rb') as f:
                                final_audio = f.read()
                        elif len(audio_clips) > 1:
                            # Concatenate all character audio clips with 0.3s pause
                            list_file = f"{tmpdir}/concat_list.txt"
                            silence_path = f"{tmpdir}/silence.mp3"
                            # Generate 0.3s silence
                            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.3", silence_path],
                                           capture_output=True, timeout=10)
                            with open(list_file, 'w') as f:
                                for ci, cp in enumerate(audio_clips):
                                    f.write(f"file '{cp}'\n")
                                    if ci < len(audio_clips) - 1 and os.path.exists(silence_path):
                                        f.write(f"file '{silence_path}'\n")
                            merged_path = f"{tmpdir}/merged.mp3"
                            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c:a", "libmp3lame", "-q:a", "4", merged_path],
                                           capture_output=True, timeout=30)
                            with open(merged_path, 'rb') as f:
                                final_audio = f.read()
                        else:
                            narration_outputs.append({"scene_number": scene_num, "narration": dialogue, "audio_url": None})
                            continue

                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(final_audio, filename, "audio/mpeg")
                    narration_outputs.append({"scene_number": scene_num, "narration": dialogue, "audio_url": audio_url})
                    logger.info(f"Studio [{project_id}]: Dubbed scene {scene_num} done ({len(final_audio)//1024}KB, {len(parts)} voices)")

                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Dubbed scene {scene_num} failed: {e}")
                    narration_outputs.append({"scene_number": scene_num, "narration": dialogue, "audio_url": None, "error": str(e)[:100]})

                _update_project_field(tenant_id, project_id, {
                    "narration_status": {"phase": "generating_audio", "done": i + 1, "total": len(scenes)},
                })

        else:
            # ── NARRATED MODE: Single narrator voice ──
            narration_system = f"""You are a NARRATOR for cinematic storytelling. Given scenes, write compelling narration text for EACH scene.
Rules:
- Each scene narration is MAX 25 words (fits 12 seconds)
- Be dramatic, evocative, emotional
- Use the scene dialogue and description as basis
- **MANDATORY**: Write ALL narration text in {LANG_FULL_NAMES.get(lang, lang)}. NEVER write in English unless the language IS English.
- Output ONLY valid JSON array: [{{"scene_number": 1, "narration": "text..."}}]"""

            scene_summaries = "\n".join([
                f"Scene {s.get('scene_number', i+1)}: {s.get('title','')} — {s.get('description','')} — Dialogue: {s.get('dialogue','')}"
                for i, s in enumerate(scenes)
            ])

            script_result = _call_claude_sync(narration_system, f"Scenes:\n{scene_summaries}")

            import json as json_mod
            narrations = []
            if '[' in script_result:
                try:
                    start = script_result.index('[')
                    end = script_result.rindex(']') + 1
                    narrations = json_mod.loads(script_result[start:end])
                except Exception:
                    pass

            if not narrations:
                narrations = [{"scene_number": i+1, "narration": s.get("dialogue", s.get("description", ""))[:80]} for i, s in enumerate(scenes)]

            _update_project_field(tenant_id, project_id, {
                "narration_status": {"phase": "generating_audio", "done": 0, "total": len(narrations)},
            })

            narration_outputs = []
            for i, narr in enumerate(narrations):
                scene_num = narr.get("scene_number", i + 1)
                text = narr.get("narration", "")
                if not text.strip():
                    narration_outputs.append({"scene_number": scene_num, "text": "", "audio_url": None})
                    continue
                try:
                    audio_bytes = _generate_narration_audio(text, voice_id, stability, similarity, style_val, lang)
                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                    narration_outputs.append({"scene_number": scene_num, "text": text, "audio_url": audio_url})
                    logger.info(f"Studio [{project_id}]: Narration scene {scene_num} done ({len(audio_bytes)//1024}KB)")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Narration scene {scene_num} failed: {e}")
                    narration_outputs.append({"scene_number": scene_num, "text": text, "audio_url": None, "error": str(e)[:100]})

                _update_project_field(tenant_id, project_id, {
                    "narration_status": {"phase": "generating_audio", "done": i + 1, "total": len(narrations)},
                })

        # Save all narrations to project
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["narrations"] = narration_outputs
            project["narration_status"] = {"phase": "complete", "done": len(narration_outputs), "total": len(narration_outputs)}
            project["voice_config"] = {"voice_id": voice_id, "stability": stability, "similarity": similarity, "style_val": style_val}
            _add_milestone(project, "narration_generated", f"Narração gerada — {len([n for n in narration_outputs if n.get('audio_url')])} cenas")
            _save_project(tenant_id, settings, projects)

        logger.info(f"Studio [{project_id}]: All narrations done")

    except Exception as e:
        logger.error(f"Studio [{project_id}] narration error: {e}")
        _update_project_field(tenant_id, project_id, {
            "narration_status": {"phase": "error", "error": str(e)[:300]},
        })


@router.post("/projects/{project_id}/generate-narration")
async def generate_narration(project_id: str, req: GenerateNarrationRequest, tenant=Depends(get_current_tenant)):
    """Generate ElevenLabs narration for all scenes in a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.get("scenes"):
        raise HTTPException(status_code=400, detail="No scenes. Use the Screenwriter first.")

    thread = threading.Thread(
        target=_run_narration_background,
        args=(tenant["id"], project_id, req.voice_id, req.stability, req.similarity, req.style_val),
        daemon=True,
    )
    thread.start()

    return {"status": "started", "total_scenes": len(project["scenes"])}


@router.get("/projects/{project_id}/narrations")
async def get_narrations(project_id: str, tenant=Depends(get_current_tenant)):
    """Get narration status and outputs for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "narrations": project.get("narrations", []),
        "narration_status": project.get("narration_status", {}),
        "voice_config": project.get("voice_config", {}),
    }



# ── Performance Analytics ──

@router.get("/analytics/performance")
async def get_performance_analytics(tenant=Depends(get_current_tenant)):
    """Analyze performance data from all productions — timing, costs, efficiency."""
    from datetime import datetime as dt

    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects", [])

    # Collect data
    completed = [p for p in projects if p.get("status") == "complete" and p.get("milestones")]
    errored = [p for p in projects if p.get("status") == "error"]
    all_projects = projects

    # Parse milestones for timing
    productions = []
    for proj in completed:
        ms = proj.get("milestones", [])
        ms_dict = {m["key"]: m["at"] for m in ms if "at" in m}
        scenes_count = len(proj.get("scenes", []))
        videos_count = len([o for o in proj.get("outputs", []) if o.get("url") and o.get("type") == "video" and o.get("scene_number", 0) > 0])

        # Calculate durations from milestones
        created_at = ms_dict.get("project_created", "")
        agents_at = ms_dict.get("agents_complete", "")
        videos_at = ms_dict.get("videos_generated", "")
        film_at = ms_dict.get("film_complete", "")

        def _parse_ts(ts_str):
            if not ts_str:
                return None
            try:
                return dt.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                return None

        t_created = _parse_ts(created_at)
        t_agents = _parse_ts(agents_at)
        t_videos = _parse_ts(videos_at)
        t_film = _parse_ts(film_at)

        agent_duration = (t_agents - t_created).total_seconds() if t_created and t_agents else None
        video_duration = (t_videos - t_agents).total_seconds() if t_agents and t_videos else None
        total_duration = (t_film - t_created).total_seconds() if t_created and t_film else None

        # Extract timing from milestone labels (e.g., "Produção paralela — 523s")
        for m in ms:
            label = m.get("label", "")
            if "s" in label and any(c.isdigit() for c in label):
                import re
                nums = re.findall(r'(\d+)s', label)
                if nums:
                    if "agente" in label.lower() or "paralela" in label.lower():
                        agent_duration = float(nums[0])
                    elif "vídeo" in label.lower():
                        video_duration = float(nums[0])

        # Per-scene video timing from milestones
        scene_times = []
        for m in ms:
            if m["key"].startswith("video_scene_"):
                scene_times.append(m["at"])

        productions.append({
            "project_id": proj["id"],
            "name": proj.get("name", "Sem nome"),
            "scenes": scenes_count,
            "videos": videos_count,
            "agent_seconds": round(agent_duration) if agent_duration else None,
            "video_seconds": round(video_duration) if video_duration else None,
            "total_seconds": round(total_duration) if total_duration else None,
            "milestones": len(ms),
            "pipeline_version": "v3" if any("paralela" in m.get("label", "") for m in ms) else "v2" if any("Agentes de cinema" in m.get("label", "") for m in ms) else "v1",
        })

    # Compute aggregated stats
    agent_times = [p["agent_seconds"] for p in productions if p["agent_seconds"]]
    video_times = [p["video_seconds"] for p in productions if p["video_seconds"]]
    total_times = [p["total_seconds"] for p in productions if p["total_seconds"]]
    all_scenes = [p["scenes"] for p in productions if p["scenes"] > 0]

    def avg(lst):
        return round(sum(lst) / len(lst)) if lst else 0

    # Estimated Claude tokens used (rough: ~1500 tokens per scene director call)
    total_scenes_produced = sum(p["scenes"] for p in productions)
    est_claude_tokens = total_scenes_produced * 1500
    # v1: 3 calls per scene, v2: 3 batch calls, v3: 1 call per scene
    v1_count = len([p for p in productions if p["pipeline_version"] == "v1"])
    v2_count = len([p for p in productions if p["pipeline_version"] == "v2"])
    v3_count = len([p for p in productions if p["pipeline_version"] == "v3"])

    return {
        "summary": {
            "total_projects": len(all_projects),
            "completed": len(completed),
            "errored": len(errored),
            "total_scenes_produced": total_scenes_produced,
            "total_videos_generated": sum(p["videos"] for p in productions),
        },
        "timing": {
            "avg_agent_seconds": avg(agent_times),
            "avg_video_seconds": avg(video_times),
            "avg_total_seconds": avg(total_times),
            "min_total_seconds": min(total_times) if total_times else 0,
            "max_total_seconds": max(total_times) if total_times else 0,
            "avg_scenes_per_project": avg(all_scenes),
        },
        "pipeline_versions": {
            "v1_sequential": v1_count,
            "v2_batched": v2_count,
            "v3_parallel_teams": v3_count,
        },
        "cost_estimate": {
            "claude_calls_total": total_scenes_produced + len(completed),
            "claude_tokens_est": est_claude_tokens,
            "sora2_videos": sum(p["videos"] for p in productions),
            "optimization_note": f"v3 saves ~{(total_scenes_produced * 2) if total_scenes_produced > 0 else 0} Claude calls vs v1 ({total_scenes_produced}×3 → {total_scenes_produced}×1)",
        },
        "productions": sorted(productions, key=lambda x: x.get("total_seconds") or 999999),
        "recommendations": _generate_recommendations(productions, completed, errored),
    }


def _generate_recommendations(productions, completed, errored):
    """AI-like performance recommendations based on data."""
    recs = []
    if errored:
        error_rate = len(errored) / (len(completed) + len(errored)) * 100 if (len(completed) + len(errored)) > 0 else 0
        recs.append(f"Taxa de erro: {error_rate:.0f}%. Considere usar Pipeline v5 para maior estabilidade.")
    if len(completed) > 3:
        recs.append("Bom volume de produções concluídas. Pipeline estável.")
    return recs


# ═══════════════════════════════════════════════════════════
