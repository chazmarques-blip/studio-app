from fastapi import FastAPI, APIRouter, Depends
from fastapi.staticfiles import StaticFiles
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
from routers.google import router as google_router
from routers.campaigns import router as campaigns_router
from routers.pipeline import router as pipeline_router
from routers.agent_generator import router as agent_generator_router
from routers.data import router as data_router

app = FastAPI(title="AgentZZ API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@api_router.get("/health")
async def health():
    return {"status": "ok", "service": "agentzz-api", "version": "0.4.0", "database": "supabase"}


@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    from datetime import datetime, timezone, timedelta
    from collections import Counter

    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    empty = {"messages_today": 0, "resolution_rate": 0, "active_leads": 0, "revenue": 0, "plan": "free",
             "messages_used": 0, "messages_limit": 50, "agents_count": 0, "agents_limit": 1,
             "recent_conversations": [], "agents": [], "crm_pipeline": {}, "messages_by_day": [], "channel_stats": []}
    if not tenant_result.data:
        return empty
    tenant = tenant_result.data[0]
    tid = tenant["id"]

    # Agents
    agents_data = supabase.table("agents").select("*").eq("tenant_id", tid).execute().data or []

    # Leads
    leads_data = supabase.table("leads").select("*").eq("tenant_id", tid).execute().data or []
    pipeline = Counter(l.get("stage", "new") for l in leads_data)
    total_value = sum(float(l.get("value", 0)) for l in leads_data if l.get("stage") == "won")

    # Conversations (recent 5)
    convos = supabase.table("conversations").select("*").eq("tenant_id", tid).order("last_message_at", desc=True).limit(5).execute().data or []

    # All conversations for channel stats
    all_convos = supabase.table("conversations").select("id, channel_type, status, created_at").eq("tenant_id", tid).execute().data or []
    channel_counter = Counter(c.get("channel_type", "web") for c in all_convos)
    resolved = sum(1 for c in all_convos if c.get("status") == "resolved")
    resolution_rate = round((resolved / len(all_convos) * 100) if all_convos else 0)

    # Messages last 7 days
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    msgs_week = supabase.table("messages").select("created_at, sender").gte("created_at", week_ago).execute().data or []
    # Filter by tenant conversations
    convo_ids = {c["id"] for c in all_convos}
    # Group by day
    day_counts = Counter()
    today_count = 0
    today_str = now.strftime("%Y-%m-%d")
    for m in msgs_week:
        day = (m.get("created_at") or "")[:10]
        day_counts[day] += 1
        if day == today_str:
            today_count += 1
    messages_by_day = []
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        label = (now - timedelta(days=i)).strftime("%a")
        messages_by_day.append({"date": d, "label": label, "count": day_counts.get(d, 0)})

    # Agent performance
    agent_list = []
    for a in agents_data:
        a_convos = [c for c in all_convos if c.get("agent_id") == a.get("id")]
        agent_list.append({
            "id": a["id"], "name": a["name"], "type": a.get("type", "support"),
            "status": a.get("status", "active"),
            "conversations": len(a_convos),
            "resolved": sum(1 for c in a_convos if c.get("status") == "resolved"),
        })

    # Channel stats
    channel_stats = [{"channel": ch, "count": ct} for ch, ct in channel_counter.most_common()]

    usage = tenant.get("usage", {}) or {}
    limits = tenant.get("limits", {}) or {}

    return {
        "messages_today": today_count or usage.get("messages_sent_this_period", 0),
        "resolution_rate": resolution_rate,
        "active_leads": len([l for l in leads_data if l.get("stage") not in ("won", "lost")]),
        "total_leads": len(leads_data),
        "revenue": total_value,
        "plan": tenant.get("plan", "free"),
        "plan_status": tenant.get("plan_status", "active"),
        "billing_cycle": tenant.get("settings", {}).get("billing_cycle", "monthly"),
        "messages_used": usage.get("messages_sent_this_period", 0),
        "messages_limit": limits.get("messages_limit", 50),
        "agents_count": len(agents_data),
        "agents_limit": limits.get("agents", 1),
        "messages_by_day": messages_by_day,
        "recent_conversations": [{"id": c["id"], "contact_name": c.get("contact_name", "Unknown"), "channel_type": c.get("channel_type", "web"), "status": c.get("status", "active"), "last_message_at": c.get("last_message_at")} for c in convos],
        "agents": agent_list,
        "crm_pipeline": {"new": pipeline.get("new", 0), "qualified": pipeline.get("qualified", 0), "proposal": pipeline.get("proposal", 0), "won": pipeline.get("won", 0), "lost": pipeline.get("lost", 0)},
        "channel_stats": channel_stats,
    }


PLAN_CONFIG = {
    "free": {"agents": 1, "messages_limit": 200, "messages_period": "month", "channels": 1, "personal_agent": False},
    "starter": {"agents": 3, "messages_limit": 1500, "messages_period": "month", "channels": 5, "personal_agent": False},
    "pro": {"agents": 5, "messages_limit": 5000, "messages_period": "month", "channels": 5, "personal_agent": True},
    "enterprise": {"agents": 10, "messages_limit": 10000, "messages_period": "month", "channels": 5, "personal_agent": True},
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
app.include_router(google_router)
app.include_router(campaigns_router)
app.include_router(pipeline_router)
app.include_router(agent_generator_router)
app.include_router(data_router)
app.include_router(api_router)

# Serve uploaded files (pipeline images, etc.)
os.makedirs("/app/backend/uploads/pipeline", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="/app/backend/uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
