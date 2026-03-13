from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from pymongo import MongoClient
import os
import uuid
import time

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

# MongoDB
_mongo = MongoClient(os.environ["MONGO_URL"])
_db = _mongo[os.environ["DB_NAME"]]
campaigns_col = _db["campaigns"]
creatives_col = _db["creatives"]

# Indexes
campaigns_col.create_index("tenant_id")
creatives_col.create_index("tenant_id")
creatives_col.create_index("campaign_id")


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
    agent_type: str  # copywriter, designer, reviewer, publisher
    prompt: str
    context: Optional[dict] = {}
    session_id: Optional[str] = None

class CreativeCreate(BaseModel):
    campaign_id: Optional[str] = None
    type: str = "copy"
    title: str
    content: dict = {}


# ── Helpers ──

async def _get_tenant(user):
    t = supabase.table("tenants").select("id, plan").eq("owner_id", user["id"]).execute()
    if not t.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t.data[0]


def _check_enterprise(plan: str):
    if plan not in ("enterprise",):
        raise HTTPException(status_code=403, detail="Marketing AI Studio requires Enterprise plan. Upgrade to unlock.")


def _doc(d):
    """Remove MongoDB _id from document"""
    if d and "_id" in d:
        del d["_id"]
    return d


# ── Campaign CRUD ──

@router.get("")
async def list_campaigns(user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    docs = list(campaigns_col.find({"tenant_id": tenant["id"]}).sort("created_at", -1))
    return {"campaigns": [_doc(d) for d in docs]}


@router.post("")
async def create_campaign(data: CampaignCreate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    campaign = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant["id"],
        "name": data.name,
        "type": data.type,
        "status": "draft",
        "target_segment": data.target_segment or {},
        "messages": data.messages or [],
        "schedule": data.schedule or {},
        "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0},
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    campaigns_col.insert_one(campaign)
    return _doc(campaign)


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    doc = campaigns_col.find_one({"id": campaign_id, "tenant_id": tenant["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _doc(doc)


@router.put("/{campaign_id}")
async def update_campaign(campaign_id: str, data: CampaignUpdate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = campaigns_col.update_one(
        {"id": campaign_id, "tenant_id": tenant["id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    doc = campaigns_col.find_one({"id": campaign_id})
    return _doc(doc)


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = campaigns_col.delete_one({"id": campaign_id, "tenant_id": tenant["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    creatives_col.delete_many({"campaign_id": campaign_id})
    return {"status": "deleted"}


@router.post("/{campaign_id}/activate")
async def activate_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = campaigns_col.update_one(
        {"id": campaign_id, "tenant_id": tenant["id"]},
        {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "activated"}


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = campaigns_col.update_one(
        {"id": campaign_id, "tenant_id": tenant["id"]},
        {"$set": {"status": "paused", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "paused"}


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
        "target_segment": {"stages": ["new"]},
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
        "target_segment": {"stages": ["qualified"], "temperatures": ["cold"]},
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
        "target_segment": {"stages": ["won"]},
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
        "target_segment": {"stages": ["new", "qualified"]},
    },
]


@router.get("/templates/list")
async def list_templates(user=Depends(get_current_user)):
    return {"templates": CAMPAIGN_TEMPLATES}


# ── Creatives ──

@router.get("/creatives/list")
async def list_creatives(campaign_id: Optional[str] = None, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    query = {"tenant_id": tenant["id"]}
    if campaign_id:
        query["campaign_id"] = campaign_id
    docs = list(creatives_col.find(query).sort("created_at", -1).limit(50))
    return {"creatives": [_doc(d) for d in docs]}


@router.post("/creatives/save")
async def save_creative(data: CreativeCreate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    creative = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant["id"],
        "campaign_id": data.campaign_id,
        "type": data.type,
        "title": data.title,
        "content": data.content,
        "ai_metadata": {},
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    creatives_col.insert_one(creative)
    return _doc(creative)


@router.delete("/creatives/{creative_id}")
async def delete_creative(creative_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = creatives_col.delete_one({"id": creative_id, "tenant_id": tenant["id"]})
    if result.deleted_count == 0:
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
    _check_enterprise(tenant["plan"])

    agent_cfg = STUDIO_AGENTS.get(data.agent_type)
    if not agent_cfg:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {data.agent_type}")

    session_id = data.session_id or f"studio-{user['id']}-{data.agent_type}-{uuid.uuid4().hex[:8]}"

    if session_id not in studio_sessions:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=session_id,
            system_message=agent_cfg["system"]
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
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
    response = await chat.send_message(UserMessage(text=prompt))
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

    existing = campaigns_col.count_documents({"tenant_id": tid})
    if existing > 0:
        return {"status": "already_seeded", "count": existing}

    now = datetime.now(timezone.utc).isoformat()
    test_campaigns = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "name": "Boas-vindas AgentZZ",
            "type": "drip",
            "status": "active",
            "target_segment": {"stages": ["new"], "temperatures": ["warm", "hot"]},
            "messages": [
                {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Ola {{name}}! Bem-vindo ao AgentZZ. Estamos prontos para revolucionar seu atendimento com IA!"},
                {"step": 2, "delay_hours": 24, "channel": "whatsapp", "content": "{{name}}, voce sabia que nossos agentes IA podem atender em 5 canais simultaneamente? Quer ver como funciona?"},
                {"step": 3, "delay_hours": 72, "channel": "email", "content": "{{name}}, preparamos um guia exclusivo para voce tirar o maximo do AgentZZ. Confira!"},
            ],
            "schedule": {"send_time": "09:00", "timezone": "America/Sao_Paulo"},
            "stats": {"sent": 342, "delivered": 338, "opened": 215, "clicked": 89, "converted": 23},
            "created_by": user["id"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "name": "Reativacao - Leads Frios",
            "type": "nurture",
            "status": "active",
            "target_segment": {"stages": ["qualified"], "temperatures": ["cold"]},
            "messages": [
                {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Oi {{name}}, sentimos sua falta! O AgentZZ evoluiu muito desde sua ultima visita."},
                {"step": 2, "delay_hours": 48, "channel": "whatsapp", "content": "{{name}}, temos uma oferta exclusiva para voce voltar: 30 dias gratis no plano Pro!"},
            ],
            "schedule": {"send_time": "14:00", "timezone": "America/Sao_Paulo"},
            "stats": {"sent": 156, "delivered": 152, "opened": 98, "clicked": 45, "converted": 12},
            "created_by": user["id"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "name": "Lancamento - Marketing AI Studio",
            "type": "promotional",
            "status": "draft",
            "target_segment": {"stages": ["new", "qualified", "proposal"]},
            "messages": [
                {"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "{{name}}, o futuro do marketing chegou! Apresentamos o Marketing AI Studio do AgentZZ."},
                {"step": 2, "delay_hours": 24, "channel": "instagram", "content": "4 agentes IA trabalhando 24h para criar suas campanhas. Descubra o Marketing AI Studio!"},
                {"step": 3, "delay_hours": 48, "channel": "email", "content": "{{name}}, veja como empresas estao triplicando resultados com o Marketing AI Studio do AgentZZ."},
            ],
            "schedule": {"start_date": "2026-04-01", "end_date": "2026-04-30", "send_time": "10:00", "timezone": "America/Sao_Paulo"},
            "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0},
            "created_by": user["id"],
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "name": "Pos-Venda Premium",
            "type": "nurture",
            "status": "paused",
            "target_segment": {"stages": ["won"]},
            "messages": [
                {"step": 1, "delay_hours": 24, "channel": "whatsapp", "content": "Obrigado por escolher o AgentZZ, {{name}}! Como posso ajudar na configuracao?"},
                {"step": 2, "delay_hours": 168, "channel": "whatsapp", "content": "{{name}}, como esta indo com o AgentZZ? Tem alguma duvida? Estou aqui!"},
            ],
            "schedule": {"send_time": "11:00", "timezone": "America/Sao_Paulo"},
            "stats": {"sent": 89, "delivered": 87, "opened": 72, "clicked": 34, "converted": 8},
            "created_by": user["id"],
            "created_at": now,
            "updated_at": now,
        },
    ]

    test_creatives = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "campaign_id": test_campaigns[2]["id"],
            "type": "social_post",
            "title": "Post Instagram - AI Studio Launch",
            "content": {
                "body": "Seus agentes de marketing agora trabalham 24/7. Apresentamos o Marketing AI Studio: Copywriter, Designer, Reviewer e Publisher, todos potencializados por IA.",
                "cta": "Experimente gratis por 14 dias",
                "platform": "instagram",
                "hashtags": "#MarketingIA #AgentZZ #AutomacaoMarketing"
            },
            "ai_metadata": {"model": "claude-sonnet-4-5", "tokens_estimate": 85},
            "status": "approved",
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tid,
            "campaign_id": test_campaigns[2]["id"],
            "type": "copy",
            "title": "Email Copy - AI Studio Benefits",
            "content": {
                "subject": "Seus concorrentes ja estao usando IA para marketing. E voce?",
                "body": "O Marketing AI Studio do AgentZZ reune 4 agentes especializados que criam, revisam e publicam conteudo automaticamente. Resultados reais: 3x mais engajamento, 60% menos tempo de producao.",
                "cta": "Comecar agora"
            },
            "ai_metadata": {"model": "claude-sonnet-4-5", "tokens_estimate": 120},
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        },
    ]

    for c in test_campaigns:
        campaigns_col.insert_one(c.copy())
    for cr in test_creatives:
        creatives_col.insert_one(cr.copy())

    return {"status": "seeded", "campaigns": len(test_campaigns), "creatives": len(test_creatives)}
