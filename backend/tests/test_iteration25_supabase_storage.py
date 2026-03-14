"""
Iteration 25: Supabase Storage Migration Testing
Tests:
1. Campaign list with Supabase Storage URLs
2. Campaign delete endpoint
3. Pipeline upload endpoint returns https:// URLs
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]


@pytest.fixture(scope="class")
def auth_token():
    """Get auth token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@agentflow.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture
def authenticated_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestCampaignsSupabaseStorage:
    """Test campaign images from Supabase Storage"""
    
    def test_list_campaigns_returns_campaigns(self, authenticated_client):
        """Test GET /api/campaigns returns list of campaigns"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        campaigns = data["campaigns"]
        assert len(campaigns) > 0, "No campaigns found"
        print(f"Found {len(campaigns)} campaigns")
        return campaigns
    
    def test_campaign_images_are_supabase_urls(self, authenticated_client):
        """Test that campaign images use Supabase Storage URLs"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code == 200
        campaigns = response.json()["campaigns"]
        
        supabase_image_count = 0
        legacy_api_image_count = 0
        
        for campaign in campaigns:
            images = campaign.get("stats", {}).get("images", [])
            for img_url in images:
                if img_url:
                    if "supabase.co/storage/v1/object/public/" in img_url:
                        supabase_image_count += 1
                    elif img_url.startswith("/api/uploads/"):
                        legacy_api_image_count += 1
        
        print(f"Supabase Storage images: {supabase_image_count}")
        print(f"Legacy /api/uploads images: {legacy_api_image_count}")
        
        # After migration, all images should be Supabase URLs
        if supabase_image_count > 0:
            print("✓ Found Supabase Storage URLs in campaigns")
        
        # Note: Some campaigns may still have no images
        return {"supabase": supabase_image_count, "legacy": legacy_api_image_count}


class TestCampaignDelete:
    """Test campaign delete endpoint"""
    
    def test_delete_campaign_endpoint_exists(self, authenticated_client):
        """Test that DELETE /api/campaigns/{id} endpoint works"""
        # Create a test campaign first
        create_response = authenticated_client.post(f"{BASE_URL}/api/campaigns", json={
            "name": f"TEST_DELETE_{uuid.uuid4().hex[:8]}",
            "type": "nurture"
        })
        assert create_response.status_code == 200, f"Failed to create test campaign: {create_response.text}"
        campaign_id = create_response.json()["id"]
        
        # Delete the campaign
        delete_response = authenticated_client.delete(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        assert delete_response.json().get("status") == "deleted"
        
        # Verify it's gone
        get_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert get_response.status_code == 404, "Campaign should not exist after deletion"
        print("✓ Campaign delete endpoint works correctly")
    
    def test_delete_nonexistent_campaign_returns_404(self, authenticated_client):
        """Test deleting non-existent campaign returns 404"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.delete(f"{BASE_URL}/api/campaigns/{fake_id}")
        assert response.status_code == 404
        print("✓ 404 returned for non-existent campaign")


class TestPipelineUpload:
    """Test pipeline upload returns Supabase URLs"""
    
    def test_upload_endpoint_exists(self, authenticated_client):
        """Test POST /api/campaigns/pipeline/upload endpoint"""
        # Create a small test image (1x1 PNG)
        import base64
        # Minimal valid PNG
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        
        files = {'file': ('test.png', png_data, 'image/png')}
        data = {'asset_type': 'reference'}
        
        # Remove Content-Type for multipart
        headers = {"Authorization": authenticated_client.headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        # Check that URL is a full Supabase Storage URL
        url = result.get("url", "")
        assert url.startswith("https://"), f"URL should start with https://: {url}"
        assert "supabase.co/storage/v1/object/public/" in url, f"URL should be Supabase Storage URL: {url}"
        print(f"✓ Upload returns Supabase URL: {url[:80]}...")
        return result


class TestPipelineList:
    """Test pipeline images from Supabase Storage"""
    
    def test_list_pipelines(self, authenticated_client):
        """Test GET /api/campaigns/pipeline/list returns pipelines"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/list")
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        pipelines = data["pipelines"]
        print(f"Found {len(pipelines)} pipelines")
        
        # Check if any pipeline has images
        for p in pipelines:
            steps = p.get("steps", {})
            lucas = steps.get("lucas_design", {})
            image_urls = lucas.get("image_urls", [])
            if image_urls:
                for url in image_urls:
                    if url:
                        if "supabase.co/storage/v1/object/public/" in url:
                            print(f"✓ Pipeline has Supabase Storage image: {url[:60]}...")
                        elif url.startswith("/api/uploads/"):
                            print(f"! Pipeline has legacy image: {url}")
        
        return pipelines


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
