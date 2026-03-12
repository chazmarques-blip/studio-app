from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper
from core.models import ChannelCreate

router = APIRouter(prefix="/api", tags=["channels"])


@router.post("/channels")
async def create_channel(data: ChannelCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    existing = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", data.type).execute()
    if existing.data:
        updates = {"config": data.config or {}, "status": "connecting", "updated_at": datetime.now(timezone.utc).isoformat()}
        supabase.table("channels").update(updates).eq("id", existing.data[0]["id"]).execute()
        return {**existing.data[0], **updates}
    channel = {
        "tenant_id": tenant["id"],
        "type": data.type,
        "status": "connecting",
        "config": data.config or {},
    }
    result = supabase.table("channels").insert(channel).execute()
    return result.data[0]


@router.get("/channels")
async def list_channels(user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    result = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).execute()
    return {"channels": result.data}


@router.put("/channels/{channel_id}/status")
async def update_channel_status(channel_id: str, status: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    supabase.table("channels").update({"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", channel_id).eq("tenant_id", tenant["id"]).execute()
    return {"status": "ok"}


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    supabase.table("channels").delete().eq("id", channel_id).eq("tenant_id", tenant["id"]).execute()
    return {"status": "ok"}
