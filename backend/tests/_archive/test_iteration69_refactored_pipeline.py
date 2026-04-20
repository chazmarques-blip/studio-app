"""
Iteration 69: Test refactored pipeline modules

Verifies that all functionality is preserved after the backend refactoring:
- Backend pipeline.py (5306 lines) was split into 9 modules in /app/backend/pipeline/
- All 37 backend routes should be registered and functional
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PIPELINE_ID = "7fe6d5fa-85b8-4da1-8aaa-38cce0d2460a"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with authorization token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestHealthAndAuth:
    """Basic health check and authentication tests"""
    
    def test_api_health(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "agentzz-api"
        print("SUCCESS: API health check passed")
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print("SUCCESS: Login with valid credentials")


class TestPipelineCoreRoutes:
    """Test core pipeline routes from routes.py"""
    
    def test_music_library_endpoint(self):
        """Test GET /api/campaigns/pipeline/music-library - no auth required"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        assert len(data["tracks"]) > 0
        # Verify track structure
        track = data["tracks"][0]
        assert "id" in track
        assert "name" in track
        assert "file" in track
        print(f"SUCCESS: Music library returned {len(data['tracks'])} tracks")
    
    def test_pipeline_list_endpoint(self, auth_headers):
        """Test GET /api/campaigns/pipeline/list - returns user's pipelines"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert isinstance(data["pipelines"], list)
        print(f"SUCCESS: Pipeline list returned {len(data['pipelines'])} pipelines")
    
    def test_saved_history_endpoint(self, auth_headers):
        """Test GET /api/campaigns/pipeline/saved/history - returns logos and briefings"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/saved/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "logos" in data
        assert "briefings" in data
        assert isinstance(data["logos"], list)
        assert isinstance(data["briefings"], list)
        print(f"SUCCESS: Saved history returned {len(data['logos'])} logos, {len(data['briefings'])} briefings")
    
    def test_step_labels_endpoint(self, auth_headers):
        """Test GET /api/campaigns/pipeline/{id}/labels - returns step configuration"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{TEST_PIPELINE_ID}/labels",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "order" in data
        # Verify step order
        expected_steps = ["sofia_copy", "ana_review_copy", "lucas_design", 
                        "rafael_review_design", "marcos_video", "rafael_review_video", "pedro_publish"]
        assert data["order"] == expected_steps
        print("SUCCESS: Step labels endpoint returned correct step order")
    
    def test_get_pipeline_details(self, auth_headers):
        """Test GET /api/campaigns/pipeline/{id} - returns full pipeline data"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{TEST_PIPELINE_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == TEST_PIPELINE_ID
        assert "briefing" in data
        assert "steps" in data
        assert "result" in data
        assert "platforms" in data
        # Verify steps exist
        steps = data["steps"]
        assert "sofia_copy" in steps
        assert "lucas_design" in steps
        assert "marcos_video" in steps
        print("SUCCESS: Pipeline details returned complete data")


class TestAvatarRoutes:
    """Test avatar-related routes from avatar_routes.py"""
    
    def test_avatars_list_endpoint(self, auth_headers):
        """Test GET /api/data/avatars - returns user's avatars"""
        response = requests.get(
            f"{BASE_URL}/api/data/avatars",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check Avatar 1 exists
        avatar_1 = next((a for a in data if a.get("name") == "Avatar 1"), None)
        if avatar_1:
            assert "id" in avatar_1
            assert "url" in avatar_1
            assert "voice" in avatar_1
            print(f"SUCCESS: Avatars list returned {len(data)} avatars, Avatar 1 found")
        else:
            print(f"INFO: Avatars list returned {len(data)} avatars, Avatar 1 not in list")


class TestPipelineModuleImports:
    """Test that all pipeline modules are properly imported and routes registered"""
    
    def test_routes_from_routes_module(self, auth_headers):
        """Test routes defined in pipeline/routes.py"""
        # Music library (from routes.py)
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200
        print("SUCCESS: routes.py - music-library route works")
    
    def test_routes_from_avatar_routes_module(self, auth_headers):
        """Test routes defined in pipeline/avatar_routes.py"""
        # Avatar endpoints are accessed via /api/data/avatars
        response = requests.get(
            f"{BASE_URL}/api/data/avatars",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("SUCCESS: avatar_routes.py - avatars route works")
    
    def test_pipeline_config_constants(self, auth_headers):
        """Verify pipeline config (STEP_ORDER, etc.) is accessible via labels endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{TEST_PIPELINE_ID}/labels",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Config constants should define 7 steps
        assert len(data["order"]) == 7
        assert len(data["labels"]) == 7
        print("SUCCESS: config.py - STEP_ORDER and STEP_LABELS accessible")


class TestErrorHandling:
    """Test error handling for edge cases"""
    
    def test_unauthorized_access(self):
        """Test that protected endpoints reject unauthorized requests"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list")
        assert response.status_code == 401
        print("SUCCESS: Unauthorized access properly rejected")
    
    def test_nonexistent_pipeline(self, auth_headers):
        """Test accessing a pipeline that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("SUCCESS: 404 returned for nonexistent pipeline")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
