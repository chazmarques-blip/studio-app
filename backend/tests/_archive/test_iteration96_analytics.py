"""
Iteration 96: Testing Performance Analytics Endpoint
- GET /api/studio/analytics/performance returns valid JSON with summary, timing, pipeline_versions, cost_estimate, productions, recommendations
- Verify analytics data structure and values
- Verify existing studio endpoints still work (projects, start-production, delete)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAnalyticsEndpoint:
    """Test the new Performance Analytics endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_analytics_endpoint_returns_valid_json(self):
        """GET /api/studio/analytics/performance returns valid JSON structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200, f"Analytics endpoint failed: {response.text}"
        data = response.json()
        
        # Verify top-level keys exist
        assert "summary" in data, "Missing 'summary' key"
        assert "timing" in data, "Missing 'timing' key"
        assert "pipeline_versions" in data, "Missing 'pipeline_versions' key"
        assert "cost_estimate" in data, "Missing 'cost_estimate' key"
        assert "productions" in data, "Missing 'productions' key"
        assert "recommendations" in data, "Missing 'recommendations' key"
        print(f"PASS: Analytics endpoint returns valid JSON with all required keys")
    
    def test_analytics_summary_structure(self):
        """Verify summary contains correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        summary = response.json().get("summary", {})
        
        # Verify summary fields
        assert "total_projects" in summary, "Missing 'total_projects' in summary"
        assert "completed" in summary, "Missing 'completed' in summary"
        assert "errored" in summary, "Missing 'errored' in summary"
        assert "total_scenes_produced" in summary, "Missing 'total_scenes_produced' in summary"
        assert "total_videos_generated" in summary, "Missing 'total_videos_generated' in summary"
        
        # Verify data types
        assert isinstance(summary["total_projects"], int)
        assert isinstance(summary["completed"], int)
        assert isinstance(summary["errored"], int)
        assert isinstance(summary["total_scenes_produced"], int)
        assert isinstance(summary["total_videos_generated"], int)
        
        print(f"PASS: Summary structure valid - completed={summary['completed']}, scenes={summary['total_scenes_produced']}, videos={summary['total_videos_generated']}")
    
    def test_analytics_timing_structure(self):
        """Verify timing contains correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        timing = response.json().get("timing", {})
        
        # Verify timing fields
        assert "avg_agent_seconds" in timing, "Missing 'avg_agent_seconds' in timing"
        assert "avg_video_seconds" in timing, "Missing 'avg_video_seconds' in timing"
        assert "avg_total_seconds" in timing, "Missing 'avg_total_seconds' in timing"
        assert "min_total_seconds" in timing, "Missing 'min_total_seconds' in timing"
        assert "max_total_seconds" in timing, "Missing 'max_total_seconds' in timing"
        assert "avg_scenes_per_project" in timing, "Missing 'avg_scenes_per_project' in timing"
        
        print(f"PASS: Timing structure valid - avg_total={timing['avg_total_seconds']}s")
    
    def test_analytics_pipeline_versions_structure(self):
        """Verify pipeline_versions contains v1, v2, v3 counts"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        versions = response.json().get("pipeline_versions", {})
        
        # Verify pipeline version fields
        assert "v1_sequential" in versions, "Missing 'v1_sequential' in pipeline_versions"
        assert "v2_batched" in versions, "Missing 'v2_batched' in pipeline_versions"
        assert "v3_parallel_teams" in versions, "Missing 'v3_parallel_teams' in pipeline_versions"
        
        # Verify data types
        assert isinstance(versions["v1_sequential"], int)
        assert isinstance(versions["v2_batched"], int)
        assert isinstance(versions["v3_parallel_teams"], int)
        
        print(f"PASS: Pipeline versions - v1={versions['v1_sequential']}, v2={versions['v2_batched']}, v3={versions['v3_parallel_teams']}")
    
    def test_analytics_cost_estimate_structure(self):
        """Verify cost_estimate contains correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        cost = response.json().get("cost_estimate", {})
        
        # Verify cost estimate fields
        assert "claude_calls_total" in cost, "Missing 'claude_calls_total' in cost_estimate"
        assert "claude_tokens_est" in cost, "Missing 'claude_tokens_est' in cost_estimate"
        assert "sora2_videos" in cost, "Missing 'sora2_videos' in cost_estimate"
        assert "optimization_note" in cost, "Missing 'optimization_note' in cost_estimate"
        
        print(f"PASS: Cost estimate - claude_calls={cost['claude_calls_total']}, sora2_videos={cost['sora2_videos']}")
    
    def test_analytics_productions_is_list(self):
        """Verify productions is a list with correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        productions = response.json().get("productions", [])
        
        assert isinstance(productions, list), "productions should be a list"
        
        if len(productions) > 0:
            prod = productions[0]
            assert "project_id" in prod, "Missing 'project_id' in production"
            assert "name" in prod, "Missing 'name' in production"
            assert "scenes" in prod, "Missing 'scenes' in production"
            assert "videos" in prod, "Missing 'videos' in production"
            assert "pipeline_version" in prod, "Missing 'pipeline_version' in production"
            print(f"PASS: Productions list has {len(productions)} items with correct structure")
        else:
            print(f"PASS: Productions list is empty (no completed productions)")
    
    def test_analytics_recommendations_is_list(self):
        """Verify recommendations is a list with type and text"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        recommendations = response.json().get("recommendations", [])
        
        assert isinstance(recommendations, list), "recommendations should be a list"
        
        if len(recommendations) > 0:
            rec = recommendations[0]
            assert "type" in rec, "Missing 'type' in recommendation"
            assert "text" in rec, "Missing 'text' in recommendation"
            assert rec["type"] in ["critical", "warning", "info", "success"], f"Invalid recommendation type: {rec['type']}"
            print(f"PASS: Recommendations list has {len(recommendations)} items - first type: {rec['type']}")
        else:
            print(f"PASS: Recommendations list is empty")
    
    def test_analytics_data_values(self):
        """Verify analytics returns correct data values (completed=1, scenes=2, v2_batched=1)"""
        response = requests.get(
            f"{BASE_URL}/api/studio/analytics/performance",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Based on context: completed=1, total_scenes_produced=2, v2_batched=1
        summary = data.get("summary", {})
        versions = data.get("pipeline_versions", {})
        
        # Verify expected values (from previous test context)
        assert summary.get("completed") >= 1, f"Expected at least 1 completed, got {summary.get('completed')}"
        assert summary.get("total_scenes_produced") >= 2, f"Expected at least 2 scenes, got {summary.get('total_scenes_produced')}"
        assert versions.get("v2_batched") >= 1, f"Expected at least 1 v2_batched, got {versions.get('v2_batched')}"
        
        print(f"PASS: Analytics data values correct - completed={summary.get('completed')}, scenes={summary.get('total_scenes_produced')}, v2_batched={versions.get('v2_batched')}")


class TestExistingStudioEndpoints:
    """Verify existing studio endpoints still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_projects_still_works(self):
        """GET /api/studio/projects returns projects list"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers
        )
        assert response.status_code == 200, f"GET projects failed: {response.text}"
        data = response.json()
        assert "projects" in data, "Missing 'projects' key"
        assert isinstance(data["projects"], list), "projects should be a list"
        print(f"PASS: GET /api/studio/projects returns {len(data['projects'])} projects")
    
    def test_start_production_validates_project(self):
        """POST /api/studio/start-production returns 404 for nonexistent project"""
        response = requests.post(
            f"{BASE_URL}/api/studio/start-production",
            headers=self.headers,
            json={"project_id": "nonexistent_test_123", "video_duration": 12}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: POST /api/studio/start-production returns 404 for nonexistent project")
    
    def test_delete_project_works(self):
        """DELETE /api/studio/projects/{id} returns ok status"""
        # Delete a test project (even if it doesn't exist, should return ok)
        response = requests.delete(
            f"{BASE_URL}/api/studio/projects/TEST_delete_test_123",
            headers=self.headers
        )
        assert response.status_code == 200, f"DELETE failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
        print(f"PASS: DELETE /api/studio/projects returns ok status")


class TestClaudeRetryLogicCodeReview:
    """Code review verification for Claude retry logic"""
    
    def test_call_claude_sync_has_5_retries(self):
        """Verify _call_claude_sync has 5 retries with exponential backoff"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        
        # Find _call_claude_sync function and verify it has 5 retries
        assert "def _call_claude_sync" in content, "_call_claude_sync function not found"
        
        # Find the sync function section and check for range(5)
        sync_start = content.find("def _call_claude_sync")
        sync_end = content.find("\ndef ", sync_start + 1)
        sync_func = content[sync_start:sync_end] if sync_end > sync_start else content[sync_start:]
        
        assert "for attempt in range(5)" in sync_func, f"Expected 'for attempt in range(5)' in _call_claude_sync"
        
        # Verify exponential backoff formula
        assert "wait = min(5 * (2 ** attempt), 60)" in sync_func, "Exponential backoff formula not found in _call_claude_sync"
        
        # Verify retryable error conditions
        assert '"502"' in sync_func or "'502'" in sync_func, "502 error not in retryable conditions"
        assert '"503"' in sync_func or "'503'" in sync_func, "503 error not in retryable conditions"
        assert '"529"' in sync_func or "'529'" in sync_func, "529 error not in retryable conditions"
        assert '"timeout"' in sync_func or "'timeout'" in sync_func, "timeout not in retryable conditions"
        assert '"overloaded"' in sync_func or "'overloaded'" in sync_func, "overloaded not in retryable conditions"
        
        print(f"PASS: _call_claude_sync has 5 retries with exponential backoff (wait = min(5 * 2^attempt, 60))")
    
    def test_call_claude_async_has_3_retries(self):
        """Verify _call_claude_async has 3 retries"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        
        # Find _call_claude_async function
        assert "async def _call_claude_async" in content, "_call_claude_async function not found"
        
        # Find the async function section and check for range(3)
        async_start = content.find("async def _call_claude_async")
        async_end = content.find("\ndef ", async_start + 1)
        async_func = content[async_start:async_end] if async_end > async_start else content[async_start:]
        
        assert "for attempt in range(3)" in async_func, f"Expected 'for attempt in range(3)' in _call_claude_async"
        
        print(f"PASS: _call_claude_async has 3 retries")
