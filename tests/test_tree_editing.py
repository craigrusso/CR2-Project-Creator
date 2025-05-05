#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, 
                             QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel, QStyle)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QIcon

# Import styling and color scheme
from app.ui.tree_styling import apply_tree_styling
from app.ui.color_scheme_pyqt import APP_COLORS, BUTTON_STYLE


class TreeEditingTestWindow(QMainWindow):
    """Test window for tree widget styling and editing"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Editing Test")
        self.resize(600, 500)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        header_label = QLabel("Tree Editing Test - Verify Icons and Editing")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(header_label)
        
        # Create description
        description = QLabel(
            "This test verifies:\n"
            "1. Folder icons are visible\n"
            "2. Branch indicators (twirl arrows) work\n"
            "3. Inline editing works correctly\n\n"
            "Instructions:\n"
            "- Double-click on an item to edit it\n"
            "- Press Enter to confirm the edit\n"
            "- Press Escape to cancel the edit"
        )
        description.setStyleSheet(f"background-color: {APP_COLORS['card_bg']}; padding: 10px; border-radius: 5px; color: {APP_COLORS['text']};")
        main_layout.addWidget(description)
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Item Name"])
        
        # Configure tree for optimal visibility
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        
        # CRITICAL: These settings ensure branch indicators are visible
        self.tree.setRootIsDecorated(True)
        self.tree.setItemsExpandable(True)
        
        # Increase indentation for better visibility of structure
        self.tree.setIndentation(25)
        self.tree.setIconSize(QSize(16, 16))
        self.tree.setEditTriggers(QTreeWidget.EditKeyPressed | QTreeWidget.DoubleClicked)
        
        # Add some test items
        self._populate_tree()
        
        # Add tree to layout
        main_layout.addWidget(self.tree)
        
        # Create button bar
        button_layout = QHBoxLayout()
        
        # Add folder button
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        button_layout.addWidget(add_folder_btn)
        
        # Add file button
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_file)
        button_layout.addWidget(add_file_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected)
        button_layout.addWidget(delete_btn)
        
        # Edit button
        edit_btn = QPushButton("Edit Selected")
        edit_btn.clicked.connect(self._edit_selected)
        button_layout.addWidget(edit_btn)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Set up editing signals to track edits
        self.tree.itemChanged.connect(self._on_item_changed)
    
    def _populate_tree(self):
        """Add sample items to the tree"""
        # Create root items
        project_root = QTreeWidgetItem(self.tree)
        project_root.setText(0, "Project Root")
        project_root.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        project_root.setFlags(project_root.flags() | Qt.ItemIsEditable)
        
        # Add some folders with nested structure
        folders = [
            "01_VIDEO_ASSETS",
            "02_AUDIO_ASSETS",
            "03_IMAGE_ASSETS",
            "04_PROJECT_FILES"
        ]
        
        folder_items = {}
        
        for folder_name in folders:
            folder_item = QTreeWidgetItem(project_root)
            folder_item.setText(0, folder_name)
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
            folder_items[folder_name] = folder_item
        
        # Add subfolders
        video_subfolders = ["01_RAW", "02_EDITED", "03_EXPORTED"]
        for subfolder in video_subfolders:
            subfolder_item = QTreeWidgetItem(folder_items["01_VIDEO_ASSETS"])
            subfolder_item.setText(0, subfolder)
            subfolder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            subfolder_item.setFlags(subfolder_item.flags() | Qt.ItemIsEditable)
        
        # Add some files to the folders
        files = {
            "01_VIDEO_ASSETS": ["clip001.mp4", "clip002.mp4"],
            "02_AUDIO_ASSETS": ["voice_over.wav", "background_music.mp3"],
            "03_IMAGE_ASSETS": ["logo.png", "background.jpg"],
            "04_PROJECT_FILES": ["main_project.prproj", "effects_project.aep"]
        }
        
        for folder_name, file_list in files.items():
            folder_item = folder_items[folder_name]
            for file_name in file_list:
                file_item = QTreeWidgetItem(folder_item)
                file_item.setText(0, file_name)
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
        
        # Expand root
        project_root.setExpanded(True)
        folder_items["01_VIDEO_ASSETS"].setExpanded(True)
    
    def _add_folder(self):
        """Add a new folder to the selected item"""
        # Get selected item or root
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.invisibleRootItem()
        
        # Create new folder
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, "New Folder")
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
        
        # Expand parent
        parent_item.setExpanded(True)
        
        # Select and edit the new item
        self.tree.setCurrentItem(folder_item)
        self.tree.editItem(folder_item, 0)
    
    def _add_file(self):
        """Add a new file to the selected item"""
        # Get selected item or root
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.invisibleRootItem()
        
        # Create new file
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, "new_file.txt")
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
        
        # Expand parent
        parent_item.setExpanded(True)
        
        # Select and edit the new item
        self.tree.setCurrentItem(file_item)
        self.tree.editItem(file_item, 0)
    
    def _delete_selected(self):
        """Delete the selected items"""
        selected_items = self.tree.selectedItems()
        
        for item in selected_items:
            parent = item.parent() or self.tree.invisibleRootItem()
            parent.removeChild(item)
    
    def _edit_selected(self):
        """Edit the selected item"""
        selected_items = self.tree.selectedItems()
        if selected_items:
            self.tree.editItem(selected_items[0], 0)
    
    def _on_item_changed(self, item, column):
        """Handle item change events"""
        print(f"Item edited: New text = '{item.text(column)}'")


if __name__ == "__main__":
    # Create application
    app = QApplication(sys.argv)
    
    # Set app stylesheet for a coherent look using app color scheme
    app.setStyleSheet(f"""
        QMainWindow {{
            background-color: {APP_COLORS['bg']};
            color: {APP_COLORS['text']};
        }}
        QLabel {{
            color: {APP_COLORS['text']};
        }}
        QTreeWidget {{
            background-color: {APP_COLORS['bg']};
            alternate-background-color: {APP_COLORS['card_bg']};
            color: {APP_COLORS['text']};
            border: 1px solid {APP_COLORS['border']};
        }}
        QTreeWidget::item {{
            border: none;
            border-bottom: 1px solid transparent;
            padding: 4px 2px;
            min-height: 24px;
        }}
        QTreeWidget::item:selected {{
            background-color: {APP_COLORS['highlight_bg']};
            color: {APP_COLORS['highlight_text']};
        }}
        QTreeWidget::item:hover:!selected {{
            background-color: {APP_COLORS['hover_bg']};
        }}
        /* Style branch when selected for consistent color */
        QTreeWidget::branch:selected {{
            background-color: {APP_COLORS['highlight_bg']};
        }}
        QPushButton {{
            background-color: {APP_COLORS['card_bg']};
            color: {APP_COLORS['text']};
            border: 1px solid {APP_COLORS['border']};
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {APP_COLORS['hover_bg']};
            border: 1px solid {APP_COLORS['accent']};
        }}
        QPushButton:pressed {{
            background-color: {APP_COLORS['accent']};
            color: {APP_COLORS['highlight_text']};
        }}
    """)
    
    # Create and show the window
    window = TreeEditingTestWindow()
    
    # Apply consistent tree styling to ensure branch indicators and consistent colors
    apply_tree_styling(window.tree)
    
    window.show()
    
    # Run application
    sys.exit(app.exec_()) 