#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tutorial State Management

Handles saving and loading tutorial completion states, user preferences,
and tutorial progress tracking.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from app.core.config_manager import get_app_preference, set_app_preference


class TutorialState(QObject):
    """Manages tutorial completion state and user preferences"""
    
    # Signals
    tutorial_completed = pyqtSignal(str)  # tutorial_id
    tutorial_skipped = pyqtSignal(str)    # tutorial_id
    preference_changed = pyqtSignal(str, bool)  # key, value
    
    def __init__(self):
        super().__init__()
        self._load_preferences()
    
    def _load_preferences(self):
        """Load tutorial preferences from app config"""
        self.preferences = {
            'show_welcome_slideshow': get_app_preference('tutorial_show_welcome_slideshow', True),
            'show_guided_tour': get_app_preference('tutorial_show_guided_tour', True),
            'auto_start_tutorials': get_app_preference('tutorial_auto_start', True),
            'slideshow_auto_advance': get_app_preference('tutorial_slideshow_auto_advance', False),
            'slideshow_speed': get_app_preference('tutorial_slideshow_speed', 4000),  # 4 seconds
        }
        
        self.completed_tutorials = get_app_preference('tutorial_completed_tutorials', [])
        if not isinstance(self.completed_tutorials, list):
            self.completed_tutorials = []
    
    def save_preferences(self):
        """Save current preferences to app config"""
        for key, value in self.preferences.items():
            set_app_preference(f'tutorial_{key}', value)
        
        set_app_preference('tutorial_completed_tutorials', self.completed_tutorials)
    
    def is_tutorial_completed(self, tutorial_id):
        """Check if a specific tutorial has been completed"""
        return tutorial_id in self.completed_tutorials
    
    def mark_tutorial_completed(self, tutorial_id):
        """Mark a tutorial as completed"""
        if tutorial_id not in self.completed_tutorials:
            self.completed_tutorials.append(tutorial_id)
            self.save_preferences()
            self.tutorial_completed.emit(tutorial_id)
    
    def mark_tutorial_skipped(self, tutorial_id):
        """Mark a tutorial as skipped (same as completed for state tracking)"""
        self.mark_tutorial_completed(tutorial_id)
        self.tutorial_skipped.emit(tutorial_id)
    
    def reset_tutorial(self, tutorial_id):
        """Reset a specific tutorial (mark as not completed)"""
        if tutorial_id in self.completed_tutorials:
            self.completed_tutorials.remove(tutorial_id)
            self.save_preferences()
    
    def reset_all_tutorials(self):
        """Reset all tutorials (mark all as not completed)"""
        self.completed_tutorials.clear()
        self.save_preferences()
    
    def get_preference(self, key, default=None):
        """Get a tutorial preference value"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """Set a tutorial preference value"""
        if key in self.preferences and self.preferences[key] != value:
            self.preferences[key] = value
            self.save_preferences()
            self.preference_changed.emit(key, value)
    
    def should_show_tutorial(self, tutorial_id):
        """Determine if a tutorial should be shown based on state and preferences"""
        # Don't show if already completed
        if self.is_tutorial_completed(tutorial_id):
            return False
        
        # Check specific preferences
        if tutorial_id == 'welcome_slideshow':
            return self.get_preference('show_welcome_slideshow', True)
        elif tutorial_id == 'guided_tour':
            return self.get_preference('show_guided_tour', True)
        
        # Default to showing if auto_start is enabled
        return self.get_preference('auto_start_tutorials', True)
    
    def is_first_launch(self):
        """Check if this is the user's first time launching the app"""
        return len(self.completed_tutorials) == 0
    
    def get_tutorial_progress(self):
        """Get overall tutorial completion progress as a percentage"""
        total_tutorials = 2  # welcome_slideshow, guided_tour
        completed = len(self.completed_tutorials)
        return min(100, (completed / total_tutorials) * 100) 