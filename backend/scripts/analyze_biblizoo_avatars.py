"""
Script para analisar visualmente os avatares Biblizoo e corrigir os prompts
Usa Gemini Vision para identificar o animal em cada imagem
"""
import sys
sys.path.insert(0, '/app/backend')

import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

from core.deps import supabase
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import os
import requests
import base64

# Carregar dados de referência
with open('/tmp/biblizoo_parte1.json', 'r', encoding='utf-8') as f:
    parte1 = json.load(f)

print(f"✅ Carregados {len(parte1)} personagens da Parte 1")

# Criar dicionário de referência: animal_en -> dados completos
ref_dict = {}
for char in parte1:
    animal_key = char['animal_en'].lower()
    ref_dict[animal_key] = char

print(f"✅ Dicionário de referência criado com {len(ref_dict)} entradas")

# Buscar avatares Biblizoo do banco
user_result = supabase.table('users').select('*').eq('email', 'test@studiox.com').execute()
user = user_result.data[0]
tenant_id = user.get('tenant_id')

tenant_result = supabase.table('tenants').select('*').eq('id', tenant_id).execute()
tenant = tenant_result.data[0]
settings = tenant.get('settings', {})
avatars = settings.get('studio_avatars', [])

# Filtrar avatares Biblizoo
biblizoo_avatars = []
for avatar in avatars:
    name = (avatar.get('name') or '').lower()
    prompt = (avatar.get('prompt') or '').lower()
    
    if 'biblizoo' in name or 'biblizoo' in prompt or 'bíblico' in name:
        biblizoo_avatars.append(avatar)

print(f"\n✅ Encontrados {len(biblizoo_avatars)} avatares Biblizoo no banco")
print("\n" + "="*80)
print("INICIANDO ANÁLISE VISUAL COM GEMINI VISION")
print("="*80 + "\n")

# Função para baixar imagem e converter para base64
def download_image_to_base64(url):
    """Baixa imagem e converte para base64"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            print(f"   ❌ Erro ao baixar: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Erro ao baixar: {e}")
        return None

# Função async para analisar imagem
async def analyze_avatar_image(avatar):
    """Usa Gemini Vision para identificar o animal na imagem"""
    avatar_id = avatar.get('id')
    avatar_name = avatar.get('name', 'SEM NOME')
    image_url = avatar.get('url')
    
    print(f"\n🔍 Analisando: {avatar_name} (ID: {avatar_id})")
    print(f"   URL: {image_url[:80]}...")
    
    # Baixar imagem
    print(f"   📥 Baixando imagem...")
    image_base64 = download_image_to_base64(image_url)
    
    if not image_base64:
        return {
            'id': avatar_id,
            'name': avatar_name,
            'status': 'ERROR',
            'error': 'Falha ao baixar imagem'
        }
    
    print(f"   ✅ Imagem baixada ({len(image_base64)} bytes em base64)")
    
    # Criar chat Gemini Vision
    chat = LlmChat(
        api_key=os.environ.get('EMERGENT_LLM_KEY'),
        session_id=f"avatar_analysis_{avatar_id}",
        system_message="You are an expert at identifying animals in cartoon/chibi 3D renders. Be precise and concise."
    ).with_model("gemini", "gemini-2.5-flash")
    
    # Criar mensagem com imagem
    image_content = ImageContent(image_base64=image_base64)
    
    user_message = UserMessage(
        text="""Analyze this chibi 3D cartoon character image and identify the animal.
        
Respond ONLY with the animal name in English, in this exact format:
Animal: [animal name]

Examples:
- Animal: golden lion cub
- Animal: noble deer
- Animal: doe deer
- Animal: black wolf
- Animal: young lamb
- Animal: elder dromedary camel

Be specific and precise. Look at fur color, features, horns, ears, tail, body shape.""",
        file_contents=[image_content]
    )
    
    try:
        print(f"   🤖 Analisando com Gemini Vision...")
        response = await chat.send_message(user_message)
        
        # Extrair animal da resposta
        animal_identified = response.strip()
        if "Animal:" in animal_identified:
            animal_identified = animal_identified.split("Animal:")[1].strip()
        
        print(f"   ✅ Animal identificado: {animal_identified}")
        
        return {
            'id': avatar_id,
            'name': avatar_name,
            'url': image_url,
            'current_prompt': avatar.get('prompt', ''),
            'identified_animal': animal_identified.lower(),
            'status': 'SUCCESS'
        }
        
    except Exception as e:
        print(f"   ❌ Erro na análise: {e}")
        return {
            'id': avatar_id,
            'name': avatar_name,
            'status': 'ERROR',
            'error': str(e)
        }

# Executar análise
async def main():
    results = []
    
    # Analisar TODOS os avatares
    for i, avatar in enumerate(biblizoo_avatars, 1):
        print(f"\n{'='*80}")
        print(f"AVATAR {i}/{len(biblizoo_avatars)}")
        print(f"{'='*80}")
        
        result = await analyze_avatar_image(avatar)
        results.append(result)
        
        # Pequena pausa entre requisições
        await asyncio.sleep(2)
    
    # Salvar resultados
    with open('/tmp/biblizoo_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'='*80}")
    print(f"✅ ANÁLISE COMPLETA!")
    print(f"{'='*80}")
    print(f"Resultados salvos em: /tmp/biblizoo_analysis_results.json")
    print(f"\nResumo:")
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    print(f"  ✅ Sucesso: {success_count}")
    print(f"  ❌ Erro: {error_count}")

# Executar
asyncio.run(main())
