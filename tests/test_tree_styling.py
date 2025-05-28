#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify tree styling with branch indicators and consistent selection colors
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

# Import tree styling and color scheme
from app.ui.tree_styling import apply_tree_styling
from app.ui.color_scheme_pyqt import APP_COLORS

class TreeStylingTestWindow(QMainWindow):
    """Test window for tree widget styling verification"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Styling Test")
        self.resize(500, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        header = QLabel("Tree Styling Test")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        description = QLabel(
            "This test verifies:\n"
            "1. Branch indicators are visible\n"
            "2. Selection colors are consistent between items and branches\n"
            "3. The tree styling follows the app's color scheme"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create the tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tree Item"])
        layout.addWidget(self.tree)
        
        # Apply tree styling to ensure branch indicators are visible
        apply_tree_styling(self.tree)
        
        # Set a debugger label to show selection state
        self.debug_label = QLabel("Selection: None")
        layout.addWidget(self.debug_label)
        
        # Populate the tree with test items
        self._populate_tree()
        
        # Connect to selection changed signal
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _populate_tree(self):
        """Add test items to the tree"""
        # Create root items
        for i in range(3):
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, f"Root Item {i+1}")
            root_item.setFlags(root_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Add child items
            for j in range(3):
                child_item = QTreeWidgetItem(root_item)
                child_item.setText(0, f"Child {i+1}.{j+1}")
                child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Add grandchildren
                for k in range(2):
                    grandchild = QTreeWidgetItem(child_item)
                    grandchild.setText(0, f"Item {i+1}.{j+1}.{k+1}")
                    grandchild.setFlags(grandchild.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Expand all items
        self.tree.expandAll()
    
    def _on_selection_changed(self):
        """Handle selection changes"""
        selected = self.tree.selectedItems()
        if selected:
            names = [item.text(0) for item in selected]
            self.debug_label.setText(f"Selection: {', '.join(names)}")
        else:
            self.debug_label.setText("Selection: None")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style sheet from color scheme
    app.setStyleSheet(f"""
        QMainWindow {{
            background-color: {APP_COLORS['bg']};
            color: {APP_COLORS['text']};
        }}
        
        QLabel {{
            color: {APP_COLORS['text']};
        }}
    """)
    
    window = TreeStylingTestWindow()
    window.show()
    
    sys.exit(app.exec()) 