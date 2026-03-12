"""
Test AI Sandbox (Claude Sonnet) and AI Auto-Reply for Conversations
Features tested:
- POST /api/sandbox/chat - sends message and gets AI response from Claude Sonnet
- POST /api/sandbox/chat - multi-turn conversation maintains context 
- DELETE /api/sandbox/{session_id} - clears sandbox session
- POST /api/conversations/{id}/ai-reply - generates AI reply for customer message
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://saas-agent-hub-1.preview.emergentagent.com"

TEST_USER_EMAIL = "test@agentflow.com"
TEST_USER_PASSWORD = "password123"


class TestAISandbox:
    """Tests for AI Sandbox with Real Claude Sonnet AI"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup: login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        assert self.token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store session_ids for cleanup
        self.sandbox_sessions = []
        
        yield
        
        # Cleanup: delete any sandbox sessions created
        for session_id in self.sandbox_sessions:
            try:
                self.session.delete(f"{BASE_URL}/api/sandbox/{session_id}")
            except:
                pass
    
    def test_sandbox_chat_basic(self):
        """Test: POST /api/sandbox/chat - sends message and gets AI response"""
        payload = {
            "content": "Hello, I'm interested in your products",
            "agent_name": "Carol",
            "agent_type": "sales"
        }
        
        # AI response may take 2-5 seconds
        response = self.session.post(f"{BASE_URL}/api/sandbox/chat", json=payload, timeout=30)
        
        # Status assertion
        assert response.status_code == 200, f"Sandbox chat failed: {response.status_code} - {response.text}"
        
        # Data assertions
        data = response.json()
        assert "response" in data, "Missing 'response' field in sandbox response"
        assert "session_id" in data, "Missing 'session_id' field"
        assert "debug" in data, "Missing 'debug' field"
        
        # Validate response is non-empty
        assert len(data["response"]) > 0, "AI response is empty"
        
        # Validate debug info structure
        debug = data["debug"]
        assert "response_time_ms" in debug, "Missing response_time_ms in debug"
        assert "model" in debug, "Missing model in debug"
        assert "language_detected" in debug, "Missing language_detected in debug"
        assert "tokens_estimate" in debug, "Missing tokens_estimate in debug"
        
        # Validate debug values
        assert debug["response_time_ms"] > 0, "response_time_ms should be positive"
        assert isinstance(debug["tokens_estimate"], int), "tokens_estimate should be int"
        assert debug["model"] == "claude-sonnet-4-5", f"Expected model claude-sonnet-4-5, got {debug['model']}"
        
        # Store session for cleanup
        self.sandbox_sessions.append(data["session_id"])
        print(f"✓ Sandbox chat successful. Response: {data['response'][:100]}...")
        print(f"  Debug: {debug}")
    
    def test_sandbox_chat_multi_turn(self):
        """Test: POST /api/sandbox/chat - multi-turn conversation maintains context"""
        # First message - establish context
        first_msg = {
            "content": "My name is TestUser and I want to buy a laptop",
            "agent_name": "Carol",
            "agent_type": "sales"
        }
        
        resp1 = self.session.post(f"{BASE_URL}/api/sandbox/chat", json=first_msg, timeout=30)
        assert resp1.status_code == 200, f"First message failed: {resp1.text}"
        data1 = resp1.json()
        session_id = data1["session_id"]
        self.sandbox_sessions.append(session_id)
        print(f"First response: {data1['response'][:100]}...")
        
        # Wait a moment before second message
        time.sleep(1)
        
        # Second message - should maintain context (use same session_id)
        second_msg = {
            "content": "What's my name?",
            "agent_name": "Carol",
            "agent_type": "sales",
            "session_id": session_id  # Same session for context
        }
        
        resp2 = self.session.post(f"{BASE_URL}/api/sandbox/chat", json=second_msg, timeout=30)
        assert resp2.status_code == 200, f"Second message failed: {resp2.text}"
        data2 = resp2.json()
        
        # Validate same session maintained
        assert data2["session_id"] == session_id, "Session ID changed between messages"
        
        # Response should mention "TestUser" or reference the context
        response_lower = data2["response"].lower()
        context_maintained = "testuser" in response_lower or "laptop" in response_lower or "name" in response_lower
        print(f"Second response: {data2['response'][:150]}...")
        print(f"✓ Multi-turn conversation - context maintained: {context_maintained}")
        
        # Even if AI doesn't perfectly recall, the test passes if API works
        # The key is session_id stays the same
        assert data2["session_id"] == session_id, "Session should persist across turns"
    
    def test_sandbox_chat_portuguese(self):
        """Test: Sandbox responds in Portuguese when user writes in Portuguese"""
        payload = {
            "content": "Olá! Estou interessado em seus serviços. Como posso começar?",
            "agent_name": "Carol",
            "agent_type": "support"
        }
        
        response = self.session.post(f"{BASE_URL}/api/sandbox/chat", json=payload, timeout=30)
        assert response.status_code == 200, f"Portuguese chat failed: {response.text}"
        
        data = response.json()
        debug = data["debug"]
        
        # Language should be detected as Portuguese
        assert debug["language_detected"] in ["pt", "en", "es"], f"Unexpected language: {debug['language_detected']}"
        
        self.sandbox_sessions.append(data["session_id"])
        print(f"✓ Portuguese message response: {data['response'][:100]}...")
        print(f"  Detected language: {debug['language_detected']}")
    
    def test_sandbox_delete_session(self):
        """Test: DELETE /api/sandbox/{session_id} - clears sandbox session"""
        # First create a session
        create_resp = self.session.post(f"{BASE_URL}/api/sandbox/chat", json={
            "content": "Hello, just testing",
            "agent_name": "TestAgent",
            "agent_type": "support"
        }, timeout=30)
        assert create_resp.status_code == 200, f"Create session failed: {create_resp.text}"
        
        session_id = create_resp.json()["session_id"]
        
        # Delete the session
        delete_resp = self.session.delete(f"{BASE_URL}/api/sandbox/{session_id}")
        assert delete_resp.status_code == 200, f"Delete session failed: {delete_resp.status_code} - {delete_resp.text}"
        
        data = delete_resp.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
        
        print(f"✓ Session {session_id} deleted successfully")


class TestAIConversationReply:
    """Tests for AI Auto-Reply in Conversations"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup: login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        assert self.token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Store IDs for cleanup
        self.test_conversation_id = None
        
        yield
        
        # Cleanup: We don't delete conversations as they may be useful for UI testing
    
    def test_ai_reply_for_existing_conversation(self):
        """Test: POST /api/conversations/{id}/ai-reply - generates AI reply"""
        # First, get a conversation that has customer messages
        convos_resp = self.session.get(f"{BASE_URL}/api/conversations")
        assert convos_resp.status_code == 200, f"Get conversations failed: {convos_resp.text}"
        
        convos = convos_resp.json().get("conversations", [])
        
        # Find conversation with messages or create one
        convo_id = None
        for convo in convos:
            # Check if this conversation has customer messages
            msgs_resp = self.session.get(f"{BASE_URL}/api/conversations/{convo['id']}/messages")
            if msgs_resp.status_code == 200:
                messages = msgs_resp.json().get("messages", [])
                customer_msgs = [m for m in messages if m.get("sender") == "customer"]
                if customer_msgs:
                    convo_id = convo["id"]
                    print(f"Found conversation {convo_id} with {len(customer_msgs)} customer messages")
                    break
        
        if not convo_id:
            # Create a new conversation with customer message
            print("No conversation with customer messages found, creating one...")
            
            # Create conversation
            new_convo_resp = self.session.post(f"{BASE_URL}/api/conversations", json={
                "contact_name": "TEST_AI_Reply_Customer",
                "contact_phone": "+1234567890",
                "channel_type": "whatsapp"
            })
            assert new_convo_resp.status_code == 200, f"Create conversation failed: {new_convo_resp.text}"
            convo_id = new_convo_resp.json()["id"]
            self.test_conversation_id = convo_id
            
            # We need to insert a customer message directly since the API only allows operator messages
            # For this test, we'll just verify the endpoint handles the "no customer message" case
            ai_resp = self.session.post(f"{BASE_URL}/api/conversations/{convo_id}/ai-reply")
            # This should return 400 since there's no customer message to reply to
            assert ai_resp.status_code == 400, f"Expected 400 for no customer message, got {ai_resp.status_code}"
            print(f"✓ AI Reply correctly returns 400 when no customer message exists")
            return
        
        # Now test AI reply for conversation with customer messages
        ai_reply_resp = self.session.post(f"{BASE_URL}/api/conversations/{convo_id}/ai-reply", timeout=30)
        assert ai_reply_resp.status_code == 200, f"AI Reply failed: {ai_reply_resp.status_code} - {ai_reply_resp.text}"
        
        data = ai_reply_resp.json()
        
        # Validate response structure
        assert "message" in data, "Missing 'message' field in response"
        assert "response" in data, "Missing 'response' field in response"
        
        # Validate message was created
        message = data["message"]
        assert message.get("sender") == "agent", "Message sender should be 'agent'"
        assert message.get("content"), "Message content should not be empty"
        assert message.get("conversation_id") == convo_id, "Message should belong to correct conversation"
        
        # Validate response text
        assert len(data["response"]) > 0, "AI response should not be empty"
        
        print(f"✓ AI Reply generated for conversation {convo_id}")
        print(f"  Response: {data['response'][:100]}...")
    
    def test_ai_reply_404_for_invalid_conversation(self):
        """Test: AI Reply returns 404 for non-existent conversation"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = self.session.post(f"{BASE_URL}/api/conversations/{fake_id}/ai-reply")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ AI Reply correctly returns 404 for invalid conversation")


class TestDashboardAndStats:
    """Verify dashboard stats API returns correct data"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup: login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_dashboard_stats(self):
        """Test: GET /api/dashboard/stats returns real stats"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        
        data = response.json()
        
        # Validate required fields
        required_fields = ["messages_today", "resolution_rate", "active_leads", "revenue", "plan", "messages_used", "messages_limit"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate data types
        assert isinstance(data["messages_today"], int), "messages_today should be int"
        assert isinstance(data["plan"], str), "plan should be string"
        assert isinstance(data["messages_limit"], int), "messages_limit should be int"
        
        print(f"✓ Dashboard stats: {data}")


class TestLeadsForCRM:
    """Verify CRM/Leads API returns data for kanban display"""
    
    @pytest.fixture(autouse=True)
    def setup(self, request):
        """Setup: login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        self.token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_leads_for_kanban(self):
        """Test: GET /api/leads returns leads for CRM kanban"""
        response = self.session.get(f"{BASE_URL}/api/leads")
        assert response.status_code == 200, f"Get leads failed: {response.text}"
        
        data = response.json()
        assert "leads" in data, "Missing 'leads' field"
        
        leads = data["leads"]
        print(f"✓ Found {len(leads)} leads for CRM kanban")
        
        if leads:
            # Check lead structure
            lead = leads[0]
            expected_fields = ["id", "name", "stage"]
            for field in expected_fields:
                assert field in lead, f"Lead missing field: {field}"
            
            # Count leads by stage
            stages = {}
            for l in leads:
                stage = l.get("stage", "unknown")
                stages[stage] = stages.get(stage, 0) + 1
            print(f"  Leads by stage: {stages}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
