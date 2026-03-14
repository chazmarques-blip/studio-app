"""
Generate a new commercial video using the UPGRADED agent pipeline.
Simulates the full Marcos output with all new sections:
CHARACTER DESCRIPTION, CLIP 1, CLIP 2, NARRATION SCRIPT with timing marks,
MUSIC DIRECTION, CTA SEQUENCE.
Campaign: My Truck especial (truck financing for Latino workers)
"""
import os, sys, asyncio, time
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# First, let's use Claude to generate the Marcos output with the new prompt
from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

MARCOS_SYSTEM = """You are Marcos, an elite AI Commercial Director. Create a broadcast-quality 24-second commercial with TWO 12-second clips that feel like ONE continuous masterpiece.

Format your output EXACTLY like this:

===CHARACTER DESCRIPTION===
[SURGICAL precision: age, ethnicity, build, hair, facial features, clothing]

===CLIP 1 PROMPT===
[80-120 words. Seconds 0-12. Include full character description. End with clear transition moment.]

===CLIP 2 PROMPT===
[80-120 words. Seconds 12-24. Include full character description again. Start at transition. End with clean frame for logo.]

===NARRATION SCRIPT===
[0-6s]: [Hook - intimate, personal]
[6-12s]: [Solution - exciting, benefits]
[12-18s]: [Proof - desire, transformation]
[18-24s]: [CTA - URGENT, FOMO, contact method, final tagline]

===MUSIC DIRECTION===
Mood: [upbeat/emotional/cinematic/energetic/corporate]
Description: [2-3 sentences about instruments, tempo, energy]

===CTA SEQUENCE===
Brand name: [company name]
Tagline: [powerful phrase]
Contact: [contact method]
Visual: [how final 3 seconds look]

===VIDEO FORMAT===
Format: horizontal
Duration: 24"""

MARCOS_PROMPT = """Create a 24-second commercial video for this campaign.

Brand/Company: My Truck
Platforms: whatsapp, instagram, facebook, tiktok, google_ads
Approved campaign copy: From "No Credit" to "New Truck" in 48 Hours. Passport-only approval for hardworking Latino professionals. Low down payment, fast approval, keys in your hand this week.
Visual direction: Golden hour lighting, aspirational, transformation story. Construction worker getting his own truck.
Video brief: 
  VIDEO TAGLINE: Your Truck. Your Future.
  VIDEO TONE: Starts intimate and personal, builds to aspirational triumph, ends with urgent excitement
  MUSIC MOOD: cinematic
  CTA FOR VIDEO: Chat on WhatsApp now
  CONTACT FOR CTA: WhatsApp: +1 (555) 123-4567

Write ALL narration in ENGLISH (same language as the campaign copy).

REQUIREMENTS:
1. TWO clips that feel like ONE continuous shot
2. DYNAMIC narration with timing marks
3. Final 3 seconds: clean dark background for "My Truck" logo + tagline + WhatsApp number
4. The narration must create FOMO and urgency"""


async def main():
    print("=" * 60)
    print("STEP 1: Generating Marcos's commercial concept with Claude...")
    print("=" * 60)
    
    # Use Claude to generate the full Marcos output
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"marcos-v4-test-{int(time.time())}",
        system_message=MARCOS_SYSTEM
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")
    
    response = await asyncio.wait_for(
        chat.send_message(UserMessage(text=MARCOS_PROMPT)),
        timeout=120
    )
    
    marcos_output = response.text if hasattr(response, 'text') else str(response)
    print(f"\nMarcos output ({len(marcos_output)} chars):")
    print(marcos_output[:500])
    print("...")
    
    # Save the full output for reference
    with open("/tmp/marcos_full_output.txt", "w") as f:
        f.write(marcos_output)
    
    print("\n" + "=" * 60)
    print("STEP 2: Generating commercial video from Marcos's concept...")
    print("=" * 60)
    
    # Import and use the pipeline function
    sys.path.insert(0, '/app/backend/routers')
    from pipeline import _generate_commercial_video
    
    url = await _generate_commercial_video("new_v4", marcos_output, "1280x720")
    
    if url:
        print(f"\n{'=' * 60}")
        print(f"SUCCESS! Full commercial video:")
        print(f"URL: {url}")
        print(f"{'=' * 60}")
    else:
        print("\nFAILED: Video generation failed")


if __name__ == "__main__":
    asyncio.run(main())
