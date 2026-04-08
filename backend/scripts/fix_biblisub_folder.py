#!/usr/bin/env python3
"""
Script para mover personagens com "Biblisub Baby" no nome para a pasta correta.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deps import supabase, logger
from datetime import datetime, timezone

def fix_biblisub_avatars():
    """Move avatars with 'Biblisub Baby' to correct folder."""
    
    try:
        # Get all tenants
        tenants_response = supabase.table("tenants").select("*").execute()
        tenants = tenants_response.data or []
        
        logger.info(f"Processing {len(tenants)} tenants...")
        
        total_fixed = 0
        
        for tenant in tenants:
            tenant_id = tenant.get("id")
            settings = tenant.get("settings") or {}
            
            avatars = settings.get("studio_avatars", [])
            folders = settings.get("avatar_folders", [])
            
            # Find or create "Biblisub Baby" folder
            biblisub_folder = next((f for f in folders if f.get("name", "").lower() == "biblisub baby"), None)
            
            if not biblisub_folder:
                # Create folder
                import uuid
                now = datetime.now(timezone.utc).isoformat()
                biblisub_folder = {
                    "id": uuid.uuid4().hex[:12],
                    "name": "Biblisub Baby",
                    "avatar_ids": [],
                    "created_at": now,
                    "updated_at": now,
                }
                folders.append(biblisub_folder)
                logger.info(f"Created 'Biblisub Baby' folder for tenant {tenant_id}")
            
            # Find avatars with "Biblisub Baby" in name
            modified = False
            for avatar in avatars:
                name = avatar.get("name", "")
                if "biblisub baby" in name.lower():
                    current_folder = avatar.get("folder_id")
                    
                    if current_folder != biblisub_folder["id"]:
                        # Remove from old folder
                        if current_folder:
                            old_folder = next((f for f in folders if f.get("id") == current_folder), None)
                            if old_folder:
                                avatar_ids = old_folder.get("avatar_ids", [])
                                if avatar["id"] in avatar_ids:
                                    avatar_ids.remove(avatar["id"])
                                    old_folder["avatar_ids"] = avatar_ids
                        
                        # Add to new folder
                        avatar["folder_id"] = biblisub_folder["id"]
                        avatar_ids = biblisub_folder.get("avatar_ids", [])
                        if avatar["id"] not in avatar_ids:
                            avatar_ids.append(avatar["id"])
                            biblisub_folder["avatar_ids"] = avatar_ids
                        
                        modified = True
                        total_fixed += 1
                        logger.info(f"✅ Moved '{name}' to Biblisub Baby folder")
            
            if modified:
                # Save changes
                settings["studio_avatars"] = avatars
                settings["avatar_folders"] = folders
                
                supabase.table("tenants").update({
                    "settings": settings
                }).eq("id", tenant_id).execute()
                
                logger.info(f"Saved changes for tenant {tenant_id}")
        
        logger.info(f"✅ Migration complete! Fixed {total_fixed} avatars")
        return total_fixed
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    print("Starting Biblisub Baby folder migration...")
    fixed = fix_biblisub_avatars()
    print(f"✅ Done! Fixed {fixed} avatars")
