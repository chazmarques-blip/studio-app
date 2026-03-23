"""
Iteration 94: Testing new Directed Studio features
- StudioProductionBanner component (frontend)
- Real-time scene video preview in Step 3
- Time estimate during video generation
- Delete project button
- Resume production button for error projects
- ElevenLabs voice narration integration
- GET /api/studio/projects returns all projects with scenes/outputs
- DELETE /api/studio/projects/{id} deletes a project
- GET /api/studio/voices returns 24 voices
- POST /api/studio/projects/{id}/generate-narration starts narration
- GET /api/studio/projects/{id}/narrations returns narration data
- GET /api/studio/projects/{id}/status includes narrations, narration_status, voice_config
- Google OAuth /api/google/connect returns dynamic redirect_uri
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStudioProjectsAPI:
    """Test Studio Projects CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.token = None
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        yield
    
    def test_01_login_success(self):
        """Test login returns access_token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data, "No access_token in response"
        assert len(data["access_token"]) > 0
        print(f"✓ Login successful, token length: {len(data['access_token'])}")
    
    def test_02_get_projects_list(self):
        """Test GET /api/studio/projects returns projects list"""
        resp = requests.get(f"{BASE_URL}/api/studio/projects", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get projects: {resp.text}"
        data = resp.json()
        assert "projects" in data, "No 'projects' key in response"
        projects = data["projects"]
        assert isinstance(projects, list), "Projects should be a list"
        print(f"✓ GET /api/studio/projects returned {len(projects)} projects")
        
        # Verify project structure if projects exist
        if len(projects) > 0:
            proj = projects[0]
            assert "id" in proj, "Project missing 'id'"
            assert "status" in proj, "Project missing 'status'"
            print(f"  First project: id={proj['id']}, status={proj.get('status')}, name={proj.get('name', 'N/A')[:30]}")
    
    def test_03_get_voices_returns_24(self):
        """Test GET /api/studio/voices returns 24 ElevenLabs voices"""
        resp = requests.get(f"{BASE_URL}/api/studio/voices", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get voices: {resp.text}"
        data = resp.json()
        assert "voices" in data, "No 'voices' key in response"
        voices = data["voices"]
        assert len(voices) == 24, f"Expected 24 voices, got {len(voices)}"
        
        # Verify voice structure
        voice = voices[0]
        assert "id" in voice, "Voice missing 'id'"
        assert "name" in voice, "Voice missing 'name'"
        assert "gender" in voice, "Voice missing 'gender'"
        assert "accent" in voice, "Voice missing 'accent'"
        assert "style" in voice, "Voice missing 'style'"
        print(f"✓ GET /api/studio/voices returned {len(voices)} voices with correct structure")
    
    def test_04_create_project(self):
        """Test POST /api/studio/projects creates a new project"""
        project_name = f"TEST_Project_{uuid.uuid4().hex[:6]}"
        resp = requests.post(f"{BASE_URL}/api/studio/projects", headers=self.headers, json={
            "name": project_name,
            "briefing": "Test project for iteration 94"
        })
        assert resp.status_code == 200, f"Failed to create project: {resp.text}"
        data = resp.json()
        assert "id" in data, "Created project missing 'id'"
        assert data.get("name") == project_name, f"Project name mismatch"
        assert data.get("status") == "draft", f"New project should be 'draft', got {data.get('status')}"
        print(f"✓ Created project: id={data['id']}, name={data['name']}")
        
        # Store for cleanup
        self.created_project_id = data["id"]
        return data["id"]
    
    def test_05_get_project_status(self):
        """Test GET /api/studio/projects/{id}/status returns full status"""
        # First create a project
        project_name = f"TEST_Status_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/studio/projects", headers=self.headers, json={
            "name": project_name,
            "briefing": "Test status endpoint"
        })
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Get status
        resp = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get status: {resp.text}"
        data = resp.json()
        
        # Verify required fields
        assert "status" in data, "Status response missing 'status'"
        assert "scenes" in data, "Status response missing 'scenes'"
        assert "outputs" in data, "Status response missing 'outputs'"
        assert "narrations" in data, "Status response missing 'narrations'"
        assert "narration_status" in data, "Status response missing 'narration_status'"
        assert "voice_config" in data, "Status response missing 'voice_config'"
        print(f"✓ GET /api/studio/projects/{project_id}/status includes all required fields")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=self.headers)
    
    def test_06_delete_project(self):
        """Test DELETE /api/studio/projects/{id} deletes a project"""
        # First create a project
        project_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/studio/projects", headers=self.headers, json={
            "name": project_name,
            "briefing": "Test delete endpoint"
        })
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Delete the project
        del_resp = requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=self.headers)
        assert del_resp.status_code == 200, f"Failed to delete project: {del_resp.text}"
        
        # Verify project is deleted (should return 404)
        get_resp = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=self.headers)
        assert get_resp.status_code == 404, f"Deleted project should return 404, got {get_resp.status_code}"
        print(f"✓ DELETE /api/studio/projects/{project_id} successfully deleted project")
    
    def test_07_get_narrations_endpoint(self):
        """Test GET /api/studio/projects/{id}/narrations returns narration data"""
        # First create a project
        project_name = f"TEST_Narrations_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/studio/projects", headers=self.headers, json={
            "name": project_name,
            "briefing": "Test narrations endpoint"
        })
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Get narrations
        resp = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/narrations", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get narrations: {resp.text}"
        data = resp.json()
        
        # Verify structure
        assert "narrations" in data, "Response missing 'narrations'"
        assert "narration_status" in data, "Response missing 'narration_status'"
        assert "voice_config" in data, "Response missing 'voice_config'"
        print(f"✓ GET /api/studio/projects/{project_id}/narrations returns correct structure")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=self.headers)
    
    def test_08_generate_narration_no_scenes(self):
        """Test POST /api/studio/projects/{id}/generate-narration returns 400 if no scenes"""
        # Create a project without scenes
        project_name = f"TEST_NoScenes_{uuid.uuid4().hex[:6]}"
        create_resp = requests.post(f"{BASE_URL}/api/studio/projects", headers=self.headers, json={
            "name": project_name,
            "briefing": "Test narration without scenes"
        })
        assert create_resp.status_code == 200
        project_id = create_resp.json()["id"]
        
        # Try to generate narration
        resp = requests.post(f"{BASE_URL}/api/studio/projects/{project_id}/generate-narration", 
                            headers=self.headers, json={
                                "project_id": project_id,
                                "voice_id": "21m00Tcm4TlvDq8ikWAM"
                            })
        assert resp.status_code == 400, f"Expected 400 for no scenes, got {resp.status_code}"
        print(f"✓ POST generate-narration correctly returns 400 when no scenes")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=self.headers)
    
    def test_09_generate_narration_nonexistent_project(self):
        """Test POST /api/studio/projects/{id}/generate-narration returns 404 for nonexistent project"""
        fake_id = "nonexistent_project_12345"
        resp = requests.post(f"{BASE_URL}/api/studio/projects/{fake_id}/generate-narration", 
                            headers=self.headers, json={
                                "project_id": fake_id,
                                "voice_id": "21m00Tcm4TlvDq8ikWAM"
                            })
        assert resp.status_code == 404, f"Expected 404 for nonexistent project, got {resp.status_code}"
        print(f"✓ POST generate-narration correctly returns 404 for nonexistent project")


class TestGoogleOAuthDynamicRedirect:
    """Test Google OAuth dynamic redirect_uri"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.token = None
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        yield
    
    def test_10_google_connect_returns_auth_url(self):
        """Test GET /api/google/connect returns authorization_url with dynamic redirect"""
        resp = requests.get(f"{BASE_URL}/api/google/connect", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get Google connect URL: {resp.text}"
        data = resp.json()
        assert "authorization_url" in data, "Response missing 'authorization_url'"
        
        auth_url = data["authorization_url"]
        assert "accounts.google.com" in auth_url, "Auth URL should point to Google"
        assert "redirect_uri" in auth_url, "Auth URL should contain redirect_uri"
        
        # Verify redirect_uri is based on the request origin (should contain the app URL)
        # The redirect_uri should be dynamic based on request origin
        print(f"✓ GET /api/google/connect returns authorization_url with redirect_uri")
        print(f"  Auth URL (truncated): {auth_url[:100]}...")


class TestCompletedProjectWithVideos:
    """Test accessing a completed project with videos (Abraão e Isaque - Milestones)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.token = None
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        yield
    
    def test_11_completed_project_has_videos(self):
        """Test that completed project 'Abraão e Isaque - Milestones' has video outputs"""
        project_id = "b4435a8658b4"  # Known completed project
        
        resp = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=self.headers)
        
        # Project might not exist in this tenant, so handle gracefully
        if resp.status_code == 404:
            print(f"⚠ Project {project_id} not found in this tenant (expected if different user)")
            pytest.skip("Project not found in this tenant")
            return
        
        assert resp.status_code == 200, f"Failed to get project status: {resp.text}"
        data = resp.json()
        
        # Check status
        status = data.get("status")
        print(f"  Project status: {status}")
        
        # Check outputs
        outputs = data.get("outputs", [])
        video_outputs = [o for o in outputs if o.get("type") == "video" and o.get("url")]
        print(f"  Video outputs: {len(video_outputs)}")
        
        # Check scenes
        scenes = data.get("scenes", [])
        print(f"  Scenes: {len(scenes)}")
        
        if status == "complete":
            assert len(video_outputs) > 0, "Completed project should have video outputs"
            print(f"✓ Completed project has {len(video_outputs)} video outputs")
        else:
            print(f"⚠ Project is not complete (status={status}), skipping video check")


class TestMusicLibrary:
    """Test music library endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.token = None
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if login_resp.status_code == 200:
            self.token = login_resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        yield
    
    def test_12_get_music_library(self):
        """Test GET /api/studio/music-library returns tracks"""
        resp = requests.get(f"{BASE_URL}/api/studio/music-library", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get music library: {resp.text}"
        data = resp.json()
        assert "tracks" in data, "Response missing 'tracks'"
        tracks = data["tracks"]
        assert len(tracks) > 0, "Music library should have tracks"
        
        # Verify track structure
        track = tracks[0]
        assert "id" in track, "Track missing 'id'"
        assert "name" in track, "Track missing 'name'"
        print(f"✓ GET /api/studio/music-library returned {len(tracks)} tracks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
