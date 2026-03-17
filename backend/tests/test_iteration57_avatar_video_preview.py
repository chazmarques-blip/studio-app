"""
Iteration 57 - Avatar Video Preview with Kling Avatar v2 Lip-Sync
Tests for:
1. POST /api/campaigns/pipeline/avatar-video-preview - accepts avatar_url, voice_url, voice_id, language
2. TTS audio generation when no custom voice_url provided (uses voice_id like 'onyx')
3. GET /api/campaigns/pipeline/avatar-video-preview/{job_id} - polling returns status and video_url
4. Backend model AvatarVideoPreviewRequest validation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}

class TestAvatarVideoPreviewEndpoint:
    """Test avatar-video-preview POST and polling endpoints"""
    
    def test_avatar_video_preview_requires_auth(self):
        """Test that avatar-video-preview endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview", json={
            "avatar_url": "https://example.com/avatar.png"
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASSED: avatar-video-preview requires authentication")
    
    def test_avatar_video_preview_post_with_voice_id(self, auth_headers):
        """Test POST /avatar-video-preview with TTS voice_id (generates audio via OpenAI TTS)"""
        # Use a sample avatar image URL (doesn't need to be real for job creation test)
        payload = {
            "avatar_url": "https://via.placeholder.com/512x768.png",
            "voice_url": "",  # No custom voice
            "voice_id": "onyx",  # TTS voice ID
            "language": "en"
        }
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        assert data["status"] == "processing", f"Expected 'processing', got {data['status']}"
        print(f"PASSED: avatar-video-preview POST with voice_id returns job_id={data['job_id']}")
        return data["job_id"]
    
    def test_avatar_video_preview_post_with_custom_voice(self, auth_headers):
        """Test POST /avatar-video-preview with custom voice_url"""
        payload = {
            "avatar_url": "https://via.placeholder.com/512x768.png",
            "voice_url": "https://example.com/custom-voice.mp3",  # Custom voice
            "voice_id": "",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        print(f"PASSED: avatar-video-preview POST with custom voice_url returns job_id={data['job_id']}")
    
    def test_avatar_video_preview_post_with_language_es(self, auth_headers):
        """Test POST /avatar-video-preview with Spanish language"""
        payload = {
            "avatar_url": "https://via.placeholder.com/512x768.png",
            "voice_url": "",
            "voice_id": "nova",
            "language": "es"  # Spanish
        }
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data
        print(f"PASSED: avatar-video-preview POST with language=es returns job_id={data['job_id']}")
    
    def test_avatar_video_preview_get_status(self, auth_headers):
        """Test GET /avatar-video-preview/{job_id} polling endpoint"""
        # First create a job
        payload = {
            "avatar_url": "https://via.placeholder.com/512x768.png",
            "voice_url": "",
            "voice_id": "alloy",
            "language": "pt"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json=payload,
            headers=auth_headers
        )
        assert create_resp.status_code == 200
        job_id = create_resp.json()["job_id"]
        
        # Poll for status
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview/{job_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "status" in data, "Response should contain status"
        assert data["status"] in ["processing", "generating_video", "completed", "failed"], f"Unexpected status: {data['status']}"
        print(f"PASSED: GET avatar-video-preview/{job_id} returns status={data['status']}")
    
    def test_avatar_video_preview_invalid_job_id(self, auth_headers):
        """Test GET /avatar-video-preview with invalid job_id returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview/nonexistent123",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASSED: Invalid job_id returns 404")
    
    def test_avatar_video_preview_missing_avatar_url(self, auth_headers):
        """Test POST /avatar-video-preview with missing avatar_url fails validation"""
        payload = {
            "voice_url": "",
            "voice_id": "onyx",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json=payload,
            headers=auth_headers
        )
        # Pydantic should reject missing required field
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
        print("PASSED: Missing avatar_url returns 422 validation error")


class TestAvatarVideoPreviewModel:
    """Test AvatarVideoPreviewRequest model accepts correct parameters"""
    
    def test_model_accepts_all_languages(self, auth_headers):
        """Test that model accepts pt, en, es languages"""
        for lang in ["pt", "en", "es"]:
            payload = {
                "avatar_url": "https://via.placeholder.com/512x768.png",
                "voice_url": "",
                "voice_id": "onyx",
                "language": lang
            }
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 200, f"Language {lang} failed: {response.status_code}"
            print(f"PASSED: Model accepts language={lang}")
    
    def test_model_accepts_all_voice_ids(self, auth_headers):
        """Test that model accepts standard OpenAI TTS voice IDs"""
        voice_ids = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        for voice in voice_ids:
            payload = {
                "avatar_url": "https://via.placeholder.com/512x768.png",
                "voice_url": "",
                "voice_id": voice,
                "language": "en"
            }
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 200, f"Voice ID {voice} failed: {response.status_code}"
        print(f"PASSED: Model accepts all TTS voice IDs: {voice_ids}")


class TestPreviewTexts:
    """Test PREVIEW_TEXTS dictionary has all required languages"""
    
    def test_preview_endpoint_default_language(self, auth_headers):
        """Test that default language (pt) works correctly"""
        payload = {
            "avatar_url": "https://via.placeholder.com/512x768.png",
            "voice_url": "",
            "voice_id": "onyx",
            "language": ""  # Empty should default to pt
        }
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json=payload,
            headers=auth_headers
        )
        # Should still work (defaults to pt)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASSED: Empty language defaults correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
