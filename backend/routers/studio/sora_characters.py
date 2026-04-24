"""Sora 2 Characters API — Voice & Appearance Consistency Across Scenes.

Uses OpenAI's official Sora 2 Characters endpoint (`POST /v1/sora/characters`)
to create reusable `character_id`s from an anchor scene. Subsequent scenes
reuse the ID to lock voice + appearance natively at the model level.

This module is PURELY ADDITIVE — existing projects without
`character.sora_character_id` behave exactly as before.
"""
from ._shared import *
import requests


# ───────────────────────── Helpers ─────────────────────────

def _default_timestamps_for_duration(duration_seconds: float) -> str:
    """Pick two timestamps where the character is likely visible.

    Sora 2 expects two seconds separated by comma. We pick ~30% and ~70%
    of the clip length — avoiding transitions at start/end.
    """
    try:
        d = max(2.0, float(duration_seconds or 12))
    except Exception:
        d = 12.0
    t1 = max(1, int(d * 0.30))
    t2 = max(t1 + 1, int(d * 0.70))
    return f"{t1},{t2}"


def _find_first_scene_with_character(scenes: list, character_name: str) -> Optional[dict]:
    """Find the first rendered scene where `character_name` appears.

    Looks at scene.characters / scene.characters_in_scene and requires the
    scene to have a `video_url` already produced.
    """
    if not character_name:
        return None
    target = character_name.strip().lower()
    for scene in scenes or []:
        if not scene.get("video_url"):
            continue
        chars = (
            scene.get("characters_in_scene")
            or scene.get("characters")
            or []
        )
        names = []
        for c in chars:
            if isinstance(c, dict):
                names.append(str(c.get("name", "")).strip().lower())
            elif isinstance(c, str):
                names.append(c.strip().lower())
        if target in names:
            return scene
    return None


def _register_sora_character_http(
    openai_key: str,
    video_url: str,
    timestamps: str,
    label: Optional[str] = None,
) -> tuple:
    """POST /v1/videos/characters — returns (character_id, error_reason_or_None).

    Uses the CURRENT OpenAI Videos API (as of Feb 2026):
      - URL: https://api.openai.com/v1/videos/characters
      - Format: multipart/form-data with fields `video` (file) and `name`
      - Video MUST be 2-4 seconds long — we crop the anchor clip with ffmpeg
      - Moderation: OpenAI rejects faces/sensitive content
      - Returns: {"id": "char_xxx", "name": "..."}

    Returns a tuple (char_id, error_reason):
      - Success: (char_id, None)
      - Failure: (None, "reason")
    """
    if not openai_key:
        logger.warning("Sora Characters: OPENAI_API_KEY missing — skipping register")
        return None, "openai_key_missing"
    if not video_url:
        logger.warning("Sora Characters: invalid input (no video_url)")
        return None, "no_video_url"

    import subprocess
    import tempfile
    import os as _os

    tmp_dir = tempfile.mkdtemp(prefix="sora_char_")
    try:
        dl = requests.get(video_url, timeout=90, stream=True)
        if dl.status_code != 200:
            logger.error(f"Sora Characters: could not download anchor video {video_url[:80]}… ({dl.status_code})")
            return None, f"download_failed_{dl.status_code}"
        raw_path = _os.path.join(tmp_dir, "anchor_raw.mp4")
        with open(raw_path, "wb") as f:
            f.write(dl.content)
        if _os.path.getsize(raw_path) < 1024:
            return None, "video_too_small"

        start_s = 1.0
        try:
            if timestamps and "," in timestamps:
                parts = timestamps.split(",")
                start_s = max(0.0, float(parts[0]))
        except Exception:
            start_s = 1.0
        clip_duration = 3.0

        cropped_path = _os.path.join(tmp_dir, "anchor_3s.mp4")
        ff = subprocess.run(
            [
                "ffmpeg", "-y", "-ss", str(start_s), "-i", raw_path,
                "-t", str(clip_duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                cropped_path,
            ],
            capture_output=True, timeout=60,
        )
        if ff.returncode != 0 or not _os.path.exists(cropped_path) or _os.path.getsize(cropped_path) < 1024:
            logger.error(f"Sora Characters: ffmpeg crop failed — {ff.stderr.decode(errors='ignore')[:200]}")
            return None, "ffmpeg_crop_failed"

        headers = {"Authorization": f"Bearer {openai_key}"}
        with open(cropped_path, "rb") as cf:
            files = {"video": ("anchor_3s.mp4", cf.read(), "video/mp4")}
        data = {}
        if label:
            data["name"] = label[:60]

        resp = requests.post(
            "https://api.openai.com/v1/videos/characters",
            headers=headers,
            files=files,
            data=data,
            timeout=180,
        )
        if resp.status_code >= 400:
            err_body = resp.text[:500]
            logger.error(f"Sora Characters register failed: {resp.status_code} {err_body[:200]}")
            # Parse specific error codes
            reason = f"api_{resp.status_code}"
            try:
                parsed = resp.json().get("error", {})
                code = parsed.get("code")
                if code == "input_moderation":
                    reason = "moderation_rejected"
                elif "duration" in (parsed.get("message", "") or "").lower():
                    reason = "duration_invalid"
                elif "face" in (parsed.get("message", "") or "").lower():
                    reason = "face_detected"
            except Exception:
                pass
            return None, reason
        result = resp.json()
        char_id = result.get("id") or result.get("character_id")
        if not char_id:
            logger.error(f"Sora Characters: no id returned: {result}")
            return None, "no_id_in_response"
        logger.info(f"Sora Characters registered: {char_id} (name={label})")
        return char_id, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Sora Characters network error: {e}")
        return None, "network_error"
    except Exception as e:
        logger.error(f"Sora Characters unexpected error: {e}")
        return None, "unexpected_error"
    finally:
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


def _sora_character_ids_for_scene(project: dict, scene: dict, max_refs: int = 2) -> list:
    """Return the list of registered Sora character_ids that should be injected
    into `characters: [...]` for this scene.

    Respects Sora 2's 2-character-per-generation limit. If a project character
    has no `sora_character_id`, it is skipped (natural fallback to prompt-only).
    """
    characters = project.get("characters") or []
    if not characters:
        return []

    # Build name -> character_id lookup
    id_by_name = {}
    for c in characters:
        if not isinstance(c, dict):
            continue
        cid = (c.get("sora_character_id") or "").strip()
        name = str(c.get("name", "")).strip().lower()
        if cid and name:
            id_by_name[name] = cid
    if not id_by_name:
        return []

    # Which characters are in this scene?
    scene_chars = (
        scene.get("characters_in_scene")
        or scene.get("characters")
        or []
    )
    ordered_ids = []
    for sc in scene_chars:
        name = ""
        if isinstance(sc, dict):
            name = str(sc.get("name", "")).strip().lower()
        elif isinstance(sc, str):
            name = sc.strip().lower()
        if name and name in id_by_name and id_by_name[name] not in ordered_ids:
            ordered_ids.append(id_by_name[name])
        if len(ordered_ids) >= max_refs:
            break
    return ordered_ids


# ───────────────────────── Endpoints ─────────────────────────

class RegisterSoraCharacterRequest(BaseModel):
    character_name: str
    scene_number: Optional[int] = None  # If omitted, auto-picks first rendered scene
    timestamps: Optional[str] = None    # e.g. "3,6" — if omitted, derives from duration


@router.post("/projects/{project_id}/register-sora-character")
async def register_sora_character(
    project_id: str,
    req: RegisterSoraCharacterRequest,
    tenant=Depends(get_current_tenant),
):
    """Register a single character with Sora 2 using a specific rendered scene
    as the voice/appearance anchor. Saves `sora_character_id` on the character
    in `project.characters`.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes in project")

    # Pick anchor scene
    if req.scene_number is not None:
        anchor = next((s for s in scenes if s.get("scene_number") == req.scene_number), None)
        if not anchor:
            raise HTTPException(status_code=404, detail=f"Scene {req.scene_number} not found")
        if not anchor.get("video_url"):
            raise HTTPException(status_code=400, detail=f"Scene {req.scene_number} has no rendered video yet")
    else:
        anchor = _find_first_scene_with_character(scenes, req.character_name)
        if not anchor:
            raise HTTPException(
                status_code=404,
                detail=f"No rendered scene contains '{req.character_name}' yet",
            )

    timestamps = req.timestamps or _default_timestamps_for_duration(
        anchor.get("duration") or 12
    )
    char_id, err_reason = _register_sora_character_http(
        openai_key=OPENAI_API_KEY,
        video_url=anchor["video_url"],
        timestamps=timestamps,
        label=req.character_name,
    )
    if not char_id:
        # Friendly error messages for common rejections
        _friendly = {
            "moderation_rejected": "A OpenAI rejeitou o vídeo por moderação (personagens realistas/rostos humanos não são aceitos). Tente com personagens em estilo animado/estilizado.",
            "face_detected": "A OpenAI detectou um rosto real no vídeo e recusou o registro.",
            "duration_invalid": "O vídeo precisa ter entre 2-4 segundos. Re-gere a cena e tente de novo.",
            "openai_key_missing": "OpenAI API key não está configurada no servidor.",
            "download_failed_404": "Não foi possível baixar o vídeo da cena âncora.",
        }
        msg = _friendly.get(err_reason, f"Sora Characters API rejeitou o registro ({err_reason})")
        raise HTTPException(status_code=502, detail=msg)

    # Persist on project.characters[].sora_character_id
    characters = project.get("characters") or []
    updated = False
    for c in characters:
        if isinstance(c, dict) and str(c.get("name", "")).strip().lower() == req.character_name.strip().lower():
            c["sora_character_id"] = char_id
            c["sora_character_anchor_scene"] = anchor.get("scene_number")
            c["sora_character_timestamps"] = timestamps
            updated = True
            break
    if not updated:
        # Character not in project.characters yet — append
        characters.append({
            "name": req.character_name,
            "sora_character_id": char_id,
            "sora_character_anchor_scene": anchor.get("scene_number"),
            "sora_character_timestamps": timestamps,
        })

    _update_project_field(tenant["id"], project_id, {"characters": characters})

    return {
        "character_name": req.character_name,
        "sora_character_id": char_id,
        "anchor_scene": anchor.get("scene_number"),
        "timestamps": timestamps,
    }


@router.post("/projects/{project_id}/auto-register-sora-characters")
async def auto_register_sora_characters(
    project_id: str,
    tenant=Depends(get_current_tenant),
):
    """Scan all rendered scenes and auto-register every main character with Sora 2
    using the FIRST scene in which they appear as the voice anchor.

    Skips characters that already have a `sora_character_id`. Safe to call
    multiple times — idempotent.
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", []) or []
    characters = project.get("characters", []) or []
    if not scenes or not characters:
        return {"registered": [], "skipped": [], "failed": [], "message": "No scenes or characters"}

    registered, skipped, failed = [], [], []

    for char in characters:
        if not isinstance(char, dict):
            continue
        name = str(char.get("name", "")).strip()
        if not name:
            continue
        if char.get("sora_character_id"):
            skipped.append({"name": name, "reason": "already_registered"})
            continue

        anchor = _find_first_scene_with_character(scenes, name)
        if not anchor:
            failed.append({"name": name, "reason": "no_rendered_scene"})
            continue

        # Skip if previously failed with a sticky error (won't resolve on retry)
        STICKY_ERRORS = {"moderation_rejected", "face_detected", "openai_key_missing"}
        if char.get("sora_character_lock_error") in STICKY_ERRORS:
            failed.append({"name": name, "reason": char["sora_character_lock_error"]})
            continue

        timestamps = _default_timestamps_for_duration(anchor.get("duration") or 12)
        char_id, err_reason = _register_sora_character_http(
            openai_key=OPENAI_API_KEY,
            video_url=anchor["video_url"],
            timestamps=timestamps,
            label=name,
        )
        if not char_id:
            char["sora_character_lock_error"] = err_reason
            char["sora_character_lock_attempted_at"] = datetime.utcnow().isoformat()
            failed.append({"name": name, "reason": err_reason or "api_rejected"})
            continue

        char["sora_character_id"] = char_id
        char["sora_character_anchor_scene"] = anchor.get("scene_number")
        char["sora_character_timestamps"] = timestamps
        char["sora_character_locked_at"] = datetime.utcnow().isoformat()
        char.pop("sora_character_lock_error", None)
        char.pop("sora_character_lock_attempted_at", None)
        registered.append({
            "name": name,
            "sora_character_id": char_id,
            "anchor_scene": anchor.get("scene_number"),
        })

    # Always persist — both registrations AND sticky error marks
    _update_project_field(tenant["id"], project_id, {"characters": characters})

    return {
        "registered": registered,
        "skipped": skipped,
        "failed": failed,
        "total_registered": len(registered),
    }


@router.get("/projects/{project_id}/sora-characters")
async def list_sora_characters(project_id: str, tenant=Depends(get_current_tenant)):
    """Return the current Sora character_id mapping for the project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", []) or []
    result = []
    for c in characters:
        if not isinstance(c, dict):
            continue
        result.append({
            "name": c.get("name"),
            "sora_character_id": c.get("sora_character_id"),
            "anchor_scene": c.get("sora_character_anchor_scene"),
            "timestamps": c.get("sora_character_timestamps"),
        })
    return {"characters": result}


@router.get("/projects/{project_id}/voice-status")
async def get_voice_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Unified voice status for the project — combines Sora Character Lock + ElevenLabs fallback.

    Returns, for each character:
      - sora_character_id / anchor_scene / locked_at  (primary = Sora native voice)
      - elevenlabs_voice_id / elevenlabs_voice_name   (fallback = dubbed TTS)
      - status: "locked" | "fallback_only" | "unassigned"
    """
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", []) or []
    voice_map = project.get("voice_map", {}) or {}
    video_engine = project.get("video_engine", "kling")

    # Build a lookup of ElevenLabs voices (id -> name)
    voice_name_by_id = {}
    try:
        from ._shared import ELEVENLABS_VOICES
        for v in ELEVENLABS_VOICES:
            if isinstance(v, dict) and v.get("id"):
                voice_name_by_id[v["id"]] = v.get("name", "—")
    except Exception:
        pass

    result = []
    counts = {"locked": 0, "fallback_only": 0, "unassigned": 0}
    for c in characters:
        if not isinstance(c, dict):
            continue
        name = c.get("name") or ""
        sora_id = c.get("sora_character_id")
        anchor = c.get("sora_character_anchor_scene")
        locked_at = c.get("sora_character_locked_at")
        timestamps = c.get("sora_character_timestamps")

        # Case-insensitive match for voice_map
        el_voice_id = None
        for k, vid in voice_map.items():
            if isinstance(k, str) and k.strip().lower() == name.strip().lower():
                el_voice_id = vid
                break
        el_voice_name = voice_name_by_id.get(el_voice_id) if el_voice_id else None

        if sora_id:
            status = "locked"
        elif el_voice_id:
            status = "fallback_only"
        else:
            status = "unassigned"
        counts[status] = counts.get(status, 0) + 1

        result.append({
            "name": name,
            "status": status,
            "sora_character_id": sora_id,
            "anchor_scene": anchor,
            "locked_at": locked_at,
            "timestamps": timestamps,
            "lock_error": c.get("sora_character_lock_error"),
            "lock_error_at": c.get("sora_character_lock_attempted_at"),
            "elevenlabs_voice_id": el_voice_id,
            "elevenlabs_voice_name": el_voice_name,
        })

    return {
        "characters": result,
        "video_engine": video_engine,
        "counts": counts,
        "total": len(result),
    }


@router.delete("/projects/{project_id}/sora-characters/{character_name}")
async def unregister_sora_character(
    project_id: str,
    character_name: str,
    tenant=Depends(get_current_tenant),
):
    """Remove the Sora character_id binding so next production uses prompt-only fallback."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", []) or []
    removed = False
    for c in characters:
        if isinstance(c, dict) and str(c.get("name", "")).strip().lower() == character_name.strip().lower():
            for k in (
                "sora_character_id",
                "sora_character_anchor_scene",
                "sora_character_timestamps",
                "sora_character_locked_at",
                "sora_character_lock_error",
                "sora_character_lock_attempted_at",
            ):
                c.pop(k, None)
            removed = True
            break
    if removed:
        _update_project_field(tenant["id"], project_id, {"characters": characters})
    return {"character_name": character_name, "removed": removed}
