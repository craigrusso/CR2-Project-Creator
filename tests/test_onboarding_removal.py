#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test file to verify guided tour removal and slideshow updates.
"""

import unittest
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.onboarding.config import CUSTOM_SLIDESHOW_CONTENT, DEFAULT_PREFERENCES
from app.onboarding.tutorial_manager import TutorialManager
from app.onboarding.slideshow import TutorialSlideshow, SlideshowSlide, ImageWithArrow


class TestOnboardingRemoval(unittest.TestCase):
    """Test cases for verifying guided tour removal and slideshow updates"""

    def test_guided_tour_removed_from_preferences(self):
        """Test that guided tour preferences have been removed"""
        # Check that guided tour preferences are not in the defaults
        self.assertNotIn('show_guided_tour', DEFAULT_PREFERENCES)
        self.assertNotIn('guided_tour_completed', DEFAULT_PREFERENCES)
        
        # Check that welcome slideshow preference is still there
        self.assertIn('show_welcome_slideshow', DEFAULT_PREFERENCES)

    def test_slideshow_content_updated(self):
        """Test that slideshow content has been updated with new copy"""
        # Check that we have the expected number of slides
        self.assertEqual(len(CUSTOM_SLIDESHOW_CONTENT), 5)
        
        # Check that first slide mentions "Add Template" instead of "Create Template"
        first_slide = CUSTOM_SLIDESHOW_CONTENT[0]
        self.assertIn("Add Template", first_slide['content'])
        self.assertNotIn("Create Template", first_slide['content'])
        
        # Check that final slide mentions "Create Project(s)"
        final_slide = CUSTOM_SLIDESHOW_CONTENT[-1]
        self.assertIn("Create Project(s)", final_slide['content'])

    def test_new_slides_added(self):
        """Test that the 4th slide has been added"""
        # Check that we have 5 slides total
        self.assertEqual(len(CUSTOM_SLIDESHOW_CONTENT), 5)
        
        # Check that the 4th slide (index 3) has the correct content
        fourth_slide = CUSTOM_SLIDESHOW_CONTENT[3]
        self.assertIn("project name", fourth_slide['content'].lower())
        self.assertIn("template", fourth_slide['content'].lower())

    def test_multi_step_sequence_slide(self):
        """Test that slide 3 (index 2) has multi-step sequence"""
        slide_3 = CUSTOM_SLIDESHOW_CONTENT[2]
        self.assertIn('multi_step_sequence', slide_3)
        self.assertIsInstance(slide_3['multi_step_sequence'], list)
        self.assertEqual(len(slide_3['multi_step_sequence']), 4)

    def test_tutorial_manager_no_guided_tour(self):
        """Test that tutorial manager doesn't reference guided tour"""
        # This should not raise any import errors
        manager = TutorialManager()
        
        # Check that guided tour methods don't exist
        self.assertFalse(hasattr(manager, 'show_guided_tour'))
        self.assertFalse(hasattr(manager, 'start_guided_tour'))

    def test_tutorial_state_progress_calculation(self):
        """Test that tutorial progress calculation works with only slideshow"""
        from app.onboarding.tutorial_state import TutorialState
        
        state = TutorialState()
        
        # Reset all tutorials to ensure clean state
        state.reset_all_tutorials()
        
        # Initially should be 0% (no tutorials completed)
        self.assertEqual(state.get_tutorial_progress(), 0)
        
        # After completing slideshow, should be 100%
        state.mark_tutorial_completed('welcome_slideshow')
        self.assertEqual(state.get_tutorial_progress(), 100)

    def test_config_has_correct_slides(self):
        """Test that config has the correct slide structure"""
        # Check second slide has arrow data
        second_slide = CUSTOM_SLIDESHOW_CONTENT[1]
        self.assertIn('arrow_image_path', second_slide)
        self.assertEqual(second_slide['arrow_image_path'], 'sample_svgs/SLIDE_02_ARROW.png')
        
        # Check that multi-step slide exists
        multi_step_slide = None
        for slide in CUSTOM_SLIDESHOW_CONTENT:
            if slide.get('multi_step_sequence'):
                multi_step_slide = slide
                break
        
        self.assertIsNotNone(multi_step_slide)
        self.assertEqual(len(multi_step_slide['multi_step_sequence']), 4)


class TestSubNavigation(unittest.TestCase):
    """Test cases for the new sub-navigation system"""

    def setUp(self):
        """Set up test environment"""
        from PyQt6.QtWidgets import QApplication
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

    def test_sub_navigation_detection(self):
        """Test that slides correctly detect when they need sub-navigation"""
        slideshow = TutorialSlideshow()
        
        # Slide 2 (index 2) should have 4 sub-steps
        slide_2 = slideshow.slides[2]
        self.assertEqual(slide_2.get_total_sub_steps(), 4)
        
        # Slide 1 should have sub-navigation for arrow animation
        slide_1 = slideshow.slides[1]
        self.assertGreater(slide_1.get_total_sub_steps(), 0)

    def test_image_with_arrow_step_jumping(self):
        """Test that ImageWithArrow can jump to specific steps"""
        # Create a mock multi-step sequence
        multi_step_sequence = [
            {'action': 'show_arrow', 'delay': 1000, 'arrow_image': 'test1.png'},
            {'action': 'fade_arrow_show_overlay', 'delay': 2000, 'overlay_image': 'overlay.png'},
            {'action': 'show_final_arrow', 'delay': 1500, 'arrow_image': 'test2.png'},
            {'action': 'show_advanced_arrow', 'delay': 1500, 'arrow_image': 'test3.png'}
        ]
        
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(100, 100)  # Create a small test pixmap
        
        widget = ImageWithArrow(
            pixmap=pixmap,
            multi_step_sequence=multi_step_sequence
        )
        
        # Test total steps
        self.assertEqual(widget.get_total_steps(), 4)
        
        # Test jumping to different steps
        widget.jump_to_step(0)
        self.assertEqual(widget.get_current_step(), 0)
        
        widget.jump_to_step(2)
        self.assertEqual(widget.get_current_step(), 2)
        
        # Test boundary conditions
        widget.jump_to_step(-1)  # Should not change
        self.assertEqual(widget.get_current_step(), 2)
        
        widget.jump_to_step(10)  # Should not change
        self.assertEqual(widget.get_current_step(), 2)

    def test_slide_sub_nav_dots_creation(self):
        """Test that slides create sub-navigation dots correctly"""
        slideshow = TutorialSlideshow()
        
        # Find a slide with sub-navigation
        slide_with_sub_nav = None
        for slide in slideshow.slides:
            if slide.get_total_sub_steps() > 1:
                slide_with_sub_nav = slide
                break
        
        self.assertIsNotNone(slide_with_sub_nav, "Should have at least one slide with sub-navigation")
        
        # Check that sub-navigation widget was created
        self.assertTrue(hasattr(slide_with_sub_nav, 'sub_nav_widget'))
        if slide_with_sub_nav.sub_nav_widget:
            self.assertTrue(hasattr(slide_with_sub_nav, 'sub_nav_dots'))
            self.assertGreater(len(slide_with_sub_nav.sub_nav_dots), 1)

    def test_sub_nav_state_updates(self):
        """Test that sub-navigation state updates correctly"""
        slideshow = TutorialSlideshow()
        
        # Find slide 2 (the multi-step slide)
        slide_2 = slideshow.slides[2]
        
        if slide_2.sub_nav_widget:
            # Initial state should be step 0
            self.assertEqual(slide_2.get_current_sub_step(), 0)
            
            # Simulate step change
            slide_2._update_sub_nav_state(2)
            self.assertEqual(slide_2.get_current_sub_step(), 2)

    def tearDown(self):
        """Clean up after tests"""
        if self.app:
            self.app.quit()


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 