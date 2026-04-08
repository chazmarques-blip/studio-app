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


def _auto_detect_folder_from_name(avatar_name: str, existing_folders: list) -> Optional[str]:
    """
    Auto-detect folder based on avatar name extension/tag.
    
    Examples:
        "Pescocinho Biblizoo Baby" → finds/creates "Biblizoo Baby" folder
        "Jonas Biblizoo Baby" → finds/creates "Biblizoo Baby" folder
    
    Returns folder_id if match found, or tag name to create folder.
    """
    if not avatar_name or len(avatar_name) < 5:
        return None
    
    # Common folder tags/extensions (case-insensitive)
    common_tags = [
        "Biblizoo Baby",
        "BibleZoo",
    ]
    
    # Check if name contains a known tag
    name_lower = avatar_name.lower()
    for tag in common_tags:
        if tag.lower() in name_lower:
            # Find existing folder
            folder = next((f for f in existing_folders if f.get("name", "").lower() == tag.lower()), None)
            if folder:
                logger.info(f"Avatar '{avatar_name}' auto-assigned to folder '{tag}' ({folder['id']})")
                return folder["id"]
            # Tag found but folder doesn't exist - return tag to create
            logger.info(f"Avatar '{avatar_name}' will create folder '{tag}'")
            return f"CREATE:{tag}"
    
    # Extract last 2 words as potential tag
    words = avatar_name.strip().split()
    if len(words) >= 3:
        potential_tag = " ".join(words[-2:])
        
        # Check if looks like a tag (capitalized)
        if potential_tag[0].isupper():
            folder = next((f for f in existing_folders if f.get("name", "").lower() == potential_tag.lower()), None)
            if folder:
                logger.info(f"Avatar '{avatar_name}' auto-assigned to folder '{potential_tag}'")
                return folder["id"]
            # Potential tag found
            return f"CREATE:{potential_tag}"
    
    return None


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
    
    # ── Project Defaults (NEW) ──
    default_visual_style: Optional[str] = None
    default_animation_sub: Optional[str] = None
    default_target_audience: Optional[str] = None
    default_character_folder_id: Optional[str] = None
    default_format_strategy: Optional[str] = None
    default_video_engine: Optional[str] = None
    default_target_duration: Optional[int] = None

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
    prompt: str = ""
    folder_id: Optional[str] = None  # ✅ ADDED: For folder organization  # Prompt usado para gerar o personagem


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
        # Project Defaults
        "default_visual_style": data.default_visual_style,
        "default_animation_sub": data.default_animation_sub,
        "default_target_audience": data.default_target_audience,
        "default_character_folder_id": data.default_character_folder_id,
        "default_format_strategy": data.default_format_strategy,
        "default_video_engine": data.default_video_engine,
        "default_target_duration": data.default_target_duration,
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
    """
    List all avatars for current tenant
    
    On first access, auto-seeds official Biblizoo Baby avatars if tenant has no avatars
    """
    settings = _get_settings(tenant["id"])
    avatars = settings.get("studio_avatars", [])
    
    # Auto-seed official avatars if tenant has none
    if len(avatars) == 0:
        logger.info(f"Tenant {tenant['id']}: No avatars found, seeding official avatars...")
        avatars = _seed_official_avatars(tenant["id"])
    
    return avatars


def _seed_official_avatars(tenant_id: str) -> list:
    """
    Seed official Biblizoo Baby avatars for new tenants
    
    Returns list of seeded avatars
    """
    # Check if there's a master tenant with official avatars
    # For now, return empty list - will be implemented with migration
    logger.info(f"Seeding official avatars for tenant {tenant_id} (not implemented yet)")
    return []



@router.post("/avatars")
async def upsert_avatar(data: AvatarIn, user=Depends(get_current_user), tenant=Depends(get_current_tenant)):
    settings = _get_settings(tenant["id"])
    avatars = settings.get("studio_avatars", [])
    folders = settings.get("avatar_folders", [])
    now = datetime.now(timezone.utc).isoformat()
    doc_id = data.id or uuid.uuid4().hex[:12]

    # ✅ AUTO-DETECT folder from name extension
    folder_id = data.folder_id
    if not folder_id and data.name:
        auto_folder = _auto_detect_folder_from_name(data.name, folders)
        if auto_folder:
            if auto_folder.startswith("CREATE:"):
                # Create new folder
                folder_name = auto_folder.replace("CREATE:", "")
                new_folder_id = uuid.uuid4().hex[:12]
                new_folder = {
                    "id": new_folder_id,
                    "name": folder_name,
                    "avatar_ids": [],
                    "created_at": now,
                    "updated_at": now,
                }
                folders.append(new_folder)
                settings["avatar_folders"] = folders
                folder_id = new_folder_id
                logger.info(f"✅ Created folder '{folder_name}' ({new_folder_id}) for avatar '{data.name}'")
            else:
                # Use existing folder
                folder_id = auto_folder

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
        "prompt": data.prompt,
        "folder_id": folder_id,  # ✅ Assign to folder
        "updated_at": now,
    }

    existing_idx = next((i for i, a in enumerate(avatars) if a.get("id") == doc_id), None)
    if existing_idx is not None:
        doc["created_at"] = avatars[existing_idx].get("created_at", now)
        avatars[existing_idx] = doc
    else:
        doc["created_at"] = now
        avatars.append(doc)

    # ✅ Update folder's avatar_ids
    if folder_id:
        folder = next((f for f in folders if f.get("id") == folder_id), None)
        if folder:
            avatar_ids = folder.get("avatar_ids", [])
            if doc_id not in avatar_ids:
                avatar_ids.append(doc_id)
                folder["avatar_ids"] = avatar_ids
                folder["updated_at"] = now
                settings["avatar_folders"] = folders

    settings["studio_avatars"] = avatars
    _save_settings(tenant["id"], settings)
    
    # Auto-sync character library for affected projects
    _trigger_character_library_sync(tenant["id"], folder_id)
    
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




def _trigger_character_library_sync(tenant_id: str, folder_id: Optional[str]):
    """
    Trigger character library sync for projects using this folder
    
    Called when:
    - Avatar is added/updated in a folder
    - Avatar folder_id is changed
    
    This updates the character_library in all projects that use this folder.
    """
    if not folder_id:
        return  # Avatar not in any folder
    
    try:
        from services.character_library_service import CharacterLibraryService
        
        # Get settings
        settings = _get_settings(tenant_id)
        
        # Get all projects
        projects = settings.get("studio_projects", [])
        
        # Get folder info
        folders = settings.get("avatar_folders", [])
        folder = next((f for f in folders if f.get("id") == folder_id), None)
        
        if not folder:
            return
        
        # Get avatars in this folder
        all_avatars = settings.get("studio_avatars", [])
        folder_avatars = [a for a in all_avatars if a.get("folder_id") == folder_id]
        
        # Update character library for each project using this folder
        updated_count = 0
        for project in projects:
            # Check if project uses this folder
            existing_lib = project.get("character_library")
            if existing_lib and existing_lib.get("folder_id") == folder_id:
                # Re-sync character library
                new_library = CharacterLibraryService.build_character_library(
                    folder_id=folder_id,
                    folder_name=folder["name"],
                    avatars=folder_avatars
                )
                project["character_library"] = new_library
                updated_count += 1
                logger.info(f"Auto-synced character library for project {project.get('id')}")
        
        if updated_count > 0:
            settings["studio_projects"] = projects
            _save_settings(tenant_id, settings)
            logger.info(f"Auto-sync: Updated {updated_count} projects with new character library")
    
    except Exception as e:
        # Don't fail the avatar save if sync fails
        logger.error(f"Failed to auto-sync character library: {e}")
