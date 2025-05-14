#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to force icon refresh for all tree widgets
Run this script after updating the icon_utilities.py module
"""

import sys
import os
import time

# Add the parent directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTreeWidget
from PyQt5.QtCore import Qt

# Import tree styling and icon utilities
from app.ui.tree_styling import apply_styling_to_all_tree_widgets
from app.ui.icon_utilities import clear_icon_cache
from app.ui.color_scheme_pyqt import APP_COLORS

class IconRefreshTestWindow(QMainWindow):
    """Test window for manual icon refresh"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Icon Refresh Test")
        self.resize(400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        header = QLabel("Icon Refresh Utility")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        description = QLabel(
            "This utility forces a refresh of all icons in the application. "
            "Use this if file icons are not displaying correctly."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create refresh button
        self.refresh_button = QPushButton("Refresh All Icons")
        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {APP_COLORS['accent']};
                color: {APP_COLORS['highlight_text']};
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {APP_COLORS['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {APP_COLORS['accent_pressed']};
            }}
        """)
        self.refresh_button.clicked.connect(self.refresh_icons)
        layout.addWidget(self.refresh_button)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Add a sample tree for testing
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File Path"])
        layout.addWidget(self.tree)
        
        # Apply initial styling
        apply_styling_to_all_tree_widgets(self)
        
        # Populate with sample items
        self._populate_sample_tree()
    
    def _populate_sample_tree(self):
        """Add sample items to test the icon display"""
        from PyQt5.QtWidgets import QTreeWidgetItem
        
        # Adobe files
        adobe_folder = QTreeWidgetItem(self.tree)
        adobe_folder.setText(0, "Adobe Files")
        adobe_folder.setData(0, Qt.UserRole, "folder")
        
        # Premiere Pro project
        prproj_item = QTreeWidgetItem(adobe_folder)
        prproj_item.setText(0, "MyProject.prproj")
        prproj_item.setData(0, Qt.UserRole, "file")
        
        # After Effects project
        aep_item = QTreeWidgetItem(adobe_folder)
        aep_item.setText(0, "Animation.aep")
        aep_item.setData(0, Qt.UserRole, "file")
        
        # Photoshop file
        psd_item = QTreeWidgetItem(adobe_folder)
        psd_item.setText(0, "Graphic.psd")
        psd_item.setData(0, Qt.UserRole, "file")
        
        # Media files folder
        media_folder = QTreeWidgetItem(self.tree)
        media_folder.setText(0, "Media Files")
        media_folder.setData(0, Qt.UserRole, "folder")
        
        # Video files
        mp4_item = QTreeWidgetItem(media_folder)
        mp4_item.setText(0, "Interview.mp4")
        mp4_item.setData(0, Qt.UserRole, "file")
        
        mov_item = QTreeWidgetItem(media_folder)
        mov_item.setText(0, "Footage.mov")
        mov_item.setData(0, Qt.UserRole, "file")
        
        # Expand all items
        self.tree.expandAll()
    
    def refresh_icons(self):
        """Clear icon cache and reapply styling to all trees"""
        self.status_label.setText("Refreshing icons...")
        QApplication.processEvents()  # Force UI update
        
        # Clear the icon cache
        clear_icon_cache()
        
        # Reapply styling to all tree widgets in the application
        styled_count = apply_styling_to_all_tree_widgets(QApplication.topLevelWidgets()[0])
        
        self.status_label.setText(f"Refreshed icons for {styled_count} tree widgets")
        
        # Force redraw of visible trees
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                widget.repaint()

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
    
    window = IconRefreshTestWindow()
    window.show()
    
    sys.exit(app.exec_()) 