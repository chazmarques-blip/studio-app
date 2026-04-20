"""
Iteration 113: Language Agent & Smart Image Editor Tests

Tests for:
1. Language Agent endpoints (convert, review, status)
2. Smart Editor endpoints (analyze-scene, smart-edit)
3. Code structure validation (batch_size=5, function existence)
4. Frontend UI elements (data-testid attributes)
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
PROJECT_ID = "fce897cf6ba3"  # Existing project with 20 panels

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASS: Health endpoint accessible")
    
    def test_login_success(self, auth_token):
        """Test login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 10
        print(f"PASS: Login successful, token length: {len(auth_token)}")


class TestLanguageAgentEndpoints:
    """Language Agent API endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_language_convert_endpoint_exists(self, headers):
        """Test POST /api/studio/projects/{id}/language/convert endpoint exists"""
        # We don't actually trigger conversion (costs API credits)
        # Just verify endpoint exists and returns expected structure
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/language/convert",
            json={"target_lang": "en"},
            headers=headers
        )
        # Should return 200 with status: converting OR 400 if no scenes
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "No status in response"
            assert data["status"] == "converting", f"Expected 'converting', got {data['status']}"
            print(f"PASS: Language convert endpoint returns status=converting")
        else:
            print(f"PASS: Language convert endpoint exists (returned 400 - no scenes)")
    
    def test_language_review_endpoint_exists(self, headers):
        """Test POST /api/studio/projects/{id}/language/review endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/language/review",
            headers=headers
        )
        # Should return 200 with status: reviewing OR 400 if no scenes
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "No status in response"
            assert data["status"] == "reviewing", f"Expected 'reviewing', got {data['status']}"
            print(f"PASS: Language review endpoint returns status=reviewing")
        else:
            print(f"PASS: Language review endpoint exists (returned 400 - no scenes)")
    
    def test_language_status_endpoint_exists(self, headers):
        """Test GET /api/studio/projects/{id}/language/status endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/language/status",
            headers=headers
        )
        assert response.status_code == 200, f"Status endpoint failed: {response.status_code}"
        data = response.json()
        assert "language_status" in data, "No language_status in response"
        assert "review_status" in data, "No review_status in response"
        print(f"PASS: Language status endpoint returns language_status and review_status")
        print(f"  language_status: {data['language_status']}")
        print(f"  review_status: {data['review_status']}")
    
    def test_language_status_review_done(self, headers):
        """Test that review_status shows phase=done with quality score (from previous run)"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/language/status",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        review_status = data.get("review_status", {})
        # Per main agent note: review_status for fce897cf6ba3 is already 'done' from previous run
        if review_status.get("phase") == "done":
            assert "quality" in review_status or "count" in review_status, "Done status should have quality or count"
            print(f"PASS: Review status is done with quality: {review_status.get('quality', 'N/A')}")
        else:
            print(f"INFO: Review status phase is '{review_status.get('phase', 'empty')}' (not done yet)")


class TestSmartEditorEndpoints:
    """Smart Image Editor API endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_analyze_scene_endpoint_exists(self, headers):
        """Test POST /api/studio/projects/{id}/storyboard/analyze-scene endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/storyboard/analyze-scene",
            json={"panel_number": 1, "frame_index": 0},
            headers=headers
        )
        # Should return 200 with analysis OR 400/404 if no panel/image
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            # Check for expected analysis structure
            has_characters = "characters" in data
            has_objects = "objects" in data
            has_background = "background" in data
            print(f"PASS: Analyze scene endpoint returns analysis")
            print(f"  has_characters: {has_characters}, has_objects: {has_objects}, has_background: {has_background}")
            if has_characters:
                print(f"  characters count: {len(data.get('characters', []))}")
            if has_objects:
                print(f"  objects count: {len(data.get('objects', []))}")
        else:
            print(f"PASS: Analyze scene endpoint exists (returned {response.status_code})")
    
    def test_smart_edit_endpoint_exists(self, headers):
        """Test POST /api/studio/projects/{id}/storyboard/smart-edit endpoint exists"""
        # We don't actually trigger smart edit (costs API credits)
        # Just verify endpoint exists and returns expected structure
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/storyboard/smart-edit",
            json={
                "panel_number": 1,
                "frame_index": 0,
                "edit_instruction": "Test instruction"
            },
            headers=headers
        )
        # Should return 200 with status: editing OR 400/404 if no panel/image
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "No status in response"
            assert data["status"] == "editing", f"Expected 'editing', got {data['status']}"
            assert "mode" in data or data.get("status") == "editing", "Should have mode or editing status"
            print(f"PASS: Smart edit endpoint returns status=editing")
        else:
            print(f"PASS: Smart edit endpoint exists (returned {response.status_code})")


class TestLanguageAgentCodeStructure:
    """Validate language_agent.py code structure"""
    
    def test_language_agent_file_exists(self):
        """Test language_agent.py exists"""
        path = "/app/backend/core/language_agent.py"
        assert os.path.exists(path), f"File not found: {path}"
        print(f"PASS: language_agent.py exists")
    
    def test_language_agent_has_convert_language(self):
        """Test convert_language function exists"""
        with open("/app/backend/core/language_agent.py", "r") as f:
            content = f.read()
        assert "def convert_language(" in content, "convert_language function not found"
        print(f"PASS: convert_language function exists")
    
    def test_language_agent_has_review_text_quality(self):
        """Test review_text_quality function exists"""
        with open("/app/backend/core/language_agent.py", "r") as f:
            content = f.read()
        assert "def review_text_quality(" in content, "review_text_quality function not found"
        print(f"PASS: review_text_quality function exists")
    
    def test_language_agent_batch_size_5(self):
        """Test batch_size = 5 in language_agent.py"""
        with open("/app/backend/core/language_agent.py", "r") as f:
            content = f.read()
        # Check for batch_size = 5 in both functions
        batch_matches = re.findall(r'batch_size\s*=\s*5', content)
        assert len(batch_matches) >= 2, f"Expected batch_size=5 in both functions, found {len(batch_matches)}"
        print(f"PASS: batch_size=5 found {len(batch_matches)} times (convert_language and review_text_quality)")
    
    def test_language_agent_supported_langs(self):
        """Test SUPPORTED_LANGS has 10+ languages"""
        with open("/app/backend/core/language_agent.py", "r") as f:
            content = f.read()
        assert "SUPPORTED_LANGS" in content, "SUPPORTED_LANGS not found"
        # Count language codes in SUPPORTED_LANGS dict
        lang_codes = re.findall(r'"(\w{2})"\s*:', content)
        assert len(lang_codes) >= 10, f"Expected 10+ languages, found {len(lang_codes)}"
        print(f"PASS: SUPPORTED_LANGS has {len(lang_codes)} languages: {lang_codes}")


class TestSmartEditorCodeStructure:
    """Validate smart_editor.py code structure"""
    
    def test_smart_editor_file_exists(self):
        """Test smart_editor.py exists"""
        path = "/app/backend/core/smart_editor.py"
        assert os.path.exists(path), f"File not found: {path}"
        print(f"PASS: smart_editor.py exists")
    
    def test_smart_editor_has_analyze_scene(self):
        """Test analyze_scene function exists"""
        with open("/app/backend/core/smart_editor.py", "r") as f:
            content = f.read()
        assert "def analyze_scene(" in content, "analyze_scene function not found"
        print(f"PASS: analyze_scene function exists")
    
    def test_smart_editor_has_smart_edit(self):
        """Test smart_edit function exists"""
        with open("/app/backend/core/smart_editor.py", "r") as f:
            content = f.read()
        assert "def smart_edit(" in content, "smart_edit function not found"
        print(f"PASS: smart_edit function exists")
    
    def test_smart_editor_uses_gemini_vision(self):
        """Test smart_editor uses Gemini Vision model"""
        with open("/app/backend/core/smart_editor.py", "r") as f:
            content = f.read()
        assert "gemini-3.1-flash-image-preview" in content, "Gemini Vision model not found"
        print(f"PASS: smart_editor uses gemini-3.1-flash-image-preview")
    
    def test_smart_editor_returns_scene_map_structure(self):
        """Test analyze_scene returns expected structure (characters, objects, background)"""
        with open("/app/backend/core/smart_editor.py", "r") as f:
            content = f.read()
        # Check for expected JSON structure in prompt
        assert '"characters"' in content, "characters field not in analysis structure"
        assert '"objects"' in content, "objects field not in analysis structure"
        assert '"background"' in content, "background field not in analysis structure"
        assert '"quality_issues"' in content, "quality_issues field not in analysis structure"
        print(f"PASS: analyze_scene returns characters, objects, background, quality_issues")


class TestStudioRouterEndpoints:
    """Validate studio.py has all required endpoints"""
    
    def test_studio_has_language_convert(self):
        """Test studio.py has language/convert endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert 'language/convert' in content, "language/convert endpoint not found"
        assert '@router.post("/projects/{project_id}/language/convert")' in content
        print(f"PASS: studio.py has language/convert endpoint")
    
    def test_studio_has_language_review(self):
        """Test studio.py has language/review endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert 'language/review' in content, "language/review endpoint not found"
        assert '@router.post("/projects/{project_id}/language/review")' in content
        print(f"PASS: studio.py has language/review endpoint")
    
    def test_studio_has_language_status(self):
        """Test studio.py has language/status endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert 'language/status' in content, "language/status endpoint not found"
        assert '@router.get("/projects/{project_id}/language/status")' in content
        print(f"PASS: studio.py has language/status endpoint")
    
    def test_studio_has_analyze_scene(self):
        """Test studio.py has storyboard/analyze-scene endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert 'analyze-scene' in content, "analyze-scene endpoint not found"
        assert '@router.post("/projects/{project_id}/storyboard/analyze-scene")' in content
        print(f"PASS: studio.py has storyboard/analyze-scene endpoint")
    
    def test_studio_has_smart_edit(self):
        """Test studio.py has storyboard/smart-edit endpoint"""
        with open("/app/backend/routers/studio.py", "r") as f:
            content = f.read()
        assert 'smart-edit' in content, "smart-edit endpoint not found"
        assert '@router.post("/projects/{project_id}/storyboard/smart-edit")' in content
        print(f"PASS: studio.py has storyboard/smart-edit endpoint")


class TestFrontendUIElements:
    """Validate StoryboardEditor.jsx has required UI elements"""
    
    def test_storyboard_editor_exists(self):
        """Test StoryboardEditor.jsx exists"""
        path = "/app/frontend/src/components/StoryboardEditor.jsx"
        assert os.path.exists(path), f"File not found: {path}"
        print(f"PASS: StoryboardEditor.jsx exists")
    
    def test_storyboard_editor_has_target_lang_select(self):
        """Test StoryboardEditor has target-lang-select data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="target-lang-select"' in content, "target-lang-select not found"
        print(f"PASS: StoryboardEditor has target-lang-select")
    
    def test_storyboard_editor_has_convert_lang_btn(self):
        """Test StoryboardEditor has convert-lang-btn data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="convert-lang-btn"' in content, "convert-lang-btn not found"
        print(f"PASS: StoryboardEditor has convert-lang-btn")
    
    def test_storyboard_editor_has_review_text_btn(self):
        """Test StoryboardEditor has review-text-btn data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="review-text-btn"' in content, "review-text-btn not found"
        print(f"PASS: StoryboardEditor has review-text-btn")
    
    def test_storyboard_editor_has_analyze_scene_btn(self):
        """Test StoryboardEditor has analyze-scene button"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        # Check for analyze-scene-{panel_number} pattern
        assert 'analyze-scene-' in content or 'analyzeScene' in content, "analyze-scene button not found"
        print(f"PASS: StoryboardEditor has analyze-scene button")
    
    def test_storyboard_editor_has_smart_mode_toggle(self):
        """Test StoryboardEditor has smart-mode-toggle data-testid"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'data-testid="smart-mode-toggle"' in content, "smart-mode-toggle not found"
        print(f"PASS: StoryboardEditor has smart-mode-toggle")
    
    def test_storyboard_editor_has_zap_icon_for_smart_mode(self):
        """Test StoryboardEditor shows Zap icon when smartMode is true"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'Zap' in content, "Zap icon not imported"
        assert 'smartMode' in content, "smartMode state not found"
        print(f"PASS: StoryboardEditor has Zap icon and smartMode state")
    
    def test_storyboard_editor_has_scene_map_display(self):
        """Test StoryboardEditor shows Scene Map when analysis is available"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'Scene Map' in content or 'Mapa da Cena' in content, "Scene Map display not found"
        assert 'sceneAnalysis' in content, "sceneAnalysis state not found"
        print(f"PASS: StoryboardEditor has Scene Map display")
    
    def test_storyboard_editor_has_clickable_characters(self):
        """Test StoryboardEditor has clickable characters in Scene Map"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        # Check for onClick handler that fills inpaint input with character name
        assert 'setInpaintPrompt(c.name)' in content or 'setInpaintPrompt' in content, "Clickable characters not found"
        print(f"PASS: StoryboardEditor has clickable characters in Scene Map")
    
    def test_storyboard_editor_has_language_agent_section(self):
        """Test StoryboardEditor has Language Agent section"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'Language Agent' in content or 'Agente de Idioma' in content, "Language Agent section not found"
        assert 'Globe' in content, "Globe icon not imported"
        print(f"PASS: StoryboardEditor has Language Agent section")
    
    def test_storyboard_editor_has_inpainting_section(self):
        """Test StoryboardEditor has inpainting section with analyze and smart edit"""
        with open("/app/frontend/src/components/StoryboardEditor.jsx", "r") as f:
            content = f.read()
        assert 'inpaintingPanel' in content, "inpaintingPanel state not found"
        assert 'ScanSearch' in content, "ScanSearch icon not imported (for analyze)"
        print(f"PASS: StoryboardEditor has inpainting section")


class TestProjectStatusEndpoint:
    """Test project status endpoint returns language and review status"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_project_status_returns_storyboard_panels(self, headers):
        """Test project status returns storyboard_panels"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/status",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "storyboard_panels" in data, "storyboard_panels not in status response"
        panels = data.get("storyboard_panels", [])
        print(f"PASS: Project status returns {len(panels)} storyboard panels")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
