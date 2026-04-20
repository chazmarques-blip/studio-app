"""
Iteration 102: Post-Production and Localization API Tests
Tests Phase A (Post-Production with narration + music + transitions) and Phase B (Multi-language localization)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_PROJECT_ID = "864f3e7e0464"  # Abraao e Isaac - Preview v5 Test

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
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestPostProductionStatus:
    """Test GET /api/studio/projects/{id}/post-production-status"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_post_production_status_endpoint(self, auth_token):
        """Test post-production status returns correct structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/post-production-status",
            headers=headers
        )
        assert response.status_code == 200, f"Status code: {response.status_code}, Response: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "status" in data, "Missing 'status' field"
        assert "narrations" in data, "Missing 'narrations' field"
        assert "voice_config" in data, "Missing 'voice_config' field"
        
        print(f"✓ Post-production status endpoint returns correct structure")
        print(f"  Status: {data.get('status', {})}")
    
    def test_post_production_status_has_phase(self, auth_token):
        """Test post-production status has phase field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/post-production-status",
            headers=headers
        )
        data = response.json()
        status = data.get("status", {})
        
        # Verify phase is present (should be 'complete' for test project)
        assert "phase" in status, f"Missing 'phase' in status: {status}"
        print(f"✓ Phase: {status.get('phase')}")
    
    def test_post_production_status_complete_fields(self, auth_token):
        """Test completed post-production has final_url, duration, has_narration, has_music"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/post-production-status",
            headers=headers
        )
        data = response.json()
        status = data.get("status", {})
        
        if status.get("phase") == "complete":
            assert "final_url" in status, "Missing 'final_url' for complete status"
            assert status.get("final_url"), "final_url is empty"
            print(f"✓ Final URL: {status.get('final_url')[:80]}...")
            
            # Check optional fields
            if "duration" in status:
                print(f"✓ Duration: {status.get('duration')}s")
            if "has_narration" in status:
                print(f"✓ Has narration: {status.get('has_narration')}")
            if "has_music" in status:
                print(f"✓ Has music: {status.get('has_music')}")
        else:
            pytest.skip(f"Post-production not complete, phase: {status.get('phase')}")


class TestLocalizations:
    """Test GET /api/studio/projects/{id}/localizations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_localizations_endpoint(self, auth_token):
        """Test localizations endpoint returns correct structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/localizations",
            headers=headers
        )
        assert response.status_code == 200, f"Status code: {response.status_code}, Response: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "localizations" in data, "Missing 'localizations' field"
        assert "statuses" in data, "Missing 'statuses' field"
        assert "final_videos" in data, "Missing 'final_videos' field"
        assert "original_language" in data, "Missing 'original_language' field"
        
        print(f"✓ Localizations endpoint returns correct structure")
        print(f"  Original language: {data.get('original_language')}")
        print(f"  Localizations: {list(data.get('localizations', {}).keys())}")
        print(f"  Final videos: {list(data.get('final_videos', {}).keys())}")
    
    def test_localizations_has_pt_and_en(self, auth_token):
        """Test project has PT (original) and EN (localized) videos"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/localizations",
            headers=headers
        )
        data = response.json()
        
        final_videos = data.get("final_videos", {})
        
        # Should have PT (original) and EN (localized)
        assert "pt" in final_videos, f"Missing PT video. Available: {list(final_videos.keys())}"
        assert "en" in final_videos, f"Missing EN video. Available: {list(final_videos.keys())}"
        
        print(f"✓ PT video present: {final_videos.get('pt', {}).get('url', '')[:60]}...")
        print(f"✓ EN video present: {final_videos.get('en', {}).get('url', '')[:60]}...")
    
    def test_localization_statuses(self, auth_token):
        """Test localization statuses are returned"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/localizations",
            headers=headers
        )
        data = response.json()
        
        statuses = data.get("statuses", {})
        
        # EN should be complete
        if "en" in statuses:
            en_status = statuses["en"]
            print(f"✓ EN status: {en_status.get('phase')}")
            if en_status.get("phase") == "complete":
                assert "final_url" in en_status, "EN complete but missing final_url"
        
        print(f"✓ Localization statuses: {statuses}")


class TestPostProduceValidation:
    """Test POST /api/studio/projects/{id}/post-produce validation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_post_produce_requires_scene_videos(self, auth_token):
        """Test post-produce returns 400 if no scene videos"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a new empty project to test validation
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=headers,
            json={"name": "TEST_empty_project", "briefing": "Test", "language": "pt"}
        )
        
        if create_response.status_code == 200:
            new_project_id = create_response.json().get("id")
            
            # Try to post-produce without scene videos
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{new_project_id}/post-produce",
                headers=headers,
                json={"voice_id": "21m00Tcm4TlvDq8ikWAM"}
            )
            
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print(f"✓ Post-produce correctly returns 400 for project without scene videos")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{new_project_id}", headers=headers)
        else:
            pytest.skip("Could not create test project")


class TestLocalizeValidation:
    """Test POST /api/studio/projects/{id}/localize validation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_localize_rejects_same_language(self, auth_token):
        """Test localize returns 400 if target language is same as original"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to localize to PT (same as original)
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/localize",
            headers=headers,
            json={"target_language": "pt"}  # Same as original
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ Localize correctly returns 400 for same language")
    
    def test_localize_requires_final_video(self, auth_token):
        """Test localize returns 400 if no final video exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a new empty project to test validation
        create_response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=headers,
            json={"name": "TEST_no_final_video", "briefing": "Test", "language": "pt"}
        )
        
        if create_response.status_code == 200:
            new_project_id = create_response.json().get("id")
            
            # Try to localize without final video
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{new_project_id}/localize",
                headers=headers,
                json={"target_language": "en"}
            )
            
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print(f"✓ Localize correctly returns 400 for project without final video")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/studio/projects/{new_project_id}", headers=headers)
        else:
            pytest.skip("Could not create test project")


class TestProjectStatus:
    """Test project status endpoint for post-production data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        return response.json().get("access_token")
    
    def test_project_status_has_outputs(self, auth_token):
        """Test project status includes outputs with final videos"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        outputs = data.get("outputs", [])
        assert len(outputs) > 0, "No outputs in project"
        
        # Check for final video
        final_videos = [o for o in outputs if o.get("type") == "final_video"]
        print(f"✓ Project has {len(outputs)} outputs, {len(final_videos)} final videos")
        
        for fv in final_videos:
            print(f"  - {fv.get('language', '?')}: {fv.get('url', '')[:60]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
