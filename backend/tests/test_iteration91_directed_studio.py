"""
Iteration 91: Directed Studio Mode Testing
Tests for the new Directed Studio feature including:
- GET /api/studio/voices - returns voices array with 24+ entries
- GET /api/studio/music-library - returns tracks array (not dict)
- POST /api/studio/projects - creates project in MongoDB
- GET /api/studio/projects - returns list of user's projects
- POST /api/auth/login - authentication
"""
import pytest
import requests
import os

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
        assert "access_token" in data or "token" in data, f"No token in response: {data}"
        return data.get("access_token") or data.get("token")


class TestStudioVoices:
    """Tests for GET /api/studio/voices endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_voices_returns_array(self, auth_token):
        """Test that /api/studio/voices returns voices array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        assert response.status_code == 200, f"Voices endpoint failed: {response.text}"
        data = response.json()
        assert "voices" in data, f"No 'voices' key in response: {data}"
        assert isinstance(data["voices"], list), f"voices is not a list: {type(data['voices'])}"
    
    def test_voices_has_24_plus_entries(self, auth_token):
        """Test that voices array has 24+ entries"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        assert response.status_code == 200
        data = response.json()
        voices = data.get("voices", [])
        assert len(voices) >= 24, f"Expected 24+ voices, got {len(voices)}"
    
    def test_voices_structure(self, auth_token):
        """Test that each voice has required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=headers)
        assert response.status_code == 200
        data = response.json()
        voices = data.get("voices", [])
        assert len(voices) > 0, "No voices returned"
        
        # Check first voice has required fields
        voice = voices[0]
        assert "id" in voice, f"Voice missing 'id': {voice}"
        assert "name" in voice, f"Voice missing 'name': {voice}"
        assert "gender" in voice, f"Voice missing 'gender': {voice}"
    
    def test_voices_filter_by_gender(self, auth_token):
        """Test filtering voices by gender"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test female filter
        response = requests.get(f"{BASE_URL}/api/studio/voices?gender=female", headers=headers)
        assert response.status_code == 200
        data = response.json()
        voices = data.get("voices", [])
        for voice in voices:
            assert voice.get("gender") == "female", f"Non-female voice in filtered results: {voice}"


class TestStudioMusicLibrary:
    """Tests for GET /api/studio/music-library endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_music_library_returns_array(self, auth_token):
        """Test that /api/studio/music-library returns tracks as array (not dict)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/music-library", headers=headers)
        assert response.status_code == 200, f"Music library endpoint failed: {response.text}"
        data = response.json()
        assert "tracks" in data, f"No 'tracks' key in response: {data}"
        assert isinstance(data["tracks"], list), f"tracks is not a list (was dict before fix): {type(data['tracks'])}"
    
    def test_music_library_has_tracks(self, auth_token):
        """Test that music library has tracks"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/music-library", headers=headers)
        assert response.status_code == 200
        data = response.json()
        tracks = data.get("tracks", [])
        assert len(tracks) > 0, "No tracks in music library"
    
    def test_music_track_structure(self, auth_token):
        """Test that each track has required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/music-library", headers=headers)
        assert response.status_code == 200
        data = response.json()
        tracks = data.get("tracks", [])
        assert len(tracks) > 0, "No tracks returned"
        
        # Check first track has required fields
        track = tracks[0]
        assert "id" in track, f"Track missing 'id': {track}"
        assert "name" in track, f"Track missing 'name': {track}"


class TestStudioProjects:
    """Tests for studio projects CRUD"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_create_project(self, auth_token):
        """Test POST /api/studio/projects creates a project"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        project_data = {
            "name": "TEST_Studio Project",
            "scene_type": "single_image",
            "briefing": "Test scene description",
            "avatar_urls": ["https://example.com/avatar1.png"],
            "asset_urls": [],
            "voice_config": {},
            "music_config": {},
            "language": "pt"
        }
        response = requests.post(f"{BASE_URL}/api/studio/projects", json=project_data, headers=headers)
        assert response.status_code == 200, f"Create project failed: {response.text}"
        data = response.json()
        assert "id" in data, f"Project missing 'id': {data}"
        assert data.get("name") == "TEST_Studio Project", f"Project name mismatch: {data}"
        assert data.get("scene_type") == "single_image", f"Scene type mismatch: {data}"
        return data["id"]
    
    def test_list_projects(self, auth_token):
        """Test GET /api/studio/projects returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        assert response.status_code == 200, f"List projects failed: {response.text}"
        data = response.json()
        assert "projects" in data, f"No 'projects' key in response: {data}"
        assert isinstance(data["projects"], list), f"projects is not a list: {type(data['projects'])}"
    
    def test_create_and_verify_project(self, auth_token):
        """Test creating a project and verifying it appears in list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create project
        project_data = {
            "name": f"TEST_Verify Project",
            "scene_type": "multi_avatar_image",
            "briefing": "Multi-avatar test scene",
            "avatar_urls": ["https://example.com/avatar1.png", "https://example.com/avatar2.png"],
            "asset_urls": [],
            "voice_config": {"0": {"voice_id": "test_voice", "voice_name": "Test Voice"}},
            "music_config": {"track_id": "upbeat"},
            "language": "en"
        }
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=project_data, headers=headers)
        assert create_response.status_code == 200
        created = create_response.json()
        project_id = created.get("id")
        assert project_id, "No project ID returned"
        
        # Verify in list
        list_response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        assert list_response.status_code == 200
        projects = list_response.json().get("projects", [])
        
        # Find our project
        found = any(p.get("name") == "TEST_Verify Project" for p in projects)
        assert found, f"Created project not found in list. Projects: {[p.get('name') for p in projects]}"


class TestDashboardAccess:
    """Test dashboard access after login"""
    
    def test_dashboard_stats_after_login(self):
        """Test that dashboard stats endpoint works after login"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        data = login_response.json()
        token = data.get("access_token") or data.get("token")
        
        # Access dashboard stats
        headers = {"Authorization": f"Bearer {token}"}
        stats_response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert stats_response.status_code == 200, f"Dashboard stats failed: {stats_response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
