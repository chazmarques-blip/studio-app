"""
Test suite for Dashboard Stats API - Iteration 13
Tests the enhanced /api/dashboard/stats endpoint with rich data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardStats:
    """Dashboard Stats endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def authenticated_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_dashboard_stats_endpoint_returns_200(self, authenticated_headers):
        """Test that dashboard stats endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_dashboard_stats_has_messages_today(self, authenticated_headers):
        """Test messages_today field exists and is numeric"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "messages_today" in data, "messages_today field missing"
        assert isinstance(data["messages_today"], (int, float)), "messages_today should be numeric"
    
    def test_dashboard_stats_has_resolution_rate(self, authenticated_headers):
        """Test resolution_rate field exists and is percentage"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "resolution_rate" in data, "resolution_rate field missing"
        assert isinstance(data["resolution_rate"], (int, float)), "resolution_rate should be numeric"
        assert 0 <= data["resolution_rate"] <= 100, "resolution_rate should be 0-100"
    
    def test_dashboard_stats_has_active_leads(self, authenticated_headers):
        """Test active_leads and total_leads fields"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "active_leads" in data, "active_leads field missing"
        assert "total_leads" in data, "total_leads field missing"
        assert isinstance(data["active_leads"], int), "active_leads should be int"
    
    def test_dashboard_stats_has_revenue(self, authenticated_headers):
        """Test revenue field exists and is numeric"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "revenue" in data, "revenue field missing"
        assert isinstance(data["revenue"], (int, float)), "revenue should be numeric"
    
    def test_dashboard_stats_has_plan_info(self, authenticated_headers):
        """Test plan and usage information fields"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "plan" in data, "plan field missing"
        assert "messages_used" in data, "messages_used field missing"
        assert "messages_limit" in data, "messages_limit field missing"
        assert "agents_count" in data, "agents_count field missing"
        assert "agents_limit" in data, "agents_limit field missing"
    
    def test_dashboard_stats_has_messages_by_day(self, authenticated_headers):
        """Test messages_by_day array structure for chart data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "messages_by_day" in data, "messages_by_day field missing"
        assert isinstance(data["messages_by_day"], list), "messages_by_day should be array"
        assert len(data["messages_by_day"]) == 7, "messages_by_day should have 7 days"
        
        # Check structure of each day
        for day_data in data["messages_by_day"]:
            assert "date" in day_data, "Each day should have date field"
            assert "label" in day_data, "Each day should have label field (day abbreviation)"
            assert "count" in day_data, "Each day should have count field"
            assert isinstance(day_data["count"], (int, float)), "count should be numeric"
    
    def test_dashboard_stats_has_recent_conversations(self, authenticated_headers):
        """Test recent_conversations array structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "recent_conversations" in data, "recent_conversations field missing"
        assert isinstance(data["recent_conversations"], list), "recent_conversations should be array"
        
        # Check structure of conversations if any exist
        if len(data["recent_conversations"]) > 0:
            convo = data["recent_conversations"][0]
            assert "id" in convo, "Conversation should have id"
            assert "contact_name" in convo, "Conversation should have contact_name"
            assert "channel_type" in convo, "Conversation should have channel_type"
            assert "status" in convo, "Conversation should have status"
            assert "last_message_at" in convo, "Conversation should have last_message_at"
    
    def test_dashboard_stats_has_agents(self, authenticated_headers):
        """Test agents array structure with performance data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "agents" in data, "agents field missing"
        assert isinstance(data["agents"], list), "agents should be array"
        
        # Check structure of agents if any exist
        if len(data["agents"]) > 0:
            agent = data["agents"][0]
            assert "id" in agent, "Agent should have id"
            assert "name" in agent, "Agent should have name"
            assert "type" in agent, "Agent should have type"
            assert "conversations" in agent, "Agent should have conversations count"
            assert "resolved" in agent, "Agent should have resolved count"
    
    def test_dashboard_stats_has_crm_pipeline(self, authenticated_headers):
        """Test crm_pipeline object with stage counts"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "crm_pipeline" in data, "crm_pipeline field missing"
        assert isinstance(data["crm_pipeline"], dict), "crm_pipeline should be object"
        
        # Check required stages
        pipeline = data["crm_pipeline"]
        assert "new" in pipeline, "Pipeline should have new stage"
        assert "qualified" in pipeline, "Pipeline should have qualified stage"
        assert "proposal" in pipeline, "Pipeline should have proposal stage"
        assert "won" in pipeline, "Pipeline should have won stage"
        
        # All values should be non-negative integers
        for stage, count in pipeline.items():
            assert isinstance(count, int), f"{stage} count should be int"
            assert count >= 0, f"{stage} count should be non-negative"
    
    def test_dashboard_stats_has_channel_stats(self, authenticated_headers):
        """Test channel_stats array structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=authenticated_headers)
        data = response.json()
        assert "channel_stats" in data, "channel_stats field missing"
        assert isinstance(data["channel_stats"], list), "channel_stats should be array"
        
        # Check structure of channel stats if any exist
        if len(data["channel_stats"]) > 0:
            stat = data["channel_stats"][0]
            assert "channel" in stat, "Channel stat should have channel field"
            assert "count" in stat, "Channel stat should have count field"
    
    def test_dashboard_stats_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_returns_200(self):
        """Test health endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_health_returns_ok_status(self):
        """Test health endpoint returns status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok, got {data}"
