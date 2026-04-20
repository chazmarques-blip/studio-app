"""
Iteration 128: Sound Design Agent (Agente de Sonoplastia IA) Tests
Tests the ElevenLabs Voice Design API integration for custom voice generation.

Endpoints tested:
- POST /api/studio/projects/{id}/auto-assign-voices (catalog voices - fast)
- GET /api/studio/projects/{id}/voice-map (get saved voice assignments)
- POST /api/studio/projects/{id}/voice-map (save manual voice edits)
- POST /api/studio/projects/{id}/design-character-voice (Sound Agent for single character)
- POST /api/studio/projects/{id}/select-designed-voice (save preview as permanent voice)

NOTE: design-all-voices endpoint is SKIPPED (too slow ~60-120s per run)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_PROJECT_ID = "d27afb0e79ff"  # BIBLIZOO 2 project with 17 characters
TEST_CHARACTER = "Adão"  # Character to test single voice design

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Shared requests session with auth header."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestVoiceMapEndpoints:
    """Test basic voice map CRUD operations (catalog voices)."""

    def test_get_voice_map_endpoint_exists(self, api_client):
        """GET /api/studio/projects/{id}/voice-map returns 200."""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print(f"✓ GET voice-map returned 200")

    def test_get_voice_map_has_required_fields(self, api_client):
        """Response contains voice_map and voice_details."""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "voice_map" in data, "Response missing 'voice_map' field"
        assert "voice_details" in data, "Response missing 'voice_details' field"
        print(f"✓ voice_map has {len(data['voice_map'])} characters, voice_details has {len(data['voice_details'])} entries")

    def test_auto_assign_voices_endpoint_exists(self, api_client):
        """POST /api/studio/projects/{id}/auto-assign-voices returns 200."""
        response = api_client.post(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/auto-assign-voices", json={}, timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print(f"✓ POST auto-assign-voices returned 200")

    def test_auto_assign_returns_voice_map(self, api_client):
        """Auto-assign returns voice_map and voice_details."""
        response = api_client.post(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/auto-assign-voices", json={}, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "voice_map" in data, "Response missing 'voice_map'"
        assert "voice_details" in data, "Response missing 'voice_details'"
        assert len(data["voice_map"]) > 0, "voice_map is empty"
        print(f"✓ Auto-assign mapped {len(data['voice_map'])} characters")

    def test_update_voice_map_endpoint_exists(self, api_client):
        """POST /api/studio/projects/{id}/voice-map saves manual edits."""
        # Use a valid ElevenLabs voice ID (Rachel)
        test_voice_id = "21m00Tcm4TlvDq8ikWAM"
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/voice-map",
            json={"voice_map": {TEST_CHARACTER: test_voice_id}},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "voice_map" in data
        assert data["voice_map"].get(TEST_CHARACTER) == test_voice_id, "Voice map not updated correctly"
        print(f"✓ POST voice-map updated {TEST_CHARACTER} to {test_voice_id}")


class TestSoundDesignAgentSingleCharacter:
    """Test Sound Design Agent for single character voice generation."""

    def test_design_character_voice_endpoint_exists(self, api_client):
        """POST /api/studio/projects/{id}/design-character-voice returns 200."""
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/design-character-voice",
            json={"character_name": TEST_CHARACTER},
            timeout=60  # Single character takes 10-20s
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        print(f"✓ POST design-character-voice returned 200 for {TEST_CHARACTER}")

    def test_design_character_voice_response_structure(self, api_client):
        """Response includes voice_description and previews array."""
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/design-character-voice",
            json={"character_name": TEST_CHARACTER},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "character_name" in data, "Response missing 'character_name'"
        assert data["character_name"] == TEST_CHARACTER
        
        assert "voice_description" in data, "Response missing 'voice_description'"
        assert isinstance(data["voice_description"], str), "voice_description should be a string"
        assert len(data["voice_description"]) > 50, f"voice_description too short: {len(data['voice_description'])} chars"
        
        assert "previews" in data, "Response missing 'previews'"
        assert isinstance(data["previews"], list), "previews should be a list"
        
        print(f"✓ voice_description: {data['voice_description'][:100]}...")
        print(f"✓ previews count: {len(data['previews'])}")

    def test_design_character_voice_previews_structure(self, api_client):
        """Each preview has generated_voice_id, audio_base64, duration_secs."""
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/design-character-voice",
            json={"character_name": TEST_CHARACTER},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        
        previews = data.get("previews", [])
        assert len(previews) >= 1, "Expected at least 1 preview"
        
        for i, preview in enumerate(previews):
            assert "generated_voice_id" in preview, f"Preview {i} missing 'generated_voice_id'"
            assert isinstance(preview["generated_voice_id"], str), f"Preview {i} generated_voice_id should be string"
            assert len(preview["generated_voice_id"]) > 10, f"Preview {i} generated_voice_id too short"
            
            assert "audio_base64" in preview, f"Preview {i} missing 'audio_base64'"
            assert isinstance(preview["audio_base64"], str), f"Preview {i} audio_base64 should be string"
            assert len(preview["audio_base64"]) > 1000, f"Preview {i} audio_base64 too short (likely empty)"
            
            assert "duration_secs" in preview, f"Preview {i} missing 'duration_secs'"
            assert isinstance(preview["duration_secs"], (int, float)), f"Preview {i} duration_secs should be number"
            
            print(f"✓ Preview {i}: voice_id={preview['generated_voice_id'][:20]}..., duration={preview['duration_secs']}s, audio_size={len(preview['audio_base64'])} chars")

    def test_design_character_voice_invalid_character(self, api_client):
        """Returns 404 for non-existent character."""
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/design-character-voice",
            json={"character_name": "NonExistentCharacter12345"},
            timeout=30
        )
        assert response.status_code == 404, f"Expected 404 for invalid character, got {response.status_code}"
        print(f"✓ Returns 404 for non-existent character")


class TestSelectDesignedVoice:
    """Test saving a designed voice preview as permanent voice."""

    def test_select_designed_voice_requires_valid_preview(self, api_client):
        """Returns error for invalid generated_voice_id."""
        response = api_client.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/select-designed-voice",
            json={
                "character_name": TEST_CHARACTER,
                "generated_voice_id": "invalid_voice_id_12345",
                "voice_name": "Test Voice"
            },
            timeout=30
        )
        # Should return 500 (ElevenLabs API error) or 400 (validation error)
        assert response.status_code in [400, 500], f"Expected 400/500 for invalid voice_id, got {response.status_code}"
        print(f"✓ Returns error for invalid generated_voice_id: {response.status_code}")


class TestVoicesEndpoint:
    """Test the voices catalog endpoint."""

    def test_get_voices_catalog(self, api_client):
        """GET /api/studio/voices returns voice catalog."""
        response = api_client.get(f"{BASE_URL}/api/studio/voices", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "voices" in data, "Response missing 'voices'"
        assert len(data["voices"]) > 0, "Voices catalog is empty"
        
        # Check voice structure
        voice = data["voices"][0]
        assert "id" in voice, "Voice missing 'id'"
        assert "name" in voice, "Voice missing 'name'"
        assert "gender" in voice, "Voice missing 'gender'"
        
        print(f"✓ Voices catalog has {len(data['voices'])} voices")
        print(f"✓ Sample voice: {voice['name']} ({voice['gender']})")


class TestProjectExists:
    """Verify test project exists and has characters."""

    def test_project_exists(self, api_client):
        """GET /api/studio/projects/{id} returns project data."""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}", timeout=30)
        assert response.status_code == 200, f"Test project not found: {response.status_code}"
        data = response.json()
        assert "name" in data, "Project missing 'name'"
        print(f"✓ Project found: {data.get('name', 'Unknown')}")

    def test_project_has_characters(self, api_client):
        """Project has characters for voice assignment."""
        response = api_client.get(f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}", timeout=30)
        assert response.status_code == 200
        data = response.json()
        characters = data.get("characters", [])
        assert len(characters) > 0, "Project has no characters"
        
        # Check if test character exists
        char_names = [c.get("name") for c in characters]
        assert TEST_CHARACTER in char_names, f"Test character '{TEST_CHARACTER}' not found in project"
        
        print(f"✓ Project has {len(characters)} characters")
        print(f"✓ Characters: {', '.join(char_names[:5])}{'...' if len(char_names) > 5 else ''}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
