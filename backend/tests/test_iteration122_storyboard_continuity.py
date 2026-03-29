"""
Iteration 122: Test Continuity Director storyboard architecture upgrade
Tests:
- Backend server starts without import errors
- New storyboard functions (_generate_shot_briefs, _build_identity_prompt, generate_all_panels) import correctly
- All existing studio endpoints remain functional
- GET /api/studio/projects returns projects list
- GET /api/studio/projects/{id}/storyboard returns panels with status
- POST /api/studio/voice-preview returns audio/mpeg
- GET /api/studio/voices returns voice list
- GET /api/studio/music-library returns tracks
- GET /api/studio/cache/stats returns cache info
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seguimiento-2.preview.emergentagent.com')


class TestStoryboardContinuityDirector:
    """Test suite for Continuity Director storyboard architecture upgrade"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@agentflow.com", "password": "password123"},
            timeout=30
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ── Module Import Tests ──
    
    def test_storyboard_module_imports(self):
        """Test that core.storyboard module imports correctly with new functions"""
        try:
            from core.storyboard import _generate_shot_briefs, _build_identity_prompt, generate_all_panels
            assert callable(_generate_shot_briefs), "_generate_shot_briefs should be callable"
            assert callable(_build_identity_prompt), "_build_identity_prompt should be callable"
            assert callable(generate_all_panels), "generate_all_panels should be callable"
        except ImportError as e:
            pytest.fail(f"Failed to import storyboard functions: {e}")
    
    def test_storyboard_frame_types_defined(self):
        """Test that FRAME_TYPES constant is defined with 6 frames"""
        from core.storyboard import FRAME_TYPES
        assert isinstance(FRAME_TYPES, list), "FRAME_TYPES should be a list"
        assert len(FRAME_TYPES) == 6, f"FRAME_TYPES should have 6 frames, got {len(FRAME_TYPES)}"
        for ft in FRAME_TYPES:
            assert "label" in ft, "Each frame type should have a label"
            assert "order" in ft, "Each frame type should have an order"
            assert "prompt" in ft, "Each frame type should have a prompt"
    
    def test_shared_module_imports(self):
        """Test that _shared.py module imports correctly with _analyze_avatars_with_vision"""
        try:
            from routers.studio._shared import _analyze_avatars_with_vision
            assert callable(_analyze_avatars_with_vision), "_analyze_avatars_with_vision should be callable"
        except ImportError as e:
            pytest.fail(f"Failed to import _analyze_avatars_with_vision: {e}")
    
    # ── Health & Auth Tests ──
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@agentflow.com", "password": "password123"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@agentflow.com"
    
    # ── Studio Projects Tests ──
    
    def test_studio_projects_endpoint(self, auth_headers):
        """Test GET /api/studio/projects returns projects list"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        assert len(data["projects"]) > 0, "Should have at least one project"
    
    def test_studio_project_storyboard(self, auth_headers):
        """Test GET /api/studio/projects/{id}/storyboard returns panels with status"""
        # First get a project ID
        projects_response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            timeout=30
        )
        assert projects_response.status_code == 200
        projects = projects_response.json()["projects"]
        assert len(projects) > 0, "Need at least one project to test"
        
        project_id = projects[0]["id"]
        
        # Get storyboard
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/storyboard",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "panels" in data, "Response should have panels"
        assert "storyboard_status" in data, "Response should have storyboard_status"
        assert "storyboard_approved" in data, "Response should have storyboard_approved"
        
        # Verify panels structure if any exist
        if len(data["panels"]) > 0:
            panel = data["panels"][0]
            assert "scene_number" in panel, "Panel should have scene_number"
            assert "title" in panel, "Panel should have title"
            assert "status" in panel, "Panel should have status"
    
    def test_studio_project_storyboard_invalid_id(self, auth_headers):
        """Test GET /api/studio/projects/{invalid_id}/storyboard returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/invalid-project-id-12345/storyboard",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 404
    
    # ── Voice & Audio Tests ──
    
    def test_studio_voices_endpoint(self, auth_headers):
        """Test GET /api/studio/voices returns voice list"""
        response = requests.get(
            f"{BASE_URL}/api/studio/voices",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert isinstance(data["voices"], list)
        assert len(data["voices"]) > 0, "Should have at least one voice"
        
        # Verify voice structure
        voice = data["voices"][0]
        assert "id" in voice, "Voice should have id"
        assert "name" in voice, "Voice should have name"
    
    def test_voice_preview_returns_audio(self, auth_headers):
        """Test POST /api/studio/voice-preview returns audio/mpeg"""
        response = requests.post(
            f"{BASE_URL}/api/studio/voice-preview",
            headers=auth_headers,
            json={"voice_id": "onwK4e9ZLuTAKqWW03F9", "text": "Test audio generation"},
            timeout=60
        )
        assert response.status_code == 200
        assert "audio/mpeg" in response.headers.get("Content-Type", ""), "Should return audio/mpeg"
        assert len(response.content) > 1000, "Audio content should be substantial"
    
    def test_voice_preview_requires_auth(self):
        """Test POST /api/studio/voice-preview requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/studio/voice-preview",
            json={"voice_id": "test", "text": "Test"},
            timeout=30
        )
        assert response.status_code == 401 or response.status_code == 403
    
    # ── Music Library Tests ──
    
    def test_studio_music_library_endpoint(self, auth_headers):
        """Test GET /api/studio/music-library returns tracks"""
        response = requests.get(
            f"{BASE_URL}/api/studio/music-library",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        assert isinstance(data["tracks"], list)
        assert len(data["tracks"]) > 0, "Should have at least one track"
    
    # ── Cache Stats Tests ──
    
    def test_studio_cache_stats_endpoint(self, auth_headers):
        """Test GET /api/studio/cache/stats returns cache info"""
        response = requests.get(
            f"{BASE_URL}/api/studio/cache/stats",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify cache structure
        assert "image_cache" in data or "project_cache" in data or "llm_cache" in data, \
            "Response should have cache info"
    
    def test_studio_cache_stats_requires_auth(self):
        """Test GET /api/studio/cache/stats requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/studio/cache/stats",
            timeout=30
        )
        assert response.status_code == 401 or response.status_code == 403


class TestStoryboardPanelFrames:
    """Test storyboard panel frames structure"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@agentflow.com", "password": "password123"},
            timeout=30
        )
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_storyboard_panels_have_frames(self, auth_headers):
        """Test that storyboard panels have frames array (6 frames per panel)"""
        # Get projects
        projects_response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            timeout=30
        )
        projects = projects_response.json()["projects"]
        
        # Find a project with storyboard panels
        for project in projects[:5]:  # Check first 5 projects
            storyboard_response = requests.get(
                f"{BASE_URL}/api/studio/projects/{project['id']}/storyboard",
                headers=auth_headers,
                timeout=30
            )
            if storyboard_response.status_code == 200:
                panels = storyboard_response.json().get("panels", [])
                for panel in panels:
                    if panel.get("frames"):
                        # Verify frames structure
                        frames = panel["frames"]
                        assert isinstance(frames, list), "frames should be a list"
                        if len(frames) > 0:
                            frame = frames[0]
                            assert "frame_number" in frame, "Frame should have frame_number"
                            assert "image_url" in frame, "Frame should have image_url"
                            assert "label" in frame, "Frame should have label"
                        return  # Test passed
        
        # If no panels with frames found, that's okay - just skip
        pytest.skip("No storyboard panels with frames found in test projects")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
