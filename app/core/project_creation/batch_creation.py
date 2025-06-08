#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import re
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

from app.core.project_operations import handle_batch_create
from .sequence_generator import SequenceGenerator


class BatchCreationManager:
    """Handles batch project creation logic"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window
        
        Args:
            main_window: Reference to the main application window
        """
        self.main_window = main_window
    
    def process_batch_projects(self):
        """Process the entered project names for batch creation"""
        # Get project names from text area
        text = self.main_window.batch_text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self.main_window, "Warning", "Please enter at least one project name.")
            return
        
        # Parse project names
        project_names = re.split(r'[\n,;]+', text)
        project_names = [name.strip() for name in project_names if name.strip()]
        
        if not project_names:
            QMessageBox.warning(self.main_window, "Warning", "No valid project names found.")
            return
        
        # Generate final list with sequences if enabled
        final_projects = []
        for base_name in project_names:
            sequence_names = self._generate_sequence_names(base_name)
            final_projects.extend(sequence_names)
        
        # Show confirmation
        if QMessageBox.question(
            self.main_window, 
            "Confirm Batch Creation", 
            f"You are about to create {len(final_projects)} projects.\n\nDo you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.No:
            return
        
        # Show creating message in status bar
        self.main_window.show_status_message(f"Creating {len(final_projects)} projects...", message_type="info")
        
        # Convert list to text for handle_batch_create
        projects_text = "\n".join(final_projects)
        
        # Start batch creation process
        self.main_window.batch_results = handle_batch_create(self.main_window, projects_text)
        
        # Start result checking timer
        if not hasattr(self.main_window, 'batch_check_timer'):
            self.main_window.batch_check_timer = QTimer()
            self.main_window.batch_check_timer.timeout.connect(self.main_window.check_batch_results)
        
        self.main_window.batch_check_timer.start(500)  # Check every 500ms
    
    def handle_enhanced_batch_creation(self, project_names):
        """Handle the project creation from the enhanced dialog
        
        Args:
            project_names (list): List of project names to create
        """
        # Show creating message in status bar
        self.main_window.show_status_message(f"Creating {len(project_names)} projects...", message_type="info")
        
        # Convert list of project names to a string for handle_batch_create
        projects_text = "\n".join(project_names)
        
        # Start batch creation process
        self.main_window.batch_results = handle_batch_create(self.main_window, projects_text)
        
        # Start result checking timer
        if not hasattr(self.main_window, 'batch_check_timer'):
            self.main_window.batch_check_timer = QTimer()
            self.main_window.batch_check_timer.timeout.connect(self.main_window.check_batch_results)
        
        self.main_window.batch_check_timer.start(500)  # Check every 500ms
    
    def _generate_sequence_names(self, base_name):
        """Generate sequence names based on current settings (wrapper for SequenceGenerator)
        
        Args:
            base_name (str): The base project name
            
        Returns:
            list: List of generated sequence names
        """
        # Collect UI widgets into dictionary for the sequence generator
        ui_widgets = {
            'enable_versioning': self.main_window.enable_versioning,
            'sequence_type': self.main_window.sequence_type,
            'name_position': self.main_window.name_position,
            'start_date': self.main_window.start_date,
            'date_count': self.main_window.date_count,
            'date_interval': self.main_window.date_interval,
            'date_interval_type': self.main_window.date_interval_type,
            'date_format': self.main_window.date_format,
            'version_count': self.main_window.version_count,
            'version_format': self.main_window.version_format,
            'number_start': self.main_window.number_start,
            'number_count': self.main_window.number_count,
            'number_format': self.main_window.number_format,
        }
        
        return SequenceGenerator.generate_sequence_names(base_name, ui_widgets) 