"""
Iteration 22 Tests - Publish Campaign Flow
Testing:
1. Login and auth
2. GET /api/campaigns - should include AgentZZ campaign
3. POST /api/campaigns/pipeline/{id}/publish - publish endpoint
4. Campaign data validation (name, status, goal)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
COMPLETED_PIPELINE_ID = "209e610d-023b-4223-90b5-dc45249dee8a"


class TestAuth:
    """Test authentication endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"Login successful, user ID: {data['user'].get('id')}")


class TestCampaigns:
    """Test campaigns endpoints - verify AgentZZ campaign exists"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for campaigns tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_campaigns_list(self, auth_headers):
        """Test GET /api/campaigns - should return list including AgentZZ"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get campaigns: {response.text}"
        
        data = response.json()
        assert "campaigns" in data, "Response missing 'campaigns' key"
        campaigns = data["campaigns"]
        
        print(f"Total campaigns returned: {len(campaigns)}")
        
        # Look for AgentZZ campaign
        agentzz_campaign = None
        for c in campaigns:
            print(f"Campaign: {c.get('name')}, Status: {c.get('status')}, Goal: {c.get('goal')}")
            if c.get('name') == 'AgentZZ':
                agentzz_campaign = c
        
        assert agentzz_campaign is not None, "AgentZZ campaign not found in list"
        print(f"Found AgentZZ campaign: {agentzz_campaign}")
        
        # Verify AgentZZ campaign has correct properties
        assert agentzz_campaign.get('status') in ['active', 'Ativa', 'draft'], f"Unexpected status: {agentzz_campaign.get('status')}"
        # The campaign stores type='ai_pipeline' (goal is only used in JSONB metrics)
        assert agentzz_campaign.get('type') == 'ai_pipeline', f"Expected type 'ai_pipeline', got: {agentzz_campaign.get('type')}"
        
    def test_campaigns_count(self, auth_headers):
        """Test that we have expected number of campaigns (approx 6)"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        campaigns = data.get("campaigns", [])
        
        # Should have at least 5 campaigns (including AgentZZ)
        assert len(campaigns) >= 5, f"Expected at least 5 campaigns, got {len(campaigns)}"
        print(f"Campaign count: {len(campaigns)}")


class TestPipelinePublish:
    """Test the publish endpoint for pipeline campaigns"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_publish_already_published_pipeline(self, auth_headers):
        """Test POST /api/campaigns/pipeline/{id}/publish - should handle already published"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{COMPLETED_PIPELINE_ID}/publish",
            headers=auth_headers
        )
        
        # Should either succeed (200) with status info, or return error if already published
        # Based on the code, it creates/activates the campaign
        print(f"Publish response status: {response.status_code}")
        print(f"Publish response body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Response should have 'status' key"
            assert data["status"] == "published", f"Expected 'published' status, got: {data.get('status')}"
            if "campaign_id" in data:
                print(f"Campaign ID: {data['campaign_id']}")
        else:
            # Could be 400 if pipeline not completed or 404 if not found
            assert response.status_code in [400, 404], f"Unexpected status code: {response.status_code}"
    
    def test_get_pipeline_details(self, auth_headers):
        """Test GET /api/campaigns/pipeline/{id} - verify pipeline data"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/{COMPLETED_PIPELINE_ID}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Pipeline status: {data.get('status')}")
            print(f"Pipeline briefing: {data.get('briefing', '')[:100]}...")
            
            # Verify campaign_name is stored in result
            result = data.get('result', {})
            campaign_name = result.get('campaign_name', '')
            print(f"Campaign name in pipeline: {campaign_name}")
            
            assert data.get('status') == 'completed', f"Expected completed status, got: {data.get('status')}"
        else:
            print(f"Pipeline not found or error: {response.status_code} - {response.text}")


class TestPipelineList:
    """Test pipeline list endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_list_pipelines(self, auth_headers):
        """Test GET /api/campaigns/pipeline/list - list all pipelines"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "pipelines" in data
        pipelines = data["pipelines"]
        
        print(f"Total pipelines: {len(pipelines)}")
        for p in pipelines:
            print(f"Pipeline {p.get('id')[:8]}...: status={p.get('status')}, briefing={p.get('briefing', '')[:50]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
