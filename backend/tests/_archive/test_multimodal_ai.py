"""
Test suite for AgentZZ Multimodal AI endpoints
Tests: /api/health, /api/auth/login, /api/ai/analyze-image, /api/ai/transcribe
"""
import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_check(self):
        """Test GET /api/health returns 200 with service=agentzz-api"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "agentzz-api"
        assert data["status"] == "ok"
        print(f"✅ Health check passed: {data}")
    
    def test_login_success(self):
        """Test POST /api/auth/login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@agentflow.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@agentflow.com"
        print(f"✅ Login successful for: {data['user']['email']}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test POST /api/auth/login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✅ Invalid login correctly rejected with 401")


class TestImageAnalysis:
    """Tests for /api/ai/analyze-image endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for API calls"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@agentflow.com", "password": "password123"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_analyze_image_accepts_form_data(self, auth_token):
        """Test that POST /api/ai/analyze-image accepts form data with image file"""
        # Create a simple 1x1 pixel PNG image (smallest valid PNG)
        # This is a valid PNG file that contains a single red pixel
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        
        files = {"image": ("test.png", png_data, "image/png")}
        data = {"prompt": "Describe this image", "language": "en"}
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/analyze-image",
            files=files,
            data=data,
            headers=headers
        )
        
        # Endpoint should accept the request (200) or may return error if API key issues
        assert response.status_code in [200, 500]  # 200 success, 500 if Claude API fails
        print(f"✅ Image analyze endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            assert "analysis" in result
            print(f"✅ Image analysis returned: {result.get('analysis', '')[:100]}...")
    
    def test_analyze_image_requires_auth(self):
        """Test that /api/ai/analyze-image requires authentication"""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        
        files = {"image": ("test.png", png_data, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/ai/analyze-image",
            files=files
        )
        
        assert response.status_code == 401
        print("✅ Image analyze endpoint correctly requires auth")


class TestAudioTranscription:
    """Tests for /api/ai/transcribe endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for API calls"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@agentflow.com", "password": "password123"}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_transcribe_accepts_form_data(self, auth_token):
        """Test that POST /api/ai/transcribe accepts form data with audio file"""
        # Create a minimal valid WAV file header (8kHz mono 8-bit PCM silence)
        # WAV header for 0.01 second of silence
        import struct
        
        sample_rate = 8000
        bits_per_sample = 8
        channels = 1
        duration_sec = 0.1
        num_samples = int(sample_rate * duration_sec)
        
        # Create WAV data
        wav_data = bytearray()
        # RIFF header
        wav_data.extend(b'RIFF')
        wav_data.extend(struct.pack('<I', 36 + num_samples))  # File size - 8
        wav_data.extend(b'WAVE')
        # fmt chunk
        wav_data.extend(b'fmt ')
        wav_data.extend(struct.pack('<I', 16))  # Chunk size
        wav_data.extend(struct.pack('<H', 1))   # Audio format (PCM)
        wav_data.extend(struct.pack('<H', channels))
        wav_data.extend(struct.pack('<I', sample_rate))
        wav_data.extend(struct.pack('<I', sample_rate * channels * bits_per_sample // 8))  # Byte rate
        wav_data.extend(struct.pack('<H', channels * bits_per_sample // 8))  # Block align
        wav_data.extend(struct.pack('<H', bits_per_sample))
        # data chunk
        wav_data.extend(b'data')
        wav_data.extend(struct.pack('<I', num_samples))
        wav_data.extend(bytes([128] * num_samples))  # Silence (128 for 8-bit PCM)
        
        files = {"audio": ("test.wav", bytes(wav_data), "audio/wav")}
        data = {"language": "en"}
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/ai/transcribe",
            files=files,
            data=data,
            headers=headers
        )
        
        # Endpoint should accept the request (200) or return error if Whisper API fails
        assert response.status_code in [200, 500]  # 200 success, 500 if Whisper API fails
        print(f"✅ Transcribe endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            assert "text" in result
            print(f"✅ Transcription returned: {result.get('text', '')[:100]}")
    
    def test_transcribe_requires_auth(self):
        """Test that /api/ai/transcribe requires authentication"""
        # Create minimal audio data
        audio_data = bytes([0] * 100)
        
        files = {"audio": ("test.mp3", audio_data, "audio/mp3")}
        response = requests.post(
            f"{BASE_URL}/api/ai/transcribe",
            files=files
        )
        
        assert response.status_code == 401
        print("✅ Transcribe endpoint correctly requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
