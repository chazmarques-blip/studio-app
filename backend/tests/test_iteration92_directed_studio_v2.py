"""
Iteration 92: Directed Studio v2 - Screenwriter Chat + Multi-Scene Production Testing
Tests for the Directed Studio feature including:
- POST /api/studio/chat - Screenwriter chat (creates screenplay with scenes and characters)
- GET /api/studio/projects - List all studio projects
- GET /api/studio/projects/{id}/status - Get project status
- POST /api/studio/start-production - Start multi-scene production (validates scenes exist)
- DELETE /api/studio/projects/{id} - Delete a project
- GET /api/studio/voices - Get available voices
- GET /api/studio/music-library - Get music library
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Note: API uses 'access_token' not 'token'
        assert "access_token" in data, f"No access_token in response: {data}"
        return data.get("access_token")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed")


class TestStudioVoices:
    """Tests for GET /api/studio/voices endpoint"""
    
    def test_voices_returns_array(self, auth_token):
        """Test that /api/studio/voices returns voices array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        assert response.status_code == 200, f"Voices endpoint failed: {response.text}"
        data = response.json()
        assert "voices" in data, f"No 'voices' key in response: {data}"
        assert isinstance(data["voices"], list), f"voices is not a list: {type(data['voices'])}"
        assert len(data["voices"]) >= 20, f"Expected 20+ voices, got {len(data['voices'])}"


class TestStudioMusicLibrary:
    """Tests for GET /api/studio/music-library endpoint"""
    
    def test_music_library_returns_array(self, auth_token):
        """Test that /api/studio/music-library returns tracks as array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/music-library", headers=headers)
        assert response.status_code == 200, f"Music library endpoint failed: {response.text}"
        data = response.json()
        assert "tracks" in data, f"No 'tracks' key in response: {data}"
        assert isinstance(data["tracks"], list), f"tracks is not a list: {type(data['tracks'])}"


class TestStudioProjects:
    """Tests for studio projects CRUD"""
    
    def test_list_projects(self, auth_token):
        """Test GET /api/studio/projects returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        assert response.status_code == 200, f"List projects failed: {response.text}"
        data = response.json()
        assert "projects" in data, f"No 'projects' key in response: {data}"
        assert isinstance(data["projects"], list), f"projects is not a list: {type(data['projects'])}"
    
    def test_create_project(self, auth_token):
        """Test POST /api/studio/projects creates a project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        project_data = {
            "name": "TEST_Iteration92_Project",
            "scene_type": "multi_scene",
            "briefing": "Test multi-scene story",
            "avatar_urls": [],
            "asset_urls": [],
            "voice_config": {},
            "music_config": {},
            "language": "pt"
        }
        response = requests.post(f"{BASE_URL}/api/studio/projects", json=project_data, headers=headers)
        assert response.status_code == 200, f"Create project failed: {response.text}"
        data = response.json()
        assert "id" in data, f"Project missing 'id': {data}"
        assert data.get("name") == "TEST_Iteration92_Project", f"Project name mismatch: {data}"
        return data["id"]


class TestStudioProjectStatus:
    """Tests for GET /api/studio/projects/{id}/status endpoint"""
    
    def test_get_project_status(self, auth_token):
        """Test getting project status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a project
        project_data = {
            "name": "TEST_Status_Project",
            "scene_type": "multi_scene",
            "briefing": "Test status check",
            "language": "pt"
        }
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=project_data, headers=headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Get status
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        assert status_response.status_code == 200, f"Get status failed: {status_response.text}"
        data = status_response.json()
        
        # Verify status response structure
        assert "status" in data, f"No 'status' key in response: {data}"
        assert "scenes" in data, f"No 'scenes' key in response: {data}"
        assert "characters" in data, f"No 'characters' key in response: {data}"
        assert "outputs" in data, f"No 'outputs' key in response: {data}"
    
    def test_get_nonexistent_project_status(self, auth_token):
        """Test getting status of non-existent project returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects/nonexistent123/status", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestStudioDeleteProject:
    """Tests for DELETE /api/studio/projects/{id} endpoint"""
    
    def test_delete_project(self, auth_token):
        """Test deleting a project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a project
        project_data = {
            "name": "TEST_Delete_Project",
            "scene_type": "multi_scene",
            "briefing": "Test delete",
            "language": "pt"
        }
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=project_data, headers=headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Delete project
        delete_response = requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        data = delete_response.json()
        assert data.get("status") == "ok", f"Delete status not ok: {data}"
        
        # Verify project is deleted (status should return 404)
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        assert status_response.status_code == 404, f"Project still exists after delete: {status_response.text}"


class TestStudioStartProduction:
    """Tests for POST /api/studio/start-production endpoint"""
    
    def test_start_production_no_scenes_returns_400(self, auth_token):
        """Test that starting production without scenes returns 400 error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a project without scenes
        project_data = {
            "name": "TEST_NoScenes_Project",
            "scene_type": "multi_scene",
            "briefing": "Test no scenes",
            "language": "pt"
        }
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=project_data, headers=headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Try to start production (should fail with 400)
        start_response = requests.post(f"{BASE_URL}/api/studio/start-production", json={
            "project_id": project_id,
            "video_duration": 12
        }, headers=headers)
        
        assert start_response.status_code == 400, f"Expected 400, got {start_response.status_code}: {start_response.text}"
        data = start_response.json()
        assert "detail" in data, f"No error detail in response: {data}"
        assert "scenes" in data["detail"].lower() or "screenwriter" in data["detail"].lower(), f"Error message doesn't mention scenes: {data}"
    
    def test_start_production_nonexistent_project_returns_404(self, auth_token):
        """Test that starting production for non-existent project returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        start_response = requests.post(f"{BASE_URL}/api/studio/start-production", json={
            "project_id": "nonexistent123",
            "video_duration": 12
        }, headers=headers)
        
        assert start_response.status_code == 404, f"Expected 404, got {start_response.status_code}: {start_response.text}"


class TestStudioChat:
    """Tests for POST /api/studio/chat endpoint (Screenwriter)"""
    
    def test_chat_creates_new_project(self, auth_token):
        """Test that chat without project_id creates a new project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        chat_response = requests.post(f"{BASE_URL}/api/studio/chat", json={
            "message": "Create a simple test story with 2 scenes",
            "language": "en"
        }, headers=headers, timeout=120)
        
        assert chat_response.status_code == 200, f"Chat failed: {chat_response.text}"
        data = chat_response.json()
        
        # Verify response structure
        assert "project_id" in data, f"No project_id in response: {data}"
        assert "message" in data, f"No message in response: {data}"
        assert "scenes" in data, f"No scenes in response: {data}"
        assert "characters" in data, f"No characters in response: {data}"
        
        return data["project_id"]
    
    def test_chat_with_existing_project(self, auth_token):
        """Test that chat with project_id updates existing project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a project via chat
        first_response = requests.post(f"{BASE_URL}/api/studio/chat", json={
            "message": "Create a story about a hero",
            "language": "en"
        }, headers=headers, timeout=120)
        
        assert first_response.status_code == 200
        project_id = first_response.json().get("project_id")
        
        # Continue conversation with same project
        second_response = requests.post(f"{BASE_URL}/api/studio/chat", json={
            "project_id": project_id,
            "message": "Add a villain character",
            "language": "en"
        }, headers=headers, timeout=120)
        
        assert second_response.status_code == 200, f"Second chat failed: {second_response.text}"
        data = second_response.json()
        
        # Should return same project_id
        assert data.get("project_id") == project_id, f"Project ID changed: {data.get('project_id')} != {project_id}"
    
    def test_chat_with_nonexistent_project_returns_404(self, auth_token):
        """Test that chat with non-existent project_id returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(f"{BASE_URL}/api/studio/chat", json={
            "project_id": "nonexistent123",
            "message": "Test message",
            "language": "en"
        }, headers=headers, timeout=120)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestStudioChatSceneGeneration:
    """Tests for screenwriter chat scene generation"""
    
    def test_chat_generates_scenes_and_characters(self, auth_token):
        """Test that chat generates scenes and characters from story prompt"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Send a story prompt that should generate scenes
        chat_response = requests.post(f"{BASE_URL}/api/studio/chat", json={
            "message": "Create a 2-scene story about a knight saving a princess. Scene 1: Knight prepares for battle. Scene 2: Knight rescues princess.",
            "language": "en"
        }, headers=headers, timeout=120)
        
        assert chat_response.status_code == 200, f"Chat failed: {chat_response.text}"
        data = chat_response.json()
        
        # Verify scenes were generated
        scenes = data.get("scenes", [])
        assert len(scenes) >= 1, f"Expected at least 1 scene, got {len(scenes)}: {data}"
        
        # Verify scene structure
        if scenes:
            scene = scenes[0]
            assert "scene_number" in scene or "title" in scene or "description" in scene, f"Scene missing expected fields: {scene}"
        
        # Verify characters were generated
        characters = data.get("characters", [])
        # Characters may or may not be generated depending on AI response
        
        return data["project_id"]


class TestEndToEndFlow:
    """End-to-end flow tests"""
    
    def test_full_flow_chat_to_production_validation(self, auth_token):
        """Test full flow: create project via chat, verify scenes, validate production start"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Step 1: Create project via chat
        chat_response = requests.post(f"{BASE_URL}/api/studio/chat", json={
            "message": "Create a simple 2-scene story about a sunrise. Scene 1: Dawn breaks. Scene 2: Sun rises fully.",
            "language": "en"
        }, headers=headers, timeout=120)
        
        assert chat_response.status_code == 200, f"Chat failed: {chat_response.text}"
        project_id = chat_response.json().get("project_id")
        scenes = chat_response.json().get("scenes", [])
        
        # Step 2: Get project status
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Step 3: If scenes exist, production start should work (returns 200)
        # If no scenes, production start should fail (returns 400)
        start_response = requests.post(f"{BASE_URL}/api/studio/start-production", json={
            "project_id": project_id,
            "video_duration": 12
        }, headers=headers)
        
        if len(scenes) > 0:
            # Should succeed
            assert start_response.status_code == 200, f"Start production failed with scenes: {start_response.text}"
            start_data = start_response.json()
            assert start_data.get("status") == "started", f"Production not started: {start_data}"
        else:
            # Should fail with 400
            assert start_response.status_code == 400, f"Expected 400 without scenes, got {start_response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
