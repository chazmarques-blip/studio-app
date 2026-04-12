"""
Test iteration 134: Frame-by-frame editing for Kling Storyboards
Tests:
1. PATCH /api/studio/projects/{projectId}/kling-storyboards/update-frame
2. GET /api/studio/projects/{projectId}/kling-storyboards - verify updated fields
3. dialogue_text field persistence
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"
PROJECT_ID = "06c877c953a3"  # Project with 30 frames


class TestFrameEditing:
    """Test frame-by-frame editing functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text[:200]}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access_token in login response")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    def test_get_storyboards_returns_frames(self):
        """Test GET endpoint returns storyboard frames"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        data = response.json()
        assert data.get("has_storyboards") == True, "Expected has_storyboards=True"
        assert data.get("total_frames", 0) > 0, "Expected total_frames > 0"
        
        # Verify scenes structure
        scenes = data.get("scenes", [])
        assert len(scenes) > 0, "Expected at least one scene"
        
        # Verify frames have required fields
        first_scene = scenes[0]
        frames = first_scene.get("frames", [])
        assert len(frames) > 0, "Expected frames in first scene"
        
        first_frame = frames[0]
        assert "frame_number" in first_frame, "Frame should have frame_number"
        assert "image_prompt" in first_frame, "Frame should have image_prompt"
        assert "kling_prompt" in first_frame, "Frame should have kling_prompt"
        
        print(f"SUCCESS: GET storyboards returned {data.get('total_frames')} frames")
    
    def test_patch_update_frame_dialogue_text(self):
        """Test PATCH endpoint updates dialogue_text field"""
        test_dialogue = f"TEST_dialogue_text_iteration134_{os.urandom(4).hex()}"
        
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "frame_number": 1,
                "dialogue_text": test_dialogue
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        data = response.json()
        assert data.get("status") == "success", f"Expected status=success, got {data}"
        assert data.get("frame_number") == 1, "Expected frame_number=1"
        assert "dialogue_text" in data.get("updated_fields", []), "dialogue_text should be in updated_fields"
        
        print(f"SUCCESS: PATCH updated dialogue_text for frame 1")
        
        # Verify persistence with GET
        get_response = self.session.get(f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards")
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        scenes = get_data.get("scenes", [])
        frame_1 = None
        for scene in scenes:
            for frame in scene.get("frames", []):
                if frame.get("frame_number") == 1:
                    frame_1 = frame
                    break
        
        assert frame_1 is not None, "Frame 1 not found after update"
        assert frame_1.get("dialogue_text") == test_dialogue, f"dialogue_text not persisted. Expected '{test_dialogue}', got '{frame_1.get('dialogue_text')}'"
        
        print(f"SUCCESS: dialogue_text persisted correctly: {test_dialogue}")
    
    def test_patch_update_frame_image_prompt(self):
        """Test PATCH endpoint updates image_prompt field"""
        test_prompt = f"TEST_image_prompt_iteration134_{os.urandom(4).hex()}"
        
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "frame_number": 2,
                "image_prompt": test_prompt
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        data = response.json()
        assert data.get("status") == "success"
        assert "image_prompt" in data.get("updated_fields", [])
        
        # Verify persistence
        get_response = self.session.get(f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards")
        get_data = get_response.json()
        
        frame_2 = None
        for scene in get_data.get("scenes", []):
            for frame in scene.get("frames", []):
                if frame.get("frame_number") == 2:
                    frame_2 = frame
                    break
        
        assert frame_2 is not None, "Frame 2 not found"
        assert frame_2.get("image_prompt") == test_prompt, f"image_prompt not persisted"
        
        print(f"SUCCESS: image_prompt persisted correctly")
    
    def test_patch_update_frame_kling_prompt(self):
        """Test PATCH endpoint updates kling_prompt field"""
        test_prompt = f"TEST_kling_prompt_iteration134_{os.urandom(4).hex()}"
        
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "frame_number": 3,
                "kling_prompt": test_prompt
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        data = response.json()
        assert data.get("status") == "success"
        assert "kling_prompt" in data.get("updated_fields", [])
        
        # Verify persistence
        get_response = self.session.get(f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards")
        get_data = get_response.json()
        
        frame_3 = None
        for scene in get_data.get("scenes", []):
            for frame in scene.get("frames", []):
                if frame.get("frame_number") == 3:
                    frame_3 = frame
                    break
        
        assert frame_3 is not None, "Frame 3 not found"
        assert frame_3.get("kling_prompt") == test_prompt, f"kling_prompt not persisted"
        
        print(f"SUCCESS: kling_prompt persisted correctly")
    
    def test_patch_update_multiple_fields(self):
        """Test PATCH endpoint updates multiple fields at once"""
        test_dialogue = f"TEST_multi_dialogue_{os.urandom(4).hex()}"
        test_image = f"TEST_multi_image_{os.urandom(4).hex()}"
        test_kling = f"TEST_multi_kling_{os.urandom(4).hex()}"
        
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "frame_number": 4,
                "dialogue_text": test_dialogue,
                "image_prompt": test_image,
                "kling_prompt": test_kling
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        data = response.json()
        assert data.get("status") == "success"
        updated_fields = data.get("updated_fields", [])
        assert "dialogue_text" in updated_fields
        assert "image_prompt" in updated_fields
        assert "kling_prompt" in updated_fields
        
        # Verify all fields persisted
        get_response = self.session.get(f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards")
        get_data = get_response.json()
        
        frame_4 = None
        for scene in get_data.get("scenes", []):
            for frame in scene.get("frames", []):
                if frame.get("frame_number") == 4:
                    frame_4 = frame
                    break
        
        assert frame_4 is not None, "Frame 4 not found"
        assert frame_4.get("dialogue_text") == test_dialogue
        assert frame_4.get("image_prompt") == test_image
        assert frame_4.get("kling_prompt") == test_kling
        
        print(f"SUCCESS: All 3 fields updated and persisted for frame 4")
    
    def test_patch_missing_frame_number_returns_400(self):
        """Test PATCH without frame_number returns 400"""
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "dialogue_text": "test"
            }
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: Missing frame_number returns 400")
    
    def test_patch_no_editable_fields_returns_400(self):
        """Test PATCH without any editable fields returns 400"""
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "frame_number": 1,
                "invalid_field": "test"
            }
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: No editable fields returns 400")
    
    def test_patch_nonexistent_frame_returns_404(self):
        """Test PATCH for non-existent frame returns 404"""
        response = self.session.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/kling-storyboards/update-frame",
            json={
                "frame_number": 9999,
                "dialogue_text": "test"
            }
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"SUCCESS: Non-existent frame returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
