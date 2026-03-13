from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import re
import time

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger

router = APIRouter(prefix="/api/campaigns/pipeline", tags=["pipeline"])

STEP_ORDER = ["sofia_copy", "ana_review_copy", "lucas_design", "ana_review_design", "pedro_publish"]
PAUSE_AFTER = {"ana_review_copy", "ana_review_design"}

STEP_LABELS = {
    "sofia_copy": {"agent": "Sofia", "role": "Copywriter", "icon": "pen-tool"},
    "ana_review_copy": {"agent": "Ana", "role": "Revisora de Copy", "icon": "check-circle"},
    "lucas_design": {"agent": "Lucas", "role": "Designer", "icon": "palette"},
    "ana_review_design": {"agent": "Ana", "role": "Revisora de Design", "icon": "check-circle"},
    "pedro_publish": {"agent": "Pedro", "role": "Publisher", "icon": "calendar-clock"},
}

STEP_SYSTEMS = {
    "sofia_copy": """You are Sofia, an expert AI copywriter. You create marketing campaign copy.
ALWAYS write in the SAME language the user writes to you.
When given a briefing, create EXACTLY 3 variations of campaign copy.
Format each variation clearly with:
===VARIATION 1===
Title: [catchy title]
Copy: [main text, 2-3 paragraphs]
CTA: [call to action]
Hashtags: [relevant hashtags]
===VARIATION 2===
...
===VARIATION 3===
...""",

    "ana_review_copy": """You are Ana, an expert marketing content reviewer and strategist.
ALWAYS write in the SAME language as the content you are reviewing.
You evaluate marketing copy for effectiveness, persuasion, and brand alignment.
When reviewing variations, score each on Clarity, Persuasion, Brand Fit (1-10) and select the best.
At the END of your review, you MUST include this exact line:
SELECTED_OPTION: [number 1, 2, or 3]""",

    "ana_review_design": """You are Ana, an expert marketing content reviewer.
ALWAYS write in the SAME language as the content you are reviewing.
You evaluate design concepts for visual impact, brand alignment, and platform suitability.
When reviewing designs for multiple platforms, select the best design for EACH platform.
At the END of your review, you MUST include a line for each platform like:
SELECTED_FOR_[PLATFORM]: [number 1, 2, or 3]
Example: SELECTED_FOR_INSTAGRAM: 2""",

    "lucas_design": """You are Lucas, an expert AI visual concept designer.
ALWAYS write in the SAME language the user writes to you.
You create detailed visual design concepts including layout, colors, imagery, typography.
When asked, create EXACTLY 3 design concept variations.
Format each variation clearly with:
===DESIGN 1===
Concept: [name]
Description: [detailed visual description]
Colors: [palette]
Typography: [font suggestions]
Layout: [composition details]
Platform Specs: [dimensions and adaptations]
===DESIGN 2===
...
===DESIGN 3===
...""",

    "pedro_publish": """You are Pedro, an expert content scheduling and publishing strategist.
ALWAYS write in the SAME language the user writes to you.
You create optimal publishing schedules and adapt content for each platform.
Include: best posting times, frequency, platform-specific adaptations, and a clear timeline.
Format as a structured schedule with dates and times.""",
}


# ── Models ──

class PipelineCreate(BaseModel):
    briefing: str
    mode: str = "semi_auto"
    platforms: list = ["whatsapp", "instagram"]
    context: Optional[dict] = {}


class PipelineApprove(BaseModel):
    selection: Optional[int] = None
    selections: Optional[dict] = None
    feedback: Optional[str] = None


# ── Helpers ──

async def _get_tenant(user):
    t = supabase.table("tenants").select("id, plan").eq("owner_id", user["id"]).execute()
    if not t.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t.data[0]


def _next_step(current):
    idx = STEP_ORDER.index(current)
    return STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None


def _parse_ana_copy_selection(text):
    match = re.search(r'SELECTED_OPTION:\s*(\d)', text)
    return int(match.group(1)) if match else 1


def _parse_ana_design_selections(text, platforms):
    selections = {}
    for p in platforms:
        match = re.search(rf'SELECTED_FOR_{p.upper()}:\s*(\d)', text)
        selections[p] = int(match.group(1)) if match else 1
    return selections


def _build_prompt(step, pipeline):
    briefing = pipeline["briefing"]
    platforms = pipeline.get("platforms") or []
    platforms_str = ", ".join(platforms)
    steps = pipeline.get("steps") or {}
    ctx = pipeline.get("result", {}).get("context", {})
    ctx_str = ""
    if ctx:
        parts = []
        if ctx.get("company"): parts.append(f"Company: {ctx['company']}")
        if ctx.get("industry"): parts.append(f"Industry: {ctx['industry']}")
        if ctx.get("audience"): parts.append(f"Target audience: {ctx['audience']}")
        if ctx.get("brand_voice"): parts.append(f"Brand voice: {ctx['brand_voice']}")
        ctx_str = "\n".join(parts)

    if step == "sofia_copy":
        return f"""Create 3 campaign copy variations for the following briefing.
Target platforms: {platforms_str}

Briefing: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}

Remember: Create EXACTLY 3 variations formatted with ===VARIATION 1===, ===VARIATION 2===, ===VARIATION 3==="""

    elif step == "ana_review_copy":
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        return f"""Review these 3 copy variations created by Sofia for the following campaign:

Briefing: {briefing}
Platforms: {platforms_str}

Sofia's variations:
{sofia_output}

Analyze each variation on: Clarity (1-10), Persuasion (1-10), Brand Alignment (1-10), CTA Strength (1-10).
Select the BEST one.
IMPORTANT: End your review with: SELECTED_OPTION: [1, 2, or 3]"""

    elif step == "lucas_design":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        if not approved_copy:
            approved_copy = steps.get("ana_review_copy", {}).get("output", "")
        return f"""Create 3 visual design concepts for the following approved campaign copy.
Target platforms: {platforms_str}

Approved copy:
{approved_copy}

Original briefing: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}

Create EXACTLY 3 design concepts. For each, specify dimensions and adaptations for: {platforms_str}.
Format with ===DESIGN 1===, ===DESIGN 2===, ===DESIGN 3==="""

    elif step == "ana_review_design":
        lucas_output = steps.get("lucas_design", {}).get("output", "")
        return f"""Review these 3 design concepts created by Lucas.
Target platforms: {platforms_str}

Design concepts:
{lucas_output}

For EACH platform, select the best design concept.
IMPORTANT: End with a line for each platform:
{chr(10).join(f'SELECTED_FOR_{p.upper()}: [1, 2, or 3]' for p in platforms)}"""

    elif step == "pedro_publish":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        design_approvals = steps.get("ana_review_design", {}).get("selections", {})
        ana_design_output = steps.get("ana_review_design", {}).get("output", "")
        return f"""Create a complete publishing schedule and strategy for this campaign.

Platforms: {platforms_str}
Approved copy: {approved_copy}
Design review and approvals: {ana_design_output}
Platform-specific design selections: {design_approvals}

Original briefing: {briefing}

Create a detailed schedule with:
- Best posting times per platform
- Content adaptations per platform
- Recommended frequency
- Timeline (next 7 days)
- Any platform-specific considerations"""

    return briefing


async def _execute_step(pipeline_id, step):
    """Execute a single pipeline step using AI"""
    pipeline = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    if not pipeline:
        return
    pipeline = pipeline[0]
    steps = pipeline.get("steps") or {}

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

        # Retry up to 2 times on transient errors
        response = None
        last_error = None
        for attempt in range(3):
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-{int(time.time())}-{attempt}",
                    system_message=system
                ).with_model("anthropic", "claude-sonnet-4-5-20250929")

                start = time.time()
                response = await chat.send_message(UserMessage(text=prompt))
                elapsed = round((time.time() - start) * 1000)
                break
            except Exception as retry_err:
                last_error = retry_err
                logger.warning(f"Pipeline step {step} attempt {attempt+1} failed: {retry_err}")
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(2)

        if response is None:
            raise last_error

        steps[step]["output"] = response
        steps[step]["status"] = "completed"
        steps[step]["completed_at"] = datetime.now(timezone.utc).isoformat()
        steps[step]["elapsed_ms"] = elapsed

        # For Ana's reviews: parse selections
        if step == "ana_review_copy":
            selected = _parse_ana_copy_selection(response)
            steps[step]["auto_selection"] = selected
            # Extract approved copy from Sofia's output
            sofia_output = steps.get("sofia_copy", {}).get("output", "")
            variations = re.split(r'===VARIATION \d+===', sofia_output)
            variations = [v.strip() for v in variations if v.strip()]
            if 0 < selected <= len(variations):
                steps[step]["approved_content"] = variations[selected - 1]
            else:
                steps[step]["approved_content"] = variations[0] if variations else sofia_output

        elif step == "ana_review_design":
            platforms = pipeline.get("platforms") or []
            selections = _parse_ana_design_selections(response, platforms)
            steps[step]["auto_selections"] = selections
            steps[step]["selections"] = selections

        # Determine next pipeline status
        nxt = _next_step(step)
        mode = pipeline.get("mode", "semi_auto")

        if not nxt:
            new_status = "completed"
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


# ── Endpoints ──

@router.get("/list")
async def list_pipelines(user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(20).execute()
    return {"pipelines": result.data or []}


@router.post("")
async def create_pipeline(data: PipelineCreate, bg: BackgroundTasks, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    if tenant["plan"] != "enterprise":
        raise HTTPException(status_code=403, detail="Pipeline requires Enterprise plan")

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
        "result": {"context": data.context or {}},
    }

    result = supabase.table("pipelines").insert(pipeline).execute()
    pid = result.data[0]["id"]

    bg.add_task(_execute_step, pid, "sofia_copy")
    return result.data[0]


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return result.data[0]


@router.post("/{pipeline_id}/approve")
async def approve_step(pipeline_id: str, data: PipelineApprove, bg: BackgroundTasks, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    if pipeline["status"] != "waiting_approval":
        raise HTTPException(status_code=400, detail="Pipeline is not waiting for approval")

    steps = pipeline.get("steps") or {}
    current = pipeline.get("current_step")

    # Find the step that just completed and needs approval
    prev_step = STEP_ORDER[STEP_ORDER.index(current) - 1] if STEP_ORDER.index(current) > 0 else current
    # Actually, current_step is set to the NEXT step when paused
    # The step that needs approval is the one before current_step
    approval_step = None
    for s in reversed(STEP_ORDER):
        if steps.get(s, {}).get("status") == "completed" and s in PAUSE_AFTER:
            approval_step = s
            break

    if not approval_step:
        raise HTTPException(status_code=400, detail="No step awaiting approval")

    # Apply user's selection
    if approval_step == "ana_review_copy" and data.selection is not None:
        steps[approval_step]["user_selection"] = data.selection
        # Update approved content with user's choice
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        variations = re.split(r'===VARIATION \d+===', sofia_output)
        variations = [v.strip() for v in variations if v.strip()]
        sel = data.selection
        if 0 < sel <= len(variations):
            steps[approval_step]["approved_content"] = variations[sel - 1]

    elif approval_step == "ana_review_design" and data.selections:
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
        bg.add_task(_execute_step, pipeline_id, nxt)
        return {"status": "approved", "next_step": nxt}
    else:
        supabase.table("pipelines").update({"status": "completed"}).eq("id", pipeline_id).execute()
        return {"status": "completed"}


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").delete().eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"status": "deleted"}


@router.post("/{pipeline_id}/retry")
async def retry_failed_step(pipeline_id: str, bg: BackgroundTasks, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    if pipeline["status"] != "failed":
        raise HTTPException(status_code=400, detail="Pipeline is not in failed state")

    steps = pipeline.get("steps") or {}
    failed_step = None
    for s in STEP_ORDER:
        if steps.get(s, {}).get("status") == "failed":
            failed_step = s
            break

    if not failed_step:
        raise HTTPException(status_code=400, detail="No failed step found")

    steps[failed_step]["status"] = "pending"
    steps[failed_step]["error"] = None
    supabase.table("pipelines").update({
        "steps": steps, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    bg.add_task(_execute_step, pipeline_id, failed_step)
    return {"status": "retrying", "step": failed_step}


@router.get("/{pipeline_id}/labels")
async def get_step_labels(pipeline_id: str, user=Depends(get_current_user)):
    return {"labels": STEP_LABELS, "order": STEP_ORDER}
