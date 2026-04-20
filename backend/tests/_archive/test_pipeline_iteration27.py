"""
Test iteration 27: Pipeline API with media_formats and address field
Tests:
- P0: POST /api/campaigns/pipeline accepts media_formats and address in contact_info
- P2: Verify music directory has 5 mood-categorized tracks
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPipelineAPI:
    """Tests for pipeline creation with new fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@agentflow.com",
            "password": "password123"
        })
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_pipeline_accepts_media_formats(self):
        """P0: Pipeline API should accept media_formats field"""
        # Auth is already setup in fixture
        
        # Create pipeline with media_formats
        payload = {
            "briefing": "Test campaign for iteration 27",
            "campaign_name": "TEST_Media_Format_Campaign",
            "mode": "semi_auto",
            "platforms": ["whatsapp", "instagram", "facebook"],
            "campaign_language": "en",
            "context": {"company": "Test Company"},
            "contact_info": {
                "phone": "+1 555-123-4567",
                "website": "www.test.com",
                "email": "test@test.com",
                "address": "123 Test Street, City, State"
            },
            "uploaded_assets": [],
            "media_formats": {
                "whatsapp": {"imgRatio": "1:1", "vidRatio": "9:16", "imgSize": "1024x1024", "vidSize": "768x1344"},
                "instagram": {"imgRatio": "1:1", "vidRatio": "9:16", "imgSize": "1024x1024", "vidSize": "768x1344"},
                "facebook": {"imgRatio": "1:1", "vidRatio": "16:9", "imgSize": "1024x1024", "vidSize": "1280x720"}
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/campaigns/pipeline", json=payload)
        
        # Should return 200/201 - the API should accept the new fields
        assert response.status_code in [200, 201], f"Pipeline creation failed: {response.status_code} - {response.text}"
        
        data = response.json()
        # Verify pipeline was created
        assert "id" in data, "Pipeline response should contain id"
        
        # Clean up - delete the pipeline
        pipeline_id = data.get("id")
        if pipeline_id:
            self.session.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}")
        
        print(f"PASSED: Pipeline API accepts media_formats field")
    
    def test_pipeline_accepts_address_in_contact_info(self):
        """P0: Pipeline API should accept address field in contact_info"""
        # Auth is already setup in fixture
        
        # Create pipeline with address in contact_info
        payload = {
            "briefing": "Test campaign with address",
            "campaign_name": "TEST_Address_Field_Campaign",
            "mode": "semi_auto",
            "platforms": ["whatsapp"],
            "contact_info": {
                "phone": "+1 555-111-2222",
                "website": "www.example.com",
                "email": "hello@example.com",
                "address": "456 Business Ave, Suite 100, Metro City"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/campaigns/pipeline", json=payload)
        
        assert response.status_code in [200, 201], f"Pipeline creation with address failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "id" in data, "Pipeline response should contain id"
        
        # Verify the address is stored in result
        pipeline_id = data.get("id")
        
        # Fetch pipeline to verify address is stored
        get_resp = self.session.get(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}")
        if get_resp.status_code == 200:
            pipeline_data = get_resp.json()
            contact_info = pipeline_data.get("result", {}).get("contact_info", {})
            assert contact_info.get("address") == "456 Business Ave, Suite 100, Metro City", \
                f"Address not stored correctly: {contact_info}"
            print(f"PASSED: Address stored correctly in pipeline result")
        
        # Clean up
        if pipeline_id:
            self.session.delete(f"{BASE_URL}/api/campaigns/pipeline/{pipeline_id}")
        
        print(f"PASSED: Pipeline API accepts address field in contact_info")


class TestMusicDirectory:
    """Tests for music directory with mood-categorized tracks"""
    
    def test_music_directory_has_5_tracks(self):
        """P2: Verify music directory has 5 mood-categorized tracks"""
        music_dir = "/app/backend/assets/music"
        
        expected_tracks = ["upbeat.mp3", "energetic.mp3", "emotional.mp3", "cinematic.mp3", "corporate.mp3"]
        
        # Check directory exists
        assert os.path.isdir(music_dir), f"Music directory not found: {music_dir}"
        
        # List files
        files = os.listdir(music_dir)
        mp3_files = [f for f in files if f.endswith('.mp3')]
        
        # Verify all expected tracks exist
        for track in expected_tracks:
            assert track in mp3_files, f"Missing music track: {track}"
            filepath = os.path.join(music_dir, track)
            assert os.path.getsize(filepath) > 0, f"Music file is empty: {track}"
        
        assert len(mp3_files) >= 5, f"Expected at least 5 music tracks, found {len(mp3_files)}"
        
        print(f"PASSED: Music directory has {len(mp3_files)} tracks: {mp3_files}")


class TestPipelineModel:
    """Tests for PipelineCreate model validation"""
    
    def test_pipeline_model_fields(self):
        """Verify PipelineCreate model has media_formats field"""
        import sys
        sys.path.insert(0, '/app/backend')
        
        from routers.pipeline import PipelineCreate
        
        # Check model fields
        fields = PipelineCreate.__annotations__
        
        assert 'media_formats' in fields, "PipelineCreate model should have media_formats field"
        assert 'contact_info' in fields, "PipelineCreate model should have contact_info field"
        
        # Create instance with all fields
        instance = PipelineCreate(
            briefing="Test",
            campaign_name="Test",
            media_formats={"whatsapp": {"imgRatio": "1:1"}}
        )
        
        assert instance.media_formats == {"whatsapp": {"imgRatio": "1:1"}}
        
        print("PASSED: PipelineCreate model has media_formats field")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
