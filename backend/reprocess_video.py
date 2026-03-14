"""Reprocess V7 video with REAL music + correct contact info."""
import os, sys, subprocess, shutil, re, asyncio
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.openai import OpenAITextToSpeech
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# Read existing marcos output
with open("/tmp/marcos_v5_output.txt") as f:
    marcos_output = f.read()

# Clean narration
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

# Replace old contact in narration with new one
narration_text = narration_text.replace("(555) 123-4567", "(321) 960-2080")
narration_text = narration_text.replace("+1 (555) 123-4567", "(321) 960-2080")

print(f"Narration ({len(narration_text.split())} words): {narration_text[:300]}")

async def main():
    pid = "new_v7"
    clip1 = "/tmp/new_v5_clip1.mp4"
    clip2 = "/tmp/new_v5_clip2.mp4"
    logo = "/app/backend/assets/brand_logo.png"
    music = "/app/backend/assets/music/upbeat.mp3"  # REAL music track

    # Verify music is real
    probe = subprocess.run(f"ffprobe -v error -show_entries format=duration,bit_rate -of csv=p=0 {music}", shell=True, capture_output=True, text=True)
    print(f"Music file: {probe.stdout.strip()} (duration,bitrate)")

    # 1. Fresh TTS
    print("\n=== STEP 1: TTS ===")
    tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
    audio_bytes = await tts.generate_speech(text=narration_text, model="tts-1-hd", voice="nova", speed=1.08, response_format="mp3")
    narr_path = f"/tmp/{pid}_narration.mp3"
    with open(narr_path, "wb") as f:
        f.write(audio_bytes)
    dur = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {narr_path}", shell=True, capture_output=True, text=True)
    print(f"Narration: {dur.stdout.strip()}s")

    # 2. Normalize clips
    print("\n=== STEP 2: Normalize ===")
    for i, clip in enumerate([clip1, clip2], 1):
        subprocess.run(f"ffmpeg -y -i {clip} -c:v libx264 -preset fast -crf 18 -r 30 -pix_fmt yuv420p -an /tmp/{pid}_norm{i}.mp4", shell=True, capture_output=True, timeout=60)

    # 3. Crossfade
    print("\n=== STEP 3: Crossfade ===")
    subprocess.run(
        f'ffmpeg -y -i /tmp/{pid}_norm1.mp4 -i /tmp/{pid}_norm2.mp4 -filter_complex "[0:v]settb=AVTB[v0];[1:v]settb=AVTB[v1];[v0][v1]xfade=transition=fade:duration=1:offset=11,format=yuv420p[vout]" -map "[vout]" -c:v libx264 -preset fast -crf 18 /tmp/{pid}_xfade.mp4',
        shell=True, capture_output=True, timeout=120)
    dur_p = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/{pid}_xfade.mp4", shell=True, capture_output=True, text=True)
    vid_duration = float(dur_p.stdout.strip()) if dur_p.stdout.strip() else 23.0
    print(f"Crossfade: {vid_duration}s")

    # 4. Logo overlay with CORRECT contact info
    print("\n=== STEP 4: Logo overlay ===")
    brand_start = max(vid_duration - 4, 18)
    brand_mid = brand_start + 0.5
    brand_late = brand_start + 1.0

    scaled = f"/tmp/{pid}_logo_scaled.png"
    subprocess.run(f"ffmpeg -y -i {logo} -vf scale=240:-1 {scaled}", shell=True, capture_output=True, timeout=30)

    tagline = "Your Truck. Your Future."
    contact = "(321) 960-2080 | mytruckflorida.com"

    vf = (
        f"[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black@1.0:t=fill:enable='between(t,{brand_start},{vid_duration})'[bg];"
        f"[1:v]scale=240:-1[logo];"
        f"[bg][logo]overlay=(W-w)/2:(H/4)-(h/2):enable='between(t,{brand_start},{vid_duration})'"
        f",drawtext=text='{tagline}':fontsize=28:fontcolor=white@0.95:x=(w-text_w)/2:y=(h*3/5):enable='between(t,{brand_mid},{vid_duration})'"
        f",drawtext=text='{contact}':fontsize=20:fontcolor=0xC9A84C@0.9:x=(w-text_w)/2:y=(h*3/5)+40:enable='between(t,{brand_late},{vid_duration})'"
    )
    r = subprocess.run(f'ffmpeg -y -i /tmp/{pid}_xfade.mp4 -i {scaled} -filter_complex "{vf}" -c:v libx264 -preset fast -crf 18 /tmp/{pid}_branded.mp4',
        shell=True, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"Logo FAILED: {r.stderr[:200]}")
        shutil.copy2(f"/tmp/{pid}_xfade.mp4", f"/tmp/{pid}_branded.mp4")
    else:
        print("Logo overlay OK")

    # 5. Mix REAL music + narration
    print("\n=== STEP 5: Audio mixing (REAL music) ===")
    narr_44k = f"/tmp/{pid}_narr_44k.wav"
    music_44k = f"/tmp/{pid}_music_44k.wav"
    subprocess.run(f"ffmpeg -y -i {narr_path} -ar 44100 -ac 2 {narr_44k}", shell=True, capture_output=True, timeout=30)
    subprocess.run(f"ffmpeg -y -i {music} -ar 44100 -ac 2 -t 30 {music_44k}", shell=True, capture_output=True, timeout=30)

    # Verify both files
    for f_name, f_path in [("narr", narr_44k), ("music", music_44k)]:
        p = subprocess.run(f"ffprobe -v error -show_entries format=duration,bit_rate -show_entries stream=sample_rate,channels -of csv=p=0 {f_path}", shell=True, capture_output=True, text=True)
        print(f"  {f_name}: {p.stdout.strip()}")

    mixed = f"/tmp/{pid}_mixed.wav"
    mix_cmd = (
        f'ffmpeg -y -i {narr_44k} -i {music_44k} '
        f'-filter_complex "'
        f'[0:a]volume=1.3[narr];'
        f'[1:a]volume=0.20[music];'
        f'[narr][music]amix=inputs=2:duration=longest:dropout_transition=3[out]'
        f'" -map "[out]" -t {vid_duration} -ar 44100 -ac 2 {mixed}'
    )
    r = subprocess.run(mix_cmd, shell=True, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"Mix FAILED: {r.stderr[:300]}")
        # Fallback: just use narration
        mixed = narr_44k
    else:
        p = subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {mixed}", shell=True, capture_output=True, text=True)
        print(f"Mixed audio: {p.stdout.strip()}s")

    # 6. Final merge
    print("\n=== STEP 6: Final merge ===")
    output = f"/tmp/{pid}_commercial.mp4"
    subprocess.run(
        f"ffmpeg -y -i /tmp/{pid}_branded.mp4 -i {mixed} -c:v copy -c:a aac -b:a 256k -ar 44100 -ac 2 -t {vid_duration} {output}",
        shell=True, capture_output=True, timeout=60)

    # 7. Upload
    print("\n=== STEP 7: Upload ===")
    sys.path.insert(0, '/app/backend/routers')
    import importlib
    import pipeline
    importlib.reload(pipeline)
    with open(output, "rb") as f:
        video_bytes = f.read()
    url = pipeline._upload_to_storage(video_bytes, f"videos/{pid}_commercial.mp4", "video/mp4")

    # Verify final
    probe = subprocess.run(f"ffprobe -v error -show_entries stream=codec_name,codec_type,sample_rate,channels -of json {output}", shell=True, capture_output=True, text=True)
    print(f"Final specs: {probe.stdout}")
    print(f"\n{'='*60}")
    print(f"SUCCESS! URL: {url}")
    print(f"{'='*60}")

asyncio.run(main())
