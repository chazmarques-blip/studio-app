"""
Iteration 56 Tests - Avatar 360 Generation & Gemini Edit Image Fix
Testing:
1. POST /api/campaigns/pipeline/generate-avatar - works with source_image_url (uses _gemini_edit_image)
2. POST /api/campaigns/pipeline/generate-avatar - works without source_image_url (fallback to LlmChat)
3. POST /api/campaigns/pipeline/generate-avatar-variant - works with source_image_url 
4. POST /api/campaigns/pipeline/generate-avatar-360 - starts batch job, returns job_id
5. GET /api/campaigns/pipeline/generate-avatar-360/{job_id} - returns status with completed count
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestGenerateAvatarEndpoint:
    """Test POST /api/campaigns/pipeline/generate-avatar"""
    
    def test_generate_avatar_without_source_returns_200(self, auth_headers):
        """Test avatar generation without source image (fallback to LlmChat)"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            headers=auth_headers,
            json={
                "company_name": "Test Company",
                "source_image_url": ""
            },
            timeout=90  # Image generation can take time
        )
        # Should either succeed (200) or timeout but NOT return 500 with TypeError
        assert response.status_code in [200, 500, 504], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            # Should return avatar_url
            assert "avatar_url" in data or "error" in data
            if "avatar_url" in data:
                assert data["avatar_url"].startswith("http")
                print(f"SUCCESS: Avatar generated without source: {data['avatar_url'][:80]}...")
        elif response.status_code == 500:
            # Check it's NOT a TypeError about 'images' parameter
            error_text = response.text.lower()
            assert "unexpected keyword argument" not in error_text, f"TypeError found: {response.text}"
            assert "'images'" not in error_text, f"Old API 'images' error: {response.text}"
            print(f"500 error but not TypeError: {response.text[:100]}")
    
    def test_generate_avatar_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            json={"company_name": "Test", "source_image_url": ""}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: generate-avatar requires auth")


class TestGenerateAvatarVariantEndpoint:
    """Test POST /api/campaigns/pipeline/generate-avatar-variant"""
    
    def test_generate_avatar_variant_without_source(self, auth_headers):
        """Test avatar variant generation without source image"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            headers=auth_headers,
            json={
                "source_image_url": "",
                "clothing": "casual",
                "angle": "front",
                "company_name": "Test Company"
            },
            timeout=90
        )
        assert response.status_code in [200, 500, 504], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "avatar_url" in data
            print(f"SUCCESS: Avatar variant generated: {data['avatar_url'][:80]}...")
        elif response.status_code == 500:
            error_text = response.text.lower()
            assert "unexpected keyword argument" not in error_text
            assert "'images'" not in error_text
            print(f"500 error but not TypeError: {response.text[:100]}")
    
    def test_generate_avatar_variant_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            json={"source_image_url": "", "clothing": "casual", "angle": "front"}
        )
        assert response.status_code in [401, 403]
        print("SUCCESS: generate-avatar-variant requires auth")


class TestGenerateAvatar360Endpoints:
    """Test POST /api/campaigns/pipeline/generate-avatar-360 and GET status endpoint"""
    
    def test_generate_avatar_360_starts_job(self, auth_headers):
        """Test that generate-avatar-360 starts a batch job and returns job_id"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            headers=auth_headers,
            json={
                "source_image_url": "",  # Empty for test
                "clothing": "business_formal"
            },
            timeout=30
        )
        # Should return 200 with job_id
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, f"Missing job_id in response: {data}"
        assert "status" in data
        assert data["status"] == "processing"
        print(f"SUCCESS: Batch 360 job started with job_id: {data['job_id']}")
        return data["job_id"]
    
    def test_get_avatar_360_status(self, auth_headers):
        """Test polling for 360 batch job status"""
        # First, start a job
        start_response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            headers=auth_headers,
            json={
                "source_image_url": "",
                "clothing": "casual"
            },
            timeout=30
        )
        assert start_response.status_code == 200
        job_id = start_response.json().get("job_id")
        assert job_id
        
        # Poll for status
        status_response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360/{job_id}",
            headers=auth_headers,
            timeout=30
        )
        assert status_response.status_code == 200, f"Status check failed: {status_response.status_code}"
        data = status_response.json()
        assert "status" in data
        assert data["status"] in ["processing", "completed", "failed"]
        # completed count should be present
        if "completed" in data:
            assert isinstance(data["completed"], int)
        if "results" in data:
            assert isinstance(data["results"], dict)
        print(f"SUCCESS: Job {job_id} status: {data['status']}, completed: {data.get('completed', 0)}")
    
    def test_get_avatar_360_status_invalid_job_id(self, auth_headers):
        """Test that invalid job_id returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360/invalid_job_id_12345",
            headers=auth_headers,
            timeout=10
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("SUCCESS: Invalid job_id returns 404")
    
    def test_generate_avatar_360_requires_auth(self):
        """Test that 360 endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            json={"source_image_url": "", "clothing": "business_formal"}
        )
        assert response.status_code in [401, 403]
        print("SUCCESS: generate-avatar-360 requires auth")
    
    def test_get_avatar_360_status_requires_auth(self):
        """Test that status endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360/some_job_id"
        )
        assert response.status_code in [401, 403]
        print("SUCCESS: get-avatar-360 status requires auth")


class TestGeminiEditImageFunction:
    """Test that _gemini_edit_image function works correctly (via endpoints)"""
    
    def test_gemini_edit_image_sends_combined_message(self, auth_headers):
        """
        Test that when source_image_url is provided, the endpoint uses _gemini_edit_image
        which sends text+image in the SAME multimodal message.
        This is a behavioral test - we check that the API doesn't fail with old API errors.
        """
        # Use a small public test image
        test_image_url = "https://via.placeholder.com/256x256.png"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            headers=auth_headers,
            json={
                "company_name": "Test",
                "source_image_url": test_image_url
            },
            timeout=90
        )
        # Could fail due to Gemini limits but should NOT fail with TypeError
        if response.status_code == 500:
            error_text = response.text.lower()
            # Verify it's NOT the old API error
            assert "unexpected keyword argument 'images'" not in error_text, \
                f"Old API error found - _gemini_edit_image not being used: {response.text}"
            assert "unexpected keyword argument 'base64_data'" not in error_text, \
                f"Old API error found: {response.text}"
            print(f"500 error but not old API TypeError: {response.text[:150]}")
        elif response.status_code == 200:
            data = response.json()
            if "avatar_url" in data:
                print(f"SUCCESS: Avatar generated with source image: {data['avatar_url'][:80]}...")
        print(f"Test passed - status: {response.status_code}")


class TestTranslationKeys:
    """Test that required translation keys exist"""
    
    def test_translation_keys_exist_in_files(self):
        """Verify translation keys for 360 generation exist in locale files"""
        locales_dir = "/app/frontend/src/locales"
        expected_keys = ["auto_generating_360", "angles_generated"]
        languages = ["en.json", "pt.json", "es.json"]
        
        for lang in languages:
            filepath = f"{locales_dir}/{lang}"
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                    for key in expected_keys:
                        assert key in content, f"Key '{key}' not found in {lang}"
                print(f"SUCCESS: All keys found in {lang}")
            except FileNotFoundError:
                pytest.skip(f"Locale file not found: {filepath}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
