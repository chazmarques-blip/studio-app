"""
Iteration 14 - Personal Agent Feature Tests
Tests for:
1. GET /api/agents/marketplace returns 25 agents (22 business + 3 personal)
2. Personal agents have locked=true for free plan users
3. POST /api/agents/deploy with personal agent returns 403 for free plan users
4. Marketplace includes plan info and personal agents section
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPersonalAgentsFeature:
    """Tests for Personal Agent feature - Iteration 14"""

    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token for all tests"""
        if TestPersonalAgentsFeature.auth_token is None:
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "test@agentflow.com",
                "password": "password123"
            })
            if login_response.status_code == 200:
                TestPersonalAgentsFeature.auth_token = login_response.json().get("access_token")
            else:
                pytest.skip("Authentication failed - cannot proceed with tests")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {TestPersonalAgentsFeature.auth_token}"}
    
    def test_marketplace_endpoint_returns_25_agents(self):
        """GET /api/agents/marketplace should return 25 agents (22 business + 3 personal)"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "agents" in data, "Response should contain 'agents' key"
        
        agents = data["agents"]
        assert len(agents) == 25, f"Expected 25 agents, got {len(agents)}"
        
        # Verify we have 3 personal agents
        personal_agents = [a for a in agents if a.get("type") == "personal"]
        assert len(personal_agents) == 3, f"Expected 3 personal agents, got {len(personal_agents)}"
        
        # Verify we have 22 business agents
        business_agents = [a for a in agents if a.get("type") != "personal"]
        assert len(business_agents) == 22, f"Expected 22 business agents, got {len(business_agents)}"

    def test_marketplace_returns_plan_info(self):
        """GET /api/agents/marketplace should return plan info"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        data = response.json()
        assert "plan" in data, "Response should contain 'plan' key"
        assert data["plan"] in ["free", "starter", "pro", "enterprise"], f"Invalid plan: {data['plan']}"

    def test_personal_agents_have_locked_flag(self):
        """Personal agents should have 'locked' flag based on plan"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        data = response.json()
        plan = data.get("plan")
        agents = data.get("agents", [])
        
        personal_agents = [a for a in agents if a.get("type") == "personal"]
        
        for agent in personal_agents:
            assert "locked" in agent, f"Personal agent {agent['name']} should have 'locked' key"
            
            # For free plan, personal agents should be locked
            if plan == "free":
                assert agent["locked"] == True, f"Personal agent {agent['name']} should be locked for free plan"

    def test_personal_agents_names(self):
        """Verify personal agents are Alex, Luna, and Max"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        data = response.json()
        personal_agents = [a for a in data["agents"] if a.get("type") == "personal"]
        
        expected_names = {"Alex", "Luna", "Max"}
        actual_names = {a["name"] for a in personal_agents}
        
        assert expected_names == actual_names, f"Expected {expected_names}, got {actual_names}"

    def test_personal_agents_have_is_personal_flag(self):
        """Personal agents should have is_personal=True"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        personal_agents = [a for a in response.json()["agents"] if a.get("type") == "personal"]
        
        for agent in personal_agents:
            assert agent.get("is_personal") == True, f"Agent {agent['name']} should have is_personal=True"

    def test_personal_agents_require_pro_plan(self):
        """Personal agents should have requires_plan='pro'"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        personal_agents = [a for a in response.json()["agents"] if a.get("type") == "personal"]
        
        for agent in personal_agents:
            assert agent.get("requires_plan") == "pro", f"Agent {agent['name']} should require pro plan"

    def test_deploy_personal_agent_free_plan_returns_403(self):
        """POST /api/agents/deploy with personal agent should return 403 for free plan"""
        # Test deploying Alex (personal agent)
        response = requests.post(
            f"{BASE_URL}/api/agents/deploy",
            headers=self.get_headers(),
            json={
                "template_name": "Alex",
                "tone": "friendly",
                "emoji_level": "low",
                "verbosity_level": "balanced"
            }
        )
        
        # Free plan user should get 403
        assert response.status_code == 403, f"Expected 403 for personal agent deploy on free plan, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        assert "Pro plan" in data["detail"] or "Upgrade" in data["detail"], f"Error should mention Pro plan: {data['detail']}"

    def test_deploy_personal_agent_luna_free_plan_returns_403(self):
        """POST /api/agents/deploy with Luna should return 403 for free plan"""
        response = requests.post(
            f"{BASE_URL}/api/agents/deploy",
            headers=self.get_headers(),
            json={
                "template_name": "Luna",
                "tone": "friendly",
                "emoji_level": "low",
                "verbosity_level": "balanced"
            }
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}. Response: {response.text}"

    def test_deploy_personal_agent_max_free_plan_returns_403(self):
        """POST /api/agents/deploy with Max should return 403 for free plan"""
        response = requests.post(
            f"{BASE_URL}/api/agents/deploy",
            headers=self.get_headers(),
            json={
                "template_name": "Max",
                "tone": "friendly",
                "emoji_level": "low",
                "verbosity_level": "balanced"
            }
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}. Response: {response.text}"

    def test_business_agents_not_locked(self):
        """Business agents should not have locked flag or have locked=False"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        business_agents = [a for a in response.json()["agents"] if a.get("type") != "personal"]
        
        # Business agents should not be locked
        for agent in business_agents:
            if "locked" in agent:
                assert agent["locked"] == False, f"Business agent {agent['name']} should not be locked"

    def test_personal_agent_description_format(self):
        """Verify personal agents have proper descriptions"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        personal_agents = [a for a in response.json()["agents"] if a.get("type") == "personal"]
        
        for agent in personal_agents:
            assert "description" in agent, f"Agent {agent['name']} should have description"
            assert len(agent["description"]) > 20, f"Agent {agent['name']} description too short"

    def test_marketplace_unauthenticated_returns_401(self):
        """GET /api/agents/marketplace without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"

    def test_agent_type_descriptions_includes_personal(self):
        """Verify personal type is properly defined"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        # Find personal agents and verify they have proper category
        personal_agents = [a for a in response.json()["agents"] if a.get("type") == "personal"]
        
        categories = {a.get("category") for a in personal_agents}
        expected_categories = {"productivity", "wellness", "finance"}
        
        assert categories == expected_categories, f"Expected categories {expected_categories}, got {categories}"


class TestBusinessAgentsDeployment:
    """Test that business agents can still be deployed normally"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        if TestBusinessAgentsDeployment.auth_token is None:
            login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "test@agentflow.com",
                "password": "password123"
            })
            if login_response.status_code == 200:
                TestBusinessAgentsDeployment.auth_token = login_response.json().get("access_token")
            else:
                pytest.skip("Authentication failed")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {TestBusinessAgentsDeployment.auth_token}"}

    def test_business_agent_carol_accessible(self):
        """Business agent Carol should be in marketplace"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace", headers=self.get_headers())
        
        assert response.status_code == 200
        
        agents = response.json()["agents"]
        carol = next((a for a in agents if a["name"] == "Carol"), None)
        
        assert carol is not None, "Carol should be in marketplace"
        assert carol.get("type") == "sales", "Carol should be a sales agent"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
