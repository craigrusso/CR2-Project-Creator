#!/usr/bin/env python3
import unittest
import sys
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QMessageBox

# Create QApplication instance before importing Qt widgets
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# Import the class under test
from app.templates.gallery_events import GalleryEvents

class TestFolderDeletion(unittest.TestCase):
    """Test cases for folder deletion using the delete key."""
    
    def setUp(self):
        """Set up the test environment."""
        # Mock the template manager with a working delete_folder method
        self.template_manager = MagicMock()
        self.template_manager.delete_folder = MagicMock(return_value=True)
        self.template_manager.load_folders = MagicMock()
        
        # Mock the app with a reference to the template manager
        self.app = MagicMock()
        self.app.template_manager = self.template_manager
        self.app.show_status_message = MagicMock()
        
        # Mock the gallery with a selected folder
        self.gallery = MagicMock()
        self.gallery.app = self.app
        self.gallery.selected_folder = "TestFolder"
        self.gallery.populate_gallery = MagicMock()
        
        # Ensure gallery has the necessary attributes that the method checks for
        self.gallery.selected_template = None
        self.gallery.multi_selected_templates = []
        self.gallery.isDialogOpen = False

    @patch('app.templates.gallery_events.QMessageBox')
    def test_delete_folder_with_delete_key(self, mock_message_box):
        """Test deleting a folder with Delete key."""
        # Create a delete key event
        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
        
        # Call the method under test
        result = GalleryEvents.key_press_event(self.gallery, event)
        
        # Verify the folder was deleted
        self.template_manager.delete_folder.assert_called_once_with("TestFolder")
        
        # Verify the gallery was refreshed
        self.gallery.populate_gallery.assert_called_once()
        
        # Verify the selected folder was cleared
        self.assertIsNone(self.gallery.selected_folder)
        
        # Verify a success message was shown
        self.app.show_status_message.assert_called_once()
        
        # Verify the event was handled
        self.assertTrue(result)
    
    @patch('app.templates.gallery_events.QMessageBox')
    def test_delete_folder_with_backspace_key(self, mock_message_box):
        """Test deleting a folder with Backspace key."""
        # Create a backspace key event
        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Backspace, Qt.NoModifier)
        
        # Call the method under test
        result = GalleryEvents.key_press_event(self.gallery, event)
        
        # Verify the folder was deleted
        self.template_manager.delete_folder.assert_called_once_with("TestFolder")
        
        # Verify the gallery was refreshed
        self.gallery.populate_gallery.assert_called_once()
        
        # Verify the selected folder was cleared
        self.assertIsNone(self.gallery.selected_folder)
        
        # Verify a success message was shown
        self.app.show_status_message.assert_called_once()
        
        # Verify the event was handled
        self.assertTrue(result)
    
    @patch('app.templates.gallery_events.QMessageBox.warning')
    def test_cannot_delete_default_folder(self, mock_warning):
        """Test that default folders cannot be deleted."""
        # Set up the mock return value
        mock_warning.return_value = None
        
        # Set the selected folder to a default folder
        self.gallery.selected_folder = "General"
        
        # Create a delete key event
        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
        
        # Call the method under test
        result = GalleryEvents.key_press_event(self.gallery, event)
        
        # Verify a warning was shown (with any arguments)
        mock_warning.assert_called_once()
        
        # Verify delete_folder was NOT called
        self.template_manager.delete_folder.assert_not_called()
        
        # Verify the event was handled
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
    # Make sure to quit the app
    sys.exit(app.exec_()) 