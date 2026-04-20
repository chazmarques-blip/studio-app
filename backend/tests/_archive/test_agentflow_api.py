"""
AgentFlow API Backend Tests
Tests for authentication, agents, and tenant endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials - use unique email to avoid conflicts
TEST_USER_EMAIL = f"test_{uuid.uuid4().hex[:8]}@agentflow.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_FULLNAME = "Test User"

# Demo user credentials (pre-existing)
DEMO_USER_EMAIL = "demo@agentflow.com"
DEMO_USER_PASSWORD = "Demo123!"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_check(self):
        """Test health endpoint returns OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "agentflow-api"
        print(f"Health check passed: {data}")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_signup_success(self):
        """Test successful user signup"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@agentflow.com"
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_FULLNAME
        })
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == unique_email
        assert data["user"]["full_name"] == TEST_USER_FULLNAME
        assert data["user"]["onboarding_completed"] == False
        print(f"Signup success for: {unique_email}")
    
    def test_signup_duplicate_email(self):
        """Test signup with duplicate email fails"""
        # First signup
        unique_email = f"test_{uuid.uuid4().hex[:8]}@agentflow.com"
        requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_FULLNAME
        })
        # Second signup with same email
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "AnotherPass123!",
            "full_name": "Another User"
        })
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data.get("detail", "").lower()
        print("Duplicate email correctly rejected")
    
    def test_login_success(self):
        """Test login with demo user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == DEMO_USER_EMAIL
        print(f"Login success for: {DEMO_USER_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data.get("detail", "").lower()
        print("Invalid credentials correctly rejected")
    
    def test_get_me_with_valid_token(self):
        """Test /auth/me with valid token"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Get profile
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == DEMO_USER_EMAIL
        print(f"Get me success: {data.get('email')}")
    
    def test_get_me_without_token(self):
        """Test /auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Missing token correctly rejected")
    
    def test_profile_update(self):
        """Test profile update"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        # Update profile
        response = requests.put(f"{BASE_URL}/api/auth/profile", 
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Demo User Updated"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("Profile update success")


class TestAgentsEndpoints:
    """Agents marketplace and CRUD tests"""
    
    def test_get_marketplace_agents(self):
        """Test marketplace returns 5 agents"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 5
        agent_names = [a["name"] for a in data["agents"]]
        assert "Carol" in agent_names
        assert "Roberto" in agent_names
        assert "Ana" in agent_names
        assert "Lucas" in agent_names
        assert "Marina" in agent_names
        print(f"Marketplace agents: {agent_names}")
    
    def test_get_agents_authenticated(self):
        """Test get agents requires auth"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/agents", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"User agents count: {len(data['agents'])}")
    
    def test_get_agents_without_auth(self):
        """Test get agents without auth fails"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 401
        print("Get agents without auth correctly rejected")


class TestTenantsEndpoints:
    """Tenant CRUD tests"""
    
    def test_create_tenant(self):
        """Test creating tenant"""
        # Create new user for clean slate
        unique_email = f"tenant_test_{uuid.uuid4().hex[:8]}@agentflow.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": "Tenant Test User"
        })
        assert signup_resp.status_code == 200
        token = signup_resp.json()["access_token"]
        
        # Create tenant
        response = requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Company"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Company"
        assert data["plan"] == "free"
        print(f"Tenant created: {data.get('name')}")
    
    def test_create_tenant_returns_existing(self):
        """Test creating tenant twice returns existing"""
        # Create new user
        unique_email = f"tenant_dup_{uuid.uuid4().hex[:8]}@agentflow.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": "Dup Tenant User"
        })
        token = signup_resp.json()["access_token"]
        
        # Create first tenant
        resp1 = requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Company One"}
        )
        assert resp1.status_code == 200
        tenant1_id = resp1.json()["id"]
        
        # Try creating second tenant - should return existing
        resp2 = requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Company Two"}
        )
        assert resp2.status_code == 200
        tenant2_id = resp2.json()["id"]
        assert tenant1_id == tenant2_id
        print("Duplicate tenant creation returns existing correctly")


class TestAgentCreationAndLimits:
    """Test agent creation with free plan limits"""
    
    def test_create_agent_requires_tenant(self):
        """Test creating agent without tenant fails"""
        # Create new user (no tenant yet)
        unique_email = f"no_tenant_{uuid.uuid4().hex[:8]}@agentflow.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": "No Tenant User"
        })
        token = signup_resp.json()["access_token"]
        
        # Try to create agent without tenant
        response = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Agent", "type": "custom"}
        )
        assert response.status_code == 400
        assert "tenant" in response.json().get("detail", "").lower()
        print("Agent creation without tenant correctly rejected")
    
    def test_create_agent_success(self):
        """Test creating agent with tenant"""
        # Create new user
        unique_email = f"agent_test_{uuid.uuid4().hex[:8]}@agentflow.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": "Agent Test User"
        })
        token = signup_resp.json()["access_token"]
        
        # Create tenant first
        requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Agent Test Company"}
        )
        
        # Create agent
        response = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "My Test Agent",
                "type": "sales",
                "description": "A test sales agent"
            }
        )
        assert response.status_code == 200, f"Agent creation failed: {response.text}"
        data = response.json()
        assert data["name"] == "My Test Agent"
        assert data["type"] == "sales"
        assert "id" in data
        print(f"Agent created: {data.get('name')}")
        return token, data["id"]
    
    def test_free_plan_agent_limit(self):
        """Test free plan allows only 1 agent"""
        # Create new user
        unique_email = f"limit_test_{uuid.uuid4().hex[:8]}@agentflow.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "full_name": "Limit Test User"
        })
        token = signup_resp.json()["access_token"]
        
        # Create tenant
        requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Limit Test Company"}
        )
        
        # Create first agent - should succeed
        resp1 = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Agent One", "type": "sales"}
        )
        assert resp1.status_code == 200
        
        # Create second agent - should fail due to free plan limit
        resp2 = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Agent Two", "type": "support"}
        )
        assert resp2.status_code == 403
        assert "free plan" in resp2.json().get("detail", "").lower()
        print("Free plan agent limit enforced correctly")


class TestDashboardStats:
    """Dashboard stats endpoint tests"""
    
    def test_get_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        # Login with demo user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "messages_today" in data
        assert "plan" in data
        assert "messages_limit" in data
        print(f"Dashboard stats: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
