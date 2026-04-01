"""
Director's Preview — Elite AI Director Agent
Reviews the entire script + dialogues with the standards of world-class directors
(Spielberg, Miyazaki, Pixar) before sending to storyboard production.
"""
from ._shared import *
import json

# Use the shared router from _shared.py (do NOT create a new router)


class DirectorReviewRequest(BaseModel):
    focus: str = "full"  # "full", "dialogues", "pacing", "emotion", "continuity"


async def _review_scene_batch(batch_scenes, characters, project_meta, lang, batch_num):
    """Review a batch of scenes in parallel (simulates multiple directors working together)."""
    import litellm
    
    LANG_MAP = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
    
    # Build script text for this batch only
    script_text = ""
    for s in batch_scenes:
        dubbed = s.get("dubbed_text", "").strip()
        narrated = s.get("narrated_text", "").strip() or s.get("narration", "").strip()
        dialogue = s.get("dialogue", "").strip()
        chars_in = s.get("characters_in_scene", [])
        
        script_text += f"\n═══ CENA {s.get('scene_number', '?')} — {s.get('title', 'Sem título')} ═══\n"
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
    
    system_prompt = f"""You are a LEGENDARY FILM DIRECTOR reviewing a BATCH of scenes from a larger project. You're part of a DIRECTOR'S TEAM — each director reviews a portion of scenes with the SAME high standards.

PROJECT: {project_meta.get('name', 'Untitled')}
BRIEFING: {project_meta.get('briefing', '')[:300]}
LANGUAGE: {LANG_MAP.get(lang, 'Portuguese')}
BATCH: {batch_num} (Scenes {batch_scenes[0].get('scene_number')} - {batch_scenes[-1].get('scene_number')})

CHARACTERS:
{char_desc}

YOUR REVIEW MUST COVER for EACH scene in this batch:

1. **DIALOGUE QUALITY** — Unique character voices, emotional depth, subtext
2. **NARRATIVE PACING** — Natural flow, proper tension/release
3. **EMOTIONAL IMPACT** — Goosebump moments, believable transitions
4. **VISUAL STORYTELLING** — Rich descriptions for storyboard artists
5. **CHARACTER CONSISTENCY** — True to established personalities
6. **MISSING ELEMENTS** — What would make this scene LEGENDARY?

SCORING STANDARDS:
- 90-100: EXCELLENT — World-class, ready for production
- 80-89: GOOD — Solid, minor polish needed
- 60-79: NEEDS_WORK — Significant improvements required
- <60: CRITICAL — Major revision needed

CRITICAL: Return ONLY valid JSON, no extra text before or after.

{{
  "batch_number": {batch_num},
  "scene_reviews": [
    {{
      "scene_number": int,
      "score": 0-100,
      "status": "EXCELLENT" or "GOOD" or "NEEDS_WORK" or "CRITICAL",
      "issues": ["issue 1", "issue 2"],
      "suggestions": ["suggestion 1"],
      "revised_dialogue": "Only if dialogue needs improvement",
      "revised_narration": "Only if narration needs improvement",
      "revised_description": "Only if scene description is too vague"
    }}
  ]
}}"""
    
    user_prompt = f"Review these {len(batch_scenes)} scenes. Return ONLY the JSON response:\n\n{script_text}"
    
    try:
        response = await litellm.acompletion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_key=api_key,
            max_tokens=6000,
            timeout=240,  # 4 minutes per batch (increased from 3min)
        )
        
        result = response.choices[0].message.content.strip()
        
        # Aggressive JSON extraction with better error handling
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
        
        # Find JSON object boundaries
        start_idx = result.find('{')
        end_idx = result.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            result = result[start_idx:end_idx]
        
        # Try to fix common JSON issues
        result = result.replace('\n', ' ')  # Remove newlines inside JSON
        result = result.replace('  ', ' ')  # Remove double spaces
        
        try:
            review_data = json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Batch {batch_num}: JSON parse error at char {e.pos}: {result[max(0,e.pos-50):e.pos+50]}")
            # Try to extract just the scene_reviews array
            if '"scene_reviews"' in result:
                try:
                    # Extract array manually
                    start = result.find('"scene_reviews"')
                    start = result.find('[', start)
                    end = result.rfind(']') + 1
                    array_str = result[start:end]
                    review_data = {"scene_reviews": json.loads(array_str)}
                except:
                    raise  # Give up if this also fails
            else:
                raise
        
        logger.info(f"Batch {batch_num}: Reviewed {len(review_data.get('scene_reviews', []))} scenes")
        return review_data.get("scene_reviews", [])
        
    except Exception as e:
        logger.error(f"Batch {batch_num} failed: {e}")
        # Return placeholder reviews for failed batch
        return [{
            "scene_number": s.get("scene_number"),
            "score": 50,
            "status": "NEEDS_WORK",
            "issues": [f"Review failed: {str(e)[:100]}"],
            "suggestions": ["Please re-run review"]
        } for s in batch_scenes]


async def _review_scene_batch_with_progress(batch_scenes, characters, project_meta, lang, batch_num, tenant_id, project_id, total_batches):
    """Same as _review_scene_batch but updates progress in real-time."""
    
    # Update progress: batch starting
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if project and project.get("director_progress"):
            progress = project["director_progress"]
            progress["current_batch"] = batch_num
            progress["status"] = f"reviewing_batch_{batch_num}"
            _update_project_field(tenant_id, project_id, {"director_progress": progress})
    except:
        pass  # Don't fail if progress update fails
    
    # Do the actual review
    result = await _review_scene_batch(batch_scenes, characters, project_meta, lang, batch_num)
    
    # Update progress: batch complete
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if project and project.get("director_progress"):
            progress = project["director_progress"]
            
            # Calculate average score of this batch
            batch_avg = sum(sr.get("score", 0) for sr in result) / len(result) if result else 0
            progress["batch_scores"].append({"batch": batch_num, "score": batch_avg})
            progress["scenes_processed"] += len(batch_scenes)
            
            # Calculate overall score so far
            all_scores = [bs["score"] for bs in progress["batch_scores"]]
            progress["current_score"] = sum(all_scores) / len(all_scores) if all_scores else 0
            
            _update_project_field(tenant_id, project_id, {"director_progress": progress})
    except:
        pass
    
    return result
    """Review a batch of scenes in parallel (simulates multiple directors working together)."""
    import litellm
    
    LANG_MAP = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
    
    # Build script text for this batch only
    script_text = ""
    for s in batch_scenes:
        dubbed = s.get("dubbed_text", "").strip()
        narrated = s.get("narrated_text", "").strip() or s.get("narration", "").strip()
        dialogue = s.get("dialogue", "").strip()
        chars_in = s.get("characters_in_scene", [])
        
        script_text += f"\n═══ CENA {s.get('scene_number', '?')} — {s.get('title', 'Sem título')} ═══\n"
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
    
    system_prompt = f"""You are a LEGENDARY FILM DIRECTOR reviewing a BATCH of scenes from a larger project. You're part of a DIRECTOR'S TEAM — each director reviews a portion of scenes with the SAME high standards.

PROJECT: {project_meta.get('name', 'Untitled')}
BRIEFING: {project_meta.get('briefing', '')[:300]}
LANGUAGE: {LANG_MAP.get(lang, 'Portuguese')}
BATCH: {batch_num} (Scenes {batch_scenes[0].get('scene_number')} - {batch_scenes[-1].get('scene_number')})

CHARACTERS:
{char_desc}

YOUR REVIEW MUST COVER for EACH scene in this batch:

1. **DIALOGUE QUALITY** — Unique character voices, emotional depth, subtext
2. **NARRATIVE PACING** — Natural flow, proper tension/release
3. **EMOTIONAL IMPACT** — Goosebump moments, believable transitions
4. **VISUAL STORYTELLING** — Rich descriptions for storyboard artists
5. **CHARACTER CONSISTENCY** — True to established personalities
6. **MISSING ELEMENTS** — What would make this scene LEGENDARY?

SCORING STANDARDS:
- 90-100: EXCELLENT — World-class, ready for production
- 80-89: GOOD — Solid, minor polish needed
- 60-79: NEEDS_WORK — Significant improvements required
- <60: CRITICAL — Major revision needed

RESPOND IN {LANG_MAP.get(lang, 'Portuguese')} with this JSON structure:
{{
  "batch_number": {batch_num},
  "scene_reviews": [
    {{
      "scene_number": int,
      "score": 0-100,
      "status": "EXCELLENT" or "GOOD" or "NEEDS_WORK" or "CRITICAL",
      "issues": ["issue 1", "issue 2"],
      "suggestions": ["suggestion 1"],
      "revised_dialogue": "Only if dialogue needs improvement — provide the improved version",
      "revised_narration": "Only if narration needs improvement",
      "revised_description": "Only if scene description is too vague for storyboard"
    }}
  ]
}}"""
    
    user_prompt = f"Review these {len(batch_scenes)} scenes with your highest professional standards:\n\n{script_text}"
    
    try:
        response = await litellm.acompletion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_key=api_key,
            max_tokens=6000,
            timeout=120,  # 2 minutes per batch (much faster than reviewing all at once)
        )
        
        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        review_data = json.loads(result.strip())
        logger.info(f"Batch {batch_num}: Reviewed {len(review_data.get('scene_reviews', []))} scenes")
        return review_data.get("scene_reviews", [])
        
    except Exception as e:
        logger.error(f"Batch {batch_num} failed: {e}")
        # Return placeholder reviews for failed batch
        return [{
            "scene_number": s.get("scene_number"),
            "score": 50,
            "status": "NEEDS_WORK",
            "issues": [f"Review failed: {str(e)[:100]}"],
            "suggestions": ["Please re-run review"]
        } for s in batch_scenes]


@router.post("/projects/{project_id}/director/review")
async def director_review(project_id: str, req: DirectorReviewRequest, tenant=Depends(get_current_tenant)):
    """The Director Agent reviews the entire project with elite professional standards.
    Uses PARALLEL BATCHING for faster reviews of large projects."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = project.get("scenes", [])
    characters = project.get("characters", [])
    if not scenes:
        raise HTTPException(status_code=400, detail="No scenes to review")

    lang = project.get("language", "pt")
    LANG_MAP = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    
    # ═══ PARALLEL BATCHING STRATEGY ═══
    # Divide scenes into batches of 6-8 scenes each
    # Process batches in parallel (simulates team of directors)
    BATCH_SIZE = 7
    batches = []
    for i in range(0, len(scenes), BATCH_SIZE):
        batches.append(scenes[i:i + BATCH_SIZE])
    
    logger.info(f"Director review: {len(scenes)} scenes → {len(batches)} batches (size={BATCH_SIZE})")
    
    # Process all batches in parallel
    import asyncio
    project_meta = {
        "name": project.get("name", "Untitled"),
        "briefing": project.get("briefing", "")
    }
    
    # Initialize progress tracking
    _update_project_field(tenant["id"], project_id, {
        "director_progress": {
            "status": "reviewing",
            "current_batch": 0,
            "total_batches": len(batches),
            "current_score": 0,
            "scenes_processed": 0,
            "total_scenes": len(scenes),
            "batch_scores": []
        }
    })
    
    batch_tasks = [
        _review_scene_batch_with_progress(batch, characters, project_meta, lang, batch_num + 1, tenant["id"], project_id, len(batches))
        for batch_num, batch in enumerate(batches)
    ]
    
    try:
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Parallel batching failed: {e}")
        raise HTTPException(500, f"Director review failed: {str(e)}")
    finally:
        # Clear progress after completion
        _update_project_field(tenant["id"], project_id, {"director_progress": None})
    
    # Merge all scene reviews from batches
    all_scene_reviews = []
    for result in batch_results:
        if isinstance(result, Exception):
            logger.error(f"Batch failed: {result}")
            continue
        if isinstance(result, list):
            all_scene_reviews.extend(result)
    
    # Calculate overall metrics
    avg_score = sum(sr.get("score", 0) for sr in all_scene_reviews) / len(all_scene_reviews) if all_scene_reviews else 0
    needs_work_count = len([sr for sr in all_scene_reviews if sr.get("score", 0) < 80])
    
    # Overall verdict based on new 90% standard
    verdict = "APPROVED" if avg_score >= 90 and needs_work_count == 0 else "NEEDS_REVISION"
    
    director_notes = f"""Revisão paralela concluída por equipe de diretores.

📊 SCORE GERAL: {avg_score:.0f}/100
{'✅ APROVADO — Qualidade cinematográfica excepcional!' if verdict == 'APPROVED' else f'⚠️ REVISÃO NECESSÁRIA — {needs_work_count} cena(s) abaixo de 80%'}

PADRÃO DE QUALIDADE:
- 90-100: EXCELENTE (pronto para produção)
- 80-89: BOM (pequenos ajustes recomendados)  
- <80: PRECISA MELHORAR (correções necessárias)

{f'Cenas que precisam de atenção: {", ".join([str(sr.get("scene_number")) for sr in all_scene_reviews if sr.get("score", 0) < 80])}' if needs_work_count > 0 else 'Todas as cenas atingiram o padrão de qualidade!'}"""
    
    # Identify strengths and improvements
    excellent_scenes = [sr for sr in all_scene_reviews if sr.get("score", 0) >= 90]
    weak_scenes = [sr for sr in all_scene_reviews if sr.get("score", 0) < 70]
    
    top_strengths = []
    if excellent_scenes:
        top_strengths.append(f"{len(excellent_scenes)} cenas com qualidade EXCELENTE (90+)")
    top_strengths.append("Revisão paralela permitiu análise mais rápida e detalhada")
    
    top_improvements = []
    if needs_work_count > 0:
        top_improvements.append(f"{needs_work_count} cenas precisam atingir pelo menos 80%")
    if weak_scenes:
        top_improvements.append(f"{len(weak_scenes)} cenas críticas (<70%) requerem atenção imediata")
    
    review_result = {
        "overall_score": round(avg_score),
        "verdict": verdict,
        "director_notes": director_notes,
        "scene_reviews": all_scene_reviews,
        "pacing_notes": f"Projeto com {len(scenes)} cenas revisadas em {len(batches)} lotes paralelos",
        "emotional_arc": f"Score médio: {avg_score:.0f}% — {'Pronto para storyboard' if verdict == 'APPROVED' else 'Aplicar correções e re-avaliar'}",
        "top_3_strengths": top_strengths[:3] if top_strengths else ["Review completed"],
        "top_3_improvements": top_improvements[:3] if top_improvements else ["Nenhuma melhoria crítica necessária"],
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "review_method": "parallel_batch",
        "batch_count": len(batches),
        "batch_size": BATCH_SIZE
    }
    
    # Save review to project
    _update_project_field(tenant["id"], project_id, {
        "director_review": review_result,
        "director_review_at": review_result["reviewed_at"]
    })
    
    logger.info(f"Director review complete: {avg_score:.0f}% avg, {needs_work_count} scenes need work")
    
    return review_result


# Removed old single-threaded review code - now using parallel batching




@router.post("/projects/{project_id}/director/apply-fixes")
async def director_apply_fixes(project_id: str, payload: dict = Body(None), tenant=Depends(get_current_tenant)):
    """Apply the director's suggested revisions to scenes (dialogue, narration, description).
    OPTIONAL: Set {"re_evaluate": true} to automatically re-run director review after applying fixes."""
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

    # Optional: Re-evaluate after applying fixes
    re_evaluate = payload.get("re_evaluate", False) if payload else False
    new_review = None
    
    if re_evaluate and applied > 0:
        logger.info(f"Studio [{project_id}]: Re-evaluating after fixes...")
        
        # Save progress state for real-time updates
        _update_project_field(tenant["id"], project_id, {
            "director_progress": {
                "status": "re_evaluating",
                "current_batch": 0,
                "total_batches": 0,
                "current_score": 0,
                "scenes_processed": 0,
                "total_scenes": len(scenes)
            }
        })
        
        try:
            # Call the director review endpoint internally
            from fastapi import Request
            req_obj = DirectorReviewRequest(focus="full")
            new_review = await director_review(project_id, req_obj, tenant)
            logger.info(f"Studio [{project_id}]: Re-evaluation complete, new score: {new_review.get('overall_score')}")
        except Exception as e:
            logger.error(f"Re-evaluation failed: {e}")
            # Don't fail the whole request if re-eval fails
            new_review = {"error": str(e)}
        finally:
            # Clear progress state
            _update_project_field(tenant["id"], project_id, {
                "director_progress": None
            })

    return {
        "applied": applied,
        "total_reviewed": len(scene_reviews),
        "re_evaluated": re_evaluate,
        "new_review": new_review if re_evaluate else None
    }


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



@router.get("/projects/{project_id}/director/progress")
async def get_director_progress(project_id: str, tenant=Depends(get_current_tenant)):
    """Get real-time progress of director review or re-evaluation."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    progress = project.get("director_progress")
    if not progress:
        return {"in_progress": False}
    
    return {
        "in_progress": True,
        "progress": progress
    }
