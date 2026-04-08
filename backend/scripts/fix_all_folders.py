#!/usr/bin/env python3
"""
Script para mover TODOS os personagens com tags conhecidas para as pastas corretas.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deps import supabase, logger
from datetime import datetime, timezone
import uuid as uuid_lib

def fix_all_folder_assignments():
    """Move avatars with known tags to correct folders."""
    
    # Known tags
    KNOWN_TAGS = [
        "Biblizoo Baby",
        "Biblis Ubaby",
        "Biblisub Baby",
        "BibleZoo",
    ]
    
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
            
            modified = False
            
            for tag in KNOWN_TAGS:
                # Find or create folder for this tag
                tag_folder = next((f for f in folders if f.get("name", "").lower() == tag.lower()), None)
                
                if not tag_folder:
                    # Create folder
                    now = datetime.now(timezone.utc).isoformat()
                    tag_folder = {
                        "id": uuid_lib.uuid4().hex[:12],
                        "name": tag,
                        "avatar_ids": [],
                        "created_at": now,
                        "updated_at": now,
                    }
                    folders.append(tag_folder)
                    logger.info(f"Created '{tag}' folder for tenant {tenant_id}")
                
                # Find avatars with this tag in name
                for avatar in avatars:
                    name = avatar.get("name", "")
                    if tag.lower() in name.lower():
                        current_folder = avatar.get("folder_id")
                        
                        if current_folder != tag_folder["id"]:
                            # Remove from old folder
                            if current_folder:
                                old_folder = next((f for f in folders if f.get("id") == current_folder), None)
                                if old_folder:
                                    avatar_ids = old_folder.get("avatar_ids", [])
                                    if avatar["id"] in avatar_ids:
                                        avatar_ids.remove(avatar["id"])
                                        old_folder["avatar_ids"] = avatar_ids
                            
                            # Add to new folder
                            avatar["folder_id"] = tag_folder["id"]
                            avatar_ids = tag_folder.get("avatar_ids", [])
                            if avatar["id"] not in avatar_ids:
                                avatar_ids.append(avatar["id"])
                                tag_folder["avatar_ids"] = avatar_ids
                            
                            modified = True
                            total_fixed += 1
                            logger.info(f"✅ Moved '{name}' to {tag} folder")
            
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
    print("Starting folder assignment migration...")
    print("This will move all avatars with known tags to correct folders")
    print("\nKnown tags:")
    print("  - Biblizoo Baby")
    print("  - Biblis Ubaby")
    print("  - Biblisub Baby")
    print("  - BibleZoo")
    print("\nProcessing...\n")
    
    fixed = fix_all_folder_assignments()
    print(f"\n✅ Done! Fixed {fixed} avatars")
