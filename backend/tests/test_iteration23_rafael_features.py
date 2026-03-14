"""
Test iteration 23 - Rafael Art Director features and revision loop
Features tested:
1. Login authentication
2. Pipeline labels endpoint (Rafael as 'Diretor de Arte')
3. Pipeline saved history endpoint (logos and briefings)
4. STEP_ORDER includes rafael_review_design (not ana_review_design)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def authenticated_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"Login successful - got access token")


class TestPipelineLabels:
    """Test pipeline labels endpoint for Rafael agent"""
    
    def test_get_labels_unauthenticated(self):
        """Test that labels endpoint requires authentication"""
        # Need a valid pipeline_id - we'll use a dummy one to test the pattern
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/test/labels")
        # Either 401/403 for auth or 404 for not found is acceptable
        assert response.status_code in [401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_labels_endpoint_rafael(self, authenticated_client):
        """Test that labels endpoint shows Rafael as Diretor de Arte"""
        # First get a pipeline list to find a valid ID
        list_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/list")
        assert list_response.status_code == 200, f"Pipeline list failed: {list_response.text}"
        pipelines = list_response.json().get("pipelines", [])
        
        if pipelines:
            pipeline_id = pipelines[0]["id"]
            response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/labels")
            assert response.status_code == 200, f"Labels endpoint failed: {response.text}"
            data = response.json()
            
            labels = data.get("labels", {})
            order = data.get("order", [])
            
            # Verify STEP_ORDER contains rafael_review_design, not ana_review_design
            assert "rafael_review_design" in order, f"rafael_review_design not in order: {order}"
            assert "ana_review_design" not in order, f"ana_review_design should NOT be in order: {order}"
            
            # Verify full order: Sofia -> Ana -> Lucas -> Rafael -> Pedro
            expected_order = ["sofia_copy", "ana_review_copy", "lucas_design", "rafael_review_design", "pedro_publish"]
            assert order == expected_order, f"STEP_ORDER mismatch: {order} != {expected_order}"
            
            # Verify Rafael label
            rafael_label = labels.get("rafael_review_design", {})
            assert rafael_label.get("agent") == "Rafael", f"Rafael agent name wrong: {rafael_label}"
            assert rafael_label.get("role") == "Diretor de Arte", f"Rafael role wrong: {rafael_label}"
            assert rafael_label.get("icon") == "award", f"Rafael icon wrong: {rafael_label}"
            
            # Verify Ana is copy reviewer, not design reviewer
            ana_label = labels.get("ana_review_copy", {})
            assert ana_label.get("agent") == "Ana", f"Ana agent name wrong: {ana_label}"
            assert ana_label.get("role") == "Revisora de Copy", f"Ana role should be Revisora de Copy: {ana_label}"
            
            print(f"Labels verified - Rafael is Diretor de Arte with 'award' icon")
            print(f"STEP_ORDER: {order}")
        else:
            pytest.skip("No pipelines found to test labels endpoint")


class TestSavedHistory:
    """Test saved logos and briefings endpoint"""
    
    def test_saved_history_endpoint(self, authenticated_client):
        """Test that saved/history returns logos and briefings"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/saved/history")
        assert response.status_code == 200, f"Saved history failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "logos" in data, "No 'logos' key in response"
        assert "briefings" in data, "No 'briefings' key in response"
        
        logos = data.get("logos", [])
        briefings = data.get("briefings", [])
        
        print(f"Saved history - logos: {len(logos)}, briefings: {len(briefings)}")
        
        # Verify logo structure if any exist
        if logos:
            logo = logos[0]
            assert "url" in logo, f"Logo missing 'url': {logo}"
            assert "filename" in logo, f"Logo missing 'filename': {logo}"
            print(f"First logo: {logo}")
        
        # Verify briefing structure if any exist
        if briefings:
            brief = briefings[0]
            assert "briefing" in brief, f"Briefing missing 'briefing' field: {brief}"
            print(f"First briefing: {brief.get('briefing', '')[:100]}...")


class TestPipelineList:
    """Test pipeline list endpoint"""
    
    def test_list_pipelines(self, authenticated_client):
        """Test pipeline list returns valid data"""
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/list")
        assert response.status_code == 200, f"Pipeline list failed: {response.text}"
        data = response.json()
        assert "pipelines" in data, "No 'pipelines' key in response"
        
        pipelines = data.get("pipelines", [])
        print(f"Found {len(pipelines)} pipelines")
        
        # If pipelines exist, verify structure
        if pipelines:
            p = pipelines[0]
            assert "id" in p, "Pipeline missing 'id'"
            assert "status" in p, "Pipeline missing 'status'"
            assert "briefing" in p, "Pipeline missing 'briefing'"
            print(f"First pipeline: id={p['id']}, status={p['status']}")


class TestStepOrderInCode:
    """Verify STEP_ORDER in backend code"""
    
    def test_step_order_matches_expectation(self, authenticated_client):
        """Verify the pipeline steps order through labels endpoint"""
        # Get pipelines first
        list_response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/list")
        if list_response.status_code != 200:
            pytest.skip("Cannot get pipeline list")
        
        pipelines = list_response.json().get("pipelines", [])
        if not pipelines:
            pytest.skip("No pipelines found")
        
        # Get labels from first pipeline
        pipeline_id = pipelines[0]["id"]
        response = authenticated_client.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/labels")
        assert response.status_code == 200
        
        order = response.json().get("order", [])
        
        # Pipeline should be: Sofia → Ana (copy) → Lucas → Rafael (design) → Pedro
        assert order[0] == "sofia_copy", f"Step 1 should be sofia_copy: {order}"
        assert order[1] == "ana_review_copy", f"Step 2 should be ana_review_copy: {order}"
        assert order[2] == "lucas_design", f"Step 3 should be lucas_design: {order}"
        assert order[3] == "rafael_review_design", f"Step 4 should be rafael_review_design: {order}"
        assert order[4] == "pedro_publish", f"Step 5 should be pedro_publish: {order}"
        
        print(f"STEP_ORDER verified: {' → '.join(order)}")
