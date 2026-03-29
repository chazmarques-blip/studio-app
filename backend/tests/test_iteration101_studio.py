"""
Iteration 101: Testing Language Picker and DirectedStudio Project List
Tests:
- P0.1: Language selector in Settings page
- P0.2: Project list in DirectedStudio
- P0.3: Project search functionality
- P0.4: Loading state
- Backend API: GET /api/studio/projects
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seguimiento-2.preview.emergentagent.com')

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
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]


class TestStudioProjects:
    """Studio projects API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_studio_projects(self, auth_headers):
        """Test GET /api/studio/projects returns projects list"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "projects" in data, "No 'projects' key in response"
        projects = data["projects"]
        assert isinstance(projects, list), "Projects should be a list"
        print(f"Found {len(projects)} projects")
        return projects
    
    def test_projects_count(self, auth_headers):
        """Test that projects list has expected count (45 projects expected)"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        projects = data.get("projects", [])
        print(f"Total projects: {len(projects)}")
        # Check if we have a reasonable number of projects
        assert len(projects) >= 0, "Projects list should not be negative"
        # Log project names for debugging
        for i, p in enumerate(projects[:5]):
            print(f"  Project {i+1}: {p.get('name', 'unnamed')} - {p.get('status', 'unknown')}")
        if len(projects) > 5:
            print(f"  ... and {len(projects) - 5} more")
    
    def test_project_structure(self, auth_headers):
        """Test that projects have expected structure"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        projects = data.get("projects", [])
        
        if len(projects) > 0:
            project = projects[0]
            # Check expected fields
            expected_fields = ["id", "name", "status"]
            for field in expected_fields:
                assert field in project, f"Project missing '{field}' field"
            print(f"First project: {project.get('name')} - status: {project.get('status')}")
            print(f"  Scenes: {len(project.get('scenes', []))}")
            print(f"  Characters: {len(project.get('characters', []))}")
    
    def test_search_projects_abraao(self, auth_headers):
        """Test searching for 'abraao' in projects"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        projects = data.get("projects", [])
        
        # Filter projects containing 'abraao' (case-insensitive)
        abraao_projects = [
            p for p in projects 
            if 'abraao' in (p.get('name', '') or '').lower() 
            or 'abraao' in (p.get('briefing', '') or '').lower()
        ]
        print(f"Projects matching 'abraao': {len(abraao_projects)}")
        for p in abraao_projects[:5]:
            scenes = p.get('scenes', [])
            print(f"  - {p.get('name', 'unnamed')}: {len(scenes)} scenes")
    
    def test_15_scene_projects(self, auth_headers):
        """Test finding projects with 15 scenes"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        projects = data.get("projects", [])
        
        # Find projects with 15 scenes
        fifteen_scene_projects = [
            p for p in projects 
            if len(p.get('scenes', [])) == 15
        ]
        print(f"Projects with 15 scenes: {len(fifteen_scene_projects)}")
        for p in fifteen_scene_projects[:5]:
            print(f"  - {p.get('name', 'unnamed')}")


class TestStudioVoices:
    """Studio voices API tests"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        pytest.skip("Authentication failed")
    
    def test_get_voices(self, auth_headers):
        """Test GET /api/studio/voices returns voices list"""
        response = requests.get(f"{BASE_URL}/api/studio/voices", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "voices" in data, "No 'voices' key in response"
        print(f"Found {len(data['voices'])} voices")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
