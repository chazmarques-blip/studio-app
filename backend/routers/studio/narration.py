"""Auto-generated module from studio.py split."""
from ._shared import *
from .screenwriter import LANG_FULL_NAMES  # Import language names mapping

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


class GenerateMusicRequest(BaseModel):
    project_id: str
    prompt: Optional[str] = None
    duration_seconds: Optional[int] = None
    style: Optional[str] = None
    age_range: Optional[str] = None
    edited_lyrics: Optional[str] = None
    adjustment: Optional[str] = None
    language: Optional[str] = None  # pt, en, es, fr, de, it, ja, ko, zh, ar, hi, he


@router.get("/music-styles")
async def get_music_styles():
    """Return available music styles for children's songs."""
    return {
        "styles": [
            {"id": "auto", "name": "Automático (por idade)", "emoji": "🎯"},
            {"id": "galinha_pintadinha", "name": "Galinha Pintadinha", "emoji": "🐔"},
            {"id": "mundo_bita", "name": "Mundo Bita", "emoji": "🌍"},
            {"id": "disney", "name": "Disney", "emoji": "🏰"},
            {"id": "pixar", "name": "Pixar", "emoji": "🎬"},
            {"id": "pop_infantil", "name": "Pop Infantil", "emoji": "🎤"},
            {"id": "mpb_infantil", "name": "MPB Infantil", "emoji": "🎸"},
            {"id": "forrozinho", "name": "Forrozinho", "emoji": "🪗"},
            {"id": "reggae_infantil", "name": "Reggae Infantil", "emoji": "🌴"},
            {"id": "rock_infantil", "name": "Rock Infantil", "emoji": "🎸"},
            {"id": "sertanejo_infantil", "name": "Sertanejo Infantil", "emoji": "🤠"},
            {"id": "hip_hop_infantil", "name": "Hip-Hop Infantil", "emoji": "🎧"},
            {"id": "lullaby", "name": "Canção de Ninar", "emoji": "🌙"},
        ],
        "age_ranges": [
            {"id": "0-3", "name": "0-3 anos"},
            {"id": "3-5", "name": "3-5 anos"},
            {"id": "5-8", "name": "5-8 anos"},
            {"id": "8-12", "name": "8-12 anos"},
        ]
    }



@router.post("/projects/{project_id}/generate-music")
async def generate_music(project_id: str, req: GenerateMusicRequest = None, tenant=Depends(get_current_tenant)):
    """Generate an original children's song with vocals and lyrics for a project.
    
    Flow:
    1. LLM generates lyrics based on the story (briefing + scenes)
    2. ElevenLabs Music composes and sings the song with those lyrics
    3. Returns music URL + lyrics text
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    elevenlabs_key = ELEVENLABS_API_KEY
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")
    
    # ── STEP 1: Generate lyrics via LLM ──
    briefing = project.get("briefing", "")[:500]
    scenes = project.get("scenes", [])
    characters = project.get("characters", [])
    char_names = [c.get("name", "") for c in characters[:5]]
    lang = project.get("language", "pt")
    
    # Scene summaries for context
    scene_summaries = []
    for s in scenes[:10]:
        title = s.get("title", "")
        desc = s.get("description", "")[:80]
        scene_summaries.append(f"- {title}: {desc}")
    scenes_text = "\n".join(scene_summaries) if scene_summaries else "No scenes available"
    
    # Age-based style
    age_range = (req.age_range if req and req.age_range else project.get("age_range", "3-5"))
    AGE_STYLES = {
        "0-3": "Very simple melody, slow tempo (80-100 BPM), gentle lullaby style, soft female voice, repetitive chorus, like Galinha Pintadinha or nursery rhymes. Ukulele, xylophone, soft percussion.",
        "3-5": "Catchy upbeat melody, moderate tempo (100-120 BPM), playful children's pop style like Mundo Bita or Galinha Pintadinha. Cheerful vocals, simple repetitive lyrics, clap-along rhythm. Acoustic guitar, piano, light drums.",
        "5-8": "Energetic and fun, tempo 110-130 BPM, adventure-style like Disney Junior songs. Clear vocals with character, sing-along chorus. Full band: guitar, bass, drums, synth pads.",
        "8-12": "Modern pop/rock for kids, tempo 120-140 BPM, inspirational Disney/Pixar movie soundtrack style. Powerful chorus, emotional bridge. Full orchestral + pop arrangement.",
    }
    
    # Musical style override
    MUSIC_STYLES = {
        "galinha_pintadinha": "Galinha Pintadinha style: very catchy, repetitive chorus, clap-along, simple acoustic instruments (ukulele, acoustic guitar, tambourine), cheerful female/male vocals, tempo 100-110 BPM.",
        "mundo_bita": "Mundo Bita style: warm, gentle, educational, acoustic guitar and piano, soft male vocals, tempo 95-110 BPM, sweet and comforting.",
        "disney": "Disney animated movie style: orchestral, emotional, cinematic, powerful chorus with harmonies, full orchestra (strings, brass, woodwinds), dramatic bridges, tempo 110-130 BPM.",
        "pixar": "Pixar movie soundtrack style: whimsical, emotional, piano-driven with orchestral swells, intimate vocals, bittersweet beauty, tempo 100-120 BPM.",
        "reggae_infantil": "Children's reggae: laid-back rhythm, offbeat guitar, bass groove, cheerful vocals, tropical feel, tempo 85-100 BPM, sunny and happy.",
        "pop_infantil": "Modern children's pop: electronic beats, synth pads, catchy hook, auto-tune light, energetic, tempo 115-130 BPM, like modern YouTube kids music.",
        "mpb_infantil": "Brazilian MPB for kids: bossa nova influence, acoustic guitar, gentle percussion, warm vocals, poetic, tempo 90-110 BPM.",
        "forrozinho": "Children's forró: accordion (sanfona), triangle, zabumba, upbeat dance rhythm, joyful, tempo 110-130 BPM, northeastern Brazilian feel.",
        "rock_infantil": "Children's rock: electric guitar, drums, bass, energetic, fun, sing-along chorus, tempo 120-140 BPM, like school of rock for kids.",
        "lullaby": "Gentle lullaby: very soft, calming, music box feel, soft piano or harp, whispery vocals, tempo 60-80 BPM, perfect for bedtime.",
        "hip_hop_infantil": "Children's hip-hop: rhythmic, fun beats, rap verses with sung chorus, boom-bap or trap-lite, tempo 90-110 BPM, educational and fun.",
        "sertanejo_infantil": "Children's sertanejo: acoustic guitar, viola caipira, gentle country feel, romantic melody, tempo 100-120 BPM, Brazilian countryside warmth.",
    }
    
    chosen_style = (req.style if req and req.style else None)
    if chosen_style and chosen_style in MUSIC_STYLES:
        style_hint = MUSIC_STYLES[chosen_style]
    else:
        style_hint = AGE_STYLES.get(age_range, AGE_STYLES["3-5"])
    
    LANG_NAMES = {
        "pt": "Portuguese", "en": "English", "es": "Spanish", "fr": "French",
        "de": "German", "it": "Italian", "ja": "Japanese", "ko": "Korean",
        "zh": "Chinese (Mandarin)", "ar": "Arabic", "hi": "Hindi", "he": "Hebrew",
        "ru": "Russian", "tr": "Turkish", "nl": "Dutch", "sv": "Swedish",
    }
    music_lang = (req.language if req and req.language else lang) or "pt"
    lang_name = LANG_NAMES.get(music_lang, "Portuguese")
    
    lyrics_prompt = f"""You are a LEGENDARY children's songwriter (like the creators of Galinha Pintadinha, Mundo Bita, and Disney songs).

Write a COMPLETE song lyrics for a children's animated story.

STORY: {briefing}
CHARACTERS: {', '.join(char_names) if char_names else 'Various characters'}
KEY SCENES:
{scenes_text}

RULES:
- Language: {lang_name} ONLY (every word must be in {lang_name})
- Age target: {age_range} years old
- Structure: Intro (2 lines) → Verse 1 (4 lines) → Chorus (4 lines) → Verse 2 (4 lines) → Chorus → Bridge (2 lines) → Final Chorus
- The chorus must be EXTREMELY catchy and repetitive — kids will sing along
- Use the character names in the lyrics
- Tell the story through the song
- Keep words simple and age-appropriate
- Include onomatopoeia and fun sounds (la la la, hey hey, clap clap, etc.)
- Total: 20-30 lines maximum

Return ONLY the lyrics, nothing else. No annotations, no [Verse 1] markers."""

    # Generate lyrics via Claude
    try:
        # If user requested an adjustment to existing lyrics
        if req and req.adjustment and req.edited_lyrics:
            system = "You are a legendary children's songwriter. Adjust the given lyrics based on the user's instructions. Return ONLY the adjusted lyrics, nothing else."
            adjust_prompt = f"""Here are the current lyrics of a children's song:

{req.edited_lyrics}

ADJUSTMENT REQUESTED: {req.adjustment}

Rewrite the lyrics applying the requested adjustment. Keep the same structure (verses, chorus) but apply the changes. Language must stay the same. Return ONLY the new lyrics."""
            lyrics = _call_claude_sync(system, adjust_prompt, max_tokens=800)
            lyrics = lyrics.strip()
            logger.info(f"MusicGen [{project_id}]: Lyrics ADJUSTED ({len(lyrics)} chars) based on: {req.adjustment[:80]}")
        
        # If user provided edited lyrics directly (regenerate with edited text)
        elif req and req.edited_lyrics and req.prompt:
            lyrics = req.edited_lyrics
            logger.info(f"MusicGen [{project_id}]: Using user-edited lyrics ({len(lyrics)} chars)")
        
        # Generate new lyrics from scratch
        else:
            system = "You are a legendary children's songwriter. Write song lyrics in the requested language. Return ONLY the lyrics."
            lyrics = _call_claude_sync(system, lyrics_prompt, max_tokens=800)
            lyrics = lyrics.strip()
            logger.info(f"MusicGen [{project_id}]: Lyrics generated ({len(lyrics)} chars, {len(lyrics.splitlines())} lines)")
    except Exception as e:
        logger.warning(f"MusicGen [{project_id}]: LLM lyrics failed: {e}, using generic")
        lyrics = req.edited_lyrics if (req and req.edited_lyrics) else None
    
    # ── STEP 2: Build ElevenLabs Music prompt with lyrics ──
    if req and req.prompt and not req.adjustment:
        # Custom prompt from "Regenerar com esta Letra" — use prompt directly but include lyrics
        if lyrics:
            music_prompt = (
                f"Children's song with vocals singing in {lang_name}. "
                f"{style_hint} "
                f"The singer should have a warm, friendly, expressive voice perfect for children's content. "
                f"LYRICS TO SING:\n{lyrics}"
            )
        else:
            music_prompt = req.prompt
    else:
        custom_style = req.style if req and req.style else None
        
        if lyrics:
            music_prompt = (
                f"Children's song with vocals singing in {lang_name}. "
                f"{style_hint} "
                f"The singer should have a warm, friendly, expressive voice perfect for children's content. "
                f"LYRICS TO SING:\n{lyrics}"
            )
        else:
            music_prompt = (
                f"Instrumental children's soundtrack in {lang_name} style. "
                f"Story: {briefing[:200]}. "
                f"{style_hint} "
                f"Family-friendly, cinematic, emotional."
            )
    
    # ── STEP 3: Generate music via ElevenLabs ──
    if req and req.duration_seconds:
        duration_ms = req.duration_seconds * 1000
    else:
        # Estimate: ~60-90 seconds for a children's song
        duration_ms = 60000 if len(scenes) <= 15 else 90000
    
    duration_ms = max(10000, min(duration_ms, 300000))
    
    try:
        from elevenlabs import ElevenLabs as ElevenLabsClient
        from elevenlabs.core.api_error import ApiError
        client = ElevenLabsClient(api_key=elevenlabs_key)
        
        logger.info(f"MusicGen [{project_id}]: Composing {duration_ms//1000}s song with vocals")
        
        # Try with original prompt, retry with ElevenLabs suggestion if rejected
        current_prompt = music_prompt
        for attempt in range(3):
            try:
                track_stream = client.music.compose(
                    prompt=current_prompt,
                    music_length_ms=duration_ms
                )
                
                audio_data = b""
                for chunk in track_stream:
                    audio_data += chunk
                break  # Success
            except ApiError as api_err:
                body = getattr(api_err, 'body', {}) or {}
                detail = body.get('detail', {}) if isinstance(body, dict) else {}
                suggestion = detail.get('data', {}).get('prompt_suggestion', '') if isinstance(detail, dict) else ''
                
                if suggestion and attempt < 2:
                    logger.warning(f"MusicGen [{project_id}]: Prompt rejected (attempt {attempt+1}), retrying with ElevenLabs suggestion")
                    current_prompt = suggestion
                    audio_data = b""
                    continue
                else:
                    raise
        
        if len(audio_data) < 1000:
            raise HTTPException(status_code=500, detail="Music generation returned empty audio")
        
        # Upload music with unique filename
        import uuid as _uuid
        song_id = str(_uuid.uuid4())[:8]
        filename = f"studio/{project_id}_song_{song_id}.mp3"
        music_url = _upload_to_storage(audio_data, filename, "audio/mpeg")
        
        # Always use the latest lyrics
        final_lyrics = lyrics or (req.edited_lyrics if req else None) or ""
        
        # Build song entry
        from datetime import datetime, timezone
        new_song = {
            "id": song_id,
            "url": music_url,
            "lyrics": final_lyrics,
            "duration_seconds": duration_ms // 1000,
            "age_range": age_range,
            "style": chosen_style or "auto",
            "language": music_lang,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Append to playlist (keep backwards compat with old generated_song)
        songs_list = project.get("generated_songs", [])
        # Migrate old single song if exists
        if not songs_list and project.get("generated_song"):
            old = project["generated_song"]
            old["id"] = old.get("id", "legacy")
            old["created_at"] = old.get("created_at", "")
            old["style"] = old.get("style", "auto")
            songs_list.append(old)
        songs_list.append(new_song)
        project["generated_songs"] = songs_list
        project["generated_song"] = new_song  # Keep for backwards compat
        _save_project(tenant["id"], settings, projects, flush_now=True)
        
        logger.info(f"MusicGen [{project_id}]: Song generated — {len(audio_data)//1024}KB")
        
        return {
            "status": "success",
            "song_id": song_id,
            "music_url": music_url,
            "lyrics": final_lyrics,
            "duration_seconds": duration_ms // 1000,
            "size_kb": len(audio_data) // 1024,
            "age_range": age_range,
            "style": chosen_style or "auto",
        }
        
    except Exception as e:
        logger.error(f"MusicGen [{project_id}]: Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Clean error message for the user
        err_str = str(e)
        if 'violated' in err_str.lower() or 'bad_prompt' in err_str.lower():
            msg = "O conteúdo da letra foi rejeitado pelo filtro. Tente editar a letra e regenerar."
        elif 'billing' in err_str.lower() or 'quota' in err_str.lower():
            msg = "Limite de créditos ElevenLabs atingido. Verifique sua conta."
        elif 'timeout' in err_str.lower():
            msg = "Timeout na geração. Tente novamente."
        else:
            msg = "Erro ao gerar música. Tente novamente."
        raise HTTPException(status_code=500, detail=msg)


@router.delete("/projects/{project_id}/songs/{song_id}")
async def delete_song(project_id: str, song_id: str, tenant=Depends(get_current_tenant)):
    """Delete a song from the project's playlist."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    songs = project.get("generated_songs", [])
    project["generated_songs"] = [s for s in songs if s.get("id") != song_id]
    
    # Update generated_song to latest remaining or None
    if project["generated_songs"]:
        project["generated_song"] = project["generated_songs"][-1]
    else:
        project["generated_song"] = None
    
    _save_project(tenant["id"], settings, projects, flush_now=True)
    return {"success": True, "remaining": len(project["generated_songs"])}





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

    # 🔗 Registry override — Hans Zimmer for voice casting
    try:
        from .agents_registry import resolve_agent_prompt
        system_prompt = resolve_agent_prompt("sound_designer_agent", fallback=system_prompt, lang=lang)
    except Exception as _e:
        logger.warning(f"Narration single-voice: registry override failed: {_e}")

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

    # 🔗 Registry override — Hans Zimmer for voice casting
    try:
        from .agents_registry import resolve_agent_prompt
        system_prompt = resolve_agent_prompt("sound_designer_agent", fallback=system_prompt, lang=lang)
    except Exception as _e:
        logger.warning(f"Narration voice-casting: registry override failed: {_e}")

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
    """Generate narration audio using ElevenLabs TTS. Returns mp3 bytes.
    
    CRITICAL FIX (2026-04-03): Always pass language_code to ensure consistent language output.
    """
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
    # CRITICAL: Always use language hint, default to "pt" if not provided
    lang_hint = LANG_HINTS.get(language_code, "pt")

    kwargs = {
        "text": text,
        "voice_id": voice_id,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings,
        "language_code": lang_hint,  # ALWAYS pass language_code (never optional)
    }

    logger.info(f"ElevenLabs TTS: lang={lang_hint}, voice={voice_id[:8]}, text_len={len(text)}")

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
                            
                            # CRITICAL FIX (2026-04-03): Clean text before TTS
                            from pipeline.media import _clean_narration_for_tts
                            cleaned_text = _clean_narration_for_tts(text)
                            if not cleaned_text.strip():
                                logger.warning(f"Studio [{project_id}]: Scene {scene_num} part {pi} cleaned to empty, using original")
                                cleaned_text = text

                            # Find matching voice from voice_map
                            matched_voice = voice_id  # default narrator
                            matched_char_name = "Narrador"
                            for cname, vid in voice_map.items():
                                if char_name_raw.lower() in cname.lower() or cname.lower() in char_name_raw.lower():
                                    matched_voice = vid
                                    matched_char_name = cname
                                    break

                            # Generate audio for this character line with EXPLICIT language
                            logger.debug(f"Studio [{project_id}]: Scene {scene_num} - {matched_char_name}: '{cleaned_text[:50]}...' (lang={lang})")
                            audio_bytes = _generate_narration_audio(cleaned_text, matched_voice, stability, similarity, style_val, lang)
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
            # CRITICAL FIX (2026-04-03): Use EXACT dialogue text from scenes instead of rewriting
            # This preserves the approved script and ensures audio matches what's written
            logger.info(f"Studio [{project_id}]: NARRATED mode — using EXACT dialogue text (no rewriting)")

            _update_project_field(tenant_id, project_id, {
                "narration_status": {"phase": "generating_audio", "done": 0, "total": len(scenes)},
            })

            narration_outputs = []
            for i, scene in enumerate(scenes):
                scene_num = scene.get("scene_number", i + 1)
                # Use EXACT dialogue from scene (already approved)
                text = scene.get("dialogue", "")
                
                # Fallback: if no dialogue, use narrated_text or description
                if not text.strip():
                    text = scene.get("narrated_text", "")
                if not text.strip():
                    text = scene.get("description", "")[:120]  # Max 120 chars from description
                
                if not text.strip():
                    narration_outputs.append({"scene_number": scene_num, "text": "", "audio_url": None})
                    logger.warning(f"Studio [{project_id}]: Scene {scene_num} has no dialogue/narration text")
                    continue
                
                # Clean text for TTS (remove stage directions, keep dialogue)
                from pipeline.media import _clean_narration_for_tts
                cleaned_text = _clean_narration_for_tts(text)
                
                # Log comparison for debugging
                if cleaned_text != text:
                    logger.info(f"Studio [{project_id}]: Scene {scene_num} text cleaned: {len(text)} → {len(cleaned_text)} chars")
                    logger.debug(f"Original: {text[:100]}...")
                    logger.debug(f"Cleaned: {cleaned_text[:100]}...")
                
                try:
                    audio_bytes = _generate_narration_audio(cleaned_text, voice_id, stability, similarity, style_val, lang)
                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                    narration_outputs.append({
                        "scene_number": scene_num, 
                        "text": cleaned_text,  # Store cleaned text that was actually spoken
                        "original_text": text,  # Store original for reference
                        "audio_url": audio_url
                    })
                    logger.info(f"Studio [{project_id}]: Narration scene {scene_num} done ({len(audio_bytes)//1024}KB, {len(cleaned_text)} chars, lang={lang})")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Narration scene {scene_num} failed: {e}")
                    narration_outputs.append({"scene_number": scene_num, "text": cleaned_text, "audio_url": None, "error": str(e)[:100]})

                _update_project_field(tenant_id, project_id, {
                    "narration_status": {"phase": "generating_audio", "done": i + 1, "total": len(scenes)},
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
