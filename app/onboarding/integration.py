#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Onboarding Integration Guide

This file shows how to integrate the onboarding system into your existing app
with minimal changes to your current codebase.
"""

from .tutorial_manager import TutorialManager


class OnboardingIntegration:
    """
    Helper class to integrate onboarding into your existing app.
    
    Usage in your main app:
    
    1. In your main app class (ProjectCreatorApp), add this to __init__:
    
        from app.onboarding.integration import OnboardingIntegration
        self.onboarding = OnboardingIntegration(self)
    
    2. After your UI is set up, call:
    
        self.onboarding.setup_ui_references()
        self.onboarding.initialize()
    
    3. Add menu items for manual tutorial access:
    
        help_menu.addAction("Show Welcome Tutorial", self.onboarding.show_welcome)
        help_menu.addAction("Show Guided Tour", self.onboarding.show_guided_tour)
        help_menu.addAction("Reset Tutorials", self.onboarding.reset_tutorials)
    
    4. Optional: Add to preferences dialog:
    
        # In your preferences dialog setup:
        tutorial_prefs = self.onboarding.get_tutorial_preferences()
        # Create checkboxes/controls for tutorial_prefs values
        # When preferences change, call:
        self.onboarding.update_preferences(new_preferences)
    """
    
    def __init__(self, main_app):
        """Initialize with reference to main app"""
        self.main_app = main_app
        self.tutorial_manager = TutorialManager(main_app)
        
        # Connect signals for optional integration
        self.tutorial_manager.tutorial_started.connect(self._on_tutorial_started)
        self.tutorial_manager.tutorial_completed.connect(self._on_tutorial_completed)
        self.tutorial_manager.all_tutorials_completed.connect(self._on_all_completed)
    
    def setup_ui_references(self):
        """
        Set up object names for UI elements that the guided tour will reference.
        Call this after your UI is fully set up.
        """
        
        # Map your actual widgets to the names expected by the guided tour
        widget_mappings = {
            # Format: 'tour_name': 'widget_attribute_path'
            'template_gallery': 'template_gallery',              # The template gallery widget
            'project_name_field': 'batch_text_edit',             # The project names text area  
            'structure_editor': 'versioning_options',            # The versioning options widget
        }
        
        # Set object names for widgets so the guided tour can find them
        for tour_name, widget_attr in widget_mappings.items():
            try:
                widget = self._find_widget_by_attr(widget_attr)
                if widget:
                    # Set the object name so findChild can locate it
                    widget.setObjectName(tour_name)
                    print(f"DEBUG: Registered widget '{widget_attr}' as '{tour_name}' for guided tour")
                else:
                    print(f"Warning: Could not find widget '{widget_attr}' for tour reference '{tour_name}'")
            except Exception as e:
                print(f"Error setting up widget reference '{widget_attr}': {e}")
                # Continue with other widgets even if one fails
    
    def _find_widget_by_attr(self, attr_path):
        """Find a widget by traversing attribute path from main app"""
        try:
            obj = self.main_app
            for attr in attr_path.split('.'):
                obj = getattr(obj, attr)
            return obj
        except AttributeError as e:
            print(f"DEBUG: Could not find widget path '{attr_path}': {e}")
            return None
    
    def initialize(self):
        """Initialize the tutorial system (call after UI setup)"""
        self.tutorial_manager.initialize()
    
    # Public methods for menu integration
    def show_welcome(self):
        """Show welcome slideshow (for menu action)"""
        self.tutorial_manager.show_slideshow_manually()
    
    def show_guided_tour(self):
        """Show guided tour (for menu action)"""
        self.tutorial_manager.show_guided_tour_manually()
    
    def reset_tutorials(self):
        """Reset all tutorials (for menu action)"""
        self.tutorial_manager.reset_tutorials()
    
    # Preferences integration
    def get_tutorial_preferences(self):
        """Get current tutorial preferences for preferences dialog"""
        return self.tutorial_manager.show_tutorial_preferences()
    
    def update_preferences(self, preferences):
        """Update tutorial preferences from preferences dialog"""
        if 'slideshow_enabled' in preferences:
            self.tutorial_manager.set_slideshow_enabled(preferences['slideshow_enabled'])
        if 'guided_tour_enabled' in preferences:
            self.tutorial_manager.set_guided_tour_enabled(preferences['guided_tour_enabled'])
        if 'auto_start' in preferences:
            self.tutorial_manager.set_auto_start_enabled(preferences['auto_start'])
        if 'auto_advance' in preferences:
            self.tutorial_manager.set_slideshow_auto_advance(preferences['auto_advance'])
        if 'speed' in preferences:
            self.tutorial_manager.set_slideshow_speed(preferences['speed'])
    
    # Event handlers (optional)
    def _on_tutorial_started(self, tutorial_type):
        """Handle tutorial start (optional - for analytics, etc.)"""
        print(f"Tutorial started: {tutorial_type}")
    
    def _on_tutorial_completed(self, tutorial_type):
        """Handle tutorial completion (optional - for analytics, etc.)"""
        print(f"Tutorial completed: {tutorial_type}")
    
    def _on_all_completed(self):
        """Handle all tutorials completed (optional)"""
        print("All tutorials completed!")
        # You could show a congratulations message, etc.
    
    # Status methods
    def is_tutorial_running(self):
        """Check if any tutorial is currently running"""
        return self.tutorial_manager.is_any_tutorial_running()
    
    def get_tutorial_progress(self):
        """Get tutorial completion progress (0-100)"""
        return self.tutorial_manager.get_tutorial_progress()


# Quick integration example for your app_module_pyqt.py:
"""
Example integration in your ProjectCreatorApp class:

class ProjectCreatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... your existing init code ...
        
        # Add onboarding system
        from app.onboarding.integration import OnboardingIntegration
        self.onboarding = OnboardingIntegration(self)
        
        # ... rest of your init ...
        
        # After UI setup is complete:
        self.onboarding.setup_ui_references()
        self.onboarding.initialize()
    
    def create_menu(self):
        # ... your existing menu code ...
        
        # Add tutorial menu items to Help menu
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("Show Welcome Tutorial", self.onboarding.show_welcome)
        help_menu.addAction("Show Guided Tour", self.onboarding.show_guided_tour)
        help_menu.addSeparator()
        help_menu.addAction("Reset Tutorials", self.onboarding.reset_tutorials)
""" 