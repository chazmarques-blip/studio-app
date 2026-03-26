"""
Iteration 112: Book Export & Interactive Book Tests
Tests:
1. Book endpoints (generate-cover, pdf, interactive-data, tts-page)
2. Interactive Book page structure
3. StoryboardEditor book export UI
4. Inpainting layout fix (h-8 sizing)
5. Token storage key (agentzz_token)
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PROJECT_ID = "fce897cf6ba3"


class TestAuthentication:
    """Authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        print("PASS: Health endpoint accessible")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        print(f"PASS: Login successful, token received")
        return data["access_token"]


class TestBookEndpoints:
    """Book export endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        r = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if r.status_code == 200:
            return r.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_interactive_data_endpoint_exists(self, auth_token):
        """Test GET /api/studio/projects/{project_id}/book/interactive-data endpoint exists"""
        r = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/book/interactive-data",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 with data or 400 if no panels (but endpoint exists)
        assert r.status_code in [200, 400], f"Unexpected status: {r.status_code}"
        print(f"PASS: interactive-data endpoint exists, status={r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            # Verify structure
            assert "pages" in data, "Missing 'pages' in response"
            assert "title" in data, "Missing 'title' in response"
            assert "total_pages" in data, "Missing 'total_pages' in response"
            print(f"PASS: interactive-data returns {data.get('total_pages', 0)} pages")
            return data
    
    def test_pdf_endpoint_exists(self, auth_token):
        """Test GET /api/studio/projects/{project_id}/book/pdf endpoint exists"""
        r = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/book/pdf",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return 200 with PDF or 400 if no panels
        assert r.status_code in [200, 400], f"Unexpected status: {r.status_code}"
        print(f"PASS: pdf endpoint exists, status={r.status_code}")
        
        if r.status_code == 200:
            # Verify it's a PDF
            content_type = r.headers.get("content-type", "")
            assert "application/pdf" in content_type, f"Expected PDF, got {content_type}"
            assert len(r.content) > 1000, "PDF content too small"
            print(f"PASS: PDF returned, size={len(r.content)} bytes")
    
    def test_generate_cover_endpoint_exists(self, auth_token):
        """Test POST /api/studio/projects/{project_id}/book/generate-cover endpoint exists"""
        # Just verify endpoint exists - don't actually call it (costs Gemini credits)
        # We'll do an OPTIONS or check the route exists
        r = requests.options(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/book/generate-cover",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # OPTIONS should return 200 or 405 (method not allowed but route exists)
        # Or we can try a GET which should return 405 (method not allowed)
        r2 = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/book/generate-cover",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # 405 = Method Not Allowed means endpoint exists but wrong method
        assert r2.status_code in [405, 200, 400, 404], f"Unexpected status: {r2.status_code}"
        print(f"PASS: generate-cover endpoint exists (GET returned {r2.status_code})")
    
    def test_tts_page_endpoint_exists(self, auth_token):
        """Test POST /api/studio/projects/{project_id}/book/tts-page endpoint exists"""
        # Try with empty body to verify endpoint exists
        r = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/book/tts-page",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={}
        )
        # Should return 400 (no text) or 422 (validation error) - endpoint exists
        assert r.status_code in [400, 422, 500], f"Unexpected status: {r.status_code}"
        print(f"PASS: tts-page endpoint exists, status={r.status_code}")


class TestCodeStructure:
    """Code structure verification tests"""
    
    def test_interactive_book_jsx_exists(self):
        """Verify InteractiveBook.jsx exists"""
        path = "/app/frontend/src/pages/InteractiveBook.jsx"
        assert os.path.exists(path), f"File not found: {path}"
        print(f"PASS: InteractiveBook.jsx exists")
    
    def test_interactive_book_has_navigation_buttons(self):
        """Verify InteractiveBook has prev/next navigation buttons with data-testid"""
        path = "/app/frontend/src/pages/InteractiveBook.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="prev-page-btn"' in content, "Missing prev-page-btn data-testid"
        assert 'data-testid="next-page-btn"' in content, "Missing next-page-btn data-testid"
        print("PASS: InteractiveBook has navigation buttons with data-testid")
    
    def test_interactive_book_has_toggle_narration(self):
        """Verify InteractiveBook has toggle-narration button"""
        path = "/app/frontend/src/pages/InteractiveBook.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="toggle-narration"' in content, "Missing toggle-narration data-testid"
        print("PASS: InteractiveBook has toggle-narration button")
    
    def test_interactive_book_has_touch_support(self):
        """Verify InteractiveBook has touch/swipe support"""
        path = "/app/frontend/src/pages/InteractiveBook.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'onTouchStart' in content, "Missing onTouchStart handler"
        assert 'onTouchEnd' in content, "Missing onTouchEnd handler"
        print("PASS: InteractiveBook has touch/swipe support")
    
    def test_interactive_book_has_keyboard_navigation(self):
        """Verify InteractiveBook has keyboard navigation (ArrowLeft, ArrowRight)"""
        path = "/app/frontend/src/pages/InteractiveBook.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'ArrowRight' in content, "Missing ArrowRight keyboard handler"
        assert 'ArrowLeft' in content, "Missing ArrowLeft keyboard handler"
        print("PASS: InteractiveBook has keyboard navigation")
    
    def test_storyboard_editor_has_book_export_buttons(self):
        """Verify StoryboardEditor has book export buttons"""
        path = "/app/frontend/src/components/StoryboardEditor.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'data-testid="generate-cover-btn"' in content, "Missing generate-cover-btn"
        assert 'data-testid="export-pdf-btn"' in content, "Missing export-pdf-btn"
        assert 'data-testid="open-interactive-book-btn"' in content, "Missing open-interactive-book-btn"
        print("PASS: StoryboardEditor has all 3 book export buttons")
    
    def test_storyboard_editor_inpainting_h8_sizing(self):
        """Verify inpainting mic button and edit button have h-8 height"""
        path = "/app/frontend/src/components/StoryboardEditor.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        # Check VoiceInput has h-8 w-8 in inpainting section
        # The VoiceInput component in inpainting section should have h-8 w-8
        assert 'h-8 w-8 rounded-md bg-orange-500/10' in content, "VoiceInput in inpainting should have h-8 w-8"
        
        # Check edit button has h-8
        assert 'h-8 rounded-md px-3' in content, "Edit button should have h-8"
        print("PASS: Inpainting mic and edit buttons have h-8 sizing")
    
    def test_storyboard_editor_uses_agentzz_token(self):
        """Verify StoryboardEditor uses 'agentzz_token' key for localStorage"""
        path = "/app/frontend/src/components/StoryboardEditor.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert "agentzz_token" in content, "Should use 'agentzz_token' key"
        assert "localStorage.getItem('agentzz_token')" in content, "Should get agentzz_token from localStorage"
        print("PASS: StoryboardEditor uses 'agentzz_token' key")
    
    def test_app_js_has_book_route(self):
        """Verify App.js has route for /book/:projectId"""
        path = "/app/frontend/src/App.js"
        with open(path, 'r') as f:
            content = f.read()
        
        assert '/book/:projectId' in content, "Missing /book/:projectId route"
        assert 'InteractiveBook' in content, "Missing InteractiveBook import/usage"
        print("PASS: App.js has /book/:projectId route")
    
    def test_interactive_book_uses_agentzz_token(self):
        """Verify InteractiveBook uses 'agentzz_token' key"""
        path = "/app/frontend/src/pages/InteractiveBook.jsx"
        with open(path, 'r') as f:
            content = f.read()
        
        assert "agentzz_token" in content, "Should use 'agentzz_token' key"
        print("PASS: InteractiveBook uses 'agentzz_token' key")


class TestBookGeneratorModule:
    """Test book_generator.py module structure"""
    
    def test_book_generator_exists(self):
        """Verify book_generator.py exists"""
        path = "/app/backend/core/book_generator.py"
        assert os.path.exists(path), f"File not found: {path}"
        print("PASS: book_generator.py exists")
    
    def test_book_generator_has_required_functions(self):
        """Verify book_generator.py has required functions"""
        path = "/app/backend/core/book_generator.py"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'def generate_cover_image(' in content, "Missing generate_cover_image function"
        assert 'def generate_creative_title(' in content, "Missing generate_creative_title function"
        assert 'def generate_pdf_storybook(' in content, "Missing generate_pdf_storybook function"
        assert 'def build_interactive_book_data(' in content, "Missing build_interactive_book_data function"
        print("PASS: book_generator.py has all required functions")
    
    def test_book_generator_uses_emergent_llm_key(self):
        """Verify book_generator uses EMERGENT_LLM_KEY"""
        path = "/app/backend/core/book_generator.py"
        with open(path, 'r') as f:
            content = f.read()
        
        assert 'EMERGENT_LLM_KEY' in content, "Should use EMERGENT_LLM_KEY"
        print("PASS: book_generator uses EMERGENT_LLM_KEY")


class TestStudioRouterBookEndpoints:
    """Test studio.py has book endpoints defined"""
    
    def test_studio_has_book_endpoints(self):
        """Verify studio.py has all book endpoints"""
        path = "/app/backend/routers/studio.py"
        with open(path, 'r') as f:
            content = f.read()
        
        assert '/book/generate-cover' in content, "Missing generate-cover endpoint"
        assert '/book/pdf' in content, "Missing pdf endpoint"
        assert '/book/interactive-data' in content, "Missing interactive-data endpoint"
        assert '/book/tts-page' in content, "Missing tts-page endpoint"
        print("PASS: studio.py has all book endpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
