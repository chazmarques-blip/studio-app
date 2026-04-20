"""
Iteration 68 Tests - Avatar Language and Voice Persistence
Tests:
1. POST /api/data/avatars with language='es' - verify it saves and returns language field
2. GET /api/data/avatars - verify avatars include language field
3. POST /api/data/avatars with voice data - verify voice is persisted
4. DELETE /api/data/avatars/{id} - verify cleanup works
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestAvatarLanguageField:
    """Test avatar language field persistence"""
    
    def test_create_avatar_with_language_es(self, auth_headers):
        """Test creating avatar with Spanish language"""
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar ES",
            "url": "https://example.com/avatar.png",
            "language": "es",
            "clothing": "casual"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        
        print(f"Create avatar response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("language") == "es", f"Expected language='es', got {data.get('language')}"
        assert data.get("id") == test_id
        assert data.get("name") == "Test Avatar ES"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/data/avatars/{test_id}", headers=auth_headers)
        
        print("PASSED: Avatar created with language='es'")
    
    def test_create_avatar_with_language_pt(self, auth_headers):
        """Test creating avatar with Portuguese language (default)"""
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar PT",
            "url": "https://example.com/avatar_pt.png",
            "language": "pt"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("language") == "pt", f"Expected language='pt', got {data.get('language')}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/data/avatars/{test_id}", headers=auth_headers)
        
        print("PASSED: Avatar created with language='pt'")
    
    def test_list_avatars_includes_language(self, auth_headers):
        """Test GET /api/data/avatars returns language field"""
        # First create an avatar with specific language
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar for List",
            "url": "https://example.com/avatar_list.png",
            "language": "en"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        assert create_resp.status_code == 200
        
        # Now list all avatars
        response = requests.get(
            f"{BASE_URL}/api/data/avatars",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        avatars = response.json()
        
        # Find our test avatar
        test_avatar = next((a for a in avatars if a.get("id") == test_id), None)
        assert test_avatar is not None, "Test avatar not found in list"
        assert test_avatar.get("language") == "en", f"Language field not correct: {test_avatar.get('language')}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/data/avatars/{test_id}", headers=auth_headers)
        
        print("PASSED: GET avatars includes language field")


class TestAvatarVoicePersistence:
    """Test avatar voice data persistence"""
    
    def test_create_avatar_with_voice_custom(self, auth_headers):
        """Test creating avatar with custom voice (url-based)"""
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar Voice",
            "url": "https://example.com/avatar_voice.png",
            "language": "pt",
            "voice": {
                "type": "custom",
                "url": "https://example.com/voice.mp3"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        
        print(f"Create avatar with voice response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("voice") is not None, "Voice field is missing"
        assert data["voice"].get("type") == "custom"
        assert data["voice"].get("url") == "https://example.com/voice.mp3"
        
        # Verify persistence by fetching
        get_resp = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers)
        avatars = get_resp.json()
        persisted_avatar = next((a for a in avatars if a.get("id") == test_id), None)
        assert persisted_avatar is not None
        assert persisted_avatar.get("voice", {}).get("url") == "https://example.com/voice.mp3"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/data/avatars/{test_id}", headers=auth_headers)
        
        print("PASSED: Avatar created with custom voice")
    
    def test_create_avatar_with_voice_openai(self, auth_headers):
        """Test creating avatar with OpenAI voice (voice_id based)"""
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar OpenAI Voice",
            "url": "https://example.com/avatar_openai.png",
            "language": "en",
            "voice": {
                "type": "openai",
                "voice_id": "shimmer"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("voice") is not None
        assert data["voice"].get("type") == "openai"
        assert data["voice"].get("voice_id") == "shimmer"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/data/avatars/{test_id}", headers=auth_headers)
        
        print("PASSED: Avatar created with OpenAI voice")
    
    def test_update_avatar_voice(self, auth_headers):
        """Test updating an existing avatar's voice"""
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        
        # Create without voice
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar Update",
            "url": "https://example.com/avatar_update.png",
            "language": "pt"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        assert create_resp.status_code == 200
        
        # Update with voice
        update_data = {
            "id": test_id,
            "name": "Test Avatar Update",
            "url": "https://example.com/avatar_update.png",
            "language": "es",  # Also update language
            "voice": {
                "type": "custom",
                "url": "https://example.com/new_voice.mp3"
            }
        }
        
        update_resp = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=update_data,
            headers=auth_headers
        )
        
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data.get("language") == "es", "Language not updated"
        assert data.get("voice", {}).get("url") == "https://example.com/new_voice.mp3"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/data/avatars/{test_id}", headers=auth_headers)
        
        print("PASSED: Avatar voice updated")


class TestAvatarDeletion:
    """Test avatar deletion cleanup"""
    
    def test_delete_avatar(self, auth_headers):
        """Test DELETE /api/data/avatars/{id}"""
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        avatar_data = {
            "id": test_id,
            "name": "Test Avatar Delete",
            "url": "https://example.com/avatar_delete.png",
            "language": "pt"
        }
        
        # Create
        create_resp = requests.post(
            f"{BASE_URL}/api/data/avatars",
            json=avatar_data,
            headers=auth_headers
        )
        assert create_resp.status_code == 200
        
        # Delete
        delete_resp = requests.delete(
            f"{BASE_URL}/api/data/avatars/{test_id}",
            headers=auth_headers
        )
        
        print(f"Delete response: {delete_resp.status_code}")
        assert delete_resp.status_code == 200
        
        # Verify deletion - avatar should not be in list
        get_resp = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers)
        avatars = get_resp.json()
        deleted_avatar = next((a for a in avatars if a.get("id") == test_id), None)
        assert deleted_avatar is None, "Avatar was not deleted"
        
        print("PASSED: Avatar deleted successfully")


class TestLoginAndAuth:
    """Test login endpoint"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        print(f"Login response: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        
        print("PASSED: Login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
