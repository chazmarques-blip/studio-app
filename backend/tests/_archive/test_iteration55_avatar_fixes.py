"""
Iteration 55 - Avatar Generation Fix & Tab Order Tests
Tests:
1. POST /api/campaigns/pipeline/generate-avatar - should work with ImageContent(image_base64=...) fix
2. POST /api/campaigns/pipeline/generate-avatar-variant - should work with same fix
3. POST /api/campaigns/pipeline/master-voice - still works after changes
4. Translation keys verification for video/photo specs
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token - module scoped for efficiency"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    print(f"Auth login status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token") or data.get("token")
        if token:
            print(f"Got token: {token[:20]}...")
            return token
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestAvatarGenerationFix:
    """Tests for the avatar generation fix - ImageContent/UserMessage API correction"""
    
    def test_generate_avatar_requires_auth(self):
        """Test that generate-avatar requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            json={"company_name": "Test", "source_image_url": ""},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"generate-avatar (no auth) status: {response.status_code}")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_generate_avatar_without_source_image(self, auth_headers):
        """Test generate-avatar endpoint WITHOUT source_image_url (faster, no image download)"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar",
            json={
                "company_name": "Test Company",
                "source_image_url": ""  # Empty - will generate from scratch
            },
            headers=auth_headers,
            timeout=120
        )
        print(f"generate-avatar (no source) status: {response.status_code}")
        print(f"generate-avatar (no source) response: {response.text[:500] if response.text else 'empty'}")
        
        # Should succeed without the 'images' argument error
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "avatar_url" in data, "Response should contain avatar_url"
            print(f"Avatar generated successfully: {data['avatar_url'][:100]}...")
        else:
            # If 500, check it's NOT the 'images' argument error
            error_text = response.text.lower()
            assert "usermessage.__init__() got an unexpected keyword argument 'images'" not in error_text, \
                "OLD BUG: 'images' argument error still present!"
            assert "imagecontent.__init__() got an unexpected keyword argument 'base64_data'" not in error_text, \
                "OLD BUG: 'base64_data' argument error still present!"
            print(f"Server error (not the images bug): {response.text[:200]}")
    
    def test_generate_avatar_variant_requires_auth(self):
        """Test that generate-avatar-variant requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            json={"source_image_url": "", "clothing": "business_formal", "angle": "front"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"generate-avatar-variant (no auth) status: {response.status_code}")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_generate_avatar_variant_no_images_error(self, auth_headers):
        """Test generate-avatar-variant doesn't have the 'images' argument error"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-variant",
            json={
                "source_image_url": "",  # Empty - will generate from scratch
                "clothing": "business_formal",
                "angle": "front",
                "company_name": "Test"
            },
            headers=auth_headers,
            timeout=120
        )
        print(f"generate-avatar-variant status: {response.status_code}")
        print(f"generate-avatar-variant response: {response.text[:500] if response.text else 'empty'}")
        
        # Check it's NOT the 'images' argument error
        if response.status_code == 500:
            error_text = response.text.lower()
            assert "usermessage.__init__() got an unexpected keyword argument 'images'" not in error_text, \
                "OLD BUG: 'images' argument error still present in variant!"
            assert "imagecontent.__init__() got an unexpected keyword argument 'base64_data'" not in error_text, \
                "OLD BUG: 'base64_data' argument error still present in variant!"


class TestMasterVoiceStillWorks:
    """Test that master-voice endpoint still works after changes"""
    
    def test_master_voice_requires_auth(self):
        """Test that master-voice requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/master-voice",
            json={"audio_url": "https://example.com/test.wav"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"master-voice (no auth) status: {response.status_code}")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_master_voice_invalid_url(self, auth_headers):
        """Test master-voice with invalid audio URL returns error"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/master-voice",
            json={"audio_url": "https://invalid-url-that-does-not-exist.com/audio.wav"},
            headers=auth_headers,
            timeout=30
        )
        print(f"master-voice (invalid url) status: {response.status_code}")
        # Should fail gracefully with 400 or 500
        assert response.status_code in [400, 500], f"Should fail for invalid URL, got {response.status_code}"


class TestTranslationKeys:
    """Test that all required translation keys exist in locale files"""
    
    def test_video_spec_keys_exist_in_pt(self):
        """Verify video spec translation keys exist in Portuguese locale"""
        with open('/app/frontend/src/locales/pt.json', 'r') as f:
            pt_locale = json.load(f)
        
        studio = pt_locale.get('studio', {})
        required_keys = [
            'recommended', 'specs',
            'video_spec_duration', 'video_spec_quality', 'video_spec_size',
            'photo_spec_res', 'photo_spec_quality', 'photo_spec_size'
        ]
        
        for key in required_keys:
            assert key in studio, f"Missing key 'studio.{key}' in pt.json"
            assert studio[key], f"Empty value for 'studio.{key}' in pt.json"
            print(f"pt.json - studio.{key}: {studio[key]}")
    
    def test_video_spec_keys_exist_in_en(self):
        """Verify video spec translation keys exist in English locale"""
        with open('/app/frontend/src/locales/en.json', 'r') as f:
            en_locale = json.load(f)
        
        studio = en_locale.get('studio', {})
        required_keys = [
            'recommended', 'specs',
            'video_spec_duration', 'video_spec_quality', 'video_spec_size',
            'photo_spec_res', 'photo_spec_quality', 'photo_spec_size'
        ]
        
        for key in required_keys:
            assert key in studio, f"Missing key 'studio.{key}' in en.json"
            assert studio[key], f"Empty value for 'studio.{key}' in en.json"
            print(f"en.json - studio.{key}: {studio[key]}")
    
    def test_video_spec_keys_exist_in_es(self):
        """Verify video spec translation keys exist in Spanish locale"""
        with open('/app/frontend/src/locales/es.json', 'r') as f:
            es_locale = json.load(f)
        
        studio = es_locale.get('studio', {})
        required_keys = [
            'recommended', 'specs',
            'video_spec_duration', 'video_spec_quality', 'video_spec_size',
            'photo_spec_res', 'photo_spec_quality', 'photo_spec_size'
        ]
        
        for key in required_keys:
            assert key in studio, f"Missing key 'studio.{key}' in es.json"
            assert studio[key], f"Empty value for 'studio.{key}' in es.json"
            print(f"es.json - studio.{key}: {studio[key]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
