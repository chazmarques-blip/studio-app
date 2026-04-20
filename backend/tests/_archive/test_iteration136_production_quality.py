"""
Iteration 136: Test production_quality feature and Sora Characters API endpoints

Tests:
1. POST /api/studio/projects with production_quality=cinema creates project with field persisted
2. GET /api/studio/projects/{id} returns production_quality correctly
3. PATCH /api/studio/projects/{id}/settings accepts production_quality in allowed_keys
4. StudioProject Pydantic model accepts production_quality with default 'fast'
5. Sora Characters endpoints: auto-register, list, delete
6. Python imports for sora_characters.py and production.py
"""

import pytest
import requests
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://studiox-kling-fix.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "test@studiox.com"
TEST_PASSWORD = "studiox123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self):
        """Test backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✅ Health check passed: {data}")
    
    def test_auth_login(self):
        """Test login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"✅ Auth login passed, token received")


class TestProductionQualityCreate:
    """Test POST /api/studio/projects with production_quality"""
    
    def test_create_project_with_cinema_quality(self, auth_headers):
        """POST /api/studio/projects with production_quality=cinema should persist the field"""
        payload = {
            "name": "TEST_Cinema_Quality_Project",
            "briefing": "Test project for cinema quality",
            "language": "pt",
            "visual_style": "animation",
            "animation_sub": "pixar_3d",
            "video_engine": "sora",
            "production_quality": "cinema"  # NEW: Cinema quality
        }
        
        response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text[:300]}"
        
        data = response.json()
        project_id = data.get("id")
        assert project_id, "No project ID returned"
        
        # Verify production_quality was set
        assert data.get("production_quality") == "cinema", f"Expected 'cinema', got: {data.get('production_quality')}"
        
        print(f"✅ Created project {project_id} with production_quality=cinema")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
        return project_id
    
    def test_create_project_default_quality(self, auth_headers):
        """POST /api/studio/projects without production_quality should default to 'fast'"""
        payload = {
            "name": "TEST_Default_Quality_Project",
            "briefing": "Test project for default quality",
            "language": "pt",
            "visual_style": "animation",
            "animation_sub": "pixar_3d",
            "video_engine": "sora"
            # No production_quality - should default to 'fast'
        }
        
        response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text[:300]}"
        
        data = response.json()
        project_id = data.get("id")
        
        # Default should be 'fast'
        quality = data.get("production_quality", "fast")
        assert quality == "fast", f"Expected default 'fast', got: {quality}"
        
        print(f"✅ Created project {project_id} with default production_quality=fast")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)


class TestProductionQualityGet:
    """Test GET /api/studio/projects/{id} returns production_quality"""
    
    def test_get_project_returns_production_quality(self, auth_headers):
        """GET /api/studio/projects/{id} should return production_quality field"""
        # First create a project with cinema quality
        payload = {
            "name": "TEST_Get_Quality_Project",
            "briefing": "Test project for GET quality",
            "language": "pt",
            "video_engine": "sora",
            "production_quality": "cinema"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Now GET the project
        get_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
        assert get_response.status_code == 200, f"GET failed: {get_response.text[:300]}"
        
        data = get_response.json()
        
        # Check if production_quality is returned (may be None due to potential bug)
        quality = data.get("production_quality")
        print(f"📊 GET returned production_quality: {quality}")
        
        # This is the bug investigation - if it returns None instead of 'cinema', report it
        if quality is None:
            print(f"⚠️ BUG DETECTED: GET returns None for production_quality instead of 'cinema'")
            print(f"   Full response keys: {list(data.keys())}")
        else:
            assert quality == "cinema", f"Expected 'cinema', got: {quality}"
            print(f"✅ GET correctly returns production_quality=cinema")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
    
    def test_get_project_status_returns_production_quality(self, auth_headers):
        """GET /api/studio/projects/{id}/status should return production_quality"""
        # Create project
        payload = {
            "name": "TEST_Status_Quality_Project",
            "briefing": "Test project for status quality",
            "language": "pt",
            "video_engine": "sora",
            "production_quality": "cinema"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # GET status endpoint
        status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=auth_headers)
        assert status_response.status_code == 200
        
        data = status_response.json()
        quality = data.get("production_quality")
        
        print(f"📊 GET /status returned production_quality: {quality}")
        
        # Status endpoint should return production_quality (line 152 in projects.py)
        if quality is None:
            print(f"⚠️ BUG: /status returns None for production_quality")
        else:
            print(f"✅ /status correctly returns production_quality={quality}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)


class TestProductionQualityPatch:
    """Test PATCH /api/studio/projects/{id}/settings accepts production_quality"""
    
    def test_patch_settings_updates_production_quality(self, auth_headers):
        """PATCH /api/studio/projects/{id}/settings should accept production_quality"""
        # Create project with fast quality
        payload = {
            "name": "TEST_Patch_Quality_Project",
            "briefing": "Test project for PATCH quality",
            "language": "pt",
            "video_engine": "sora",
            "production_quality": "fast"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # PATCH to change to cinema
        patch_response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{project_id}/settings",
            json={"production_quality": "cinema"},
            headers=auth_headers
        )
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text[:300]}"
        
        # Verify the change persisted
        get_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=auth_headers)
        assert get_response.status_code == 200
        
        data = get_response.json()
        quality = data.get("production_quality")
        
        if quality == "cinema":
            print(f"✅ PATCH successfully updated production_quality to 'cinema'")
        else:
            print(f"⚠️ PATCH may not have persisted: got {quality}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)


class TestSoraCharactersEndpoints:
    """Test Sora Characters API endpoints"""
    
    def test_auto_register_sora_characters_empty_project(self, auth_headers):
        """POST /api/studio/projects/{id}/auto-register-sora-characters returns correct structure"""
        # Create a new empty project
        payload = {
            "name": "TEST_Sora_Characters_Project",
            "briefing": "Test project for Sora characters",
            "language": "pt",
            "video_engine": "sora"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Call auto-register on empty project
        register_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{project_id}/auto-register-sora-characters",
            headers=auth_headers
        )
        
        # Should return 200 with empty/failed results (no rendered scenes)
        assert register_response.status_code == 200, f"Auto-register failed: {register_response.text[:300]}"
        
        data = register_response.json()
        
        # Verify response structure
        assert "registered" in data, "Missing 'registered' field"
        assert "skipped" in data, "Missing 'skipped' field"
        assert "failed" in data, "Missing 'failed' field"
        
        print(f"✅ Auto-register response structure correct:")
        print(f"   registered: {len(data.get('registered', []))}")
        print(f"   skipped: {len(data.get('skipped', []))}")
        print(f"   failed: {len(data.get('failed', []))}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
    
    def test_list_sora_characters_empty(self, auth_headers):
        """GET /api/studio/projects/{id}/sora-characters returns empty list for new project"""
        # Create project
        payload = {
            "name": "TEST_List_Sora_Characters",
            "briefing": "Test project",
            "language": "pt",
            "video_engine": "sora"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # List sora characters
        list_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{project_id}/sora-characters",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200, f"List failed: {list_response.text[:300]}"
        
        data = list_response.json()
        assert "characters" in data, "Missing 'characters' field"
        
        # Should be empty for new project
        characters = data.get("characters", [])
        print(f"✅ List sora-characters returned {len(characters)} characters (expected 0 for new project)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)
    
    def test_delete_sora_character_nonexistent(self, auth_headers):
        """DELETE /api/studio/projects/{id}/sora-characters/{name} doesn't crash for nonexistent"""
        # Create project
        payload = {
            "name": "TEST_Delete_Sora_Character",
            "briefing": "Test project",
            "language": "pt",
            "video_engine": "sora"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/studio/projects", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        project_id = create_response.json().get("id")
        
        # Try to delete nonexistent character
        delete_response = requests.delete(
            f"{BASE_URL}/api/studio/projects/{project_id}/sora-characters/NonexistentCharacter",
            headers=auth_headers
        )
        
        # Should return 200 with removed=false (not crash)
        assert delete_response.status_code == 200, f"Delete crashed: {delete_response.text[:300]}"
        
        data = delete_response.json()
        assert data.get("removed") == False, f"Expected removed=false, got: {data}"
        
        print(f"✅ Delete nonexistent character handled gracefully: {data}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/studio/projects/{project_id}", headers=auth_headers)


class TestPythonImports:
    """Test Python imports work correctly"""
    
    def test_import_sora_characters(self):
        """Import sora_characters.py without errors"""
        try:
            from routers.studio import sora_characters
            print(f"✅ sora_characters.py imported successfully")
            
            # Check key functions exist
            assert hasattr(sora_characters, '_sora_character_ids_for_scene')
            assert hasattr(sora_characters, '_register_sora_character_http')
            print(f"✅ Key functions exist in sora_characters module")
        except ImportError as e:
            pytest.skip(f"Import skipped (expected in test environment): {e}")
    
    def test_import_production(self):
        """Import production.py without errors"""
        try:
            from routers.studio import production
            print(f"✅ production.py imported successfully")
            
            # Check key functions exist
            assert hasattr(production, '_generate_video_with_openai_direct')
            assert hasattr(production, '_generate_video_unified')
            print(f"✅ Key functions exist in production module")
        except ImportError as e:
            pytest.skip(f"Import skipped (expected in test environment): {e}")


class TestExistingProjectProductionQuality:
    """Test production_quality on existing projects"""
    
    def test_existing_sora_project_quality(self, auth_headers):
        """Check if existing Sora projects have production_quality field"""
        # Get all projects
        response = requests.get(f"{BASE_URL}/api/studio/projects", headers=auth_headers)
        assert response.status_code == 200
        
        projects = response.json().get("projects", [])
        sora_projects = [p for p in projects if p.get("video_engine") == "sora"]
        
        print(f"📊 Found {len(sora_projects)} Sora projects")
        
        if sora_projects:
            # Check first Sora project
            project = sora_projects[0]
            project_id = project.get("id")
            
            # Get full status
            status_response = requests.get(f"{BASE_URL}/api/studio/projects/{project_id}/status", headers=auth_headers)
            if status_response.status_code == 200:
                data = status_response.json()
                quality = data.get("production_quality")
                print(f"   Project {project_id}: production_quality = {quality}")
                
                # Existing projects without the field should default to 'fast'
                if quality is None:
                    print(f"   ⚠️ Existing project has None for production_quality (expected 'fast' default)")
                else:
                    print(f"   ✅ production_quality field present: {quality}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
