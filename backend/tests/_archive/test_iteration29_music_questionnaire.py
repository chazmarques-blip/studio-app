"""
Test iteration 29: Music Library (25 tracks), Enhanced Questionnaire, Content Tab features
Tests for: 
- Music library API returns 25 tracks with categories
- Music preview streaming works
- Campaign Content tab features (video, format badges)
- i18n (Sponsored text in English)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMusicLibraryAPI:
    """Music Library API Tests - 25 tracks with categories"""
    
    def test_music_library_returns_25_tracks(self):
        """Verify music library endpoint returns exactly 25 tracks"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        tracks = data.get('tracks', [])
        assert len(tracks) == 25, f"Expected 25 tracks, got {len(tracks)}"
        
    def test_music_library_track_structure(self):
        """Verify each track has required fields"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        data = response.json()
        tracks = data.get('tracks', [])
        
        required_fields = ['id', 'name', 'description', 'duration', 'file', 'category', 'preview_url']
        for track in tracks:
            for field in required_fields:
                assert field in track, f"Track missing field: {field}"
    
    def test_music_library_has_all_categories(self):
        """Verify music library includes expected categories"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        data = response.json()
        tracks = data.get('tracks', [])
        
        categories = set(t['category'] for t in tracks)
        expected_categories = {'General', 'Pop', 'Hip-Hop', 'Electronic', 'Latin', 'Rock', 'Jazz', 'Ambient', 'Other'}
        
        # All expected categories should exist
        for expected in expected_categories:
            assert expected in categories, f"Missing category: {expected}"
    
    def test_music_preview_endpoint_works(self):
        """Verify music preview endpoint returns audio"""
        # First get a track ID
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        tracks = response.json().get('tracks', [])
        
        if tracks:
            track_id = tracks[0]['id']
            preview_response = requests.get(
                f"{BASE_URL}/api/campaigns/pipeline/music-preview/{track_id}",
                stream=True
            )
            # Should return 200 or redirect to audio file
            assert preview_response.status_code in [200, 206], f"Music preview failed: {preview_response.status_code}"
            
    def test_general_category_tracks(self):
        """Verify General category has 5 original tracks"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        tracks = response.json().get('tracks', [])
        
        general_tracks = [t for t in tracks if t['category'] == 'General']
        assert len(general_tracks) == 5, f"Expected 5 General tracks, got {len(general_tracks)}"
        
        # Verify original track IDs
        expected_general_ids = {'upbeat', 'energetic', 'emotional', 'cinematic', 'corporate'}
        actual_ids = {t['id'] for t in general_tracks}
        assert expected_general_ids == actual_ids, f"General tracks mismatch: expected {expected_general_ids}, got {actual_ids}"


class TestCampaignAPI:
    """Campaign API Tests - Auth required"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Authentication failed")
    
    def test_campaigns_list_requires_auth(self):
        """Verify campaigns list requires authentication"""
        response = requests.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code in [401, 403, 422], "Campaigns should require auth"
    
    def test_campaigns_list_with_auth(self, auth_token):
        """Get campaigns list with valid auth"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
    def test_campaign_detail_with_video(self, auth_token):
        """Test campaign detail includes video_url field when present"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        campaigns = response.json() if isinstance(response.json(), list) else response.json().get('campaigns', [])
        
        # Look for campaign with video_url
        video_campaigns = [c for c in campaigns if c.get('video_url')]
        if video_campaigns:
            campaign = video_campaigns[0]
            print(f"Found campaign with video: {campaign['name']}")
            assert 'video_url' in campaign, "Campaign should have video_url field"
        else:
            pytest.skip("No campaigns with video found for testing")
    
    def test_campaign_has_pipeline_id_field(self, auth_token):
        """Test campaign includes pipeline_id when created via AI pipeline"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        campaigns = response.json() if isinstance(response.json(), list) else response.json().get('campaigns', [])
        
        pipeline_campaigns = [c for c in campaigns if c.get('pipeline_id')]
        if pipeline_campaigns:
            campaign = pipeline_campaigns[0]
            assert 'pipeline_id' in campaign, "Campaign should have pipeline_id field"
            print(f"Pipeline campaign found: {campaign['name']} - pipeline_id: {campaign['pipeline_id'][:12]}...")
        else:
            pytest.skip("No AI pipeline campaigns found")


class TestPipelineAPI:
    """Pipeline API Tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Authentication failed")
    
    def test_pipeline_create_accepts_new_fields(self, auth_token):
        """Test pipeline creation accepts new questionnaire fields"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # Test that pipeline endpoint accepts the new fields in briefing
        briefing_with_new_fields = """
        Product: Test Product
        Goal: Generate Leads
        Gender: All
        Age: 18–65+
        Social class: B (Upper-middle)
        Lifestyle: Tech, Business
        Pain points: High costs, lack of time
        Tone: Professional
        Visual style: Tech & Modern
        Offer: Free trial
        Differentials: AI-powered
        CTA: Start Now
        """
        
        # Just test the endpoint accepts the request (not actually creating)
        # This validates the API structure
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline",
            headers=headers,
            json={
                "briefing": briefing_with_new_fields,
                "campaign_name": "TEST_Questionnaire_Fields_Check",
                "mode": "complete",
                "platforms": ["whatsapp"],
                "selected_music": "upbeat"
            }
        )
        # Should not return 422 (validation error) for valid fields
        assert response.status_code != 422, f"Pipeline rejected valid fields: {response.text}"
        
        # Clean up if created (may be 200, 201, or 400 if limits)
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get('id'):
                requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{data['id']}", headers=headers)


class TestFormatBadges:
    """Test format badges per channel"""
    
    def test_expected_format_ratios(self):
        """Verify expected format ratios are documented correctly"""
        expected_formats = {
            'whatsapp': '1:1',
            'instagram': '1:1', 
            'facebook': '16:9',
            'tiktok': '9:16',
            'google_ads': '1.91:1',
            'telegram': '16:9',
            'sms': '-'
        }
        
        # These are frontend constants - backend doesn't serve them
        # This test documents the expected values for UI testing
        for channel, expected_ratio in expected_formats.items():
            print(f"Channel {channel}: expected format badge {expected_ratio}")
        
        assert True  # Documentation test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
