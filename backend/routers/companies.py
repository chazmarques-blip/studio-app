"""
Companies/Project Master Router - Organize projects under companies/brands
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timezone
from core.deps import supabase, get_current_user

router = APIRouter(prefix="/api/companies", tags=["companies"])

# Pydantic models
class CompanyCreate(BaseModel):
    name: str
    logo_url: Optional[str] = None
    folder_ids: Optional[List[str]] = []  # Associated character folders
    default_visual_style: Optional[str] = "animation"
    default_animation_sub: Optional[str] = "pixar_3d"
    default_format_strategy: Optional[str] = "safe_zone"
    default_language: Optional[str] = "pt"

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    logo_position: Optional[str] = None
    folder_ids: Optional[List[str]] = None
    default_visual_style: Optional[str] = None
    default_animation_sub: Optional[str] = None
    default_target_audience: Optional[str] = None
    default_character_folder_id: Optional[str] = None
    default_format_strategy: Optional[str] = None
    default_video_engine: Optional[str] = None
    default_target_duration: Optional[int] = None

@router.get("")
async def get_companies(user = Depends(get_current_user)):
    """Get all companies for current user"""
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    companies = result.data.get('settings', {}).get('companies', [])
    return {"companies": companies}

@router.post("")
async def create_company(data: CompanyCreate, user = Depends(get_current_user)):
    """Create a new company/project master"""
    company = {
        "id": str(uuid4()),
        "name": data.name,
        "logo_url": data.logo_url,
        "folder_ids": data.folder_ids or [],
        "default_settings": {
            "visual_style": data.default_visual_style,
            "animation_sub": data.default_animation_sub,
            "format_strategy": data.default_format_strategy,
            "language": data.default_language
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_count": 0
    }
    
    # Get current companies
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    companies = settings.get('companies', [])
    companies.append(company)
    settings['companies'] = companies
    
    # Update tenant
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return company

@router.put("/{company_id}")
async def update_company(company_id: str, data: CompanyUpdate, user = Depends(get_current_user)):
    """Update a company"""
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    companies = settings.get('companies', [])
    
    # Find and update company
    company_found = False
    for company in companies:
        if company['id'] == company_id:
            company_found = True
            if data.name is not None:
                company['name'] = data.name
            if data.logo_url is not None:
                company['logo_url'] = data.logo_url
            if data.logo_position is not None:
                company['logo_position'] = data.logo_position
            if data.folder_ids is not None:
                company['folder_ids'] = data.folder_ids
            
            # Initialize default_settings if it doesn't exist
            if 'default_settings' not in company:
                company['default_settings'] = {}
            
            # Update ALL default settings
            if data.default_visual_style is not None:
                company['default_settings']['visual_style'] = data.default_visual_style
            if data.default_animation_sub is not None:
                company['default_settings']['animation_sub'] = data.default_animation_sub
            if data.default_target_audience is not None:
                company['default_settings']['target_audience'] = data.default_target_audience
            if data.default_character_folder_id is not None:
                company['default_settings']['character_folder_id'] = data.default_character_folder_id
            if data.default_format_strategy is not None:
                company['default_settings']['format_strategy'] = data.default_format_strategy
            if data.default_video_engine is not None:
                company['default_settings']['video_engine'] = data.default_video_engine
            if data.default_target_duration is not None:
                company['default_settings']['target_duration'] = data.default_target_duration
            
            company['updated_at'] = datetime.now(timezone.utc).isoformat()
            break
    
    if not company_found:
        raise HTTPException(status_code=404, detail="Company not found")
    
    settings['companies'] = companies
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    print(f"✅ [COMPANY] Updated {company_id} with defaults: {company.get('default_settings', {})}")
    
    return {"success": True}

@router.delete("/{company_id}")
async def delete_company(company_id: str, user = Depends(get_current_user)):
    """Delete a company"""
    result = supabase.table('tenants').select('settings').eq('owner_id', user['id']).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    settings = result.data.get('settings', {})
    companies = settings.get('companies', [])
    companies = [c for c in companies if c['id'] != company_id]
    settings['companies'] = companies
    
    # Update tenant
    supabase.table('tenants').update({'settings': settings}).eq('owner_id', user['id']).execute()
    
    return {"success": True}
