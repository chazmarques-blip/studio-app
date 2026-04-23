"""
StudioX — Multi-Format Export
Reformats an existing final video into multiple aspect ratios for different
platforms (YouTube Shorts 9:16, Instagram Square 1:1, Instagram Feed 4:5, etc.)
using ffmpeg. Strategy: SCALE + BLURRED BACKDROP + CENTER CROP for top quality.

Endpoint: POST /api/studio/projects/{id}/export-format
Body: { "format": "9:16" | "1:1" | "4:5" | "16:9" }

Returns the URL of the reformatted video (persistent storage).
"""
from ._shared import *
from fastapi import BackgroundTasks
import os
import uuid
import subprocess
import tempfile

# Target resolutions per format (width × height)
_FORMAT_PRESETS = {
    "16:9": {"w": 1920, "h": 1080, "label": "YouTube/Landscape 16:9"},
    "9:16": {"w": 1080, "h": 1920, "label": "Reels/Shorts/TikTok 9:16"},
    "1:1": {"w": 1080, "h": 1080, "label": "Instagram Square 1:1"},
    "4:5": {"w": 1080, "h": 1350, "label": "Instagram Feed 4:5"},
}


def _reformat_video(source_path: str, target_path: str, w: int, h: int) -> bool:
    """
    Use ffmpeg to reformat:
      - If target aspect > source: letterbox with blurred backdrop (nice for Reels)
      - If target aspect < source: pillarbox with blurred backdrop
      - Both pad with blurred scaled copy of original (no black bars)
    """
    try:
        # Complex filter: create a blurred background + foreground centered
        filter_complex = (
            f"[0:v]split=2[bg][fg];"
            # Background: scale to fill target, crop overflow, blur heavily
            f"[bg]scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},gblur=sigma=30[bg_blur];"
            # Foreground: scale to fit inside target preserving aspect, no crop
            f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease[fg_scaled];"
            # Overlay foreground centered on blurred background
            f"[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2[out]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", source_path,
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "copy",
            target_path,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"reformat ffmpeg failed: {result.stderr.decode()[:500]}")
            return False
        return os.path.exists(target_path) and os.path.getsize(target_path) > 0
    except subprocess.TimeoutExpired:
        logger.error("reformat ffmpeg timeout after 5min")
        return False
    except Exception as e:
        logger.error(f"reformat error: {e}")
        return False


def _run_export_background(tenant_id: str, project_id: str, fmt: str, source_url: str):
    """Background task: download source, reformat, upload, save URL."""
    try:
        from .agents_activity import set_active_agent, clear_active_agent
        set_active_agent(tenant_id, project_id, "post_producer_agent", f"Exportando em {fmt}…")

        preset = _FORMAT_PRESETS[fmt]
        w, h = preset["w"], preset["h"]

        # Download source
        import requests as _rq
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "source.mp4")
            dst = os.path.join(td, f"export_{fmt.replace(':', 'x')}.mp4")

            r = _rq.get(source_url, stream=True, timeout=120)
            r.raise_for_status()
            with open(src, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

            logger.info(f"export-format [{project_id}] {fmt}: downloaded, reformatting to {w}x{h}")
            ok = _reformat_video(src, dst, w, h)
            if not ok:
                raise RuntimeError("ffmpeg reformat failed")

            with open(dst, "rb") as f:
                data = f.read()
            safe_fmt = fmt.replace(":", "x")
            filename = f"studio/exports/{project_id}_{safe_fmt}_{uuid.uuid4().hex[:6]}.mp4"
            public_url = _upload_to_storage(data, filename, "video/mp4")

            logger.info(f"export-format [{project_id}] {fmt}: uploaded to {public_url}")

            # Persist on project.exports[fmt]
            settings, projects, project = _get_project(tenant_id, project_id)
            if project:
                exports = project.get("exports") or {}
                exports[fmt] = {
                    "url": public_url,
                    "format": fmt,
                    "resolution": f"{w}x{h}",
                    "label": preset["label"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                project["exports"] = exports
                _save_project(tenant_id, settings, projects, flush_now=True)

        clear_active_agent(tenant_id, project_id)
    except Exception as e:
        logger.error(f"export-format [{project_id}] {fmt}: FAILED — {e}")
        try:
            settings, projects, project = _get_project(tenant_id, project_id)
            if project:
                exports = project.get("exports") or {}
                exports[fmt] = {"error": str(e)[:200], "failed_at": datetime.now(timezone.utc).isoformat()}
                project["exports"] = exports
                _save_project(tenant_id, settings, projects, flush_now=True)
        except Exception:
            pass
        try:
            from .agents_activity import clear_active_agent
            clear_active_agent(tenant_id, project_id)
        except Exception:
            pass


class ExportFormatRequest(BaseModel):
    format: str  # "9:16" | "1:1" | "4:5" | "16:9"


@router.post("/projects/{project_id}/export-format")
async def request_format_export(
    project_id: str,
    req: ExportFormatRequest,
    background_tasks: BackgroundTasks,
    tenant=Depends(get_current_tenant),
):
    """
    Request a reformatted export (9:16, 1:1, 4:5, etc.) of the project's final
    video. Runs in background — poll GET /projects/{id} for project.exports[fmt].
    """
    if req.format not in _FORMAT_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Valid: {list(_FORMAT_PRESETS.keys())}",
        )

    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the "complete" final video URL
    final_url = None
    for o in project.get("outputs") or []:
        if o.get("label") == "complete" and o.get("type") == "video":
            final_url = o.get("url")
            break
    if not final_url:
        # Fallback: first video output
        for o in project.get("outputs") or []:
            if o.get("type") == "video" and o.get("url"):
                final_url = o.get("url")
                break
    if not final_url:
        raise HTTPException(
            status_code=400,
            detail="Project has no final video to export. Generate the movie first.",
        )

    # Mark as processing
    exports = project.get("exports") or {}
    exports[req.format] = {
        "status": "processing",
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
    _update_project_field(tenant["id"], project_id, {"exports": exports}, flush_now=True)

    background_tasks.add_task(
        _run_export_background,
        tenant["id"],
        project_id,
        req.format,
        final_url,
    )

    return {
        "status": "processing",
        "format": req.format,
        "preset": _FORMAT_PRESETS[req.format],
        "message": f"Export to {req.format} started in background. Poll project.exports.{req.format} for URL.",
    }


@router.get("/projects/{project_id}/exports")
async def list_exports(project_id: str, tenant=Depends(get_current_tenant)):
    """Returns all reformatted exports for this project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "exports": project.get("exports") or {},
        "available_formats": _FORMAT_PRESETS,
    }
