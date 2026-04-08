#!/usr/bin/env python3
"""
Script para listar todos os personagens e suas pastas atuais.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deps import supabase, logger

def list_avatars():
    """List all avatars and their folders."""
    
    try:
        # Get all tenants
        tenants_response = supabase.table("tenants").select("*").execute()
        tenants = tenants_response.data or []
        
        print(f"\n{'='*80}")
        print(f"Found {len(tenants)} tenant(s)")
        print(f"{'='*80}\n")
        
        for tenant in tenants:
            tenant_id = tenant.get("id")
            settings = tenant.get("settings") or {}
            
            avatars = settings.get("studio_avatars", [])
            folders = settings.get("avatar_folders", [])
            
            print(f"\n🏢 TENANT: {tenant_id}")
            print(f"   Folders: {len(folders)}")
            print(f"   Avatars: {len(avatars)}")
            
            # List folders
            if folders:
                print(f"\n   📁 PASTAS:")
                for folder in folders:
                    avatar_count = len(folder.get("avatar_ids", []))
                    print(f"      - {folder.get('name')} (ID: {folder.get('id')}) - {avatar_count} personagens")
            
            # List avatars (last 20)
            if avatars:
                print(f"\n   👤 PERSONAGENS (últimos 20):")
                for avatar in avatars[-20:]:
                    folder_id = avatar.get("folder_id")
                    folder_name = "Sem Pasta"
                    
                    if folder_id:
                        folder = next((f for f in folders if f.get("id") == folder_id), None)
                        if folder:
                            folder_name = folder.get("name", "???")
                    
                    name = avatar.get("name", "Sem Nome")
                    print(f"      - {name:40s} → Pasta: {folder_name}")
            
            print(f"\n{'='*80}\n")
        
    except Exception as e:
        logger.error(f"Failed to list avatars: {e}")
        raise


if __name__ == "__main__":
    list_avatars()
