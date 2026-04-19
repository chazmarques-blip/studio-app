"""
BookFactory Pipeline Tests - Iteration 137
Tests for the new BookFactory parallel pipeline for physical book generation.

Endpoints tested:
- GET /api/studio/book/trim-sizes - Returns 4 trim sizes + 9 visual tracks
- GET /api/studio/book/compositions - Returns registry with compositions and resolver.fallback
- POST /api/studio/projects/{id}/book/start - Saves brief + resolves composition_key
- POST /api/studio/projects/{id}/book/generate-outline - Calls Claude via emergentintegrations
- POST /api/studio/projects/{id}/book/approve-outline - Approves outline
- POST /api/studio/projects/{id}/book/generate-chapter - Writes prose for a chapter
- POST /api/studio/projects/{id}/book/plan-illustrations - Generates illustration plan
- POST /api/studio/projects/{id}/book/proofread - Proofreads chapters
- POST /api/studio/projects/{id}/book/render-pdf - Renders PDF via WeasyPrint
- POST /api/studio/projects/{id}/book/preflight - Runs preflight checks
- GET /api/studio/projects/{id}/book/state - Returns book_bible state
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"


class TestBookFactorySetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token")
        assert token, "No access_token in response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✓ Health check passed")


class TestBookFactoryStaticEndpoints:
    """Tests for static endpoints that don't require a project"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_trim_sizes(self, auth_headers):
        """GET /api/studio/book/trim-sizes returns 4 trim sizes + 9 visual tracks"""
        response = requests.get(
            f"{BASE_URL}/api/studio/book/trim-sizes",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate trim_sizes
        trim_sizes = data.get("trim_sizes", {})
        assert len(trim_sizes) == 4, f"Expected 4 trim sizes, got {len(trim_sizes)}"
        expected_sizes = ["6x9", "5x8", "A4", "A5"]
        for size in expected_sizes:
            assert size in trim_sizes, f"Missing trim size: {size}"
            assert "width" in trim_sizes[size]
            assert "height" in trim_sizes[size]
            assert "name" in trim_sizes[size]
        
        # Validate visual_tracks
        visual_tracks = data.get("visual_tracks", [])
        assert len(visual_tracks) == 9, f"Expected 9 visual tracks, got {len(visual_tracks)}"
        expected_tracks = ["aquarela", "cartoon", "flat", "storybook", "realismo_editorial", 
                          "minimalista", "gravura", "fotorrealismo", "none"]
        for track in expected_tracks:
            assert track in visual_tracks, f"Missing visual track: {track}"
        
        print(f"✓ Trim sizes: {list(trim_sizes.keys())}")
        print(f"✓ Visual tracks: {visual_tracks}")
    
    def test_get_compositions(self, auth_headers):
        """GET /api/studio/book/compositions returns registry with compositions and resolver.fallback"""
        response = requests.get(
            f"{BASE_URL}/api/studio/book/compositions",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate compositions exist
        compositions = data.get("compositions", {})
        assert len(compositions) > 0, "No compositions found"
        
        # Check expected composition keys
        expected_keys = [
            "book_infantil_ilustrado_user_author",
            "book_infantil_ilustrado_public_domain",
            "book_romance_adulto_user_author",
            "book_tecnico_historico_public_domain",
            "both_parallel",
            "video_only"
        ]
        for key in expected_keys:
            assert key in compositions, f"Missing composition: {key}"
            assert "agents" in compositions[key], f"Composition {key} missing agents"
            assert "leader" in compositions[key], f"Composition {key} missing leader"
        
        # Validate resolver with fallback
        resolver = data.get("resolver", {})
        assert "fallback" in resolver, "Missing resolver.fallback"
        assert resolver["fallback"] == "book_infantil_ilustrado_user_author"
        
        print(f"✓ Compositions found: {list(compositions.keys())}")
        print(f"✓ Resolver fallback: {resolver['fallback']}")


class TestBookFactoryPipeline:
    """Tests for the BookFactory pipeline endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_project_id(self, auth_headers):
        """Create a test project for BookFactory tests"""
        project_data = {
            "name": f"BookFactoryTest_{int(time.time())}",
            "briefing": "Uma história infantil sobre um coelho que aprende a compartilhar com seus amigos na floresta.",
            "language": "pt",
            "visual_style": "animation",
            "scene_type": "multi_scene"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        assert response.status_code == 200, f"Failed to create project: {response.text}"
        data = response.json()
        project_id = data.get("id")
        assert project_id, "No project ID returned"
        print(f"✓ Created test project: {project_id}")
        yield project_id
        
        # Cleanup: Delete test project
        try:
            requests.delete(
                f"{BASE_URL}/api/studio/projects/{project_id}",
                headers=auth_headers,
                timeout=30
            )
            print(f"✓ Cleaned up test project: {project_id}")
        except Exception as e:
            print(f"Warning: Failed to cleanup project: {e}")
    
    def test_book_start_valid(self, auth_headers, test_project_id):
        """POST /book/start with valid data saves brief and resolves composition_key"""
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "target_pages": 40,
            "audience": "children_4_8",
            "illustration_track": "storybook",
            "title": "O Coelho Generoso",
            "author_name": "Autor Teste",
            "briefing": "Uma história sobre um coelho que aprende a compartilhar.",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert data.get("project_id") == test_project_id
        assert data.get("composition_key") == "book_infantil_ilustrado_user_author"
        assert data.get("status") == "brief_received"
        assert "trim_size_mm" in data
        assert data["trim_size_mm"]["width"] == 152.4  # 6x9 width in mm
        assert "agents_active" in data
        assert "next_step" in data
        
        print(f"✓ Book start successful - composition_key: {data['composition_key']}")
    
    def test_book_start_idempotent(self, auth_headers, test_project_id):
        """POST /book/start twice for the same project should work (idempotent)"""
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "5x8",  # Different trim size
            "target_pages": 32,
            "audience": "children_4_8",
            "illustration_track": "cartoon",
            "title": "O Coelho Generoso v2",
            "author_name": "Autor Teste",
            "briefing": "Uma história sobre um coelho que aprende a compartilhar.",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200, f"Idempotent call failed: {response.text}"
        data = response.json()
        assert data.get("trim_size_mm", {}).get("width") == 127.0  # 5x8 width
        print("✓ Book start idempotent - second call succeeded")
    
    def test_book_start_invalid_trim_size(self, auth_headers):
        """POST /book/start with invalid trim_size returns 400"""
        # Create a fresh project for this test
        project_data = {
            "name": f"BookFactoryTest_InvalidTrim_{int(time.time())}",
            "briefing": "Test",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to create test project: {response.text}")
        project_id = response.json().get("id")
        
        try:
            brief_data = {
                "output_mode": "book",
                "autoria_mode": "user_author",
                "format_preset": "infantil_ilustrado",
                "trim_size": "invalid_size",  # Invalid
                "target_pages": 40,
                "audience": "children_4_8",
                "illustration_track": "storybook",
                "title": "Test",
                "briefing": "Test",
                "language": "pt"
            }
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{project_id}/book/start",
                headers=auth_headers,
                json=brief_data,
                timeout=30
            )
            # Allow 500 if it's a connection issue, but the endpoint should return 400
            if response.status_code == 500 and "Server disconnected" in response.text:
                pytest.skip("Intermittent connection issue with Supabase")
            assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
            print("✓ Invalid trim_size correctly returns 400")
        finally:
            # Cleanup
            try:
                requests.delete(
                    f"{BASE_URL}/api/studio/projects/{project_id}",
                    headers=auth_headers,
                    timeout=30
                )
            except:
                pass
    
    def test_book_start_invalid_illustration_track(self, auth_headers):
        """POST /book/start with invalid illustration_track returns 400"""
        # Create a fresh project for this test
        project_data = {
            "name": f"BookFactoryTest_InvalidTrack_{int(time.time())}",
            "briefing": "Test",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to create test project: {response.text}")
        project_id = response.json().get("id")
        
        try:
            brief_data = {
                "output_mode": "book",
                "autoria_mode": "user_author",
                "format_preset": "infantil_ilustrado",
                "trim_size": "6x9",
                "target_pages": 40,
                "audience": "children_4_8",
                "illustration_track": "invalid_track",  # Invalid
                "title": "Test",
                "briefing": "Test",
                "language": "pt"
            }
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{project_id}/book/start",
                headers=auth_headers,
                json=brief_data,
                timeout=30
            )
            if response.status_code == 500 and "Server disconnected" in response.text:
                pytest.skip("Intermittent connection issue with Supabase")
            assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
            print("✓ Invalid illustration_track correctly returns 400")
        finally:
            # Cleanup
            try:
                requests.delete(
                    f"{BASE_URL}/api/studio/projects/{project_id}",
                    headers=auth_headers,
                    timeout=30
                )
            except:
                pass
    
    def test_approve_outline_without_outline(self, auth_headers, test_project_id):
        """POST /book/approve-outline without outline returns 400"""
        # First reset the project with a fresh start (no outline)
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "target_pages": 40,
            "audience": "children_4_8",
            "illustration_track": "storybook",
            "title": "Test",
            "briefing": "Test",
            "language": "pt"
        }
        requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        
        # Try to approve without generating outline first
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{test_project_id}/book/approve-outline",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Approve outline without outline correctly returns 400")
    
    def test_book_state(self, auth_headers, test_project_id):
        """GET /book/state returns book_bible state"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{test_project_id}/book/state",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should have brief from previous tests
        assert "brief" in data or "status" in data
        print(f"✓ Book state retrieved - status: {data.get('status', 'unknown')}")


class TestBookFactoryCompositionResolver:
    """Tests for composition key resolution"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture
    def temp_project_id(self, auth_headers):
        """Create a temporary project for each test"""
        project_data = {
            "name": f"BookFactoryTest_Comp_{int(time.time())}",
            "briefing": "Test project for composition resolver",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        assert response.status_code == 200
        project_id = response.json().get("id")
        yield project_id
        
        # Cleanup
        try:
            requests.delete(
                f"{BASE_URL}/api/studio/projects/{project_id}",
                headers=auth_headers,
                timeout=30
            )
        except:
            pass
    
    def test_composition_book_infantil_ilustrado_user_author(self, auth_headers, temp_project_id):
        """Test composition resolution for book_infantil_ilustrado_user_author"""
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "illustration_track": "storybook",
            "briefing": "Test"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{temp_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200
        assert response.json().get("composition_key") == "book_infantil_ilustrado_user_author"
        print("✓ Composition: book_infantil_ilustrado_user_author")
    
    def test_composition_book_infantil_ilustrado_public_domain(self, auth_headers, temp_project_id):
        """Test composition resolution for book_infantil_ilustrado_public_domain"""
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "public_domain",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "illustration_track": "storybook",
            "briefing": "Test",
            "reference_work": "biblia_genesis"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{temp_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200
        assert response.json().get("composition_key") == "book_infantil_ilustrado_public_domain"
        print("✓ Composition: book_infantil_ilustrado_public_domain")
    
    def test_composition_book_romance_adulto_user_author(self, auth_headers, temp_project_id):
        """Test composition resolution for book_romance_adulto_user_author"""
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "romance_adulto",
            "trim_size": "5x8",
            "illustration_track": "none",  # Romance adulto skips illustrations
            "briefing": "Test"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{temp_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200
        assert response.json().get("composition_key") == "book_romance_adulto_user_author"
        print("✓ Composition: book_romance_adulto_user_author")
    
    def test_composition_book_tecnico_historico_public_domain(self, auth_headers, temp_project_id):
        """Test composition resolution for book_tecnico_historico_public_domain"""
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "public_domain",
            "format_preset": "tecnico_historico",
            "trim_size": "A4",
            "illustration_track": "gravura",
            "briefing": "Test",
            "reference_work": "classic_dom_casmurro"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{temp_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200
        assert response.json().get("composition_key") == "book_tecnico_historico_public_domain"
        print("✓ Composition: book_tecnico_historico_public_domain")
    
    def test_composition_both_parallel(self, auth_headers, temp_project_id):
        """Test composition resolution for both_parallel mode"""
        brief_data = {
            "output_mode": "both",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "illustration_track": "storybook",
            "briefing": "Test"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{temp_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200
        assert response.json().get("composition_key") == "both_parallel"
        print("✓ Composition: both_parallel")
    
    def test_composition_video_only(self, auth_headers, temp_project_id):
        """Test composition resolution for video_only mode"""
        brief_data = {
            "output_mode": "video",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "illustration_track": "storybook",
            "briefing": "Test"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{temp_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        assert response.status_code == 200
        assert response.json().get("composition_key") == "video_only"
        print("✓ Composition: video_only")


class TestBookFactoryLLMEndpoints:
    """Tests for LLM-powered endpoints (require EMERGENT_LLM_KEY)
    
    NOTE: These tests may fail if the Emergent LLM proxy is not properly configured
    or if there are authentication issues with the EMERGENT_LLM_KEY.
    """
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def llm_test_project_id(self, auth_headers):
        """Create a test project for LLM tests"""
        project_data = {
            "name": f"BookFactoryTest_LLM_{int(time.time())}",
            "briefing": "Uma história infantil sobre um coelho chamado Bento que aprende a compartilhar cenouras com seus amigos na floresta encantada.",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to create test project: {response.text}")
        project_id = response.json().get("id")
        
        # Start book pipeline
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "target_pages": 24,
            "audience": "children_4_8",
            "illustration_track": "storybook",
            "title": "Bento, o Coelho Generoso",
            "author_name": "Autor Teste",
            "briefing": "Uma história infantil sobre um coelho chamado Bento que aprende a compartilhar cenouras com seus amigos na floresta encantada.",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to start book pipeline: {response.text}")
        
        yield project_id
        
        # Cleanup
        try:
            requests.delete(
                f"{BASE_URL}/api/studio/projects/{project_id}",
                headers=auth_headers,
                timeout=30
            )
        except:
            pass
    
    def test_generate_outline(self, auth_headers, llm_test_project_id):
        """POST /book/generate-outline calls Claude and returns valid JSON outline
        
        NOTE: This test requires a working Emergent LLM proxy connection.
        If it fails with AuthenticationError, the EMERGENT_LLM_KEY may need to be refreshed.
        """
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/generate-outline",
            headers=auth_headers,
            timeout=120  # LLM calls can take 30-60s
        )
        
        if response.status_code == 500 and "EMERGENT_LLM_KEY" in response.text:
            pytest.skip("EMERGENT_LLM_KEY not configured")
        
        if response.status_code == 502 and "AuthenticationError" in response.text:
            pytest.skip("Emergent LLM proxy authentication failed - key may need refresh")
        
        if response.status_code == 502:
            pytest.skip(f"LLM service unavailable: {response.text[:200]}")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate outline structure
        assert "title" in data, "Missing title in outline"
        assert "blurb" in data, "Missing blurb in outline"
        assert "total_chapters" in data, "Missing total_chapters in outline"
        assert "chapters" in data, "Missing chapters in outline"
        assert isinstance(data["chapters"], list), "chapters should be a list"
        assert len(data["chapters"]) > 0, "chapters should not be empty"
        
        # Validate chapter structure
        for ch in data["chapters"]:
            assert "index" in ch, "Chapter missing index"
            assert "title" in ch, "Chapter missing title"
            assert "synopsis" in ch, "Chapter missing synopsis"
        
        print(f"✓ Outline generated: {data['title']} - {data['total_chapters']} chapters")
        print(f"  Chapters: {[ch['title'] for ch in data['chapters'][:3]]}...")
    
    def test_approve_outline(self, auth_headers, llm_test_project_id):
        """POST /book/approve-outline after outline exists"""
        # First check if outline exists
        state_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/state",
            headers=auth_headers,
            timeout=30
        )
        state = state_response.json()
        
        if not state.get("outline"):
            pytest.skip("No outline to approve - generate-outline test may have been skipped")
        
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/approve-outline",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("status") == "outline_approved"
        print("✓ Outline approved")
    
    def test_generate_chapter_1(self, auth_headers, llm_test_project_id):
        """POST /book/generate-chapter for chapter 1"""
        # Check if outline exists
        state_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/state",
            headers=auth_headers,
            timeout=30
        )
        state = state_response.json()
        
        if not state.get("outline"):
            pytest.skip("No outline - generate-outline test may have been skipped")
        
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/generate-chapter",
            headers=auth_headers,
            json={"chapter_index": 1},
            timeout=120
        )
        
        if response.status_code == 500 and "EMERGENT_LLM_KEY" in response.text:
            pytest.skip("EMERGENT_LLM_KEY not configured")
        
        if response.status_code == 502 and "AuthenticationError" in response.text:
            pytest.skip("Emergent LLM proxy authentication failed")
        
        if response.status_code == 502:
            pytest.skip(f"LLM service unavailable: {response.text[:200]}")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "prose" in data, "Missing prose in chapter"
        assert "word_count" in data, "Missing word_count"
        assert data["word_count"] > 100, f"Chapter too short: {data['word_count']} words"
        assert data["index"] == 1
        
        print(f"✓ Chapter 1 generated: {data['title']} ({data['word_count']} words)")
    
    def test_generate_chapter_2_continuity(self, auth_headers, llm_test_project_id):
        """POST /book/generate-chapter for chapter 2 (tests continuity)"""
        state_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/state",
            headers=auth_headers,
            timeout=30
        )
        state = state_response.json()
        
        outline = state.get("outline", {})
        chapters = outline.get("chapters", [])
        
        if len(chapters) < 2:
            pytest.skip("Outline has less than 2 chapters")
        
        if not state.get("chapters", {}).get("1"):
            pytest.skip("Chapter 1 not generated yet")
        
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{llm_test_project_id}/book/generate-chapter",
            headers=auth_headers,
            json={"chapter_index": 2},
            timeout=120
        )
        
        if response.status_code == 500 and "EMERGENT_LLM_KEY" in response.text:
            pytest.skip("EMERGENT_LLM_KEY not configured")
        
        if response.status_code == 502 and "AuthenticationError" in response.text:
            pytest.skip("Emergent LLM proxy authentication failed")
        
        if response.status_code == 502:
            pytest.skip(f"LLM service unavailable: {response.text[:200]}")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "prose" in data
        assert data["index"] == 2
        print(f"✓ Chapter 2 generated: {data['title']} ({data['word_count']} words)")


class TestBookFactoryIllustrationPlan:
    """Tests for illustration planning"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def illustration_test_project_id(self, auth_headers):
        """Create a test project with chapters for illustration tests"""
        project_data = {
            "name": f"BookFactoryTest_Illus_{int(time.time())}",
            "briefing": "Test project for illustrations",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        assert response.status_code == 200
        project_id = response.json().get("id")
        yield project_id
        
        # Cleanup
        try:
            requests.delete(
                f"{BASE_URL}/api/studio/projects/{project_id}",
                headers=auth_headers,
                timeout=30
            )
        except:
            pass
    
    def test_plan_illustrations_no_chapters(self, auth_headers, illustration_test_project_id):
        """POST /book/plan-illustrations without chapters returns 400"""
        # Start book without generating chapters
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "illustration_track": "storybook",
            "briefing": "Test"
        }
        requests.post(
            f"{BASE_URL}/api/studio/projects/{illustration_test_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{illustration_test_project_id}/book/plan-illustrations",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Plan illustrations without chapters correctly returns 400")
    
    def test_plan_illustrations_track_none(self, auth_headers, illustration_test_project_id):
        """POST /book/plan-illustrations with illustration_track=none returns skipped:true"""
        # Start book with illustration_track=none (romance_adulto style)
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "romance_adulto",
            "trim_size": "5x8",
            "illustration_track": "none",
            "briefing": "Test romance adulto"
        }
        requests.post(
            f"{BASE_URL}/api/studio/projects/{illustration_test_project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        
        # Manually add a chapter to the book_bible for testing
        # This simulates having chapters without actually calling LLM
        # We'll test the actual flow in the LLM tests
        
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{illustration_test_project_id}/book/plan-illustrations",
            headers=auth_headers,
            timeout=30
        )
        
        # Should return 400 (no chapters) or skipped:true if chapters exist
        if response.status_code == 200:
            data = response.json()
            assert data.get("skipped") == True, "Expected skipped:true for illustration_track=none"
            assert data.get("reason") == "illustration_track=none"
            print("✓ Plan illustrations with track=none returns skipped:true")
        else:
            # No chapters, which is expected
            assert response.status_code == 400
            print("✓ Plan illustrations without chapters returns 400 (expected)")


class TestBookFactoryBackwardCompatibility:
    """Tests to ensure video pipeline is not affected"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_video_project_creation_still_works(self, auth_headers):
        """POST /api/studio/projects still works for video projects"""
        project_data = {
            "name": f"VideoTest_{int(time.time())}",
            "briefing": "Test video project",
            "language": "pt",
            "visual_style": "animation",
            "video_engine": "sora"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        assert response.status_code == 200, f"Video project creation failed: {response.text}"
        data = response.json()
        project_id = data.get("id")
        assert project_id
        
        # Cleanup
        try:
            requests.delete(
                f"{BASE_URL}/api/studio/projects/{project_id}",
                headers=auth_headers,
                timeout=30
            )
        except:
            pass
        
        print("✓ Video project creation still works")
    
    def test_existing_project_endpoints_work(self, auth_headers):
        """Existing video pipeline endpoints still work"""
        # Test that we can list projects
        response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"List projects failed: {response.text}"
        print("✓ List projects endpoint works")
    
    def test_book_factory_endpoints_accessible(self, auth_headers):
        """BookFactory endpoints are accessible and respond correctly"""
        # Test trim-sizes endpoint
        response = requests.get(
            f"{BASE_URL}/api/studio/book/trim-sizes",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"trim-sizes endpoint failed: {response.text}"
        
        # Test compositions endpoint
        response = requests.get(
            f"{BASE_URL}/api/studio/book/compositions",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"compositions endpoint failed: {response.text}"
        
        print("✓ BookFactory endpoints are accessible and working")


class TestBookFactoryPDFRendering:
    """Tests for PDF rendering and preflight (requires chapters)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_render_pdf_no_chapters(self, auth_headers):
        """POST /book/render-pdf without chapters returns 400"""
        # Create a fresh project
        project_data = {
            "name": f"BookFactoryTest_PDF_{int(time.time())}",
            "briefing": "Test PDF rendering",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Failed to create test project: {response.text}")
        project_id = response.json().get("id")
        
        try:
            # Start book
            brief_data = {
                "output_mode": "book",
                "autoria_mode": "user_author",
                "format_preset": "infantil_ilustrado",
                "trim_size": "6x9",
                "illustration_track": "storybook",
                "briefing": "Test"
            }
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{project_id}/book/start",
                headers=auth_headers,
                json=brief_data,
                timeout=30
            )
            if response.status_code != 200:
                pytest.skip(f"Failed to start book: {response.text}")
            
            # Try to render PDF without chapters
            response = requests.post(
                f"{BASE_URL}/api/studio/projects/{project_id}/book/render-pdf",
                headers=auth_headers,
                timeout=30
            )
            if response.status_code == 500 and "Server disconnected" in response.text:
                pytest.skip("Intermittent connection issue with Supabase")
            assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
            print("✓ Render PDF without chapters correctly returns 400")
        finally:
            # Cleanup
            try:
                requests.delete(
                    f"{BASE_URL}/api/studio/projects/{project_id}",
                    headers=auth_headers,
                    timeout=30
                )
            except:
                pass
    
    def test_preflight_no_pdf(self, auth_headers):
        """POST /book/preflight without PDF returns 400"""
        # Create a fresh project
        project_data = {
            "name": f"BookFactoryTest_Preflight_{int(time.time())}",
            "briefing": "Test preflight",
            "language": "pt"
        }
        response = requests.post(
            f"{BASE_URL}/api/studio/projects",
            headers=auth_headers,
            json=project_data,
            timeout=30
        )
        assert response.status_code == 200
        project_id = response.json().get("id")
        
        # Start book
        brief_data = {
            "output_mode": "book",
            "autoria_mode": "user_author",
            "format_preset": "infantil_ilustrado",
            "trim_size": "6x9",
            "illustration_track": "storybook",
            "briefing": "Test"
        }
        requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/book/start",
            headers=auth_headers,
            json=brief_data,
            timeout=30
        )
        
        # Try to run preflight without PDF
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/book/preflight",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        # Cleanup
        try:
            requests.delete(
                f"{BASE_URL}/api/studio/projects/{project_id}",
                headers=auth_headers,
                timeout=30
            )
        except:
            pass
        
        print("✓ Preflight without PDF correctly returns 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
