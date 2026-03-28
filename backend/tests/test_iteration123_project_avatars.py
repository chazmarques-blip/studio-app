"""
Iteration 123: Test project-scoped avatar system
Tests the new endpoints for project-specific avatar management:
- GET /api/studio/projects/{id}/project-avatars
- POST /api/studio/projects/{id}/project-avatars
- POST /api/studio/projects/{id}/project-avatars/import
- DELETE /api/studio/projects/{id}/project-avatars/{avatar_id}
- GET /api/data/avatars (global library)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

# Test project IDs from context
PROJECT_ID_WITH_DATA = "1a0779dd0ce7"  # ADAO E EVA BIBLIZOO - has character_avatars
PROJECT_ID_CLEAN = "d27afb0e79ff"  # ADAO E EVA BIBLIZOO 2


class TestAuth:
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
        assert len(data["access_token"]) > 0


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestGlobalAvatarLibrary:
    """Test global avatar library endpoint (GET /api/data/avatars)"""
    
    def test_get_global_avatars_requires_auth(self):
        """Global avatars endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/data/avatars")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_get_global_avatars_success(self, auth_headers):
        """Get global avatar library with auth"""
        response = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get avatars: {response.text}"
        data = response.json()
        # Response should be a list
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"Global library has {len(data)} avatars")


class TestProjectAvatarsEndpoints:
    """Test project-scoped avatar endpoints"""
    
    def test_get_project_avatars_requires_auth(self):
        """Project avatars endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{PROJECT_ID_WITH_DATA}/project-avatars")
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_get_project_avatars_success(self, auth_headers):
        """Get project-specific avatars"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_WITH_DATA}/project-avatars",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "avatars" in data, f"No avatars key in response: {data}"
        assert isinstance(data["avatars"], list)
        print(f"Project {PROJECT_ID_WITH_DATA} has {len(data['avatars'])} project-scoped avatars")
    
    def test_get_project_avatars_invalid_project(self, auth_headers):
        """Get avatars for non-existent project returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/nonexistent123/project-avatars",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_add_avatar_to_project(self, auth_headers):
        """Add a new avatar to a project"""
        test_avatar = {
            "id": f"TEST_{uuid.uuid4().hex[:8]}",
            "name": "Test Avatar",
            "url": "https://example.com/test-avatar.png",
            "description": "Test avatar for iteration 123"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers,
            json={"avatar": test_avatar, "save_to_library": False}
        )
        assert response.status_code == 200, f"Failed to add avatar: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert "avatar" in data
        assert data["avatar"]["id"] == test_avatar["id"]
        print(f"Added avatar {test_avatar['id']} to project")
        
        # Verify avatar is in project
        verify_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        avatars = verify_response.json().get("avatars", [])
        avatar_ids = [a.get("id") for a in avatars]
        assert test_avatar["id"] in avatar_ids, f"Avatar not found in project: {avatar_ids}"
        
        # Cleanup - remove the test avatar
        cleanup_response = requests.delete(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars/{test_avatar['id']}",
            headers=auth_headers
        )
        assert cleanup_response.status_code == 200
    
    def test_add_avatar_with_save_to_library(self, auth_headers):
        """Add avatar to project AND global library"""
        test_avatar = {
            "id": f"TEST_LIB_{uuid.uuid4().hex[:8]}",
            "name": "Test Library Avatar",
            "url": "https://example.com/test-library-avatar.png"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers,
            json={"avatar": test_avatar, "save_to_library": True}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify in global library
        lib_response = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers)
        assert lib_response.status_code == 200
        global_avatars = lib_response.json()
        global_ids = [a.get("id") for a in global_avatars]
        assert test_avatar["id"] in global_ids, f"Avatar not in global library: {global_ids[:5]}..."
        print(f"Avatar {test_avatar['id']} saved to both project and global library")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars/{test_avatar['id']}",
            headers=auth_headers
        )
    
    def test_remove_avatar_from_project(self, auth_headers):
        """Remove avatar from project (keeps in global library)"""
        # First add an avatar
        test_avatar = {
            "id": f"TEST_DEL_{uuid.uuid4().hex[:8]}",
            "name": "Avatar to Delete",
            "url": "https://example.com/delete-me.png"
        }
        add_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers,
            json={"avatar": test_avatar, "save_to_library": True}
        )
        assert add_response.status_code == 200
        
        # Remove from project
        del_response = requests.delete(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars/{test_avatar['id']}",
            headers=auth_headers
        )
        assert del_response.status_code == 200, f"Delete failed: {del_response.text}"
        assert del_response.json().get("status") == "ok"
        
        # Verify removed from project
        verify_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers
        )
        avatars = verify_response.json().get("avatars", [])
        avatar_ids = [a.get("id") for a in avatars]
        assert test_avatar["id"] not in avatar_ids, "Avatar still in project after delete"
        print(f"Avatar {test_avatar['id']} removed from project")


class TestImportFromLibrary:
    """Test importing avatars from global library to project"""
    
    def test_import_requires_auth(self):
        """Import endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars/import",
            json={"avatar_ids": ["test"]}
        )
        assert response.status_code in [401, 403]
    
    def test_import_empty_ids_fails(self, auth_headers):
        """Import with empty avatar_ids returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars/import",
            headers=auth_headers,
            json={"avatar_ids": []}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_import_from_library(self, auth_headers):
        """Import avatars from global library into project"""
        # First, get global library to find an avatar to import
        lib_response = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers)
        if lib_response.status_code != 200:
            pytest.skip("Could not get global library")
        
        global_avatars = lib_response.json()
        if not global_avatars:
            pytest.skip("No avatars in global library to import")
        
        # Get current project avatars
        proj_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers
        )
        current_ids = set(a.get("id") for a in proj_response.json().get("avatars", []))
        
        # Find an avatar not already in project
        avatar_to_import = None
        for av in global_avatars:
            if av.get("id") and av["id"] not in current_ids:
                avatar_to_import = av
                break
        
        if not avatar_to_import:
            pytest.skip("All global avatars already in project")
        
        # Import the avatar
        import_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars/import",
            headers=auth_headers,
            json={"avatar_ids": [avatar_to_import["id"]]}
        )
        assert import_response.status_code == 200, f"Import failed: {import_response.text}"
        data = import_response.json()
        assert data.get("status") == "ok"
        assert data.get("imported") >= 0  # Could be 0 if already imported
        print(f"Imported {data.get('imported')} avatar(s), total: {data.get('total')}")
        
        # Verify avatar is now in project
        verify_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers
        )
        new_ids = [a.get("id") for a in verify_response.json().get("avatars", [])]
        assert avatar_to_import["id"] in new_ids, "Imported avatar not found in project"


class TestProjectStatusIncludesAvatars:
    """Test that project status endpoint includes project_avatars"""
    
    def test_project_status_has_project_avatars(self, auth_headers):
        """GET /api/studio/projects/{id}/status includes project_avatars"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_WITH_DATA}/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should have project_avatars field
        assert "project_avatars" in data, f"No project_avatars in status: {list(data.keys())}"
        assert isinstance(data["project_avatars"], list)
        print(f"Project status includes {len(data['project_avatars'])} project_avatars")
        
        # Should also have character_avatars (existing field)
        assert "character_avatars" in data


class TestNewProjectStartsEmpty:
    """Test that new projects start with empty avatar pool"""
    
    def test_create_project_has_empty_avatars(self, auth_headers):
        """New project should have empty project_avatars"""
        # Create a new project
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json={
                "name": f"TEST_Empty_Avatar_Project_{uuid.uuid4().hex[:6]}",
                "briefing": "Test project for avatar isolation",
                "language": "pt"
            }
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        new_project = create_response.json()
        project_id = new_project.get("id")
        
        # Verify project_avatars is empty
        assert "project_avatars" in new_project, f"No project_avatars in new project: {list(new_project.keys())}"
        assert new_project["project_avatars"] == [], f"New project should have empty avatars: {new_project['project_avatars']}"
        print(f"New project {project_id} created with empty project_avatars")
        
        # Also verify via status endpoint
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=auth_headers
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("project_avatars") == [], "Status should show empty project_avatars"
        
        # Cleanup - delete the test project
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
        print(f"Cleaned up test project {project_id}")


class TestNoCrossProjectPollution:
    """Test that avatars don't leak between projects"""
    
    def test_avatars_isolated_between_projects(self, auth_headers):
        """Avatars added to one project don't appear in another"""
        # Get avatars from project 1
        proj1_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_WITH_DATA}/project-avatars",
            headers=auth_headers
        )
        proj1_avatars = proj1_response.json().get("avatars", [])
        proj1_ids = set(a.get("id") for a in proj1_avatars)
        
        # Get avatars from project 2
        proj2_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers
        )
        proj2_avatars = proj2_response.json().get("avatars", [])
        proj2_ids = set(a.get("id") for a in proj2_avatars)
        
        # Add a unique avatar to project 1
        unique_avatar = {
            "id": f"TEST_UNIQUE_{uuid.uuid4().hex[:8]}",
            "name": "Unique to Project 1",
            "url": "https://example.com/unique.png"
        }
        add_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_WITH_DATA}/project-avatars",
            headers=auth_headers,
            json={"avatar": unique_avatar, "save_to_library": False}
        )
        assert add_response.status_code == 200
        
        # Verify it's NOT in project 2
        proj2_check = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_CLEAN}/project-avatars",
            headers=auth_headers
        )
        proj2_new_ids = [a.get("id") for a in proj2_check.json().get("avatars", [])]
        assert unique_avatar["id"] not in proj2_new_ids, "Avatar leaked to other project!"
        print(f"Avatar {unique_avatar['id']} correctly isolated to project {PROJECT_ID_WITH_DATA}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID_WITH_DATA}/project-avatars/{unique_avatar['id']}",
            headers=auth_headers
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
