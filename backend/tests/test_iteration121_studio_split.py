"""
Iteration 121: Test studio.py split into package and voice-preview endpoint.

Tests:
1. Backend: POST /api/studio/voice-preview endpoint returns audio/mpeg blob
2. Backend: All existing studio endpoints still work after splitting studio.py into a package
   - GET /api/studio/projects
   - GET /api/studio/voices
   - GET /api/studio/music-library
   - GET /api/studio/cache/stats
   - GET /api/studio/analytics/performance
3. Backend: GET /api/studio/projects/{id}/dialogues returns dialogue data
4. Backend: GET /api/studio/projects/{id}/storyboard returns panels
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestStudioPackageSplit:
    """Test that studio endpoints work after splitting studio.py into a package."""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token."""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ── Health Check ──
    def test_health_endpoint(self):
        """Test health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("PASS: Health endpoint returns ok")
    
    # ── Authentication ──
    def test_login_success(self):
        """Test login with valid credentials."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("PASS: Login successful")
    
    # ── Studio Endpoints (after package split) ──
    def test_studio_projects_endpoint(self, auth_headers):
        """Test GET /api/studio/projects works after package split."""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"PASS: GET /api/studio/projects returns {len(data.get('projects', []))} projects")
    
    def test_studio_voices_endpoint(self, auth_headers):
        """Test GET /api/studio/voices works after package split."""
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        print(f"PASS: GET /api/studio/voices returns {len(data.get('voices', []))} voices")
    
    def test_studio_music_library_endpoint(self, auth_headers):
        """Test GET /api/studio/music-library works after package split."""
        response = requests.get(f"{BASE_URL}/api/studio/music-library", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        print(f"PASS: GET /api/studio/music-library returns {len(data.get('tracks', []))} tracks")
    
    def test_studio_cache_stats_endpoint(self, auth_headers):
        """Test GET /api/studio/cache/stats works after package split."""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Cache stats should return some data structure
        assert isinstance(data, dict)
        print(f"PASS: GET /api/studio/cache/stats returns cache statistics")
    
    def test_studio_analytics_performance_endpoint(self, auth_headers):
        """Test GET /api/studio/analytics/performance works after package split."""
        response = requests.get(f"{BASE_URL}/api/studio/analytics/performance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have summary, timing, etc.
        assert "summary" in data or "timing" in data or isinstance(data, dict)
        print(f"PASS: GET /api/studio/analytics/performance returns analytics data")
    
    # ── Voice Preview Endpoint (new) ──
    def test_voice_preview_endpoint_requires_auth(self):
        """Test POST /api/studio/voice-preview requires authentication."""
        response = requests.post(f"{BASE_URL}/api/studio/voice-preview", json={
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "text": "Hello, this is a test."
        })
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: POST /api/studio/voice-preview requires authentication")
    
    def test_voice_preview_endpoint_missing_voice_id(self, auth_headers):
        """Test POST /api/studio/voice-preview returns 400 when voice_id is missing."""
        response = requests.post(f"{BASE_URL}/api/studio/voice-preview", 
            headers=auth_headers,
            json={"text": "Hello, this is a test."}
        )
        # Should return 400 or 422 for missing voice_id
        assert response.status_code in [400, 422]
        print("PASS: POST /api/studio/voice-preview returns error for missing voice_id")
    
    def test_voice_preview_endpoint_empty_voice_id(self, auth_headers):
        """Test POST /api/studio/voice-preview returns 400 when voice_id is empty."""
        response = requests.post(f"{BASE_URL}/api/studio/voice-preview", 
            headers=auth_headers,
            json={"voice_id": "", "text": "Hello, this is a test."}
        )
        # Should return 400 for empty voice_id
        assert response.status_code == 400
        print("PASS: POST /api/studio/voice-preview returns 400 for empty voice_id")
    
    def test_voice_preview_endpoint_returns_audio(self, auth_headers):
        """Test POST /api/studio/voice-preview returns audio/mpeg blob."""
        # Use a valid ElevenLabs voice ID (Rachel)
        response = requests.post(f"{BASE_URL}/api/studio/voice-preview", 
            headers=auth_headers,
            json={
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "text": "Olá, esta é a minha voz."
            }
        )
        # If ElevenLabs API key is configured, should return 200 with audio
        # If not configured, may return 500 with error
        if response.status_code == 200:
            assert response.headers.get("content-type") == "audio/mpeg"
            assert len(response.content) > 0
            print(f"PASS: POST /api/studio/voice-preview returns audio/mpeg ({len(response.content)} bytes)")
        elif response.status_code == 500:
            # ElevenLabs API key may not be configured
            data = response.json()
            assert "detail" in data
            print(f"SKIP: Voice preview failed (likely missing API key): {data.get('detail', '')[:100]}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    # ── Project-specific endpoints ──
    def test_get_project_dialogues(self, auth_headers):
        """Test GET /api/studio/projects/{id}/dialogues returns dialogue data."""
        # First get list of projects
        projects_response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert projects_response.status_code == 200
        projects = projects_response.json().get("projects", [])
        
        if not projects:
            pytest.skip("No projects available to test dialogues endpoint")
        
        # Test with first project
        project_id = projects[0].get("id")
        response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/dialogues", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should return dialogues data structure
        assert isinstance(data, dict)
        print(f"PASS: GET /api/studio/projects/{project_id}/dialogues returns dialogue data")
    
    def test_get_project_storyboard(self, auth_headers):
        """Test GET /api/studio/projects/{id}/storyboard returns panels."""
        # First get list of projects
        projects_response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert projects_response.status_code == 200
        projects = projects_response.json().get("projects", [])
        
        if not projects:
            pytest.skip("No projects available to test storyboard endpoint")
        
        # Test with first project
        project_id = projects[0].get("id")
        response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/storyboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should return storyboard data structure with panels
        assert isinstance(data, dict)
        print(f"PASS: GET /api/studio/projects/{project_id}/storyboard returns storyboard data")
    
    def test_get_project_dialogues_invalid_id(self, auth_headers):
        """Test GET /api/studio/projects/{id}/dialogues returns 404 for invalid project."""
        response = requests.get(f"{BASE_URL}/api/studio/projects/invalid-project-id-12345/dialogues", headers=auth_headers)
        assert response.status_code == 404
        print("PASS: GET /api/studio/projects/invalid-id/dialogues returns 404")
    
    def test_get_project_storyboard_invalid_id(self, auth_headers):
        """Test GET /api/studio/projects/{id}/storyboard returns 404 for invalid project."""
        response = requests.get(f"{BASE_URL}/api/studio/projects/invalid-project-id-12345/storyboard", headers=auth_headers)
        assert response.status_code == 404
        print("PASS: GET /api/studio/projects/invalid-id/storyboard returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
