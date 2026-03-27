"""
Generate a 12-second commercial video for the "My Truck especial" campaign using Sora 2.
"""
import os
import sys
import time

# Get the Emergent LLM key from backend .env
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
if not EMERGENT_KEY:
    print("ERROR: EMERGENT_LLM_KEY not found in backend/.env")
    sys.exit(1)

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

# Campaign context:
# - Product: Passport-only truck financing for Latino professionals
# - Copy: "From 'No Credit' to 'New Truck' in 48 Hours" 
# - Image: Confident Latino construction worker beside a white Ford F-150
# - Target: Construction workers, delivery pros, cleaning business owners
# - Emotion: Empowerment, independence, pride

VIDEO_PROMPT = """Cinematic commercial opening: close-up of weathered hands with work calluses opening a US passport, golden sunlight streaming through a window. Camera pulls back smoothly revealing a Latino construction worker in his late 30s wearing an orange safety vest, standing in a dealership office. He signs a document with determination. Quick transition to bright exterior: the same man walks confidently toward a pristine white pickup truck gleaming in golden hour light. He opens the door, sits behind the wheel, and grips the steering wheel with both hands — his expression shifts from disbelief to quiet pride. Final shot: drone-style pullback as he drives the truck away from the lot onto an open road, sunset behind him. Warm amber color palette, commercial photography quality, cinematic lens flares."""

print(f"Starting Sora 2 video generation...")
print(f"Prompt: {VIDEO_PROMPT[:200]}...")
print(f"Duration: 12 seconds")
print(f"Size: 1792x1024 (landscape)")
print(f"Model: sora-2")
print()

start_time = time.time()

try:
    video_gen = OpenAIVideoGeneration(api_key=EMERGENT_KEY)
    video_bytes = video_gen.text_to_video(
        prompt=VIDEO_PROMPT,
        model="sora-2",
        size="1280x720",
        duration=12,
        max_wait_time=600
    )
    
    elapsed = time.time() - start_time
    
    if video_bytes:
        # Save locally first
        output_path = "/tmp/my_truck_commercial.mp4"
        with open(output_path, "wb") as f:
            f.write(video_bytes)
        print(f"SUCCESS: Video generated in {elapsed:.1f}s")
        print(f"File size: {len(video_bytes) / 1024:.1f} KB")
        print(f"Saved to: {output_path}")
        
        # Upload to Supabase Storage
        from supabase import create_client
        SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
        SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
        
        if SUPABASE_URL and SUPABASE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            filename = "videos/my_truck_comercial_demo.mp4"
            try:
                supabase.storage.from_("pipeline-assets").upload(
                    filename, video_bytes,
                    {"content-type": "video/mp4", "upsert": "true"}
                )
                public_url = supabase.storage.from_("pipeline-assets").get_public_url(filename)
                print(f"Uploaded to Supabase: {public_url}")
            except Exception as e:
                print(f"Upload error (non-fatal): {e}")
        else:
            print("WARN: Supabase credentials not found, video saved locally only")
    else:
        print(f"FAILED: Empty video bytes after {elapsed:.1f}s")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"ERROR after {elapsed:.1f}s: {e}")
    import traceback
    traceback.print_exc()
