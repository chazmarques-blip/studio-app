"""
Director's Preview — Elite AI Director Agent
Reviews the entire script + dialogues with the standards of world-class directors
(Spielberg, Miyazaki, Pixar) before sending to storyboard production.
"""
from ._shared import *

# Use the shared router from _shared.py (do NOT create a new router)


class DirectorReviewRequest(BaseModel):
    focus: str = "full"  # "full", "dialogues", "pacing", "emotion", "continuity"


@router.post("/projects/{project_id}/director/review")
async def director_review(project_id: str, req: DirectorReviewRequest, tenant=Depends(get_current_tenant)):
    """The Director Agent reviews the entire project with elite professional standards."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    characters = project.get("characters", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to review")

    lang = project.get("language", "pt")
    LANG_MAP = {"pt": "Portuguese", "en": "English", "es": "Spanish"}

    # Build the full script for the director to review
    script_text = ""
    for i, s in enumerate(scenes):
        dubbed = s.get("dubbed_text", "").strip()
        narrated = s.get("narrated_text", "").strip() or s.get("narration", "").strip()
        dialogue = s.get("dialogue", "").strip()
        chars_in = s.get("characters_in_scene", [])

        script_text += f"\n═══ CENA {s.get('scene_number', i+1)} — {s.get('title', 'Sem título')} ═══\n"
        script_text += f"Tempo: {s.get('time_start', '?')} - {s.get('time_end', '?')}\n"
        script_text += f"Emoção: {s.get('emotion', '?')}\n"
        script_text += f"Câmara: {s.get('camera', '?')}\n"
        script_text += f"Personagens: {', '.join(chars_in) if chars_in else 'Não definido'}\n"
        script_text += f"Descrição: {s.get('description', '?')}\n"
        if dubbed:
            script_text += f"DIÁLOGO DUBLADO:\n{dubbed}\n"
        elif dialogue:
            script_text += f"DIÁLOGO ORIGINAL:\n{dialogue}\n"
        if narrated:
            script_text += f"NARRAÇÃO:\n{narrated}\n"
        script_text += "\n"

    char_desc = "\n".join([
        f"- {c.get('name', '?')}: {c.get('description', '?')} | Papel: {c.get('role', '?')}"
        for c in characters
    ])

    system_prompt = f"""You are a LEGENDARY FILM DIRECTOR — your work has won every major award. You combine the visual storytelling of Spielberg, the emotional depth of Miyazaki, the narrative perfection of Pixar, and the dramatic intensity of Nolan.

You are reviewing a project BEFORE it goes to storyboard production. Your job is to ensure EVERY scene is PERFECT. Nothing mediocre passes your review.

PROJECT: {project.get('name', 'Untitled')}
BRIEFING: {project.get('briefing', '')[:500]}
LANGUAGE: {LANG_MAP.get(lang, 'Portuguese')}
TOTAL SCENES: {len(scenes)}

CHARACTERS:
{char_desc}

YOUR REVIEW MUST COVER:

1. **DIALOGUE QUALITY** (Each character must have a UNIQUE voice — not just different words, but different PERSONALITY in how they speak)
   - Are the dialogues emotionally rich and character-specific?
   - Does each character speak in a way that reflects their personality?
   - Are there enough pauses, reactions, and emotional beats?
   - Is there subtext (what characters mean vs what they say)?

2. **NARRATIVE PACING** (The story must breathe — tension, release, climax, resolution)
   - Does the story flow naturally from scene to scene?
   - Are there moments of rest after intense scenes?
   - Is the climax properly built up?
   - Are transitions smooth?

3. **EMOTIONAL ARC** (The audience must FEEL something at every moment)
   - Does each scene have a clear emotional purpose?
   - Are emotional transitions believable?
   - Are there "goosebump moments"?
   - Is the ending emotionally satisfying?

4. **VISUAL STORYTELLING** (Every scene must paint a picture BEFORE the storyboard draws it)
   - Are scene descriptions rich enough for the storyboard artist?
   - Are camera angles appropriate for the emotional moment?
   - Are character positions and actions clear?
   - Will the storyboard know exactly what to draw?

5. **CHARACTER CONSISTENCY** (Characters must behave consistently with who they are)
   - Does each character stay true to their established personality?
   - Are character relationships developing naturally?
   - Are there any out-of-character moments?

6. **MISSING ELEMENTS** (What's missing that a great film would have?)
   - Missing emotional beats
   - Missing character reactions
   - Scenes that need more dialogue or narration
   - Scenes where the description is too vague for storyboard

RESPOND IN {LANG_MAP.get(lang, 'Portuguese')} with this JSON structure:
{{
  "overall_score": 0-100,
  "verdict": "APPROVED" or "NEEDS_REVISION",
  "director_notes": "Your overall artistic assessment (2-3 paragraphs, passionate, detailed)",
  "scene_reviews": [
    {{
      "scene_number": 1,
      "score": 0-100,
      "status": "EXCELLENT" or "GOOD" or "NEEDS_WORK" or "CRITICAL",
      "issues": ["issue 1", "issue 2"],
      "suggestions": ["suggestion 1"],
      "revised_dialogue": "Only if dialogue needs improvement — provide the improved version",
      "revised_narration": "Only if narration needs improvement",
      "revised_description": "Only if scene description is too vague for storyboard"
    }}
  ],
  "pacing_notes": "Assessment of overall story pacing",
  "emotional_arc": "Assessment of emotional journey",
  "top_3_strengths": ["strength 1", "strength 2", "strength 3"],
  "top_3_improvements": ["improvement 1", "improvement 2", "improvement 3"]
}}"""

    user_prompt = f"Review this project with your highest professional standards:\n\n{script_text}"

    try:
        import litellm
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
        
        logger.info(f"Director review started for {len(scenes)} scenes")
        
        response = await litellm.acompletion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_key=api_key,
            max_tokens=8000,
            timeout=360,  # Increased timeout for large projects (6 minutes = 360s)
        )
        
        result = response.choices[0].message.content.strip()
        logger.info(f"Director review response received: {len(result)} chars")
        
        review = _parse_json(result)

        if not review:
            # Try to extract JSON
            if '{' in result:
                import json as json_mod
                start = result.index('{')
                end = result.rindex('}') + 1
                review = json_mod.loads(result[start:end])

        if not review:
            raise HTTPException(status_code=500, detail="Failed to parse director review")

        # Save the review to the project
        _update_project_field(tenant["id"], project_id, {
            "director_review": review,
            "director_review_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"Studio [{project_id}]: Director Review — Score: {review.get('overall_score', '?')}/100, Verdict: {review.get('verdict', '?')}")

        return review

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Studio [{project_id}]: Director Review failed: {e}")
        raise HTTPException(status_code=500, detail=f"Director review failed: {str(e)[:200]}")


@router.post("/projects/{project_id}/director/apply-fixes")
async def director_apply_fixes(project_id: str, tenant=Depends(get_current_tenant)):
    """Apply the director's suggested revisions to scenes (dialogue, narration, description)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    review = project.get("director_review", {})
    scene_reviews = review.get("scene_reviews", [])
    if not scene_reviews:
        raise HTTPException(status_code=400, detail="No director review found. Run review first.")

    scenes = project.get("scenes", [])
    applied = 0

    for sr in scene_reviews:
        snum = sr.get("scene_number")
        if not snum:
            continue
        scene_idx = next((i for i, s in enumerate(scenes) if s.get("scene_number") == snum), None)
        if scene_idx is None:
            continue

        updated = False
        if sr.get("revised_dialogue") and sr["revised_dialogue"].strip():
            scenes[scene_idx]["dubbed_text"] = sr["revised_dialogue"]
            updated = True
        if sr.get("revised_narration") and sr["revised_narration"].strip():
            scenes[scene_idx]["narrated_text"] = sr["revised_narration"]
            updated = True
        if sr.get("revised_description") and sr["revised_description"].strip():
            scenes[scene_idx]["description"] = sr["revised_description"]
            updated = True

        if updated:
            applied += 1

    if applied > 0:
        _update_project_field(tenant["id"], project_id, {"scenes": scenes})

    logger.info(f"Studio [{project_id}]: Director fixes applied to {applied}/{len(scene_reviews)} scenes")

    return {"applied": applied, "total_reviewed": len(scene_reviews)}


@router.get("/projects/{project_id}/director/review")
async def get_director_review(project_id: str, tenant=Depends(get_current_tenant)):
    """Get the last director review for a project."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    review = project.get("director_review")
    if not review:
        return {"has_review": False}

    return {
        "has_review": True,
        "review": review,
        "reviewed_at": project.get("director_review_at"),
    }
