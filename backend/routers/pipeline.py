from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import asyncio
import base64
import re
import time
import uuid
import os
import threading
import shutil

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger

router = APIRouter(prefix="/api/campaigns/pipeline", tags=["pipeline"])

UPLOADS_DIR = "/app/backend/uploads/pipeline"
ASSETS_DIR = "/app/backend/uploads/pipeline/assets"
os.makedirs(ASSETS_DIR, exist_ok=True)
BACKEND_URL = os.environ.get("BACKEND_URL", "")

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
    contact_info: Optional[dict] = {}
    uploaded_assets: Optional[list] = []


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


async def _generate_image(prompt_text, pipeline_id, index):
    """Generate a single image using Gemini Nano Banana and save to disk"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"img-{pipeline_id}-{index}-{int(time.time())}",
            system_message="You are a professional graphic designer. Generate high-quality marketing images."
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])

        msg = UserMessage(text=prompt_text)
        text_resp, images = await chat.send_message_multimodal_response(msg)

        if images and len(images) > 0:
            img_data = base64.b64decode(images[0]["data"])
            filename = f"{pipeline_id}_{index}_{uuid.uuid4().hex[:6]}.png"
            filepath = os.path.join(UPLOADS_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            return f"/api/uploads/pipeline/{filename}"
    except Exception as e:
        logger.warning(f"Nano Banana image generation failed for index {index}: {e}")
    return None


async def _generate_design_images(pipeline_id, concepts_text, platforms):
    """Parse Lucas's concepts and generate images for each"""
    # Get pipeline data for brand info
    pipeline_data = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    brand_context = ""
    if pipeline_data:
        p = pipeline_data[0]
        result_data = p.get("result", {})
        ctx = result_data.get("context", {})
        assets = result_data.get("uploaded_assets", [])
        contact = result_data.get("contact_info", {})

        brand_parts = []
        if ctx.get("company"):
            brand_parts.append(f"The brand name is '{ctx['company']}'. Include the text '{ctx['company']}' prominently in the design.")
        if contact.get("website"):
            brand_parts.append(f"Include the website '{contact['website']}' in the design.")
        if assets:
            logo_assets = [a for a in assets if a.get("type") == "logo"]
            if logo_assets:
                brand_parts.append("CRITICAL: The brand has an official logo that must NOT be recreated, redrawn, or modified in ANY way. Do NOT generate or create a new logo. The official logo will be overlaid separately. Instead, leave a clear space or area in the design where the logo can be placed. Focus on the campaign visual, imagery, and text without attempting to recreate the logo.")
            ref_assets = [a for a in assets if a.get("type") == "reference"]
            if ref_assets:
                brand_parts.append(f"Use visual style inspired by {len(ref_assets)} reference image(s) provided: modern, professional aesthetic.")
        if brand_parts:
            brand_context = "\nBRAND REQUIREMENTS (MANDATORY): " + " ".join(brand_parts)

    # First, use Claude to extract image prompts from Lucas's descriptions
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"prompt-extract-{pipeline_id}-{int(time.time())}",
            system_message="You extract image generation prompts from design concept descriptions. Return ONLY the prompts, one per line, numbered. Each prompt should be a detailed, visual description suitable for AI image generation. No explanations."
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        extract_prompt = f"""Extract exactly 3 image generation prompts from these design concepts. Each prompt should describe the visual in detail (colors, composition, style, mood, text overlays). Keep prompts under 200 words each.
{brand_context}

Design concepts:
{concepts_text}

Format:
1. [detailed image prompt including any brand name text]
2. [detailed image prompt including any brand name text]
3. [detailed image prompt including any brand name text]"""

        response = await chat.send_message(UserMessage(text=extract_prompt))
        prompts = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', response, re.DOTALL)
        prompts = [p.strip() for p in prompts if p.strip()][:3]

        if len(prompts) < 3:
            # Fallback: use generic prompts from the concepts
            prompts = [
                f"Professional marketing banner design concept 1, modern clean style, {platforms[0] if platforms else 'social media'} format",
                f"Professional marketing banner design concept 2, bold colors, {platforms[0] if platforms else 'social media'} format",
                f"Professional marketing banner design concept 3, minimalist elegant, {platforms[0] if platforms else 'social media'} format",
            ]
    except Exception as e:
        logger.warning(f"Prompt extraction failed: {e}")
        prompts = [
            "Professional marketing campaign banner, modern design, vibrant colors, social media format",
            "Creative marketing visual, bold typography, gradient background, digital marketing",
            "Elegant promotional graphic, minimalist style, premium feel, brand campaign",
        ]

    # Generate images sequentially to avoid overwhelming the API
    image_urls = []
    for i, prompt in enumerate(prompts):
        url = await _generate_image(prompt, pipeline_id, i + 1)
        image_urls.append(url)

    return image_urls, prompts


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
    contact = pipeline.get("result", {}).get("contact_info", {})
    assets = pipeline.get("result", {}).get("uploaded_assets", [])

    ctx_str = ""
    if ctx:
        parts = []
        if ctx.get("company"): parts.append(f"Company: {ctx['company']}")
        if ctx.get("industry"): parts.append(f"Industry: {ctx['industry']}")
        if ctx.get("audience"): parts.append(f"Target audience: {ctx['audience']}")
        if ctx.get("brand_voice"): parts.append(f"Brand voice: {ctx['brand_voice']}")
        ctx_str = "\n".join(parts)

    contact_str = ""
    if contact:
        cparts = []
        if contact.get("phone"): cparts.append(f"Phone: {contact['phone']}")
        if contact.get("website"): cparts.append(f"Website: {contact['website']}")
        if contact.get("email"): cparts.append(f"Email: {contact['email']}")
        if cparts:
            contact_str = "\nContact information to include in the campaign:\n" + "\n".join(cparts)

    assets_str = ""
    if assets:
        logo_assets = [a for a in assets if a.get("type") == "logo"]
        ref_assets = [a for a in assets if a.get("type") == "reference"]
        aparts = []
        if logo_assets:
            aparts.append(f"Brand logo has been uploaded ({len(logo_assets)} file(s)). Use the brand identity from the logo in the campaign visuals.")
        if ref_assets:
            aparts.append(f"Reference images have been uploaded ({len(ref_assets)} file(s)). Use these as visual inspiration and style reference for the campaign designs.")
        if aparts:
            assets_str = "\nUploaded assets:\n" + "\n".join(aparts)

    if step == "sofia_copy":
        return f"""Create 3 campaign copy variations for the following briefing.
Target platforms: {platforms_str}

Briefing: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}
{assets_str}

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
{contact_str}
{assets_str}

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
{contact_str}

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

        # Use appropriate model per step - Gemini Flash for simpler steps
        STEP_MODELS = {
            "sofia_copy": ("anthropic", "claude-sonnet-4-5-20250929"),
            "ana_review_copy": ("gemini", "gemini-2.0-flash"),
            "lucas_design": ("anthropic", "claude-sonnet-4-5-20250929"),
            "ana_review_design": ("gemini", "gemini-2.0-flash"),
            "pedro_publish": ("gemini", "gemini-2.0-flash"),
        }
        provider, model = STEP_MODELS.get(step, ("anthropic", "claude-sonnet-4-5-20250929"))

        # Retry up to 2 times on transient errors
        response = None
        last_error = None
        for attempt in range(3):
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-{int(time.time())}-{attempt}",
                    system_message=system
                ).with_model(provider, model)

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
            steps[step]["status"] = "completed"

        # Determine next pipeline status
        nxt = _next_step(step)
        mode = pipeline.get("mode", "semi_auto")

        if not nxt:
            new_status = "completed"
            # Save as campaign in campaigns table
            try:
                approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
                image_urls = steps.get("lucas_design", {}).get("image_urls", [])
                schedule_text = steps.get("pedro_publish", {}).get("output", "")
                ctx = pipeline.get("result", {}).get("context", {})
                campaign_name = ctx.get("company", "") or pipeline.get("briefing", "")[:50]
                supabase.table("campaigns").insert({
                    "tenant_id": pipeline["tenant_id"],
                    "name": f"[Pipeline] {campaign_name}",
                    "type": "ai_pipeline",
                    "status": "draft",
                    "target_segment": {"platforms": pipeline.get("platforms", [])},
                    "messages": [{"step": 1, "channel": "multi", "content": approved_copy, "delay_hours": 0}],
                    "schedule": {"pipeline_id": pipeline_id, "schedule_text": schedule_text},
                    "stats": {"images": [u for u in image_urls if u], "pipeline_id": pipeline_id},
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


# ── Endpoints ──

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

@router.post("/upload")
async def upload_pipeline_asset(
    file: UploadFile = File(...),
    asset_type: str = Form("reference"),
    user=Depends(get_current_user)
):
    """Upload a brand logo or reference image for the pipeline"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = os.path.splitext(file.filename or "upload.png")[1] or ".png"
    filename = f"{asset_type}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(ASSETS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/api/uploads/pipeline/assets/{filename}"
    return {"url": url, "filename": filename, "type": asset_type, "size": len(content)}


@router.get("/list")
async def list_pipelines(user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(20).execute()
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
        },
    }

    result = supabase.table("pipelines").insert(pipeline).execute()
    pid = result.data[0]["id"]

    _start_step_bg(pid, "sofia_copy")
    return result.data[0]


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return result.data[0]


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
        _start_step_bg(pipeline_id, nxt)
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
async def retry_failed_step(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    if pipeline["status"] not in ("failed", "running"):
        raise HTTPException(status_code=400, detail="Pipeline is not in a retryable state")

    steps = pipeline.get("steps") or {}
    retry_step = None
    for s in STEP_ORDER:
        st = steps.get(s, {}).get("status")
        if st in ("failed", "running"):
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


class RegenerateDesignRequest(BaseModel):
    design_index: int = 0
    feedback: str = ""


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
    enhanced_prompt = f"{original_prompt}. ADJUSTMENTS REQUESTED: {data.feedback}" if data.feedback else original_prompt

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
            if fresh.get("current_step") in ("ana_review_design", "lucas_design"):
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
