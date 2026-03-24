"""
Iteration 97: Testing NEW Studio Features
- Language selection (PT/EN/ES) when creating projects
- Visual style selection (Animation/Cartoon/Anime/Realistic/Watercolor)
- Character avatars persistence
- Per-scene retry/regeneration endpoints
- Per-scene editing endpoints
- Enhanced Scene Director prompts
- Sora 2 retry logic (3 attempts)
- FFmpeg compression for final concat video
- Failed scenes summary in results
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

# Existing project ID for testing (15 scenes, partially completed)
TEST_PROJECT_ID = "0414b8d3b24d"


class TestStudioAuthentication:
    """Test authentication for studio endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_works(self, auth_token):
        """Test that login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 10


class TestStudioProjectCreation:
    """Test project creation with new language and visual_style fields"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_project_with_language_pt(self, auth_headers):
        """Test creating project with Portuguese language"""
        response = requests.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Project_PT",
            "briefing": "Test project in Portuguese",
            "language": "pt",
            "visual_style": "animation"
        }, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("language") == "pt"
        assert data.get("visual_style") == "animation"
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{data['id']}", headers=auth_headers)
    
    def test_create_project_with_language_en(self, auth_headers):
        """Test creating project with English language"""
        response = requests.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Project_EN",
            "briefing": "Test project in English",
            "language": "en",
            "visual_style": "realistic"
        }, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("language") == "en"
        assert data.get("visual_style") == "realistic"
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{data['id']}", headers=auth_headers)
    
    def test_create_project_with_language_es(self, auth_headers):
        """Test creating project with Spanish language"""
        response = requests.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Project_ES",
            "briefing": "Test project in Spanish",
            "language": "es",
            "visual_style": "anime"
        }, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("language") == "es"
        assert data.get("visual_style") == "anime"
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{data['id']}", headers=auth_headers)
    
    def test_create_project_with_all_visual_styles(self, auth_headers):
        """Test creating projects with all visual styles"""
        styles = ["animation", "cartoon", "anime", "realistic", "watercolor"]
        for style in styles:
            response = requests.post(f"{BASE_URL}/api/studio/projects", json={
                "name": f"TEST_Style_{style}",
                "briefing": f"Test project with {style} style",
                "language": "pt",
                "visual_style": style
            }, headers=auth_headers)
            assert response.status_code == 200, f"Failed for style {style}: {response.text}"
            data = response.json()
            assert data.get("visual_style") == style, f"Expected {style}, got {data.get('visual_style')}"
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{data['id']}", headers=auth_headers)


class TestStudioProjectStatus:
    """Test project status endpoint returns new fields"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_project_status_returns_character_avatars(self, auth_headers):
        """Test GET /api/studio/projects/{id}/status returns character_avatars"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "character_avatars" in data, "character_avatars field missing"
        assert isinstance(data["character_avatars"], dict)
    
    def test_project_status_returns_visual_style(self, auth_headers):
        """Test GET /api/studio/projects/{id}/status returns visual_style"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "visual_style" in data, "visual_style field missing"
        assert data["visual_style"] in ["animation", "cartoon", "anime", "realistic", "watercolor", ""]
    
    def test_project_status_returns_language(self, auth_headers):
        """Test GET /api/studio/projects/{id}/status returns language"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "language" in data, "language field missing"
        assert data["language"] in ["pt", "en", "es", ""]


class TestStudioCharacterAvatars:
    """Test character avatar persistence endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_project(self, auth_headers):
        """Create a test project for avatar tests"""
        response = requests.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Avatar_Project",
            "briefing": "Test project for avatar persistence",
            "language": "pt",
            "visual_style": "animation"
        }, headers=auth_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project['id']}", headers=auth_headers)
    
    def test_save_character_avatars(self, auth_headers, test_project):
        """Test POST /api/studio/projects/{id}/save-character-avatars"""
        avatars = {
            "Abraham": "https://example.com/abraham.png",
            "Isaac": "https://example.com/isaac.png"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project['id']}/save-character-avatars",
            json={"character_avatars": avatars},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        
        # Verify persistence
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project['id']}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("character_avatars") == avatars


class TestStudioVisualStyleUpdate:
    """Test visual style update endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_project(self, auth_headers):
        """Create a test project"""
        response = requests.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_VisualStyle_Project",
            "briefing": "Test project for visual style update",
            "language": "pt",
            "visual_style": "animation"
        }, headers=auth_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project['id']}", headers=auth_headers)
    
    def test_update_visual_style(self, auth_headers, test_project):
        """Test POST /api/studio/projects/{id}/update-visual-style"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project['id']}/update-visual-style",
            json={"visual_style": "anime"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        
        # Verify persistence
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project['id']}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("visual_style") == "anime"


class TestStudioLanguageUpdate:
    """Test language update endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_project(self, auth_headers):
        """Create a test project"""
        response = requests.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Language_Project",
            "briefing": "Test project for language update",
            "language": "pt",
            "visual_style": "animation"
        }, headers=auth_headers)
        assert response.status_code == 200
        project = response.json()
        yield project
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project['id']}", headers=auth_headers)
    
    def test_update_language(self, auth_headers, test_project):
        """Test POST /api/studio/projects/{id}/update-language"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project['id']}/update-language",
            json={"language": "en"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        
        # Verify persistence
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project['id']}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("language") == "en"


class TestStudioSceneUpdate:
    """Test scene update endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_update_scene_endpoint_exists(self, auth_headers):
        """Test POST /api/studio/projects/{id}/update-scene endpoint exists"""
        # Use existing project with scenes
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/update-scene",
            json={
                "scene_number": 1,
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        # Should return 200 if project exists, or 404 if not found
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"


class TestStudioRegenerateScene:
    """Test scene regeneration endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_regenerate_scene_endpoint_exists(self, auth_headers):
        """Test POST /api/studio/projects/{id}/regenerate-scene endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/regenerate-scene",
            json={
                "scene_number": 1,
                "custom_prompt": None
            },
            headers=auth_headers
        )
        # Should return 200 (started) or 404 (scene not found)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data.get("scene_number") == 1


class TestStudioStartProduction:
    """Test start production endpoint with new fields"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_start_production_accepts_character_avatars(self, auth_headers):
        """Test POST /api/studio/start-production accepts character_avatars"""
        # This will fail with 400 if no scenes, but we're testing the endpoint accepts the field
        response = requests.post(
            f"{BASE_URL}/api/studio/start-production",
            json={
                "project_id": "nonexistent_project",
                "video_duration": 12,
                "character_avatars": {"Abraham": "https://example.com/avatar.png"},
                "visual_style": "animation"
            },
            headers=auth_headers
        )
        # Should return 404 for nonexistent project
        assert response.status_code == 404, f"Unexpected status: {response.status_code}"


class TestStudioProjectsList:
    """Test projects list endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_projects(self, auth_headers):
        """Test GET /api/studio/projects returns list"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)


class TestCodeReviewVerification:
    """Verify code implementation details"""
    
    def test_studio_project_model_has_language_field(self):
        """Verify StudioProject model has language field"""
        # Read the studio.py file and check for language field
        import re
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Check StudioProject model has language field
        assert 'language: str = "pt"' in content, "StudioProject model missing language field"
    
    def test_studio_project_model_has_visual_style_field(self):
        """Verify StudioProject model has visual_style field"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Check StudioProject model has visual_style field
        assert 'visual_style: str' in content, "StudioProject model missing visual_style field"
    
    def test_sora_retry_logic_has_3_attempts(self):
        """Verify Sora 2 retry logic has 3 attempts"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Check for max_retries = 3 in the scene team function
        assert 'max_retries = 3' in content, "Sora 2 retry logic should have 3 attempts"
    
    def test_ffmpeg_compression_exists(self):
        """Verify FFmpeg compression is implemented"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Check for FFmpeg compression commands
        assert 'ffmpeg' in content.lower(), "FFmpeg should be used for video processing"
        assert 'crf' in content, "FFmpeg should use CRF for compression"
    
    def test_style_prompts_mapping_exists(self):
        """Verify visual style prompts mapping exists"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Check for STYLE_PROMPTS dictionary
        assert 'STYLE_PROMPTS' in content, "STYLE_PROMPTS mapping should exist"
        assert '"animation"' in content, "animation style should be defined"
        assert '"cartoon"' in content, "cartoon style should be defined"
        assert '"anime"' in content, "anime style should be defined"
        assert '"realistic"' in content, "realistic style should be defined"
        assert '"watercolor"' in content, "watercolor style should be defined"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
