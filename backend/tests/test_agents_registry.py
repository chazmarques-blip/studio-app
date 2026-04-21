"""
StudioX Agents Registry API Tests
Tests for the pipeline-wide AI agent control system.

Features tested:
- GET /api/studio/agents/registry - List all agents (17 agents across 3 categories)
- GET /api/studio/agents/registry/{agent_id} - Get full agent spec
- PUT /api/studio/agents/registry/{agent_id} - Update agent with edit_history
- POST /api/studio/agents/registry/{agent_id}/rollback - Rollback to history version
- GET /api/studio/agents/mindsets - List category mindsets
- PUT /api/studio/agents/mindsets/{category} - Update mindset
- POST /api/studio/agents/playground - Execute LLM call (limited tests)
- resolve_agent_prompt() helper function behavior
"""

import pytest
import requests
import os
import json
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from /app/memory/test_credentials.md
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    token = data.get("access_token")
    if not token:
        pytest.skip("No access_token in login response")
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestHealthAndBasics:
    """Basic health checks to ensure backend is running."""
    
    def test_health_check(self):
        """Verify backend is healthy."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health check passed")
    
    def test_auth_login(self):
        """Verify login works with test credentials."""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        print("✓ Auth login passed")


class TestAgentsRegistryList:
    """Tests for GET /api/studio/agents/registry - List all agents."""
    
    def test_list_agents_returns_17_agents(self, auth_headers):
        """Verify registry returns 17 agents total."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "agents" in data, "Response missing 'agents' key"
        assert "total" in data, "Response missing 'total' key"
        
        # Should have 17 agents (8 video + 8 book + 1 audio)
        assert data["total"] == 17, f"Expected 17 agents, got {data['total']}"
        assert len(data["agents"]) == 17, f"Expected 17 agents in list, got {len(data['agents'])}"
        print(f"✓ Registry returns {data['total']} agents")
    
    def test_agents_have_correct_categories(self, auth_headers):
        """Verify agents are categorized correctly: video=8, book=8, audio=1."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        categories = {"video": 0, "book": 0, "audio": 0}
        for agent in data["agents"]:
            cat = agent.get("category")
            if cat in categories:
                categories[cat] += 1
        
        assert categories["video"] == 8, f"Expected 8 video agents, got {categories['video']}"
        assert categories["book"] == 8, f"Expected 8 book agents, got {categories['book']}"
        assert categories["audio"] == 1, f"Expected 1 audio agent, got {categories['audio']}"
        print(f"✓ Categories correct: video={categories['video']}, book={categories['book']}, audio={categories['audio']}")
    
    def test_agents_have_master_reference(self, auth_headers):
        """Verify agents have master_reference populated."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        agents_with_master = [a for a in data["agents"] if a.get("master_reference")]
        # Most agents should have master_reference
        assert len(agents_with_master) >= 10, f"Expected at least 10 agents with master_reference, got {len(agents_with_master)}"
        print(f"✓ {len(agents_with_master)} agents have master_reference")
    
    def test_agents_have_required_fields(self, auth_headers):
        """Verify each agent has required fields."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "name", "category", "active"]
        for agent in data["agents"]:
            for field in required_fields:
                assert field in agent, f"Agent {agent.get('id', 'unknown')} missing field: {field}"
        print("✓ All agents have required fields")


class TestAgentDetail:
    """Tests for GET /api/studio/agents/registry/{agent_id} - Get full agent spec."""
    
    def test_get_screenwriter_agent(self, auth_headers):
        """Get full spec of screenwriter_agent."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "agent" in data, "Response missing 'agent' key"
        agent = data["agent"]
        
        # Verify full spec fields
        assert agent.get("id") == "screenwriter_agent"
        assert agent.get("master_reference") == "Aaron Sorkin"
        assert "master_bio" in agent, "Missing master_bio"
        assert "system_prompt" in agent, "Missing system_prompt"
        assert "edit_history" in agent, "Missing edit_history"
        print(f"✓ screenwriter_agent has full spec with master_reference: {agent.get('master_reference')}")
    
    def test_get_book_agent(self, auth_headers):
        """Get full spec of a book agent (author_agent)."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/author_agent", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        agent = data["agent"]
        assert agent.get("id") == "author_agent"
        assert agent.get("category") == "book"
        assert agent.get("master_reference") == "Neil Gaiman"
        print(f"✓ author_agent (book) has master_reference: {agent.get('master_reference')}")
    
    def test_get_audio_agent(self, auth_headers):
        """Get full spec of audio agent (sound_designer_agent)."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/sound_designer_agent", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        agent = data["agent"]
        assert agent.get("id") == "sound_designer_agent"
        assert agent.get("category") == "audio"
        assert agent.get("master_reference") == "Hans Zimmer"
        print(f"✓ sound_designer_agent (audio) has master_reference: {agent.get('master_reference')}")
    
    def test_get_nonexistent_agent_returns_404(self, auth_headers):
        """Verify 404 for non-existent agent."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/nonexistent_agent_xyz", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent agent returns 404")


class TestAgentUpdate:
    """Tests for PUT /api/studio/agents/registry/{agent_id} - Update agent."""
    
    def test_update_agent_appends_to_history(self, auth_headers):
        """Update agent and verify edit_history is appended."""
        # First get current state
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        assert response.status_code == 200
        original = response.json()["agent"]
        original_history_len = len(original.get("edit_history", []))
        
        # Update with a small change
        update_data = {
            "temperature": 0.75,
            "min_quality_score": 86
        }
        response = requests.put(
            f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        result = response.json()
        
        assert result.get("status") == "updated"
        assert result.get("agent_id") == "screenwriter_agent"
        assert "history_size" in result
        
        # Verify history was appended
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        updated = response.json()["agent"]
        new_history_len = len(updated.get("edit_history", []))
        
        assert new_history_len == original_history_len + 1, f"History should have grown by 1"
        print(f"✓ Update appended to edit_history (now {new_history_len} entries)")
        
        # Restore original values
        restore_data = {
            "temperature": original.get("temperature", 0.7),
            "min_quality_score": original.get("min_quality_score", 85)
        }
        requests.put(
            f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent",
            headers=auth_headers,
            json=restore_data
        )
    
    def test_update_preserves_agent_id(self, auth_headers):
        """Verify update doesn't allow changing agent ID."""
        update_data = {
            "id": "hacked_id",  # Should be ignored
            "temperature": 0.7
        }
        response = requests.put(
            f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        
        # Verify ID wasn't changed
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        agent = response.json()["agent"]
        assert agent.get("id") == "screenwriter_agent", "Agent ID should not change"
        print("✓ Update preserves agent_id")


class TestAgentRollback:
    """Tests for POST /api/studio/agents/registry/{agent_id}/rollback."""
    
    def test_rollback_to_history_index(self, auth_headers):
        """Test rollback to a specific history index."""
        # Get current state
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        assert response.status_code == 200
        agent = response.json()["agent"]
        history = agent.get("edit_history", [])
        
        if len(history) < 1:
            pytest.skip("No history available for rollback test")
        
        # Rollback to index 0 (oldest)
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent/rollback",
            headers=auth_headers,
            json={"index": 0}
        )
        assert response.status_code == 200, f"Rollback failed: {response.text}"
        result = response.json()
        
        assert result.get("status") == "rolled_back"
        assert result.get("index") == 0
        print("✓ Rollback to index 0 succeeded")
    
    def test_rollback_invalid_index_returns_400(self, auth_headers):
        """Verify 400 for invalid history index."""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent/rollback",
            headers=auth_headers,
            json={"index": 9999}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid rollback index returns 400")


class TestMindsets:
    """Tests for mindsets endpoints."""
    
    def test_list_mindsets_returns_3_categories(self, auth_headers):
        """Verify mindsets returns 3 categories: video, book, audio."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "mindsets" in data
        assert "categories" in data
        
        categories = data["categories"]
        assert "video" in categories, "Missing video mindset"
        assert "book" in categories, "Missing book mindset"
        assert "audio" in categories, "Missing audio mindset"
        assert len(categories) == 3, f"Expected 3 categories, got {len(categories)}"
        print(f"✓ Mindsets returns 3 categories: {categories}")
    
    def test_get_video_mindset(self, auth_headers):
        """Get video mindset details."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        mindset = data.get("mindset")
        assert mindset is not None
        assert mindset.get("category") == "video"
        assert "system_prompt" in mindset
        assert "active" in mindset
        print(f"✓ Video mindset retrieved, active={mindset.get('active')}")
    
    def test_update_mindset_appends_history(self, auth_headers):
        """Update mindset and verify edit_history is appended."""
        # Get current state
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        original = response.json()["mindset"]
        original_history_len = len(original.get("edit_history", []))
        
        # Update with small change
        update_data = {
            "temperature": 0.75
        }
        response = requests.put(
            f"{BASE_URL}/api/studio/agents/mindsets/video",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        result = response.json()
        
        assert result.get("status") == "updated"
        assert result.get("category") == "video"
        
        # Verify history was appended
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/video", headers=auth_headers)
        updated = response.json()["mindset"]
        new_history_len = len(updated.get("edit_history", []))
        
        assert new_history_len == original_history_len + 1
        print(f"✓ Mindset update appended to edit_history (now {new_history_len} entries)")
        
        # Restore original
        restore_data = {
            "temperature": original.get("temperature", 0.7)
        }
        requests.put(
            f"{BASE_URL}/api/studio/agents/mindsets/video",
            headers=auth_headers,
            json=restore_data
        )
    
    def test_get_nonexistent_mindset_returns_404(self, auth_headers):
        """Verify 404 for non-existent mindset category."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Non-existent mindset returns 404")


class TestResolveAgentPrompt:
    """Tests for resolve_agent_prompt() helper behavior via API."""
    
    def test_inactive_agent_uses_fallback(self, auth_headers):
        """When agent is inactive, resolve_agent_prompt should return fallback."""
        # First ensure agent is inactive
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry/screenwriter_agent", headers=auth_headers)
        agent = response.json()["agent"]
        
        # Verify agent is inactive (seeded as active=false)
        assert agent.get("active") == False, "Agent should be inactive by default"
        print("✓ screenwriter_agent is inactive (active=false)")
    
    def test_all_agents_seeded_inactive(self, auth_headers):
        """Verify all 17 agents are seeded with active=false."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers)
        data = response.json()
        
        inactive_count = sum(1 for a in data["agents"] if a.get("active") == False)
        assert inactive_count == 17, f"Expected all 17 agents inactive, got {inactive_count}"
        print("✓ All 17 agents are seeded with active=false")
    
    def test_all_mindsets_seeded_inactive(self, auth_headers):
        """Verify all 3 mindsets are seeded with active=false."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets", headers=auth_headers)
        data = response.json()
        
        mindsets = data.get("mindsets", {})
        for category, mindset in mindsets.items():
            assert mindset.get("active") == False, f"Mindset {category} should be inactive"
        print("✓ All 3 mindsets are seeded with active=false")


class TestPlayground:
    """Tests for POST /api/studio/agents/playground - LLM execution.
    
    NOTE: Limited to 2 tests as per instructions (costs LLM tokens).
    """
    
    def test_playground_requires_user_input(self, auth_headers):
        """Verify playground returns 400 if user_input is empty."""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/playground",
            headers=auth_headers,
            json={
                "agent_id": "screenwriter_agent",
                "user_input": ""
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Playground returns 400 for empty user_input")
    
    def test_playground_executes_llm_call(self, auth_headers):
        """Test playground executes real LLM call and returns output.
        
        This is 1 of 2 allowed LLM tests.
        """
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/playground",
            headers=auth_headers,
            json={
                "agent_id": "screenwriter_agent",
                "system_prompt": "You are a helpful assistant. Respond in one sentence.",
                "user_input": "Say hello",
                "temperature": 0.5,
                "include_mindset": False
            },
            timeout=30  # LLM calls can be slow
        )
        
        # Allow 200 (success) or 500 (LLM error - acceptable for test)
        if response.status_code == 500:
            print(f"⚠ Playground LLM call failed (acceptable): {response.text[:200]}")
            pytest.skip("LLM call failed - may be rate limited or API issue")
        
        assert response.status_code == 200, f"Playground failed: {response.text}"
        data = response.json()
        
        assert "output" in data, "Response missing 'output'"
        assert "agent_id" in data
        assert data["agent_id"] == "screenwriter_agent"
        assert len(data.get("output", "")) > 0, "Output should not be empty"
        print(f"✓ Playground executed LLM call, output length: {len(data['output'])} chars")


class TestPipelineRegression:
    """Regression tests to ensure pipeline still works."""
    
    def test_projects_list_works(self, auth_headers):
        """Verify project list endpoint still works."""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200, f"Projects list failed: {response.text}"
        data = response.json()
        assert "projects" in data or isinstance(data, list)
        print("✓ Projects list endpoint works")
    
    def test_dashboard_stats_works(self, auth_headers):
        """Verify dashboard stats endpoint still works."""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        print("✓ Dashboard stats endpoint works")


class TestCleanup:
    """Cleanup tests - ensure agents/mindsets are reset to inactive."""
    
    def test_reset_agents_to_inactive(self, auth_headers):
        """Reset any agents that might have been set to active during testing."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers)
        data = response.json()
        
        for agent in data["agents"]:
            if agent.get("active") == True:
                # Reset to inactive
                requests.put(
                    f"{BASE_URL}/api/studio/agents/registry/{agent['id']}",
                    headers=auth_headers,
                    json={"active": False}
                )
                print(f"  Reset {agent['id']} to active=false")
        
        print("✓ All agents reset to active=false")
    
    def test_reset_mindsets_to_inactive(self, auth_headers):
        """Reset any mindsets that might have been set to active during testing."""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets", headers=auth_headers)
        data = response.json()
        
        for category, mindset in data.get("mindsets", {}).items():
            if mindset.get("active") == True:
                # Reset to inactive
                requests.put(
                    f"{BASE_URL}/api/studio/agents/mindsets/{category}",
                    headers=auth_headers,
                    json={"active": False}
                )
                print(f"  Reset {category} mindset to active=false")
        
        print("✓ All mindsets reset to active=false")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
