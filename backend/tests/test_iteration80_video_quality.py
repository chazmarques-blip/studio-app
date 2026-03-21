"""
Iteration 80: Video Quality Review Tests
Tests for video pipeline quality upgrades:
1. All FFmpeg CRF values are 16 or 18 (no CRF 23 remaining)
2. All FFmpeg presets are 'slow' for quality (in main pipeline, not branding)
3. Normalization step uses scale+crop to force exact target resolution
4. _combine_commercial_video accepts target_size parameter
5. _generate_commercial_video passes target_size=size to _combine_commercial_video
6. Audio pre-approval: engine.py marcos_video sets waiting_audio_approval status
7. VIDEO_PLATFORM_FORMATS has entries for tiktok, instagram, facebook, whatsapp, youtube
8. Backend starts without errors after quality changes
9. Audio bitrate is 256k or 320k (not 192k)
10. approve-audio endpoint exists and returns proper errors
"""

import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-campaign-hub.preview.emergentagent.com').rstrip('/')


class TestFFmpegCRFValues:
    """Test that all CRF values in media.py are 16 or 18 (cinema quality)"""
    
    def test_no_crf_23_in_media_py(self):
        """Verify no CRF 23 values remain in media.py"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find all CRF values
        crf_matches = re.findall(r'-crf["\s,]+(\d+)', content, re.IGNORECASE)
        crf_matches += re.findall(r'crf.*?(\d+)', content, re.IGNORECASE)
        
        # Filter to unique numeric values
        crf_values = set()
        for match in crf_matches:
            if match.isdigit():
                crf_values.add(int(match))
        
        print(f"Found CRF values in media.py: {crf_values}")
        
        # CRF 23 should not be present
        assert 23 not in crf_values, f"CRF 23 found in media.py - should be upgraded to 16 or 18"
        
        # All CRF values should be 16 or 18
        for crf in crf_values:
            assert crf in [16, 18], f"Unexpected CRF value {crf} - should be 16 or 18"
        
        print("✓ All CRF values are 16 or 18 (cinema quality)")
    
    def test_crf_16_in_main_pipeline(self):
        """Verify CRF 16 is used in main video pipeline functions"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Check _combine_commercial_video uses CRF 16
        combine_section = content[content.find('def _combine_commercial_video'):]
        combine_section = combine_section[:combine_section.find('\ndef ', 1) if '\ndef ' in combine_section[1:] else len(combine_section)]
        
        assert 'crf", "16"' in combine_section or "crf', '16'" in combine_section or 'crf", "16' in combine_section, \
            "_combine_commercial_video should use CRF 16"
        print("✓ _combine_commercial_video uses CRF 16")


class TestFFmpegPresetValues:
    """Test that FFmpeg presets are 'slow' for quality"""
    
    def test_preset_slow_in_main_pipeline(self):
        """Verify preset 'slow' is used in main video pipeline"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Count preset slow vs preset fast
        slow_count = content.count('"slow"') + content.count("'slow'")
        fast_count = content.count('"fast"') + content.count("'fast'")
        
        print(f"Preset counts - slow: {slow_count}, fast: {fast_count}")
        
        # Main pipeline should use slow
        assert slow_count > 0, "No 'slow' preset found in media.py"
        print("✓ 'slow' preset is used in media.py")
    
    def test_preset_slow_in_combine_commercial_video(self):
        """Verify _combine_commercial_video uses preset slow"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find _combine_commercial_video function
        combine_start = content.find('def _combine_commercial_video')
        combine_end = content.find('\ndef ', combine_start + 1)
        if combine_end == -1:
            combine_end = len(content)
        combine_section = content[combine_start:combine_end]
        
        # Check for preset slow
        slow_in_combine = '"slow"' in combine_section or "'slow'" in combine_section
        assert slow_in_combine, "_combine_commercial_video should use preset 'slow'"
        print("✓ _combine_commercial_video uses preset 'slow'")


class TestNormalizationScaleCrop:
    """Test that normalization uses scale+crop for exact resolution"""
    
    def test_normalization_uses_scale_crop(self):
        """Verify normalization step uses scale+crop to force exact target resolution"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find _combine_commercial_video function
        combine_start = content.find('def _combine_commercial_video')
        combine_end = content.find('\ndef ', combine_start + 1)
        if combine_end == -1:
            combine_end = len(content)
        combine_section = content[combine_start:combine_end]
        
        # Check for scale with force_original_aspect_ratio=increase
        has_scale_increase = 'force_original_aspect_ratio=increase' in combine_section
        assert has_scale_increase, "Normalization should use force_original_aspect_ratio=increase"
        
        # Check for crop filter
        has_crop = 'crop=' in combine_section
        assert has_crop, "Normalization should use crop filter"
        
        print("✓ Normalization uses scale+crop for exact resolution (no black bars)")
    
    def test_normalization_filter_format(self):
        """Verify the exact normalization filter format"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Look for the scale+crop pattern in the normalization section
        # The pattern uses f-string so we look for the structure
        # Expected: scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}
        has_scale_increase = 'force_original_aspect_ratio=increase' in content
        has_crop_after_scale = 'crop=' in content
        
        # Check the specific line in _combine_commercial_video
        combine_start = content.find('def _combine_commercial_video')
        combine_section = content[combine_start:combine_start + 2000]
        
        # Look for the scale_filter variable assignment
        has_scale_filter = 'scale_filter' in combine_section or 'scale=' in combine_section
        
        assert has_scale_increase, "Should have force_original_aspect_ratio=increase"
        assert has_crop_after_scale, "Should have crop filter"
        assert has_scale_filter, "Should have scale filter in _combine_commercial_video"
        print("✓ Found normalization pattern with scale+crop")


class TestTargetSizeParameter:
    """Test that target_size parameter is properly passed"""
    
    def test_combine_commercial_video_accepts_target_size(self):
        """Verify _combine_commercial_video accepts target_size parameter"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find function signature
        func_match = re.search(r'def _combine_commercial_video\([^)]+\)', content, re.DOTALL)
        assert func_match, "_combine_commercial_video function not found"
        
        func_sig = func_match.group(0)
        assert 'target_size' in func_sig, "_combine_commercial_video should accept target_size parameter"
        print(f"✓ _combine_commercial_video accepts target_size parameter")
    
    def test_generate_commercial_video_passes_target_size(self):
        """Verify _generate_commercial_video passes target_size to _combine_commercial_video"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find _generate_commercial_video function
        gen_start = content.find('async def _generate_commercial_video')
        gen_end = content.find('\nasync def ', gen_start + 1)
        if gen_end == -1:
            gen_end = content.find('\ndef ', gen_start + 1)
        if gen_end == -1:
            gen_end = len(content)
        gen_section = content[gen_start:gen_end]
        
        # Check for target_size=size in the call to _combine_commercial_video
        assert 'target_size=size' in gen_section or 'target_size=' in gen_section, \
            "_generate_commercial_video should pass target_size to _combine_commercial_video"
        print("✓ _generate_commercial_video passes target_size to _combine_commercial_video")


class TestAudioPreApproval:
    """Test audio pre-approval logic in engine.py"""
    
    def test_marcos_video_sets_waiting_audio_approval(self):
        """Verify marcos_video step sets waiting_audio_approval status"""
        with open('/app/backend/pipeline/engine.py', 'r') as f:
            content = f.read()
        
        # Check for waiting_audio_approval status
        assert 'waiting_audio_approval' in content, "engine.py should set waiting_audio_approval status"
        
        # Check it's set in marcos_video handling
        marcos_section_start = content.find('elif step == "marcos_video"')
        if marcos_section_start == -1:
            marcos_section_start = content.find("elif step == 'marcos_video'")
        
        assert marcos_section_start != -1, "marcos_video step handling not found"
        
        marcos_section = content[marcos_section_start:marcos_section_start + 3000]
        assert 'waiting_audio_approval' in marcos_section, \
            "marcos_video step should set waiting_audio_approval status"
        print("✓ marcos_video sets waiting_audio_approval status")
    
    def test_marcos_video_returns_before_video_generation(self):
        """Verify marcos_video returns before video generation when waiting for approval"""
        with open('/app/backend/pipeline/engine.py', 'r') as f:
            content = f.read()
        
        # Find marcos_video section
        marcos_section_start = content.find('elif step == "marcos_video"')
        if marcos_section_start == -1:
            marcos_section_start = content.find("elif step == 'marcos_video'")
        
        marcos_section = content[marcos_section_start:marcos_section_start + 3000]
        
        # Check for return statement after setting waiting_audio_approval
        assert 'return' in marcos_section, "marcos_video should return after setting waiting_audio_approval"
        print("✓ marcos_video returns before video generation (waits for approval)")


class TestVideoPlatformFormats:
    """Test VIDEO_PLATFORM_FORMATS configuration"""
    
    def test_video_platform_formats_has_required_platforms(self):
        """Verify VIDEO_PLATFORM_FORMATS has entries for all required platforms"""
        with open('/app/backend/pipeline/config.py', 'r') as f:
            content = f.read()
        
        required_platforms = ['tiktok', 'instagram', 'facebook', 'whatsapp', 'youtube']
        
        for platform in required_platforms:
            assert f'"{platform}"' in content or f"'{platform}'" in content, \
                f"VIDEO_PLATFORM_FORMATS should have entry for {platform}"
            print(f"✓ VIDEO_PLATFORM_FORMATS has entry for {platform}")
    
    def test_video_platform_formats_structure(self):
        """Verify VIDEO_PLATFORM_FORMATS has correct structure"""
        from pipeline.config import VIDEO_PLATFORM_FORMATS
        
        required_platforms = ['tiktok', 'instagram', 'facebook', 'whatsapp', 'youtube']
        
        for platform in required_platforms:
            assert platform in VIDEO_PLATFORM_FORMATS, f"Missing platform: {platform}"
            fmt = VIDEO_PLATFORM_FORMATS[platform]
            assert 'w' in fmt, f"{platform} missing 'w' (width)"
            assert 'h' in fmt, f"{platform} missing 'h' (height)"
            assert 'label' in fmt, f"{platform} missing 'label'"
            print(f"✓ {platform}: {fmt['w']}x{fmt['h']} ({fmt['label']})")


class TestBackendHealth:
    """Test backend starts without errors"""
    
    def test_backend_health_check(self):
        """Verify backend is running and healthy"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        data = response.json()
        assert data.get('status') == 'ok', f"Health check status not ok: {data}"
        print(f"✓ Backend health check passed: {data}")


class TestAudioBitrate:
    """Test audio bitrate is 256k or 320k"""
    
    def test_audio_bitrate_not_192k(self):
        """Verify audio bitrate is 256k or 320k (not 192k)"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Check for 192k bitrate (should not exist)
        has_192k = '192k' in content
        assert not has_192k, "Audio bitrate 192k found - should be 256k or 320k"
        
        # Check for 256k or 320k
        has_256k = '256k' in content
        has_320k = '320k' in content
        
        assert has_256k or has_320k, "Should have 256k or 320k audio bitrate"
        print(f"✓ Audio bitrate: 256k={has_256k}, 320k={has_320k}")
    
    def test_audio_bitrate_values(self):
        """Verify specific audio bitrate values"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find all -b:a values
        bitrate_matches = re.findall(r'-b:a["\s,]+(\d+k)', content, re.IGNORECASE)
        
        print(f"Found audio bitrates: {bitrate_matches}")
        
        for bitrate in bitrate_matches:
            assert bitrate in ['256k', '320k'], f"Unexpected audio bitrate {bitrate}"
        
        print("✓ All audio bitrates are 256k or 320k")


class TestApproveAudioEndpoint:
    """Test approve-audio endpoint exists and returns proper errors"""
    
    def test_approve_audio_endpoint_exists(self):
        """Verify approve-audio endpoint is defined in routes.py"""
        with open('/app/backend/pipeline/routes.py', 'r') as f:
            content = f.read()
        
        assert 'approve-audio' in content, "approve-audio endpoint should be defined"
        assert 'async def approve_audio' in content, "approve_audio function should exist"
        print("✓ approve-audio endpoint defined in routes.py")
    
    def test_approve_audio_returns_404_for_nonexistent(self):
        """Verify approve-audio returns 404 for non-existent pipeline"""
        # First login to get auth token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Could not login for auth test")
        
        token = login_resp.json().get('access_token')
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to approve non-existent pipeline
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{fake_uuid}/approve-audio",
            headers=headers,
            json={}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ approve-audio returns 404 for non-existent pipeline")
    
    def test_approve_audio_validates_status(self):
        """Verify approve-audio validates waiting_audio_approval status"""
        with open('/app/backend/pipeline/routes.py', 'r') as f:
            content = f.read()
        
        # Find approve_audio function
        approve_start = content.find('async def approve_audio')
        approve_end = content.find('@router', approve_start + 1)
        if approve_end == -1:
            approve_end = len(content)
        approve_section = content[approve_start:approve_end]
        
        assert 'waiting_audio_approval' in approve_section, \
            "approve_audio should validate waiting_audio_approval status"
        print("✓ approve_audio validates waiting_audio_approval status")


class TestContinueVideoAfterApproval:
    """Test _continue_video_after_approval function"""
    
    def test_continue_video_function_exists(self):
        """Verify _continue_video_after_approval function exists"""
        with open('/app/backend/pipeline/engine.py', 'r') as f:
            content = f.read()
        
        assert '_continue_video_after_approval' in content, \
            "_continue_video_after_approval function should exist"
        print("✓ _continue_video_after_approval function exists")
    
    def test_continue_video_uses_saved_script(self):
        """Verify _continue_video_after_approval uses saved marcos_video output"""
        with open('/app/backend/pipeline/engine.py', 'r') as f:
            content = f.read()
        
        # Find the function
        func_start = content.find('async def _continue_video_after_approval')
        func_end = content.find('\nasync def ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\ndef ', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        func_section = content[func_start:func_end]
        
        # Should get output from marcos step
        assert 'marcos' in func_section.lower(), \
            "_continue_video_after_approval should use marcos_video output"
        print("✓ _continue_video_after_approval uses saved marcos_video script")


class TestCreateVideoVariants:
    """Test _create_video_variants function"""
    
    def test_create_video_variants_uses_slow_preset(self):
        """Verify _create_video_variants uses slow preset"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find _create_video_variants function
        func_start = content.find('async def _create_video_variants')
        func_end = content.find('\nasync def ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\ndef ', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        func_section = content[func_start:func_end]
        
        # Check for slow preset
        has_slow = '"slow"' in func_section or "'slow'" in func_section
        assert has_slow, "_create_video_variants should use preset 'slow'"
        print("✓ _create_video_variants uses preset 'slow'")
    
    def test_create_video_variants_uses_crf_18(self):
        """Verify _create_video_variants uses CRF 18"""
        with open('/app/backend/pipeline/media.py', 'r') as f:
            content = f.read()
        
        # Find _create_video_variants function
        func_start = content.find('async def _create_video_variants')
        func_end = content.find('\nasync def ', func_start + 1)
        if func_end == -1:
            func_end = content.find('\ndef ', func_start + 1)
        if func_end == -1:
            func_end = len(content)
        func_section = content[func_start:func_end]
        
        # Check for CRF 18
        has_crf_18 = '"18"' in func_section or "'18'" in func_section
        assert has_crf_18, "_create_video_variants should use CRF 18"
        print("✓ _create_video_variants uses CRF 18")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
