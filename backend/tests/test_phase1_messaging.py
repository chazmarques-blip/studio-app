"""
AgentFlow Phase 1 API Tests - Messaging Infrastructure
Tests for conversations, channels, leads, messages endpoints
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials - existing test user with Portuguese language
TEST_USER_EMAIL = "test@agentflow.com"
TEST_USER_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def auth_header(auth_token):
    """Return auth header dict"""
    return {"Authorization": f"Bearer {auth_token}"}


# === CONVERSATION TESTS ===
class TestConversations:
    """Conversation endpoint tests"""
    
    def test_create_conversation(self, auth_header):
        """POST /api/conversations creates conversation"""
        response = requests.post(f"{BASE_URL}/api/conversations", 
            headers=auth_header,
            json={
                "contact_name": f"TEST_Contact_{int(time.time())}",
                "contact_phone": "+5511999999999",
                "contact_email": "contact@test.com",
                "channel_type": "whatsapp"
            }
        )
        assert response.status_code == 200, f"Create conversation failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["channel_type"] == "whatsapp"
        assert data["status"] == "active"
        print(f"Conversation created: {data['id']}")
        return data["id"]
    
    def test_list_conversations(self, auth_header):
        """GET /api/conversations lists conversations"""
        response = requests.get(f"{BASE_URL}/api/conversations", headers=auth_header)
        assert response.status_code == 200, f"List conversations failed: {response.text}"
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        print(f"Conversations count: {len(data['conversations'])}")
    
    def test_list_conversations_with_channel_filter(self, auth_header):
        """GET /api/conversations?channel_type=whatsapp filters by channel"""
        response = requests.get(f"{BASE_URL}/api/conversations?channel_type=whatsapp", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        # All returned should be whatsapp
        for convo in data["conversations"]:
            assert convo["channel_type"] == "whatsapp"
        print(f"WhatsApp conversations: {len(data['conversations'])}")
    
    def test_get_conversation_detail(self, auth_header):
        """GET /api/conversations/{id} returns conversation detail"""
        # First create a conversation
        create_resp = requests.post(f"{BASE_URL}/api/conversations", 
            headers=auth_header,
            json={"contact_name": "TEST_Detail_Contact", "channel_type": "instagram"}
        )
        convo_id = create_resp.json()["id"]
        
        # Get detail
        response = requests.get(f"{BASE_URL}/api/conversations/{convo_id}", headers=auth_header)
        assert response.status_code == 200, f"Get conversation failed: {response.text}"
        data = response.json()
        assert data["id"] == convo_id
        assert data["contact_name"] == "TEST_Detail_Contact"
        print(f"Conversation detail fetched: {data['id']}")


# === MESSAGE TESTS ===
class TestMessages:
    """Message endpoint tests"""
    
    def test_send_message_to_conversation(self, auth_header):
        """POST /api/conversations/{id}/messages sends message"""
        # Create conversation first
        convo_resp = requests.post(f"{BASE_URL}/api/conversations", 
            headers=auth_header,
            json={"contact_name": "TEST_Message_Contact", "channel_type": "whatsapp"}
        )
        convo_id = convo_resp.json()["id"]
        
        # Send message
        response = requests.post(f"{BASE_URL}/api/conversations/{convo_id}/messages", 
            headers=auth_header,
            json={"content": "Hello, this is a test message!", "message_type": "text"}
        )
        assert response.status_code == 200, f"Send message failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["content"] == "Hello, this is a test message!"
        assert data["sender"] == "operator"
        print(f"Message sent: {data['id']}")
    
    def test_get_messages_from_conversation(self, auth_header):
        """GET /api/conversations/{id}/messages returns messages"""
        # Create conversation
        convo_resp = requests.post(f"{BASE_URL}/api/conversations", 
            headers=auth_header,
            json={"contact_name": "TEST_GetMsgs_Contact", "channel_type": "telegram"}
        )
        convo_id = convo_resp.json()["id"]
        
        # Send a few messages
        for i in range(3):
            requests.post(f"{BASE_URL}/api/conversations/{convo_id}/messages", 
                headers=auth_header,
                json={"content": f"Test message {i+1}", "message_type": "text"}
            )
        
        # Get messages
        response = requests.get(f"{BASE_URL}/api/conversations/{convo_id}/messages", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 3
        print(f"Messages retrieved: {len(data['messages'])}")


# === CHANNEL TESTS ===
class TestChannels:
    """Channel endpoint tests"""
    
    def test_create_whatsapp_channel(self, auth_header):
        """POST /api/channels creates WhatsApp channel"""
        response = requests.post(f"{BASE_URL}/api/channels", 
            headers=auth_header,
            json={
                "type": "whatsapp",
                "config": {"instance_name": "test_instance"}
            }
        )
        assert response.status_code == 200, f"Create channel failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["type"] == "whatsapp"
        assert data["status"] in ["connecting", "connected"]
        print(f"Channel created: {data['id']}, status: {data['status']}")
    
    def test_list_channels(self, auth_header):
        """GET /api/channels lists channels"""
        response = requests.get(f"{BASE_URL}/api/channels", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)
        print(f"Channels count: {len(data['channels'])}")


# === LEADS / CRM TESTS ===
class TestLeads:
    """Lead CRUD endpoint tests"""
    
    def test_create_lead(self, auth_header):
        """POST /api/leads creates lead"""
        response = requests.post(f"{BASE_URL}/api/leads", 
            headers=auth_header,
            json={
                "name": f"TEST_Lead_{int(time.time())}",
                "phone": "+5511888888888",
                "email": "lead@test.com",
                "company": "Test Company Inc",
                "stage": "new",
                "value": 5000.00
            }
        )
        assert response.status_code == 200, f"Create lead failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["stage"] == "new"
        assert float(data["value"]) == 5000.00
        print(f"Lead created: {data['id']}, stage: {data['stage']}")
        return data["id"]
    
    def test_list_leads(self, auth_header):
        """GET /api/leads lists leads"""
        response = requests.get(f"{BASE_URL}/api/leads", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert isinstance(data["leads"], list)
        print(f"Leads count: {len(data['leads'])}")
    
    def test_list_leads_with_stage_filter(self, auth_header):
        """GET /api/leads?stage=new filters by stage"""
        # First create a lead with 'new' stage
        requests.post(f"{BASE_URL}/api/leads", 
            headers=auth_header,
            json={"name": "TEST_New_Lead", "stage": "new"}
        )
        
        response = requests.get(f"{BASE_URL}/api/leads?stage=new", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        # All returned should be 'new' stage
        for lead in data["leads"]:
            assert lead["stage"] == "new"
        print(f"New stage leads: {len(data['leads'])}")
    
    def test_update_lead_stage(self, auth_header):
        """PUT /api/leads/{id} updates lead stage"""
        # Create lead first
        create_resp = requests.post(f"{BASE_URL}/api/leads", 
            headers=auth_header,
            json={"name": "TEST_Update_Lead", "stage": "new"}
        )
        lead_id = create_resp.json()["id"]
        
        # Update stage
        response = requests.put(f"{BASE_URL}/api/leads/{lead_id}", 
            headers=auth_header,
            json={"stage": "qualified", "score": 75}
        )
        assert response.status_code == 200, f"Update lead failed: {response.text}"
        data = response.json()
        assert data["stage"] == "qualified"
        assert data["score"] == 75
        print(f"Lead updated: {data['id']}, stage: {data['stage']}")
    
    def test_get_lead_detail(self, auth_header):
        """GET /api/leads/{id} returns lead detail"""
        # Create lead
        create_resp = requests.post(f"{BASE_URL}/api/leads", 
            headers=auth_header,
            json={"name": "TEST_Detail_Lead", "stage": "proposal", "value": 10000}
        )
        lead_id = create_resp.json()["id"]
        
        # Get detail
        response = requests.get(f"{BASE_URL}/api/leads/{lead_id}", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead_id
        assert data["name"] == "TEST_Detail_Lead"
        assert data["stage"] == "proposal"
        print(f"Lead detail fetched: {data['id']}")


# === WEBHOOK TESTS ===
class TestWebhook:
    """WhatsApp webhook endpoint tests"""
    
    def test_whatsapp_webhook_get_verify(self):
        """GET /api/webhook/whatsapp returns verification status"""
        response = requests.get(f"{BASE_URL}/api/webhook/whatsapp")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
        print(f"Webhook verified: {data['service']}")
    
    def test_whatsapp_webhook_post_receives_message(self):
        """POST /api/webhook/whatsapp receives incoming messages (MOCKED - no real Evolution API)"""
        # Simulated Evolution API payload
        payload = {
            "event": "messages.upsert",
            "instance": "test_instance",
            "data": {
                "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False},
                "message": {"conversation": "Hello from WhatsApp!"}
            }
        }
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=payload)
        assert response.status_code == 200
        data = response.json()
        # May return no_channel if no matching channel exists, which is expected
        assert data["status"] in ["ok", "no_channel", "ignored"]
        print(f"Webhook POST response: {data['status']}")


# === DASHBOARD STATS TESTS ===
class TestDashboardStats:
    """Dashboard stats with real data tests"""
    
    def test_dashboard_stats_returns_real_data(self, auth_header):
        """GET /api/dashboard/stats returns real stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "messages_today" in data
        assert "resolution_rate" in data
        assert "active_leads" in data
        assert "revenue" in data
        assert "plan" in data
        assert "messages_used" in data
        assert "messages_limit" in data
        assert "agents_count" in data
        print(f"Dashboard stats: plan={data['plan']}, messages={data['messages_used']}/{data['messages_limit']}, agents={data['agents_count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
