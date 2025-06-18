#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tutorial Manager

Main controller for the onboarding tutorial system. Coordinates between
slideshow tutorials, guided tours, and state management.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget

from .tutorial_state import TutorialState
from .slideshow import TutorialSlideshow
from .guided_tour import GuidedTour


class TutorialManager(QObject):
    """Main tutorial system controller"""
    
    # Signals
    tutorial_started = pyqtSignal(str)  # tutorial_type
    tutorial_completed = pyqtSignal(str)  # tutorial_type
    tutorial_skipped = pyqtSignal(str)  # tutorial_type
    all_tutorials_completed = pyqtSignal()
    
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.state = TutorialState()
        self.slideshow = None
        self.guided_tour = None
        
        # Connect state signals
        self.state.tutorial_completed.connect(self._handle_tutorial_completed)
        self.state.tutorial_skipped.connect(self._handle_tutorial_skipped)
        
        # Delay timer for showing tutorials after app startup
        self.startup_timer = QTimer()
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self._check_and_show_tutorials)
    
    def set_parent_widget(self, parent_widget):
        """Set the parent widget for tutorials"""
        self.parent_widget = parent_widget
    
    def initialize(self):
        """Initialize the tutorial system after app startup"""
        # Delay tutorial check to allow app to fully load
        self.startup_timer.start(1000)  # 1 second delay
    
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
    
    def show_guided_tour(self):
        """Show the guided tour"""
        if self.guided_tour:
            return  # Already showing
        
        self.guided_tour = GuidedTour(self.parent_widget)
        
        # Connect signals
        self.guided_tour.completed.connect(lambda: self._guided_tour_finished(completed=True))
        self.guided_tour.skipped.connect(lambda: self._guided_tour_finished(completed=False))
        
        # Start tour
        self.guided_tour.start_tour()
        self.tutorial_started.emit('guided_tour')
    
    def _slideshow_finished(self, tutorial_id, completed):
        """Handle slideshow completion"""
        if completed:
            self.state.mark_tutorial_completed(tutorial_id)
            # Show guided tour next if it should be shown
            auto_start_tour = self.state.get_preference('auto_start_guided_tour_after_slideshow', True)
            if auto_start_tour and self.state.should_show_tutorial('guided_tour'):
                print("DEBUG: Starting guided tour after slideshow completion")
                QTimer.singleShot(1000, self.show_guided_tour)  # Small delay
            else:
                print(f"DEBUG: Guided tour not starting - auto_start: {auto_start_tour}, should_show: {self.state.should_show_tutorial('guided_tour')}")
        else:
            self.state.mark_tutorial_skipped(tutorial_id)
        
        # Clean up
        if self.slideshow:
            self.slideshow.deleteLater()
            self.slideshow = None
    
    def _guided_tour_finished(self, completed):
        """Handle guided tour completion"""
        if completed:
            self.state.mark_tutorial_completed('guided_tour')
        else:
            self.state.mark_tutorial_skipped('guided_tour')
        
        # Clean up
        if self.guided_tour:
            self.guided_tour.deleteLater()
            self.guided_tour = None
        
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
        return (self.state.is_tutorial_completed('welcome_slideshow') and 
                self.state.is_tutorial_completed('guided_tour'))
    
    def stop_all_tutorials(self):
        """Stop all running tutorials"""
        if self.slideshow:
            self.slideshow.close()
            self.slideshow = None
        
        if self.guided_tour:
            self.guided_tour.stop_tour()
            self.guided_tour = None
    
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
    
    def set_guided_tour_enabled(self, enabled):
        """Enable/disable the guided tour"""
        self.state.set_preference('show_guided_tour', enabled)
    
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
        return self.slideshow is not None or self.guided_tour is not None
    
    def get_current_tutorial_type(self):
        """Get the type of currently running tutorial"""
        if self.slideshow:
            return 'welcome_slideshow'
        elif self.guided_tour:
            return 'guided_tour'
        return None
    
    # Integration methods for main app
    def on_app_fully_loaded(self):
        """Call this when the main app is fully loaded and ready for tutorials"""
        self._check_and_show_tutorials()
    
    def register_widget_for_tour(self, widget, widget_name):
        """Register a widget with a specific name for the guided tour"""
        if widget and hasattr(widget, 'setObjectName'):
            widget.setObjectName(widget_name)
    
    def update_tour_target(self, step_index, widget_name):
        """Update the target widget for a specific guided tour step"""
        if self.guided_tour:
            self.guided_tour.set_target_widget_by_name(step_index, widget_name)
    
    # Menu integration methods
    def show_slideshow_manually(self):
        """Show slideshow when triggered from menu (regardless of state)"""
        self.show_welcome_slideshow()
    
    def show_guided_tour_manually(self):
        """Show guided tour when triggered from menu (regardless of state)"""
        self.show_guided_tour()
    
    def show_tutorial_preferences(self):
        """Show tutorial preferences (to be integrated with app preferences)"""
        # This would typically open the preferences dialog with tutorial settings
        # For now, we'll just print the current state
        prefs = {
            'slideshow_enabled': self.state.get_preference('show_welcome_slideshow'),
            'guided_tour_enabled': self.state.get_preference('show_guided_tour'),
            'auto_start': self.state.get_preference('auto_start_tutorials'),
            'auto_advance': self.state.get_preference('slideshow_auto_advance'),
            'speed': self.state.get_preference('slideshow_speed')
        }
        return prefs
    
    def stop_guided_tour(self):
        """Stop the guided tour immediately"""
        try:
            if hasattr(self, 'guided_tour') and self.guided_tour:
                self.guided_tour.stop_tour()
                self.guided_tour = None
                print("DEBUG: Guided tour stopped successfully")
        except Exception as e:
            print(f"Error stopping guided tour: {e}")
    
    def stop_slideshow(self):
        """Stop the slideshow immediately"""
        try:
            if hasattr(self, 'current_slideshow') and self.current_slideshow:
                if self.current_slideshow.isVisible():
                    self.current_slideshow.close()
                self.current_slideshow = None
                print("DEBUG: Slideshow stopped successfully")
        except Exception as e:
            print(f"Error stopping slideshow: {e}")
    
    def cleanup_all_tutorials(self):
        """Clean up all running tutorials"""
        self.stop_guided_tour()
        self.stop_slideshow()
        print("DEBUG: All tutorials cleaned up") 