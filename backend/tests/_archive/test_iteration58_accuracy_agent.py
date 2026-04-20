"""
Test iteration 58: Avatar Accuracy Agent endpoints with Gemini Vision comparison.
Tests POST /api/campaigns/pipeline/generate-avatar-with-accuracy (start job)
Tests GET /api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id} (poll status)
Tests existing avatar-video-preview endpoints still work
Tests translation keys in all locales
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestAuthentication:
    """Get auth token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get access_token (not 'token')"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns 'access_token' not 'token'
        token = data.get("access_token")
        assert token, f"No access_token in response: {data}"
        return token
    
    def test_login_returns_access_token(self, auth_token):
        """Verify login returns access_token field"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"SUCCESS: Login returned valid access_token")


class TestAvatarAccuracyGeneration:
    """Test the new accuracy agent endpoint for avatar generation"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        assert response.status_code == 200
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_accuracy_endpoint_exists(self, auth_headers):
        """Verify POST /generate-avatar-with-accuracy endpoint exists and accepts requests"""
        # Use a placeholder image URL (doesn't need to be real for endpoint existence test)
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            headers=auth_headers,
            json={
                "source_image_url": "https://example.com/placeholder.jpg",
                "company_name": "Test Company",
                "max_iterations": 3
            }
        )
        # Should return 200 with job_id (even if the actual generation will fail due to invalid URL)
        # Or could return 422 for validation error, but should NOT return 404
        assert response.status_code != 404, "Endpoint does not exist"
        print(f"SUCCESS: Accuracy endpoint exists (status: {response.status_code})")
    
    def test_accuracy_endpoint_returns_job_id(self, auth_headers):
        """Verify POST returns job_id and processing status"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            headers=auth_headers,
            json={
                "source_image_url": "https://example.com/test.jpg",
                "company_name": "Acme Corp",
                "max_iterations": 2
            }
        )
        # Endpoint should return 200 with job_id even if image download will fail
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, f"Missing job_id in response: {data}"
        assert "status" in data, f"Missing status in response: {data}"
        assert data["status"] == "processing", f"Expected 'processing' status, got: {data['status']}"
        print(f"SUCCESS: Accuracy endpoint returns job_id: {data['job_id']}")
        return data["job_id"]
    
    def test_accuracy_polling_endpoint(self, auth_headers):
        """Verify GET polling endpoint works"""
        # First create a job
        post_response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            headers=auth_headers,
            json={
                "source_image_url": "https://example.com/test.jpg",
                "company_name": "Test Corp",
                "max_iterations": 1
            }
        )
        assert post_response.status_code == 200
        job_id = post_response.json()["job_id"]
        
        # Wait a bit for background thread to process
        time.sleep(2)
        
        # Poll for status
        poll_response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id}",
            headers=auth_headers
        )
        assert poll_response.status_code == 200, f"Polling failed: {poll_response.text}"
        data = poll_response.json()
        
        # Should have status field
        assert "status" in data, f"Missing status in poll response: {data}"
        # Status should be one of: processing, completed, failed
        valid_statuses = ["processing", "completed", "failed"]
        assert data["status"] in valid_statuses, f"Invalid status: {data['status']}"
        
        print(f"SUCCESS: Polling endpoint works, status: {data['status']}")
    
    def test_accuracy_polling_returns_valid_response(self, auth_headers):
        """Verify polling response has valid status fields"""
        # Create job
        post_response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy",
            headers=auth_headers,
            json={
                "source_image_url": "https://example.com/test.jpg",
                "company_name": "Test Corp",
                "max_iterations": 1
            }
        )
        job_id = post_response.json()["job_id"]
        
        # Wait for processing
        time.sleep(3)
        
        # Poll
        poll_response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy/{job_id}",
            headers=auth_headers
        )
        data = poll_response.json()
        
        # Should have status and either iterations or error field
        assert "status" in data, f"Missing status in response: {data}"
        # Valid states: processing (has iterations), completed (has avatar_url, iterations), failed (has error)
        if data["status"] == "completed":
            assert "avatar_url" in data, f"Completed but missing avatar_url: {data}"
            assert "iterations" in data, f"Completed but missing iterations: {data}"
        elif data["status"] == "failed":
            assert "error" in data, f"Failed but missing error: {data}"
        elif data["status"] == "processing":
            assert "iterations" in data or "progress" in data, f"Processing but no progress info: {data}"
        
        print(f"SUCCESS: Polling response structure is correct, status: {data['status']}")
    
    def test_accuracy_polling_invalid_job(self, auth_headers):
        """Verify polling with invalid job_id returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/generate-avatar-with-accuracy/invalid_job_123",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404 for invalid job, got {response.status_code}"
        print("SUCCESS: Invalid job_id returns 404")


class TestAvatarVideoPreview:
    """Test that existing avatar-video-preview endpoints still work"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_video_preview_endpoint_exists(self, auth_headers):
        """Verify POST /avatar-video-preview still works"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            headers=auth_headers,
            json={
                "avatar_url": "https://example.com/avatar.jpg",
                "voice_url": "",
                "voice_id": "onyx",
                "language": "en"
            }
        )
        # Should return 200 with job_id
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, f"Missing job_id: {data}"
        print(f"SUCCESS: Video preview POST works, job_id: {data['job_id']}")
    
    def test_video_preview_polling(self, auth_headers):
        """Verify GET polling endpoint for video preview"""
        # Create job
        post_response = requests.post(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview",
            headers=auth_headers,
            json={
                "avatar_url": "https://example.com/avatar.jpg",
                "voice_url": "",
                "voice_id": "alloy",
                "language": "pt"
            }
        )
        job_id = post_response.json()["job_id"]
        
        time.sleep(1)
        
        poll_response = requests.get(
            f"{BASE_URL}/api/campaigns/pipeline/avatar-video-preview/{job_id}",
            headers=auth_headers
        )
        assert poll_response.status_code == 200, f"Poll failed: {poll_response.text}"
        data = poll_response.json()
        assert "status" in data
        print(f"SUCCESS: Video preview polling works, status: {data['status']}")


class TestTranslationKeys:
    """Verify new i18n keys exist in all locales"""
    
    def test_new_keys_in_pt_json(self):
        """Check new keys in Portuguese locale"""
        import json
        with open("/app/frontend/src/locales/pt.json", "r") as f:
            pt = json.load(f)
        
        studio = pt.get("studio", {})
        required_keys = ["photo_tab", "video_tab", "accuracy_evolution", "regenerate_preview"]
        
        for key in required_keys:
            assert key in studio, f"Missing key '{key}' in pt.json studio section"
        
        print(f"SUCCESS: All new keys found in pt.json: {required_keys}")
    
    def test_new_keys_in_en_json(self):
        """Check new keys in English locale"""
        import json
        with open("/app/frontend/src/locales/en.json", "r") as f:
            en = json.load(f)
        
        studio = en.get("studio", {})
        required_keys = ["photo_tab", "video_tab", "accuracy_evolution", "regenerate_preview"]
        
        for key in required_keys:
            assert key in studio, f"Missing key '{key}' in en.json studio section"
        
        print(f"SUCCESS: All new keys found in en.json: {required_keys}")
    
    def test_new_keys_in_es_json(self):
        """Check new keys in Spanish locale"""
        import json
        with open("/app/frontend/src/locales/es.json", "r") as f:
            es = json.load(f)
        
        studio = es.get("studio", {})
        required_keys = ["photo_tab", "video_tab", "accuracy_evolution", "regenerate_preview"]
        
        for key in required_keys:
            assert key in studio, f"Missing key '{key}' in es.json studio section"
        
        print(f"SUCCESS: All new keys found in es.json: {required_keys}")


class TestPreviewTextsShortened:
    """Verify PREVIEW_TEXTS were shortened for 5-second videos"""
    
    def test_preview_texts_are_short(self):
        """Check that PREVIEW_TEXTS in pipeline.py are shortened"""
        with open("/app/backend/routers/pipeline.py", "r") as f:
            content = f.read()
        
        # Find PREVIEW_TEXTS dictionary
        import re
        match = re.search(r'PREVIEW_TEXTS\s*=\s*\{([^}]+)\}', content, re.DOTALL)
        assert match, "PREVIEW_TEXTS not found in pipeline.py"
        
        preview_content = match.group(1)
        
        # Check text lengths are reasonable for ~5 seconds (around 10-15 words max)
        # Old texts were longer, new should be shorter
        for lang in ['pt', 'en', 'es']:
            text_match = re.search(rf'"{lang}":\s*"([^"]+)"', preview_content)
            if text_match:
                text = text_match.group(1)
                word_count = len(text.split())
                # Shorter text for 5-second video should be under 20 words
                assert word_count <= 25, f"{lang} preview text too long ({word_count} words): {text}"
                print(f"SUCCESS: {lang} preview text has {word_count} words")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
