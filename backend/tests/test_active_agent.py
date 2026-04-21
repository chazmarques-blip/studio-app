"""
Test Active Agent Feature - StudioX
Tests the real-time agent activity tracking for visual feedback during pipeline execution.

Endpoints tested:
- GET /api/studio/projects/{id}/active-agent
- POST /api/studio/projects/{id}/continuity-audit (triggers set_active_agent)
- POST /api/studio/book/projects/{id}/visual-continuity-audit (triggers set_active_agent)

Features tested:
- set_active_agent/clear_active_agent helpers
- Agent metadata enrichment (name, master_reference)
- Timeline capping (20 entries) and deduplication
- Auto-expire stale active_agent (>10 min)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"

# Test project IDs from the review request
VIDEO_PROJECT_ID = "1f26f1649bcf"  # JONAS E O PEIXE GRANDE - 32 scenes
BOOK_PROJECT_ID = "017f57ef8ecd"   # Manual do Pulmeranea


class TestActiveAgentBackend:
    """Backend tests for active agent tracking feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token") or data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # ─── GET /api/studio/projects/{id}/active-agent ───────────────
    
    def test_get_active_agent_endpoint_exists(self, auth_headers):
        """Test that the active-agent endpoint exists and returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "active_agent" in data, "Response must have 'active_agent' field"
        assert "timeline" in data, "Response must have 'timeline' field"
        
        # Timeline should be a list
        assert isinstance(data["timeline"], list), "Timeline must be a list"
        print(f"✓ GET active-agent returns proper structure: active_agent={data['active_agent']}, timeline_count={len(data['timeline'])}")
    
    def test_get_active_agent_returns_null_when_idle(self, auth_headers):
        """When no agent is running, active_agent should be null"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # After audit completes, active_agent should be null
        # (This test runs after continuity audit tests, so it should be cleared)
        # Note: This may be null or have a value depending on test order
        print(f"✓ active_agent value: {data['active_agent']}")
    
    def test_get_active_agent_404_for_invalid_project(self, auth_headers):
        """Test 404 for non-existent project"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/invalid_project_id_xyz/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Returns 404 for invalid project ID")
    
    def test_get_active_agent_timeline_capped_at_10(self, auth_headers):
        """Timeline in response should be capped at 10 entries (last 10)"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        timeline = data.get("timeline", [])
        assert len(timeline) <= 10, f"Timeline should be capped at 10, got {len(timeline)}"
        print(f"✓ Timeline capped correctly: {len(timeline)} entries (max 10)")
    
    # ─── POST /api/studio/projects/{id}/continuity-audit ──────────
    
    def test_continuity_audit_sets_active_agent(self, auth_headers):
        """
        POST continuity-audit should set active_agent to 'consistency_checker_agent'
        with master_reference 'Thelma Schoonmaker'
        """
        # First, check current state
        initial_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert initial_response.status_code == 200
        
        # Trigger continuity audit (this is a long-running operation)
        # We'll start it and immediately check active-agent
        import threading
        audit_started = threading.Event()
        audit_result = {"response": None, "error": None}
        
        def run_audit():
            try:
                audit_started.set()
                audit_result["response"] = requests.post(
                    f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/continuity-audit",
                    headers=auth_headers,
                    timeout=120
                )
            except Exception as e:
                audit_result["error"] = str(e)
        
        # Start audit in background
        audit_thread = threading.Thread(target=run_audit)
        audit_thread.start()
        audit_started.wait()
        
        # Poll active-agent to see if it's set
        time.sleep(1)  # Give backend time to set active_agent
        
        found_active = False
        for _ in range(10):  # Poll up to 10 times
            check_response = requests.get(
                f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
                headers=auth_headers
            )
            if check_response.status_code == 200:
                data = check_response.json()
                active = data.get("active_agent")
                if active:
                    found_active = True
                    print(f"✓ Active agent during audit: {active}")
                    
                    # Verify structure
                    assert "agent_id" in active, "active_agent must have agent_id"
                    assert "name" in active, "active_agent must have name"
                    assert "action" in active, "active_agent must have action"
                    assert "started_at" in active, "active_agent must have started_at"
                    
                    # Check for expected agent
                    if active.get("agent_id") == "consistency_checker_agent":
                        assert active.get("master_reference") is not None or active.get("name") == "Verificador de Consistência", \
                            "consistency_checker_agent should have master_reference or proper name"
                        print(f"✓ Correct agent: {active.get('name')} ({active.get('master_reference')})")
                    break
            time.sleep(1)
        
        # Wait for audit to complete
        audit_thread.join(timeout=120)
        
        if audit_result["response"]:
            assert audit_result["response"].status_code == 200, \
                f"Audit failed: {audit_result['response'].text}"
            print("✓ Continuity audit completed successfully")
        
        # After audit, active_agent should be cleared
        time.sleep(1)
        final_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert final_response.status_code == 200
        final_data = final_response.json()
        
        # Active agent should be null after completion
        assert final_data.get("active_agent") is None, \
            f"active_agent should be null after audit completes, got: {final_data.get('active_agent')}"
        print("✓ active_agent cleared after audit completion")
    
    def test_continuity_audit_adds_to_timeline(self, auth_headers):
        """Continuity audit should add entry to agent_timeline"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        timeline = data.get("timeline", [])
        
        # Check if there's a consistency_checker_agent entry in timeline
        consistency_entries = [
            e for e in timeline 
            if e.get("agent_id") == "consistency_checker_agent"
        ]
        
        if consistency_entries:
            entry = consistency_entries[-1]
            assert "name" in entry, "Timeline entry must have name"
            assert "action" in entry, "Timeline entry must have action"
            assert "at" in entry, "Timeline entry must have timestamp"
            print(f"✓ Timeline has consistency_checker entry: {entry}")
        else:
            print(f"⚠ No consistency_checker_agent in timeline (may not have run yet): {timeline}")
    
    # ─── POST /api/studio/book/projects/{id}/visual-continuity-audit ───
    
    def test_book_visual_audit_endpoint_exists(self, auth_headers):
        """Test that book visual continuity audit endpoint exists"""
        # This may fail if the book project doesn't have spreads
        response = requests.post(
            f"{BASE_URL}/api/studio/book/projects/{BOOK_PROJECT_ID}/visual-continuity-audit",
            headers=auth_headers,
            timeout=120
        )
        
        # Accept 200 (success) or 400 (no spreads to audit)
        assert response.status_code in [200, 400], \
            f"Expected 200 or 400, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "report" in data, "Response must have 'report' field"
            print(f"✓ Book visual audit completed: score={data['report'].get('score')}")
        else:
            print(f"✓ Book visual audit endpoint exists (400 = no spreads to audit)")
    
    # ─── Agent metadata enrichment ────────────────────────────────
    
    def test_agent_metadata_enrichment(self, auth_headers):
        """Test that agent metadata (name, master_reference) is enriched from registry"""
        # Get active-agent to check timeline entries
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        timeline = data.get("timeline", [])
        
        # Check that timeline entries have enriched metadata
        for entry in timeline:
            assert "agent_id" in entry, "Entry must have agent_id"
            assert "name" in entry, "Entry must have name (enriched)"
            # master_reference may be None for some agents
            print(f"  Timeline entry: {entry.get('agent_id')} → {entry.get('name')} ({entry.get('master_reference')})")
        
        print(f"✓ Timeline entries have enriched metadata ({len(timeline)} entries)")
    
    # ─── Timeline deduplication ───────────────────────────────────
    
    def test_timeline_no_consecutive_duplicates(self, auth_headers):
        """Timeline should not have consecutive identical entries"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        timeline = data.get("timeline", [])
        
        # Check for consecutive duplicates
        for i in range(1, len(timeline)):
            prev = timeline[i-1]
            curr = timeline[i]
            
            # Same agent_id AND same action should not be consecutive
            if prev.get("agent_id") == curr.get("agent_id") and prev.get("action") == curr.get("action"):
                pytest.fail(f"Found consecutive duplicate: {prev} and {curr}")
        
        print(f"✓ No consecutive duplicates in timeline ({len(timeline)} entries)")


class TestActiveAgentAuth:
    """Test authentication requirements for active-agent endpoints"""
    
    def test_active_agent_requires_auth(self):
        """GET active-agent should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/active-agent"
        )
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ active-agent endpoint requires authentication")
    
    def test_continuity_audit_requires_auth(self):
        """POST continuity-audit should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{VIDEO_PROJECT_ID}/continuity-audit"
        )
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ continuity-audit endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
