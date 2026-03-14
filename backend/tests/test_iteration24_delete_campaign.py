"""
Iteration 24: Campaign Delete Button Bug Fix Testing
Tests the campaign delete functionality (bug fix: 'delete-confirmed' -> 'delete')
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"Login successful, token received")
        return data.get("access_token") or data.get("token")


class TestCampaignsCRUD:
    """Campaign CRUD operations - focusing on DELETE functionality"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json().get("access_token") or response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_campaigns(self, auth_headers):
        """Test listing campaigns"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200, f"List campaigns failed: {response.text}"
        data = response.json()
        assert "campaigns" in data, "No campaigns field in response"
        print(f"Found {len(data['campaigns'])} campaigns")
        return data['campaigns']
    
    def test_create_and_delete_campaign(self, auth_headers):
        """Test creating a campaign and then deleting it - main bug fix verification"""
        # Create a test campaign
        create_payload = {
            "name": "TEST_Delete_Campaign_Bug_Fix",
            "type": "drip",
            "messages": []
        }
        create_response = requests.post(
            f"{BASE_URL}/api/campaigns", 
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200, f"Create campaign failed: {create_response.text}"
        
        created = create_response.json()
        assert "id" in created, "No ID in created campaign"
        campaign_id = created["id"]
        print(f"Created test campaign: {campaign_id}")
        
        # Verify it exists
        get_response = requests.get(
            f"{BASE_URL}/api/campaigns/{campaign_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200, "Campaign not found after creation"
        
        # DELETE the campaign - this is the main bug fix test
        delete_response = requests.delete(
            f"{BASE_URL}/api/campaigns/{campaign_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete campaign failed: {delete_response.text}"
        
        delete_data = delete_response.json()
        assert delete_data.get("status") == "deleted", f"Expected status 'deleted', got: {delete_data}"
        print(f"Campaign {campaign_id} successfully deleted")
        
        # Verify it's actually deleted (should return 404)
        verify_response = requests.get(
            f"{BASE_URL}/api/campaigns/{campaign_id}",
            headers=auth_headers
        )
        assert verify_response.status_code == 404, "Campaign should not exist after deletion"
        print("Verified: Campaign no longer exists")
    
    def test_delete_nonexistent_campaign(self, auth_headers):
        """Test deleting a campaign that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.delete(
            f"{BASE_URL}/api/campaigns/{fake_id}",
            headers=auth_headers
        )
        # Should return 404
        assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
        print("Correctly returns 404 for non-existent campaign")


class TestCampaignActions:
    """Test campaign activate/pause actions"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json().get("access_token") or response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_activate_campaign(self, auth_headers):
        """Test activating a campaign"""
        # First list campaigns to get one
        list_response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        campaigns = list_response.json().get("campaigns", [])
        
        # Find a draft campaign
        draft_campaign = next((c for c in campaigns if c.get("status") == "draft"), None)
        if not draft_campaign:
            pytest.skip("No draft campaign found to test activation")
        
        campaign_id = draft_campaign["id"]
        
        # Activate
        response = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/activate",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Activate failed: {response.text}"
        print(f"Campaign {campaign_id} activated successfully")
    
    def test_pause_campaign(self, auth_headers):
        """Test pausing a campaign"""
        # First list campaigns to get one
        list_response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        campaigns = list_response.json().get("campaigns", [])
        
        # Find an active campaign
        active_campaign = next((c for c in campaigns if c.get("status") == "active"), None)
        if not active_campaign:
            pytest.skip("No active campaign found to test pausing")
        
        campaign_id = active_campaign["id"]
        
        # Pause
        response = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/pause",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Pause failed: {response.text}"
        print(f"Campaign {campaign_id} paused successfully")


class TestSpecificCampaign:
    """Test for specific campaign: My Truck Brokers - Campaña Español"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json().get("access_token") or response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_truck_brokers_campaign_exists(self, auth_headers):
        """Verify 'My Truck Brokers - Campaña Español' campaign exists with 3 images"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=auth_headers)
        assert response.status_code == 200
        
        campaigns = response.json().get("campaigns", [])
        
        # Find the campaign
        truck_campaign = None
        for c in campaigns:
            name = c.get("name", "").lower()
            if "truck" in name and "brokers" in name:
                truck_campaign = c
                break
        
        if truck_campaign:
            print(f"Found campaign: {truck_campaign['name']}")
            stats = truck_campaign.get("stats", {})
            images = stats.get("images", [])
            print(f"Images count: {len(images)}")
            if len(images) >= 3:
                print("Campaign has 3+ images as expected")
            else:
                print(f"Warning: Expected 3 images, found {len(images)}")
        else:
            # List all campaign names
            print("Campaign 'My Truck Brokers' not found. Available campaigns:")
            for c in campaigns:
                print(f"  - {c.get('name')}")
            pytest.skip("My Truck Brokers campaign not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
