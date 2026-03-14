"""Reprocess V5 video with FIXED music + logo overlay using existing clips."""
import os, sys, subprocess, shutil
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

import asyncio, re
from emergentintegrations.llm.openai import OpenAITextToSpeech
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# Read existing narration text
with open("/tmp/marcos_v5_output.txt") as f:
    marcos_output = f.read()

narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===MUSIC DIRECTION===', marcos_output, re.IGNORECASE)
narration_text = ""
if narr_match:
    narration_text = narr_match.group(1).strip()
    narration_text = re.sub(r'\[\d+-\d+s?\]:\s*', '', narration_text)
    narration_text = re.sub(r'\[.*?SILENCE.*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\[.*?music\s+only.*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\[.*?logo\s+on\s+screen.*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\[(?:COMPLETE|TOTAL|FULL)?\s*(?:SILENCE|QUIET|PAUSE|NO NARRATION).*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\n{2,}', '\n', narration_text).strip()

print(f"Narration ({len(narration_text.split())} words): {narration_text[:200]}")

async def main():
    pid = "new_v6"
    clip1 = "/tmp/new_v5_clip1.mp4"
    clip2 = "/tmp/new_v5_clip2.mp4"
    logo = "/app/backend/assets/brand_logo.png"
    music = "/app/backend/assets/music/upbeat.mp3"
    
    # 1. Generate fresh narration
    print("\n=== STEP 1: TTS Narration (Nova, 1.08x) ===")
    tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
    audio_bytes = await tts.generate_speech(text=narration_text, model="tts-1-hd", voice="nova", speed=1.08, response_format="mp3")
    narr_path = f"/tmp/{pid}_narration.mp3"
    with open(narr_path, "wb") as f:
        f.write(audio_bytes)
    dur = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {narr_path}", shell=True, capture_output=True, text=True)
    print(f"Narration: {dur.stdout.strip()}s")

    # 2. Normalize clips
    print("\n=== STEP 2: Normalize clips ===")
    for i, clip in enumerate([clip1, clip2], 1):
        subprocess.run(f"ffmpeg -y -i {clip} -c:v libx264 -preset fast -crf 18 -r 30 -pix_fmt yuv420p -an /tmp/{pid}_norm{i}.mp4", shell=True, capture_output=True, timeout=60)
        print(f"  Clip {i} normalized")

    # 3. Crossfade
    print("\n=== STEP 3: Crossfade ===")
    xfade = f'ffmpeg -y -i /tmp/{pid}_norm1.mp4 -i /tmp/{pid}_norm2.mp4 -filter_complex "[0:v]settb=AVTB[v0];[1:v]settb=AVTB[v1];[v0][v1]xfade=transition=fade:duration=1:offset=11,format=yuv420p[vout]" -map "[vout]" -c:v libx264 -preset fast -crf 18 /tmp/{pid}_xfade.mp4'
    subprocess.run(xfade, shell=True, capture_output=True, timeout=120)
    dur_p = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/{pid}_xfade.mp4", shell=True, capture_output=True, text=True)
    vid_duration = float(dur_p.stdout.strip()) if dur_p.stdout.strip() else 23.0
    print(f"  Crossfade done: {vid_duration}s")

    # 4. Logo overlay (fully opaque black background)
    print("\n=== STEP 4: Brand logo overlay ===")
    brand_start = max(vid_duration - 4, 18)
    brand_mid = brand_start + 0.5
    brand_late = brand_start + 1.0

    scaled = f"/tmp/{pid}_logo_scaled.png"
    subprocess.run(f"ffmpeg -y -i {logo} -vf scale=240:-1 {scaled}", shell=True, capture_output=True, timeout=30)
    
    vf = (
        f"[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black@1.0:t=fill:enable='between(t,{brand_start},{vid_duration})'[bg];"
        f"[1:v]scale=240:-1[logo];"
        f"[bg][logo]overlay=(W-w)/2:(H/4)-(h/2):enable='between(t,{brand_start},{vid_duration})'"
        f",drawtext=text='Your Truck. Your Future.':fontsize=28:fontcolor=white@0.95:x=(w-text_w)/2:y=(h*3/5):enable='between(t,{brand_mid},{vid_duration})'"
        f",drawtext=text='WhatsApp  +1 (555) 123-4567':fontsize=20:fontcolor=0xC9A84C@0.9:x=(w-text_w)/2:y=(h*3/5)+40:enable='between(t,{brand_late},{vid_duration})'"
    )
    logo_cmd = f'ffmpeg -y -i /tmp/{pid}_xfade.mp4 -i {scaled} -filter_complex "{vf}" -c:v libx264 -preset fast -crf 18 /tmp/{pid}_branded.mp4'
    r = subprocess.run(logo_cmd, shell=True, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"Logo overlay FAILED: {r.stderr[:300]}")
        shutil.copy2(f"/tmp/{pid}_xfade.mp4", f"/tmp/{pid}_branded.mp4")
    else:
        print("  Logo overlay OK")

    # 5. Mix audio: resample both to 44100Hz stereo, then mix
    print("\n=== STEP 5: Audio mixing (narration + background music) ===")
    narr_44k = f"/tmp/{pid}_narr_44k.wav"
    music_44k = f"/tmp/{pid}_music_44k.wav"
    subprocess.run(f"ffmpeg -y -i {narr_path} -ar 44100 -ac 2 {narr_44k}", shell=True, capture_output=True, timeout=30)
    subprocess.run(f"ffmpeg -y -i {music} -ar 44100 -ac 2 {music_44k}", shell=True, capture_output=True, timeout=30)
    
    mixed = f"/tmp/{pid}_mixed.wav"
    mix_cmd = (
        f'ffmpeg -y -i {narr_44k} -i {music_44k} '
        f'-filter_complex "'
        f'[0:a]volume=1.2,apad[narr];'
        f'[1:a]volume=0.25,aloop=loop=-1:size=2e+09[music];'
        f'[narr][music]amix=inputs=2:duration=first:dropout_transition=3[out]'
        f'" -map "[out]" -t {vid_duration} -ar 44100 -ac 2 {mixed}'
    )
    r = subprocess.run(mix_cmd, shell=True, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"Mix FAILED: {r.stderr[:300]}")
        mixed = narr_path
    else:
        mix_dur = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {mixed}", shell=True, capture_output=True, text=True)
        print(f"  Mixed audio: {mix_dur.stdout.strip()}s (44100Hz stereo)")

    # 6. Merge video + mixed audio
    print("\n=== STEP 6: Final merge ===")
    output = f"/tmp/{pid}_commercial.mp4"
    subprocess.run(
        f"ffmpeg -y -i /tmp/{pid}_branded.mp4 -i {mixed} -c:v copy -c:a aac -b:a 256k -ar 44100 -ac 2 -t {vid_duration} {output}",
        shell=True, capture_output=True, timeout=60
    )

    # 7. Upload
    print("\n=== STEP 7: Upload to Supabase ===")
    sys.path.insert(0, '/app/backend/routers')
    from pipeline import _upload_to_storage
    with open(output, "rb") as f:
        video_bytes = f.read()
    url = _upload_to_storage(video_bytes, f"videos/{pid}_commercial.mp4", "video/mp4")
    
    # Verify
    probe = subprocess.run(f"ffprobe -v error -show_entries stream=codec_name,codec_type,sample_rate,channels -of json {output}", shell=True, capture_output=True, text=True)
    print(f"\nFinal specs: {probe.stdout}")
    
    print(f"\n{'='*60}")
    print(f"SUCCESS! Video URL: {url}")
    print(f"{'='*60}")

asyncio.run(main())
