"""
Iteration 132: Kling Storyboard Frame Count Bug Fix
Tests for the GET /api/studio/projects/{projectId}/kling-storyboards endpoint

Bug: total_frames was returning 1 (number of scenes) instead of 30 (actual frames)
Fix: Changed total_frames calculation to sum frames across all scenes
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestKlingStoryboards:
    """Test Kling Storyboard API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with authentication"""
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.project_id = "06c877c953a3"  # Test project with Kling storyboards
    
    def test_get_kling_storyboards_returns_correct_frame_count(self):
        """
        BUG FIX TEST: Verify total_frames returns actual frame count, not scene count
        
        Before fix: total_frames = 1 (number of scenes)
        After fix: total_frames = 30 (actual frames across all scenes)
        """
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{self.project_id}/kling-storyboards",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"GET failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "has_storyboards" in data
        assert "total_frames" in data
        assert "total_scenes" in data
        assert "scenes" in data
        
        # Verify frame count is correct (should be 30, not 1)
        if data["has_storyboards"]:
            # Calculate expected frame count
            expected_frames = sum(len(scene.get("frames", [])) for scene in data["scenes"])
            
            # CRITICAL: total_frames should match actual frame count
            assert data["total_frames"] == expected_frames, \
                f"total_frames mismatch: got {data['total_frames']}, expected {expected_frames}"
            
            # For this specific project, we expect 30 frames
            assert data["total_frames"] == 30, \
                f"Expected 30 frames for 5-minute video, got {data['total_frames']}"
            
            print(f"✅ total_frames correctly returns {data['total_frames']} (not scene count)")
    
    def test_get_kling_storyboards_structure(self):
        """Verify the response structure is correct"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{self.project_id}/kling-storyboards",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level structure
        assert isinstance(data.get("has_storyboards"), bool)
        assert isinstance(data.get("total_frames"), int)
        assert isinstance(data.get("total_scenes"), int)
        assert isinstance(data.get("scenes"), list)
        
        # Check scene structure
        if data["scenes"]:
            scene = data["scenes"][0]
            assert "scene_number" in scene or "frames" in scene
            
            # Check frame structure
            if scene.get("frames"):
                frame = scene["frames"][0]
                assert "frame_number" in frame
                assert "image_prompt" in frame
                assert "kling_prompt" in frame
                
                print(f"✅ Response structure is correct")
                print(f"   - {data['total_scenes']} scene(s)")
                print(f"   - {data['total_frames']} total frame(s)")
    
    def test_get_kling_storyboards_nonexistent_project(self):
        """Verify 404 for non-existent project"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/nonexistent123/kling-storyboards",
            headers=self.headers
        )
        
        assert response.status_code == 404
        print("✅ Returns 404 for non-existent project")


class TestKlingStoryboardGeneration:
    """Test Kling Storyboard generation endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test with authentication"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@studiox.com", "password": "studiox123"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_generate_endpoint_exists(self):
        """Verify the generate endpoint exists (don't actually generate)"""
        # Just check that the endpoint responds (even if it fails due to missing data)
        # We don't want to trigger actual generation in tests
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/nonexistent123/kling-storyboards/generate",
            headers=self.headers,
            json={}
        )
        
        # Should return 404 for non-existent project, not 405 (method not allowed)
        assert response.status_code in [404, 400, 500], \
            f"Unexpected status: {response.status_code}"
        print("✅ Generate endpoint exists and responds")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
