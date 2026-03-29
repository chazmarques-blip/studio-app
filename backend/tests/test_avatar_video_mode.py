"""
Test Suite for Avatar/Presenter and Video Mode Features
Tests the new avatar generation, video mode selector, and presenter video endpoints
"""

import pytest
import requests
import os
import time

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


class TestAvatarGeneration:
    """Test avatar generation endpoint using Nano Banana (Gemini image)"""

    def test_generate_avatar_success(self, auth_token):
        """POST /api/campaigns/pipeline/generate-avatar returns valid Supabase URL"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={"company_name": "Test Avatar Company"},
            timeout=60  # Avatar generation takes 10-15 seconds
        )
        
        assert response.status_code == 200, f"Avatar generation failed: {response.text}"
        data = response.json()
        
        # Verify response contains avatar_url
        assert "avatar_url" in data, "Response missing avatar_url field"
        avatar_url = data["avatar_url"]
        
        # Verify it's a valid Supabase storage URL
        assert "supabase.co/storage" in avatar_url, f"Not a Supabase URL: {avatar_url}"
        assert avatar_url.endswith(".png"), f"Avatar should be PNG: {avatar_url}"
        print(f"SUCCESS: Avatar generated at {avatar_url}")

    def test_generate_avatar_requires_auth(self):
        """Avatar generation requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            json={"company_name": "Test"},
            timeout=10
        )
        assert response.status_code in [401, 403], f"Expected 401/403 but got {response.status_code}"


class TestPresenterVideoEndpoint:
    """Test presenter video endpoint (fal.ai integration)"""

    def test_generate_presenter_video_returns_503_without_fal_key(self, auth_token):
        """POST /api/campaigns/pipeline/generate-presenter-video returns 503 when FAL_KEY not set"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-presenter-video",
            headers={"Authorization": f"Bearer {auth_token}"},
            data={
                "pipeline_id": "test123",
                "avatar_url": "https://example.com/avatar.png",
                "audio_url": "https://example.com/audio.mp3"
            },
            timeout=10
        )
        
        assert response.status_code == 503, f"Expected 503 but got {response.status_code}: {response.text}"
        data = response.json()
        assert "FAL_KEY" in data.get("detail", ""), f"Error message should mention FAL_KEY: {data}"
        print("SUCCESS: Presenter video endpoint returns 503 graceful degradation")

    def test_generate_presenter_video_requires_auth(self):
        """Presenter video requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-presenter-video",
            data={"pipeline_id": "test", "avatar_url": "test", "audio_url": "test"},
            timeout=10
        )
        assert response.status_code in [401, 403], f"Expected 401/403 but got {response.status_code}"


class TestPipelineVideoModeFields:
    """Test pipeline creation accepts video_mode and avatar_url fields"""

    def test_pipeline_accepts_video_mode_narration(self, auth_token):
        """Pipeline creation accepts video_mode=narration (default)"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "briefing": "Test briefing for video mode narration",
                "campaign_name": "Video Mode Narration Test",
                "mode": "semi_auto",
                "platforms": ["instagram"],
                "video_mode": "narration",
                "skip_video": False
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        data = response.json()
        result = data.get("result", {})
        
        assert result.get("video_mode") == "narration", f"Expected narration, got {result.get('video_mode')}"
        print("SUCCESS: Pipeline accepts video_mode=narration")

    def test_pipeline_accepts_video_mode_presenter(self, auth_token):
        """Pipeline creation accepts video_mode=presenter with avatar_url"""
        avatar_url = "https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/avatars/test.png"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "briefing": "Test briefing for presenter mode",
                "campaign_name": "Presenter Mode Test",
                "mode": "semi_auto",
                "platforms": ["instagram"],
                "video_mode": "presenter",
                "avatar_url": avatar_url,
                "skip_video": False
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        data = response.json()
        result = data.get("result", {})
        
        assert result.get("video_mode") == "presenter", f"Expected presenter, got {result.get('video_mode')}"
        assert result.get("avatar_url") == avatar_url, f"Expected avatar_url to be set"
        print("SUCCESS: Pipeline accepts video_mode=presenter and avatar_url")

    def test_pipeline_accepts_video_mode_none(self, auth_token):
        """Pipeline creation accepts skip_video=true (Sem Video)"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
            json={
                "briefing": "Test briefing with no video",
                "campaign_name": "Skip Video Test",
                "mode": "semi_auto",
                "platforms": ["instagram"],
                "video_mode": "none",
                "skip_video": True
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        data = response.json()
        result = data.get("result", {})
        
        assert result.get("skip_video") == True, f"Expected skip_video=True"
        print("SUCCESS: Pipeline accepts skip_video=true")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
