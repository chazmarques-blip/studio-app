"""
Iteration 54: Voice Mastering & Avatar Video Preview Tests
Features tested:
- POST /api/campaigns/pipeline/upload-voice-recording - uploads audio file and returns {audio_url}
- POST /api/campaigns/pipeline/master-voice - accepts {audio_url} and returns {audio_url} with enhanced audio
- POST /api/campaigns/pipeline/avatar-video-preview - accepts {avatar_url} and returns {job_id, status}
- GET /api/campaigns/pipeline/avatar-video-preview/{job_id} - returns job status and video_url when completed
"""
import pytest
import requests
import os
import time
import wave
import struct
import math

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestUploadVoiceRecording:
    """Test POST /api/campaigns/pipeline/upload-voice-recording endpoint"""
    
    def test_upload_voice_recording_requires_auth(self):
        """Verify endpoint requires authentication."""
        files = {"file": ("test.wav", b"fake audio content", "audio/wav")}
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline/upload-voice-recording", files=files)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("TEST PASSED: upload-voice-recording requires auth")

    def test_upload_voice_recording_rejects_non_audio(self, auth_headers):
        """Verify endpoint rejects non-audio files."""
        files = {"file": ("test.txt", b"this is not audio", "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload-voice-recording",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "audio" in data.get("detail", "").lower()
        print("TEST PASSED: upload-voice-recording rejects non-audio files")

    def test_upload_voice_recording_success(self, auth_headers):
        """Test successful audio file upload."""
        # Create a simple WAV file
        wav_path = "/tmp/test_voice_recording.wav"
        self._create_test_wav(wav_path, duration_secs=2, frequency=440)
        
        with open(wav_path, "rb") as f:
            files = {"file": ("recording.wav", f, "audio/wav")}
            response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/upload-voice-recording",
                files=files,
                headers=auth_headers
            )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "audio_url" in data, f"Missing audio_url in response: {data}"
        assert data["audio_url"].startswith("http"), f"Invalid audio_url: {data['audio_url']}"
        print(f"TEST PASSED: upload-voice-recording success - URL: {data['audio_url'][:80]}...")
        
        # Store URL for master-voice test
        pytest.test_audio_url = data["audio_url"]
        
        # Cleanup
        try: os.remove(wav_path)
        except: pass

    def _create_test_wav(self, filepath, duration_secs=2, frequency=440, sample_rate=44100):
        """Create a test WAV file with a sine wave tone."""
        n_samples = int(duration_secs * sample_rate)
        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(n_samples):
                sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav.writeframes(struct.pack('<h', sample))


class TestMasterVoice:
    """Test POST /api/campaigns/pipeline/master-voice endpoint"""

    def test_master_voice_requires_auth(self):
        """Verify endpoint requires authentication."""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/master-voice",
            json={"audio_url": "https://example.com/test.mp3"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("TEST PASSED: master-voice requires auth")

    def test_master_voice_with_invalid_url(self, auth_headers):
        """Test master-voice with an invalid audio URL."""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/master-voice",
            json={"audio_url": "https://invalid-url-that-doesnt-exist.com/fake.mp3"},
            headers=auth_headers,
            timeout=30
        )
        # Should return 400 or 500 for invalid URL
        assert response.status_code in [400, 500], f"Expected 400/500, got {response.status_code}"
        print("TEST PASSED: master-voice handles invalid URL correctly")

    def test_master_voice_with_valid_audio(self, auth_headers):
        """Test master-voice with a valid uploaded audio file."""
        # First upload an audio file
        wav_path = "/tmp/test_for_mastering.wav"
        self._create_test_wav(wav_path, duration_secs=3, frequency=880)
        
        with open(wav_path, "rb") as f:
            files = {"file": ("recording.wav", f, "audio/wav")}
            upload_response = requests.post(
                f"{BASE_URL}/api/campaigns/pipeline/upload-voice-recording",
                files=files,
                headers=auth_headers
            )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        audio_url = upload_response.json()["audio_url"]
        
        # Now test mastering
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/master-voice",
            json={"audio_url": audio_url},
            headers=auth_headers,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "audio_url" in data, f"Missing audio_url in response: {data}"
        assert data["audio_url"].startswith("http"), f"Invalid mastered audio_url: {data['audio_url']}"
        print(f"TEST PASSED: master-voice success")
        print(f"  Original size: {data.get('original_size', 'N/A')} bytes")
        print(f"  Mastered size: {data.get('mastered_size', 'N/A')} bytes")
        print(f"  Mastered URL: {data['audio_url'][:80]}...")
        
        # Cleanup
        try: os.remove(wav_path)
        except: pass

    def _create_test_wav(self, filepath, duration_secs=2, frequency=440, sample_rate=44100):
        """Create a test WAV file with a sine wave tone."""
        n_samples = int(duration_secs * sample_rate)
        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(n_samples):
                sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav.writeframes(struct.pack('<h', sample))


class TestAvatarVideoPreview:
    """Test POST/GET /api/campaigns/pipeline/avatar-video-preview endpoints"""
    
    def test_avatar_video_preview_post_requires_auth(self):
        """Verify POST endpoint requires authentication."""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json={"avatar_url": "https://example.com/avatar.png"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("TEST PASSED: avatar-video-preview POST requires auth")

    def test_avatar_video_preview_get_requires_auth(self):
        """Verify GET endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview/fake_job_id")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("TEST PASSED: avatar-video-preview GET requires auth")

    def test_avatar_video_preview_get_invalid_job(self, auth_headers):
        """Test GET with invalid job ID returns 404."""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview/invalid_job_12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("TEST PASSED: avatar-video-preview GET returns 404 for invalid job")

    def test_avatar_video_preview_start_job(self, auth_headers):
        """Test starting a video preview job - should return job_id and status."""
        # Use a placeholder avatar URL (actual video generation may take 80+ seconds)
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            json={"avatar_url": "https://example.com/test_avatar.png"},
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, f"Missing job_id in response: {data}"
        assert "status" in data, f"Missing status in response: {data}"
        assert data["status"] == "processing", f"Expected status 'processing', got: {data['status']}"
        print(f"TEST PASSED: avatar-video-preview POST returns job_id={data['job_id']}, status={data['status']}")
        
        # Store job_id for polling test
        pytest.preview_job_id = data["job_id"]

    def test_avatar_video_preview_poll_job(self, auth_headers):
        """Test polling for job status."""
        job_id = getattr(pytest, 'preview_job_id', None)
        if not job_id:
            pytest.skip("No job_id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview/{job_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "status" in data, f"Missing status in response: {data}"
        # Status should be one of: processing, completed, failed
        valid_statuses = ["processing", "completed", "failed"]
        assert data["status"] in valid_statuses, f"Invalid status: {data['status']}"
        print(f"TEST PASSED: avatar-video-preview GET poll returns status={data['status']}")
        
        # If completed, verify video_url
        if data["status"] == "completed":
            assert "video_url" in data, "Missing video_url in completed response"
            print(f"  Video URL: {data['video_url'][:80]}...")


class TestTranslationKeys:
    """Verify translation keys exist in both en.json and pt.json"""
    
    def test_voice_mastering_translations_exist(self):
        """Verify all voice mastering translation keys exist."""
        import json
        
        required_keys = [
            "studio.master_voice",
            "studio.mastering", 
            "studio.mastered",
            "studio.original_voice",
            "studio.recorded_voice",
            "studio.voice_mastered",
        ]
        
        en_path = "/app/frontend/src/locales/en.json"
        pt_path = "/app/frontend/src/locales/pt.json"
        
        with open(en_path, 'r') as f:
            en_data = json.load(f)
        with open(pt_path, 'r') as f:
            pt_data = json.load(f)
        
        missing_en = []
        missing_pt = []
        
        for key in required_keys:
            parts = key.split(".")
            en_val = en_data
            pt_val = pt_data
            
            for part in parts:
                en_val = en_val.get(part, {}) if isinstance(en_val, dict) else None
                pt_val = pt_val.get(part, {}) if isinstance(pt_val, dict) else None
            
            if not en_val or isinstance(en_val, dict):
                missing_en.append(key)
            if not pt_val or isinstance(pt_val, dict):
                missing_pt.append(key)
        
        assert not missing_en, f"Missing EN keys: {missing_en}"
        assert not missing_pt, f"Missing PT keys: {missing_pt}"
        print(f"TEST PASSED: All {len(required_keys)} voice mastering translation keys exist in en.json and pt.json")

    def test_video_preview_translations_exist(self):
        """Verify all video preview translation keys exist."""
        import json
        
        required_keys = [
            "studio.video_preview",
            "studio.generate_video_preview",
            "studio.generating_preview",
            "studio.preview_generated",
        ]
        
        en_path = "/app/frontend/src/locales/en.json"
        pt_path = "/app/frontend/src/locales/pt.json"
        
        with open(en_path, 'r') as f:
            en_data = json.load(f)
        with open(pt_path, 'r') as f:
            pt_data = json.load(f)
        
        missing_en = []
        missing_pt = []
        
        for key in required_keys:
            parts = key.split(".")
            en_val = en_data
            pt_val = pt_data
            
            for part in parts:
                en_val = en_val.get(part, {}) if isinstance(en_val, dict) else None
                pt_val = pt_val.get(part, {}) if isinstance(pt_val, dict) else None
            
            if not en_val or isinstance(en_val, dict):
                missing_en.append(key)
            if not pt_val or isinstance(pt_val, dict):
                missing_pt.append(key)
        
        assert not missing_en, f"Missing EN keys: {missing_en}"
        assert not missing_pt, f"Missing PT keys: {missing_pt}"
        print(f"TEST PASSED: All {len(required_keys)} video preview translation keys exist in en.json and pt.json")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
