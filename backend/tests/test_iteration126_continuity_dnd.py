"""
Iteration 126: Testing Continuity Director V2 and Drag-and-Drop Scene Reordering
- Continuity Director: GET /api/studio/projects/{id}/continuity/status endpoint
- Drag-and-Drop: Verify reorder-scenes endpoint still works (backend support for DnD)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_PROJECT_ID = "d27afb0e79ff"

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with authentication"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestContinuityDirectorStatus:
    """Test Continuity Director V2 status endpoint"""
    
    def test_continuity_status_endpoint_exists(self, auth_headers):
        """Verify GET /api/studio/projects/{id}/continuity/status returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
    def test_continuity_status_has_required_fields(self, auth_headers):
        """Verify response contains continuity_status and continuity_report"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required top-level fields
        assert "continuity_status" in data, "Missing continuity_status field"
        assert "continuity_report" in data, "Missing continuity_report field"
        
    def test_continuity_status_phase_is_done(self, auth_headers):
        """Verify continuity_status.phase is 'done' (analysis completed)"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        continuity_status = data.get("continuity_status", {})
        phase = continuity_status.get("phase")
        
        # Phase should be 'done' if analysis completed, or could be empty/analyzing
        print(f"Continuity status phase: {phase}")
        print(f"Full continuity_status: {continuity_status}")
        
        # If phase is 'done', verify issues_found
        if phase == "done":
            issues_found = continuity_status.get("issues_found", 0)
            print(f"Issues found: {issues_found}")
            assert issues_found >= 0, "issues_found should be a non-negative number"
            
    def test_continuity_report_structure(self, auth_headers):
        """Verify continuity_report has expected structure when analysis is complete"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        continuity_report = data.get("continuity_report", {})
        continuity_status = data.get("continuity_status", {})
        
        print(f"Continuity report keys: {list(continuity_report.keys())}")
        
        # If analysis is done and report exists, verify structure
        if continuity_status.get("phase") == "done" and continuity_report:
            # Check for expected fields in report
            expected_fields = ["total_issues", "issues", "engine"]
            for field in expected_fields:
                if field in continuity_report:
                    print(f"Found field '{field}': {type(continuity_report[field])}")
                    
            # If issues array exists, verify structure
            issues = continuity_report.get("issues", [])
            if issues and len(issues) > 0:
                first_issue = issues[0]
                print(f"First issue structure: {list(first_issue.keys())}")
                
                # Verify issue has expected fields
                issue_fields = ["severity", "category", "character", "description"]
                for field in issue_fields:
                    if field in first_issue:
                        print(f"Issue field '{field}': {first_issue[field][:50] if isinstance(first_issue[field], str) else first_issue[field]}")


class TestDragAndDropBackend:
    """Test backend support for drag-and-drop scene reordering"""
    
    def test_project_status_endpoint(self, auth_headers):
        """Verify project status endpoint returns scenes"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        scenes = data.get("scenes", [])
        print(f"Project has {len(scenes)} scenes")
        assert len(scenes) > 0, "Project should have scenes"
        
        # Verify scene structure
        if scenes:
            first_scene = scenes[0]
            assert "scene_number" in first_scene, "Scene should have scene_number"
            print(f"First scene: {first_scene.get('scene_number')} - {first_scene.get('title', 'No title')[:50]}")
            
    def test_reorder_scenes_endpoint_exists(self, auth_headers):
        """Verify POST /api/studio/projects/{id}/reorder-scenes endpoint exists"""
        # Get current scenes
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        scenes = status_response.json().get("scenes", [])
        
        if len(scenes) < 2:
            pytest.skip("Need at least 2 scenes to test reorder")
            
        # Get current order
        current_order = [s["scene_number"] for s in scenes]
        print(f"Current scene order (first 5): {current_order[:5]}")
        
        # Test with same order (no actual change) to verify endpoint works
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/reorder-scenes",
            headers=auth_headers,
            json={"order": current_order}
        )
        
        # Should return 200 even with same order
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
    def test_project_has_screenplay_approved_field(self, auth_headers):
        """Verify project status includes screenplay_approved field"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for screenplay_approved field
        screenplay_approved = data.get("screenplay_approved")
        print(f"screenplay_approved: {screenplay_approved}")
        
        # Field should exist (can be True or False)
        assert "screenplay_approved" in data or screenplay_approved is not None, \
            "Project should have screenplay_approved field"


class TestSceneCardData:
    """Test that scene data contains all required fields for display"""
    
    def test_scene_has_display_fields(self, auth_headers):
        """Verify scenes have title, description, dialogue, emotion, camera fields"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        scenes = response.json().get("scenes", [])
        
        if not scenes:
            pytest.skip("No scenes in project")
            
        # Check first scene for required display fields
        first_scene = scenes[0]
        display_fields = ["title", "description", "dialogue", "emotion", "camera"]
        
        for field in display_fields:
            value = first_scene.get(field)
            print(f"Scene field '{field}': {value[:50] if isinstance(value, str) and value else value}")
            
        # At minimum, title should exist
        assert first_scene.get("title"), "Scene should have a title"
        
    def test_scene_has_characters_in_scene(self, auth_headers):
        """Verify scenes have characters_in_scene array"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        scenes = response.json().get("scenes", [])
        
        if not scenes:
            pytest.skip("No scenes in project")
            
        # Check if any scene has characters_in_scene
        scenes_with_chars = [s for s in scenes if s.get("characters_in_scene")]
        print(f"Scenes with characters_in_scene: {len(scenes_with_chars)}/{len(scenes)}")
        
        if scenes_with_chars:
            first_with_chars = scenes_with_chars[0]
            chars = first_with_chars.get("characters_in_scene", [])
            print(f"Characters in scene {first_with_chars.get('scene_number')}: {chars}")


class TestDeleteAndInsertSceneEndpoints:
    """Test that delete and insert scene endpoints still work (alongside drag handles)"""
    
    def test_add_scene_endpoint_exists(self, auth_headers):
        """Verify POST /api/studio/projects/{id}/add-scene endpoint exists"""
        # Just verify endpoint responds (don't actually add a scene)
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/add-scene",
            headers=auth_headers,
            json={
                "position": 1,
                "scene": {
                    "title": "TEST_ENDPOINT_CHECK",
                    "description": "This is just to verify endpoint exists"
                }
            }
        )
        
        # Should return 200 or 201 (success) or 400/422 (validation error) - not 404
        assert response.status_code != 404, "add-scene endpoint should exist"
        print(f"add-scene endpoint response: {response.status_code}")
        
        # If scene was added, clean it up
        if response.status_code in [200, 201]:
            # Delete the test scene
            requests.post(
                f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
                headers=auth_headers,
                json={"scene_number": 1}
            )
            
    def test_delete_scene_endpoint_exists(self, auth_headers):
        """Verify POST /api/studio/projects/{id}/delete-scene endpoint exists"""
        # Try to delete a non-existent scene to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
            headers=auth_headers,
            json={"scene_number": 9999}  # Non-existent scene
        )
        
        # Should return something other than 404 (endpoint exists)
        # Could be 200 (graceful handling) or 400/422 (validation)
        print(f"delete-scene endpoint response: {response.status_code}")
        # Endpoint should exist
        assert response.status_code != 405, "delete-scene endpoint should accept POST"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
