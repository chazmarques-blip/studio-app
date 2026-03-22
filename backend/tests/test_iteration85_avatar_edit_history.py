"""
Test iteration 85: Avatar Edit History Persistence Feature
Tests for:
- POST /api/data/avatars with edit_history field - should persist edit_history array
- GET /api/data/avatars - should return edit_history for each avatar
- DELETE /api/data/avatars/{avatar_id}/history/{entry_index} - should delete a specific history entry
- DELETE /api/data/avatars/{avatar_id}/history/{entry_index} - invalid index should return 400
- DELETE /api/data/avatars/{avatar_id}/history/{entry_index} - invalid avatar_id should return 404
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestAvatarEditHistoryPersistence:
    """Tests for avatar edit_history persistence feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get access token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        login_data = login_response.json()
        # Auth returns 'access_token' field (not 'token')
        token = login_data.get("access_token")
        assert token, f"No access_token in response: {login_data}"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.test_avatar_id = None
        yield
        
        # Cleanup: delete test avatar if created
        if self.test_avatar_id:
            try:
                self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}")
            except:
                pass
    
    def test_01_create_avatar_with_edit_history(self):
        """Test POST /api/data/avatars with edit_history field persists correctly"""
        test_edit_history = [
            {
                "url": "https://example.com/avatar_base.png",
                "instruction": "Base original",
                "timestamp": "2026-03-22T10:00:00.000Z",
                "isBase": True
            },
            {
                "url": "https://example.com/avatar_v2.png",
                "instruction": "Changed clothing to casual",
                "timestamp": "2026-03-22T10:05:00.000Z",
                "isBase": False
            },
            {
                "url": "https://example.com/avatar_v3.png",
                "instruction": "Added sunglasses",
                "timestamp": "2026-03-22T10:10:00.000Z",
                "isBase": False
            }
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_{int(time.time())}",
            "url": "https://example.com/avatar_v3.png",
            "name": "TEST Avatar with History",
            "source_photo_url": "https://example.com/source.png",
            "clothing": "casual",
            "language": "pt",
            "edit_history": test_edit_history
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert response.status_code == 200, f"Create avatar failed: {response.text}"
        
        data = response.json()
        self.test_avatar_id = data.get("id")
        
        # Verify edit_history is returned in response
        assert "edit_history" in data, "edit_history not in response"
        assert len(data["edit_history"]) == 3, f"Expected 3 history entries, got {len(data['edit_history'])}"
        
        # Verify history entries structure
        assert data["edit_history"][0]["isBase"] == True, "First entry should be base"
        assert data["edit_history"][0]["instruction"] == "Base original"
        assert data["edit_history"][1]["instruction"] == "Changed clothing to casual"
        assert data["edit_history"][2]["instruction"] == "Added sunglasses"
        
        print(f"PASS: Avatar created with edit_history containing {len(data['edit_history'])} entries")
    
    def test_02_get_avatars_returns_edit_history(self):
        """Test GET /api/data/avatars returns edit_history for each avatar"""
        # First create an avatar with history
        test_edit_history = [
            {"url": "https://example.com/base.png", "instruction": "Base original", "timestamp": "2026-03-22T10:00:00.000Z", "isBase": True},
            {"url": "https://example.com/v2.png", "instruction": "Edit 1", "timestamp": "2026-03-22T10:05:00.000Z", "isBase": False}
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_get_{int(time.time())}",
            "url": "https://example.com/v2.png",
            "name": "TEST Avatar for GET",
            "edit_history": test_edit_history
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Now GET all avatars
        get_response = self.session.get(f"{BASE_URL}/api/data/avatars")
        assert get_response.status_code == 200, f"GET avatars failed: {get_response.text}"
        
        avatars = get_response.json()
        assert isinstance(avatars, list), "Response should be a list"
        
        # Find our test avatar
        test_avatar = next((a for a in avatars if a.get("id") == self.test_avatar_id), None)
        assert test_avatar is not None, f"Test avatar {self.test_avatar_id} not found in list"
        
        # Verify edit_history is present
        assert "edit_history" in test_avatar, "edit_history not in avatar from GET"
        assert len(test_avatar["edit_history"]) == 2, f"Expected 2 history entries, got {len(test_avatar['edit_history'])}"
        
        print(f"PASS: GET /api/data/avatars returns edit_history with {len(test_avatar['edit_history'])} entries")
    
    def test_03_delete_history_entry_success(self):
        """Test DELETE /api/data/avatars/{avatar_id}/history/{entry_index} deletes specific entry"""
        # Create avatar with 3 history entries
        test_edit_history = [
            {"url": "https://example.com/base.png", "instruction": "Base original", "timestamp": "2026-03-22T10:00:00.000Z", "isBase": True},
            {"url": "https://example.com/v2.png", "instruction": "Edit 1 - to delete", "timestamp": "2026-03-22T10:05:00.000Z", "isBase": False},
            {"url": "https://example.com/v3.png", "instruction": "Edit 2", "timestamp": "2026-03-22T10:10:00.000Z", "isBase": False}
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_delete_{int(time.time())}",
            "url": "https://example.com/v3.png",
            "name": "TEST Avatar for Delete",
            "edit_history": test_edit_history
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Delete entry at index 1 (the "Edit 1 - to delete" entry)
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}/history/1")
        assert delete_response.status_code == 200, f"Delete history entry failed: {delete_response.text}"
        
        delete_data = delete_response.json()
        assert delete_data.get("status") == "ok", "Expected status 'ok'"
        assert "edit_history" in delete_data, "Response should include updated edit_history"
        
        # Verify the entry was deleted
        remaining_history = delete_data["edit_history"]
        assert len(remaining_history) == 2, f"Expected 2 entries after delete, got {len(remaining_history)}"
        
        # Verify the correct entry was deleted (index 1 should now be "Edit 2")
        assert remaining_history[0]["instruction"] == "Base original", "Base entry should remain"
        assert remaining_history[1]["instruction"] == "Edit 2", "Edit 2 should now be at index 1"
        
        print(f"PASS: DELETE history entry at index 1 successful, {len(remaining_history)} entries remaining")
    
    def test_04_delete_history_entry_invalid_index_returns_400(self):
        """Test DELETE with invalid index returns 400"""
        # Create avatar with 2 history entries
        test_edit_history = [
            {"url": "https://example.com/base.png", "instruction": "Base", "timestamp": "2026-03-22T10:00:00.000Z", "isBase": True},
            {"url": "https://example.com/v2.png", "instruction": "Edit 1", "timestamp": "2026-03-22T10:05:00.000Z", "isBase": False}
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_invalid_idx_{int(time.time())}",
            "url": "https://example.com/v2.png",
            "name": "TEST Avatar Invalid Index",
            "edit_history": test_edit_history
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Try to delete entry at index 10 (out of bounds)
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}/history/10")
        assert delete_response.status_code == 400, f"Expected 400 for invalid index, got {delete_response.status_code}"
        
        error_data = delete_response.json()
        assert "detail" in error_data, "Error response should have detail"
        assert "invalid" in error_data["detail"].lower() or "index" in error_data["detail"].lower(), \
            f"Error message should mention invalid index: {error_data['detail']}"
        
        print(f"PASS: DELETE with invalid index returns 400 with message: {error_data['detail']}")
    
    def test_05_delete_history_entry_negative_index_returns_400(self):
        """Test DELETE with negative index returns 400"""
        # Create avatar with history
        test_edit_history = [
            {"url": "https://example.com/base.png", "instruction": "Base", "timestamp": "2026-03-22T10:00:00.000Z", "isBase": True}
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_neg_idx_{int(time.time())}",
            "url": "https://example.com/base.png",
            "name": "TEST Avatar Negative Index",
            "edit_history": test_edit_history
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Try to delete entry at index -1 (negative)
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}/history/-1")
        # FastAPI may return 422 for invalid path parameter or 400 for business logic
        assert delete_response.status_code in [400, 422], f"Expected 400 or 422 for negative index, got {delete_response.status_code}"
        
        print(f"PASS: DELETE with negative index returns {delete_response.status_code}")
    
    def test_06_delete_history_entry_invalid_avatar_id_returns_404(self):
        """Test DELETE with non-existent avatar_id returns 404"""
        fake_avatar_id = "nonexistent_avatar_12345"
        
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{fake_avatar_id}/history/0")
        assert delete_response.status_code == 404, f"Expected 404 for invalid avatar_id, got {delete_response.status_code}"
        
        error_data = delete_response.json()
        assert "detail" in error_data, "Error response should have detail"
        assert "not found" in error_data["detail"].lower() or "avatar" in error_data["detail"].lower(), \
            f"Error message should mention avatar not found: {error_data['detail']}"
        
        print(f"PASS: DELETE with invalid avatar_id returns 404 with message: {error_data['detail']}")
    
    def test_07_update_avatar_preserves_edit_history(self):
        """Test that updating an avatar preserves its edit_history"""
        # Create avatar with history
        test_edit_history = [
            {"url": "https://example.com/base.png", "instruction": "Base", "timestamp": "2026-03-22T10:00:00.000Z", "isBase": True},
            {"url": "https://example.com/v2.png", "instruction": "Edit 1", "timestamp": "2026-03-22T10:05:00.000Z", "isBase": False}
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_update_{int(time.time())}",
            "url": "https://example.com/v2.png",
            "name": "TEST Avatar Update",
            "edit_history": test_edit_history
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Update the avatar with new history entry
        updated_history = test_edit_history + [
            {"url": "https://example.com/v3.png", "instruction": "Edit 2 - new", "timestamp": "2026-03-22T10:15:00.000Z", "isBase": False}
        ]
        
        update_data = {
            "id": self.test_avatar_id,
            "url": "https://example.com/v3.png",
            "name": "TEST Avatar Update - Modified",
            "edit_history": updated_history
        }
        
        update_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=update_data)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_avatar = update_response.json()
        assert len(updated_avatar["edit_history"]) == 3, f"Expected 3 history entries after update, got {len(updated_avatar['edit_history'])}"
        assert updated_avatar["edit_history"][2]["instruction"] == "Edit 2 - new"
        
        # Verify via GET
        get_response = self.session.get(f"{BASE_URL}/api/data/avatars")
        assert get_response.status_code == 200
        
        avatars = get_response.json()
        test_avatar = next((a for a in avatars if a.get("id") == self.test_avatar_id), None)
        assert test_avatar is not None
        assert len(test_avatar["edit_history"]) == 3
        
        print(f"PASS: Avatar update preserves and extends edit_history to {len(test_avatar['edit_history'])} entries")
    
    def test_08_create_avatar_without_edit_history(self):
        """Test creating avatar without edit_history initializes empty array"""
        avatar_data = {
            "id": f"TEST_avatar_no_history_{int(time.time())}",
            "url": "https://example.com/avatar.png",
            "name": "TEST Avatar No History"
            # No edit_history field
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        self.test_avatar_id = data.get("id")
        
        # edit_history should be initialized as empty array
        assert "edit_history" in data, "edit_history should be in response"
        assert data["edit_history"] == [], f"edit_history should be empty array, got {data['edit_history']}"
        
        print("PASS: Avatar without edit_history initializes with empty array")
    
    def test_09_delete_history_entry_empty_history_returns_400(self):
        """Test DELETE on avatar with empty history returns 400"""
        # Create avatar without history
        avatar_data = {
            "id": f"TEST_avatar_empty_hist_{int(time.time())}",
            "url": "https://example.com/avatar.png",
            "name": "TEST Avatar Empty History",
            "edit_history": []
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Try to delete entry at index 0 (no entries exist)
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}/history/0")
        assert delete_response.status_code == 400, f"Expected 400 for empty history, got {delete_response.status_code}"
        
        print("PASS: DELETE on empty history returns 400")


class TestAvatarEditHistoryDataIntegrity:
    """Tests for data integrity of edit_history"""
    
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
        self.test_avatar_id = None
        yield
        
        if self.test_avatar_id:
            try:
                self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}")
            except:
                pass
    
    def test_10_edit_history_preserves_all_fields(self):
        """Test that all fields in edit_history entries are preserved"""
        test_edit_history = [
            {
                "url": "https://example.com/base.png",
                "instruction": "Base original",
                "timestamp": "2026-03-22T10:00:00.000Z",
                "isBase": True,
                "extra_field": "should be preserved"  # Extra field
            }
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_fields_{int(time.time())}",
            "url": "https://example.com/base.png",
            "name": "TEST Avatar Fields",
            "edit_history": test_edit_history
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert response.status_code == 200
        
        data = response.json()
        self.test_avatar_id = data.get("id")
        
        # Verify all fields are preserved
        history_entry = data["edit_history"][0]
        assert history_entry["url"] == "https://example.com/base.png"
        assert history_entry["instruction"] == "Base original"
        assert history_entry["timestamp"] == "2026-03-22T10:00:00.000Z"
        assert history_entry["isBase"] == True
        
        print("PASS: All edit_history fields are preserved")
    
    def test_11_multiple_sequential_deletes(self):
        """Test multiple sequential delete operations work correctly"""
        # Create avatar with 4 history entries
        test_edit_history = [
            {"url": "https://example.com/v1.png", "instruction": "Base", "timestamp": "2026-03-22T10:00:00.000Z", "isBase": True},
            {"url": "https://example.com/v2.png", "instruction": "Edit 1", "timestamp": "2026-03-22T10:05:00.000Z", "isBase": False},
            {"url": "https://example.com/v3.png", "instruction": "Edit 2", "timestamp": "2026-03-22T10:10:00.000Z", "isBase": False},
            {"url": "https://example.com/v4.png", "instruction": "Edit 3", "timestamp": "2026-03-22T10:15:00.000Z", "isBase": False}
        ]
        
        avatar_data = {
            "id": f"TEST_avatar_multi_del_{int(time.time())}",
            "url": "https://example.com/v4.png",
            "name": "TEST Avatar Multi Delete",
            "edit_history": test_edit_history
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=avatar_data)
        assert create_response.status_code == 200
        created_avatar = create_response.json()
        self.test_avatar_id = created_avatar.get("id")
        
        # Delete entry at index 1 (Edit 1)
        del1_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}/history/1")
        assert del1_response.status_code == 200
        remaining = del1_response.json()["edit_history"]
        assert len(remaining) == 3
        
        # Delete entry at index 1 again (now Edit 2)
        del2_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{self.test_avatar_id}/history/1")
        assert del2_response.status_code == 200
        remaining = del2_response.json()["edit_history"]
        assert len(remaining) == 2
        
        # Verify remaining entries
        assert remaining[0]["instruction"] == "Base"
        assert remaining[1]["instruction"] == "Edit 3"
        
        print(f"PASS: Multiple sequential deletes work correctly, {len(remaining)} entries remaining")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
