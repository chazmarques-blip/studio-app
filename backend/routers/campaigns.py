from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
import time

from core.deps import supabase, get_current_user, logger
from core.llm import DirectChat, DEFAULT_MODEL

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


# ── Models ──

class CampaignCreate(BaseModel):
    name: str
    type: str = "nurture"
    target_segment: Optional[dict] = {}
    messages: Optional[list] = []
    schedule: Optional[dict] = {}

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    target_segment: Optional[dict] = None
    messages: Optional[list] = None
    schedule: Optional[dict] = None

class StudioRequest(BaseModel):
    agent_type: str
    prompt: str
    context: Optional[dict] = {}
    session_id: Optional[str] = None

class CreativeCreate(BaseModel):
    campaign_id: Optional[str] = None
    type: str = "copy"
    title: str
    content: Optional[dict] = {}


# ── Helpers ──

async def _get_tenant(user):
    t = supabase.table("tenants").select("id, plan").eq("owner_id", user["id"]).execute()
    if not t.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t.data[0]


def _check_enterprise(plan: str):
    if plan != "enterprise":
        raise HTTPException(status_code=403, detail="Marketing AI Studio requires Enterprise plan. Upgrade to unlock.")


def _row_to_campaign(row):
    """Convert Supabase row to campaign response format"""
    metrics = row.get("metrics") or {}
    return {
        "id": row["id"],
        "tenant_id": row.get("tenant_id"),
        "name": row["name"],
        "type": metrics.get("type", "nurture"),
        "status": row.get("status", "draft"),
        "target_segment": metrics.get("target_segment", {}),
        "messages": metrics.get("messages", []),
        "schedule": metrics.get("schedule", {}),
        "stats": metrics.get("stats", {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0}),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


# ── Campaign CRUD ──

@router.get("")
async def list_campaigns(user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).order("created_at", desc=True).execute()
    return {"campaigns": [_row_to_campaign(r) for r in (result.data or [])]}


@router.post("")
async def create_campaign(data: CampaignCreate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    now = datetime.now(timezone.utc).isoformat()
    campaign = {
        "tenant_id": tenant["id"],
        "name": data.name,
        "status": "draft",
        "goal": data.type,
        "metrics": {
            "type": data.type,
            "target_segment": data.target_segment or {},
            "messages": data.messages or [],
            "schedule": data.schedule or {},
            "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0},
            "created_by": user["id"],
        },
    }
    result = supabase.table("campaigns").insert(campaign).execute()
    return _row_to_campaign(result.data[0])


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("campaigns").select("*").eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _row_to_campaign(result.data[0])


@router.put("/{campaign_id}")
async def update_campaign(campaign_id: str, data: CampaignUpdate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    current = supabase.table("campaigns").select("*").eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    existing_metrics = current.data[0].get("metrics") or {}
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if data.name is not None:
        updates["name"] = data.name
    if data.status is not None:
        updates["status"] = data.status
    if data.type is not None:
        existing_metrics["type"] = data.type
        updates["goal"] = data.type
    if data.target_segment is not None:
        existing_metrics["target_segment"] = data.target_segment
    if data.messages is not None:
        existing_metrics["messages"] = data.messages
    if data.schedule is not None:
        existing_metrics["schedule"] = data.schedule

    updates["metrics"] = existing_metrics
    result = supabase.table("campaigns").update(updates).eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _row_to_campaign(result.data[0])


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    supabase.table("creatives").delete().eq("campaign_id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    result = supabase.table("campaigns").delete().eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "deleted"}


@router.post("/{campaign_id}/activate")
async def activate_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("campaigns").update({
        "status": "active", "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "activated"}


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("campaigns").update({
        "status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "paused"}


class VideoUrlUpdate(BaseModel):
    video_url: str

@router.put("/{campaign_id}/video")
async def update_campaign_video(campaign_id: str, data: VideoUrlUpdate, user=Depends(get_current_user)):
    """Associate a video URL with a campaign's stats"""
    tenant = await _get_tenant(user)
    current = supabase.table("campaigns").select("*").eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    existing_metrics = current.data[0].get("metrics") or {}
    stats = existing_metrics.get("stats", {})
    stats["video_url"] = data.video_url
    existing_metrics["stats"] = stats
    result = supabase.table("campaigns").update({
        "metrics": existing_metrics,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", campaign_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Failed to update")
    return _row_to_campaign(result.data[0])


# ── Campaign Templates ──

CAMPAIGN_TEMPLATES = [
    {
        "id": "welcome_drip",
        "name": "Welcome Drip",
        "name_pt": "Boas-vindas Automaticas",
        "type": "drip",
        "description": "Automated welcome sequence for new leads",
        "description_pt": "Sequencia automatica de boas-vindas para novos leads",
        "messages": [
            {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Ola {{name}}! Bem-vindo(a) a {{company}}. Estamos felizes em te-lo conosco!"},
            {"step": 2, "delay_hours": 24, "channel": "whatsapp", "content": "Oi {{name}}, viu nossos recursos principais? Posso te ajudar a conhecer melhor!"},
            {"step": 3, "delay_hours": 72, "channel": "whatsapp", "content": "{{name}}, como esta sua experiencia? Estou aqui para qualquer duvida!"},
        ],
    },
    {
        "id": "reengagement",
        "name": "Re-engagement",
        "name_pt": "Reativacao de Leads",
        "type": "nurture",
        "description": "Win back inactive leads with targeted messages",
        "description_pt": "Reconquiste leads inativos com mensagens direcionadas",
        "messages": [
            {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Oi {{name}}, sentimos sua falta! Temos novidades que podem te interessar."},
            {"step": 2, "delay_hours": 48, "channel": "whatsapp", "content": "{{name}}, preparamos uma oferta especial para voce. Quer saber mais?"},
        ],
    },
    {
        "id": "post_sale",
        "name": "Post-Sale Follow-up",
        "name_pt": "Pos-Venda",
        "type": "nurture",
        "description": "Build loyalty with post-purchase engagement",
        "description_pt": "Construa fidelidade com engajamento pos-compra",
        "messages": [
            {"step": 1, "delay_hours": 24, "channel": "whatsapp", "content": "Ola {{name}}! Obrigado pela confianca. Como foi sua experiencia?"},
            {"step": 2, "delay_hours": 168, "channel": "whatsapp", "content": "{{name}}, tudo bem com seu produto/servico? Lembre-se que estamos aqui para ajudar!"},
        ],
    },
    {
        "id": "seasonal_promo",
        "name": "Seasonal Promotion",
        "name_pt": "Promocao Sazonal",
        "type": "promotional",
        "description": "Time-limited promotional campaign",
        "description_pt": "Campanha promocional por tempo limitado",
        "messages": [
            {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "{{name}}, preparamos algo especial para voce! Aproveite nossa promocao exclusiva."},
        ],
    },
]


@router.get("/templates/list")
async def list_templates(user=Depends(get_current_user)):
    return {"templates": CAMPAIGN_TEMPLATES}


# ── Creatives ──

@router.get("/creatives/list")
async def list_creatives(campaign_id: Optional[str] = None, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    query = supabase.table("creatives").select("*").eq("tenant_id", tenant["id"])
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    result = query.order("created_at", desc=True).limit(50).execute()
    return {"creatives": result.data or []}


@router.post("/creatives/save")
async def save_creative(data: CreativeCreate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    creative = {
        "tenant_id": tenant["id"],
        "campaign_id": data.campaign_id,
        "type": data.type,
        "title": data.title,
        "content": str(data.content) if data.content else "",
        "metadata": {"ai_metadata": {}, "content_data": data.content or {}},
        "status": "draft",
    }
    result = supabase.table("creatives").insert(creative).execute()
    return result.data[0]


@router.delete("/creatives/{creative_id}")
async def delete_creative(creative_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("creatives").delete().eq("id", creative_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Creative not found")
    return {"status": "deleted"}


# ── AI Studio Agents ──

STUDIO_AGENTS = {
    "copywriter": {
        "name": "Sofia Copywriter",
        "system": """You are Sofia, an expert AI copywriter for digital marketing campaigns. You write in the same language the user writes to you.
Your specialties:
- Social media posts (Instagram, Facebook, WhatsApp, LinkedIn)
- Ad copy (Google Ads, Meta Ads)
- Email marketing campaigns
- Landing page copy
- CTAs and headlines
Rules:
- Be creative, persuasive, and on-brand
- Always provide 2-3 variations
- Include emojis when appropriate for social media
- Keep text concise and action-oriented
- Suggest hashtags for social posts
- Format output clearly with headers for each variation"""
    },
    "designer": {
        "name": "Lucas Designer",
        "system": """You are Lucas, an expert AI visual concept designer. You write in the same language the user writes to you.
Your specialties:
- Creating detailed image prompts for AI image generation
- Visual brand concepts and mood boards
- Color palette suggestions
- Layout recommendations for social media posts
- Banner and ad creative descriptions
Rules:
- Provide detailed, specific visual descriptions
- Include colors, composition, mood, style references
- Suggest dimensions for different platforms (Instagram 1080x1080, Stories 1080x1920, Facebook 1200x630)
- Always provide 2-3 visual concept variations
- Reference modern design trends
- Format output clearly with concept name, description, and technical specs"""
    },
    "reviewer": {
        "name": "Ana Reviewer",
        "system": """You are Ana, an expert AI marketing content reviewer and strategist. You write in the same language the user writes to you.
Your specialties:
- Reviewing marketing copy for effectiveness
- Analyzing target audience alignment
- Checking brand voice consistency
- Improving conversion potential
- A/B test suggestions
Rules:
- Rate content on: Clarity (1-10), Persuasion (1-10), Brand Alignment (1-10), CTA Strength (1-10)
- Provide specific improvement suggestions
- Highlight strengths and weaknesses
- Suggest A/B testing variations
- Consider cultural and language nuances
- Format output with clear ratings and actionable feedback"""
    },
    "publisher": {
        "name": "Pedro Publisher",
        "system": """You are Pedro, an expert AI content scheduling and publishing strategist. You write in the same language the user writes to you.
Your specialties:
- Optimal posting times for each platform
- Content calendar planning
- Cross-platform adaptation
- Campaign scheduling strategies
- Audience engagement optimization
Rules:
- Recommend best posting times based on platform and audience
- Adapt content format for each channel (WhatsApp, Instagram, Facebook, Email)
- Create weekly/monthly content calendars
- Suggest frequency and cadence
- Include timezone considerations
- Format output as a clear schedule with dates, times, and platform-specific content"""
    },
}

studio_sessions = {}


@router.post("/studio/generate")
async def studio_generate(data: StudioRequest, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)

    agent_cfg = STUDIO_AGENTS.get(data.agent_type)
    if not agent_cfg:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {data.agent_type}")

    session_id = data.session_id or f"studio-{user['id']}-{data.agent_type}-{uuid.uuid4().hex[:8]}"

    if session_id not in studio_sessions:
        chat = DirectChat(system_message=agent_cfg["system"])
        studio_sessions[session_id] = chat
    else:
        chat = studio_sessions[session_id]

    context_str = ""
    if data.context:
        if data.context.get("company"):
            context_str += f"\nCompany: {data.context['company']}"
        if data.context.get("industry"):
            context_str += f"\nIndustry: {data.context['industry']}"
        if data.context.get("audience"):
            context_str += f"\nTarget audience: {data.context['audience']}"
        if data.context.get("brand_voice"):
            context_str += f"\nBrand voice: {data.context['brand_voice']}"
        if data.context.get("previous_content"):
            context_str += f"\nContent to review/improve:\n{data.context['previous_content']}"

    prompt = data.prompt
    if context_str:
        prompt = f"{prompt}\n\nContext:{context_str}"

    start = time.time()
    response = await chat.send_message(prompt)
    elapsed = round((time.time() - start) * 1000)

    return {
        "response": response,
        "agent": agent_cfg["name"],
        "session_id": session_id,
        "metadata": {
            "response_time_ms": elapsed,
            "model": "claude-sonnet-4-5",
            "agent_type": data.agent_type,
        }
    }


@router.delete("/studio/session/{session_id}")
async def clear_studio_session(session_id: str, user=Depends(get_current_user)):
    studio_sessions.pop(session_id, None)
    return {"status": "ok"}


# ── Seed Test Data ──

@router.post("/seed-test")
async def seed_test_campaigns(user=Depends(get_current_user)):
    """Seed test campaigns for AgentZZ demo"""
    tenant = await _get_tenant(user)
    tid = tenant["id"]

    existing = supabase.table("campaigns").select("id").eq("tenant_id", tid).execute()
    if existing.data and len(existing.data) > 0:
        return {"status": "already_seeded", "count": len(existing.data)}

    now = datetime.now(timezone.utc).isoformat()
    test_campaigns = [
        {
            "tenant_id": tid,
            "name": "Boas-vindas AgentZZ",
            "status": "active",
            "goal": "drip",
            "metrics": {
                "type": "drip",
                "target_segment": {"stages": ["new"], "temperatures": ["warm", "hot"]},
                "messages": [
                    {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Ola {{name}}! Bem-vindo ao AgentZZ. Estamos prontos para revolucionar seu atendimento com IA!"},
                    {"step": 2, "delay_hours": 24, "channel": "whatsapp", "content": "{{name}}, voce sabia que nossos agentes IA podem atender em 5 canais simultaneamente? Quer ver como funciona?"},
                    {"step": 3, "delay_hours": 72, "channel": "email", "content": "{{name}}, preparamos um guia exclusivo para voce tirar o maximo do AgentZZ. Confira!"},
                ],
                "schedule": {"send_time": "09:00", "timezone": "America/Sao_Paulo"},
                "stats": {"sent": 342, "delivered": 338, "opened": 215, "clicked": 89, "converted": 23},
                "created_by": user["id"],
            },
        },
        {
            "tenant_id": tid,
            "name": "Reativacao - Leads Frios",
            "status": "active",
            "goal": "nurture",
            "metrics": {
                "type": "nurture",
                "target_segment": {"stages": ["qualified"], "temperatures": ["cold"]},
                "messages": [
                    {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Oi {{name}}, sentimos sua falta! O AgentZZ evoluiu muito desde sua ultima visita."},
                    {"step": 2, "delay_hours": 48, "channel": "whatsapp", "content": "{{name}}, temos uma oferta exclusiva para voce voltar: 30 dias gratis no plano Pro!"},
                ],
                "schedule": {"send_time": "14:00", "timezone": "America/Sao_Paulo"},
                "stats": {"sent": 156, "delivered": 152, "opened": 98, "clicked": 45, "converted": 12},
                "created_by": user["id"],
            },
        },
        {
            "tenant_id": tid,
            "name": "Lancamento - Marketing AI Studio",
            "status": "draft",
            "goal": "promotional",
            "metrics": {
                "type": "promotional",
                "target_segment": {"stages": ["new", "qualified", "proposal"]},
                "messages": [
                    {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "{{name}}, o futuro do marketing chegou! Apresentamos o Marketing AI Studio do AgentZZ."},
                    {"step": 2, "delay_hours": 24, "channel": "instagram", "content": "4 agentes IA trabalhando 24h para criar suas campanhas. Descubra o Marketing AI Studio!"},
                    {"step": 3, "delay_hours": 48, "channel": "email", "content": "{{name}}, veja como empresas estao triplicando resultados com o Marketing AI Studio do AgentZZ."},
                ],
                "schedule": {"start_date": "2026-04-01", "end_date": "2026-04-30", "send_time": "10:00", "timezone": "America/Sao_Paulo"},
                "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0},
                "created_by": user["id"],
            },
        },
        {
            "tenant_id": tid,
            "name": "Pos-Venda Premium",
            "status": "paused",
            "goal": "nurture",
            "metrics": {
                "type": "nurture",
                "target_segment": {"stages": ["won"]},
                "messages": [
                    {"step": 1, "delay_hours": 24, "channel": "whatsapp", "content": "Obrigado por escolher o AgentZZ, {{name}}! Como posso ajudar na configuracao?"},
                    {"step": 2, "delay_hours": 168, "channel": "whatsapp", "content": "{{name}}, como esta indo com o AgentZZ? Tem alguma duvida? Estou aqui!"},
                ],
                "schedule": {"send_time": "11:00", "timezone": "America/Sao_Paulo"},
                "stats": {"sent": 89, "delivered": 87, "opened": 72, "clicked": 34, "converted": 8},
                "created_by": user["id"],
            },
        },
    ]

    campaign_ids = []
    for c in test_campaigns:
        result = supabase.table("campaigns").insert(c).execute()
        campaign_ids.append(result.data[0]["id"])

    # Creatives for the promotional campaign
    promo_id = campaign_ids[2]
    test_creatives = [
        {
            "tenant_id": tid,
            "campaign_id": promo_id,
            "type": "social_post",
            "title": "Post Instagram - AI Studio Launch",
            "content": "Seus agentes de marketing agora trabalham 24/7. Apresentamos o Marketing AI Studio: Copywriter, Designer, Reviewer e Publisher, todos potencializados por IA.",
            "metadata": {
                "content_data": {
                    "body": "Seus agentes de marketing agora trabalham 24/7.",
                    "cta": "Experimente gratis por 14 dias",
                    "platform": "instagram",
                    "hashtags": "#MarketingIA #AgentZZ #AutomacaoMarketing"
                },
                "ai_metadata": {"model": "claude-sonnet-4-5", "tokens_estimate": 85}
            },
            "status": "approved",
        },
        {
            "tenant_id": tid,
            "campaign_id": promo_id,
            "type": "copy",
            "title": "Email Copy - AI Studio Benefits",
            "content": "O Marketing AI Studio do AgentZZ reune 4 agentes especializados que criam, revisam e publicam conteudo automaticamente.",
            "metadata": {
                "content_data": {
                    "subject": "Seus concorrentes ja estao usando IA para marketing. E voce?",
                    "body": "O Marketing AI Studio do AgentZZ reune 4 agentes especializados.",
                    "cta": "Comecar agora"
                },
                "ai_metadata": {"model": "claude-sonnet-4-5", "tokens_estimate": 120}
            },
            "status": "draft",
        },
    ]

    for cr in test_creatives:
        supabase.table("creatives").insert(cr).execute()

    return {"status": "seeded", "campaigns": len(test_campaigns), "creatives": len(test_creatives)}
