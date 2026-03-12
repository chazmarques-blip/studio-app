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
        return {"messages_today": 0, "resolution_rate": 0, "active_leads": 0, "revenue": 0, "plan": "free", "messages_used": 0, "messages_limit": 50}
    tenant = tenant_result.data[0]
    agent_count = len(supabase.table("agents").select("id").eq("tenant_id", tenant["id"]).execute().data)
    return {
        "messages_today": tenant.get("usage", {}).get("messages_sent_this_period", 0),
        "resolution_rate": 0,
        "active_leads": 0,
        "revenue": 0,
        "plan": tenant.get("plan", "free"),
        "messages_used": tenant.get("usage", {}).get("messages_sent_this_period", 0),
        "messages_limit": tenant.get("limits", {}).get("messages_limit", 50),
        "agents_count": agent_count,
        "agents_limit": tenant.get("limits", {}).get("agents", 1),
    }


# Include all routers
app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(conversations_router)
app.include_router(leads_router)
app.include_router(ai_router)
app.include_router(whatsapp_router)
app.include_router(channels_router)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
