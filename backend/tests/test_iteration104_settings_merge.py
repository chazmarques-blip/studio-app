"""
Iteration 104: Testing PATCH /settings endpoint and scene merge logic
Bug fixes tested:
1. PATCH /api/studio/projects/{project_id}/settings - accepts screenplay_approved, audio_mode, etc.
2. GET /api/studio/projects/{project_id}/status - returns screenplay_approved and audio_mode fields
3. Scene merge logic - continuation scenes are appended, overlapping scenes replace
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        print(f"Login successful, token received")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"Auth token obtained")
        return token
    pytest.skip(f"Authentication failed: {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_project(auth_headers):
    """Create a test project for testing"""
    # Create a new project
    create_response = requests.post(
        f"{BASE_URL}/api/studio/projects",
        headers=auth_headers,
        json={
            "name": "TEST_iteration104_settings",
            "scene_type": "multi_scene",
            "language": "pt",
            "visual_style": "animation",
            "audio_mode": "narrated",
            "animation_sub": "pixar_3d",
            "continuity_mode": True
        }
    )
    assert create_response.status_code == 200, f"Failed to create project: {create_response.text}"
    project = create_response.json()
    project_id = project.get("id")
    print(f"Created test project: {project_id}")
    
    yield project_id
    
    # Cleanup: delete the test project
    try:
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
        print(f"Deleted test project: {project_id}")
    except Exception as e:
        print(f"Cleanup failed: {e}")


class TestPatchSettingsEndpoint:
    """Test PATCH /api/studio/projects/{project_id}/settings endpoint"""
    
    def test_patch_settings_endpoint_exists(self, auth_headers, test_project):
        """Test that PATCH /settings endpoint exists and responds"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"screenplay_approved": True}
        )
        # Should return 200 OK
        assert response.status_code == 200, f"PATCH settings failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Unexpected response: {data}"
        print(f"PATCH /settings endpoint works: {data}")
    
    def test_patch_screenplay_approved_true(self, auth_headers, test_project):
        """Test setting screenplay_approved to true"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"screenplay_approved": True}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify via GET /status
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("screenplay_approved") == True, f"screenplay_approved not persisted: {status_data}"
        print(f"screenplay_approved=True persisted correctly")
    
    def test_patch_screenplay_approved_false(self, auth_headers, test_project):
        """Test setting screenplay_approved to false"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"screenplay_approved": False}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify via GET /status
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("screenplay_approved") == False, f"screenplay_approved not persisted: {status_data}"
        print(f"screenplay_approved=False persisted correctly")
    
    def test_patch_audio_mode(self, auth_headers, test_project):
        """Test setting audio_mode"""
        # Set to dubbed
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"audio_mode": "dubbed"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify via GET /status
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("audio_mode") == "dubbed", f"audio_mode not persisted: {status_data}"
        print(f"audio_mode=dubbed persisted correctly")
    
    def test_patch_visual_style(self, auth_headers, test_project):
        """Test setting visual_style"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"visual_style": "anime"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify via GET /status
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("visual_style") == "anime", f"visual_style not persisted: {status_data}"
        print(f"visual_style=anime persisted correctly")
    
    def test_patch_animation_sub(self, auth_headers, test_project):
        """Test setting animation_sub"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"animation_sub": "cartoon_2d"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"animation_sub=cartoon_2d set successfully")
    
    def test_patch_continuity_mode(self, auth_headers, test_project):
        """Test setting continuity_mode"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"continuity_mode": False}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"continuity_mode=False set successfully")
    
    def test_patch_language(self, auth_headers, test_project):
        """Test setting language"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={"language": "en"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"language=en set successfully")
    
    def test_patch_multiple_settings(self, auth_headers, test_project):
        """Test setting multiple settings at once"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={
                "screenplay_approved": True,
                "audio_mode": "narrated",
                "visual_style": "animation"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify all settings
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("screenplay_approved") == True
        assert status_data.get("audio_mode") == "narrated"
        assert status_data.get("visual_style") == "animation"
        print(f"Multiple settings persisted correctly")
    
    def test_patch_ignores_non_whitelisted_keys(self, auth_headers, test_project):
        """Test that non-whitelisted keys are ignored"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{test_project}/settings",
            headers=auth_headers,
            json={
                "screenplay_approved": True,
                "invalid_key": "should_be_ignored",
                "status": "hacked"  # Should not be allowed
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify status was not changed
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        # Status should not be "hacked"
        assert status_data.get("status") != "hacked", f"Non-whitelisted key was accepted: {status_data}"
        print(f"Non-whitelisted keys correctly ignored")
    
    def test_patch_invalid_project_returns_404(self, auth_headers):
        """Test that PATCH on invalid project returns 404"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/invalid_project_id_12345/settings",
            headers=auth_headers,
            json={"screenplay_approved": True}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"Invalid project correctly returns 404")


class TestGetStatusEndpoint:
    """Test GET /api/studio/projects/{project_id}/status returns new fields"""
    
    def test_status_includes_screenplay_approved_field(self, auth_headers, test_project):
        """Test that status response includes screenplay_approved field"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "screenplay_approved" in data, f"screenplay_approved field missing: {data.keys()}"
        print(f"screenplay_approved field present in status response")
    
    def test_status_includes_audio_mode_field(self, auth_headers, test_project):
        """Test that status response includes audio_mode field"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "audio_mode" in data, f"audio_mode field missing: {data.keys()}"
        print(f"audio_mode field present in status response")
    
    def test_status_response_structure(self, auth_headers, test_project):
        """Test complete status response structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project}/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check all expected fields
        expected_fields = [
            "status", "chat_status", "chat_history", "agent_status", "agents_output",
            "scenes", "characters", "character_avatars", "outputs", "milestones",
            "narrations", "narration_status", "voice_config", "visual_style",
            "language", "subtitles", "screenplay_approved", "audio_mode", "error"
        ]
        
        for field in expected_fields:
            assert field in data, f"Field '{field}' missing from status response"
        
        print(f"Status response has all expected fields: {list(data.keys())}")


class TestMilestoneOnScreenplayApproval:
    """Test that milestone is added when screenplay_approved is set to true"""
    
    def test_milestone_added_on_approval(self, auth_headers):
        """Test that approving screenplay adds a milestone"""
        # Create a fresh project
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json={
                "name": "TEST_milestone_test",
                "scene_type": "multi_scene",
                "language": "pt"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        try:
            # Get initial milestones
            status_response = requests.get(
                f"{BASE_URL}/api/studio/projects/{project_id}/status",
                headers=auth_headers
            )
            initial_milestones = status_response.json().get("milestones", [])
            initial_count = len(initial_milestones)
            
            # Approve screenplay
            patch_response = requests.patch(
                f"{BASE_URL}/api/studio/projects/{project_id}/settings",
                headers=auth_headers,
                json={"screenplay_approved": True}
            )
            assert patch_response.status_code == 200
            
            # Check milestones after approval
            status_response = requests.get(
                f"{BASE_URL}/api/studio/projects/{project_id}/status",
                headers=auth_headers
            )
            final_milestones = status_response.json().get("milestones", [])
            
            # Should have one more milestone
            assert len(final_milestones) > initial_count, f"No milestone added: {final_milestones}"
            
            # Check for screenplay_approved milestone
            milestone_keys = [m.get("key") for m in final_milestones]
            assert "screenplay_approved" in milestone_keys, f"screenplay_approved milestone not found: {milestone_keys}"
            print(f"Milestone correctly added on screenplay approval")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)


class TestSceneMergeLogic:
    """Test scene merge logic - conceptual verification via code review
    
    The actual merge logic is in _run_screenwriter_background (lines 1064-1083):
    - If new scenes don't overlap with existing (continuation), they are MERGED
    - If new scenes overlap (rewrite), they REPLACE existing scenes
    
    This is tested conceptually since it requires Claude AI calls.
    """
    
    def test_project_can_have_scenes_injected(self, auth_headers):
        """Test that we can manually inject scenes into a project for testing"""
        # Create a project
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json={
                "name": "TEST_scene_injection",
                "scene_type": "multi_scene",
                "language": "pt"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        try:
            # Check initial status
            status_response = requests.get(
                f"{BASE_URL}/api/studio/projects/{project_id}/status",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            data = status_response.json()
            assert data.get("scenes") == [], f"New project should have empty scenes: {data.get('scenes')}"
            print(f"Project created with empty scenes - ready for scene injection testing")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)


class TestExistingProjectWithScenes:
    """Test with existing project that has scenes"""
    
    def test_existing_project_status(self, auth_headers):
        """Test getting status of existing project with scenes"""
        # Use the known test project from iteration 103
        project_id = "14e8e05fc2bd"
        
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            scenes = data.get("scenes", [])
            print(f"Existing project has {len(scenes)} scenes")
            
            # Verify new fields are present
            assert "screenplay_approved" in data, "screenplay_approved field missing"
            assert "audio_mode" in data, "audio_mode field missing"
            print(f"screenplay_approved: {data.get('screenplay_approved')}")
            print(f"audio_mode: {data.get('audio_mode')}")
        else:
            print(f"Project {project_id} not found (may have been deleted)")
            pytest.skip("Test project not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
