"""
Iteration 8 Backend Tests: Marketplace Agents (22 agents with detailed prompts) and Route-Agent Endpoint
Tests:
1. GET /api/agents/marketplace - returns 22 agents with system_prompt > 400 chars each
2. POST /api/conversations/{id}/route-agent - endpoint exists, returns proper error for invalid conversation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestMarketplaceAgents:
    """Test marketplace agents with detailed prompts"""

    def test_marketplace_returns_22_agents(self):
        """Verify marketplace returns exactly 22 agents"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "agents" in data, "Response should contain 'agents' key"
        
        agents = data["agents"]
        assert len(agents) == 22, f"Expected 22 agents, got {len(agents)}"
        print(f"PASS: Marketplace returns {len(agents)} agents")

    def test_all_agents_have_detailed_prompts(self):
        """Verify all agents have system_prompt > 400 chars"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        assert response.status_code == 200
        
        agents = response.json()["agents"]
        
        agents_with_short_prompts = []
        for agent in agents:
            name = agent.get("name", "Unknown")
            prompt = agent.get("system_prompt", "")
            prompt_len = len(prompt)
            
            if prompt_len < 400:
                agents_with_short_prompts.append(f"{name}: {prompt_len} chars")
            else:
                print(f"PASS: {name} has {prompt_len} chars in system_prompt")
        
        assert len(agents_with_short_prompts) == 0, f"Agents with prompts < 400 chars: {agents_with_short_prompts}"
        print(f"PASS: All 22 agents have system_prompt > 400 chars")

    def test_agents_have_required_fields(self):
        """Verify agents have all required fields"""
        response = requests.get(f"{BASE_URL}/api/agents/marketplace")
        assert response.status_code == 200
        
        agents = response.json()["agents"]
        required_fields = ["name", "type", "description", "system_prompt", "category"]
        
        for agent in agents:
            for field in required_fields:
                assert field in agent, f"Agent {agent.get('name', 'Unknown')} missing field: {field}"
        
        print(f"PASS: All agents have required fields")


class TestRouteAgentEndpoint:
    """Test route-agent endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")

    def test_route_agent_requires_auth(self):
        """Route-agent endpoint should require authentication"""
        fake_convo_id = "non-existent-id"
        response = requests.post(f"{BASE_URL}/api/conversations/{fake_convo_id}/route-agent")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("PASS: Route-agent requires authentication")

    def test_route_agent_invalid_conversation(self, auth_token):
        """Route-agent should return 404 for non-existent conversation"""
        fake_convo_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/conversations/{fake_convo_id}/route-agent",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404, f"Expected 404 for invalid convo, got {response.status_code}"
        print("PASS: Route-agent returns 404 for invalid conversation")


class TestHealthAndBasicEndpoints:
    """Basic health and endpoint availability tests"""

    def test_health_endpoint(self):
        """Health endpoint works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("service") == "agentzz-api"
        print("PASS: Health endpoint returns service='agentzz-api'")

    def test_login_works(self):
        """Login with test credentials works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("email") == TEST_EMAIL
        print("PASS: Login works with test credentials")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
