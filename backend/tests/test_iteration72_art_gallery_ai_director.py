"""
Iteration 72: Art Gallery UI + AI Image Director Backend Tests

Tests:
1. Backend module imports for AI Director functions
2. _ai_analyze_video_for_crops function structure validation
3. _create_video_variants integration with AI Director
4. API health endpoint
5. API campaigns endpoint (authenticated)
"""

import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-campaign-hub.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestModuleImports:
    """Test that all AI Director functions are properly importable"""
    
    def test_import_ai_analyze_video_for_crops(self):
        """Verify _ai_analyze_video_for_crops function exists and is importable"""
        from pipeline.media import _ai_analyze_video_for_crops
        assert callable(_ai_analyze_video_for_crops), "_ai_analyze_video_for_crops should be callable"
        print("✓ _ai_analyze_video_for_crops importable")
    
    def test_import_create_video_variants(self):
        """Verify _create_video_variants function exists and is importable"""
        from pipeline.media import _create_video_variants
        assert callable(_create_video_variants), "_create_video_variants should be callable"
        print("✓ _create_video_variants importable")
    
    def test_import_create_platform_variants(self):
        """Verify _create_platform_variants function exists"""
        from pipeline.media import _create_platform_variants
        assert callable(_create_platform_variants), "_create_platform_variants should be callable"
        print("✓ _create_platform_variants importable")
    
    def test_import_pipeline_engine(self):
        """Verify pipeline engine imports media functions correctly"""
        from pipeline.engine import _create_video_variants
        assert callable(_create_video_variants), "Engine should import _create_video_variants"
        print("✓ pipeline.engine imports media functions correctly")


class TestAIDirectorFunctionStructure:
    """Test AI Director function signatures and async nature"""
    
    def test_ai_analyze_function_is_async(self):
        """Verify _ai_analyze_video_for_crops is an async function"""
        import inspect
        from pipeline.media import _ai_analyze_video_for_crops
        assert inspect.iscoroutinefunction(_ai_analyze_video_for_crops), "Should be async"
        print("✓ _ai_analyze_video_for_crops is async")
    
    def test_create_video_variants_is_async(self):
        """Verify _create_video_variants is an async function"""
        import inspect
        from pipeline.media import _create_video_variants
        assert inspect.iscoroutinefunction(_create_video_variants), "Should be async"
        print("✓ _create_video_variants is async")
    
    def test_ai_analyze_accepts_expected_params(self):
        """Verify function signature accepts pipeline_id, master_path, master_w, master_h, platforms"""
        import inspect
        from pipeline.media import _ai_analyze_video_for_crops
        sig = inspect.signature(_ai_analyze_video_for_crops)
        params = list(sig.parameters.keys())
        assert 'pipeline_id' in params, "Should accept pipeline_id"
        assert 'master_path' in params, "Should accept master_path"
        assert 'master_w' in params, "Should accept master_w"
        assert 'master_h' in params, "Should accept master_h"
        assert 'platforms' in params, "Should accept platforms"
        print(f"✓ _ai_analyze_video_for_crops params: {params}")


class TestAPIEndpoints:
    """Test API endpoints are working"""
    
    def test_health_endpoint(self):
        """Health check endpoint should return status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') in ['ok', 'healthy'], f"Expected ok/healthy, got {data.get('status')}"
        print(f"✓ /api/health: {data}")
    
    def test_login_and_get_token(self):
        """Login to get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        # Login may return 200 or 401 depending on test data existence
        if response.status_code == 200:
            data = response.json()
            assert 'token' in data or 'access_token' in data, "Should return token"
            print(f"✓ Login successful")
            return data.get('token') or data.get('access_token')
        else:
            print(f"⚠ Login returned {response.status_code} - test user may not exist")
            pytest.skip("Test user not available")
    
    def test_campaigns_endpoint_requires_auth(self):
        """Campaigns endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ /api/campaigns requires authentication")


class TestPipelineConfig:
    """Test pipeline configuration for video formats"""
    
    def test_video_platform_formats_exist(self):
        """Verify VIDEO_PLATFORM_FORMATS config exists"""
        from pipeline.config import VIDEO_PLATFORM_FORMATS
        assert isinstance(VIDEO_PLATFORM_FORMATS, dict), "Should be a dict"
        assert 'tiktok' in VIDEO_PLATFORM_FORMATS, "Should include tiktok"
        assert 'instagram_reels' in VIDEO_PLATFORM_FORMATS, "Should include instagram_reels"
        print(f"✓ VIDEO_PLATFORM_FORMATS: {list(VIDEO_PLATFORM_FORMATS.keys())}")
    
    def test_platform_aspect_ratios_exist(self):
        """Verify PLATFORM_ASPECT_RATIOS config exists"""
        from pipeline.config import PLATFORM_ASPECT_RATIOS
        assert isinstance(PLATFORM_ASPECT_RATIOS, dict), "Should be a dict"
        print(f"✓ PLATFORM_ASPECT_RATIOS: {list(PLATFORM_ASPECT_RATIOS.keys())}")


class TestMediaUtilDependencies:
    """Test media utility dependencies"""
    
    def test_ffprobe_duration_exists(self):
        """Verify _ffprobe_duration helper exists"""
        from pipeline.utils import _ffprobe_duration
        assert callable(_ffprobe_duration), "Should be callable"
        print("✓ _ffprobe_duration importable")
    
    def test_ffprobe_dimensions_exists(self):
        """Verify _ffprobe_dimensions helper exists"""
        from pipeline.utils import _ffprobe_dimensions
        assert callable(_ffprobe_dimensions), "Should be callable"
        print("✓ _ffprobe_dimensions importable")
    
    def test_ffmpeg_path_exists(self):
        """Verify FFMPEG_PATH is defined"""
        from pipeline.utils import FFMPEG_PATH
        assert FFMPEG_PATH is not None, "FFMPEG_PATH should be defined"
        print(f"✓ FFMPEG_PATH: {FFMPEG_PATH}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
