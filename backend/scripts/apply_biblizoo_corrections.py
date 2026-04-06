"""
Script para aplicar correções nos avatares Biblizoo
Match os animais identificados com o JSON de referência e atualiza o banco
"""
import sys
sys.path.insert(0, '/app/backend')

import json
from dotenv import load_dotenv
load_dotenv()

from core.deps import supabase

# Carregar análise e referência
with open('/tmp/biblizoo_analysis_results.json', 'r', encoding='utf-8') as f:
    analysis = json.load(f)

with open('/tmp/biblizoo_parte1.json', 'r', encoding='utf-8') as f:
    parte1 = json.load(f)

# Criar dicionário de referência: animal_en -> dados
ref_dict = {}
for char in parte1:
    animal_key = char['animal_en'].lower()
    ref_dict[animal_key] = char
    # Adicionar variações
    if 'doe deer' in animal_key:
        ref_dict['fawn'] = char
        ref_dict['deer'] = char
    elif 'rhinoceros' in animal_key:
        ref_dict['rhino'] = char
    elif 'tortoise' in animal_key:
        ref_dict['turtle'] = char
        ref_dict['tortoise'] = char
    elif 'serpent' in animal_key or 'snake' in animal_key:
        ref_dict['snake'] = char
        ref_dict['lizard'] = char
        ref_dict['serpent'] = char

print("="*80)
print("APLICANDO CORREÇÕES NOS AVATARES BIBLIZOO")
print("="*80)

# Buscar avatares que precisam de correção
avatars_to_fix = []
for result in analysis:
    if result['status'] == 'SUCCESS' and not result.get('current_prompt'):
        avatars_to_fix.append(result)

print(f"\n✅ Encontrados {len(avatars_to_fix)} avatares para corrigir\n")

# Buscar usuário e tenant
user_result = supabase.table('users').select('*').eq('email', 'test@studiox.com').execute()
user = user_result.data[0]
tenant_id = user.get('tenant_id')

tenant_result = supabase.table('tenants').select('*').eq('id', tenant_id).execute()
tenant = tenant_result.data[0]
settings = tenant.get('settings', {})
avatars_list = settings.get('studio_avatars', [])

# Aplicar correções
corrections_applied = 0
corrections_log = []

for i, avatar_data in enumerate(avatars_to_fix, 1):
    avatar_id = avatar_data['id']
    avatar_name = avatar_data['name']
    identified_animal = avatar_data['identified_animal']
    
    print(f"\n{i}. {avatar_name} (ID: {avatar_id})")
    print(f"   Animal identificado: {identified_animal}")
    
    # Buscar correspondência no dicionário de referência
    if identified_animal in ref_dict:
        ref_data = ref_dict[identified_animal]
        correct_name = ref_data['nome']
        correct_prompt = ref_data['prompt']
        
        print(f"   ✅ Match encontrado: {correct_name}")
        print(f"   📝 Prompt: {correct_prompt[:80]}...")
        
        # Buscar avatar no array
        avatar_index = next((idx for idx, a in enumerate(avatars_list) if a.get('id') == avatar_id), None)
        
        if avatar_index is not None:
            # Atualizar prompt (manter o nome original)
            avatars_list[avatar_index]['prompt'] = correct_prompt
            
            corrections_log.append({
                'id': avatar_id,
                'old_name': avatar_name,
                'new_name': correct_name,
                'animal': identified_animal,
                'prompt_added': True
            })
            
            corrections_applied += 1
            print(f"   ✅ Atualizado no array")
        else:
            print(f"   ❌ Avatar não encontrado no array")
    else:
        print(f"   ⚠️  Nenhum match encontrado no dicionário de referência")
        print(f"   Chaves disponíveis: {list(ref_dict.keys())[:10]}...")

# Salvar de volta no Supabase
if corrections_applied > 0:
    print(f"\n{'='*80}")
    print(f"SALVANDO {corrections_applied} CORREÇÕES NO BANCO DE DADOS")
    print(f"{'='*80}\n")
    
    settings['studio_avatars'] = avatars_list
    
    try:
        result = supabase.table('tenants').update({
            'settings': settings
        }).eq('id', tenant_id).execute()
        
        print(f"✅ Correções salvas com sucesso!")
        
        # Salvar log
        with open('/tmp/biblizoo_corrections_log.json', 'w', encoding='utf-8') as f:
            json.dump(corrections_log, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 Log de correções salvo em: /tmp/biblizoo_corrections_log.json")
        
        print(f"\n{'='*80}")
        print(f"RESUMO DAS CORREÇÕES")
        print(f"{'='*80}\n")
        
        for correction in corrections_log:
            print(f"• {correction['old_name']} → {correction['new_name']}")
            print(f"  Animal: {correction['animal']}")
            print(f"  Prompt adicionado: ✅")
            print()
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
else:
    print(f"\n⚠️  Nenhuma correção aplicada")

print(f"\n{'='*80}")
print(f"✅ PROCESSO CONCLUÍDO!")
print(f"{'='*80}")
print(f"Total de correções aplicadas: {corrections_applied}/{len(avatars_to_fix)}")
