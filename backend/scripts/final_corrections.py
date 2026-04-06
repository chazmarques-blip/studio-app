"""
Correção final: Golias e Adão
"""
import sys
sys.path.insert(0, '/app/backend')

import json
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env do diretório correto
env_path = Path('/app/backend/.env')
load_dotenv(env_path)

from core.deps import supabase

print("="*80)
print("CORREÇÃO FINAL: GOLIAS E ADÃO")
print("="*80)

# Buscar usuário e tenant
user_result = supabase.table('users').select('*').eq('email', 'test@studiox.com').execute()
user = user_result.data[0]
tenant_id = user.get('tenant_id')

tenant_result = supabase.table('tenants').select('*').eq('id', tenant_id).execute()
tenant = tenant_result.data[0]
settings = tenant.get('settings', {})
avatars_list = settings.get('studio_avatars', [])

# Dados corretos
golias_prompt = "chibi 3D render of Golias Biblizoo, rhinoceros, front-facing standing pose, huge shiny black round eyes with bold intimidating light reflection, extra large oversized round head 55% of body height, VIVID deep electric purple-grey armored skin with bright orange horn, massive stocky body with tiny feet for comic contrast, wearing an ancient Philistine giant warrior mini outfit: full bright bronze scale armor covering chest in shiny overlapping gold and orange scales, bold red Philistine plumed helmet with vivid blue feather crest, bright crimson kilt with gold geometric border, bronze greaves on thick legs, enormous oversized bright gold spear in one hand, grumpy fierce expression, ultra-vibrant saturated colors, clean white background, soft warm studio lighting, child-friendly, ultra-detailed, 4k --ar 2:3 --v 6 --style raw --q 2"

adao_prompt = "chibi 3D render of Adão Biblizoo, noble deer, front-facing standing pose, huge shiny bright green round eyes with light reflection, oversized round head 50% of body height, VIVID warm chestnut-orange fur with bright cream belly, small green antler nubs with tiny lime green leaves, wearing a biblical Garden of Eden mini outfit: wide loincloth skirt of large stitched fig leaves in vivid emerald green and lime yellow layered together, bare small hooves, ultra-vibrant saturated colors, clean white background, soft warm studio lighting, child-friendly, ultra-detailed, 4k --ar 2:3 --v 6 --style raw --q 2"

corrections_made = []

# 1. Corrigir Golias
golias_id = "7a8640ee3009"
golias_index = next((idx for idx, a in enumerate(avatars_list) if a.get('id') == golias_id), None)

if golias_index is not None:
    avatars_list[golias_index]['prompt'] = golias_prompt
    print("\n✅ Golias Biblizoo Baby:")
    print(f"   ID: {golias_id}")
    print(f"   Prompt adicionado: {golias_prompt[:80]}...")
    corrections_made.append("Golias")
else:
    print("\n❌ Golias não encontrado")

# 2. Corrigir Adão (que recebeu prompt de Eva por engano)
adao_id = "e19dafbb0fe0"
adao_index = next((idx for idx, a in enumerate(avatars_list) if a.get('id') == adao_id), None)

if adao_index is not None:
    current_prompt = avatars_list[adao_index].get('prompt', '')
    if 'Eva Biblizoo' in current_prompt or 'doe deer' in current_prompt:
        avatars_list[adao_index]['prompt'] = adao_prompt
        print("\n✅ Adão Biblizoo:")
        print(f"   ID: {adao_id}")
        print(f"   Prompt CORRIGIDO (era de Eva/doe deer, agora é de Adão/noble deer)")
        print(f"   Novo prompt: {adao_prompt[:80]}...")
        corrections_made.append("Adão")
    else:
        print("\n⚠️  Adão já tem prompt correto")
        print(f"   Prompt atual: {current_prompt[:80] if current_prompt else 'VAZIO'}...")
else:
    print("\n❌ Adão não encontrado")

# Salvar
if corrections_made:
    settings['studio_avatars'] = avatars_list
    
    try:
        result = supabase.table('tenants').update({
            'settings': settings
        }).eq('id', tenant_id).execute()
        
        print(f"\n{'='*80}")
        print(f"✅ CORREÇÕES FINAIS SALVAS COM SUCESSO!")
        print(f"{'='*80}")
        print(f"Avatares corrigidos: {', '.join(corrections_made)}")
        
    except Exception as e:
        print(f"\n❌ Erro ao salvar: {e}")
else:
    print("\n⚠️  Nenhuma correção necessária")
