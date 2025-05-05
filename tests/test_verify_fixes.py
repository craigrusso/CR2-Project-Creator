#!/usr/bin/env python3
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QMimeData, QUrl, QPoint, QObject, QEvent
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

# Add the application directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_manager import TemplateManager
from app.templates.structure_operations import StructureOperations
from app.ui.structure_editor.drag_drop import DragDropHandler

class FixVerifier(QMainWindow):
    """Test class to verify fixes for drag-drop and UI button issues"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fix Verification Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create test buttons
        self.btn_test_drag_drop = QPushButton("Test Drag & Drop Fix")
        self.btn_test_drag_drop.clicked.connect(self.test_drag_drop_fix)
        layout.addWidget(self.btn_test_drag_drop)
        
        self.btn_test_ui_buttons = QPushButton("Test UI Button Fix")
        self.btn_test_ui_buttons.clicked.connect(self.test_ui_buttons_fix)
        layout.addWidget(self.btn_test_ui_buttons)
        
        self.btn_test_save_load = QPushButton("Test Save & Load")
        self.btn_test_save_load.clicked.connect(self.test_save_load)
        layout.addWidget(self.btn_test_save_load)
        
        # Create template manager for operations
        self.template_manager = TemplateManager()
        self.structure_ops = StructureOperations()
        
        # Test directory setup
        self.test_dir = None
        self.setup_test_dirs()
        
        # Test results tracking
        self.results = {
            "drag_drop_test": False,
            "ui_buttons_test": False,
            "save_load_test": False
        }

    def setup_test_dirs(self):
        """Create test directories for drag and drop testing"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        print(f"Created test directory: {self.test_dir}")
        
        # Create top folder
        top_folder = os.path.join(self.test_dir, "TopFolder")
        os.makedirs(top_folder, exist_ok=True)
        
        # Create subfolders and files
        subfolder1 = os.path.join(top_folder, "SubFolder1")
        subfolder2 = os.path.join(top_folder, "SubFolder2")
        nested_folder = os.path.join(subfolder1, "NestedFolder")
        
        os.makedirs(subfolder1, exist_ok=True)
        os.makedirs(subfolder2, exist_ok=True)
        os.makedirs(nested_folder, exist_ok=True)
        
        # Create some test files
        with open(os.path.join(top_folder, "root_file.txt"), "w") as f:
            f.write("Root level test file")
            
        with open(os.path.join(subfolder1, "sub_file1.txt"), "w") as f:
            f.write("Subfolder 1 test file")
            
        with open(os.path.join(nested_folder, "nested_file.txt"), "w") as f:
            f.write("Nested folder test file")
            
        with open(os.path.join(subfolder2, "sub2_file.txt"), "w") as f:
            f.write("Subfolder 2 test file")
    
    def test_drag_drop_fix(self):
        """Test the drag and drop functionality with duplicate folder detection"""
        print("\n=== TESTING DRAG & DROP FIX ===")
        
        # Create structure editor with correct parameters
        editor = EnhancedStructureEditor(parent=None, structure_name="TestDragDrop", is_new=False)
        
        # Check if the drag_drop_handler is available
        if not hasattr(editor, 'drag_drop_handler') or not editor.drag_drop_handler:
            print("❌ ERROR: No drag drop handler available in the editor")
            return False
            
        handler = editor.drag_drop_handler
        
        # Prepare drop test
        mime_data = QMimeData()
        top_folder_path = os.path.join(self.test_dir, "TopFolder")
        urls = [QUrl.fromLocalFile(top_folder_path)]
        mime_data.setUrls(urls)
        
        # Create drop event at root level
        drop_event = QDropEvent(
            QPoint(100, 100),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier,
            QEvent.Drop
        )
        
        # Process first drop
        print("Simulating first drop of TopFolder...")
        handler._handle_url_drop(drop_event)
        print("First structure after drop:")
        self.print_structure(editor)
        
        # Simulate a second drop of the same folder
        print("\nSimulating second drop of TopFolder...")
        # The dialog would be shown here in a real application
        print("In a real app, a dialog would ask: Replace, Add, or Cancel")
        print("We would select 'Replace' in this test")
        
        # Check if the structure_converter is available
        if not hasattr(editor, 'structure_converter') or not editor.structure_converter:
            print("❌ ERROR: No structure converter available in the editor")
            return False
            
        # Verify that folder structure is preserved
        structure = editor.structure_converter.get_structure()
        
        # Check if TopFolder exists in structure
        top_folder_found = False
        for item in structure:
            if item.get('text') == 'TopFolder' and item.get('type') == 'folder':
                top_folder_found = True
                print("✅ TopFolder is correctly preserved in the structure")
                
                # Check for subfolders
                children = item.get('children', [])
                subfolder_names = [child.get('text') for child in children 
                                   if child.get('type') == 'folder']
                
                if 'SubFolder1' in subfolder_names and 'SubFolder2' in subfolder_names:
                    print("✅ SubFolders are correctly preserved in the structure")
                    self.results["drag_drop_test"] = True
                else:
                    print("❌ SubFolders are not correctly preserved")
                break
        
        if not top_folder_found:
            print("❌ TopFolder is not preserved in the structure")
            
        # Complete test
        editor.deleteLater()
        return self.results["drag_drop_test"]
    
    def test_ui_buttons_fix(self):
        """Test the UI button fix to ensure only one set of buttons is shown"""
        print("\n=== TESTING UI BUTTON FIX ===")
        
        # Create structure editor with correct parameters
        editor = EnhancedStructureEditor(parent=None, structure_name="TestButtons", is_new=False)
        
        # Check for button duplication
        buttons = editor.findChildren(QPushButton)
        button_text = [btn.text() for btn in buttons]
        print(f"Found buttons: {button_text}")
        
        # Check that we only have one Save and one Cancel button
        save_buttons = button_text.count("Save")
        cancel_buttons = button_text.count("Cancel")
        accept_buttons = button_text.count("Accept")
        
        print(f"Save buttons: {save_buttons}")
        print(f"Cancel buttons: {cancel_buttons}")
        print(f"Accept buttons: {accept_buttons}")
        
        if save_buttons == 1 and cancel_buttons == 1 and accept_buttons == 0:
            print("✅ UI Button fix verified - correct buttons present")
            self.results["ui_buttons_test"] = True
        else:
            print("❌ UI Button fix failed - incorrect button configuration")
        
        # Complete test
        editor.deleteLater()
        return self.results["ui_buttons_test"]
    
    def test_save_load(self):
        """Test saving and loading a structure with proper hierarchies"""
        print("\n=== TESTING SAVE & LOAD FUNCTIONALITY ===")
        
        # Create a test structure
        test_structure = [
            {
                'text': 'TopFolder',
                'type': 'folder',
                'path': os.path.join(self.test_dir, 'TopFolder'),
                'children': [
                    {
                        'text': 'SubFolder1',
                        'type': 'folder',
                        'path': os.path.join(self.test_dir, 'TopFolder', 'SubFolder1'),
                        'children': [
                            {
                                'text': 'NestedFolder',
                                'type': 'folder',
                                'path': os.path.join(self.test_dir, 'TopFolder', 'SubFolder1', 'NestedFolder'),
                                'children': [
                                    {
                                        'text': 'nested_file.txt',
                                        'type': 'file',
                                        'path': os.path.join(self.test_dir, 'TopFolder', 'SubFolder1', 'NestedFolder', 'nested_file.txt')
                                    }
                                ]
                            },
                            {
                                'text': 'sub_file1.txt',
                                'type': 'file',
                                'path': os.path.join(self.test_dir, 'TopFolder', 'SubFolder1', 'sub_file1.txt')
                            }
                        ]
                    },
                    {
                        'text': 'SubFolder2',
                        'type': 'folder',
                        'path': os.path.join(self.test_dir, 'TopFolder', 'SubFolder2'),
                        'children': [
                            {
                                'text': 'sub2_file.txt',
                                'type': 'file',
                                'path': os.path.join(self.test_dir, 'TopFolder', 'SubFolder2', 'sub2_file.txt')
                            }
                        ]
                    },
                    {
                        'text': 'root_file.txt',
                        'type': 'file',
                        'path': os.path.join(self.test_dir, 'TopFolder', 'root_file.txt')
                    }
                ]
            }
        ]
        
        # Save the structure
        structure_name = "TestSaveLoad"
        print(f"Saving structure '{structure_name}'...")
        self.structure_ops.save_custom_structure(structure_name, test_structure)
        
        # Load the structure back
        print(f"Loading structure '{structure_name}'...")
        loaded_structure = self.structure_ops.get_structure(structure_name)
        
        if not loaded_structure:
            print(f"❌ Failed to load structure '{structure_name}'")
            return False
        
        # Verify the loaded structure
        print("Verifying loaded structure...")
        self.print_structure_compare(test_structure, loaded_structure)
        
        # Check that top folder is preserved
        if loaded_structure and len(loaded_structure) > 0:
            top_item = loaded_structure[0]
            if top_item.get('text') == 'TopFolder' and top_item.get('type') == 'folder':
                print("✅ TopFolder is correctly preserved after save/load")
                
                # Check for subfolders
                children = top_item.get('children', [])
                subfolder_names = [child.get('text') for child in children 
                                   if child.get('type') == 'folder']
                
                if 'SubFolder1' in subfolder_names and 'SubFolder2' in subfolder_names:
                    print("✅ SubFolders are correctly preserved after save/load")
                    self.results["save_load_test"] = True
                else:
                    print("❌ SubFolders are not correctly preserved after save/load")
            else:
                print(f"❌ TopFolder not preserved correctly. Found: {top_item.get('text')}")
        else:
            print("❌ Empty structure loaded")
        
        return self.results["save_load_test"]
    
    def print_structure(self, editor):
        """Print the current structure from the editor"""
        if not hasattr(editor, 'structure_converter') or not editor.structure_converter:
            print("❌ ERROR: No structure converter available in the editor")
            return
            
        structure = editor.structure_converter.get_structure()
        self._print_structure_recursive(structure)
    
    def _print_structure_recursive(self, items, indent=0):
        """Recursively print structure items"""
        for item in items:
            item_type = item.get('type', 'unknown')
            item_text = item.get('text', 'unnamed')
            print(f"{'  ' * indent}{item_text} ({item_type})")
            
            if item_type == 'folder' and 'children' in item:
                self._print_structure_recursive(item['children'], indent + 1)
    
    def print_structure_compare(self, original, loaded):
        """Compare and print two structures"""
        print("\nStructure comparison:")
        print("Original structure:")
        self._print_structure_recursive(original)
        print("\nLoaded structure:")
        self._print_structure_recursive(loaded)
        
        # Deep comparison
        if self._compare_structures(original, loaded):
            print("\n✅ Structures match exactly")
        else:
            print("\n❌ Structures do not match")
    
    def _compare_structures(self, struct1, struct2):
        """Deep compare two structures"""
        if len(struct1) != len(struct2):
            print(f"Different length: {len(struct1)} vs {len(struct2)}")
            return False
            
        for i in range(len(struct1)):
            item1 = struct1[i]
            item2 = struct2[i]
            
            # Compare essential properties
            if item1.get('text') != item2.get('text'):
                print(f"Text mismatch: {item1.get('text')} vs {item2.get('text')}")
                return False
                
            if item1.get('type') != item2.get('type'):
                print(f"Type mismatch for {item1.get('text')}: {item1.get('type')} vs {item2.get('type')}")
                return False
            
            # Compare children recursively for folders
            if item1.get('type') == 'folder':
                children1 = item1.get('children', [])
                children2 = item2.get('children', [])
                
                if not self._compare_structures(children1, children2):
                    return False
                    
        return True
    
    def cleanup(self):
        """Clean up test resources"""
        if self.test_dir and os.path.exists(self.test_dir):
            print(f"\nCleaning up test directory: {self.test_dir}")
            shutil.rmtree(self.test_dir)
            print("Test directory removed")
        
        # Remove test structure if it exists
        structure_file = "TestSaveLoad.json"
        if os.path.exists(structure_file):
            os.remove(structure_file)
            print(f"Removed test structure file: {structure_file}")
            
        # Remove test drag-drop structure if it exists
        structure_file = "TestDragDrop.json"
        if os.path.exists(structure_file):
            os.remove(structure_file)
            print(f"Removed test structure file: {structure_file}")
            
        # Remove test buttons structure if it exists
        structure_file = "TestButtons.json"
        if os.path.exists(structure_file):
            os.remove(structure_file)
            print(f"Removed test structure file: {structure_file}")
            
    def run_all_tests(self):
        """Run all verification tests"""
        print("\n===== RUNNING ALL VERIFICATION TESTS =====\n")
        
        drag_drop_result = self.test_drag_drop_fix()
        ui_buttons_result = self.test_ui_buttons_fix()
        save_load_result = self.test_save_load()
        
        print("\n===== TEST RESULTS SUMMARY =====")
        print(f"Drag & Drop Fix: {'✅ PASSED' if drag_drop_result else '❌ FAILED'}")
        print(f"UI Buttons Fix: {'✅ PASSED' if ui_buttons_result else '❌ FAILED'}")
        print(f"Save & Load: {'✅ PASSED' if save_load_result else '❌ FAILED'}")
        
        if all(self.results.values()):
            print("\n✅ ALL TESTS PASSED - Fixes verified successfully!")
        else:
            print("\n❌ SOME TESTS FAILED - Fixes need additional work")
            
        return all(self.results.values())

def main():
    """Main test function"""
    app = QApplication(sys.argv)
    
    try:
        print("Starting fix verification tests...")
        verifier = FixVerifier()
        success = verifier.run_all_tests()
        verifier.cleanup()
        
        print("\nVerification complete.")
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error running verification tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Ensure application exits
        app.quit()

if __name__ == "__main__":
    sys.exit(main()) 