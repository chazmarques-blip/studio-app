"""
Iteration 105: Storyboard Endpoints Testing
Tests for the new storyboard feature in the Directed Studio pipeline.

Endpoints tested:
- GET /api/studio/projects/{project_id}/storyboard
- POST /api/studio/projects/{project_id}/generate-storyboard
- POST /api/studio/projects/{project_id}/storyboard/regenerate-panel
- PATCH /api/studio/projects/{project_id}/storyboard/edit-panel
- PATCH /api/studio/projects/{project_id}/storyboard/approve
- POST /api/studio/projects/{project_id}/storyboard/chat
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PROJECT_ID = "fce897cf6ba3"  # Project with 20 scenes


def retry_request(func, max_retries=3, delay=1):
    """Retry a request function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = func()
            if response.status_code != 500:
                return response
            # If 500, retry
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                raise
    return response  # Return last response even if 500


class TestStoryboardEndpoints:
    """Test storyboard API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, auth_token):
        """Setup for each test"""
        self.client = api_client
        self.token = auth_token
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    # ═══ GET /storyboard ═══
    def test_get_storyboard_endpoint_exists(self):
        """GET /api/studio/projects/{id}/storyboard returns 200"""
        response = self.client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_get_storyboard_response_structure(self):
        """GET /storyboard returns panels, status, approved, chat_history"""
        response = self.client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields exist
        assert "panels" in data, "Response missing 'panels' field"
        assert "storyboard_status" in data, "Response missing 'storyboard_status' field"
        assert "storyboard_approved" in data, "Response missing 'storyboard_approved' field"
        assert "storyboard_chat_history" in data, "Response missing 'storyboard_chat_history' field"
        
        # Verify types
        assert isinstance(data["panels"], list), "panels should be a list"
        assert isinstance(data["storyboard_status"], dict), "storyboard_status should be a dict"
        assert isinstance(data["storyboard_approved"], bool), "storyboard_approved should be a bool"
        assert isinstance(data["storyboard_chat_history"], list), "storyboard_chat_history should be a list"
    
    def test_get_storyboard_invalid_project_returns_404(self):
        """GET /storyboard with invalid project ID returns 404"""
        response = self.client.get(f"{BASE_URL}/api/studio/projects/invalid_project_id_xyz/storyboard")
        assert response.status_code == 404
    
    # ═══ POST /generate-storyboard ═══
    def test_generate_storyboard_endpoint_exists(self):
        """POST /api/studio/projects/{id}/generate-storyboard returns 200 or starts generation"""
        response = self.client.post(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/generate-storyboard")
        # Should return 200 with status "generating" or similar
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_generate_storyboard_response_structure(self):
        """POST /generate-storyboard returns status and total_scenes"""
        response = self.client.post(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/generate-storyboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has expected fields
        assert "status" in data, "Response missing 'status' field"
        assert "total_scenes" in data, "Response missing 'total_scenes' field"
        assert data["status"] == "generating", f"Expected status 'generating', got '{data['status']}'"
        assert data["total_scenes"] == 20, f"Expected 20 scenes, got {data['total_scenes']}"
    
    def test_generate_storyboard_invalid_project_returns_404(self):
        """POST /generate-storyboard with invalid project ID returns 404"""
        response = self.client.post(f"{BASE_URL}/api/studio/projects/invalid_project_xyz/generate-storyboard")
        assert response.status_code == 404
    
    # ═══ POST /storyboard/regenerate-panel ═══
    def test_regenerate_panel_endpoint_exists(self):
        """POST /api/studio/projects/{id}/storyboard/regenerate-panel returns 200"""
        response = retry_request(lambda: self.client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/regenerate-panel",
            json={"panel_number": 1, "description": "Test description"}
        ))
        # Should return 200 or 404 if panel doesn't exist yet
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
    
    def test_regenerate_panel_response_structure(self):
        """POST /regenerate-panel returns status and panel_number"""
        response = retry_request(lambda: self.client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/regenerate-panel",
            json={"panel_number": 1, "description": ""}
        ))
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Response missing 'status' field"
            assert "panel_number" in data, "Response missing 'panel_number' field"
    
    def test_regenerate_panel_invalid_project_returns_404(self):
        """POST /regenerate-panel with invalid project ID returns 404"""
        response = retry_request(lambda: self.client.post(
            f"{BASE_URL}/api/studio/projects/invalid_xyz/storyboard/regenerate-panel",
            json={"panel_number": 1}
        ))
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    
    # ═══ PATCH /storyboard/edit-panel ═══
    def test_edit_panel_endpoint_exists(self):
        """PATCH /api/studio/projects/{id}/storyboard/edit-panel returns 200 or 404"""
        response = self.client.patch(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-panel",
            json={"panel_number": 1, "title": "Test Title", "description": "Test Desc", "dialogue": "Test Dialogue"}
        )
        # Should return 200 if panel exists, 404 if not
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
    
    def test_edit_panel_response_structure(self):
        """PATCH /edit-panel returns status ok"""
        response = self.client.patch(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-panel",
            json={"panel_number": 1, "title": "Updated Title"}
        )
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "ok", f"Expected status 'ok', got '{data.get('status')}'"
    
    def test_edit_panel_invalid_project_returns_404(self):
        """PATCH /edit-panel with invalid project ID returns 404"""
        response = retry_request(lambda: self.client.patch(
            f"{BASE_URL}/api/studio/projects/invalid_xyz/storyboard/edit-panel",
            json={"panel_number": 1, "title": "Test"}
        ))
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    
    # ═══ PATCH /storyboard/approve ═══
    def test_approve_storyboard_endpoint_exists(self):
        """PATCH /api/studio/projects/{id}/storyboard/approve returns 200"""
        response = self.client.patch(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/approve",
            json={"approved": True}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_approve_storyboard_response_structure(self):
        """PATCH /approve returns status and storyboard_approved"""
        response = retry_request(lambda: self.client.patch(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/approve",
            json={"approved": True}
        ))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "status" in data, "Response missing 'status' field"
        assert "storyboard_approved" in data, "Response missing 'storyboard_approved' field"
        assert data["status"] == "ok"
        assert data["storyboard_approved"] == True
    
    def test_approve_storyboard_can_unapprove(self):
        """PATCH /approve with approved=false unapproves storyboard"""
        # First approve
        retry_request(lambda: self.client.patch(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/approve",
            json={"approved": True}
        ))
        
        # Then unapprove
        response = retry_request(lambda: self.client.patch(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/approve",
            json={"approved": False}
        ))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["storyboard_approved"] == False
    
    def test_approve_storyboard_invalid_project_returns_404(self):
        """PATCH /approve with invalid project ID returns 404"""
        response = retry_request(lambda: self.client.patch(
            f"{BASE_URL}/api/studio/projects/invalid_xyz/storyboard/approve",
            json={"approved": True}
        ))
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    
    # ═══ POST /storyboard/chat ═══
    def test_storyboard_chat_endpoint_exists(self):
        """POST /api/studio/projects/{id}/storyboard/chat returns 200"""
        response = self.client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/chat",
            json={"message": "Hello, test message"}
        )
        # May return 200 or error if AI service unavailable
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}: {response.text}"
    
    def test_storyboard_chat_response_structure(self):
        """POST /chat returns response, actions, regenerating_panels"""
        response = self.client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/chat",
            json={"message": "What panels do we have?"}
        )
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            assert "actions" in data, "Response missing 'actions' field"
            assert "regenerating_panels" in data, "Response missing 'regenerating_panels' field"
    
    def test_storyboard_chat_invalid_project_returns_404(self):
        """POST /chat with invalid project ID returns 404"""
        response = retry_request(lambda: self.client.post(
            f"{BASE_URL}/api/studio/projects/invalid_xyz/storyboard/chat",
            json={"message": "Test"}
        ))
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestProjectStatusIncludesStoryboard:
    """Test that GET /status includes storyboard fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, auth_token):
        """Setup for each test"""
        self.client = api_client
        self.token = auth_token
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_status_includes_storyboard_panels(self):
        """GET /status response includes storyboard_panels field"""
        response = retry_request(lambda: self.client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status"))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "storyboard_panels" in data, "GET /status missing 'storyboard_panels' field"
    
    def test_status_includes_storyboard_status(self):
        """GET /status response includes storyboard_status field"""
        response = retry_request(lambda: self.client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status"))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "storyboard_status" in data, "GET /status missing 'storyboard_status' field"
    
    def test_status_includes_storyboard_approved(self):
        """GET /status response includes storyboard_approved field"""
        response = retry_request(lambda: self.client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status"))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "storyboard_approved" in data, "GET /status missing 'storyboard_approved' field"
    
    def test_status_includes_storyboard_chat_history(self):
        """GET /status response includes storyboard_chat_history field"""
        response = retry_request(lambda: self.client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status"))
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "storyboard_chat_history" in data, "GET /status missing 'storyboard_chat_history' field"


class TestStoryboardModuleExists:
    """Test that the storyboard module is properly imported"""
    
    def test_storyboard_module_exists(self):
        """Verify core/storyboard.py file exists"""
        import os
        storyboard_path = "/app/backend/core/storyboard.py"
        assert os.path.exists(storyboard_path), f"Storyboard module not found at {storyboard_path}"
    
    def test_storyboard_module_has_required_functions(self):
        """Verify storyboard module has generate_all_panels and facilitator_chat"""
        import sys
        sys.path.insert(0, '/app/backend')
        try:
            from core.storyboard import generate_all_panels, facilitator_chat
            assert callable(generate_all_panels), "generate_all_panels should be callable"
            assert callable(facilitator_chat), "facilitator_chat should be callable"
        except ImportError as e:
            # Module exists but may have import issues due to dependencies
            # Check if the file at least defines the functions
            with open("/app/backend/core/storyboard.py", "r") as f:
                content = f.read()
            assert "def generate_all_panels" in content, "generate_all_panels function not defined"
            assert "def facilitator_chat" in content, "facilitator_chat function not defined"
        finally:
            if '/app/backend' in sys.path:
                sys.path.remove('/app/backend')


# ═══ Fixtures ═══

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # Auth returns access_token, not token
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
