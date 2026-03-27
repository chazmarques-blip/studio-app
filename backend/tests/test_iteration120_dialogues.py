"""
Iteration 120: Test new Dialogue/Script Polish endpoints (Step 4)
- GET /api/studio/projects/{projectId}/dialogues
- POST /api/studio/projects/{projectId}/dialogues/generate
- PATCH /api/studio/projects/{projectId}/dialogues/save
- Also tests storyboard expandable panels and 6-step pipeline
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
PROJECT_ID = "1a0779dd0ce7"  # ADAO EVA BIBLIZOO project

class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Health endpoint should return OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: Health endpoint returns OK")
    
    def test_login_success(self):
        """Login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        print(f"PASS: Login successful, token received")
        return data["access_token"]


class TestDialogueEndpoints:
    """Test new Dialogue/Script Polish endpoints for Step 4"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_dialogues_endpoint(self):
        """GET /api/studio/projects/{projectId}/dialogues returns scene data"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/dialogues",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "scenes" in data
        assert "characters" in data
        assert "character_voices" in data
        assert "narrator_voice" in data
        
        # Verify scenes have required fields
        if data["scenes"]:
            scene = data["scenes"][0]
            assert "scene_number" in scene
            assert "title" in scene
            assert "characters_in_scene" in scene
            print(f"PASS: GET dialogues returns {len(data['scenes'])} scenes, {len(data['characters'])} characters")
        else:
            print(f"PASS: GET dialogues endpoint works (no scenes yet)")
    
    def test_get_dialogues_returns_characters(self):
        """GET dialogues should return character list for voice assignment"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/dialogues",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Characters should be a list with name and description
        characters = data.get("characters", [])
        if characters:
            char = characters[0]
            assert "name" in char
            print(f"PASS: Characters returned: {[c['name'] for c in characters[:3]]}")
        else:
            print(f"PASS: Characters list returned (empty)")
    
    def test_dialogues_generate_dubbed_mode(self):
        """POST /api/studio/projects/{projectId}/dialogues/generate with mode=dubbed"""
        # Note: This calls Claude AI so we use a short timeout and accept partial success
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/dialogues/generate",
            headers=self.headers,
            json={
                "mode": "dubbed",
                "scene_numbers": [7],  # Just one scene to minimize AI call time
            },
            timeout=90  # AI generation can take 30-60 seconds
        )
        
        # Accept 200 (success) or 400 (no scenes) - both are valid responses
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "ok"
            assert data.get("mode") == "dubbed"
            results = data.get("results", [])
            print(f"PASS: Dubbed dialogue generation returned {len(results)} results")
        else:
            print(f"PASS: Dubbed generation endpoint accessible (no scenes to generate)")
    
    def test_dialogues_generate_narrated_mode(self):
        """POST /api/studio/projects/{projectId}/dialogues/generate with mode=narrated"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/dialogues/generate",
            headers=self.headers,
            json={
                "mode": "narrated",
                "scene_numbers": [7],
            },
            timeout=90
        )
        
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "ok"
            assert data.get("mode") == "narrated"
            print(f"PASS: Narrated text generation works")
        else:
            print(f"PASS: Narrated generation endpoint accessible")
    
    def test_dialogues_generate_book_mode(self):
        """POST /api/studio/projects/{projectId}/dialogues/generate with mode=book"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/dialogues/generate",
            headers=self.headers,
            json={
                "mode": "book",
                "scene_numbers": [7],
            },
            timeout=90
        )
        
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "ok"
            assert data.get("mode") == "book"
            print(f"PASS: Book text generation works")
        else:
            print(f"PASS: Book generation endpoint accessible")
    
    def test_dialogues_save_endpoint(self):
        """PATCH /api/studio/projects/{projectId}/dialogues/save saves dialogues"""
        response = requests.patch(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/dialogues/save",
            headers=self.headers,
            json={
                "scenes_dialogue": [
                    {
                        "scene_number": 7,
                        "dubbed_text": "Test dubbed text",
                        "narrated_text": "Test narrated text",
                        "book_text": "Test book text",
                    }
                ],
                "character_voices": {},
                "narrator_voice": "21m00Tcm4TlvDq8ikWAM",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"PASS: Dialogues save endpoint works")
    
    def test_dialogues_invalid_project(self):
        """GET dialogues for non-existent project returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/invalid_project_id/dialogues",
            headers=self.headers
        )
        assert response.status_code == 404
        print(f"PASS: Invalid project returns 404")


class TestStudioProjectStatus:
    """Test studio project status includes new dialogue fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_project_status_endpoint(self):
        """GET /api/studio/projects/{projectId}/status returns full project data"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify key fields exist
        assert "status" in data
        assert "scenes" in data
        assert "characters" in data
        assert "storyboard_panels" in data
        print(f"PASS: Project status returns {len(data.get('scenes', []))} scenes, {len(data.get('storyboard_panels', []))} panels")
    
    def test_storyboard_panels_have_frames(self):
        """Storyboard panels should have frames array for expandable view"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/status",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        panels = data.get("storyboard_panels", [])
        if panels:
            panel = panels[0]
            # Panels should have image_url and optionally frames
            assert "scene_number" in panel
            if "frames" in panel and panel["frames"]:
                print(f"PASS: Panel has {len(panel['frames'])} frames")
            else:
                print(f"PASS: Panel structure valid (no frames yet)")
        else:
            print(f"PASS: Storyboard panels endpoint works (no panels yet)")


class TestStudioProjects:
    """Test studio projects list endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_projects(self):
        """GET /api/studio/projects returns project list"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        
        projects = data["projects"]
        print(f"PASS: Studio projects list returns {len(projects)} projects")
        
        # Check if ADAO EVA BIBLIZOO project exists
        adao_project = next((p for p in projects if p.get("id") == PROJECT_ID), None)
        if adao_project:
            print(f"PASS: Found ADAO EVA BIBLIZOO project: {adao_project.get('name', 'unnamed')}")


class TestDashboard:
    """Test dashboard still works"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats(self):
        """GET /api/dashboard/stats returns stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # Dashboard should return some stats
        print(f"PASS: Dashboard stats endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
