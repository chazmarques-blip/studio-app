"""
Iteration 93: Testing new narration features and project management improvements
- GET /api/studio/voices - should return 24 voices
- GET /api/studio/projects - should return projects list
- DELETE /api/studio/projects/{id} - should delete a project
- GET /api/studio/projects/{id}/narrations - should return narration status
- POST /api/studio/projects/{id}/generate-narration - should start narration generation
- GET /api/studio/projects/{id}/status - should include narrations, narration_status, voice_config fields
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestVoicesEndpoint:
    """Test GET /api/studio/voices endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_get_voices_returns_24_voices(self, auth_token):
        """GET /api/studio/voices should return 24 voices"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "voices" in data, f"No 'voices' key in response: {data}"
        
        voices = data["voices"]
        assert isinstance(voices, list), f"voices should be a list, got {type(voices)}"
        assert len(voices) == 24, f"Expected 24 voices, got {len(voices)}"
        print(f"✓ GET /api/studio/voices returned {len(voices)} voices")
        
    def test_voices_have_required_fields(self, auth_token):
        """Each voice should have id, name, gender, accent, style"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        
        assert response.status_code == 200
        voices = response.json()["voices"]
        
        required_fields = ["id", "name", "gender", "accent", "style"]
        for voice in voices:
            for field in required_fields:
                assert field in voice, f"Voice missing field '{field}': {voice}"
        
        print(f"✓ All {len(voices)} voices have required fields: {required_fields}")
    
    def test_voices_include_rachel_default(self, auth_token):
        """Rachel (21m00Tcm4TlvDq8ikWAM) should be in the voices list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        
        assert response.status_code == 200
        voices = response.json()["voices"]
        
        rachel = next((v for v in voices if v["id"] == "21m00Tcm4TlvDq8ikWAM"), None)
        assert rachel is not None, "Rachel voice not found in voices list"
        assert rachel["name"] == "Rachel", f"Expected name 'Rachel', got '{rachel['name']}'"
        print(f"✓ Rachel voice found: {rachel}")


class TestProjectsCRUD:
    """Test projects CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_get_projects_list(self, auth_token):
        """GET /api/studio/projects should return projects list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "projects" in data, f"No 'projects' key in response: {data}"
        assert isinstance(data["projects"], list), f"projects should be a list"
        print(f"✓ GET /api/studio/projects returned {len(data['projects'])} projects")
    
    def test_create_and_delete_project(self, auth_token):
        """Create a project and then delete it"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create project
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", 
            headers=headers,
            json={"name": "TEST_DeleteMe_Project", "briefing": "Test project for deletion"})
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        project = create_response.json()
        project_id = project["id"]
        print(f"✓ Created project: {project_id}")
        
        # Verify project exists
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        assert status_response.status_code == 200, f"Project not found after creation"
        
        # Delete project
        delete_response = requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        assert delete_response.json().get("status") == "ok", f"Delete response: {delete_response.json()}"
        print(f"✓ Deleted project: {project_id}")
        
        # Verify project is gone
        verify_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        assert verify_response.status_code == 404, f"Project should be deleted, got {verify_response.status_code}"
        print(f"✓ Verified project {project_id} is deleted (404)")


class TestProjectStatusFields:
    """Test that project status includes new narration fields"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def test_project(self, auth_token):
        """Create a test project for status tests"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/studio/projects",
            headers=headers,
            json={"name": "TEST_StatusFields_Project", "briefing": "Test project for status fields"})
        project = response.json()
        yield project
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project['id']}", headers=headers)
    
    def test_status_includes_narration_fields(self, auth_token, test_project):
        """GET /api/studio/projects/{id}/status should include narrations, narration_status, voice_config"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects/{test_project['id']}/status", headers=headers)
        
        assert response.status_code == 200, f"Status failed: {response.text}"
        data = response.json()
        
        # Check new narration fields exist
        assert "narrations" in data, f"Missing 'narrations' field in status: {data.keys()}"
        assert "narration_status" in data, f"Missing 'narration_status' field in status: {data.keys()}"
        assert "voice_config" in data, f"Missing 'voice_config' field in status: {data.keys()}"
        
        # Verify types
        assert isinstance(data["narrations"], list), f"narrations should be list, got {type(data['narrations'])}"
        assert isinstance(data["narration_status"], dict), f"narration_status should be dict, got {type(data['narration_status'])}"
        assert isinstance(data["voice_config"], dict), f"voice_config should be dict, got {type(data['voice_config'])}"
        
        print(f"✓ Project status includes narration fields: narrations={data['narrations']}, narration_status={data['narration_status']}, voice_config={data['voice_config']}")


class TestNarrationEndpoints:
    """Test narration generation endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_get_narrations_for_nonexistent_project(self, auth_token):
        """GET /api/studio/projects/{id}/narrations should return 404 for nonexistent project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects/nonexistent123/narrations", headers=headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ GET narrations for nonexistent project returns 404")
    
    def test_generate_narration_no_scenes(self, auth_token):
        """POST /api/studio/projects/{id}/generate-narration should fail if no scenes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create project without scenes
        create_response = requests.post(f"{BASE_URL}/api/studio/projects",
            headers=headers,
            json={"name": "TEST_NoScenes_Project", "briefing": "Test project without scenes"})
        project = create_response.json()
        project_id = project["id"]
        
        try:
            # Try to generate narration
            narration_response = requests.post(
                f"{BASE_URL}/api/studio/projects/{project_id}/generate-narration",
                headers=headers,
                json={"project_id": project_id, "voice_id": "21m00Tcm4TlvDq8ikWAM"})
            
            assert narration_response.status_code == 400, f"Expected 400 for no scenes, got {narration_response.status_code}: {narration_response.text}"
            print(f"✓ Generate narration without scenes returns 400")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=headers)
    
    def test_generate_narration_nonexistent_project(self, auth_token):
        """POST /api/studio/projects/{id}/generate-narration should return 404 for nonexistent project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/nonexistent123/generate-narration",
            headers=headers,
            json={"project_id": "nonexistent123", "voice_id": "21m00Tcm4TlvDq8ikWAM"})
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Generate narration for nonexistent project returns 404")
    
    def test_get_narrations_for_project(self, auth_token):
        """GET /api/studio/projects/{id}/narrations should return narration data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create project
        create_response = requests.post(f"{BASE_URL}/api/studio/projects",
            headers=headers,
            json={"name": "TEST_Narrations_Project", "briefing": "Test project for narrations"})
        project = create_response.json()
        project_id = project["id"]
        
        try:
            # Get narrations
            response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/narrations", headers=headers)
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            
            assert "narrations" in data, f"Missing 'narrations' in response: {data}"
            assert "narration_status" in data, f"Missing 'narration_status' in response: {data}"
            assert "voice_config" in data, f"Missing 'voice_config' in response: {data}"
            
            print(f"✓ GET narrations returns proper structure: {data}")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=headers)


class TestNarrationWithScenes:
    """Test narration generation with a project that has scenes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_generate_narration_starts_background_job(self, auth_token):
        """POST /api/studio/projects/{id}/generate-narration should start background job for project with scenes"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Use existing project with scenes (b4435a8658b4 mentioned in the request)
        # First check if it exists
        project_id = "b4435a8658b4"
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        
        if status_response.status_code != 200:
            # Create a project with scenes via chat
            print("Creating project with scenes via chat...")
            chat_response = requests.post(f"{BASE_URL}/api/studio/chat",
                headers=headers,
                json={
                    "message": "Create a simple 2-scene story about a sunrise",
                    "language": "pt"
                },
                timeout=60)
            
            if chat_response.status_code == 200:
                project_id = chat_response.json().get("project_id")
                # Wait for screenwriter to complete
                for _ in range(20):
                    time.sleep(3)
                    status = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
                    if status.status_code == 200:
                        data = status.json()
                        if data.get("chat_status") == "done" and len(data.get("scenes", [])) > 0:
                            break
            else:
                pytest.skip(f"Could not create project with scenes: {chat_response.text}")
        
        # Check if project has scenes
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        if status_response.status_code != 200:
            pytest.skip("Project not found")
        
        status_data = status_response.json()
        scenes = status_data.get("scenes", [])
        
        if len(scenes) == 0:
            pytest.skip("Project has no scenes, skipping narration test")
        
        print(f"Project {project_id} has {len(scenes)} scenes")
        
        # Start narration generation
        narration_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/generate-narration",
            headers=headers,
            json={
                "project_id": project_id,
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "stability": 0.30,
                "similarity": 0.80,
                "style_val": 0.55
            })
        
        assert narration_response.status_code == 200, f"Expected 200, got {narration_response.status_code}: {narration_response.text}"
        data = narration_response.json()
        
        assert data.get("status") == "started", f"Expected status 'started', got: {data}"
        assert "total_scenes" in data, f"Missing 'total_scenes' in response: {data}"
        
        print(f"✓ Narration generation started: {data}")


class TestExistingProjectWithScenes:
    """Test with an existing project that has scenes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_find_project_with_scenes(self, auth_token):
        """Find a project with scenes for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        assert response.status_code == 200
        
        projects = response.json().get("projects", [])
        projects_with_scenes = [p for p in projects if len(p.get("scenes", [])) > 0]
        
        print(f"Found {len(projects_with_scenes)} projects with scenes out of {len(projects)} total")
        
        if projects_with_scenes:
            proj = projects_with_scenes[0]
            print(f"✓ Project with scenes: id={proj['id']}, name={proj.get('name', 'N/A')}, scenes={len(proj.get('scenes', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
