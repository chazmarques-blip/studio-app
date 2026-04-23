"""
Test suite for Mindset Templates (Dream Teams) feature
Tests: GET /api/studio/agents/mindset-templates, POST /apply, POST /deactivate
Also tests DELETE /api/studio/projects/{id} regression
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"

# Expected template IDs
EXPECTED_TEMPLATE_IDS = [
    "cinema_arte",
    "blockbuster", 
    "animacao_pixar",
    "documentario",
    "noir_suspense",
    "infantil_picturebook",
    "bibizoo",
    "bibizoo_baby",
    "petz_genius"
]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data.get("access_token")
    assert token, "No access_token in response"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestMindsetTemplatesList:
    """Tests for GET /api/studio/agents/mindset-templates"""
    
    def test_list_templates_returns_200(self, auth_headers):
        """Endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindset-templates", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_list_templates_returns_9_templates(self, auth_headers):
        """Should return exactly 9 templates"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindset-templates", headers=auth_headers)
        data = response.json()
        templates = data.get("templates", [])
        assert len(templates) == 9, f"Expected 9 templates, got {len(templates)}"
    
    def test_list_templates_has_all_expected_ids(self, auth_headers):
        """All 9 expected template IDs should be present"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindset-templates", headers=auth_headers)
        data = response.json()
        templates = data.get("templates", [])
        template_ids = [t.get("id") for t in templates]
        
        for expected_id in EXPECTED_TEMPLATE_IDS:
            assert expected_id in template_ids, f"Missing template: {expected_id}"
    
    def test_list_templates_has_count_field(self, auth_headers):
        """Response should have count field"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindset-templates", headers=auth_headers)
        data = response.json()
        assert "count" in data, "Missing 'count' field"
        assert data["count"] == 9, f"Expected count=9, got {data['count']}"
    
    def test_list_templates_has_active_by_category(self, auth_headers):
        """Response should have active_by_category field"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindset-templates", headers=auth_headers)
        data = response.json()
        assert "active_by_category" in data, "Missing 'active_by_category' field"
    
    def test_bibizoo_template_structure(self, auth_headers):
        """Bibizoo template should have correct structure"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindset-templates", headers=auth_headers)
        data = response.json()
        templates = data.get("templates", [])
        
        bibizoo = next((t for t in templates if t.get("id") == "bibizoo"), None)
        assert bibizoo is not None, "Bibizoo template not found"
        
        # Check required fields
        assert bibizoo.get("name") == "Bibizoo (6–9 anos)", f"Wrong name: {bibizoo.get('name')}"
        assert bibizoo.get("emoji") == "🦁", f"Wrong emoji: {bibizoo.get('emoji')}"
        assert bibizoo.get("category") == "video", f"Wrong category: {bibizoo.get('category')}"
        assert "agents" in bibizoo, "Missing 'agents' field"
        assert len(bibizoo.get("agents", [])) >= 4, f"Expected at least 4 agents, got {len(bibizoo.get('agents', []))}"
        
        # Check screenwriter agent has Phil Lord & Christopher Miller
        screenwriter = next((a for a in bibizoo.get("agents", []) if a.get("agent_id") == "screenwriter_agent"), None)
        assert screenwriter is not None, "screenwriter_agent not found in bibizoo"
        assert screenwriter.get("master_reference") == "Phil Lord & Christopher Miller", f"Wrong master_reference: {screenwriter.get('master_reference')}"


class TestMindsetTemplatesApply:
    """Tests for POST /api/studio/agents/mindset-templates/apply"""
    
    def test_apply_bibizoo_returns_200(self, auth_headers):
        """Apply bibizoo template should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_apply_bibizoo_response_structure(self, auth_headers):
        """Apply response should have correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        data = response.json()
        
        assert data.get("status") == "applied", f"Expected status='applied', got {data.get('status')}"
        assert data.get("template_id") == "bibizoo", f"Expected template_id='bibizoo', got {data.get('template_id')}"
        assert data.get("template_name") == "Bibizoo (6–9 anos)", f"Wrong template_name: {data.get('template_name')}"
        assert data.get("category") == "video", f"Expected category='video', got {data.get('category')}"
        assert data.get("mindset_activated") == True, "mindset_activated should be True"
        assert "agents_updated" in data, "Missing 'agents_updated' field"
    
    def test_apply_bibizoo_updates_mindset_file(self, auth_headers):
        """After apply, mindsets.json should have template_id='bibizoo' and active=true"""
        # Apply template
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        
        # Check mindset via API
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get mindset: {response.text}"
        
        data = response.json()
        mindset = data.get("mindset", {})
        
        assert mindset.get("active") == True, f"Expected active=True, got {mindset.get('active')}"
        assert mindset.get("template_id") == "bibizoo", f"Expected template_id='bibizoo', got {mindset.get('template_id')}"
    
    def test_apply_bibizoo_updates_screenwriter_agent(self, auth_headers):
        """After apply, screenwriter_agent should have master_reference='Phil Lord & Christopher Miller'"""
        # Apply template
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        
        # Check agent via API
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get agent: {response.text}"
        
        data = response.json()
        agent = data.get("agent", {})
        
        assert agent.get("master_reference") == "Phil Lord & Christopher Miller", \
            f"Expected master_reference='Phil Lord & Christopher Miller', got {agent.get('master_reference')}"
    
    def test_apply_invalid_template_returns_404(self, auth_headers):
        """Apply with invalid template_id should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "invalid_template_xyz", "category": "video"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestMindsetTemplatesDeactivate:
    """Tests for POST /api/studio/agents/mindset-templates/deactivate"""
    
    def test_deactivate_returns_200(self, auth_headers):
        """Deactivate should return 200"""
        # First apply a template
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        
        # Then deactivate
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/deactivate",
            headers=auth_headers,
            params={"category": "video"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_deactivate_response_structure(self, auth_headers):
        """Deactivate response should have correct structure"""
        # First apply
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        
        # Then deactivate
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/deactivate",
            headers=auth_headers,
            params={"category": "video"}
        )
        data = response.json()
        
        assert data.get("status") == "deactivated", f"Expected status='deactivated', got {data.get('status')}"
        assert data.get("category") == "video", f"Expected category='video', got {data.get('category')}"
    
    def test_deactivate_updates_mindset_file(self, auth_headers):
        """After deactivate, mindsets.json should have active=false"""
        # First apply
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "bibizoo", "category": "video"}
        )
        
        # Then deactivate
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/deactivate",
            headers=auth_headers,
            params={"category": "video"}
        )
        
        # Check mindset via API
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        data = response.json()
        mindset = data.get("mindset", {})
        
        assert mindset.get("active") == False, f"Expected active=False, got {mindset.get('active')}"


class TestEditHistory:
    """Tests for edit_history after apply/deactivate"""
    
    def test_apply_adds_edit_history_to_mindset(self, auth_headers):
        """After apply, mindset should have new edit_history entry"""
        # Get initial history count
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        initial_history = len(response.json().get("mindset", {}).get("edit_history", []))
        
        # Apply template
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "cinema_arte", "category": "video"}
        )
        
        # Check history increased
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        new_history = len(response.json().get("mindset", {}).get("edit_history", []))
        
        assert new_history > initial_history, f"Expected history to increase, was {initial_history}, now {new_history}"
    
    def test_apply_adds_edit_history_to_agents(self, auth_headers):
        """After apply, affected agents should have new edit_history entries"""
        # Get initial history count for screenwriter
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        initial_history = len(response.json().get("agent", {}).get("edit_history", []))
        
        # Apply template
        requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/apply",
            headers=auth_headers,
            json={"template_id": "blockbuster", "category": "video"}
        )
        
        # Check history increased
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        new_history = len(response.json().get("agent", {}).get("edit_history", []))
        
        assert new_history > initial_history, f"Expected agent history to increase, was {initial_history}, now {new_history}"


class TestDeleteProjectRegression:
    """Regression test for DELETE /api/studio/projects/{id}"""
    
    def test_create_and_delete_project(self, auth_headers):
        """Create a test project and delete it"""
        # Create project
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json={
                "name": "TEST_EXCLUIR_MINDSET_TEST",
                "briefing": "Test project for delete regression",
                "output_mode": "video"
            }
        )
        assert create_response.status_code in [200, 201], f"Failed to create project: {create_response.text}"
        
        project_id = create_response.json().get("id")
        assert project_id, "No project ID returned"
        
        # Delete project
        delete_response = requests.delete(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        # Verify project is gone
        get_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404, f"Project should be deleted, but got {get_response.status_code}"


class TestCleanup:
    """Cleanup: deactivate mindset after tests"""
    
    def test_cleanup_deactivate_mindset(self, auth_headers):
        """Deactivate mindset to leave clean state"""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/mindset-templates/deactivate",
            headers=auth_headers,
            params={"category": "video"}
        )
        assert response.status_code == 200, f"Cleanup failed: {response.text}"
        
        # Verify deactivated
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        mindset = response.json().get("mindset", {})
        assert mindset.get("active") == False, "Mindset should be deactivated after cleanup"
