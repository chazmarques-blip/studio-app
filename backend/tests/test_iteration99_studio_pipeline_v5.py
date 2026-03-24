"""
Iteration 99: Testing Directed Studio Pipeline v5 - Pre-Production Intelligence
Tests for:
1. Backend server health and API availability
2. Authentication with test credentials
3. Studio projects CRUD operations
4. Screenwriter chat endpoint
5. New helper functions importability (_analyze_avatars_with_vision, _build_production_design, _create_composite_avatar)
6. DirectSora2Client class availability
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestHealthAndAuth:
    """Basic health check and authentication tests"""
    
    def test_health_endpoint(self):
        """Test backend health check"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: Health check returns status=ok")
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        print(f"PASS: Login successful with {TEST_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"},
            timeout=15
        )
        assert response.status_code == 401
        print(f"PASS: Invalid login returns 401")


class TestStudioProjectsAPI:
    """Studio projects CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_studio_projects(self):
        """Test GET /api/studio/projects endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        print(f"PASS: GET /api/studio/projects returns {len(data['projects'])} projects")
    
    def test_create_studio_project(self):
        """Test POST /api/studio/projects creates a new project"""
        project_data = {
            "name": f"TEST_Pipeline_v5_{int(time.time())}",
            "briefing": "Test project for Pipeline v5 testing",
            "language": "pt",
            "visual_style": "animation"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json=project_data,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data.get("name") == project_data["name"]
        assert data.get("visual_style") == "animation"
        assert data.get("language") == "pt"
        print(f"PASS: Created project with id={data['id']}")
        
        # Cleanup - delete the test project
        project_id = data["id"]
        delete_response = requests.delete(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=self.headers,
            timeout=15
        )
        assert delete_response.status_code == 200
        print(f"PASS: Deleted test project {project_id}")
    
    def test_studio_chat_endpoint(self):
        """Test POST /api/studio/chat sends message to screenwriter"""
        # First create a project
        project_data = {
            "name": f"TEST_Chat_{int(time.time())}",
            "briefing": "Test chat project",
            "language": "pt"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json=project_data,
            timeout=15
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        # Send chat message
        chat_data = {
            "project_id": project_id,
            "message": "Create a simple test story",
            "language": "pt"
        }
        chat_response = requests.post(
            f"{BASE_URL}/api/studio/chat",
            headers=self.headers,
            json=chat_data,
            timeout=20
        )
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert "project_id" in data
        assert data.get("status") in ["thinking", "done"]
        print(f"PASS: Chat endpoint returns status={data.get('status')}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=self.headers,
            timeout=15
        )
    
    def test_get_project_status(self):
        """Test GET /api/studio/projects/{id}/status endpoint"""
        # First create a project
        project_data = {
            "name": f"TEST_Status_{int(time.time())}",
            "briefing": "Test status project",
            "language": "pt"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json=project_data,
            timeout=15
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]
        
        # Get status
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=self.headers,
            timeout=15
        )
        assert status_response.status_code == 200
        data = status_response.json()
        assert "status" in data
        assert "scenes" in data
        assert "characters" in data
        print(f"PASS: Project status endpoint returns status={data.get('status')}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=self.headers,
            timeout=15
        )


class TestHelperFunctionsImportability:
    """Test that new helper functions are importable"""
    
    def test_analyze_avatars_with_vision_importable(self):
        """Test _analyze_avatars_with_vision function is importable"""
        import sys
        backend_path = '/app/backend'
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        try:
            from routers.studio import _analyze_avatars_with_vision
            assert callable(_analyze_avatars_with_vision)
            print("PASS: _analyze_avatars_with_vision is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _analyze_avatars_with_vision: {e}")
    
    def test_build_production_design_importable(self):
        """Test _build_production_design function is importable"""
        import sys
        backend_path = '/app/backend'
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        try:
            from routers.studio import _build_production_design
            assert callable(_build_production_design)
            print("PASS: _build_production_design is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _build_production_design: {e}")
    
    def test_create_composite_avatar_importable(self):
        """Test _create_composite_avatar function is importable"""
        import sys
        backend_path = '/app/backend'
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        try:
            from routers.studio import _create_composite_avatar
            assert callable(_create_composite_avatar)
            print("PASS: _create_composite_avatar is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _create_composite_avatar: {e}")
    
    def test_direct_sora2_client_importable(self):
        """Test DirectSora2Client class is importable"""
        import sys
        backend_path = '/app/backend'
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        try:
            from core.llm import DirectSora2Client
            assert DirectSora2Client is not None
            # Test instantiation
            client = DirectSora2Client(api_key="test-key")
            assert hasattr(client, 'text_to_video')
            print("PASS: DirectSora2Client is importable and has text_to_video method")
        except ImportError as e:
            pytest.fail(f"Failed to import DirectSora2Client: {e}")


class TestStudioVoicesAndMusic:
    """Test studio voices and music library endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_voices(self):
        """Test GET /api/studio/voices endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/studio/voices",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        print(f"PASS: GET /api/studio/voices returns {len(data.get('voices', []))} voices")
    
    def test_get_music_library(self):
        """Test GET /api/studio/music-library endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/studio/music-library",
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        print(f"PASS: GET /api/studio/music-library returns {len(data.get('tracks', []))} tracks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
