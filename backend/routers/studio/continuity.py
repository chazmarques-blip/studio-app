"""Auto-generated module from studio.py split."""
from ._shared import *

# ══ CONTINUITY DIRECTOR ENDPOINTS ══

@router.post("/projects/{project_id}/continuity/analyze")
async def analyze_continuity_start(project_id: str, body: dict = Body(default={}), tenant=Depends(get_current_tenant)):
    """Start a background continuity analysis of the entire storyboard."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    panels = project.get("storyboard_panels", [])
    if not panels:
        raise HTTPException(status_code=400, detail="No storyboard panels to analyze")

    # Check if already running
    cs = project.get("continuity_status", {})
    if cs.get("phase") == "analyzing":
        return {"status": "already_running"}

    user_notes = body.get("user_notes", "")
    project["continuity_status"] = {"phase": "analyzing", "current": 0, "total": len(panels), "issues_found": 0}
    if user_notes:
        project["continuity_user_notes"] = user_notes
    _save_project(tenant["id"], settings, projects)

    def _bg_continuity_analyze():
        try:
            from core.continuity_director import analyze_continuity

            def progress_cb(current, total, batch_issues):
                try:
                    _s, _p, _proj = _get_project(tenant["id"], project_id)
                    if _proj:
                        _proj["continuity_status"] = {
                            "phase": "analyzing",
                            "current": current,
                            "total": total,
                            "issues_found": _proj.get("continuity_status", {}).get("issues_found", 0) + batch_issues,
                        }
                        _save_project(tenant["id"], _s, _p)
                except Exception:
                    pass

            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if not _proj:
                return

            report = analyze_continuity(
                project_id=project_id,
                panels=_proj.get("storyboard_panels", []),
                scenes=_proj.get("scenes", []),
                characters=_proj.get("characters", []),
                character_avatars=_proj.get("character_avatars", {}),
                user_notes=_proj.get("continuity_user_notes", ""),
                progress_callback=progress_cb,
            )

            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                _proj["continuity_report"] = report
                _proj["continuity_status"] = {
                    "phase": "done",
                    "total": report.get("total_scenes_analyzed", 0),
                    "current": report.get("total_scenes_analyzed", 0),
                    "issues_found": report.get("total_issues", 0),
                    "high": report.get("high_count", 0),
                    "medium": report.get("medium_count", 0),
                    "low": report.get("low_count", 0),
                }
                _save_project(tenant["id"], _s, _p, flush_now=True)
                logger.info(f"Continuity [{project_id}]: Analysis complete — {report.get('total_issues', 0)} issues")
        except Exception as e:
            logger.error(f"Continuity [{project_id}]: Analysis failed: {e}")
            try:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["continuity_status"] = {"phase": "error", "detail": str(e)[:200]}
                    _save_project(tenant["id"], _s, _p, flush_now=True)
            except Exception:
                pass

    thread = threading.Thread(target=_bg_continuity_analyze, daemon=True)
    thread.start()
    return {"status": "analyzing", "total_panels": len(panels)}


@router.get("/projects/{project_id}/continuity/status")
async def get_continuity_status(project_id: str, tenant=Depends(get_current_tenant)):
    """Poll continuity analysis/correction status."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "continuity_status": project.get("continuity_status", {}),
        "continuity_report": project.get("continuity_report", {}),
    }


@router.post("/projects/{project_id}/continuity/auto-correct")
async def auto_correct_continuity(project_id: str, tenant=Depends(get_current_tenant)):
    """Auto-correct all issues found by the continuity analysis (background task)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    report = project.get("continuity_report", {})
    issues = report.get("issues", [])
    if not issues:
        raise HTTPException(status_code=400, detail="No issues to correct. Run analysis first.")

    # Filter only high and medium severity issues for auto-correction
    correctable = [i for i in issues if i.get("severity") in ("high", "medium") and i.get("correction")]
    if not correctable:
        return {"status": "no_corrections_needed", "message": "No high/medium issues with corrections available"}

    cs = project.get("continuity_status", {})
    if cs.get("phase") == "correcting":
        return {"status": "already_running"}

    project["continuity_status"] = {
        "phase": "correcting",
        "current": 0,
        "total": len(correctable),
        "corrected": 0,
        "failed": 0,
    }
    _save_project(tenant["id"], settings, projects)

    def _bg_auto_correct():
        try:
            from core.continuity_director import auto_correct_issue
            corrected_count = 0
            failed_count = 0

            for idx, issue in enumerate(correctable):
                scene_num = issue.get("scene_number")
                correction = issue.get("correction", "")
                frame_index = issue.get("frame_index", 0)
                if not scene_num or not correction:
                    failed_count += 1
                    continue

                # Get the current project state for this panel
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if not _proj:
                    break

                panels = _proj.get("storyboard_panels", [])
                panel = next((p for p in panels if p.get("scene_number") == scene_num), None)
                if not panel:
                    failed_count += 1
                    continue

                # Use the specific frame_index from the issue
                frames = panel.get("frames", [])
                if frames and frame_index < len(frames):
                    source_url = frames[frame_index].get("image_url", panel.get("image_url"))
                else:
                    source_url = panel.get("image_url")

                if not source_url:
                    failed_count += 1
                    continue

                try:
                    result_bytes = auto_correct_issue(
                        image_url=source_url,
                        correction_instruction=correction,
                        project_id=project_id,
                        panel_number=scene_num,
                        frame_index=frame_index,
                    )

                    if result_bytes:
                        fname = f"storyboard/{project_id}/panel_{scene_num}_frame_{frame_index+1}_corrected.png"
                        new_url = _upload_to_storage(result_bytes, fname, "image/png")

                        # Update the specific frame
                        _s2, _p2, _proj2 = _get_project(tenant["id"], project_id)
                        if _proj2:
                            for p in _proj2.get("storyboard_panels", []):
                                if p.get("scene_number") == scene_num:
                                    p_frames = p.get("frames", [])
                                    if p_frames and frame_index < len(p_frames):
                                        p_frames[frame_index]["image_url"] = new_url
                                    if frame_index == 0 or not p_frames:
                                        p["image_url"] = new_url
                                    p["status"] = "done"
                                    p["last_edit"] = f"[Continuity Director] F{frame_index+1}: {correction[:80]}"
                                    p["generated_at"] = datetime.now(timezone.utc).isoformat()
                            _proj2["continuity_status"] = {
                                "phase": "correcting",
                                "current": idx + 1,
                                "total": len(correctable),
                                "corrected": corrected_count + 1,
                                "failed": failed_count,
                            }
                            _save_project(tenant["id"], _s2, _p2)
                        corrected_count += 1
                        logger.info(f"Continuity [{project_id}]: Corrected scene {scene_num} frame {frame_index} — {correction[:60]}")
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Continuity [{project_id}]: Correction failed scene {scene_num}: {e}")
                    failed_count += 1

            # Final status update
            _s, _p, _proj = _get_project(tenant["id"], project_id)
            if _proj:
                _proj["continuity_status"] = {
                    "phase": "corrected",
                    "current": len(correctable),
                    "total": len(correctable),
                    "corrected": corrected_count,
                    "failed": failed_count,
                }
                _save_project(tenant["id"], _s, _p, flush_now=True)
                logger.info(f"Continuity [{project_id}]: Auto-correct complete — {corrected_count} corrected, {failed_count} failed")
        except Exception as e:
            logger.error(f"Continuity [{project_id}]: Auto-correct failed: {e}")
            try:
                _s, _p, _proj = _get_project(tenant["id"], project_id)
                if _proj:
                    _proj["continuity_status"] = {"phase": "error", "detail": str(e)[:200]}
                    _save_project(tenant["id"], _s, _p, flush_now=True)
            except Exception:
                pass

    thread = threading.Thread(target=_bg_auto_correct, daemon=True)
    thread.start()
    return {"status": "correcting", "total_corrections": len(correctable)}



