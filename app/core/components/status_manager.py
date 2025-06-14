#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Status bar and message management component
"""

from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import QTimer


class StatusManager:
    """Handles status bar and status message display"""
    
    def __init__(self, app_instance):
        """Initialize the status manager"""
        self.app = app_instance
        
    def setup_status_bar(self):
        """Set up the status bar"""
        print("DEBUG: Creating status bar...")
        
        # Create status bar
        self.app.status_bar = QStatusBar()
        self.app.setStatusBar(self.app.status_bar)
        self.app.status_message = QLabel("")
        self.app.status_bar.addWidget(self.app.status_message)
        
        # Configure status bar for proper text display
        self.app.status_bar.setStyleSheet("""
            QStatusBar { 
                padding-left: 8px; 
                min-height: 24px;
            }
            QStatusBar::item {
                border: none;
                padding-left: 8px;
            }
        """)
        
        print("DEBUG: Status bar created")
    
    def show_status_message(self, message, message_type="info", duration=5000):
        """Show a status message with optional color coding and auto-clear"""
        if not hasattr(self.app, 'status_message') or not self.app.status_message:
            return
        
        # Color coding based on message type
        color_map = {
            "info": "#E0E0E0",      # Light gray for info
            "success": "#4CAF50",   # Green for success
            "warning": "#FF9800",   # Orange for warnings
            "error": "#F44336"      # Red for errors
        }
        
        color = color_map.get(message_type, "#E0E0E0")
        
        # Set the styled message
        self.app.status_message.setText(message)
        self.app.status_message.setStyleSheet(f"color: {color};")
        
        # Stop any existing timer
        if hasattr(self.app, 'status_message_timer'):
            self.app.status_message_timer.stop()
        
        # Set up auto-clear timer for non-permanent messages
        if duration > 0 and message_type != "error":  # Keep error messages visible longer
            self.app.status_message_timer.start(duration)
    
    def _reset_status_bar(self):
        """Reset the status bar to default state"""
        if hasattr(self.app, 'status_message') and self.app.status_message:
            self.app.status_message.setText("")
            self.app.status_message.setStyleSheet("color: #E0E0E0;")
        
        if hasattr(self.app, 'status_message_timer'):
            self.app.status_message_timer.stop()
    
    def show_permanent_message(self, message, message_type="info"):
        """Show a permanent status message that won't auto-clear"""
        self.show_status_message(message, message_type, duration=0)
    
    def clear_status_message(self):
        """Manually clear the status message"""
        self._reset_status_bar()
    
    def show_loading_message(self, message):
        """Show a loading message with info styling"""
        self.show_status_message(f"⏳ {message}", "info", duration=0)
    
    def show_success_message(self, message, duration=3000):
        """Show a success message with green styling"""
        self.show_status_message(f"✓ {message}", "success", duration)
    
    def show_warning_message(self, message, duration=5000):
        """Show a warning message with orange styling"""
        self.show_status_message(f"⚠ {message}", "warning", duration)
    
    def show_error_message(self, message, duration=10000):
        """Show an error message with red styling (longer duration)"""
        self.show_status_message(f"✗ {message}", "error", duration)
    
    def update_path_display(self, path):
        """Update status bar to show a file path"""
        if path:
            # Truncate long paths for better display
            from app.utils.utils import truncate_path
            display_path = truncate_path(path, max_length=80)
            self.show_permanent_message(f"Location: {display_path}", "info")
    
    def show_project_creation_status(self, project_name, path):
        """Show status for successful project creation"""
        self.show_success_message(f"Project '{project_name}' created at: {path}")
        
    def show_batch_creation_status(self, successful_count, total_count):
        """Show status for batch project creation"""
        if successful_count == total_count:
            self.show_success_message(f"Successfully created {successful_count} projects")
        elif successful_count > 0:
            self.show_warning_message(f"Created {successful_count} of {total_count} projects")
        else:
            self.show_error_message(f"Failed to create any projects ({total_count} attempted)")
    
    def show_template_status(self, template_name, action="selected"):
        """Show status for template operations"""
        if action == "selected":
            self.show_status_message(f"Template selected: {template_name}", "info")
        elif action == "loaded":
            self.show_success_message(f"Template loaded: {template_name}")
        elif action == "error":
            self.show_error_message(f"Error with template: {template_name}")
    
    def show_file_operation_status(self, operation, file_path, success=True):
        """Show status for file operations"""
        from app.utils.utils import truncate_path
        display_path = truncate_path(file_path, max_length=60)
        
        if success:
            self.show_success_message(f"{operation} completed: {display_path}")
        else:
            self.show_error_message(f"{operation} failed: {display_path}")
    
    def show_update_status(self, message, has_update=False):
        """Show status for update checks"""
        if has_update:
            self.show_status_message(f"🔄 {message}", "warning", duration=10000)
        else:
            self.show_status_message(message, "info", duration=3000) 