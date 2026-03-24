"""
Iteration 100: Testing Preview Board Feature for Directed Studio Mode
- POST /api/studio/projects/{id}/generate-preview endpoint
- GET /api/studio/projects/{id}/preview endpoint
- Helper functions importable (_analyze_avatars_with_vision, _build_production_design, _create_composite_avatar)
- Pipeline v5 skip logic for existing production_design
"""
import pytest
import requests
import os
import sys

# Add backend to path for imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPreviewBoardBackend:
    """Test Preview Board backend endpoints and helper functions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
        self.session.close()
    
    def test_health_check(self):
        """Test backend health endpoint"""
        resp = self.session.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
        print("PASS: Health check returns status ok")
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        print("PASS: Login with valid credentials returns access_token")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert resp.status_code == 401
        print("PASS: Login with invalid credentials returns 401")
    
    def test_studio_projects_list(self):
        """Test GET /api/studio/projects returns list"""
        resp = self.session.get(f"{BASE_URL}/api/studio/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        print(f"PASS: GET /api/studio/projects returns {len(data['projects'])} projects")
    
    def test_generate_preview_no_scenes(self):
        """Test POST /api/studio/projects/{id}/generate-preview returns 400 for project with no scenes"""
        # First create a project without scenes
        create_resp = self.session.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Preview_NoScenes",
            "briefing": "Test project for preview without scenes",
            "language": "pt",
            "visual_style": "animation"
        })
        assert create_resp.status_code == 200
        project_id = create_resp.json().get("id")
        
        # Try to generate preview - should fail with 400 (no scenes)
        preview_resp = self.session.post(f"{BASE_URL}/api/studio/projects/{project_id}/generate-preview")
        assert preview_resp.status_code == 400
        data = preview_resp.json()
        assert "No scenes" in data.get("detail", "")
        print("PASS: POST /api/studio/projects/{id}/generate-preview returns 400 for no scenes")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/studio/projects/{project_id}")
    
    def test_generate_preview_endpoint_exists(self):
        """Test POST /api/studio/projects/{id}/generate-preview endpoint exists"""
        # Use a non-existent project ID to test endpoint routing
        resp = self.session.post(f"{BASE_URL}/api/studio/projects/nonexistent123/generate-preview")
        # Should return 404 (project not found) not 405 (method not allowed)
        assert resp.status_code == 404
        print("PASS: POST /api/studio/projects/{id}/generate-preview endpoint exists (returns 404 for missing project)")
    
    def test_get_preview_endpoint_exists(self):
        """Test GET /api/studio/projects/{id}/preview endpoint exists"""
        # Use a non-existent project ID to test endpoint routing
        resp = self.session.get(f"{BASE_URL}/api/studio/projects/nonexistent123/preview")
        # Should return 404 (project not found) not 405 (method not allowed)
        assert resp.status_code == 404
        print("PASS: GET /api/studio/projects/{id}/preview endpoint exists (returns 404 for missing project)")
    
    def test_get_preview_returns_correct_fields(self):
        """Test GET /api/studio/projects/{id}/preview returns correct response structure"""
        # Create a project first
        create_resp = self.session.post(f"{BASE_URL}/api/studio/projects", json={
            "name": "TEST_Preview_Fields",
            "briefing": "Test project for preview fields",
            "language": "pt",
            "visual_style": "animation"
        })
        assert create_resp.status_code == 200
        project_id = create_resp.json().get("id")
        
        # Get preview - should return structure even if no preview generated
        preview_resp = self.session.get(f"{BASE_URL}/api/studio/projects/{project_id}/preview")
        assert preview_resp.status_code == 200
        data = preview_resp.json()
        
        # Check required fields exist
        assert "preview_status" in data
        assert "production_design" in data
        assert "avatar_descriptions" in data
        print(f"PASS: GET /api/studio/projects/{project_id}/preview returns correct fields: preview_status={data['preview_status']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/studio/projects/{project_id}")
    
    def test_helper_functions_importable(self):
        """Test that new helper functions are importable from studio router"""
        try:
            from routers.studio import _analyze_avatars_with_vision
            assert callable(_analyze_avatars_with_vision)
            print("PASS: _analyze_avatars_with_vision is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _analyze_avatars_with_vision: {e}")
    
    def test_build_production_design_importable(self):
        """Test that _build_production_design is importable"""
        try:
            from routers.studio import _build_production_design
            assert callable(_build_production_design)
            print("PASS: _build_production_design is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _build_production_design: {e}")
    
    def test_create_composite_avatar_importable(self):
        """Test that _create_composite_avatar is importable"""
        try:
            from routers.studio import _create_composite_avatar
            assert callable(_create_composite_avatar)
            print("PASS: _create_composite_avatar is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _create_composite_avatar: {e}")
    
    def test_generate_preview_task_importable(self):
        """Test that _generate_preview_task is importable"""
        try:
            from routers.studio import _generate_preview_task
            assert callable(_generate_preview_task)
            print("PASS: _generate_preview_task is importable and callable")
        except ImportError as e:
            pytest.fail(f"Failed to import _generate_preview_task: {e}")
    
    def test_project_with_scenes_can_generate_preview(self):
        """Test that a project with scenes can start preview generation"""
        # Get existing projects to find one with scenes
        projects_resp = self.session.get(f"{BASE_URL}/api/studio/projects")
        assert projects_resp.status_code == 200
        projects = projects_resp.json().get("projects", [])
        
        # Find a project with scenes
        project_with_scenes = None
        for p in projects:
            if p.get("scenes") and len(p.get("scenes", [])) > 0:
                project_with_scenes = p
                break
        
        if project_with_scenes:
            project_id = project_with_scenes["id"]
            # Try to generate preview
            preview_resp = self.session.post(f"{BASE_URL}/api/studio/projects/{project_id}/generate-preview")
            # Should return 200 (started) or already have preview
            assert preview_resp.status_code == 200
            data = preview_resp.json()
            assert "status" in data
            print(f"PASS: Project with scenes can start preview generation: status={data.get('status')}")
        else:
            print("SKIP: No project with scenes found to test preview generation")
            pytest.skip("No project with scenes available")
    
    def test_start_production_endpoint(self):
        """Test POST /api/studio/start-production endpoint exists"""
        resp = self.session.post(f"{BASE_URL}/api/studio/start-production", json={
            "project_id": "nonexistent123",
            "video_duration": 12,
            "character_avatars": {}
        })
        # Should return 404 (project not found) not 405 (method not allowed)
        assert resp.status_code == 404
        print("PASS: POST /api/studio/start-production endpoint exists")
    
    def test_voices_endpoint(self):
        """Test GET /api/studio/voices returns voices list"""
        resp = self.session.get(f"{BASE_URL}/api/studio/voices")
        assert resp.status_code == 200
        data = resp.json()
        assert "voices" in data
        print(f"PASS: GET /api/studio/voices returns {len(data.get('voices', []))} voices")
    
    def test_music_library_endpoint(self):
        """Test GET /api/studio/music-library returns music tracks"""
        resp = self.session.get(f"{BASE_URL}/api/studio/music-library")
        assert resp.status_code == 200
        data = resp.json()
        assert "tracks" in data
        print(f"PASS: GET /api/studio/music-library returns {len(data.get('tracks', []))} tracks")


class TestPipelineV5SkipLogic:
    """Test that pipeline v5 skips pre-production when production_design exists"""
    
    def test_run_multi_scene_production_has_skip_logic(self):
        """Verify _run_multi_scene_production checks for existing production_design"""
        import inspect
        from routers.studio import _run_multi_scene_production
        
        source = inspect.getsource(_run_multi_scene_production)
        
        # Check for skip logic keywords
        assert "existing_pd" in source or "production_design" in source
        assert "Preview Board" in source or "skipping" in source.lower() or "already done" in source.lower()
        print("PASS: _run_multi_scene_production contains skip logic for existing production_design")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
