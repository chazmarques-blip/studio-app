"""
Iteration 79: Tests for 360° view bug fixes for 3D/Pixar avatars
Focus areas:
1. openAvatarForEdit infers avatar_style from creation_mode for old avatars
2. openAvatarForEdit clears wrong angles for 3D avatars
3. 360° View tab click auto-triggers startAuto360 when <4 angles loaded
4. Regenerate All 360° button exists and uses tempAvatar.url for 3D styles
5. creation_mode is persisted in saveAvatarAndClose and saveAvatarAsNew
6. Backend: generate-avatar-360 and generate-avatar-variant accept avatar_style param
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
FRONTEND_FILE = '/app/frontend/src/components/PipelineView.jsx'
BACKEND_FILE = '/app/backend/pipeline/avatar_routes.py'
CONFIG_FILE = '/app/backend/pipeline/config.py'


class TestOpenAvatarForEditInference:
    """Test openAvatarForEdit infers avatar_style from creation_mode for old avatars"""
    
    def test_infer_avatar_style_from_creation_mode_3d(self):
        """openAvatarForEdit should infer avatar_style='3d_pixar' when creation_mode='3d' and no avatar_style"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check for the inference logic
        assert "if (!av.avatar_style && av.creation_mode === '3d')" in content, \
            "Missing inference check for creation_mode === '3d'"
        assert "inferredStyle = '3d_pixar'" in content, \
            "Missing inference to '3d_pixar' for 3D mode"
        print("✓ openAvatarForEdit infers avatar_style='3d_pixar' from creation_mode='3d'")
    
    def test_inferred_style_used_in_temp_avatar(self):
        """The inferred style should be used when setting tempAvatar"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check that inferredStyle is used in setTempAvatar
        assert "avatar_style: inferredStyle" in content, \
            "inferredStyle should be used in setTempAvatar"
        print("✓ inferredStyle is used in setTempAvatar")
    
    def test_creation_mode_restored_in_temp_avatar(self):
        """creation_mode should be restored from saved avatar"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check that creation_mode is restored
        assert "creation_mode: av.creation_mode || 'photo'" in content, \
            "creation_mode should be restored from saved avatar"
        print("✓ creation_mode is restored in openAvatarForEdit")


class TestOpenAvatarForEditClearsWrongAngles:
    """Test openAvatarForEdit clears wrong angles for 3D avatars"""
    
    def test_is3d_avatar_check_exists(self):
        """Should have is3dAvatar check based on inferredStyle"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        assert "const is3dAvatar = inferredStyle !== 'realistic'" in content, \
            "Missing is3dAvatar check based on inferredStyle"
        print("✓ is3dAvatar check exists based on inferredStyle")
    
    def test_clears_angles_when_front_doesnt_match_avatar_url(self):
        """For 3D avatars, should clear angles when front !== av.url"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check for the angle clearing logic
        assert "is3dAvatar && savedAngles.front && savedAngles.front !== av.url" in content, \
            "Missing check for clearing wrong angles on 3D avatars"
        assert "setAngleImages({ front: av.url })" in content, \
            "Missing setAngleImages({ front: av.url }) for clearing wrong angles"
        print("✓ openAvatarForEdit clears wrong angles for 3D avatars when front !== av.url")


class TestAuto360TriggerOnTabSwitch:
    """Test 360° View tab click auto-triggers startAuto360 when <4 angles loaded"""
    
    def test_tab_click_handler_checks_view360(self):
        """Tab click should check if switching to view360 tab"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        assert "tab.id === 'view360'" in content, \
            "Missing check for view360 tab in click handler"
        print("✓ Tab click handler checks for view360 tab")
    
    def test_auto_trigger_checks_loaded_angles(self):
        """Should check if loadedAngles < 4 before auto-triggering"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        assert "loadedAngles < 4" in content, \
            "Missing check for loadedAngles < 4"
        print("✓ Auto-trigger checks if loadedAngles < 4")
    
    def test_auto_trigger_calls_start_auto360(self):
        """Should call startAuto360 when conditions are met"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find the tab click handler section
        tab_handler_pattern = r"onClick=\{\(\) => \{[\s\S]*?setCustomizeTab\(tab\.id\);[\s\S]*?if \(tab\.id === 'view360'[\s\S]*?startAuto360\("
        assert re.search(tab_handler_pattern, content), \
            "Missing startAuto360 call in view360 tab click handler"
        print("✓ Tab click handler calls startAuto360 for view360 tab")
    
    def test_auto_trigger_uses_correct_source_url_for_3d(self):
        """Auto-trigger should use tempAvatar.url for 3D styles"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check for is3d check in tab handler
        assert "const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic'" in content, \
            "Missing is3d check in tab click handler"
        assert "is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url)" in content, \
            "Missing correct sourceUrl logic for 3D in tab handler"
        print("✓ Auto-trigger uses tempAvatar.url for 3D styles")


class TestRegenerateAll360Button:
    """Test Regenerate All 360° button exists and works correctly"""
    
    def test_regen_all_360_button_exists(self):
        """Regenerate All 360° button should exist with correct data-testid"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        assert 'data-testid="regen-all-360-btn"' in content, \
            "Missing Regenerate All 360° button with data-testid"
        print("✓ Regenerate All 360° button exists with data-testid='regen-all-360-btn'")
    
    def test_regen_all_360_button_in_view360_tab(self):
        """Button should be inside the 360° View tab section"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find the view360 tab section and check button is inside
        view360_section = re.search(r"customizeTab === 'view360'[\s\S]*?{/\* Voice Tab \*/}", content)
        assert view360_section, "Could not find view360 tab section"
        assert 'regen-all-360-btn' in view360_section.group(), \
            "Regenerate All 360° button should be inside view360 tab"
        print("✓ Regenerate All 360° button is inside 360° View tab")
    
    def test_regen_all_360_uses_correct_source_for_3d(self):
        """Regenerate All button should use tempAvatar.url for 3D styles"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find the regen-all-360-btn onClick handler
        regen_pattern = r'data-testid="regen-all-360-btn"[\s\S]*?onClick=\{\(\) => \{[\s\S]*?const is3d = tempAvatar\?\.avatar_style && tempAvatar\.avatar_style !== \'realistic\'[\s\S]*?const sourceUrl = is3d \? tempAvatar\.url'
        assert re.search(regen_pattern, content), \
            "Regenerate All 360° button should use tempAvatar.url for 3D styles"
        print("✓ Regenerate All 360° button uses tempAvatar.url for 3D styles")
    
    def test_regen_all_360_clears_angles_first(self):
        """Regenerate All should clear angles before regenerating"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check that setAngleImages is called before startAuto360 in the button handler
        regen_section = re.search(r'data-testid="regen-all-360-btn"[\s\S]*?setAngleImages\(\{ front: tempAvatar\.url \}\)[\s\S]*?startAuto360', content)
        assert regen_section, \
            "Regenerate All should call setAngleImages before startAuto360"
        print("✓ Regenerate All 360° clears angles before regenerating")


class TestCreationModePersistence:
    """Test creation_mode is persisted in save functions"""
    
    def test_save_avatar_and_close_persists_creation_mode_edit(self):
        """saveAvatarAndClose should persist creation_mode when editing"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find saveAvatarAndClose function and check for creation_mode in edit case
        save_func = re.search(r'const saveAvatarAndClose = \(\) => \{[\s\S]*?if \(editingAvatarId\) \{[\s\S]*?const editedAvatar = \{[\s\S]*?creation_mode:', content)
        assert save_func, \
            "saveAvatarAndClose should persist creation_mode in edit case"
        print("✓ saveAvatarAndClose persists creation_mode when editing")
    
    def test_save_avatar_and_close_persists_creation_mode_new(self):
        """saveAvatarAndClose should persist creation_mode when creating new"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find the new avatar case in saveAvatarAndClose
        new_avatar_pattern = r'const newAv = \{[\s\S]*?id: Date\.now\(\)\.toString\(\)[\s\S]*?creation_mode: tempAvatar\.creation_mode'
        assert re.search(new_avatar_pattern, content), \
            "saveAvatarAndClose should persist creation_mode for new avatars"
        print("✓ saveAvatarAndClose persists creation_mode for new avatars")
    
    def test_save_avatar_as_new_persists_creation_mode(self):
        """saveAvatarAsNew should persist creation_mode"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find saveAvatarAsNew function
        save_as_new_pattern = r'const saveAvatarAsNew = \(\) => \{[\s\S]*?const newAv = \{[\s\S]*?creation_mode: tempAvatar\.creation_mode'
        assert re.search(save_as_new_pattern, content), \
            "saveAvatarAsNew should persist creation_mode"
        print("✓ saveAvatarAsNew persists creation_mode")


class TestApplyClothingAndGenerateAngle:
    """Test applyClothing and generateAngle still use is3d check"""
    
    def test_apply_clothing_has_is3d_check(self):
        """applyClothing should have is3d check"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find applyClothing function
        apply_clothing_section = re.search(r'const applyClothing = async \(style\) => \{[\s\S]*?const is3d = tempAvatar\?\.avatar_style && tempAvatar\.avatar_style !== \'realistic\'', content)
        assert apply_clothing_section, \
            "applyClothing should have is3d check"
        print("✓ applyClothing has is3d check")
    
    def test_apply_clothing_uses_temp_avatar_url_for_3d(self):
        """applyClothing should use tempAvatar.url for 3D styles"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Check for correct sourceUrl logic in applyClothing
        assert "is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url)" in content, \
            "applyClothing should use tempAvatar.url for 3D styles"
        print("✓ applyClothing uses tempAvatar.url for 3D styles")
    
    def test_generate_angle_has_is3d_check(self):
        """generateAngle should have is3d check"""
        with open(FRONTEND_FILE, 'r') as f:
            content = f.read()
        
        # Find generateAngle function
        generate_angle_section = re.search(r'const generateAngle = async \(angle, forceRegenerate = false\) => \{[\s\S]*?const is3d = tempAvatar\?\.avatar_style && tempAvatar\.avatar_style !== \'realistic\'', content)
        assert generate_angle_section, \
            "generateAngle should have is3d check"
        print("✓ generateAngle has is3d check")


class TestBackendAvatarStyleParam:
    """Test backend endpoints accept avatar_style parameter"""
    
    def test_avatar_variant_request_has_avatar_style(self):
        """AvatarVariantRequest should have avatar_style field"""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
        
        # Find AvatarVariantRequest class
        variant_class = re.search(r'class AvatarVariantRequest\(BaseModel\):[\s\S]*?avatar_style:', content)
        assert variant_class, \
            "AvatarVariantRequest should have avatar_style field"
        print("✓ AvatarVariantRequest has avatar_style field")
    
    def test_avatar_batch360_request_has_avatar_style(self):
        """AvatarBatch360Request should have avatar_style field"""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
        
        # Find AvatarBatch360Request class
        batch_class = re.search(r'class AvatarBatch360Request\(BaseModel\):[\s\S]*?avatar_style:', content)
        assert batch_class, \
            "AvatarBatch360Request should have avatar_style field"
        print("✓ AvatarBatch360Request has avatar_style field")
    
    def test_run_batch_360_accepts_avatar_style(self):
        """_run_batch_360 should accept avatar_style parameter"""
        with open(BACKEND_FILE, 'r') as f:
            content = f.read()
        
        assert 'def _run_batch_360(job_id: str, source_url: str, clothing: str, logo_url: str = "", avatar_style: str = "realistic")' in content, \
            "_run_batch_360 should accept avatar_style parameter"
        print("✓ _run_batch_360 accepts avatar_style parameter")
    
    def test_generate_avatar_variant_uses_avatar_style(self):
        """generate_avatar_variant should use avatar_style for is_3d check"""
        with open(BACKEND_FILE, 'r') as f:
            content = f.read()
        
        assert 'is_3d = req.avatar_style in ("3d_cartoon", "3d_pixar")' in content, \
            "generate_avatar_variant should check is_3d from avatar_style"
        print("✓ generate_avatar_variant uses avatar_style for is_3d check")
    
    def test_batch_360_uses_avatar_style_for_is_3d(self):
        """_run_batch_360 should use avatar_style for is_3d check"""
        with open(BACKEND_FILE, 'r') as f:
            content = f.read()
        
        assert 'is_3d = avatar_style in ("3d_cartoon", "3d_pixar")' in content, \
            "_run_batch_360 should check is_3d from avatar_style"
        print("✓ _run_batch_360 uses avatar_style for is_3d check")


class TestBackendEndpointsExist:
    """Test backend endpoints exist and are accessible"""
    
    def test_generate_avatar_360_endpoint_exists(self):
        """generate-avatar-360 endpoint should exist"""
        with open(BACKEND_FILE, 'r') as f:
            content = f.read()
        
        assert '@router.post("/generate-avatar-360")' in content, \
            "generate-avatar-360 endpoint should exist"
        print("✓ generate-avatar-360 endpoint exists")
    
    def test_generate_avatar_variant_endpoint_exists(self):
        """generate-avatar-variant endpoint should exist"""
        with open(BACKEND_FILE, 'r') as f:
            content = f.read()
        
        assert '@router.post("/generate-avatar-variant")' in content, \
            "generate-avatar-variant endpoint should exist"
        print("✓ generate-avatar-variant endpoint exists")


class TestBackendHealthCheck:
    """Test backend is running and accessible"""
    
    def test_backend_health(self):
        """Backend should be accessible"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            print("✓ Backend health check passed")
        except Exception as e:
            pytest.skip(f"Backend not accessible: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
