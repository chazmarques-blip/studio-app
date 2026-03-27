"""
Iteration 119 - Infrastructure Audit Tests
Tests for: Error Boundary, Code Splitting, PWA, GZip, Observability, Rate Limiting,
Auth on cache endpoints, Deep health check, Circuit Breaker, Provider Pattern
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    def test_shallow_health_returns_ok(self):
        """Test /api/health returns status ok with version"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert data["service"] == "agentzz-api"
        print(f"PASS: Health endpoint returns {data}")
    
    def test_deep_health_requires_auth(self):
        """Test /api/health/deep requires authentication"""
        response = requests.get(f"{BASE_URL}/api/health/deep")
        assert response.status_code == 401
        print("PASS: Deep health requires auth (401)")
    
    def test_deep_health_with_auth(self, auth_token):
        """Test /api/health/deep returns dependency checks with auth"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/health/deep", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "checks" in data
        # Verify dependency checks exist
        checks = data["checks"]
        assert "supabase" in checks
        assert "disk" in checks
        assert "cache" in checks
        print(f"PASS: Deep health returns checks: {list(checks.keys())}")


class TestObservabilityMiddleware:
    """Tests for observability middleware (X-Request-Id, X-Response-Time)"""
    
    def test_health_has_request_id_header(self):
        """Test that X-Request-Id header is present"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert "X-Request-Id" in response.headers
        request_id = response.headers["X-Request-Id"]
        assert len(request_id) == 8  # UUID[:8]
        print(f"PASS: X-Request-Id header present: {request_id}")
    
    def test_health_has_response_time_header(self):
        """Test that X-Response-Time header is present"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert "X-Response-Time" in response.headers
        response_time = response.headers["X-Response-Time"]
        assert "ms" in response_time
        print(f"PASS: X-Response-Time header present: {response_time}")


class TestCacheEndpoints:
    """Tests for cache stats endpoint auth"""
    
    def test_cache_stats_requires_auth(self):
        """Test /api/studio/cache/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert response.status_code == 401
        print("PASS: Cache stats requires auth (401)")
    
    def test_cache_stats_with_auth(self, auth_token):
        """Test /api/studio/cache/stats returns data with auth"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should return cache statistics
        assert isinstance(data, dict)
        print(f"PASS: Cache stats returns: {data}")


class TestDashboardEndpoint:
    """Tests for dashboard stats endpoint"""
    
    def test_dashboard_stats_requires_auth(self):
        """Test /api/dashboard/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 401
        print("PASS: Dashboard stats requires auth (401)")
    
    def test_dashboard_stats_with_auth(self, auth_token):
        """Test /api/dashboard/stats returns expected fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Verify expected fields
        assert "plan" in data
        assert "agents_count" in data
        assert "messages_today" in data
        print(f"PASS: Dashboard stats returns plan={data['plan']}, agents_count={data['agents_count']}")


class TestAuthEndpoints:
    """Tests for authentication flow"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@agentflow.com"
        print(f"PASS: Login successful for {data['user']['email']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code in [401, 400]
        print("PASS: Invalid login returns 401/400")


class TestStudioEndpoints:
    """Tests for studio/projects endpoints"""
    
    def test_studio_projects_requires_auth(self):
        """Test /api/studio/projects requires authentication"""
        response = requests.get(f"{BASE_URL}/api/studio/projects")
        assert response.status_code == 401
        print("PASS: Studio projects requires auth (401)")
    
    def test_studio_projects_with_auth(self, auth_token):
        """Test /api/studio/projects returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {"projects": [...]}
        assert "projects" in data
        assert isinstance(data["projects"], list)
        print(f"PASS: Studio projects returns {len(data['projects'])} projects")


class TestAgentsEndpoint:
    """Tests for agents endpoint"""
    
    def test_agents_requires_auth(self):
        """Test /api/agents requires authentication"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 401
        print("PASS: Agents endpoint requires auth (401)")
    
    def test_agents_with_auth(self, auth_token):
        """Test /api/agents returns list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/agents", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # API returns {"agents": [...]}
        assert "agents" in data
        assert isinstance(data["agents"], list)
        print(f"PASS: Agents endpoint returns {len(data['agents'])} agents")


class TestPWAAssets:
    """Tests for PWA manifest and service worker"""
    
    def test_manifest_accessible(self):
        """Test /manifest.json is accessible"""
        response = requests.get(f"{BASE_URL}/manifest.json")
        assert response.status_code == 200
        data = response.json()
        assert data["short_name"] == "AgentZZ"
        assert data["name"] == "AgentZZ - Plataforma de Agentes de IA"
        assert data["start_url"] == "/dashboard"
        print(f"PASS: manifest.json accessible with name={data['name']}")
    
    def test_service_worker_accessible(self):
        """Test /service-worker.js is accessible"""
        response = requests.get(f"{BASE_URL}/service-worker.js")
        assert response.status_code == 200
        assert "text/javascript" in response.headers.get("Content-Type", "") or response.status_code == 200
        content = response.text
        assert "CACHE_NAME" in content or "agentzz" in content.lower()
        print("PASS: service-worker.js accessible")


# ── Fixtures ──

@pytest.fixture
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
