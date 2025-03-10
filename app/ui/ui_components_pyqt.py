#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import json
import shutil
import datetime
import subprocess
import re
import platform
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLineEdit, QFrame, QScrollArea,
                            QToolTip, QSizePolicy, QFileDialog, QDialog,
                            QCheckBox, QListWidget, QListWidgetItem,
                            QTextEdit, QTreeWidget, QTreeWidgetItem,
                            QMessageBox, QInputDialog, QGridLayout, QTabWidget,
                            QApplication, QStyle)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QCursor, QIcon, QColor, QPalette

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, LINEEDIT_STYLE, LABEL_STYLE

# Get suitable system font for different platforms
def get_system_font():
    """Return an appropriate system font based on platform"""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI"
    elif system == "Darwin":  # macOS
        return "Helvetica Neue"  # Just use Helvetica which is guaranteed to exist
    else:  # Linux and others
        return "Ubuntu,DejaVu Sans,Liberation Sans,Arial"

# System font to use throughout the app
SYSTEM_FONT = get_system_font()

class ToolTip:
    """
    Creates a tooltip for a given widget when the mouse hovers over it.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        
        # Connect hover events to show tooltip
        widget.setToolTip(text)

class ScrollableFrame(QScrollArea):
    """
    A scrollable frame that automatically adjusts its content.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create content widget
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)
        self.setWidgetResizable(True)
        
        # Set up layout for content
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_widget.setLayout(self.content_layout)
        
        # Styling
        self.setFrameShape(QFrame.NoFrame)
        self.content_widget.setStyleSheet(f"background-color: {colors['bg']}; color: {colors['text']};")
        self.setStyleSheet(f"background-color: {colors['bg']}; border: none;")
    
    def addWidget(self, widget):
        """Add a widget to the scrollable content"""
        self.content_layout.addWidget(widget)
    
    def setSpacing(self, spacing):
        """Set spacing between widgets"""
        self.content_layout.setSpacing(spacing)
    
    def setContentsMargins(self, left, top, right, bottom):
        """Set margins of the content area"""
        self.content_layout.setContentsMargins(left, top, right, bottom)

class CardFrame(QFrame):
    """
    A card-like frame with title and content area.
    """
    def __init__(self, parent=None, title=None):
        super().__init__(parent)
        
        # Clear out any existing layouts to avoid "QLayout: Attempting to add QLayout" error
        if self.layout() is not None:
            # Save the old layout so we can remove it properly
            old_layout = self.layout()
            # Remove all items from the old layout
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
            # Delete the old layout
            old_layout.setParent(None)
            # Give the old layout to a temporary widget to handle destruction
            temp = QWidget()
            temp.setLayout(old_layout)
            temp.deleteLater()
        
        # Set up layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        # Add title if provided
        if title:
            title_label = QLabel(title)
            title_label.setFont(QFont(SYSTEM_FONT, 12, QFont.Bold))
            title_label.setStyleSheet(f"color: {colors['text']};")
            self.main_layout.addWidget(title_label)
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border-radius: 5px;
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
        """)

class SearchBox(QWidget):
    """
    A search box with label and search input.
    """
    def __init__(self, parent=None, label_text="Search:", callback=None):
        super().__init__(parent)
        
        # Setup layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # Label
        if label_text:
            self.label = QLabel(label_text)
            self.label.setFont(QFont(SYSTEM_FONT, 10))
            self.label.setStyleSheet(LABEL_STYLE)
            self.layout.addWidget(self.label)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search terms...")
        self.search_input.setStyleSheet(LINEEDIT_STYLE)
        self.layout.addWidget(self.search_input)
        
        # Connect callback
        if callback:
            self.search_input.textChanged.connect(callback)
    
    def get(self):
        """Get the current search text"""
        return self.search_input.text()
    
    def set(self, value):
        """Set the search text"""
        self.search_input.setText(value)

class TemplateFileCard(QFrame):
    """
    Card to display a template file with selection capability.
    """
    def __init__(self, parent, template_path, select_callback=None, remove_callback=None):
        super().__init__(parent)
        
        self.template_path = template_path
        self.select_callback = select_callback
        self.remove_callback = remove_callback
        self.selected = False
        
        # Setup styling
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)
        
        # Use a fixed grid layout with fixed row heights
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setSpacing(2)
        self.grid.setRowStretch(0, 3)  # Icon gets most space
        self.grid.setRowStretch(1, 0)  # Title gets minimum space needed
        self.grid.setRowStretch(2, 0)  # Template label gets minimum space
        self.grid.setRowStretch(3, 0)  # Path gets minimum space
        self.grid.setRowStretch(4, 2)  # Bottom empty space
        
        # Card content
        try:
            # Extract template name from path
            self.template_name = os.path.basename(template_path)
            self.template_name = os.path.splitext(self.template_name)[0]
            
            # Create template icon and title
            self.icon_label = QLabel("📄") # Document icon
            self.icon_label.setFont(QFont(SYSTEM_FONT, 24))
            self.icon_label.setAlignment(Qt.AlignCenter)
            
            self.title_label = QLabel(self.template_name)
            self.title_label.setFont(QFont(SYSTEM_FONT, 10, QFont.Bold))
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setWordWrap(True)
            
            # Simple template label 
            self.template_label = QLabel("Template")
            self.template_label.setFont(QFont(SYSTEM_FONT, 9))
            self.template_label.setAlignment(Qt.AlignCenter)
            self.template_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            
            # Path label (truncated if too long)
            display_path = template_path
            if len(display_path) > 40:
                display_path = "..." + display_path[-40:]
            
            self.path_label = QLabel(display_path)
            self.path_label.setFont(QFont(SYSTEM_FONT, 8))
            self.path_label.setAlignment(Qt.AlignCenter)
            self.path_label.setWordWrap(True)
            
            # Empty widget for bottom space
            empty = QWidget()
            empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Add widgets to grid
            self.grid.addWidget(self.icon_label, 0, 0)
            self.grid.addWidget(self.title_label, 1, 0)
            self.grid.addWidget(self.template_label, 2, 0)
            self.grid.addWidget(self.path_label, 3, 0)
            self.grid.addWidget(empty, 4, 0)
            
            # Add remove button if callback provided
            if remove_callback:
                self.remove_btn = QPushButton("×")
                self.remove_btn.setFixedSize(20, 20)
                self.remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border-radius: 10px;
                        border: none;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                    }
                """)
                self.remove_btn.setCursor(Qt.PointingHandCursor)
                self.remove_btn.clicked.connect(lambda: self.remove_callback(self.template_path))
                self.remove_btn.setToolTip("Remove from recent templates")
                
                # Place in top-right corner
                self.grid.addWidget(self.remove_btn, 0, 0, 1, 1, Qt.AlignRight | Qt.AlignTop)
                
        except Exception as e:
            self.error_label = QLabel(f"Error: {str(e)}")
            self.grid.addWidget(self.error_label, 4, 0)
            
        # Install event filter for hover effects
        self.installEventFilter(self)
        self._update_styling()
    
    def eventFilter(self, obj, event):
        """Handle mouse events for hover effects"""
        if obj is self:
            if event.type() == QEvent.Enter:
                self._on_hover_enter()
                return True
            elif event.type() == QEvent.Leave:
                self._on_hover_leave()
                return True
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if self.select_callback:
                    self.select_callback(self.template_path)
                return True
        
        return super().eventFilter(obj, event)
    
    def _on_hover_enter(self):
        """Handle mouse enter event"""
        if not self.selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['hover_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                }}
            """)
    
    def _on_hover_leave(self):
        """Handle mouse leave event"""
        if not self.selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                }}
            """)
    
    def set_highlighted(self, highlighted):
        """Set card as highlighted or not"""
        self.selected = highlighted
        self._update_styling()
    
    def _update_styling(self):
        """Update card styling based on selection state"""
        if self.selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['highlight_bg']};
                    border: 2px solid {colors['accent']};
                    border-radius: 5px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                }}
            """)

class StructureEditor(QDialog):
    """
    Dialog for editing project structure templates.
    """
    def __init__(self, parent=None, structure=None, save_callback=None, title="Edit Structure", app=None):
        super().__init__(parent)
        
        self.structure = structure or {}
        self.save_callback = save_callback
        self.app = app
        
        # Setup window
        self.setWindowTitle(title)
        self.resize(600, 500)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # Structure name
        name_layout = QHBoxLayout()
        self.layout.addLayout(name_layout)
        
        name_label = QLabel("Structure Name:")
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter structure name...")
        name_layout.addWidget(self.name_input)
        
        # Tree view for structure
        tree_label = QLabel("Folder Structure:")
        tree_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(tree_label)
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Folder Name"])
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.setIndentation(20)
        self.layout.addWidget(self.tree)
        
        # Populate tree with current structure
        self._populate_tree()
        
        # Buttons for manipulating tree
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)
        
        add_btn = QPushButton("Add Folder")
        add_btn.clicked.connect(self._add_folder)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_folder)
        button_layout.addWidget(remove_btn)
        
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self._rename_folder)
        button_layout.addWidget(rename_btn)
        
        # Save/Cancel buttons
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(BUTTON_STYLE)
        self.save_button.clicked.connect(self.save_structure)
        self.button_layout.addWidget(self.save_button)
        
    def _populate_tree(self):
        """Populate the tree widget with the structure"""
        self.tree.clear()
        
        # Create the root item
        root = QTreeWidgetItem(self.tree)
        root.setText(0, "ProjectRoot")
        root.setExpanded(True)
        
        # Add the structure recursively
        self._add_tree_items(root, self.structure)
        
    def _add_tree_items(self, parent_item, structure_dict):
        """Recursively add items to the tree from the structure dictionary"""
        for folder_name, sub_folders in structure_dict.items():
            item = QTreeWidgetItem(parent_item)
            item.setText(0, folder_name)
            item.setExpanded(True)
            
            if isinstance(sub_folders, dict):
                self._add_tree_items(item, sub_folders)
                
    def _add_folder(self):
        """Add a new folder to the selected item"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.topLevelItem(0)
        
        # Get folder name from user
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Enter folder name:")
        
        if ok and folder_name:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, folder_name)
            parent_item.setExpanded(True)
            
    def _remove_folder(self):
        """Remove the selected folder"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        parent = item.parent()
        
        # Don't allow removing the root item
        if not parent:
            QMessageBox.warning(self, "Warning", "Cannot remove the root folder")
            return
            
        # Confirm deletion
        confirm = QMessageBox.question(self, "Confirm Deletion", 
                                    f"Are you sure you want to delete '{item.text(0)}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            parent.removeChild(item)
            
    def _rename_folder(self):
        """Rename the selected folder"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        current_name = item.text(0)
        
        # Don't allow renaming the root item
        if not item.parent():
            QMessageBox.warning(self, "Warning", "Cannot rename the root folder")
            return
            
        # Get new name from user
        new_name, ok = QInputDialog.getText(self, "Rename Folder", 
                                         "Enter new folder name:", text=current_name)
        
        if ok and new_name and new_name != current_name:
            item.setText(0, new_name)
            
    def _get_structure_from_tree(self):
        """Build a structure dictionary from the tree widget"""
        structure = {}
        root = self.tree.topLevelItem(0)
        
        self._build_structure_dict(root, structure)
        
        return structure
        
    def _build_structure_dict(self, item, structure_dict):
        """Recursively build a dictionary from the tree item"""
        for i in range(item.childCount()):
            child = item.child(i)
            folder_name = child.text(0)
            
            if child.childCount() > 0:
                structure_dict[folder_name] = {}
                self._build_structure_dict(child, structure_dict[folder_name])
            else:
                structure_dict[folder_name] = {}
                
    def save_structure(self):
        """Save the structure and close the dialog"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.critical(self, "Error", "Please enter a name for the structure")
            return
            
        # Get the structure from the tree
        structure = self._get_structure_from_tree()
        
        # Call the save callback if provided
        if self.save_callback:
            self.save_callback(name, structure)
            
        self.accept()

class TemplateDirectoryEditor(QDialog):
    """
    Dialog for editing template directories.
    """
    def __init__(self, parent=None, template_path=None, save_callback=None):
        super().__init__(parent)
        
        self.template_path = template_path
        self.save_callback = save_callback
        self.template_info = {}
        
        # Load template info
        if template_path and os.path.isdir(template_path):
            template_json_path = os.path.join(template_path, "template.json")
            if os.path.exists(template_json_path):
                try:
                    with open(template_json_path, 'r') as f:
                        self.template_info = json.load(f)
                except Exception as e:
                    print(f"Error loading template info: {e}")
        
        # Setup window
        self.setWindowTitle("Template Directory Editor")
        self.resize(800, 650)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # === Basic Info Tab ===
        self._create_basic_info_tab()
        
        # === Structure Tab ===
        self._create_structure_tab()
        
        # === Files Tab (for editing actual file content) ===
        self._create_files_tab()
        
        # Add tabs to the main layout
        self.layout.addWidget(self.tabs)
        
        # Add buttons at the bottom
        self._create_buttons()
    
    def _create_basic_info_tab(self):
        """Create the basic info tab"""
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Basic info explanation
        basic_info_explanation = QLabel("Enter basic information about your template:")
        basic_info_explanation.setWordWrap(True)
        basic_layout.addWidget(basic_info_explanation)
        
        # Template name
        name_label = QLabel("Template Name:")
        name_label.setStyleSheet("font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setText(self.template_info.get('name', os.path.basename(self.template_path) if self.template_path else ''))
        
        # Category
        category_label = QLabel("Category:")
        category_label.setStyleSheet("font-weight: bold;")
        self.category_input = QLineEdit()
        self.category_input.setText(self.template_info.get('category', 'General'))
        
        # Description
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: bold;")
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(self.template_info.get('description', ''))
        self.desc_input.setMinimumHeight(100)
        
        # Add to basic layout
        basic_layout.addWidget(name_label)
        basic_layout.addWidget(self.name_input)
        basic_layout.addWidget(category_label)
        basic_layout.addWidget(self.category_input)
        basic_layout.addWidget(desc_label)
        basic_layout.addWidget(self.desc_input)
        
        # Add to tabs
        self.tabs.addTab(basic_tab, "Basic Information")
    
    def _create_structure_tab(self):
        """Create the structure tab"""
        structure_tab = QWidget()
        structure_layout = QVBoxLayout(structure_tab)
        
        structure_info_label = QLabel("Define the folder structure that will be created when using this template:")
        structure_info_label.setWordWrap(True)
        structure_layout.addWidget(structure_info_label)
        
        # Add drag and drop hint
        drag_drop_hint = QLabel("Tip: You can drag and drop folders directly from your file system to quickly import an existing structure.")
        drag_drop_hint.setWordWrap(True)
        drag_drop_hint.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        structure_layout.addWidget(drag_drop_hint)
        
        # Structure tree view
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels(["Folder/File Name"])
        self.structure_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.structure_tree.setDragEnabled(True)
        self.structure_tree.setDragDropMode(QTreeWidget.DragDrop)
        self.structure_tree.setAcceptDrops(True)
        self.structure_tree.viewport().setAcceptDrops(True)
        self.structure_tree.setDropIndicatorShown(True)
        self.structure_tree.dragEnterEvent = self._tree_dragEnterEvent
        self.structure_tree.dragMoveEvent = self._tree_dragMoveEvent
        self.structure_tree.dropEvent = self._tree_dropEvent
        structure_layout.addWidget(self.structure_tree)
        
        # Root item
        self.root_item = QTreeWidgetItem(self.structure_tree)
        self.root_item.setText(0, "Project Root")
        self.root_item.setExpanded(True)
        
        # Populate tree with current template structure
        if self.template_path and os.path.isdir(self.template_path):
            self._populate_tree_from_directory(self.root_item, self.template_path)
        
        # Buttons for tree manipulation
        tree_buttons = QHBoxLayout()
        
        add_folder_btn = QPushButton("Add Folder")
        add_file_btn = QPushButton("Add File")
        remove_btn = QPushButton("Remove")
        rename_btn = QPushButton("Rename")
        
        add_folder_btn.clicked.connect(self._add_folder)
        add_file_btn.clicked.connect(self._add_file)
        remove_btn.clicked.connect(self._remove_item)
        rename_btn.clicked.connect(self._rename_item)
        
        tree_buttons.addWidget(add_folder_btn)
        tree_buttons.addWidget(add_file_btn)
        tree_buttons.addWidget(remove_btn)
        tree_buttons.addWidget(rename_btn)
        
        structure_layout.addLayout(tree_buttons)
        
        # Add to tabs
        self.tabs.addTab(structure_tab, "Folder Structure")
    
    def _create_files_tab(self):
        """Create the files tab"""
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        
        files_info_label = QLabel("Template files with placeholder content:")
        files_info_label.setWordWrap(True)
        files_layout.addWidget(files_info_label)
        
        # File list with explanation
        files_explanation = QLabel("This tab allows you to edit the content of text files in your template. "
                               "Files will be automatically populated when you add them to the structure.")
        files_explanation.setWordWrap(True)
        files_explanation.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        files_layout.addWidget(files_explanation)
        
        # File list
        files_list_frame = QFrame()
        files_list_layout = QHBoxLayout(files_list_frame)
        files_list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.files_list = QListWidget()
        self.files_list.itemSelectionChanged.connect(self._on_file_selected)
        files_list_layout.addWidget(self.files_list)
        
        # File buttons
        file_buttons = QVBoxLayout()
        add_file_to_list_btn = QPushButton("Add")
        remove_file_btn = QPushButton("Remove")
        
        add_file_to_list_btn.clicked.connect(self._add_file_to_template)
        remove_file_btn.clicked.connect(self._remove_file_from_template)
        
        file_buttons.addWidget(add_file_to_list_btn)
        file_buttons.addWidget(remove_file_btn)
        file_buttons.addStretch()
        
        files_list_layout.addLayout(file_buttons)
        files_layout.addWidget(files_list_frame)
        
        # File content editor
        content_label = QLabel("File Content:")
        content_label.setStyleSheet("font-weight: bold;")
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText("Select a file to edit its content")
        self.content_editor.setMinimumHeight(200)
        
        save_content_btn = QPushButton("Save Content")
        save_content_btn.clicked.connect(self._save_file_content)
        
        files_layout.addWidget(content_label)
        files_layout.addWidget(self.content_editor)
        files_layout.addWidget(save_content_btn)
        
        # Populate file list if template path exists
        if self.template_path and os.path.isdir(self.template_path):
            self._populate_file_list(self.template_path)
        
        # Add to tabs
        self.tabs.addTab(files_tab, "Files")
    
    def _create_buttons(self):
        """Create the bottom buttons"""
        self.button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save Template")
        self.save_button.setObjectName("accentButton")
        self.save_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.save_button.clicked.connect(self.save_template)
        self.button_layout.addWidget(self.save_button)
        
        self.layout.addLayout(self.button_layout)
    
    def _populate_tree_from_directory(self, parent_item, directory_path):
        """Populate the tree with items from a directory structure"""
        # Skip template.json file
        skip_files = ["template.json"]
        
        try:
            items = os.listdir(directory_path)
            for item in sorted(items):
                if item in skip_files:
                    continue
                    
                item_path = os.path.join(directory_path, item)
                is_dir = os.path.isdir(item_path)
                
                tree_item = QTreeWidgetItem(parent_item)
                tree_item.setText(0, item)
                
                if is_dir:
                    # It's a directory, set icon and expand
                    tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    tree_item.setExpanded(True)
                    # Recursively add children
                    self._populate_tree_from_directory(tree_item, item_path)
                else:
                    # It's a file, set icon
                    tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        except Exception as e:
            print(f"Error populating tree: {e}")
    
    def _populate_file_list(self, directory_path):
        """Populate the file list with files from the template directory"""
        self.files_list.clear()
        
        # Skip template.json and directories
        skip_files = ["template.json"]
        
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in sorted(files):
                    if file in skip_files:
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, directory_path)
                    
                    # Only add text files that can be edited
                    if self._is_text_file(file_path):
                        self.files_list.addItem(rel_path)
        except Exception as e:
            print(f"Error populating file list: {e}")
    
    def _is_text_file(self, file_path):
        """Check if a file is likely a text file that can be edited"""
        # List of common text file extensions
        text_extensions = ['.html', '.css', '.js', '.json', '.txt', '.md', '.xml', '.csv', '.py', '.c', '.cpp', '.h', '.java', '.php', '.rb', '.pl', '.sh', '.bat', '.ini']
        
        # Check if extension matches common text extensions
        _, ext = os.path.splitext(file_path)
        if ext.lower() in text_extensions:
            return True
        
        # For files without extension or unknown extension, try to detect
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read as text
                return True
        except UnicodeDecodeError:
            return False  # Not a text file
        except Exception:
            return False  # Some other error, assume not a text file
    
    def _add_folder(self):
        """Add a new folder to the structure"""
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder Name:")
        if ok and folder_name:
            selected_items = self.structure_tree.selectedItems()
            parent_item = selected_items[0] if selected_items else self.root_item
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, folder_name)
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            parent_item.setExpanded(True)
    
    def _add_file(self):
        """Add a new file to the structure from the user's filesystem"""
        # First, let user select a file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai);;Text Files (*.html *.css *.js *.txt *.md)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Get the filename and suggested name with {{PROJECT_NAME}} placeholder
        original_filename = os.path.basename(file_path)
        filename_base, filename_ext = os.path.splitext(original_filename)
        suggested_name = f"{{{{PROJECT_NAME}}}}{filename_ext}"
        
        # Ask for the filename to use (with the project name placeholder)
        new_filename, ok = QInputDialog.getText(
            self,
            "File Name in Template",
            "Enter filename (use {{PROJECT_NAME}} as placeholder):",
            text=suggested_name
        )
        
        if not ok or not new_filename:
            return
            
        # Get selected target directory in the structure tree
        selected_items = self.structure_tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.root_item
        
        # If the selected item is a file, use its parent as the directory
        if parent_item != self.root_item and parent_item.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.SP_FileIcon).cacheKey():
            parent_item = parent_item.parent() or self.root_item
        
        # Add the file to the structure tree
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, new_filename)
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setData(0, Qt.UserRole, file_path)  # Store original file path for later
        parent_item.setExpanded(True)
        
        # If we have a template directory, copy the file there
        if self.template_path and os.path.isdir(self.template_path):
            try:
                # Determine the target path within the template directory
                # Get the path from root to selected directory
                target_dir_path = self._get_item_path(parent_item)
                target_dir = os.path.join(self.template_path, target_dir_path)
                
                # Make sure the target directory exists
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy the file to the template directory
                dest_path = os.path.join(target_dir, new_filename)
                shutil.copy2(file_path, dest_path)
                
                # If it's a text file, replace placeholders
                if self._is_text_file(dest_path):
                    self._replace_placeholders(dest_path)
                
                # Update the file list on the Files tab
                self._populate_file_list(self.template_path)
                
                QMessageBox.information(
                    self, 
                    "File Added", 
                    f"File '{new_filename}' added to the template structure at '{target_dir_path}'.\n\n"
                    f"When a project is created, {{PROJECT_NAME}} placeholders will be replaced with the actual project name."
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to copy file: {str(e)}")
    
    def _get_item_path(self, item):
        """Get the path from root to the given item"""
        path_parts = []
        current = item
        
        # Don't include the root item in the path
        while current and current != self.root_item:
            path_parts.insert(0, current.text(0))
            current = current.parent()
            
        return os.path.join(*path_parts) if path_parts else ""
    
    def _replace_placeholders(self, file_path):
        """Replace placeholders in text files"""
        try:
            if not self._is_text_file(file_path):
                return
                
            # Read the file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Replace some common placeholders with their template versions
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            current_year = datetime.datetime.now().strftime("%Y")
            
            # Replace direct project name references with the placeholder
            content = content.replace("{{DATE}}", current_date)
            content = content.replace("{{YEAR}}", current_year)
            
            # Write back the content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error replacing placeholders in {file_path}: {e}")
    
    def _remove_item(self):
        """Remove selected item from the structure tree"""
        selected_items = self.structure_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if item != self.root_item:  # Don't remove the root
                parent = item.parent() or self.structure_tree.invisibleRootItem()
                parent.removeChild(item)
    
    def _rename_item(self):
        """Rename selected item in the structure tree"""
        selected_items = self.structure_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if item != self.root_item:  # Don't rename the root
                name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=item.text(0))
                if ok and name:
                    item.setText(0, name)
    
    def _add_file_to_template(self):
        """Add a file to the template"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Add",
            "",
            "Text Files (*.html *.css *.js *.txt *.md);;All Files (*)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
        
        # Get the filename
        filename = os.path.basename(file_path)
        
        # Ask where to add it in the template
        if self.template_path and os.path.isdir(self.template_path):
            # Copy the file to the template directory
            dest_path = os.path.join(self.template_path, filename)
            try:
                shutil.copy2(file_path, dest_path)
                # Refresh file list
                self._populate_file_list(self.template_path)
                # Select the new file
                for i in range(self.files_list.count()):
                    if self.files_list.item(i).text() == filename:
                        self.files_list.setCurrentRow(i)
                        break
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add file: {str(e)}")
    
    def _remove_file_from_template(self):
        """Remove selected file from the template"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
            
        filename = selected_items[0].text()
        if not filename:
            return
            
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to remove '{filename}' from the template?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
            
        # Remove the file
        if self.template_path and os.path.isdir(self.template_path):
            file_path = os.path.join(self.template_path, filename)
            try:
                os.remove(file_path)
                # Refresh file list
                self._populate_file_list(self.template_path)
                # Clear editor
                self.content_editor.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to remove file: {str(e)}")
    
    def _on_file_selected(self):
        """Handle file selection in the list"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            self.content_editor.clear()
            return
            
        filename = selected_items[0].text()
        if not filename or not self.template_path:
            self.content_editor.clear()
            return
            
        # Load file content
        file_path = os.path.join(self.template_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content_editor.setPlainText(f.read())
        except Exception as e:
            self.content_editor.setPlainText(f"Error loading file: {str(e)}")
    
    def _save_file_content(self):
        """Save changes to the selected file"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
            
        filename = selected_items[0].text()
        if not filename or not self.template_path:
            return
            
        # Save content to file
        file_path = os.path.join(self.template_path, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.content_editor.toPlainText())
            QMessageBox.information(self, "Success", f"File '{filename}' saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
    
    def _get_structure_from_tree(self):
        """Get a structure definition from the tree widget"""
        result = []
        
        def traverse(item):
            items = []
            for i in range(item.childCount()):
                child = item.child(i)
                child_name = child.text(0)
                has_children = child.childCount() > 0
                
                if has_children:
                    # Directory with children
                    sub_items = traverse(child)
                    items.append({child_name: sub_items})
                else:
                    # Is it a folder or file? Check the icon
                    icon = child.icon(0)
                    if icon.isNull() or child.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.SP_DirIcon).cacheKey():
                        # It's a folder (empty)
                        items.append(f"{child_name}/")
                    else:
                        # It's a file
                        items.append(child_name)
            
            return items
        
        return traverse(self.root_item)
    
    def save_template(self):
        """Save the template and close the dialog"""
        # Validate basic info
        name = self.name_input.text().strip()
        category = self.category_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Template name is required")
            return
            
        if not category:
            QMessageBox.warning(self, "Validation Error", "Category is required")
            return
        
        # Create structure name
        structure_name = f"Template_{name}"
        
        # Get structure from tree
        structure = self._get_structure_from_tree()
        
        # Update template info
        self.template_info['name'] = name
        self.template_info['category'] = category
        self.template_info['description'] = description
        self.template_info['structure_name'] = structure_name
        self.template_info['updated'] = datetime.datetime.now().isoformat()
        
        if not self.template_path:
            QMessageBox.warning(self, "Error", "No template directory specified")
            return
        
        try:
            # Save template.json
            template_json_path = os.path.join(self.template_path, "template.json")
            with open(template_json_path, 'w') as f:
                json.dump(self.template_info, f, indent=2)
                
            # Also save the structure definition
            parent = self.parent()
            if parent and hasattr(parent, 'template_manager'):
                parent.template_manager.save_custom_structure(structure_name, structure)
            
            # Call the save callback if provided
            if self.save_callback:
                self.save_callback(self.template_path)
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")
            return

    def _tree_dragEnterEvent(self, event):
        """Custom drag enter event for the tree widget"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            QTreeWidget.dragEnterEvent(self.structure_tree, event)
            
    def _tree_dragMoveEvent(self, event):
        """Custom drag move event for the tree widget"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            QTreeWidget.dragMoveEvent(self.structure_tree, event)
            
    def _tree_dropEvent(self, event):
        """Custom drop event for the tree widget"""
        if event.mimeData().hasUrls():
            print("DEBUG: TemplateDirectoryEditor drop event with URLs detected")
            # Get drop position
            drop_item = self.structure_tree.itemAt(event.pos())
            if not drop_item:
                drop_item = self.root_item
                print("DEBUG: Drop location is root item")
            else:
                print(f"DEBUG: Drop location is {drop_item.text(0)}")
                
            # Process the dropped URLs
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"DEBUG: Processing dropped path: {file_path}")
                
                # Ensure path exists and is accessible
                if not os.path.exists(file_path):
                    print(f"DEBUG: Path doesn't exist: {file_path}")
                    continue
                    
                if os.path.isdir(file_path):
                    print(f"DEBUG: It's a directory: {file_path}")
                    # For macOS, handle folder paths more carefully
                    dir_name = os.path.basename(os.path.normpath(file_path))
                    print(f"DEBUG: Directory name extracted: {dir_name}")
                    
                    # Skip hidden Mac folders
                    if dir_name.startswith('.'):
                        print(f"DEBUG: Skipping hidden Mac directory: {dir_name}")
                        continue
                    
                    # Create folder item directly
                    folder_item = QTreeWidgetItem(drop_item)
                    folder_item.setText(0, dir_name)
                    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    folder_item.setExpanded(True)
                    
                    # If we have a template directory, create the actual directory
                    if self.template_path and os.path.isdir(self.template_path):
                        # Calculate the relative path for this directory
                        rel_path = self._get_item_path(folder_item)
                        target_dir = os.path.join(self.template_path, rel_path)
                        
                        # Create the directory if it doesn't exist
                        try:
                            os.makedirs(target_dir, exist_ok=True)
                            print(f"DEBUG: Created directory: {target_dir}")
                        except Exception as e:
                            print(f"DEBUG: Error creating directory {target_dir}: {e}")
                    
                    # Recursively process subdirectories
                    try:
                        for item in sorted(os.listdir(file_path)):
                            # Skip hidden Mac files
                            if item.startswith('.'):
                                continue
                                
                            item_full_path = os.path.join(file_path, item)
                            if os.path.isdir(item_full_path):
                                self._process_dropped_directory(item_full_path, folder_item)
                            else:
                                self._add_file_to_tree(item_full_path, folder_item)
                    except Exception as e:
                        print(f"DEBUG: Error processing directory contents: {e}")
                else:
                    print(f"DEBUG: It's a file: {file_path}")
                    self._add_file_to_tree(file_path, drop_item)
            
            print("DEBUG: Drop event processing completed")
            event.acceptProposedAction()
        else:
            QTreeWidget.dropEvent(self.structure_tree, event)
            
    def _process_dropped_directory(self, dir_path, parent_item):
        """Process a directory dropped onto the tree"""
        # Create a folder item for this directory
        dir_name = os.path.basename(dir_path)
        
        # Skip .DS_Store and other hidden Mac files
        if dir_name.startswith('.'):
            return None
            
        # Create the folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, dir_name)
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        folder_item.setExpanded(True)
        
        # If we have a template directory, create the actual directory
        if self.template_path and os.path.isdir(self.template_path):
            # Calculate the relative path for this directory
            rel_path = self._get_item_path(folder_item)
            target_dir = os.path.join(self.template_path, rel_path)
            
            # Create the directory if it doesn't exist
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                print(f"Error creating directory {target_dir}: {e}")
        
        # Add all subdirectories and files
        try:
            for item in os.listdir(dir_path):
                # Skip hidden files on Mac
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    # Recursively add subdirectory
                    self._process_dropped_directory(item_path, folder_item)
                else:
                    # Add file
                    self._add_file_to_tree(item_path, folder_item)
        except Exception as e:
            print(f"Error processing directory {dir_path}: {e}")
            
        return folder_item
            
    def _add_file_to_tree(self, file_path, parent_item):
        """Add a file to the structure tree and copy it to the template"""
        # Get filename and suggested name with PROJECT_NAME placeholder
        original_filename = os.path.basename(file_path)
        filename_base, filename_ext = os.path.splitext(original_filename)
        
        # Create a new file item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, original_filename)
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setData(0, Qt.UserRole, file_path)  # Store the original path
        
        # Auto-expand the parent
        parent_item.setExpanded(True)
        
        # If we have a template directory, copy the file
        if self.template_path and os.path.isdir(self.template_path):
            try:
                # Calculate the relative path for this file
                rel_path = self._get_item_path(parent_item)
                target_dir = os.path.join(self.template_path, rel_path)
                
                # Make sure the target directory exists
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy the file
                dest_path = os.path.join(target_dir, original_filename)
                shutil.copy2(file_path, dest_path)
                
                # If it's a text file, add placeholders
                if self._is_text_file(dest_path):
                    self._replace_placeholders(dest_path)
                    
                # Update the files list
                self._populate_file_list(self.template_path)
            except Exception as e:
                print(f"Error copying file {file_path}: {e}")

class ProjectNameInput(QDialog):
    """
    Dialog for inputting project names for batch creation
    """
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback
        
        # Set window properties
        self.setWindowTitle("Batch Project Creation")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Enter Project Names")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet(f"color: {colors['text']};")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "Enter one project name per line. You can also separate names with commas or semicolons.\n"
            "All projects will be created using the currently selected template and output location."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {colors['secondary_text']};")
        layout.addWidget(instructions)
        
        # Text input area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Project 1\nProject 2\nProject 3")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.create_button = QPushButton("Create Projects")
        self.create_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.create_button.clicked.connect(self.process_projects)
        button_layout.addWidget(self.create_button)
        
        layout.addLayout(button_layout)
        
        # Set focus to text edit
        self.text_edit.setFocus()
    
    def process_projects(self):
        """Process the entered project names and pass to callback"""
        text = self.text_edit.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter at least one project name.")
            return
        
        # Split by newlines, commas, or semicolons
        project_names = re.split(r'[\n,;]+', text)
        project_names = [name.strip() for name in project_names if name.strip()]
        
        if not project_names:
            QMessageBox.warning(self, "Warning", "No valid project names found.")
            return
        
        # Check for duplicate names
        if len(project_names) != len(set(project_names)):
            duplicates = [name for name in project_names if project_names.count(name) > 1]
            if QMessageBox.question(
                self, 
                "Duplicate Names", 
                f"The following names appear more than once: {', '.join(set(duplicates))}\n\nDo you want to continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.No:
                return
        
        # Validate parent has needed attributes for project creation
        parent = self.parent()
        missing_requirements = []
        
        if not hasattr(parent, 'template_file_path') or not parent.template_file_path:
            missing_requirements.append("No template file selected")
        
        output_dir = parent.get_current_output_dir() if hasattr(parent, 'get_current_output_dir') else None
        if not output_dir:
            missing_requirements.append("No output directory selected")
        
        if missing_requirements:
            QMessageBox.critical(
                self, 
                "Missing Requirements", 
                "Cannot create projects due to the following issues:\n\n" + 
                "\n".join([f"• {item}" for item in missing_requirements])
            )
            self.reject()
            return
        
        # Show confirmation with count
        if QMessageBox.question(
            self, 
            "Confirm Batch Creation", 
            f"You are about to create {len(project_names)} projects.\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return
            
        if self.callback:
            self.callback(project_names)
        self.accept()

class TemplateFolderCard(QFrame):
    """Template folder card widget for displaying a folder in the gallery"""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, parent=None, folder_name="", app=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.app = app
        self.selected = False
        self.hover = False
        
        # Setup styling
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(200, 250)
        self.setCursor(Qt.PointingHandCursor)
        
        # Use a fixed grid layout with fixed row heights
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setSpacing(2)
        self.grid.setRowStretch(0, 3)  # Icon gets most space
        self.grid.setRowStretch(1, 0)  # Title gets minimum space needed
        self.grid.setRowStretch(2, 0)  # Folder label gets minimum space
        self.grid.setRowStretch(3, 2)  # Bottom empty space
        
        # Folder icon
        self.icon_label = QLabel("📁")  # Using a folder emoji
        self.icon_label.setFont(QFont("Segoe UI", 48))
        self.icon_label.setStyleSheet(f"color: {colors['secondary_text']};")
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Folder name
        self.title = QLabel(folder_name)
        self.title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: white;")
        
        # Folder label
        self.folder_label = QLabel("Folder")
        self.folder_label.setFont(QFont("Segoe UI", 9))
        self.folder_label.setAlignment(Qt.AlignCenter)
        self.folder_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        
        # Empty widget for bottom space
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Add widgets to grid
        self.grid.addWidget(self.icon_label, 0, 0)
        self.grid.addWidget(self.title, 1, 0)
        self.grid.addWidget(self.folder_label, 2, 0)
        self.grid.addWidget(empty, 3, 0)
        
        # Install event filter for mouse events
        self.installEventFilter(self)
        self._update_styling()
    
    def eventFilter(self, obj, event):
        """Handle mouse events for hover and click effects"""
        if obj is self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self._update_styling()
                return True
            elif event.type() == QEvent.Leave:
                self.hover = False
                self._update_styling()
                return True
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self.clicked.emit(self.folder_name)
                return True
        return super().eventFilter(obj, event)
        
    def _update_styling(self):
        """Update folder card styling based on hover state"""
        base_style = f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 5px;
            }}
        """
        
        hover_style = f"""
            QFrame {{
                background-color: {colors['highlight_bg']};
                border: 2px solid {colors['accent']};
                border-radius: 5px;
            }}
        """
        
        # Keep text colors consistent
        self.title.setStyleSheet("color: white;")
        self.folder_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        
        # Apply main frame styles without affecting layout
        if self.hover:
            self.setStyleSheet(hover_style)
        else:
            self.setStyleSheet(base_style) 