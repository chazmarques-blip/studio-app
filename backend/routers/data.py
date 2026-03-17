"""
Data persistence router — Companies & Avatars stored in MongoDB.
Replaces localStorage with server-side persistence.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from pymongo import MongoClient
import os
import uuid

from core.deps import get_current_user, logger

router = APIRouter(prefix="/api/data", tags=["data"])

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "agentzz")
_mongo = MongoClient(MONGO_URL)
_db = _mongo[DB_NAME]
companies_col = _db["companies"]
avatars_col = _db["avatars"]

# Ensure indexes
companies_col.create_index("user_id")
avatars_col.create_index("user_id")


# ── Models ──

class CompanyIn(BaseModel):
    id: Optional[str] = None
    name: str
    phone: str = ""
    is_whatsapp: bool = True
    website_url: str = ""
    logo_url: str = ""
    is_primary: bool = False

class AvatarIn(BaseModel):
    id: Optional[str] = None
    url: str = ""
    name: str = ""
    source_photo_url: str = ""
    clothing: str = "company_uniform"
    voice: Optional[dict] = None
    angles: Optional[dict] = None
    video_url: Optional[str] = None


# ── Companies CRUD ──

@router.get("/companies")
async def list_companies(user=Depends(get_current_user)):
    docs = list(companies_col.find({"user_id": user["id"]}, {"_id": 0}))
    return docs

@router.post("/companies")
async def upsert_company(data: CompanyIn, user=Depends(get_current_user)):
    uid = user["id"]
    now = datetime.now(timezone.utc).isoformat()
    doc_id = data.id or uuid.uuid4().hex[:12]

    # If setting as primary, unset others
    if data.is_primary:
        companies_col.update_many({"user_id": uid}, {"$set": {"is_primary": False}})

    doc = {
        "id": doc_id,
        "user_id": uid,
        "name": data.name,
        "phone": data.phone,
        "is_whatsapp": data.is_whatsapp,
        "website_url": data.website_url,
        "logo_url": data.logo_url,
        "is_primary": data.is_primary,
        "updated_at": now,
    }

    existing = companies_col.find_one({"id": doc_id, "user_id": uid})
    if existing:
        companies_col.update_one({"id": doc_id, "user_id": uid}, {"$set": doc})
    else:
        doc["created_at"] = now
        companies_col.insert_one(doc)

    # Return without _id
    result = companies_col.find_one({"id": doc_id, "user_id": uid}, {"_id": 0})
    return result

@router.post("/companies/primary/{company_id}")
async def set_primary_company(company_id: str, user=Depends(get_current_user)):
    uid = user["id"]
    companies_col.update_many({"user_id": uid}, {"$set": {"is_primary": False}})
    companies_col.update_one({"id": company_id, "user_id": uid}, {"$set": {"is_primary": True}})
    return {"status": "ok"}

@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, user=Depends(get_current_user)):
    companies_col.delete_one({"id": company_id, "user_id": user["id"]})
    return {"status": "ok"}


# ── Avatars CRUD ──

@router.get("/avatars")
async def list_avatars(user=Depends(get_current_user)):
    docs = list(avatars_col.find({"user_id": user["id"]}, {"_id": 0}))
    return docs

@router.post("/avatars")
async def upsert_avatar(data: AvatarIn, user=Depends(get_current_user)):
    uid = user["id"]
    now = datetime.now(timezone.utc).isoformat()
    doc_id = data.id or uuid.uuid4().hex[:12]

    doc = {
        "id": doc_id,
        "user_id": uid,
        "url": data.url,
        "name": data.name,
        "source_photo_url": data.source_photo_url,
        "clothing": data.clothing,
        "voice": data.voice,
        "angles": data.angles,
        "video_url": data.video_url,
        "updated_at": now,
    }

    existing = avatars_col.find_one({"id": doc_id, "user_id": uid})
    if existing:
        avatars_col.update_one({"id": doc_id, "user_id": uid}, {"$set": doc})
    else:
        doc["created_at"] = now
        avatars_col.insert_one(doc)

    result = avatars_col.find_one({"id": doc_id, "user_id": uid}, {"_id": 0})
    return result

@router.delete("/avatars/{avatar_id}")
async def delete_avatar(avatar_id: str, user=Depends(get_current_user)):
    avatars_col.delete_one({"id": avatar_id, "user_id": user["id"]})
    return {"status": "ok"}

@router.delete("/avatars")
async def delete_all_avatars(user=Depends(get_current_user)):
    result = avatars_col.delete_many({"user_id": user["id"]})
    return {"status": "ok", "deleted": result.deleted_count}
