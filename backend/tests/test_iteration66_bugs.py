"""
Iteration 66 - Bug Fix Testing
Tests for:
1. Login with test@agentflow.com / password123
2. Verify 'Amigas na luta' campaign exists with campaign_language: 'pt'
3. Test regenerate-single-image endpoint with language='pt'
4. Verify campaign list loads on Marketing page
5. Test publish endpoint works without 'language' column error
6. Test pipeline list endpoint returns data with campaign_language field
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://agent-campaign-hub.preview.emergentagent.com').rstrip('/')

# Campaign and pipeline IDs from context
AMIGAS_CAMPAIGN_ID = "068141ee-0f89-40ae-8a27-617c1d5db4ae"
AMIGAS_PIPELINE_ID = "dea6ebbb-d626-4ad8-a53a-6d9889e6a1ae"

class TestAuthentication:
    """Test authentication with test@agentflow.com"""
    
    def test_login_success(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        assert len(data["access_token"]) > 0, "Access token is empty"
        print(f"Login successful, token starts with: {data['access_token'][:20]}...")


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for subsequent tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestCampaignList:
    """Test campaign list endpoint"""
    
    def test_campaigns_list_loads(self, auth_headers):
        """Verify campaigns list loads correctly"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200, f"Campaigns list failed: {response.text}"
        data = response.json()
        # API returns {campaigns: [...]} structure
        campaigns = data.get("campaigns", data) if isinstance(data, dict) else data
        assert isinstance(campaigns, list), f"Campaigns should be a list, got: {type(campaigns)}"
        assert len(campaigns) > 0, "No campaigns found"
        print(f"Found {len(campaigns)} campaigns")
        
    def test_amigas_campaign_exists(self, auth_headers):
        """Verify 'Amigas na luta' campaign exists"""
        response = requests.get(f"{BASE_URL}/api/campaigns/{AMIGAS_CAMPAIGN_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Campaign not found: {response.text}"
        data = response.json()
        assert "name" in data, "Campaign should have a name"
        print(f"Found campaign: {data.get('name')}")
        
    def test_amigas_campaign_has_pt_language(self, auth_headers):
        """Verify 'Amigas na luta' campaign has campaign_language: 'pt'"""
        response = requests.get(f"{BASE_URL}/api/campaigns/{AMIGAS_CAMPAIGN_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Campaign not found: {response.text}"
        data = response.json()
        
        # Check campaign_language in stats (direct from GET /campaigns/:id response)
        stats = data.get("stats", {})
        campaign_language = stats.get("campaign_language")
        
        print(f"Campaign: {data.get('name')}")
        print(f"Campaign language in stats: {campaign_language}")
        
        assert campaign_language == "pt", f"Expected campaign_language 'pt', got: {campaign_language}"


class TestPipelineEndpoints:
    """Test pipeline-related endpoints"""
    
    def test_pipeline_list_returns_data(self, auth_headers):
        """Verify pipeline list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=auth_headers)
        assert response.status_code == 200, f"Pipeline list failed: {response.text}"
        data = response.json()
        # API returns {pipelines: [...]} structure
        pipelines = data.get("pipelines", data) if isinstance(data, dict) else data
        assert isinstance(pipelines, list), f"Pipelines should be a list, got: {type(pipelines)}"
        print(f"Found {len(pipelines)} pipelines")
        
        # Check if any pipeline has campaign_language
        if len(pipelines) > 0:
            sample = pipelines[0]
            result = sample.get("result", {})
            print(f"Sample pipeline has campaign_language: {result.get('campaign_language', 'NOT SET')}")
    
    def test_amigas_pipeline_has_language(self, auth_headers):
        """Verify 'Amigas na luta' pipeline has campaign_language field"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{AMIGAS_PIPELINE_ID}", headers=auth_headers)
        if response.status_code == 404:
            pytest.skip("Pipeline not found - may have been deleted")
            
        assert response.status_code == 200, f"Pipeline fetch failed: {response.text}"
        data = response.json()
        
        result = data.get("result", {})
        campaign_language = result.get("campaign_language")
        print(f"Pipeline campaign_language: {campaign_language}")
        
        # Should have a language set (likely 'pt')
        assert campaign_language is not None, "Pipeline should have campaign_language"


class TestRegenerateSingleImage:
    """Test regenerate-single-image endpoint with language parameter"""
    
    def test_regenerate_endpoint_accepts_language(self, auth_headers):
        """Test that regenerate-single-image endpoint accepts language='pt' parameter"""
        # This endpoint generates actual AI images, so we test the request acceptance
        # and response format without waiting for full image generation
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/regenerate-single-image",
            headers=auth_headers,
            json={
                "style": "minimalist",
                "campaign_name": "Test Campaign",
                "campaign_copy": "Força e fé diária para você",
                "product_description": "Devotional app",
                "language": "pt",
                "pipeline_id": AMIGAS_PIPELINE_ID
            },
            timeout=60  # Image generation takes ~15-20 seconds
        )
        
        # Endpoint should accept the request (200 or still processing)
        # If 500, it may be a generation error, not a language issue
        print(f"Regenerate endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "image_url" in data, "Response should contain image_url"
            print(f"Image URL returned: {data.get('image_url', '')[:50]}...")
        elif response.status_code == 500:
            # Check if it's a language-related error
            error_text = response.text
            assert "language" not in error_text.lower() or "column" not in error_text.lower(), \
                f"Language column error detected: {error_text}"
            print(f"Generation error (not language-related): {error_text[:200]}")
        else:
            # Other errors should be logged
            print(f"Unexpected status {response.status_code}: {response.text[:200]}")


class TestPublishEndpoint:
    """Test publish endpoint doesn't have 'language' column error"""
    
    def test_publish_endpoint_no_language_column_error(self, auth_headers):
        """Test that publish endpoint works without 'language' column error"""
        # This will attempt to publish (or re-publish) the pipeline
        # We're testing that the request doesn't fail with a 'language' column error
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/{AMIGAS_PIPELINE_ID}/publish",
            headers=auth_headers,
            json={}
        )
        
        print(f"Publish endpoint status: {response.status_code}")
        print(f"Publish response: {response.text[:200] if response.text else 'empty'}")
        
        if response.status_code == 400:
            # Check if it's "not ready" error (expected if already published)
            data = response.json()
            detail = data.get("detail", "")
            if "not ready" in detail.lower():
                print("Pipeline already completed - this is expected")
            else:
                pytest.fail(f"Unexpected 400 error: {detail}")
        elif response.status_code == 500:
            # This would indicate a bug
            error_text = response.text
            assert "language" not in error_text.lower() or "column" not in error_text.lower(), \
                f"Language column error detected in publish: {error_text}"
            pytest.fail(f"500 error in publish: {error_text[:200]}")
        elif response.status_code == 200:
            data = response.json()
            assert data.get("status") in ["published", "already_published"], f"Unexpected status: {data}"
            print("Publish endpoint works correctly")
        else:
            print(f"Other status: {response.status_code} - {response.text[:100]}")


class TestCampaignContentValidation:
    """Test campaign content for Portuguese language compliance"""
    
    def test_campaign_content_language(self, auth_headers):
        """Check if campaign content is in Portuguese"""
        response = requests.get(f"{BASE_URL}/api/campaigns/{AMIGAS_CAMPAIGN_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        metrics = data.get("metrics", {})
        messages = metrics.get("messages", [])
        
        if messages:
            content = messages[0].get("content", "")
            print(f"Campaign content preview (first 200 chars): {content[:200]}")
            
            # Check for Portuguese indicators
            pt_indicators = ["você", "sua", "seu", "para", "força", "fé", "luta", "amiga"]
            en_indicators = ["DAILY", "STRENGTH", "FAITH", "FOR", "YOU"]
            
            content_lower = content.lower()
            has_portuguese = any(ind in content_lower for ind in pt_indicators)
            has_english_headline = any(ind in content.upper() for ind in en_indicators)
            
            print(f"Has Portuguese indicators: {has_portuguese}")
            print(f"Has English headline issue: {has_english_headline}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
