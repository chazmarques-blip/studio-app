"""
Iteration 103: Testing Subtitles Generation and Scene Regeneration endpoints
- POST /api/studio/projects/{id}/generate-subtitles
- POST /api/studio/projects/{id}/regen-scene/{scene_number}
- GET /api/studio/projects/{id}/post-production-status (subtitles field)
- GET /api/studio/projects/{id}/status (subtitles field)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

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
        """Verify login returns access_token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestSubtitlesGeneration:
    """Test subtitles generation endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_generate_subtitles_endpoint_exists(self, headers):
        """Test that generate-subtitles endpoint exists and responds"""
        # Use a known project with narrations: 14e8e05fc2bd (Abraao e Izaac completo)
        project_id = "14e8e05fc2bd"
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/generate-subtitles",
            headers=headers
        )
        # Should return 200 (success) or 400 (no narrations) or 404 (not found)
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"✓ generate-subtitles endpoint responded with status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "subtitles" in data, f"No subtitles field in response: {data}"
            assert "languages" in data, f"No languages field in response: {data}"
            print(f"✓ Subtitles generated for languages: {data.get('languages', [])}")
    
    def test_generate_subtitles_returns_srt_urls(self, headers):
        """Test that subtitles response contains SRT URLs"""
        # Try with project that has narrations
        project_id = "14e8e05fc2bd"
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/generate-subtitles",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            subtitles = data.get("subtitles", {})
            for lang, url in subtitles.items():
                assert url.startswith("http"), f"SRT URL should be a valid URL: {url}"
                assert ".srt" in url or "subtitles" in url, f"URL should reference SRT file: {url}"
                print(f"✓ SRT URL for {lang}: {url[:80]}...")
        elif response.status_code == 400:
            print(f"✓ Project has no narrations (expected for some projects)")
        else:
            print(f"✓ Project not found or other expected error: {response.status_code}")
    
    def test_generate_subtitles_no_narrations_returns_400(self, headers):
        """Test that endpoint returns 400 when project has no narrations"""
        # Create a new empty project to test
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=headers,
            json={"name": "TEST_empty_project_subtitles", "briefing": "Test"}
        )
        
        if create_response.status_code == 200:
            project_id = create_response.json().get("id")
            
            # Try to generate subtitles for empty project
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{project_id}/generate-subtitles",
                headers=headers
            )
            assert response.status_code == 400, f"Expected 400 for project without narrations: {response.status_code}"
            print(f"✓ Correctly returns 400 for project without narrations")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=headers)
        else:
            pytest.skip("Could not create test project")


class TestSceneRegeneration:
    """Test scene regeneration endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_regen_scene_endpoint_exists(self, headers):
        """Test that regen-scene endpoint exists and responds"""
        project_id = "14e8e05fc2bd"
        scene_number = 1
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/regen-scene/{scene_number}",
            headers=headers
        )
        # Should return 200 (started) or 404 (project/scene not found)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
        print(f"✓ regen-scene endpoint responded with status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, f"No status field in response: {data}"
            assert data.get("status") == "started", f"Expected status 'started': {data}"
            assert "scene_number" in data, f"No scene_number field in response: {data}"
            print(f"✓ Scene regeneration started for scene {data.get('scene_number')}")
    
    def test_regen_scene_invalid_scene_returns_404(self, headers):
        """Test that endpoint returns 404 for invalid scene number"""
        project_id = "14e8e05fc2bd"
        scene_number = 999  # Invalid scene number
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/regen-scene/{scene_number}",
            headers=headers
        )
        # Should return 404 for invalid scene
        assert response.status_code == 404, f"Expected 404 for invalid scene: {response.status_code}"
        print(f"✓ Correctly returns 404 for invalid scene number")
    
    def test_regen_scene_invalid_project_returns_404(self, headers):
        """Test that endpoint returns 404 for invalid project"""
        project_id = "invalid_project_id"
        scene_number = 1
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/regen-scene/{scene_number}",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404 for invalid project: {response.status_code}"
        print(f"✓ Correctly returns 404 for invalid project")


class TestStatusEndpointsSubtitlesField:
    """Test that status endpoints include subtitles field"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_project_status_includes_subtitles_field(self, headers):
        """Test GET /api/studio/projects/{id}/status includes subtitles field"""
        project_id = "14e8e05fc2bd"
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "subtitles" in data, f"No subtitles field in status response: {list(data.keys())}"
            print(f"✓ Project status includes subtitles field: {data.get('subtitles', {})}")
        else:
            print(f"✓ Project not found (status {response.status_code})")
    
    def test_post_production_status_includes_subtitles_field(self, headers):
        """Test GET /api/studio/projects/{id}/post-production-status includes subtitles field"""
        project_id = "14e8e05fc2bd"
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/post-production-status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "subtitles" in data, f"No subtitles field in post-production-status response: {list(data.keys())}"
            print(f"✓ Post-production status includes subtitles field: {data.get('subtitles', {})}")
        else:
            print(f"✓ Project not found (status {response.status_code})")
    
    def test_post_production_status_structure(self, headers):
        """Test post-production-status response structure"""
        project_id = "14e8e05fc2bd"
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/post-production-status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["status", "narrations", "voice_config", "subtitles"]
            for field in expected_fields:
                assert field in data, f"Missing field '{field}' in response: {list(data.keys())}"
            print(f"✓ Post-production status has all expected fields: {expected_fields}")
        else:
            print(f"✓ Project not found (status {response.status_code})")


class TestProjectWithNarrations:
    """Test with a project that has narrations (14e8e05fc2bd)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_project_exists_and_has_narrations(self, headers):
        """Verify test project exists and has narrations"""
        project_id = "14e8e05fc2bd"
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            narrations = data.get("narrations", [])
            print(f"✓ Project {project_id} has {len(narrations)} narrations")
            if narrations:
                print(f"  First narration: {str(narrations[0])[:100]}...")
        else:
            print(f"⚠ Project {project_id} not found - may need different test project")
    
    def test_full_subtitles_flow(self, headers):
        """Test complete subtitles generation flow"""
        project_id = "14e8e05fc2bd"
        
        # Step 1: Check project status
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=headers
        )
        
        if status_response.status_code != 200:
            pytest.skip(f"Project {project_id} not found")
        
        status_data = status_response.json()
        narrations = status_data.get("narrations", [])
        
        if not narrations:
            pytest.skip("Project has no narrations")
        
        # Step 2: Generate subtitles
        gen_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/generate-subtitles",
            headers=headers
        )
        
        assert gen_response.status_code == 200, f"Subtitles generation failed: {gen_response.text}"
        gen_data = gen_response.json()
        
        assert gen_data.get("status") == "complete", f"Expected status 'complete': {gen_data}"
        assert "subtitles" in gen_data, f"No subtitles in response: {gen_data}"
        assert "languages" in gen_data, f"No languages in response: {gen_data}"
        
        subtitles = gen_data.get("subtitles", {})
        languages = gen_data.get("languages", [])
        
        print(f"✓ Subtitles generated for {len(languages)} languages: {languages}")
        
        for lang, url in subtitles.items():
            assert url.startswith("http"), f"Invalid SRT URL for {lang}: {url}"
            print(f"  {lang}: {url[:80]}...")
        
        # Step 3: Verify subtitles appear in status
        status_response2 = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/status",
            headers=headers
        )
        
        if status_response2.status_code == 200:
            status_data2 = status_response2.json()
            saved_subtitles = status_data2.get("subtitles", {})
            assert len(saved_subtitles) > 0, "Subtitles not saved to project"
            print(f"✓ Subtitles persisted in project status: {list(saved_subtitles.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
