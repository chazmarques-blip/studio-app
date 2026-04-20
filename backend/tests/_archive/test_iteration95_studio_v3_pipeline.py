"""
Iteration 95: Testing Directed Studio v3 Pipeline Rewrite
- Per-scene parallel teams architecture
- New scene statuses: queued, directing, waiting_sora, generating_video, done, error
- Backend API endpoints for studio operations
- Frontend scene status rendering
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

# Known completed project ID from context
COMPLETED_PROJECT_ID = "b4435a8658b4"


class TestStudioV3Pipeline:
    """Test Directed Studio v3 pipeline endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for all tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_01_login_success(self):
        """Test login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"PASS: Login successful, got access_token")
    
    def test_02_get_projects_list(self):
        """Test GET /api/studio/projects returns projects correctly"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        print(f"PASS: GET /api/studio/projects returned {len(data['projects'])} projects")
    
    def test_03_get_project_status_with_new_scene_states(self):
        """Test GET /api/studio/projects/{id}/status returns scene_status with new states"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{COMPLETED_PROJECT_ID}/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "status" in data
        assert "agent_status" in data
        assert "scenes" in data
        assert "outputs" in data
        
        # Check agent_status structure for v3 pipeline
        agent_status = data.get("agent_status", {})
        if agent_status:
            # v3 pipeline should have scene_status dict
            if "scene_status" in agent_status:
                scene_status = agent_status["scene_status"]
                print(f"Scene status dict: {scene_status}")
                # Valid states: queued, directing, waiting_sora, generating_video, done, error
                valid_states = {"queued", "directing", "waiting_sora", "generating_video", "done", "error", "agents_done"}
                for scene_num, state in scene_status.items():
                    assert state in valid_states, f"Invalid scene state: {state}"
        
        print(f"PASS: GET /api/studio/projects/{COMPLETED_PROJECT_ID}/status - status={data['status']}, scenes={len(data.get('scenes', []))}")
    
    def test_04_get_voices_returns_24(self):
        """Test GET /api/studio/voices returns 24 voices"""
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        voices = data["voices"]
        assert len(voices) == 24, f"Expected 24 voices, got {len(voices)}"
        
        # Verify voice structure
        for voice in voices[:3]:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice
            assert "accent" in voice
            assert "style" in voice
        
        print(f"PASS: GET /api/studio/voices returned {len(voices)} voices with correct structure")
    
    def test_05_delete_project_works(self):
        """Test DELETE /api/studio/projects/{id} works"""
        # First create a test project
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json={"name": "TEST_delete_project_v95", "briefing": "Test project for deletion"}
        )
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        assert project_id
        
        # Delete the project
        delete_response = requests.delete(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        
        # Verify project is deleted (should return 404)
        get_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=self.headers
        )
        assert get_response.status_code == 404
        
        print(f"PASS: DELETE /api/studio/projects/{project_id} - project deleted and returns 404")
    
    def test_06_start_production_accepts_request(self):
        """Test POST /api/studio/start-production accepts and validates request"""
        # Create a test project first
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json={"name": "TEST_start_production_v95", "briefing": "Test project for production"}
        )
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Try to start production (should fail with 400 because no scenes)
        start_response = requests.post(
            f"{BASE_URL}/api/studio/start-production",
            headers=self.headers,
            json={
                "project_id": project_id,
                "video_duration": 12,
                "character_avatars": {}
            }
        )
        # Should return 400 because no scenes defined
        assert start_response.status_code == 400
        assert "No scenes" in start_response.json().get("detail", "")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=self.headers)
        
        print(f"PASS: POST /api/studio/start-production validates scenes requirement (returns 400 for no scenes)")
    
    def test_07_start_production_nonexistent_project(self):
        """Test POST /api/studio/start-production returns 404 for nonexistent project"""
        response = requests.post(
            f"{BASE_URL}/api/studio/start-production",
            headers=self.headers,
            json={
                "project_id": "nonexistent_project_id_xyz",
                "video_duration": 12,
                "character_avatars": {}
            }
        )
        assert response.status_code == 404
        print(f"PASS: POST /api/studio/start-production returns 404 for nonexistent project")
    
    def test_08_generate_narration_starts(self):
        """Test POST /api/studio/projects/{id}/generate-narration starts narration"""
        # Create a test project
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json={"name": "TEST_narration_v95", "briefing": "Test project for narration"}
        )
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Try to generate narration (should fail with 400 because no scenes)
        narration_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/generate-narration",
            headers=self.headers,
            json={
                "project_id": project_id,
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "stability": 0.30,
                "similarity": 0.80,
                "style_val": 0.55
            }
        )
        # Should return 400 because no scenes
        assert narration_response.status_code == 400
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=self.headers)
        
        print(f"PASS: POST /api/studio/projects/{project_id}/generate-narration validates scenes requirement")
    
    def test_09_get_narrations_returns_data(self):
        """Test GET /api/studio/projects/{id}/narrations returns data"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{COMPLETED_PROJECT_ID}/narrations",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "narrations" in data
        assert "narration_status" in data
        assert "voice_config" in data
        
        print(f"PASS: GET /api/studio/projects/{COMPLETED_PROJECT_ID}/narrations - narrations={len(data.get('narrations', []))}")
    
    def test_10_completed_project_has_outputs(self):
        """Test completed project b4435a8658b4 has video outputs"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{COMPLETED_PROJECT_ID}/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify project is complete
        assert data.get("status") == "complete", f"Expected status 'complete', got '{data.get('status')}'"
        
        # Verify outputs exist
        outputs = data.get("outputs", [])
        assert len(outputs) > 0, "Expected at least one output for completed project"
        
        # Verify video outputs have URLs
        video_outputs = [o for o in outputs if o.get("type") == "video" and o.get("url")]
        assert len(video_outputs) > 0, "Expected at least one video output with URL"
        
        print(f"PASS: Completed project has {len(video_outputs)} video outputs")
    
    def test_11_music_library_endpoint(self):
        """Test GET /api/studio/music-library returns tracks"""
        response = requests.get(f"{BASE_URL}/api/studio/music-library", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        print(f"PASS: GET /api/studio/music-library returned {len(data.get('tracks', []))} tracks")
    
    def test_12_create_project_returns_correct_structure(self):
        """Test POST /api/studio/projects returns correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers,
            json={"name": "TEST_structure_v95", "briefing": "Test project structure"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "id" in data
        assert "name" in data
        assert "status" in data
        assert data["status"] == "draft"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{data['id']}", headers=self.headers)
        
        print(f"PASS: POST /api/studio/projects returns correct structure with id={data['id']}, status=draft")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
