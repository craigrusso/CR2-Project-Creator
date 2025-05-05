#!/usr/bin/env python3
# Test script to verify default structures format

import os
import sys
import json
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox
from PyQt5.QtCore import Qt

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app modules
from app.core.app_config import DEFAULT_STRUCTURES as APP_CONFIG_STRUCTURES
from app.constants import DEFAULT_STRUCTURES as CONSTANTS_STRUCTURES
from app.dialogs.dialog_windows_pyqt import preview_structure
from app.ui.color_scheme_pyqt import COMBOBOX_STYLE

class DefaultStructuresTestDialog(QDialog):
    """Dialog to test the updated default structures"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Default Structures Test")
        self.resize(800, 600)
        
        # UI setup
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Default Structures Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "This test verifies that the default structures have been properly updated with the new format.\n"
            "Select a structure from either source to preview it and check that empty folders use the new dictionary format."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Structure source selector
        source_layout = QVBoxLayout()
        source_label = QLabel("Structure Source:")
        source_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        source_layout.addWidget(source_label)
        
        self.source_combo = QComboBox()
        self.source_combo.addItem("app/core/app_config.py", "app_config")
        self.source_combo.addItem("app/constants.py", "constants")
        self.source_combo.currentIndexChanged.connect(self.update_structure_list)
        self.source_combo.setStyleSheet(COMBOBOX_STYLE)
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)
        
        # Structure selector
        structure_layout = QVBoxLayout()
        structure_label = QLabel("Select Structure:")
        structure_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        structure_layout.addWidget(structure_label)
        
        self.structure_combo = QComboBox()
        self.structure_combo.setMinimumWidth(300)
        self.structure_combo.currentIndexChanged.connect(self.show_structure_preview)
        self.structure_combo.setStyleSheet(COMBOBOX_STYLE)
        structure_layout.addWidget(self.structure_combo)
        layout.addLayout(structure_layout)
        
        # Structure preview
        preview_label = QLabel("Structure Format Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.format_preview = QTextEdit()
        self.format_preview.setReadOnly(True)
        self.format_preview.setMinimumHeight(200)
        self.format_preview.setStyleSheet("""
            background-color: #2A2A2A;
            color: #FFFFFF;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
        """)
        layout.addWidget(self.format_preview)
        
        # Buttons
        preview_btn = QPushButton("Show Tree Preview")
        preview_btn.clicked.connect(self.show_tree_preview)
        layout.addWidget(preview_btn)
        
        validate_btn = QPushButton("Validate All Structures")
        validate_btn.clicked.connect(self.validate_all_structures)
        layout.addWidget(validate_btn)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("margin-top: 10px; color: #666;")
        layout.addWidget(self.status_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        # Initialize with app_config structures
        self.update_structure_list()
    
    def update_structure_list(self):
        """Update the structure list based on selected source"""
        source = self.source_combo.currentData()
        self.structure_combo.clear()
        
        if source == "app_config":
            structures = APP_CONFIG_STRUCTURES
        else:
            structures = CONSTANTS_STRUCTURES
        
        for name in sorted(structures.keys()):
            self.structure_combo.addItem(name, name)
    
    def get_current_structure(self):
        """Get the currently selected structure"""
        source = self.source_combo.currentData()
        structure_name = self.structure_combo.currentData()
        
        if source == "app_config":
            return APP_CONFIG_STRUCTURES.get(structure_name, [])
        else:
            return CONSTANTS_STRUCTURES.get(structure_name, [])
    
    def show_structure_preview(self):
        """Show a preview of the selected structure format"""
        structure = self.get_current_structure()
        
        # Format the structure as JSON for display
        json_str = json.dumps(structure, indent=2)
        self.format_preview.setText(json_str)
        
        # Update status
        self.status_label.setText(f"Showing format preview of {self.structure_combo.currentText()}")
    
    def show_tree_preview(self):
        """Show the tree visualization of the structure"""
        structure = self.get_current_structure()
        structure_name = self.structure_combo.currentText()
        
        # Show the preview dialog
        self.status_label.setText(f"Showing tree preview of {structure_name}...")
        preview_structure(self, structure)
        self.status_label.setText(f"Tree preview of {structure_name} displayed")
    
    def validate_all_structures(self):
        """Validate that all structures use the new format for empty folders"""
        self.status_label.setText("Validating all structures...")
        
        # Check both sets of structures
        all_valid = True
        issues = []
        
        # Check app_config structures
        for name, structure in APP_CONFIG_STRUCTURES.items():
            valid, issue = self._validate_structure(structure, f"app_config.{name}")
            if not valid:
                all_valid = False
                issues.extend(issue)
        
        # Check constants structures
        for name, structure in CONSTANTS_STRUCTURES.items():
            valid, issue = self._validate_structure(structure, f"constants.{name}")
            if not valid:
                all_valid = False
                issues.extend(issue)
        
        # Display results
        if all_valid:
            self.status_label.setText("All structures are valid! Empty folders use the new dictionary format.")
            self.format_preview.setText("✅ All structures passed validation.\n\nEmpty folders are properly represented as dictionaries with empty lists.")
        else:
            self.status_label.setText("Some structures have issues with folder representation.")
            self.format_preview.setText("❌ Some structures have issues:\n\n" + "\n".join(issues))
    
    def _validate_structure(self, structure, path=""):
        """Recursively validate a structure, ensuring empty folders use new format"""
        valid = True
        issues = []
        
        if not isinstance(structure, list):
            return False, [f"{path}: Root structure should be a list"]
        
        for i, item in enumerate(structure):
            item_path = f"{path}[{i}]"
            
            if isinstance(item, str):
                # Check if it's an empty folder in old format (with trailing slash)
                if item.endswith('/'):
                    valid = False
                    issues.append(f"{item_path}: '{item}' uses old format with trailing slash. Should be {{'{item[:-1]}': []}}")
            elif isinstance(item, dict):
                # This is correct format, but check if any children use old format
                for folder_name, children in item.items():
                    if isinstance(children, list):
                        child_valid, child_issues = self._validate_structure(children, f"{item_path}.{folder_name}")
                        if not child_valid:
                            valid = False
                            issues.extend(child_issues)
                    else:
                        valid = False
                        issues.append(f"{item_path}.{folder_name}: Value should be a list, not {type(children)}")
            else:
                valid = False
                issues.append(f"{item_path}: Item should be a string or dict, not {type(item)}")
        
        return valid, issues

def run_test():
    """Run the default structures test"""
    app = QApplication(sys.argv)
    dialog = DefaultStructuresTestDialog()
    dialog.show()
    app.exec_()

if __name__ == "__main__":
    run_test() 