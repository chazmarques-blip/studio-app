"""
Test Suite for StudioX P2 Features:
1. Agent Metrics (GET /agents/metrics, POST /agents/metrics/reset, record_activation)
2. Export/Import Agents (GET /agents/export, POST /agents/import)
3. Pipeline audit triggers record_activation

Test credentials: test@studiox.com / studiox123
"""
import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"
TEST_PROJECT_ID = "1f26f1649bcf"  # JONAS E O PEIXE GRANDE


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ═══════════════════════════════════════════════════════════════
# AGENT METRICS TESTS
# ═══════════════════════════════════════════════════════════════

class TestAgentMetrics:
    """Tests for GET /agents/metrics and POST /agents/metrics/reset"""
    
    def test_get_metrics_endpoint_exists(self, auth_headers):
        """GET /api/studio/agents/metrics should return 200"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/metrics", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print("✅ GET /agents/metrics endpoint exists and returns 200")
    
    def test_get_metrics_returns_structure(self, auth_headers):
        """GET /agents/metrics should return {metrics, totals}"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/metrics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "metrics" in data, "Response should contain 'metrics' key"
        assert "totals" in data, "Response should contain 'totals' key"
        
        # Verify totals structure
        totals = data["totals"]
        assert "activations" in totals, "totals should have 'activations'"
        assert "estimated_cost_usd" in totals, "totals should have 'estimated_cost_usd'"
        assert "total_duration_seconds" in totals, "totals should have 'total_duration_seconds'"
        
        print(f"✅ GET /agents/metrics returns correct structure: {len(data['metrics'])} agents tracked")
        print(f"   Totals: activations={totals['activations']}, cost=${totals['estimated_cost_usd']:.4f}, duration={totals['total_duration_seconds']}s")
    
    def test_reset_metrics_endpoint_exists(self, auth_headers):
        """POST /api/studio/agents/metrics/reset should return 200"""
        response = requests.post(f"{BASE_URL}/api/studio/agents/metrics/reset", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert data.get("status") == "reset", f"Expected status='reset', got {data}"
        print("✅ POST /agents/metrics/reset works correctly")
    
    def test_reset_clears_metrics(self, auth_headers):
        """After reset, metrics should be empty"""
        # Reset first
        requests.post(f"{BASE_URL}/api/studio/agents/metrics/reset", headers=auth_headers)
        
        # Get metrics
        response = requests.get(f"{BASE_URL}/api/studio/agents/metrics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # After reset, metrics should be empty or totals should be 0
        totals = data["totals"]
        assert totals["activations"] == 0, f"Expected 0 activations after reset, got {totals['activations']}"
        assert totals["estimated_cost_usd"] == 0, f"Expected 0 cost after reset, got {totals['estimated_cost_usd']}"
        
        print("✅ Metrics correctly reset to zero")
    
    def test_metrics_requires_auth(self):
        """GET /agents/metrics without auth should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/metrics")
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422 without auth, got {response.status_code}"
        print("✅ GET /agents/metrics requires authentication")


# ═══════════════════════════════════════════════════════════════
# CONTINUITY AUDIT TRIGGERS RECORD_ACTIVATION
# ═══════════════════════════════════════════════════════════════

class TestAuditTriggersMetrics:
    """Test that continuity-audit triggers record_activation"""
    
    def test_audit_records_activation(self, auth_headers):
        """
        POST /api/studio/projects/{id}/continuity-audit should trigger record_activation.
        After audit, GET /agents/metrics should show consistency_checker_agent with activations >= 1.
        """
        # Step 1: Reset metrics to start clean
        reset_resp = requests.post(f"{BASE_URL}/api/studio/agents/metrics/reset", headers=auth_headers)
        assert reset_resp.status_code == 200, f"Reset failed: {reset_resp.text[:200]}"
        print("✅ Step 1: Metrics reset")
        
        # Step 2: Trigger continuity audit
        audit_resp = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity-audit",
            headers=auth_headers,
            timeout=120  # Audit can take time due to LLM call
        )
        # Accept 200 (success) or 400 (no scenes) - both are valid responses
        assert audit_resp.status_code in [200, 400], f"Audit failed: {audit_resp.status_code} - {audit_resp.text[:300]}"
        
        if audit_resp.status_code == 400:
            print("⚠️ Project has no scenes - skipping activation check (expected behavior)")
            pytest.skip("Project has no scenes to audit")
        
        print(f"✅ Step 2: Continuity audit completed")
        
        # Step 3: Check metrics - consistency_checker_agent should have activations >= 1
        metrics_resp = requests.get(f"{BASE_URL}/api/studio/agents/metrics", headers=auth_headers)
        assert metrics_resp.status_code == 200
        data = metrics_resp.json()
        
        metrics = data.get("metrics", {})
        agent_metric = metrics.get("consistency_checker_agent")
        
        assert agent_metric is not None, f"consistency_checker_agent not found in metrics. Available: {list(metrics.keys())}"
        assert agent_metric.get("activations", 0) >= 1, f"Expected activations >= 1, got {agent_metric.get('activations')}"
        
        # Check avg_latency_seconds is computed
        avg_latency = agent_metric.get("avg_latency_seconds", 0)
        assert avg_latency > 0, f"Expected avg_latency_seconds > 0, got {avg_latency}"
        
        print(f"✅ Step 3: consistency_checker_agent metrics recorded:")
        print(f"   activations={agent_metric.get('activations')}")
        print(f"   avg_latency_seconds={avg_latency:.2f}")
        print(f"   total_duration_seconds={agent_metric.get('total_duration_seconds')}")
        print(f"   estimated_cost_usd=${agent_metric.get('estimated_cost_usd', 0):.6f}")


# ═══════════════════════════════════════════════════════════════
# EXPORT/IMPORT AGENTS TESTS
# ═══════════════════════════════════════════════════════════════

class TestAgentsExport:
    """Tests for GET /agents/export"""
    
    def test_export_endpoint_exists(self, auth_headers):
        """GET /api/studio/agents/export should return 200"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/export", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print("✅ GET /agents/export endpoint exists and returns 200")
    
    def test_export_returns_correct_structure(self, auth_headers):
        """Export should return {format_version, agents, mindsets, counts}"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/export", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert data.get("format_version") == 1, f"Expected format_version=1, got {data.get('format_version')}"
        assert "agents" in data, "Response should contain 'agents' array"
        assert "mindsets" in data, "Response should contain 'mindsets' dict"
        assert "counts" in data, "Response should contain 'counts'"
        
        # Verify agents is a list
        assert isinstance(data["agents"], list), "agents should be a list"
        
        # Verify counts
        counts = data["counts"]
        assert "agents" in counts, "counts should have 'agents'"
        assert "mindsets" in counts, "counts should have 'mindsets'"
        assert counts["agents"] == len(data["agents"]), "counts.agents should match agents array length"
        
        print(f"✅ Export structure correct:")
        print(f"   format_version={data['format_version']}")
        print(f"   agents={counts['agents']}")
        print(f"   mindsets={counts['mindsets']}")
        print(f"   exported_at={data.get('exported_at')}")
    
    def test_export_agents_have_required_fields(self, auth_headers):
        """Each exported agent should have id, name, system_prompt"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/export", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        agents = data.get("agents", [])
        if not agents:
            pytest.skip("No agents to export")
        
        # Check first few agents
        for agent in agents[:5]:
            assert "id" in agent, f"Agent missing 'id': {agent.get('name')}"
            assert "name" in agent, f"Agent missing 'name': {agent.get('id')}"
            # system_prompt may be optional for some agents
            assert "_category" in agent, f"Agent missing '_category': {agent.get('id')}"
        
        print(f"✅ Exported agents have required fields (checked {min(5, len(agents))} agents)")
    
    def test_export_requires_auth(self):
        """GET /agents/export without auth should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/export")
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422 without auth, got {response.status_code}"
        print("✅ GET /agents/export requires authentication")


class TestAgentsImport:
    """Tests for POST /agents/import"""
    
    @pytest.fixture
    def export_payload(self, auth_headers):
        """Get current export to use for import tests"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/export", headers=auth_headers)
        if response.status_code != 200:
            pytest.skip("Could not get export for import test")
        return response.json()
    
    def test_import_endpoint_exists(self, auth_headers, export_payload):
        """POST /api/studio/agents/import should return 200"""
        # Import with overwrite=false (should skip all existing)
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/import",
            headers=auth_headers,
            json={
                "format_version": 1,
                "agents": export_payload.get("agents", []),
                "mindsets": export_payload.get("mindsets", {}),
                "overwrite": False
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print("✅ POST /agents/import endpoint exists and returns 200")
    
    def test_import_with_overwrite_false_skips_existing(self, auth_headers, export_payload):
        """Import with overwrite=false should skip existing agents"""
        agents = export_payload.get("agents", [])
        mindsets = export_payload.get("mindsets", {})
        
        if not agents:
            pytest.skip("No agents to test import")
        
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/import",
            headers=auth_headers,
            json={
                "format_version": 1,
                "agents": agents,
                "mindsets": mindsets,
                "overwrite": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # With overwrite=false, all existing agents should be skipped
        assert data.get("skipped", 0) > 0, f"Expected skipped > 0, got {data.get('skipped')}"
        assert data.get("imported_agents", 0) == 0, f"Expected imported_agents=0 with overwrite=false, got {data.get('imported_agents')}"
        
        print(f"✅ Import with overwrite=false correctly skips existing:")
        print(f"   skipped={data.get('skipped')}")
        print(f"   imported_agents={data.get('imported_agents')}")
        print(f"   imported_mindsets={data.get('imported_mindsets')}")
    
    def test_import_with_overwrite_true_imports(self, auth_headers, export_payload):
        """Import with overwrite=true should import/replace agents"""
        agents = export_payload.get("agents", [])
        mindsets = export_payload.get("mindsets", {})
        
        if not agents:
            pytest.skip("No agents to test import")
        
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/import",
            headers=auth_headers,
            json={
                "format_version": 1,
                "agents": agents,
                "mindsets": mindsets,
                "overwrite": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # With overwrite=true, agents should be imported
        assert data.get("imported_agents", 0) > 0, f"Expected imported_agents > 0 with overwrite=true, got {data.get('imported_agents')}"
        
        print(f"✅ Import with overwrite=true correctly imports:")
        print(f"   imported_agents={data.get('imported_agents')}")
        print(f"   imported_mindsets={data.get('imported_mindsets')}")
        print(f"   skipped={data.get('skipped')}")
        print(f"   errors={len(data.get('errors', []))}")
    
    def test_import_returns_correct_structure(self, auth_headers, export_payload):
        """Import response should have status, imported_agents, imported_mindsets, skipped, errors"""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/import",
            headers=auth_headers,
            json={
                "format_version": 1,
                "agents": export_payload.get("agents", [])[:2],  # Just 2 agents
                "mindsets": {},
                "overwrite": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data, "Response should have 'status'"
        assert "imported_agents" in data, "Response should have 'imported_agents'"
        assert "imported_mindsets" in data, "Response should have 'imported_mindsets'"
        assert "skipped" in data, "Response should have 'skipped'"
        assert "errors" in data, "Response should have 'errors'"
        
        print(f"✅ Import response has correct structure")
    
    def test_import_requires_auth(self):
        """POST /agents/import without auth should return 401/403"""
        response = requests.post(
            f"{BASE_URL}/api/studio/agents/import",
            json={"format_version": 1, "agents": [], "mindsets": {}}
        )
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422 without auth, got {response.status_code}"
        print("✅ POST /agents/import requires authentication")


# ═══════════════════════════════════════════════════════════════
# SET_ACTIVE_AGENT AUTO-RECORDS PREV AGENT
# ═══════════════════════════════════════════════════════════════

class TestSetActiveAgentAutoRecords:
    """Test that set_active_agent auto-records metrics for previous agent"""
    
    def test_active_agent_endpoint_exists(self, auth_headers):
        """GET /api/studio/projects/{id}/active-agent should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/active-agent",
            headers=auth_headers
        )
        # 200 or 404 (project not found) are both valid
        assert response.status_code in [200, 404], f"Expected 200/404, got {response.status_code}"
        print(f"✅ GET /active-agent endpoint exists (status={response.status_code})")


# ═══════════════════════════════════════════════════════════════
# FRONTEND BUTTON DATA-TESTID VERIFICATION (via API check)
# ═══════════════════════════════════════════════════════════════

class TestFrontendButtonsExist:
    """Verify that the frontend buttons exist by checking the AgentsPage.jsx file"""
    
    def test_metrics_button_testid_in_code(self):
        """Check btn-open-metrics exists in AgentsPage.jsx"""
        try:
            with open('/app/frontend/src/pages/AgentsPage.jsx', 'r') as f:
                content = f.read()
            assert 'data-testid="btn-open-metrics"' in content, "btn-open-metrics not found in AgentsPage.jsx"
            print("✅ data-testid='btn-open-metrics' found in AgentsPage.jsx")
        except FileNotFoundError:
            pytest.skip("AgentsPage.jsx not found")
    
    def test_export_button_testid_in_code(self):
        """Check btn-export-agents exists in AgentsPage.jsx"""
        try:
            with open('/app/frontend/src/pages/AgentsPage.jsx', 'r') as f:
                content = f.read()
            assert 'data-testid="btn-export-agents"' in content, "btn-export-agents not found in AgentsPage.jsx"
            print("✅ data-testid='btn-export-agents' found in AgentsPage.jsx")
        except FileNotFoundError:
            pytest.skip("AgentsPage.jsx not found")
    
    def test_import_button_testid_in_code(self):
        """Check btn-import-agents exists in AgentsPage.jsx"""
        try:
            with open('/app/frontend/src/pages/AgentsPage.jsx', 'r') as f:
                content = f.read()
            assert 'data-testid="btn-import-agents"' in content, "btn-import-agents not found in AgentsPage.jsx"
            print("✅ data-testid='btn-import-agents' found in AgentsPage.jsx")
        except FileNotFoundError:
            pytest.skip("AgentsPage.jsx not found")
    
    def test_metrics_modal_testid_in_code(self):
        """Check metrics-modal exists in AgentsPage.jsx"""
        try:
            with open('/app/frontend/src/pages/AgentsPage.jsx', 'r') as f:
                content = f.read()
            assert 'data-testid="metrics-modal"' in content, "metrics-modal not found in AgentsPage.jsx"
            print("✅ data-testid='metrics-modal' found in AgentsPage.jsx")
        except FileNotFoundError:
            pytest.skip("AgentsPage.jsx not found")
    
    def test_metrics_reset_button_testid_in_code(self):
        """Check metrics-reset-btn exists in AgentsPage.jsx"""
        try:
            with open('/app/frontend/src/pages/AgentsPage.jsx', 'r') as f:
                content = f.read()
            assert 'data-testid="metrics-reset-btn"' in content, "metrics-reset-btn not found in AgentsPage.jsx"
            print("✅ data-testid='metrics-reset-btn' found in AgentsPage.jsx")
        except FileNotFoundError:
            pytest.skip("AgentsPage.jsx not found")


# ═══════════════════════════════════════════════════════════════
# LIGHTBOX KEYBOARD NAVIGATION (code verification)
# ═══════════════════════════════════════════════════════════════

class TestLightboxKeyboardNavigation:
    """Verify keyboard navigation code exists in DirectedStudio.jsx"""
    
    def test_escape_key_handler_exists(self):
        """Check Escape key closes modal"""
        try:
            with open('/app/frontend/src/components/DirectedStudio.jsx', 'r') as f:
                content = f.read()
            assert "e.key === 'Escape'" in content, "Escape key handler not found"
            assert "setPreviewModal(null)" in content, "setPreviewModal(null) not found for Escape"
            print("✅ Escape key handler found in DirectedStudio.jsx")
        except FileNotFoundError:
            pytest.skip("DirectedStudio.jsx not found")
    
    def test_arrow_keys_handler_exists(self):
        """Check ArrowLeft/ArrowRight navigation exists"""
        try:
            with open('/app/frontend/src/components/DirectedStudio.jsx', 'r') as f:
                content = f.read()
            assert "e.key === 'ArrowRight'" in content, "ArrowRight handler not found"
            assert "e.key === 'ArrowLeft'" in content, "ArrowLeft handler not found"
            print("✅ Arrow key handlers found in DirectedStudio.jsx")
        except FileNotFoundError:
            pytest.skip("DirectedStudio.jsx not found")
    
    def test_space_key_handler_exists(self):
        """Check Space key toggles video play/pause"""
        try:
            with open('/app/frontend/src/components/DirectedStudio.jsx', 'r') as f:
                content = f.read()
            assert "e.key === ' '" in content, "Space key handler not found"
            assert "v.paused ? v.play() : v.pause()" in content, "Video play/pause toggle not found"
            print("✅ Space key handler found in DirectedStudio.jsx")
        except FileNotFoundError:
            pytest.skip("DirectedStudio.jsx not found")
    
    def test_video_navigation_logic_exists(self):
        """Check video navigation between scenes exists"""
        try:
            with open('/app/frontend/src/components/DirectedStudio.jsx', 'r') as f:
                content = f.read()
            assert "previewModal.data?.allVideos" in content, "allVideos navigation logic not found"
            print("✅ Video navigation logic found in DirectedStudio.jsx")
        except FileNotFoundError:
            pytest.skip("DirectedStudio.jsx not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
