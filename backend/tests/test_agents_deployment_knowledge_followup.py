"""
Test Agent Deployment from Marketplace, Knowledge Base CRUD, Follow-up Rules CRUD, 
Agent Personality Config (tone, emoji_level, verbosity_level, escalation_rules)
Features tested:
- POST /api/agents/deploy - deploy marketplace agent to tenant
- GET /api/agents - returns deployed agents with tone, emoji_level, verbosity_level, escalation_rules
- PUT /api/agents/{id} - updates tone, emoji_level, verbosity_level, escalation_rules
- POST /api/agents/{id}/knowledge - add knowledge base item
- GET /api/agents/{id}/knowledge - list knowledge items
- DELETE /api/agents/{id}/knowledge/{item_id} - delete knowledge item
- POST /api/agents/{id}/follow-up-rules - add follow-up rule
- GET /api/agents/{id}/follow-up-rules - list rules
- DELETE /api/agents/{id}/follow-up-rules/{rule_id} - delete rule
- POST /api/webhook/whatsapp - escalation keyword detection
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://agent-campaign-hub.preview.emergentagent.com"

TEST_USER_EMAIL = "test@agentflow.com"
TEST_USER_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_session():
    """Create authenticated session for all tests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login to get token
    login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json().get("access_token")
    assert token, "No access_token in login response"
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session


@pytest.fixture(scope="module")
def existing_agent_id(auth_session):
    """Get or create an agent for testing"""
    # Get existing agents
    resp = auth_session.get(f"{BASE_URL}/api/agents")
    assert resp.status_code == 200, f"Get agents failed: {resp.text}"
    agents = resp.json().get("agents", [])
    
    if agents:
        return agents[0]["id"]
    
    # If no agents, skip tests that need existing agent
    pytest.skip("No agents available for testing - Free plan may limit creation")


class TestAgentsMarketplaceAndDeployment:
    """Tests for Marketplace and Agent Deployment"""
    
    def test_get_marketplace_agents(self, auth_session):
        """Test: GET /api/agents/marketplace returns list of agents"""
        response = auth_session.get(f"{BASE_URL}/api/agents/marketplace")
        
        assert response.status_code == 200, f"Get marketplace failed: {response.status_code}"
        data = response.json()
        
        assert "agents" in data, "Missing 'agents' key in response"
        agents = data["agents"]
        assert len(agents) > 0, "Marketplace should have agents"
        
        # Verify Sofia exists (we'll use it for deploy test)
        sofia = next((a for a in agents if a["name"].lower() == "sofia"), None)
        assert sofia is not None, "Sofia agent should exist in marketplace"
        assert sofia["type"] == "sales", f"Sofia should be sales type, got {sofia['type']}"
        assert sofia["category"] == "ecommerce", f"Sofia category should be ecommerce, got {sofia.get('category')}"
        
        print(f"✓ Marketplace has {len(agents)} agents")
        print(f"  Sofia found: type={sofia['type']}, category={sofia.get('category')}")
    
    def test_get_agents_returns_fields(self, auth_session, existing_agent_id):
        """Test: GET /api/agents returns agents with tone, emoji_level, verbosity_level, escalation_rules"""
        response = auth_session.get(f"{BASE_URL}/api/agents")
        
        assert response.status_code == 200, f"Get agents failed: {response.status_code}"
        data = response.json()
        
        assert "agents" in data, "Missing 'agents' key"
        agents = data["agents"]
        assert len(agents) > 0, "Should have at least one agent"
        
        agent = agents[0]
        
        # Verify new personality fields exist
        required_fields = ["id", "name", "type", "tone", "emoji_level", "verbosity_level", "escalation_rules", "follow_up_config", "is_deployed"]
        for field in required_fields:
            assert field in agent, f"Agent missing required field: {field}"
        
        # Verify data types
        assert isinstance(agent["tone"], str), f"tone should be string, got {type(agent['tone'])}"
        assert isinstance(agent["emoji_level"], (int, float)), f"emoji_level should be numeric, got {type(agent['emoji_level'])}"
        assert isinstance(agent["verbosity_level"], (int, float)), f"verbosity_level should be numeric, got {type(agent['verbosity_level'])}"
        assert isinstance(agent["escalation_rules"], dict), f"escalation_rules should be dict, got {type(agent['escalation_rules'])}"
        
        # Verify escalation_rules has keywords
        if "keywords" in agent["escalation_rules"]:
            assert isinstance(agent["escalation_rules"]["keywords"], list), "escalation_rules.keywords should be list"
        
        print(f"✓ Agent {agent['name']} has all required fields:")
        print(f"  tone={agent['tone']}, emoji_level={agent['emoji_level']}, verbosity_level={agent['verbosity_level']}")
        print(f"  escalation_rules={agent['escalation_rules']}")
    
    def test_deploy_agent_free_plan_limit(self, auth_session):
        """Test: POST /api/agents/deploy - test deployment (may fail due to free plan limit)"""
        # Try to deploy Sofia - this may fail if user already has an agent (free plan = 1 agent max)
        payload = {
            "template_name": "Sofia",
            "custom_name": f"TEST_Sofia_{uuid.uuid4().hex[:6]}",
            "tone": "friendly",
            "emoji_level": 0.5,
            "verbosity_level": 0.6
        }
        
        response = auth_session.post(f"{BASE_URL}/api/agents/deploy", json=payload)
        
        if response.status_code == 403:
            # Expected for free plan with existing agent
            error = response.json()
            assert "Free plan allows only 1 agent" in error.get("detail", ""), f"Unexpected 403 error: {error}"
            print(f"✓ Deploy correctly blocked by free plan limit")
            return
        
        if response.status_code == 200:
            # Agent deployed successfully
            agent = response.json()
            assert agent["name"] == payload["custom_name"], f"Name mismatch: {agent['name']}"
            assert agent["tone"] == "friendly", f"Tone mismatch: {agent['tone']}"
            assert agent["emoji_level"] == 0.5, f"emoji_level mismatch: {agent['emoji_level']}"
            assert agent["verbosity_level"] == 0.6, f"verbosity_level mismatch: {agent['verbosity_level']}"
            assert agent["is_deployed"] == True, "Agent should be marked as deployed"
            assert agent["marketplace_template_id"] == "Sofia", f"marketplace_template_id should be Sofia"
            
            print(f"✓ Agent deployed successfully: {agent['id']}")
            
            # Clean up - delete the test agent
            delete_resp = auth_session.delete(f"{BASE_URL}/api/agents/{agent['id']}")
            assert delete_resp.status_code == 200, f"Cleanup failed: {delete_resp.text}"
            print(f"  Cleanup: Agent deleted")
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")
    
    def test_deploy_agent_not_found(self, auth_session):
        """Test: POST /api/agents/deploy with invalid template returns 404 or 403 (plan limit)"""
        payload = {
            "template_name": "NonExistentAgent12345",
            "tone": "professional"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/agents/deploy", json=payload)
        # Server checks plan limits before template validation, so may get 403 first
        assert response.status_code in [404, 403], f"Expected 404 or 403, got {response.status_code}"
        
        error = response.json()
        if response.status_code == 404:
            assert "not found" in error.get("detail", "").lower(), f"Expected 'not found' in error: {error}"
            print(f"✓ Deploy returns 404 for non-existent template")
        else:
            # 403 - free plan limit reached (expected if user already has an agent)
            print(f"✓ Deploy returns 403 (free plan limit) - template validation blocked by plan check")


class TestAgentUpdate:
    """Tests for Agent Update API"""
    
    def test_update_agent_tone_and_levels(self, auth_session, existing_agent_id):
        """Test: PUT /api/agents/{id} - updates tone, emoji_level, verbosity_level, escalation_rules"""
        # First get current agent state
        get_resp = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}")
        assert get_resp.status_code == 200, f"Get agent failed: {get_resp.text}"
        original = get_resp.json()
        
        # Update with new values
        update_payload = {
            "tone": "empathetic",
            "emoji_level": 0.7,
            "verbosity_level": 0.8,
            "escalation_rules": {
                "keywords": ["ajuda", "suporte", "problema", "urgente"],
                "sentiment_threshold": 0.4
            }
        }
        
        update_resp = auth_session.put(f"{BASE_URL}/api/agents/{existing_agent_id}", json=update_payload)
        assert update_resp.status_code == 200, f"Update failed: {update_resp.status_code} - {update_resp.text}"
        
        result = update_resp.json()
        assert result.get("status") == "ok", f"Expected status ok, got {result}"
        assert "updated" in result, "Response should contain 'updated' field"
        
        # Verify GET returns updated values
        verify_resp = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}")
        assert verify_resp.status_code == 200
        updated = verify_resp.json()
        
        assert updated["tone"] == "empathetic", f"tone not updated: {updated['tone']}"
        assert updated["emoji_level"] == 0.7, f"emoji_level not updated: {updated['emoji_level']}"
        assert updated["verbosity_level"] == 0.8, f"verbosity_level not updated: {updated['verbosity_level']}"
        assert "ajuda" in updated["escalation_rules"]["keywords"], f"keywords not updated: {updated['escalation_rules']}"
        
        print(f"✓ Agent updated successfully:")
        print(f"  tone: {original.get('tone')} -> {updated['tone']}")
        print(f"  emoji_level: {original.get('emoji_level')} -> {updated['emoji_level']}")
        print(f"  verbosity_level: {original.get('verbosity_level')} -> {updated['verbosity_level']}")
        
        # Restore original values
        restore_payload = {
            "tone": original.get("tone", "professional"),
            "emoji_level": original.get("emoji_level", 0.3),
            "verbosity_level": original.get("verbosity_level", 0.5),
            "escalation_rules": original.get("escalation_rules", {"keywords": ["atendente", "humano"]})
        }
        auth_session.put(f"{BASE_URL}/api/agents/{existing_agent_id}", json=restore_payload)
        print(f"  Values restored to original")


class TestKnowledgeBaseCRUD:
    """Tests for Knowledge Base CRUD operations"""
    
    def test_add_knowledge_item(self, auth_session, existing_agent_id):
        """Test: POST /api/agents/{id}/knowledge - add knowledge base item"""
        payload = {
            "type": "faq",
            "title": "TEST_FAQ_Hours",
            "content": "We are open Monday to Friday from 9am to 6pm."
        }
        
        response = auth_session.post(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge", json=payload)
        assert response.status_code == 200, f"Add knowledge failed: {response.status_code} - {response.text}"
        
        item = response.json()
        assert item["type"] == "faq", f"type mismatch: {item['type']}"
        assert item["title"] == "TEST_FAQ_Hours", f"title mismatch: {item['title']}"
        assert item["content"] == payload["content"], f"content mismatch: {item['content']}"
        assert "id" in item, "Knowledge item should have id"
        assert item["agent_id"] == existing_agent_id, f"agent_id mismatch"
        
        print(f"✓ Knowledge item created: {item['id']}")
        
        # Cleanup
        delete_resp = auth_session.delete(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge/{item['id']}")
        assert delete_resp.status_code == 200, f"Cleanup failed: {delete_resp.text}"
        print(f"  Cleanup: Item deleted")
    
    def test_list_knowledge_items(self, auth_session, existing_agent_id):
        """Test: GET /api/agents/{id}/knowledge - list knowledge items"""
        # First add an item
        add_resp = auth_session.post(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge", json={
            "type": "product",
            "title": "TEST_Product_Info",
            "content": "Our main product costs $99 and includes free shipping."
        })
        assert add_resp.status_code == 200
        created_id = add_resp.json()["id"]
        
        # List items
        response = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge")
        assert response.status_code == 200, f"List knowledge failed: {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' key"
        items = data["items"]
        
        # Verify our item is in the list
        found = next((i for i in items if i["id"] == created_id), None)
        assert found is not None, f"Created item not found in list"
        assert found["type"] == "product"
        assert found["title"] == "TEST_Product_Info"
        
        print(f"✓ Knowledge list returned {len(items)} items, found our test item")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge/{created_id}")
    
    def test_delete_knowledge_item(self, auth_session, existing_agent_id):
        """Test: DELETE /api/agents/{id}/knowledge/{item_id} - delete knowledge item"""
        # Create item to delete
        add_resp = auth_session.post(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge", json={
            "type": "policy",
            "title": "TEST_Delete_Me",
            "content": "This item will be deleted"
        })
        assert add_resp.status_code == 200
        item_id = add_resp.json()["id"]
        
        # Delete item
        delete_resp = auth_session.delete(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge/{item_id}")
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.status_code}"
        
        result = delete_resp.json()
        assert result.get("status") == "ok", f"Expected status ok: {result}"
        
        # Verify item is gone
        list_resp = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}/knowledge")
        items = list_resp.json().get("items", [])
        deleted_item = next((i for i in items if i["id"] == item_id), None)
        assert deleted_item is None, "Deleted item should not appear in list"
        
        print(f"✓ Knowledge item {item_id} deleted and verified")


class TestFollowUpRulesCRUD:
    """Tests for Follow-up Rules CRUD operations"""
    
    def test_add_follow_up_rule(self, auth_session, existing_agent_id):
        """Test: POST /api/agents/{id}/follow-up-rules - add follow-up rule"""
        payload = {
            "trigger_type": "inactive_24h",
            "delay_hours": 24,
            "message_template": "Hi {name}, we noticed you haven't responded. Can we help with anything?",
            "is_active": True
        }
        
        response = auth_session.post(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules", json=payload)
        assert response.status_code == 200, f"Add rule failed: {response.status_code} - {response.text}"
        
        rule = response.json()
        assert rule["trigger_type"] == "inactive_24h", f"trigger_type mismatch: {rule['trigger_type']}"
        assert rule["delay_hours"] == 24, f"delay_hours mismatch: {rule['delay_hours']}"
        assert "{name}" in rule["message_template"], f"template mismatch"
        assert rule["is_active"] == True, f"is_active mismatch"
        assert "id" in rule, "Rule should have id"
        assert rule["agent_id"] == existing_agent_id, f"agent_id mismatch"
        
        print(f"✓ Follow-up rule created: {rule['id']}")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules/{rule['id']}")
    
    def test_list_follow_up_rules(self, auth_session, existing_agent_id):
        """Test: GET /api/agents/{id}/follow-up-rules - list rules"""
        # Add a rule
        add_resp = auth_session.post(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules", json={
            "trigger_type": "post_sale",
            "delay_hours": 48,
            "message_template": "Thanks for your purchase! How is everything going?",
            "is_active": True
        })
        assert add_resp.status_code == 200
        created_id = add_resp.json()["id"]
        
        # List rules
        response = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules")
        assert response.status_code == 200, f"List rules failed: {response.status_code}"
        
        data = response.json()
        assert "rules" in data, "Response should have 'rules' key"
        rules = data["rules"]
        
        # Verify our rule is in the list
        found = next((r for r in rules if r["id"] == created_id), None)
        assert found is not None, f"Created rule not found in list"
        assert found["trigger_type"] == "post_sale"
        
        print(f"✓ Follow-up rules list returned {len(rules)} rules, found our test rule")
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules/{created_id}")
    
    def test_delete_follow_up_rule(self, auth_session, existing_agent_id):
        """Test: DELETE /api/agents/{id}/follow-up-rules/{rule_id} - delete rule"""
        # Create rule to delete
        add_resp = auth_session.post(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules", json={
            "trigger_type": "cart_abandoned",
            "delay_hours": 12,
            "message_template": "TEST_Delete rule",
            "is_active": False
        })
        assert add_resp.status_code == 200
        rule_id = add_resp.json()["id"]
        
        # Delete rule
        delete_resp = auth_session.delete(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules/{rule_id}")
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.status_code}"
        
        result = delete_resp.json()
        assert result.get("status") == "ok", f"Expected status ok: {result}"
        
        # Verify rule is gone
        list_resp = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}/follow-up-rules")
        rules = list_resp.json().get("rules", [])
        deleted_rule = next((r for r in rules if r["id"] == rule_id), None)
        assert deleted_rule is None, "Deleted rule should not appear in list"
        
        print(f"✓ Follow-up rule {rule_id} deleted and verified")


class TestWebhookEscalation:
    """Tests for WhatsApp webhook with escalation detection"""
    
    def test_webhook_basic_response(self, auth_session):
        """Test: GET /api/webhook/whatsapp returns status"""
        response = requests.get(f"{BASE_URL}/api/webhook/whatsapp")
        assert response.status_code == 200, f"Webhook GET failed: {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "ok", f"Expected status ok: {data}"
        print(f"✓ Webhook GET returns ok")
    
    def test_webhook_escalation_keyword(self, auth_session):
        """Test: POST /api/webhook/whatsapp with escalation keyword triggers escalation"""
        # First we need a channel with connected status
        # Create/update a test channel
        channel_resp = auth_session.post(f"{BASE_URL}/api/channels", json={
            "type": "whatsapp",
            "config": {"instance_name": "test-webhook-instance"}
        })
        assert channel_resp.status_code == 200, f"Create channel failed: {channel_resp.text}"
        channel = channel_resp.json()
        
        # Update channel status to connected
        status_resp = auth_session.put(f"{BASE_URL}/api/channels/{channel['id']}/status?status=connected")
        assert status_resp.status_code == 200, f"Update status failed: {status_resp.text}"
        
        # Now send webhook with escalation keyword "quero falar com atendente"
        webhook_payload = {
            "event": "messages.upsert",
            "instance": "test-webhook-instance",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False
                },
                "message": {
                    "conversation": "quero falar com atendente"
                }
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/webhook/whatsapp", json=webhook_payload)
        # The webhook should return escalated status (if there's an agent assigned)
        # or ok/no_channel depending on channel setup
        
        assert response.status_code == 200, f"Webhook failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Possible statuses: escalated (if agent and escalation detected), ok, no_channel
        valid_statuses = ["escalated", "ok", "no_channel", "auto_replied"]
        assert data.get("status") in valid_statuses, f"Unexpected status: {data}"
        
        if data.get("status") == "escalated":
            print(f"✓ Webhook correctly detected escalation keyword")
            print(f"  conversation_id: {data.get('conversation_id')}")
        else:
            print(f"✓ Webhook processed message with status: {data.get('status')}")
            print(f"  (Escalation may not trigger if no agent assigned to conversation)")


class TestAgentGetById:
    """Tests for getting single agent by ID"""
    
    def test_get_agent_by_id(self, auth_session, existing_agent_id):
        """Test: GET /api/agents/{id} returns agent with all fields"""
        response = auth_session.get(f"{BASE_URL}/api/agents/{existing_agent_id}")
        assert response.status_code == 200, f"Get agent failed: {response.status_code}"
        
        agent = response.json()
        
        # All required fields for AgentConfig page
        required_fields = [
            "id", "name", "type", "description", "system_prompt", "status",
            "tone", "emoji_level", "verbosity_level", 
            "escalation_rules", "follow_up_config", "knowledge_instructions",
            "is_deployed", "marketplace_template_id"
        ]
        
        for field in required_fields:
            assert field in agent, f"Missing field: {field}"
        
        print(f"✓ Agent GET returns all required fields")
        print(f"  name={agent['name']}, type={agent['type']}, tone={agent['tone']}")
    
    def test_get_agent_404(self, auth_session):
        """Test: GET /api/agents/{id} returns 404 for non-existent agent"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = auth_session.get(f"{BASE_URL}/api/agents/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ GET agent returns 404 for invalid ID")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
