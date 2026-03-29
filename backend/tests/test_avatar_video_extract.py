"""
Test Suite for Avatar Video Extraction Feature (Iteration 53)
Tests the new extract-from-video endpoint that extracts frame and audio from video uploads.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seguimiento-2.preview.emergentagent.com')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


class TestExtractFromVideoEndpoint:
    """Test POST /api/campaigns/pipeline/extract-from-video endpoint"""

    def test_extract_from_video_requires_auth(self):
        """Extract from video requires authentication"""
        with open("/tmp/test_video.mp4", "rb") as f:
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/extract-from-video",
                files={"file": ("test.mp4", f, "video/mp4")},
                timeout=30
            )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: extract-from-video requires authentication")

    def test_extract_from_video_rejects_non_video(self, auth_token):
        """Extract endpoint returns 400 for non-video files"""
        # Create a simple text file to test rejection
        test_content = b"This is not a video file"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/extract-from-video",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.txt", test_content, "text/plain")},
            timeout=30
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "video" in data.get("detail", "").lower(), f"Error should mention 'video': {data}"
        print("SUCCESS: extract-from-video rejects non-video files with 400")

    def test_extract_from_video_rejects_image_file(self, auth_token):
        """Extract endpoint returns 400 for image files (wrong MIME type)"""
        # Create a fake image file to test rejection
        test_content = b"fake image data"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/extract-from-video",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.jpg", test_content, "image/jpeg")},
            timeout=30
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "video" in data.get("detail", "").lower(), f"Error should mention 'video': {data}"
        print("SUCCESS: extract-from-video rejects image files with 400")

    def test_extract_from_video_success(self, auth_token):
        """Extract from valid video returns frame_url and audio_url"""
        video_path = "/tmp/test_video.mp4"
        assert os.path.exists(video_path), "Test video file not found - run ffmpeg to create it first"
        
        with open(video_path, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/extract-from-video",
                headers={"Authorization": f"Bearer {auth_token}"},
                files={"file": ("test_video.mp4", f, "video/mp4")},
                timeout=120  # Allow time for video processing
            )
        
        assert response.status_code == 200, f"Extraction failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify frame_url is returned
        assert "frame_url" in data, f"Response missing frame_url: {data}"
        frame_url = data["frame_url"]
        assert frame_url is not None, "frame_url should not be None"
        assert "supabase.co/storage" in frame_url, f"frame_url should be Supabase URL: {frame_url}"
        print(f"SUCCESS: frame_url extracted: {frame_url[:80]}...")
        
        # Verify audio_url is returned (may be None if no audio in video)
        assert "audio_url" in data, f"Response missing audio_url key: {data}"
        audio_url = data.get("audio_url")
        if audio_url:
            assert "supabase.co/storage" in audio_url, f"audio_url should be Supabase URL: {audio_url}"
            print(f"SUCCESS: audio_url extracted: {audio_url[:80]}...")
        else:
            print("Note: audio_url is None (video may not have audio)")
        
        # Verify duration is returned
        assert "duration" in data, f"Response missing duration: {data}"
        duration = data["duration"]
        assert isinstance(duration, (int, float)), f"duration should be numeric: {duration}"
        assert duration > 0, f"duration should be positive: {duration}"
        print(f"SUCCESS: Video duration: {duration} seconds")


class TestPipelineWithExtractedVoice:
    """Test that pipeline correctly accepts avatar_voice from extracted video audio"""

    def test_pipeline_accepts_avatar_voice_from_extraction(self, auth_token):
        """Pipeline creation accepts avatar_voice field with custom voice from extraction"""
        extracted_audio_url = "https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/voice_recordings/video_voice_test.mp3"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "briefing": "Test briefing with extracted voice",
                "campaign_name": "Extracted Voice Test",
                "mode": "semi_auto",
                "platforms": ["instagram"],
                "video_mode": "narration",
                "avatar_voice": {
                    "type": "custom",
                    "url": extracted_audio_url
                },
                "skip_video": False
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        data = response.json()
        result = data.get("result", {})
        
        # Verify avatar_voice was accepted
        avatar_voice = result.get("avatar_voice")
        assert avatar_voice is not None, f"Expected avatar_voice to be set: {result}"
        assert avatar_voice.get("type") == "custom", f"Expected custom voice type"
        print(f"SUCCESS: Pipeline accepts avatar_voice from video extraction")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
