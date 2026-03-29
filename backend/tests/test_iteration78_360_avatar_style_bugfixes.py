"""
Iteration 78: Test 360° Avatar Style Bug Fixes

Bug fixes being tested:
1. applyClothing uses tempAvatar.url (not source_photo_url) when avatar_style is 3d_pixar or 3d_cartoon
2. generateAngle uses tempAvatar.url when avatar_style is 3d_pixar or 3d_cartoon
3. startAuto360 from applyClothing passes the correct sourceUrl for 3D styles
4. Download button uses fetch+blob download pattern (not <a target=_blank>)
5. saveAvatarAndClose persists avatar_style in both edit and new avatar cases
6. saveAvatarAsNew persists avatar_style
7. openAvatarForEdit restores avatar_style from saved avatar
8. Landing V2 renders at / route
9. Backend accepts avatar_style param in generate-avatar-360 and generate-avatar-variant
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seguimiento-2.preview.emergentagent.com').rstrip('/')


class TestBackendAvatarStyleEndpoints:
    """Test backend endpoints accept avatar_style parameter"""
    
    def test_generate_avatar_variant_endpoint_exists(self):
        """Verify generate-avatar-variant endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            json={
                "source_image_url": "https://example.com/test.jpg",
                "clothing": "company_uniform",
                "angle": "front",
                "avatar_style": "3d_pixar"
            },
            timeout=10
        )
        # Should return 401 (unauthorized) or 422 (validation) but NOT 404
        assert response.status_code != 404, f"Endpoint not found: {response.status_code}"
        print(f"✓ generate-avatar-variant endpoint exists (status: {response.status_code})")
    
    def test_generate_avatar_360_endpoint_exists(self):
        """Verify generate-avatar-360 endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            json={
                "source_image_url": "https://example.com/test.jpg",
                "clothing": "company_uniform",
                "logo_url": "",
                "avatar_style": "3d_cartoon"
            },
            timeout=10
        )
        # Should return 401 (unauthorized) or 422 (validation) but NOT 404
        assert response.status_code != 404, f"Endpoint not found: {response.status_code}"
        print(f"✓ generate-avatar-360 endpoint exists (status: {response.status_code})")


class TestBackendConfigModels:
    """Test backend config models have avatar_style field"""
    
    def test_avatar_variant_request_has_avatar_style(self):
        """Verify AvatarVariantRequest model has avatar_style field"""
        config_path = "/app/backend/pipeline/config.py"
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check AvatarVariantRequest class
        assert "class AvatarVariantRequest" in content, "AvatarVariantRequest class not found"
        
        # Find the class definition and check for avatar_style
        variant_match = re.search(r'class AvatarVariantRequest.*?(?=class|\Z)', content, re.DOTALL)
        assert variant_match, "Could not find AvatarVariantRequest class"
        variant_class = variant_match.group(0)
        
        assert "avatar_style" in variant_class, "avatar_style field not in AvatarVariantRequest"
        assert "'realistic'" in variant_class or '"realistic"' in variant_class, "Default value 'realistic' not found"
        print("✓ AvatarVariantRequest has avatar_style field with default 'realistic'")
    
    def test_avatar_batch360_request_has_avatar_style(self):
        """Verify AvatarBatch360Request model has avatar_style field"""
        config_path = "/app/backend/pipeline/config.py"
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check AvatarBatch360Request class
        assert "class AvatarBatch360Request" in content, "AvatarBatch360Request class not found"
        
        # Find the class definition and check for avatar_style
        batch_match = re.search(r'class AvatarBatch360Request.*?(?=class|\Z)', content, re.DOTALL)
        assert batch_match, "Could not find AvatarBatch360Request class"
        batch_class = batch_match.group(0)
        
        assert "avatar_style" in batch_class, "avatar_style field not in AvatarBatch360Request"
        print("✓ AvatarBatch360Request has avatar_style field")


class TestBackendAvatarRoutesLogic:
    """Test backend avatar_routes.py has correct 3D style handling"""
    
    def test_generate_avatar_variant_uses_avatar_style(self):
        """Verify generate_avatar_variant function uses avatar_style parameter"""
        routes_path = "/app/backend/pipeline/avatar_routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check that the function uses req.avatar_style
        assert "req.avatar_style" in content, "req.avatar_style not used in avatar_routes.py"
        
        # Check for is_3d logic
        assert 'is_3d = req.avatar_style in ("3d_cartoon", "3d_pixar")' in content or \
               "is_3d = req.avatar_style in ('3d_cartoon', '3d_pixar')" in content, \
               "is_3d check not found in generate_avatar_variant"
        print("✓ generate_avatar_variant uses avatar_style parameter with is_3d check")
    
    def test_run_batch_360_accepts_avatar_style(self):
        """Verify _run_batch_360 function accepts avatar_style parameter"""
        routes_path = "/app/backend/pipeline/avatar_routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check function signature
        assert 'def _run_batch_360(job_id: str, source_url: str, clothing: str, logo_url: str = "", avatar_style: str = "realistic")' in content or \
               "def _run_batch_360(job_id: str, source_url: str, clothing: str, logo_url: str = '', avatar_style: str = 'realistic')" in content, \
               "_run_batch_360 doesn't have avatar_style parameter"
        print("✓ _run_batch_360 accepts avatar_style parameter")
    
    def test_3d_prompts_avoid_photorealistic(self):
        """Verify 3D style prompts explicitly avoid photorealistic"""
        routes_path = "/app/backend/pipeline/avatar_routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check for the critical instruction in prompts
        assert "do NOT make it photorealistic" in content.lower() or \
               "do not make it photorealistic" in content.lower(), \
               "3D prompts don't contain 'do NOT make it photorealistic'"
        print("✓ 3D style prompts contain 'do NOT make it photorealistic'")
    
    def test_generate_avatar_360_passes_avatar_style(self):
        """Verify generate_avatar_360 endpoint passes avatar_style to _run_batch_360"""
        routes_path = "/app/backend/pipeline/avatar_routes.py"
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Check that the thread is started with avatar_style
        assert "req.avatar_style" in content, "req.avatar_style not passed to _run_batch_360"
        
        # Check the thread call includes avatar_style
        assert "_run_batch_360" in content and "avatar_style" in content, \
               "_run_batch_360 call doesn't include avatar_style"
        print("✓ generate_avatar_360 passes avatar_style to _run_batch_360")


class TestFrontendApplyClothingLogic:
    """Test frontend applyClothing function uses correct sourceUrl for 3D styles"""
    
    def test_apply_clothing_has_is3d_check(self):
        """Verify applyClothing checks is3d before determining sourceUrl"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Search for is3d in the applyClothing context (lines 557-588)
        assert "const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic'" in content, \
               "is3d check not found in applyClothing"
        print("✓ applyClothing has is3d check")
    
    def test_apply_clothing_uses_temp_avatar_url_for_3d(self):
        """Verify applyClothing uses tempAvatar.url for 3D styles"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Check for the conditional sourceUrl logic
        assert "is3d ? tempAvatar.url" in content or "is3d ? tempAvatar?.url" in content, \
               "applyClothing doesn't use tempAvatar.url for 3D styles"
        print("✓ applyClothing uses tempAvatar.url for 3D styles (is3d ? tempAvatar.url)")
    
    def test_apply_clothing_sends_avatar_style_to_api(self):
        """Verify applyClothing sends avatar_style to API"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Check for avatar_style in the generate-avatar-variant API call
        # The pattern should be in the applyClothing function
        assert "avatar_style: tempAvatar?.avatar_style || 'realistic'" in content, \
               "avatar_style not sent in applyClothing API call"
        print("✓ applyClothing sends avatar_style to API")


class TestFrontendGenerateAngleLogic:
    """Test frontend generateAngle function uses correct sourceUrl for 3D styles"""
    
    def test_generate_angle_has_is3d_check(self):
        """Verify generateAngle checks is3d before determining sourceUrl"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Count occurrences of is3d check - should be at least 2 (applyClothing and generateAngle)
        is3d_count = content.count("const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic'")
        assert is3d_count >= 2, f"is3d check found only {is3d_count} times, expected at least 2 (applyClothing and generateAngle)"
        print(f"✓ generateAngle has is3d check (found {is3d_count} occurrences)")
    
    def test_generate_angle_uses_temp_avatar_url_for_3d(self):
        """Verify generateAngle uses tempAvatar.url for 3D styles"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Count occurrences of the sourceUrl pattern - should be at least 2
        source_url_count = content.count("const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url)")
        assert source_url_count >= 2, f"sourceUrl pattern found only {source_url_count} times, expected at least 2"
        print(f"✓ generateAngle uses tempAvatar.url for 3D styles (found {source_url_count} occurrences)")
    
    def test_generate_angle_sends_avatar_style_to_api(self):
        """Verify generateAngle sends avatar_style to API"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Count occurrences of avatar_style in API calls - should be multiple
        avatar_style_count = content.count("avatar_style: tempAvatar?.avatar_style || 'realistic'")
        assert avatar_style_count >= 2, f"avatar_style in API calls found only {avatar_style_count} times, expected at least 2"
        print(f"✓ generateAngle sends avatar_style to API (found {avatar_style_count} occurrences)")


class TestFrontendStartAuto360Logic:
    """Test frontend startAuto360 function passes correct sourceUrl for 3D styles"""
    
    def test_start_auto360_accepts_style_param(self):
        """Verify startAuto360 accepts style parameter"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Check function signature
        assert "startAuto360 = async (sourceUrl, clothing = 'company_uniform', style = 'realistic')" in content or \
               'startAuto360 = async (sourceUrl, clothing = "company_uniform", style = "realistic")' in content, \
               "startAuto360 doesn't accept style parameter"
        print("✓ startAuto360 accepts style parameter")
    
    def test_start_auto360_sends_avatar_style_to_api(self):
        """Verify startAuto360 sends avatar_style to API"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Check for avatar_style: style in the API call
        assert "avatar_style: style" in content, "avatar_style not sent in startAuto360 API call"
        print("✓ startAuto360 sends avatar_style to API")


class TestFrontendDownloadButton:
    """Test download button uses fetch+blob pattern instead of <a target=_blank>"""
    
    def test_download_button_uses_fetch_blob(self):
        """Verify download button uses fetch+blob download pattern"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Find download button section
        download_match = re.search(r'data-testid="download-avatar-btn".*?</button>', content, re.DOTALL)
        assert download_match, "download-avatar-btn not found"
        download_section = download_match.group(0)
        
        # Check for fetch+blob pattern
        assert "fetch(" in download_section, "fetch() not used in download button"
        assert ".blob()" in download_section, ".blob() not used in download button"
        assert "createObjectURL" in download_section, "createObjectURL not used in download button"
        assert "revokeObjectURL" in download_section, "revokeObjectURL not used (memory leak)"
        print("✓ Download button uses fetch+blob download pattern")
    
    def test_download_button_not_using_target_blank(self):
        """Verify download button doesn't use target=_blank (which opens in new tab)"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Find download button section
        download_match = re.search(r'data-testid="download-avatar-btn".*?</button>', content, re.DOTALL)
        assert download_match, "download-avatar-btn not found"
        download_section = download_match.group(0)
        
        # Should NOT have target="_blank" in the download logic
        assert 'target="_blank"' not in download_section and "target='_blank'" not in download_section, \
               "Download button still uses target=_blank (opens in new tab instead of downloading)"
        print("✓ Download button doesn't use target=_blank")


class TestFrontendAvatarStylePersistence:
    """Test avatar_style is persisted when saving/loading avatars"""
    
    def test_save_avatar_and_close_persists_avatar_style(self):
        """Verify saveAvatarAndClose persists avatar_style"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Check that avatar_style is included in the saved object (both edit and new cases)
        # Line 447: avatar_style: tempAvatar.avatar_style || 'realistic',
        # Line 463: avatar_style: tempAvatar.avatar_style || 'realistic',
        assert content.count("avatar_style: tempAvatar.avatar_style || 'realistic'") >= 2, \
               "avatar_style not persisted in saveAvatarAndClose (both edit and new cases)"
        print("✓ saveAvatarAndClose persists avatar_style in both edit and new avatar cases")
    
    def test_save_avatar_as_new_persists_avatar_style(self):
        """Verify saveAvatarAsNew persists avatar_style"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Line 487: avatar_style: tempAvatar.avatar_style || 'realistic',
        # This is the 3rd occurrence (after the 2 in saveAvatarAndClose)
        assert content.count("avatar_style: tempAvatar.avatar_style || 'realistic'") >= 3, \
               "avatar_style not persisted in saveAvatarAsNew"
        print("✓ saveAvatarAsNew persists avatar_style")
    
    def test_open_avatar_for_edit_restores_avatar_style(self):
        """Verify openAvatarForEdit restores avatar_style from saved avatar"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Check that avatar_style is restored from av.avatar_style
        # Line 504: avatar_style: av.avatar_style || 'realistic',
        assert "avatar_style: av.avatar_style || 'realistic'" in content, \
               "avatar_style not restored in openAvatarForEdit"
        print("✓ openAvatarForEdit restores avatar_style from saved avatar")


class TestLandingV2Route:
    """Test Landing V2 renders at / route"""
    
    def test_landing_v2_route_exists(self):
        """Verify / route renders Landing V2"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200, f"Landing page returned {response.status_code}"
        print("✓ Landing page loads at / route")
    
    def test_app_js_routes_to_landing_v2(self):
        """Verify App.js routes / to LandingV2"""
        app_path = "/app/frontend/src/App.js"
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check for LandingV2 import and route
        assert "LandingV2" in content, "LandingV2 not imported in App.js"
        assert 'path="/"' in content or "path='/'" in content, "/ route not defined in App.js"
        print("✓ App.js routes '/' to LandingV2")


class TestTempAvatarStoresAvatarStyle:
    """Test tempAvatar stores avatar_style when created"""
    
    def test_temp_avatar_stores_avatar_style_from_prompt(self):
        """Verify tempAvatar stores avatar_style when created from prompt mode"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Line 420: avatar_style: style,
        # This is in generateAvatarFromPrompt
        assert "avatar_style: style," in content, "avatar_style not set in tempAvatar from prompt mode"
        print("✓ tempAvatar stores avatar_style when created from prompt mode")
    
    def test_temp_avatar_stores_avatar_style_from_photo(self):
        """Verify tempAvatar stores avatar_style when created from photo mode"""
        jsx_path = "/app/frontend/src/components/PipelineView.jsx"
        with open(jsx_path, 'r') as f:
            content = f.read()
        
        # Line 365: avatar_style: 'realistic',
        # This is in generateAvatarFromPhoto
        assert "avatar_style: 'realistic'," in content, "avatar_style not set in tempAvatar from photo mode"
        print("✓ tempAvatar stores avatar_style when created from photo mode")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
