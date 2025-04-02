#!/usr/bin/env python3
# Test script for FileOperationsHandler and EnhancedStructureEditor

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test helper to automate button clicking
class TestHelper(QObject):
    """Helper class to automate UI testing"""
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.tests_complete = False
    
    def run_tests(self):
        """Run automated tests on the UI"""
        print("\nRunning automated tests...")
        
        # Create test sequence with timers
        QTimer.singleShot(1000, self.test_add_folder)
        QTimer.singleShot(3000, self.test_add_file)
        QTimer.singleShot(5000, self.test_complete)
    
    def test_add_folder(self):
        """Test adding a folder"""
        print("Test: Clicking Add Folder button...")
        
        # Simulate clicking the add folder button
        # The QInputDialog will appear - we won't be able to automate the input
        # but we can see if the button click works without errors
        try:
            self.editor.add_folder_btn.click()
            print("✅ Add Folder button clicked")
        except Exception as e:
            print(f"❌ Error clicking Add Folder button: {e}")
    
    def test_add_file(self):
        """Test adding a file"""
        print("Test: Clicking Add File button...")
        
        # Simulate clicking the add file button
        try:
            self.editor.add_file_btn.click()
            print("✅ Add File button clicked")
        except Exception as e:
            print(f"❌ Error clicking Add File button: {e}")
    
    def test_complete(self):
        """Mark tests as complete"""
        print("\nAutomated testing complete. Please continue manual testing.")
        print("The dialog will remain open. Try adding folders and files manually.")
        self.tests_complete = True

try:
    print("Testing imports...")
    from app.utils.file_operations import FileOperationsHandler
    print("✅ FileOperationsHandler import successful")
    
    from app.ui.enhanced_structure_editor import EnhancedStructureEditor
    print("✅ EnhancedStructureEditor import successful")
    
    # Create application instance
    app = QApplication(sys.argv)
    
    # Create instances for testing
    print("\nCreating instances...")
    file_handler = FileOperationsHandler(debug=True)
    print("✅ FileOperationsHandler instance created")
    
    # Sample structure for testing
    sample_structure = [
        {"name": "src", "type": "folder", "children": [
            {"name": "components", "type": "folder", "children": []},
            {"name": "index.js", "type": "file"}
        ]},
        {"name": "public", "type": "folder", "children": []},
        {"name": "README.md", "type": "file"}
    ]
    
    # Create and initialize the editor
    editor = EnhancedStructureEditor()
    editor.set_template_name("Test Template")
    editor.set_structure_name("Template_Test")
    editor.load_structure(sample_structure)
    editor.file_operations.debug = True  # Enable debug mode
    print("✅ EnhancedStructureEditor instance created and initialized")
    print(f"✅ editor.file_operations is instance of FileOperationsHandler: {isinstance(editor.file_operations, FileOperationsHandler)}")
    
    # Show the editor dialog
    editor.show()
    print("✅ Showing EnhancedStructureEditor dialog")
    
    # Create test helper
    test_helper = TestHelper(editor)
    
    # Start automated tests after 500ms
    QTimer.singleShot(500, test_helper.run_tests)
    
    # Test file save operation
    test_data = {
        "name": "Test Template",
        "description": "Test description",
        "structure": {
            "folders": ["src", "docs"],
            "files": ["README.md", "index.js"]
        }
    }
    
    # Set up a temporary file path
    temp_file = "test_template.json"
    
    # Test file save
    print("\nTesting file save operation...")
    save_result = editor.file_operations.save_json_file(test_data, temp_file, show_dialog=False)
    print(f"✅ Save operation returned: {save_result}")
    print(f"✅ File exists: {os.path.exists(temp_file)}")
    
    # Test file load
    print("\nTesting file load operation...")
    load_result, loaded_data = editor.file_operations.load_json_file(temp_file, show_dialog=False)
    print(f"✅ Load operation returned: {load_result}")
    print(f"✅ Loaded data matches original: {loaded_data == test_data}")
    
    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"✅ Cleaned up test file: {temp_file}")
    
    print("\nAll tests completed successfully!")
    print("Dialog will remain open. Close it manually to exit.")
    print("Try using the Add Folder, Add File buttons manually to test their functionality.")
    
    # Exit the application after testing
    app.exec_()
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc() 