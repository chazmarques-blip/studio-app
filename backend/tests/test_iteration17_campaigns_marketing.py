"""
Test file for Iteration 17 - Marketing Campaign Hub & AI Studio
Tests:
- Campaign CRUD operations
- Campaign activate/pause
- Campaign templates
- Creatives CRUD
- AI Studio generate (Enterprise gating)
- Test data seeding
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestCampaignsCRUD:
    """Campaign CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token before each test class"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health check passed: {data}")
    
    def test_list_campaigns(self):
        """GET /api/campaigns - List all campaigns"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)
        print(f"✓ List campaigns: {len(data['campaigns'])} campaigns found")
    
    def test_create_campaign(self):
        """POST /api/campaigns - Create a new campaign"""
        campaign_data = {
            "name": "TEST_Campaign_Iteration17",
            "type": "nurture",
            "target_segment": {"stages": ["new"]},
            "messages": [{"step": 1, "delay_hours": 0, "channel": "whatsapp", "content": "Test message"}]
        }
        response = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == campaign_data["name"]
        assert data["type"] == campaign_data["type"]
        assert data["status"] == "draft"
        print(f"✓ Created campaign: {data['id']}, name={data['name']}")
        # Store for cleanup
        self.created_campaign_id = data["id"]
        return data["id"]
    
    def test_get_campaign_by_id(self):
        """GET /api/campaigns/{id} - Get single campaign"""
        # First create a campaign
        campaign_id = self.test_create_campaign()
        
        response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id
        print(f"✓ Get campaign by ID: {campaign_id}")
    
    def test_activate_campaign(self):
        """POST /api/campaigns/{id}/activate - Activate a draft campaign"""
        # First create a campaign
        campaign_id = self.test_create_campaign()
        
        response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/activate", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "activated"
        
        # Verify status changed
        verify_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=self.headers)
        verify_data = verify_response.json()
        assert verify_data["status"] == "active"
        print(f"✓ Campaign activated: {campaign_id}")
    
    def test_pause_campaign(self):
        """POST /api/campaigns/{id}/pause - Pause an active campaign"""
        # First create and activate a campaign
        campaign_id = self.test_create_campaign()
        requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/activate", headers=self.headers)
        
        response = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/pause", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        
        # Verify status changed
        verify_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=self.headers)
        verify_data = verify_response.json()
        assert verify_data["status"] == "paused"
        print(f"✓ Campaign paused: {campaign_id}")
    
    def test_delete_campaign(self):
        """DELETE /api/campaigns/{id} - Delete a campaign"""
        # First create a campaign
        campaign_id = self.test_create_campaign()
        
        response = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        
        # Verify campaign no longer exists
        verify_response = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=self.headers)
        assert verify_response.status_code == 404
        print(f"✓ Campaign deleted: {campaign_id}")


class TestCampaignTemplates:
    """Campaign templates endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_list_templates(self):
        """GET /api/campaigns/templates/list - List campaign templates"""
        response = requests.get(f"{BASE_URL}/api/campaigns/templates/list", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        assert len(data["templates"]) > 0
        
        # Verify template structure
        template = data["templates"][0]
        assert "id" in template
        assert "name" in template
        assert "type" in template
        assert "messages" in template
        print(f"✓ List templates: {len(data['templates'])} templates found")
        for t in data["templates"]:
            print(f"  - {t['id']}: {t['name']} ({t['type']})")


class TestCreatives:
    """Creatives endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_list_creatives(self):
        """GET /api/campaigns/creatives/list - List saved creatives"""
        response = requests.get(f"{BASE_URL}/api/campaigns/creatives/list", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "creatives" in data
        assert isinstance(data["creatives"], list)
        print(f"✓ List creatives: {len(data['creatives'])} creatives found")
    
    def test_save_creative(self):
        """POST /api/campaigns/creatives/save - Save a creative"""
        creative_data = {
            "type": "copy",
            "title": "TEST_Creative_Iteration17",
            "content": {"body": "Test creative content", "platform": "instagram"}
        }
        response = requests.post(f"{BASE_URL}/api/campaigns/creatives/save", json=creative_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == creative_data["title"]
        print(f"✓ Saved creative: {data['id']}")
        return data["id"]
    
    def test_delete_creative(self):
        """DELETE /api/campaigns/creatives/{id} - Delete a creative"""
        # First create a creative
        creative_id = self.test_save_creative()
        
        response = requests.delete(f"{BASE_URL}/api/campaigns/creatives/{creative_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        print(f"✓ Deleted creative: {creative_id}")


class TestAIStudio:
    """AI Studio endpoint tests - Enterprise plan gating"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_check_user_plan(self):
        """Verify user has Enterprise plan (required for AI Studio)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ User plan: {data.get('plan', 'unknown')}")
        return data.get("plan")
    
    def test_studio_generate_copywriter(self):
        """POST /api/campaigns/studio/generate - Test copywriter agent"""
        plan = self.test_check_user_plan()
        
        studio_data = {
            "agent_type": "copywriter",
            "prompt": "Create a short Instagram caption about AI automation",
            "context": {"company": "AgentZZ", "industry": "SaaS"}
        }
        response = requests.post(f"{BASE_URL}/api/campaigns/studio/generate", json=studio_data, headers=self.headers)
        
        if plan != "enterprise":
            # Should return 403 for non-Enterprise users
            assert response.status_code == 403
            assert "Enterprise" in response.json().get("detail", "")
            print(f"✓ AI Studio correctly blocked for non-Enterprise user")
        else:
            # Enterprise users should get 200
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "agent" in data
            assert data["agent"] == "Sofia Copywriter"
            assert "session_id" in data
            print(f"✓ AI Studio copywriter response received (Enterprise user)")
            print(f"  Agent: {data['agent']}")
            print(f"  Response time: {data.get('metadata', {}).get('response_time_ms', 'N/A')}ms")
    
    def test_studio_generate_designer(self):
        """POST /api/campaigns/studio/generate - Test designer agent"""
        plan = self.test_check_user_plan()
        if plan != "enterprise":
            pytest.skip("Skipping - Enterprise plan required")
        
        studio_data = {
            "agent_type": "designer",
            "prompt": "Create a visual concept for a social media header",
            "context": {"company": "AgentZZ"}
        }
        response = requests.post(f"{BASE_URL}/api/campaigns/studio/generate", json=studio_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "Lucas Designer"
        print(f"✓ AI Studio designer response received")
    
    def test_studio_generate_reviewer(self):
        """POST /api/campaigns/studio/generate - Test reviewer agent"""
        plan = self.test_check_user_plan()
        if plan != "enterprise":
            pytest.skip("Skipping - Enterprise plan required")
        
        studio_data = {
            "agent_type": "reviewer",
            "prompt": "Review this copy: 'Try our AI platform today!'",
            "context": {}
        }
        response = requests.post(f"{BASE_URL}/api/campaigns/studio/generate", json=studio_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "Ana Reviewer"
        print(f"✓ AI Studio reviewer response received")
    
    def test_studio_generate_publisher(self):
        """POST /api/campaigns/studio/generate - Test publisher agent"""
        plan = self.test_check_user_plan()
        if plan != "enterprise":
            pytest.skip("Skipping - Enterprise plan required")
        
        studio_data = {
            "agent_type": "publisher",
            "prompt": "Create a weekly content calendar",
            "context": {}
        }
        response = requests.post(f"{BASE_URL}/api/campaigns/studio/generate", json=studio_data, headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "Pedro Publisher"
        print(f"✓ AI Studio publisher response received")
    
    def test_studio_invalid_agent(self):
        """Test invalid agent type returns error"""
        plan = self.test_check_user_plan()
        if plan != "enterprise":
            pytest.skip("Skipping - Enterprise plan required")
        
        studio_data = {
            "agent_type": "invalid_agent",
            "prompt": "Test",
            "context": {}
        }
        response = requests.post(f"{BASE_URL}/api/campaigns/studio/generate", json=studio_data, headers=self.headers)
        assert response.status_code == 400
        assert "Unknown agent type" in response.json().get("detail", "")
        print(f"✓ Invalid agent type correctly rejected")


class TestSeedData:
    """Test data seeding endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_seed_test_data(self):
        """POST /api/campaigns/seed-test - Seed test campaigns"""
        response = requests.post(f"{BASE_URL}/api/campaigns/seed-test", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        # If already seeded, status will be 'already_seeded', otherwise 'seeded'
        assert data["status"] in ["seeded", "already_seeded"]
        print(f"✓ Seed test data: {data}")


class TestCleanup:
    """Cleanup test-created data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_cleanup_test_campaigns(self):
        """Delete TEST_ prefixed campaigns"""
        # List all campaigns
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=self.headers)
        campaigns = response.json().get("campaigns", [])
        
        deleted_count = 0
        for camp in campaigns:
            if camp["name"].startswith("TEST_"):
                del_response = requests.delete(f"{BASE_URL}/api/campaigns/{camp['id']}", headers=self.headers)
                if del_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test campaigns")
    
    def test_cleanup_test_creatives(self):
        """Delete TEST_ prefixed creatives"""
        # List all creatives
        response = requests.get(f"{BASE_URL}/api/campaigns/creatives/list", headers=self.headers)
        creatives = response.json().get("creatives", [])
        
        deleted_count = 0
        for cr in creatives:
            if cr.get("title", "").startswith("TEST_"):
                del_response = requests.delete(f"{BASE_URL}/api/campaigns/creatives/{cr['id']}", headers=self.headers)
                if del_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test creatives")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
