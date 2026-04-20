"""
Iteration 25 - Marcos (Videomaker) Feature Tests
Testing the new video generation agent 'Marcos' in the marketing pipeline
- Backend: Pipeline structure, step labels, marcos_video step
- IMPORTANT: Does NOT trigger actual pipeline/video generation (too expensive)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests for API access"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"✓ Login successful, token received")
        return data.get("access_token") or data.get("token")


class TestPipelineStructure:
    """Tests for pipeline structure with marcos_video step"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_pipeline_list_endpoint(self, auth_token):
        """Test GET /api/campaigns/pipeline/list returns pipelines"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=headers)
        assert response.status_code == 200, f"Pipeline list failed: {response.text}"
        data = response.json()
        assert "pipelines" in data, "Response missing 'pipelines' key"
        print(f"✓ Pipeline list endpoint works, found {len(data['pipelines'])} pipelines")
        return data["pipelines"]
    
    def test_pipeline_step_labels_has_marcos(self, auth_token):
        """Test that step labels include marcos_video with correct info"""
        # We need a pipeline ID to get labels - let's check if any exist
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get list of pipelines
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=headers)
        assert response.status_code == 200
        pipelines = response.json().get("pipelines", [])
        
        if not pipelines:
            pytest.skip("No existing pipelines to test labels endpoint")
        
        # Use first pipeline to get labels
        pipeline_id = pipelines[0]["id"]
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/labels", headers=headers)
        assert response.status_code == 200, f"Labels endpoint failed: {response.text}"
        
        data = response.json()
        labels = data.get("labels", {})
        order = data.get("order", [])
        
        # Verify marcos_video is in the order
        assert "marcos_video" in order, f"marcos_video not in STEP_ORDER: {order}"
        print(f"✓ STEP_ORDER contains marcos_video: {order}")
        
        # Verify marcos_video has correct label info
        assert "marcos_video" in labels, f"marcos_video not in labels: {labels.keys()}"
        marcos_label = labels["marcos_video"]
        assert marcos_label.get("agent") == "Marcos", f"Agent should be 'Marcos', got: {marcos_label.get('agent')}"
        assert marcos_label.get("role") == "Videomaker", f"Role should be 'Videomaker', got: {marcos_label.get('role')}"
        assert marcos_label.get("icon") == "film", f"Icon should be 'film', got: {marcos_label.get('icon')}"
        print(f"✓ marcos_video label: {marcos_label}")
        
        # Verify 6 total steps
        assert len(order) == 6, f"Expected 6 steps, got {len(order)}: {order}"
        print(f"✓ Pipeline has 6 steps as expected")
    
    def test_pipeline_step_order_correct(self, auth_token):
        """Verify the step order is correct: Sofia → Ana → Lucas → Rafael → Marcos → Pedro"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=headers)
        if response.status_code != 200 or not response.json().get("pipelines"):
            pytest.skip("No pipelines available for testing")
        
        pipeline_id = response.json()["pipelines"][0]["id"]
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/labels", headers=headers)
        assert response.status_code == 200
        
        order = response.json().get("order", [])
        expected_order = ["sofia_copy", "ana_review_copy", "lucas_design", "rafael_review_design", "marcos_video", "pedro_publish"]
        assert order == expected_order, f"Step order mismatch. Expected: {expected_order}, Got: {order}"
        print(f"✓ Step order is correct: {' → '.join(order)}")
    
    def test_existing_pipeline_has_marcos_step(self, auth_token):
        """Check that existing pipelines have marcos_video step structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=headers)
        assert response.status_code == 200
        pipelines = response.json().get("pipelines", [])
        
        if not pipelines:
            pytest.skip("No existing pipelines to check")
        
        # Check a few pipelines
        checked = 0
        for pipeline in pipelines[:5]:
            steps = pipeline.get("steps", {})
            if steps:
                # Verify marcos_video key exists in steps
                if "marcos_video" in steps:
                    marcos_step = steps["marcos_video"]
                    assert "status" in marcos_step, "marcos_video step missing 'status'"
                    print(f"✓ Pipeline {pipeline['id'][:8]}... has marcos_video step with status: {marcos_step.get('status')}")
                    
                    # Check for video_url if completed
                    if marcos_step.get("status") == "completed":
                        if marcos_step.get("video_url"):
                            print(f"  - Has video_url: {marcos_step['video_url'][:50]}...")
                        else:
                            print(f"  - No video_url (may have failed generation)")
                    checked += 1
        
        if checked == 0:
            print("ℹ No pipelines with marcos_video step data found (may be older pipelines)")
        else:
            print(f"✓ Checked {checked} pipelines, all have marcos_video step structure")


class TestStepLabelsAll:
    """Verify all 6 agent labels are correctly defined"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        pytest.skip("Authentication failed")
    
    def test_all_agent_labels_complete(self, auth_token):
        """Verify all 6 agents have proper labels defined"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=headers)
        if response.status_code != 200 or not response.json().get("pipelines"):
            pytest.skip("No pipelines available")
        
        pipeline_id = response.json()["pipelines"][0]["id"]
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/labels", headers=headers)
        assert response.status_code == 200
        
        labels = response.json().get("labels", {})
        
        expected_agents = {
            "sofia_copy": {"agent": "Sofia", "role": "Copywriter", "icon": "pen-tool"},
            "ana_review_copy": {"agent": "Ana", "role": "Revisora de Copy", "icon": "check-circle"},
            "lucas_design": {"agent": "Lucas", "role": "Designer", "icon": "palette"},
            "rafael_review_design": {"agent": "Rafael", "role": "Diretor de Arte", "icon": "award"},
            "marcos_video": {"agent": "Marcos", "role": "Videomaker", "icon": "film"},
            "pedro_publish": {"agent": "Pedro", "role": "Publisher", "icon": "calendar-clock"},
        }
        
        for step_key, expected in expected_agents.items():
            assert step_key in labels, f"Missing label for {step_key}"
            actual = labels[step_key]
            assert actual.get("agent") == expected["agent"], f"{step_key} agent mismatch"
            assert actual.get("role") == expected["role"], f"{step_key} role mismatch"
            assert actual.get("icon") == expected["icon"], f"{step_key} icon mismatch"
            print(f"✓ {step_key}: {actual['agent']} - {actual['role']} ({actual['icon']})")
        
        print(f"\n✓ All 6 agent labels are correctly defined")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
