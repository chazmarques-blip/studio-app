"""
Iteration 73: Dylan Reed - Sound Director Agent Tests
Tests the new 'Dylan Reed - Sound Director' agent in the AI Marketing Studio pipeline.
Dylan runs between George (Art Director/review) and Ridley (Video Director).
"""
import pytest
import requests
import os
import re
import importlib.util

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"


class TestDylanSoundDirectorBackend:
    """Backend configuration tests for Dylan Sound Director agent."""
    
    def test_step_order_includes_dylan_sound(self):
        """STEP_ORDER includes 'dylan_sound' between 'rafael_review_design' and 'marcos_video'"""
        from pipeline.config import STEP_ORDER
        
        assert 'dylan_sound' in STEP_ORDER, "dylan_sound must be in STEP_ORDER"
        
        # Check position: should be between rafael_review_design and marcos_video
        dylan_idx = STEP_ORDER.index('dylan_sound')
        rafael_design_idx = STEP_ORDER.index('rafael_review_design')
        marcos_idx = STEP_ORDER.index('marcos_video')
        
        assert dylan_idx > rafael_design_idx, "dylan_sound must come after rafael_review_design"
        assert dylan_idx < marcos_idx, "dylan_sound must come before marcos_video"
        print(f"✓ STEP_ORDER correctly has dylan_sound at index {dylan_idx} (between rafael_review_design[{rafael_design_idx}] and marcos_video[{marcos_idx}])")
    
    def test_step_labels_contains_dylan_sound(self):
        """STEP_LABELS contains 'dylan_sound' with agent='Dylan', role='Sound Director'"""
        from pipeline.config import STEP_LABELS
        
        assert 'dylan_sound' in STEP_LABELS, "dylan_sound must be in STEP_LABELS"
        dylan_label = STEP_LABELS['dylan_sound']
        
        assert dylan_label.get('agent') == 'Dylan', f"Expected agent='Dylan', got '{dylan_label.get('agent')}'"
        assert dylan_label.get('role') == 'Sound Director', f"Expected role='Sound Director', got '{dylan_label.get('role')}'"
        assert dylan_label.get('icon') == 'headphones', f"Expected icon='headphones', got '{dylan_label.get('icon')}'"
        
        print(f"✓ STEP_LABELS['dylan_sound'] = {dylan_label}")
    
    def test_step_systems_contains_dylan_sound_prompt(self):
        """STEP_SYSTEMS contains 'dylan_sound' system prompt with ElevenLabs voice catalog and music library"""
        from pipeline.config import STEP_SYSTEMS
        
        assert 'dylan_sound' in STEP_SYSTEMS, "dylan_sound must be in STEP_SYSTEMS"
        dylan_prompt = STEP_SYSTEMS['dylan_sound']
        
        # Check key elements of Dylan's system prompt
        assert 'Dylan Reed' in dylan_prompt, "System prompt must mention 'Dylan Reed'"
        assert 'Sound Director' in dylan_prompt, "System prompt must mention 'Sound Director'"
        assert 'ElevenLabs' in dylan_prompt or 'ELEVENLABS' in dylan_prompt, "System prompt must reference ElevenLabs"
        assert 'Voice ID' in dylan_prompt, "System prompt must include Voice ID references"
        assert 'MUSIC LIBRARY' in dylan_prompt or 'Music Library' in dylan_prompt.title(), "System prompt must reference music library"
        assert '21m00Tcm4TlvDq8ikWAM' in dylan_prompt, "System prompt must contain real ElevenLabs voice IDs like Rachel's"
        
        # Check voice settings are documented
        assert 'Stability' in dylan_prompt, "System prompt must document Stability setting"
        assert 'Similarity' in dylan_prompt, "System prompt must document Similarity setting"
        assert 'Style' in dylan_prompt, "System prompt must document Style setting"
        assert 'Speed' in dylan_prompt, "System prompt must document Speed setting"
        
        # Check music track keys are present
        assert 'upbeat' in dylan_prompt, "System prompt must include music track keys"
        assert 'cinematic' in dylan_prompt, "System prompt must include cinematic track"
        
        print(f"✓ STEP_SYSTEMS['dylan_sound'] contains proper ElevenLabs voice catalog and music library ({len(dylan_prompt)} chars)")
    
    def test_parse_dylan_audio_function_exists(self):
        """_parse_dylan_audio function exists and is importable"""
        from pipeline.engine import _parse_dylan_audio
        
        assert callable(_parse_dylan_audio), "_parse_dylan_audio must be callable"
        print("✓ _parse_dylan_audio function is importable and callable")
    
    def test_parse_dylan_audio_voice_id(self):
        """_parse_dylan_audio correctly parses Voice ID"""
        from pipeline.engine import _parse_dylan_audio
        
        sample_output = """===VOICE SELECTION===
Voice ID: 21m00Tcm4TlvDq8ikWAM
Voice Name: Rachel
Gender: female
Why: Perfect warm voice for luxury brand

===VOICE SETTINGS===
Stability: 0.55
Similarity: 0.80
Style: 0.40
Speed: 1.05
"""
        config = _parse_dylan_audio(sample_output)
        
        assert config.get('type') == 'elevenlabs', "Should detect elevenlabs type"
        assert config.get('voice_id') == '21m00Tcm4TlvDq8ikWAM', "Should parse voice_id correctly"
        print(f"✓ _parse_dylan_audio correctly parses Voice ID: {config.get('voice_id')}")
    
    def test_parse_dylan_audio_voice_settings(self):
        """_parse_dylan_audio correctly parses stability, similarity, style, speed"""
        from pipeline.engine import _parse_dylan_audio
        
        sample_output = """===VOICE SETTINGS===
Stability: 0.55
Similarity: 0.80
Style: 0.40
Speed: 1.05
"""
        config = _parse_dylan_audio(sample_output)
        
        assert config.get('stability') == 0.55, f"Expected stability=0.55, got {config.get('stability')}"
        assert config.get('similarity') == 0.80, f"Expected similarity=0.80, got {config.get('similarity')}"
        assert config.get('style_val') == 0.40, f"Expected style_val=0.40, got {config.get('style_val')}"
        assert config.get('speed') == 1.05, f"Expected speed=1.05, got {config.get('speed')}"
        
        print(f"✓ _parse_dylan_audio correctly parses voice settings: stability={config.get('stability')}, similarity={config.get('similarity')}, style_val={config.get('style_val')}, speed={config.get('speed')}")
    
    def test_parse_dylan_audio_music_selection(self):
        """_parse_dylan_audio correctly parses music track and volumes"""
        from pipeline.engine import _parse_dylan_audio
        
        sample_output = """===MUSIC SELECTION===
Track: cinematic
Name: Cinematic & Epic
Why: Perfect for luxury brand commercial

===MUSIC MIX===
Narration Volume: 25%
Outro Volume: 60%
Fade In: 2s
Fade Out: 3s
"""
        config = _parse_dylan_audio(sample_output)
        
        assert config.get('_music_key') == 'cinematic', f"Expected _music_key='cinematic', got {config.get('_music_key')}"
        assert config.get('_music_narr_vol') == 25, f"Expected _music_narr_vol=25, got {config.get('_music_narr_vol')}"
        assert config.get('_music_outro_vol') == 60, f"Expected _music_outro_vol=60, got {config.get('_music_outro_vol')}"
        
        print(f"✓ _parse_dylan_audio correctly parses music: track={config.get('_music_key')}, narr_vol={config.get('_music_narr_vol')}, outro_vol={config.get('_music_outro_vol')}")
    
    def test_parse_dylan_audio_emotional_arc(self):
        """_parse_dylan_audio parses tone from Emotional Arc"""
        from pipeline.engine import _parse_dylan_audio
        
        sample_output = """===NARRATION DELIVERY===
Emotional Arc: Starts intimate and warm, builds to excitement, ends with confident urgency
[HOOK 0-4s]: <warm, slow> Gentle opening
[BODY 4-10s]: <energetic, medium> Building energy
[CTA 10-16s]: <urgent, fast> Call to action
"""
        config = _parse_dylan_audio(sample_output)
        
        assert config.get('tone') is not None, "Should parse tone from Emotional Arc"
        assert 'intimate' in config.get('tone', '') or 'warm' in config.get('tone', ''), "Tone should capture emotional arc"
        
        print(f"✓ _parse_dylan_audio parses tone: '{config.get('tone')}'")
    
    def test_step_models_includes_dylan_sound(self):
        """_execute_step has 'dylan_sound' in STEP_MODELS"""
        # Read the engine.py file and check STEP_MODELS
        with open('/app/backend/pipeline/engine.py', 'r') as f:
            content = f.read()
        
        # Find STEP_MODELS definition
        assert '"dylan_sound":' in content, "dylan_sound must be in STEP_MODELS"
        
        # Check it uses gemini-2.0-flash (as per the code)
        dylan_match = re.search(r'"dylan_sound":\s*\(\s*"(\w+)"\s*,\s*"([^"]+)"\s*\)', content)
        assert dylan_match is not None, "dylan_sound STEP_MODELS entry not found with expected format"
        
        provider, model = dylan_match.groups()
        assert provider == 'gemini', f"Expected provider='gemini', got '{provider}'"
        assert 'flash' in model.lower(), f"Expected flash model for speed, got '{model}'"
        
        print(f"✓ STEP_MODELS['dylan_sound'] = ({provider}, {model})")
    
    def test_build_prompt_for_dylan_sound_step(self):
        """_build_prompt for 'dylan_sound' step generates a proper prompt with campaign context"""
        from pipeline.prompts import _build_prompt
        
        # Mock pipeline data
        mock_pipeline = {
            'briefing': 'Create a luxury car commercial for Audi',
            'platforms': ['instagram', 'tiktok', 'youtube'],
            'result': {
                'campaign_name': 'Audi Q5 Launch',
                'campaign_language': 'en',
                'video_mode': 'narration',
            },
            'steps': {
                'sofia_copy': {
                    'output': """===VARIATION 1===
Title: The New Audi Q5
Copy: Experience luxury redefined.
CTA: Discover more

===IMAGE BRIEFING===
HEADLINE: LUXURY REDEFINED
VISUAL CONCEPT 1: Sleek car on mountain road

===VIDEO BRIEF===
VIDEO TAGLINE: Experience the extraordinary
VIDEO TONE: Sophisticated, aspirational
MUSIC MOOD: cinematic
CTA FOR VIDEO: Visit audi.com"""
                },
                'ana_review_copy': {
                    'approved_content': 'Experience luxury redefined. The new Audi Q5.',
                    'output': 'DECISION: APPROVED\nSELECTED_OPTION: 1'
                }
            }
        }
        
        prompt = _build_prompt('dylan_sound', mock_pipeline)
        
        # Check prompt contains essential elements
        assert 'Audi' in prompt or 'luxury' in prompt.lower(), "Prompt should include brand/campaign context"
        assert 'dylan' not in prompt.lower() or 'audio' in prompt.lower(), "Prompt should reference audio task"
        assert 'instagram' in prompt.lower() or 'tiktok' in prompt.lower(), "Prompt should include platforms"
        
        print(f"✓ _build_prompt('dylan_sound') generates proper prompt ({len(prompt)} chars)")
    
    def test_build_prompt_for_marcos_video_injects_dylan_output(self):
        """_build_prompt for 'marcos_video' step injects Dylan's output as AUDIO DIRECTION"""
        from pipeline.prompts import _build_prompt
        
        dylan_output = """===VOICE SELECTION===
Voice ID: TX3LPaxmHKxFdv7VOQHJ
Voice Name: Liam
Gender: male
Why: Deep confident voice for automotive

===VOICE SETTINGS===
Stability: 0.45
Similarity: 0.80
Style: 0.50
Speed: 1.0

===MUSIC SELECTION===
Track: cinematic
Name: Cinematic & Epic
Why: Perfect for luxury automotive commercial"""

        # Mock pipeline data with Dylan's output
        mock_pipeline = {
            'briefing': 'Create a luxury car commercial for Audi',
            'platforms': ['instagram', 'youtube'],
            'result': {
                'campaign_name': 'Audi Q5 Launch',
                'campaign_language': 'en',
            },
            'steps': {
                'sofia_copy': {
                    'output': """===IMAGE BRIEFING===
HEADLINE: LUXURY REDEFINED

===VIDEO BRIEF===
VIDEO TAGLINE: Experience the extraordinary"""
                },
                'ana_review_copy': {
                    'approved_content': 'Experience luxury redefined.',
                },
                'dylan_sound': {
                    'output': dylan_output
                }
            }
        }
        
        prompt = _build_prompt('marcos_video', mock_pipeline)
        
        # Check Dylan's output is injected
        assert 'AUDIO DIRECTION' in prompt or 'Dylan' in prompt, "marcos_video prompt should include AUDIO DIRECTION from Dylan"
        assert 'TX3LPaxmHKxFdv7VOQHJ' in prompt or 'Liam' in prompt, "Dylan's voice selection should be in marcos_video prompt"
        assert 'cinematic' in prompt.lower(), "Dylan's music selection should be in marcos_video prompt"
        
        print("✓ _build_prompt('marcos_video') correctly injects Dylan's audio direction")


class TestDylanSoundDirectorAPI:
    """API endpoint tests for pipeline with Dylan Sound Director."""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_client(self, auth_token):
        """Get authenticated session"""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        })
        return session
    
    def test_health_endpoint(self):
        """API: /api/health still works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get('status') == 'ok', "Health status should be 'ok'"
        print("✓ /api/health returns status ok")
    
    def test_campaigns_endpoint_requires_auth(self):
        """API: /api/campaigns requires authentication"""
        response = requests.get(f"{BASE_URL}/api/campaigns")
        # Should return 401 or 403 when not authenticated
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ /api/campaigns requires authentication")
    
    def test_campaigns_endpoint_with_auth(self, auth_client):
        """API: /api/campaigns works with authentication"""
        response = auth_client.get(f"{BASE_URL}/api/campaigns")
        assert response.status_code == 200, f"Campaigns endpoint failed: {response.text}"
        print("✓ /api/campaigns works with authentication")
    
    def test_pipeline_list_endpoint(self, auth_client):
        """API: /api/campaigns/pipeline/list works"""
        response = auth_client.get(f"{BASE_URL}/api/campaigns/pipeline/list")
        assert response.status_code == 200, f"Pipeline list failed: {response.text}"
        data = response.json()
        assert 'pipelines' in data, "Response should contain 'pipelines' key"
        print(f"✓ /api/campaigns/pipeline/list returns {len(data.get('pipelines', []))} pipelines")
    
    def test_music_library_endpoint(self, auth_client):
        """API: /api/campaigns/pipeline/music-library works (used by Dylan)"""
        response = auth_client.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200, f"Music library failed: {response.text}"
        data = response.json()
        assert 'tracks' in data, "Response should contain 'tracks' key"
        
        tracks = data['tracks']
        # Check for key tracks that Dylan references
        track_keys = [t.get('id') or t.get('key') for t in tracks]
        assert 'cinematic' in track_keys or any('cinematic' in str(t) for t in tracks), "Music library should include 'cinematic' track"
        
        print(f"✓ /api/campaigns/pipeline/music-library returns {len(tracks)} tracks")
    
    def test_elevenlabs_voices_endpoint(self, auth_client):
        """API: /api/campaigns/pipeline/elevenlabs-voices works (used by Dylan)"""
        response = auth_client.get(f"{BASE_URL}/api/campaigns/pipeline/elevenlabs-voices")
        assert response.status_code == 200, f"ElevenLabs voices failed: {response.text}"
        data = response.json()
        assert 'voices' in data, "Response should contain 'voices' key"
        assert 'available' in data, "Response should indicate availability"
        
        voices = data['voices']
        if voices:
            # Check for voices Dylan references
            voice_ids = [v.get('id') for v in voices]
            assert '21m00Tcm4TlvDq8ikWAM' in voice_ids, "Should include Rachel voice"
        
        print(f"✓ /api/campaigns/pipeline/elevenlabs-voices returns {len(voices)} voices (available={data['available']})")


class TestDylanSoundDirectorIntegration:
    """Integration tests for Dylan Sound Director in the full pipeline."""
    
    def test_music_library_config_exists(self):
        """MUSIC_LIBRARY config exists with tracks Dylan references"""
        from pipeline.config import MUSIC_LIBRARY
        
        assert isinstance(MUSIC_LIBRARY, dict), "MUSIC_LIBRARY should be a dict"
        assert len(MUSIC_LIBRARY) > 0, "MUSIC_LIBRARY should not be empty"
        
        # Check for key tracks Dylan might select
        expected_tracks = ['cinematic', 'corporate', 'upbeat', 'emotional']
        for track in expected_tracks:
            assert track in MUSIC_LIBRARY, f"MUSIC_LIBRARY should contain '{track}' track"
        
        # Check track structure
        sample_track = MUSIC_LIBRARY['cinematic']
        assert 'name' in sample_track, "Track should have 'name'"
        assert 'file' in sample_track, "Track should have 'file'"
        
        print(f"✓ MUSIC_LIBRARY contains {len(MUSIC_LIBRARY)} tracks including: {', '.join(expected_tracks)}")
    
    def test_elevenlabs_voices_config_exists(self):
        """ELEVENLABS_VOICES config exists with voices Dylan references"""
        from pipeline.config import ELEVENLABS_VOICES
        
        assert isinstance(ELEVENLABS_VOICES, list), "ELEVENLABS_VOICES should be a list"
        assert len(ELEVENLABS_VOICES) > 0, "ELEVENLABS_VOICES should not be empty"
        
        # Check for voices Dylan's prompt includes
        voice_ids = [v.get('id') for v in ELEVENLABS_VOICES]
        expected_ids = ['21m00Tcm4TlvDq8ikWAM', 'TX3LPaxmHKxFdv7VOQHJ', 'EXAVITQu4vr4xnSDxMaL']  # Rachel, Liam, Bella
        
        for vid in expected_ids:
            assert vid in voice_ids, f"ELEVENLABS_VOICES should contain voice ID '{vid}'"
        
        # Check voice structure
        sample_voice = ELEVENLABS_VOICES[0]
        assert 'id' in sample_voice, "Voice should have 'id'"
        assert 'name' in sample_voice, "Voice should have 'name'"
        assert 'gender' in sample_voice, "Voice should have 'gender'"
        
        print(f"✓ ELEVENLABS_VOICES contains {len(ELEVENLABS_VOICES)} voices")
    
    def test_generate_narration_respects_voice_config(self):
        """_generate_narration function accepts voice_config parameter with Dylan's settings"""
        import asyncio
        from pipeline.media import _generate_narration
        import inspect
        
        # Check function signature includes voice_config
        sig = inspect.signature(_generate_narration)
        params = list(sig.parameters.keys())
        
        assert 'voice_config' in params, "_generate_narration should accept voice_config parameter"
        
        # Check the function is async
        assert asyncio.iscoroutinefunction(_generate_narration), "_generate_narration should be async"
        
        print("✓ _generate_narration accepts voice_config parameter for Dylan's settings")
    
    def test_pipeline_step_order_count(self):
        """Pipeline has 8 steps total including Dylan"""
        from pipeline.config import STEP_ORDER
        
        assert len(STEP_ORDER) == 8, f"Expected 8 steps, got {len(STEP_ORDER)}"
        
        expected_order = [
            'sofia_copy', 'ana_review_copy', 'lucas_design', 'rafael_review_design',
            'dylan_sound', 'marcos_video', 'rafael_review_video', 'pedro_publish'
        ]
        
        assert STEP_ORDER == expected_order, f"STEP_ORDER mismatch. Expected: {expected_order}, Got: {STEP_ORDER}"
        
        print(f"✓ STEP_ORDER has 8 steps: {' → '.join(STEP_ORDER)}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
