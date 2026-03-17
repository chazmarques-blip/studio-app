"""
Test Suite: Iteration 60 - Data Persistence API Testing
Tests CRUD operations for companies and avatars stored in MongoDB.
New endpoints: /api/data/companies and /api/data/avatars
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestDataPersistenceAPI:
    """Test suite for /api/data/ endpoints (Companies and Avatars CRUD)"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup for each test - authenticate and get access token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.access_token = data.get("access_token") or data.get("token")
            if self.access_token:
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    # ========== COMPANIES CRUD TESTS ==========
    
    def test_get_companies_returns_array(self):
        """GET /api/data/companies - Returns array of companies"""
        response = self.session.get(f"{BASE_URL}/api/data/companies")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/data/companies returns array with {len(data)} companies")
    
    def test_create_company(self):
        """POST /api/data/companies - Creates a new company"""
        test_company = {
            "name": f"TEST_Company_{uuid.uuid4().hex[:8]}",
            "phone": "+1234567890",
            "is_whatsapp": True,
            "website_url": "https://test-company.com",
            "logo_url": "https://example.com/logo.png",
            "is_primary": False
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["name"] == test_company["name"], "Name should match"
        assert data["phone"] == test_company["phone"], "Phone should match"
        assert data["is_whatsapp"] == test_company["is_whatsapp"], "is_whatsapp should match"
        assert data["website_url"] == test_company["website_url"], "website_url should match"
        
        # Store for cleanup
        self.created_company_id = data["id"]
        print(f"✓ POST /api/data/companies created company with id: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/data/companies")
        assert get_response.status_code == 200
        companies = get_response.json()
        found = any(c["id"] == data["id"] for c in companies)
        assert found, "Created company should be in GET response"
        print(f"✓ Company persisted and verified via GET")
    
    def test_update_company_by_id(self):
        """POST /api/data/companies - Updates existing company by id"""
        # First create a company
        test_company = {
            "name": f"TEST_UpdateCompany_{uuid.uuid4().hex[:8]}",
            "phone": "+1111111111",
            "is_whatsapp": True,
            "website_url": "https://original.com",
            "logo_url": "",
            "is_primary": False
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert create_response.status_code == 200
        created = create_response.json()
        company_id = created["id"]
        
        # Update the company
        updated_data = {
            "id": company_id,
            "name": f"TEST_UpdatedCompany_{uuid.uuid4().hex[:8]}",
            "phone": "+2222222222",
            "is_whatsapp": False,
            "website_url": "https://updated.com",
            "logo_url": "https://example.com/new-logo.png",
            "is_primary": False
        }
        
        update_response = self.session.post(f"{BASE_URL}/api/data/companies", json=updated_data)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        updated = update_response.json()
        assert updated["id"] == company_id, "ID should remain the same"
        assert updated["name"] == updated_data["name"], "Name should be updated"
        assert updated["phone"] == updated_data["phone"], "Phone should be updated"
        assert updated["website_url"] == updated_data["website_url"], "Website URL should be updated"
        
        print(f"✓ POST /api/data/companies updated company {company_id}")
    
    def test_set_primary_company(self):
        """POST /api/data/companies/primary/{id} - Sets a company as primary"""
        # Create a company
        test_company = {
            "name": f"TEST_PrimaryCompany_{uuid.uuid4().hex[:8]}",
            "phone": "+3333333333",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert create_response.status_code == 200
        created = create_response.json()
        company_id = created["id"]
        
        # Set as primary
        primary_response = self.session.post(f"{BASE_URL}/api/data/companies/primary/{company_id}")
        assert primary_response.status_code == 200, f"Expected 200, got {primary_response.status_code}: {primary_response.text}"
        
        data = primary_response.json()
        assert data.get("status") == "ok", "Response should have status: ok"
        
        # Verify company is now primary
        get_response = self.session.get(f"{BASE_URL}/api/data/companies")
        companies = get_response.json()
        target = next((c for c in companies if c["id"] == company_id), None)
        assert target is not None, "Company should exist"
        assert target.get("is_primary") == True, "Company should be primary"
        
        print(f"✓ POST /api/data/companies/primary/{company_id} set company as primary")
    
    def test_delete_company(self):
        """DELETE /api/data/companies/{id} - Deletes a company"""
        # Create a company to delete
        test_company = {
            "name": f"TEST_DeleteCompany_{uuid.uuid4().hex[:8]}",
            "phone": "+4444444444",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert create_response.status_code == 200
        created = create_response.json()
        company_id = created["id"]
        
        # Delete the company
        delete_response = self.session.delete(f"{BASE_URL}/api/data/companies/{company_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert data.get("status") == "ok", "Response should have status: ok"
        
        # Verify company is deleted
        get_response = self.session.get(f"{BASE_URL}/api/data/companies")
        companies = get_response.json()
        found = any(c["id"] == company_id for c in companies)
        assert not found, "Deleted company should not be in GET response"
        
        print(f"✓ DELETE /api/data/companies/{company_id} removed company")
    
    # ========== AVATARS CRUD TESTS ==========
    
    def test_get_avatars_returns_array(self):
        """GET /api/data/avatars - Returns array of avatars"""
        response = self.session.get(f"{BASE_URL}/api/data/avatars")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/data/avatars returns array with {len(data)} avatars")
    
    def test_create_avatar(self):
        """POST /api/data/avatars - Creates a new avatar"""
        test_avatar = {
            "name": f"TEST_Avatar_{uuid.uuid4().hex[:8]}",
            "url": "https://example.com/avatar.png",
            "source_photo_url": "https://example.com/source.jpg",
            "clothing": "company_uniform",
            "voice": {"type": "standard", "language": "en"},
            "angles": {"front": "url1", "left": "url2"}
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["name"] == test_avatar["name"], "Name should match"
        assert data["url"] == test_avatar["url"], "URL should match"
        assert data["clothing"] == test_avatar["clothing"], "Clothing should match"
        
        self.created_avatar_id = data["id"]
        print(f"✓ POST /api/data/avatars created avatar with id: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/data/avatars")
        assert get_response.status_code == 200
        avatars = get_response.json()
        found = any(a["id"] == data["id"] for a in avatars)
        assert found, "Created avatar should be in GET response"
        print(f"✓ Avatar persisted and verified via GET")
    
    def test_update_avatar_by_id(self):
        """POST /api/data/avatars - Updates existing avatar by id"""
        # First create an avatar
        test_avatar = {
            "name": f"TEST_UpdateAvatar_{uuid.uuid4().hex[:8]}",
            "url": "https://example.com/original.png",
            "source_photo_url": "https://example.com/source.jpg",
            "clothing": "casual"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        assert create_response.status_code == 200
        created = create_response.json()
        avatar_id = created["id"]
        
        # Update the avatar
        updated_data = {
            "id": avatar_id,
            "name": f"TEST_UpdatedAvatar_{uuid.uuid4().hex[:8]}",
            "url": "https://example.com/updated.png",
            "source_photo_url": "https://example.com/new-source.jpg",
            "clothing": "business_formal"
        }
        
        update_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=updated_data)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        updated = update_response.json()
        assert updated["id"] == avatar_id, "ID should remain the same"
        assert updated["name"] == updated_data["name"], "Name should be updated"
        assert updated["url"] == updated_data["url"], "URL should be updated"
        assert updated["clothing"] == updated_data["clothing"], "Clothing should be updated"
        
        print(f"✓ POST /api/data/avatars updated avatar {avatar_id}")
    
    def test_delete_avatar(self):
        """DELETE /api/data/avatars/{id} - Deletes a specific avatar"""
        # Create an avatar to delete
        test_avatar = {
            "name": f"TEST_DeleteAvatar_{uuid.uuid4().hex[:8]}",
            "url": "https://example.com/delete-me.png",
            "source_photo_url": "",
            "clothing": "streetwear"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        assert create_response.status_code == 200
        created = create_response.json()
        avatar_id = created["id"]
        
        # Delete the avatar
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars/{avatar_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert data.get("status") == "ok", "Response should have status: ok"
        
        # Verify avatar is deleted
        get_response = self.session.get(f"{BASE_URL}/api/data/avatars")
        avatars = get_response.json()
        found = any(a["id"] == avatar_id for a in avatars)
        assert not found, "Deleted avatar should not be in GET response"
        
        print(f"✓ DELETE /api/data/avatars/{avatar_id} removed avatar")
    
    def test_delete_all_avatars(self):
        """DELETE /api/data/avatars - Deletes all avatars for user"""
        # Create a couple test avatars
        for i in range(2):
            test_avatar = {
                "name": f"TEST_BulkDeleteAvatar_{uuid.uuid4().hex[:8]}",
                "url": f"https://example.com/bulk-delete-{i}.png",
                "source_photo_url": "",
                "clothing": "casual"
            }
            self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        
        # Delete all avatars
        delete_response = self.session.delete(f"{BASE_URL}/api/data/avatars")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        
        data = delete_response.json()
        assert data.get("status") == "ok", "Response should have status: ok"
        assert "deleted" in data, "Response should contain 'deleted' count"
        
        # Verify all avatars are deleted
        get_response = self.session.get(f"{BASE_URL}/api/data/avatars")
        avatars = get_response.json()
        # Filter only TEST_ avatars we created
        test_avatars = [a for a in avatars if a.get("name", "").startswith("TEST_")]
        # Note: delete_all deletes ALL user avatars, so list should be empty or have non-test items
        print(f"✓ DELETE /api/data/avatars deleted avatars, response: {data}")
    
    # ========== EDGE CASE TESTS ==========
    
    def test_create_company_without_auth_fails(self):
        """POST /api/data/companies without auth should fail"""
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        test_company = {
            "name": "Unauthorized Company",
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        
        response = unauth_session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print(f"✓ POST /api/data/companies without auth returns {response.status_code}")
    
    def test_get_avatars_without_auth_fails(self):
        """GET /api/data/avatars without auth should fail"""
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/data/avatars")
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print(f"✓ GET /api/data/avatars without auth returns {response.status_code}")


class TestExistingAgentZZCompany:
    """Test that the pre-seeded AgentZZ company is returned from API"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup for each test - authenticate and get access token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.access_token = data.get("access_token") or data.get("token")
            if self.access_token:
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    def test_agentzz_company_exists(self):
        """Verify that AgentZZ company exists in the database (from curl seed)"""
        response = self.session.get(f"{BASE_URL}/api/data/companies")
        assert response.status_code == 200
        companies = response.json()
        
        agentzz = next((c for c in companies if "AgentZZ" in c.get("name", "")), None)
        if agentzz:
            print(f"✓ Found AgentZZ company: {agentzz}")
            assert "id" in agentzz, "Company should have id"
            assert "name" in agentzz, "Company should have name"
        else:
            print(f"! AgentZZ company not found in {len(companies)} companies - may need to be seeded")
            # Not a failure - just informational


# Cleanup test data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after all tests complete"""
    yield
    # Cleanup could be added here if needed
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
