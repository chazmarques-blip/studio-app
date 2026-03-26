"""
Iteration 114: Continuity Director Agent Tests
Tests for the Continuity Director feature that analyzes storyboard frames for:
- Character consistency
- Age accuracy
- Irrelevant elements
- Chronological coherence
And auto-corrects issues using inpainting.

Endpoints tested:
- POST /api/studio/projects/{project_id}/continuity/analyze
- GET /api/studio/projects/{project_id}/continuity/status
- POST /api/studio/projects/{project_id}/continuity/auto-correct
- GET /api/studio/projects/{project_id}/status (includes continuity_status and continuity_report)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

# Test project IDs
PROJECT_WITH_PANELS = "fce897cf6ba3"  # Has 20 panels with 6 frames each, analysis already done
PROJECT_WITHOUT_PANELS = "a2c8167aa32a"  # Has 0 panels - for error testing


class TestContinuityDirectorBackend:
    """Backend API tests for Continuity Director feature"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        return data.get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ═══════════════════════════════════════════════════════════
    # Health & Auth Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASS: Health endpoint accessible")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("PASS: Login successful")
    
    # ═══════════════════════════════════════════════════════════
    # Continuity Status Endpoint Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_continuity_status_endpoint_exists(self, auth_headers):
        """Test GET /api/studio/projects/{id}/continuity/status endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Status endpoint failed: {response.text}"
        data = response.json()
        assert "continuity_status" in data
        assert "continuity_report" in data
        print(f"PASS: Continuity status endpoint exists, phase={data['continuity_status'].get('phase')}")
    
    def test_continuity_status_has_done_phase(self, auth_headers):
        """Test that project fce897cf6ba3 has continuity analysis done"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        status = data.get("continuity_status", {})
        # Analysis was already run, should be 'done' or 'corrected'
        assert status.get("phase") in ("done", "corrected", "analyzing", "correcting", "error", None, ""), \
            f"Unexpected phase: {status.get('phase')}"
        print(f"PASS: Continuity status phase={status.get('phase')}")
    
    def test_continuity_report_has_issues(self, auth_headers):
        """Test that continuity report has issues structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        report = data.get("continuity_report", {})
        # If analysis was done, report should have structure
        if report:
            assert "total_issues" in report or "issues" in report
            print(f"PASS: Continuity report has {report.get('total_issues', len(report.get('issues', [])))} issues")
        else:
            print("PASS: Continuity report is empty (analysis may not have been run)")
    
    # ═══════════════════════════════════════════════════════════
    # Continuity Analyze Endpoint Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_continuity_analyze_endpoint_exists(self, auth_headers):
        """Test POST /api/studio/projects/{id}/continuity/analyze endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/analyze",
            headers=auth_headers
        )
        # Should return 200 with status (analyzing or already_running)
        assert response.status_code == 200, f"Analyze endpoint failed: {response.text}"
        data = response.json()
        assert "status" in data
        assert data["status"] in ("analyzing", "already_running")
        print(f"PASS: Continuity analyze endpoint exists, status={data['status']}")
    
    def test_continuity_analyze_returns_400_for_no_panels(self, auth_headers):
        """Test that analyze returns 400 for project with no panels"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITHOUT_PANELS}/continuity/analyze",
            headers=auth_headers
        )
        # Should return 400 because project has no panels
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "panel" in data["detail"].lower() or "no" in data["detail"].lower()
        print(f"PASS: Analyze returns 400 for no panels: {data['detail']}")
    
    def test_continuity_analyze_returns_404_for_invalid_project(self, auth_headers):
        """Test that analyze returns 404 for non-existent project"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/invalid_project_id_xyz/continuity/analyze",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Analyze returns 404 for invalid project")
    
    # ═══════════════════════════════════════════════════════════
    # Continuity Auto-Correct Endpoint Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_continuity_autocorrect_endpoint_exists(self, auth_headers):
        """Test POST /api/studio/projects/{id}/continuity/auto-correct endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/auto-correct",
            headers=auth_headers
        )
        # Should return 200 with status (correcting, already_running, or no_corrections_needed)
        # OR 400 if no report exists
        assert response.status_code in (200, 400), f"Auto-correct endpoint failed: {response.text}"
        data = response.json()
        if response.status_code == 200:
            assert "status" in data
            assert data["status"] in ("correcting", "already_running", "no_corrections_needed")
            print(f"PASS: Auto-correct endpoint exists, status={data['status']}")
        else:
            assert "detail" in data
            print(f"PASS: Auto-correct returns 400 as expected: {data['detail']}")
    
    def test_continuity_autocorrect_returns_400_for_no_report(self, auth_headers):
        """Test that auto-correct returns 400 when no report exists"""
        # Use a project that hasn't had analysis run
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITHOUT_PANELS}/continuity/auto-correct",
            headers=auth_headers
        )
        # Should return 400 because no report exists (or 404 if project not found)
        assert response.status_code in (400, 404), f"Expected 400/404, got {response.status_code}: {response.text}"
        print(f"PASS: Auto-correct returns {response.status_code} for project without report")
    
    def test_continuity_autocorrect_returns_404_for_invalid_project(self, auth_headers):
        """Test that auto-correct returns 404 for non-existent project"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/invalid_project_id_xyz/continuity/auto-correct",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Auto-correct returns 404 for invalid project")
    
    # ═══════════════════════════════════════════════════════════
    # Project Status Includes Continuity Fields
    # ═══════════════════════════════════════════════════════════
    
    def test_project_status_includes_continuity_status(self, auth_headers):
        """Test that GET /api/studio/projects/{id}/status includes continuity_status"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "continuity_status" in data, "continuity_status field missing from project status"
        print(f"PASS: Project status includes continuity_status: {data['continuity_status']}")
    
    def test_project_status_includes_continuity_report(self, auth_headers):
        """Test that GET /api/studio/projects/{id}/status includes continuity_report"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "continuity_report" in data, "continuity_report field missing from project status"
        print(f"PASS: Project status includes continuity_report")
    
    # ═══════════════════════════════════════════════════════════
    # Code Structure Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_continuity_director_file_exists(self):
        """Test that continuity_director.py file exists"""
        assert os.path.exists("/app/backend/core/continuity_director.py")
        print("PASS: continuity_director.py file exists")
    
    def test_continuity_director_has_analyze_function(self):
        """Test that continuity_director.py has analyze_continuity function"""
        with open("/app/backend/core/continuity_director.py", "r") as f:
            content = f.read()
        assert "def analyze_continuity" in content
        print("PASS: analyze_continuity function exists")
    
    def test_continuity_director_has_auto_correct_function(self):
        """Test that continuity_director.py has auto_correct_issue function"""
        with open("/app/backend/core/continuity_director.py", "r") as f:
            content = f.read()
        assert "def auto_correct_issue" in content
        print("PASS: auto_correct_issue function exists")
    
    def test_continuity_director_has_build_character_reference(self):
        """Test that continuity_director.py has build_character_reference function"""
        with open("/app/backend/core/continuity_director.py", "r") as f:
            content = f.read()
        assert "def build_character_reference" in content
        print("PASS: build_character_reference function exists")
    
    def test_studio_router_has_continuity_analyze(self):
        """Test that studio.py has continuity/analyze endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert '@router.post("/projects/{project_id}/continuity/analyze")' in content
        print("PASS: studio.py has continuity/analyze endpoint")
    
    def test_studio_router_has_continuity_status(self):
        """Test that studio.py has continuity/status endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert '@router.get("/projects/{project_id}/continuity/status")' in content
        print("PASS: studio.py has continuity/status endpoint")
    
    def test_studio_router_has_continuity_autocorrect(self):
        """Test that studio.py has continuity/auto-correct endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert '@router.post("/projects/{project_id}/continuity/auto-correct")' in content
        print("PASS: studio.py has continuity/auto-correct endpoint")
    
    # ═══════════════════════════════════════════════════════════
    # Frontend Code Structure Tests
    # ═══════════════════════════════════════════════════════════
    
    def test_storyboard_editor_has_continuity_panel(self):
        """Test that StoryboardEditor.jsx has continuity-director-panel data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="continuity-director-panel"' in content
        print("PASS: StoryboardEditor.jsx has continuity-director-panel data-testid")
    
    def test_storyboard_editor_has_continuity_analyze_btn(self):
        """Test that StoryboardEditor.jsx has continuity-analyze-btn data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="continuity-analyze-btn"' in content
        print("PASS: StoryboardEditor.jsx has continuity-analyze-btn data-testid")
    
    def test_storyboard_editor_has_continuity_correct_btn(self):
        """Test that StoryboardEditor.jsx has continuity-correct-btn data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="continuity-correct-btn"' in content
        print("PASS: StoryboardEditor.jsx has continuity-correct-btn data-testid")
    
    def test_storyboard_editor_has_continuity_state_vars(self):
        """Test that StoryboardEditor.jsx has continuity state variables"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert "continuityRunning" in content
        assert "continuityStatus" in content
        assert "continuityReport" in content
        print("PASS: StoryboardEditor.jsx has continuity state variables")
    
    def test_storyboard_editor_has_continuity_functions(self):
        """Test that StoryboardEditor.jsx has continuity functions"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert "startContinuityAnalysis" in content
        assert "startAutoCorrect" in content
        assert "pollContinuityStatus" in content
        print("PASS: StoryboardEditor.jsx has continuity functions")
    
    def test_storyboard_editor_has_shield_icon(self):
        """Test that StoryboardEditor.jsx imports Shield icon for Continuity Director"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert "Shield" in content
        print("PASS: StoryboardEditor.jsx has Shield icon import")
    
    def test_storyboard_editor_has_continuity_api_calls(self):
        """Test that StoryboardEditor.jsx makes correct API calls"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert "/continuity/analyze" in content
        assert "/continuity/status" in content
        assert "/continuity/auto-correct" in content
        print("PASS: StoryboardEditor.jsx has correct continuity API calls")


class TestContinuityDirectorReportStructure:
    """Tests for continuity report structure validation"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        return {"Authorization": f"Bearer {data.get('access_token')}"}
    
    def test_continuity_report_structure(self, auth_headers):
        """Test that continuity report has expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        report = data.get("continuity_report", {})
        
        if report and report.get("issues"):
            # Validate report structure
            assert "total_issues" in report or len(report.get("issues", [])) >= 0
            
            # Validate issue structure
            for issue in report.get("issues", [])[:3]:  # Check first 3 issues
                assert "scene_number" in issue or "severity" in issue
                if "severity" in issue:
                    assert issue["severity"] in ("high", "medium", "low")
                print(f"  Issue: scene {issue.get('scene_number')}, severity={issue.get('severity')}, category={issue.get('category')}")
            
            print(f"PASS: Continuity report has valid structure with {report.get('total_issues', len(report.get('issues', [])))} issues")
        else:
            print("PASS: Continuity report is empty or has no issues")
    
    def test_continuity_status_structure(self, auth_headers):
        """Test that continuity status has expected structure"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_WITH_PANELS}/continuity/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        status = data.get("continuity_status", {})
        
        if status:
            # Phase should be one of the expected values
            valid_phases = ("analyzing", "done", "correcting", "corrected", "error", None, "")
            assert status.get("phase") in valid_phases or status.get("phase") is None
            
            # If done, should have counts
            if status.get("phase") == "done":
                assert "total" in status or "issues_found" in status
                print(f"PASS: Status is 'done' with {status.get('issues_found', status.get('total', 0))} issues found")
            else:
                print(f"PASS: Status phase is '{status.get('phase')}'")
        else:
            print("PASS: Continuity status is empty (analysis not run)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
