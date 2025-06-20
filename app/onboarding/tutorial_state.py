#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tutorial State Management

Manages tutorial completion state and user preferences.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from app.core.config_manager import get_app_preference, set_app_preference


class TutorialState(QObject):
    """Manages tutorial state and preferences"""
    
    # Signals
    tutorial_completed = pyqtSignal(str)  # tutorial_id
    tutorial_skipped = pyqtSignal(str)    # tutorial_id
    
    def __init__(self):
        super().__init__()
        self._load_state()
    
    def _load_state(self):
        """Load tutorial state from preferences"""
        # Load completion state
        self.completed_tutorials = get_app_preference('tutorial_completed_tutorials', [])
        
        # Load preferences
        self.preferences = {
            'show_welcome_slideshow': get_app_preference('tutorial_show_welcome_slideshow', True),
            'auto_start_tutorials': get_app_preference('tutorial_auto_start_tutorials', True),
            'slideshow_auto_advance': get_app_preference('tutorial_slideshow_auto_advance', False),
            'slideshow_speed': get_app_preference('tutorial_slideshow_speed', 4000),
        }
    
    def _save_state(self):
        """Save tutorial state to preferences"""
        set_app_preference('tutorial_completed_tutorials', self.completed_tutorials)
        
        # Save preferences
        for key, value in self.preferences.items():
            set_app_preference(f'tutorial_{key}', value)
    
    def mark_tutorial_completed(self, tutorial_id):
        """Mark a tutorial as completed"""
        if tutorial_id not in self.completed_tutorials:
            self.completed_tutorials.append(tutorial_id)
            self._save_state()
            self.tutorial_completed.emit(tutorial_id)
    
    def mark_tutorial_skipped(self, tutorial_id):
        """Mark a tutorial as skipped (not completed but don't show again)"""
        # For now, treat skipped same as completed
        self.mark_tutorial_completed(tutorial_id)
        self.tutorial_skipped.emit(tutorial_id)
    
    def is_tutorial_completed(self, tutorial_id):
        """Check if a tutorial is completed"""
        return tutorial_id in self.completed_tutorials
    
    def reset_tutorial(self, tutorial_id):
        """Reset a specific tutorial's completion state"""
        if tutorial_id in self.completed_tutorials:
            self.completed_tutorials.remove(tutorial_id)
            self._save_state()
    
    def reset_all_tutorials(self):
        """Reset all tutorial completion state"""
        self.completed_tutorials = []
        self._save_state()
    
    def should_show_tutorial(self, tutorial_id):
        """Determine if a tutorial should be shown based on state and preferences"""
        # Don't show if already completed
        if self.is_tutorial_completed(tutorial_id):
            return False
        
        # Check specific preferences
        if tutorial_id == 'welcome_slideshow':
            return self.get_preference('show_welcome_slideshow', True)
        
        # Default to showing if auto_start is enabled
        return self.get_preference('auto_start_tutorials', True)
    
    def is_first_launch(self):
        """Check if this is the user's first time launching the app"""
        return len(self.completed_tutorials) == 0
    
    def get_tutorial_progress(self):
        """Get overall tutorial completion progress as a percentage"""
        total_tutorials = 1  # Only welcome_slideshow now
        completed = len(self.completed_tutorials)
        return min(100, (completed / total_tutorials) * 100)
    
    def get_preference(self, key, default=None):
        """Get a tutorial preference value"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key, value):
        """Set a tutorial preference value"""
        self.preferences[key] = value
        self._save_state() 