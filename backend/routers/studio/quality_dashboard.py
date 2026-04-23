"""
StudioX — Quality Dashboard
Aggregate view across the tenant's projects: continuity scores, auto-fix runs,
total cost, avg production time. One endpoint for the home dashboard KPIs.
"""
from ._shared import *


@router.get("/quality-dashboard")
async def quality_dashboard(tenant=Depends(get_current_tenant)):
    """
    Returns tenant-wide quality KPIs:
      - total_projects, complete_projects
      - avg_continuity_score (video projects with audits)
      - green/yellow/red project counts
      - auto_fix_runs total + scenes_regenerated total
      - estimated_cost_usd (from agent_metrics)
      - hot issues (projects with score < 70 that need attention)
    """
    settings = _get_settings(tenant["id"])
    projects = settings.get("studio_projects") or []

    video_projects = [
        p for p in projects
        if not p.get("pdf_url")
        and not p.get("book_state", {}).get("pdf_url")
        and p.get("output_mode") != "book"
    ]
    book_projects = [
        p for p in projects
        if p.get("output_mode") == "book" or p.get("pdf_url") or p.get("book_state", {}).get("pdf_url")
    ]

    # Video continuity stats
    with_audit = [p for p in video_projects if (p.get("continuity_report") or {}).get("score") is not None]
    scores = [int((p.get("continuity_report") or {}).get("score", 0)) for p in with_audit]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    green = len([s for s in scores if s >= 85])
    yellow = len([s for s in scores if 70 <= s < 85])
    red = len([s for s in scores if s < 70])

    # Auto-fix stats
    auto_fixes = [p.get("continuity_auto_fix") for p in video_projects if p.get("continuity_auto_fix")]
    total_auto_fix_runs = len(auto_fixes)
    total_scenes_regenerated = sum(
        len((af or {}).get("regenerated_scenes") or [])
        for af in auto_fixes
    )

    # Cost from agent_metrics
    metrics = settings.get("agent_metrics") or {}
    total_cost = round(
        sum(float(m.get("estimated_cost_usd", 0.0)) for m in metrics.values()),
        4,
    )
    total_activations = sum(int(m.get("activations", 0)) for m in metrics.values())

    # Hot issues: score < 70
    hot_issues = []
    for p in sorted(with_audit, key=lambda x: int((x.get("continuity_report") or {}).get("score", 100))):
        score = int((p.get("continuity_report") or {}).get("score", 0))
        if score >= 70:
            break
        hot_issues.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "score": score,
            "issues_count": len((p.get("continuity_report") or {}).get("issues") or []),
            "auto_fix_status": (p.get("continuity_auto_fix") or {}).get("status"),
        })
        if len(hot_issues) >= 10:
            break

    # Book quality stats
    with_book_audit = [p for p in book_projects if (p.get("book_continuity_report") or {}).get("score") is not None]
    book_scores = [int((p.get("book_continuity_report") or {}).get("score", 0)) for p in with_book_audit]
    avg_book_score = round(sum(book_scores) / len(book_scores), 1) if book_scores else 0.0

    # Complete projects
    complete = [
        p for p in video_projects
        if any(o.get("label") == "complete" and o.get("type") == "video" for o in (p.get("outputs") or []))
    ]

    return {
        "videos": {
            "total": len(video_projects),
            "complete": len(complete),
            "audited": len(with_audit),
            "avg_continuity_score": avg_score,
            "green": green,
            "yellow": yellow,
            "red": red,
        },
        "books": {
            "total": len(book_projects),
            "audited": len(with_book_audit),
            "avg_quality_score": avg_book_score,
        },
        "auto_fix": {
            "runs": total_auto_fix_runs,
            "scenes_regenerated": total_scenes_regenerated,
        },
        "cost": {
            "total_usd": total_cost,
            "total_activations": total_activations,
        },
        "hot_issues": hot_issues,
    }
