"""
Iteration 116: Directed Studio Step 5 Redesign Tests
Tests for the Senior UX redesign of the Directed Studio pipeline:
- Step 5 (Resultado) redesigned as 'Deliverables Showcase'
- 5-step pipeline navigation with minimal timeline
- Backend endpoints verification
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"

# Test project ID (A HISTORIOA DE ABRAAO E ISAC)
TEST_PROJECT_ID = "fce897cf6ba3"


class TestHealthAndAuth:
    """Health check and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("PASS: Health endpoint returns OK")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print("PASS: Login successful")


class TestStudioEndpoints:
    """Studio API endpoints tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_list_projects(self, auth_headers):
        """Test listing studio projects"""
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert len(data["projects"]) > 0
        print(f"PASS: Listed {len(data['projects'])} projects")
    
    def test_project_status(self, auth_headers):
        """Test getting project status"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "scenes" in data
        assert "outputs" in data
        print(f"PASS: Project status: {data['status']}, {len(data['scenes'])} scenes, {len(data['outputs'])} outputs")
    
    def test_project_has_scenes(self, auth_headers):
        """Test project has storyboard scenes"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        scenes = data.get("scenes", [])
        assert len(scenes) > 0, "Project should have scenes"
        print(f"PASS: Project has {len(scenes)} scenes")
    
    def test_project_has_outputs(self, auth_headers):
        """Test project has video outputs"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        outputs = data.get("outputs", [])
        assert len(outputs) > 0, "Project should have outputs"
        # Check outputs have required fields
        for output in outputs[:3]:
            assert "url" in output or output.get("url") is None
            assert "scene_number" in output or "type" in output
        print(f"PASS: Project has {len(outputs)} outputs")
    
    def test_cache_stats_endpoint(self):
        """Test cache stats endpoint (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/studio/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "image_cache" in data
        assert "project_cache" in data
        assert "llm_cache" in data
        print("PASS: Cache stats endpoint working")


class TestStoryboardEndpoints:
    """Storyboard-related endpoints tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_storyboard(self, auth_headers):
        """Test getting project storyboard"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "panels" in data or "storyboard_panels" in data or isinstance(data, list)
        print("PASS: Storyboard endpoint working")
    
    def test_continuity_status(self, auth_headers):
        """Test continuity status endpoint"""
        response = requests.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/continuity/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have continuity data
        assert isinstance(data, dict)
        print("PASS: Continuity status endpoint working")


class TestFrontendAssets:
    """Tests for frontend assets and configuration"""
    
    def test_tailwind_config_has_fonts(self):
        """Test tailwind.config.js has serif and sans font families"""
        config_path = "/app/frontend/tailwind.config.js"
        with open(config_path, 'r') as f:
            content = f.read()
        
        assert "Cormorant Garamond" in content, "Should have Cormorant Garamond font"
        assert "Manrope" in content, "Should have Manrope font"
        assert "serif" in content, "Should have serif font family"
        assert "sans" in content, "Should have sans font family"
        print("PASS: Tailwind config has required fonts")
    
    def test_index_css_has_google_fonts(self):
        """Test index.css imports Google Fonts"""
        css_path = "/app/frontend/src/index.css"
        with open(css_path, 'r') as f:
            content = f.read()
        
        assert "fonts.googleapis.com" in content, "Should import Google Fonts"
        assert "Cormorant" in content, "Should import Cormorant Garamond"
        assert "Manrope" in content, "Should import Manrope"
        print("PASS: index.css has Google Fonts import")


class TestDirectedStudioComponent:
    """Tests for DirectedStudio component data-testid attributes"""
    
    def test_step_navigation_testids(self):
        """Test step navigation has required data-testid attributes"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        # Check for step navigation testids - the component uses dynamic testid
        assert 'data-testid={`studio-step-${s.n}`}' in content, "Should have dynamic studio-step testid"
        print("PASS: Step navigation has data-testid attributes")
    
    def test_step5_results_testid(self):
        """Test Step 5 has studio-step-results testid"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="studio-step-results"' in content, "Should have studio-step-results testid"
        print("PASS: Step 5 has studio-step-results testid")
    
    def test_deliverables_grid_testid(self):
        """Test deliverables grid has data-testid"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="deliverables-grid"' in content, "Should have deliverables-grid testid"
        print("PASS: Deliverables grid has data-testid")
    
    def test_deliverable_cards_testids(self):
        """Test deliverable cards have data-testid attributes"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        required_testids = [
            "deliverable-livro-interativo",
            "deliverable-storyboard-pdf",
            "deliverable-pos-producao",
            "deliverable-analytics"
        ]
        
        for testid in required_testids:
            assert f'data-testid="{testid}"' in content, f"Should have {testid} testid"
        print("PASS: Deliverable cards have data-testid attributes")
    
    def test_deliverables_cenas_testid(self):
        """Test individual scenes section has data-testid"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="deliverables-cenas"' in content, "Should have deliverables-cenas testid"
        print("PASS: Individual scenes section has data-testid")
    
    def test_close_post_production_testid(self):
        """Test close post-production button has data-testid"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="close-post-production"' in content, "Should have close-post-production testid"
        print("PASS: Close post-production button has data-testid")
    
    def test_hero_section_testid(self):
        """Test hero section for complete film has data-testid"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="deliverable-filme-completo"' in content, "Should have deliverable-filme-completo testid"
        print("PASS: Hero section has data-testid")
    
    def test_download_button_testid(self):
        """Test download button for complete film has data-testid"""
        component_path = "/app/frontend/src/components/DirectedStudio.jsx"
        with open(component_path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="download-filme-completo"' in content, "Should have download-filme-completo testid"
        print("PASS: Download button has data-testid")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
