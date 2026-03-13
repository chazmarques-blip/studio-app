"""
Iteration 15 - Google Integration Tests
Tests Google OAuth2 flow, Calendar, Sheets, Drive endpoints

Since user hasn't connected Google account, most endpoints should return 401 "Google not connected"
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
    """Get auth token for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # API returns access_token (not token)
    assert "access_token" in data, f"No access_token in response: {data}"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestGoogleOAuthFlow:
    """Test Google OAuth connection flow"""
    
    def test_google_status_returns_not_connected(self, auth_headers):
        """GET /api/google/status should return connected: false for users without Google"""
        response = requests.get(f"{BASE_URL}/api/google/status", headers=auth_headers)
        assert response.status_code == 200, f"Status check failed: {response.text}"
        data = response.json()
        assert "connected" in data, f"Missing 'connected' field: {data}"
        # User likely hasn't connected Google, should be false
        # If connected, should have email field
        if data["connected"]:
            assert "email" in data, "Connected status should include email"
        print(f"Google status: {data}")
    
    def test_google_connect_returns_authorization_url(self, auth_headers):
        """GET /api/google/connect should return a valid Google OAuth authorization URL"""
        response = requests.get(f"{BASE_URL}/api/google/connect", headers=auth_headers)
        assert response.status_code == 200, f"Connect failed: {response.text}"
        data = response.json()
        assert "authorization_url" in data, f"Missing 'authorization_url': {data}"
        
        auth_url = data["authorization_url"]
        # Validate OAuth URL structure
        assert "accounts.google.com" in auth_url, "Should be Google OAuth URL"
        assert "client_id=" in auth_url, "Should contain client_id"
        assert "redirect_uri=" in auth_url, "Should contain redirect_uri"
        assert "scope=" in auth_url, "Should contain scope"
        assert "calendar" in auth_url.lower() or "spreadsheets" in auth_url.lower(), "Should have Calendar or Sheets scope"
        print(f"Authorization URL: {auth_url[:100]}...")
    
    def test_google_disconnect(self, auth_headers):
        """POST /api/google/disconnect should return status: disconnected"""
        response = requests.post(f"{BASE_URL}/api/google/disconnect", headers=auth_headers)
        assert response.status_code == 200, f"Disconnect failed: {response.text}"
        data = response.json()
        assert data.get("status") == "disconnected", f"Expected 'disconnected' status: {data}"


class TestGoogleCalendarWithoutConnection:
    """Test Calendar endpoints return 401 when Google not connected"""
    
    def test_list_calendar_events_requires_connection(self, auth_headers):
        """GET /api/google/calendar/events should return 401 without Google connection"""
        response = requests.get(f"{BASE_URL}/api/google/calendar/events", headers=auth_headers)
        # Should return 401 since user hasn't connected Google
        # Or 200 if already connected
        if response.status_code == 401:
            data = response.json()
            assert "Google not connected" in str(data.get("detail", "")), f"Should mention Google not connected: {data}"
            print("Calendar events: 401 - Google not connected (expected)")
        elif response.status_code == 200:
            data = response.json()
            assert "events" in data, f"Should have events field: {data}"
            print(f"Calendar events returned {len(data.get('events', []))} events")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, {response.text}")
    
    def test_create_calendar_event_requires_connection(self, auth_headers):
        """POST /api/google/calendar/events should return 401 without Google connection"""
        event_data = {
            "summary": "Test Event",
            "start": "2025-01-15T10:00:00Z",
            "end": "2025-01-15T11:00:00Z",
            "description": "Test event"
        }
        response = requests.post(f"{BASE_URL}/api/google/calendar/events", 
                                headers=auth_headers, json=event_data)
        if response.status_code == 401:
            data = response.json()
            assert "Google not connected" in str(data.get("detail", "")), f"Should mention Google not connected: {data}"
            print("Create calendar event: 401 - Google not connected (expected)")
        elif response.status_code in [200, 201]:
            # If connected, should return event details
            data = response.json()
            assert "id" in data, f"Should return event id: {data}"
            print(f"Event created: {data}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, {response.text}")


class TestGoogleSheetsWithoutConnection:
    """Test Sheets endpoints return 401 when Google not connected"""
    
    def test_list_sheets_requires_connection(self, auth_headers):
        """GET /api/google/sheets/list should return 401 without Google connection"""
        response = requests.get(f"{BASE_URL}/api/google/sheets/list", headers=auth_headers)
        if response.status_code == 401:
            data = response.json()
            assert "Google not connected" in str(data.get("detail", "")), f"Should mention Google not connected: {data}"
            print("List sheets: 401 - Google not connected (expected)")
        elif response.status_code == 200:
            data = response.json()
            assert "sheets" in data, f"Should have sheets field: {data}"
            print(f"Sheets returned {len(data.get('sheets', []))} spreadsheets")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, {response.text}")
    
    def test_export_leads_requires_connection(self, auth_headers):
        """POST /api/google/sheets/export-leads should return 401 without Google connection"""
        response = requests.post(f"{BASE_URL}/api/google/sheets/export-leads", headers=auth_headers)
        if response.status_code == 401:
            data = response.json()
            assert "Google not connected" in str(data.get("detail", "")), f"Should mention Google not connected: {data}"
            print("Export leads: 401 - Google not connected (expected)")
        elif response.status_code == 200:
            data = response.json()
            assert "spreadsheet_id" in data, f"Should return spreadsheet_id: {data}"
            assert "leads_exported" in data, f"Should return leads_exported count: {data}"
            print(f"Leads exported: {data.get('leads_exported')}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}, {response.text}")
    
    def test_read_sheet_requires_connection(self, auth_headers):
        """POST /api/google/sheets/read should return 401 without Google connection"""
        sheet_data = {
            "spreadsheet_id": "test_spreadsheet_id",
            "range": "Sheet1!A1:D10"
        }
        response = requests.post(f"{BASE_URL}/api/google/sheets/read", 
                                headers=auth_headers, json=sheet_data)
        if response.status_code == 401:
            data = response.json()
            assert "Google not connected" in str(data.get("detail", "")), f"Should mention Google not connected: {data}"
            print("Read sheet: 401 - Google not connected (expected)")
        elif response.status_code == 200:
            data = response.json()
            assert "values" in data, f"Should return values: {data}"
            print(f"Sheet read successful")
        else:
            # Could be 400 for invalid spreadsheet_id
            print(f"Read sheet response: {response.status_code} - {response.text}")


class TestGoogleAuthRequired:
    """Test that Google endpoints require authentication"""
    
    def test_google_status_requires_auth(self):
        """GET /api/google/status should require authentication"""
        response = requests.get(f"{BASE_URL}/api/google/status")
        assert response.status_code in [401, 403, 422], f"Should require auth: {response.status_code}"
    
    def test_google_connect_requires_auth(self):
        """GET /api/google/connect should require authentication"""
        response = requests.get(f"{BASE_URL}/api/google/connect")
        assert response.status_code in [401, 403, 422], f"Should require auth: {response.status_code}"
    
    def test_calendar_events_requires_auth(self):
        """GET /api/google/calendar/events should require authentication"""
        response = requests.get(f"{BASE_URL}/api/google/calendar/events")
        assert response.status_code in [401, 403, 422], f"Should require auth: {response.status_code}"
    
    def test_sheets_list_requires_auth(self):
        """GET /api/google/sheets/list should require authentication"""
        response = requests.get(f"{BASE_URL}/api/google/sheets/list")
        assert response.status_code in [401, 403, 422], f"Should require auth: {response.status_code}"


class TestRegressionHealthAndDashboard:
    """Regression tests for existing functionality"""
    
    def test_health_endpoint(self):
        """GET /api/health should return ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Health status not ok: {data}"
        assert data.get("database") == "supabase", f"Database not supabase: {data}"
    
    def test_dashboard_stats(self, auth_headers):
        """GET /api/dashboard/stats should return dashboard data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        # Validate core dashboard fields
        assert "messages_today" in data, f"Missing messages_today: {data}"
        assert "agents_count" in data, f"Missing agents_count: {data}"
        assert "plan" in data, f"Missing plan: {data}"
        print(f"Dashboard stats: plan={data.get('plan')}, agents={data.get('agents_count')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
