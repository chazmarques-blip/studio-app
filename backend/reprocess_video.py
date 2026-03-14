"""
Reprocess the V5 commercial using EXISTING Sora 2 clips.
Only regenerates: TTS narration + FFmpeg (logo + music + combine).
No new Sora 2 calls needed.
"""
import os, sys, asyncio, re
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Read the existing marcos output
with open("/tmp/marcos_v5_output.txt", "r") as f:
    marcos_output = f.read()

# Parse narration and clean it properly
narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===MUSIC DIRECTION===', marcos_output, re.IGNORECASE)
narration_text = ""
if narr_match:
    narration_text = narr_match.group(1).strip()
    # Remove timing marks
    narration_text = re.sub(r'\[\d+-\d+s?\]:\s*', '', narration_text)
    # Remove SILENCE instructions and stage directions
    narration_text = re.sub(r'\[.*?SILENCE.*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\[.*?music\s+only.*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\[.*?logo\s+on\s+screen.*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\[(?:COMPLETE|TOTAL|FULL)?\s*(?:SILENCE|QUIET|PAUSE|NO NARRATION).*?\]', '', narration_text, flags=re.IGNORECASE)
    narration_text = re.sub(r'\n{2,}', '\n', narration_text).strip()

print(f"Cleaned narration ({len(narration_text.split())} words):")
print(narration_text)
print()

# Parse CTA
cta_match = re.search(r'===CTA SEQUENCE===([\s\S]*?)===VIDEO FORMAT===', marcos_output, re.IGNORECASE)
brand_name = "MY TRUCK"
tagline = "Your Truck. Your Future."
contact_cta = "WhatsApp: +1 (555) 123-4567"
if cta_match:
    cta_block = cta_match.group(1)
    m = re.search(r'Brand\s*name:\s*(.+)', cta_block, re.IGNORECASE)
    if m: brand_name = m.group(1).strip()
    m = re.search(r'Tagline:\s*(.+)', cta_block, re.IGNORECASE)
    if m: tagline = m.group(1).strip()
    m = re.search(r'Contact:\s*(.+)', cta_block, re.IGNORECASE)
    if m: contact_cta = m.group(1).strip()

print(f"Brand: {brand_name}")
print(f"Tagline: {tagline}")
print(f"Contact: {contact_cta}")

async def main():
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
    
    # 1. Regenerate TTS narration with energetic voice
    print("\n=== STEP 1: Generating new TTS narration (Nova voice, 1.08x) ===")
    tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
    audio_bytes = await tts.generate_speech(
        text=narration_text, model="tts-1-hd",
        voice="nova", speed=1.08, response_format="mp3"
    )
    audio_path = "/tmp/new_v5_narration_v2.mp3"
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    
    import subprocess
    probe = subprocess.run(
        "ffprobe -v error -show_entries format=duration -of csv=p=0 " + audio_path,
        shell=True, capture_output=True, text=True
    )
    print(f"New narration duration: {probe.stdout.strip()}s")
    
    # 2. Re-combine with existing clips
    print("\n=== STEP 2: Re-combining video with logo + music + new narration ===")
    
    clip1 = "/tmp/new_v5_clip1.mp4"
    clip2 = "/tmp/new_v5_clip2.mp4"
    logo = "/app/backend/assets/brand_logo.png"
    pid = "new_v5b"
    
    # Import the updated combine function
    sys.path.insert(0, '/app/backend/routers')
    
    # Need to reload the module to get our fixes
    import importlib
    import pipeline
    importlib.reload(pipeline)
    
    url = pipeline._combine_commercial_video(
        clip1, clip2, audio_path, brand_name, pid,
        logo_path=logo, tagline=tagline, contact_cta=contact_cta
    )
    
    if url:
        print(f"\n{'=' * 60}")
        print(f"SUCCESS! Reprocessed commercial video:")
        print(f"URL: {url}")
        print(f"{'=' * 60}")
        
        # Verify final specs
        probe = subprocess.run(
            f"ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/{pid}_commercial.mp4",
            shell=True, capture_output=True, text=True
        )
        print(f"Final video duration: {probe.stdout.strip()}s")
        probe2 = subprocess.run(
            f"ffprobe -v error -show_entries stream=codec_type -of csv=p=0 /tmp/{pid}_commercial.mp4",
            shell=True, capture_output=True, text=True
        )
        print(f"Streams: {probe2.stdout.strip()}")
    else:
        print("\nFAILED")

asyncio.run(main())
