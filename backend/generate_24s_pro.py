"""
Generate IMPROVED 24-second commercial with professional continuity.
Key improvements:
- Same character description in BOTH clips for visual consistency
- Smooth narrative arc with natural transition point at 12s mark  
- Crossfade transition instead of hard cut
- Narration paced to match the visual story beats
"""
import os
import sys
import time
import asyncio
import subprocess

sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
from emergentintegrations.llm.openai import OpenAITextToSpeech

# ── CONSISTENT CHARACTER & SCENE DEFINITION ──
# Used in BOTH prompts for visual continuity
CHARACTER = "a Latino man in his late 30s with short dark hair, light stubble, wearing a bright orange high-visibility safety vest over a dark gray henley shirt"
TRUCK = "a brand new pristine white Ford F-150 pickup truck with chrome details gleaming in warm golden hour sunlight"
COLOR_PALETTE = "warm amber and gold tones, cinematic shallow depth of field, golden hour natural lighting, lens flares"

# ── CLIP 1: THE DREAM BEGINS (0-12s) ──
# Narrative: Struggle → Hope → The Moment of Approval
CLIP_1_PROMPT = f"""Cinematic commercial. Interior of a clean modern office bathed in warm golden light streaming through large windows. {CHARACTER} sits across a wooden desk from a friendly female advisor in business attire. Close-up of his weathered calloused hands sliding a US passport across the desk. The advisor smiles and nods approvingly. She slides back a document and offers a gold pen. He signs with quiet determination, his expression shifting from nervous concentration to profound relief. She stands and extends her hand for a congratulatory handshake. He shakes it firmly, a genuine smile breaking across his face. Camera follows him as he stands and walks toward the glass office door, pushing it open toward brilliant outdoor sunlight. {COLOR_PALETTE}, professional commercial photography quality."""

# ── CLIP 2: THE DREAM REALIZED (12-24s) ──
# Narrative: Continuation from walking outside → Meeting the truck → Driving into his future  
CLIP_2_PROMPT = f"""Cinematic commercial continuation. {CHARACTER} walks out of a glass door into bright golden sunlight, squinting slightly with an expression of anticipation. Camera tracks him walking through a clean dealership lot. He stops as he sees {TRUCK} parked prominently ahead. Slow cinematic walk toward the truck, his hand reaching out to touch the pristine white hood. He opens the driver door, sits inside, grips the steering wheel with both calloused hands, closes his eyes for one emotional moment, then opens them with a proud confident smile. Cut to: smooth aerial drone shot of the white F-150 driving along a scenic two-lane road surrounded by golden fields at sunset, construction tools visible in the truck bed. {COLOR_PALETTE}, professional commercial photography quality."""

# ── NARRATION: Paced for 24 seconds ──
# Beat 1 (0-6s): Problem + Solution  
# Beat 2 (6-12s): The moment / emotional hook
# Beat 3 (12-18s): The transformation  
# Beat 4 (18-24s): CTA
NARRATION_TEXT = """No credit history? Just your passport. That's all it takes. In forty-eight hours, you could be signing for your own work truck. Imagine: the keys in your hand, your name on the title, your business growing every single day. We've helped hundreds of hardworking people just like you get on the road. Don't let another contract slip away. Chat with us on WhatsApp right now and get pre-approved in minutes. Your truck. Your future. It starts today."""


def generate_clip(prompt, name):
    print(f"\n[VIDEO] Generating {name}...")
    start = time.time()
    try:
        vg = OpenAIVideoGeneration(api_key=EMERGENT_KEY)
        video_bytes = vg.text_to_video(
            prompt=prompt, model="sora-2",
            size="1280x720", duration=12, max_wait_time=600
        )
        elapsed = time.time() - start
        if video_bytes:
            path = f"/tmp/{name}.mp4"
            with open(path, "wb") as f:
                f.write(video_bytes)
            print(f"[VIDEO] {name}: {elapsed:.0f}s, {len(video_bytes)/1024:.0f}KB")
            return path
        print(f"[VIDEO] {name}: FAILED (empty) after {elapsed:.0f}s")
    except Exception as e:
        print(f"[VIDEO] {name}: ERROR - {e}")
    return None


async def generate_narration():
    print("\n[AUDIO] Generating narration...")
    start = time.time()
    try:
        tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
        audio = await tts.generate_speech(
            text=NARRATION_TEXT, model="tts-1-hd",
            voice="onyx", speed=0.92, response_format="mp3"
        )
        elapsed = time.time() - start
        if audio:
            path = "/tmp/narration_v2.mp3"
            with open(path, "wb") as f:
                f.write(audio)
            print(f"[AUDIO] Done: {elapsed:.0f}s, {len(audio)/1024:.0f}KB")
            return path
    except Exception as e:
        print(f"[AUDIO] ERROR - {e}")
    return None


def combine_with_crossfade(clip1, clip2, audio, output):
    """Combine 2 clips with 1-second crossfade + audio narration"""
    print("\n[FFMPEG] Combining with professional crossfade...")
    
    # Re-encode both clips to ensure identical codecs for crossfade
    for i, clip in enumerate([clip1, clip2], 1):
        cmd = f"ffmpeg -y -i {clip} -c:v libx264 -preset fast -crf 18 -r 30 -pix_fmt yuv420p -an /tmp/clip{i}_norm.mp4"
        subprocess.run(cmd, shell=True, capture_output=True)
        print(f"  Normalized clip {i}")
    
    # Apply 1-second crossfade between clips
    crossfade_cmd = (
        'ffmpeg -y -i /tmp/clip1_norm.mp4 -i /tmp/clip2_norm.mp4 '
        '-filter_complex "'
        '[0:v]settb=AVTB[v0];'
        '[1:v]settb=AVTB[v1];'
        '[v0][v1]xfade=transition=fade:duration=1:offset=11,format=yuv420p[vout]'
        '" -map "[vout]" -c:v libx264 -preset fast -crf 18 /tmp/crossfaded.mp4'
    )
    result = subprocess.run(crossfade_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Crossfade failed: {result.stderr[-200:]}")
        # Fallback to simple concat
        print("  Falling back to concat with fade...")
        with open("/tmp/clips.txt", "w") as f:
            f.write(f"file '/tmp/clip1_norm.mp4'\nfile '/tmp/clip2_norm.mp4'\n")
        subprocess.run("ffmpeg -y -f concat -safe 0 -i /tmp/clips.txt -c copy /tmp/crossfaded.mp4", shell=True, capture_output=True)
    else:
        print("  Crossfade applied (1s fade)")
    
    # Merge video + narration audio
    merge_cmd = f"ffmpeg -y -i /tmp/crossfaded.mp4 -i {audio} -c:v copy -c:a aac -b:a 192k -shortest {output}"
    subprocess.run(merge_cmd, shell=True, capture_output=True)
    
    if os.path.exists(output):
        size = os.path.getsize(output)
        # Get duration
        probe = subprocess.run(
            f'ffprobe -v error -show_entries format=duration -of csv=p=0 {output}',
            shell=True, capture_output=True, text=True
        )
        dur = probe.stdout.strip()
        print(f"[FFMPEG] Final: {output} ({size/1024:.0f}KB, {dur}s)")
        return True
    print("[FFMPEG] FAILED")
    return False


def upload(filepath, remote):
    print(f"\n[UPLOAD] Uploading to Supabase...")
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        with open(filepath, "rb") as f:
            data = f.read()
        sb.storage.from_("pipeline-assets").upload(remote, data, {"content-type": "video/mp4", "upsert": "true"})
        url = sb.storage.from_("pipeline-assets").get_public_url(remote)
        print(f"[UPLOAD] Done: {url}")
        return url
    except Exception as e:
        print(f"[UPLOAD] ERROR: {e}")
        return None


async def main():
    total = time.time()
    
    # 1. Generate narration first (fast ~5s)
    audio = await generate_narration()
    if not audio:
        print("FATAL: Narration failed"); return
    
    # 2. Generate both clips (slow ~3min each)
    c1 = generate_clip(CLIP_1_PROMPT, "truck_v2_clip1")
    if not c1:
        print("FATAL: Clip 1 failed"); return
    
    c2 = generate_clip(CLIP_2_PROMPT, "truck_v2_clip2")
    if not c2:
        print("FATAL: Clip 2 failed"); return
    
    # 3. Combine with crossfade + narration
    output = "/tmp/my_truck_24s_pro.mp4"
    ok = combine_with_crossfade(c1, c2, audio, output)
    
    if ok:
        url = upload(output, "videos/my_truck_24s_pro_crossfade.mp4")
        elapsed = time.time() - total
        print(f"\n{'='*60}")
        print(f"COMPLETE! {elapsed:.0f}s ({elapsed/60:.1f} min)")
        print(f"24s commercial with crossfade + narration")
        print(f"URL: {url}")
        print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
