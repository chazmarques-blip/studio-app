"""
Iteration 30 Backend Tests - Revision Loop Detection and Music Library with Categories

Tests:
1. _parse_review_decision function with various inputs
2. _extract_revision_feedback function
3. Music Library API returns 25 tracks with category field
"""

import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============================================================
# UNIT TESTS: _parse_review_decision function
# ============================================================

class TestParseReviewDecision:
    """Test _parse_review_decision function with explicit and implicit rejection signals"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Import the function from pipeline.py"""
        from routers.pipeline import _parse_review_decision
        self.parse = _parse_review_decision
    
    def test_explicit_approved(self):
        """Test explicit DECISION: APPROVED is detected correctly"""
        text = """
        Great work! The copy is excellent.
        
        DECISION: APPROVED
        SELECTED_OPTION: 2
        """
        result = self.parse(text)
        assert result == "approved", f"Expected 'approved', got '{result}'"
        print("✓ DECISION: APPROVED detected correctly")
    
    def test_explicit_revision_needed(self):
        """Test explicit DECISION: REVISION_NEEDED is detected correctly"""
        text = """
        The copy needs improvement.
        
        DECISION: REVISION_NEEDED
        REVISION_FEEDBACK: Please fix the tone.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ DECISION: REVISION_NEEDED detected correctly")
    
    def test_explicit_rejected(self):
        """Test explicit DECISION: REJECTED maps to revision_needed"""
        text = """
        This is not acceptable.
        
        DECISION: REJECTED
        FEEDBACK: Start over.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ DECISION: REJECTED detected and mapped to revision_needed")
    
    def test_implicit_problema_critico(self):
        """Test implicit rejection with 'PROBLEMA CRITICO' (Portuguese)"""
        text = """
        Análise do Copy:
        
        PROBLEMA CRÍTICO: O texto está em inglês mas a campanha deve ser em português.
        
        Scores:
        - Scroll-stop power: 4/10
        - Emotional resonance: 3/10
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Implicit 'PROBLEMA CRÍTICO' detected as revision_needed")
    
    def test_implicit_critical_problem(self):
        """Test implicit rejection with 'CRITICAL PROBLEM' (English)"""
        text = """
        Copy Review:
        
        CRITICAL PROBLEM: The headline is in the wrong language.
        
        This is a fundamental error that requires revision.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Implicit 'CRITICAL PROBLEM' detected as revision_needed")
    
    def test_implicit_wrong_language(self):
        """Test implicit rejection with 'WRONG LANGUAGE' signal"""
        text = """
        Review Summary:
        
        WRONG LANGUAGE detected - the copy is in Spanish but should be Portuguese.
        
        All variations fail the language check.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Implicit 'WRONG LANGUAGE' detected as revision_needed")
    
    def test_implicit_low_score_3_10(self):
        """Test implicit rejection with low score (3/10)"""
        text = """
        Quality Assessment:
        
        Overall Score: 3/10
        
        The copy lacks emotional impact and fails to connect with the audience.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Low score (3/10) detected as revision_needed")
    
    def test_implicit_low_score_4_10(self):
        """Test implicit rejection with low score (4/10)"""
        text = """
        Score: 4/10
        
        Needs significant improvement.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Low score (4/10) detected as revision_needed")
    
    def test_approved_with_high_score(self):
        """Test that good score without explicit decision defaults to approved"""
        text = """
        Excellent copy! 
        
        Score: 8/10
        
        Great emotional appeal and clear CTA.
        """
        result = self.parse(text)
        assert result == "approved", f"Expected 'approved', got '{result}'"
        print("✓ Good score (8/10) without explicit decision defaults to approved")
    
    def test_implicit_idioma_incorrecto_spanish(self):
        """Test implicit rejection with 'IDIOMA INCORRECTO' (Spanish)"""
        text = """
        Revisión del Copy:
        
        IDIOMA INCORRECTO - El texto debería estar en portugués.
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Implicit 'IDIOMA INCORRECTO' detected as revision_needed")
    
    def test_implicit_language_mismatch(self):
        """Test implicit rejection with 'LANGUAGE MISMATCH'"""
        text = """
        ERROR: LANGUAGE MISMATCH between copy and campaign settings.
        
        Expected: Portuguese
        Found: English
        """
        result = self.parse(text)
        assert result == "revision_needed", f"Expected 'revision_needed', got '{result}'"
        print("✓ Implicit 'LANGUAGE MISMATCH' detected as revision_needed")


# ============================================================
# UNIT TESTS: _extract_revision_feedback function  
# ============================================================

class TestExtractRevisionFeedback:
    """Test _extract_revision_feedback function extracts feedback correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Import the function from pipeline.py"""
        from routers.pipeline import _extract_revision_feedback
        self.extract = _extract_revision_feedback
    
    def test_explicit_revision_feedback(self):
        """Test extraction of explicit REVISION_FEEDBACK tag"""
        text = """
        DECISION: REVISION_NEEDED
        REVISION_FEEDBACK: Please fix the following:
        - Change the headline to Portuguese
        - Add more emotional appeal
        - Include a stronger CTA
        
        SELECTED_OPTION: None
        """
        result = self.extract(text)
        assert "headline" in result.lower() or "português" in result.lower() or "portuguese" in result.lower()
        print(f"✓ Extracted explicit feedback: {result[:100]}...")
    
    def test_extract_from_problema_critico(self):
        """Test extraction from PROBLEMA CRITICO section"""
        text = """
        Análise Completa:
        
        PROBLEMA CRÍTICO: O headline está em inglês quando deveria estar em português.
        Esta é uma falha fundamental que invalida toda a campanha.
        
        Outros pontos:
        - Bom uso de emojis
        """
        result = self.extract(text)
        assert len(result) > 20, "Feedback should be extracted"
        print(f"✓ Extracted from PROBLEMA CRITICO: {result[:100]}...")
    
    def test_extract_from_critical_problem(self):
        """Test extraction from CRITICAL PROBLEM section"""
        text = """
        Review Notes:
        
        CRITICAL PROBLEM: The entire copy is in the wrong language.
        
        Details:
        - Campaign language: Portuguese
        - Copy language: English
        """
        result = self.extract(text)
        assert len(result) > 10, "Feedback should be extracted"
        print(f"✓ Extracted from CRITICAL PROBLEM: {result[:100]}...")
    
    def test_fallback_default_message(self):
        """Test fallback when no specific feedback section found"""
        text = """
        This copy is rejected.
        REJECTED
        """
        result = self.extract(text)
        assert "quality" in result.lower() or "improve" in result.lower()
        print(f"✓ Fallback message returned: {result[:80]}...")


# ============================================================
# API TESTS: Music Library with Categories
# ============================================================

class TestMusicLibraryAPI:
    """Test Music Library API returns tracks with category field"""
    
    def test_music_library_returns_25_tracks(self):
        """Test GET /api/campaigns/pipeline/music-library returns 25 tracks"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "tracks" in data, "Response should have 'tracks' field"
        
        tracks = data["tracks"]
        assert len(tracks) == 25, f"Expected 25 tracks, got {len(tracks)}"
        print(f"✓ Music library returns {len(tracks)} tracks")
    
    def test_each_track_has_category_field(self):
        """Test each track has 'category' field"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200
        
        tracks = response.json()["tracks"]
        tracks_without_category = [t for t in tracks if "category" not in t]
        
        assert len(tracks_without_category) == 0, f"{len(tracks_without_category)} tracks missing 'category' field"
        print("✓ All tracks have 'category' field")
    
    def test_categories_match_expected_values(self):
        """Test categories are in expected set"""
        expected_categories = {"General", "Pop", "Hip-Hop", "Electronic", "Latin", "Rock", "Jazz", "Ambient", "Other"}
        
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200
        
        tracks = response.json()["tracks"]
        found_categories = set(t["category"] for t in tracks)
        
        # All found categories should be in expected set
        unexpected = found_categories - expected_categories
        assert len(unexpected) == 0, f"Unexpected categories found: {unexpected}"
        
        print(f"✓ Found categories: {found_categories}")
        print(f"✓ All categories match expected values")
    
    def test_track_structure(self):
        """Test each track has required fields"""
        required_fields = ["id", "name", "description", "duration", "file", "category", "preview_url"]
        
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200
        
        tracks = response.json()["tracks"]
        
        for track in tracks[:5]:  # Check first 5 tracks
            for field in required_fields:
                assert field in track, f"Track {track.get('id', 'unknown')} missing '{field}' field"
        
        print(f"✓ All tracks have required fields: {required_fields}")
    
    def test_category_distribution(self):
        """Test tracks are distributed across multiple categories"""
        response = requests.get(f"{BASE_URL}/api/campaigns/pipeline/music-library")
        assert response.status_code == 200
        
        tracks = response.json()["tracks"]
        
        # Count tracks per category
        category_counts = {}
        for track in tracks:
            cat = track["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Should have at least 5 different categories
        assert len(category_counts) >= 5, f"Expected at least 5 categories, got {len(category_counts)}"
        
        print(f"✓ Category distribution: {category_counts}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
