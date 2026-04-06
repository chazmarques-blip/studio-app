"""
Script para listar todos os avatares da pasta Biblizoo Baby
"""
from dotenv import load_dotenv
load_dotenv()

from core.deps import supabase
import json

# Buscar tenant do usuário test@studiox.com
user_result = supabase.table("users").select("*").eq("email", "test@studiox.com").execute()
if not user_result.data:
    print("Usuário não encontrado")
    exit(1)

user = user_result.data[0]
tenant_id = user.get("tenant_id")

if not tenant_id:
    print("Tenant não encontrado para o usuário")
    exit(1)

# Buscar tenant e settings
tenant_result = supabase.table("tenants").select("*").eq("id", tenant_id).execute()
if not tenant_result.data:
    print("Tenant não encontrado no banco")
    exit(1)

tenant = tenant_result.data[0]
settings = tenant.get("settings", {})
avatars = settings.get("studio_avatars", [])

# Buscar folders para encontrar a pasta "Biblizoo Baby"
folders = settings.get("avatar_folders", [])
biblizoo_folder = None
for folder in folders:
    if "biblizoo" in folder.get("name", "").lower() and "baby" in folder.get("name", "").lower():
        biblizoo_folder = folder
        break

if not biblizoo_folder:
    print("Pasta 'Biblizoo Baby' não encontrada!")
    print("\nPastas disponíveis:")
    for f in folders:
        print(f"  - {f.get('name')} (ID: {f.get('id')})")
    exit(1)

print(f"✅ Pasta encontrada: {biblizoo_folder['name']} (ID: {biblizoo_folder['id']})")
print(f"\nTotal de avatares no sistema: {len(avatars)}")

# Filtrar avatares da pasta Biblizoo
biblizoo_avatars = []
for avatar in avatars:
    folder_id = avatar.get("folder_id")
    if folder_id == biblizoo_folder["id"]:
        biblizoo_avatars.append(avatar)

print(f"Avatares na pasta 'Biblizoo Baby': {len(biblizoo_avatars)}\n")

# Mostrar detalhes
for i, avatar in enumerate(biblizoo_avatars, 1):
    print(f"{i}. ID: {avatar.get('id')}")
    print(f"   Nome: {avatar.get('name', 'SEM NOME')}")
    print(f"   URL: {avatar.get('url', 'SEM URL')[:80]}...")
    print(f"   Prompt: {avatar.get('prompt', 'SEM PROMPT')[:80]}...")
    print()

# Salvar em JSON para análise
output = {
    "folder_id": biblizoo_folder["id"],
    "folder_name": biblizoo_folder["name"],
    "total_avatars": len(biblizoo_avatars),
    "avatars": biblizoo_avatars
}

with open("/tmp/biblizoo_current_state.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Estado atual salvo em /tmp/biblizoo_current_state.json")
