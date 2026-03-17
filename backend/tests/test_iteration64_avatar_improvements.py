"""
Iteration 64 Backend Tests - Avatar Generation Improvements
Tests: EDIT-based generation prompt, Logo background removal, _gemini_edit_multi_ref function
"""
import pytest
import requests
import os
import time
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-campaign-hub.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and get access token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }, timeout=30)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    # Uses access_token, not token
    token = data.get("access_token")
    assert token, f"No access_token in response: {data}"
    return token

@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for requests"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestBackendStartup:
    """Backend health and startup tests"""
    
    def test_backend_running(self):
        """Backend is running and responding"""
        resp = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        # Even unauthorized, should return 4xx not 5xx
        assert resp.status_code < 500, f"Backend error: {resp.status_code}"
        print("PASSED: Backend is running")


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_returns_access_token(self):
        """Login returns access_token field (not token)"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=30)
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        assert "access_token" in data, f"Missing access_token in: {data.keys()}"
        assert data["access_token"], "access_token is empty"
        print(f"PASSED: Login returns access_token field")


class TestAvatarGenerationEndpoints:
    """Test avatar generation endpoints with logo_url parameter"""
    
    def test_generate_avatar_with_accuracy_accepts_logo_url(self, auth_headers):
        """POST /api/campaigns/pipeline/generate-avatar-with-accuracy accepts logo_url and returns job_id"""
        # Use a placeholder image URL for testing
        payload = {
            "source_image_url": "https://via.placeholder.com/400x400.png",
            "video_frame_urls": [],
            "company_name": "TestCompany",
            "logo_url": "https://via.placeholder.com/100x100.png",
            "max_iterations": 1
        }
        resp = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "job_id" in data, f"Response should contain job_id: {data}"
        print(f"PASSED: generate-avatar-with-accuracy accepts logo_url, job_id={data['job_id'][:10]}...")
        return data["job_id"]
    
    def test_generate_avatar_with_accuracy_status(self, auth_headers):
        """GET /api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id} returns status"""
        # First create a job
        payload = {
            "source_image_url": "https://via.placeholder.com/400x400.png",
            "logo_url": "https://via.placeholder.com/100x100.png",
            "max_iterations": 1
        }
        resp = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert resp.status_code == 200, f"Job creation failed: {resp.text}"
        job_id = resp.json()["job_id"]
        
        # Check status
        status_resp = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id}",
            headers=auth_headers,
            timeout=30
        )
        assert status_resp.status_code == 200, f"Status check failed: {status_resp.status_code}"
        data = status_resp.json()
        assert "status" in data, f"Response should contain status: {data}"
        assert data["status"] in ["processing", "completed", "failed"], f"Invalid status: {data['status']}"
        print(f"PASSED: Status endpoint returns valid status: {data['status']}")
    
    def test_generate_avatar_variant_accepts_logo_url(self, auth_headers):
        """POST /api/campaigns/pipeline/generate-avatar-variant accepts logo_url parameter"""
        payload = {
            "source_image_url": "https://via.placeholder.com/400x400.png",
            "clothing": "company_uniform",
            "logo_url": "https://via.placeholder.com/100x100.png"
        }
        resp = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        # Should not return 422 (validation error)
        assert resp.status_code != 422, f"422 validation error - logo_url not accepted: {resp.text}"
        # 200 or 500 (if image generation fails) is acceptable - we're testing param acceptance
        assert resp.status_code in [200, 500], f"Unexpected status: {resp.status_code}"
        print(f"PASSED: generate-avatar-variant accepts logo_url (status: {resp.status_code})")
    
    def test_generate_avatar_360_accepts_logo_url(self, auth_headers):
        """POST /api/campaigns/pipeline/generate-avatar-360 accepts logo_url and returns job_id"""
        payload = {
            "source_image_url": "https://via.placeholder.com/400x400.png",
            "clothing": "company_uniform",
            "logo_url": "https://via.placeholder.com/100x100.png"
        }
        resp = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            json=payload,
            headers=auth_headers,
            timeout=60
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "job_id" in data, f"Response should contain job_id: {data}"
        print(f"PASSED: generate-avatar-360 accepts logo_url, job_id={data['job_id'][:10]}...")


class TestCompaniesAndAvatarsData:
    """Test company and avatar data endpoints"""
    
    def test_get_companies(self, auth_headers):
        """GET /api/data/companies returns list of companies"""
        resp = requests.get(f"{BASE_URL}/api/data/companies", headers=auth_headers, timeout=30)
        assert resp.status_code == 200, f"Failed: {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASSED: GET /api/data/companies returns {len(data)} companies")
        
        # Check if companies have logo_url field
        if data:
            company = data[0]
            # logo_url is an optional field
            print(f"  - First company: {company.get('name', 'Unknown')}, has_logo_url: {'logo_url' in company}")
    
    def test_get_avatars(self, auth_headers):
        """GET /api/data/avatars returns list of avatars"""
        resp = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers, timeout=30)
        assert resp.status_code == 200, f"Failed: {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"PASSED: GET /api/data/avatars returns {len(data)} avatars")


class TestCodeVerification:
    """Verify code implementation details"""
    
    def test_pass_threshold_is_7(self):
        """PASS_THRESHOLD in _accuracy_compare should be 7"""
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        # Find PASS_THRESHOLD
        match = re.search(r'PASS_THRESHOLD\s*=\s*(\d+)', content)
        assert match, "PASS_THRESHOLD not found in pipeline.py"
        threshold = int(match.group(1))
        assert threshold == 7, f"PASS_THRESHOLD should be 7, got {threshold}"
        print(f"PASSED: PASS_THRESHOLD = {threshold}")
    
    def test_composite_logo_function_exists(self):
        """_composite_logo_on_avatar function exists and uses numpy"""
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        assert "def _composite_logo_on_avatar" in content, "Function _composite_logo_on_avatar not found"
        
        # Check for numpy usage in the file (near the function)
        assert "import numpy as np" in content, "numpy import not found"
        assert "dark_mask" in content, "dark_mask variable not found (black background removal)"
        assert "< 50" in content, "Threshold check (< 50) not found for dark pixel detection"
        print("PASSED: _composite_logo_on_avatar exists and uses numpy for black background removal")
    
    def test_gemini_edit_multi_ref_exists(self):
        """_gemini_edit_multi_ref function exists for multiple reference images"""
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        assert "_gemini_edit_multi_ref" in content, "Function _gemini_edit_multi_ref not found"
        assert "extra_refs" in content, "extra_refs parameter not found in _gemini_edit_multi_ref"
        print("PASSED: _gemini_edit_multi_ref function exists with extra_refs parameter")
    
    def test_avatar_accuracy_request_has_logo_url(self):
        """AvatarAccuracyRequest model includes logo_url field"""
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        # Find AvatarAccuracyRequest class
        class_match = re.search(r'class AvatarAccuracyRequest\(BaseModel\):([\s\S]*?)(?=\nclass |\ndef |\n\n\n)', content)
        assert class_match, "AvatarAccuracyRequest class not found"
        class_body = class_match.group(1)
        assert "logo_url" in class_body, "logo_url field not in AvatarAccuracyRequest"
        print("PASSED: AvatarAccuracyRequest has logo_url field")
    
    def test_json_parsing_uses_regex_first(self):
        """_accuracy_compare uses regex-first approach for score extraction"""
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        # Check that function exists
        assert "async def _accuracy_compare" in content, "_accuracy_compare function not found"
        
        # Check for regex score extraction pattern
        assert 'score_match = re.search' in content, "re.search for score not found in _accuracy_compare"
        assert '"score"' in content, "score extraction pattern not found"
        assert 'extracted_score' in content, "extracted_score variable not found"
        print("PASSED: _accuracy_compare uses regex-first approach for score extraction")


class TestFrontendResolveImageUrl:
    """Test resolveImageUrl utility for cache-busting"""
    
    def test_resolve_image_url_file_exists(self):
        """resolveImageUrl.js file exists and has cache-busting logic"""
        util_path = "/app/frontend/src/utils/resolveImageUrl.js"
        with open(util_path, "r") as f:
            content = f.read()
        
        assert "resolveImageUrl" in content, "resolveImageUrl function not found"
        assert "supabase" in content, "Supabase URL handling not found"
        assert "Date.now()" in content or "t=" in content, "Cache-busting logic not found"
        print("PASSED: resolveImageUrl.js has cache-busting for Supabase Storage URLs")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
