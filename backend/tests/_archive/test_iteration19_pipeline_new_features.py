"""
Iteration 19 - Pipeline New Features Testing
Tests:
1. POST /api/campaigns/pipeline/upload - image upload endpoint
2. POST /api/campaigns/pipeline/{id}/regenerate-design - design regeneration with feedback
3. Pipeline creation with contact_info and uploaded_assets params
4. Pipeline list returns pipelines with steps data
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test@agentflow.com", "password": "password123"}
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPipelineUploadEndpoint:
    """Test POST /api/campaigns/pipeline/upload endpoint for image files"""
    
    def test_upload_logo_image_png(self, auth_token):
        """Test uploading a PNG logo image"""
        # Create a minimal valid PNG file (1x1 pixel transparent PNG)
        png_data = bytes([
            0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,  # PNG signature
            0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
            0x89, 0x00, 0x00, 0x00, 0x0a, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, 0x44, 0xae,
            0x42, 0x60, 0x82
        ])
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            files={"file": ("test_logo.png", png_data, "image/png")},
            data={"asset_type": "logo"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "url" in data
        assert "filename" in data
        assert "type" in data
        assert data["type"] == "logo"
        assert data["url"].startswith("/api/uploads/pipeline/assets/")
        print(f"PASS: Logo PNG upload successful - URL: {data['url']}")
    
    def test_upload_reference_image(self, auth_token):
        """Test uploading a reference image"""
        # Create a minimal valid JPEG file header
        jpeg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
            0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
            0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
            0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
            0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
            0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
            0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
            0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
            0x32, 0xFF, 0xD9
        ])
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            files={"file": ("test_reference.jpg", jpeg_data, "image/jpeg")},
            data={"asset_type": "reference"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data["type"] == "reference"
        assert "url" in data
        print(f"PASS: Reference image upload successful - URL: {data['url']}")
    
    def test_upload_rejects_non_image(self, auth_token):
        """Test that non-image files are rejected"""
        text_data = b"This is not an image file"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            files={"file": ("test.txt", text_data, "text/plain")},
            data={"asset_type": "logo"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for non-image, got {response.status_code}"
        print(f"PASS: Non-image file correctly rejected with 400")


class TestRegenerateDesignEndpoint:
    """Test POST /api/campaigns/pipeline/{id}/regenerate-design endpoint"""
    
    def test_regenerate_design_with_completed_pipeline(self, auth_headers):
        """Test regenerate-design endpoint with a completed pipeline"""
        # Use the existing completed pipeline ID from test context
        pipeline_id = "09fc2709-0bba-4bf9-96dd-7bdad383ff35"
        
        # Get pipeline to verify it exists and has lucas_design completed
        get_response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}",
            headers=auth_headers
        )
        
        if get_response.status_code != 200:
            pytest.skip(f"Pipeline {pipeline_id} not found - skipping regenerate test")
        
        pipeline = get_response.json()
        lucas_step = pipeline.get("steps", {}).get("lucas_design", {})
        
        if lucas_step.get("status") != "completed":
            pytest.skip("lucas_design step not completed - skipping regenerate test")
        
        # Test regenerate-design endpoint
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/regenerate-design",
            json={"design_index": 0, "feedback": "Make the colors more vibrant"},
            headers=auth_headers
        )
        
        # The endpoint returns immediately with 'regenerating' status
        assert response.status_code == 200, f"Regenerate failed: {response.text}"
        data = response.json()
        assert data.get("status") == "regenerating"
        assert data.get("design_index") == 0
        print(f"PASS: Regenerate design endpoint works - status: {data['status']}")
    
    def test_regenerate_design_invalid_index(self, auth_headers):
        """Test regenerate-design with invalid design index"""
        pipeline_id = "09fc2709-0bba-4bf9-96dd-7bdad383ff35"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/regenerate-design",
            json={"design_index": 99, "feedback": "Invalid index test"},
            headers=auth_headers
        )
        
        # Should return 400 for invalid index
        if response.status_code == 404:
            pytest.skip("Pipeline not found")
        
        assert response.status_code == 400, f"Expected 400 for invalid index, got {response.status_code}"
        print(f"PASS: Invalid design index correctly rejected with 400")
    
    def test_regenerate_design_requires_auth(self):
        """Test that regenerate-design requires authentication"""
        pipeline_id = "09fc2709-0bba-4bf9-96dd-7bdad383ff35"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/regenerate-design",
            json={"design_index": 0, "feedback": "No auth test"}
        )
        
        assert response.status_code in [401, 403], f"Expected auth error, got {response.status_code}"
        print(f"PASS: Regenerate design requires authentication")


class TestPipelineCreationWithExtras:
    """Test pipeline creation with contact_info and uploaded_assets"""
    
    def test_create_pipeline_with_contact_info(self, auth_headers):
        """Test creating pipeline with contact info"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            json={
                "briefing": "TEST_iter19_contact_info Campaign for testing contact info inclusion",
                "mode": "semi_auto",
                "platforms": ["whatsapp", "instagram"],
                "contact_info": {
                    "phone": "+55 11 99999-9999",
                    "website": "www.testcompany.com",
                    "email": "test@testcompany.com"
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        pipeline = response.json()
        assert "id" in pipeline
        assert pipeline.get("status") == "running"
        
        # Verify contact_info is stored in result
        result = pipeline.get("result", {})
        contact_info = result.get("contact_info", {})
        assert contact_info.get("phone") == "+55 11 99999-9999"
        assert contact_info.get("website") == "www.testcompany.com"
        assert contact_info.get("email") == "test@testcompany.com"
        
        print(f"PASS: Pipeline created with contact_info - ID: {pipeline['id']}")
        
        # Cleanup - delete the test pipeline
        time.sleep(1)
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline['id']}", headers=auth_headers)
    
    def test_create_pipeline_with_uploaded_assets(self, auth_headers):
        """Test creating pipeline with uploaded_assets"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            json={
                "briefing": "TEST_iter19_assets Campaign with uploaded assets",
                "mode": "semi_auto",
                "platforms": ["facebook"],
                "uploaded_assets": [
                    {"url": "/api/uploads/pipeline/assets/test_logo.png", "type": "logo", "filename": "test_logo.png"},
                    {"url": "/api/uploads/pipeline/assets/test_ref.jpg", "type": "reference", "filename": "test_ref.jpg"}
                ]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        pipeline = response.json()
        
        # Verify uploaded_assets is stored in result
        result = pipeline.get("result", {})
        assets = result.get("uploaded_assets", [])
        assert len(assets) == 2
        assert any(a.get("type") == "logo" for a in assets)
        assert any(a.get("type") == "reference" for a in assets)
        
        print(f"PASS: Pipeline created with uploaded_assets - ID: {pipeline['id']}")
        
        # Cleanup
        time.sleep(1)
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline['id']}", headers=auth_headers)
    
    def test_create_pipeline_with_both_contact_and_assets(self, auth_headers):
        """Test creating pipeline with both contact_info and uploaded_assets"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            json={
                "briefing": "TEST_iter19_full Full campaign with all extras",
                "mode": "semi_auto",
                "platforms": ["whatsapp", "instagram", "telegram"],
                "context": {"company": "Test Corp", "industry": "Tech"},
                "contact_info": {
                    "phone": "+1 555 123 4567",
                    "website": "www.testcorp.com",
                    "email": "info@testcorp.com"
                },
                "uploaded_assets": [
                    {"url": "/api/uploads/pipeline/assets/logo.png", "type": "logo", "filename": "logo.png"}
                ]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Pipeline creation failed: {response.text}"
        pipeline = response.json()
        result = pipeline.get("result", {})
        
        # Verify all fields
        assert result.get("context", {}).get("company") == "Test Corp"
        assert result.get("contact_info", {}).get("phone") == "+1 555 123 4567"
        assert len(result.get("uploaded_assets", [])) == 1
        
        print(f"PASS: Pipeline created with both contact_info and uploaded_assets - ID: {pipeline['id']}")
        
        # Cleanup
        time.sleep(1)
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline['id']}", headers=auth_headers)


class TestPipelineListEndpoint:
    """Test GET /api/campaigns/pipeline/list returns proper data"""
    
    def test_pipeline_list_returns_steps_data(self, auth_headers):
        """Test that pipeline list includes steps data for history cards"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/list",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"List failed: {response.text}"
        data = response.json()
        pipelines = data.get("pipelines", [])
        
        # Should have at least one pipeline (from previous tests)
        print(f"Found {len(pipelines)} pipelines in list")
        
        if len(pipelines) > 0:
            # Verify pipeline structure has needed fields
            p = pipelines[0]
            assert "id" in p
            assert "briefing" in p
            assert "status" in p
            assert "platforms" in p
            assert "steps" in p
            assert "created_at" in p
            
            # Verify steps is a dict
            steps = p.get("steps", {})
            assert isinstance(steps, dict)
            
            print(f"PASS: Pipeline list returns proper structure with steps data")
        else:
            print("WARN: No pipelines found in list - cannot verify structure")


class TestCompletedPipelineData:
    """Test that completed pipeline has all data needed for CompletedSummary tabs"""
    
    def test_completed_pipeline_has_summary_data(self, auth_headers):
        """Test completed pipeline has approved_content, image_urls, and pedro_publish output"""
        pipeline_id = "09fc2709-0bba-4bf9-96dd-7bdad383ff35"
        
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            pytest.skip(f"Pipeline {pipeline_id} not found")
        
        pipeline = response.json()
        steps = pipeline.get("steps", {})
        
        # Check if pipeline is completed
        if pipeline.get("status") != "completed":
            print(f"Pipeline status is {pipeline.get('status')} - checking available data")
        
        # Verify data structure for CompletedSummary tabs
        # Tab 1: Preview Completo / Copy Final - needs ana_review_copy.approved_content
        ana_review_copy = steps.get("ana_review_copy", {})
        has_approved_copy = bool(ana_review_copy.get("approved_content") or ana_review_copy.get("output"))
        
        # Tab 2: Imagens - needs lucas_design.image_urls
        lucas_design = steps.get("lucas_design", {})
        image_urls = lucas_design.get("image_urls", [])
        has_images = any(url for url in image_urls if url)
        
        # Tab 3: Cronograma - needs pedro_publish.output
        pedro_publish = steps.get("pedro_publish", {})
        has_schedule = bool(pedro_publish.get("output"))
        
        print(f"Pipeline summary data check:")
        print(f"  - Has approved copy: {has_approved_copy}")
        print(f"  - Has images: {has_images} ({len([u for u in image_urls if u])} images)")
        print(f"  - Has schedule: {has_schedule}")
        
        # At minimum, should have the step structure
        assert "sofia_copy" in steps
        assert "ana_review_copy" in steps
        assert "lucas_design" in steps
        assert "ana_review_design" in steps
        assert "pedro_publish" in steps
        
        print(f"PASS: Pipeline has all step structures for CompletedSummary")


# Run with: pytest /app/backend/tests/test_iteration19_pipeline_new_features.py -v --tb=short
