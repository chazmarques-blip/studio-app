"""
Iteration 127: Voice Assignment Feature Tests
Tests for the new AI-powered voice assignment system:
- POST /api/studio/projects/{id}/auto-assign-voices
- GET /api/studio/projects/{id}/voice-map
- POST /api/studio/projects/{id}/voice-map (manual update)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_PROJECT_ID = "d27afb0e79ff"
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def get_auth_headers():
    """Headers with auth token"""
    token = get_auth_token()
    if not token:
        pytest.skip("Authentication failed")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


class TestVoiceMapEndpoints:
    """Tests for voice map CRUD endpoints"""

    def test_get_voice_map_endpoint_exists(self):
        """GET /api/studio/projects/{id}/voice-map should return 200"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ GET voice-map returns 200")

    def test_get_voice_map_has_required_fields(self):
        """GET voice-map should return voice_map and voice_details"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        data = response.json()
        assert "voice_map" in data, "Response missing 'voice_map' field"
        assert "voice_details" in data, "Response missing 'voice_details' field"
        print(f"✓ voice-map response has voice_map and voice_details fields")

    def test_voice_map_has_characters(self):
        """voice_map should have character mappings (from previous auto-assign)"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        data = response.json()
        voice_map = data.get("voice_map", {})
        # Project d27afb0e79ff should have characters mapped
        assert len(voice_map) > 0, "voice_map should have character mappings"
        print(f"✓ voice_map has {len(voice_map)} character mappings")

    def test_voice_details_structure(self):
        """voice_details should have voice_id, voice_name, gender, accent, style"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        data = response.json()
        voice_details = data.get("voice_details", {})
        
        if len(voice_details) > 0:
            first_char = list(voice_details.keys())[0]
            detail = voice_details[first_char]
            assert "voice_id" in detail, "voice_details missing voice_id"
            assert "voice_name" in detail, "voice_details missing voice_name"
            assert "gender" in detail, "voice_details missing gender"
            assert "accent" in detail, "voice_details missing accent"
            assert "style" in detail, "voice_details missing style"
            print(f"✓ voice_details has correct structure: {detail}")
        else:
            pytest.skip("No voice_details to validate structure")


class TestAutoAssignVoices:
    """Tests for AI voice assignment endpoint"""

    def test_auto_assign_voices_endpoint_exists(self):
        """POST /api/studio/projects/{id}/auto-assign-voices should return 200"""
        headers = get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/auto-assign-voices",
            headers=headers,
            timeout=90  # Claude call may take time
        )
        # Should return 200 (success)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ POST auto-assign-voices returns 200")

    def test_auto_assign_returns_voice_map(self):
        """auto-assign-voices should return voice_map and voice_details"""
        headers = get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/auto-assign-voices",
            headers=headers,
            timeout=90  # Claude call may take time
        )
        data = response.json()
        assert "voice_map" in data, "Response missing 'voice_map'"
        assert "voice_details" in data, "Response missing 'voice_details'"
        print(f"✓ auto-assign-voices returns voice_map and voice_details")

    def test_auto_assign_maps_all_characters(self):
        """auto-assign should map all characters in the project"""
        headers = get_auth_headers()
        # First get project status to know character count
        status_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/status",
            headers=headers
        )
        characters = status_response.json().get("characters", [])
        
        # Now check voice map
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        voice_map = response.json().get("voice_map", {})
        
        # All characters should have a voice assigned
        for char in characters:
            char_name = char.get("name", "")
            if char_name:
                assert char_name in voice_map, f"Character '{char_name}' not in voice_map"
        print(f"✓ All {len(characters)} characters have voice assignments")


class TestUpdateVoiceMap:
    """Tests for manual voice map update endpoint"""

    def test_update_voice_map_endpoint_exists(self):
        """POST /api/studio/projects/{id}/voice-map should return 200"""
        headers = get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers,
            json={"voice_map": {"TestCharacter": "21m00Tcm4TlvDq8ikWAM"}}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ POST voice-map (update) returns 200")

    def test_update_voice_map_merges_with_existing(self):
        """Update should merge with existing voice_map, not replace"""
        headers = get_auth_headers()
        # Get current voice map
        get_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        original_map = get_response.json().get("voice_map", {})
        original_count = len(original_map)
        
        # Update with a new character
        test_char = "TEST_NewCharacter"
        test_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        
        update_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers,
            json={"voice_map": {test_char: test_voice}}
        )
        updated_map = update_response.json().get("voice_map", {})
        
        # Should have original + new
        assert test_char in updated_map, f"New character '{test_char}' not in updated map"
        assert updated_map[test_char] == test_voice, "Voice ID not saved correctly"
        
        # Original characters should still be there
        for char in list(original_map.keys())[:3]:  # Check first 3
            assert char in updated_map, f"Original character '{char}' lost after update"
        
        print(f"✓ Update merges correctly: {original_count} -> {len(updated_map)} characters")

    def test_update_voice_map_returns_voice_details(self):
        """Update should return voice_details with full voice info"""
        headers = get_auth_headers()
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers,
            json={"voice_map": {"Narrador": "21m00Tcm4TlvDq8ikWAM"}},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.text, "Response body is empty"
        data = response.json()
        assert "voice_details" in data, "Update response missing voice_details"
        
        if "Narrador" in data.get("voice_details", {}):
            detail = data["voice_details"]["Narrador"]
            assert detail.get("voice_name") == "Rachel", f"Expected Rachel, got {detail.get('voice_name')}"
        print(f"✓ Update returns voice_details with full info")


class TestVoiceIdValidation:
    """Tests for voice ID validation"""

    def test_voice_ids_are_valid_elevenlabs_ids(self):
        """All voice IDs in voice_map should be valid ElevenLabs IDs"""
        headers = get_auth_headers()
        # Get available voices
        voices_response = requests.get(
            f"{BASE_URL}/api/studio/voices",
            headers=headers
        )
        valid_ids = {v["id"] for v in voices_response.json().get("voices", [])}
        
        # Get voice map
        map_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        voice_map = map_response.json().get("voice_map", {})
        
        # All voice IDs should be valid
        for char_name, voice_id in voice_map.items():
            assert voice_id in valid_ids, f"Invalid voice ID '{voice_id}' for character '{char_name}'"
        
        print(f"✓ All {len(voice_map)} voice IDs are valid ElevenLabs voices")


class TestVoiceMapPersistence:
    """Tests for voice map persistence"""

    def test_voice_map_persists_after_auto_assign(self):
        """Voice map should persist after auto-assign"""
        headers = get_auth_headers()
        # Auto-assign
        assign_response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/auto-assign-voices",
            headers=headers,
            timeout=90
        )
        assigned_map = assign_response.json().get("voice_map", {})
        
        # GET should return same map
        get_response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            headers=headers
        )
        persisted_map = get_response.json().get("voice_map", {})
        
        # Should match
        for char_name, voice_id in assigned_map.items():
            assert char_name in persisted_map, f"Character '{char_name}' not persisted"
            assert persisted_map[char_name] == voice_id, f"Voice ID mismatch for '{char_name}'"
        
        print(f"✓ Voice map persists correctly ({len(persisted_map)} characters)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
