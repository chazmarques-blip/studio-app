"""Generate video for the Cargo Van pipeline that was missing its video"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

PIPELINE_ID = "e99361f4-a380-408e-9794-1c9090dccdd4"
CAMPAIGN_ID = "7e094f9e-6180-4ad6-bd00-bfef64c9ab87"

async def main():
    # Get the pipeline
    result = sb.table("pipelines").select("*").eq("id", PIPELINE_ID).execute()
    if not result.data:
        print("Pipeline not found!")
        return
    
    pipeline = result.data[0]
    steps = pipeline.get("steps", {})
    marcos = steps.get("marcos_video", {})
    marcos_output = marcos.get("output", "")
    
    if not marcos_output:
        print("No marcos_video output found!")
        return
    
    print(f"Found marcos output: {len(marcos_output)} chars")
    print(f"Pipeline platforms: {pipeline.get('platforms', [])}")
    
    # Import the video generation function
    from routers.pipeline import _generate_commercial_video
    
    # Get user-selected music
    user_music = pipeline.get("result", {}).get("selected_music", "")
    
    # Generate the video (horizontal 1280x720 for this campaign)
    size = "1280x720"
    print(f"Starting video generation: size={size}, music={user_music or 'auto'}")
    
    video_url = await _generate_commercial_video(PIPELINE_ID, marcos_output, size, selected_music_override=user_music)
    
    if video_url:
        print(f"\nSUCCESS! Video URL: {video_url}")
        
        # Update the pipeline step
        steps["marcos_video"]["video_url"] = video_url
        sb.table("pipelines").update({
            "steps": steps,
        }).eq("id", PIPELINE_ID).execute()
        print("Pipeline updated with video URL")
        
        # Update the campaign stats
        campaign = sb.table("campaigns").select("*").eq("id", CAMPAIGN_ID).execute()
        if campaign.data:
            metrics = campaign.data[0].get("metrics", {})
            stats = metrics.get("stats", {})
            stats["video_url"] = video_url
            metrics["stats"] = stats
            sb.table("campaigns").update({"metrics": metrics}).eq("id", CAMPAIGN_ID).execute()
            print(f"Campaign '{campaign.data[0]['name']}' updated with video URL")
        
        print("\nDONE! Video generated and linked to campaign.")
    else:
        print("\nFAILED: Video generation returned None")

if __name__ == "__main__":
    asyncio.run(main())
