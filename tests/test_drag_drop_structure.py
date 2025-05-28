#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for diagnosing drag and drop folder structure issues.
This script simulates drag and drop operations and verifies that the 
folder structure is correctly saved and loaded.
"""

import sys
import os
import json
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTreeWidget
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt6.QtGui import QDropEvent

# Create application instance before importing UI components
app = QApplication(sys.argv)

# Import structure editor after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.drag_drop import DragDropHandler
from app.templates.template_manager import TemplateManager

class DragDropTester(QMainWindow):
    """Test window for drag and drop operations"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag Drop Structure Test")
        self.setMinimumSize(800, 600)
        
        # Create test directory structure
        self.test_dir = tempfile.mkdtemp()
        print(f"Test directory: {self.test_dir}")
        self.setup_test_dirs()
        
        # Create template manager
        self.template_manager = TemplateManager()
        
        # Set up central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create editor
        self.editor = EnhancedStructureEditor(
            structure_name="DragDropTest",
            is_new=True
        )
        
        # Add the editor to the layout
        layout.addWidget(self.editor)
        
        # Add test buttons
        self.add_test_buttons(layout)
    
    def add_test_buttons(self, layout):
        """Add test control buttons"""
        test_button = QPushButton("Test Drag Drop")
        test_button.clicked.connect(self.test_drag_drop)
        layout.addWidget(test_button)
        
        save_button = QPushButton("Save Structure")
        save_button.clicked.connect(self.save_structure)
        layout.addWidget(save_button)
        
        load_button = QPushButton("Load Structure")
        load_button.clicked.connect(self.load_structure)
        layout.addWidget(load_button)
        
        print_button = QPushButton("Print Structure")
        print_button.clicked.connect(self.print_structure)
        layout.addWidget(print_button)
    
    def setup_test_dirs(self):
        """Set up test directories for drag and drop testing"""
        # Create a complex folder structure
        self.top_folder = os.path.join(self.test_dir, "TopFolder")
        os.makedirs(self.top_folder)
        
        # Create subfolders and files
        subfolder1 = os.path.join(self.top_folder, "SubFolder1")
        subfolder2 = os.path.join(self.top_folder, "SubFolder2")
        nested_folder = os.path.join(subfolder1, "NestedFolder")
        
        os.makedirs(subfolder1)
        os.makedirs(subfolder2)
        os.makedirs(nested_folder)
        
        # Create some test files
        with open(os.path.join(self.top_folder, "root_file.txt"), "w") as f:
            f.write("Root level file")
        
        with open(os.path.join(subfolder1, "sub_file1.txt"), "w") as f:
            f.write("Subfolder 1 file")
            
        with open(os.path.join(nested_folder, "nested_file.txt"), "w") as f:
            f.write("Nested folder file")
            
        with open(os.path.join(subfolder2, "sub2_file.txt"), "w") as f:
            f.write("Subfolder 2 file")
    
    def test_drag_drop(self):
        """Simulate drag and drop operation"""
        print("\n=== TESTING DRAG AND DROP ===")
        
        if not hasattr(self.editor, 'drag_drop_handler') or not self.editor.drag_drop_handler:
            print("ERROR: No drag drop handler available in the editor")
            return
            
        handler = self.editor.drag_drop_handler
        tree = self.editor.tree_widget
        
        # Create a drop event that simulates dragging a folder from the file system
        mime_data = QMimeData()
        url = QUrl.fromLocalFile(self.top_folder)
        mime_data.setUrls([url])
        
        # Center of tree widget
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
        
        # Process the drop event
        try:
            # Simulate the drop
            handler._handle_url_drop(drop_event)
            print("Drag and drop simulation completed successfully")
            
            # Print the resulting structure
            self.print_structure()
        except Exception as e:
            print(f"Error during drag and drop: {e}")
            import traceback
            traceback.print_exc()
    
    def save_structure(self):
        """Save the current structure"""
        print("\n=== SAVING STRUCTURE ===")
        
        if not hasattr(self.editor, 'structure_converter') or not self.editor.structure_converter:
            print("ERROR: No structure converter available in the editor")
            return
            
        # Get the structure from the tree
        structure = self.editor.structure_converter.create_structure_from_tree()
        
        # Print structure before saving
        print("Structure before saving:")
        self.print_structure_data(structure)
        
        # Save using template manager
        try:
            success = self.template_manager.save_custom_structure("DragDropTest", structure)
            if success:
                print("Structure saved successfully")
            else:
                print("Failed to save structure")
        except Exception as e:
            print(f"Error saving structure: {e}")
            import traceback
            traceback.print_exc()
    
    def load_structure(self):
        """Load the saved structure"""
        print("\n=== LOADING STRUCTURE ===")
        
        try:
            # Load the structure
            structure = self.template_manager.get_structure("DragDropTest")
            
            if structure:
                print("Structure loaded successfully")
                
                # Print the loaded structure
                print("Loaded structure:")
                self.print_structure_data(structure)
                
                # Load into the editor
                if hasattr(self.editor, 'structure_converter') and self.editor.structure_converter:
                    # Clear the tree first
                    self.editor.tree_widget.clear()
                    
                    # Load the structure
                    self.editor.structure_converter.load_structure(structure)
                    print("Structure loaded into editor")
                    
                    # Print the structure from the editor after loading
                    print("Structure from editor after loading:")
                    self.print_structure()
            else:
                print("Failed to load structure")
        except Exception as e:
            print(f"Error loading structure: {e}")
            import traceback
            traceback.print_exc()
    
    def print_structure(self):
        """Print the current structure from the editor"""
        if not hasattr(self.editor, 'structure_converter') or not self.editor.structure_converter:
            print("ERROR: No structure converter available in the editor")
            return
            
        # Get the structure from the tree
        structure = self.editor.structure_converter.create_structure_from_tree()
        
        # Print the structure
        self.print_structure_data(structure)
    
    def print_structure_data(self, structure, indent=0):
        """Print a structure data object in a readable format"""
        spacing = "  " * indent
        
        if not structure:
            print(f"{spacing}Empty structure")
            return
        
        if isinstance(structure, list):
            for item in structure:
                self.print_structure_data(item, indent)
        elif isinstance(structure, dict):
            for folder_name, children in structure.items():
                print(f"{spacing}📁 {folder_name}/")
                self.print_structure_data(children, indent + 1)
        else:
            print(f"{spacing}📄 {structure}")
    
    def closeEvent(self, event):
        """Clean up test resources when closing"""
        try:
            shutil.rmtree(self.test_dir)
            print(f"Removed test directory: {self.test_dir}")
        except Exception as e:
            print(f"Error removing test directory: {e}")
        event.accept()

if __name__ == "__main__":
    try:
        window = DragDropTester()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 