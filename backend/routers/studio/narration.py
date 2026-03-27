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
            # ElevenLabs voice mapping for character types
            DUBBED_VOICES = {
                "narrator": voice_id,  # User-selected voice for narrator
                "male_elder": "VR6AewLTigWG4xSOukaG",   # Arnold - deep male
                "male_young": "pNInz6obpgDQGcFmaJgB",    # Adam - young male
                "female_elder": "EXAVITQu4vr4xnSDxMaL",  # Bella - female
                "female_young": "jBpfuIE2acCO8z3wKNLl",   # Gigi - young female
                "child": "jsCqWAovK2LkecY7zXl4",          # Freya - light voice for kids
                "angel": "onwK4e9ZLuTAKqWW03F9",          # Daniel - ethereal male
            }

            # Map character names to voice types
            characters = project.get("characters", [])
            char_voice_map = {}
            for c in characters:
                name = c.get("name", "").lower()
                if "narrador" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["narrator"]
                elif "anjo" in name or "angel" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["angel"]
                elif "sara" in name or "rebeca" in name or "agar" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["female_elder"]
                elif "isaque" in name or "isaac" in name:
                    # Check if adolescent or child
                    if "adolescente" in name or "jovem" in name:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_young"]
                    elif "bebê" in name or "bebe" in name or "criança" in name:
                        char_voice_map[c["name"]] = DUBBED_VOICES["child"]
                    else:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_young"]
                elif "abraão" in name or "abraao" in name or "abraham" in name:
                    if "jovem" in name:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_young"]
                    else:
                        char_voice_map[c["name"]] = DUBBED_VOICES["male_elder"]
                elif "deus" in name or "god" in name:
                    char_voice_map[c["name"]] = DUBBED_VOICES["angel"]
                else:
                    char_voice_map[c["name"]] = DUBBED_VOICES["male_elder"]

            # Default mappings for common Portuguese names
            char_voice_map["Narrador"] = DUBBED_VOICES["narrator"]
            char_voice_map["Deus"] = DUBBED_VOICES["angel"]

            logger.info(f"Studio [{project_id}]: DUBBED mode — {len(char_voice_map)} character voices mapped")

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

                            # Find matching voice
                            matched_voice = DUBBED_VOICES["narrator"]
                            for cname, vid in char_voice_map.items():
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
