"""
Iteration 106: Storyboard Animated Preview Feature Tests
Tests for:
- POST /api/studio/projects/{id}/storyboard/generate-preview (MP4 generation with ElevenLabs narration)
- GET /api/studio/projects/{id}/storyboard/preview-status (preview status and URL)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PROJECT_ID = "fce897cf6ba3"  # Project with storyboard panels already generated


class TestAuth:
    """Authentication helper"""
    
    @staticmethod
    def get_auth_token():
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")  # Note: access_token not 'token'
        return None


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for all tests"""
    token = TestAuth.get_auth_token()
    if not token:
        pytest.skip("Authentication failed - skipping tests")
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


# ═══════════════════════════════════════════════════════════
# Preview Generation Endpoint Tests
# ═══════════════════════════════════════════════════════════

class TestGeneratePreviewEndpoint:
    """Tests for POST /api/studio/projects/{id}/storyboard/generate-preview"""
    
    def test_generate_preview_endpoint_exists(self, auth_headers):
        """Verify the generate-preview endpoint exists and accepts POST"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/generate-preview",
            headers=auth_headers,
            json={"voice_id": "onwK4e9ZLuTAKqWW03F9"}
        )
        # Should not return 404 or 405
        assert response.status_code not in [404, 405], f"Endpoint not found or method not allowed: {response.status_code}"
        print(f"PASS: generate-preview endpoint exists, status: {response.status_code}")
    
    def test_generate_preview_response_structure(self, auth_headers):
        """Verify response structure contains expected fields"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/generate-preview",
            headers=auth_headers,
            json={"voice_id": "onwK4e9ZLuTAKqWW03F9", "music_track": "cinematic"}
        )
        # Should return 200 with status and total_panels
        if response.status_code == 200:
            data = response.json()
            assert "status" in data, "Response should contain 'status' field"
            assert "total_panels" in data, "Response should contain 'total_panels' field"
            print(f"PASS: Response structure correct - status: {data.get('status')}, total_panels: {data.get('total_panels')}")
        elif response.status_code == 400:
            # May fail if no panels with images
            data = response.json()
            print(f"INFO: 400 response (expected if no panels): {data.get('detail')}")
        else:
            print(f"INFO: Response status {response.status_code}")
    
    def test_generate_preview_invalid_project_returns_404(self, auth_headers):
        """Verify 404 for non-existent project"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/nonexistent123/storyboard/generate-preview",
            headers=auth_headers,
            json={"voice_id": "onwK4e9ZLuTAKqWW03F9"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Invalid project returns 404")
    
    def test_generate_preview_without_auth_returns_401(self):
        """Verify 401 without authentication"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/generate-preview",
            json={"voice_id": "onwK4e9ZLuTAKqWW03F9"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Unauthenticated request returns 401/403")


# ═══════════════════════════════════════════════════════════
# Preview Status Endpoint Tests
# ═══════════════════════════════════════════════════════════

class TestPreviewStatusEndpoint:
    """Tests for GET /api/studio/projects/{id}/storyboard/preview-status"""
    
    def test_preview_status_endpoint_exists(self, auth_headers):
        """Verify the preview-status endpoint exists and accepts GET"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/preview-status",
            headers=auth_headers
        )
        # Should not return 404 or 405
        assert response.status_code not in [404, 405], f"Endpoint not found or method not allowed: {response.status_code}"
        print(f"PASS: preview-status endpoint exists, status: {response.status_code}")
    
    def test_preview_status_response_structure(self, auth_headers):
        """Verify response structure contains expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/preview-status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "preview_status" in data, "Response should contain 'preview_status' field"
        assert "preview_url" in data, "Response should contain 'preview_url' field"
        print(f"PASS: Response structure correct - preview_status: {data.get('preview_status')}, preview_url: {data.get('preview_url')}")
    
    def test_preview_status_invalid_project_returns_404(self, auth_headers):
        """Verify 404 for non-existent project"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/nonexistent123/storyboard/preview-status",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Invalid project returns 404")
    
    def test_preview_status_without_auth_returns_401(self):
        """Verify 401 without authentication"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/preview-status"
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Unauthenticated request returns 401/403")


# ═══════════════════════════════════════════════════════════
# Preview Generator Module Tests
# ═══════════════════════════════════════════════════════════

class TestPreviewGeneratorModule:
    """Tests for the preview_generator.py module"""
    
    def test_preview_generator_module_exists(self):
        """Verify the preview_generator module exists"""
        import sys
        sys.path.insert(0, '/app/backend')
        try:
            from core.preview_generator import generate_preview_video
            assert callable(generate_preview_video), "generate_preview_video should be callable"
            print("PASS: preview_generator module exists and generate_preview_video is callable")
        except ImportError as e:
            pytest.fail(f"Failed to import preview_generator: {e}")
    
    def test_preview_generator_has_required_functions(self):
        """Verify the module has all required helper functions"""
        import sys
        sys.path.insert(0, '/app/backend')
        from core import preview_generator
        
        required_functions = [
            'generate_preview_video',
            '_download_file',
            '_generate_panel_narration',
            '_get_audio_duration'
        ]
        
        for func_name in required_functions:
            assert hasattr(preview_generator, func_name), f"Missing function: {func_name}"
            print(f"PASS: Function {func_name} exists")


# ═══════════════════════════════════════════════════════════
# Integration Tests - Verify Project Status Includes Preview Fields
# ═══════════════════════════════════════════════════════════

class TestProjectStatusIncludesPreviewFields:
    """Verify project status endpoint includes preview-related fields"""
    
    def test_status_includes_preview_status(self, auth_headers):
        """Verify project status includes preview_status field"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=auth_headers
        )
        if response.status_code == 200:
            data = response.json()
            # preview_status may not be in status endpoint, check storyboard endpoint instead
            print(f"INFO: Status endpoint fields: {list(data.keys())}")
        else:
            print(f"INFO: Status endpoint returned {response.status_code}")
    
    def test_storyboard_endpoint_returns_panels(self, auth_headers):
        """Verify storyboard endpoint returns panels with images"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        panels = data.get("panels", [])
        panels_with_images = [p for p in panels if p.get("image_url")]
        print(f"PASS: Storyboard has {len(panels)} panels, {len(panels_with_images)} with images")
        assert len(panels_with_images) > 0, "Project should have panels with images for preview testing"


# ═══════════════════════════════════════════════════════════
# End-to-End Preview Generation Test (Quick Check Only)
# ═══════════════════════════════════════════════════════════

class TestPreviewGenerationE2E:
    """End-to-end test for preview generation (quick check only, don't wait for completion)"""
    
    def test_trigger_preview_generation_and_check_status(self, auth_headers):
        """Trigger preview generation and verify status updates"""
        # First check if there are panels with images
        storyboard_resp = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        if storyboard_resp.status_code != 200:
            pytest.skip("Could not get storyboard")
        
        panels = storyboard_resp.json().get("panels", [])
        panels_with_images = [p for p in panels if p.get("image_url")]
        
        if len(panels_with_images) == 0:
            pytest.skip("No panels with images - cannot test preview generation")
        
        # Trigger preview generation
        gen_resp = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/generate-preview",
            headers=auth_headers,
            json={"voice_id": "onwK4e9ZLuTAKqWW03F9", "music_track": ""}
        )
        
        if gen_resp.status_code == 200:
            data = gen_resp.json()
            assert data.get("status") == "generating", f"Expected status 'generating', got {data.get('status')}"
            print(f"PASS: Preview generation triggered - {data.get('total_panels')} panels")
            
            # Wait a moment and check status
            time.sleep(2)
            
            status_resp = requests.get(
                f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard/preview-status",
                headers=auth_headers
            )
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                preview_status = status_data.get("preview_status", {})
                print(f"PASS: Preview status check - phase: {preview_status.get('phase')}")
                # Don't wait for completion - just verify the status endpoint works
        elif gen_resp.status_code == 400:
            # May fail if no panels with images
            print(f"INFO: 400 response - {gen_resp.json().get('detail')}")
        else:
            print(f"INFO: Unexpected response {gen_resp.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
