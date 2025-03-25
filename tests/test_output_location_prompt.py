#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QFileDialog
from app.core.app_module_pyqt import ProjectCreatorApp
from app.core.project_operations import create_project


class TestOutputLocationPrompt(unittest.TestCase):
    """Test that the application prompts for output location when none is selected"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Create a QApplication instance
        cls.app = QApplication.instance() or QApplication([])
        
        # Create temporary directory for testing
        cls.temp_dir = tempfile.mkdtemp()
        cls.output_dir = os.path.join(cls.temp_dir, "output")
        os.makedirs(cls.output_dir, exist_ok=True)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        # Remove temporary directory
        shutil.rmtree(cls.temp_dir)
        
    def setUp(self):
        """Set up for each test"""
        # Create the application
        self.project_app = ProjectCreatorApp()
        # Clear output directory
        self.project_app.output_dir_input.setText("")
        
    def tearDown(self):
        """Clean up after each test"""
        self.project_app.close()
        
    @patch('app.core.app_module_pyqt.QFileDialog.getExistingDirectory')
    def test_batch_create_prompts_for_output_location(self, mock_dialog):
        """Test that batch project creation prompts for output location if none is selected"""
        # Set up mock to return a directory
        mock_dialog.return_value = self.output_dir
        
        # Set up project names
        self.project_app.batch_text_edit.setPlainText("Test Project")
        
        # Set up a template
        self.project_app.selected_template = {
            'name': 'Test Template',
            'path': os.path.join(self.temp_dir, 'test_template.json'),
            'type': 'file'
        }
        
        # Force the output directory to be None
        # Since we're now using use_fallbacks=False, we don't need to override get_current_output_dir
        # We just need to ensure the output dir input is empty
        self.project_app.output_dir_input.setText("")
            
        # Mock show_status_message to capture message
        self.project_app.show_status_message = MagicMock()
        
        # Mock handle_batch_create to avoid actual project creation
        with patch('app.core.app_module_pyqt.handle_batch_create', return_value={}):
            # Call batch project creation
            self.project_app.process_batch_projects()
            
            # Verify that getExistingDirectory was called at least once
            mock_dialog.assert_called()
                
    @patch('app.core.app_module_pyqt.QFileDialog.getExistingDirectory')
    def test_batch_create_shows_warning_if_cancelled(self, mock_dialog):
        """Test that batch project creation shows warning if user cancels output location selection"""
        # Set up mock to return empty string (cancelled)
        mock_dialog.return_value = ""
        
        # Set up project names
        self.project_app.batch_text_edit.setPlainText("Test Project")
        
        # Set up a template
        self.project_app.selected_template = {
            'name': 'Test Template',
            'path': os.path.join(self.temp_dir, 'test_template.json'),
            'type': 'file'
        }
        
        # Ensure output dir input is empty
        self.project_app.output_dir_input.setText("")
        
        # Mock show_status_message to capture message
        self.project_app.show_status_message = MagicMock()
        
        # Call batch project creation
        self.project_app.process_batch_projects()
        
        # Verify that getExistingDirectory was called at least once
        mock_dialog.assert_called()
        
        # Verify that warning message was shown
        self.project_app.show_status_message.assert_called_once_with(
            "Please select an output location to create projects", message_type="warning")
            
    @patch('app.core.app_module_pyqt.QFileDialog.getExistingDirectory')
    def test_single_project_prompts_for_output_location(self, mock_dialog):
        """Test that single project creation prompts for output location if none is selected"""
        # Set up mock to return a directory
        mock_dialog.return_value = self.output_dir
        
        # Mock project name input as it doesn't exist directly on ProjectCreatorApp
        self.project_app.project_name_input = MagicMock()
        self.project_app.project_name_input.text = MagicMock(return_value="Test Project")
        
        # Set up a template
        self.project_app.selected_template = {
            'name': 'Test Template',
            'path': os.path.join(self.temp_dir, 'test_template.json'),
            'type': 'file'
        }
        
        # Ensure output dir input is empty
        self.project_app.output_dir_input.setText("")
        
        # Mock QMessageBox.information to avoid dialog
        with patch('app.core.project_operations.QMessageBox.information'), \
             patch('app.core.project_operations.QMessageBox.critical'), \
             patch('app.core.project_builder.ProjectBuilder.create_project', return_value=(True, self.output_dir)):
            
            # Call create_project
            create_project(self.project_app)
            
            # Verify that getExistingDirectory was called at least once
            mock_dialog.assert_called()
    
    def test_fallback_behavior(self):
        """Test that fallback behavior works correctly when enabled"""
        # Set up output directory in config
        test_dir = os.path.join(self.temp_dir, "config_test_dir")
        os.makedirs(test_dir, exist_ok=True)
        self.project_app.config["last_output_dir"] = test_dir
        
        # Make sure UI field is empty
        self.project_app.output_dir_input.setText("")
        
        # With fallbacks enabled, should return the config dir
        output_dir = self.project_app.get_current_output_dir(use_fallbacks=True)
        self.assertEqual(output_dir, test_dir)
        
        # Without fallbacks, should return None
        output_dir = self.project_app.get_current_output_dir(use_fallbacks=False)
        self.assertIsNone(output_dir)


if __name__ == '__main__':
    unittest.main() 