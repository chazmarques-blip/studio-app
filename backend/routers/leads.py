from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper
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
