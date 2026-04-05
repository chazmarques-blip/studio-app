"""
Avatar Folders Router - Organize avatars into folders/projects
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone
from core.auth import get_current_user_id

router = APIRouter(prefix="/api/folders", tags=["folders"])

# Pydantic models
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = "#8B5CF6"

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None

class AssignAvatarsToFolder(BaseModel):
    avatar_ids: List[str]
    folder_id: str

@router.get("")
async def get_folders(user_id: str = Depends(get_current_user_id)):
    """Get all folders for current user"""
    from core.db import get_db
    db = await get_db()
    
    # Get user's tenant
    tenant = await db.tenants.find_one({"owner_id": user_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    folders = tenant.get("settings", {}).get("avatar_folders", [])
    return {"folders": folders}

@router.post("")
async def create_folder(data: FolderCreate, user_id: str = Depends(get_current_user_id)):
    """Create a new folder"""
    from core.db import get_db
    db = await get_db()
    
    folder = {
        "id": str(uuid4()),
        "name": data.name,
        "parent_id": data.parent_id,
        "color": data.color or "#8B5CF6",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "avatar_ids": []
    }
    
    # Update tenant settings
    result = await db.tenants.update_one(
        {"owner_id": user_id},
        {"$push": {"settings.avatar_folders": folder}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return folder

@router.put("/{folder_id}")
async def update_folder(folder_id: str, data: FolderUpdate, user_id: str = Depends(get_current_user_id)):
    """Update folder name, parent, or color"""
    from core.db import get_db
    db = await get_db()
    
    update_fields = {}
    if data.name is not None:
        update_fields["settings.avatar_folders.$.name"] = data.name
    if data.parent_id is not None:
        update_fields["settings.avatar_folders.$.parent_id"] = data.parent_id
    if data.color is not None:
        update_fields["settings.avatar_folders.$.color"] = data.color
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.tenants.update_one(
        {"owner_id": user_id, "settings.avatar_folders.id": folder_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {"success": True}

@router.delete("/{folder_id}")
async def delete_folder(folder_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a folder"""
    from core.db import get_db
    db = await get_db()
    
    result = await db.tenants.update_one(
        {"owner_id": user_id},
        {"$pull": {"settings.avatar_folders": {"id": folder_id}}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {"success": True}

@router.post("/assign-avatars")
async def assign_avatars_to_folder(data: AssignAvatarsToFolder, user_id: str = Depends(get_current_user_id)):
    """Assign multiple avatars to a folder"""
    from core.db import get_db
    db = await get_db()
    
    # Add avatar IDs to folder's avatar_ids array (avoiding duplicates)
    result = await db.tenants.update_one(
        {"owner_id": user_id, "settings.avatar_folders.id": data.folder_id},
        {"$addToSet": {"settings.avatar_folders.$.avatar_ids": {"$each": data.avatar_ids}}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {"success": True, "assigned_count": len(data.avatar_ids)}

@router.post("/remove-avatars")
async def remove_avatars_from_folder(data: AssignAvatarsToFolder, user_id: str = Depends(get_current_user_id)):
    """Remove avatars from a folder"""
    from core.db import get_db
    db = await get_db()
    
    result = await db.tenants.update_one(
        {"owner_id": user_id, "settings.avatar_folders.id": data.folder_id},
        {"$pullAll": {"settings.avatar_folders.$.avatar_ids": data.avatar_ids}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return {"success": True}
