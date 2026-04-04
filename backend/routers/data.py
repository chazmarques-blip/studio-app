"""
Data persistence router — Companies & Avatars stored in Supabase.
Uses the tenants table's 'settings' JSONB column for structured storage.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from core.deps import supabase, get_current_user, get_current_tenant, logger

router = APIRouter(prefix="/api/data", tags=["data"])


# ── Models ──

class CompanyIn(BaseModel):
    id: Optional[str] = None
    name: str
    phone: str = ""
    is_whatsapp: bool = True
    website_url: str = ""
    logo_url: str = ""
    is_primary: bool = False
    product_description: str = ""
    profile_type: str = "company"
    facebook_url: str = ""
    instagram_url: str = ""
    tiktok_url: str = ""

class AvatarIn(BaseModel):
    id: Optional[str] = None
    url: str = ""
    name: str = ""
    source_photo_url: str = ""
    clothing: str = "company_uniform"
    voice: Optional[dict] = None
    angles: Optional[dict] = None
    video_url: Optional[str] = None
    language: str = "pt"
    edit_history: Optional[list] = None
    avatar_style: str = "realistic"
    creation_mode: str = "photo"


def _get_settings(tenant_id: str) -> dict:
    """Read current settings from tenant (via project cache for consistency)."""
    from core.cache import project_cache
    return project_cache.get_settings(tenant_id)


def _save_settings(tenant_id: str, settings: dict):
    """Save settings to tenant (via project cache for consistency)."""
    from core.cache import project_cache
    project_cache.save_settings(tenant_id, settings)


# ── Companies CRUD ──

@router.get("/companies")
async def list_companies(user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    return settings.get("studio_companies", [])


@router.post("/companies")
async def upsert_company(data: CompanyIn, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    companies = settings.get("studio_companies", [])
    now = datetime.now(timezone.utc).isoformat()
    doc_id = data.id or uuid.uuid4().hex[:12]

    # If setting as primary, unset others
    if data.is_primary:
        for c in companies:
            c["is_primary"] = False

    doc = {
        "id": doc_id,
        "name": data.name,
        "phone": data.phone,
        "is_whatsapp": data.is_whatsapp,
        "website_url": data.website_url,
        "logo_url": data.logo_url,
        "is_primary": data.is_primary,
        "product_description": data.product_description,
        "profile_type": data.profile_type,
        "facebook_url": data.facebook_url,
        "instagram_url": data.instagram_url,
        "tiktok_url": data.tiktok_url,
        "updated_at": now,
    }

    existing_idx = next((i for i, c in enumerate(companies) if c.get("id") == doc_id), None)
    if existing_idx is not None:
        doc["created_at"] = companies[existing_idx].get("created_at", now)
        companies[existing_idx] = doc
    else:
        doc["created_at"] = now
        companies.append(doc)

    settings["studio_companies"] = companies
    _save_settings(tenant["id"], settings)
    return doc


@router.post("/companies/primary/{company_id}")
async def set_primary_company(company_id: str, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    companies = settings.get("studio_companies", [])
    for c in companies:
        c["is_primary"] = (c.get("id") == company_id)
    settings["studio_companies"] = companies
    _save_settings(tenant["id"], settings)
    return {"status": "ok"}


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    companies = settings.get("studio_companies", [])
    companies = [c for c in companies if c.get("id") != company_id]
    settings["studio_companies"] = companies
    _save_settings(tenant["id"], settings)
    return {"status": "ok"}


# ── Avatars CRUD ──

@router.get("/avatars")
async def list_avatars(user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    return settings.get("studio_avatars", [])


@router.post("/avatars")
async def upsert_avatar(data: AvatarIn, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    avatars = settings.get("studio_avatars", [])
    now = datetime.now(timezone.utc).isoformat()
    doc_id = data.id or uuid.uuid4().hex[:12]

    doc = {
        "id": doc_id,
        "url": data.url,
        "name": data.name,
        "source_photo_url": data.source_photo_url,
        "clothing": data.clothing,
        "voice": data.voice,
        "angles": data.angles,
        "video_url": data.video_url,
        "language": data.language,
        "edit_history": data.edit_history or [],
        "avatar_style": data.avatar_style,
        "creation_mode": data.creation_mode,
        "updated_at": now,
    }

    existing_idx = next((i for i, a in enumerate(avatars) if a.get("id") == doc_id), None)
    if existing_idx is not None:
        doc["created_at"] = avatars[existing_idx].get("created_at", now)
        avatars[existing_idx] = doc
    else:
        doc["created_at"] = now
        avatars.append(doc)

    settings["studio_avatars"] = avatars
    _save_settings(tenant["id"], settings)
    return doc




@router.delete("/avatars/{avatar_id}/history/{entry_index}")
async def delete_avatar_history_entry(avatar_id: str, entry_index: int, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    """Delete a specific edit history entry from an avatar."""
    settings = _get_settings(tenant["id"])
    avatars = settings.get("studio_avatars", [])
    avatar = next((a for a in avatars if a.get("id") == avatar_id), None)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    history = avatar.get("edit_history", [])
    if entry_index < 0 or entry_index >= len(history):
        raise HTTPException(status_code=400, detail="Invalid history index")
    history.pop(entry_index)
    avatar["edit_history"] = history
    settings["studio_avatars"] = avatars
    _save_settings(tenant["id"], settings)
    return {"status": "ok", "edit_history": history}


@router.delete("/avatars/{avatar_id}")
async def delete_avatar(avatar_id: str, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    """Delete a specific avatar by ID"""
    settings = _get_settings(tenant["id"])
    avatars = settings.get("studio_avatars", [])
    
    existing_idx = next((i for i, a in enumerate(avatars) if a.get("id") == avatar_id), None)
    if existing_idx is None:
        raise HTTPException(status_code=404, detail=f"Avatar {avatar_id} not found")
    
    deleted = avatars.pop(existing_idx)
    settings["studio_avatars"] = avatars
    _save_settings(tenant["id"], settings)
    return {"status": "ok", "deleted": deleted["name"], "id": avatar_id}


@router.delete("/avatars")
async def delete_all_avatars(user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    count = len(settings.get("studio_avatars", []))
    settings["studio_avatars"] = []
    _save_settings(tenant["id"], settings)
    return {"status": "ok", "deleted": count}
