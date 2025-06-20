#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Onboarding Integration Helper

Simplified integration for adding onboarding tutorials to existing PyQt6 applications.
Just instantiate this class in your main app and call the setup methods.
"""

from .tutorial_manager import TutorialManager


class OnboardingIntegration:
    """Simplified integration helper for onboarding tutorials"""
    
    def __init__(self, main_app):
        """Initialize with main application instance"""
        self.main_app = main_app
        self.tutorial_manager = TutorialManager(main_app)
        
        # Connect tutorial events (optional - for analytics, etc.)
        self.tutorial_manager.tutorial_started.connect(self._on_tutorial_started)
        self.tutorial_manager.tutorial_completed.connect(self._on_tutorial_completed)
        self.tutorial_manager.all_tutorials_completed.connect(self._on_all_completed)
    
    def setup_ui_references(self):
        """Map your app's widgets to tutorial system expectations"""
        # This method can be expanded to set up widget references
        # if needed for future enhancements
        pass
    
    def initialize(self):
        """Initialize the tutorial system - call after UI is fully set up"""
        self.tutorial_manager.initialize()
    
    # Public methods for menu integration
    def show_welcome(self):
        """Show welcome slideshow (for menu action)"""
        self.tutorial_manager.show_slideshow_manually()
    
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
        """Handle all tutorials completion (optional - for analytics, etc.)"""
        print("All tutorials completed")


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
        help_menu.addAction("Reset Tutorials", self.onboarding.reset_tutorials)
""" 