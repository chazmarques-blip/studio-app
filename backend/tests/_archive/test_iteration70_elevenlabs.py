"""
Iteration 70 - ElevenLabs Premium Voice Integration Tests

Tests:
1. GET /api/campaigns/pipeline/elevenlabs-voices - Returns list of 10 voices
2. POST /api/campaigns/pipeline/voice-preview with voice_type='elevenlabs' - Returns audio_url
3. POST /api/campaigns/pipeline/voice-preview with voice_type='openai' - Still works (regression)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestElevenLabsIntegration:
    """ElevenLabs voice integration tests"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Authenticate once for all tests"""
        if TestElevenLabsIntegration.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "test@agentflow.com",
                "password": "password123"
            })
            if response.status_code == 200:
                TestElevenLabsIntegration.auth_token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestElevenLabsIntegration.auth_token}"}
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASSED: Health check endpoint working")
    
    def test_login(self):
        """Test login endpoint returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"PASSED: Login successful, got access_token")
    
    def test_get_elevenlabs_voices(self):
        """Test GET /api/campaigns/pipeline/elevenlabs-voices returns list of 10 voices"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/elevenlabs-voices",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "voices" in data, "Response missing 'voices' key"
        assert "available" in data, "Response missing 'available' key"
        
        # Verify 10 voices
        voices = data["voices"]
        assert len(voices) == 10, f"Expected 10 voices, got {len(voices)}"
        
        # Verify available flag is True (ElevenLabs API key is configured)
        assert data["available"] == True, f"ElevenLabs should be available, got {data['available']}"
        
        # Verify voice structure (check first voice)
        first_voice = voices[0]
        assert "id" in first_voice, "Voice missing 'id'"
        assert "name" in first_voice, "Voice missing 'name'"
        assert "gender" in first_voice, "Voice missing 'gender'"
        assert "accent" in first_voice, "Voice missing 'accent'"
        assert "style" in first_voice, "Voice missing 'style'"
        
        # Verify specific voices exist (Rachel, Liam, Drew per config.py)
        voice_names = [v["name"] for v in voices]
        assert "Rachel" in voice_names, "Rachel voice not found"
        assert "Liam" in voice_names, "Liam voice not found"
        assert "Drew" in voice_names, "Drew voice not found"
        
        print(f"PASSED: ElevenLabs voices endpoint returns {len(voices)} voices")
        print(f"Voice names: {voice_names}")
        print(f"Available: {data['available']}")
    
    def test_voice_preview_elevenlabs(self):
        """Test POST /api/campaigns/pipeline/voice-preview with voice_type='elevenlabs'"""
        # Use Rachel's voice_id from ELEVENLABS_VOICES constant
        rachel_voice_id = "21m00Tcm4TlvDq8ikWAM"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=self.headers,
            json={
                "voice_id": rachel_voice_id,
                "voice_type": "elevenlabs",
                "text": "Hello! This is a test of the ElevenLabs premium voice."
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "audio_url" in data, "Response missing 'audio_url'"
        assert "voice_id" in data, "Response missing 'voice_id'"
        assert "voice_type" in data, "Response missing 'voice_type'"
        
        # Verify values
        assert data["voice_id"] == rachel_voice_id
        assert data["voice_type"] == "elevenlabs"
        assert data["audio_url"].startswith("http"), f"audio_url should be a URL, got {data['audio_url']}"
        
        print(f"PASSED: ElevenLabs voice preview generated")
        print(f"Audio URL: {data['audio_url'][:80]}...")
    
    def test_voice_preview_elevenlabs_liam(self):
        """Test ElevenLabs with Liam voice (male)"""
        liam_voice_id = "TX3LPaxmHKxFdv7VOQHJ"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=self.headers,
            json={
                "voice_id": liam_voice_id,
                "voice_type": "elevenlabs",
                "text": "This is Liam, testing the deep confident voice."
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["voice_type"] == "elevenlabs"
        assert data["voice_id"] == liam_voice_id
        print(f"PASSED: ElevenLabs Liam voice preview generated")
    
    def test_voice_preview_openai_regression(self):
        """Test POST /api/campaigns/pipeline/voice-preview with voice_type='openai' still works"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=self.headers,
            json={
                "voice_id": "alloy",
                "voice_type": "openai",
                "text": "Hello! This is a test of the OpenAI alloy voice."
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "audio_url" in data, "Response missing 'audio_url'"
        assert "voice_id" in data, "Response missing 'voice_id'"
        assert "voice_type" in data, "Response missing 'voice_type'"
        
        # Verify values
        assert data["voice_id"] == "alloy"
        assert data["voice_type"] == "openai"
        assert data["audio_url"].startswith("http")
        
        print(f"PASSED: OpenAI voice preview still works (regression test)")
    
    def test_voice_preview_openai_onyx(self):
        """Test OpenAI onyx voice"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=self.headers,
            json={
                "voice_id": "onyx",
                "voice_type": "openai",
                "text": "This is the onyx voice, deep and authoritative."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["voice_type"] == "openai"
        assert data["voice_id"] == "onyx"
        print(f"PASSED: OpenAI onyx voice preview generated")
    
    def test_voice_preview_default_type(self):
        """Test voice preview defaults to 'openai' when voice_type not specified"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/voice-preview",
            headers=self.headers,
            json={
                "voice_id": "nova",
                "text": "Testing default voice type."
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Default voice_type should be 'openai'
        assert data["voice_type"] == "openai"
        print(f"PASSED: Default voice_type is 'openai'")


class TestElevenLabsVoicesList:
    """Additional tests for ElevenLabs voice list structure"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Authenticate once for all tests"""
        if TestElevenLabsVoicesList.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "test@agentflow.com",
                "password": "password123"
            })
            if response.status_code == 200:
                TestElevenLabsVoicesList.auth_token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestElevenLabsVoicesList.auth_token}"}
    
    def test_voices_have_correct_ids(self):
        """Verify all 10 voice IDs match the expected format"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/elevenlabs-voices",
            headers=self.headers
        )
        data = response.json()
        voices = data["voices"]
        
        # All voice IDs should be 20+ char strings
        for v in voices:
            assert len(v["id"]) >= 20, f"Voice ID too short: {v['id']}"
        
        print(f"PASSED: All voice IDs are valid format")
    
    def test_voices_have_gender(self):
        """Verify all voices have male/female gender"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/elevenlabs-voices",
            headers=self.headers
        )
        data = response.json()
        voices = data["voices"]
        
        for v in voices:
            assert v["gender"] in ["male", "female"], f"Invalid gender: {v['gender']}"
        
        male_count = sum(1 for v in voices if v["gender"] == "male")
        female_count = sum(1 for v in voices if v["gender"] == "female")
        
        print(f"PASSED: {male_count} male voices, {female_count} female voices")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
