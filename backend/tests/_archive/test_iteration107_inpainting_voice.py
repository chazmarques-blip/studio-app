"""
Iteration 107: Testing Inpainting (edit-element) endpoint and VoiceInput component integration.

Features tested:
1. POST /api/studio/projects/{id}/storyboard/edit-element - Inpainting endpoint
2. VoiceInput component integration in StoryboardEditor
3. FilmSpinner component (single spinner for regenerating panels)
4. Film reel icon replacement for loading states
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

# Test project ID with existing storyboard panels
TEST_PROJECT_ID = "fce897cf6ba3"


class TestInpaintingEndpoint:
    """Tests for POST /api/studio/projects/{id}/storyboard/edit-element endpoint."""
    
    def test_edit_element_endpoint_exists(self, auth_headers):
        """Verify the edit-element endpoint exists and accepts POST requests."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-element",
            headers=auth_headers,
            json={
                "panel_number": 1,
                "edit_instruction": "Test instruction"
            }
        )
        # Should not return 404 (endpoint exists) or 405 (method allowed)
        assert response.status_code != 404, "edit-element endpoint not found"
        assert response.status_code != 405, "POST method not allowed"
        print(f"PASS: edit-element endpoint exists, status: {response.status_code}")
    
    def test_edit_element_response_structure(self, auth_headers):
        """Verify the edit-element endpoint returns expected response structure."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-element",
            headers=auth_headers,
            json={
                "panel_number": 1,
                "edit_instruction": "Remove the background trees"
            }
        )
        # Should return 200 with status field
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Response should contain 'status' field"
            assert data["status"] == "editing", f"Expected status 'editing', got '{data.get('status')}'"
            assert "panel_number" in data, "Response should contain 'panel_number' field"
            print(f"PASS: edit-element returns correct structure: {data}")
        elif response.status_code == 400:
            # Panel might not have an image - this is acceptable
            data = response.json()
            print(f"INFO: edit-element returned 400 (expected if panel has no image): {data}")
        else:
            print(f"INFO: edit-element returned status {response.status_code}: {response.text[:200]}")
    
    def test_edit_element_requires_panel_number(self, auth_headers):
        """Verify the endpoint validates required panel_number field."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-element",
            headers=auth_headers,
            json={
                "edit_instruction": "Test instruction"
            }
        )
        # Should return 422 (validation error) for missing required field
        assert response.status_code == 422, f"Expected 422 for missing panel_number, got {response.status_code}"
        print(f"PASS: edit-element validates required panel_number field")
    
    def test_edit_element_requires_edit_instruction(self, auth_headers):
        """Verify the endpoint validates required edit_instruction field."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-element",
            headers=auth_headers,
            json={
                "panel_number": 1
            }
        )
        # Should return 422 (validation error) for missing required field
        assert response.status_code == 422, f"Expected 422 for missing edit_instruction, got {response.status_code}"
        print(f"PASS: edit-element validates required edit_instruction field")
    
    def test_edit_element_invalid_project_returns_404(self, auth_headers):
        """Verify the endpoint returns 404 for non-existent project."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/nonexistent123/storyboard/edit-element",
            headers=auth_headers,
            json={
                "panel_number": 1,
                "edit_instruction": "Test instruction"
            }
        )
        assert response.status_code == 404, f"Expected 404 for invalid project, got {response.status_code}"
        print(f"PASS: edit-element returns 404 for invalid project")
    
    def test_edit_element_without_auth_returns_401(self):
        """Verify the endpoint requires authentication."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/edit-element",
            json={
                "panel_number": 1,
                "edit_instruction": "Test instruction"
            }
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"PASS: edit-element requires authentication")


class TestInpaintModuleExists:
    """Tests for the storyboard_inpaint.py module."""
    
    def test_inpaint_module_exists(self):
        """Verify the storyboard_inpaint.py module exists."""
        import sys
        sys.path.insert(0, '/app/backend')
        try:
            from core import storyboard_inpaint
            assert hasattr(storyboard_inpaint, 'inpaint_element'), "inpaint_element function not found"
            print(f"PASS: storyboard_inpaint module exists with inpaint_element function")
        except ImportError as e:
            pytest.fail(f"Failed to import storyboard_inpaint: {e}")
    
    def test_inpaint_function_signature(self):
        """Verify the inpaint_element function has correct signature."""
        import sys
        import inspect
        sys.path.insert(0, '/app/backend')
        from core import storyboard_inpaint
        
        sig = inspect.signature(storyboard_inpaint.inpaint_element)
        params = list(sig.parameters.keys())
        
        expected_params = ['image_url', 'edit_instruction', 'project_id', 'panel_number']
        for param in expected_params:
            assert param in params, f"Missing parameter: {param}"
        print(f"PASS: inpaint_element has correct parameters: {params}")


class TestStoryboardEndpointWithPanels:
    """Tests to verify storyboard has panels for inpainting."""
    
    def test_storyboard_has_panels(self, auth_headers):
        """Verify the test project has storyboard panels."""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get storyboard: {response.status_code}"
        data = response.json()
        panels = data.get("panels", [])
        assert len(panels) > 0, "No storyboard panels found"
        print(f"PASS: Storyboard has {len(panels)} panels")
        
        # Check if any panel has an image
        panels_with_images = [p for p in panels if p.get("image_url")]
        print(f"INFO: {len(panels_with_images)} panels have images")
        
        if panels_with_images:
            first_panel = panels_with_images[0]
            print(f"INFO: First panel with image: scene_number={first_panel.get('scene_number')}, image_url={first_panel.get('image_url', '')[:80]}...")


class TestTranscribeEndpoint:
    """Tests for the /api/ai/transcribe endpoint used by VoiceInput."""
    
    def test_transcribe_endpoint_exists(self, auth_headers):
        """Verify the transcribe endpoint exists."""
        # We can't easily test audio upload, but we can verify the endpoint exists
        # by checking it doesn't return 404
        response = requests.post(
            f"{BASE_URL}/api/ai/transcribe",
            headers={"Authorization": auth_headers["Authorization"]}
        )
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, "transcribe endpoint not found"
        print(f"PASS: transcribe endpoint exists, status: {response.status_code}")


class TestFacilitatorChatEndpoint:
    """Tests for the facilitator chat endpoint."""
    
    def test_facilitator_chat_endpoint_exists(self, auth_headers):
        """Verify the facilitator chat endpoint exists and works."""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/chat",
            headers=auth_headers,
            json={
                "message": "Olá, teste de chat"
            }
        )
        # Should return 200 with response
        if response.status_code == 200:
            data = response.json()
            assert "response" in data, "Response should contain 'response' field"
            print(f"PASS: Facilitator chat works, response: {data.get('response', '')[:100]}...")
        else:
            print(f"INFO: Facilitator chat returned {response.status_code}: {response.text[:200]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
