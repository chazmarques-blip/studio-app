"""
Iteration 16 - Agent Config Integrations Tab Tests
Tests Google integration on AgentConfig page:
- GET /api/google/status returns connected: true with mock email
- GET /api/google/calendar/list and sheets/list return 500 (mock tokens)
- PUT /api/agents/{agent_id} saves integrations_config correctly
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_AGENT_ID = "003330f0-4eaf-452c-9aea-aaf28a0f5c94"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access_token in response: {data}"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestGoogleStatus:
    """Test Google status endpoint returns valid response"""
    
    def test_google_status_returns_valid_response(self, auth_headers):
        """GET /api/google/status should return connected: true/false with valid structure"""
        response = requests.get(f"{BASE_URL}/api/google/status", headers=auth_headers)
        assert response.status_code == 200, f"Status check failed: {response.text}"
        data = response.json()
        assert "connected" in data, f"Missing 'connected' field: {data}"
        
        # If connected, should have email
        if data["connected"]:
            assert "email" in data, f"Connected status should include email: {data}"
            print(f"Google connected: {data['email']}")
        else:
            print("Google not connected (mock tokens may have been disconnected)")
        
        print(f"Google status response: {data}")


class TestGoogleListEndpoints:
    """Test calendar/list and sheets/list return appropriate error when not connected"""
    
    def test_calendar_list_requires_connection(self, auth_headers):
        """GET /api/google/calendar/list returns 401 or 500 when Google not properly connected"""
        response = requests.get(f"{BASE_URL}/api/google/calendar/list", headers=auth_headers)
        # Either 401 (not connected) or 500 (mock tokens can't auth)
        assert response.status_code in [401, 500], f"Expected 401 or 500, got: {response.status_code}"
        if response.status_code == 401:
            print(f"Calendar list: 401 - Google not connected")
        else:
            print(f"Calendar list: 500 - Mock tokens failed (expected)")
    
    def test_sheets_list_requires_connection(self, auth_headers):
        """GET /api/google/sheets/list returns 401 or 500 when Google not properly connected"""
        response = requests.get(f"{BASE_URL}/api/google/sheets/list", headers=auth_headers)
        # Either 401 (not connected) or 500 (mock tokens can't auth)
        assert response.status_code in [401, 500], f"Expected 401 or 500, got: {response.status_code}"
        if response.status_code == 401:
            print(f"Sheets list: 401 - Google not connected")
        else:
            print(f"Sheets list: 500 - Mock tokens failed (expected)")


class TestAgentIntegrationsConfig:
    """Test PUT /api/agents/{agent_id} saves integrations_config correctly"""
    
    def test_save_integrations_config(self, auth_headers):
        """PUT /api/agents/{agent_id} saves google_calendar, google_sheets config"""
        integrations_config = {
            "google_calendar": {
                "enabled": True,
                "calendar_id": "test-calendar-for-iteration16"
            },
            "google_sheets": {
                "enabled": True,
                "spreadsheet_id": "test-sheet-for-iteration16",
                "range": "TestRange!A1:Z100"
            },
            "google_drive": {
                "enabled": False
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/agents/{TEST_AGENT_ID}",
            headers=auth_headers,
            json={"integrations_config": integrations_config}
        )
        assert response.status_code == 200, f"Save failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status: ok, got: {data}"
        assert "ai_config" in data.get("updated", []), f"ai_config should be in updated list: {data}"
        print(f"Integrations config saved: {data}")
    
    def test_verify_integrations_config_persisted(self, auth_headers):
        """GET /api/agents/{agent_id} returns saved integrations_config"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Get agent failed: {response.text}"
        data = response.json()
        
        # Verify integrations_config was extracted correctly
        assert "integrations_config" in data, f"Missing integrations_config: {data.keys()}"
        ic = data["integrations_config"]
        
        # Verify Google Calendar config
        assert ic.get("google_calendar", {}).get("enabled") == True, f"Calendar not enabled: {ic}"
        assert ic.get("google_calendar", {}).get("calendar_id") == "test-calendar-for-iteration16", f"Wrong calendar_id: {ic}"
        
        # Verify Google Sheets config
        assert ic.get("google_sheets", {}).get("enabled") == True, f"Sheets not enabled: {ic}"
        assert ic.get("google_sheets", {}).get("spreadsheet_id") == "test-sheet-for-iteration16", f"Wrong spreadsheet_id: {ic}"
        assert ic.get("google_sheets", {}).get("range") == "TestRange!A1:Z100", f"Wrong range: {ic}"
        
        print(f"Integrations config persisted correctly: {ic}")
    
    def test_update_google_drive_toggle(self, auth_headers):
        """Toggle Google Drive enabled status"""
        # Enable Google Drive
        response = requests.put(
            f"{BASE_URL}/api/agents/{TEST_AGENT_ID}",
            headers=auth_headers,
            json={"integrations_config": {"google_drive": {"enabled": True}}}
        )
        assert response.status_code == 200, f"Save failed: {response.text}"
        
        # Verify
        get_response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        data = get_response.json()
        assert data["integrations_config"]["google_drive"]["enabled"] == True, f"Drive not enabled: {data}"
        print("Google Drive toggle verified")


class TestAgentConfigPage:
    """Test that agent config page returns all required fields"""
    
    def test_agent_has_all_config_sections(self, auth_headers):
        """GET /api/agents/{agent_id} returns personality_config, integrations_config, channel_config"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert response.status_code == 200, f"Get agent failed: {response.text}"
        data = response.json()
        
        # Verify all config sections exist
        assert "personality_config" in data, f"Missing personality_config: {data.keys()}"
        assert "integrations_config" in data, f"Missing integrations_config: {data.keys()}"
        assert "channel_config" in data, f"Missing channel_config: {data.keys()}"
        assert "has_original" in data, f"Missing has_original flag: {data.keys()}"
        
        print(f"Agent has all config sections: personality_config, integrations_config, channel_config, has_original")
    
    def test_agent_basic_fields(self, auth_headers):
        """Verify agent has basic fields like name, type, tone"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        data = response.json()
        
        assert "name" in data, f"Missing name"
        assert "type" in data, f"Missing type"
        assert "tone" in data, f"Missing tone"
        assert "emoji_level" in data, f"Missing emoji_level"
        assert "verbosity_level" in data, f"Missing verbosity_level"
        
        print(f"Agent: {data['name']}, type: {data['type']}, tone: {data['tone']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
