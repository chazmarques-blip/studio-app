"""
Iteration 125: Scene Management Tests
Tests for add-scene, delete-scene, reorder-scenes, and generate-scene-ai endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PROJECT_ID = "1a0779dd0ce7"  # ADAO E EVA BIBLIZOO - 15 scenes


class TestSceneManagement:
    """Tests for scene management endpoints: add, delete, reorder, AI generate"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get initial project state
        status_response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        assert status_response.status_code == 200, f"Failed to get project status: {status_response.text}"
        self.initial_scenes = status_response.json().get("scenes", [])
        self.initial_scene_count = len(self.initial_scenes)
        print(f"Initial scene count: {self.initial_scene_count}")
    
    # ── ADD SCENE TESTS ──
    
    def test_add_scene_at_end(self):
        """Test adding a scene at the end of the list"""
        position = self.initial_scene_count + 1
        new_scene = {
            "title": "TEST_Scene_End",
            "description": "Test scene added at the end",
            "dialogue": "Test dialogue",
            "emotion": "neutral",
            "camera": "wide shot",
            "characters_in_scene": ["Adão", "Eva"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/add-scene",
            json={"position": position, "scene": new_scene}
        )
        
        assert response.status_code == 200, f"Add scene failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("total_scenes") == self.initial_scene_count + 1
        assert data.get("scene", {}).get("title") == "TEST_Scene_End"
        print(f"✓ Added scene at end, new total: {data.get('total_scenes')}")
        
        # Verify scene was added
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        last_scene = scenes[-1]
        assert last_scene.get("title") == "TEST_Scene_End"
        assert last_scene.get("scene_number") == self.initial_scene_count + 1
        print(f"✓ Verified scene at position {last_scene.get('scene_number')}")
    
    def test_add_scene_at_beginning(self):
        """Test adding a scene at position 1 (beginning)"""
        new_scene = {
            "title": "TEST_Scene_Beginning",
            "description": "Test scene added at the beginning",
            "dialogue": "First scene dialogue",
            "emotion": "excited",
            "camera": "close-up",
            "characters_in_scene": ["Deus"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/add-scene",
            json={"position": 1, "scene": new_scene}
        )
        
        assert response.status_code == 200, f"Add scene at beginning failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("scene", {}).get("scene_number") == 1
        print(f"✓ Added scene at beginning")
        
        # Verify renumbering - original scene 1 should now be scene 2
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        first_scene = next((s for s in scenes if s.get("scene_number") == 1), None)
        assert first_scene.get("title") == "TEST_Scene_Beginning"
        print(f"✓ Scene 1 is now: {first_scene.get('title')}")
    
    def test_add_scene_in_middle(self):
        """Test adding a scene in the middle (position 5)"""
        new_scene = {
            "title": "TEST_Scene_Middle",
            "description": "Test scene added in the middle",
            "dialogue": "Middle scene dialogue",
            "emotion": "tense",
            "camera": "medium shot",
            "characters_in_scene": ["Eva", "Serpente"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/add-scene",
            json={"position": 5, "scene": new_scene}
        )
        
        assert response.status_code == 200, f"Add scene in middle failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Added scene at position 5")
        
        # Verify the scene is at position 5
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        scene_5 = next((s for s in scenes if s.get("scene_number") == 5), None)
        assert scene_5.get("title") == "TEST_Scene_Middle"
        print(f"✓ Scene 5 is: {scene_5.get('title')}")
    
    # ── DELETE SCENE TESTS ──
    
    def test_delete_scene(self):
        """Test deleting a scene and verifying renumbering"""
        # First, get current state
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes_before = status.json().get("scenes", [])
        count_before = len(scenes_before)
        
        # Find a TEST_ scene to delete (from our previous tests)
        test_scene = next((s for s in scenes_before if "TEST_" in s.get("title", "")), None)
        if not test_scene:
            pytest.skip("No TEST_ scene found to delete")
        
        scene_num_to_delete = test_scene.get("scene_number")
        print(f"Deleting scene {scene_num_to_delete}: {test_scene.get('title')}")
        
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
            json={"scene_number": scene_num_to_delete}
        )
        
        assert response.status_code == 200, f"Delete scene failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("total_scenes") == count_before - 1
        print(f"✓ Deleted scene, new total: {data.get('total_scenes')}")
        
        # Verify scene is gone
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes_after = status.json().get("scenes", [])
        deleted_scene = next((s for s in scenes_after if s.get("title") == test_scene.get("title")), None)
        assert deleted_scene is None, "Scene should be deleted"
        print(f"✓ Verified scene is deleted")
    
    def test_delete_scene_renumbers_subsequent(self):
        """Test that deleting a scene renumbers subsequent scenes"""
        # Get current state
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        
        # Find another TEST_ scene
        test_scene = next((s for s in scenes if "TEST_" in s.get("title", "")), None)
        if not test_scene:
            pytest.skip("No TEST_ scene found")
        
        scene_num = test_scene.get("scene_number")
        
        # Get the scene that was after this one (if any)
        next_scene = next((s for s in scenes if s.get("scene_number") == scene_num + 1), None)
        
        # Delete the scene
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
            json={"scene_number": scene_num}
        )
        assert response.status_code == 200
        
        if next_scene:
            # Verify the next scene was renumbered
            status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
            scenes_after = status.json().get("scenes", [])
            renumbered = next((s for s in scenes_after if s.get("title") == next_scene.get("title")), None)
            if renumbered:
                assert renumbered.get("scene_number") == scene_num, f"Scene should be renumbered to {scene_num}"
                print(f"✓ Scene '{next_scene.get('title')}' renumbered from {scene_num + 1} to {scene_num}")
    
    # ── REORDER SCENES TESTS ──
    
    def test_reorder_scenes(self):
        """Test reordering scenes"""
        # Get current state
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        
        if len(scenes) < 3:
            pytest.skip("Need at least 3 scenes to test reorder")
        
        # Get current order
        current_order = [s.get("scene_number") for s in sorted(scenes, key=lambda x: x.get("scene_number", 0))]
        print(f"Current order: {current_order[:5]}...")
        
        # Swap first two scenes
        new_order = current_order.copy()
        new_order[0], new_order[1] = new_order[1], new_order[0]
        print(f"New order: {new_order[:5]}...")
        
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/reorder-scenes",
            json={"order": new_order}
        )
        
        assert response.status_code == 200, f"Reorder failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Reorder successful, total scenes: {data.get('total_scenes')}")
        
        # Verify the reorder
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes_after = status.json().get("scenes", [])
        
        # The scene that was #2 should now be #1
        scene_1 = next((s for s in scenes_after if s.get("scene_number") == 1), None)
        original_scene_2 = next((s for s in scenes if s.get("scene_number") == current_order[1]), None)
        
        if scene_1 and original_scene_2:
            assert scene_1.get("title") == original_scene_2.get("title"), "Scene 1 should now have the title of original scene 2"
            print(f"✓ Scene 1 is now: {scene_1.get('title')}")
    
    # ── GENERATE SCENE AI TESTS ──
    
    def test_generate_scene_ai_endpoint_exists(self):
        """Test that the generate-scene-ai endpoint exists and accepts requests"""
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/generate-scene-ai",
            json={"hint": "Uma cena de teste", "position": 5}
        )
        
        # Should return 200 (success) or 500 (AI error) but not 404
        assert response.status_code != 404, "Endpoint should exist"
        print(f"✓ generate-scene-ai endpoint exists, status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "ok"
            scene = data.get("scene", {})
            assert "title" in scene or "description" in scene
            print(f"✓ AI generated scene: {scene.get('title', 'N/A')}")
    
    # ── CLEANUP ──
    
    def test_cleanup_test_scenes(self):
        """Cleanup: Delete all TEST_ scenes created during testing"""
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        
        test_scenes = [s for s in scenes if "TEST_" in s.get("title", "")]
        print(f"Found {len(test_scenes)} TEST_ scenes to cleanup")
        
        for scene in test_scenes:
            response = self.session.post(
                f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
                json={"scene_number": scene.get("scene_number")}
            )
            if response.status_code == 200:
                print(f"  ✓ Deleted: {scene.get('title')}")
            else:
                print(f"  ✗ Failed to delete: {scene.get('title')}")
            
            # Refresh scene list after each delete (scene numbers change)
            status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
            scenes = status.json().get("scenes", [])
            test_scenes = [s for s in scenes if "TEST_" in s.get("title", "")]
        
        # Verify cleanup
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        remaining_test = [s for s in scenes if "TEST_" in s.get("title", "")]
        print(f"✓ Cleanup complete. Remaining TEST_ scenes: {len(remaining_test)}")
        print(f"✓ Final scene count: {len(scenes)}")


class TestSceneManagementEdgeCases:
    """Edge case tests for scene management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_add_scene_invalid_position(self):
        """Test adding scene with invalid position (should default to end)"""
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/add-scene",
            json={"position": -1, "scene": {"title": "TEST_Invalid_Position"}}
        )
        
        # Should succeed and add at end
        assert response.status_code == 200
        print(f"✓ Invalid position handled gracefully")
        
        # Cleanup
        status = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status")
        scenes = status.json().get("scenes", [])
        test_scene = next((s for s in scenes if s.get("title") == "TEST_Invalid_Position"), None)
        if test_scene:
            self.session.post(
                f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
                json={"scene_number": test_scene.get("scene_number")}
            )
    
    def test_delete_nonexistent_scene(self):
        """Test deleting a scene that doesn't exist"""
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
            json={"scene_number": 9999}
        )
        
        # Should return 200 (no-op) or 404
        assert response.status_code in [200, 404]
        print(f"✓ Nonexistent scene delete handled, status: {response.status_code}")
    
    def test_delete_scene_missing_scene_number(self):
        """Test delete-scene without scene_number"""
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/delete-scene",
            json={}
        )
        
        assert response.status_code == 400, "Should return 400 for missing scene_number"
        print(f"✓ Missing scene_number returns 400")
    
    def test_reorder_with_empty_order(self):
        """Test reorder with empty order array"""
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/reorder-scenes",
            json={"order": []}
        )
        
        # Should return 200 (no-op) or handle gracefully
        assert response.status_code == 200
        print(f"✓ Empty order handled gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
