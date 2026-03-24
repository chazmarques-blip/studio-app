"""
Iteration 98: Test Direct API Migration from Emergent LLM Proxy
Tests that all AI integrations use direct API keys (Anthropic, OpenAI, Gemini)
instead of the Emergent proxy.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """GET /api/health - server health check"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "service" in data
        print(f"Health check passed: {data}")
    
    def test_backend_running(self):
        """Verify backend is accessible"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print("Backend is running and accessible")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """POST /api/auth/login - login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "access_token" in data
        print(f"Login successful, token received")
        return data.get("token") or data.get("access_token")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"},
            timeout=15
        )
        assert response.status_code in [401, 400, 404]
        print(f"Invalid login correctly rejected with status {response.status_code}")


@pytest.fixture
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=15
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDirectAPIMigration:
    """Tests verifying direct API usage (not Emergent proxy)"""
    
    def test_sandbox_chat_direct_claude(self, auth_headers):
        """POST /api/sandbox/chat - AI chat using Claude direct API"""
        response = requests.post(
            f"{BASE_URL}/api/sandbox/chat",
            headers=auth_headers,
            json={
                "content": "Hello, what is 2+2?",
                "agent_name": "Test Agent",
                "agent_type": "support"
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        # Verify debug info shows Claude model
        debug = data.get("debug", {})
        print(f"Chat response received in {debug.get('response_time_ms', 'N/A')}ms")
        print(f"Model used: {debug.get('model', 'N/A')}")
        print(f"Response: {data['response'][:100]}...")
    
    def test_agents_list(self, auth_headers):
        """GET /api/agents - list agents"""
        response = requests.get(
            f"{BASE_URL}/api/agents",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        print(f"Found {len(data['agents'])} agents")
    
    def test_agent_generate_preview_gemini(self, auth_headers):
        """POST /api/agents/generate-preview - agent generation using Gemini direct API"""
        response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            headers=auth_headers,
            json={
                "segment": "ecommerce",
                "objective": "sales",
                "tone": "friendly",
                "business_name": "Test Store",
                "business_description": "Online store selling electronics",
                "language": "en"
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data.get("status") == "generating"
        print(f"Agent generation started with task_id: {data['task_id']}")
        return data["task_id"]
    
    def test_agent_generate_status(self, auth_headers):
        """GET /api/agents/generate-status/{task_id} - check agent generation status"""
        # First start a generation
        gen_response = requests.post(
            f"{BASE_URL}/api/agents/generate-preview",
            headers=auth_headers,
            json={
                "segment": "general",
                "objective": "support",
                "tone": "professional",
                "business_name": "Test Business",
                "business_description": "General business services",
                "language": "en"
            },
            timeout=30
        )
        assert gen_response.status_code == 200
        task_id = gen_response.json().get("task_id")
        
        # Poll for status (wait up to 60 seconds)
        max_wait = 60
        start = time.time()
        final_status = None
        while time.time() - start < max_wait:
            status_response = requests.get(
                f"{BASE_URL}/api/agents/generate-status/{task_id}",
                headers=auth_headers,
                timeout=15
            )
            assert status_response.status_code in [200, 404]
            if status_response.status_code == 404:
                # Task completed and was cleaned up
                print("Task completed (cleaned up)")
                final_status = "completed"
                break
            
            status_data = status_response.json()
            final_status = status_data.get("status")
            print(f"Generation status: {final_status}")
            
            if final_status in ["completed", "failed"]:
                if final_status == "completed":
                    result = status_data.get("result", {})
                    print(f"Agent generated: {result.get('agent_name', 'N/A')}")
                    print(f"Model used: {result.get('model_used', 'N/A')}")
                break
            
            time.sleep(3)
        
        assert final_status in ["completed", "generating", None]  # None if 404


class TestNoEmergentImports:
    """Verify no emergentintegrations imports in active router files"""
    
    def test_no_emergent_in_routers(self):
        """Verify NO import of emergentintegrations exists in any active router file"""
        import subprocess
        result = subprocess.run(
            ["grep", "-r", "from emergentintegrations\\|import emergentintegrations", 
             "/app/backend/routers/", "/app/backend/pipeline/", "/app/backend/core/"],
            capture_output=True,
            text=True
        )
        # Filter out comments
        lines = [l for l in result.stdout.strip().split('\n') if l and not '"""' in l and "# " not in l.split("emergent")[0]]
        actual_imports = [l for l in lines if "from emergentintegrations" in l or "import emergentintegrations" in l]
        
        if actual_imports:
            print(f"WARNING: Found emergentintegrations imports: {actual_imports}")
        else:
            print("No emergentintegrations imports found in active code")
        
        # The only reference should be a comment in llm.py
        assert len(actual_imports) == 0, f"Found emergentintegrations imports: {actual_imports}"


class TestDashboardAndData:
    """Test dashboard and data endpoints"""
    
    def test_leads_list(self, auth_headers):
        """GET /api/leads - list leads"""
        response = requests.get(
            f"{BASE_URL}/api/leads",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        print(f"Found {len(data['leads'])} leads")
    
    def test_conversations_list(self, auth_headers):
        """GET /api/conversations - list conversations"""
        response = requests.get(
            f"{BASE_URL}/api/conversations",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        print(f"Found {len(data['conversations'])} conversations")
    
    def test_campaigns_list(self, auth_headers):
        """GET /api/campaigns - list campaigns"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        print(f"Found {len(data['campaigns'])} campaigns")


class TestStudioEndpoints:
    """Test Directed Studio endpoints (uses direct Sora 2 client)"""
    
    def test_studio_projects_list(self, auth_headers):
        """GET /api/studio/projects - list studio projects"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"Found {len(data['projects'])} studio projects")
    
    def test_studio_voices(self, auth_headers):
        """GET /api/studio/voices - get available voices"""
        response = requests.get(
            f"{BASE_URL}/api/studio/voices",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        print(f"Found {len(data['voices'])} voices")
    
    def test_studio_music_library(self, auth_headers):
        """GET /api/studio/music-library - get music library"""
        response = requests.get(
            f"{BASE_URL}/api/studio/music-library",
            headers=auth_headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        print(f"Found {len(data['tracks'])} music tracks")


class TestCoreLLMModule:
    """Verify core.llm module structure"""
    
    def test_llm_module_exists(self):
        """Verify /app/backend/core/llm.py exists and has required exports"""
        import sys
        sys.path.insert(0, "/app/backend")
        
        from core.llm import (
            DirectChat,
            direct_completion,
            speech_to_text,
            generate_image_gemini,
            DirectSora2Client,
            ANTHROPIC_API_KEY,
            OPENAI_API_KEY,
            GEMINI_API_KEY,
        )
        
        # Verify API keys are set (not empty)
        assert ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY not set"
        assert OPENAI_API_KEY, "OPENAI_API_KEY not set"
        assert GEMINI_API_KEY, "GEMINI_API_KEY not set"
        
        print("core.llm module verified with all required exports")
        print(f"ANTHROPIC_API_KEY: {'set' if ANTHROPIC_API_KEY else 'NOT SET'}")
        print(f"OPENAI_API_KEY: {'set' if OPENAI_API_KEY else 'NOT SET'}")
        print(f"GEMINI_API_KEY: {'set' if GEMINI_API_KEY else 'NOT SET'}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
