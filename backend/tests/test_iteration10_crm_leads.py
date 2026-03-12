"""
Iteration 10: CRM Kanban with AI Lead Scoring Tests
Tests for:
- GET /api/leads - list leads
- POST /api/leads - create lead
- GET /api/leads/{id} - get single lead
- PUT /api/leads/{id} - update lead stage
- DELETE /api/leads/{id} - delete lead
- POST /api/leads/{id}/ai-score - AI analysis
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCRMLeadsAPI:
    """CRM Leads API tests for iteration 10"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        return response.json().get("access_token")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    # Test 1: Health Check
    def test_health_check(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Health check passed - version: {data.get('version')}")
    
    # Test 2: Authentication
    def test_login_returns_token(self):
        """Test login endpoint returns access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✓ Login successful, token received")
    
    # Test 3: GET /api/leads - List leads
    def test_list_leads(self, auth_headers):
        """Test GET /api/leads returns leads list"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert isinstance(data["leads"], list)
        print(f"✓ List leads returned {len(data['leads'])} leads")
    
    # Test 4: POST /api/leads - Create lead
    def test_create_lead(self, auth_headers):
        """Test POST /api/leads creates new lead"""
        lead_data = {
            "name": "TEST_John Doe",
            "phone": "+1234567890",
            "email": "testjohn@test.com",
            "company": "Test Corp",
            "value": 5000.00,
            "stage": "new"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data.get("name") == "TEST_John Doe"
        assert data.get("phone") == "+1234567890"
        assert data.get("email") == "testjohn@test.com"
        assert data.get("company") == "Test Corp"
        assert float(data.get("value", 0)) == 5000.0
        assert data.get("stage") == "new"
        print(f"✓ Lead created with ID: {data['id']}")
        return data
    
    # Test 5: GET /api/leads/{id} - Get single lead
    def test_get_lead_by_id(self, auth_headers):
        """Test GET /api/leads/{id} returns single lead"""
        # First create a lead
        lead_data = {
            "name": "TEST_Get Lead",
            "phone": "+1111111111",
            "email": "getlead@test.com",
            "company": "Get Corp",
            "value": 1000.00,
            "stage": "new"
        }
        create_resp = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        created_lead = create_resp.json()
        lead_id = created_lead["id"]
        
        # Now get the lead
        response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["name"] == "TEST_Get Lead"
        print(f"✓ Get lead by ID returned: {data['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
    
    # Test 6: PUT /api/leads/{id} - Update lead stage
    def test_update_lead_stage(self, auth_headers):
        """Test PUT /api/leads/{id} updates lead stage"""
        # Create a lead
        lead_data = {
            "name": "TEST_Update Stage Lead",
            "phone": "+2222222222",
            "email": "updatestage@test.com",
            "company": "Update Corp",
            "value": 2000.00,
            "stage": "new"
        }
        create_resp = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        created_lead = create_resp.json()
        lead_id = created_lead["id"]
        assert created_lead["stage"] == "new"
        
        # Update stage to qualified
        update_data = {"stage": "qualified"}
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "qualified"
        print(f"✓ Lead stage updated from 'new' to 'qualified'")
        
        # Verify persistence with GET
        get_resp = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["stage"] == "qualified"
        print("✓ Stage change persisted (verified via GET)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
    
    # Test 7: PUT - Update multiple fields
    def test_update_lead_multiple_fields(self, auth_headers):
        """Test PUT /api/leads/{id} updates multiple fields"""
        # Create a lead
        lead_data = {
            "name": "TEST_Multi Update Lead",
            "phone": "+3333333333",
            "email": "multi@test.com",
            "company": "Multi Corp",
            "value": 3000.00,
            "stage": "new"
        }
        create_resp = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Update multiple fields
        update_data = {
            "stage": "proposal",
            "value": 5000.0,
            "company": "Updated Corp"
        }
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "proposal"
        assert float(data.get("value", 0)) == 5000.0
        assert data["company"] == "Updated Corp"
        print("✓ Lead updated with multiple fields")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
    
    # Test 8: DELETE /api/leads/{id} - Delete lead
    def test_delete_lead(self, auth_headers):
        """Test DELETE /api/leads/{id} removes lead"""
        # Create a lead
        lead_data = {
            "name": "TEST_Delete Lead",
            "phone": "+4444444444",
            "email": "delete@test.com",
            "company": "Delete Corp",
            "value": 1000.00,
            "stage": "new"
        }
        create_resp = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Delete the lead
        response = requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print(f"✓ Lead {lead_id} deleted successfully")
        
        # Verify deletion with GET (should return 404)
        get_resp = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 404
        print("✓ Deleted lead not found (verified via GET 404)")
    
    # Test 9: POST /api/leads/{id}/ai-score - AI scoring
    def test_ai_score_lead(self, auth_headers):
        """Test POST /api/leads/{id}/ai-score returns AI analysis"""
        # Create a lead
        lead_data = {
            "name": "TEST_AI Score Lead",
            "phone": "+5555555555",
            "email": "aiscore@test.com",
            "company": "AI Corp",
            "value": 10000.00,
            "stage": "qualified"
        }
        create_resp = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Run AI scoring
        response = requests.post(f"{BASE_URL}/api/leads/{lead_id}/ai-score", headers=auth_headers, timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        # Validate AI response structure
        assert "score" in data, "AI response missing 'score'"
        assert "reason" in data, "AI response missing 'reason'"
        assert isinstance(data["score"], int)
        assert 0 <= data["score"] <= 100
        print(f"✓ AI Score: {data['score']}/100")
        print(f"✓ AI Reason: {data.get('reason', 'N/A')}")
        
        # Verify score is persisted
        get_resp = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        persisted_lead = get_resp.json()
        assert persisted_lead["score"] == data["score"]
        print("✓ AI score persisted to lead record")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)
    
    # Test 10: GET /api/leads with stage filter
    def test_list_leads_with_stage_filter(self, auth_headers):
        """Test GET /api/leads?stage=new filters by stage"""
        response = requests.get(f"{BASE_URL}/api/leads?stage=new", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        # Verify all returned leads have stage 'new'
        for lead in data["leads"]:
            assert lead.get("stage") == "new"
        print(f"✓ Filter by stage 'new' returned {len(data['leads'])} leads")
    
    # Test 11: GET /api/leads/{id} for non-existent lead
    def test_get_nonexistent_lead(self, auth_headers):
        """Test GET /api/leads/{id} returns 404 for non-existent lead"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(f"{BASE_URL}/api/leads/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Non-existent lead returns 404")
    
    # Test 12: Stage transitions (won/lost)
    def test_stage_transitions(self, auth_headers):
        """Test lead stage transitions to won and lost"""
        # Create a lead
        lead_data = {
            "name": "TEST_Stage Transition Lead",
            "phone": "+6666666666",
            "email": "transition@test.com",
            "company": "Transition Corp",
            "value": 8000.00,
            "stage": "proposal"
        }
        create_resp = requests.post(f"{BASE_URL}/api/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Update to won
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", json={"stage": "won"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["stage"] == "won"
        print("✓ Lead moved to 'won' stage")
        
        # Update to lost
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", json={"stage": "lost"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["stage"] == "lost"
        print("✓ Lead moved to 'lost' stage")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_headers)


class TestLeadsCleanup:
    """Cleanup test data after tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        token = response.json().get("access_token")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def test_cleanup_test_leads(self, auth_headers):
        """Clean up all TEST_ prefixed leads"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=auth_headers)
        if response.status_code == 200:
            leads = response.json().get("leads", [])
            deleted = 0
            for lead in leads:
                if lead.get("name", "").startswith("TEST_"):
                    del_resp = requests.delete(f"{BASE_URL}/api/leads/{lead['id']}", headers=auth_headers)
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"✓ Cleaned up {deleted} test leads")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
