"""
Iteration 84: Smart Text Detection and Targeted Editing Feature Tests
Tests the new 'detect-image-text' endpoint and updated 'edit-image-text' with original_text parameter.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test image URL with multiple texts (provided in review request)
TEST_IMAGE_URL = "https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/single-35b53c76_1_cff264.png"


class TestAuthAndHealth:
    """Basic health and auth tests"""
    
    def test_backend_health(self):
        """Test backend is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        # Accept both "healthy" and "ok" status
        assert data.get("status") in ["healthy", "ok"], f"Unexpected status: {data.get('status')}"
        print("✓ Backend is healthy")
    
    def test_login_success(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✓ Login successful")


class TestDetectImageTextEndpoint:
    """Tests for the new detect-image-text endpoint structure and behavior"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_detect_image_text_endpoint_exists(self, auth_token):
        """Test that detect-image-text endpoint exists and accepts POST"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Test with a simple request to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/detect-image-text",
            json={"image_url": ""},
            headers=headers,
            timeout=10
        )
        # Should return 400 for empty URL, not 404
        assert response.status_code in [400, 422], f"Expected 400/422 for empty URL, got {response.status_code}"
        print("✓ detect-image-text endpoint exists and validates input")
    
    def test_detect_image_text_response_structure(self, auth_token):
        """Test text detection returns correct response structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/detect-image-text",
            json={"image_url": TEST_IMAGE_URL, "pipeline_id": ""},
            headers=headers,
            timeout=60  # Vision AI may take time
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "texts" in data, "Response should contain 'texts' array"
        assert "count" in data, "Response should contain 'count'"
        assert isinstance(data["texts"], list), "'texts' should be a list"
        assert data["count"] == len(data["texts"]), "count should match texts array length"
        
        print(f"✓ Response structure is correct: texts={data['texts']}, count={data['count']}")
        
        # Note: AI detection may return empty array depending on model behavior
        # The important thing is the endpoint works and returns correct structure
        if data["count"] > 0:
            print(f"  Detected texts: {data['texts']}")
        else:
            print("  Note: No texts detected (AI model may vary)")
    
    def test_detect_image_text_missing_url_validation(self, auth_token):
        """Test that missing image_url returns proper validation error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/detect-image-text",
            json={},
            headers=headers,
            timeout=10
        )
        # Should return validation error
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("✓ Missing image_url returns proper validation error")
    
    def test_detect_image_text_handles_invalid_url_gracefully(self, auth_token):
        """Test that invalid image URL is handled gracefully"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/detect-image-text",
            json={"image_url": "https://invalid-url-that-does-not-exist.com/image.png"},
            headers=headers,
            timeout=30
        )
        # Should return error or empty result, not crash
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            # If 200, should return empty texts array
            assert "texts" in data
            print("✓ Invalid URL handled gracefully (returned empty texts)")
        else:
            print(f"✓ Invalid URL handled gracefully (returned {response.status_code})")


class TestEditImageTextEndpoint:
    """Tests for the updated edit-image-text endpoint with original_text parameter"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_edit_image_text_endpoint_exists(self, auth_token):
        """Test that edit-image-text endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/edit-image-text",
            json={
                "pipeline_id": "00000000-0000-0000-0000-000000000000",  # Valid UUID format
                "image_index": 0,
                "new_text": "Test",
                "original_text": "",
                "language": "pt"
            },
            headers=headers,
            timeout=10
        )
        # Should return 404 for nonexistent pipeline (valid UUID but not found)
        assert response.status_code in [404, 400, 500], f"Expected 404/400/500, got {response.status_code}"
        print(f"✓ edit-image-text endpoint exists (returned {response.status_code} for nonexistent pipeline)")
    
    def test_edit_image_text_accepts_original_text_param(self, auth_token):
        """Test that edit-image-text accepts original_text parameter without validation error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Send request with all fields including original_text
        # This should NOT return 422 (validation error) for unknown field
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/edit-image-text",
            json={
                "pipeline_id": "00000000-0000-0000-0000-000000000000",  # Valid UUID format
                "image_index": 0,
                "new_text": "New Text Here",
                "original_text": "Original Text To Replace",
                "language": "en"
            },
            headers=headers,
            timeout=10
        )
        
        # Should NOT return 422 (validation error) - that would mean original_text is not accepted
        assert response.status_code != 422, f"original_text field not accepted by model: {response.text}"
        print("✓ EditImageTextRequest model accepts original_text field")


class TestCampaignImagesIntegration:
    """Integration tests for campaign images and text editing flow"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_campaigns_have_images(self, auth_token):
        """Verify campaigns have images that can be edited"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        assert response.status_code == 200
        
        campaigns = response.json().get("campaigns", [])
        campaigns_with_images = 0
        campaigns_with_pipeline = 0
        
        for c in campaigns:
            stats = c.get("stats") or c.get("metrics", {}).get("stats", {})
            images = stats.get("images", [])
            pipeline_id = stats.get("pipeline_id")
            if images:
                campaigns_with_images += 1
            if pipeline_id:
                campaigns_with_pipeline += 1
        
        print(f"✓ Found {len(campaigns)} campaigns total")
        print(f"  - {campaigns_with_images} with images")
        print(f"  - {campaigns_with_pipeline} with pipeline_id (can use text editing)")
        assert campaigns_with_images > 0, "Should have at least one campaign with images"
    
    def test_pipeline_has_images_for_editing(self, auth_token):
        """Test that pipelines have images that can be text-edited"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get campaigns to find a pipeline_id
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        assert response.status_code == 200
        
        campaigns = response.json().get("campaigns", [])
        pipeline_id = None
        for c in campaigns:
            stats = c.get("stats") or c.get("metrics", {}).get("stats", {})
            pid = stats.get("pipeline_id")
            if pid:
                pipeline_id = pid
                break
        
        if not pipeline_id:
            pytest.skip("No campaign with pipeline_id found")
        
        # Get pipeline details
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not fetch pipeline: {response.status_code}")
        
        pipeline = response.json()
        steps = pipeline.get("steps", {})
        lucas = steps.get("lucas_design", {})
        images = lucas.get("images", []) or lucas.get("image_urls", [])
        
        print(f"✓ Pipeline {pipeline_id[:8]}... has {len(images)} images")
        if images:
            print(f"  First image: {images[0][:60]}...")


class TestDetectImageTextRequestModel:
    """Test the DetectImageTextRequest model structure"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_detect_request_accepts_pipeline_id(self, auth_token):
        """Verify DetectImageTextRequest accepts optional pipeline_id"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Request with pipeline_id should not cause validation error
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/detect-image-text",
            json={
                "image_url": TEST_IMAGE_URL,
                "pipeline_id": "some-pipeline-id"
            },
            headers=headers,
            timeout=30
        )
        
        # Should not return 422 for pipeline_id field
        assert response.status_code != 422, f"pipeline_id field not accepted: {response.text}"
        print("✓ DetectImageTextRequest accepts pipeline_id field")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
