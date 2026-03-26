"""
Test Suite for Studio Post-Production Features (Iteration 118)
Tests: Upload narration, delete narration, post-production status endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
PROJECT_ID = "fce897cf6ba3"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")  # Note: returns 'access_token' not 'token'
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestStudioNarrationEndpoints:
    """Test narration upload and delete endpoints"""

    def test_upload_narration_without_file_returns_422(self, api_client):
        """POST /api/studio/projects/{id}/upload-narration/{scene_number} without file should return 422"""
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/upload-narration/1"
        )
        # Without file, FastAPI returns 422 Unprocessable Entity
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text[:200]}"
        print(f"PASS: Upload narration without file returns 422 as expected")

    def test_delete_narration_returns_200(self, api_client):
        """DELETE /api/studio/projects/{id}/narration/{scene_number} should return 200"""
        response = api_client.delete(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/narration/999"  # Non-existent scene
        )
        # Should return 200 even if narration doesn't exist (idempotent delete)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "deleted" in data
        assert data["deleted"] == True
        assert data["scene_number"] == 999
        print(f"PASS: Delete narration returns 200 with correct response structure")


class TestStudioProjectStatus:
    """Test project status endpoint for post-production data"""

    def test_project_status_returns_outputs(self, api_client):
        """GET /api/studio/projects/{id}/status should return outputs with final_video"""
        response = api_client.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/status"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        
        # Check required fields exist
        assert "outputs" in data, "Response should contain 'outputs'"
        assert "status" in data, "Response should contain 'status'"
        
        outputs = data.get("outputs", [])
        print(f"Project has {len(outputs)} outputs")
        
        # Check for final_video output
        final_videos = [o for o in outputs if o.get("type") == "final_video"]
        print(f"Found {len(final_videos)} final_video outputs")
        
        if final_videos:
            fv = final_videos[0]
            assert "url" in fv, "final_video should have 'url'"
            print(f"PASS: Final video found with URL: {fv.get('url', '')[:80]}...")
            
            # Check for narration and music flags
            has_narration = fv.get("has_narration", False)
            has_music = fv.get("has_music", False)
            duration = fv.get("duration", 0)
            print(f"  - has_narration: {has_narration}")
            print(f"  - has_music: {has_music}")
            print(f"  - duration: {duration}s")
        else:
            print("INFO: No final_video found in outputs (post-production may not be complete)")
        
        print(f"PASS: Project status endpoint returns correct structure")


class TestStudioPostProductionStatus:
    """Test post-production status endpoint"""

    def test_post_production_status_endpoint(self, api_client):
        """GET /api/studio/projects/{id}/post-production-status should return status"""
        response = api_client.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/post-production-status"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        
        # Check required fields
        assert "status" in data, "Response should contain 'status'"
        
        status = data.get("status", {})
        phase = status.get("phase", "")
        print(f"Post-production phase: {phase}")
        
        if phase == "complete":
            assert "final_url" in status, "Complete status should have 'final_url'"
            print(f"PASS: Post-production complete with final_url: {status.get('final_url', '')[:80]}...")
            
            # Check for narration and music flags
            has_narration = status.get("has_narration", False)
            has_music = status.get("has_music", False)
            duration = status.get("duration", 0)
            print(f"  - has_narration: {has_narration}")
            print(f"  - has_music: {has_music}")
            print(f"  - duration: {duration}s")
        else:
            print(f"INFO: Post-production phase is '{phase}' (not complete)")
        
        # Check narrations array
        narrations = data.get("narrations", [])
        print(f"Found {len(narrations)} narrations")
        
        print(f"PASS: Post-production status endpoint returns correct structure")


class TestStudioLocalizations:
    """Test localizations endpoint"""

    def test_localizations_endpoint(self, api_client):
        """GET /api/studio/projects/{id}/localizations should return localization data"""
        response = api_client.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/localizations"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        
        # Check required fields
        assert "localizations" in data, "Response should contain 'localizations'"
        assert "final_videos" in data, "Response should contain 'final_videos'"
        assert "statuses" in data, "Response should contain 'statuses'"
        
        print(f"Localizations: {list(data.get('localizations', {}).keys())}")
        print(f"Final videos: {list(data.get('final_videos', {}).keys())}")
        print(f"PASS: Localizations endpoint returns correct structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
