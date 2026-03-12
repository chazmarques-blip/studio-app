from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import jwt as pyjwt
from passlib.context import CryptContext

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


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    status: Optional[str] = None
    language_mode: Optional[str] = None
    fixed_language: Optional[str] = None
    personality: Optional[dict] = None


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


# --- Include router ---
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
