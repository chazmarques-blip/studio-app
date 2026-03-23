"""
Iteration 90: UI Improvements Testing
- Date format dd/mm/yyyy (text input with mask, not native date picker)
- Phone number with country code selector and proper mask per country
- All labels in English
- Backend API: birth_date, phone, preferred_contact storage and retrieval
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthEndpoints:
    """Test auth endpoints for extended profile fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_email = "test@agentflow.com"
        self.test_password = "password123"
    
    def get_auth_token(self):
        """Get authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def test_login_returns_extended_fields(self):
        """Test that login returns birth_date, phone, preferred_contact"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify user object has extended fields
        assert "user" in data
        user = data["user"]
        assert "birth_date" in user, "birth_date field missing from login response"
        assert "phone" in user, "phone field missing from login response"
        assert "preferred_contact" in user, "preferred_contact field missing from login response"
        print(f"Login response extended fields: birth_date={user['birth_date']}, phone={user['phone']}, preferred_contact={user['preferred_contact']}")
    
    def test_auth_me_returns_extended_fields(self):
        """Test that GET /api/auth/me returns birth_date, phone, preferred_contact"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"GET /auth/me failed: {response.text}"
        data = response.json()
        
        # Verify extended fields
        assert "birth_date" in data, "birth_date field missing from /auth/me response"
        assert "phone" in data, "phone field missing from /auth/me response"
        assert "preferred_contact" in data, "preferred_contact field missing from /auth/me response"
        print(f"/auth/me extended fields: birth_date={data['birth_date']}, phone={data['phone']}, preferred_contact={data['preferred_contact']}")
    
    def test_profile_update_with_iso_date(self):
        """Test PUT /api/auth/profile with ISO date format (yyyy-mm-dd)"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        # Update profile with ISO date format
        update_data = {
            "birth_date": "1990-05-15",  # ISO format
            "phone": "+1 (727) 459-2334",  # US format with country code
            "preferred_contact": "whatsapp"
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        print(f"Profile update response: {data}")
        
        # Verify the update persisted
        response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        assert me_data.get("birth_date") == "1990-05-15", f"birth_date not persisted: {me_data.get('birth_date')}"
        assert me_data.get("phone") == "+1 (727) 459-2334", f"phone not persisted: {me_data.get('phone')}"
        assert me_data.get("preferred_contact") == "whatsapp", f"preferred_contact not persisted: {me_data.get('preferred_contact')}"
    
    def test_profile_update_with_br_phone(self):
        """Test profile update with Brazilian phone format"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        update_data = {
            "phone": "+55 (11) 99999-9999",  # BR format
            "preferred_contact": "sms"
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        
        # Verify
        response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        assert me_data.get("phone") == "+55 (11) 99999-9999"
        assert me_data.get("preferred_contact") == "sms"
        print(f"BR phone update verified: {me_data.get('phone')}")
    
    def test_profile_update_with_gb_phone(self):
        """Test profile update with UK phone format"""
        token = self.get_auth_token()
        assert token, "Failed to get auth token"
        
        update_data = {
            "phone": "+44 7911 123456",  # GB format
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        
        # Verify
        response = self.session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        assert me_data.get("phone") == "+44 7911 123456"
        print(f"GB phone update verified: {me_data.get('phone')}")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
