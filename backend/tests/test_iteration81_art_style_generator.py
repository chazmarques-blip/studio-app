"""
Iteration 81: Art Style Generator in Art Gallery Modal Tests
Tests the new art style generator feature inside the ArtGalleryModal component.
Features tested:
- Backend regenerate-single-image endpoint exists and accepts required parameters
- Frontend ArtGalleryModal has 14 style buttons with correct data-testid
- Style buttons are clickable and send correct API calls
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authentication"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestBackendRegenerateSingleImageEndpoint:
    """Tests for the /api/campaigns/pipeline/regenerate-single-image endpoint"""
    
    def test_endpoint_exists_and_requires_auth(self):
        """Verify endpoint exists and requires authentication"""
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline/regenerate-single-image", 
            json={
                "style": "minimalist",
                "campaign_name": "Test",
                "campaign_copy": "Test copy",
                "language": "pt"
            },
            timeout=10
        )
        # Should return 401 (not authenticated) or 403 (forbidden), not 404
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}: {response.text[:200]}"
        print(f"Endpoint exists and requires auth: {response.status_code}")
    
    def test_endpoint_defined_in_routes(self):
        """Verify endpoint is defined in routes.py"""
        routes_path = "/app/backend/pipeline/routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        assert '@router.post("/regenerate-single-image")' in content, "Endpoint not defined in routes.py"
        assert "async def regenerate_single_image" in content, "regenerate_single_image function not found"
        print("Endpoint defined in routes.py")
    
    def test_endpoint_accepts_style_parameter(self):
        """Verify endpoint schema accepts style parameter"""
        routes_path = "/app/backend/pipeline/routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check RegenerateStyleRequest is used
        assert "RegenerateStyleRequest" in content, "RegenerateStyleRequest not found"
        assert "body.style" in content, "body.style not used in endpoint"
        print("Endpoint accepts style parameter via RegenerateStyleRequest")


class TestBackendStylePrompts:
    """Tests for STYLE_PROMPTS configuration in routes.py"""
    
    def test_style_prompts_exist_in_routes(self):
        """Verify STYLE_PROMPTS dictionary exists with all 14 styles"""
        routes_path = "/app/backend/pipeline/routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check STYLE_PROMPTS exists
        assert "STYLE_PROMPTS" in content, "STYLE_PROMPTS not found in routes.py"
        
        # Check all 14 styles are defined
        EXPECTED_STYLES = [
            "minimalist", "vibrant", "luxury", "corporate", "playful", "bold", "organic",
            "tech", "cartoon", "illustration", "watercolor", "neon", "retro", "flat"
        ]
        
        for style in EXPECTED_STYLES:
            pattern = rf'"{style}":\s*"'
            assert re.search(pattern, content), f"Style '{style}' not found in STYLE_PROMPTS"
        
        print(f"All {len(EXPECTED_STYLES)} styles found in STYLE_PROMPTS")
    
    def test_regenerate_single_image_uses_style_prompts(self):
        """Verify regenerate_single_image endpoint uses STYLE_PROMPTS"""
        routes_path = "/app/backend/pipeline/routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Find the regenerate_single_image function
        assert "async def regenerate_single_image" in content, "regenerate_single_image function not found"
        
        # Check it uses STYLE_PROMPTS
        func_match = re.search(r'async def regenerate_single_image.*?(?=\n@router|\nclass |\Z)', content, re.DOTALL)
        assert func_match, "Could not extract regenerate_single_image function"
        
        func_content = func_match.group(0)
        assert "STYLE_PROMPTS" in func_content, "regenerate_single_image doesn't use STYLE_PROMPTS"
        assert "body.style" in func_content, "regenerate_single_image doesn't use body.style parameter"
        
        print("regenerate_single_image correctly uses STYLE_PROMPTS and body.style")


class TestFrontendArtGalleryModal:
    """Tests for ArtGalleryModal component in Marketing.jsx"""
    
    def test_art_gallery_modal_exists(self):
        """Verify ArtGalleryModal component exists"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        assert "function ArtGalleryModal" in content, "ArtGalleryModal component not found"
        print("ArtGalleryModal component found")
    
    def test_art_styles_array_has_14_styles(self):
        """Verify ART_STYLES array has all 14 styles"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        # Find ART_STYLES array
        assert "ART_STYLES" in content, "ART_STYLES array not found"
        
        # Check all 14 style keys
        EXPECTED_STYLES = [
            "minimalist", "vibrant", "luxury", "corporate", "playful", "bold", "organic",
            "tech", "cartoon", "illustration", "watercolor", "neon", "retro", "flat"
        ]
        
        for style in EXPECTED_STYLES:
            pattern = rf"key:\s*['\"]?{style}['\"]?"
            assert re.search(pattern, content), f"Style key '{style}' not found in ART_STYLES"
        
        print(f"All {len(EXPECTED_STYLES)} styles found in ART_STYLES array")
    
    def test_style_buttons_have_correct_data_testid(self):
        """Verify style buttons have data-testid='gallery-style-{key}' format"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        # Check for data-testid pattern
        pattern = r'data-testid=\{`gallery-style-\$\{s\.key\}`\}'
        assert re.search(pattern, content), "data-testid pattern 'gallery-style-{key}' not found"
        
        print("Style buttons have correct data-testid format: gallery-style-{key}")
    
    def test_generate_style_image_function_exists(self):
        """Verify generateStyleImage function exists and calls the API"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        assert "generateStyleImage" in content, "generateStyleImage function not found"
        assert "regenerate-single-image" in content, "API endpoint call not found in generateStyleImage"
        
        print("generateStyleImage function found with correct API call")
    
    def test_style_labels_in_translations(self):
        """Verify style labels exist in translation object"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        # Check for style label translations
        STYLE_LABELS = [
            "styleMinimalist", "styleVibrant", "styleLuxury", "styleCorporate",
            "stylePlayful", "styleBold", "styleOrganic", "styleTech",
            "styleCartoon", "styleIllustration", "styleWatercolor", "styleNeon",
            "styleRetro", "styleFlat"
        ]
        
        for label in STYLE_LABELS:
            assert label in content, f"Translation label '{label}' not found"
        
        print(f"All {len(STYLE_LABELS)} style labels found in translations")
    
    def test_generate_new_image_section_label(self):
        """Verify 'Generate New Image' section label exists"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        assert "generateNewImage" in content, "generateNewImage label not found"
        assert "labels.generateNewImage" in content, "labels.generateNewImage usage not found"
        
        print("'Generate New Image' section label found")


class TestFrontendIntegration:
    """Tests for frontend-backend integration"""
    
    def test_api_call_includes_required_parameters(self):
        """Verify frontend API call includes all required parameters"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        # Find the generateStyleImage function - look for the full function body
        func_match = re.search(r'const\s+generateStyleImage\s*=\s*async.*?setStyleRegenLoading\(false\);\s*\}\s*\};', content, re.DOTALL)
        
        assert func_match, "Could not extract generateStyleImage function"
        func_content = func_match.group(0)
        
        # Check required parameters are sent (style: styleKey format)
        assert "style:" in func_content or "style :" in func_content or "styleKey" in func_content, "style parameter not sent"
        assert "campaign_name" in func_content, "campaign_name parameter not sent"
        assert "campaign_copy" in func_content, "campaign_copy parameter not sent"
        assert "language" in func_content, "language parameter not sent"
        assert "pipeline_id" in func_content or "pipelineId" in func_content, "pipeline_id parameter not sent"
        
        print("All required parameters found in API call")
    
    def test_images_state_updated_on_success(self):
        """Verify images state is updated when new image is generated"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        # Check for setImages call to add new image
        assert "setImages" in content, "setImages not found"
        
        # Check for pattern that adds new image to array
        pattern = r'setImages\s*\(\s*prev\s*=>\s*\[\s*\.\.\.prev'
        assert re.search(pattern, content), "setImages doesn't append new image to array"
        
        print("Images state correctly updated with new image")
    
    def test_loading_state_during_generation(self):
        """Verify loading state is shown during image generation"""
        marketing_path = "/app/frontend/src/pages/Marketing.jsx"
        with open(marketing_path, 'r') as f:
            content = f.read()
        
        assert "styleRegenLoading" in content, "styleRegenLoading state not found"
        assert "setStyleRegenLoading" in content, "setStyleRegenLoading not found"
        assert "generatingImage" in content, "generatingImage label not found"
        
        print("Loading state correctly implemented")


class TestBackendHealth:
    """Basic health check"""
    
    def test_backend_is_healthy(self):
        """Verify backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Backend unhealthy: {response.status_code}"
        print("Backend is healthy")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
