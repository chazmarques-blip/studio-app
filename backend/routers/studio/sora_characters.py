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
) -> Optional[str]:
    """POST /v1/sora/characters — returns `character_id` or None on failure.

    Raises nothing; logs errors and returns None so callers fall back safely.
    """
    if not openai_key:
        logger.warning("Sora Characters: OPENAI_API_KEY missing — skipping register")
        return None
    if not video_url or not timestamps:
        logger.warning(f"Sora Characters: invalid input video_url={bool(video_url)} ts={timestamps}")
        return None

    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sora-2-character",
        "url": video_url,
        "timestamps": timestamps,
    }
    if label:
        payload["label"] = label[:60]

    try:
        resp = requests.post(
            "https://api.openai.com/v1/sora/characters",
            headers=headers,
            json=payload,
            timeout=120,
        )
        if resp.status_code >= 400:
            logger.error(
                f"Sora Characters register failed: {resp.status_code} {resp.text[:300]}"
            )
            return None
        data = resp.json()
        char_id = data.get("id") or data.get("character_id")
        if not char_id:
            logger.error(f"Sora Characters: no id returned: {data}")
            return None
        logger.info(f"Sora Characters registered: {char_id} (label={label})")
        return char_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Sora Characters network error: {e}")
        return None


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
    char_id = _register_sora_character_http(
        openai_key=OPENAI_API_KEY,
        video_url=anchor["video_url"],
        timestamps=timestamps,
        label=req.character_name,
    )
    if not char_id:
        raise HTTPException(status_code=502, detail="Sora Characters API rejected registration")

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

        timestamps = _default_timestamps_for_duration(anchor.get("duration") or 12)
        char_id = _register_sora_character_http(
            openai_key=OPENAI_API_KEY,
            video_url=anchor["video_url"],
            timestamps=timestamps,
            label=name,
        )
        if not char_id:
            failed.append({"name": name, "reason": "api_rejected"})
            continue

        char["sora_character_id"] = char_id
        char["sora_character_anchor_scene"] = anchor.get("scene_number")
        char["sora_character_timestamps"] = timestamps
        registered.append({
            "name": name,
            "sora_character_id": char_id,
            "anchor_scene": anchor.get("scene_number"),
        })

    if registered:
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
            for k in ("sora_character_id", "sora_character_anchor_scene", "sora_character_timestamps"):
                c.pop(k, None)
            removed = True
            break
    if removed:
        _update_project_field(tenant["id"], project_id, {"characters": characters})
    return {"character_name": character_name, "removed": removed}
