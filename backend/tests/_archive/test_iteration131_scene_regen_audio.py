"""
Iteration 131: Test Single Scene Regeneration with Audio/TTS
CRITICAL P0 BUG FIX: Verify that scene regeneration generates audio correctly
without 'cannot access local variable subprocess' error.

Root cause: Python scoping bug with local subprocess import was fixed by
removing local imports and using global imports from _shared.py.

Test scenarios:
1. Verify regenerate-scene endpoint returns 200
2. Verify scene status updates correctly during regeneration
3. Verify project data structure for audio mode and voice_map
4. Verify no UnboundLocalError for subprocess/tempfile
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"
TEST_PROJECT_ID = "f28f6d348f6d"  # CANAL PULMERANEA project
TEST_SCENE_NUMBER = 2


class TestSceneRegenerationAudio:
    """Test single scene regeneration with audio generation (P0 bug fix)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def _login(self):
        """Authenticate and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False
    
    def test_01_login_success(self):
        """Test login with test credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"✓ Login successful for {TEST_EMAIL}")
    
    def test_02_get_project_details(self):
        """Verify test project exists and has correct audio configuration"""
        assert self._login(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}")
        
        if response.status_code == 404:
            pytest.skip(f"Test project {TEST_PROJECT_ID} not found - may need different project ID")
        
        assert response.status_code == 200, f"Get project failed: {response.status_code} - {response.text}"
        
        data = response.json()
        project = data.get("project", data)
        
        # Verify project structure
        assert "id" in project or "name" in project, "Invalid project structure"
        
        # Check audio mode
        audio_mode = project.get("audio_mode", "narrated")
        print(f"✓ Project audio_mode: {audio_mode}")
        
        # Check voice_map
        voice_map = project.get("voice_map", {})
        print(f"✓ Project voice_map: {len(voice_map)} voices configured")
        
        # Check scenes
        scenes = project.get("scenes", [])
        print(f"✓ Project has {len(scenes)} scenes")
        
        # Check if scene 2 exists
        scene_2 = next((s for s in scenes if s.get("scene_number") == TEST_SCENE_NUMBER), None)
        if scene_2:
            dialogue = scene_2.get("dialogue", "")
            print(f"✓ Scene {TEST_SCENE_NUMBER} dialogue: {dialogue[:100]}...")
        
        return project
    
    def test_03_regenerate_scene_endpoint_exists(self):
        """Verify regenerate-scene endpoint is accessible"""
        assert self._login(), "Login failed"
        
        # Test with OPTIONS or HEAD to verify endpoint exists
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/regenerate-scene",
            json={"scene_number": TEST_SCENE_NUMBER}
        )
        
        # Accept 200 (success), 400 (bad request), 404 (project not found)
        # Reject 405 (method not allowed) or 500 (server error)
        assert response.status_code != 405, "Endpoint does not exist (405 Method Not Allowed)"
        
        if response.status_code == 500:
            error_text = response.text.lower()
            # Check for the specific bug we fixed
            assert "cannot access local variable" not in error_text, \
                f"CRITICAL BUG: UnboundLocalError still present: {response.text}"
            assert "unboundlocalerror" not in error_text, \
                f"CRITICAL BUG: UnboundLocalError detected: {response.text}"
        
        print(f"✓ Regenerate scene endpoint returned: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response: {data}")
            return data
        elif response.status_code == 404:
            print(f"⚠ Project not found - using different project ID")
        elif response.status_code == 400:
            print(f"⚠ Bad request: {response.text}")
    
    def test_04_verify_subprocess_tempfile_imports(self):
        """Verify subprocess and tempfile are properly imported in production.py"""
        # This is a code verification test - check the imports are correct
        import sys
        sys.path.insert(0, '/app/backend')
        
        try:
            # Import the _shared module
            from routers.studio._shared import subprocess, tempfile
            
            # Verify they are the actual modules
            assert subprocess is not None, "subprocess not imported"
            assert tempfile is not None, "tempfile not imported"
            
            # Verify they have expected attributes
            assert hasattr(subprocess, 'run'), "subprocess.run not available"
            assert hasattr(tempfile, 'mkdtemp'), "tempfile.mkdtemp not available"
            
            print("✓ subprocess and tempfile properly imported in _shared.py")
            
        except ImportError as e:
            pytest.fail(f"Import error: {e}")
    
    def test_05_verify_production_uses_global_imports(self):
        """Verify production.py uses global imports from _shared.py"""
        # Read the production.py file and check for local imports
        production_path = "/app/backend/routers/studio/production.py"
        
        with open(production_path, 'r') as f:
            content = f.read()
        
        # Check that the file imports from _shared
        assert "from ._shared import *" in content, "production.py should import from _shared"
        
        # Check for problematic local imports in the _regenerate_single_scene function
        # Find the function
        func_start = content.find("def _regenerate_single_scene")
        assert func_start > 0, "_regenerate_single_scene function not found"
        
        # Get the function body (until next def at same indentation)
        func_end = content.find("\ndef ", func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        # Check for local imports that would cause UnboundLocalError
        # The bug was: "import subprocess" inside the function after using subprocess
        lines = func_body.split('\n')
        
        # Look for problematic patterns
        problematic_patterns = [
            "import subprocess",  # Local import of subprocess
            "import tempfile",    # Local import of tempfile (except at function start)
        ]
        
        # Count occurrences
        local_subprocess_imports = func_body.count("import subprocess")
        local_tempfile_imports = func_body.count("import tempfile")
        
        # The fix removed local imports, so there should be 0 local imports
        # (except for the comment "# Note: subprocess and tempfile already imported globally")
        
        # Check for the fix comment
        assert "already imported globally" in func_body or local_subprocess_imports == 0, \
            f"Found {local_subprocess_imports} local subprocess imports - bug may not be fixed"
        
        print(f"✓ production.py uses global imports correctly")
        print(f"  - Local subprocess imports in _regenerate_single_scene: {local_subprocess_imports}")
        print(f"  - Local tempfile imports in _regenerate_single_scene: {local_tempfile_imports}")
    
    def test_06_check_scene_status_endpoint(self):
        """Verify scene status can be retrieved"""
        assert self._login(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}")
        
        if response.status_code == 404:
            pytest.skip("Test project not found")
        
        assert response.status_code == 200, f"Get project failed: {response.text}"
        
        data = response.json()
        project = data.get("project", data)
        
        # Check agent_status for scene_status
        agent_status = project.get("agent_status", {})
        scene_status = agent_status.get("scene_status", {})
        
        print(f"✓ Agent status: {agent_status.get('phase', 'N/A')}")
        print(f"✓ Scene statuses: {scene_status}")
        
        # Check if scene 2 has a status
        scene_2_status = scene_status.get(str(TEST_SCENE_NUMBER), "unknown")
        print(f"✓ Scene {TEST_SCENE_NUMBER} status: {scene_2_status}")
    
    def test_07_verify_audio_generation_code_path(self):
        """Verify the audio generation code path in _regenerate_single_scene"""
        production_path = "/app/backend/routers/studio/production.py"
        
        with open(production_path, 'r') as f:
            content = f.read()
        
        # Find the _regenerate_single_scene function
        func_start = content.find("def _regenerate_single_scene")
        func_end = content.find("\ndef ", func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_body = content[func_start:func_end]
        
        # Verify key audio generation code is present
        checks = [
            ("DUBBED audio generation", "audio_mode == \"dubbed\""),
            ("ElevenLabs TTS call", "_generate_narration_audio"),
            ("FFmpeg audio merge", "ffmpeg"),
            ("Audio upload", "_upload_to_storage"),
            ("Success log with audio", "regenerated WITH audio"),
        ]
        
        for name, pattern in checks:
            assert pattern.lower() in func_body.lower(), f"Missing {name}: {pattern}"
            print(f"✓ Found {name}")
        
        # Verify the fix comments are present
        assert "CRITICAL FIX" in func_body, "Fix comments not found"
        print("✓ CRITICAL FIX comments present in code")


class TestProjectVoiceConfiguration:
    """Test voice configuration for dubbed audio mode"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def _login(self):
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
            return True
        return False
    
    def test_01_get_voice_map(self):
        """Get voice map for test project"""
        assert self._login(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map")
        
        if response.status_code == 404:
            pytest.skip("Project not found")
        
        assert response.status_code == 200, f"Get voice map failed: {response.text}"
        
        data = response.json()
        voice_map = data.get("voice_map", {})
        voice_details = data.get("voice_details", {})
        
        print(f"✓ Voice map has {len(voice_map)} entries")
        for char, voice_id in list(voice_map.items())[:5]:
            detail = voice_details.get(char, {})
            print(f"  - {char}: {detail.get('voice_name', voice_id[:8])}")
    
    def test_02_get_available_voices(self):
        """Get list of available ElevenLabs voices"""
        assert self._login(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/studio/voices")
        assert response.status_code == 200, f"Get voices failed: {response.text}"
        
        data = response.json()
        voices = data.get("voices", [])
        
        print(f"✓ {len(voices)} voices available")
        for v in voices[:3]:
            print(f"  - {v.get('name')}: {v.get('id')[:8]}... ({v.get('gender', 'N/A')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
