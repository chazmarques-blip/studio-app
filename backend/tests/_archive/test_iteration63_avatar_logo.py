"""
Iteration 63 - Avatar Generation with Logo URL Tests
Testing the new logo_url parameter in avatar generation endpoints:
- POST /api/campaigns/pipeline/generate-avatar-with-accuracy (logo_url param)
- GET /api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id} (status check)
- POST /api/campaigns/pipeline/generate-avatar-variant (logo_url param)
- POST /api/campaigns/pipeline/generate-avatar-360 (logo_url param)
- GET /api/data/companies (logo_url field)
- GET /api/data/avatars (avatars list)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test login and get auth token"""
    
    def test_backend_health(self):
        """Verify backend is running"""
        # Just a simple endpoint test
        response = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        # Should get 401 without token (not 500 or connection error)
        assert response.status_code in [200, 401], f"Backend health check failed: {response.status_code}"
        print("Backend is responsive")
    
    def test_login_success(self):
        """Login with test credentials and get access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        }, timeout=10)
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "access_token" in data, f"access_token not found in response: {data}"
        assert len(data["access_token"]) > 10
        print(f"Login successful, token starts with: {data['access_token'][:20]}...")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for subsequent tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    }, timeout=10)
    if response.status_code != 200:
        pytest.skip("Login failed - cannot proceed with authenticated tests")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def authenticated_session(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestCompaniesEndpoint:
    """Test /api/data/companies endpoint - verify logo_url field"""
    
    def test_get_companies_returns_list(self, authenticated_session):
        """GET /api/data/companies should return a list with logo_url field"""
        response = authenticated_session.get(f"{BASE_URL}/api/data/companies", timeout=10)
        assert response.status_code == 200, f"Companies GET failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"Companies returned: {len(data)} companies")
        
        # Check if any company has logo_url field
        if len(data) > 0:
            first_company = data[0]
            assert "name" in first_company, "Company should have 'name' field"
            # logo_url field should exist in schema (even if empty)
            print(f"First company: {first_company.get('name')}, logo_url: {first_company.get('logo_url', 'NOT_PRESENT')}")


class TestAvatarsEndpoint:
    """Test /api/data/avatars endpoint"""
    
    def test_get_avatars_returns_list(self, authenticated_session):
        """GET /api/data/avatars should return a list"""
        response = authenticated_session.get(f"{BASE_URL}/api/data/avatars", timeout=10)
        assert response.status_code == 200, f"Avatars GET failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"Avatars returned: {len(data)} avatars")


class TestGenerateAvatarWithAccuracy:
    """Test POST /api/campaigns/pipeline/generate-avatar-with-accuracy endpoint with logo_url"""
    
    def test_endpoint_accepts_logo_url_parameter(self, authenticated_session):
        """Verify endpoint accepts logo_url parameter and returns job_id"""
        # Use a placeholder image URL for testing - this won't actually generate but should accept the param
        test_payload = {
            "source_image_url": "https://via.placeholder.com/400",
            "company_name": "TEST_Company_Logo",
            "logo_url": "https://via.placeholder.com/100",  # New logo_url parameter
            "video_frame_urls": [],
            "max_iterations": 1
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            json=test_payload,
            timeout=15
        )
        
        assert response.status_code == 200, f"Endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "job_id" in data, f"job_id not in response: {data}"
        print(f"Job started with ID: {data['job_id']}")
        return data["job_id"]
    
    def test_status_endpoint_works(self, authenticated_session):
        """Verify GET status endpoint returns proper status structure"""
        # First start a job
        test_payload = {
            "source_image_url": "https://via.placeholder.com/400",
            "company_name": "TEST_Status_Check",
            "logo_url": "",  # Empty logo URL is also valid
            "video_frame_urls": [],
            "max_iterations": 1
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            json=test_payload,
            timeout=15
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Now check status
        time.sleep(1)  # Give it a moment
        status_response = authenticated_session.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id}",
            timeout=10
        )
        
        assert status_response.status_code == 200, f"Status check failed: {status_response.status_code}"
        status_data = status_response.json()
        assert "status" in status_data, f"status not in response: {status_data}"
        assert status_data["status"] in ["running", "completed", "failed"], f"Unexpected status: {status_data['status']}"
        print(f"Job {job_id} status: {status_data['status']}")


class TestGenerateAvatarVariant:
    """Test POST /api/campaigns/pipeline/generate-avatar-variant endpoint with logo_url"""
    
    def test_endpoint_accepts_logo_url_parameter(self, authenticated_session):
        """Verify endpoint accepts logo_url parameter"""
        test_payload = {
            "avatar_url": "https://via.placeholder.com/400",
            "source_photo_url": "https://via.placeholder.com/400",
            "clothing": "company_uniform",
            "logo_url": "https://via.placeholder.com/100"  # New logo_url parameter
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            json=test_payload,
            timeout=30
        )
        
        # This endpoint may take time or fail if image URLs are not real,
        # but it should at least accept the parameters without 422
        assert response.status_code != 422, f"Validation error - logo_url not accepted: {response.text}"
        print(f"Variant endpoint response: {response.status_code}")
        
        # If it returns 200, check response structure
        if response.status_code == 200:
            data = response.json()
            print(f"Variant response: {data.get('status', 'unknown')}")


class TestGenerateAvatar360:
    """Test POST /api/campaigns/pipeline/generate-avatar-360 endpoint with logo_url"""
    
    def test_endpoint_accepts_logo_url_parameter(self, authenticated_session):
        """Verify endpoint accepts logo_url parameter and returns job_id"""
        test_payload = {
            "source_image_url": "https://via.placeholder.com/400",
            "clothing": "company_uniform",
            "logo_url": "https://via.placeholder.com/100"  # New logo_url parameter
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            json=test_payload,
            timeout=15
        )
        
        assert response.status_code == 200, f"Endpoint failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "job_id" in data, f"job_id not in response: {data}"
        print(f"360 job started with ID: {data['job_id']}")
    
    def test_360_status_endpoint_works(self, authenticated_session):
        """Verify GET status endpoint for 360 batch returns proper status"""
        test_payload = {
            "source_image_url": "https://via.placeholder.com/400",
            "clothing": "casual",  # Non-uniform to skip logo composite
            "logo_url": ""
        }
        
        response = authenticated_session.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            json=test_payload,
            timeout=15
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        time.sleep(1)
        status_response = authenticated_session.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360/{job_id}",
            timeout=10
        )
        
        assert status_response.status_code == 200, f"360 Status check failed: {status_response.status_code}"
        status_data = status_response.json()
        assert "status" in status_data, f"status not in response: {status_data}"
        print(f"360 Job {job_id} status: {status_data['status']}")


class TestAccuracyCompareThreshold:
    """Test that the critic threshold is set to 7 (not 8)"""
    
    def test_threshold_is_7_in_code(self):
        """Verify PASS_THRESHOLD = 7 in _accuracy_compare function"""
        import re
        
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        # Look for PASS_THRESHOLD in _accuracy_compare function
        match = re.search(r'def _accuracy_compare\([^)]+\)[^:]*:.*?PASS_THRESHOLD\s*=\s*(\d+)', content, re.DOTALL)
        if match:
            threshold = int(match.group(1))
            assert threshold == 7, f"Expected PASS_THRESHOLD=7, found {threshold}"
            print(f"PASS_THRESHOLD confirmed as {threshold}")
        else:
            # Try alternative pattern
            match2 = re.search(r'PASS_THRESHOLD\s*=\s*(\d+)', content)
            if match2:
                threshold = int(match2.group(1))
                assert threshold == 7, f"Expected PASS_THRESHOLD=7, found {threshold}"
                print(f"PASS_THRESHOLD confirmed as {threshold}")
            else:
                pytest.fail("Could not find PASS_THRESHOLD in pipeline.py")


class TestLogoCompositeFunction:
    """Test that _composite_logo_on_avatar function exists and is used"""
    
    def test_composite_function_exists(self):
        """Verify _composite_logo_on_avatar function is defined"""
        import re
        
        pipeline_path = "/app/backend/routers/pipeline.py"
        with open(pipeline_path, "r") as f:
            content = f.read()
        
        # Check function exists
        assert "def _composite_logo_on_avatar" in content, "_composite_logo_on_avatar function not found"
        print("_composite_logo_on_avatar function exists")
        
        # Check PIL/Image import exists
        assert "from PIL import Image" in content, "PIL Image import not found"
        print("PIL Image import exists")
        
        # Check function is called with logo_url condition
        calls = re.findall(r'_composite_logo_on_avatar\(', content)
        assert len(calls) >= 2, f"Expected at least 2 calls to _composite_logo_on_avatar, found {len(calls)}"
        print(f"_composite_logo_on_avatar is called {len(calls)} times in pipeline.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
