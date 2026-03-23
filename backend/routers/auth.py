from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from core.deps import supabase, create_token, get_current_user, get_tenant as get_tenant_helper, pwd_context
from core.models import ProfileUpdate, SignUpRequest, SignInRequest, TenantCreate

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/signup")
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


@router.post("/auth/login")
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
            "avatar_url": user.get("avatar_url"),
        }
    }


@router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    result = supabase.table("users").select("id, email, full_name, ui_language, company_name, onboarding_completed, created_at").eq("id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = result.data[0]
    # Get avatar from tenant settings
    tenant = supabase.table("tenants").select("settings").eq("owner_id", user["id"]).execute()
    if tenant.data:
        settings = tenant.data[0].get("settings", {}) or {}
        user_data["avatar_url"] = settings.get("avatar_url")
    return user_data


@router.put("/auth/profile")
async def update_profile(update: ProfileUpdate, user=Depends(get_current_user)):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    if updates:
        supabase.table("users").update(updates).eq("id", user["id"]).execute()
    return {"status": "ok", "updated": updates}


# --- Tenants ---
@router.post("/tenants")
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


@router.get("/tenants")
async def get_tenant(user=Depends(get_current_user)):
    result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No tenant found. Create one first.")
    return result.data[0]
