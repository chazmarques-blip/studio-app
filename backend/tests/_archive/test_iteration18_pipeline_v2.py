"""
Iteration 18 v2 - Pipeline API Testing for New Features
Tests for the new AgentZZ AI Marketing Pipeline features:

Features tested:
- POST /api/campaigns/pipeline/upload - File upload for brand logos and reference images
- POST /api/campaigns/pipeline - Create pipeline with contact_info and uploaded_assets
- Pipeline creation response includes result.contact_info and result.uploaded_assets
- GET /api/campaigns/pipeline/list - List pipelines with history
- GET /api/campaigns/pipeline/{id} - Get pipeline with steps data for CompletedSummary
"""

import pytest
import requests
import time
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestPipelineUpload:
    """Test the file upload endpoint POST /api/campaigns/pipeline/upload"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_upload_logo_image(self, auth_headers):
        """POST /api/campaigns/pipeline/upload - Upload a logo image"""
        # Create a simple test image (1x1 PNG)
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82  # IEND chunk
        ])
        
        files = {
            'file': ('test_logo.png', io.BytesIO(png_bytes), 'image/png')
        }
        data = {'asset_type': 'logo'}
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        # Validate response structure
        assert "url" in result, "Response should have 'url'"
        assert "filename" in result, "Response should have 'filename'"
        assert "type" in result, "Response should have 'type'"
        assert "size" in result, "Response should have 'size'"
        
        assert result["type"] == "logo", f"Type should be 'logo', got {result['type']}"
        assert result["url"].startswith("/api/uploads/pipeline/assets/"), f"URL should start with /api/uploads/pipeline/assets/, got {result['url']}"
        assert result["filename"].startswith("logo_"), f"Filename should start with 'logo_', got {result['filename']}"
        
        print(f"Logo upload successful: {result}")
    
    def test_upload_reference_image(self, auth_headers):
        """POST /api/campaigns/pipeline/upload - Upload a reference image"""
        # Create a simple test image (1x1 PNG)
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {
            'file': ('reference_style.png', io.BytesIO(png_bytes), 'image/png')
        }
        data = {'asset_type': 'reference'}
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        assert result["type"] == "reference", f"Type should be 'reference', got {result['type']}"
        assert result["filename"].startswith("reference_"), f"Filename should start with 'reference_', got {result['filename']}"
        
        print(f"Reference image upload successful: {result}")
    
    def test_upload_rejects_non_image(self, auth_headers):
        """POST /api/campaigns/pipeline/upload - Should reject non-image files"""
        files = {
            'file': ('test.txt', io.BytesIO(b'This is not an image'), 'text/plain')
        }
        data = {'asset_type': 'logo'}
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            headers=auth_headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 400, f"Should reject non-image, got {response.status_code}"
        result = response.json()
        assert "image" in result.get("detail", "").lower(), "Error should mention image requirement"
        print(f"Non-image correctly rejected: {result}")


class TestPipelineWithContactAndAssets:
    """Test pipeline creation with contact_info and uploaded_assets"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_create_pipeline_with_contact_info(self, auth_headers):
        """POST /api/campaigns/pipeline - Create with contact_info in request body"""
        payload = {
            "briefing": "TEST_Campanha com dados de contato para teste",
            "mode": "auto",
            "platforms": ["whatsapp", "instagram"],
            "context": {
                "company": "Test Company",
                "industry": "Tech",
                "audience": "Developers",
                "brand_voice": "Professional"
            },
            "contact_info": {
                "phone": "+55 11 99999-9999",
                "website": "www.testcompany.com",
                "email": "contato@testcompany.com"
            },
            "uploaded_assets": []
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json=payload)
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        
        data = response.json()
        pipeline_id = data["id"]
        
        # Verify contact_info is stored in result
        assert "result" in data, "Response should have 'result'"
        result = data.get("result", {})
        assert "contact_info" in result, "Result should have 'contact_info'"
        
        contact_info = result.get("contact_info", {})
        assert contact_info.get("phone") == "+55 11 99999-9999", "Phone should match"
        assert contact_info.get("website") == "www.testcompany.com", "Website should match"
        assert contact_info.get("email") == "contato@testcompany.com", "Email should match"
        
        print(f"Pipeline created with contact_info: {contact_info}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
    
    def test_create_pipeline_with_uploaded_assets(self, auth_headers):
        """POST /api/campaigns/pipeline - Create with uploaded_assets in request body"""
        payload = {
            "briefing": "TEST_Campanha com assets para teste",
            "mode": "auto",
            "platforms": ["instagram"],
            "context": {},
            "contact_info": {},
            "uploaded_assets": [
                {"url": "/api/uploads/pipeline/assets/test_logo.png", "type": "logo", "filename": "test_logo.png"},
                {"url": "/api/uploads/pipeline/assets/test_ref.png", "type": "reference", "filename": "test_ref.png"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json=payload)
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        
        data = response.json()
        pipeline_id = data["id"]
        
        # Verify uploaded_assets is stored in result
        result = data.get("result", {})
        assert "uploaded_assets" in result, "Result should have 'uploaded_assets'"
        
        assets = result.get("uploaded_assets", [])
        assert len(assets) == 2, f"Should have 2 assets, got {len(assets)}"
        
        asset_types = [a["type"] for a in assets]
        assert "logo" in asset_types, "Should have logo asset"
        assert "reference" in asset_types, "Should have reference asset"
        
        print(f"Pipeline created with uploaded_assets: {assets}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
    
    def test_create_pipeline_with_both_contact_and_assets(self, auth_headers):
        """POST /api/campaigns/pipeline - Create with both contact_info and assets"""
        payload = {
            "briefing": "TEST_Campanha completa com contato e assets",
            "mode": "semi_auto",
            "platforms": ["whatsapp", "instagram", "facebook"],
            "context": {
                "company": "AgentZZ",
                "industry": "SaaS / AI"
            },
            "contact_info": {
                "phone": "+55 21 88888-8888",
                "website": "www.agentzz.com",
                "email": "hello@agentzz.com"
            },
            "uploaded_assets": [
                {"url": "/api/uploads/pipeline/assets/logo_brand.png", "type": "logo", "filename": "logo_brand.png"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json=payload)
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        
        data = response.json()
        pipeline_id = data["id"]
        
        # Verify both are stored
        result = data.get("result", {})
        assert result.get("contact_info", {}).get("phone") == "+55 21 88888-8888"
        assert len(result.get("uploaded_assets", [])) == 1
        
        print(f"Pipeline with both contact and assets created: {pipeline_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)


class TestPipelineHistoryMetadata:
    """Test pipeline list returns proper metadata for history cards"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_pipeline_list_has_metadata_for_cards(self, auth_headers):
        """GET /api/campaigns/pipeline/list - Verify response has fields needed for HistoryCard"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=auth_headers)
        assert response.status_code == 200, f"List failed: {response.text}"
        
        data = response.json()
        pipelines = data.get("pipelines", [])
        
        if len(pipelines) == 0:
            print("No existing pipelines - creating one for test")
            # Create a test pipeline
            create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
                "briefing": "TEST_Pipeline para teste de metadata",
                "mode": "auto",
                "platforms": ["whatsapp"]
            })
            pipeline_id = create_resp.json().get("id")
            
            # Re-fetch list
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=auth_headers)
            pipelines = response.json().get("pipelines", [])
            
            # Cleanup later
            test_pipeline_id = pipeline_id
        else:
            test_pipeline_id = None
        
        # Verify each pipeline has required fields for HistoryCard component
        for p in pipelines:
            assert "id" in p, "Pipeline should have 'id'"
            assert "briefing" in p, "Pipeline should have 'briefing'"
            assert "status" in p, "Pipeline should have 'status'"
            assert "platforms" in p, "Pipeline should have 'platforms'"
            assert "steps" in p, "Pipeline should have 'steps'"
            assert "created_at" in p, "Pipeline should have 'created_at'"
            
            # For completed pipelines, verify steps has image_urls for thumbnails
            steps = p.get("steps", {})
            if p.get("status") == "completed" and "lucas_design" in steps:
                lucas = steps.get("lucas_design", {})
                # image_urls should exist (may be empty or have URLs)
                print(f"Pipeline {p['id']}: lucas_design has image_urls={lucas.get('image_urls', 'NOT_SET')}")
        
        print(f"Verified metadata for {len(pipelines)} pipelines")
        
        # Cleanup if we created one
        if test_pipeline_id:
            requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{test_pipeline_id}", headers=auth_headers)


class TestCompletedPipelineSummaryData:
    """Test that completed pipelines have all data needed for CompletedSummary component"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_completed_pipeline_has_summary_data(self, auth_headers):
        """Verify completed pipeline has data for 3 tabs: Copy Final, Images, Schedule"""
        # Get list of pipelines
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=auth_headers)
        assert response.status_code == 200
        
        pipelines = response.json().get("pipelines", [])
        
        # Find a completed pipeline
        completed = [p for p in pipelines if p.get("status") == "completed"]
        
        if len(completed) == 0:
            print("No completed pipelines found - skipping summary data test")
            pytest.skip("No completed pipelines available for testing")
        
        pipeline = completed[0]
        steps = pipeline.get("steps", {})
        
        # Tab 1: Copy Final - needs ana_review_copy.approved_content OR sofia_copy.output
        ana_copy = steps.get("ana_review_copy", {})
        sofia = steps.get("sofia_copy", {})
        has_copy = bool(ana_copy.get("approved_content") or sofia.get("output"))
        
        # Tab 2: Images - needs lucas_design.image_urls
        lucas = steps.get("lucas_design", {})
        image_urls = lucas.get("image_urls", [])
        has_images = len([u for u in image_urls if u]) > 0
        
        # Tab 3: Schedule - needs pedro_publish.output
        pedro = steps.get("pedro_publish", {})
        has_schedule = bool(pedro.get("output"))
        
        print(f"Completed pipeline {pipeline['id']}:")
        print(f"  - Copy Final (approved_content): {bool(ana_copy.get('approved_content'))}")
        print(f"  - Copy Final (sofia output): {bool(sofia.get('output'))}")
        print(f"  - Images: {len(image_urls)} URLs, has_images={has_images}")
        print(f"  - Schedule: {has_schedule}")
        
        # At minimum, a completed pipeline should have copy
        assert has_copy, "Completed pipeline should have copy content"
        
        # Pedro's output indicates full completion
        if has_schedule:
            print("Pipeline has full completion with schedule")


class TestPipelineRetry:
    """Test pipeline retry functionality"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_retry_endpoint_exists(self, auth_headers):
        """POST /api/campaigns/pipeline/{id}/retry - Verify endpoint exists"""
        # Create a pipeline
        create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Pipeline para teste de retry",
            "mode": "auto",
            "platforms": ["whatsapp"]
        })
        assert create_resp.status_code in [200, 201]
        pipeline_id = create_resp.json()["id"]
        
        # Try retry (will fail if not in retryable state, but endpoint should exist)
        retry_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/retry", headers=auth_headers)
        
        # Accept either success or "not retryable" error
        assert retry_resp.status_code in [200, 400], f"Unexpected status: {retry_resp.status_code}"
        
        if retry_resp.status_code == 400:
            # Should explain why not retryable
            detail = retry_resp.json().get("detail", "")
            print(f"Retry rejected (expected): {detail}")
        else:
            print(f"Retry initiated: {retry_resp.json()}")
        
        # Cleanup
        time.sleep(1)
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
