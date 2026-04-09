#!/usr/bin/env python3
"""
Teste simples da API Google Imagen 3.0 com GEMINI_API_KEY
"""
import os
import asyncio
import httpx
import base64
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

async def test_imagen():
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    
    if not gemini_key:
        print("❌ GEMINI_API_KEY não encontrada!")
        return
    
    print(f"✅ GEMINI_API_KEY encontrada: {gemini_key[:20]}...")
    
    # Gemini Nano Banana (gemini-2.5-flash-image) - generateContent endpoint
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
    
    headers = {
        "x-goog-api-key": gemini_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "A serene landscape with mountains and a lake at sunset"
            }]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }
    
    print("\n🚀 Chamando API Gemini Nano Banana...")
    print(f"URL: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"\n📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ Sucesso!")
                print(f"Resposta: {result.keys()}")
                
                # Gemini returns candidates with parts containing inline_data
                if "candidates" in result:
                    for candidate in result["candidates"]:
                        if "content" in candidate:
                            parts = candidate["content"].get("parts", [])
                            for part in parts:
                                if "inlineData" in part:
                                    mime_type = part["inlineData"].get("mimeType")
                                    image_base64 = part["inlineData"].get("data")
                                    
                                    print(f"Imagem encontrada: {mime_type}")
                                    print(f"Base64 length: {len(image_base64)} caracteres")
                                    
                                    # Salvar imagem de teste
                                    image_bytes = base64.b64decode(image_base64)
                                    with open("/tmp/test_gemini_image.png", "wb") as f:
                                        f.write(image_bytes)
                                    print("✅ Imagem salva em /tmp/test_gemini_image.png")
                                    return
                
                print(f"⚠️ Nenhuma imagem encontrada na resposta: {result}")
            else:
                print(f"❌ Erro: {response.status_code}")
                print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Exceção: {e}")

if __name__ == "__main__":
    asyncio.run(test_imagen())
