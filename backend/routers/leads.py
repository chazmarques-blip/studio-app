from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
import uuid

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper, logger
from core.llm import direct_completion, DEFAULT_MODEL
from core.models import LeadCreate, LeadUpdate

router = APIRouter(prefix="/api", tags=["leads"])


@router.get("/leads")
async def list_leads(stage: Optional[str] = None, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    query = supabase.table("leads").select("*").eq("tenant_id", tenant["id"]).order("updated_at", desc=True)
    if stage:
        query = query.eq("stage", stage)
    result = query.execute()
    return {"leads": result.data}


@router.post("/leads")
async def create_lead(data: LeadCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    lead = {
        "tenant_id": tenant["id"],
        "name": data.name,
        "phone": data.phone,
        "email": data.email,
        "company": data.company,
        "conversation_id": data.conversation_id,
        "stage": data.stage,
        "value": float(data.value),
        "score": 0,
        "ai_analysis": {},
        "metadata": {},
    }
    result = supabase.table("leads").insert(lead).execute()
    return result.data[0]


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    result = supabase.table("leads").select("*").eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result.data[0]


@router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, data: LeadUpdate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = supabase.table("leads").update(updates).eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result.data[0]


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    supabase.table("leads").delete().eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    return {"status": "ok"}


@router.post("/leads/{lead_id}/ai-score")
async def ai_score_lead(lead_id: str, user=Depends(get_current_user)):
    """Use AI to analyze and score a lead based on their data and conversation history"""
    tenant = await get_tenant_helper(user)
    lead_result = supabase.table("leads").select("*").eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    if not lead_result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = lead_result.data[0]

    # Gather conversation context if available
    convo_context = ""
    if lead.get("conversation_id"):
        msgs = supabase.table("messages").select("sender, content").eq("conversation_id", lead["conversation_id"]).order("created_at", desc=False).limit(15).execute()
        if msgs.data:
            convo_context = "\n".join([f"{m['sender']}: {m['content']}" for m in msgs.data])

    prompt = f"""Analyze this lead and provide a JSON response with:
- "score": integer 0-100 (likelihood of conversion)
- "stage_suggestion": one of "new", "qualified", "proposal", "won", "lost"
- "reason": brief explanation (1-2 sentences)
- "next_action": recommended next step (1 sentence)

Lead data:
- Name: {lead.get('name', 'Unknown')}
- Company: {lead.get('company', 'N/A')}
- Phone: {lead.get('phone', 'N/A')}
- Email: {lead.get('email', 'N/A')}
- Current stage: {lead.get('stage', 'new')}
- Value: ${lead.get('value', 0)}
"""
    if convo_context:
        prompt += f"\nConversation history:\n{convo_context}"
    else:
        prompt += "\nNo conversation history available."

    prompt += "\n\nRespond ONLY with valid JSON, no extra text."

    try:
        response = await direct_completion(
            system_prompt="You are a sales lead scoring AI. Analyze leads and return JSON with score, stage_suggestion, reason, and next_action.",
            user_message=prompt,
        )

        import json
        # Try to parse JSON from response
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        analysis = json.loads(clean)

        score = max(0, min(100, int(analysis.get("score", 50))))
        ai_data = {
            "score": score,
            "stage_suggestion": analysis.get("stage_suggestion", lead.get("stage", "new")),
            "reason": analysis.get("reason", ""),
            "next_action": analysis.get("next_action", ""),
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }

        supabase.table("leads").update({
            "score": score,
            "ai_analysis": ai_data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", lead_id).execute()

        return ai_data

    except Exception as e:
        logger.error(f"AI scoring error: {e}")
        fallback = {"score": 50, "stage_suggestion": lead.get("stage", "new"), "reason": "Unable to analyze automatically", "next_action": "Manual review recommended"}
        supabase.table("leads").update({"score": 50, "ai_analysis": fallback, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", lead_id).execute()
        return fallback
