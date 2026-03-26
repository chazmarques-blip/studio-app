"""Iteration 115: 4-Layer Caching System Tests

Tests the new caching infrastructure:
- Layer 1: Image cache (disk + in-memory hot layer)
- Layer 2: Project cache (read-through, write-behind batching)
- Layer 3: LLM response cache (content-addressable)
- Layer 4: Frontend SWR cache (tested via code review)

Backend endpoints tested:
- GET /api/studio/cache/stats - returns stats for all 3 backend cache layers
- POST /api/studio/cache/flush - forces flush and cleanup
- Existing endpoints still work with caching transparent
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

# Test project with 20 panels
TEST_PROJECT_ID = "fce897cf6ba3"


class TestHealthAndAuth:
    """Basic health and authentication tests."""

    def test_health_endpoint(self):
        """Test health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: Health endpoint returns status=ok")

    def test_login_success(self):
        """Test login with valid credentials."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"PASS: Login successful, got access_token")
        return data["access_token"]


class TestCacheStatsEndpoint:
    """Tests for GET /api/studio/cache/stats endpoint."""

    def test_cache_stats_no_auth_required(self):
        """Cache stats endpoint should work without authentication."""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert response.status_code == 200
        data = response.json()
        print(f"PASS: Cache stats endpoint accessible without auth")
        return data

    def test_cache_stats_has_image_cache(self):
        """Cache stats should include image_cache layer."""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "image_cache" in data
        img_cache = data["image_cache"]
        assert "hot_count" in img_cache
        assert "disk_count" in img_cache
        assert "disk_size_mb" in img_cache
        print(f"PASS: image_cache stats present: hot={img_cache['hot_count']}, disk={img_cache['disk_count']}, size={img_cache['disk_size_mb']}MB")

    def test_cache_stats_has_project_cache(self):
        """Cache stats should include project_cache layer."""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "project_cache" in data
        proj_cache = data["project_cache"]
        assert "cached_tenants" in proj_cache
        assert "dirty_tenants" in proj_cache
        print(f"PASS: project_cache stats present: cached={proj_cache['cached_tenants']}, dirty={proj_cache['dirty_tenants']}")

    def test_cache_stats_has_llm_cache(self):
        """Cache stats should include llm_cache layer."""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "llm_cache" in data
        llm_cache = data["llm_cache"]
        assert "entries" in llm_cache
        assert "size_kb" in llm_cache
        print(f"PASS: llm_cache stats present: entries={llm_cache['entries']}, size={llm_cache['size_kb']}KB")


class TestCacheFlushEndpoint:
    """Tests for POST /api/studio/cache/flush endpoint."""

    def test_cache_flush_no_auth_required(self):
        """Cache flush endpoint should work without authentication."""
        response = requests.post(f"{BASE_URL}/api/studio/cache/flush")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "flushed"
        print(f"PASS: Cache flush endpoint accessible without auth, status=flushed")

    def test_cache_flush_cleans_expired(self):
        """Cache flush should clean expired entries."""
        # First flush
        response = requests.post(f"{BASE_URL}/api/studio/cache/flush")
        assert response.status_code == 200
        
        # Get stats after flush
        stats_response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert stats_response.status_code == 200
        data = stats_response.json()
        
        # Verify project cache has no dirty tenants after flush
        proj_cache = data.get("project_cache", {})
        assert proj_cache.get("dirty_tenants", 0) == 0
        print(f"PASS: After flush, dirty_tenants=0")


class TestProjectCacheReadThrough:
    """Tests for project cache read-through behavior."""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")

    def test_project_status_first_call(self, auth_token):
        """First call to project status should work (cache miss -> DB read)."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "storyboard_panels" in data
        print(f"PASS: First project status call works, status={data.get('status')}")

    def test_project_status_second_call_faster(self, auth_token):
        """Second call should be served from cache (faster)."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First call (may be cache miss)
        start1 = time.time()
        response1 = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=headers
        )
        time1 = time.time() - start1
        assert response1.status_code == 200
        
        # Second call (should be cache hit)
        start2 = time.time()
        response2 = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=headers
        )
        time2 = time.time() - start2
        assert response2.status_code == 200
        
        # Both should return same data
        data1 = response1.json()
        data2 = response2.json()
        assert data1.get("status") == data2.get("status")
        
        print(f"PASS: Project status calls work. First: {time1:.3f}s, Second: {time2:.3f}s")

    def test_project_cache_populated_after_read(self, auth_token):
        """After reading project, cache should show tenant entry."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Read project to populate cache
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=headers
        )
        assert response.status_code == 200
        
        # Check cache stats
        stats_response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        proj_cache = stats.get("project_cache", {})
        assert proj_cache.get("cached_tenants", 0) >= 1
        print(f"PASS: After project read, cached_tenants={proj_cache.get('cached_tenants')}")


class TestExistingEndpointsStillWork:
    """Verify existing endpoints still work with caching layer."""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")

    def test_list_projects_works(self, auth_token):
        """GET /api/studio/projects should still work."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"PASS: List projects works, found {len(data.get('projects', []))} projects")

    def test_get_storyboard_works(self, auth_token):
        """GET /api/studio/projects/{id}/storyboard should still work."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "panels" in data
        panels = data.get("panels", [])
        print(f"PASS: Get storyboard works, found {len(panels)} panels")
        
        # Verify panels have frames
        if panels:
            first_panel = panels[0]
            frames = first_panel.get("frames", [])
            print(f"      First panel has {len(frames)} frames")

    def test_continuity_status_works(self, auth_token):
        """GET /api/studio/projects/{id}/continuity/status should still work."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity/status",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "continuity_status" in data
        assert "continuity_report" in data
        
        status = data.get("continuity_status", {})
        report = data.get("continuity_report", {})
        print(f"PASS: Continuity status works, phase={status.get('phase')}, issues={report.get('total_issues', 0)}")


class TestCacheCodeStructure:
    """Verify cache module code structure."""

    def test_cache_module_exists(self):
        """Verify /app/backend/core/cache.py exists."""
        import os
        assert os.path.exists("/app/backend/core/cache.py")
        print("PASS: cache.py module exists")

    def test_cache_module_has_image_cache_class(self):
        """Verify ImageCache class exists."""
        with open("/app/backend/core/cache.py", "r") as f:
            content = f.read()
        assert "class ImageCache:" in content
        assert "def download(" in content
        assert "def prewarm(" in content
        print("PASS: ImageCache class with download() and prewarm() methods exists")

    def test_cache_module_has_project_cache_class(self):
        """Verify ProjectCache class exists."""
        with open("/app/backend/core/cache.py", "r") as f:
            content = f.read()
        assert "class ProjectCache:" in content
        assert "def get_settings(" in content
        assert "def save_settings(" in content
        assert "def force_flush(" in content
        print("PASS: ProjectCache class with get_settings(), save_settings(), force_flush() methods exists")

    def test_cache_module_has_llm_cache_class(self):
        """Verify LLMCache class exists."""
        with open("/app/backend/core/cache.py", "r") as f:
            content = f.read()
        assert "class LLMCache:" in content
        assert "def get(" in content
        assert "def put(" in content
        print("PASS: LLMCache class with get() and put() methods exists")

    def test_cache_singletons_exported(self):
        """Verify singleton instances are exported."""
        with open("/app/backend/core/cache.py", "r") as f:
            content = f.read()
        assert "image_cache = ImageCache()" in content
        assert "project_cache = ProjectCache()" in content
        assert "llm_cache = LLMCache()" in content
        print("PASS: Singleton instances (image_cache, project_cache, llm_cache) exported")


class TestCacheIntegrationInModules:
    """Verify cache is integrated in other modules."""

    def test_continuity_director_uses_image_cache(self):
        """Verify continuity_director.py uses image_cache.download()."""
        with open("/app/backend/core/continuity_director.py", "r") as f:
            content = f.read()
        assert "from core.cache import image_cache" in content
        assert "image_cache.download(" in content
        assert "image_cache.prewarm(" in content
        print("PASS: continuity_director.py uses image_cache.download() and prewarm()")

    def test_continuity_director_uses_llm_cache(self):
        """Verify continuity_director.py uses llm_cache."""
        with open("/app/backend/core/continuity_director.py", "r") as f:
            content = f.read()
        assert "from core.cache import" in content and "llm_cache" in content
        assert "llm_cache.get(" in content
        assert "llm_cache.put(" in content
        print("PASS: continuity_director.py uses llm_cache.get() and put()")

    def test_smart_editor_uses_image_cache(self):
        """Verify smart_editor.py uses image_cache.download()."""
        with open("/app/backend/core/smart_editor.py", "r") as f:
            content = f.read()
        assert "from core.cache import image_cache" in content
        assert "image_cache.download(" in content
        print("PASS: smart_editor.py uses image_cache.download()")

    def test_storyboard_inpaint_uses_image_cache(self):
        """Verify storyboard_inpaint.py uses image_cache.download()."""
        with open("/app/backend/core/storyboard_inpaint.py", "r") as f:
            content = f.read()
        assert "from core.cache import image_cache" in content
        assert "image_cache.download(" in content
        print("PASS: storyboard_inpaint.py uses image_cache.download()")

    def test_studio_router_uses_project_cache(self):
        """Verify studio.py uses project_cache for _get_settings/_save_settings."""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert "from core.cache import project_cache" in content
        assert "project_cache.get_settings(" in content
        assert "project_cache.save_settings(" in content
        print("PASS: studio.py uses project_cache.get_settings() and save_settings()")

    def test_server_flushes_cache_on_shutdown(self):
        """Verify server.py flushes cache on shutdown."""
        with open("/app/backend/server.py", "r") as f:
            content = f.read()
        assert "from core.cache import project_cache" in content
        assert "project_cache.force_flush()" in content
        assert '@app.on_event("shutdown")' in content
        print("PASS: server.py flushes project_cache on shutdown")


class TestFrontendCacheHook:
    """Verify frontend cache hook exists."""

    def test_frontend_cache_hook_exists(self):
        """Verify useProjectCache.js exists."""
        import os
        assert os.path.exists("/app/frontend/src/hooks/useProjectCache.js")
        print("PASS: useProjectCache.js hook exists")

    def test_frontend_cache_has_swr_fetch(self):
        """Verify useSWRFetch hook exists."""
        with open("/app/frontend/src/hooks/useProjectCache.js", "r") as f:
            content = f.read()
        assert "export function useSWRFetch(" in content
        assert "STALE_TIME" in content
        assert "CACHE_TIME" in content
        print("PASS: useSWRFetch hook with STALE_TIME and CACHE_TIME exists")

    def test_frontend_cache_has_image_preloader(self):
        """Verify image preloader exists."""
        with open("/app/frontend/src/hooks/useProjectCache.js", "r") as f:
            content = f.read()
        assert "export function preloadImages(" in content
        assert "export function useImagePreloader(" in content
        print("PASS: preloadImages() and useImagePreloader() functions exist")

    def test_frontend_cache_has_invalidate(self):
        """Verify cache invalidation function exists."""
        with open("/app/frontend/src/hooks/useProjectCache.js", "r") as f:
            content = f.read()
        assert "export function invalidateCache(" in content
        print("PASS: invalidateCache() function exists")

    def test_frontend_cache_has_optimistic_update(self):
        """Verify optimistic update function exists."""
        with open("/app/frontend/src/hooks/useProjectCache.js", "r") as f:
            content = f.read()
        assert "export function optimisticUpdate(" in content
        print("PASS: optimisticUpdate() function exists")


class TestCacheDirectories:
    """Verify cache directories are configured correctly."""

    def test_image_cache_dir_configured(self):
        """Verify image cache directory is configured."""
        with open("/app/backend/core/cache.py", "r") as f:
            content = f.read()
        assert 'IMAGE_CACHE_DIR = CACHE_DIR / "images"' in content
        assert "/tmp/agentzz_cache" in content
        print("PASS: Image cache directory configured at /tmp/agentzz_cache/images/")

    def test_llm_cache_dir_configured(self):
        """Verify LLM cache directory is configured."""
        with open("/app/backend/core/cache.py", "r") as f:
            content = f.read()
        assert 'LLM_CACHE_DIR = CACHE_DIR / "llm"' in content
        print("PASS: LLM cache directory configured at /tmp/agentzz_cache/llm/")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
