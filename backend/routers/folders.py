"""
Avatar Folders Router - Organize avatars into folders/projects
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone
from core.deps import supabase, get_current_user

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


class BulkFoldersUpdate(BaseModel):
    folders: List[dict]

@router.get("")
async def get_folders(user = Depends(get_current_user)):
    """Get all folders for current user"""
    # Get user's tenant from supabase
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    folders = result.data.get('settings', {}).get('avatar_folders', [])
    return {"folders": folders}

@router.post("")
async def create_folder(data: FolderCreate, user = Depends(get_current_user)):
    """Create a new folder"""
    folder = {
        "id": str(uuid4()),
        "name": data.name,
        "parent_id": data.parent_id,
        "color": data.color or "#8B5CF6",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "avatar_ids": []
    }
    
    # Get current folders
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    folders = settings.get('avatar_folders', [])
    folders.append(folder)
    settings['avatar_folders'] = folders
    
    # Update tenant
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return folder

@router.delete("/{folder_id}")
async def delete_folder(folder_id: str, user = Depends(get_current_user)):
    """Delete a folder"""
    # Get current folders
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    folders = settings.get('avatar_folders', [])
    folders = [f for f in folders if f['id'] != folder_id]
    settings['avatar_folders'] = folders
    
    # Update tenant
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return {"success": True}

@router.put("/bulk-update")
async def bulk_update_folders(data: BulkFoldersUpdate, user = Depends(get_current_user)):
    """Replace ALL folders atomically (avoids race conditions)"""
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    settings['avatar_folders'] = data.folders
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return {"success": True, "count": len(data.folders)}



@router.post("/assign-avatars")
async def assign_avatars_to_folder(data: AssignAvatarsToFolder, user = Depends(get_current_user)):
    """Assign multiple avatars to a folder"""
    # Get current folders
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    folders = settings.get('avatar_folders', [])
    
    # Find and update folder
    for folder in folders:
        if folder['id'] == data.folder_id:
            current_ids = set(folder.get('avatar_ids', []))
            current_ids.update(data.avatar_ids)
            folder['avatar_ids'] = list(current_ids)
            break
    
    settings['avatar_folders'] = folders
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return {"success": True, "assigned_count": len(data.avatar_ids)}


class UpdateFolderAvatars(BaseModel):
    folder_id: str
    avatar_ids: List[str]

@router.put("/update-avatars")
async def update_folder_avatars(data: UpdateFolderAvatars, user = Depends(get_current_user)):
    """Replace folder's avatar_ids entirely (used to clean stale IDs)"""
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    folders = settings.get('avatar_folders', [])
    
    for folder in folders:
        if folder['id'] == data.folder_id:
            folder['avatar_ids'] = data.avatar_ids
            break
    
    settings['avatar_folders'] = folders
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return {"success": True, "count": len(data.avatar_ids)}
