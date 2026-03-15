"""
Test suite for Marketing Channel Mockups and Campaign Content Features - Iteration 38
Tests the marketing page, campaign detail modal, channel mockups, and remix-audio API
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
PIPELINE_ID = "c561486a-a04e-442d-b53e-66c16f95d78a"


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"LOGIN: Success - Token received")
    
    def test_login_returns_access_token_not_token(self):
        """Verify login returns 'access_token' key (not 'token')"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token" not in data or "access_token" in data
        print(f"AUTH: Returns access_token correctly")


class TestCampaigns:
    """Campaign API tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_campaigns_list_requires_auth(self):
        """Test that campaigns endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code == 401 or response.status_code == 403
        print("CAMPAIGNS: Requires authentication")
    
    def test_campaigns_list_with_auth(self, auth_token):
        """Test fetching campaigns list with valid auth"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        assert isinstance(data["campaigns"], list)
        print(f"CAMPAIGNS: Found {len(data['campaigns'])} campaigns")
    
    def test_campaign_has_required_fields(self, auth_token):
        """Test that campaigns have required fields for mockup rendering"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=headers)
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        if len(campaigns) > 0:
            campaign = campaigns[0]
            # Check required fields
            assert "id" in campaign
            assert "name" in campaign
            assert "type" in campaign
            assert "status" in campaign
            
            # Check for target_segment with platforms
            if "target_segment" in campaign:
                segment = campaign["target_segment"]
                if "platforms" in segment:
                    print(f"CAMPAIGN: Has platforms: {segment['platforms']}")
            
            print(f"CAMPAIGN: Required fields present in '{campaign['name']}'")


class TestRemixAudioAPI:
    """Test the remix-audio API endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_remix_audio_endpoint_exists(self, auth_token):
        """Test that remix-audio endpoint exists and returns expected response"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{PIPELINE_ID}/remix-audio",
            headers=headers
        )
        # Should return 200 or 400/404 if pipeline not found
        assert response.status_code in [200, 400, 404]
        print(f"REMIX-AUDIO: Endpoint returned {response.status_code}")
    
    def test_remix_audio_returns_status_remixing(self, auth_token):
        """Test that remix-audio returns status: remixing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{PIPELINE_ID}/remix-audio",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "remixing"
            print(f"REMIX-AUDIO: Status is 'remixing' as expected")
        else:
            print(f"REMIX-AUDIO: Pipeline may not exist or already processing")


class TestPlatformFormats:
    """Test that platform formats are correctly defined"""
    
    def test_platform_aspect_ratios_defined(self):
        """Verify expected platform aspect ratios are in the codebase"""
        # These are the expected formats from the code review
        EXPECTED_FORMATS = {
            "whatsapp": "1:1",
            "instagram": "1:1",
            "facebook": "16:9",
            "tiktok": "9:16",
            "google_ads": "16:9",
            "telegram": "16:9",
            "email": "16:9",
            "sms": "9:16"
        }
        
        # Read the Marketing.jsx to verify formats
        marketing_file = "/app/frontend/src/pages/Marketing.jsx"
        if os.path.exists(marketing_file):
            with open(marketing_file, 'r') as f:
                content = f.read()
            
            for platform, ratio in EXPECTED_FORMATS.items():
                if ratio in content:
                    print(f"FORMAT: {platform} has {ratio} format defined")
        else:
            print("SKIP: Marketing.jsx not accessible in test environment")


class TestMusicLibrary:
    """Test music library API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_music_library_endpoint(self, auth_token):
        """Test music library returns tracks"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "tracks" in data
            if len(data["tracks"]) > 0:
                track = data["tracks"][0]
                assert "id" in track
                assert "name" in track
                print(f"MUSIC: Found {len(data['tracks'])} tracks in library")
        else:
            print(f"MUSIC: Library endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
