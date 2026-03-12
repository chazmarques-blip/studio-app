from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime, timezone, timedelta
import jwt as pyjwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'agentflow-jwt-secret-key-2025-super-secure')
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
    timezone: Optional[str] = None


# --- Auth Routes ---
class SignUpRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class SignInRequest(BaseModel):
    email: str
    password: str

@api_router.post("/auth/signup")
async def signup(req: SignUpRequest):
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": req.email,
        "password_hash": pwd_context.hash(req.password),
        "full_name": req.full_name,
        "ui_language": "en",
        "company_name": "",
        "onboarding_completed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, req.email)
    return {
        "access_token": token,
        "user": {"id": user_id, "email": req.email, "full_name": req.full_name, "ui_language": "en", "onboarding_completed": False}
    }

@api_router.post("/auth/login")
async def login(req: SignInRequest):
    user = await db.users.find_one({"email": req.email})
    if not user or not pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["id"], user["email"])
    return {
        "access_token": token,
        "user": {
            "id": user["id"], "email": user["email"],
            "full_name": user.get("full_name", ""),
            "ui_language": user.get("ui_language", "en"),
            "company_name": user.get("company_name", ""),
            "onboarding_completed": user.get("onboarding_completed", False)
        }
    }

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
    return {"status": "ok", "service": "agentflow-api", "version": "0.1.0"}


# --- Profile / User ---
@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return user_doc

@api_router.put("/auth/profile")
async def update_profile(update: ProfileUpdate, user=Depends(get_current_user)):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one({"id": user["id"]}, {"$set": updates})
    return {"status": "ok", "updated": updates}


# --- Tenants ---
@api_router.post("/tenants")
async def create_tenant(data: TenantCreate, user=Depends(get_current_user)):
    # Check if user already has a tenant
    existing = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if existing:
        return existing

    tenant = {
        "id": str(uuid.uuid4()),
        "owner_id": user["id"],
        "name": data.name,
        "slug": data.slug or data.name.lower().replace(" ", "-"),
        "plan": "free",
        "plan_status": "active",
        "limits": {
            "agents": 1,
            "messages_period": "week",
            "messages_limit": 50,
            "channels": 1,
        },
        "usage": {
            "agents_created": 0,
            "messages_sent_this_period": 0,
            "period_start": datetime.now(timezone.utc).isoformat(),
        },
        "settings": {"timezone": "UTC"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tenants.insert_one({**tenant})
    # Remove _id from response
    return {k: v for k, v in tenant.items() if k != "_id"}

@api_router.get("/tenants")
async def get_tenant(user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found. Create one first.")
    return tenant


# --- Agents ---
MARKETPLACE_AGENTS = [
    {"name": "Carol", "type": "sales", "description": "AI-powered sales assistant. Handles inquiries, qualifies leads, and closes deals.", "personality": {"tone": 0.7, "verbosity": 0.5, "emoji_usage": 0.4}, "system_prompt": "You are Carol, a friendly and professional sales assistant. Help customers find products, answer questions, and guide them through the purchase process."},
    {"name": "Roberto", "type": "support", "description": "Technical support specialist. Resolves issues, guides troubleshooting, and escalates when needed.", "personality": {"tone": 0.5, "verbosity": 0.6, "emoji_usage": 0.2}, "system_prompt": "You are Roberto, a patient and knowledgeable technical support agent. Help customers resolve their technical issues step by step."},
    {"name": "Ana", "type": "scheduling", "description": "Appointment scheduling assistant. Manages calendars, books meetings, and sends reminders.", "personality": {"tone": 0.6, "verbosity": 0.3, "emoji_usage": 0.3}, "system_prompt": "You are Ana, an efficient scheduling assistant. Help customers book appointments, check availability, and manage their calendar."},
    {"name": "Lucas", "type": "sac", "description": "Customer service agent. Handles complaints, processes returns, and ensures satisfaction.", "personality": {"tone": 0.4, "verbosity": 0.5, "emoji_usage": 0.1}, "system_prompt": "You are Lucas, a professional customer service agent. Handle complaints with empathy, process returns, and ensure customer satisfaction."},
    {"name": "Marina", "type": "onboarding", "description": "Welcome and onboarding specialist. Guides new customers through first steps.", "personality": {"tone": 0.8, "verbosity": 0.6, "emoji_usage": 0.6}, "system_prompt": "You are Marina, a warm and enthusiastic onboarding specialist. Welcome new customers and guide them through their first steps."},
]

@api_router.get("/agents/marketplace")
async def get_marketplace():
    return {"agents": MARKETPLACE_AGENTS}

@api_router.post("/agents")
async def create_agent(data: AgentCreate, user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=400, detail="Create a tenant first")

    # Check agent limit
    agent_count = await db.agents.count_documents({"tenant_id": tenant["id"]})
    if tenant["plan"] == "free" and agent_count >= 1:
        raise HTTPException(status_code=403, detail="Free plan allows only 1 agent. Upgrade to create more.")

    agent = {
        "id": str(uuid.uuid4()),
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.agents.insert_one({**agent})
    # Update usage
    await db.tenants.update_one(
        {"id": tenant["id"]},
        {"$inc": {"usage.agents_created": 1}}
    )
    return {k: v for k, v in agent.items() if k != "_id"}

@api_router.get("/agents")
async def get_agents(user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        return {"agents": []}
    agents = await db.agents.find({"tenant_id": tenant["id"]}, {"_id": 0}).to_list(100)
    return {"agents": agents}

@api_router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    agent = await db.agents.find_one({"id": agent_id, "tenant_id": tenant["id"]}, {"_id": 0})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@api_router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, data: AgentUpdate, user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.agents.update_one(
        {"id": agent_id, "tenant_id": tenant["id"]},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "ok", "updated": updates}

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    result = await db.agents.delete_one({"id": agent_id, "tenant_id": tenant["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.tenants.update_one({"id": tenant["id"]}, {"$inc": {"usage.agents_created": -1}})
    return {"status": "ok"}


# --- Dashboard Stats ---
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    tenant = await db.tenants.find_one({"owner_id": user["id"]}, {"_id": 0})
    if not tenant:
        return {"messages_today": 0, "resolution_rate": 0, "active_leads": 0, "revenue": 0, "plan": "free", "messages_used": 0, "messages_limit": 50}

    agent_count = await db.agents.count_documents({"tenant_id": tenant["id"]})
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
