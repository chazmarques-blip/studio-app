"""
Comparison: GPT Image 1 vs Gemini Nano Banana (gemini-3-pro-image-preview)
Same prompt, both models, side by side.
"""
import asyncio
import os
import base64
import time
import uuid
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from emergentintegrations.llm.chat import LlmChat, UserMessage

from supabase import create_client

EMERGENT_KEY = os.environ["EMERGENT_LLM_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
BUCKET = "pipeline-assets"

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# The SAME prompt for both models - a real marketing campaign image
PROMPT = """Create a powerful, high-impact marketing image for a truck sales platform called 'My Truck Brokers'. 

The image must include a short bold headline text: 'GANA $400 USD' prominently displayed.

Visual scene: A sleek, powerful semi-truck photographed from a dramatic low angle at golden hour. The truck is on an open highway with a stunning sunset sky. Professional commercial photography style. Rich warm tones with deep shadows. The feeling should be of freedom, opportunity, and power.

Style: Cinematic commercial photography, 1080x1080 square format, magazine-quality lighting. Bold clean modern typography for the headline text."""


async def generate_gpt_image1():
    """Generate with OpenAI GPT Image 1"""
    print("--- GPT Image 1 ---")
    start = time.time()
    try:
        gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)
        images = await gen.generate_images(
            prompt=PROMPT,
            model="gpt-image-1",
            number_of_images=1
        )
        elapsed = time.time() - start
        if images and len(images) > 0:
            img_bytes = images[0]
            fname = f"comparison/gpt_image1_{uuid.uuid4().hex[:6]}.png"
            sb.storage.from_(BUCKET).upload(fname, img_bytes, file_options={"content-type": "image/png", "upsert": "true"})
            url = sb.storage.from_(BUCKET).get_public_url(fname)
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Size: {len(img_bytes) / 1024:.0f} KB")
            print(f"  URL: {url}")
            return {"model": "GPT Image 1", "time": elapsed, "size_kb": len(img_bytes) / 1024, "url": url}
        else:
            print(f"  No images returned after {elapsed:.1f}s")
            return None
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR after {elapsed:.1f}s: {e}")
        return None


async def generate_nano_banana():
    """Generate with Gemini Nano Banana (gemini-3-pro-image-preview)"""
    print("--- Gemini Nano Banana ---")
    start = time.time()
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"compare-{uuid.uuid4().hex[:8]}",
            system_message="You are an expert image generation AI. Generate exactly what is described."
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=PROMPT)
        text_response, images = await chat.send_message_multimodal_response(msg)
        elapsed = time.time() - start
        
        if text_response:
            print(f"  Text response: {text_response[:100]}...")
        
        if images and len(images) > 0:
            img_data = images[0]
            img_bytes = base64.b64decode(img_data['data'])
            fname = f"comparison/nano_banana_{uuid.uuid4().hex[:6]}.png"
            sb.storage.from_(BUCKET).upload(fname, img_bytes, file_options={"content-type": "image/png", "upsert": "true"})
            url = sb.storage.from_(BUCKET).get_public_url(fname)
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Size: {len(img_bytes) / 1024:.0f} KB")
            print(f"  URL: {url}")
            return {"model": "Nano Banana", "time": elapsed, "size_kb": len(img_bytes) / 1024, "url": url}
        else:
            print(f"  No images returned after {elapsed:.1f}s")
            return None
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR after {elapsed:.1f}s: {e}")
        return None


async def main():
    print("=" * 60)
    print("IMAGE GENERATION COMPARISON")
    print(f"Prompt: {PROMPT[:80]}...")
    print("=" * 60)
    
    # Run both in parallel
    results = await asyncio.gather(
        generate_gpt_image1(),
        generate_nano_banana(),
        return_exceptions=True
    )
    
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    for r in results:
        if isinstance(r, Exception):
            print(f"  Error: {r}")
        elif r:
            print(f"\n  {r['model']}:")
            print(f"    Time: {r['time']:.1f}s")
            print(f"    Size: {r['size_kb']:.0f} KB")
            print(f"    URL: {r['url']}")
        else:
            print("  No result")

asyncio.run(main())
