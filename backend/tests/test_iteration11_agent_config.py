"""
Iteration 11 Tests - Enhanced Agent Configuration with 6 Tabs
- Personality Config (tone, sliders, flags)
- Knowledge Base CRUD
- Integrations Config
- Channel Config
- Escalation Rules
- Automations/Follow-up Rules
- Telegram Setup Endpoint
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://saas-agent-hub-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_AGENT_ID = "003330f0-4eaf-452c-9aea-aaf28a0f5c94"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Health check endpoint returns ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("✓ Health endpoint working")
    
    def test_login_returns_token(self):
        """Login endpoint returns access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print(f"✓ Login successful, token received")


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="class")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestAgentGet:
    """Test GET /api/agents/{agent_id} returns new config fields"""
    
    def test_get_agent_returns_personality_config(self, auth_headers):
        """GET agent includes personality_config extracted from personality.config"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "personality_config" in data
        print(f"✓ personality_config present in agent response")
    
    def test_get_agent_returns_integrations_config(self, auth_headers):
        """GET agent includes integrations_config extracted from ai_config.integrations"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "integrations_config" in data
        print(f"✓ integrations_config present in agent response")
    
    def test_get_agent_returns_channel_config(self, auth_headers):
        """GET agent includes channel_config extracted from ai_config.channels"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "channel_config" in data
        print(f"✓ channel_config present in agent response")
    
    def test_get_agent_returns_standard_fields(self, auth_headers):
        """GET agent returns standard fields (name, tone, emoji_level, etc.)"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "tone" in data
        assert "escalation_rules" in data
        assert "follow_up_config" in data
        print(f"✓ Standard agent fields present")


class TestAgentUpdate:
    """Test PUT /api/agents/{agent_id} stores new config fields"""
    
    def test_update_personality_config(self, auth_headers):
        """PUT agent with personality_config stores it in personality.config"""
        test_config = {
            "proactivity": 0.7,
            "creativity": 0.6,
            "formality": 0.5,
            "flags": {
                "auto_multilingual": True,
                "remember_context": True,
                "auto_escalate": True,
                "suggest_products": False,
                "collect_data": True
            }
        }
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, 
            json={"personality_config": test_config})
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "personality" in data.get("updated", [])
        
        # Verify by GET
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data.get("personality_config", {}).get("proactivity") == 0.7
        print(f"✓ personality_config saved and retrieved correctly")
    
    def test_update_integrations_config(self, auth_headers):
        """PUT agent with integrations_config stores it in ai_config.integrations"""
        test_config = {
            "google_calendar": {"enabled": True},
            "google_sheets": {"enabled": False},
            "google_drive": {"enabled": False},
            "custom_api": {"enabled": False},
            "webhook": {"enabled": False}
        }
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, 
            json={"integrations_config": test_config})
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "ai_config" in data.get("updated", [])
        
        # Verify by GET
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data.get("integrations_config", {}).get("google_calendar", {}).get("enabled") == True
        print(f"✓ integrations_config saved and retrieved correctly")
    
    def test_update_channel_config(self, auth_headers):
        """PUT agent with channel_config stores it in ai_config.channels"""
        test_config = {
            "telegram": {"enabled": True, "bot_token": ""},
            "whatsapp": {"enabled": False},
            "instagram": {"enabled": False},
            "messenger": {"enabled": False},
            "sms": {"enabled": False},
            "webchat": {"enabled": False}
        }
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, 
            json={"channel_config": test_config})
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "ai_config" in data.get("updated", [])
        
        # Verify by GET
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data.get("channel_config", {}).get("telegram", {}).get("enabled") == True
        print(f"✓ channel_config saved and retrieved correctly")
    
    def test_update_tone_and_sliders(self, auth_headers):
        """PUT agent with tone, emoji_level, verbosity_level"""
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, 
            json={
                "tone": "friendly",
                "emoji_level": 0.5,
                "verbosity_level": 0.7
            })
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        
        # Verify by GET
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data.get("tone") == "friendly"
        assert verify_data.get("emoji_level") == 0.5
        assert verify_data.get("verbosity_level") == 0.7
        print(f"✓ tone and slider values saved correctly")
    
    def test_update_escalation_rules(self, auth_headers):
        """PUT agent with escalation_rules"""
        test_rules = {
            "keywords": ["help", "manager", "human", "agent"],
            "sentiment_threshold": 0.4,
            "notify_operator": True
        }
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, 
            json={"escalation_rules": test_rules})
        
        assert response.status_code == 200
        
        # Verify by GET
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data.get("escalation_rules", {}).get("sentiment_threshold") == 0.4
        print(f"✓ escalation_rules saved correctly")
    
    def test_update_follow_up_config(self, auth_headers):
        """PUT agent with follow_up_config"""
        test_config = {
            "enabled": True,
            "max_follow_ups": 5,
            "cool_down_days": 3
        }
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, 
            json={"follow_up_config": test_config})
        
        assert response.status_code == 200
        
        # Verify by GET
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        assert verify_data.get("follow_up_config", {}).get("enabled") == True
        assert verify_data.get("follow_up_config", {}).get("max_follow_ups") == 5
        print(f"✓ follow_up_config saved correctly")


class TestTelegramEndpoints:
    """Test Telegram setup and webhook endpoints"""
    
    def test_telegram_setup_validates_token_format(self, auth_headers):
        """POST /api/telegram/setup validates bot token"""
        # Test with invalid/fake token - should return error
        response = requests.post(f"{BASE_URL}/api/telegram/setup", 
            headers=auth_headers, 
            json={
                "agent_id": TEST_AGENT_ID,
                "bot_token": "invalid-token-format"
            })
        
        # Should return 400 for invalid token
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"✓ Telegram setup validates token format (returns 400 for invalid)")
    
    def test_telegram_webhook_verify_endpoint(self):
        """GET /api/webhook/telegram/{agent_id} returns ok status"""
        response = requests.get(f"{BASE_URL}/api/webhook/telegram/{TEST_AGENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("agent_id") == TEST_AGENT_ID
        print(f"✓ Telegram webhook verify endpoint returns ok")


class TestKnowledgeBaseCRUD:
    """Test Knowledge Base CRUD operations"""
    
    def test_get_knowledge(self, auth_headers):
        """GET /api/agents/{agent_id}/knowledge returns items list"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/knowledge", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✓ GET knowledge returns items list ({len(data['items'])} items)")
    
    def test_add_and_delete_knowledge(self, auth_headers):
        """POST then DELETE knowledge item"""
        # Create knowledge item
        test_kb = {
            "agent_id": TEST_AGENT_ID,  # Required by model
            "type": "faq",
            "title": "TEST_FAQ_Title",
            "content": "This is test FAQ content for iteration 11 testing"
        }
        create_response = requests.post(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/knowledge", 
            headers=auth_headers, json=test_kb)
        
        assert create_response.status_code == 200
        created = create_response.json()
        assert created.get("id") is not None
        assert created.get("title") == test_kb["title"]
        kb_id = created["id"]
        print(f"✓ Created knowledge item with id: {kb_id}")
        
        # Verify it exists
        list_response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/knowledge", headers=auth_headers)
        items = list_response.json().get("items", [])
        assert any(item["id"] == kb_id for item in items)
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/knowledge/{kb_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        print(f"✓ Deleted knowledge item")
        
        # Verify it's gone
        verify_response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/knowledge", headers=auth_headers)
        remaining_items = verify_response.json().get("items", [])
        assert not any(item["id"] == kb_id for item in remaining_items)
        print(f"✓ Verified knowledge item deleted")


class TestFollowUpRulesCRUD:
    """Test Follow-up Rules CRUD operations"""
    
    def test_get_follow_up_rules(self, auth_headers):
        """GET /api/agents/{agent_id}/follow-up-rules returns rules list"""
        response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/follow-up-rules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert isinstance(data["rules"], list)
        print(f"✓ GET follow-up-rules returns rules list ({len(data['rules'])} rules)")
    
    def test_add_and_delete_follow_up_rule(self, auth_headers):
        """POST then DELETE follow-up rule"""
        # Create rule
        test_rule = {
            "agent_id": TEST_AGENT_ID,  # Required by model
            "trigger_type": "inactive_24h",
            "delay_hours": 48,
            "message_template": "TEST_Hello {name}, checking in!",
            "is_active": True
        }
        create_response = requests.post(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/follow-up-rules", 
            headers=auth_headers, json=test_rule)
        
        assert create_response.status_code == 200
        created = create_response.json()
        assert created.get("id") is not None
        assert created.get("trigger_type") == test_rule["trigger_type"]
        rule_id = created["id"]
        print(f"✓ Created follow-up rule with id: {rule_id}")
        
        # Verify it exists
        list_response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/follow-up-rules", headers=auth_headers)
        rules = list_response.json().get("rules", [])
        assert any(r["id"] == rule_id for r in rules)
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/follow-up-rules/{rule_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        print(f"✓ Deleted follow-up rule")
        
        # Verify it's gone
        verify_response = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}/follow-up-rules", headers=auth_headers)
        remaining_rules = verify_response.json().get("rules", [])
        assert not any(r["id"] == rule_id for r in remaining_rules)
        print(f"✓ Verified follow-up rule deleted")


class TestCompleteConfigFlow:
    """Test complete save flow - all configs together"""
    
    def test_save_all_configs_together(self, auth_headers):
        """PUT agent with all config types at once"""
        full_update = {
            "name": "Test Agent Updated",
            "tone": "professional",
            "emoji_level": 0.3,
            "verbosity_level": 0.5,
            "knowledge_instructions": "Always be helpful and professional.",
            "personality_config": {
                "proactivity": 0.5,
                "creativity": 0.5,
                "formality": 0.7,
                "flags": {
                    "auto_multilingual": True,
                    "remember_context": True,
                    "auto_escalate": True
                }
            },
            "integrations_config": {
                "google_calendar": {"enabled": False},
                "custom_api": {"enabled": False}
            },
            "channel_config": {
                "telegram": {"enabled": False},
                "whatsapp": {"enabled": False}
            },
            "escalation_rules": {
                "keywords": ["help", "human"],
                "sentiment_threshold": 0.3,
                "notify_operator": True
            },
            "follow_up_config": {
                "enabled": False,
                "max_follow_ups": 3,
                "cool_down_days": 7
            }
        }
        
        response = requests.put(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", 
            headers=auth_headers, json=full_update)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        
        # Verify all saved
        verify = requests.get(f"{BASE_URL}/api/agents/{TEST_AGENT_ID}", headers=auth_headers)
        assert verify.status_code == 200
        verify_data = verify.json()
        
        assert verify_data.get("tone") == "professional"
        assert verify_data.get("emoji_level") == 0.3
        assert verify_data.get("knowledge_instructions") == "Always be helpful and professional."
        assert verify_data.get("personality_config", {}).get("formality") == 0.7
        assert verify_data.get("escalation_rules", {}).get("notify_operator") == True
        assert verify_data.get("follow_up_config", {}).get("enabled") == False
        
        print(f"✓ Complete config save flow successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
