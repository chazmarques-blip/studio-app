"""
Generate a 24-second commercial video with professional narration for "My Truck especial" campaign.
Pipeline: 2x Sora 2 clips (12s each) + OpenAI TTS narration + ffmpeg merge
"""
import os
import sys
import time
import asyncio

sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
from emergentintegrations.llm.openai import OpenAITextToSpeech

# ── Campaign Context ──
# Product: Passport-only truck financing for Latino workers
# Copy: "From 'No Credit' to 'New Truck' in 48 Hours"
# Target: Construction workers, delivery pros, cleaning business owners
# Language: English (campaign language)

# ── Video Prompts (2 clips, 12s each = 24s total) ──

CLIP_1_PROMPT = """Cinematic commercial opening shot: extreme close-up of weathered calloused hands carefully opening a US passport, warm golden morning sunlight streaming through a window creating lens flares. Camera smoothly pulls back revealing a confident Latino construction worker in his late 30s wearing a bright orange safety vest, sitting across a desk from a smiling finance advisor. He signs a document with a gold pen, his expression changing from nervous to relieved. Cut to: the same man walking out of a dealership office into bright sunlight, silhouetted against a beautiful sunrise, as he approaches a pristine white Ford F-150 pickup truck gleaming with dew drops. Warm amber and gold color palette, cinematic shallow depth of field, natural lighting, commercial photography quality."""

CLIP_2_PROMPT = """Continuation of commercial: A confident Latino construction worker in an orange safety vest opens the door of a pristine white Ford F-150 pickup truck, sits behind the wheel, grips the steering wheel with both hands and closes his eyes for a moment of gratitude. His expression shifts to a proud smile. Cut to: aerial drone shot following the white truck driving along a scenic road at golden hour, construction tools visible in the truck bed. Cut to: the truck arriving at a busy construction site, the man steps out confidently, waves to his crew. Final shot: cinematic close-up of the truck keys in his hand with a blurred truck in the background, warm golden sunlight creating a beautiful bokeh. Text overlay: 'YOUR TRUCK. YOUR FUTURE.' Professional commercial quality, warm amber tones, cinematic lens."""

# ── Narration Script (strong CTA, in English) ──
NARRATION_TEXT = """No credit? No problem. With passport-only approval, you can be driving your own work truck in just 48 hours. Imagine: your own vehicle, your own schedule, your own business growing every single day. We've helped hundreds of hardworking people just like you. Low down payment, fast approval, and keys in your hand this week. Don't wait another day losing contracts. Chat with us on WhatsApp now and get pre-approved in minutes. Your truck. Your future. It starts today."""

def generate_video_clip(prompt, clip_name, size="1280x720"):
    """Generate a single 12-second video clip with Sora 2"""
    print(f"\n[VIDEO] Generating {clip_name}...")
    start = time.time()
    try:
        video_gen = OpenAIVideoGeneration(api_key=EMERGENT_KEY)
        video_bytes = video_gen.text_to_video(
            prompt=prompt,
            model="sora-2",
            size=size,
            duration=12,
            max_wait_time=600
        )
        elapsed = time.time() - start
        if video_bytes:
            path = f"/tmp/{clip_name}.mp4"
            with open(path, "wb") as f:
                f.write(video_bytes)
            print(f"[VIDEO] {clip_name} generated in {elapsed:.0f}s ({len(video_bytes)/1024:.0f}KB)")
            return path
        print(f"[VIDEO] {clip_name} FAILED: empty bytes after {elapsed:.0f}s")
    except Exception as e:
        print(f"[VIDEO] {clip_name} ERROR: {e}")
    return None

async def generate_narration():
    """Generate narration audio with OpenAI TTS HD"""
    print("\n[AUDIO] Generating narration with OpenAI TTS HD...")
    start = time.time()
    try:
        tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
        audio_bytes = await tts.generate_speech(
            text=NARRATION_TEXT,
            model="tts-1-hd",
            voice="onyx",  # Deep, authoritative - perfect for commercial narration
            speed=0.95,  # Slightly slower for commercial gravitas
            response_format="mp3"
        )
        elapsed = time.time() - start
        if audio_bytes:
            path = "/tmp/narration.mp3"
            with open(path, "wb") as f:
                f.write(audio_bytes)
            print(f"[AUDIO] Narration generated in {elapsed:.0f}s ({len(audio_bytes)/1024:.0f}KB)")
            return path
        print(f"[AUDIO] FAILED: empty audio after {elapsed:.0f}s")
    except Exception as e:
        print(f"[AUDIO] ERROR: {e}")
    return None

def combine_video_audio(clip1_path, clip2_path, audio_path, output_path):
    """Combine 2 video clips + audio narration with ffmpeg"""
    print("\n[FFMPEG] Combining clips + narration...")
    
    # Step 1: Create a file list for concatenation
    with open("/tmp/clips.txt", "w") as f:
        f.write(f"file '{clip1_path}'\n")
        f.write(f"file '{clip2_path}'\n")
    
    # Step 2: Concatenate the 2 video clips
    concat_cmd = "ffmpeg -y -f concat -safe 0 -i /tmp/clips.txt -c copy /tmp/combined_video.mp4"
    print(f"  Concatenating clips...")
    os.system(concat_cmd)
    
    # Step 3: Merge video + audio (audio as narration track)
    merge_cmd = f"ffmpeg -y -i /tmp/combined_video.mp4 -i {audio_path} -c:v copy -c:a aac -b:a 192k -shortest {output_path}"
    print(f"  Merging video + narration...")
    os.system(merge_cmd)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"[FFMPEG] Final video: {output_path} ({size/1024:.0f}KB)")
        return True
    print("[FFMPEG] FAILED: output file not created")
    return False

def upload_to_supabase(filepath, remote_name):
    """Upload to Supabase Storage"""
    print(f"\n[UPLOAD] Uploading to Supabase...")
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        with open(filepath, "rb") as f:
            video_bytes = f.read()
        supabase.storage.from_("pipeline-assets").upload(
            remote_name, video_bytes,
            {"content-type": "video/mp4", "upsert": "true"}
        )
        public_url = supabase.storage.from_("pipeline-assets").get_public_url(remote_name)
        print(f"[UPLOAD] Done: {public_url}")
        return public_url
    except Exception as e:
        print(f"[UPLOAD] ERROR: {e}")
        return None

async def main():
    total_start = time.time()
    
    # Generate narration first (fast, ~5s)
    audio_path = await generate_narration()
    if not audio_path:
        print("FATAL: Narration generation failed")
        return
    
    # Generate both video clips (slow, ~3min each)
    clip1_path = generate_video_clip(CLIP_1_PROMPT, "truck_clip1")
    if not clip1_path:
        print("FATAL: Clip 1 generation failed")
        return
        
    clip2_path = generate_video_clip(CLIP_2_PROMPT, "truck_clip2")
    if not clip2_path:
        print("FATAL: Clip 2 generation failed")
        return
    
    # Combine everything
    output_path = "/tmp/my_truck_24s_commercial.mp4"
    success = combine_video_audio(clip1_path, clip2_path, audio_path, output_path)
    
    if success:
        # Upload to Supabase
        url = upload_to_supabase(output_path, "videos/my_truck_24s_commercial_narrated.mp4")
        
        total = time.time() - total_start
        print(f"\n{'='*60}")
        print(f"COMPLETE! Total time: {total:.0f}s ({total/60:.1f} min)")
        print(f"Video: 24 seconds, 1280x720, with professional narration")
        print(f"URL: {url}")
        print(f"{'='*60}")
    else:
        print("FATAL: Video combination failed")

if __name__ == "__main__":
    asyncio.run(main())
