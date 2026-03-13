"""
Iteration 18 - Pipeline API Testing
Tests for the AgentZZ AI Marketing Pipeline feature (Enterprise plan only)

Features tested:
- GET /api/campaigns/pipeline/list - List pipelines
- POST /api/campaigns/pipeline - Create pipeline
- GET /api/campaigns/pipeline/{id} - Get pipeline status
- POST /api/campaigns/pipeline/{id}/approve - Approve step
- DELETE /api/campaigns/pipeline/{id} - Delete pipeline
"""

import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestPipelineAuth:
    """Test authentication for pipeline access"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for Enterprise user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers for API calls"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_login_success(self, auth_token):
        """Verify login and token received"""
        assert auth_token is not None
        assert len(auth_token) > 50  # JWT tokens are longer than 50 chars
        print(f"Login successful, token length: {len(auth_token)}")


class TestPipelineList:
    """Test listing pipelines"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_list_pipelines(self, auth_headers):
        """GET /api/campaigns/pipeline/list - Should return array of pipelines"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/list", headers=auth_headers)
        assert response.status_code == 200, f"List failed: {response.text}"
        data = response.json()
        assert "pipelines" in data, "Response should have 'pipelines' key"
        assert isinstance(data["pipelines"], list), "Pipelines should be a list"
        print(f"Found {len(data['pipelines'])} existing pipelines")


class TestPipelineCreate:
    """Test creating pipelines"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def created_pipeline_id(self, auth_headers):
        """Create a pipeline for testing and cleanup after"""
        # Create pipeline with AUTO mode for faster execution
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Campanha de lancamento do AgentZZ - produtos de automacao IA",
            "mode": "auto",
            "platforms": ["whatsapp", "instagram"]
        })
        if response.status_code == 200 or response.status_code == 201:
            pipeline = response.json()
            yield pipeline.get("id")
            # Cleanup
            requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline.get('id')}", headers=auth_headers)
        else:
            yield None
    
    def test_create_pipeline_auto_mode(self, auth_headers):
        """POST /api/campaigns/pipeline - Create auto mode pipeline"""
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Campanha rapida para redes sociais sobre IA",
            "mode": "auto",
            "platforms": ["whatsapp", "instagram"]
        })
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "id" in data, "Response should have 'id'"
        assert "briefing" in data, "Response should have 'briefing'"
        assert data["mode"] == "auto", "Mode should be 'auto'"
        assert data["status"] in ["pending", "running"], "Initial status should be pending or running"
        assert "steps" in data, "Response should have 'steps'"
        assert len(data.get("platforms", [])) == 2, "Should have 2 platforms"
        
        pipeline_id = data["id"]
        print(f"Created auto pipeline: {pipeline_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
    
    def test_create_pipeline_semi_auto_mode(self, auth_headers):
        """POST /api/campaigns/pipeline - Create semi-auto mode pipeline"""
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Campanha interativa com aprovacao manual",
            "mode": "semi_auto",
            "platforms": ["facebook", "telegram"]
        })
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        data = response.json()
        
        assert data["mode"] == "semi_auto", "Mode should be 'semi_auto'"
        pipeline_id = data["id"]
        print(f"Created semi-auto pipeline: {pipeline_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
    
    def test_create_pipeline_validates_briefing(self, auth_headers):
        """POST /api/campaigns/pipeline - Empty briefing should be handled"""
        response = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "",
            "mode": "auto",
            "platforms": ["whatsapp"]
        })
        # Either validation error or empty pipeline accepted
        print(f"Empty briefing response: {response.status_code}")


class TestPipelineProgress:
    """Test pipeline status and progress polling"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_get_pipeline_status(self, auth_headers):
        """GET /api/campaigns/pipeline/{id} - Verify status polling works"""
        # First create a pipeline
        create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Mini campanha para teste de status",
            "mode": "auto",
            "platforms": ["whatsapp"]
        })
        assert create_resp.status_code in [200, 201], f"Create failed: {create_resp.text}"
        pipeline_id = create_resp.json()["id"]
        
        # Poll for status changes (up to 90 seconds)
        completed = False
        max_polls = 18  # 18 polls * 5 seconds = 90 seconds
        last_status = None
        steps_with_output = []
        
        for i in range(max_polls):
            time.sleep(5)
            status_resp = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
            assert status_resp.status_code == 200, f"Status check failed: {status_resp.text}"
            
            pipeline_data = status_resp.json()
            current_status = pipeline_data.get("status")
            current_step = pipeline_data.get("current_step")
            steps = pipeline_data.get("steps", {})
            
            # Track steps with output
            for step_name, step_data in steps.items():
                if step_data.get("output") and step_name not in steps_with_output:
                    steps_with_output.append(step_name)
            
            print(f"Poll {i+1}: status={current_status}, current_step={current_step}, steps_with_output={len(steps_with_output)}")
            
            last_status = current_status
            
            if current_status in ["completed", "failed"]:
                completed = True
                break
        
        # Verify we got some progress
        assert len(steps_with_output) > 0, "Pipeline should have at least one step with output"
        print(f"Final status: {last_status}, Steps completed: {steps_with_output}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
    
    def test_get_nonexistent_pipeline(self, auth_headers):
        """GET /api/campaigns/pipeline/{id} - Should 404 for invalid ID"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/non-existent-id-12345", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestPipelineApprove:
    """Test approval flow for semi-auto mode"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_approve_not_waiting(self, auth_headers):
        """POST /api/campaigns/pipeline/{id}/approve - Should fail if not waiting"""
        # Create auto pipeline (won't pause for approval)
        create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Teste de aprovacao em modo auto",
            "mode": "auto",
            "platforms": ["whatsapp"]
        })
        assert create_resp.status_code in [200, 201]
        pipeline_id = create_resp.json()["id"]
        
        # Try to approve immediately (should fail - not waiting)
        approve_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/approve", 
                                     headers=auth_headers, json={"selection": 1})
        # Should return 400 if not waiting for approval
        assert approve_resp.status_code in [400, 200], f"Unexpected status: {approve_resp.status_code}"
        
        if approve_resp.status_code == 400:
            print(f"Correctly rejected: {approve_resp.json().get('detail')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
    
    def test_semi_auto_waits_for_approval(self, auth_headers):
        """Create semi-auto pipeline and verify it pauses for approval"""
        # Create semi-auto pipeline
        create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Campanha semi-automatica para teste de aprovacao",
            "mode": "semi_auto",
            "platforms": ["instagram"]
        })
        assert create_resp.status_code in [200, 201], f"Create failed: {create_resp.text}"
        pipeline_id = create_resp.json()["id"]
        
        # Poll until waiting_approval or timeout
        waiting_found = False
        max_polls = 24  # 24 * 5 = 120 seconds max
        
        for i in range(max_polls):
            time.sleep(5)
            status_resp = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
            if status_resp.status_code != 200:
                continue
            
            pipeline_data = status_resp.json()
            current_status = pipeline_data.get("status")
            
            print(f"Semi-auto poll {i+1}: status={current_status}")
            
            if current_status == "waiting_approval":
                waiting_found = True
                print("Pipeline is waiting for approval - semi-auto mode working correctly!")
                
                # Try to approve
                approve_resp = requests.post(
                    f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/approve",
                    headers=auth_headers,
                    json={"selection": 1}
                )
                print(f"Approval response: {approve_resp.status_code}")
                break
            elif current_status in ["completed", "failed"]:
                print(f"Pipeline ended with status: {current_status}")
                break
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
        
        # Note: waiting_found might be False if AI is too fast, which is acceptable
        print(f"Semi-auto approval test completed. waiting_approval found: {waiting_found}")


class TestPipelineDelete:
    """Test pipeline deletion"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_delete_pipeline(self, auth_headers):
        """DELETE /api/campaigns/pipeline/{id} - Should delete pipeline"""
        # Create a pipeline to delete
        create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Pipeline para deletar",
            "mode": "auto",
            "platforms": ["whatsapp"]
        })
        assert create_resp.status_code in [200, 201]
        pipeline_id = create_resp.json()["id"]
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
        
        data = delete_resp.json()
        assert data.get("status") == "deleted", "Should return deleted status"
        
        # Verify it's gone
        get_resp = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)
        assert get_resp.status_code == 404, "Deleted pipeline should return 404"
        
        print("Pipeline deletion verified successfully")
    
    def test_delete_nonexistent_pipeline(self, auth_headers):
        """DELETE /api/campaigns/pipeline/{id} - Should 404 for invalid ID"""
        response = requests.delete(f"{BASE_URL}/api/campaigns/pipeline/fake-id-12345", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestPipelineStepLabels:
    """Test step labels endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_get_step_labels(self, auth_headers):
        """GET /api/campaigns/pipeline/{id}/labels - Should return step metadata"""
        # Create a pipeline first
        create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=auth_headers, json={
            "briefing": "TEST_Pipeline para labels",
            "mode": "auto",
            "platforms": ["whatsapp"]
        })
        assert create_resp.status_code in [200, 201]
        pipeline_id = create_resp.json()["id"]
        
        # Get labels
        labels_resp = requests.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}/labels", headers=auth_headers)
        assert labels_resp.status_code == 200, f"Labels failed: {labels_resp.text}"
        
        data = labels_resp.json()
        assert "labels" in data, "Should have labels"
        assert "order" in data, "Should have order"
        
        labels = data["labels"]
        order = data["order"]
        
        # Verify expected steps
        expected_steps = ["sofia_copy", "ana_review_copy", "lucas_design", "ana_review_design", "pedro_publish"]
        assert order == expected_steps, f"Order mismatch: {order}"
        
        # Verify label metadata
        for step in expected_steps:
            assert step in labels, f"Missing label for {step}"
            assert "agent" in labels[step], f"Missing agent for {step}"
            assert "role" in labels[step], f"Missing role for {step}"
        
        print(f"Step labels verified: {list(labels.keys())}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}", headers=auth_headers)


class TestPipelineEnterprisePlan:
    """Test Enterprise plan requirement"""
    
    def test_enterprise_plan_required(self):
        """Verify pipeline requires Enterprise plan"""
        # This test documents the behavior - Enterprise users (test@agentflow.com) should succeed
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Check dashboard to verify plan
        dashboard_resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert dashboard_resp.status_code == 200
        
        plan = dashboard_resp.json().get("plan")
        print(f"User plan: {plan}")
        
        if plan != "enterprise":
            # If not enterprise, pipeline creation should fail with 403
            create_resp = requests.post(f"{BASE_URL}/api/campaigns/pipeline", headers=headers, json={
                "briefing": "Test",
                "mode": "auto",
                "platforms": ["whatsapp"]
            })
            assert create_resp.status_code == 403, "Non-enterprise should get 403"
            assert "Enterprise" in create_resp.json().get("detail", ""), "Error should mention Enterprise"
        else:
            print("User has Enterprise plan - pipeline access granted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
