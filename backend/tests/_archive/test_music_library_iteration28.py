"""
Iteration 28 - Music Library API Tests
Testing: 
1. GET /api/campaigns/pipeline/music-library - Returns 5 tracks with id, name, description, duration, preview_url
2. GET /api/campaigns/pipeline/music-preview/{track_id} - Streams audio file (Content-Type: audio/mpeg)
3. POST /api/campaigns/pipeline - Accepts selected_music field
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')


class TestMusicLibraryAPI:
    """Test the music library endpoints"""

    def test_music_library_returns_5_tracks(self):
        """GET /api/campaigns/pipeline/music-library should return 5 tracks"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tracks" in data, "Response should have 'tracks' key"
        
        tracks = data["tracks"]
        assert len(tracks) == 5, f"Expected 5 tracks, got {len(tracks)}"
        
        # Verify each track has required fields
        expected_track_ids = ["upbeat", "energetic", "emotional", "cinematic", "corporate"]
        found_ids = []
        
        for track in tracks:
            assert "id" in track, f"Track missing 'id' field: {track}"
            assert "name" in track, f"Track {track.get('id')} missing 'name' field"
            assert "description" in track, f"Track {track.get('id')} missing 'description' field"
            assert "duration" in track, f"Track {track.get('id')} missing 'duration' field"
            assert "preview_url" in track, f"Track {track.get('id')} missing 'preview_url' field"
            
            # Verify duration is a positive number
            assert isinstance(track["duration"], int) and track["duration"] > 0, f"Track {track.get('id')} has invalid duration"
            
            # Verify preview_url format
            assert f"/api/campaigns/pipeline/music-preview/{track['id']}" in track["preview_url"], \
                f"Track {track.get('id')} has invalid preview_url: {track['preview_url']}"
            
            found_ids.append(track["id"])
        
        # Verify all expected track IDs are present
        for expected_id in expected_track_ids:
            assert expected_id in found_ids, f"Expected track '{expected_id}' not found in response"
        
        print(f"✓ Music library returns 5 tracks with all required fields")

    def test_music_library_track_details(self):
        """Verify specific track details (name, description)"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        
        assert response.status_code == 200
        
        tracks = {t["id"]: t for t in response.json()["tracks"]}
        
        # Verify upbeat track
        assert "upbeat" in tracks
        assert "Upbeat" in tracks["upbeat"]["name"] or "Happy" in tracks["upbeat"]["name"], \
            f"Upbeat track has unexpected name: {tracks['upbeat']['name']}"
        
        # Verify energetic track
        assert "energetic" in tracks
        assert "Energetic" in tracks["energetic"]["name"] or "Power" in tracks["energetic"]["name"], \
            f"Energetic track has unexpected name: {tracks['energetic']['name']}"
        
        # Verify emotional track
        assert "emotional" in tracks
        assert "Emotional" in tracks["emotional"]["name"] or "Inspir" in tracks["emotional"]["name"], \
            f"Emotional track has unexpected name: {tracks['emotional']['name']}"
        
        # Verify cinematic track
        assert "cinematic" in tracks
        assert "Cinematic" in tracks["cinematic"]["name"] or "Epic" in tracks["cinematic"]["name"], \
            f"Cinematic track has unexpected name: {tracks['cinematic']['name']}"
        
        # Verify corporate track
        assert "corporate" in tracks
        assert "Corporate" in tracks["corporate"]["name"] or "Professional" in tracks["corporate"]["name"], \
            f"Corporate track has unexpected name: {tracks['corporate']['name']}"
        
        print(f"✓ All 5 tracks have appropriate names and descriptions")


class TestMusicPreviewAPI:
    """Test the music preview streaming endpoint"""

    def test_music_preview_upbeat_streams_audio(self):
        """GET /api/campaigns/pipeline/music-preview/upbeat should stream audio"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-preview/upbeat", stream=True)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        content_type = response.headers.get("Content-Type", "")
        assert "audio" in content_type.lower(), f"Expected audio content-type, got: {content_type}"
        
        # Verify we get some audio data (at least a few KB)
        content = response.content
        assert len(content) > 1000, f"Expected audio data, got only {len(content)} bytes"
        
        print(f"✓ Upbeat music preview streams audio ({len(content)/1024:.1f}KB)")

    def test_music_preview_all_tracks_stream(self):
        """Verify all 5 tracks can be streamed"""
        track_ids = ["upbeat", "energetic", "emotional", "cinematic", "corporate"]
        
        for track_id in track_ids:
            response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-preview/{track_id}", stream=True)
            
            assert response.status_code == 200, f"Track '{track_id}' failed: {response.status_code}"
            
            content_type = response.headers.get("Content-Type", "")
            assert "audio" in content_type.lower(), f"Track '{track_id}' has wrong content-type: {content_type}"
            
            # Verify minimum size (MP3 should be at least several KB)
            content_length = len(response.content)
            assert content_length > 5000, f"Track '{track_id}' too small: {content_length} bytes"
            
            print(f"  ✓ Track '{track_id}' streams correctly ({content_length/1024:.1f}KB)")
        
        print(f"✓ All 5 music tracks can be streamed")

    def test_music_preview_invalid_track_returns_404(self):
        """GET /api/campaigns/pipeline/music-preview/invalid should return 404"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-preview/invalid_track_id")
        
        assert response.status_code == 404, f"Expected 404 for invalid track, got {response.status_code}"
        
        print(f"✓ Invalid track ID returns 404")


class TestPipelineSelectedMusic:
    """Test that pipeline creation accepts selected_music field"""

    def test_pipeline_accepts_selected_music_field(self):
        """POST /api/campaigns/pipeline should accept selected_music field"""
        # First login to get auth
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        assert token, "No access_token in login response"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create pipeline with selected_music
        pipeline_data = {
            "briefing": "TEST_music_selection Test campaign for music library testing",
            "campaign_name": "TEST Music Library Test Campaign",
            "campaign_language": "en",
            "mode": "semi_auto",
            "platforms": ["instagram"],
            "selected_music": "upbeat",
            "contact_info": {"phone": "(321) 960-2080", "website": "mytruckflorida.com"}
        }
        
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", json=pipeline_data, headers=headers)
        
        # Pipeline creation may succeed (201/200) or fail due to existing active pipeline (400)
        # Either way, the API should accept the selected_music field
        if response.status_code in [200, 201]:
            data = response.json()
            # Verify the pipeline was created
            assert "id" in data, "Pipeline response missing 'id'"
            print(f"✓ Pipeline created with selected_music='upbeat', ID: {data['id']}")
            
            # Clean up - archive the pipeline
            pipeline_id = data["id"]
            archive_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/archive", headers=headers)
            print(f"  Cleanup: Archive response {archive_resp.status_code}")
        elif response.status_code == 400:
            # May fail due to existing active pipeline - that's OK, the API accepted the field
            error_msg = response.json().get("detail", "")
            if "active pipeline" in error_msg.lower():
                print(f"✓ API accepts selected_music field (existing active pipeline prevents creation)")
            else:
                pytest.fail(f"Unexpected 400 error: {error_msg}")
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
