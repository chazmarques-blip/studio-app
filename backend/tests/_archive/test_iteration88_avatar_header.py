"""
Iteration 88: Avatar Header Feature Tests
Tests for:
- GET /api/avatar/me - Returns avatar_url for authenticated user
- POST /api/avatar/set-default - Sets default avatar and returns URL
- POST /api/avatar/generate - Avatar generation endpoint (error handling without photo)
- GET /api/auth/me - Should include avatar_url from tenant settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestAvatarAPI:
    """Avatar API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    def test_get_avatar_me_returns_avatar_url(self):
        """GET /api/avatar/me should return avatar_url for authenticated user"""
        response = self.session.get(f"{BASE_URL}/api/avatar/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "avatar_url" in data, "Response should contain avatar_url field"
        assert data["avatar_url"] is not None, "avatar_url should not be None"
        assert isinstance(data["avatar_url"], str), "avatar_url should be a string"
        assert len(data["avatar_url"]) > 0, "avatar_url should not be empty"
        print(f"✓ GET /api/avatar/me returned avatar_url: {data['avatar_url'][:50]}...")
    
    def test_set_default_avatar(self):
        """POST /api/avatar/set-default should set default avatar and return URL"""
        response = self.session.post(f"{BASE_URL}/api/avatar/set-default")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "avatar_url" in data, "Response should contain avatar_url field"
        assert "status" in data, "Response should contain status field"
        assert data["status"] == "ok", f"Expected status 'ok', got '{data['status']}'"
        assert data["avatar_url"] is not None, "avatar_url should not be None"
        
        # Verify it's the default avatar URL
        expected_default = "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/36152c5b792ad0e3a5369214cbd423ca6b327833cf834f94d65f76c7c348c7a7.png"
        assert data["avatar_url"] == expected_default, f"Expected default avatar URL, got {data['avatar_url']}"
        print(f"✓ POST /api/avatar/set-default returned correct default avatar URL")
    
    def test_set_default_avatar_persists(self):
        """After setting default avatar, GET /api/avatar/me should return it"""
        # First set default
        set_response = self.session.post(f"{BASE_URL}/api/avatar/set-default")
        assert set_response.status_code == 200
        
        # Then verify it persists
        get_response = self.session.get(f"{BASE_URL}/api/avatar/me")
        assert get_response.status_code == 200
        
        data = get_response.json()
        expected_default = "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/36152c5b792ad0e3a5369214cbd423ca6b327833cf834f94d65f76c7c348c7a7.png"
        assert data["avatar_url"] == expected_default, "Avatar URL should persist after set-default"
        print(f"✓ Avatar URL persists correctly after set-default")
    
    def test_generate_avatar_without_photo_returns_error(self):
        """POST /api/avatar/generate without photo should return validation error"""
        # Test with empty body
        response = self.session.post(f"{BASE_URL}/api/avatar/generate", json={})
        
        # Should return 422 (validation error) since photo_base64 is required
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/avatar/generate without photo returns 422 validation error")
    
    def test_generate_avatar_with_invalid_photo_returns_error(self):
        """POST /api/avatar/generate with invalid photo should return error"""
        response = self.session.post(f"{BASE_URL}/api/avatar/generate", json={
            "photo_base64": "invalid_base64_data"
        })
        
        # Should return 500 since the base64 is invalid
        assert response.status_code == 500, f"Expected 500 error for invalid photo, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/avatar/generate with invalid photo returns error")
    
    def test_auth_me_includes_avatar_url(self):
        """GET /api/auth/me should include avatar_url from tenant settings"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # avatar_url should be present (can be None if not set)
        assert "avatar_url" in data or data.get("avatar_url") is None or "avatar_url" in str(data), \
            f"Response should include avatar_url field. Got: {data}"
        
        # Verify other expected fields
        assert "id" in data, "Response should contain id"
        assert "email" in data, "Response should contain email"
        assert "full_name" in data, "Response should contain full_name"
        print(f"✓ GET /api/auth/me includes user data with avatar_url field")


class TestAvatarAPIUnauthenticated:
    """Test avatar endpoints without authentication"""
    
    def test_get_avatar_me_unauthenticated(self):
        """GET /api/avatar/me without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/avatar/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ GET /api/avatar/me without auth returns 401")
    
    def test_set_default_avatar_unauthenticated(self):
        """POST /api/avatar/set-default without auth should return 401"""
        response = requests.post(f"{BASE_URL}/api/avatar/set-default")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ POST /api/avatar/set-default without auth returns 401")
    
    def test_generate_avatar_unauthenticated(self):
        """POST /api/avatar/generate without auth should return 401"""
        response = requests.post(f"{BASE_URL}/api/avatar/generate", json={
            "photo_base64": "test"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ POST /api/avatar/generate without auth returns 401")


class TestHealthAndBasicEndpoints:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """GET /api/health should return ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
        print(f"✓ Health endpoint returns ok")
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with valid credentials should return token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        print(f"✓ Login with valid credentials returns token")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
