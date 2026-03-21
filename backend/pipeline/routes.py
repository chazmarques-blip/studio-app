"""Pipeline core routes: CRUD, music, publishing, regeneration."""
import asyncio
import os
import re
import uuid
import subprocess
import time
import threading
import urllib.request
import base64
from datetime import datetime, timezone
from io import BytesIO

from fastapi import Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from PIL import Image

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from core.deps import supabase, get_current_user, EMERGENT_KEY, logger
from pipeline.router import router
from pipeline.config import (
    STEP_ORDER, STEP_LABELS, PAUSE_AFTER, MUSIC_LIBRARY,
    PLATFORM_ASPECT_RATIOS, VIDEO_PLATFORM_FORMATS,
    EMERGENT_PROXY_URL, UPLOADS_DIR, STORAGE_BUCKET,
    PipelineCreate, PipelineApprove,
    RegenerateDesignRequest, RegenerateStyleRequest,
    EditImageTextRequest, PublishRequest,
    UpdateCopyRequest, RegenerateImageRequest, CloneLanguageRequest,
)
from pipeline.utils import (
    _upload_to_storage, _get_tenant, _next_step,
    _clean_copy_text, _gemini_edit_image, _gemini_edit_multi_ref,
    _ffprobe_duration, _delete_from_storage, _describe_person,
    FFMPEG_PATH,
)
from pipeline.media import (
    _generate_image, _generate_single_image,
    _resize_image_for_platform, _create_platform_variants,
    _create_video_variants, _generate_design_images,
    _generate_commercial_video, _generate_presenter_video,
    _generate_narration, _combine_commercial_video,
    _edit_exact_image, _edit_text_in_image,
)
from pipeline.engine import (
    _start_step_bg, _active_pipelines,
    _recover_orphaned_pipelines,
)




def _find_campaign_for_pipeline(campaigns, pipeline_id):
    """Find a campaign that matches a pipeline_id.
    Checks metrics.schedule.pipeline_id (primary) and metrics.stats.pipeline_id (legacy)."""
    for c in campaigns:
        m = c.get("metrics") or {}
        sched_pid = m.get("schedule", {}).get("pipeline_id")
        legacy_pid = m.get("stats", {}).get("pipeline_id")
        if sched_pid == pipeline_id or legacy_pid == pipeline_id:
            return c
    return None


def _update_campaign_stats(campaign, updates):
    """Update a campaign's metrics.stats with the given dict, preserving existing data."""
    m = campaign.get("metrics") or {}
    st = m.get("stats") or {}
    st.update(updates)
    m["stats"] = st
    supabase.table("campaigns").update({"metrics": m}).eq("id", campaign["id"]).execute()
    return st



@router.get("/music-library")
async def get_music_library():
    """Return available background music tracks with preview URLs"""
    music_dir = "/app/backend/assets/music"
    tracks = []
    for key, info in MUSIC_LIBRARY.items():
        filepath = os.path.join(music_dir, info["file"])
        if os.path.exists(filepath):
            tracks.append({
                "id": key,
                "name": info["name"],
                "description": info["description"],
                "duration": info["duration"],
                "file": info["file"],
                "category": info.get("category", "General"),
                "preview_url": f"/api/campaigns/pipeline/music-preview/{key}",
            })
    return {"tracks": tracks}

@router.get("/music-preview/{track_id}")
async def preview_music(track_id: str):
    """Stream a music track for preview"""
    from fastapi.responses import FileResponse
    info = MUSIC_LIBRARY.get(track_id)
    if not info:
        raise HTTPException(status_code=404, detail="Track not found")
    filepath = f"/app/backend/assets/music/{info['file']}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="audio/mpeg", filename=info["file"])



@router.post("/upload")
async def upload_pipeline_asset(
    file: UploadFile = File(...),
    asset_type: str = Form("reference"),
    user=Depends(get_current_user)
):
    """Upload a brand logo or reference image to Supabase Storage"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = os.path.splitext(file.filename or "upload.png")[1] or ".png"
    filename = f"assets/{asset_type}_{uuid.uuid4().hex[:8]}{ext}"
    content_type = file.content_type or "image/png"
    public_url = _upload_to_storage(content, filename, content_type)
    return {"url": public_url, "filename": filename, "type": asset_type, "size": len(content)}



@router.get("/list")
async def list_pipelines(user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(20).execute()
    # Trigger recovery for stuck pipelines in background
    try:
        _recover_orphaned_pipelines()
    except Exception:
        pass
    return {"pipelines": result.data or []}




@router.post("")
async def create_pipeline(data: PipelineCreate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)

    init_steps = {}
    for s in STEP_ORDER:
        init_steps[s] = {"status": "pending", "output": None, "started_at": None, "completed_at": None}

    pipeline = {
        "tenant_id": tenant["id"],
        "briefing": data.briefing,
        "mode": data.mode,
        "platforms": data.platforms,
        "status": "running",
        "current_step": "sofia_copy",
        "steps": init_steps,
        "result": {
            "context": data.context or {},
            "contact_info": data.contact_info or {},
            "uploaded_assets": data.uploaded_assets or [],
            "campaign_name": data.campaign_name or "",
            "campaign_language": data.campaign_language or "",
            "media_formats": data.media_formats or {},
            "selected_music": data.selected_music or "",
            "skip_video": data.skip_video or False,
            "video_mode": data.video_mode or "narration",
            "avatar_url": data.avatar_url or "",
            "avatar_voice": data.avatar_voice or None,
        },
    }

    result = supabase.table("pipelines").insert(pipeline).execute()
    pid = result.data[0]["id"]

    _start_step_bg(pid, "sofia_copy")
    return result.data[0]





@router.get("/saved/history")
async def get_saved_history_v2(user=Depends(get_current_user)):
    """Get saved logos and recent briefings from previous pipelines"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("briefing, result, platforms, created_at").eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(20).execute()
    pipelines = result.data or []

    logos = []
    seen_urls = set()
    briefings = []
    seen_briefings = set()

    for p in pipelines:
        assets = (p.get("result") or {}).get("uploaded_assets") or []
        for a in assets:
            if a.get("type") == "logo" and a.get("url") and a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                logos.append({"url": a["url"], "filename": a.get("filename", "logo")})
        b = p.get("briefing", "").strip()
        camp_name = (p.get("result") or {}).get("campaign_name", "")
        camp_lang = (p.get("result") or {}).get("campaign_language", "")
        if b and b not in seen_briefings:
            seen_briefings.add(b)
            briefings.append({
                "briefing": b, "campaign_name": camp_name,
                "campaign_language": camp_lang,
                "platforms": p.get("platforms", []),
                "created_at": p.get("created_at", ""),
            })

    return {"logos": logos[:10], "briefings": briefings[:10]}




@router.delete("/saved/logo")
async def delete_saved_logo_v2(url: str, user=Depends(get_current_user)):
    """Delete a saved logo file from Supabase Storage or local disk"""
    await _get_tenant(user)
    if url.startswith("http"):
        # Supabase Storage URL — extract filename from URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/pipeline-assets/assets/logo_xxx.png
        parts = url.split(f"/{STORAGE_BUCKET}/")
        if len(parts) == 2:
            _delete_from_storage(parts[1])
        return {"status": "deleted", "url": url}
    elif url.startswith("/api/uploads/pipeline/"):
        # Legacy local file
        filename = url.split("/")[-1]
        filepath = os.path.join(UPLOADS_DIR, "assets", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        return {"status": "deleted", "url": url}
    else:
        raise HTTPException(status_code=400, detail="Invalid logo URL")




@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    # Auto-recover stuck pipelines on get
    if pipeline.get("status") == "running":
        current = pipeline.get("current_step", "")
        step_data = pipeline.get("steps", {}).get(current, {})
        step_status = step_data.get("status", "")
        
        should_recover = False
        if step_status == "pending" and current in STEP_ORDER and pipeline["id"] not in _active_pipelines:
            should_recover = True
        elif step_status == "running" and current in STEP_ORDER and pipeline["id"] not in _active_pipelines:
            # Check if stuck for more than 3 minutes
            started = step_data.get("started_at", "")
            if started:
                try:
                    from datetime import datetime, timezone
                    started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - started_dt).total_seconds()
                    if age > 180:
                        should_recover = True
                        # Reset the step to pending before restarting
                        steps = pipeline.get("steps", {})
                        steps[current]["status"] = "pending"
                        steps[current]["started_at"] = None
                        supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline["id"]).execute()
                        pipeline["steps"] = steps
                except Exception:
                    pass
        
        if should_recover:
            logger.info(f"GET auto-recovery: Starting step {current} for pipeline {pipeline_id}")
            _start_step_bg(pipeline_id, current)
    return pipeline




@router.post("/{pipeline_id}/approve")
async def approve_step(pipeline_id: str, data: PipelineApprove, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    if pipeline["status"] != "waiting_approval":
        raise HTTPException(status_code=400, detail="Pipeline is not waiting for approval")

    steps = pipeline.get("steps") or {}

    # Find the step that just completed and needs approval
    # First, try using current_step - the pending step IS what needs to run next
    current = pipeline.get("current_step", "")
    approval_step = None

    if current and steps.get(current, {}).get("status") == "pending":
        # The current step is pending — find the previous completed step
        idx = STEP_ORDER.index(current) if current in STEP_ORDER else -1
        if idx > 0:
            approval_step = STEP_ORDER[idx - 1]

    # Fallback: search in reverse for any completed step at a pause point
    if not approval_step:
        for s in reversed(STEP_ORDER):
            if steps.get(s, {}).get("status") == "completed" and s in PAUSE_AFTER:
                approval_step = s
                break

    # Final fallback: find last completed step before first pending step
    if not approval_step:
        for i, s in enumerate(STEP_ORDER):
            if steps.get(s, {}).get("status") == "pending" and i > 0:
                approval_step = STEP_ORDER[i - 1]
                break

    if not approval_step:
        raise HTTPException(status_code=400, detail="No step awaiting approval")

    # Apply user's selection
    if approval_step == "ana_review_copy" and data.selection is not None:
        steps[approval_step]["user_selection"] = data.selection
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        copy_only = re.split(r'===\s*IMAGE BRIEFING\s*===', sofia_output, flags=re.IGNORECASE)[0]
        variations = re.split(r'===\s*VARIATION \d+\s*===', copy_only)
        variations = [v.strip() for v in variations[1:] if v.strip()]
        sel = data.selection
        if 0 < sel <= len(variations):
            steps[approval_step]["approved_content"] = variations[sel - 1]

    elif approval_step == "rafael_review_design" and data.selections:
        steps[approval_step]["user_selections"] = data.selections
        steps[approval_step]["selections"] = data.selections

    if data.feedback:
        steps[approval_step]["user_feedback"] = data.feedback

    supabase.table("pipelines").update({
        "steps": steps,
        "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    # Run next step
    nxt = _next_step(approval_step)
    if nxt:
        _start_step_bg(pipeline_id, nxt)
        return {"status": "approved", "next_step": nxt}
    else:
        supabase.table("pipelines").update({"status": "completed"}).eq("id", pipeline_id).execute()
        return {"status": "completed"}


from pipeline.engine import _start_video_after_approval_bg


@router.post("/{pipeline_id}/approve-audio")
async def approve_audio(pipeline_id: str, data: PipelineApprove, user=Depends(get_current_user)):
    """Approve or reject the audio preview before video generation (saves Sora 2 credits)."""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    if pipeline["status"] != "waiting_audio_approval":
        raise HTTPException(status_code=400, detail="Pipeline is not waiting for audio approval")

    steps = pipeline.get("steps") or {}
    marcos = steps.get("marcos_video", {})

    if data.feedback and not getattr(data, 'approved', True):
        # Rejected: rerun marcos_video with feedback
        marcos["revision_feedback"] = data.feedback
        marcos["previous_output"] = marcos.get("output", "")
        marcos["status"] = "pending"
        supabase.table("pipelines").update({
            "steps": steps, "status": "running", "current_step": "marcos_video",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", pipeline_id).execute()
        _start_step_bg(pipeline_id, "marcos_video")
        return {"status": "revision_requested", "next_step": "marcos_video"}

    # Approved: If user selected an alternative voice, save it
    selected_voice_id = getattr(data, 'selected_voice_id', None) or ""
    if selected_voice_id:
        # User chose an alternative voice — update the voice config for video generation
        alternatives = marcos.get("voice_alternatives", [])
        chosen = next((a for a in alternatives if a.get("voice_id") == selected_voice_id), None)
        if chosen:
            marcos["selected_voice_config"] = {
                "voice_id": selected_voice_id,
                "stability": 0.40,
                "similarity_boost": 0.80,
                "style": 0.45,
            }
            # Also update Dylan's output to reflect the new voice choice
            dylan = steps.get("dylan_sound", {})
            dylan_output = dylan.get("output", "")
            if dylan_output:
                dylan["output"] = re.sub(
                    r'Voice ID:\s*\S+', f'Voice ID: {selected_voice_id}', dylan_output
                )
                steps["dylan_sound"] = dylan

    marcos["audio_approved"] = True
    marcos["audio_approved_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("pipelines").update({
        "steps": steps,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    _start_video_after_approval_bg(pipeline_id)
    return {"status": "approved", "message": "Video generation started"}


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").delete().eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"status": "deleted"}




@router.post("/{pipeline_id}/retry")
async def retry_failed_step(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    if pipeline["status"] not in ("failed", "running", "waiting_audio_approval"):
        raise HTTPException(status_code=400, detail="Pipeline is not in a retryable state")

    steps = pipeline.get("steps") or {}
    retry_step = None
    for s in STEP_ORDER:
        st = steps.get(s, {}).get("status")
        if st in ("failed", "running", "generating_images", "generating_video", "waiting_audio_approval"):
            retry_step = s
            break

    if not retry_step:
        raise HTTPException(status_code=400, detail="No retryable step found")

    steps[retry_step]["status"] = "pending"
    steps[retry_step]["error"] = None
    supabase.table("pipelines").update({
        "steps": steps, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    _start_step_bg(pipeline_id, retry_step)
    return {"status": "retrying", "step": retry_step}




@router.post("/{pipeline_id}/regenerate-design")
async def regenerate_design(pipeline_id: str, data: RegenerateDesignRequest, user=Depends(get_current_user)):
    """Regenerate a specific design image with user feedback"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    lucas = steps.get("lucas_design", {})

    if lucas.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Design step not completed")

    old_prompts = lucas.get("image_prompts", [])
    old_urls = lucas.get("image_urls", [])
    idx = data.design_index

    if idx < 0 or idx >= len(old_prompts):
        raise HTTPException(status_code=400, detail="Invalid design index")

    # Build enhanced prompt with feedback
    original_prompt = old_prompts[idx]
    enhanced_prompt = f"{original_prompt}. ADJUSTMENTS: {data.feedback}. ABSOLUTE RULE: ZERO text, words, logos, or placeholder shapes in the image. Pure visual only." if data.feedback else original_prompt

    # Mark as regenerating
    lucas["status"] = "generating_images"
    steps["lucas_design"] = lucas
    supabase.table("pipelines").update({
        "steps": steps, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    # Regenerate in background thread
    def _regen():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            new_url = loop.run_until_complete(_generate_image(enhanced_prompt, pipeline_id, idx + 10))
            fresh = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data[0]
            s = fresh.get("steps", {})
            urls = s.get("lucas_design", {}).get("image_urls", list(old_urls))
            prompts = s.get("lucas_design", {}).get("image_prompts", list(old_prompts))
            if new_url:
                urls[idx] = new_url
                prompts[idx] = enhanced_prompt
            s["lucas_design"]["image_urls"] = urls
            s["lucas_design"]["image_prompts"] = prompts
            s["lucas_design"]["status"] = "completed"
            prev_status = fresh.get("status")
            new_status = "waiting_approval" if prev_status == "running" else prev_status
            if fresh.get("current_step") in ("rafael_review_design", "lucas_design"):
                new_status = "waiting_approval"
            supabase.table("pipelines").update({
                "steps": s, "status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
        except Exception as e:
            logger.error(f"Regenerate design failed: {e}")
            fresh = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data[0]
            s = fresh.get("steps", {})
            s["lucas_design"]["status"] = "completed"
            supabase.table("pipelines").update({
                "steps": s, "status": "waiting_approval",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
        finally:
            loop.close()

    t = threading.Thread(target=_regen, daemon=True)
    t.start()
    return {"status": "regenerating", "design_index": idx}




@router.get("/{pipeline_id}/labels")
async def get_step_labels(pipeline_id: str, user=Depends(get_current_user)):
    return {"labels": STEP_LABELS, "order": STEP_ORDER}




@router.post("/{pipeline_id}/regenerate-video-variants")
async def regenerate_video_variants(pipeline_id: str, user=Depends(get_current_user)):
    """Regenerate per-platform video variants from the master video."""
    tenant = await _get_tenant(user)
    pipeline = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute().data
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    p = pipeline[0]
    marcos = p.get("steps", {}).get("marcos_video", {})
    video_url = marcos.get("video_url")
    video_format = marcos.get("video_format", "horizontal")
    platforms = p.get("platforms", [])
    if not video_url:
        raise HTTPException(status_code=400, detail="No master video to create variants from")

    try:
        variants = await _create_video_variants(pipeline_id, video_url, video_format, platforms)
        if variants:
            steps = p.get("steps", {})
            steps["marcos_video"]["video_variants"] = variants
            supabase.table("pipelines").update({
                "steps": steps,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
            # Also update campaign stats
            campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
            c = _find_campaign_for_pipeline(campaigns, pipeline_id)
            if c:
                _update_campaign_stats(c, {"video_variants": variants})
                logger.info(f"Updated campaign {c['id']} with {len(variants)} video variants")
            return {"status": "success", "variants": variants, "count": len(variants)}
        return {"status": "no_variants_generated"}
    except Exception as e:
        logger.error(f"Regenerate video variants failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.post("/{pipeline_id}/remix-audio")
async def remix_audio(pipeline_id: str, user=Depends(get_current_user)):
    """Re-mix audio for an existing video with corrected volume levels"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    marcos = steps.get("marcos_video", {})
    video_url = marcos.get("video_url", "")
    marcos_output = marcos.get("output", "")
    if not video_url:
        raise HTTPException(status_code=400, detail="No video found to remix")

    # Parse music mood from marcos output
    music_mood = "corporate"
    music_match = re.search(r'===MUSIC DIRECTION===([\s\S]*?)===(?:NARRATION TONE|CTA SEQUENCE)===', marcos_output, re.IGNORECASE)
    if music_match:
        mood_line = re.search(r'Mood:\s*(\w+)', music_match.group(1), re.IGNORECASE)
        if mood_line:
            music_mood = mood_line.group(1).strip().lower()

    # User-selected music override
    user_music = pipeline.get("result", {}).get("selected_music", "")
    if user_music:
        music_mood = user_music

    def _remix_bg(pid, vid_url, mood):
        import urllib.request as urlreq
        try:
            # Download existing video
            vid_path = f"/tmp/{pid}_remix_src.mp4"
            urlreq.urlretrieve(vid_url, vid_path)

            # Extract video (no audio) and existing narration
            vid_only = f"/tmp/{pid}_remix_vid.mp4"
            subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -an -c:v copy {vid_only}", shell=True, capture_output=True, timeout=60)

            # Extract existing audio to analyze
            old_audio = f"/tmp/{pid}_remix_old_audio.wav"
            subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -vn -acodec pcm_s16le -ar 44100 -ac 2 {old_audio}", shell=True, capture_output=True, timeout=30)

            # Get video duration
            vid_duration = _ffprobe_duration(vid_only) or 23.0

            # Select music
            music_dir = "/app/backend/assets/music"
            mood_map = {
                "upbeat": "upbeat.mp3", "energetic": "energetic.mp3", "exciting": "energetic.mp3",
                "emotional": "emotional.mp3", "inspirational": "emotional.mp3",
                "cinematic": "cinematic.mp3", "dramatic": "cinematic.mp3", "epic": "cinematic.mp3",
                "corporate": "corporate.mp3", "professional": "corporate.mp3", "clean": "corporate.mp3",
                "luxury": "jazz_smooth.mp3", "elegant": "classical_piano.mp3", "sophisticated": "jazz_smooth.mp3",
                "relaxing": "ambient_dreamy.mp3", "calm": "ambient_nature.mp3", "peaceful": "ambient_nature.mp3",
                "modern": "electronic_chill.mp3", "tech": "electronic_chill.mp3",
                "warm": "pop_acoustic.mp3", "friendly": "country_modern.mp3",
                "fun": "pop_dance.mp3", "happy": "pop_acoustic.mp3",
            }
            mood_file = mood_map.get(mood, "corporate.mp3")
            bg_music = os.path.join(music_dir, mood_file)
            if not os.path.exists(bg_music):
                bg_music = os.path.join(music_dir, "corporate.mp3")

            # Resample with pre-reduced music volume
            narr_rs = f"/tmp/{pid}_remix_narr.wav"
            music_rs = f"/tmp/{pid}_remix_music.wav"
            # Use old audio as narration source (it already has the mixed audio, so we try to use original narration if available)
            narr_src = f"/tmp/{pid}_narration.mp3"
            if not os.path.exists(narr_src):
                narr_src = old_audio  # fallback to extracted audio
            subprocess.run(f"{FFMPEG_PATH} -y -i {narr_src} -ar 44100 -ac 2 {narr_rs}", shell=True, capture_output=True, timeout=30)
            subprocess.run(f"{FFMPEG_PATH} -y -i {bg_music} -af volume=0.08 -ar 44100 -ac 2 -t {vid_duration} {music_rs}", shell=True, capture_output=True, timeout=30)

            # Professional mix
            mixed = f"/tmp/{pid}_remix_mixed.wav"
            mix_filter = (
                f"[0:a]volume=1.5,acompressor=threshold=-20dB:ratio=4:attack=5:release=200[narr];"
                f"[1:a]afade=t=in:d=2,afade=t=out:st={max(vid_duration-3, 18)}:d=3[music];"
                f"[narr][music]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[out]"
            )
            r = subprocess.run([FFMPEG_PATH, "-y", "-i", narr_rs, "-i", music_rs, "-filter_complex", mix_filter, "-map", "[out]", "-t", str(vid_duration), "-ar", "44100", "-ac", "2", mixed], capture_output=True, text=True, timeout=60)

            if r.returncode != 0:
                logger.error(f"Remix audio mix failed: {r.stderr[:200]}")
                return

            # Merge new audio with video
            output = f"/tmp/{pid}_remixed.mp4"
            subprocess.run([FFMPEG_PATH, "-y", "-i", vid_only, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output], capture_output=True, timeout=60)

            if os.path.exists(output):
                with open(output, "rb") as f:
                    video_bytes = f.read()
                filename = f"videos/{pid}_commercial.mp4"
                new_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                # Update pipeline
                steps["marcos_video"]["video_url"] = new_url
                supabase.table("pipelines").update({"steps": steps}).eq("id", pid).execute()
                # Also update campaign if exists (search by pipeline_id in metrics JSONB)
                try:
                    camps = supabase.table("campaigns").select("id, metrics").eq("tenant_id", supabase.table("pipelines").select("tenant_id").eq("id", pid).single().execute().data["tenant_id"]).execute()
                    c = _find_campaign_for_pipeline(camps.data or [], pid)
                    if c:
                        _update_campaign_stats(c, {"video_url": new_url})
                        logger.info(f"Updated campaign {c['id']} with new video URL")
                except Exception as ce:
                    logger.warning(f"Campaign update skipped: {ce}")
                logger.info(f"Audio remixed successfully for pipeline {pid}")
        except Exception as e:
            logger.error(f"Remix failed for {pid}: {e}")

    t = threading.Thread(target=_remix_bg, args=(pipeline_id, video_url, music_mood), daemon=True)
    t.start()
    return {"status": "remixing", "message": "Audio is being remixed with corrected levels"}




@router.post("/remix-all-videos")
async def remix_all_videos(user=Depends(get_current_user)):
    """Batch remix audio for ALL existing videos with corrected volume levels"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("id, steps, result").eq("tenant_id", tenant["id"]).execute()
    pipelines_with_video = []
    for p in (result.data or []):
        vid_url = (p.get("steps") or {}).get("marcos_video", {}).get("video_url", "")
        if vid_url:
            pipelines_with_video.append(p["id"])

    # Process all remixes in a single background thread, sequentially
    def _batch_remix_all(pipeline_ids, tenant_id):
        import urllib.request as urlreq
        for pid in pipeline_ids:
            try:
                p_data = supabase.table("pipelines").select("*").eq("id", pid).single().execute()
                if not p_data.data:
                    continue
                steps = p_data.data.get("steps", {})
                marcos = steps.get("marcos_video", {})
                video_url = marcos.get("video_url", "")
                marcos_output = marcos.get("output", "")
                if not video_url:
                    continue
                music_mood = "corporate"
                music_match = re.search(r'Mood:\s*(\w+)', marcos_output, re.IGNORECASE)
                if music_match:
                    music_mood = music_match.group(1).strip().lower()
                user_music = p_data.data.get("result", {}).get("selected_music", "")
                if user_music:
                    music_mood = user_music

                vid_path = f"/tmp/{pid}_remix_src.mp4"
                urlreq.urlretrieve(video_url, vid_path)
                vid_only = f"/tmp/{pid}_remix_vid.mp4"
                subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -an -c:v copy {vid_only}", shell=True, capture_output=True, timeout=60)
                vid_duration = _ffprobe_duration(vid_only) or 23.0
                music_dir = "/app/backend/assets/music"
                mood_map = {
                    "upbeat": "upbeat.mp3", "energetic": "energetic.mp3", "cinematic": "cinematic.mp3",
                    "corporate": "corporate.mp3", "emotional": "emotional.mp3", "luxury": "jazz_smooth.mp3",
                    "calm": "ambient_nature.mp3", "modern": "electronic_chill.mp3", "warm": "pop_acoustic.mp3",
                    "fun": "pop_dance.mp3", "elegant": "classical_piano.mp3",
                }
                bg_music = os.path.join(music_dir, mood_map.get(music_mood, "corporate.mp3"))
                if not os.path.exists(bg_music):
                    bg_music = os.path.join(music_dir, "corporate.mp3")
                narr_src = f"/tmp/{pid}_narration.mp3"
                if not os.path.exists(narr_src):
                    old_audio = f"/tmp/{pid}_remix_old.wav"
                    subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -vn -acodec pcm_s16le -ar 44100 -ac 2 {old_audio}", shell=True, capture_output=True, timeout=30)
                    narr_src = old_audio
                narr_rs = f"/tmp/{pid}_remix_narr.wav"
                music_rs = f"/tmp/{pid}_remix_music.wav"
                subprocess.run(f"{FFMPEG_PATH} -y -i {narr_src} -ar 44100 -ac 2 {narr_rs}", shell=True, capture_output=True, timeout=30)
                subprocess.run(f"{FFMPEG_PATH} -y -i {bg_music} -af volume=0.08 -ar 44100 -ac 2 -t {vid_duration} {music_rs}", shell=True, capture_output=True, timeout=30)
                mixed = f"/tmp/{pid}_remix_mixed.wav"
                mix_filter = f"[0:a]volume=1.5,acompressor=threshold=-20dB:ratio=4:attack=5:release=200[narr];[1:a]afade=t=in:d=2,afade=t=out:st={max(vid_duration-3,18)}:d=3[music];[narr][music]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[out]"
                subprocess.run([FFMPEG_PATH, "-y", "-i", narr_rs, "-i", music_rs, "-filter_complex", mix_filter, "-map", "[out]", "-t", str(vid_duration), "-ar", "44100", "-ac", "2", mixed], capture_output=True, timeout=60)
                output = f"/tmp/{pid}_remixed.mp4"
                subprocess.run([FFMPEG_PATH, "-y", "-i", vid_only, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output], capture_output=True, timeout=60)
                if os.path.exists(output):
                    with open(output, "rb") as f:
                        vb = f.read()
                    fn = f"videos/{pid}_commercial.mp4"
                    new_url = _upload_to_storage(vb, fn, "video/mp4")
                    steps["marcos_video"]["video_url"] = new_url
                    supabase.table("pipelines").update({"steps": steps}).eq("id", pid).execute()
                    # Update linked campaign
                    try:
                        camps = supabase.table("campaigns").select("id, metrics").eq("tenant_id", tenant_id).execute()
                        c = _find_campaign_for_pipeline(camps.data or [], pid)
                        if c:
                            _update_campaign_stats(c, {"video_url": new_url})
                    except Exception:
                        pass
                    logger.info(f"Batch remix done: {pid}")
                # Clean up temp files
                for f in [vid_path, vid_only, narr_rs, music_rs, mixed, output]:
                    try:
                        os.remove(f)
                    except Exception:
                        pass
                time.sleep(3)  # Delay between uploads to avoid overwhelming Supabase
            except Exception as e:
                logger.error(f"Batch remix failed for {pid}: {e}")
        logger.info(f"Batch remix complete: processed {len(pipeline_ids)} pipelines")

    t = threading.Thread(target=_batch_remix_all, args=(pipelines_with_video, tenant["id"]), daemon=True)
    t.start()
    return {"status": "remixing", "count": len(pipelines_with_video), "pipelines": pipelines_with_video}









@router.post("/regenerate-single-image")
async def regenerate_single_image(body: RegenerateStyleRequest, user=Depends(get_current_user)):
    """Generate a single image with a specific visual style, without needing a full pipeline"""
    tenant = await _get_tenant(user)

    STYLE_PROMPTS = {
        "minimalist": "Ultra minimalist composition. Single powerful focal element against vast negative space. Muted, desaturated palette with one accent color. Zen-like simplicity. Think Apple product photography.",
        "vibrant": "Explosion of saturated colors and dynamic energy. Bold complementary color clashes, motion blur effects, dramatic perspective. Youthful, electric atmosphere.",
        "luxury": "Premium luxury photography. Rich dark backgrounds, dramatic studio lighting with gold/warm highlights, silk textures, shallow depth of field. Ultra-sophisticated mood.",
        "corporate": "Editorial business photography. Clean natural lighting, professional environment, confident subjects or pristine product shots. Trustworthy blue-gray color grading.",
        "playful": "Joyful, whimsical visual storytelling. Bright candy colors, unexpected perspectives, playful subjects in dynamic poses. Warm, inviting, fun.",
        "bold": "High-impact, stop-the-scroll photography. Extreme contrast, dramatic shadows, close-up details, powerful visual tension. Fearless composition.",
        "organic": "Warm, natural, earthy photography. Golden hour lighting, natural textures (wood, linen, stone), warm earth tones, authentic lifestyle moments.",
        "tech": "Futuristic, sleek technology aesthetic. Dark environment with neon accent lighting, reflective surfaces, geometric precision, blue-purple color palette.",
        "cartoon": "Fun cartoon illustration style. Bold outlines, flat vibrant colors, exaggerated proportions, comic book feel. Characters with expressive faces and dynamic poses. Clean vector-like aesthetics.",
        "illustration": "Beautiful hand-drawn illustration. Detailed artistic strokes, warm color palette, editorial magazine quality. Elegant and refined artistic interpretation with depth and texture.",
        "watercolor": "Soft watercolor painting style. Flowing transparent washes of color, gentle gradients, organic paint drips and splashes. Dreamy, artistic, elegant feel with muted pastels.",
        "neon": "Vibrant neon glow aesthetic. Dark background with electric neon colors (pink, cyan, purple). Glowing text effects, cyberpunk atmosphere, high contrast between dark and bright elements.",
        "retro": "Vintage retro style. 70s/80s color palette with warm oranges, browns and teals. Film grain texture, rounded typography, nostalgic feel. Groovy patterns and vintage photography effects.",
        "flat": "Modern flat design illustration. Clean geometric shapes, limited color palette, no gradients or shadows. Bold solid colors, simple icons, contemporary minimalist graphic design.",
        "professional": "High-end commercial photography. Studio-quality lighting, professional color grading, clean background, sharp focus on subject with natural bokeh."
    }

    LANG_MAP = {"pt": "Portuguese (Português)", "es": "Spanish (Español)", "en": "English", "fr": "French (Français)", "de": "German", "it": "Italian"}

    # If pipeline_id is provided and language not explicitly set, fetch from pipeline
    actual_lang = body.language
    if body.pipeline_id and not actual_lang:
        try:
            p = supabase.table("pipelines").select("result").eq("id", body.pipeline_id).execute()
            if p.data:
                pipeline_lang = (p.data[0].get("result") or {}).get("campaign_language", "")
                if pipeline_lang:
                    actual_lang = pipeline_lang
                    logger.info(f"Using pipeline language: {actual_lang}")
        except Exception as e:
            logger.warning(f"Failed to fetch pipeline language: {e}")

    lang_name = LANG_MAP.get(actual_lang, "Portuguese (Português)")
    lang_code = actual_lang or "pt"

    style_desc = STYLE_PROMPTS.get(body.style, STYLE_PROMPTS["professional"])

    # Extract a headline from the campaign copy to use as the EXACT text in the image
    copy_hint = body.campaign_copy[:300] if body.campaign_copy else ""
    extracted_headline = ""
    if copy_hint:
        # Try to extract the title/first line as the headline
        lines = [l.strip() for l in copy_hint.split('\n') if l.strip() and not l.strip().startswith('#')]
        if lines:
            first_line = lines[0]
            # Use the first meaningful line as headline (strip emoji, limit to 7 words)
            headline_words = re.sub(r'[^\w\s]', '', first_line).split()[:7]
            extracted_headline = ' '.join(headline_words)

    # Build prompt with LANGUAGE as the FIRST and DOMINANT instruction
    LANG_PROMPT_TEMPLATES = {
        "pt": "Crie uma imagem de marketing impressionante para: {context}. A mensagem da campanha é: {copy}",
        "es": "Crea una imagen de marketing impresionante para: {context}. El mensaje de la campaña es: {copy}",
        "en": "Create a stunning marketing visual for: {context}. The campaign message is: {copy}",
    }

    if body.prompt_override.strip():
        content_prompt = body.prompt_override.strip()
    else:
        context = body.product_description or body.campaign_name or "brand"
        template = LANG_PROMPT_TEMPLATES.get(lang_code, LANG_PROMPT_TEMPLATES["pt"])
        content_prompt = template.format(context=context, copy=copy_hint[:200] if copy_hint else context)

    # Language enforcement for the prompt
    if lang_code == "en":
        lang_enforcement_top = f"⚠️ MANDATORY: ALL visible text in this image MUST be in English."
        lang_enforcement_bottom = f"🚨 EVERY word visible in the image MUST be in English. Do NOT write text in Spanish, Portuguese, or any other language."
        headline_no_translate = ""
    else:
        lang_enforcement_top = f"⚠️ MANDATORY: ALL visible text in this image MUST be in {lang_name}. ZERO English text allowed."
        lang_enforcement_bottom = f"🚨 EVERY word visible in the image MUST be in {lang_name}. If you write ANY English text, the image is REJECTED."
        headline_no_translate = f" DO NOT translate this headline to English."

    if extracted_headline:
        headline_instruction = f'\nTHE HEADLINE TEXT IN THE IMAGE MUST BE EXACTLY: "{extracted_headline}" (or a short variation of it, MAX 7 words, in {lang_name}).{headline_no_translate}'
    else:
        headline_instruction = f"\nINCLUDE one short impactful headline text (3-7 words) written in {lang_name}, in bold clean typography."

    prompt = f"""{lang_enforcement_top}
{content_prompt}

VISUAL STYLE: {style_desc}
{headline_instruction}
No logos or brand names. 1080x1080 square format.
{lang_enforcement_bottom}"""

    pid = f"single-{uuid.uuid4().hex[:8]}"
    url = await _generate_image(prompt, pid, 1)
    if not url:
        raise HTTPException(status_code=500, detail="Image generation failed after retries")

    # Save image to pipeline gallery if pipeline_id provided
    if body.pipeline_id:
        try:
            p = supabase.table("pipelines").select("steps, tenant_id, platforms").eq("id", body.pipeline_id).eq("tenant_id", tenant["id"]).execute()
            if p.data:
                steps = p.data[0].get("steps", {})
                platforms = p.data[0].get("platforms", [])
                lucas_step = steps.get("lucas_design", {})
                # Merge images from both fields: originals (image_urls) + new ones (images)
                imgs_field = lucas_step.get("images", [])
                urls_field = lucas_step.get("image_urls", [])
                # Deduplicate: originals first, then new ones not already present
                seen = set()
                existing_images = []
                for u in (urls_field + imgs_field):
                    if u and u not in seen:
                        seen.add(u)
                        existing_images.append(u)
                existing_images.append(url)
                lucas_step["images"] = existing_images
                lucas_step["image_urls"] = existing_images  # legacy compat

                # Generate platform variants for this new image
                if platforms:
                    try:
                        new_img_idx = len(existing_images) - 1
                        new_variants = await _create_platform_variants(body.pipeline_id, [url], platforms)
                        existing_variants = lucas_step.get("platform_variants", {})
                        for platform_key, variant_list in new_variants.items():
                            if platform_key not in existing_variants:
                                existing_variants[platform_key] = []
                            existing_variants[platform_key].extend(variant_list)
                        lucas_step["platform_variants"] = existing_variants
                        logger.info(f"Created platform variants for new image across {len(new_variants)} platforms")
                    except Exception as pv_err:
                        logger.warning(f"Failed to create platform variants for new image: {pv_err}")

                steps["lucas_design"] = lucas_step
                supabase.table("pipelines").update({"steps": steps}).eq("id", body.pipeline_id).execute()
                logger.info(f"Saved new style image to pipeline {body.pipeline_id} gallery ({len(existing_images)} total)")

                # Also update linked campaign
                campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
                c = _find_campaign_for_pipeline(campaigns, body.pipeline_id)
                if c:
                    _update_campaign_stats(c, {"images": existing_images, "platform_variants": lucas_step.get("platform_variants", {})})
                    logger.info(f"Updated campaign {c['id']} images + variants ({len(existing_images)} total)")
        except Exception as e:
            logger.warning(f"Failed to save image to pipeline gallery: {e}")

    return {"status": "generated", "image_url": url, "style": body.style}




@router.post("/edit-image-text")
async def edit_image_text(body: EditImageTextRequest, user=Depends(get_current_user)):
    """Edit ONLY the text in an image while preserving the entire visual composition"""
    tenant = await _get_tenant(user)

    # Get pipeline data
    p = supabase.table("pipelines").select("steps, tenant_id, platforms, result").eq("id", body.pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not p.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = p.data[0]
    steps = pipeline.get("steps", {})
    lucas_step = steps.get("lucas_design", {})
    # Merge images from both fields: originals (image_urls) + new ones (images)
    imgs_field = lucas_step.get("images", [])
    urls_field = lucas_step.get("image_urls", [])
    seen = set()
    existing_images = []
    for u in (urls_field + imgs_field):
        if u and u not in seen:
            seen.add(u)
            existing_images.append(u)
    platforms = pipeline.get("platforms", [])

    if body.image_index >= len(existing_images):
        raise HTTPException(status_code=400, detail="Image index out of range")

    original_url = existing_images[body.image_index]

    # Use Gemini image editing to change ONLY the text, preserving the original image
    new_url = await _edit_text_in_image(
        source_image_url=original_url,
        new_text=body.new_text,
        language=body.language or "pt",
        pipeline_id=body.pipeline_id,
        index=body.image_index,
    )

    if not new_url:
        raise HTTPException(status_code=500, detail="Text editing failed — could not modify text in image")

    # Replace the image at the same index
    existing_images[body.image_index] = new_url
    lucas_step["images"] = existing_images
    lucas_step["image_urls"] = existing_images  # legacy compat

    # Generate platform variants for the replacement image
    if platforms:
        try:
            new_variants = await _create_platform_variants(body.pipeline_id, [new_url], platforms)
            existing_variants = lucas_step.get("platform_variants", {})
            for platform_key, variant_list in new_variants.items():
                if platform_key in existing_variants and body.image_index < len(existing_variants[platform_key]):
                    existing_variants[platform_key][body.image_index] = variant_list[0] if variant_list else existing_variants[platform_key][body.image_index]
                elif platform_key not in existing_variants:
                    existing_variants[platform_key] = variant_list
            lucas_step["platform_variants"] = existing_variants
        except Exception as pv_err:
            logger.warning(f"Failed to create platform variants for text edit: {pv_err}")

    steps["lucas_design"] = lucas_step
    supabase.table("pipelines").update({"steps": steps}).eq("id", body.pipeline_id).execute()
    logger.info(f"Replaced image {body.image_index} with text-edited version in pipeline {body.pipeline_id}")

    # Update linked campaign
    try:
        campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
        c = _find_campaign_for_pipeline(campaigns, body.pipeline_id)
        if c:
            _update_campaign_stats(c, {"images": existing_images, "platform_variants": lucas_step.get("platform_variants", {})})
            logger.info(f"Updated campaign {c['id']} with text-edited image")
    except Exception as e:
        logger.warning(f"Failed to update campaign with text-edited image: {e}")

    return {"status": "updated", "image_url": new_url, "image_index": body.image_index}








@router.post("/migrate-images")
async def migrate_pipeline_images(user=Depends(get_current_user)):
    """One-time migration: merge image_urls into images for all pipelines and sync to campaigns"""
    tenant = await _get_tenant(user)
    pipelines = supabase.table("pipelines").select("id, steps, tenant_id, platforms").eq("tenant_id", tenant["id"]).execute().data or []
    campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
    
    fixed_pipelines = 0
    fixed_campaigns = 0
    
    for p in pipelines:
        steps = p.get("steps", {})
        lucas = steps.get("lucas_design", {})
        imgs = lucas.get("images", [])
        urls = lucas.get("image_urls", [])
        
        if not urls and not imgs:
            continue
        
        # Merge: originals first, then new ones
        seen = set()
        merged = []
        for u in (urls + imgs):
            if u and u not in seen:
                seen.add(u)
                merged.append(u)
        
        if merged != imgs or merged != urls:
            lucas["images"] = merged
            lucas["image_urls"] = merged
            steps["lucas_design"] = lucas
            supabase.table("pipelines").update({"steps": steps}).eq("id", p["id"]).execute()
            fixed_pipelines += 1
            
            # Sync to linked campaign
            c = _find_campaign_for_pipeline(campaigns, p["id"])
            if c:
                _update_campaign_stats(c, {"images": merged})
                fixed_campaigns += 1
    
    return {"fixed_pipelines": fixed_pipelines, "fixed_campaigns": fixed_campaigns, "total_pipelines": len(pipelines)}

@router.post("/{pipeline_id}/archive")
async def archive_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    """Archive/dismiss a pipeline so the user can create a new one"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("id, tenant_id, status").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    supabase.table("pipelines").update({"status": "archived"}).eq("id", pipeline_id).execute()
    return {"status": "archived", "pipeline_id": pipeline_id}





@router.post("/{pipeline_id}/publish")
async def publish_pipeline_campaign(pipeline_id: str, body: PublishRequest = PublishRequest(), user=Depends(get_current_user)):
    """Publish a campaign created from a completed pipeline"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    if pipeline.get("status") not in ("completed", "waiting_approval"):
        raise HTTPException(status_code=400, detail="Pipeline is not ready")

    steps = pipeline.get("steps") or {}
    approved_copy = body.edited_copy or steps.get("ana_review_copy", {}).get("approved_content", "")
    clean_copy = _clean_copy_text(approved_copy)
    lucas_step = steps.get("lucas_design", {})
    # Use 'images' (includes regenerated) with fallback to 'image_urls' (originals only)
    image_urls = lucas_step.get("images", []) or lucas_step.get("image_urls", [])
    platform_variants = lucas_step.get("platform_variants", {})
    video_url = steps.get("marcos_video", {}).get("video_url", "")
    schedule_text = steps.get("pedro_publish", {}).get("output", "")
    user_campaign_name = pipeline.get("result", {}).get("campaign_name", "")
    ctx = pipeline.get("result", {}).get("context", {})
    campaign_name = user_campaign_name or ctx.get("company", "") or pipeline.get("briefing", "")[:50]

    # Find existing campaign from this pipeline
    campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
    campaign_id = None
    c = _find_campaign_for_pipeline(campaigns, pipeline_id)
    if c:
        campaign_id = c["id"]

    camp_lang = pipeline.get("result", {}).get("campaign_language", "pt")
    campaign_data = {
        "name": campaign_name,
        "status": "created",
        "goal": "ai_pipeline",
        "metrics": {
            "type": "ai_pipeline",
            "target_segment": {"platforms": pipeline.get("platforms", [])},
            "messages": [{"step": 1, "channel": "multi", "content": clean_copy, "delay_hours": 0}],
            "schedule": {"pipeline_id": pipeline_id, "schedule_text": schedule_text},
            "stats": {
                "sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0,
                "images": [u for u in image_urls if u],
                "platform_variants": platform_variants,
                "video_url": video_url,
                "video_variants": steps.get("marcos_video", {}).get("video_variants", {}),
                "pipeline_id": pipeline_id,
                "campaign_language": camp_lang,
            },
        },
    }

    if campaign_id:
        supabase.table("campaigns").update({**campaign_data, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", campaign_id).execute()
    else:
        campaign_data["tenant_id"] = tenant["id"]
        insert_result = supabase.table("campaigns").insert(campaign_data).execute()
        campaign_id = insert_result.data[0]["id"]

    # Mark pipeline as completed/published
    supabase.table("pipelines").update({"status": "completed"}).eq("id", pipeline_id).execute()

    return {"status": "published", "campaign_id": campaign_id}





@router.post("/{pipeline_id}/regenerate-video")
async def regenerate_video(pipeline_id: str, user=Depends(get_current_user)):
    """Regenerate the commercial video for a completed pipeline and update its campaign"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    marcos = steps.get("marcos_video", {})
    marcos_output = marcos.get("output", "")
    if not marcos_output:
        raise HTTPException(status_code=400, detail="No video script found in pipeline")

    # Determine video format
    format_match = re.search(r'Format:\s*(horizontal|vertical)', marcos_output, re.IGNORECASE)
    video_format = format_match.group(1).lower() if format_match else "horizontal"
    FORMAT_MAP = {"vertical": "720x1280", "horizontal": "1280x720"}
    size = FORMAT_MAP.get(video_format, "1280x720")
    user_music = pipeline.get("result", {}).get("selected_music", "")

    # Mark as generating
    steps["marcos_video"]["status"] = "generating_video"
    steps["marcos_video"]["video_url"] = None
    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

    # Generate in background
    async def _regen():
        try:
            avatar_voice_regen = pipeline.get("result", {}).get("avatar_voice", None)
            video_mode = pipeline.get("result", {}).get("video_mode", "narration")
            avatar_url = pipeline.get("result", {}).get("avatar_url", "")

            if video_mode == "presenter" and avatar_url:
                video_url = await _generate_presenter_video(pipeline_id, marcos_output, avatar_url, size, user_music, voice_config=avatar_voice_regen)
            else:
                video_url = await _generate_commercial_video(pipeline_id, marcos_output, size, selected_music_override=user_music, voice_config=avatar_voice_regen)
            steps["marcos_video"]["video_url"] = video_url
            steps["marcos_video"]["status"] = "completed"
            supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

            # Auto-update associated campaign
            if video_url:
                # Create video variants for each platform
                video_variants = {}
                try:
                    platforms = pipeline.get("platforms", [])
                    video_variants = await _create_video_variants(pipeline_id, video_url, video_format, platforms)
                    steps["marcos_video"]["video_variants"] = video_variants
                    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()
                    logger.info(f"Regenerated video variants for {len(video_variants)} platforms")
                except Exception as vv_err:
                    logger.warning(f"Failed to create video variants during regen: {vv_err}")

                campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
                c = _find_campaign_for_pipeline(campaigns, pipeline_id)
                if c:
                    _update_campaign_stats(c, {"video_url": video_url, "video_variants": video_variants})
                    logger.info(f"Auto-updated campaign {c['id']} with video + {len(video_variants)} variants")
        except Exception as e:
            logger.error(f"Video regeneration failed: {e}")
            # Preserve existing video_url on failure — don't clear a successful video
            if not steps["marcos_video"].get("video_url"):
                steps["marcos_video"]["status"] = "completed"
                supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

    asyncio.create_task(_regen())
    return {"status": "generating", "pipeline_id": pipeline_id, "message": "Video regeneration started"}



# ── Campaign Editing Endpoints ──



@router.put("/{pipeline_id}/update-copy")
async def update_pipeline_copy(pipeline_id: str, data: UpdateCopyRequest, user=Depends(get_current_user)):
    """Update the copy text in a completed pipeline and sync to campaign"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    sofia = steps.get("sofia_copy", {})
    sofia["output"] = data.copy_text
    steps["sofia_copy"] = sofia
    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

    # Sync updated copy to the campaign messages
    campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
    c = _find_campaign_for_pipeline(campaigns, pipeline_id)
    if c:
        m = c.get("metrics") or {}
        # Parse variations and rebuild messages
        variations = re.split(r'===\s*VARIATION\s*\d+\s*===', data.copy_text, flags=re.IGNORECASE)
        variations = [v.strip() for v in variations if v.strip()]
        platforms = pipeline.get("platforms") or []
        new_messages = []
        for i, plat in enumerate(platforms):
            var_idx = i % max(len(variations), 1)
            text = _clean_copy_text(variations[var_idx] if variations else data.copy_text)
            new_messages.append({"channel": plat, "content": text, "delay_hours": 0})
        m["messages"] = new_messages
        supabase.table("campaigns").update({"metrics": m}).eq("id", c["id"]).execute()
        logger.info(f"Updated campaign {c['id']} copy from pipeline {pipeline_id}")

    return {"status": "updated", "pipeline_id": pipeline_id}




@router.post("/{pipeline_id}/regenerate-image")
async def regenerate_pipeline_image(pipeline_id: str, data: RegenerateImageRequest, user=Depends(get_current_user)):
    """Regenerate a specific image in the pipeline with optional feedback"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    lucas = steps.get("lucas_design", {})
    # Merge images from both fields
    imgs_field = lucas.get("images", [])
    urls_field = lucas.get("image_urls", [])
    seen = set()
    image_urls = []
    for u in (urls_field + imgs_field):
        if u and u not in seen:
            seen.add(u)
            image_urls.append(u)

    if data.image_index < 0 or data.image_index >= len(image_urls):
        raise HTTPException(status_code=400, detail=f"Invalid image index {data.image_index}. Available: 0-{len(image_urls)-1}")

    # Get pipeline context for image generation
    pipeline_result = pipeline.get("result") or {}
    campaign_language = pipeline_result.get("campaign_language", "en")
    lang_name = {"en": "English", "pt": "Portuguese (Português)", "es": "Spanish (Español)", "fr": "French (Français)", "de": "German", "it": "Italian", "ht": "Haitian Creole"}.get(campaign_language, "English")
    platforms = pipeline.get("platforms") or ["instagram"]

    # Build enhanced prompt with feedback
    sofia_output = steps.get("sofia_copy", {}).get("output", "")
    briefing = pipeline.get("briefing", "")

    lang_header = f"""⚠️ ABSOLUTE MANDATORY LANGUAGE RULE — OVERRIDES EVERYTHING BELOW:
ALL text, headlines, words, phrases visible in this image MUST be written EXCLUSIVELY in {lang_name}.
DO NOT use English or any other language. If any text would naturally be in English, TRANSLATE it to {lang_name}.
This is NON-NEGOTIABLE. Any text not in {lang_name} makes the image UNUSABLE.
"""

    base_prompt = f"""Create a professional marketing image for: {briefing[:300]}
Campaign copy context (use as reference for tone and language): {sofia_output[:200]}
Target platforms: {', '.join(platforms)}"""

    if data.feedback:
        base_prompt = f"""REGENERATION REQUEST — The previous image was NOT satisfactory.
USER FEEDBACK: {data.feedback}

Based on this feedback, create a NEW and IMPROVED image.
Original context: {briefing[:300]}
Campaign copy context (use as reference for tone and language): {sofia_output[:200]}
Target platforms: {', '.join(platforms)}"""

    enhanced_prompt = f"""{lang_header}
{base_prompt}

Technical: Ultra high-quality, 4K, professional color grading. Square 1080x1080.
NO logos, NO brand names, NO website URLs.
🚨 FINAL CHECK: Every single word visible in the generated image MUST be in {lang_name}. Zero exceptions."""

    async def _regen_image():
        try:
            logger.info(f"Regenerating image {data.image_index} for pipeline {pipeline_id}")
            new_url = await _generate_single_image(enhanced_prompt, pipeline_id, f"regen_{data.image_index}")
            if new_url:
                # Update main image
                image_urls[data.image_index] = new_url
                lucas["images"] = image_urls
                lucas["image_urls"] = image_urls  # legacy compat
                steps["lucas_design"] = lucas
                supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

                # Regenerate ALL platform variants using the updated image list
                try:
                    new_variants = await _create_platform_variants(pipeline_id, image_urls, platforms)
                    lucas["platform_variants"] = new_variants
                    steps["lucas_design"] = lucas
                    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()
                    logger.info(f"Platform variants regenerated for pipeline {pipeline_id}")
                except Exception as ve:
                    logger.warning(f"Platform variant regeneration failed (non-critical): {ve}")

                # Sync to campaign
                campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
                c = _find_campaign_for_pipeline(campaigns, pipeline_id)
                if c:
                    _update_campaign_stats(c, {"images": image_urls, "platform_variants": lucas.get("platform_variants", {})})
                    logger.info(f"Updated campaign images for pipeline {pipeline_id}")

                logger.info(f"Image {data.image_index} regenerated successfully: {new_url}")
            else:
                logger.error(f"Image regeneration returned None for pipeline {pipeline_id}")
        except Exception as e:
            logger.error(f"Image regeneration failed: {e}")

    asyncio.create_task(_regen_image())
    return {"status": "regenerating", "pipeline_id": pipeline_id, "image_index": data.image_index}




@router.post("/{pipeline_id}/clone-language")
async def clone_pipeline_language(pipeline_id: str, data: CloneLanguageRequest, user=Depends(get_current_user)):
    """Clone a completed pipeline into a different language, creating a new campaign"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    original = result.data[0]
    orig_result = original.get("result") or {}
    orig_name = orig_result.get("campaign_name", "Campaign")
    orig_lang = orig_result.get("campaign_language", "en")

    lang_labels = {"en": "English", "pt": "Portuguese", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "ja": "Japanese", "zh": "Chinese"}
    target_label = lang_labels.get(data.target_language, data.target_language.upper())

    if orig_lang == data.target_language:
        raise HTTPException(status_code=400, detail=f"Campaign is already in {target_label}")

    # Create new pipeline with same config but different language
    init_steps = {}
    for s in STEP_ORDER:
        init_steps[s] = {"status": "pending", "output": None, "started_at": None, "completed_at": None}

    new_name = f"{orig_name} ({target_label})"
    new_pipeline = {
        "tenant_id": tenant["id"],
        "briefing": original.get("briefing", ""),
        "mode": "auto",
        "platforms": original.get("platforms", []),
        "status": "running",
        "current_step": "sofia_copy",
        "steps": init_steps,
        "result": {
            "context": orig_result.get("context", {}),
            "contact_info": orig_result.get("contact_info", {}),
            "uploaded_assets": orig_result.get("uploaded_assets", []),
            "campaign_name": new_name,
            "campaign_language": data.target_language,
            "media_formats": orig_result.get("media_formats", {}),
            "selected_music": orig_result.get("selected_music", ""),
            "skip_video": orig_result.get("skip_video", False),
            "video_mode": orig_result.get("video_mode", "narration"),
            "avatar_url": orig_result.get("avatar_url", ""),
            "avatar_voice": orig_result.get("avatar_voice", None),
            "apply_brand": orig_result.get("apply_brand", False),
            "brand_data": orig_result.get("brand_data", None),
            "cloned_from": pipeline_id,
        },
    }

    new_result = supabase.table("pipelines").insert(new_pipeline).execute()
    new_pid = new_result.data[0]["id"]

    _start_step_bg(new_pid, "sofia_copy")
    logger.info(f"Cloned pipeline {pipeline_id} ({orig_lang}) -> {new_pid} ({data.target_language}) as '{new_name}'")

    return {
        "status": "running",
        "pipeline_id": new_pid,
        "campaign_name": new_name,
        "target_language": data.target_language,
        "cloned_from": pipeline_id,
    }


