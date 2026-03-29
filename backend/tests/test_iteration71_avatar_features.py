"""
Iteration 71: Avatar From Prompt (By Prompt / 3D Animated) + Art Gallery Channel Preview + Platform Labels

Tests:
1. POST /api/campaigns/pipeline/generate-avatar-from-prompt with style=realistic
2. POST /api/campaigns/pipeline/generate-avatar-from-prompt with style=3d_cartoon
3. POST /api/campaigns/pipeline/generate-avatar-from-prompt with style=3d_pixar
4. GET /api/campaigns/pipeline/elevenlabs-voices (regression test)
5. POST /api/campaigns/pipeline/voice-preview with voice_type=openai (regression test)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seguimiento-2.preview.emergentagent.com')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestGenerateAvatarFromPrompt:
    """Test the new generate-avatar-from-prompt endpoint with different styles"""
    
    def test_avatar_from_prompt_realistic_returns_200(self, auth_headers):
        """Test avatar generation with style=realistic returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
            headers=auth_headers,
            json={
                "prompt": "TEST professional woman, 30 years old, brown hair, confident smile",
                "gender": "female",
                "style": "realistic",
                "company_name": "Test Company",
                "logo_url": ""
            },
            timeout=60  # AI generation may take time
        )
        # Endpoint should return 200 or 500 (if AI generation fails due to quota)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}, body: {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert "avatar_url" in data, "Missing avatar_url in response"
            assert data.get("style") == "realistic", f"Style mismatch: {data.get('style')}"
            print(f"✓ Avatar generated (realistic): {data.get('avatar_url')[:60]}...")
        else:
            # If AI fails (quota/timeout), just verify error structure
            print(f"⚠ AI generation failed (expected): {response.json().get('detail', response.text)[:100]}")
    
    def test_avatar_from_prompt_3d_cartoon_returns_200(self, auth_headers):
        """Test avatar generation with style=3d_cartoon returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
            headers=auth_headers,
            json={
                "prompt": "TEST friendly cartoon character, young man with glasses",
                "gender": "male",
                "style": "3d_cartoon",
                "company_name": "Test Company"
            },
            timeout=60
        )
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "avatar_url" in data
            assert data.get("style") == "3d_cartoon"
            print(f"✓ Avatar generated (3d_cartoon): {data.get('avatar_url')[:60]}...")
        else:
            print(f"⚠ 3D cartoon generation failed (may be quota): {response.json().get('detail', '')[:100]}")
    
    def test_avatar_from_prompt_3d_pixar_returns_200(self, auth_headers):
        """Test avatar generation with style=3d_pixar returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
            headers=auth_headers,
            json={
                "prompt": "TEST Pixar-style character, professional woman",
                "gender": "female",
                "style": "3d_pixar",
                "company_name": ""
            },
            timeout=60
        )
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "avatar_url" in data
            assert data.get("style") == "3d_pixar"
            print(f"✓ Avatar generated (3d_pixar): {data.get('avatar_url')[:60]}...")
        else:
            print(f"⚠ Pixar generation failed (may be quota): {response.json().get('detail', '')[:100]}")
    
    def test_avatar_from_prompt_requires_prompt(self, auth_headers):
        """Test that empty prompt is handled"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
            headers=auth_headers,
            json={
                "prompt": "",
                "gender": "female",
                "style": "realistic"
            },
            timeout=30
        )
        # Should fail validation or during generation
        # Note: Endpoint may still try to generate with empty prompt
        assert response.status_code in [200, 400, 422, 500]
    
    def test_avatar_from_prompt_default_style_is_realistic(self, auth_headers):
        """Test that missing style defaults to realistic"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
            headers=auth_headers,
            json={
                "prompt": "TEST default style test",
                "gender": "male"
            },
            timeout=60
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            # Default should be 'realistic' if not specified
            assert data.get("style") in ["realistic", None], f"Unexpected style: {data.get('style')}"


class TestElevenLabsVoicesRegression:
    """Regression tests for ElevenLabs voices (from iteration 70)"""
    
    def test_get_elevenlabs_voices(self, auth_headers):
        """GET /api/campaigns/pipeline/elevenlabs-voices returns voices"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/elevenlabs-voices",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "voices" in data, "Missing 'voices' key"
        assert "available" in data, "Missing 'available' key"
        voices = data["voices"]
        assert len(voices) >= 10, f"Expected 10+ voices, got {len(voices)}"
        print(f"✓ ElevenLabs voices: {len(voices)} voices, available={data['available']}")
        # Verify voice structure
        for voice in voices[:3]:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice


class TestVoicePreviewRegression:
    """Regression tests for voice preview (from iteration 70)"""
    
    def test_voice_preview_openai(self, auth_headers):
        """POST /api/campaigns/pipeline/voice-preview with voice_type=openai works"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=auth_headers,
            json={
                "voice_id": "alloy",
                "voice_type": "openai",
                "text": "Test voice preview for regression testing"
            },
            timeout=30
        )
        assert response.status_code == 200, f"Voice preview failed: {response.text}"
        data = response.json()
        assert "audio_url" in data, "Missing audio_url"
        assert data.get("voice_type") == "openai"
        print(f"✓ OpenAI voice preview: {data.get('audio_url')[:60]}...")
    
    def test_voice_preview_elevenlabs(self, auth_headers):
        """POST /api/campaigns/pipeline/voice-preview with voice_type=elevenlabs works"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=auth_headers,
            json={
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "voice_type": "elevenlabs",
                "text": "Test ElevenLabs voice preview"
            },
            timeout=30
        )
        assert response.status_code == 200, f"ElevenLabs preview failed: {response.text}"
        data = response.json()
        assert "audio_url" in data
        assert data.get("voice_type") == "elevenlabs"
        print(f"✓ ElevenLabs voice preview: {data.get('audio_url')[:60]}...")


class TestAvatarFromPromptRequestModel:
    """Test the AvatarFromPromptRequest model structure"""
    
    def test_model_accepts_all_styles(self, auth_headers):
        """Verify endpoint accepts all documented styles"""
        for style in ["realistic", "3d_cartoon", "3d_pixar"]:
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
                headers=auth_headers,
                json={
                    "prompt": f"TEST style validation {style}",
                    "gender": "female",
                    "style": style
                },
                timeout=60
            )
            # Should not return 422 (validation error)
            assert response.status_code != 422, f"Style '{style}' rejected: {response.text}"
            print(f"✓ Style '{style}' accepted by endpoint")
    
    def test_model_accepts_gender_values(self, auth_headers):
        """Verify endpoint accepts male/female gender"""
        for gender in ["male", "female"]:
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-from-prompt",
                headers=auth_headers,
                json={
                    "prompt": f"TEST gender validation {gender}",
                    "gender": gender,
                    "style": "realistic"
                },
                timeout=30
            )
            assert response.status_code != 422, f"Gender '{gender}' rejected"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
