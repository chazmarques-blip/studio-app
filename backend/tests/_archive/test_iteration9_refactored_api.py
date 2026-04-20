"""
Iteration 9: Test backend after monolithic server.py refactored to modular routers
All API endpoints should behave exactly the same as before.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoint:
    """Test health endpoint returns correct version 0.4.0"""
    
    def test_health_returns_ok_with_version(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.4.0"
        assert data["service"] == "agentzz-api"
        assert data["database"] == "supabase"


class TestAuthEndpoints:
    """Test auth router endpoints"""
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with test credentials returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@agentflow.com"
        assert len(data["access_token"]) > 0
    
    def test_login_with_invalid_credentials(self):
        """POST /api/auth/login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_get_me_returns_user_data(self):
        """GET /api/auth/me returns user data with authorization header"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Get user profile
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == "test@agentflow.com"
    
    def test_get_me_without_auth_returns_401(self):
        """GET /api/auth/me without authorization returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_update_profile(self):
        """PUT /api/auth/profile updates user profile"""
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Update profile
        update_resp = requests.put(f"{BASE_URL}/api/auth/profile", headers=headers, json={
            "full_name": "Test User Updated"
        })
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["status"] == "ok"


class TestAgentsEndpoints:
    """Test agents router endpoints"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_marketplace_returns_22_agents(self):
        """GET /api/agents/marketplace returns 22 agents"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 22
        
        # Verify each agent has required fields
        for agent in data["agents"]:
            assert "name" in agent
            assert "type" in agent
            assert "description" in agent
            assert "system_prompt" in agent
    
    def test_get_user_agents(self):
        """GET /api/agents returns user's agents list"""
        response = requests.get(f"{BASE_URL}/api/agents", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        # Should be a list (can be empty)
        assert isinstance(data["agents"], list)


class TestDashboardEndpoints:
    """Test dashboard router endpoints"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_dashboard_stats(self):
        """GET /api/dashboard/stats returns dashboard metrics"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Should have basic stats structure
        assert "messages_today" in data or "plan" in data


class TestLeadsEndpoints:
    """Test leads router endpoints"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_leads(self):
        """GET /api/leads returns leads list"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert isinstance(data["leads"], list)


class TestConversationsEndpoints:
    """Test conversations router endpoints"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_conversations(self):
        """GET /api/conversations returns conversations list"""
        response = requests.get(f"{BASE_URL}/api/conversations", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)


class TestChannelsEndpoints:
    """Test channels router endpoints"""
    
    @pytest.fixture(autouse=True)
    def auth_token(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        self.token = login_resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_channels(self):
        """GET /api/channels returns channels list"""
        response = requests.get(f"{BASE_URL}/api/channels", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
