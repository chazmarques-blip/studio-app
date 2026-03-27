"""
Generate a new commercial video using the UPGRADED V5 agent pipeline.
Uses the real My Truck logo, energetic narration, background music,
and proper timing (narration ends 3-4s before video end).
"""
import os, sys, asyncio, time
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

MARCOS_SYSTEM = """You are Marcos, an elite AI Commercial Director. Create a broadcast-quality 24-second commercial with TWO 12-second clips that feel like ONE continuous masterpiece.

CRITICAL NARRATION TIMING RULE:
- The narration MUST be SHORT and PUNCHY — maximum 50-60 words total
- The spoken narration MUST END by second 19 AT THE LATEST
- The last 4 seconds (19-23s) are COMPLETELY SILENT — only background music plays while the brand logo + tagline + contact info appear on screen
- This is NON-NEGOTIABLE. A narration that runs past 19 seconds = UNUSABLE VIDEO

NARRATION ENERGY:
- Write like the BEST Super Bowl commercial voiceover
- Tone: EXCITED, TRIUMPHANT, celebrating a massive achievement
- NOT calm, NOT documentary-style, NOT narrative
- Think sports announcer meets motivational speaker
- Short PUNCHY sentences. Power words. Dramatic energy.

Format your output EXACTLY like this:

===CHARACTER DESCRIPTION===
[SURGICAL precision: age, ethnicity, build, hair, facial features, clothing]

===CLIP 1 PROMPT===
[80-120 words. Seconds 0-12. Include full character description. End with clear transition moment.]

===CLIP 2 PROMPT===
[80-120 words. Seconds 12-24. Include full character description again. Start at transition. Final 2 seconds: clean dark frame for logo.]

===NARRATION SCRIPT===
[0-5s]: [Hook — bold, attention-grabbing, ENERGETIC]
[5-10s]: [Solution — exciting, benefits, energy RISING]
[10-16s]: [Transformation — triumph, peak excitement, CELEBRATING]
[16-19s]: [CTA — ONE short powerful sentence. Contact + tagline. Then STOP.]
[19-23s]: [SILENCE — music only, logo on screen]

===MUSIC DIRECTION===
Mood: [upbeat/emotional/cinematic/energetic/corporate]
Description: [2-3 sentences about instruments, tempo, energy]

===CTA SEQUENCE===
Brand name: [company name]
Tagline: [powerful phrase]
Contact: [contact method]
Visual: [how final 4 seconds look]

===VIDEO FORMAT===
Format: horizontal
Duration: 24"""

MARCOS_PROMPT = """Create a 24-second commercial video for this campaign.

Brand/Company: My Truck - Pickup Shop
Platforms: whatsapp, instagram, facebook, tiktok, google_ads
Approved campaign copy: From "No Credit" to "New Truck" in 48 Hours. Passport-only approval for hardworking Latino professionals. Low down payment, fast approval, keys in your hand this week.
Visual direction: Golden hour lighting, aspirational, transformation story. Construction worker getting his own truck.
Video brief: 
  VIDEO TAGLINE: Your Truck. Your Future.
  VIDEO TONE: Triumphant, celebratory, like winning a championship. Energy that makes you want to stand up and cheer.
  MUSIC MOOD: energetic
  CTA FOR VIDEO: Chat on WhatsApp now
  CONTACT FOR CTA: WhatsApp: +1 (555) 123-4567

Write ALL narration in ENGLISH (same language as the campaign copy).

CRITICAL REQUIREMENTS:
1. TWO clips that feel like ONE continuous shot
2. NARRATION: Maximum 50-60 words. MUST END by second 19. Last 4 seconds = SILENT (logo only)
3. ENERGY: Like celebrating a life-changing achievement. NOT calm or documentary.
4. Final 4 seconds: clean dark background for My Truck logo + tagline + WhatsApp number
5. The narration creates EXCITEMENT and TRIUMPH, not just information"""


async def main():
    print("=" * 60)
    print("STEP 1: Generating Marcos's commercial concept with Claude...")
    print("=" * 60)
    
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"marcos-v5-test-{int(time.time())}",
        system_message=MARCOS_SYSTEM
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    
    response = await asyncio.wait_for(
        chat.send_message(UserMessage(text=MARCOS_PROMPT)),
        timeout=120
    )
    
    marcos_output = response.text if hasattr(response, 'text') else str(response)
    print(f"\nMarcos output ({len(marcos_output)} chars):")
    print(marcos_output[:800])
    print("...")
    
    with open("/tmp/marcos_v5_output.txt", "w") as f:
        f.write(marcos_output)
    
    # Count narration words
    import re
    narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===MUSIC DIRECTION===', marcos_output, re.IGNORECASE)
    if narr_match:
        narr_text = re.sub(r'\[\d+-\d+s?\]:\s*', '', narr_match.group(1).strip())
        narr_text = re.sub(r'\[SILENCE.*?\]', '', narr_text).strip()
        word_count = len(narr_text.split())
        print(f"\nNarration word count: {word_count} words (target: 50-60)")
        print(f"Narration text: {narr_text[:300]}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Generating commercial video from Marcos's concept...")
    print("=" * 60)
    
    sys.path.insert(0, '/app/backend/routers')
    from pipeline import _generate_commercial_video
    
    url = await _generate_commercial_video("new_v5", marcos_output, "1280x720")
    
    if url:
        print(f"\n{'=' * 60}")
        print(f"SUCCESS! Full commercial video:")
        print(f"URL: {url}")
        print(f"{'=' * 60}")
    else:
        print("\nFAILED: Video generation failed")


if __name__ == "__main__":
    asyncio.run(main())
