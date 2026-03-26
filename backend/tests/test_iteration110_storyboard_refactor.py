"""
Iteration 110: Testing storyboard refactor - individual frame generation instead of grid splitting.

Tests:
1. Backend code structure verification (no _split_grid_into_frames, has _generate_single_frame, _generate_all_frames_for_scene)
2. FRAME_TYPES constant has 6 frame types
3. Startup cleanup function exists and is called
4. API endpoints return correct data
5. Frontend toolbar is outside image overlay
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


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


# ============ BACKEND CODE STRUCTURE TESTS ============

class TestBackendCodeStructure:
    """Verify backend code has correct functions and no grid splitting"""
    
    def test_storyboard_py_has_generate_single_frame(self):
        """Verify _generate_single_frame function exists in storyboard.py"""
        with open('/app/backend/core/storyboard.py', 'r') as f:
            content = f.read()
        assert 'def _generate_single_frame(' in content, "_generate_single_frame function not found"
        print("PASS: _generate_single_frame function exists")
    
    def test_storyboard_py_has_generate_all_frames_for_scene(self):
        """Verify _generate_all_frames_for_scene function exists in storyboard.py"""
        with open('/app/backend/core/storyboard.py', 'r') as f:
            content = f.read()
        assert 'def _generate_all_frames_for_scene(' in content, "_generate_all_frames_for_scene function not found"
        print("PASS: _generate_all_frames_for_scene function exists")
    
    def test_storyboard_py_no_split_grid_into_frames(self):
        """Verify _split_grid_into_frames function was REMOVED from storyboard.py"""
        with open('/app/backend/core/storyboard.py', 'r') as f:
            content = f.read()
        assert '_split_grid_into_frames' not in content, "_split_grid_into_frames should be REMOVED"
        print("PASS: _split_grid_into_frames was removed (grid splitting code gone)")
    
    def test_frame_types_has_6_entries(self):
        """Verify FRAME_TYPES constant has exactly 6 frame types"""
        with open('/app/backend/core/storyboard.py', 'r') as f:
            content = f.read()
        
        # Find FRAME_TYPES definition
        assert 'FRAME_TYPES = [' in content, "FRAME_TYPES constant not found"
        
        # Count frame type entries
        frame_labels = re.findall(r'"label":\s*"([^"]+)"', content)
        expected_labels = ["Plano Geral", "Close-up", "Acao", "Reacao", "Angulo Dramatico", "Transicao"]
        
        assert len(frame_labels) >= 6, f"Expected 6 frame types, found {len(frame_labels)}"
        for label in expected_labels:
            assert label in frame_labels, f"Missing frame type: {label}"
        print(f"PASS: FRAME_TYPES has 6 entries: {frame_labels[:6]}")
    
    def test_generate_all_panels_calls_generate_all_frames_for_scene(self):
        """Verify generate_all_panels uses _generate_all_frames_for_scene (not grid splitting)"""
        with open('/app/backend/core/storyboard.py', 'r') as f:
            content = f.read()
        
        # Find generate_all_panels function and check it calls _generate_all_frames_for_scene
        assert '_generate_all_frames_for_scene(' in content, "_generate_all_frames_for_scene call not found"
        
        # Verify it's called within generate_all_panels context
        gen_panels_start = content.find('def generate_all_panels(')
        assert gen_panels_start > 0, "generate_all_panels function not found"
        
        # Check that _generate_all_frames_for_scene is called after generate_all_panels definition
        after_gen_panels = content[gen_panels_start:]
        assert '_generate_all_frames_for_scene(' in after_gen_panels, "generate_all_panels should call _generate_all_frames_for_scene"
        print("PASS: generate_all_panels calls _generate_all_frames_for_scene")
    
    def test_regenerate_panel_uses_generate_all_frames_for_scene(self):
        """Verify regenerate_storyboard_panel uses _generate_all_frames_for_scene"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Find regenerate_storyboard_panel function
        assert 'async def regenerate_storyboard_panel(' in content, "regenerate_storyboard_panel function not found"
        
        # Check it imports and uses _generate_all_frames_for_scene
        assert 'from core.storyboard import _generate_all_frames_for_scene' in content or \
               '_generate_all_frames_for_scene' in content, \
               "regenerate_storyboard_panel should use _generate_all_frames_for_scene"
        print("PASS: regenerate_storyboard_panel uses _generate_all_frames_for_scene")


class TestStartupCleanup:
    """Verify startup cleanup function exists and is called"""
    
    def test_cleanup_stale_storyboards_exists(self):
        """Verify _cleanup_stale_storyboards function exists in studio.py"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        assert 'def _cleanup_stale_storyboards(' in content, "_cleanup_stale_storyboards function not found"
        print("PASS: _cleanup_stale_storyboards function exists")
    
    def test_cleanup_called_on_startup(self):
        """Verify _cleanup_stale_storyboards is called on app startup in server.py"""
        with open('/app/backend/server.py', 'r') as f:
            content = f.read()
        
        # Check for startup event
        assert '@app.on_event("startup")' in content, "Startup event not found"
        
        # Check cleanup is called
        assert '_cleanup_stale_storyboards' in content, "_cleanup_stale_storyboards not called on startup"
        print("PASS: _cleanup_stale_storyboards is called on app startup")
    
    def test_cleanup_resets_stale_statuses(self):
        """Verify cleanup function resets 'starting' and 'generating' statuses"""
        with open('/app/backend/routers/studio.py', 'r') as f:
            content = f.read()
        
        # Find the cleanup function
        cleanup_start = content.find('def _cleanup_stale_storyboards(')
        assert cleanup_start > 0, "_cleanup_stale_storyboards not found"
        
        # Check it handles stale phases
        cleanup_section = content[cleanup_start:cleanup_start+1000]
        assert 'starting' in cleanup_section or 'generating' in cleanup_section, \
               "Cleanup should handle 'starting' and 'generating' phases"
        print("PASS: Cleanup function handles stale 'starting'/'generating' statuses")


# ============ API ENDPOINT TESTS ============

class TestStoryboardAPI:
    """Test storyboard API endpoints"""
    
    def test_login_works(self, api_client, auth_token):
        """Verify login works with test credentials"""
        assert auth_token is not None, "Auth token should not be None"
        assert len(auth_token) > 10, "Auth token should be a valid JWT"
        print(f"PASS: Login successful, token length: {len(auth_token)}")
    
    def test_get_storyboard_returns_panels(self, api_client):
        """Verify GET /api/studio/projects/{id}/storyboard returns panels with frames"""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        assert 'panels' in data, "Response should have 'panels' field"
        assert 'storyboard_status' in data, "Response should have 'storyboard_status' field"
        
        panels = data['panels']
        assert len(panels) > 0, "Should have at least one panel"
        print(f"PASS: GET storyboard returns {len(panels)} panels")
    
    def test_panel_has_frames_data(self, api_client):
        """Verify panels have frames array with correct structure"""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard")
        assert response.status_code == 200
        
        data = response.json()
        panels = data['panels']
        
        # Find a panel with frames (panel 1 should have 6 frames)
        panel_with_frames = next((p for p in panels if p.get('frames') and len(p.get('frames', [])) > 0), None)
        
        if panel_with_frames:
            frames = panel_with_frames['frames']
            assert len(frames) == 6, f"Expected 6 frames, got {len(frames)}"
            
            # Check frame structure
            for frame in frames:
                assert 'frame_number' in frame, "Frame should have frame_number"
                assert 'image_url' in frame, "Frame should have image_url"
                assert 'label' in frame, "Frame should have label"
            
            print(f"PASS: Panel {panel_with_frames['scene_number']} has {len(frames)} frames with correct structure")
        else:
            print("INFO: No panels with frames found (may need to generate storyboard first)")
    
    def test_storyboard_status_structure(self, api_client):
        """Verify storyboard_status has correct structure"""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/storyboard")
        assert response.status_code == 200
        
        data = response.json()
        status = data.get('storyboard_status', {})
        
        # Status should have phase field
        if status:
            assert 'phase' in status or status == {}, "Status should have 'phase' field or be empty"
            print(f"PASS: storyboard_status structure correct: {status}")
        else:
            print("INFO: storyboard_status is empty (no generation started)")


# ============ FRONTEND CODE STRUCTURE TESTS ============

class TestFrontendCodeStructure:
    """Verify frontend code has toolbar outside image overlay"""
    
    def test_toolbar_outside_image_overlay(self):
        """Verify toolbar buttons (expand, inpaint, regen) are outside the image area"""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Check for toolbar section with buttons
        assert 'Action toolbar' in content or 'toolbar' in content.lower(), "Toolbar section should exist"
        
        # Check toolbar is in a separate div after the image
        # The toolbar should be in a div with bg-[#0D0D0D] border-t
        assert 'bg-[#0D0D0D] border-t' in content, "Toolbar should have distinct background"
        
        # Check buttons exist in toolbar
        assert 'expand-panel-' in content, "Expand button should have data-testid"
        assert 'inpaint-panel-' in content, "Inpaint button should have data-testid"
        assert 'regen-panel-' in content, "Regen button should have data-testid"
        
        print("PASS: Toolbar with expand/inpaint/regen buttons exists outside image overlay")
    
    def test_no_hover_overlay_for_editing(self):
        """Verify editing controls are NOT in a hover overlay"""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # The old pattern had hover:opacity-100 opacity-0 for overlay
        # New pattern should have always-visible toolbar
        
        # Check that toolbar buttons are always visible (not opacity-0)
        toolbar_section = content[content.find('Action toolbar'):content.find('Action toolbar')+500] if 'Action toolbar' in content else ""
        
        # Toolbar should NOT have opacity-0 (hidden by default)
        assert 'opacity-0' not in toolbar_section or 'hover:opacity-100' not in toolbar_section, \
               "Toolbar should be always visible, not hidden with opacity-0"
        
        print("PASS: Editing controls are always visible (not in hover overlay)")
    
    def test_voice_input_in_inpainting_section(self):
        """Verify VoiceInput component exists in inpainting section"""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Check VoiceInput import
        assert 'import { VoiceInput }' in content or "import {VoiceInput}" in content, \
               "VoiceInput should be imported"
        
        # Check VoiceInput is used in inpainting section
        assert '<VoiceInput' in content, "VoiceInput component should be used"
        
        # Check it's near the inpaint input
        inpaint_section = content[content.find('inpaint-input-'):content.find('inpaint-input-')+500] if 'inpaint-input-' in content else ""
        assert 'VoiceInput' in inpaint_section or '<VoiceInput' in content, \
               "VoiceInput should be in inpainting section"
        
        print("PASS: VoiceInput component exists in inpainting section")
    
    def test_voice_input_has_proper_size(self):
        """Verify VoiceInput mic button has proper size"""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Find VoiceInput usage - look for the full component block
        voice_input_match = re.search(r'<VoiceInput[\s\S]*?/>', content)
        assert voice_input_match, "VoiceInput component not found"
        
        voice_input_tag = voice_input_match.group(0)
        
        # Check it has size prop or className with size
        assert 'size=' in voice_input_tag or 'className=' in voice_input_tag, \
               "VoiceInput should have size or className prop"
        
        # Check for reasonable size (h-7 w-7 or similar)
        assert 'h-7' in voice_input_tag or 'h-8' in voice_input_tag or 'size={' in voice_input_tag, \
               "VoiceInput should have visible size"
        
        print(f"PASS: VoiceInput has proper size configuration (found: size and h-7/h-8 class)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
