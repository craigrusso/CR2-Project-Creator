#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tutorial Manager

Coordinates the tutorial system, managing slideshow tutorials.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from .slideshow import TutorialSlideshow
from .tutorial_state import TutorialState


class TutorialManager(QObject):
    """Main tutorial coordination class - manages slideshow only"""
    
    # Signals
    tutorial_started = pyqtSignal(str)  # tutorial_type
    tutorial_completed = pyqtSignal(str)  # tutorial_type
    tutorial_skipped = pyqtSignal(str)  # tutorial_type
    all_tutorials_completed = pyqtSignal()
    
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.state = TutorialState()
        
        # Tutorial components
        self.slideshow = None
        
        # Connect state signals
        self.state.tutorial_completed.connect(self._handle_tutorial_completed)
        self.state.tutorial_skipped.connect(self._handle_tutorial_skipped)

    def initialize(self):
        """Initialize the tutorial system and check if tutorials should be shown"""
        if not self.parent_widget:
            return
        
        self._check_and_show_tutorials()
    
    def _check_and_show_tutorials(self):
        """Check if tutorials should be shown and show them"""
        if not self.parent_widget:
            return
        
        # Check if this is first launch or if user wants to see tutorials
        if self.state.is_first_launch() or self.should_show_welcome():
            self.show_welcome_slideshow()
    
    def should_show_welcome(self):
        """Check if welcome slideshow should be shown"""
        return (self.state.should_show_tutorial('welcome_slideshow') and 
                self.state.get_preference('auto_start_tutorials', True))
    
    def show_welcome_slideshow(self):
        """Show the welcome slideshow tutorial"""
        if self.slideshow:
            return  # Already showing
        
        self.slideshow = TutorialSlideshow(self.parent_widget)
        
        # Connect signals
        self.slideshow.completed.connect(lambda: self._slideshow_finished('welcome_slideshow', completed=True))
        self.slideshow.skipped.connect(lambda: self._slideshow_finished('welcome_slideshow', completed=False))
        
        # Show slideshow
        self.slideshow.show()
        self.tutorial_started.emit('welcome_slideshow')
        
        # Start auto-advance if enabled
        if self.state.get_preference('slideshow_auto_advance', False):
            speed = self.state.get_preference('slideshow_speed', 4000)
            self.slideshow.start_auto_advance(speed)
    
    def _slideshow_finished(self, tutorial_id, completed):
        """Handle slideshow completion"""
        if completed:
            self.state.mark_tutorial_completed(tutorial_id)
        else:
            self.state.mark_tutorial_skipped(tutorial_id)
        
        # Clean up
        if self.slideshow:
            self.slideshow.deleteLater()
            self.slideshow = None
        
        # Check if all tutorials are completed
        if self._all_tutorials_completed():
            self.all_tutorials_completed.emit()
    
    def _handle_tutorial_completed(self, tutorial_id):
        """Handle tutorial completion from state manager"""
        self.tutorial_completed.emit(tutorial_id)
    
    def _handle_tutorial_skipped(self, tutorial_id):
        """Handle tutorial skipping from state manager"""
        self.tutorial_skipped.emit(tutorial_id)
    
    def _all_tutorials_completed(self):
        """Check if all tutorials have been completed"""
        return self.state.is_tutorial_completed('welcome_slideshow')
    
    def stop_all_tutorials(self):
        """Stop all running tutorials"""
        if self.slideshow:
            self.slideshow.close()
            self.slideshow = None
    
    def reset_tutorials(self):
        """Reset all tutorial progress"""
        self.stop_all_tutorials()
        self.state.reset_all_tutorials()
    
    def reset_specific_tutorial(self, tutorial_id):
        """Reset a specific tutorial"""
        self.state.reset_tutorial(tutorial_id)
    
    # Tutorial preference methods
    def set_slideshow_enabled(self, enabled):
        """Enable/disable the welcome slideshow"""
        self.state.set_preference('show_welcome_slideshow', enabled)
    
    def set_auto_start_enabled(self, enabled):
        """Enable/disable automatic tutorial startup"""
        self.state.set_preference('auto_start_tutorials', enabled)
    
    def set_slideshow_auto_advance(self, enabled):
        """Enable/disable slideshow auto-advance"""
        self.state.set_preference('slideshow_auto_advance', enabled)
    
    def set_slideshow_speed(self, milliseconds):
        """Set slideshow auto-advance speed"""
        self.state.set_preference('slideshow_speed', milliseconds)
    
    # Status methods
    def is_tutorial_completed(self, tutorial_id):
        """Check if a tutorial is completed"""
        return self.state.is_tutorial_completed(tutorial_id)
    
    def get_tutorial_progress(self):
        """Get overall tutorial progress percentage"""
        return self.state.get_tutorial_progress()
    
    def is_any_tutorial_running(self):
        """Check if any tutorial is currently running"""
        return self.slideshow is not None
    
    def get_current_tutorial_type(self):
        """Get the type of currently running tutorial"""
        if self.slideshow:
            return 'welcome_slideshow'
        return None
    
    # Integration methods for main app
    def on_app_fully_loaded(self):
        """Call this when the main app is fully loaded and ready for tutorials"""
        self._check_and_show_tutorials()
    
    # Menu integration methods
    def show_slideshow_manually(self):
        """Show slideshow when triggered from menu (regardless of state)"""
        self.show_welcome_slideshow()
    
    def show_tutorial_preferences(self):
        """Show tutorial preferences (to be integrated with app preferences)"""
        # This would typically open the preferences dialog with tutorial settings
        # For now, we'll just print the current state
        prefs = {
            'slideshow_enabled': self.state.get_preference('show_welcome_slideshow'),
            'auto_start': self.state.get_preference('auto_start_tutorials'),
            'auto_advance': self.state.get_preference('slideshow_auto_advance'),
            'speed': self.state.get_preference('slideshow_speed')
        }
        return prefs
    
    def stop_slideshow(self):
        """Stop the slideshow immediately"""
        try:
            if hasattr(self, 'slideshow') and self.slideshow:
                if self.slideshow.isVisible():
                    self.slideshow.close()
                self.slideshow = None
                print("DEBUG: Slideshow stopped successfully")
        except Exception as e:
            print(f"Error stopping slideshow: {e}")
    
    def cleanup_all_tutorials(self):
        """Clean up all running tutorials"""
        self.stop_slideshow()
        print("DEBUG: All tutorials cleaned up") 