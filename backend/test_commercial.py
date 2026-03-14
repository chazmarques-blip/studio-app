"""
Test the improved commercial video pipeline with Marcos's new 2-clip system.
"""
import os, sys, asyncio
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# Simulate what Marcos (Claude) would output with the new format
MARCOS_OUTPUT = """===CHARACTER DESCRIPTION===
A confident Latino man in his late 30s with short dark hair and light stubble, wearing a bright orange high-visibility safety vest over a dark gray henley shirt, with calloused working hands and a determined expression.

===CLIP 1 PROMPT===
Cinematic commercial opening: Extreme close-up of calloused weathered hands carefully opening a blue US passport under warm golden morning light streaming through office windows, creating soft lens flares. Camera smoothly pulls back revealing a confident Latino man in his late 30s with short dark hair and light stubble wearing a bright orange safety vest over a dark gray henley, sitting across a polished wooden desk. A female advisor in professional attire slides a document toward him. He picks up a gold pen and signs with quiet determination, his expression shifting from concentration to relief. The advisor extends her hand. He shakes it firmly, breaking into a genuine proud smile. Camera tracks him as he pushes open the glass door, walking toward brilliant golden sunlight outside. Warm amber color palette throughout.

===CLIP 2 PROMPT===
Cinematic commercial continuation: A confident Latino man in his late 30s with short dark hair and light stubble wearing a bright orange safety vest pushes through a glass door into brilliant golden sunlight. He walks across a clean dealership lot, his eyes fixed on a pristine white Ford F-150 pickup truck gleaming in golden hour light ahead. He runs his calloused hand along the truck's hood, opens the driver door and sits behind the wheel. Grips the steering wheel with both hands, closes his eyes for an emotional moment, then opens them with a beaming proud smile. Aerial drone shot: the white F-150 drives along a scenic country road at golden sunset, construction tools visible in the bed. Final frame: slow zoom on the truck against a warm amber sky, the image gradually simplifying into a clean dark background.

===NARRATION SCRIPT===
No credit? No problem. Just your passport and forty-eight hours — that's all that stands between you and your own truck. Right now, hundreds of hardworking people just like you are getting approved. Low down payment. Fast approval. No hassles, no runaround. Imagine pulling up to the job site in YOUR truck. Your name on the title. Your business, growing every single day. But spots are filling up fast and this offer won't last. Grab your passport, chat with us on WhatsApp right now, and drive away this week. Your truck. Your future. It starts today.

===BRAND NAME===
MY TRUCK

===VIDEO FORMAT===
Format: horizontal
Duration: 24"""

async def main():
    # Import the function from pipeline
    sys.path.insert(0, '/app/backend/routers')
    from pipeline import _generate_commercial_video
    
    print("Starting commercial video generation with new pipeline...")
    print("This will: 2x Sora 2 clips + TTS narration + crossfade + brand logo")
    print()
    
    url = await _generate_commercial_video("demo_v3", MARCOS_OUTPUT, "1280x720")
    
    if url:
        print(f"\nSUCCESS! Commercial video URL: {url}")
    else:
        print("\nFAILED: Video generation failed")

if __name__ == "__main__":
    asyncio.run(main())
