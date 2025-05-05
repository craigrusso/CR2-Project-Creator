#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for structure editor UI functionality.
Tests context menu, folder icons, and inline text editing.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

# Create application instance first
app = QApplication(sys.argv)

# Import structure editor after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestDialog(QDialog):
    """Dialog to run structure editor tests"""
    
    def __init__(self):
        super(TestDialog, self).__init__()
        self.setWindowTitle("Structure Editor Test")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Add instructions
        instructions = QLabel(
            "Testing Structure Editor UI Features:\n"
            "1. Test folder creation and icons\n"
            "2. Test inline text editing\n"
            "3. Test right-click context menu\n"
            "4. Test 'Use Project Name' feature"
        )
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Add button to launch structure editor
        launch_btn = QPushButton("Launch Structure Editor")
        launch_btn.clicked.connect(self.launch_editor)
        layout.addWidget(launch_btn)
        
        # Add results label
        self.results_label = QLabel("Results will appear here")
        self.results_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.results_label)
    
    def launch_editor(self):
        """Launch the structure editor for testing"""
        try:
            # Create structure editor with test project name
            editor = EnhancedStructureEditor(
                structure_name="Test_Project",
                is_new=True
            )
            
            # Show the editor as a dialog
            result = editor.exec_()
            
            if result == QDialog.Accepted:
                # If editor was accepted, show success
                self.results_label.setText("Editor accepted (Save clicked)")
                self.results_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                # If editor was cancelled, show cancelled
                self.results_label.setText("Editor cancelled (Cancel clicked)")
                self.results_label.setStyleSheet("color: red;")
        except Exception as e:
            # If error occurred, show error
            import traceback
            traceback.print_exc()
            self.results_label.setText(f"Error: {str(e)}")
            self.results_label.setStyleSheet("color: red; font-weight: bold;")

if __name__ == "__main__":
    try:
        # Create and show test dialog
        dialog = TestDialog()
        dialog.show()
        
        # Run application
        sys.exit(app.exec_())
    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 