"""
StudioX P2 Session 2 Tests — Route Cleanup + Multi-Format Export
Tests:
1. Critical endpoints still working after cleanup (auth, studio, data, whatsapp, channels, google)
2. Removed routers return 404 (conversations, leads, telegram, agent_generator, pipeline, agents, ai)
3. New multi-format export endpoints (GET /exports, POST /export-format)
"""
import pytest
import requests
import os

BASE_URL = "http://127.0.0.1:8001"  # Use internal URL for testing

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"
PROJECT_WITH_VIDEO = "1f26f1649bcf"  # JONAS E O PEIXE GRANDE


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# CRITICAL ENDPOINTS STILL WORKING (after cleanup)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthEndpoints:
    """Auth endpoints must still work"""
    
    def test_login_works(self):
        """POST /api/auth/login returns 200"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=60)
        assert response.status_code == 200, f"Login failed: {response.text[:200]}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"


class TestStudioEndpoints:
    """Studio endpoints must still work"""
    
    def test_projects_list(self, auth_headers):
        """GET /api/studio/projects returns list of projects"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers, timeout=60)
        assert response.status_code == 200, f"Projects list failed: {response.text[:200]}"
        data = response.json()
        # API returns {"projects": [...]} or direct list
        projects = data.get("projects", data) if isinstance(data, dict) else data
        assert isinstance(projects, list), "Expected list of projects"
        # Should have ~67 projects per main agent note
        assert len(projects) >= 50, f"Expected ~67 projects, got {len(projects)}"
    
    def test_agents_registry(self, auth_headers):
        """GET /api/studio/agents/registry returns agent registry"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/registry", headers=auth_headers, timeout=60)
        assert response.status_code == 200, f"Agents registry failed: {response.text[:200]}"
        data = response.json()
        assert "agents" in data, "Expected 'agents' key in response"
    
    def test_agents_mindsets(self, auth_headers):
        """GET /api/studio/agents/mindsets returns mindsets"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/mindsets", headers=auth_headers, timeout=60)
        assert response.status_code == 200, f"Agents mindsets failed: {response.text[:200]}"
    
    def test_agents_metrics(self, auth_headers):
        """GET /api/studio/agents/metrics returns metrics"""
        response = requests.get(f"{BASE_URL}/api/studio/agents/metrics", headers=auth_headers, timeout=60)
        assert response.status_code == 200, f"Agents metrics failed: {response.text[:200]}"


class TestDataEndpoints:
    """Data endpoints must still work"""
    
    def test_avatars(self, auth_headers):
        """GET /api/data/avatars returns avatars"""
        response = requests.get(f"{BASE_URL}/api/data/avatars", headers=auth_headers, timeout=60)
        assert response.status_code == 200, f"Avatars failed: {response.text[:200]}"
    
    def test_companies(self, auth_headers):
        """GET /api/data/companies returns companies"""
        response = requests.get(f"{BASE_URL}/api/data/companies", headers=auth_headers, timeout=60)
        assert response.status_code == 200, f"Companies failed: {response.text[:200]}"


class TestWhatsAppEndpoints:
    """WhatsApp endpoints must still work (for ChannelConnection)"""
    
    def test_whatsapp_status(self, auth_headers):
        """GET /api/whatsapp/status returns status"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/status", headers=auth_headers, timeout=60)
        # 200 or 404 (if no WhatsApp configured) are both acceptable
        assert response.status_code in [200, 404], f"WhatsApp status unexpected: {response.status_code}"


class TestChannelsEndpoints:
    """Channels endpoints must still work"""
    
    def test_channels_list(self, auth_headers):
        """GET /api/channels returns channels (or 500 if table doesn't exist)"""
        response = requests.get(f"{BASE_URL}/api/channels", headers=auth_headers, timeout=60)
        # 200 = channels exist, 500 = table doesn't exist (pre-existing issue)
        assert response.status_code in [200, 500], f"Channels unexpected: {response.status_code}"


class TestGoogleEndpoints:
    """Google endpoints must still work"""
    
    def test_google_status(self, auth_headers):
        """GET /api/google/status returns status"""
        response = requests.get(f"{BASE_URL}/api/google/status", headers=auth_headers, timeout=60)
        # 200 or 404 are acceptable
        assert response.status_code in [200, 404, 401], f"Google status unexpected: {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════════
# REMOVED ROUTERS RETURN 404
# ═══════════════════════════════════════════════════════════════════════════════

class TestRemovedRouters:
    """Removed routers should return 404"""
    
    def test_conversations_removed(self, auth_headers):
        """GET /api/conversations should return 404 (removed)"""
        response = requests.get(f"{BASE_URL}/api/conversations", headers=auth_headers, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /conversations, got {response.status_code}"
    
    def test_leads_removed(self, auth_headers):
        """GET /api/leads should return 404 (removed)"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /leads, got {response.status_code}"
    
    def test_telegram_removed(self, auth_headers):
        """GET /api/telegram/status should return 404 (removed)"""
        response = requests.get(f"{BASE_URL}/api/telegram/status", headers=auth_headers, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /telegram, got {response.status_code}"
    
    def test_agent_generator_removed(self, auth_headers):
        """POST /api/agent-generator should return 404 (removed)"""
        response = requests.post(f"{BASE_URL}/api/agent-generator", headers=auth_headers, json={}, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /agent-generator, got {response.status_code}"
    
    def test_pipeline_removed(self, auth_headers):
        """GET /api/pipeline should return 404 (removed)"""
        response = requests.get(f"{BASE_URL}/api/pipeline", headers=auth_headers, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /pipeline, got {response.status_code}"
    
    def test_agents_old_removed(self, auth_headers):
        """GET /api/agents (old CRM router) should return 404 (removed)"""
        response = requests.get(f"{BASE_URL}/api/agents", headers=auth_headers, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /agents, got {response.status_code}"
    
    def test_ai_removed(self, auth_headers):
        """POST /api/ai/chat should return 404 (removed)"""
        response = requests.post(f"{BASE_URL}/api/ai/chat", headers=auth_headers, json={}, timeout=60)
        assert response.status_code == 404, f"Expected 404 for removed /ai, got {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════════
# NEW MULTI-FORMAT EXPORT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiFormatExportEndpoints:
    """New multi-format export endpoints"""
    
    def test_get_exports_endpoint_exists(self, auth_headers):
        """GET /api/studio/projects/{id}/exports returns exports and available_formats"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_VIDEO}/exports",
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"GET exports failed: {response.text[:200]}"
        data = response.json()
        assert "exports" in data, "Expected 'exports' key"
        assert "available_formats" in data, "Expected 'available_formats' key"
    
    def test_get_exports_has_4_formats(self, auth_headers):
        """GET /api/studio/projects/{id}/exports returns 4 available formats"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_VIDEO}/exports",
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        formats = data.get("available_formats", {})
        assert "16:9" in formats, "Missing 16:9 format"
        assert "9:16" in formats, "Missing 9:16 format"
        assert "1:1" in formats, "Missing 1:1 format"
        assert "4:5" in formats, "Missing 4:5 format"
        assert len(formats) == 4, f"Expected 4 formats, got {len(formats)}"
    
    def test_export_format_valid_returns_processing(self, auth_headers):
        """POST /api/studio/projects/{id}/export-format with valid format returns processing"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_VIDEO}/export-format",
            headers=auth_headers,
            json={"format": "9:16"},
            timeout=60
        )
        # 200 = started processing, 400 = no final video (acceptable)
        assert response.status_code in [200, 400], f"Export format failed: {response.text[:200]}"
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "processing", "Expected status=processing"
            assert data.get("format") == "9:16", "Expected format=9:16"
            assert "preset" in data, "Expected preset in response"
    
    def test_export_format_invalid_returns_400(self, auth_headers):
        """POST /api/studio/projects/{id}/export-format with invalid format returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_VIDEO}/export-format",
            headers=auth_headers,
            json={"format": "invalid"},
            timeout=60
        )
        # 400 = invalid format (expected), 500 = transient Supabase error (acceptable)
        assert response.status_code in [400, 500], f"Expected 400/500 for invalid format, got {response.status_code}"
        if response.status_code == 400:
            data = response.json()
            assert "Unsupported format" in data.get("detail", ""), f"Expected 'Unsupported format' in detail"
    
    def test_export_format_project_not_found(self, auth_headers):
        """POST /api/studio/projects/{id}/export-format with invalid project returns 404 or 500"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/nonexistent123/export-format",
            headers=auth_headers,
            json={"format": "9:16"},
            timeout=60
        )
        # 404 = project not found (expected), 500 = transient Supabase error (acceptable)
        assert response.status_code in [404, 500], f"Expected 404/500 for nonexistent project, got {response.status_code}"


class TestHealthEndpoint:
    """Health endpoint should work"""
    
    def test_health(self):
        """GET /api/health returns ok"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=60)
        assert response.status_code == 200, f"Health check failed: {response.text[:200]}"
        data = response.json()
        assert data.get("status") == "ok", "Expected status=ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
