from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper
from core.models import AgentCreate, AgentUpdate, KnowledgeCreate, FollowUpRuleCreate, DeployAgentRequest
from core.constants import MARKETPLACE_AGENTS

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents/marketplace")
async def get_marketplace():
    return {"agents": MARKETPLACE_AGENTS}


@router.post("/agents")
async def create_agent(data: AgentCreate, user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=400, detail="Create a tenant first")
    tenant = tenant_result.data[0]

    agent_count = len(supabase.table("agents").select("id").eq("tenant_id", tenant["id"]).execute().data)
    if tenant["plan"] == "free" and agent_count >= 1:
        raise HTTPException(status_code=403, detail="Free plan allows only 1 agent. Upgrade to create more.")

    agent = {
        "tenant_id": tenant["id"],
        "name": data.name,
        "type": data.type,
        "description": data.description,
        "system_prompt": data.system_prompt,
        "status": "active",
        "language_mode": data.language_mode,
        "fixed_language": data.fixed_language,
        "personality": data.personality or {"tone": 0.6, "verbosity": 0.4, "emoji_usage": 0.3},
        "ai_config": {"model": "claude-sonnet", "temperature": 0.7, "max_tokens": 500},
        "stats": {"total_conversations": 0, "total_messages": 0, "resolution_rate": 0},
        "tone": data.tone,
        "emoji_level": data.emoji_level,
        "verbosity_level": data.verbosity_level,
        "escalation_rules": data.escalation_rules or {"keywords": ["atendente", "humano", "gerente", "reclamação"], "sentiment_threshold": 0.3},
        "follow_up_config": data.follow_up_config or {"enabled": False, "delay_hours": 24, "max_follow_ups": 3, "cool_down_days": 7},
        "knowledge_instructions": data.knowledge_instructions,
        "is_deployed": True,
        "marketplace_template_id": data.marketplace_template_id,
    }
    result = supabase.table("agents").insert(agent).execute()
    current_usage = tenant.get("usage", {})
    current_usage["agents_created"] = current_usage.get("agents_created", 0) + 1
    supabase.table("tenants").update({"usage": current_usage}).eq("id", tenant["id"]).execute()
    return result.data[0]


@router.get("/agents")
async def get_agents(user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("id").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        return {"agents": []}
    tenant_id = tenant_result.data[0]["id"]
    agents = supabase.table("agents").select("*").eq("tenant_id", tenant_id).execute()
    return {"agents": agents.data}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("id").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_id = tenant_result.data[0]["id"]
    result = supabase.table("agents").select("*").eq("id", agent_id).eq("tenant_id", tenant_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result.data[0]


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: AgentUpdate, user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("id").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_id = tenant_result.data[0]["id"]
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = supabase.table("agents").update(updates).eq("id", agent_id).eq("tenant_id", tenant_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "ok", "updated": updates}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant = tenant_result.data[0]
    result = supabase.table("agents").delete().eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    current_usage = tenant.get("usage", {})
    current_usage["agents_created"] = max(0, current_usage.get("agents_created", 0) - 1)
    supabase.table("tenants").update({"usage": current_usage}).eq("id", tenant["id"]).execute()
    return {"status": "ok"}


# --- Deploy Agent from Marketplace ---
@router.post("/agents/deploy")
async def deploy_marketplace_agent(data: DeployAgentRequest, user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=400, detail="Create a tenant first")
    tenant = tenant_result.data[0]

    agent_count = len(supabase.table("agents").select("id").eq("tenant_id", tenant["id"]).execute().data)
    if tenant["plan"] == "free" and agent_count >= 1:
        raise HTTPException(status_code=403, detail="Free plan allows only 1 agent. Upgrade to create more.")

    template = None
    for a in MARKETPLACE_AGENTS:
        if a["name"].lower() == data.template_name.lower():
            template = a
            break
    if not template:
        raise HTTPException(status_code=404, detail=f"Marketplace agent '{data.template_name}' not found")

    agent = {
        "tenant_id": tenant["id"],
        "name": data.custom_name or template["name"],
        "type": template["type"],
        "description": template["description"],
        "system_prompt": template["system_prompt"],
        "status": "active",
        "language_mode": "auto_detect",
        "fixed_language": "pt",
        "personality": template.get("personality", {}),
        "ai_config": {"model": "claude-sonnet", "temperature": 0.7, "max_tokens": 500},
        "stats": {"total_conversations": 0, "total_messages": 0, "resolution_rate": 0},
        "tone": data.tone,
        "emoji_level": data.emoji_level,
        "verbosity_level": data.verbosity_level,
        "escalation_rules": {"keywords": ["atendente", "humano", "gerente", "reclamação"], "sentiment_threshold": 0.3},
        "follow_up_config": {"enabled": False, "delay_hours": 24, "max_follow_ups": 3, "cool_down_days": 7},
        "knowledge_instructions": "",
        "is_deployed": True,
        "marketplace_template_id": template["name"],
    }
    result = supabase.table("agents").insert(agent).execute()

    current_usage = tenant.get("usage", {})
    current_usage["agents_created"] = current_usage.get("agents_created", 0) + 1
    supabase.table("tenants").update({"usage": current_usage}).eq("id", tenant["id"]).execute()
    return result.data[0]


# --- Knowledge Base ---
@router.get("/agents/{agent_id}/knowledge")
async def get_knowledge(agent_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = supabase.table("agent_knowledge").select("*").eq("agent_id", agent_id).order("created_at", desc=False).execute()
    return {"items": result.data}


@router.post("/agents/{agent_id}/knowledge")
async def add_knowledge(agent_id: str, data: KnowledgeCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    item = {"agent_id": agent_id, "type": data.type, "title": data.title, "content": data.content}
    result = supabase.table("agent_knowledge").insert(item).execute()
    return result.data[0]


@router.delete("/agents/{agent_id}/knowledge/{item_id}")
async def delete_knowledge(agent_id: str, item_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    supabase.table("agent_knowledge").delete().eq("id", item_id).eq("agent_id", agent_id).execute()
    return {"status": "ok"}


# --- Follow-up Rules ---
@router.get("/agents/{agent_id}/follow-up-rules")
async def get_follow_up_rules(agent_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = supabase.table("follow_up_rules").select("*").eq("agent_id", agent_id).execute()
    return {"rules": result.data}


@router.post("/agents/{agent_id}/follow-up-rules")
async def add_follow_up_rule(agent_id: str, data: FollowUpRuleCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    rule = {
        "agent_id": agent_id,
        "trigger_type": data.trigger_type,
        "delay_hours": data.delay_hours,
        "message_template": data.message_template,
        "is_active": data.is_active,
    }
    result = supabase.table("follow_up_rules").insert(rule).execute()
    return result.data[0]


@router.delete("/agents/{agent_id}/follow-up-rules/{rule_id}")
async def delete_follow_up_rule(agent_id: str, rule_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    supabase.table("follow_up_rules").delete().eq("id", rule_id).eq("agent_id", agent_id).execute()
    return {"status": "ok"}
