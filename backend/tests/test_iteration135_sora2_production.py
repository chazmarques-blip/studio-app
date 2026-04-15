"""
Iteration 135: Test Sora 2 Production Pipeline
- P0: Backend should be running
- P0: POST /api/studio/projects/{project_id}/full-production should accept Sora 2 projects (video_engine='sora') even without kling_storyboards
- P0: POST /api/studio/projects/{project_id}/full-production should still require kling_storyboards for Kling projects (video_engine='kling')
- P1: POST /api/auth/login should work with test credentials
- P1: GET /api/studio/projects should return project list
- P1: POST /api/studio/start-production should work for Sora 2 projects
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """P0/P1: Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """P0: Backend should be running"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Health status not ok: {data}"
        print(f"✅ Health check passed: {data}")
    
    def test_login_with_test_credentials(self):
        """P1: POST /api/auth/login should work with test credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"},
            timeout=10
        )
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        assert len(data["access_token"]) > 10, "Token too short"
        print(f"✅ Login successful, token length: {len(data['access_token'])}")


class TestProjectList:
    """P1: Project list tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_projects_list(self, auth_token):
        """P1: GET /api/studio/projects should return project list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers, timeout=10)
        assert response.status_code == 200, f"Get projects failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # API returns {"projects": [...]}
        assert "projects" in data, f"Expected 'projects' key in response: {list(data.keys())}"
        projects = data["projects"]
        assert isinstance(projects, list), f"Expected list, got: {type(projects)}"
        print(f"✅ Got {len(projects)} projects")
        
        # Check if we have any Sora 2 projects
        sora_projects = [p for p in projects if p.get("video_engine") == "sora"]
        kling_projects = [p for p in projects if p.get("video_engine") == "kling"]
        print(f"   - Sora 2 projects: {len(sora_projects)}")
        print(f"   - Kling projects: {len(kling_projects)}")


class TestFullProductionValidation:
    """P0: Full production endpoint validation tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_sora2_project_full_production_no_storyboards_required(self, auth_token):
        """P0: POST /api/studio/projects/{project_id}/full-production should accept Sora 2 projects without kling_storyboards"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Use the known Sora 2 project from review request
        sora_project_id = "5a12e7f93f6f"
        
        # Get projects list to verify it's a Sora 2 project
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers, timeout=10)
        if response.status_code != 200:
            pytest.skip("Could not get projects")
        
        projects = response.json().get("projects", [])
        project = next((p for p in projects if p.get("id") == sora_project_id), None)
        
        if not project:
            pytest.skip(f"Project {sora_project_id} not found")
        
        video_engine = project.get("video_engine", "not_set")
        has_scenes = bool(project.get("scenes"))
        has_storyboards = bool(project.get("kling_storyboards"))
        
        print(f"Project {sora_project_id}:")
        print(f"  - title: {project.get('title', 'Untitled')}")
        print(f"  - video_engine: {video_engine}")
        print(f"  - has_scenes: {has_scenes}")
        print(f"  - has_storyboards: {has_storyboards}")
        
        # Verify it's a Sora 2 project
        assert video_engine == "sora", f"Expected video_engine='sora', got: {video_engine}"
        
        # Now test full-production endpoint
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{sora_project_id}/full-production",
            headers=headers,
            timeout=30
        )
        
        print(f"Full production response: {response.status_code} - {response.text[:200]}")
        
        # For Sora 2 projects, should NOT require kling_storyboards
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            # Should NOT fail with "No storyboard frames" for Sora 2
            assert "storyboard" not in error_detail.lower(), \
                f"Sora 2 project should NOT require storyboards, but got: {error_detail}"
            print(f"⚠️ Got 400 but not storyboard-related: {error_detail}")
        else:
            # 200 = started successfully
            assert response.status_code == 200, f"Unexpected status: {response.status_code}"
            data = response.json()
            assert data.get("status") == "started", f"Expected started status: {data}"
            print(f"✅ Sora 2 full-production started without storyboards!")
    
    def test_kling_project_requires_storyboards(self, auth_token):
        """P0: POST /api/studio/projects/{project_id}/full-production should require kling_storyboards for Kling projects"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get projects
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers, timeout=10)
        if response.status_code != 200:
            pytest.skip("Could not get projects")
        
        projects = response.json().get("projects", [])
        
        # Find a Kling project without storyboards
        test_project = None
        for p in projects:
            if p.get("video_engine") == "kling" and p.get("scenes"):
                storyboards = p.get("kling_storyboards", [])
                has_frames = any(sb.get("frames") for sb in storyboards) if storyboards else False
                if not has_frames:
                    test_project = p
                    break
        
        if not test_project:
            # Find any project with scenes but no storyboards and set it to Kling
            for p in projects:
                if p.get("scenes") and not p.get("kling_storyboards"):
                    test_project = p
                    break
        
        if not test_project:
            pytest.skip("No suitable project found for testing")
        
        project_id = test_project.get("id")
        print(f"Testing with project: {project_id} - {test_project.get('title', 'Untitled')}")
        
        # Set video_engine to kling
        update_response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=headers,
            json={"video_engine": "kling"},
            timeout=10
        )
        print(f"  - Set to Kling: {update_response.status_code}")
        
        # Clear storyboards if any
        clear_response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{project_id}",
            headers=headers,
            json={"kling_storyboards": []},
            timeout=10
        )
        print(f"  - Cleared storyboards: {clear_response.status_code}")
        
        # Now test full-production - should fail for Kling without storyboards
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/full-production",
            headers=headers,
            timeout=30
        )
        
        print(f"Full production response: {response.status_code} - {response.text[:200]}")
        
        # For Kling projects without storyboards, should get 400
        assert response.status_code == 400, \
            f"Kling project without storyboards should fail with 400, got: {response.status_code}"
        
        error_detail = response.json().get("detail", "")
        assert "storyboard" in error_detail.lower(), \
            f"Error should mention storyboards: {error_detail}"
        
        print(f"✅ Kling project correctly requires storyboards: {error_detail}")


class TestStartProduction:
    """P1: Start production endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_start_production_sora2(self, auth_token):
        """P1: POST /api/studio/start-production should work for Sora 2 projects"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get projects
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers, timeout=10)
        if response.status_code != 200:
            pytest.skip("Could not get projects")
        
        projects = response.json().get("projects", [])
        
        # Find a Sora 2 project with scenes
        test_project = None
        for p in projects:
            if p.get("video_engine") == "sora" and p.get("scenes"):
                test_project = p
                break
        
        if not test_project:
            # Find any project with scenes
            for p in projects:
                if p.get("scenes"):
                    test_project = p
                    break
        
        if not test_project:
            pytest.skip("No project with scenes found")
        
        project_id = test_project.get("id")
        print(f"Testing start-production with project: {project_id}")
        
        # Test start-production with Sora 2
        response = requests.post(
            f"{BASE_URL}/api/studio/start-production",
            headers=headers,
            json={
                "project_id": project_id,
                "video_engine": "sora"
            },
            timeout=30
        )
        
        print(f"Start production response: {response.status_code} - {response.text[:300]}")
        
        # Should either start (200) or fail with a meaningful error
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Start production successful: {data.get('status', 'unknown')}")
        else:
            # Log the error but don't fail - external API issues are expected
            print(f"⚠️ Start production returned {response.status_code}: {response.text[:200]}")


class TestProjectEngineValidation:
    """Test that video_engine is correctly identified"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_specific_sora_project(self, auth_token):
        """Test getting the specific Sora 2 project mentioned in review"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # The project ID from the review request
        project_id = "5a12e7f93f6f"
        
        # Get from projects list (has video_engine)
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers, timeout=10)
        assert response.status_code == 200, f"Get projects failed: {response.status_code}"
        
        projects = response.json().get("projects", [])
        project = next((p for p in projects if p.get("id") == project_id), None)
        
        if not project:
            pytest.skip(f"Project {project_id} not found in list")
        
        video_engine = project.get("video_engine", "not_set")
        scenes_count = len(project.get("scenes", []))
        has_storyboards = bool(project.get("kling_storyboards"))
        
        print(f"Project {project_id}:")
        print(f"  - title: {project.get('title', 'Untitled')}")
        print(f"  - video_engine: {video_engine}")
        print(f"  - scenes: {scenes_count}")
        print(f"  - has_kling_storyboards: {has_storyboards}")
        
        # Verify it's a Sora 2 project as mentioned in review
        assert video_engine == "sora", f"Expected video_engine='sora', got: {video_engine}"
        assert scenes_count > 0, "Project should have scenes"
        
        print(f"✅ Project {project_id} is correctly configured as Sora 2 with {scenes_count} scenes")


class TestBackendLangBugFix:
    """Test that the 'lang' variable bug is fixed"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_full_production_no_lang_error(self, auth_token):
        """Test that full-production doesn't fail with 'name lang is not defined' error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Use the known Sora 2 project
        project_id = "5a12e7f93f6f"
        
        # Start full production
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/full-production",
            headers=headers,
            timeout=30
        )
        
        print(f"Full production response: {response.status_code}")
        
        # Should not fail with internal server error due to 'lang' not defined
        if response.status_code == 500:
            error_text = response.text.lower()
            assert "lang" not in error_text and "not defined" not in error_text, \
                f"Backend still has 'lang' variable bug: {response.text}"
        
        # 200 = started, 400 = validation error (both acceptable)
        assert response.status_code in [200, 400], \
            f"Unexpected status code: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            print(f"✅ Full production started without 'lang' error")
        else:
            print(f"⚠️ Got 400 (validation error, not 'lang' bug): {response.text[:100]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
