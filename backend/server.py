from fastapi import FastAPI, APIRouter, Depends
from starlette.middleware.cors import CORSMiddleware
import os
import logging

from core.deps import supabase, get_current_user

from routers.auth import router as auth_router
from routers.agents import router as agents_router
from routers.conversations import router as conversations_router
from routers.leads import router as leads_router
from routers.ai import router as ai_router
from routers.whatsapp import router as whatsapp_router
from routers.channels import router as channels_router
from routers.telegram import router as telegram_router

app = FastAPI(title="AgentZZ API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@api_router.get("/health")
async def health():
    return {"status": "ok", "service": "agentzz-api", "version": "0.4.0", "database": "supabase"}


@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        return {"messages_today": 0, "resolution_rate": 0, "active_leads": 0, "revenue": 0, "plan": "free", "messages_used": 0, "messages_limit": 50, "agents_count": 0, "agents_limit": 1, "period_start": None}
    tenant = tenant_result.data[0]
    agent_count = len(supabase.table("agents").select("id").eq("tenant_id", tenant["id"]).execute().data)
    lead_count = len(supabase.table("leads").select("id").eq("tenant_id", tenant["id"]).execute().data)
    return {
        "messages_today": tenant.get("usage", {}).get("messages_sent_this_period", 0),
        "resolution_rate": 0,
        "active_leads": lead_count,
        "revenue": 0,
        "plan": tenant.get("plan", "free"),
        "plan_status": tenant.get("plan_status", "active"),
        "billing_cycle": tenant.get("settings", {}).get("billing_cycle", "monthly"),
        "messages_used": tenant.get("usage", {}).get("messages_sent_this_period", 0),
        "messages_limit": tenant.get("limits", {}).get("messages_limit", 50),
        "agents_count": agent_count,
        "agents_limit": tenant.get("limits", {}).get("agents", 1),
        "period_start": tenant.get("usage", {}).get("period_start"),
    }


PLAN_CONFIG = {
    "free": {"agents": 1, "messages_limit": 200, "messages_period": "month", "channels": 1},
    "starter": {"agents": 3, "messages_limit": 1500, "messages_period": "month", "channels": 5},
    "pro": {"agents": 5, "messages_limit": 5000, "messages_period": "month", "channels": 5},
    "enterprise": {"agents": 10, "messages_limit": 10000, "messages_period": "month", "channels": 5},
}


@api_router.post("/billing/upgrade")
async def upgrade_plan(data: dict, user=Depends(get_current_user)):
    from datetime import datetime, timezone
    plan = data.get("plan", "free")
    billing_cycle = data.get("billing_cycle", "monthly")

    if plan not in PLAN_CONFIG:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid plan")

    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")

    limits = PLAN_CONFIG[plan]
    settings = tenant_result.data[0].get("settings", {}) or {}
    settings["billing_cycle"] = billing_cycle

    supabase.table("tenants").update({
        "plan": plan,
        "plan_status": "active",
        "limits": limits,
        "settings": settings,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", tenant_result.data[0]["id"]).execute()

    return {"status": "ok", "plan": plan, "limits": limits}


# Include all routers
app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(conversations_router)
app.include_router(leads_router)
app.include_router(ai_router)
app.include_router(whatsapp_router)
app.include_router(channels_router)
app.include_router(telegram_router)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
