"""
AgentFlow API Backend Tests - Supabase Migration
Tests for authentication, agents, tenants, and dashboard endpoints after MongoDB to Supabase migration
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials - existing test user
TEST_USER_EMAIL = "test@agentflow.com"
TEST_USER_PASSWORD = "password123"


class TestHealthEndpoint:
    """Health check endpoint - verifies Supabase database connection"""
    
    def test_health_check_returns_supabase(self):
        """Test health endpoint returns database: supabase"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "agentflow-api"
        assert data["database"] == "supabase", f"Expected database=supabase, got {data.get('database')}"
        print(f"Health check passed - database: {data['database']}")


class TestAuthEndpoints:
    """Authentication endpoint tests with Supabase"""
    
    def test_signup_creates_user_in_supabase(self):
        """Test user signup creates user in Supabase"""
        unique_email = f"test_new_{int(time.time())}_{uuid.uuid4().hex[:6]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "TestPass123!",
            "full_name": "Test New User"
        })
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == unique_email
        assert data["user"]["full_name"] == "Test New User"
        assert data["user"]["onboarding_completed"] == False
        assert "id" in data["user"]
        print(f"Signup success - user created in Supabase: {unique_email}")
    
    def test_signup_duplicate_email_rejected(self):
        """Test signup with duplicate email (test@agentflow.com already exists)"""
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": TEST_USER_EMAIL,
            "password": "AnotherPass123!",
            "full_name": "Duplicate User"
        })
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data.get("detail", "").lower()
        print("Duplicate email correctly rejected")
    
    def test_login_returns_jwt_token(self):
        """Test login with test@agentflow.com returns JWT token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        # Verify JWT structure (header.payload.signature)
        token_parts = data["access_token"].split(".")
        assert len(token_parts) == 3, "Token should have 3 parts (JWT format)"
        print(f"Login success - JWT token returned for: {TEST_USER_EMAIL}")
    
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
    
    def test_get_me_returns_user_profile(self):
        """Test GET /api/auth/me returns user profile"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Get profile
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        assert "id" in data
        assert "full_name" in data
        assert "ui_language" in data
        assert "created_at" in data
        print(f"Get me success: {data.get('email')}, id: {data.get('id')}")
    
    def test_get_me_without_token_fails(self):
        """Test /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Missing token correctly rejected")
    
    def test_profile_update(self):
        """Test PUT /api/auth/profile updates user data"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        # Update profile - only use valid columns that exist in Supabase users table
        response = requests.put(f"{BASE_URL}/api/auth/profile", 
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Test User"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "updated" in data
        print(f"Profile update success: {data.get('updated')}")


class TestTenantsEndpoints:
    """Tenant CRUD tests with Supabase"""
    
    def test_create_tenant(self):
        """Test POST /api/tenants creates tenant"""
        # Create new user for clean slate
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
        unique_email = f"tenant_test_{unique_id}@test.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "TestPass123!",
            "full_name": "Tenant Test User"
        })
        assert signup_resp.status_code == 200
        token = signup_resp.json()["access_token"]
        
        # Create tenant with unique name/slug
        tenant_name = f"Test Company {unique_id}"
        response = requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": tenant_name}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == tenant_name
        assert data["plan"] == "free"
        assert "limits" in data
        assert data["limits"]["agents"] == 1  # Free plan limit
        print(f"Tenant created: {data.get('name')}, plan: {data.get('plan')}")
    
    def test_get_tenant_returns_tenant(self):
        """Test GET /api/tenants returns tenant"""
        # Login with test user who already has tenant
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/tenants", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "plan" in data
        print(f"Get tenant success: {data.get('name')}")


class TestMarketplaceAgents:
    """Marketplace agents endpoint - should return 22 agents after migration"""
    
    def test_marketplace_returns_22_agents(self):
        """Test GET /api/agents/marketplace returns 22 agents"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        agent_count = len(data["agents"])
        assert agent_count == 22, f"Expected 22 agents, got {agent_count}"
        
        # Verify some agent names exist
        agent_names = [a["name"] for a in data["agents"]]
        assert "Carol" in agent_names
        assert "Roberto" in agent_names
        assert "Sofia" in agent_names  # E-commerce agent
        assert "Valentina" in agent_names  # Travel agent
        
        # Verify agent structure
        first_agent = data["agents"][0]
        assert "name" in first_agent
        assert "type" in first_agent
        assert "category" in first_agent
        assert "description" in first_agent
        assert "rating" in first_agent
        
        print(f"Marketplace agents: {agent_count} agents returned")
        print(f"Sample agents: {agent_names[:5]}")


class TestUserAgents:
    """User agent CRUD tests with Supabase"""
    
    def test_get_agents_returns_user_agents(self):
        """Test GET /api/agents returns user agents"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_resp.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/agents", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
        print(f"User agents count: {len(data['agents'])}")
    
    def test_get_agents_without_auth_fails(self):
        """Test get agents without auth fails"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 401
        print("Get agents without auth correctly rejected")
    
    def test_create_agent_with_tenant(self):
        """Test POST /api/agents creates agent (requires tenant)"""
        # Create new user
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
        unique_email = f"agent_test_{unique_id}@test.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "TestPass123!",
            "full_name": "Agent Test User"
        })
        token = signup_resp.json()["access_token"]
        
        # Create tenant first (required)
        tenant_resp = requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"Agent Test Company {unique_id}"}
        )
        assert tenant_resp.status_code == 200, f"Tenant creation failed: {tenant_resp.text}"
        
        # Create agent
        response = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "My Test Sales Agent",
                "type": "sales",
                "description": "A test sales agent"
            }
        )
        assert response.status_code == 200, f"Agent creation failed: {response.text}"
        data = response.json()
        assert data["name"] == "My Test Sales Agent"
        assert data["type"] == "sales"
        assert "id" in data
        assert data["status"] == "active"
        print(f"Agent created: {data.get('name')}, id: {data.get('id')}")
    
    def test_create_agent_without_tenant_fails(self):
        """Test creating agent without tenant fails"""
        # Create new user (no tenant yet)
        unique_email = f"no_tenant_{int(time.time())}_{uuid.uuid4().hex[:6]}@test.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "TestPass123!",
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
    
    def test_free_plan_agent_limit_enforced(self):
        """Test free plan allows only 1 agent"""
        # Create new user
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
        unique_email = f"limit_test_{unique_id}@test.com"
        signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "password": "TestPass123!",
            "full_name": "Limit Test User"
        })
        token = signup_resp.json()["access_token"]
        
        # Create tenant with unique slug
        tenant_resp = requests.post(f"{BASE_URL}/api/tenants", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": f"Limit Test Company {unique_id}"}
        )
        assert tenant_resp.status_code == 200, f"Tenant creation failed: {tenant_resp.text}"
        
        # Create first agent - should succeed
        resp1 = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Agent One", "type": "sales"}
        )
        assert resp1.status_code == 200, f"First agent creation failed: {resp1.text}"
        
        # Create second agent - should fail due to free plan limit
        resp2 = requests.post(f"{BASE_URL}/api/agents", 
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Agent Two", "type": "support"}
        )
        assert resp2.status_code == 403
        assert "free plan" in resp2.json().get("detail", "").lower()
        print("Free plan agent limit (1 agent) enforced correctly")


class TestDashboardStats:
    """Dashboard stats endpoint tests"""
    
    def test_get_dashboard_stats(self):
        """Test GET /api/dashboard/stats returns stats"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
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
        assert "agents_count" in data
        assert "agents_limit" in data
        print(f"Dashboard stats: plan={data.get('plan')}, agents={data.get('agents_count')}/{data.get('agents_limit')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
