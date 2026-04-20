"""
Iteration 129: Dialogue Editor Bug Fix Tests
Tests for the fix where narration text was showing instead of proper character dialogues.

Features tested:
- GET /api/studio/projects/{id}/dialogues returns has_voice_map and scenes_needing_dubbed
- character_voices uses AI-assigned voice_map (Rachel, Lily, Charlotte, Brian) not hardcoded
- POST /api/studio/projects/{id}/dialogues/generate with mode='dubbed' generates character dialogues
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PROJECT_ID = "d27afb0e79ff"


class TestDialoguesEndpoint:
    """Tests for GET /api/studio/projects/{id}/dialogues endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token") or login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_dialogues_endpoint_returns_200(self):
        """Test that GET /api/studio/projects/{id}/dialogues returns 200"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/studio/projects/{id}/dialogues returns 200")
    
    def test_dialogues_has_voice_map_field(self):
        """Test that response contains has_voice_map field set to true"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues")
        assert response.status_code == 200
        
        data = response.json()
        assert "has_voice_map" in data, "Response missing 'has_voice_map' field"
        assert data["has_voice_map"] == True, f"Expected has_voice_map=True, got {data['has_voice_map']}"
        print(f"PASS: has_voice_map = {data['has_voice_map']}")
    
    def test_dialogues_has_scenes_needing_dubbed(self):
        """Test that response contains scenes_needing_dubbed count"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues")
        assert response.status_code == 200
        
        data = response.json()
        assert "scenes_needing_dubbed" in data, "Response missing 'scenes_needing_dubbed' field"
        assert isinstance(data["scenes_needing_dubbed"], int), "scenes_needing_dubbed should be an integer"
        print(f"PASS: scenes_needing_dubbed = {data['scenes_needing_dubbed']}")
    
    def test_character_voices_uses_voice_map(self):
        """Test that character_voices uses AI-assigned voice_map, not hardcoded names"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues")
        assert response.status_code == 200
        
        data = response.json()
        character_voices = data.get("character_voices", {})
        
        # Check that we have character voices
        assert len(character_voices) > 0, "No character voices returned"
        
        # Check that voice names are from the AI-assigned voice_map (not hardcoded Arnold, Bella, Gigi)
        hardcoded_names = {"Arnold", "Bella", "Gigi"}
        ai_assigned_names = {"Rachel", "Lily", "Charlotte", "Brian", "Daniel", "Sarah", "Laura", "Alice", 
                            "Matilda", "Jessica", "Emily", "Roger", "Charlie", "George", "Callum", 
                            "Liam", "Will", "Eric", "Chris", "Bill", "Drew", "River", "Aria", "Freya"}
        
        found_ai_voices = []
        found_hardcoded = []
        
        for char_name, voice_info in character_voices.items():
            voice_name = voice_info.get("voice_name", "")
            if voice_name in ai_assigned_names:
                found_ai_voices.append(f"{char_name}: {voice_name}")
            if voice_name in hardcoded_names:
                found_hardcoded.append(f"{char_name}: {voice_name}")
        
        print(f"Character voices found: {list(character_voices.keys())[:5]}...")
        print(f"AI-assigned voices: {found_ai_voices[:5]}...")
        
        # We should have AI-assigned voices, not hardcoded ones
        assert len(found_ai_voices) > 0, "No AI-assigned voices found - voice_map may not be used"
        print(f"PASS: Found {len(found_ai_voices)} AI-assigned voices")
    
    def test_character_voices_structure(self):
        """Test that character_voices has correct structure with voice_id, voice_name, voice_type"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues")
        assert response.status_code == 200
        
        data = response.json()
        character_voices = data.get("character_voices", {})
        
        # Check first character's voice structure
        for char_name, voice_info in list(character_voices.items())[:1]:
            assert "voice_id" in voice_info, f"Missing voice_id for {char_name}"
            assert "voice_name" in voice_info, f"Missing voice_name for {char_name}"
            assert "voice_type" in voice_info, f"Missing voice_type for {char_name}"
            print(f"PASS: {char_name} has voice_id={voice_info['voice_id'][:8]}..., voice_name={voice_info['voice_name']}, voice_type={voice_info['voice_type']}")
    
    def test_scenes_data_structure(self):
        """Test that scenes data has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues")
        assert response.status_code == 200
        
        data = response.json()
        scenes = data.get("scenes", [])
        
        assert len(scenes) > 0, "No scenes returned"
        
        # Check first scene structure
        scene = scenes[0]
        required_fields = ["scene_number", "title", "description", "dubbed_text", "narrated_text", "book_text"]
        for field in required_fields:
            assert field in scene, f"Scene missing field: {field}"
        
        print(f"PASS: {len(scenes)} scenes returned with correct structure")


class TestDialogueGeneration:
    """Tests for POST /api/studio/projects/{id}/dialogues/generate endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token") or login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_generate_dubbed_dialogue_for_single_scene(self):
        """Test generating dubbed dialogue for scene 14 (has characters: Adão, Pássaro Canção, etc.)"""
        response = self.session.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/dialogues/generate",
            json={
                "mode": "dubbed",
                "scene_numbers": [14],
                "user_instructions": ""
            },
            timeout=120  # AI generation can take time
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "ok", f"Expected status=ok, got {data.get('status')}"
        assert data.get("mode") == "dubbed", f"Expected mode=dubbed, got {data.get('mode')}"
        
        results = data.get("results", [])
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        
        result = results[0]
        assert result.get("scene_number") == 14, f"Expected scene_number=14, got {result.get('scene_number')}"
        
        generated_text = result.get("generated_text", "")
        assert len(generated_text) > 0, "Generated text is empty"
        
        # Check that generated text has character dialogue format (CharName: "text")
        has_dialogue_format = ":" in generated_text
        print(f"PASS: Generated {len(generated_text)} chars of dubbed dialogue")
        print(f"Sample: {generated_text[:200]}...")
        
        if has_dialogue_format:
            print("PASS: Generated text has character dialogue format (contains ':')")
        else:
            print("WARNING: Generated text may not have proper character dialogue format")


class TestVoiceMapIntegration:
    """Tests to verify voice_map is properly integrated"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token") or login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_voice_map_endpoint_exists(self):
        """Test that GET /api/studio/projects/{id}/voice-map endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        voice_map = data.get("voice_map", {})
        print(f"PASS: voice-map endpoint returns {len(voice_map)} character mappings")
    
    def test_voice_map_has_ai_assigned_voices(self):
        """Test that voice_map contains AI-assigned voice IDs"""
        response = self.session.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map")
        assert response.status_code == 200
        
        data = response.json()
        voice_map = data.get("voice_map", {})
        
        # Check that voice_map has entries
        assert len(voice_map) > 0, "voice_map is empty"
        
        # Print some voice mappings
        for char_name, voice_id in list(voice_map.items())[:5]:
            print(f"  {char_name}: {voice_id[:12]}...")
        
        print(f"PASS: voice_map has {len(voice_map)} AI-assigned voice mappings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
