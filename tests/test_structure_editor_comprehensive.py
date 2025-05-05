#!/usr/bin/env python3
# Comprehensive test script for structure editor and structure preview
# Tests edge cases and potential crash scenarios

import os
import sys
import tempfile
import shutil
import time
import json
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QTreeWidget, QTreeWidgetItem,
                           QTabWidget, QWidget, QMessageBox, QFileDialog,
                           QListWidget, QComboBox)
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QDrag, QPixmap

# Import app modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_gallery_ui_pyqt import TemplateGallery
from app.dialogs.dialog_windows_pyqt import preview_structure

class TestSignals(QObject):
    """Signal handler for test events"""
    test_completed = pyqtSignal(bool, str)

class StructureEditorTester(QDialog):
    """Test harness for structure editor and preview functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Structure Editor Comprehensive Test")
        self.setMinimumSize(900, 700)
        
        # Create managers
        self.template_manager = TemplateManager()
        self.project_builder = ProjectBuilder(self.template_manager)
        
        # Create signal handler
        self.signals = TestSignals()
        
        # Setup UI
        self.init_ui()
        
        # Test results storage
        self.test_results = {}
        self.current_test = None
        self.temp_dirs = []
        
        # Track structure editor instance
        self.structure_editor = None
        
    def init_ui(self):
        """Initialize the test UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Structure Editor & Preview Comprehensive Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Description
        description = QLabel(
            "This test suite checks the structure editor and structure preview "
            "functionality for edge cases that might cause crashes or incorrect behavior."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create tab widget for test categories
        self.tabs = QTabWidget()
        
        # Tab 1: Structure Editor Tests
        self.editor_tab = QWidget()
        editor_layout = QVBoxLayout(self.editor_tab)
        
        editor_intro = QLabel("Tests for structure editor functionality:")
        editor_layout.addWidget(editor_intro)
        
        # Structure editor test buttons
        self.editor_tests_list = QListWidget()
        self.editor_tests_list.addItems([
            "Create New Structure",
            "Edit Existing Structure",
            "File/Folder with Same Name",
            "JSON vs Folder Conflict",
            "Nested JSON Files",
            "Empty Structure",
            "Very Large Structure (100+ items)",
            "Special Characters in Names",
            "Unicode Characters (Emoji)",
            "Create and Immediately Edit",
            "Duplicate Structure",
            "Change Item Type"
        ])
        editor_layout.addWidget(self.editor_tests_list)
        
        editor_run_btn = QPushButton("Run Selected Editor Test")
        editor_run_btn.clicked.connect(self.run_editor_test)
        editor_layout.addWidget(editor_run_btn)
        
        # Tab 2: Structure Preview Tests
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        
        preview_intro = QLabel("Tests for structure preview functionality:")
        preview_layout.addWidget(preview_intro)
        
        # Structure preview test buttons
        self.preview_tests_list = QListWidget()
        self.preview_tests_list.addItems([
            "Preview Empty Structure",
            "Preview Complex Structure",
            "Preview with JSON File/Folder Conflicts",
            "Preview Structure with Special Characters",
            "Preview Structure with Unicode Characters",
            "Preview Structure with Nested Empty Folders",
            "Preview Very Large Structure",
            "Multiple Preview Windows",
            "Rapid Open/Close Preview",
            "Preview Structure with Placeholder Variables"
        ])
        preview_layout.addWidget(self.preview_tests_list)
        
        preview_run_btn = QPushButton("Run Selected Preview Test")
        preview_run_btn.clicked.connect(self.run_preview_test)
        preview_layout.addWidget(preview_run_btn)
        
        # Tab 3: Integration Tests
        self.integration_tab = QWidget()
        integration_layout = QVBoxLayout(self.integration_tab)
        
        integration_intro = QLabel("Integration tests combining editor and preview:")
        integration_layout.addWidget(integration_intro)
        
        # Integration test buttons
        self.integration_tests_list = QListWidget()
        self.integration_tests_list.addItems([
            "Create Structure & Preview",
            "Edit Structure & Preview Changes",
            "Create Project from Structure",
            "Create Project from Structure with JSON Conflicts",
            "Save Structure & Reload",
            "Editor to Project Creation Pipeline",
            "Structure Sharing Between Components",
            "Multiple Operations Sequence"
        ])
        integration_layout.addWidget(self.integration_tests_list)
        
        integration_run_btn = QPushButton("Run Selected Integration Test")
        integration_run_btn.clicked.connect(self.run_integration_test)
        integration_layout.addWidget(integration_run_btn)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.editor_tab, "Editor Tests")
        self.tabs.addTab(self.preview_tab, "Preview Tests")
        self.tabs.addTab(self.integration_tab, "Integration Tests")
        
        layout.addWidget(self.tabs)
        
        # Results area
        results_label = QLabel("Test Results:")
        layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        layout.addWidget(self.results_list)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        run_all_btn = QPushButton("Run All Tests")
        run_all_btn.clicked.connect(self.run_all_tests)
        btn_layout.addWidget(run_all_btn)
        
        clear_btn = QPushButton("Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Connect signals
        self.signals.test_completed.connect(self.on_test_completed)
        
    def log_result(self, message, is_error=False):
        """Log a test result"""
        item_text = f"[ERROR] {message}" if is_error else message
        self.results_list.addItem(item_text)
        if is_error:
            print(f"ERROR: {message}")
        else:
            print(message)
        
        # Scroll to bottom
        self.results_list.scrollToBottom()
        
        # Process events to update UI
        QApplication.processEvents()
    
    def on_test_completed(self, success, message):
        """Handle test completion signal"""
        if success:
            self.log_result(f"✅ {self.current_test}: {message}")
            self.test_results[self.current_test] = True
        else:
            self.log_result(f"❌ {self.current_test}: {message}", True)
            self.test_results[self.current_test] = False
        
        self.current_test = None
    
    def clear_results(self):
        """Clear test results"""
        self.results_list.clear()
        self.test_results = {}
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.clear_results()
        self.log_result("Starting all tests...")
        
        # Run editor tests
        for i in range(self.editor_tests_list.count()):
            self.editor_tests_list.setCurrentRow(i)
            self.run_editor_test()
            QApplication.processEvents()
            time.sleep(0.5)
        
        # Run preview tests
        for i in range(self.preview_tests_list.count()):
            self.preview_tests_list.setCurrentRow(i)
            self.run_preview_test()
            QApplication.processEvents()
            time.sleep(0.5)
        
        # Run integration tests
        for i in range(self.integration_tests_list.count()):
            self.integration_tests_list.setCurrentRow(i)
            self.run_integration_test()
            QApplication.processEvents()
            time.sleep(0.5)
        
        # Show summary
        self.log_result("\n===== TEST SUMMARY =====")
        total = len(self.test_results)
        passed = sum(1 for result in self.test_results.values() if result)
        self.log_result(f"Total tests: {total}")
        self.log_result(f"Passed: {passed}")
        self.log_result(f"Failed: {total - passed}")
        
        if passed == total:
            self.log_result("All tests passed! 🎉")
        else:
            self.log_result("Some tests failed. Check details above.", True)
    
    def run_editor_test(self):
        """Run selected structure editor test"""
        selected_items = self.editor_tests_list.selectedItems()
        if not selected_items:
            self.log_result("No editor test selected", True)
            return
        
        test_name = selected_items[0].text()
        self.current_test = test_name
        self.log_result(f"Running editor test: {test_name}")
        
        try:
            # Call appropriate test method based on test name
            if test_name == "Create New Structure":
                self.test_create_new_structure()
            elif test_name == "Edit Existing Structure":
                self.test_edit_existing_structure()
            elif test_name == "File/Folder with Same Name":
                self.test_file_folder_same_name()
            elif test_name == "JSON vs Folder Conflict":
                self.test_json_folder_conflict()
            elif test_name == "Nested JSON Files":
                self.test_nested_json_files()
            elif test_name == "Empty Structure":
                self.test_empty_structure()
            elif test_name == "Very Large Structure (100+ items)":
                self.test_large_structure()
            elif test_name == "Special Characters in Names":
                self.test_special_characters()
            elif test_name == "Unicode Characters (Emoji)":
                self.test_unicode_characters()
            elif test_name == "Create and Immediately Edit":
                self.test_create_and_edit()
            elif test_name == "Duplicate Structure":
                self.test_duplicate_structure()
            elif test_name == "Change Item Type":
                self.test_change_item_type()
            else:
                self.log_result(f"Unknown test: {test_name}", True)
        except Exception as e:
            import traceback
            self.log_result(f"Test '{test_name}' failed with exception: {e}", True)
            self.log_result(traceback.format_exc(), True)
            self.signals.test_completed.emit(False, f"Exception: {e}")
    
    def run_preview_test(self):
        """Run selected structure preview test"""
        selected_items = self.preview_tests_list.selectedItems()
        if not selected_items:
            self.log_result("No preview test selected", True)
            return
        
        test_name = selected_items[0].text()
        self.current_test = test_name
        self.log_result(f"Running preview test: {test_name}")
        
        try:
            # Call appropriate test method based on test name
            if test_name == "Preview Empty Structure":
                self.test_preview_empty()
            elif test_name == "Preview Complex Structure":
                self.test_preview_complex()
            elif test_name == "Preview with JSON File/Folder Conflicts":
                self.test_preview_json_conflicts()
            elif test_name == "Preview Structure with Special Characters":
                self.test_preview_special_chars()
            elif test_name == "Preview Structure with Unicode Characters":
                self.test_preview_unicode()
            elif test_name == "Preview Structure with Nested Empty Folders":
                self.test_preview_nested_empty()
            elif test_name == "Preview Very Large Structure":
                self.test_preview_large()
            elif test_name == "Multiple Preview Windows":
                self.test_multiple_previews()
            elif test_name == "Rapid Open/Close Preview":
                self.test_rapid_preview()
            elif test_name == "Preview Structure with Placeholder Variables":
                self.test_preview_placeholders()
            else:
                self.log_result(f"Unknown test: {test_name}", True)
        except Exception as e:
            import traceback
            self.log_result(f"Test '{test_name}' failed with exception: {e}", True)
            self.log_result(traceback.format_exc(), True)
            self.signals.test_completed.emit(False, f"Exception: {e}")
    
    def run_integration_test(self):
        """Run selected integration test"""
        selected_items = self.integration_tests_list.selectedItems()
        if not selected_items:
            self.log_result("No integration test selected", True)
            return
        
        test_name = selected_items[0].text()
        self.current_test = test_name
        self.log_result(f"Running integration test: {test_name}")
        
        try:
            # Call appropriate test method based on test name
            if test_name == "Create Structure & Preview":
                self.test_create_and_preview()
            elif test_name == "Edit Structure & Preview Changes":
                self.test_edit_and_preview()
            elif test_name == "Create Project from Structure":
                self.test_create_project()
            elif test_name == "Create Project from Structure with JSON Conflicts":
                self.test_create_project_json_conflicts()
            elif test_name == "Save Structure & Reload":
                self.test_save_and_reload()
            elif test_name == "Editor to Project Creation Pipeline":
                self.test_editor_to_project()
            elif test_name == "Structure Sharing Between Components":
                self.test_structure_sharing()
            elif test_name == "Multiple Operations Sequence":
                self.test_multiple_operations()
            else:
                self.log_result(f"Unknown test: {test_name}", True)
        except Exception as e:
            import traceback
            self.log_result(f"Test '{test_name}' failed with exception: {e}", True)
            self.log_result(traceback.format_exc(), True)
            self.signals.test_completed.emit(False, f"Exception: {e}")
    
    # === Editor Test Methods ===
    
    def test_create_new_structure(self):
        """Test creating a new structure from scratch"""
        try:
            # Create a new structure editor
            self.structure_editor = EnhancedStructureEditor(self, is_new=True)
            self.structure_editor.show()
            
            # Set a unique name
            structure_name = f"test_structure_{int(time.time())}"
            self.structure_editor.name_input.setText(structure_name)
            
            # Add a folder and a file
            QTimer.singleShot(500, lambda: self._add_test_folder_and_file())
            
            # Save the structure
            QTimer.singleShot(1500, lambda: self._save_current_editor())
            
            # Close the editor
            QTimer.singleShot(2000, lambda: self._close_editor_with_success())
        except Exception as e:
            self.signals.test_completed.emit(False, f"Failed to create new structure: {e}")
    
    def test_edit_existing_structure(self):
        """Test editing an existing structure"""
        try:
            # First create a test structure
            structure_name = f"test_edit_structure_{int(time.time())}"
            structure = [
                "README.md",
                {"src": ["index.js", "app.js"]},
                "package.json"
            ]
            
            # Save the structure
            success = self.template_manager.save_custom_structure(structure_name, structure)
            if not success:
                self.signals.test_completed.emit(False, "Failed to create test structure")
                return
            
            # Now open it in the editor
            self.structure_editor = EnhancedStructureEditor(self, structure_name=structure_name, structure=structure)
            self.structure_editor.show()
            
            # Add a new folder
            QTimer.singleShot(500, lambda: self._add_folder_to_editor("test_folder"))
            
            # Save the structure
            QTimer.singleShot(1500, lambda: self._save_current_editor())
            
            # Close the editor
            QTimer.singleShot(2000, lambda: self._close_editor_with_success())
        except Exception as e:
            self.signals.test_completed.emit(False, f"Failed to edit existing structure: {e}")
    
    def test_file_folder_same_name(self):
        """Test creating a file and folder with the same name"""
        try:
            # Create a new structure editor
            self.structure_editor = EnhancedStructureEditor(self, is_new=True)
            self.structure_editor.show()
            
            # Set a unique name
            structure_name = f"test_same_name_{int(time.time())}"
            self.structure_editor.name_input.setText(structure_name)
            
            # Add a folder and a file with the same name
            QTimer.singleShot(500, lambda: self._add_same_name_items())
            
            # Save the structure
            QTimer.singleShot(1500, lambda: self._save_current_editor())
            
            # Close the editor
            QTimer.singleShot(2000, lambda: self._close_editor_with_success())
        except Exception as e:
            self.signals.test_completed.emit(False, f"Failed in file/folder same name test: {e}")
    
    def test_json_folder_conflict(self):
        """Test creating JSON files and folders with same names"""
        try:
            # Create a new structure editor
            self.structure_editor = EnhancedStructureEditor(self, is_new=True)
            self.structure_editor.show()
            
            # Set a unique name
            structure_name = f"test_json_conflict_{int(time.time())}"
            self.structure_editor.name_input.setText(structure_name)
            
            # Add JSON files and folders with same names
            QTimer.singleShot(500, lambda: self._add_json_conflicts())
            
            # Save the structure
            QTimer.singleShot(1500, lambda: self._save_current_editor())
            
            # Close the editor
            QTimer.singleShot(2000, lambda: self._close_editor_with_success())
        except Exception as e:
            self.signals.test_completed.emit(False, f"Failed in JSON/folder conflict test: {e}")
    
    # Implement remaining test methods
    
    # === Preview Test Methods ===
    
    def test_preview_empty(self):
        """Test previewing an empty structure"""
        try:
            # Create an empty structure
            empty_structure = []
            
            # Show preview
            preview_structure(self, empty_structure)
            
            # Close preview after a delay
            QTimer.singleShot(1000, lambda: self._close_all_dialogs_with_success())
        except Exception as e:
            self.signals.test_completed.emit(False, f"Failed to preview empty structure: {e}")
    
    # Implement remaining preview test methods
    
    # === Integration Test Methods ===
    
    def test_create_and_preview(self):
        """Test creating a structure and then previewing it"""
        try:
            # Create a new structure editor
            self.structure_editor = EnhancedStructureEditor(self, is_new=True)
            self.structure_editor.show()
            
            # Set a unique name
            structure_name = f"test_create_preview_{int(time.time())}"
            self.structure_editor.name_input.setText(structure_name)
            
            # Add some content
            QTimer.singleShot(500, lambda: self._add_complex_structure())
            
            # Save the structure
            QTimer.singleShot(1500, lambda: self._save_current_editor())
            
            # Close the editor
            QTimer.singleShot(2000, lambda: self._close_editor())
            
            # Open preview after editor is closed
            QTimer.singleShot(2500, lambda: self._preview_saved_structure(structure_name))
            
            # Close preview after a delay
            QTimer.singleShot(3500, lambda: self._close_all_dialogs_with_success())
        except Exception as e:
            self.signals.test_completed.emit(False, f"Failed in create and preview test: {e}")
    
    # Implement remaining integration test methods
    
    # === Helper Methods ===
    
    def _add_test_folder_and_file(self):
        """Add a test folder and file to the structure editor"""
        try:
            # Get the root item
            root_item = self.structure_editor.tree.invisibleRootItem().child(0)
            
            # Add a folder
            self.structure_editor.tree.setCurrentItem(root_item)
            folder_item = self.structure_editor.add_folder()
            folder_item.setText(0, "test_folder")
            
            # Add a file
            file_item = QTreeWidgetItem(root_item)
            file_item.setText(0, "test_file.txt")
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            file_item.setData(0, Qt.UserRole, "file")
            
            self.log_result("Added test folder and file to editor")
        except Exception as e:
            self.log_result(f"Failed to add test items: {e}", True)
    
    def _add_folder_to_editor(self, folder_name):
        """Add a folder to the current editor"""
        try:
            # Get the root item
            root_item = self.structure_editor.tree.invisibleRootItem().child(0)
            
            # Add a folder
            self.structure_editor.tree.setCurrentItem(root_item)
            folder_item = self.structure_editor.add_folder()
            folder_item.setText(0, folder_name)
            
            self.log_result(f"Added folder '{folder_name}' to editor")
        except Exception as e:
            self.log_result(f"Failed to add folder: {e}", True)
    
    def _add_same_name_items(self):
        """Add items with the same name (one file, one folder)"""
        try:
            # Get the root item
            root_item = self.structure_editor.tree.invisibleRootItem().child(0)
            
            # Add a folder
            self.structure_editor.tree.setCurrentItem(root_item)
            folder_item = self.structure_editor.add_folder()
            folder_item.setText(0, "same_name")
            
            # Add a file with the same name
            file_item = QTreeWidgetItem(root_item)
            file_item.setText(0, "same_name")
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            file_item.setData(0, Qt.UserRole, "file")
            
            self.log_result("Added items with the same name (file and folder)")
        except Exception as e:
            self.log_result(f"Failed to add same-name items: {e}", True)
    
    def _add_json_conflicts(self):
        """Add JSON files and folders with same names"""
        try:
            # Get the root item
            root_item = self.structure_editor.tree.invisibleRootItem().child(0)
            
            # Add a JSON file
            file_item = QTreeWidgetItem(root_item)
            file_item.setText(0, "config.json")
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            file_item.setData(0, Qt.UserRole, "file")
            
            # Add a folder with the same name
            self.structure_editor.tree.setCurrentItem(root_item)
            folder_item = self.structure_editor.add_folder()
            folder_item.setText(0, "config.json")
            
            # Add a child file to the folder
            child_file = QTreeWidgetItem(folder_item)
            child_file.setText(0, "settings.json")
            child_file.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            child_file.setData(0, Qt.UserRole, "file")
            
            self.log_result("Added JSON file and folder with the same name")
        except Exception as e:
            self.log_result(f"Failed to add JSON conflicts: {e}", True)
    
    def _add_complex_structure(self):
        """Add a complex structure to the editor"""
        try:
            # Get the root item
            root_item = self.structure_editor.tree.invisibleRootItem().child(0)
            
            # Add a README file
            readme_item = QTreeWidgetItem(root_item)
            readme_item.setText(0, "README.md")
            readme_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            readme_item.setData(0, Qt.UserRole, "file")
            
            # Add src folder
            self.structure_editor.tree.setCurrentItem(root_item)
            src_folder = self.structure_editor.add_folder()
            src_folder.setText(0, "src")
            
            # Add files to src folder
            index_file = QTreeWidgetItem(src_folder)
            index_file.setText(0, "index.js")
            index_file.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            index_file.setData(0, Qt.UserRole, "file")
            
            # Add components subfolder
            self.structure_editor.tree.setCurrentItem(src_folder)
            comp_folder = self.structure_editor.add_folder()
            comp_folder.setText(0, "components")
            
            # Add files to components folder
            app_file = QTreeWidgetItem(comp_folder)
            app_file.setText(0, "App.js")
            app_file.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            app_file.setData(0, Qt.UserRole, "file")
            
            # Add package.json to root
            pkg_file = QTreeWidgetItem(root_item)
            pkg_file.setText(0, "package.json")
            pkg_file.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            pkg_file.setData(0, Qt.UserRole, "file")
            
            self.log_result("Added complex structure to editor")
        except Exception as e:
            self.log_result(f"Failed to add complex structure: {e}", True)
    
    def _save_current_editor(self):
        """Save the current structure editor"""
        try:
            if not self.structure_editor:
                self.log_result("No structure editor to save", True)
                return
            
            # Click the save button
            if hasattr(self.structure_editor, 'save_btn') and self.structure_editor.save_btn:
                self.structure_editor.save_btn.click()
                self.log_result("Saved structure")
            else:
                # Use accept as fallback
                self.structure_editor.accept()
                self.log_result("Accepted dialog (saved structure)")
        except Exception as e:
            self.log_result(f"Failed to save editor: {e}", True)
    
    def _close_editor(self):
        """Close the current structure editor"""
        try:
            if not self.structure_editor:
                return
                
            self.structure_editor.close()
            self.structure_editor = None
            self.log_result("Closed structure editor")
        except Exception as e:
            self.log_result(f"Failed to close editor: {e}", True)
    
    def _close_editor_with_success(self):
        """Close the editor and signal success"""
        self._close_editor()
        self.signals.test_completed.emit(True, "Completed successfully")
    
    def _close_all_dialogs_with_success(self):
        """Close all open dialogs and signal success"""
        # Find all top-level dialogs
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget != self:
                widget.close()
        
        self.signals.test_completed.emit(True, "Completed successfully")
    
    def _preview_saved_structure(self, structure_name):
        """Preview a saved structure"""
        try:
            # Get the structure
            structure = self.template_manager.get_structure(structure_name)
            if not structure:
                self.log_result(f"Failed to load structure '{structure_name}'", True)
                return
                
            # Show preview
            preview_structure(self, structure)
            self.log_result(f"Showing preview for '{structure_name}'")
        except Exception as e:
            self.log_result(f"Failed to preview structure: {e}", True)
    
    def closeEvent(self, event):
        """Clean up when the dialog is closed"""
        # Close any open editors
        if self.structure_editor:
            self.structure_editor.close()
            self.structure_editor = None
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp dir: {e}")
        
        super().closeEvent(event)

def run_tests():
    """Run the test suite"""
    app = QApplication.instance() or QApplication(sys.argv)
    tester = StructureEditorTester()
    tester.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_tests() 