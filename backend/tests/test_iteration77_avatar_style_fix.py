"""
Iteration 77: Test avatar_style parameter fix for 360° view bug
Bug: When generating a 3D Pixar avatar and clicking '360° View', the system was converting 
the 3D avatar to a realistic photo of a person.
Fix: Added avatar_style parameter to generate-avatar-360 and generate-avatar-variant endpoints,
with style-aware prompts that preserve the 3D art style.

Tests:
1. Backend: generate-avatar-360 accepts avatar_style parameter
2. Backend: generate-avatar-variant accepts avatar_style parameter  
3. Backend: Style-aware prompts for 3D styles (no 'photorealistic' in 3D prompts)
4. Frontend: startAuto360 sends avatar_style to API
5. Frontend: generateAngle sends avatar_style to API
6. Frontend: tempAvatar stores avatar_style
7. Landing page V2 at '/' route
8. Audio Pre-Approval endpoint exists
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAvatarStyleBackend:
    """Test avatar_style parameter in backend endpoints"""
    
    def test_avatar_variant_request_has_avatar_style_field(self):
        """AvatarVariantRequest model should have avatar_style field with default 'realistic'"""
        config_path = '/app/backend/pipeline/config.py'
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check AvatarVariantRequest has avatar_style field
        assert 'class AvatarVariantRequest' in content, "AvatarVariantRequest class not found"
        
        # Find the class definition and check for avatar_style
        variant_match = re.search(r'class AvatarVariantRequest\(BaseModel\):(.*?)(?=class|\Z)', content, re.DOTALL)
        assert variant_match, "Could not find AvatarVariantRequest class body"
        variant_body = variant_match.group(1)
        
        assert 'avatar_style' in variant_body, "avatar_style field not in AvatarVariantRequest"
        assert '"realistic"' in variant_body or "'realistic'" in variant_body, "avatar_style default should be 'realistic'"
        print("✓ AvatarVariantRequest has avatar_style field with default 'realistic'")
    
    def test_avatar_batch360_request_has_avatar_style_field(self):
        """AvatarBatch360Request model should have avatar_style field with default 'realistic'"""
        config_path = '/app/backend/pipeline/config.py'
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check AvatarBatch360Request has avatar_style field
        assert 'class AvatarBatch360Request' in content, "AvatarBatch360Request class not found"
        
        # Find the class definition and check for avatar_style
        batch_match = re.search(r'class AvatarBatch360Request\(BaseModel\):(.*?)(?=class|\Z)', content, re.DOTALL)
        assert batch_match, "Could not find AvatarBatch360Request class body"
        batch_body = batch_match.group(1)
        
        assert 'avatar_style' in batch_body, "avatar_style field not in AvatarBatch360Request"
        assert '"realistic"' in batch_body or "'realistic'" in batch_body, "avatar_style default should be 'realistic'"
        print("✓ AvatarBatch360Request has avatar_style field with default 'realistic'")
    
    def test_generate_avatar_variant_uses_avatar_style(self):
        """generate_avatar_variant endpoint should use avatar_style for style-aware prompts"""
        routes_path = '/app/backend/pipeline/avatar_routes.py'
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Find generate_avatar_variant function
        assert 'async def generate_avatar_variant' in content, "generate_avatar_variant function not found"
        
        # Check it uses req.avatar_style
        assert 'req.avatar_style' in content, "generate_avatar_variant should use req.avatar_style"
        
        # Check for 3D style detection
        assert 'is_3d = req.avatar_style in' in content or "is_3d = req.avatar_style in (" in content, \
            "generate_avatar_variant should detect 3D styles"
        
        print("✓ generate_avatar_variant uses avatar_style parameter")
    
    def test_run_batch_360_uses_avatar_style(self):
        """_run_batch_360 function should accept and use avatar_style parameter"""
        routes_path = '/app/backend/pipeline/avatar_routes.py'
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Find _run_batch_360 function signature
        batch_func_match = re.search(r'def _run_batch_360\((.*?)\):', content, re.DOTALL)
        assert batch_func_match, "_run_batch_360 function not found"
        
        func_params = batch_func_match.group(1)
        assert 'avatar_style' in func_params, "_run_batch_360 should accept avatar_style parameter"
        
        # Check it uses avatar_style for 3D detection
        # Find the function body
        func_start = batch_func_match.end()
        # Look for is_3d check within the function
        func_body_snippet = content[func_start:func_start+2000]
        assert 'is_3d = avatar_style in' in func_body_snippet or 'is_3d = avatar_style in (' in func_body_snippet, \
            "_run_batch_360 should detect 3D styles using avatar_style"
        
        print("✓ _run_batch_360 accepts and uses avatar_style parameter")
    
    def test_generate_avatar_360_passes_avatar_style_to_thread(self):
        """generate_avatar_360 endpoint should pass avatar_style to _run_batch_360 thread"""
        routes_path = '/app/backend/pipeline/avatar_routes.py'
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Find generate_avatar_360 endpoint
        assert '@router.post("/generate-avatar-360")' in content, "generate-avatar-360 endpoint not found"
        
        # Check thread creation passes avatar_style
        # Look for Thread(...args=(..., req.avatar_style)...)
        thread_match = re.search(r'Thread\(target=_run_batch_360.*?args=\((.*?)\)', content, re.DOTALL)
        assert thread_match, "Thread creation for _run_batch_360 not found"
        
        thread_args = thread_match.group(1)
        assert 'avatar_style' in thread_args or 'req.avatar_style' in thread_args, \
            "Thread should pass avatar_style to _run_batch_360"
        
        print("✓ generate_avatar_360 passes avatar_style to _run_batch_360 thread")
    
    def test_3d_style_prompts_no_photorealistic(self):
        """3D style prompts should NOT contain 'photorealistic' or 'portrait photographs'"""
        routes_path = '/app/backend/pipeline/avatar_routes.py'
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Find the 3D style prompt sections in generate_avatar_variant
        # Look for the is_3d branch
        variant_func_match = re.search(r'async def generate_avatar_variant.*?(?=@router|async def \w+\(|def \w+\()', content, re.DOTALL)
        assert variant_func_match, "generate_avatar_variant function not found"
        variant_func = variant_func_match.group(0)
        
        # Check that 3D prompts mention "do NOT make it photorealistic"
        assert 'do NOT make it photorealistic' in variant_func or 'Do NOT make it photorealistic' in variant_func, \
            "3D prompts should explicitly say 'do NOT make it photorealistic'"
        
        # Check for 3D style labels
        assert 'Pixar-style 3D animated' in variant_func or '3D cartoon animated' in variant_func, \
            "3D prompts should mention specific 3D style labels"
        
        print("✓ 3D style prompts explicitly avoid photorealistic")
    
    def test_batch_360_3d_prompts_preserve_style(self):
        """_run_batch_360 should use style-preserving prompts for 3D avatars"""
        routes_path = '/app/backend/pipeline/avatar_routes.py'
        with open(routes_path, 'r') as f:
            content = f.read()
        
        # Find _run_batch_360 function
        batch_func_match = re.search(r'def _run_batch_360\(.*?(?=@router|async def \w+\(|def \w+\()', content, re.DOTALL)
        assert batch_func_match, "_run_batch_360 function not found"
        batch_func = batch_func_match.group(0)
        
        # Check for 3D style-aware system message
        assert 'is_3d' in batch_func, "_run_batch_360 should check is_3d"
        
        # Check for style-preserving prompts
        assert 'do NOT make it photorealistic' in batch_func or 'Do NOT make it photorealistic' in batch_func, \
            "_run_batch_360 3D prompts should say 'do NOT make it photorealistic'"
        
        # Check for 3D style labels in prompts
        assert 'style_label' in batch_func or 'Pixar-style' in batch_func, \
            "_run_batch_360 should use style labels for 3D prompts"
        
        print("✓ _run_batch_360 uses style-preserving prompts for 3D avatars")


class TestAvatarStyleFrontend:
    """Test avatar_style parameter in frontend code"""
    
    def test_start_auto360_accepts_style_parameter(self):
        """startAuto360 function should accept style parameter"""
        pipeline_view_path = '/app/frontend/src/components/PipelineView.jsx'
        with open(pipeline_view_path, 'r') as f:
            content = f.read()
        
        # Find startAuto360 function definition
        func_match = re.search(r'const startAuto360 = async \((.*?)\)', content)
        assert func_match, "startAuto360 function not found"
        
        params = func_match.group(1)
        assert 'style' in params, "startAuto360 should accept style parameter"
        
        print("✓ startAuto360 accepts style parameter")
    
    def test_start_auto360_sends_avatar_style_to_api(self):
        """startAuto360 should send avatar_style to the API"""
        pipeline_view_path = '/app/frontend/src/components/PipelineView.jsx'
        with open(pipeline_view_path, 'r') as f:
            content = f.read()
        
        # Find the API call in startAuto360
        # Look for axios.post to generate-avatar-360
        api_call_match = re.search(r'axios\.post\([^)]*generate-avatar-360[^}]*\{([^}]*avatar_style[^}]*)\}', content, re.DOTALL)
        assert api_call_match, "startAuto360 should send avatar_style in API call"
        
        print("✓ startAuto360 sends avatar_style to API")
    
    def test_generate_angle_sends_avatar_style(self):
        """generateAngle function should send avatar_style to the API"""
        pipeline_view_path = '/app/frontend/src/components/PipelineView.jsx'
        with open(pipeline_view_path, 'r') as f:
            content = f.read()
        
        # Find generateAngle function
        assert 'const generateAngle = async' in content, "generateAngle function not found"
        
        # Check it sends avatar_style
        # Look for the API call to generate-avatar-variant
        angle_func_match = re.search(r'const generateAngle = async.*?(?=const \w+ = |$)', content, re.DOTALL)
        assert angle_func_match, "Could not find generateAngle function body"
        angle_func = angle_func_match.group(0)
        
        assert 'avatar_style' in angle_func, "generateAngle should send avatar_style"
        
        print("✓ generateAngle sends avatar_style to API")
    
    def test_temp_avatar_stores_avatar_style(self):
        """tempAvatar object should store avatar_style when created from prompt mode"""
        pipeline_view_path = '/app/frontend/src/components/PipelineView.jsx'
        with open(pipeline_view_path, 'r') as f:
            content = f.read()
        
        # Find generateAvatarFromPrompt function - look for the setTempAvatar call within it
        # The function starts at "const generateAvatarFromPrompt = async" and contains setTempAvatar
        assert 'const generateAvatarFromPrompt = async' in content, "generateAvatarFromPrompt function not found"
        
        # Find the setTempAvatar call that includes avatar_style
        # Look for setTempAvatar({ ... avatar_style: style ... })
        set_temp_avatar_match = re.search(r'setTempAvatar\(\{[^}]*avatar_style:\s*style[^}]*\}\)', content, re.DOTALL)
        assert set_temp_avatar_match, "setTempAvatar should include avatar_style: style"
        
        # Also verify the style variable is derived from avatarCreationMode
        assert "const style = avatarCreationMode === '3d' ? avatarPromptStyle : 'realistic'" in content, \
            "style should be derived from avatarCreationMode"
        
        print("✓ tempAvatar stores avatar_style when created from prompt mode")
    
    def test_start_auto360_called_with_style_after_prompt_generation(self):
        """After generating avatar from prompt, startAuto360 should be called with style"""
        pipeline_view_path = '/app/frontend/src/components/PipelineView.jsx'
        with open(pipeline_view_path, 'r') as f:
            content = f.read()
        
        # Find generateAvatarFromPrompt function
        prompt_func_match = re.search(r'const generateAvatarFromPrompt = async.*?(?=const \w+ = async|const \w+ = \(|$)', content, re.DOTALL)
        assert prompt_func_match, "generateAvatarFromPrompt function not found"
        prompt_func = prompt_func_match.group(0)
        
        # Check startAuto360 is called with style parameter
        assert 'startAuto360(' in prompt_func, "generateAvatarFromPrompt should call startAuto360"
        
        # Check it passes the style
        auto360_call = re.search(r'startAuto360\([^)]+\)', prompt_func)
        assert auto360_call, "startAuto360 call not found in generateAvatarFromPrompt"
        call_args = auto360_call.group(0)
        
        # Should have 3 arguments: url, clothing, style
        assert call_args.count(',') >= 2, "startAuto360 should be called with at least 3 arguments (url, clothing, style)"
        
        print("✓ startAuto360 called with style after prompt generation")


class TestLandingPageV2:
    """Test Landing V2 is served at '/' route"""
    
    def test_app_js_routes_to_landing_v2(self):
        """App.js should route '/' to LandingV2 component"""
        app_path = '/app/frontend/src/App.js'
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check import
        assert 'import LandingV2' in content, "LandingV2 should be imported"
        
        # Check route
        assert 'path="/"' in content, "Root path '/' should be defined"
        assert 'LandingV2' in content, "LandingV2 component should be used"
        
        # Check the route uses LandingV2
        route_match = re.search(r'<Route path="/".*?LandingV2', content, re.DOTALL)
        assert route_match, "Route '/' should use LandingV2 component"
        
        print("✓ App.js routes '/' to LandingV2")
    
    def test_landing_v2_page_loads(self):
        """Landing V2 page should load at root URL"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200, f"Landing page should return 200, got {response.status_code}"
        print("✓ Landing V2 page loads at '/'")


class TestAudioPreApprovalEndpoint:
    """Test Audio Pre-Approval endpoint exists"""
    
    def test_approve_audio_endpoint_returns_404_for_nonexistent(self):
        """POST /api/campaigns/pipeline/{id}/approve-audio should return 404 for non-existent pipeline"""
        # Use a valid UUID format that doesn't exist
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{fake_id}/approve-audio",
            json={"selection": 1, "feedback": ""},
            timeout=10
        )
        # Should return 404 (not found) or 401 (unauthorized) - endpoint exists
        assert response.status_code in [404, 401, 422], \
            f"approve-audio endpoint should exist, got {response.status_code}"
        print(f"✓ approve-audio endpoint exists (returns {response.status_code} for non-existent pipeline)")
    
    def test_approve_audio_endpoint_defined_in_routes(self):
        """approve-audio endpoint should be defined in routes.py"""
        routes_path = '/app/backend/pipeline/routes.py'
        with open(routes_path, 'r') as f:
            content = f.read()
        
        assert 'approve-audio' in content, "approve-audio endpoint should be defined in routes.py"
        print("✓ approve-audio endpoint defined in routes.py")


class TestAPIEndpointAvailability:
    """Test that avatar endpoints are available"""
    
    def test_generate_avatar_360_endpoint_exists(self):
        """POST /api/campaigns/pipeline/generate-avatar-360 endpoint should exist"""
        # Send minimal request to check endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-360",
            json={
                "source_image_url": "https://example.com/test.jpg",
                "clothing": "company_uniform",
                "avatar_style": "realistic"
            },
            timeout=10
        )
        # Should not return 404 (endpoint exists) - may return 401 (auth) or 500 (processing error)
        assert response.status_code != 404, \
            f"generate-avatar-360 endpoint should exist, got 404"
        print(f"✓ generate-avatar-360 endpoint exists (returns {response.status_code})")
    
    def test_generate_avatar_variant_endpoint_exists(self):
        """POST /api/campaigns/pipeline/generate-avatar-variant endpoint should exist"""
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
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404, \
            f"generate-avatar-variant endpoint should exist, got 404"
        print(f"✓ generate-avatar-variant endpoint exists (returns {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
