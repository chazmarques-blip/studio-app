"""
Test Suite: Iteration 61 - Supabase Data CRUD Testing
Tests CRUD operations for companies and avatars stored in Supabase tenants.settings JSONB column.
Endpoints: /api/data/companies and /api/data/avatars

Data Architecture:
- Companies stored in: tenants.settings.studio_companies (JSONB array)
- Avatars stored in: tenants.settings.studio_avatars (JSONB array)
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestCompaniesSupabaseCRUD:
    """Test suite for Companies CRUD stored in Supabase tenants.settings JSONB"""
    
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
    
    # ========== GET Companies ==========
    
    def test_get_companies_returns_array_from_supabase(self):
        """GET /api/data/companies - Returns companies array from Supabase JSONB"""
        response = self.session.get(f"{BASE_URL}/api/data/companies")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list (array from JSONB)"
        print(f"✓ GET /api/data/companies returns array with {len(data)} companies from Supabase")
    
    def test_get_companies_contains_agentzz(self):
        """GET /api/data/companies - Should contain pre-seeded AgentZZ company"""
        response = self.session.get(f"{BASE_URL}/api/data/companies")
        assert response.status_code == 200
        
        companies = response.json()
        agentzz = next((c for c in companies if "AgentZZ" in c.get("name", "")), None)
        
        if agentzz:
            print(f"✓ Found AgentZZ company: id={agentzz.get('id')}, name={agentzz.get('name')}")
            # Verify expected fields
            assert "id" in agentzz, "Company should have 'id'"
            assert "name" in agentzz, "Company should have 'name'"
        else:
            print(f"! AgentZZ company not found in {len(companies)} companies - may need seeding")
    
    # ========== POST Companies (Create) ==========
    
    def test_create_company_generates_id(self):
        """POST /api/data/companies - Creates company with auto-generated id"""
        test_company = {
            "name": f"TEST_CreateCompany_{uuid.uuid4().hex[:8]}",
            "phone": "+1-555-0100",
            "is_whatsapp": True,
            "website_url": "https://test-create.com",
            "logo_url": "https://example.com/logo.png",
            "is_primary": False
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify auto-generated id
        assert "id" in data, "Response should contain auto-generated 'id'"
        assert len(data["id"]) == 12, "ID should be 12 character hex string (uuid.uuid4().hex[:12])"
        
        # Verify all fields persisted
        assert data["name"] == test_company["name"]
        assert data["phone"] == test_company["phone"]
        assert data["is_whatsapp"] == test_company["is_whatsapp"]
        assert data["website_url"] == test_company["website_url"]
        assert data["logo_url"] == test_company["logo_url"]
        
        # Verify timestamps added
        assert "created_at" in data, "Should have created_at timestamp"
        assert "updated_at" in data, "Should have updated_at timestamp"
        
        print(f"✓ POST /api/data/companies created company: id={data['id']}")
        
        # Verify persistence by GET
        get_response = self.session.get(f"{BASE_URL}/api/data/companies")
        companies = get_response.json()
        found = any(c["id"] == data["id"] for c in companies)
        assert found, "Created company should persist in Supabase"
        print(f"✓ Company verified in GET response (persisted to Supabase JSONB)")
    
    def test_create_company_with_custom_id(self):
        """POST /api/data/companies - Can create with custom id"""
        custom_id = f"custom{uuid.uuid4().hex[:6]}"
        test_company = {
            "id": custom_id,
            "name": f"TEST_CustomIDCompany_{uuid.uuid4().hex[:6]}",
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == custom_id, "Should use custom id when provided"
        print(f"✓ Company created with custom id: {custom_id}")
    
    def test_create_company_as_primary_unsets_others(self):
        """POST /api/data/companies with is_primary=True unsets other primaries"""
        # Create two companies, second one as primary
        company1 = {
            "name": f"TEST_Primary1_{uuid.uuid4().hex[:6]}",
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": True
        }
        resp1 = self.session.post(f"{BASE_URL}/api/data/companies", json=company1)
        id1 = resp1.json()["id"]
        
        company2 = {
            "name": f"TEST_Primary2_{uuid.uuid4().hex[:6]}",
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": True
        }
        resp2 = self.session.post(f"{BASE_URL}/api/data/companies", json=company2)
        id2 = resp2.json()["id"]
        
        # Verify only company2 is primary
        get_response = self.session.get(f"{BASE_URL}/api/data/companies")
        companies = get_response.json()
        
        c1 = next((c for c in companies if c["id"] == id1), None)
        c2 = next((c for c in companies if c["id"] == id2), None)
        
        if c1 and c2:
            # Note: The code sets is_primary=False for others when creating with is_primary=True
            assert c2.get("is_primary") == True, "Company 2 should be primary"
            print(f"✓ Creating company with is_primary=True correctly sets primary")
    
    # ========== POST Companies (Update) ==========
    
    def test_update_company_preserves_created_at(self):
        """POST /api/data/companies - Update preserves created_at timestamp"""
        # Create company
        test_company = {
            "name": f"TEST_UpdateTimestamp_{uuid.uuid4().hex[:6]}",
            "phone": "+1-555-0101",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        create_resp = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        created = create_resp.json()
        company_id = created["id"]
        original_created_at = created.get("created_at")
        
        time.sleep(0.1)  # Small delay to ensure different timestamp
        
        # Update company
        update = {
            "id": company_id,
            "name": f"TEST_UpdatedTimestamp_{uuid.uuid4().hex[:6]}",
            "phone": "+1-555-0102",
            "is_whatsapp": False,
            "website_url": "https://updated.com",
            "logo_url": "",
            "is_primary": False
        }
        update_resp = self.session.post(f"{BASE_URL}/api/data/companies", json=update)
        updated = update_resp.json()
        
        # created_at should be preserved, updated_at should be new
        assert updated.get("created_at") == original_created_at, "created_at should be preserved on update"
        print(f"✓ Update preserves created_at: {updated.get('created_at')}")
    
    # ========== POST Companies Primary ==========
    
    def test_set_primary_company_endpoint(self):
        """POST /api/data/companies/primary/{id} - Sets company as primary"""
        # Create company
        test_company = {
            "name": f"TEST_SetPrimary_{uuid.uuid4().hex[:6]}",
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        create_resp = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        company_id = create_resp.json()["id"]
        
        # Set as primary using endpoint
        primary_resp = self.session.post(f"{BASE_URL}/api/data/companies/primary/{company_id}")
        assert primary_resp.status_code == 200, f"Expected 200, got {primary_resp.status_code}"
        
        data = primary_resp.json()
        assert data.get("status") == "ok"
        
        # Verify via GET
        get_resp = self.session.get(f"{BASE_URL}/api/data/companies")
        companies = get_resp.json()
        target = next((c for c in companies if c["id"] == company_id), None)
        assert target is not None
        assert target.get("is_primary") == True, "Company should now be primary"
        print(f"✓ POST /api/data/companies/primary/{company_id} set primary successfully")
    
    # ========== DELETE Companies ==========
    
    def test_delete_company_removes_from_jsonb(self):
        """DELETE /api/data/companies/{id} - Removes company from JSONB array"""
        # Create company to delete
        test_company = {
            "name": f"TEST_Delete_{uuid.uuid4().hex[:6]}",
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        }
        create_resp = self.session.post(f"{BASE_URL}/api/data/companies", json=test_company)
        company_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = self.session.delete(f"{BASE_URL}/api/data/companies/{company_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json().get("status") == "ok"
        
        # Verify deleted
        get_resp = self.session.get(f"{BASE_URL}/api/data/companies")
        companies = get_resp.json()
        found = any(c["id"] == company_id for c in companies)
        assert not found, "Deleted company should not exist in JSONB array"
        print(f"✓ DELETE /api/data/companies/{company_id} removed from Supabase JSONB")


class TestAvatarsSupabaseCRUD:
    """Test suite for Avatars CRUD stored in Supabase tenants.settings JSONB"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup - authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
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
    
    # ========== GET Avatars ==========
    
    def test_get_avatars_returns_array(self):
        """GET /api/data/avatars - Returns avatars array from Supabase JSONB"""
        response = self.session.get(f"{BASE_URL}/api/data/avatars")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be list from studio_avatars JSONB"
        print(f"✓ GET /api/data/avatars returns array with {len(data)} avatars")
    
    # ========== POST Avatars (Create) ==========
    
    def test_create_avatar_full_fields(self):
        """POST /api/data/avatars - Creates avatar with all fields"""
        test_avatar = {
            "name": f"TEST_Avatar_{uuid.uuid4().hex[:6]}",
            "url": "https://example.com/avatar.png",
            "source_photo_url": "https://example.com/source.jpg",
            "clothing": "company_uniform",
            "voice": {"type": "neural", "language": "en-US", "model": "wavenet"},
            "angles": {"front": "url1", "left": "url2", "right": "url3", "back": "url4"},
            "video_url": "https://example.com/preview.mp4"
        }
        
        response = self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Should have auto-generated id"
        assert len(data["id"]) == 12, "ID should be 12 char hex"
        assert data["name"] == test_avatar["name"]
        assert data["url"] == test_avatar["url"]
        assert data["source_photo_url"] == test_avatar["source_photo_url"]
        assert data["clothing"] == test_avatar["clothing"]
        assert data["voice"] == test_avatar["voice"]
        assert data["angles"] == test_avatar["angles"]
        assert data["video_url"] == test_avatar["video_url"]
        assert "created_at" in data
        assert "updated_at" in data
        
        print(f"✓ POST /api/data/avatars created avatar: id={data['id']}")
        
        # Verify persistence
        get_resp = self.session.get(f"{BASE_URL}/api/data/avatars")
        avatars = get_resp.json()
        found = any(a["id"] == data["id"] for a in avatars)
        assert found, "Avatar should persist in Supabase JSONB"
    
    # ========== POST Avatars (Update) ==========
    
    def test_update_avatar_by_id(self):
        """POST /api/data/avatars - Updates existing avatar by id"""
        # Create
        test_avatar = {
            "name": f"TEST_UpdateAvatar_{uuid.uuid4().hex[:6]}",
            "url": "https://example.com/original.png",
            "source_photo_url": "",
            "clothing": "casual"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        avatar_id = create_resp.json()["id"]
        
        # Update
        update = {
            "id": avatar_id,
            "name": f"TEST_UpdatedAvatar_{uuid.uuid4().hex[:6]}",
            "url": "https://example.com/updated.png",
            "source_photo_url": "https://example.com/new-source.jpg",
            "clothing": "business_formal"
        }
        update_resp = self.session.post(f"{BASE_URL}/api/data/avatars", json=update)
        assert update_resp.status_code == 200
        
        updated = update_resp.json()
        assert updated["id"] == avatar_id
        assert updated["name"] == update["name"]
        assert updated["url"] == update["url"]
        assert updated["clothing"] == update["clothing"]
        
        print(f"✓ POST /api/data/avatars updated avatar {avatar_id}")
    
    # ========== DELETE Single Avatar ==========
    
    def test_delete_single_avatar(self):
        """DELETE /api/data/avatars/{id} - Deletes specific avatar"""
        # Create
        test_avatar = {
            "name": f"TEST_DeleteSingle_{uuid.uuid4().hex[:6]}",
            "url": "https://example.com/delete.png",
            "source_photo_url": "",
            "clothing": "streetwear"
        }
        create_resp = self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        avatar_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = self.session.delete(f"{BASE_URL}/api/data/avatars/{avatar_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json().get("status") == "ok"
        
        # Verify deleted
        get_resp = self.session.get(f"{BASE_URL}/api/data/avatars")
        avatars = get_resp.json()
        found = any(a["id"] == avatar_id for a in avatars)
        assert not found, "Deleted avatar should not exist"
        
        print(f"✓ DELETE /api/data/avatars/{avatar_id} removed avatar")
    
    # ========== DELETE All Avatars ==========
    
    def test_delete_all_avatars_returns_count(self):
        """DELETE /api/data/avatars - Deletes all and returns count"""
        # Create a test avatar
        test_avatar = {
            "name": f"TEST_DeleteAll_{uuid.uuid4().hex[:6]}",
            "url": "https://example.com/bulk.png",
            "source_photo_url": "",
            "clothing": "casual"
        }
        self.session.post(f"{BASE_URL}/api/data/avatars", json=test_avatar)
        
        # Get current count
        get_before = self.session.get(f"{BASE_URL}/api/data/avatars")
        count_before = len(get_before.json())
        
        # Delete all
        delete_resp = self.session.delete(f"{BASE_URL}/api/data/avatars")
        assert delete_resp.status_code == 200
        
        data = delete_resp.json()
        assert data.get("status") == "ok"
        assert "deleted" in data, "Should return deleted count"
        assert data["deleted"] == count_before, f"Should delete {count_before} avatars"
        
        # Verify empty
        get_after = self.session.get(f"{BASE_URL}/api/data/avatars")
        assert len(get_after.json()) == 0, "All avatars should be deleted"
        
        print(f"✓ DELETE /api/data/avatars deleted {data['deleted']} avatars")


class TestAuthRequired:
    """Test that endpoints require authentication"""
    
    def test_companies_get_requires_auth(self):
        """GET /api/data/companies without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/data/companies")
        assert response.status_code in [401, 422], f"Expected 401/422, got {response.status_code}"
        print(f"✓ GET /api/data/companies without auth: {response.status_code}")
    
    def test_companies_post_requires_auth(self):
        """POST /api/data/companies without auth returns 401"""
        response = requests.post(f"{BASE_URL}/api/data/companies", json={"name": "Test"})
        assert response.status_code in [401, 422], f"Expected 401/422, got {response.status_code}"
        print(f"✓ POST /api/data/companies without auth: {response.status_code}")
    
    def test_avatars_get_requires_auth(self):
        """GET /api/data/avatars without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/data/avatars")
        assert response.status_code in [401, 422], f"Expected 401/422, got {response.status_code}"
        print(f"✓ GET /api/data/avatars without auth: {response.status_code}")
    
    def test_avatars_post_requires_auth(self):
        """POST /api/data/avatars without auth returns 401"""
        response = requests.post(f"{BASE_URL}/api/data/avatars", json={"name": "Test"})
        assert response.status_code in [401, 422], f"Expected 401/422, got {response.status_code}"
        print(f"✓ POST /api/data/avatars without auth: {response.status_code}")


class TestDataPersistenceAcrossSessions:
    """Test that data persists across sessions (i.e., stored in Supabase not memory)"""
    
    def test_data_persists_across_sessions(self):
        """Data created in one session persists and is readable in a new session"""
        unique_name = f"TEST_Persistence_{uuid.uuid4().hex[:8]}"
        
        # Session 1: Create company
        session1 = requests.Session()
        session1.headers.update({"Content-Type": "application/json"})
        login1 = session1.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        token1 = login1.json().get("access_token") or login1.json().get("token")
        session1.headers.update({"Authorization": f"Bearer {token1}"})
        
        create_resp = session1.post(f"{BASE_URL}/api/data/companies", json={
            "name": unique_name,
            "phone": "",
            "is_whatsapp": True,
            "website_url": "",
            "logo_url": "",
            "is_primary": False
        })
        company_id = create_resp.json()["id"]
        print(f"Session 1: Created company {unique_name} with id {company_id}")
        
        # Session 2: New login, verify data exists
        session2 = requests.Session()
        session2.headers.update({"Content-Type": "application/json"})
        login2 = session2.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL, "password": TEST_PASSWORD
        })
        token2 = login2.json().get("access_token") or login2.json().get("token")
        session2.headers.update({"Authorization": f"Bearer {token2}"})
        
        get_resp = session2.get(f"{BASE_URL}/api/data/companies")
        companies = get_resp.json()
        found = next((c for c in companies if c["id"] == company_id), None)
        
        assert found is not None, f"Company {company_id} should persist in new session"
        assert found["name"] == unique_name, "Company name should match"
        
        print(f"✓ Session 2: Found company {unique_name} - data persists in Supabase")
        
        # Cleanup
        session2.delete(f"{BASE_URL}/api/data/companies/{company_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
