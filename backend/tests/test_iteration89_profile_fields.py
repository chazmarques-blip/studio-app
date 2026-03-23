"""
Iteration 89: Extended Profile Fields Testing
Tests for birth_date, phone, preferred_contact fields in:
- POST /api/auth/signup - new fields in signup
- POST /api/auth/login - returns extended profile from tenant settings
- GET /api/auth/me - returns extended profile fields
- PUT /api/auth/profile - updates extended profile fields in tenant settings
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestExtendedProfileFields:
    """Test extended profile fields (birth_date, phone, preferred_contact)"""
    
    @pytest.fixture(scope="class")
    def test_user_credentials(self):
        """Existing test user credentials"""
        return {
            "email": "test@agentflow.com",
            "password": "password123"
        }
    
    @pytest.fixture(scope="class")
    def auth_token(self, test_user_credentials):
        """Get auth token for existing test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=test_user_credentials)
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers for authenticated requests"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # --- Login Tests ---
    def test_login_returns_extended_profile_fields(self, test_user_credentials):
        """Test that login returns birth_date, phone, preferred_contact from tenant settings"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=test_user_credentials)
        assert response.status_code == 200
        data = response.json()
        
        # Verify user object structure
        assert "user" in data
        user = data["user"]
        
        # Extended profile fields should be present (may be empty strings or default values)
        assert "birth_date" in user, "birth_date field missing from login response"
        assert "phone" in user, "phone field missing from login response"
        assert "preferred_contact" in user, "preferred_contact field missing from login response"
        
        # preferred_contact should default to 'whatsapp' if not set
        assert user["preferred_contact"] in ["whatsapp", "sms"], f"Invalid preferred_contact: {user['preferred_contact']}"
        
        print(f"Login response extended fields: birth_date={user['birth_date']}, phone={user['phone']}, preferred_contact={user['preferred_contact']}")
    
    # --- GET /auth/me Tests ---
    def test_auth_me_returns_extended_profile_fields(self, auth_headers):
        """Test that GET /auth/me returns birth_date, phone, preferred_contact"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Extended profile fields should be present
        assert "birth_date" in data, "birth_date field missing from /auth/me response"
        assert "phone" in data, "phone field missing from /auth/me response"
        assert "preferred_contact" in data, "preferred_contact field missing from /auth/me response"
        
        print(f"/auth/me extended fields: birth_date={data['birth_date']}, phone={data['phone']}, preferred_contact={data['preferred_contact']}")
    
    # --- PUT /auth/profile Tests ---
    def test_update_profile_birth_date(self, auth_headers):
        """Test updating birth_date via PUT /auth/profile"""
        test_birth_date = "1990-05-15"
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"birth_date": test_birth_date}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "birth_date" in data.get("updated", {})
        
        # Verify persistence via GET /auth/me
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["birth_date"] == test_birth_date, f"birth_date not persisted: expected {test_birth_date}, got {me_data['birth_date']}"
        
        print(f"birth_date updated and verified: {test_birth_date}")
    
    def test_update_profile_phone(self, auth_headers):
        """Test updating phone via PUT /auth/profile"""
        test_phone = "+5511999999999"
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"phone": test_phone}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "phone" in data.get("updated", {})
        
        # Verify persistence via GET /auth/me
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["phone"] == test_phone, f"phone not persisted: expected {test_phone}, got {me_data['phone']}"
        
        print(f"phone updated and verified: {test_phone}")
    
    def test_update_profile_preferred_contact_whatsapp(self, auth_headers):
        """Test updating preferred_contact to whatsapp"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"preferred_contact": "whatsapp"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify persistence
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        assert me_response.json()["preferred_contact"] == "whatsapp"
        
        print("preferred_contact updated to whatsapp and verified")
    
    def test_update_profile_preferred_contact_sms(self, auth_headers):
        """Test updating preferred_contact to sms"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json={"preferred_contact": "sms"}
        )
        assert response.status_code == 200
        
        # Verify persistence
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        assert me_response.json()["preferred_contact"] == "sms"
        
        print("preferred_contact updated to sms and verified")
        
        # Reset to whatsapp for consistency
        requests.put(f"{BASE_URL}/api/auth/profile", headers=auth_headers, json={"preferred_contact": "whatsapp"})
    
    def test_update_all_extended_fields_at_once(self, auth_headers):
        """Test updating all extended profile fields in a single request"""
        update_data = {
            "birth_date": "1990-05-15",
            "phone": "+5511999999999",
            "preferred_contact": "whatsapp"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify all fields persisted
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        assert me_data["birth_date"] == update_data["birth_date"]
        assert me_data["phone"] == update_data["phone"]
        assert me_data["preferred_contact"] == update_data["preferred_contact"]
        
        print(f"All extended fields updated and verified: {update_data}")
    
    def test_update_mixed_standard_and_extended_fields(self, auth_headers):
        """Test updating both standard user fields and extended profile fields"""
        update_data = {
            "full_name": "Test User Updated",
            "birth_date": "1990-05-15",
            "phone": "+5511999999999"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        
        # Verify via GET /auth/me
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        assert me_data["full_name"] == update_data["full_name"]
        assert me_data["birth_date"] == update_data["birth_date"]
        assert me_data["phone"] == update_data["phone"]
        
        print("Mixed standard and extended fields updated successfully")


class TestSignupWithExtendedFields:
    """Test signup with extended profile fields"""
    
    def test_signup_with_all_extended_fields(self):
        """Test signup with birth_date, phone, preferred_contact"""
        unique_email = f"test_signup_{uuid.uuid4().hex[:8]}@test.com"
        
        signup_data = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test Signup User",
            "birth_date": "1995-08-20",
            "phone": "+5521988887777",
            "preferred_contact": "sms"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        
        # Verify response contains extended fields
        assert "user" in data
        user = data["user"]
        assert user["birth_date"] == signup_data["birth_date"], f"birth_date mismatch: {user['birth_date']}"
        assert user["phone"] == signup_data["phone"], f"phone mismatch: {user['phone']}"
        assert user["preferred_contact"] == signup_data["preferred_contact"], f"preferred_contact mismatch: {user['preferred_contact']}"
        
        # Verify token is returned
        assert "access_token" in data
        
        # Verify data persisted via GET /auth/me
        auth_headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        assert me_data["birth_date"] == signup_data["birth_date"]
        assert me_data["phone"] == signup_data["phone"]
        assert me_data["preferred_contact"] == signup_data["preferred_contact"]
        
        print(f"Signup with extended fields successful for {unique_email}")
    
    def test_signup_with_default_preferred_contact(self):
        """Test signup without preferred_contact defaults to whatsapp"""
        unique_email = f"test_signup_default_{uuid.uuid4().hex[:8]}@test.com"
        
        signup_data = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test Default Contact"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        
        # preferred_contact should default to whatsapp
        user = data["user"]
        assert user["preferred_contact"] == "whatsapp", f"Default preferred_contact should be whatsapp, got: {user['preferred_contact']}"
        
        print(f"Signup with default preferred_contact verified for {unique_email}")
    
    def test_signup_with_partial_extended_fields(self):
        """Test signup with only some extended fields"""
        unique_email = f"test_signup_partial_{uuid.uuid4().hex[:8]}@test.com"
        
        signup_data = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test Partial Fields",
            "phone": "+5511912345678"
            # birth_date and preferred_contact not provided
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        
        user = data["user"]
        assert user["phone"] == signup_data["phone"]
        assert user["birth_date"] == ""  # Should be empty string
        assert user["preferred_contact"] == "whatsapp"  # Default
        
        print(f"Signup with partial extended fields verified for {unique_email}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
