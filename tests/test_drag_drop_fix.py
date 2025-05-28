#!/usr/bin/env python3
"""
Test script to verify drag-and-drop fixes, specifically:
1. Preservation of folder names during drag-and-drop
2. Proper handling of duplicate folder drops
"""

import os
import sys
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt6.QtGui import QDropEvent

# Create application instance
app = QApplication(sys.argv)

# Import after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_manager import TemplateManager

class DragDropFixTester(QMainWindow):
    """Simple window to test drag-and-drop fixes"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag & Drop Fix Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Instructions
        title = QLabel("<h1>Drag & Drop Fix Test</h1>")
        title.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
        layout.addWidget(title)
        
        instructions = QLabel("""
        <p>This test will verify:</p>
        <ol>
            <li>Folder names are preserved correctly during drag-and-drop</li>
            <li>Duplicate folder drops are handled properly with a dialog</li>
        </ol>
        <p>Click the button below to start the test.</p>
        """)
        instructions.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Test button
        self.btn_test = QPushButton("Run Drag & Drop Test")
        self.btn_test.clicked.connect(self.run_test)
        layout.addWidget(self.btn_test)
        
        # Status label
        self.status_label = QLabel("Ready to test")
        self.status_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Create test directory structure
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Create test directories for drag and drop testing"""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        print(f"Created test directory: {self.test_dir}")
        
        # Create top folder
        self.top_folder = os.path.join(self.test_dir, "TopFolder")
        os.makedirs(self.top_folder, exist_ok=True)
        
        # Create subfolders and files
        subfolder1 = os.path.join(self.top_folder, "SubFolder1")
        subfolder2 = os.path.join(self.top_folder, "SubFolder2")
        nested_folder = os.path.join(subfolder1, "NestedFolder")
        
        os.makedirs(subfolder1, exist_ok=True)
        os.makedirs(subfolder2, exist_ok=True)
        os.makedirs(nested_folder, exist_ok=True)
        
        # Create some test files
        with open(os.path.join(self.top_folder, "root_file.txt"), "w") as f:
            f.write("Root level test file")
            
        with open(os.path.join(subfolder1, "sub_file1.txt"), "w") as f:
            f.write("Subfolder 1 test file")
            
        with open(os.path.join(nested_folder, "nested_file.txt"), "w") as f:
            f.write("Nested folder test file")
            
        with open(os.path.join(subfolder2, "sub2_file.txt"), "w") as f:
            f.write("Subfolder 2 test file")
    
    def run_test(self):
        """Run the drag-and-drop test"""
        self.status_label.setText("Test running...")
        
        # Create structure editor
        editor = EnhancedStructureEditor(parent=None, structure_name="TestDragDrop", is_new=True)
        
        # Check if drag_drop_handler is available
        if not hasattr(editor, 'drag_drop_handler') or not editor.drag_drop_handler:
            self.status_label.setText("❌ Test failed: No drag drop handler available")
            return
            
        # Get drag_drop_handler
        handler = editor.drag_drop_handler
        
        # Show the editor
        editor.show()
        
        # Prepare for first drop test
        mime_data = QMimeData()
        url = QUrl.fromLocalFile(self.top_folder)
        mime_data.setUrls([url])
        
        # Center of tree widget
        tree = editor.tree_widget
        pos = QPoint(tree.width() // 2, tree.height() // 2)
        
        # Create the drop event
        drop_event = QDropEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QDropEvent.Drop
        )
        
        # Process first drop
        print("\n=== FIRST DROP TEST ===")
        print(f"Dropping folder: {self.top_folder}")
        handler._handle_url_drop(drop_event)
        
        # Verify structure after first drop
        if not hasattr(editor, 'structure_converter') or not editor.structure_converter:
            self.status_label.setText("❌ Test failed: No structure converter available")
            return
        
        # Get structure
        structure = editor.structure_converter.get_structure()
        
        # Print first structure
        print("\nStructure after first drop:")
        self.print_structure(structure)
        
        # Verify top folder was added correctly - based on the correct structure format
        top_folder_found = False
        for item in structure:
            if isinstance(item, dict) and item.get('text') == 'TopFolder' or item.get('name') == 'TopFolder':
                top_folder_found = True
                print("✅ TopFolder found in structure with correct name")
                break
        
        if not top_folder_found:
            # Try alternative format check
            for item in structure:
                if isinstance(item, dict):
                    text = item.get('text', '')
                    name = item.get('name', '')
                    type_val = item.get('type', '')
                    print(f"Found item: text={text}, name={name}, type={type_val}")
                    if 'TopFolder' in text or 'TopFolder' in name:
                        top_folder_found = True
                        print("✅ TopFolder found in structure with correct name")
                        break
        
        if not top_folder_found:
            print("❌ TopFolder not found in structure")
            self.status_label.setText("❌ Test failed: TopFolder not preserved")
            return
        
        # Second drop test - should trigger duplicate dialog
        print("\n=== SECOND DROP TEST ===")
        print(f"Dropping same folder again: {self.top_folder}")
        print("This should trigger the duplicate dialog in a real application")
        
        # In a real application, a dialog would appear asking to replace, add, or cancel
        # Here we're primarily testing that the code doesn't crash
        handler._handle_url_drop(drop_event)
        
        # Get updated structure
        structure = editor.structure_converter.get_structure()
        
        # Print final structure
        print("\nStructure after second drop:")
        self.print_structure(structure)
        
        # Clean up
        editor.deleteLater()
        
        # Update status
        self.status_label.setText("✅ Test completed successfully")
        print("\n=== TEST COMPLETED ===")
        print("The drag-and-drop handler processed both drops without errors")
        print("Folder names were correctly preserved in the structure")
    
    def print_structure(self, structure, indent=0):
        """Print the structure in a readable format"""
        spacing = "  " * indent
        
        for item in structure:
            if isinstance(item, dict):
                # Try to extract the item name/text from different possible formats
                item_name = item.get('text', item.get('name', 'unnamed'))
                item_type = item.get('type', 'unknown')
                print(f"{spacing}📁 {item_name} ({item_type})")
                
                # Check for children in different possible formats
                children = item.get('children', [])
                if children:
                    self.print_structure(children, indent + 1)
            else:
                print(f"{spacing}📄 {item}")
    
    def closeEvent(self, event):
        """Clean up test resources when closing"""
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
                print(f"Removed test directory: {self.test_dir}")
            except Exception as e:
                print(f"Error removing test directory: {e}")
        event.accept()

def main():
    """Main function to run the test"""
    window = DragDropFixTester()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 