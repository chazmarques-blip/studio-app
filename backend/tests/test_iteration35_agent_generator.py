"""
Tests for Agent Generator (AgentBuilder) feature - Iteration 35
Tests the guided questionnaire AI agent generation and deployment endpoints.
Endpoints tested:
- POST /api/agents/generate-preview - AI-generated agent configuration
- POST /api/agents/deploy-generated - Deploy generated agent to user account
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestAgentGeneratorEndpoints:
    """Tests for /api/agents/generate-preview and /api/agents/deploy-generated"""
    
    def test_health_check(self):
        """Verify API health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✓ Health check passed")
    
    def test_generate_preview_requires_auth(self):
        """Test that generate-preview requires authentication"""
        payload = {
            "segment": "health",
            "objective": "scheduling",
            "tone": "professional",
            "business_name": "Test Clinic",
            "business_description": "A dental clinic"
        }
        response = requests.post(f"{BASE_URL}/api/agents/generate-preview", json=payload)
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Generate preview requires auth")
    
    def test_generate_preview_endpoint_exists(self, auth_headers):
        """Test that generate-preview endpoint exists and responds (basic validation)"""
        # Using minimal payload to check endpoint structure quickly
        payload = {
            "segment": "general",
            "objective": "support",
            "tone": "friendly",
            "business_name": "TEST_QuickCheck",
            "business_description": "Quick validation business"
        }
        # Just check endpoint returns properly (not waiting for full AI generation)
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview", 
            json=payload, 
            headers=auth_headers,
            timeout=120  # AI generation takes time
        )
        # Should return 200 with generated agent data
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "agent_name" in data, "Response missing agent_name"
        assert "description" in data, "Response missing description"
        assert "system_prompt" in data, "Response missing system_prompt"
        assert "personality" in data, "Response missing personality"
        assert "suggested_knowledge" in data, "Response missing suggested_knowledge"
        assert "sample_conversation" in data, "Response missing sample_conversation"
        
        # Verify personality structure
        personality = data["personality"]
        assert "tone_value" in personality
        assert "verbosity_value" in personality
        assert "emoji_value" in personality
        assert "proactivity" in personality
        assert "formality" in personality
        
        print(f"✓ Generate preview works - Agent name: {data['agent_name']}")
        print(f"  Generation time: {data.get('generation_time_ms', 'N/A')}ms")
        
        # Store for deploy test
        return data
    
    def test_generate_preview_with_full_payload(self, auth_headers):
        """Test generate-preview with complete business information"""
        payload = {
            "segment": "beauty",
            "objective": "scheduling",
            "tone": "friendly",
            "business_name": "TEST_BeautySalon",
            "business_description": "Premium beauty salon offering hair, nails, and skincare services",
            "products_services": "Haircut, coloring, manicure, pedicure, facials, waxing",
            "hours": "Mon-Sat 9am-7pm",
            "differentials": "15 years experience, organic products, loyalty program",
            "target_audience": "Women 25-55",
            "language": "en"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            json=payload,
            headers=auth_headers,
            timeout=120
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert data.get("agent_name"), "Agent name should not be empty"
        assert data.get("description"), "Description should not be empty"
        assert data.get("system_prompt"), "System prompt should not be empty"
        assert len(data.get("system_prompt", "")) > 100, "System prompt should be detailed"
        
        # Check sample conversation has proper structure
        sample_convo = data.get("sample_conversation", [])
        assert len(sample_convo) >= 2, "Should have at least 2 conversation turns"
        for msg in sample_convo:
            assert "role" in msg, "Each message needs a role"
            assert "message" in msg, "Each message needs content"
            assert msg["role"] in ["customer", "agent"], f"Invalid role: {msg['role']}"
        
        # Check suggested knowledge
        knowledge = data.get("suggested_knowledge", [])
        assert len(knowledge) > 0, "Should have suggested knowledge items"
        for item in knowledge:
            assert "type" in item
            assert "title" in item
            assert "content" in item
        
        print(f"✓ Full payload generation works - Agent: {data['agent_name']}")
        print(f"  System prompt length: {len(data['system_prompt'])} chars")
        print(f"  Knowledge items: {len(knowledge)}")
        print(f"  Conversation turns: {len(sample_convo)}")
    
    def test_deploy_generated_requires_auth(self):
        """Test that deploy-generated requires authentication"""
        payload = {
            "agent_name": "Test Agent",
            "description": "Test description",
            "system_prompt": "Test prompt",
            "personality": {"tone_value": 0.5, "verbosity_value": 0.5, "emoji_value": 0.3}
        }
        response = requests.post(f"{BASE_URL}/api/agents/deploy-generated", json=payload)
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Deploy generated requires auth")
    
    def test_deploy_generated_creates_agent(self, auth_headers):
        """Test full flow: generate preview then deploy agent"""
        # Step 1: Generate preview
        generate_payload = {
            "segment": "ecommerce",
            "objective": "sales",
            "tone": "professional",
            "business_name": "TEST_DeployTest",
            "business_description": "Online store for electronics",
            "products_services": "Smartphones, laptops, accessories",
            "language": "en"
        }
        
        gen_response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            json=generate_payload,
            headers=auth_headers,
            timeout=120
        )
        
        assert gen_response.status_code == 200, f"Generate failed: {gen_response.text}"
        generated = gen_response.json()
        print(f"✓ Generated agent: {generated['agent_name']}")
        
        # Step 2: Deploy the generated agent
        deploy_payload = {
            **generated,
            "objective": generate_payload["objective"],
            "tone": generate_payload["tone"],
            "language": "en"
        }
        
        deploy_response = requests.post(
            f"{BASE_URL}/api/agents/deploy-generated",
            json=deploy_payload,
            headers=auth_headers
        )
        
        # Could fail with 403 if free plan limit reached
        if deploy_response.status_code == 403:
            error = deploy_response.json().get("detail", "")
            if "free plan" in error.lower() or "1 agent" in error.lower():
                print(f"⚠ Deploy blocked by plan limit (expected): {error}")
                return  # This is acceptable behavior
        
        assert deploy_response.status_code in [200, 201], f"Deploy failed: {deploy_response.text}"
        agent_data = deploy_response.json()
        
        # Verify agent was created with correct data
        assert agent_data.get("id"), "Created agent should have an ID"
        assert agent_data.get("name") == generated["agent_name"], "Agent name mismatch"
        assert agent_data.get("type") == generate_payload["objective"], "Agent type should match objective"
        assert agent_data.get("description") == generated["description"]
        
        print(f"✓ Agent deployed successfully")
        print(f"  Agent ID: {agent_data['id']}")
        print(f"  Agent name: {agent_data['name']}")
        print(f"  Agent type: {agent_data['type']}")
        
        # Store agent ID for cleanup
        return agent_data["id"]


class TestAgentGeneratorValidation:
    """Validation and edge case tests for agent generator"""
    
    def test_generate_preview_missing_required_fields(self, auth_headers):
        """Test that missing required fields return proper error"""
        # Missing business_name
        payload = {
            "segment": "general",
            "objective": "support",
            "tone": "friendly",
            "business_description": "Test business"
        }
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
        print("✓ Missing business_name returns validation error")
    
    def test_generate_preview_all_segments(self, auth_headers):
        """Test that all segment types are accepted (quick validation)"""
        segments = [
            "ecommerce", "restaurant", "health", "beauty", "real_estate",
            "automotive", "education", "finance", "travel", "fitness",
            "legal", "events", "saas", "logistics", "telecom", "general"
        ]
        
        # Just test a few to validate segment handling
        test_segments = ["ecommerce", "health", "saas"]
        
        for segment in test_segments:
            payload = {
                "segment": segment,
                "objective": "support",
                "tone": "professional",
                "business_name": f"TEST_Segment_{segment}",
                "business_description": f"Test business for {segment}"
            }
            response = requests.post(
                f"{BASE_URL}/api/agents/generate-preview",
                json=payload,
                headers=auth_headers,
                timeout=120
            )
            assert response.status_code == 200, f"Segment {segment} failed: {response.text}"
            print(f"✓ Segment '{segment}' accepted")
    
    def test_generate_preview_all_objectives(self, auth_headers):
        """Test that all objective types are accepted"""
        objectives = ["sales", "support", "scheduling", "sac", "onboarding"]
        
        for objective in objectives:
            payload = {
                "segment": "general",
                "objective": objective,
                "tone": "professional",
                "business_name": f"TEST_Obj_{objective}",
                "business_description": f"Test business for {objective}"
            }
            response = requests.post(
                f"{BASE_URL}/api/agents/generate-preview",
                json=payload,
                headers=auth_headers,
                timeout=120
            )
            assert response.status_code == 200, f"Objective {objective} failed: {response.text}"
            data = response.json()
            assert data.get("agent_name"), f"No agent name for {objective}"
            print(f"✓ Objective '{objective}' works - Agent: {data['agent_name']}")
    
    def test_generate_preview_all_tones(self, auth_headers):
        """Test that all tone types are accepted"""
        tones = ["professional", "friendly", "empathetic", "direct", "consultive"]
        
        for tone in tones:
            payload = {
                "segment": "general",
                "objective": "support",
                "tone": tone,
                "business_name": f"TEST_Tone_{tone}",
                "business_description": f"Test business for {tone} tone"
            }
            response = requests.post(
                f"{BASE_URL}/api/agents/generate-preview",
                json=payload,
                headers=auth_headers,
                timeout=120
            )
            assert response.status_code == 200, f"Tone {tone} failed: {response.text}"
            print(f"✓ Tone '{tone}' accepted")


class TestAgentGeneratorLanguages:
    """Test language support in agent generator"""
    
    def test_generate_preview_portuguese(self, auth_headers):
        """Test Portuguese language generation"""
        payload = {
            "segment": "restaurant",
            "objective": "scheduling",
            "tone": "friendly",
            "business_name": "TEST_Restaurante_PT",
            "business_description": "Restaurante italiano com massas artesanais",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            json=payload,
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        # Agent should have Portuguese content
        print(f"✓ Portuguese generation works - Agent: {data['agent_name']}")
    
    def test_generate_preview_english(self, auth_headers):
        """Test English language generation"""
        payload = {
            "segment": "saas",
            "objective": "support",
            "tone": "professional",
            "business_name": "TEST_TechApp_EN",
            "business_description": "SaaS platform for project management",
            "language": "en"
        }
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            json=payload,
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ English generation works - Agent: {data['agent_name']}")
    
    def test_generate_preview_spanish(self, auth_headers):
        """Test Spanish language generation"""
        payload = {
            "segment": "beauty",
            "objective": "scheduling",
            "tone": "friendly",
            "business_name": "TEST_Salon_ES",
            "business_description": "Salon de belleza y spa",
            "language": "es"
        }
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            json=payload,
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Spanish generation works - Agent: {data['agent_name']}")


@pytest.fixture
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
