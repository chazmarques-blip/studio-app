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
        "company_name": req.company_name or "",
        "onboarding_completed": False,
    }
    result = supabase.table("users").insert(user_doc).execute()
    user = result.data[0]
    token = create_token(user["id"], req.email)

    # Create tenant with extended profile fields in settings
    tenant_settings = {"timezone": "UTC"}
    if req.birth_date:
        tenant_settings["birth_date"] = req.birth_date
    if req.phone:
        tenant_settings["phone"] = req.phone
    if req.preferred_contact:
        tenant_settings["preferred_contact"] = req.preferred_contact
    tenant_doc = {
        "owner_id": user["id"],
        "name": req.full_name,
        "slug": req.email.split("@")[0].lower().replace(" ", "-"),
        "plan": "free",
        "plan_status": "active",
        "limits": {"agents": 1, "messages_period": "week", "messages_limit": 50, "channels": 1},
        "usage": {"agents_created": 0, "messages_sent_this_period": 0},
        "settings": tenant_settings,
    }
    supabase.table("tenants").insert(tenant_doc).execute()

    return {
        "access_token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "ui_language": user["ui_language"],
            "birth_date": req.birth_date or "",
            "phone": req.phone or "",
            "preferred_contact": req.preferred_contact or "whatsapp",
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

    # Get extended profile from tenant settings
    tenant = supabase.table("tenants").select("settings").eq("owner_id", user["id"]).execute()
    settings = {}
    if tenant.data:
        settings = tenant.data[0].get("settings", {}) or {}

    return {
        "access_token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "ui_language": user.get("ui_language", "en"),
            "company_name": user.get("company_name", ""),
            "birth_date": settings.get("birth_date", ""),
            "phone": settings.get("phone", ""),
            "preferred_contact": settings.get("preferred_contact", "whatsapp"),
            "onboarding_completed": user.get("onboarding_completed", False),
            "avatar_url": settings.get("avatar_url"),
        }
    }


@router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    result = supabase.table("users").select("id, email, full_name, ui_language, company_name, onboarding_completed, created_at").eq("id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = result.data[0]
    # Get avatar and extended profile from tenant settings
    tenant = supabase.table("tenants").select("settings").eq("owner_id", user["id"]).execute()
    if tenant.data:
        settings = tenant.data[0].get("settings", {}) or {}
        user_data["avatar_url"] = settings.get("avatar_url")
        user_data["birth_date"] = settings.get("birth_date", "")
        user_data["phone"] = settings.get("phone", "")
        user_data["preferred_contact"] = settings.get("preferred_contact", "whatsapp")
    return user_data


@router.put("/auth/profile")
async def update_profile(update: ProfileUpdate, user=Depends(get_current_user)):
    # Standard user fields (columns in users table)
    user_fields = {}
    if update.full_name is not None:
        user_fields["full_name"] = update.full_name
    if update.company_name is not None:
        user_fields["company_name"] = update.company_name
    if update.ui_language is not None:
        user_fields["ui_language"] = update.ui_language
    if update.onboarding_completed is not None:
        user_fields["onboarding_completed"] = update.onboarding_completed

    if user_fields:
        supabase.table("users").update(user_fields).eq("id", user["id"]).execute()

    # Extended profile fields stored in tenant settings
    extra_fields = {}
    if update.birth_date is not None:
        extra_fields["birth_date"] = update.birth_date
    if update.phone is not None:
        extra_fields["phone"] = update.phone
    if update.preferred_contact is not None:
        extra_fields["preferred_contact"] = update.preferred_contact

    if extra_fields:
        tenant = supabase.table("tenants").select("id, settings").eq("owner_id", user["id"]).execute()
        if tenant.data:
            settings = tenant.data[0].get("settings", {}) or {}
            settings.update(extra_fields)
            supabase.table("tenants").update({"settings": settings}).eq("id", tenant.data[0]["id"]).execute()

    return {"status": "ok", "updated": {**user_fields, **extra_fields}}


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
