#!/usr/bin/env python3
"""
Remove duplicate avatars (keep only unique ones by URL).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deps import supabase, logger

def remove_duplicate_avatars():
    """Remove duplicate avatars based on URL."""
    
    try:
        # Get all tenants
        tenants_response = supabase.table("tenants").select("*").execute()
        tenants = tenants_response.data or []
        
        print(f"\n{'='*80}")
        print(f"Processing {len(tenants)} tenant(s)")
        print(f"{'='*80}\n")
        
        total_removed = 0
        
        for tenant in tenants:
            tenant_id = tenant.get("id")
            settings = tenant.get("settings") or {}
            
            avatars = settings.get("studio_avatars", [])
            original_count = len(avatars)
            
            print(f"🏢 Tenant {tenant_id}: {original_count} avatars")
            
            # Find duplicates by URL
            seen_urls = {}
            unique_avatars = []
            duplicates = []
            
            for avatar in avatars:
                url = avatar.get("url")
                avatar_id = avatar.get("id")
                name = avatar.get("name", "Unknown")
                
                if url and url in seen_urls:
                    # Duplicate found
                    duplicates.append({
                        "id": avatar_id,
                        "name": name,
                        "url": url
                    })
                    print(f"   ❌ Duplicate: {name} (ID: {avatar_id})")
                else:
                    # Unique avatar
                    seen_urls[url] = avatar_id
                    unique_avatars.append(avatar)
            
            if duplicates:
                # Remove duplicates from folder references
                folders = settings.get("avatar_folders", [])
                for folder in folders:
                    avatar_ids = folder.get("avatar_ids", [])
                    # Keep only unique avatar IDs
                    unique_ids = []
                    for aid in avatar_ids:
                        if aid not in [d["id"] for d in duplicates]:
                            unique_ids.append(aid)
                    folder["avatar_ids"] = unique_ids
                
                # Save changes
                settings["studio_avatars"] = unique_avatars
                settings["avatar_folders"] = folders
                
                supabase.table("tenants").update({
                    "settings": settings
                }).eq("id", tenant_id).execute()
                
                removed_count = len(duplicates)
                total_removed += removed_count
                
                print(f"   ✅ Removed {removed_count} duplicates")
                print(f"   📊 Before: {original_count} → After: {len(unique_avatars)}")
            else:
                print(f"   ✅ No duplicates found")
            
            print()
        
        print(f"{'='*80}")
        print(f"✅ Cleanup complete! Removed {total_removed} duplicate avatars")
        print(f"{'='*80}\n")
        return total_removed
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


if __name__ == "__main__":
    print("Starting duplicate avatar cleanup...")
    removed = remove_duplicate_avatars()
    print(f"✅ Done! Removed {removed} duplicates")
