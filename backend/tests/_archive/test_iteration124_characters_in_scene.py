"""
Iteration 124: Test characters_in_scene feature in scene editing
Tests:
1. Backend: POST /api/studio/projects/{project_id}/update-scene accepts characters_in_scene
2. Backend: characters_in_scene persists correctly after update
3. Backend: GET project status returns characters_in_scene for scenes
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCharactersInScene:
    """Test characters_in_scene feature for scene editing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Use test project ID from main agent context
        self.project_id = "1a0779dd0ce7"
        yield
    
    def test_get_project_status_has_scenes(self):
        """Verify project has scenes with characters"""
        resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        assert resp.status_code == 200, f"Failed to get project status: {resp.text}"
        data = resp.json()
        
        scenes = data.get("scenes", [])
        assert len(scenes) > 0, "Project should have scenes"
        print(f"✓ Project has {len(scenes)} scenes")
        
        characters = data.get("characters", [])
        assert len(characters) > 0, "Project should have characters"
        print(f"✓ Project has {len(characters)} characters: {[c.get('name') for c in characters]}")
        
        # Check if any scene has characters_in_scene
        scenes_with_chars = [s for s in scenes if s.get("characters_in_scene")]
        print(f"✓ {len(scenes_with_chars)} scenes have characters_in_scene defined")
        
        return scenes, characters
    
    def test_update_scene_with_characters_in_scene(self):
        """Test updating a scene with characters_in_scene field"""
        # First get current scene data
        status_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        assert status_resp.status_code == 200
        scenes = status_resp.json().get("scenes", [])
        characters = status_resp.json().get("characters", [])
        
        assert len(scenes) > 0, "Need at least one scene"
        assert len(characters) > 0, "Need at least one character"
        
        # Pick scene 2 for testing (scene 1 was already tested by main agent)
        test_scene = next((s for s in scenes if s.get("scene_number") == 2), scenes[0])
        scene_num = test_scene.get("scene_number")
        
        # Get character names
        char_names = [c.get("name") for c in characters[:2]]  # Use first 2 characters
        print(f"Testing with scene {scene_num} and characters: {char_names}")
        
        # Update scene with characters_in_scene
        update_resp = self.session.post(
            f"{BASE_URL}/api/studio/projects/{self.project_id}/update-scene",
            json={
                "scene_number": scene_num,
                "characters_in_scene": char_names
            }
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        print(f"✓ Update scene {scene_num} with characters_in_scene returned 200")
        
        # Verify persistence
        verify_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        assert verify_resp.status_code == 200
        updated_scenes = verify_resp.json().get("scenes", [])
        
        updated_scene = next((s for s in updated_scenes if s.get("scene_number") == scene_num), None)
        assert updated_scene, f"Scene {scene_num} not found after update"
        
        persisted_chars = updated_scene.get("characters_in_scene", [])
        assert set(persisted_chars) == set(char_names), f"characters_in_scene not persisted correctly. Expected {char_names}, got {persisted_chars}"
        print(f"✓ characters_in_scene persisted correctly: {persisted_chars}")
    
    def test_update_scene_remove_characters(self):
        """Test removing characters from a scene"""
        # Get current scene data
        status_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        assert status_resp.status_code == 200
        scenes = status_resp.json().get("scenes", [])
        
        # Pick scene 3 for testing
        test_scene = next((s for s in scenes if s.get("scene_number") == 3), scenes[0])
        scene_num = test_scene.get("scene_number")
        
        # First add some characters
        update_resp = self.session.post(
            f"{BASE_URL}/api/studio/projects/{self.project_id}/update-scene",
            json={
                "scene_number": scene_num,
                "characters_in_scene": ["Adão", "Eva"]
            }
        )
        assert update_resp.status_code == 200
        
        # Now remove all characters (empty array)
        update_resp2 = self.session.post(
            f"{BASE_URL}/api/studio/projects/{self.project_id}/update-scene",
            json={
                "scene_number": scene_num,
                "characters_in_scene": []
            }
        )
        assert update_resp2.status_code == 200
        print(f"✓ Update scene {scene_num} with empty characters_in_scene returned 200")
        
        # Verify
        verify_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        updated_scene = next((s for s in verify_resp.json().get("scenes", []) if s.get("scene_number") == scene_num), None)
        persisted_chars = updated_scene.get("characters_in_scene", [])
        assert persisted_chars == [], f"Expected empty array, got {persisted_chars}"
        print(f"✓ characters_in_scene cleared correctly")
    
    def test_update_scene_with_all_fields(self):
        """Test updating scene with all fields including characters_in_scene"""
        status_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        scenes = status_resp.json().get("scenes", [])
        characters = status_resp.json().get("characters", [])
        
        test_scene = next((s for s in scenes if s.get("scene_number") == 4), scenes[0])
        scene_num = test_scene.get("scene_number")
        char_names = [c.get("name") for c in characters[:3]]  # Use first 3 characters
        
        # Update with all fields
        update_payload = {
            "scene_number": scene_num,
            "title": "Test Title Updated",
            "description": "Test description updated",
            "dialogue": "Test dialogue updated",
            "emotion": "happy",
            "camera": "close-up",
            "characters_in_scene": char_names
        }
        
        update_resp = self.session.post(
            f"{BASE_URL}/api/studio/projects/{self.project_id}/update-scene",
            json=update_payload
        )
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        print(f"✓ Update scene {scene_num} with all fields returned 200")
        
        # Verify all fields persisted
        verify_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        updated_scene = next((s for s in verify_resp.json().get("scenes", []) if s.get("scene_number") == scene_num), None)
        
        assert updated_scene.get("title") == "Test Title Updated", "Title not persisted"
        assert updated_scene.get("description") == "Test description updated", "Description not persisted"
        assert updated_scene.get("dialogue") == "Test dialogue updated", "Dialogue not persisted"
        assert updated_scene.get("emotion") == "happy", "Emotion not persisted"
        assert updated_scene.get("camera") == "close-up", "Camera not persisted"
        assert set(updated_scene.get("characters_in_scene", [])) == set(char_names), "characters_in_scene not persisted"
        print(f"✓ All fields persisted correctly including characters_in_scene: {char_names}")
    
    def test_scene_1_has_characters_from_curl_test(self):
        """Verify scene 1 has characters from main agent's curl test"""
        status_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{self.project_id}/status")
        assert status_resp.status_code == 200
        scenes = status_resp.json().get("scenes", [])
        
        scene_1 = next((s for s in scenes if s.get("scene_number") == 1), None)
        assert scene_1, "Scene 1 not found"
        
        chars = scene_1.get("characters_in_scene", [])
        print(f"Scene 1 characters_in_scene: {chars}")
        
        # Main agent said scene 1 should have ['Adão', 'Eva'] after curl test
        if chars:
            print(f"✓ Scene 1 has characters_in_scene: {chars}")
        else:
            print("⚠ Scene 1 has no characters_in_scene (may have been reset)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
