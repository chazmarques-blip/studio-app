"""Auto-generated module from studio.py split."""
from ._shared import *

# ══ BOOK EXPORT ENDPOINTS ══

@router.post("/projects/{project_id}/book/generate-cover")
async def generate_book_cover(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate a book cover image with all characters and creative title."""
    from core.book_generator import generate_cover_image, generate_creative_title
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    characters = project.get("characters", [])
    char_avatars = project.get("character_avatars", {})
    production_design = project.get("agents_output", {}).get("production_design", {})
    scenes = project.get("scenes", [])
    lang = project.get("language", "pt")
    name = project.get("name", "Meu Livro")

    # Generate creative title
    creative_title = generate_creative_title(name, scenes, lang)
    logger.info(f"Book [{project_id}]: Creative title: {creative_title}")

    # Generate cover image
    cover_bytes = generate_cover_image(name, characters, char_avatars, production_design, lang)
    cover_url = None
    if cover_bytes:
        fname = f"books/{project_id}/cover.png"
        cover_url = _upload_to_storage(cover_bytes, fname, "image/png")

    # Save to project
    project["book_cover_url"] = cover_url
    project["book_title"] = creative_title
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)

    return {
        "cover_url": cover_url,
        "creative_title": creative_title,
    }


@router.get("/projects/{project_id}/book/pdf")
async def export_pdf_storybook(project_id: str, tenant=Depends(get_current_tenant)):
    """Generate and return a PDF storybook."""
    from core.book_generator import generate_pdf_storybook
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    if not panels:
        raise HTTPException(status_code=400, detail="No storyboard panels")

    creative_title = project.get("book_title", project.get("name", "Meu Livro"))
    cover_url = project.get("book_cover_url")
    lang = project.get("language", "pt")

    pdf_bytes = generate_pdf_storybook(
        project_name=project.get("name", ""),
        creative_title=creative_title,
        panels=panels,
        cover_url=cover_url,
        lang=lang,
    )

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{creative_title.replace(" ", "_")}.pdf"',
        },
    )


@router.get("/projects/{project_id}/book/interactive-data")
async def get_interactive_book_data(project_id: str, tenant=Depends(get_current_tenant)):
    """Get structured JSON data for the Interactive Book reader."""
    from core.book_generator import build_interactive_book_data
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    if not panels:
        raise HTTPException(status_code=400, detail="No storyboard panels")

    creative_title = project.get("book_title", project.get("name", "Meu Livro"))
    cover_url = project.get("book_cover_url")
    lang = project.get("language", "pt")

    book_data = build_interactive_book_data(
        project_id=project_id,
        project_name=project.get("name", ""),
        creative_title=creative_title,
        panels=panels,
        cover_url=cover_url,
        lang=lang,
    )
    return book_data


@router.post("/projects/{project_id}/book/tts-page")
async def generate_page_tts(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Generate TTS audio for a specific book page."""
    text = payload.get("text", "")
    voice_id = payload.get("voice_id", "onwK4e9ZLuTAKqWW03F9")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ElevenLabs key not configured")

    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": elevenlabs_key, "Content-Type": "application/json"},
            json={
                "text": text[:500],
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.6, "similarity_boost": 0.8},
            },
        )
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"TTS failed: {r.status_code}")

        audio_bytes = r.content
        fname = f"books/{project_id}/tts_{hash(text) % 100000}.mp3"
        audio_url = _upload_to_storage(audio_bytes, fname, "audio/mpeg")
        return {"audio_url": audio_url}



@router.post("/projects/{project_id}/clear-outputs")
async def clear_scene_outputs(project_id: str, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Remove outputs for specific scenes to force re-generation. keep_scenes: list of scene numbers to KEEP."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    keep = set(payload.get("keep_scenes", []))
    outputs = project.get("outputs", [])
    kept = [o for o in outputs if o.get("scene_number") in keep or o.get("type") == "final_video"]
    removed = len(outputs) - len(kept)
    project["outputs"] = kept
    project["status"] = "complete"  # Keep complete so start-production works
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "removed": removed, "kept": len(kept)}


@router.post("/projects/{project_id}/merge-chat-scenes")
async def merge_chat_scenes(project_id: str, tenant=Depends(get_current_tenant)):
    """Extract scenes from ALL chat history messages and merge into a unified scenes array.
    Fixes projects where continuation scenes replaced earlier ones."""
    import re
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_history = project.get("chat_history", [])
    current_scenes = project.get("scenes", [])
    current_nums = {s.get("scene_number") for s in current_scenes}

    # Parse scenes from assistant messages in chat history
    scene_pattern = re.compile(
        r'\*\*CENA\s+(\d+)\*\*\s*\(([^)]+)\)\s*[—-]\s*([^\n]+)\n'
        r'_([^_]+)_\n'
        r'(?:"([^"]*)"\n)?'
        r'Personagens:\s*([^\n]+)',
        re.MULTILINE
    )

    recovered = []
    for msg in chat_history:
        if msg.get("role") != "assistant":
            continue
        text = msg.get("text", "")
        for m in scene_pattern.finditer(text):
            scene_num = int(m.group(1))
            if scene_num not in current_nums:
                recovered.append({
                    "scene_number": scene_num,
                    "time_start": m.group(2).split("-")[0].strip(),
                    "time_end": m.group(2).split("-")[1].strip() if "-" in m.group(2) else "",
                    "title": m.group(3).strip(),
                    "description": m.group(4).strip(),
                    "dialogue": m.group(5).strip() if m.group(5) else "",
                    "characters_in_scene": [c.strip() for c in m.group(6).split(",")],
                    "emotion": "",
                    "camera": "",
                    "transition": "cut",
                })
                current_nums.add(scene_num)

    if not recovered:
        return {"status": "ok", "message": "No missing scenes found in chat history", "total_scenes": len(current_scenes)}

    merged = current_scenes + recovered
    merged.sort(key=lambda x: x.get("scene_number", 0))
    project["scenes"] = merged
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _add_milestone(project, "scenes_merged", f"Cenas recuperadas do histórico — {len(recovered)} cenas adicionadas (total: {len(merged)})")
    _save_project(tenant["id"], settings, projects)

    logger.info(f"Studio [{project_id}]: Merged {len(recovered)} recovered scenes from chat history (total: {len(merged)})")
    return {
        "status": "ok",
        "recovered": len(recovered),
        "total_scenes": len(merged),
        "recovered_scene_numbers": sorted([s["scene_number"] for s in recovered]),
    }


@router.post("/projects/{project_id}/recover-videos")
async def recover_videos(project_id: str, tenant=Depends(get_current_tenant)):
    """Recover video URLs from Supabase Storage when outputs array was lost (race condition fix)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    existing_outputs = {o.get("scene_number") for o in project.get("outputs", []) if o.get("url")}
    recovered = []

    for s in scenes:
        sn = s.get("scene_number", 0)
        if sn in existing_outputs:
            continue
        filename = f"studio/{project_id}_scene_{sn}.mp4"
        try:
            url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
            # Verify the file exists by checking the URL
            import httpx
            resp = httpx.head(url, timeout=5, follow_redirects=True)
            if resp.status_code == 200:
                recovered.append({
                    "id": uuid.uuid4().hex[:8], "type": "video", "url": url,
                    "scene_number": sn, "duration": 12,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception:
            continue

    if recovered:
        outputs = project.get("outputs", [])
        outputs.extend(recovered)
        outputs.sort(key=lambda x: x.get("scene_number", 0))
        project["outputs"] = outputs
        project["status"] = "complete"
        project["error"] = None
        _add_milestone(project, "videos_recovered", f"{len(recovered)} vídeos recuperados do storage")
        _save_project(tenant["id"], settings, projects)

    return {
        "status": "ok",
        "recovered": len(recovered),
        "total_outputs": len(project.get("outputs", [])),
        "project_status": project.get("status"),
    }


