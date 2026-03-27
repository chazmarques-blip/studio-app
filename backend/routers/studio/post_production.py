"""Auto-generated module from studio.py split."""
from ._shared import *

# ── PHASE A: Post-Production (Audio Engineer) ──
# ═══════════════════════════════════════════════════════════

MUSIC_DIR = "/app/backend/assets/music"

# Map music_plan categories to library tracks
MOOD_TO_TRACK = {
    "gentle": ["emotional", "classical_piano", "ambient_dreamy"],
    "cinematic": ["cinematic", "emotional"],
    "epic": ["cinematic", "gospel_uplifting"],
    "tense": ["cinematic", "ambient_nature"],
    "triumphant": ["gospel_uplifting", "cinematic", "emotional"],
    "contemplative": ["classical_piano", "ambient_dreamy", "jazz_lofi"],
    "joyful": ["gospel_uplifting", "upbeat", "pop_acoustic"],
    "dramatic": ["cinematic", "emotional"],
    "peaceful": ["ambient_dreamy", "classical_piano"],
    "mysterious": ["ambient_nature", "electronic_chill"],
}


def _select_music_for_project(music_plan: list) -> str:
    """Select best background music track based on the Production Design music plan."""
    if not music_plan:
        return "emotional"
    mood_scores = {}
    for entry in music_plan:
        mood = entry.get("mood", "").lower()
        category = entry.get("category", "").lower()
        scenes = entry.get("scenes", [])
        weight = len(scenes) if scenes else 1
        for key, tracks in MOOD_TO_TRACK.items():
            if key in mood or key in category:
                for t in tracks:
                    mood_scores[t] = mood_scores.get(t, 0) + weight
                break
    if mood_scores:
        return max(mood_scores, key=mood_scores.get)
    return "emotional"


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 12.0


def _run_post_production(tenant_id: str, project_id: str, req: PostProduceRequest):
    """Background: Full post-production — narration + music + transitions → final video."""
    import tempfile
    import time as _time

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        scenes = project.get("scenes", [])
        outputs = project.get("outputs", [])
        lang = project.get("language", "pt")

        if not scenes:
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "error", "error": "Sem cenas no projeto"}
            })
            return

        scene_videos = sorted(
            [o for o in outputs if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")],
            key=lambda x: x.get("scene_number", 0)
        )
        if not scene_videos:
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "error", "error": "Sem vídeos. Rode a produção primeiro."}
            })
            return

        logger.info(f"Studio [{project_id}]: Post-production starting — {len(scene_videos)} videos")

        if not _ensure_ffmpeg():
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "error", "error": "FFmpeg não disponível"}
            })
            return

        tmpdir = tempfile.mkdtemp()

        # ── Step 1: Generate narrations if needed ──
        narrations = project.get("narrations", [])
        narrations_with_audio = [n for n in narrations if n.get("audio_url")]

        if len(narrations_with_audio) < len(scene_videos):
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "narration", "done": 0, "total": len(scenes), "message": "Gerando narrações..."}
            })

            narration_system = f"""You are a NARRATOR for cinematic storytelling. Write compelling narration for EACH scene.
Rules:
- Each narration MAX 25 words (12 seconds)
- Dramatic, evocative, emotional
- **MANDATORY**: Write ALL narration text in {LANG_FULL_NAMES.get(lang, lang)}. NEVER write in English unless the language IS English.
- Output ONLY valid JSON array: [{{"scene_number": 1, "narration": "text..."}}]"""

            scene_summaries = "\n".join([
                f"Scene {s.get('scene_number', i+1)}: {s.get('title','')} — {s.get('description','')} — Dialogue: {s.get('dialogue','')}"
                for i, s in enumerate(scenes)
            ])

            try:
                script_result = _call_claude_sync(narration_system, f"Scenes:\n{scene_summaries}")
                import json as json_mod
                narrations = []
                if '[' in script_result:
                    start = script_result.index('[')
                    end = script_result.rindex(']') + 1
                    narrations = json_mod.loads(script_result[start:end])
            except Exception as e:
                logger.warning(f"Studio [{project_id}]: Narration script failed: {e}")
                narrations = [{"scene_number": i+1, "narration": s.get("dialogue", s.get("description", ""))[:80]}
                              for i, s in enumerate(scenes)]

            for i, narr in enumerate(narrations):
                scene_num = narr.get("scene_number", i + 1)
                text = narr.get("narration", "")
                _update_project_field(tenant_id, project_id, {
                    "post_production_status": {"phase": "narration", "done": i, "total": len(narrations), "message": f"Narração cena {scene_num}..."}
                })
                if not text.strip():
                    narr["audio_url"] = None
                    continue
                try:
                    audio_bytes = _generate_narration_audio(text, req.voice_id, req.stability, req.similarity, req.style_val, lang)
                    filename = f"studio/{project_id}_narration_{scene_num}.mp3"
                    audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                    narr["audio_url"] = audio_url
                    logger.info(f"Studio [{project_id}]: Narration {scene_num} done ({len(audio_bytes)//1024}KB)")
                except Exception as e:
                    logger.warning(f"Studio [{project_id}]: Narration {scene_num} failed: {e}")
                    narr["audio_url"] = None

            _update_project_field(tenant_id, project_id, {
                "narrations": narrations,
                "narration_status": {"phase": "complete", "done": len(narrations), "total": len(narrations)},
                "voice_config": {"voice_id": req.voice_id, "stability": req.stability, "similarity": req.similarity, "style_val": req.style_val},
            })
        else:
            logger.info(f"Studio [{project_id}]: Using existing narrations ({len(narrations_with_audio)})")

        # ── Step 2: Download scene videos (with retry) ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "downloading", "done": 0, "total": len(scene_videos), "message": "Baixando vídeos..."}
        })

        video_files = []
        for i, sv in enumerate(scene_videos):
            local_path = f"{tmpdir}/scene_{i:03d}.mp4"
            for dl_attempt in range(4):
                try:
                    urllib.request.urlretrieve(sv["url"], local_path)
                    break
                except Exception as dl_err:
                    logger.warning(f"Studio [{project_id}]: Download retry {dl_attempt+1}/4 for scene {sv.get('scene_number', i+1)}: {dl_err}")
                    _time.sleep(2 * (dl_attempt + 1))
            video_files.append({"path": local_path, "scene_number": sv.get("scene_number", i+1)})
            _update_project_field(tenant_id, project_id, {
                "post_production_status": {"phase": "downloading", "done": i+1, "total": len(scene_videos), "message": f"Vídeo {i+1}/{len(scene_videos)}"}
            })

        # ── Step 3: Download narration audio (with retry) ──
        narration_files = {}
        for narr in narrations:
            sn = narr.get("scene_number", 0)
            url = narr.get("audio_url")
            if url and sn > 0:
                local_path = f"{tmpdir}/narration_{sn:03d}.mp3"
                for dl_attempt in range(3):
                    try:
                        urllib.request.urlretrieve(url, local_path)
                        narration_files[sn] = local_path
                        break
                    except Exception:
                        _time.sleep(1 * (dl_attempt + 1))

        # ── Step 4: Apply fade transitions + color grading + concat ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 0, "total": 4, "message": "Aplicando transições e color grading..."}
        })

        is_continuity = project.get("continuity_mode", True)

        faded_files = []
        for i, vf in enumerate(video_files):
            duration = _get_video_duration(vf["path"])
            sn = vf["scene_number"]
            scene_data = next((s for s in scenes if s.get("scene_number") == sn), {})
            trans = scene_data.get("transition", req.transition_type)
            # Enhanced transition: 1.5s for continuity mode, original for normal
            td = 1.5 if is_continuity else req.transition_duration
            faded_path = f"{tmpdir}/faded_{i:03d}.mp4"

            if trans == "fade" and duration > td * 2:
                fade_out_start = max(0, duration - td)
                # Apply color grading in continuity mode for visual consistency
                vf_filter = f"fade=t=in:st=0:d={td},fade=t=out:st={fade_out_start:.2f}:d={td}"
                if is_continuity:
                    vf_filter += ",eq=contrast=1.05:brightness=0.02:saturation=1.1,colorbalance=rs=0.03:gs=0.01:bs=-0.02"
                cmd = [
                    "ffmpeg", "-y", "-i", vf["path"],
                    "-vf", vf_filter,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an", faded_path
                ]
            else:
                if is_continuity:
                    # Even without fades, apply color grading for consistency
                    cmd = [
                        "ffmpeg", "-y", "-i", vf["path"],
                        "-vf", "eq=contrast=1.05:brightness=0.02:saturation=1.1,colorbalance=rs=0.03:gs=0.01:bs=-0.02",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an", faded_path
                    ]
                else:
                    cmd = ["ffmpeg", "-y", "-i", vf["path"], "-c:v", "copy", "-an", faded_path]

            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                shutil.copy2(vf["path"], faded_path)
            faded_files.append(faded_path)

        concat_file = f"{tmpdir}/concat.txt"
        with open(concat_file, 'w') as f:
            for fp in faded_files:
                f.write(f"file '{fp}'\n")

        silent_video = f"{tmpdir}/silent_final.mp4"
        result = subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-movflags", "+faststart", silent_video
        ], capture_output=True, timeout=300)
        if result.returncode != 0:
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", silent_video], capture_output=True, timeout=120)

        total_duration = _get_video_duration(silent_video)
        logger.info(f"Studio [{project_id}]: Video with transitions: {total_duration:.1f}s")

        # ── Step 5: Build narration audio track ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 1, "total": 4, "message": "Mixando narração..."}
        })

        narration_track = None
        if narration_files:
            scene_offsets = {}
            cumulative = 0.0
            for i, vf in enumerate(video_files):
                sn = vf["scene_number"]
                dur = _get_video_duration(faded_files[i])
                scene_offsets[sn] = cumulative
                cumulative += dur

            inputs = ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={total_duration:.2f}"]
            filter_parts = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo[base]"]
            input_idx = 1
            overlay_labels = ["base"]

            for sn in sorted(narration_files.keys()):
                offset = scene_offsets.get(sn, 0.0)
                inputs.extend(["-i", narration_files[sn]])
                label = f"n{input_idx}"
                filter_parts.append(f"[{input_idx}:a]adelay={int(offset*1000)}|{int(offset*1000)},aformat=sample_rates=44100:channel_layouts=stereo[{label}]")
                overlay_labels.append(label)
                input_idx += 1

            if len(overlay_labels) > 1:
                mix_inputs = "".join(f"[{lb}]" for lb in overlay_labels)
                filter_parts.append(f"{mix_inputs}amix=inputs={len(overlay_labels)}:duration=longest:normalize=0[narr_out]")
                narration_track = f"{tmpdir}/narration_track.mp3"
                result = subprocess.run(
                    ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(filter_parts), "-map", "[narr_out]", "-c:a", "libmp3lame", "-b:a", "192k", narration_track],
                    capture_output=True, timeout=120
                )
                if result.returncode != 0:
                    logger.warning(f"Studio [{project_id}]: Narration mix failed: {result.stderr.decode()[:200]}")
                    narration_track = None

        # ── Step 6: Prepare background music (segmented by mood) ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 2, "total": 4, "message": "Criando trilha sonora segmentada..."}
        })

        music_plan = project.get("agents_output", {}).get("production_design", {}).get("music_plan", [])
        music_track = req.music_track  # user override

        # Build scene offsets and durations
        scene_offsets = {}
        scene_durations = {}
        cumulative = 0.0
        for i, vf in enumerate(video_files):
            sn = vf["scene_number"]
            dur = _get_video_duration(faded_files[i])
            scene_offsets[sn] = cumulative
            scene_durations[sn] = dur
            cumulative += dur

        # Build music segments based on music_plan
        music_prepared = f"{tmpdir}/music.mp3"
        if music_plan and not music_track:
            # Create segmented music: different tracks for different scene groups
            segment_files = []
            for seg_idx, entry in enumerate(music_plan):
                seg_scenes = entry.get("scenes", [])
                mood = entry.get("mood", "").lower()
                category = entry.get("category", "").lower()

                # Select track for this segment
                seg_track = None
                for key, tracks in MOOD_TO_TRACK.items():
                    if key in mood or key in category:
                        seg_track = tracks[0]
                        break
                if not seg_track:
                    seg_track = "emotional"

                seg_path = os.path.join(MUSIC_DIR, f"{seg_track}.mp3")
                if not os.path.exists(seg_path):
                    seg_path = os.path.join(MUSIC_DIR, "emotional.mp3")

                # Calculate segment duration
                seg_start = min(scene_offsets.get(s, 0) for s in seg_scenes) if seg_scenes else 0
                seg_end = max(scene_offsets.get(s, 0) + scene_durations.get(s, 12) for s in seg_scenes) if seg_scenes else 12
                seg_dur = seg_end - seg_start

                seg_file = f"{tmpdir}/music_seg_{seg_idx}.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-stream_loop", "-1", "-i", seg_path,
                    "-t", f"{seg_dur:.2f}",
                    "-af", f"afade=t=in:st=0:d=1.5,afade=t=out:st={max(0, seg_dur-1.5):.2f}:d=1.5,volume={req.music_volume:.2f}",
                    "-c:a", "libmp3lame", "-b:a", "128k", seg_file
                ], capture_output=True, timeout=30)
                segment_files.append(seg_file)
                logger.info(f"Studio [{project_id}]: Music segment {seg_idx} ({seg_track}): {seg_dur:.1f}s for scenes {seg_scenes}")

            # Concatenate segments
            if segment_files:
                seg_concat = f"{tmpdir}/seg_concat.txt"
                with open(seg_concat, 'w') as f:
                    for sf in segment_files:
                        if os.path.exists(sf):
                            f.write(f"file '{sf}'\n")
                result = subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", seg_concat,
                    "-c:a", "libmp3lame", "-b:a", "128k", music_prepared
                ], capture_output=True, timeout=30)
                has_music = result.returncode == 0
            else:
                has_music = False
        else:
            # Single track (user override or no music plan)
            if not music_track:
                music_track = _select_music_for_project(music_plan)
            music_path = os.path.join(MUSIC_DIR, f"{music_track}.mp3")
            if not os.path.exists(music_path):
                music_path = os.path.join(MUSIC_DIR, "emotional.mp3")
            result = subprocess.run([
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", music_path,
                "-t", f"{total_duration:.2f}",
                "-af", f"afade=t=in:st=0:d=2,afade=t=out:st={max(0, total_duration-3):.2f}:d=3,volume={req.music_volume:.2f}",
                "-c:a", "libmp3lame", "-b:a", "128k", music_prepared
            ], capture_output=True, timeout=60)
            has_music = result.returncode == 0

        # ── Step 7: Final mix ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "mixing", "done": 3, "total": 4, "message": "Mix final: vídeo + narração + trilha..."}
        })

        final_output = f"{tmpdir}/final_with_audio.mp4"
        if narration_track and has_music:
            cmd = [
                "ffmpeg", "-y", "-i", silent_video, "-i", narration_track, "-i", music_prepared,
                "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest:weights=1 0.3:normalize=0[audio]",
                "-map", "0:v", "-map", "[audio]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", final_output
            ]
        elif narration_track:
            cmd = [
                "ffmpeg", "-y", "-i", silent_video, "-i", narration_track,
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", final_output
            ]
        elif has_music:
            cmd = [
                "ffmpeg", "-y", "-i", silent_video, "-i", music_prepared,
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", "-shortest", final_output
            ]
        else:
            shutil.copy2(silent_video, final_output)
            cmd = None

        if cmd:
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Studio [{project_id}]: Final mix failed: {result.stderr.decode()[:300]}")
                shutil.copy2(silent_video, final_output)

        file_size = os.path.getsize(final_output) if os.path.exists(final_output) else 0
        logger.info(f"Studio [{project_id}]: Final video: {file_size//1024//1024}MB, {total_duration:.1f}s")

        # Compress if > 45MB
        if file_size > 45 * 1024 * 1024:
            compressed = f"{tmpdir}/final_compressed.mp4"
            target_br = int((40 * 8 * 1024) / max(total_duration, 1))
            subprocess.run([
                "ffmpeg", "-y", "-i", final_output,
                "-c:v", "libx264", "-preset", "medium", "-b:v", f"{target_br}k",
                "-vf", "scale=960:540", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", compressed
            ], capture_output=True, timeout=600)
            if os.path.exists(compressed):
                final_output = compressed
                file_size = os.path.getsize(compressed)

        # ── Upload ──
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "uploading", "message": "Enviando vídeo final..."}
        })

        with open(final_output, 'rb') as f:
            video_bytes = f.read()

        filename = f"studio/{project_id}_final_audio_{lang}.mp4"
        try:
            url = _upload_to_storage(video_bytes, filename, "video/mp4")
        except Exception as e:
            logger.error(f"Studio [{project_id}]: Upload failed: {e}")
            url = None

        # Save
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            new_output = {
                "type": "final_video", "url": url, "language": lang,
                "music_track": music_track, "duration": total_duration,
                "has_narration": bool(narration_track), "has_music": has_music,
                "file_size_mb": round(file_size / (1024*1024), 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            project["outputs"] = [o for o in project["outputs"] if not (o.get("type") == "final_video" and o.get("language") == lang)]
            project["outputs"].append(new_output)
            project["post_production_status"] = {
                "phase": "complete", "final_url": url, "language": lang,
                "music_track": music_track, "duration": total_duration,
                "has_narration": bool(narration_track), "has_music": has_music,
            }
            _add_milestone(project, "post_production_complete", f"Pós-produção {lang.upper()} — {total_duration:.0f}s")
            _save_project(tenant_id, settings, projects)

        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info(f"Studio [{project_id}]: Post-production complete! URL: {url}")

    except Exception as e:
        logger.error(f"Studio [{project_id}] post-production error: {e}")
        _update_project_field(tenant_id, project_id, {
            "post_production_status": {"phase": "error", "error": str(e)[:300]}
        })


@router.post("/projects/{project_id}/post-produce")
async def post_produce(project_id: str, req: PostProduceRequest, tenant=Depends(get_current_tenant)):
    """Trigger full post-production: narration + music + transitions."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scene_videos = [o for o in project.get("outputs", []) if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")]
    if not scene_videos:
        raise HTTPException(status_code=400, detail="Sem vídeos. Rode a produção primeiro.")

    _update_project_field(tenant["id"], project_id, {
        "post_production_status": {"phase": "starting", "message": "Iniciando pós-produção..."}
    })

    thread = threading.Thread(target=_run_post_production, args=(tenant["id"], project_id, req), daemon=True)
    thread.start()

    return {"status": "started", "total_scenes": len(project.get("scenes", [])), "scene_videos": len(scene_videos)}


@router.get("/projects/{project_id}/post-production-status")
async def get_post_production_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Get post-production progress."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "status": project.get("post_production_status", {}),
        "narrations": project.get("narrations", []),
        "voice_config": project.get("voice_config", {}),
        "subtitles": project.get("subtitles", {}),
    }


@router.post("/projects/{project_id}/upload-narration/{scene_number}")
async def upload_narration_audio(project_id: str, scene_number: int, file: UploadFile = File(...), tenant=Depends(get_current_tenant)):
    """Upload custom narration/dubbing audio for a specific scene."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser áudio (mp3, wav, m4a)")

    audio_bytes = await file.read()
    if len(audio_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (max 20MB)")

    filename = f"studio/{project_id}_custom_narration_{scene_number}.mp3"
    audio_url = _upload_to_storage(audio_bytes, filename, file.content_type)

    narrations = project.get("narrations", [])
    found = False
    for n in narrations:
        if n.get("scene_number") == scene_number:
            n["audio_url"] = audio_url
            n["source"] = "upload"
            found = True
            break
    if not found:
        narrations.append({"scene_number": scene_number, "narration": f"Custom audio scene {scene_number}", "audio_url": audio_url, "source": "upload"})

    project["narrations"] = narrations
    _save_project(tenant["id"], settings, projects)

    return {"audio_url": audio_url, "scene_number": scene_number, "source": "upload"}


@router.delete("/projects/{project_id}/narration/{scene_number}")
async def delete_narration(project_id: str, scene_number: int, tenant=Depends(get_current_tenant)):
    """Remove narration for a specific scene."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    narrations = project.get("narrations", [])
    project["narrations"] = [n for n in narrations if n.get("scene_number") != scene_number]
    _save_project(tenant["id"], settings, projects)

    return {"deleted": True, "scene_number": scene_number}


# ═══════════════════════════════════════════════════════════
# ── PHASE B: Multi-Language Localization (Dubbing) ──
# ═══════════════════════════════════════════════════════════

LANG_NAMES = {"pt": "Português", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "it": "Italiano"}


def _run_localization(tenant_id: str, project_id: str, req: LocalizeRequest):
    """Background: Re-dub video into a new language."""
    import tempfile

    target = req.target_language

    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        original_lang = project.get("language", "pt")
        narrations = project.get("narrations", [])

        if not narrations:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "Rode a pós-produção primeiro."}
            })
            return

        logger.info(f"Studio [{project_id}]: Localization {original_lang} → {target}")
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "translating", "message": f"Traduzindo para {LANG_NAMES.get(target, target)}..."}
        })

        # ── Translate narrations ──
        import json as json_mod
        original_texts = [{"scene_number": n.get("scene_number", 0), "narration": n.get("narration", n.get("text", ""))} for n in narrations]

        translate_system = f"""Translate narration texts from {LANG_NAMES.get(original_lang, original_lang)} to {LANG_NAMES.get(target, target)}.
Rules:
- Same dramatic tone
- MAX 25 words each
- Output ONLY JSON array: [{{"scene_number": 1, "narration": "translated..."}}]"""

        try:
            result = _call_claude_sync(translate_system, f"Translate:\n{json_mod.dumps(original_texts, ensure_ascii=False)}")
            translated = []
            if '[' in result:
                translated = json_mod.loads(result[result.index('['):result.rindex(']')+1])
        except Exception as e:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": f"Tradução falhou: {str(e)[:100]}"}
            })
            return

        if not translated:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "Tradução vazia"}
            })
            return

        # ── Generate audio in target language ──
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "generating_audio", "done": 0, "total": len(translated)}
        })

        voice_id = req.voice_id or project.get("voice_config", {}).get("voice_id", "21m00Tcm4TlvDq8ikWAM")
        translated_narrations = []

        for i, t in enumerate(translated):
            sn = t.get("scene_number", i + 1)
            text = t.get("narration", "")
            if i % 5 == 0:  # Update status every 5 scenes to reduce DB pressure
                _update_project_field(tenant_id, project_id, {
                    f"localization_{target}": {"phase": "generating_audio", "done": i, "total": len(translated), "message": f"Áudio cena {sn}..."}
                })
            if not text.strip():
                translated_narrations.append({"scene_number": sn, "narration": text, "audio_url": None})
                continue
            try:
                audio_bytes = _generate_narration_audio(text, voice_id, req.stability, req.similarity, req.style_val, target)
                filename = f"studio/{project_id}_narration_{sn}_{target}.mp3"
                audio_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
                translated_narrations.append({"scene_number": sn, "narration": text, "audio_url": audio_url})
            except Exception as e:
                translated_narrations.append({"scene_number": sn, "narration": text, "audio_url": None, "error": str(e)[:100]})

        # ── Re-mix video with new audio ──
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "mixing", "message": f"Mixando vídeo {LANG_NAMES.get(target, target)}..."}
        })

        if not _ensure_ffmpeg():
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "FFmpeg indisponível"}
            })
            return

        tmpdir = tempfile.mkdtemp()

        # Find base video
        final_videos = [o for o in project.get("outputs", []) if o.get("type") == "final_video" and o.get("url")]
        if not final_videos:
            _update_project_field(tenant_id, project_id, {
                f"localization_{target}": {"phase": "error", "error": "Rode a pós-produção primeiro."}
            })
            return

        base_video = f"{tmpdir}/base.mp4"
        urllib.request.urlretrieve(final_videos[0]["url"], base_video)
        total_duration = _get_video_duration(base_video)

        # Download translated audio
        narration_files = {}
        for narr in translated_narrations:
            sn = narr.get("scene_number", 0)
            url = narr.get("audio_url")
            if url and sn > 0:
                lp = f"{tmpdir}/narr_{sn}_{target}.mp3"
                try:
                    urllib.request.urlretrieve(url, lp)
                    narration_files[sn] = lp
                except Exception:
                    pass

        # Calculate scene offsets
        sv_sorted = sorted(
            [o for o in project.get("outputs", []) if o.get("type") == "video" and o.get("scene_number", 0) > 0],
            key=lambda x: x.get("scene_number", 0)
        )
        scene_offsets = {}
        cumulative = 0.0
        for sv in sv_sorted:
            scene_offsets[sv.get("scene_number", 0)] = cumulative
            cumulative += sv.get("duration", 12.0)

        # Build narration track
        narration_track = None
        if narration_files:
            inputs = ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100:duration={total_duration:.2f}"]
            fp = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo[base]"]
            idx = 1
            labels = ["base"]
            for sn in sorted(narration_files.keys()):
                offset = scene_offsets.get(sn, 0.0)
                inputs.extend(["-i", narration_files[sn]])
                lb = f"n{idx}"
                fp.append(f"[{idx}:a]adelay={int(offset*1000)}|{int(offset*1000)},aformat=sample_rates=44100:channel_layouts=stereo[{lb}]")
                labels.append(lb)
                idx += 1

            if len(labels) > 1:
                mix_in = "".join(f"[{lb}]" for lb in labels)
                fp.append(f"{mix_in}amix=inputs={len(labels)}:duration=longest:normalize=0[out]")
                narration_track = f"{tmpdir}/narr_{target}.mp3"
                r = subprocess.run(
                    ["ffmpeg", "-y"] + inputs + ["-filter_complex", ";".join(fp), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", narration_track],
                    capture_output=True, timeout=120
                )
                if r.returncode != 0:
                    narration_track = None

        # Strip audio from base and prepare music
        silent = f"{tmpdir}/silent.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", base_video, "-c:v", "copy", "-an", silent], capture_output=True, timeout=60)

        music_key = project.get("post_production_status", {}).get("music_track", "emotional")
        mp = os.path.join(MUSIC_DIR, f"{music_key}.mp3")
        if not os.path.exists(mp):
            mp = os.path.join(MUSIC_DIR, "emotional.mp3")

        music_prep = f"{tmpdir}/music.mp3"
        r = subprocess.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", mp, "-t", f"{total_duration:.2f}",
            "-af", f"afade=t=in:st=0:d=2,afade=t=out:st={max(0,total_duration-3):.2f}:d=3,volume=0.15",
            "-c:a", "libmp3lame", "-b:a", "128k", music_prep
        ], capture_output=True, timeout=60)
        has_music = r.returncode == 0

        final_loc = f"{tmpdir}/final_{target}.mp4"
        if narration_track and has_music:
            cmd = ["ffmpeg", "-y", "-i", silent, "-i", narration_track, "-i", music_prep,
                   "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest:weights=1 0.3:normalize=0[a]",
                   "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                   "-movflags", "+faststart", "-shortest", final_loc]
        elif narration_track:
            cmd = ["ffmpeg", "-y", "-i", silent, "-i", narration_track, "-map", "0:v", "-map", "1:a",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", final_loc]
        else:
            shutil.copy2(base_video, final_loc)
            cmd = None

        if cmd:
            r = subprocess.run(cmd, capture_output=True, timeout=300)
            if r.returncode != 0:
                shutil.copy2(base_video, final_loc)

        # Compress if needed
        file_size = os.path.getsize(final_loc) if os.path.exists(final_loc) else 0
        if file_size > 45 * 1024 * 1024:
            comp = f"{tmpdir}/comp_{target}.mp4"
            tbr = int((40 * 8 * 1024) / max(total_duration, 1))
            subprocess.run(["ffmpeg", "-y", "-i", final_loc, "-c:v", "libx264", "-preset", "medium",
                            "-b:v", f"{tbr}k", "-vf", "scale=960:540", "-c:a", "aac", "-b:a", "128k",
                            "-movflags", "+faststart", comp], capture_output=True, timeout=600)
            if os.path.exists(comp):
                final_loc = comp
                file_size = os.path.getsize(comp)

        # Upload
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "uploading", "message": f"Enviando {LANG_NAMES.get(target, target)}..."}
        })

        with open(final_loc, 'rb') as f:
            vb = f.read()

        try:
            url = _upload_to_storage(vb, f"studio/{project_id}_final_{target}.mp4", "video/mp4")
        except Exception as e:
            url = None
            logger.error(f"Studio [{project_id}]: Loc upload failed: {e}")

        # Save
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            loc_out = {
                "type": "final_video", "url": url, "language": target,
                "duration": total_duration, "has_narration": bool(narration_track),
                "has_music": has_music, "file_size_mb": round(file_size/(1024*1024), 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            project["outputs"] = [o for o in project["outputs"] if not (o.get("type") == "final_video" and o.get("language") == target)]
            project["outputs"].append(loc_out)
            if not project.get("localizations"):
                project["localizations"] = {}
            project["localizations"][target] = {
                "narrations": translated_narrations, "final_url": url, "voice_id": voice_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            project[f"localization_{target}"] = {"phase": "complete", "final_url": url, "language": target}
            _add_milestone(project, f"localization_{target}", f"Localizado → {LANG_NAMES.get(target, target)}")
            _save_project(tenant_id, settings, projects)

        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info(f"Studio [{project_id}]: Localization {target} complete! URL: {url}")

    except Exception as e:
        logger.error(f"Studio [{project_id}] localization error: {e}")
        _update_project_field(tenant_id, project_id, {
            f"localization_{target}": {"phase": "error", "error": str(e)[:300]}
        })


@router.post("/projects/{project_id}/localize")
async def localize_project(project_id: str, req: LocalizeRequest, tenant=Depends(get_current_tenant)):
    """Localize a produced video to a new language (re-dub)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.target_language == project.get("language", "pt"):
        raise HTTPException(status_code=400, detail="Idioma alvo é o mesmo do original")

    has_final = any(o.get("type") == "final_video" for o in project.get("outputs", []))
    if not has_final:
        raise HTTPException(status_code=400, detail="Rode a pós-produção primeiro.")

    _update_project_field(tenant["id"], project_id, {
        f"localization_{req.target_language}": {"phase": "starting", "message": "Iniciando localização..."}
    })
    thread = threading.Thread(target=_run_localization, args=(tenant["id"], project_id, req), daemon=True)
    thread.start()
    return {"status": "started", "target_language": req.target_language, "target_name": LANG_NAMES.get(req.target_language, req.target_language)}


@router.get("/projects/{project_id}/localizations")
async def get_localizations(project_id: str, tenant=Depends(get_current_tenant)):
    """Get all localizations for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    final_videos = {}
    for o in project.get("outputs", []):
        if o.get("type") == "final_video" and o.get("url"):
            final_videos[o.get("language", "?")] = o

    statuses = {}
    for lc in ["en", "es", "fr", "de", "it", "pt"]:
        s = project.get(f"localization_{lc}", {})
        if s:
            statuses[lc] = s

    return {
        "localizations": project.get("localizations", {}),
        "statuses": statuses,
        "final_videos": final_videos,
        "original_language": project.get("language", "pt"),
        "post_production_status": project.get("post_production_status", {}),
    }



# ═══════════════════════════════════════════════════════════
# ── PHASE 3: Scene Re-edit + Subtitles ──
# ═══════════════════════════════════════════════════════════

class RegenSceneRequest(BaseModel):
    new_prompt_hint: Optional[str] = ""  # optional override for the scene prompt


@router.post("/projects/{project_id}/regen-scene/{scene_number}")
async def regen_scene(project_id: str, scene_number: int, req: RegenSceneRequest = Body(default=None), tenant=Depends(get_current_tenant)):
    """Re-generate a single scene video without re-producing the entire project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_number") == scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Cena {scene_number} não encontrada")

    # Mark as regenerating
    _update_project_field(tenant["id"], project_id, {
        f"regen_scene_{scene_number}": {"phase": "starting", "message": f"Re-gerando cena {scene_number}..."}
    })

    def _regen_bg():
        try:
            _settings, _projects, _project = _get_project(tenant["id"], project_id)
            if not _project:
                return

            animation_sub = _project.get("animation_sub", "pixar_3d")
            character_avatars = _project.get("character_avatars", {})

            # Build composite avatar for this scene
            chars_in = scene.get("characters_in_scene", [])
            composite_url = None
            if len(chars_in) > 1:
                urls = [character_avatars.get(c) for c in chars_in if character_avatars.get(c)]
                if urls:
                    composite_url = urls[0]  # Use first avatar as reference
            elif len(chars_in) == 1:
                composite_url = character_avatars.get(chars_in[0])

            # Get production design for character descriptions
            pd = _project.get("agents_output", {}).get("production_design", {})
            char_bible = pd.get("character_bible", {})
            char_descriptions = "\n".join([f"- {name}: {str(info)[:100]}" for name, info in char_bible.items()])

            # Build Sora 2 prompt
            ANIMATION_SUB_PROMPTS = {
                "pixar_3d": "Premium 3D CGI animation (Pixar/DreamWorks quality). Subsurface scattering, global illumination, cinematic DoF.",
                "cartoon_3d": "Stylized 3D cartoon (bright colors, simplified shapes, cel-shading).",
                "cartoon_2d": "Classic 2D hand-drawn animation (Disney/Ghibli quality, painted backgrounds).",
                "anime_2d": "Japanese anime style (detailed backgrounds, dramatic lighting, expressive eyes).",
                "realistic": "Cinematic photorealistic. Shallow DoF, film grain, natural lighting.",
                "watercolor": "Watercolor painting animation. Visible brush strokes, soft pastel tones.",
            }
            style_hint = ANIMATION_SUB_PROMPTS.get(animation_sub, ANIMATION_SUB_PROMPTS["pixar_3d"])

            prompt_hint = ""
            if req and req.new_prompt_hint:
                prompt_hint = f"\nADDITIONAL DIRECTION: {req.new_prompt_hint}"

            video_prompt = f"""{style_hint}
SCENE: {scene.get('title', '')}. {scene.get('description', '')}
CAMERA: {scene.get('camera', 'medium shot')}
LIGHTING: {scene.get('lighting', 'warm natural')}
CHARACTERS: {', '.join(chars_in)}
{char_descriptions}
MOOD: {scene.get('mood', '')}{prompt_hint}
CRITICAL: Maintain EXACT same character designs throughout. CONSISTENT art style."""

            if composite_url:
                video_prompt = f"[Reference character image: {composite_url}]\n{video_prompt}"

            logger.info(f"Studio [{project_id}]: Regenerating scene {scene_number}")

            _update_project_field(tenant["id"], project_id, {
                f"regen_scene_{scene_number}": {"phase": "generating", "message": "Gerando vídeo com Sora 2..."}
            })

            # Call Sora 2
            from openai import OpenAI
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            client = OpenAI(api_key=openai_key)

            try:
                response = client.responses.create(
                    model="sora",
                    input=video_prompt,
                    tools=[{"type": "video_generation", "size": "1080x1920", "duration": 10, "n_variants": 1}],
                )
                # Poll for completion
                import time as _time
                for _ in range(120):
                    response = client.responses.retrieve(response.id)
                    if response.status == "completed":
                        break
                    _time.sleep(5)

                if response.status == "completed":
                    video_url = None
                    for output in response.output:
                        if hasattr(output, 'url'):
                            video_url = output.url
                            break

                    if video_url:
                        # Download and re-upload
                        video_data = urllib.request.urlopen(video_url).read()
                        filename = f"studio/{project_id}_scene_{scene_number}_v2.mp4"
                        new_url = _upload_to_storage(video_data, filename, "video/mp4")

                        # Update the output
                        _settings, _projects, _project = _get_project(tenant["id"], project_id)
                        if _project:
                            for o in _project.get("outputs", []):
                                if o.get("scene_number") == scene_number and o.get("type") == "video":
                                    o["url"] = new_url
                                    o["regenerated"] = True
                                    o["regenerated_at"] = datetime.now(timezone.utc).isoformat()
                                    break
                            _project[f"regen_scene_{scene_number}"] = {"phase": "complete", "url": new_url}
                            _add_milestone(_project, f"regen_scene_{scene_number}", f"Cena {scene_number} regenerada")
                            _save_project(tenant["id"], _settings, _projects)
                        logger.info(f"Studio [{project_id}]: Scene {scene_number} regenerated: {new_url}")
                        return
                    else:
                        raise RuntimeError("No video URL in Sora response")
                else:
                    raise RuntimeError(f"Sora job status: {response.status}")

            except Exception as e:
                logger.error(f"Studio [{project_id}]: Scene regen failed: {e}")
                _update_project_field(tenant["id"], project_id, {
                    f"regen_scene_{scene_number}": {"phase": "error", "error": str(e)[:200]}
                })

        except Exception as e:
            logger.error(f"Studio [{project_id}]: Scene regen error: {e}")
            _update_project_field(tenant["id"], project_id, {
                f"regen_scene_{scene_number}": {"phase": "error", "error": str(e)[:200]}
            })

    thread = threading.Thread(target=_regen_bg, daemon=True)
    thread.start()
    return {"status": "started", "scene_number": scene_number}


@router.post("/projects/{project_id}/generate-subtitles")
async def generate_subtitles(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate SRT subtitles from narrations and burn them into the final video."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    narrations = project.get("narrations", [])
    if not narrations:
        raise HTTPException(status_code=400, detail="Sem narrações. Rode a pós-produção primeiro.")

    outputs = project.get("outputs", [])

    # Calculate scene offsets
    scene_videos = sorted(
        [o for o in outputs if o.get("type") == "video" and o.get("scene_number", 0) > 0 and o.get("url")],
        key=lambda x: x.get("scene_number", 0)
    )
    scene_durations = {}
    for sv in scene_videos:
        scene_durations[sv.get("scene_number", 0)] = sv.get("duration", 12.0)

    cumulative = 0.0
    srt_entries = []
    for i, narr in enumerate(narrations):
        sn = narr.get("scene_number", i + 1)
        text = narr.get("narration", narr.get("text", ""))
        if not text.strip():
            cumulative += scene_durations.get(sn, 12.0)
            continue

        start_time = cumulative + 0.5  # 0.5s delay for natural feel
        dur = scene_durations.get(sn, 12.0)
        end_time = cumulative + dur - 0.5

        # Format SRT timestamps
        def _fmt_srt(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        srt_entries.append(f"{i+1}\n{_fmt_srt(start_time)} --> {_fmt_srt(end_time)}\n{text}\n")
        cumulative += dur

    srt_content = "\n".join(srt_entries)

    # Save SRT for all languages
    lang = project.get("language", "pt")
    all_srts = {lang: srt_content}

    # Generate SRT for localized versions
    localizations = project.get("localizations", {})
    for loc_lang, loc_data in localizations.items():
        loc_narrations = loc_data.get("narrations", [])
        if loc_narrations:
            cumulative = 0.0
            loc_entries = []
            for i, narr in enumerate(loc_narrations):
                sn = narr.get("scene_number", i + 1)
                text = narr.get("narration", "")
                if not text.strip():
                    cumulative += scene_durations.get(sn, 12.0)
                    continue
                start_time = cumulative + 0.5
                dur = scene_durations.get(sn, 12.0)
                end_time = cumulative + dur - 0.5
                loc_entries.append(f"{i+1}\n{_fmt_srt(start_time)} --> {_fmt_srt(end_time)}\n{text}\n")
                cumulative += dur
            all_srts[loc_lang] = "\n".join(loc_entries)

    # Save SRTs to storage
    srt_urls = {}
    for slang, srt_text in all_srts.items():
        filename = f"studio/{project_id}_subtitles_{slang}.srt"
        srt_bytes = srt_text.encode("utf-8")
        try:
            url = _upload_to_storage(srt_bytes, filename, "text/srt")
            srt_urls[slang] = url
        except Exception as e:
            logger.warning(f"Studio [{project_id}]: SRT upload failed for {slang}: {e}")

    # Save to project
    _update_project_field(tenant["id"], project_id, {
        "subtitles": srt_urls,
    })

    return {
        "status": "complete",
        "subtitles": srt_urls,
        "languages": list(srt_urls.keys()),
    }
