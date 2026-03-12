from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header, UploadFile, File, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import logging
import base64
import tempfile
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import jwt as pyjwt
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai import OpenAISpeechToText

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Supabase connection
supabase: Client = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_KEY']
)

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="AgentFlow API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Auth Helper ---
def create_token(user_id: str, email: str):
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"id": user_id, "email": email}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.PyJWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# --- Models ---
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    ui_language: Optional[str] = None


class SignUpRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class SignInRequest(BaseModel):
    email: str
    password: str


class TenantCreate(BaseModel):
    name: str
    slug: Optional[str] = None


class AgentCreate(BaseModel):
    name: str
    type: str = "custom"
    description: str = ""
    system_prompt: str = ""
    language_mode: str = "auto_detect"
    fixed_language: str = "en"
    personality: Optional[dict] = None
    tone: str = "professional"
    emoji_level: float = 0.3
    verbosity_level: float = 0.5
    escalation_rules: Optional[dict] = None
    follow_up_config: Optional[dict] = None
    knowledge_instructions: str = ""
    marketplace_template_id: str = ""


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[str] = None
    language_mode: Optional[str] = None
    fixed_language: Optional[str] = None
    personality: Optional[dict] = None
    tone: Optional[str] = None
    emoji_level: Optional[float] = None
    verbosity_level: Optional[float] = None
    escalation_rules: Optional[dict] = None
    follow_up_config: Optional[dict] = None
    knowledge_instructions: Optional[str] = None


class KnowledgeCreate(BaseModel):
    type: str = "faq"  # faq, product, policy, hours, custom
    title: str
    content: str


class FollowUpRuleCreate(BaseModel):
    trigger_type: str  # conversation_closed, inactive_24h, inactive_48h, post_sale, cart_abandoned
    delay_hours: int = 24
    message_template: str
    is_active: bool = True


class DeployAgentRequest(BaseModel):
    template_name: str  # marketplace agent name
    custom_name: Optional[str] = None
    tone: str = "professional"
    emoji_level: float = 0.3
    verbosity_level: float = 0.5


# --- Health ---
@api_router.get("/health")
async def health():
    return {"status": "ok", "service": "agentflow-api", "version": "0.2.0", "database": "supabase"}


# --- Auth Routes ---
@api_router.post("/auth/signup")
async def signup(req: SignUpRequest):
    existing = supabase.table("users").select("id").eq("email", req.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": req.email,
        "password_hash": pwd_context.hash(req.password),
        "full_name": req.full_name,
        "ui_language": "en",
        "company_name": "",
        "onboarding_completed": False,
    }
    result = supabase.table("users").insert(user_doc).execute()
    user = result.data[0]
    token = create_token(user["id"], req.email)
    return {
        "access_token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "ui_language": user["ui_language"],
            "onboarding_completed": False,
        }
    }


@api_router.post("/auth/login")
async def login(req: SignInRequest):
    result = supabase.table("users").select("*").eq("email", req.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user = result.data[0]
    if not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"], user["email"])
    return {
        "access_token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "ui_language": user.get("ui_language", "en"),
            "company_name": user.get("company_name", ""),
            "onboarding_completed": user.get("onboarding_completed", False),
        }
    }


# --- Profile / User ---
@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    result = supabase.table("users").select("id, email, full_name, ui_language, company_name, onboarding_completed, created_at").eq("id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]


@api_router.put("/auth/profile")
async def update_profile(update: ProfileUpdate, user=Depends(get_current_user)):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    if updates:
        supabase.table("users").update(updates).eq("id", user["id"]).execute()
    return {"status": "ok", "updated": updates}


# --- Tenants ---
@api_router.post("/tenants")
async def create_tenant(data: TenantCreate, user=Depends(get_current_user)):
    existing = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if existing.data:
        return existing.data[0]

    tenant = {
        "owner_id": user["id"],
        "name": data.name,
        "slug": data.slug or data.name.lower().replace(" ", "-"),
        "plan": "free",
        "plan_status": "active",
        "limits": {"agents": 1, "messages_period": "week", "messages_limit": 50, "channels": 1},
        "usage": {"agents_created": 0, "messages_sent_this_period": 0, "period_start": datetime.now(timezone.utc).isoformat()},
        "settings": {"timezone": "UTC"},
    }
    result = supabase.table("tenants").insert(tenant).execute()
    return result.data[0]


@api_router.get("/tenants")
async def get_tenant(user=Depends(get_current_user)):
    result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No tenant found. Create one first.")
    return result.data[0]


# --- Agents ---
MARKETPLACE_AGENTS = [
    {"name": "Carol", "type": "sales", "category": "general", "description": "AI-powered sales assistant. Handles inquiries, qualifies leads, and closes deals.", "personality": {"tone": 0.7, "verbosity": 0.5, "emoji_usage": 0.4}, "system_prompt": "You are Carol, a friendly and professional sales assistant.", "rating": 4.9},
    {"name": "Roberto", "type": "support", "category": "general", "description": "Technical support specialist. Resolves issues, guides troubleshooting, and escalates when needed.", "personality": {"tone": 0.5, "verbosity": 0.6, "emoji_usage": 0.2}, "system_prompt": "You are Roberto, a patient and knowledgeable technical support agent.", "rating": 4.8},
    {"name": "Ana", "type": "scheduling", "category": "general", "description": "Appointment scheduling assistant. Manages calendars, books meetings, and sends reminders.", "personality": {"tone": 0.6, "verbosity": 0.3, "emoji_usage": 0.3}, "system_prompt": "You are Ana, an efficient scheduling assistant.", "rating": 4.7},
    {"name": "Lucas", "type": "sac", "category": "general", "description": "Customer service agent. Handles complaints, processes returns, and ensures satisfaction.", "personality": {"tone": 0.4, "verbosity": 0.5, "emoji_usage": 0.1}, "system_prompt": "You are Lucas, a professional customer service agent.", "rating": 4.6},
    {"name": "Marina", "type": "onboarding", "category": "general", "description": "Welcome and onboarding specialist. Guides new customers through first steps.", "personality": {"tone": 0.8, "verbosity": 0.6, "emoji_usage": 0.6}, "system_prompt": "You are Marina, a warm onboarding specialist.", "rating": 4.8},
    {"name": "Sofia", "type": "sales", "category": "ecommerce", "description": "E-commerce sales expert. Recommends products, handles cart recovery, and processes orders.", "personality": {"tone": 0.7, "verbosity": 0.5, "emoji_usage": 0.5}, "system_prompt": "You are Sofia, an e-commerce sales specialist.", "rating": 4.9},
    {"name": "Pedro", "type": "support", "category": "ecommerce", "description": "Order tracking and returns specialist. Handles shipping inquiries and exchange requests.", "personality": {"tone": 0.5, "verbosity": 0.4, "emoji_usage": 0.2}, "system_prompt": "You are Pedro, an order support specialist.", "rating": 4.5},
    {"name": "Julia", "type": "sales", "category": "real_estate", "description": "Real estate assistant. Qualifies buyers, schedules property visits, and shares listings.", "personality": {"tone": 0.6, "verbosity": 0.6, "emoji_usage": 0.3}, "system_prompt": "You are Julia, a professional real estate assistant.", "rating": 4.7},
    {"name": "Rafael", "type": "scheduling", "category": "health", "description": "Medical scheduling assistant. Books appointments, sends reminders, and handles rescheduling.", "personality": {"tone": 0.4, "verbosity": 0.3, "emoji_usage": 0.1}, "system_prompt": "You are Rafael, a medical scheduling assistant.", "rating": 4.8},
    {"name": "Camila", "type": "support", "category": "health", "description": "Patient support agent. Answers health service questions, insurance inquiries, and exam preparation.", "personality": {"tone": 0.5, "verbosity": 0.5, "emoji_usage": 0.1}, "system_prompt": "You are Camila, a patient support specialist.", "rating": 4.6},
    {"name": "Diego", "type": "sales", "category": "restaurant", "description": "Restaurant ordering assistant. Takes orders, suggests menu items, and handles reservations.", "personality": {"tone": 0.8, "verbosity": 0.4, "emoji_usage": 0.6}, "system_prompt": "You are Diego, a friendly restaurant assistant.", "rating": 4.9},
    {"name": "Isabela", "type": "scheduling", "category": "beauty", "description": "Beauty salon scheduler. Books appointments, suggests services, and manages waitlists.", "personality": {"tone": 0.8, "verbosity": 0.4, "emoji_usage": 0.5}, "system_prompt": "You are Isabela, a beauty salon scheduling assistant.", "rating": 4.7},
    {"name": "Thiago", "type": "sales", "category": "automotive", "description": "Automotive sales assistant. Qualifies buyers, schedules test drives, and shares vehicle details.", "personality": {"tone": 0.6, "verbosity": 0.5, "emoji_usage": 0.2}, "system_prompt": "You are Thiago, an automotive sales specialist.", "rating": 4.5},
    {"name": "Fernanda", "type": "support", "category": "education", "description": "Educational support agent. Answers course questions, handles enrollments, and provides study guidance.", "personality": {"tone": 0.6, "verbosity": 0.6, "emoji_usage": 0.3}, "system_prompt": "You are Fernanda, an educational support specialist.", "rating": 4.8},
    {"name": "Gabriel", "type": "sales", "category": "finance", "description": "Financial services assistant. Explains products, qualifies leads, and schedules consultations.", "personality": {"tone": 0.4, "verbosity": 0.5, "emoji_usage": 0.1}, "system_prompt": "You are Gabriel, a financial services assistant.", "rating": 4.6},
    {"name": "Larissa", "type": "onboarding", "category": "saas", "description": "SaaS onboarding specialist. Guides new users through setup, features, and best practices.", "personality": {"tone": 0.7, "verbosity": 0.6, "emoji_usage": 0.4}, "system_prompt": "You are Larissa, a SaaS onboarding specialist.", "rating": 4.9},
    {"name": "Bruno", "type": "support", "category": "telecom", "description": "Telecom support agent. Handles billing, plan changes, and technical connectivity issues.", "personality": {"tone": 0.5, "verbosity": 0.5, "emoji_usage": 0.2}, "system_prompt": "You are Bruno, a telecom support agent.", "rating": 4.4},
    {"name": "Valentina", "type": "sales", "category": "travel", "description": "Travel booking assistant. Suggests destinations, books hotels, and creates itineraries.", "personality": {"tone": 0.8, "verbosity": 0.6, "emoji_usage": 0.5}, "system_prompt": "You are Valentina, a travel booking specialist.", "rating": 4.8},
    {"name": "Mateus", "type": "sac", "category": "logistics", "description": "Logistics support agent. Tracks shipments, handles delivery issues, and manages freight inquiries.", "personality": {"tone": 0.4, "verbosity": 0.4, "emoji_usage": 0.1}, "system_prompt": "You are Mateus, a logistics support specialist.", "rating": 4.5},
    {"name": "Amanda", "type": "sales", "category": "fitness", "description": "Fitness sales assistant. Sells gym memberships, personal training sessions, and promotes classes.", "personality": {"tone": 0.8, "verbosity": 0.5, "emoji_usage": 0.6}, "system_prompt": "You are Amanda, a fitness sales assistant.", "rating": 4.7},
    {"name": "Ricardo", "type": "support", "category": "legal", "description": "Legal services assistant. Schedules consultations, answers basic legal questions, and collects case info.", "personality": {"tone": 0.3, "verbosity": 0.5, "emoji_usage": 0.0}, "system_prompt": "You are Ricardo, a professional legal services assistant.", "rating": 4.6},
    {"name": "Beatriz", "type": "sales", "category": "events", "description": "Event planning assistant. Handles bookings, shares packages, and manages guest lists.", "personality": {"tone": 0.8, "verbosity": 0.5, "emoji_usage": 0.5}, "system_prompt": "You are Beatriz, an event planning assistant.", "rating": 4.8},
]


@api_router.get("/agents/marketplace")
async def get_marketplace():
    return {"agents": MARKETPLACE_AGENTS}


@api_router.post("/agents")
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
    # Update usage
    current_usage = tenant.get("usage", {})
    current_usage["agents_created"] = current_usage.get("agents_created", 0) + 1
    supabase.table("tenants").update({"usage": current_usage}).eq("id", tenant["id"]).execute()
    return result.data[0]


@api_router.get("/agents")
async def get_agents(user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("id").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        return {"agents": []}
    tenant_id = tenant_result.data[0]["id"]
    agents = supabase.table("agents").select("*").eq("tenant_id", tenant_id).execute()
    return {"agents": agents.data}


@api_router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user=Depends(get_current_user)):
    tenant_result = supabase.table("tenants").select("id").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_id = tenant_result.data[0]["id"]
    result = supabase.table("agents").select("*").eq("id", agent_id).eq("tenant_id", tenant_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result.data[0]


@api_router.put("/agents/{agent_id}")
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


@api_router.delete("/agents/{agent_id}")
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


# --- Dashboard Stats ---
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


# --- Channel Models ---
class ChannelCreate(BaseModel):
    type: str  # whatsapp, instagram, facebook, telegram
    config: Optional[dict] = None


# --- Conversation Models ---
class ConversationCreate(BaseModel):
    contact_name: str
    contact_phone: str = ""
    contact_email: str = ""
    channel_type: str = "whatsapp"
    agent_id: Optional[str] = None


class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    metadata: Optional[dict] = None


# --- Lead Models ---
class LeadCreate(BaseModel):
    name: str
    phone: str = ""
    email: str = ""
    company: str = ""
    conversation_id: Optional[str] = None
    stage: str = "new"
    value: float = 0


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    stage: Optional[str] = None
    score: Optional[int] = None
    value: Optional[float] = None
    assigned_to: Optional[str] = None


# --- Helper: get tenant ---
async def get_tenant(user):
    result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return result.data[0]


# --- Channels ---
@api_router.post("/channels")
async def create_channel(data: ChannelCreate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
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


@api_router.get("/channels")
async def list_channels(user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    result = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).execute()
    return {"channels": result.data}


@api_router.put("/channels/{channel_id}/status")
async def update_channel_status(channel_id: str, status: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    supabase.table("channels").update({"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", channel_id).eq("tenant_id", tenant["id"]).execute()
    return {"status": "ok"}


@api_router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    supabase.table("channels").delete().eq("id", channel_id).eq("tenant_id", tenant["id"]).execute()
    return {"status": "ok"}


# --- Conversations ---
@api_router.get("/conversations")
async def list_conversations(channel_type: Optional[str] = None, status: Optional[str] = None, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    query = supabase.table("conversations").select("*").eq("tenant_id", tenant["id"]).order("last_message_at", desc=True)
    if channel_type and channel_type != "all":
        query = query.eq("channel_type", channel_type)
    if status:
        query = query.eq("status", status)
    result = query.limit(50).execute()
    return {"conversations": result.data}


@api_router.post("/conversations")
async def create_conversation(data: ConversationCreate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    convo = {
        "tenant_id": tenant["id"],
        "contact_name": data.contact_name,
        "contact_phone": data.contact_phone,
        "contact_email": data.contact_email,
        "channel_type": data.channel_type,
        "agent_id": data.agent_id,
        "status": "active",
        "is_handoff": False,
        "language": "",
        "metadata": {},
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase.table("conversations").insert(convo).execute()
    return result.data[0]


@api_router.get("/conversations/{convo_id}")
async def get_conversation(convo_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    result = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result.data[0]


@api_router.get("/conversations/{convo_id}/messages")
async def get_messages(convo_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    # Verify conversation belongs to tenant
    convo = supabase.table("conversations").select("id").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).execute()
    return {"messages": msgs.data}


@api_router.post("/conversations/{convo_id}/messages")
async def send_message(convo_id: str, data: MessageCreate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = {
        "conversation_id": convo_id,
        "sender": "operator",
        "content": data.content,
        "message_type": data.message_type,
        "metadata": data.metadata or {},
    }
    result = supabase.table("messages").insert(msg).execute()
    # Update last_message_at
    supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

    # Update tenant message usage
    usage = tenant.get("usage", {})
    usage["messages_sent_this_period"] = usage.get("messages_sent_this_period", 0) + 1
    supabase.table("tenants").update({"usage": usage}).eq("id", tenant["id"]).execute()

    return result.data[0]


# --- Intelligent system prompt builder ---
def build_agent_system_prompt(agent: dict, knowledge_items: list = None) -> str:
    """Build a rich system prompt based on agent config, tone, and knowledge base"""
    name = agent.get("name", "Assistant")
    agent_type = agent.get("type", "support")
    tone = agent.get("tone", "professional")
    emoji_level = agent.get("emoji_level", 0.3)
    verbosity = agent.get("verbosity_level", 0.5)
    custom_prompt = agent.get("system_prompt", "")
    knowledge_text = agent.get("knowledge_instructions", "")
    escalation = agent.get("escalation_rules", {})

    tone_map = {
        "professional": "formal, respectful, and business-oriented",
        "friendly": "warm, approachable, and conversational",
        "empathetic": "understanding, caring, and emotionally supportive",
        "direct": "clear, concise, and straight to the point",
        "consultive": "advisory, asking questions to understand needs before suggesting solutions",
    }
    tone_desc = tone_map.get(tone, tone_map["professional"])

    emoji_desc = "Never use emojis." if emoji_level < 0.2 else "Use emojis sparingly." if emoji_level < 0.5 else "Use emojis frequently to be expressive."
    verbosity_desc = "Keep responses very short (1-2 sentences)." if verbosity < 0.3 else "Give moderate detail (2-3 sentences)." if verbosity < 0.7 else "Provide detailed, comprehensive responses."

    escalation_keywords = escalation.get("keywords", ["atendente", "humano", "gerente"])

    prompt = f"""You are {name}, a specialized {agent_type} assistant.

PERSONALITY & TONE:
- Your communication style is {tone_desc}
- {emoji_desc}
- {verbosity_desc}

LANGUAGE:
- ALWAYS respond in the same language the customer writes to you
- If Portuguese, respond in Portuguese. If English, respond in English. If Spanish, respond in Spanish.

ESCALATION RULES:
- If the customer mentions any of these words: {', '.join(escalation_keywords)}, or expresses strong frustration/anger, respond that you will transfer them to a human agent
- When escalating, be empathetic and assure them a human will help shortly
"""

    if custom_prompt:
        prompt += f"\nCUSTOM INSTRUCTIONS:\n{custom_prompt}\n"

    if knowledge_text:
        prompt += f"\nKNOWLEDGE BASE INSTRUCTIONS:\n{knowledge_text}\n"

    if knowledge_items:
        prompt += "\nKNOWLEDGE BASE (use this information to answer customer questions):\n"
        for item in knowledge_items:
            prompt += f"\n## {item.get('title', '')}\n{item.get('content', '')}\n"

    prompt += "\nIMPORTANT: Be natural and human-like. Never reveal you are an AI unless directly asked."
    return prompt


def check_escalation(content: str, agent: dict) -> bool:
    """Check if message should trigger escalation to human"""
    rules = agent.get("escalation_rules", {})
    keywords = rules.get("keywords", ["atendente", "humano", "gerente", "reclamação"])
    content_lower = content.lower()
    return any(kw.lower() in content_lower for kw in keywords)


# --- Webhook for incoming messages (WhatsApp/Evolution API) ---
@api_router.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict):
    """Receive incoming WhatsApp messages and auto-reply with AI agent"""
    logger.info(f"WhatsApp webhook received")
    try:
        event = payload.get("event", "")
        instance = payload.get("instance", "")
        data = payload.get("data", {})

        if event == "messages.upsert":
            message_data = data.get("message", {})
            from_number = data.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
            content = message_data.get("conversation", "") or message_data.get("extendedTextMessage", {}).get("text", "")
            is_from_me = data.get("key", {}).get("fromMe", False)

            if is_from_me or not content:
                return {"status": "ignored"}

            # Find channel/tenant
            channels = supabase.table("channels").select("*").eq("type", "whatsapp").eq("status", "connected").execute()
            channel = None
            for ch in channels.data:
                if ch.get("config", {}).get("instance_name") == instance:
                    channel = ch
                    break
            if not channel:
                return {"status": "no_channel"}

            tenant_id = channel["tenant_id"]

            # Find or create conversation
            existing = supabase.table("conversations").select("*").eq("tenant_id", tenant_id).eq("contact_phone", from_number).eq("status", "active").execute()
            if existing.data:
                convo = existing.data[0]
                convo_id = convo["id"]
            else:
                # Find a deployed agent for this tenant
                deployed = supabase.table("agents").select("id").eq("tenant_id", tenant_id).eq("is_deployed", True).eq("status", "active").limit(1).execute()
                agent_id = deployed.data[0]["id"] if deployed.data else None

                new_convo = {
                    "tenant_id": tenant_id,
                    "channel_id": channel["id"],
                    "agent_id": agent_id,
                    "contact_name": from_number,
                    "contact_phone": from_number,
                    "channel_type": "whatsapp",
                    "status": "active",
                    "last_message_at": datetime.now(timezone.utc).isoformat(),
                }
                convo_result = supabase.table("conversations").insert(new_convo).execute()
                convo = convo_result.data[0]
                convo_id = convo["id"]

            # Store incoming message
            msg = {
                "conversation_id": convo_id,
                "sender": "customer",
                "content": content,
                "message_type": "text",
                "metadata": {"from": from_number},
            }
            supabase.table("messages").insert(msg).execute()
            supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

            # --- AUTO-REPLY with AI if conversation has an agent and is not in handoff mode ---
            if convo.get("agent_id") and not convo.get("is_handoff"):
                agent_result = supabase.table("agents").select("*").eq("id", convo["agent_id"]).execute()
                if agent_result.data:
                    agent = agent_result.data[0]

                    # Check escalation
                    if check_escalation(content, agent):
                        supabase.table("conversations").update({"is_handoff": True}).eq("id", convo_id).execute()
                        escalation_msg = {
                            "conversation_id": convo_id,
                            "sender": "agent",
                            "content": "Entendo, vou transferir você para um atendente humano. Um momento, por favor.",
                            "message_type": "text",
                            "metadata": {"escalated": True, "agent_name": agent["name"]},
                        }
                        supabase.table("messages").insert(escalation_msg).execute()
                        return {"status": "escalated", "conversation_id": convo_id}

                    # Get knowledge base for agent
                    kb = supabase.table("agent_knowledge").select("*").eq("agent_id", agent["id"]).execute()
                    system_prompt = build_agent_system_prompt(agent, kb.data)

                    # Get recent messages for context
                    recent = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).limit(20).execute()

                    # Build AI conversation
                    session_id = f"auto-{convo_id}"
                    chat = LlmChat(
                        api_key=EMERGENT_KEY,
                        session_id=session_id,
                        system_message=system_prompt
                    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

                    # Replay context
                    for m in recent.data[:-1]:
                        if m["sender"] == "customer":
                            await chat.send_message(UserMessage(text=m["content"]))

                    # Generate response
                    ai_response = await chat.send_message(UserMessage(text=content))

                    # Store AI response
                    ai_msg = {
                        "conversation_id": convo_id,
                        "sender": "agent",
                        "content": ai_response,
                        "message_type": "text",
                        "metadata": {"model": "claude-sonnet-4-5", "agent_name": agent["name"], "auto_reply": True},
                    }
                    supabase.table("messages").insert(ai_msg).execute()

                    # Update stats
                    stats = agent.get("stats", {})
                    stats["total_messages"] = stats.get("total_messages", 0) + 1
                    supabase.table("agents").update({"stats": stats}).eq("id", agent["id"]).execute()

                    return {"status": "auto_replied", "conversation_id": convo_id, "response": ai_response}

            return {"status": "ok", "conversation_id": convo_id}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

    return {"status": "ok"}


@api_router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify():
    return {"status": "ok", "service": "agentflow-whatsapp-webhook"}


# --- Deploy Agent from Marketplace ---
@api_router.post("/agents/deploy")
async def deploy_marketplace_agent(data: DeployAgentRequest, user=Depends(get_current_user)):
    """Deploy a pre-built agent from marketplace to tenant"""
    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=400, detail="Create a tenant first")
    tenant = tenant_result.data[0]

    agent_count = len(supabase.table("agents").select("id").eq("tenant_id", tenant["id"]).execute().data)
    if tenant["plan"] == "free" and agent_count >= 1:
        raise HTTPException(status_code=403, detail="Free plan allows only 1 agent. Upgrade to create more.")

    # Find marketplace template
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
@api_router.get("/agents/{agent_id}/knowledge")
async def get_knowledge(agent_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    # Verify agent belongs to tenant
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = supabase.table("agent_knowledge").select("*").eq("agent_id", agent_id).order("created_at", desc=False).execute()
    return {"items": result.data}


@api_router.post("/agents/{agent_id}/knowledge")
async def add_knowledge(agent_id: str, data: KnowledgeCreate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    item = {"agent_id": agent_id, "type": data.type, "title": data.title, "content": data.content}
    result = supabase.table("agent_knowledge").insert(item).execute()
    return result.data[0]


@api_router.delete("/agents/{agent_id}/knowledge/{item_id}")
async def delete_knowledge(agent_id: str, item_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    supabase.table("agent_knowledge").delete().eq("id", item_id).eq("agent_id", agent_id).execute()
    return {"status": "ok"}


# --- Follow-up Rules ---
@api_router.get("/agents/{agent_id}/follow-up-rules")
async def get_follow_up_rules(agent_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    agent = supabase.table("agents").select("id").eq("id", agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = supabase.table("follow_up_rules").select("*").eq("agent_id", agent_id).execute()
    return {"rules": result.data}


@api_router.post("/agents/{agent_id}/follow-up-rules")
async def add_follow_up_rule(agent_id: str, data: FollowUpRuleCreate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
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


@api_router.delete("/agents/{agent_id}/follow-up-rules/{rule_id}")
async def delete_follow_up_rule(agent_id: str, rule_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    supabase.table("follow_up_rules").delete().eq("id", rule_id).eq("agent_id", agent_id).execute()
    return {"status": "ok"}


# --- Leads / CRM ---
@api_router.get("/leads")
async def list_leads(stage: Optional[str] = None, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    query = supabase.table("leads").select("*").eq("tenant_id", tenant["id"]).order("updated_at", desc=True)
    if stage:
        query = query.eq("stage", stage)
    result = query.execute()
    return {"leads": result.data}


@api_router.post("/leads")
async def create_lead(data: LeadCreate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
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


@api_router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    result = supabase.table("leads").select("*").eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result.data[0]


@api_router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, data: LeadUpdate, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = supabase.table("leads").update(updates).eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result.data[0]


@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant(user)
    supabase.table("leads").delete().eq("id", lead_id).eq("tenant_id", tenant["id"]).execute()
    return {"status": "ok"}


EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# In-memory store for sandbox sessions (not persisted - sandbox is for testing only)
sandbox_sessions: dict = {}


class SandboxMessage(BaseModel):
    content: str
    agent_name: str = "Carol"
    agent_type: str = "sales"
    system_prompt: str = ""
    session_id: Optional[str] = None
    language: str = "auto"


class AgentReplyRequest(BaseModel):
    conversation_id: str


# --- AI Sandbox (Test Agent with Real AI) ---
@api_router.post("/sandbox/chat")
async def sandbox_chat(data: SandboxMessage, user=Depends(get_current_user)):
    session_id = data.session_id or f"sandbox-{user['id']}-{uuid.uuid4().hex[:8]}"

    system = data.system_prompt or f"""You are {data.agent_name}, a professional {data.agent_type} assistant for a business.
You are friendly, helpful and concise. You respond in the same language the customer writes to you.
If the customer writes in Portuguese, respond in Portuguese. If in English, respond in English. If in Spanish, respond in Spanish.
Keep responses under 3 sentences unless more detail is needed."""

    if session_id not in sandbox_sessions:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=session_id,
            system_message=system
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        sandbox_sessions[session_id] = chat
    else:
        chat = sandbox_sessions[session_id]

    msg = UserMessage(text=data.content)
    import time
    start = time.time()
    response = await chat.send_message(msg)
    elapsed = round((time.time() - start) * 1000)

    # Simple language detection from response
    detected_lang = "en"
    pt_words = {"olá", "oi", "obrigado", "não", "sim", "como", "está", "bem", "bom", "você"}
    es_words = {"hola", "gracias", "no", "sí", "cómo", "está", "bien", "bueno", "usted"}
    words = set(response.lower().split()[:20])
    if words & pt_words:
        detected_lang = "pt"
    elif words & es_words:
        detected_lang = "es"

    return {
        "response": response,
        "session_id": session_id,
        "debug": {
            "response_time_ms": elapsed,
            "model": "claude-sonnet-4-5",
            "language_detected": detected_lang,
            "tokens_estimate": len(response.split()),
        }
    }


@api_router.delete("/sandbox/{session_id}")
async def clear_sandbox(session_id: str, user=Depends(get_current_user)):
    sandbox_sessions.pop(session_id, None)
    return {"status": "ok"}


# --- AI Agent Auto-Reply (for conversations) ---
@api_router.post("/conversations/{convo_id}/ai-reply")
async def ai_agent_reply(convo_id: str, user=Depends(get_current_user)):
    """Generate AI agent response for the last customer message in a conversation"""
    tenant = await get_tenant(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo = convo.data[0]

    # Get the agent assigned to this conversation
    agent = None
    if convo.get("agent_id"):
        agent_result = supabase.table("agents").select("*").eq("id", convo["agent_id"]).execute()
        if agent_result.data:
            agent = agent_result.data[0]

    agent_name = agent["name"] if agent else "Assistant"
    agent_type = agent["type"] if agent else "support"
    system_prompt = agent.get("system_prompt", "") if agent else ""

    if not system_prompt:
        system_prompt = f"""You are {agent_name}, a professional {agent_type} assistant.
You are friendly, helpful and concise. Respond in the same language the customer writes.
Keep responses under 3 sentences unless more detail is needed."""

    # Get recent messages for context
    msgs = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).limit(20).execute()

    # Build conversation context
    session_id = f"convo-{convo_id}"
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=session_id,
        system_message=system_prompt
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    # Replay recent messages to build context
    for m in msgs.data[:-1]:  # All except last
        if m["sender"] == "customer":
            await chat.send_message(UserMessage(text=m["content"]))

    # Send the last customer message to get AI response
    last_customer_msg = None
    for m in reversed(msgs.data):
        if m["sender"] == "customer":
            last_customer_msg = m["content"]
            break

    if not last_customer_msg:
        raise HTTPException(status_code=400, detail="No customer message to reply to")

    response = await chat.send_message(UserMessage(text=last_customer_msg))

    # Store AI response as message
    ai_msg = {
        "conversation_id": convo_id,
        "sender": "agent",
        "content": response,
        "message_type": "text",
        "metadata": {"model": "claude-sonnet-4-5", "agent_name": agent_name},
    }
    result = supabase.table("messages").insert(ai_msg).execute()
    supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

    # Update tenant usage
    usage = tenant.get("usage", {})
    usage["messages_sent_this_period"] = usage.get("messages_sent_this_period", 0) + 1
    supabase.table("tenants").update({"usage": usage}).eq("id", tenant["id"]).execute()

    return {
        "message": result.data[0],
        "response": response,
    }


# --- Image Analysis (Claude Vision) ---
@api_router.post("/ai/analyze-image")
async def analyze_image(
    image: UploadFile = File(None),
    image_base64: str = Form(None),
    prompt: str = Form("Describe this image in detail. If it contains text, transcribe it. If it's a product, describe features and condition."),
    language: str = Form("auto"),
    user=Depends(get_current_user)
):
    """Analyze an image using Claude Vision"""
    try:
        if image:
            content = await image.read()
            b64 = base64.b64encode(content).decode('utf-8')
        elif image_base64:
            b64 = image_base64
        else:
            raise HTTPException(status_code=400, detail="Provide image file or image_base64")

        img_content = ImageContent(image_base64=b64)

        lang_instruction = ""
        if language and language != "auto":
            lang_map = {"pt": "Portuguese", "es": "Spanish", "en": "English"}
            lang_instruction = f" Respond in {lang_map.get(language, language)}."

        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"vision-{uuid.uuid4().hex[:8]}",
            system_message=f"You are an image analysis assistant.{lang_instruction}"
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        msg = UserMessage(text=prompt, file_contents=[img_content])
        import time
        start = time.time()
        response = await chat.send_message(msg)
        elapsed = round((time.time() - start) * 1000)

        return {
            "analysis": response,
            "debug": {"response_time_ms": elapsed, "model": "claude-sonnet-4-5-vision"},
        }
    except Exception as e:
        logger.error(f"Vision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Audio Transcription (Whisper) ---
@api_router.post("/ai/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(None),
    audio_base64: str = Form(None),
    language: str = Form(None),
    user=Depends(get_current_user)
):
    """Transcribe audio using OpenAI Whisper"""
    try:
        stt = OpenAISpeechToText(api_key=EMERGENT_KEY)

        if audio:
            content = await audio.read()
            suffix = Path(audio.filename).suffix if audio.filename else '.mp3'
        elif audio_base64:
            content = base64.b64decode(audio_base64)
            suffix = '.mp3'
        else:
            raise HTTPException(status_code=400, detail="Provide audio file or audio_base64")

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            import time
            start = time.time()
            with open(tmp_path, "rb") as f:
                result = await stt.transcribe(
                    file=f,
                    model="whisper-1",
                    response_format="verbose_json",
                    language=language,
                )
            elapsed = round((time.time() - start) * 1000)

            return {
                "text": result.text,
                "language": getattr(result, 'language', language or 'unknown'),
                "duration": getattr(result, 'duration', None),
                "debug": {"response_time_ms": elapsed, "model": "whisper-1"},
            }
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Multi-Agent Orchestration ---
AGENT_TYPE_DESCRIPTIONS = {
    "sales": "handles product inquiries, pricing, promotions, and closing deals",
    "support": "resolves technical issues, troubleshooting, and general support",
    "scheduling": "manages appointments, calendar, bookings, and reminders",
    "sac": "handles complaints, returns, refunds, and customer satisfaction",
    "onboarding": "guides new customers through setup and first steps",
}


@api_router.post("/conversations/{convo_id}/route-agent")
async def route_to_best_agent(convo_id: str, user=Depends(get_current_user)):
    """Analyze conversation and route to the best specialized agent"""
    tenant = await get_tenant(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get recent messages
    msgs = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).limit(10).execute()
    if not msgs.data:
        raise HTTPException(status_code=400, detail="No messages in conversation")

    # Get all deployed agents
    agents = supabase.table("agents").select("*").eq("tenant_id", tenant["id"]).eq("is_deployed", True).execute()
    if not agents.data:
        raise HTTPException(status_code=400, detail="No deployed agents")

    if len(agents.data) == 1:
        return {"agent_id": agents.data[0]["id"], "agent_name": agents.data[0]["name"], "reason": "Only one agent deployed"}

    # Build context from last messages
    context = "\n".join([f"{m['sender']}: {m['content']}" for m in msgs.data[-5:]])

    # Ask AI to classify
    agent_list = "\n".join([f"- {a['name']} ({a['type']}): {AGENT_TYPE_DESCRIPTIONS.get(a['type'], a['type'])}" for a in agents.data])

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"router-{uuid.uuid4().hex[:8]}",
        system_message="You are a conversation router. Given a conversation context and available agents, respond with ONLY the agent name that best handles this conversation. No explanation."
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    prompt = f"Available agents:\n{agent_list}\n\nConversation:\n{context}\n\nWhich agent name should handle this?"
    best_name = (await chat.send_message(UserMessage(text=prompt))).strip()

    # Find matching agent
    selected = None
    for a in agents.data:
        if a["name"].lower() in best_name.lower():
            selected = a
            break
    if not selected:
        selected = agents.data[0]

    # Update conversation with new agent
    supabase.table("conversations").update({"agent_id": selected["id"]}).eq("id", convo_id).execute()

    return {"agent_id": selected["id"], "agent_name": selected["name"], "reason": f"Routed based on conversation context"}


# --- Conversation with image/audio support ---
@api_router.post("/conversations/{convo_id}/messages/multimedia")
async def send_multimedia_message(
    convo_id: str,
    content: str = Form(""),
    message_type: str = Form("text"),
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    user=Depends(get_current_user)
):
    """Send a message with optional image or audio attachment"""
    tenant = await get_tenant(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    final_content = content
    metadata = {}

    # Process audio -> transcribe
    if audio:
        audio_content = await audio.read()
        suffix = Path(audio.filename).suffix if audio.filename else '.mp3'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_content)
            tmp_path = tmp.name
        try:
            stt = OpenAISpeechToText(api_key=EMERGENT_KEY)
            with open(tmp_path, "rb") as f:
                result = await stt.transcribe(file=f, model="whisper-1", response_format="json")
            final_content = result.text
            message_type = "audio"
            metadata["transcription"] = result.text
            metadata["original_type"] = "audio"
        finally:
            os.unlink(tmp_path)

    # Process image -> analyze
    if image:
        img_content = await image.read()
        b64 = base64.b64encode(img_content).decode('utf-8')
        metadata["image_base64_preview"] = b64[:100]  # Store preview only
        metadata["has_image"] = True
        message_type = "image"
        if not content:
            final_content = "[Image sent]"

    # Store message
    msg = {
        "conversation_id": convo_id,
        "sender": "customer",
        "content": final_content,
        "message_type": message_type,
        "metadata": metadata,
    }
    result = supabase.table("messages").insert(msg).execute()
    supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

    return result.data[0]


# --- Include router ---
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
