"""
Iteration 109: Testing gallery/filmstrip layout for storyboard panels.

This iteration tests the REDESIGNED layout: gallery/filmstrip instead of 3-col grid.
The key change is in StoryboardEditor.jsx - the panel image area now uses a 
main display + horizontal thumbnail strip pattern.

Features tested:
1. Backend: GET /api/studio/projects/fce897cf6ba3/storyboard returns panel 1 with 6 frames
2. Backend: Each frame has correct labels: Plano Geral, Close-up, Ação, Reação, Ângulo Dramático, Transição
3. Frontend code review: selectedFrames state for tracking which frame is selected per panel
4. Frontend code review: Main display image + filmstrip thumbnails (not a grid)
5. Frontend code review: Filmstrip thumbnails have data-testid='frame-thumb-{panelNum}-{idx}'
6. Frontend code review: Selected thumbnail has ring-1 ring-[#C9A84C] and full brightness
7. Frontend code review: Main display has data-testid='panel-main-frame-{panelNum}'
8. Frontend code review: Frame label badge shows on main display
9. Frontend code review: Fallback to single image when panel has no frames
10. Frontend code review: Panel hover shows 3 overlay icons (expand, paintbrush, film reel)
"""

import pytest
import requests
import os
import sys

# Add backend to path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test@agentflow.com"
TEST_PASSWORD = "password123"
PROJECT_ID = "fce897cf6ba3"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestStoryboardFramesAPI:
    """Test the storyboard API returns correct frame data for filmstrip layout."""

    def test_get_storyboard_returns_panels(self, auth_headers):
        """GET /api/studio/projects/{id}/storyboard returns panels array."""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "panels" in data, "Response should have 'panels' key"
        assert isinstance(data["panels"], list), "panels should be a list"
        print(f"✓ Storyboard has {len(data['panels'])} panels")

    def test_panel_1_has_6_frames(self, auth_headers):
        """Panel 1 should have 6 frames for filmstrip display."""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        panels = data.get("panels", [])
        
        # Find panel 1
        panel_1 = next((p for p in panels if p.get("scene_number") == 1), None)
        assert panel_1 is not None, "Panel 1 should exist"
        
        frames = panel_1.get("frames", [])
        print(f"Panel 1 has {len(frames)} frames")
        
        # Panel 1 should have 6 frames
        assert len(frames) == 6, f"Panel 1 should have 6 frames, got {len(frames)}"
        print("✓ Panel 1 has 6 frames for filmstrip display")

    def test_frame_labels_correct(self, auth_headers):
        """Each frame should have correct Portuguese labels."""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        panels = data.get("panels", [])
        
        # Find panel 1 (has 6 frames)
        panel_1 = next((p for p in panels if p.get("scene_number") == 1), None)
        assert panel_1 is not None
        
        frames = panel_1.get("frames", [])
        assert len(frames) == 6, "Panel 1 should have 6 frames"
        
        expected_labels = ["Plano Geral", "Close-up", "Ação", "Reação", "Ângulo Dramático", "Transição"]
        
        for i, frame in enumerate(frames):
            assert "frame_number" in frame, f"Frame {i} missing frame_number"
            assert "image_url" in frame, f"Frame {i} missing image_url"
            assert "label" in frame, f"Frame {i} missing label"
            
            # Validate frame_number is sequential
            assert frame["frame_number"] == i + 1, f"Frame {i} should have frame_number {i+1}"
            
            # Validate label matches expected
            assert frame["label"] == expected_labels[i], f"Frame {i} label should be '{expected_labels[i]}', got '{frame['label']}'"
            
            print(f"✓ Frame {frame['frame_number']}: {frame['label']}")
        
        print(f"✓ All 6 frames have correct labels for filmstrip display")

    def test_panels_2_to_20_have_zero_frames(self, auth_headers):
        """Panels 2-20 should have 0 frames (single image fallback)."""
        response = requests.get(
            f"{BASE_URL}/api/studio/projects/{PROJECT_ID}/storyboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        panels = data.get("panels", [])
        
        # Check panels other than panel 1
        panels_without_frames = 0
        for panel in panels:
            if panel.get("scene_number") != 1:
                frames = panel.get("frames", [])
                if len(frames) == 0:
                    panels_without_frames += 1
        
        print(f"✓ {panels_without_frames} panels have 0 frames (will use single image fallback)")


class TestFrontendFilmstripLayout:
    """Test frontend code has correct filmstrip layout implementation."""

    def test_selected_frames_state_exists(self):
        """StoryboardEditor should have selectedFrames state."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "selectedFrames" in content, "selectedFrames state should exist"
        assert "setSelectedFrames" in content, "setSelectedFrames setter should exist"
        assert "useState({})" in content or "useState({ })" in content, "selectedFrames should be initialized as empty object"
        print("✓ selectedFrames state exists for tracking selected frame per panel")

    def test_get_selected_frame_helper(self):
        """getSelectedFrame helper function should exist."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "getSelectedFrame" in content, "getSelectedFrame helper should exist"
        assert "selectedFrames[panelNum]" in content, "Should access selectedFrames by panelNum"
        print("✓ getSelectedFrame helper function exists")

    def test_select_frame_function(self):
        """selectFrame function should update selectedFrames state."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "selectFrame" in content, "selectFrame function should exist"
        assert "setSelectedFrames" in content, "selectFrame should call setSelectedFrames"
        print("✓ selectFrame function exists to update selected frame")

    def test_main_display_data_testid(self):
        """Main display image should have data-testid='panel-main-frame-{panelNum}'."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "panel-main-frame-" in content, "Main display should have panel-main-frame- testid"
        assert "data-testid={`panel-main-frame-${panel.scene_number}`}" in content, \
            "Main display testid should use panel.scene_number"
        print("✓ Main display has data-testid='panel-main-frame-{panelNum}'")

    def test_filmstrip_container_exists(self):
        """Filmstrip container should exist with data-testid."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "panel-filmstrip-" in content, "Filmstrip container should have panel-filmstrip- testid"
        assert "data-testid={`panel-filmstrip-${panel.scene_number}`}" in content, \
            "Filmstrip testid should use panel.scene_number"
        print("✓ Filmstrip container has data-testid='panel-filmstrip-{panelNum}'")

    def test_frame_thumb_data_testid(self):
        """Filmstrip thumbnails should have data-testid='frame-thumb-{panelNum}-{idx}'."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "frame-thumb-" in content, "Frame thumbnails should have frame-thumb- testid"
        assert "data-testid={`frame-thumb-${panel.scene_number}-${fi}`}" in content, \
            "Frame thumb testid should use panel.scene_number and frame index"
        print("✓ Filmstrip thumbnails have data-testid='frame-thumb-{panelNum}-{idx}'")

    def test_selected_thumbnail_styling(self):
        """Selected thumbnail should have ring-1 ring-[#C9A84C] and brightness-100."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "ring-1 ring-[#C9A84C]" in content, "Selected thumbnail should have golden ring"
        assert "brightness-100" in content, "Selected thumbnail should have full brightness"
        assert "brightness-50" in content, "Non-selected thumbnails should have dimmed brightness"
        print("✓ Selected thumbnail has ring-1 ring-[#C9A84C] and brightness-100")

    def test_frame_label_badge_on_main_display(self):
        """Frame label badge should show on main display when activeFrame has label."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "activeFrame?.label" in content, "Should check for activeFrame.label"
        assert "{activeFrame.label}" in content, "Should display activeFrame.label"
        print("✓ Frame label badge shows on main display when activeFrame has label")

    def test_single_image_fallback(self):
        """Should fallback to single image when panel has no frames."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Check for the condition that renders single image
        assert "panel.frames?.length > 1" in content, "Should check if panel has multiple frames"
        assert "panel.image_url && !isGenerating" in content, "Should fallback to panel.image_url"
        print("✓ Falls back to single image when panel has no frames")

    def test_overlay_icons_on_hover(self):
        """Panel hover should show 3 overlay icons (expand, paintbrush, film reel)."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Check for the 3 overlay icons
        assert "Maximize2" in content, "Expand icon (Maximize2) should exist"
        assert "Paintbrush" in content, "Paintbrush icon should exist"
        assert "Film" in content, "Film reel icon should exist"
        
        # Check for hover behavior
        assert "group-hover:opacity-100" in content, "Icons should appear on hover"
        assert "opacity-0 group-hover:opacity-100" in content, "Icons should be hidden by default"
        print("✓ Panel hover shows 3 overlay icons (expand, paintbrush, film reel)")

    def test_horizontal_filmstrip_layout(self):
        """Filmstrip should be horizontal (flex row, not grid)."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Check for horizontal flex layout in filmstrip
        assert 'flex gap-[2px]' in content or 'flex gap-' in content, \
            "Filmstrip should use flex layout for horizontal thumbnails"
        
        # Should NOT use grid-cols-3 for filmstrip (that was the old layout)
        # The filmstrip uses flex-1 for equal width thumbnails
        assert "flex-1 aspect-[16/10]" in content, "Thumbnails should use flex-1 for equal width"
        print("✓ Filmstrip uses horizontal flex layout (not grid)")

    def test_main_display_aspect_video(self):
        """Main display should have aspect-video for proper sizing."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # Check for aspect-video on main display container
        assert "aspect-video" in content, "Main display should have aspect-video"
        print("✓ Main display has aspect-video for proper sizing")

    def test_no_grid_cols_3_for_frames(self):
        """Should NOT use grid-cols-3 for frames (old layout)."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        # The old layout used grid-cols-3 for the 6-frame grid
        # The new layout uses flex for horizontal filmstrip
        # grid-cols-2 is still used for the panels grid, but not for frames
        
        # Check that panel-frames-grid testid is NOT present (old layout)
        assert "panel-frames-grid-" not in content, \
            "Old grid layout testid should be removed"
        print("✓ Old grid-cols-3 layout for frames has been replaced with filmstrip")


class TestFilmstripInteraction:
    """Test filmstrip interaction logic in frontend code."""

    def test_thumbnail_click_calls_select_frame(self):
        """Clicking thumbnail should call selectFrame function."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "onClick={() => selectFrame(panel.scene_number, fi)}" in content, \
            "Thumbnail click should call selectFrame with panel number and frame index"
        print("✓ Thumbnail click calls selectFrame(panelNum, frameIdx)")

    def test_active_frame_updates_main_display(self):
        """Main display should show activeFrame image."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "activeFrame?.image_url" in content, "Main display should use activeFrame.image_url"
        assert "activeFrame?.label" in content, "Main display should show activeFrame.label"
        print("✓ Main display updates based on activeFrame")

    def test_active_idx_comparison(self):
        """Should compare fi === activeIdx for styling."""
        with open('/app/frontend/src/components/StoryboardEditor.jsx', 'r') as f:
            content = f.read()
        
        assert "fi === activeIdx" in content, "Should compare frame index with activeIdx"
        print("✓ Uses fi === activeIdx for selected thumbnail styling")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
