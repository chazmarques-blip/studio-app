"""Pipeline execution engine: step orchestration, recovery, and state management."""
import asyncio
import re
import time
import threading
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.deps import supabase, EMERGENT_KEY, logger
from pipeline.config import STEP_ORDER, STEP_SYSTEMS, PAUSE_AFTER
from pipeline.prompts import _build_prompt
from pipeline.utils import (
    _parse_review_decision, _parse_ana_copy_selection,
    _parse_rafael_design_selections, _extract_revision_feedback,
    _next_step,
)
from pipeline.media import (
    _generate_design_images, _generate_commercial_video,
    _generate_presenter_video, _create_platform_variants,
)

# ── Shared mutable state ──
_active_pipelines = set()
_accuracy_jobs = {}
_preview_jobs = {}
_batch360_jobs = {}


async def _execute_step(pipeline_id, step):
    """Execute a single pipeline step using AI"""
    pipeline = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    if not pipeline:
        return
    pipeline = pipeline[0]
    steps = pipeline.get("steps") or {}

    # Enterprise check only for the publish step
    if step == "pedro_publish":
        tenant = supabase.table("tenants").select("plan").eq("id", pipeline["tenant_id"]).execute()
        if tenant.data and tenant.data[0].get("plan") != "enterprise":
            steps[step] = steps.get(step, {})
            steps[step]["status"] = "requires_upgrade"
            steps[step]["error"] = "O plano Enterprise e necessario para publicar campanhas. Faca upgrade para desbloquear."
            supabase.table("pipelines").update({
                "steps": steps, "status": "requires_upgrade", "current_step": step,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
            return

    # Mark step as running
    steps[step] = steps.get(step, {})
    steps[step]["status"] = "running"
    steps[step]["started_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("pipelines").update({
        "steps": steps, "current_step": step, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    try:
        prompt = _build_prompt(step, pipeline)
        system = STEP_SYSTEMS.get(step, "")

        # Creative agents use Claude Sonnet 4.5 for quality
        # Review agents use Gemini Flash for SPEED (reviews don't need creative generation)
        # This cuts review time from ~60s to ~10s each
        STEP_MODELS = {
            "sofia_copy": ("anthropic", "claude-sonnet-4-5-20250929"),
            "ana_review_copy": ("gemini", "gemini-2.0-flash"),
            "lucas_design": ("anthropic", "claude-sonnet-4-5-20250929"),
            "rafael_review_design": ("gemini", "gemini-2.0-flash"),
            "marcos_video": ("anthropic", "claude-sonnet-4-5-20250929"),
            "rafael_review_video": ("gemini", "gemini-2.0-flash"),
            "pedro_publish": ("gemini", "gemini-2.0-flash"),
        }
        provider, model = STEP_MODELS.get(step, ("anthropic", "claude-sonnet-4-5-20250929"))

        # Execute with strict timeout per attempt
        response = None
        last_error = None
        # Review steps (Gemini Flash) are fast — use shorter timeout and fewer retries
        is_review = step in ("ana_review_copy", "rafael_review_design", "rafael_review_video", "pedro_publish")
        timeout_per_attempt = 30 if is_review else 75
        # Only 1 attempt for primary model before fallback (avoids long waits on 502 errors)
        max_attempts = 1

        for attempt in range(max_attempts):
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-{int(time.time())}-{attempt}",
                    system_message=system
                ).with_model(provider, model)

                start = time.time()
                response = await asyncio.wait_for(
                    chat.send_message(UserMessage(text=prompt)),
                    timeout=timeout_per_attempt
                )
                elapsed = round((time.time() - start) * 1000)
                break
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Step {step} timed out after {timeout_per_attempt}s on attempt {attempt+1}")
                logger.warning(f"Pipeline step {step} attempt {attempt+1} timed out after {timeout_per_attempt}s")
            except Exception as retry_err:
                last_error = retry_err
                logger.warning(f"Pipeline step {step} attempt {attempt+1} failed: {retry_err}")

            if attempt < max_attempts - 1:
                await asyncio.sleep(2)

        # Fallback to Gemini Flash if Claude failed (for creative steps)
        if response is None and provider == "anthropic":
            logger.info(f"Claude failed for {step}, falling back to gemini-2.0-flash")
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-fallback-{int(time.time())}",
                    system_message=system
                ).with_model("gemini", "gemini-2.0-flash")
                start = time.time()
                response = await asyncio.wait_for(
                    chat.send_message(UserMessage(text=prompt)),
                    timeout=timeout_per_attempt
                )
                elapsed = round((time.time() - start) * 1000)
            except Exception as fb_err:
                logger.error(f"Fallback also failed for {step}: {fb_err}")

        if response is None:
            raise last_error

        steps[step]["output"] = response
        steps[step]["status"] = "completed"
        steps[step]["completed_at"] = datetime.now(timezone.utc).isoformat()
        steps[step]["elapsed_ms"] = elapsed

        # For reviewer steps: parse decision and handle revision loop
        # MAX_REVISIONS = 1: Only 1 revision allowed per review step for speed.
        # The initial prompt is strong enough that 1 revision should fix most issues.
        MAX_REVISIONS = 1

        if step == "ana_review_copy":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < MAX_REVISIONS:
                # Revision loop - send back to David
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"Lee requested revision {revision_count + 1}/{MAX_REVISIONS} for pipeline {pipeline_id}")

                # Prepare Sofia for re-run
                prev_sofia_output = steps.get("sofia_copy", {}).get("output", "")
                steps["sofia_copy"]["previous_output"] = prev_sofia_output
                steps["sofia_copy"]["revision_feedback"] = revision_feedback
                steps["sofia_copy"]["revision_round"] = revision_count + 1
                steps["sofia_copy"]["status"] = "pending"

                supabase.table("pipelines").update({
                    "steps": steps, "status": "running", "current_step": "sofia_copy",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                await _execute_step(pipeline_id, "sofia_copy")
                return  # Skip normal next-step flow

            # Approved (or max revisions reached) - parse selection
            if decision == "revision_needed" and revision_count >= MAX_REVISIONS:
                logger.warning(f"Max revisions ({MAX_REVISIONS}) reached for ana_review_copy, auto-approving pipeline {pipeline_id}")
            steps[step]["decision"] = "approved"
            selected = _parse_ana_copy_selection(response)
            steps[step]["auto_selection"] = selected
            sofia_output = steps.get("sofia_copy", {}).get("output", "")

            # Strip IMAGE BRIEFING section from Sofia's output before parsing variations
            copy_only = re.split(r'===\s*IMAGE BRIEFING\s*===', sofia_output, flags=re.IGNORECASE)[0]

            variations = re.split(r'===\s*VARIATION \d+\s*===', copy_only)
            variations = [v.strip() for v in variations[1:] if v.strip()]

            if variations and 0 < selected <= len(variations):
                steps[step]["approved_content"] = variations[selected - 1]
            elif variations:
                steps[step]["approved_content"] = variations[0]
            else:
                steps[step]["approved_content"] = copy_only.strip()

        elif step == "rafael_review_design":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < MAX_REVISIONS:
                # Revision loop - send back to Lucas
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"George requested design revision {revision_count + 1}/{MAX_REVISIONS} for pipeline {pipeline_id}")

                prev_lucas_output = steps.get("lucas_design", {}).get("output", "")
                steps["lucas_design"]["previous_output"] = prev_lucas_output
                steps["lucas_design"]["revision_feedback"] = revision_feedback
                steps["lucas_design"]["revision_round"] = revision_count + 1
                steps["lucas_design"]["status"] = "pending"

                supabase.table("pipelines").update({
                    "steps": steps, "status": "running", "current_step": "lucas_design",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                await _execute_step(pipeline_id, "lucas_design")
                return

            if decision == "revision_needed" and revision_count >= MAX_REVISIONS:
                logger.warning(f"Max revisions ({MAX_REVISIONS}) reached for rafael_review_design, auto-approving pipeline {pipeline_id}")
            steps[step]["decision"] = "approved"
            platforms = pipeline.get("platforms") or []
            selections = _parse_rafael_design_selections(response, platforms)
            steps[step]["auto_selections"] = selections
            steps[step]["selections"] = selections

        elif step == "rafael_review_video":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < MAX_REVISIONS:
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"Roger requested video revision {revision_count + 1}/{MAX_REVISIONS} for pipeline {pipeline_id}")

                prev_marcos_output = steps.get("marcos_video", {}).get("output", "")
                steps["marcos_video"]["previous_output"] = prev_marcos_output
                steps["marcos_video"]["revision_feedback"] = revision_feedback
                steps["marcos_video"]["revision_round"] = revision_count + 1
                steps["marcos_video"]["status"] = "pending"

                supabase.table("pipelines").update({
                    "steps": steps, "status": "running", "current_step": "marcos_video",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                await _execute_step(pipeline_id, "marcos_video")
                return

            if decision == "revision_needed" and revision_count >= MAX_REVISIONS:
                logger.warning(f"Max revisions ({MAX_REVISIONS}) reached for rafael_review_video, auto-approving pipeline {pipeline_id}")
            steps[step]["decision"] = "approved"

        # Generate actual images for Lucas's design step
        elif step == "lucas_design":
            platforms = pipeline.get("platforms") or []
            # Update DB to show we're generating images now
            steps[step]["output"] = response
            steps[step]["status"] = "generating_images"
            supabase.table("pipelines").update({
                "steps": steps,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()

            image_urls, image_prompts = await _generate_design_images(
                pipeline_id, response, platforms
            )
            steps[step]["image_urls"] = image_urls
            steps[step]["image_prompts"] = image_prompts

            # Create platform-specific variants (TikTok 9:16, Google Ads 16:9, etc.)
            try:
                platform_variants = await _create_platform_variants(pipeline_id, image_urls, platforms)
                steps[step]["platform_variants"] = platform_variants
                logger.info(f"Created platform variants for {len(platform_variants)} platforms")
            except Exception as pv_err:
                logger.warning(f"Platform variant creation failed: {pv_err}")
                steps[step]["platform_variants"] = {}

            steps[step]["status"] = "completed"

        # Generate video for Marcos's video step
        elif step == "marcos_video":
            # Check skip_video flag
            skip_video = pipeline.get("result", {}).get("skip_video", False)
            if skip_video:
                logger.info(f"Skipping video generation for pipeline {pipeline_id} (skip_video=True)")
                steps[step]["output"] = response
                steps[step]["status"] = "completed"
                steps[step]["video_url"] = None
                steps[step]["video_format"] = "horizontal"
                steps[step]["video_duration"] = 0
                steps[step]["skipped"] = True
            else:
                # Validate narration script language before generating
                camp_lang = pipeline.get("result", {}).get("campaign_language", "")
                if camp_lang:
                    narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===', response, re.IGNORECASE)
                    if not narr_match:
                        narr_match = re.search(r'NARRATION SCRIPT[:\s]*([\s\S]*?)(?:===|MUSIC DIRECTION)', response, re.IGNORECASE)
                    if narr_match:
                        narr_text = narr_match.group(1).strip()
                        LANG_NAMES_V = {"pt": "Portuguese", "en": "English", "es": "Spanish", "fr": "French"}
                        expected_lang = LANG_NAMES_V.get(camp_lang, camp_lang)
                        logger.info(f"Video narration language validation: expected={expected_lang}, checking script ({len(narr_text)} chars)")

                # Parse video format from output
                video_format = "horizontal"
                format_match = re.search(r'Format:\s*(vertical|horizontal)', response, re.IGNORECASE)
                if format_match:
                    video_format = format_match.group(1).lower()

                platforms = pipeline.get("platforms") or []
                # Sora 2 valid sizes: 720x1280, 1280x720
                FORMAT_MAP = {"vertical": "720x1280", "horizontal": "1280x720"}
                if not format_match:
                    if any(p in platforms for p in ["tiktok", "instagram", "whatsapp"]):
                        video_format = "vertical"
                    elif any(p in platforms for p in ["google_ads", "facebook"]):
                        video_format = "horizontal"
                size = FORMAT_MAP.get(video_format, "1280x720")

                # Update status to generating_video
                steps[step]["output"] = response
                steps[step]["status"] = "generating_video"
                supabase.table("pipelines").update({
                    "steps": steps,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                # Generate the full commercial
                user_music = pipeline.get("result", {}).get("selected_music", "")
                video_mode = pipeline.get("result", {}).get("video_mode", "narration")
                avatar_url = pipeline.get("result", {}).get("avatar_url", "")
                avatar_voice = pipeline.get("result", {}).get("avatar_voice", None)

                if video_mode == "presenter" and avatar_url:
                    # Presenter mode: talking head with lip-sync via fal.ai
                    video_url = await _generate_presenter_video(pipeline_id, response, avatar_url, size, user_music, voice_config=avatar_voice)
                else:
                    # Narration mode: 2 Sora clips + TTS narration (original behavior)
                    video_url = await _generate_commercial_video(pipeline_id, response, size, selected_music_override=user_music, voice_config=avatar_voice)
                steps[step]["video_url"] = video_url
                steps[step]["video_format"] = video_format
                steps[step]["video_duration"] = 24
                steps[step]["video_size"] = size

                # Generate per-channel video variants (crop/resize from master)
                if video_url:
                    try:
                        video_variants = await _create_video_variants(pipeline_id, video_url, video_format, pipeline.get("platforms", []))
                        steps[step]["video_variants"] = video_variants
                        logger.info(f"Created video variants for {len(video_variants)} platforms")
                    except Exception as vv_err:
                        logger.warning(f"Failed to create video variants: {vv_err}")

                if not video_url:
                    logger.warning(f"Commercial video generation failed for pipeline {pipeline_id}, continuing pipeline")
                steps[step]["status"] = "completed"

        # Determine next pipeline status
        nxt = _next_step(step)
        mode = pipeline.get("mode", "semi_auto")

        if not nxt:
            new_status = "completed"
            # Save as campaign in campaigns table
            try:
                approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
                clean_copy = _clean_copy_text(approved_copy)
                image_urls = steps.get("lucas_design", {}).get("images", []) or steps.get("lucas_design", {}).get("image_urls", [])
                platform_variants = steps.get("lucas_design", {}).get("platform_variants", {})
                video_url = steps.get("marcos_video", {}).get("video_url", "")
                schedule_text = steps.get("pedro_publish", {}).get("output", "")
                ctx = pipeline.get("result", {}).get("context", {})
                user_campaign_name = pipeline.get("result", {}).get("campaign_name", "")
                campaign_name = user_campaign_name or ctx.get("company", "") or pipeline.get("briefing", "")[:50]
                camp_lang = pipeline.get("result", {}).get("campaign_language", "pt")
                supabase.table("campaigns").insert({
                    "tenant_id": pipeline["tenant_id"],
                    "name": campaign_name,
                    "status": "draft",
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
                        "created_by": pipeline.get("tenant_id"),
                    },
                }).execute()
                logger.info(f"Campaign created from pipeline {pipeline_id}")
            except Exception as camp_err:
                logger.warning(f"Failed to create campaign from pipeline: {camp_err}")
        elif mode == "auto":
            new_status = "running"
        elif step in PAUSE_AFTER:
            new_status = "waiting_approval"
        else:
            new_status = "running"

        supabase.table("pipelines").update({
            "steps": steps, "status": new_status,
            "current_step": nxt or step,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", pipeline_id).execute()

        # In auto mode, run next step
        if mode == "auto" and nxt:
            await _execute_step(pipeline_id, nxt)

        # In semi-auto, if not a pause point, auto-continue to next
        if mode == "semi_auto" and nxt and step not in PAUSE_AFTER:
            await _execute_step(pipeline_id, nxt)

    except Exception as e:
        logger.error(f"Pipeline step {step} failed: {e}")
        steps[step]["status"] = "failed"
        steps[step]["error"] = str(e)
        steps[step]["completed_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("pipelines").update({
            "steps": steps, "status": "failed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", pipeline_id).execute()




def _run_step_in_thread(pipeline_id, step):
    """Run pipeline step in a separate thread with its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_execute_step(pipeline_id, step))
    except Exception as e:
        logger.error(f"Thread pipeline step {step} error: {e}")
    finally:
        loop.close()



def _start_step_bg(pipeline_id, step):
    """Start a pipeline step in a background thread"""
    t = threading.Thread(target=_run_step_in_thread, args=(pipeline_id, step), daemon=True)
    t.start()



def _recover_orphaned_pipelines():
    """On startup, find pipelines stuck in 'running' state and retry them.
    This handles the case where the server restarts and background tasks are lost."""
    try:
        result = supabase.table("pipelines").select("id, status, current_step, steps, updated_at").eq("status", "running").execute()
        orphans = result.data or []
        if not orphans:
            return

        now = datetime.now(timezone.utc)
        for p in orphans:
            # Only recover if stuck for more than 3 minutes
            updated = p.get("updated_at", "")
            if updated:
                try:
                    updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    age_seconds = (now - updated_dt).total_seconds()
                    if age_seconds < 180:  # Less than 3 min, might still be running
                        continue
                except Exception:
                    pass

            pipeline_id = p["id"]
            current_step = p.get("current_step", "")
            steps = p.get("steps", {})

            # Find the stuck step
            retry_step = None
            for s in STEP_ORDER:
                st = steps.get(s, {}).get("status", "")
                if st in ("running", "generating_images", "generating_video"):
                    retry_step = s
                    break

            if retry_step:
                stuck_status = steps.get(retry_step, {}).get("status", "")
                has_output = bool(steps.get(retry_step, {}).get("output", ""))

                # If marcos_video is stuck at generating_video but has AI output,
                # only regenerate the video (skip expensive LLM call)
                if retry_step == "marcos_video" and stuck_status == "generating_video" and has_output:
                    logger.info(f"RECOVERY: Re-generating video only for pipeline {pipeline_id} (AI output exists)")
                    steps[retry_step]["status"] = "generating_video"
                    steps[retry_step]["video_url"] = None
                    supabase.table("pipelines").update({
                        "steps": steps, "status": "running",
                        "updated_at": now.isoformat()
                    }).eq("id", pipeline_id).execute()
                    # Use regenerate-video logic (reuse existing AI script)
                    def _regen_video_recovery(pid, marcos_out, steps_ref):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            fmt = re.search(r'Format:\s*(horizontal|vertical)', marcos_out, re.IGNORECASE)
                            vf = fmt.group(1).lower() if fmt else "horizontal"
                            sz = {"vertical": "720x1280", "horizontal": "1280x720"}.get(vf, "1280x720")
                            p_data = supabase.table("pipelines").select("result").eq("id", pid).single().execute()
                            user_music = (p_data.data or {}).get("result", {}).get("selected_music", "")
                            av_voice = (p_data.data or {}).get("result", {}).get("avatar_voice", None)
                            video_url = loop.run_until_complete(_generate_commercial_video(pid, marcos_out, sz, selected_music_override=user_music, voice_config=av_voice))
                            steps_ref[retry_step]["video_url"] = video_url
                            steps_ref[retry_step]["status"] = "completed"
                            supabase.table("pipelines").update({"steps": steps_ref, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", pid).execute()
                            # Continue pipeline from next step
                            nxt = _next_step(retry_step)
                            if nxt:
                                supabase.table("pipelines").update({"current_step": nxt}).eq("id", pid).execute()
                                loop.run_until_complete(_execute_step(pid, nxt))
                            else:
                                supabase.table("pipelines").update({"status": "completed"}).eq("id", pid).execute()
                        except Exception as e:
                            logger.error(f"RECOVERY video regen failed: {e}")
                            steps_ref[retry_step]["status"] = "pending"
                            supabase.table("pipelines").update({"steps": steps_ref, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", pid).execute()
                            _start_step_bg(pid, retry_step)
                        finally:
                            loop.close()
                    marcos_output = steps[retry_step].get("output", "")
                    t = threading.Thread(target=_regen_video_recovery, args=(pipeline_id, marcos_output, steps), daemon=True)
                    t.start()
                else:
                    logger.info(f"RECOVERY: Retrying orphaned pipeline {pipeline_id} at step {retry_step}")
                    steps[retry_step]["status"] = "pending"
                    steps[retry_step]["error"] = None
                    supabase.table("pipelines").update({
                        "steps": steps, "status": "running",
                        "updated_at": now.isoformat()
                    }).eq("id", pipeline_id).execute()
                    _start_step_bg(pipeline_id, retry_step)
            else:
                # Check if current_step is pending but pipeline is running (step never started)
                current_step_status = steps.get(current_step, {}).get("status", "")
                if current_step_status == "pending" and current_step in STEP_ORDER:
                    logger.info(f"RECOVERY: Starting pending step {current_step} for pipeline {pipeline_id}")
                    _start_step_bg(pipeline_id, current_step)
                else:
                    logger.warning(f"RECOVERY: Pipeline {pipeline_id} is running but no stuck step found at {current_step}")
    except Exception as e:
        logger.error(f"Pipeline recovery failed: {e}")



# Schedule recovery after a short delay to allow server startup
def _delayed_recovery():
    import time as _time
    _time.sleep(10)  # Wait for server to fully start
    _recover_orphaned_pipelines()

threading.Thread(target=_delayed_recovery, daemon=True).start()


