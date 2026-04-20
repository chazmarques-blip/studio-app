"""
WhatsApp Integration Tests for AgentFlow
Tests the Evolution API WhatsApp endpoints with graceful failure handling
since no real Evolution API server exists
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "service" in data
        print(f"✓ Health check passed: {data}")

    def test_login_success(self):
        """POST /api/auth/login with valid credentials returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✓ Login success, token received for {data['user']['email']}")
        return data["access_token"]


@pytest.fixture
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestChannels:
    """Channel endpoint tests"""
    
    def test_get_channels_authenticated(self, auth_headers):
        """GET /api/channels returns channels array"""
        response = requests.get(f"{BASE_URL}/api/channels", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)
        print(f"✓ Channels endpoint works, found {len(data['channels'])} channels")
        return data["channels"]


class TestWhatsAppEndpoints:
    """WhatsApp Evolution API integration tests
    These endpoints make real HTTP calls to Evolution API
    Since no Evolution API server exists, we verify graceful error handling
    """
    
    def test_create_instance_graceful_failure(self, auth_headers):
        """POST /api/whatsapp/create-instance returns error when Evolution API unreachable"""
        # Use a fake Evolution API URL that won't exist
        response = requests.post(f"{BASE_URL}/api/whatsapp/create-instance", 
            headers=auth_headers,
            json={
                "api_url": "http://fake-evolution-api.local:8080",
                "api_key": "test-api-key-12345",
                "instance_name": "test-instance"
            },
            timeout=35  # Evolution API has 30s timeout
        )
        # Should return an error (500 or similar) due to connection failure
        # NOT a 200 success since Evolution API is unreachable
        # The key is that it handles the error gracefully, not crashes
        assert response.status_code in [500, 502, 503, 504, 408], \
            f"Expected error status code for unreachable API, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should contain 'detail' field"
        print(f"✓ Create instance handles unreachable API gracefully: {response.status_code}, {data.get('detail', '')[:100]}")
    
    def test_send_message_no_channel_configured(self, auth_headers):
        """POST /api/whatsapp/send returns 404 when no channel configured"""
        # First, ensure no WhatsApp channel exists
        # Clean up any existing WhatsApp channel
        channels_resp = requests.get(f"{BASE_URL}/api/channels", headers=auth_headers)
        if channels_resp.status_code == 200:
            channels = channels_resp.json().get("channels", [])
            for ch in channels:
                if ch.get("type") == "whatsapp":
                    # Delete the channel
                    requests.delete(f"{BASE_URL}/api/channels/{ch['id']}", headers=auth_headers)
        
        # Now test sending message without a channel
        response = requests.post(f"{BASE_URL}/api/whatsapp/send",
            headers=auth_headers,
            json={
                "phone_number": "+15551234567",
                "message": "Test message"
            }
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower() or "channel" in data["detail"].lower()
        print(f"✓ Send message returns 404 when no channel: {data.get('detail')}")
    
    def test_get_status_no_channel(self, auth_headers):
        """GET /api/whatsapp/status/{instance} returns error gracefully when no channel"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/status/test-instance", headers=auth_headers)
        # Should return 404 or graceful error state since no channel configured
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data
            print(f"✓ Status returns 404 when no channel: {data.get('detail')}")
        elif response.status_code == 200:
            data = response.json()
            # Even with 200, should indicate not connected
            assert data.get("connected") == False or data.get("state") in ["error", "unconfigured"]
            print(f"✓ Status returns graceful error state: {data}")
        else:
            pytest.fail(f"Unexpected status code {response.status_code}")
    
    def test_get_qr_no_channel(self, auth_headers):
        """GET /api/whatsapp/qr/{instance} returns error gracefully when no channel"""
        response = requests.get(f"{BASE_URL}/api/whatsapp/qr/test-instance", headers=auth_headers)
        # Should return 404 or graceful error state since no channel configured
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data
            print(f"✓ QR endpoint returns 404 when no channel: {data.get('detail')}")
        elif response.status_code == 400:
            data = response.json()
            print(f"✓ QR endpoint returns 400 when not configured: {data.get('detail')}")
        elif response.status_code == 200:
            data = response.json()
            # Even with 200, should indicate no QR available
            assert data.get("qr_code") is None or data.get("status") == "error"
            print(f"✓ QR returns graceful error state: {data}")
        else:
            print(f"QR endpoint status: {response.status_code}, {response.text[:200]}")


class TestWhatsAppWithChannel:
    """Tests that create a channel first then test WhatsApp endpoints"""
    
    def test_whatsapp_flow_with_fake_config(self, auth_headers):
        """Create a WhatsApp channel and test status/QR endpoints handle errors"""
        # Step 1: Create a channel with fake Evolution API config
        channel_response = requests.post(f"{BASE_URL}/api/channels",
            headers=auth_headers,
            json={
                "type": "whatsapp",
                "config": {
                    "api_url": "http://fake-evo.local:8080",
                    "api_key": "fake-key",
                    "instance_name": "fake-test-instance"
                }
            }
        )
        assert channel_response.status_code == 200
        channel = channel_response.json()
        print(f"✓ Created WhatsApp channel: {channel.get('id')}")
        
        try:
            # Step 2: Test status endpoint with the configured channel
            status_resp = requests.get(f"{BASE_URL}/api/whatsapp/status/fake-test-instance", headers=auth_headers)
            # Should return 200 with error state (Evolution API unreachable)
            assert status_resp.status_code == 200
            status_data = status_resp.json()
            assert status_data.get("connected") == False
            assert status_data.get("state") in ["error", "unconfigured", "unknown"]
            print(f"✓ Status with fake config returns graceful error: {status_data.get('state')}")
            
            # Step 3: Test QR endpoint with the configured channel  
            qr_resp = requests.get(f"{BASE_URL}/api/whatsapp/qr/fake-test-instance", headers=auth_headers)
            # Should return 200 with no QR or error state
            assert qr_resp.status_code == 200
            qr_data = qr_resp.json()
            assert qr_data.get("qr_code") is None
            print(f"✓ QR with fake config returns graceful error: {qr_data}")
            
            # Step 4: Test send message
            send_resp = requests.post(f"{BASE_URL}/api/whatsapp/send",
                headers=auth_headers,
                json={
                    "phone_number": "+15551234567",
                    "message": "Test"
                }
            )
            # Should fail gracefully (500 from connection error or similar)
            assert send_resp.status_code in [400, 500, 502, 503, 504]
            print(f"✓ Send with fake config fails gracefully: {send_resp.status_code}")
            
        finally:
            # Cleanup: Delete the test channel
            if channel.get("id"):
                requests.delete(f"{BASE_URL}/api/channels/{channel['id']}", headers=auth_headers)
                print(f"✓ Cleaned up test channel")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
