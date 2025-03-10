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
                            QApplication, QStyle, QComboBox, QSplitter,
                            QLayout, QLayoutItem)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QEvent, QRect
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
        
        # Add dropdown for predefined structures
        if app:
            structure_layout = QHBoxLayout()
            self.layout.addLayout(structure_layout)
            
            structure_label = QLabel("Use Predefined Structure:")
            structure_layout.addWidget(structure_label)
            
            self.structure_combo = QComboBox()
            self._populate_structure_combo()
            self.structure_combo.currentIndexChanged.connect(self._load_selected_structure)
            structure_layout.addWidget(self.structure_combo)
        
        # Tree view for structure
        tree_label = QLabel("Folder Structure:")
        tree_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(tree_label)
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Folder Name", "Type"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.setIndentation(20)
        
        # Enable external drag and drop
        self.tree.setAcceptDrops(True)
        self.tree.viewport().setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        
        # Custom handlers for drag and drop
        self.tree.dragEnterEvent = self._dragEnterEvent
        self.tree.dragMoveEvent = self._dragMoveEvent
        self.tree.dropEvent = self._dropEvent
        
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
        
    def _populate_structure_combo(self):
        """Populate the structure dropdown with available structures"""
        if not hasattr(self, 'structure_combo') or not self.app:
            return
            
        self.structure_combo.clear()
        
        # Add default structures
        self.structure_combo.addItem("Standard")
        self.structure_combo.addItem("Video Editing")
        self.structure_combo.addItem("Motion Graphics")
        self.structure_combo.addItem("Design")
        self.structure_combo.addItem("Audio")
        
        # Add custom structures
        if hasattr(self.app, 'template_manager'):
            for name in sorted(self.app.template_manager.custom_structures.keys()):
                self.structure_combo.addItem(name)
                
    def _load_selected_structure(self):
        """Load the selected structure from the dropdown"""
        if not hasattr(self, 'structure_combo') or not self.app:
            return
            
        structure_name = self.structure_combo.currentText()
        if not structure_name:
            return
            
        # Get the structure
        if hasattr(self.app, 'template_manager'):
            structure = self.app.template_manager.get_structure(structure_name)
            if structure:
                self.structure = structure
                self._populate_tree()
        
    def _populate_tree(self):
        """Populate the tree widget with the structure"""
        self.tree.clear()
        
        # Create the root item
        root = QTreeWidgetItem(self.tree)
        root.setText(0, "ProjectRoot")
        root.setText(1, "Directory")  # Add type column
        root.setExpanded(True)
        
        # Set folder icon for the root
        root.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        
        # Add the structure recursively
        self._add_tree_items(root, self.structure)
        
    def _add_tree_items(self, parent_item, structure_dict):
        """Recursively add items to the tree from the structure dictionary"""
        if not isinstance(structure_dict, dict):
            print(f"WARNING: Expected dict for structure but got {type(structure_dict)}")
            return
            
        for folder_name, sub_folders in structure_dict.items():
            item = QTreeWidgetItem(parent_item)
            item.setText(0, folder_name)
            item.setText(1, "Directory")  # Add type column
            item.setExpanded(True)
            
            # Set folder icon for items
            item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            
            if isinstance(sub_folders, dict):
                self._add_tree_items(item, sub_folders)
                
    def _dragEnterEvent(self, event):
        """Handle drag enter events, including from external sources"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # Default handling for internal drags
            QTreeWidget.dragEnterEvent(self.tree, event)
            
    def _dragMoveEvent(self, event):
        """Handle drag move events, including from external sources"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # Default handling for internal drags
            QTreeWidget.dragMoveEvent(self.tree, event)
            
    def _dropEvent(self, event):
        """Handle drop events, including from external sources"""
        if event.mimeData().hasUrls():
            # External drop from OS file browser
            urls = event.mimeData().urls()
            
            # Get the drop target item
            drop_position = event.pos()
            target_item = self.tree.itemAt(drop_position)
            if not target_item:
                target_item = self.tree.topLevelItem(0)  # Default to root if no target
                
            # Process each dropped URL
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.exists(file_path):
                    self._add_external_path(file_path, target_item)
            
            # Auto-save the structure after drop
            self._auto_save_structure_after_drop()
                    
            event.acceptProposedAction()
        else:
            # Default handling for internal drags
            QTreeWidget.dropEvent(self.tree, event)
            
            # Auto-save after internal drop too
            self._auto_save_structure_after_drop()
    
    def _auto_save_structure_after_drop(self):
        """Auto-save the structure after a drop event"""
        try:
            # Get the structure name from the input field
            if hasattr(self, 'name_input') and self.app:
                name = self.name_input.text().strip()
                if name:
                    # Get the structure from the tree
                    structure = self._get_structure_from_tree()
                    
                    # Debug
                    print(f"DEBUG: Auto-saving structure after drop: {name}")
                    print(f"DEBUG: Structure content: {json.dumps(structure, indent=2)}")
                    
                    # Save it
                    if hasattr(self.app, 'template_manager'):
                        self.app.template_manager.save_custom_structure(name, structure)
        except Exception as e:
            print(f"DEBUG: Error auto-saving structure after drop: {e}")

    def _add_external_path(self, path, parent_item):
        """Add an external file or directory path to the tree"""
        name = os.path.basename(path)
        
        # Create a new item
        item = QTreeWidgetItem(parent_item)
        item.setText(0, name)
        
        # Set appropriate icon and type
        if os.path.isdir(path):
            item.setText(1, "Directory")
            item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            
            # If it's a directory, add all its contents recursively
            for child_name in os.listdir(path):
                child_path = os.path.join(path, child_name)
                self._add_external_path(child_path, item)
        else:
            item.setText(1, "File")
            item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            
        item.setExpanded(True)
            
    def _add_folder(self):
        """Add a new folder to the tree"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.topLevelItem(0)
        
        # Get folder name from user
        folder_name, ok = QInputDialog.getText(self, "Add Folder", 
                                            "Enter folder name:")
        
        if ok and folder_name:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, folder_name)
            item.setText(1, "Directory")  # Add type column
            
            # Set folder icon
            item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            
            parent_item.setExpanded(True)
            
    def _remove_folder(self):
        """Remove the selected folder"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        
        # Don't allow removing the root item
        if not item.parent():
            QMessageBox.warning(self, "Warning", "Cannot remove the root folder")
            return
            
        # Confirm removal
        confirm = QMessageBox.question(self, "Confirm Removal", 
                                    f"Are you sure you want to remove '{item.text(0)}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            # Get parent and index to remove
            parent = item.parent()
            index = parent.indexOfChild(item)
            parent.takeChild(index)
            
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
        
        # Debug output
        print(f"DEBUG: Generated structure from tree: {json.dumps(structure, indent=2)}")
        
        return structure
        
    def _build_structure_dict(self, item, structure_dict):
        """Recursively build a dictionary from the tree item"""
        for i in range(item.childCount()):
            child = item.child(i)
            folder_name = child.text(0)
            is_dir = child.text(1) == "Directory"
            
            if is_dir:
                structure_dict[folder_name] = {}
                if child.childCount() > 0:
                    self._build_structure_dict(child, structure_dict[folder_name])
            else:
                # For files, we still use an empty dict to maintain consistency
                structure_dict[folder_name] = {}
                
    def save_structure(self):
        """Save the structure and close the dialog"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.critical(self, "Error", "Please enter a name for the structure")
            return
            
        # Get the structure from the tree
        structure = self._get_structure_from_tree()
        
        # Output debug information
        try:
            print(f"DEBUG: Saving structure '{name}' with {len(structure)} items")
            print(f"DEBUG: Structure content: {json.dumps(structure, indent=2)}")
        except Exception as e:
            print(f"DEBUG: Error serializing structure: {e}")
        
        # Call the save callback if provided
        if self.save_callback:
            self.save_callback(name, structure)
            
        self.accept()

class TemplateDirectoryEditor(QDialog):
    """
    Dialog for editing directory-based templates.
    """
    def __init__(self, parent=None, template_path=None, save_callback=None, app=None):
        super().__init__(parent)
        
        self.template_path = template_path
        self.save_callback = save_callback
        self.app = app
        self.selected_file = None
        
        # Setup window
        self.setWindowTitle("Template Directory Editor")
        self.resize(800, 600)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Create tabs for different aspects of the template
        self._create_basic_info_tab()
        self._create_structure_tab()
        self._create_files_tab()
        
        # Create buttons
        self._create_buttons()
        
        # Load template data if path provided
        if template_path and os.path.isdir(template_path):
            self._load_template_data()
            
    def _create_basic_info_tab(self):
        """Create the basic info tab"""
        basic_tab = QWidget()
        self.tabs.addTab(basic_tab, "Basic Info")
        
        # Layout for this tab
        layout = QVBoxLayout(basic_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Template name
        name_layout = QHBoxLayout()
        name_label = QLabel("Template Name:")
        name_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_layout.addWidget(category_label)
        
        self.category_input = QLineEdit()
        category_layout.addWidget(self.category_input)
        layout.addLayout(category_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        layout.addWidget(self.desc_input)
        
        # Load template data if available
        if self.template_path and os.path.isdir(self.template_path):
            template_json_path = os.path.join(self.template_path, "template.json")
            if os.path.exists(template_json_path):
                try:
                    with open(template_json_path, 'r') as f:
                        info = json.load(f)
                        self.name_input.setText(info.get('name', ''))
                        self.category_input.setText(info.get('category', ''))
                        self.desc_input.setText(info.get('description', ''))
                except Exception as e:
                    print(f"Error loading template info: {e}")
                    
    def _create_structure_tab(self):
        """Create the structure tab"""
        structure_tab = QWidget()
        self.tabs.addTab(structure_tab, "Structure")
        
        # Layout for this tab
        layout = QVBoxLayout(structure_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Add dropdown for predefined structures
        if self.app:
            structure_layout = QHBoxLayout()
            layout.addLayout(structure_layout)
            
            structure_label = QLabel("Use Predefined Structure:")
            structure_layout.addWidget(structure_label)
            
            self.structure_combo = QComboBox()
            self._populate_structure_combo()
            self.structure_combo.currentIndexChanged.connect(self._load_selected_structure)
            structure_layout.addWidget(self.structure_combo)
            
            # Add a button to open the structure editor
            edit_structure_btn = QPushButton("Edit Structures...")
            edit_structure_btn.clicked.connect(self._open_structure_editor)
            structure_layout.addWidget(edit_structure_btn)
        
        # Tree view layout
        layout.addWidget(QLabel("Directory Structure:"))
        
        # Create tree widget for the structure
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels(["Name", "Type"])
        self.structure_tree.setColumnWidth(0, 300)
        layout.addWidget(self.structure_tree)
        
        # Enable drag & drop
        self.structure_tree.setDragEnabled(True)
        self.structure_tree.setAcceptDrops(True)
        self.structure_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.structure_tree.viewport().setAcceptDrops(True)
        self.structure_tree.setDropIndicatorShown(True)
        
        # Set custom event handlers for drag & drop
        self.structure_tree.dragEnterEvent = self._tree_dragEnterEvent
        self.structure_tree.dragMoveEvent = self._tree_dragMoveEvent
        self.structure_tree.dropEvent = self._tree_dropEvent
        
        # Buttons for manipulating the tree
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        btn_layout.addWidget(add_folder_btn)
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_file)
        btn_layout.addWidget(add_file_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_item)
        btn_layout.addWidget(remove_btn)
        
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self._rename_item)
        btn_layout.addWidget(rename_btn)
        
        # If we have a path, populate the tree
        if self.template_path and os.path.isdir(self.template_path):
            # Create the root item
            root = QTreeWidgetItem(self.structure_tree)
            root.setText(0, "Template Root")
            root.setText(1, "Directory")
            root.setExpanded(True)
            
            # Set folder icon
            root.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            
            # Populate the tree recursively
            self._populate_tree_from_directory(root, self.template_path)

    def _populate_structure_combo(self):
        """Populate the structure dropdown with available structures"""
        if not hasattr(self, 'structure_combo') or not self.app:
            return
            
        self.structure_combo.clear()
        
        # Add default structures
        self.structure_combo.addItem("Standard")
        self.structure_combo.addItem("Video Editing")
        self.structure_combo.addItem("Motion Graphics")
        self.structure_combo.addItem("Design")
        self.structure_combo.addItem("Audio")
        
        # Add custom structures
        if hasattr(self.app, 'template_manager'):
            for name in sorted(self.app.template_manager.custom_structures.keys()):
                self.structure_combo.addItem(name)
    
    def _load_selected_structure(self):
        """Load the selected structure from the dropdown"""
        if not hasattr(self, 'structure_combo') or not self.app:
            return
            
        structure_name = self.structure_combo.currentText()
        if not structure_name:
            return
            
        # Get the structure
        if hasattr(self.app, 'template_manager'):
            structure = self.app.template_manager.get_structure(structure_name)
            if structure:
                # Clear the tree except for the root
                root = self.structure_tree.topLevelItem(0)
                if root:
                    # Remove all children
                    while root.childCount() > 0:
                        root.removeChild(root.child(0))
                else:
                    # Create the root if it doesn't exist
                    root = QTreeWidgetItem(self.structure_tree)
                    root.setText(0, "Template Root")
                    root.setText(1, "Directory")
                    root.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    
                # Add the structure recursively
                self._add_structure_to_tree(root, structure)
                root.setExpanded(True)
    
    def _add_structure_to_tree(self, parent_item, structure_dict):
        """Recursively add a structure dictionary to the tree"""
        for folder_name, sub_folders in structure_dict.items():
            # Create a new folder item
            item = QTreeWidgetItem(parent_item)
            item.setText(0, folder_name)
            item.setText(1, "Directory")
            item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            
            # If it has subfolders, add them recursively
            if isinstance(sub_folders, dict) and sub_folders:
                self._add_structure_to_tree(item, sub_folders)
                
            item.setExpanded(True)
    
    def _open_structure_editor(self):
        """Open the structure editor dialog"""
        if not self.app:
            return
            
        from app.core.structures_pyqt import edit_structure, create_custom_structure
        create_custom_structure(self.app)
        
        # Update the dropdown after editing
        self._populate_structure_combo()

    def _tree_dragEnterEvent(self, event):
        """Handle drag enter events including from external sources"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            QTreeWidget.dragEnterEvent(self.structure_tree, event)
            
    def _tree_dragMoveEvent(self, event):
        """Handle drag move events including from external sources"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            QTreeWidget.dragMoveEvent(self.structure_tree, event)
            
    def _tree_dropEvent(self, event):
        """Handle drop events including from external sources"""
        if event.mimeData().hasUrls():
            # External drop - from file explorer
            urls = event.mimeData().urls()
            drop_position = event.pos()
            
            # Find the item at the drop position
            target_item = self.structure_tree.itemAt(drop_position)
            
            # If no item found, use the root
            if not target_item:
                if self.structure_tree.topLevelItemCount() > 0:
                    target_item = self.structure_tree.topLevelItem(0)
                else:
                    # Create root if it doesn't exist
                    target_item = QTreeWidgetItem(self.structure_tree)
                    target_item.setText(0, "Template Root")
                    target_item.setText(1, "Directory")
                    target_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    
            # Check if the target is a file - we can only drop into directories
            if target_item.text(1) != "Directory":
                # Get the parent directory instead
                if target_item.parent():
                    target_item = target_item.parent()
                else:
                    # If somehow we don't have a parent, use the root
                    target_item = self.structure_tree.topLevelItem(0)
                    
            # Process each dropped URL
            for url in urls:
                file_path = url.toLocalFile()
                
                if not file_path or not os.path.exists(file_path):
                    continue
                    
                if os.path.isdir(file_path):
                    # Directory: process recursively
                    self._process_dropped_directory(file_path, target_item)
                else:
                    # File: add directly
                    self._add_file_to_tree(file_path, target_item)
            
            # Auto-save the structure if this is associated with a template
            self._auto_save_structure_after_drop()
                    
            event.acceptProposedAction()
        else:
            # Internal drop
            QTreeWidget.dropEvent(self.structure_tree, event)
            
            # Auto-save after internal drop too
            self._auto_save_structure_after_drop()
    
    def _auto_save_structure_after_drop(self):
        """Auto-save the structure after a drop event"""
        try:
            # Get the template name from the name input
            if hasattr(self, 'name_input') and self.app:
                template_name = self.name_input.text().strip()
                if template_name:
                    structure_name = f"Template_{template_name}"
                    
                    # Get the structure from the tree
                    structure = self._get_structure_from_tree()
                    
                    # Debug
                    print(f"DEBUG: Auto-saving structure after drop: {structure_name}")
                    
                    # Save it
                    if hasattr(self.app, 'template_manager'):
                        self.app.template_manager.save_custom_structure(structure_name, structure)
        except Exception as e:
            print(f"DEBUG: Error auto-saving structure after drop: {e}")

    def _process_dropped_directory(self, dir_path, parent_item):
        """Process a dropped directory and all its contents recursively"""
        dir_name = os.path.basename(dir_path)
        
        # Create directory item
        dir_item = QTreeWidgetItem(parent_item)
        dir_item.setText(0, dir_name)
        dir_item.setText(1, "Directory")
        dir_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        
        # Process all files and subdirectories
        for item_name in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item_name)
            
            if os.path.isdir(item_path):
                # Recursively process subdirectory
                self._process_dropped_directory(item_path, dir_item)
            else:
                # Add file
                self._add_file_to_tree(item_path, dir_item)
                
        # Expand the new directory item
        dir_item.setExpanded(True)

    def _add_file_to_tree(self, file_path, parent_item):
        """Add a file to the structure tree"""
        file_name = os.path.basename(file_path)
        
        # Create a file item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, file_name)
        file_item.setText(1, "File")
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        
        # Store original path as data
        file_item.setData(0, Qt.UserRole, file_path)
        
    def _create_files_tab(self):
        """Create the files tab"""
        files_tab = QWidget()
        self.tabs.addTab(files_tab, "Files")
        
        # Layout for this tab
        layout = QVBoxLayout(files_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # File list with explanation
        layout.addWidget(QLabel("Template Files:"))
        
        # Explanation text
        explanation = QLabel("This tab allows you to edit the content of text files in your template. "
                          "Files will be automatically populated when you add them to the structure.")
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(explanation)
        
        # Create split view for files
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)  # 1 = stretch factor
        
        # File list on the left
        file_list_widget = QWidget()
        file_list_layout = QVBoxLayout(file_list_widget)
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.files_list = QListWidget()
        self.files_list.itemSelectionChanged.connect(self._on_file_selected)
        file_list_layout.addWidget(self.files_list)
        
        # Buttons for file list
        buttons_layout = QHBoxLayout()
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_file_to_template)
        buttons_layout.addWidget(add_file_btn)
        
        remove_file_btn = QPushButton("Remove")
        remove_file_btn.clicked.connect(self._remove_file_from_template)
        buttons_layout.addWidget(remove_file_btn)
        
        file_list_layout.addLayout(buttons_layout)
        
        # Add list to splitter
        splitter.addWidget(file_list_widget)
        
        # Editor on the right
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        editor_layout.addWidget(QLabel("File Content:"))
        
        self.file_editor = QTextEdit()
        self.file_editor.setPlaceholderText("Select a file to edit its content")
        editor_layout.addWidget(self.file_editor)
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_file_content)
        editor_layout.addWidget(save_btn)
        
        # Add editor to splitter
        splitter.addWidget(editor_widget)
        
        # Set initial sizes
        splitter.setSizes([200, 400])
        
        # If template path exists, populate the file list
        if self.template_path and os.path.isdir(self.template_path):
            self._populate_file_list()
            
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
                    # It's a directory
                    tree_item.setText(1, "Directory")
                    tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    tree_item.setExpanded(True)
                    # Recursively add children
                    self._populate_tree_from_directory(tree_item, item_path)
                else:
                    # It's a file
                    tree_item.setText(1, "File")
                    tree_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        except Exception as e:
            print(f"Error populating tree: {e}")
            
    def _populate_file_list(self):
        """Populate the file list with text files from the template directory"""
        self.files_list.clear()
        
        # Skip template.json
        skip_files = ["template.json"]
        
        try:
            for root, dirs, files in os.walk(self.template_path):
                for file in sorted(files):
                    if file in skip_files:
                        continue
                        
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.template_path)
                    
                    # Only add text files
                    if self._is_text_file(file_path):
                        self.files_list.addItem(rel_path)
        except Exception as e:
            print(f"Error populating file list: {e}")
            
    def _is_text_file(self, file_path):
        """Check if a file is a text file that can be edited"""
        # Common text file extensions
        text_extensions = ['.txt', '.html', '.css', '.js', '.json', '.md', '.xml', '.csv', 
                         '.py', '.c', '.cpp', '.h', '.java', '.php', '.sh', '.bat', '.ini']
                         
        # Check extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() in text_extensions:
            return True
            
        # For files without recognized extension, try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read as text
                return True
        except UnicodeDecodeError:
            return False  # Binary file
        except Exception:
            return False  # Other error
            
    def _on_file_selected(self):
        """Handle selection change in the file list"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            self.file_editor.clear()
            self.selected_file = None
            return
            
        file_rel_path = selected_items[0].text()
        if not file_rel_path or not self.template_path:
            return
            
        # Get full path
        file_path = os.path.join(self.template_path, file_rel_path)
        self.selected_file = file_path
        
        # Load file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self.file_editor.setPlainText(content)
        except Exception as e:
            self.file_editor.setPlainText(f"Error loading file: {str(e)}")
            
    def _save_file_content(self):
        """Save the content of the currently selected file"""
        if not self.selected_file or not os.path.exists(self.selected_file):
            QMessageBox.warning(self, "Error", "No file selected")
            return
            
        try:
            with open(self.selected_file, 'w', encoding='utf-8') as f:
                f.write(self.file_editor.toPlainText())
            QMessageBox.information(self, "Success", "File saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
            
    def _add_folder(self):
        """Add a new folder to the structure"""
        folder_name, ok = QInputDialog.getText(self, "Add Folder", "Folder Name:")
        if not ok or not folder_name:
            return
            
        # Get the selected item or use root
        selected_items = self.structure_tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.structure_tree.topLevelItem(0)
        
        # If the selected item is a file, use its parent
        if parent_item and parent_item.text(1) != "Directory":
            parent_item = parent_item.parent()
            
        # If still no parent, use root
        if not parent_item and self.structure_tree.topLevelItemCount() > 0:
            parent_item = self.structure_tree.topLevelItem(0)
            
        # Create the folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, folder_name)
        folder_item.setText(1, "Directory")
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        
        # Expand the parent
        if parent_item:
            parent_item.setExpanded(True)
            
    def _add_file(self):
        """Add a new file to the structure"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Get the selected item or use root
        selected_items = self.structure_tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.structure_tree.topLevelItem(0)
        
        # If the selected item is a file, use its parent
        if parent_item and parent_item.text(1) != "Directory":
            parent_item = parent_item.parent()
            
        # If still no parent, use root
        if not parent_item and self.structure_tree.topLevelItemCount() > 0:
            parent_item = self.structure_tree.topLevelItem(0)
            
        # Add the file to the tree
        self._add_file_to_tree(file_path, parent_item)
        
        # Expand the parent
        if parent_item:
            parent_item.setExpanded(True)
            
    def _remove_item(self):
        """Remove the selected item from the structure tree"""
        selected_items = self.structure_tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        
        # Don't remove the root
        if item == self.structure_tree.topLevelItem(0):
            QMessageBox.warning(self, "Warning", "Cannot remove the root item")
            return
            
        # Confirm removal
        msg = f"Are you sure you want to remove '{item.text(0)}'?"
        if item.text(1) == "Directory" and item.childCount() > 0:
            msg += " This will also remove all its contents."
            
        reply = QMessageBox.question(self, "Confirm Removal", msg, 
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                 
        if reply == QMessageBox.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                # It's a top-level item (but not the root)
                index = self.structure_tree.indexOfTopLevelItem(item)
                self.structure_tree.takeTopLevelItem(index)
                
    def _rename_item(self):
        """Rename the selected item"""
        selected_items = self.structure_tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        
        # Don't rename the root
        if item == self.structure_tree.topLevelItem(0):
            QMessageBox.warning(self, "Warning", "Cannot rename the root item")
            return
            
        # Get new name
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", 
                                        QLineEdit.Normal, old_name)
                                        
        if ok and new_name and new_name != old_name:
            item.setText(0, new_name)
            
    def _add_file_to_template(self):
        """Add a file to the template for editing"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "Text Files (*.txt *.html *.css *.js *.json *.md *.xml *.py *.c *.cpp *.h *.java);;All Files (*)"
        )
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Check if it's a text file
        if not self._is_text_file(file_path):
            QMessageBox.warning(self, "Warning", "Only text files can be added for editing")
            return
            
        # Get the file name
        file_name = os.path.basename(file_path)
        
        # Copy the file to the template directory if needed
        if self.template_path and os.path.isdir(self.template_path):
            try:
                dest_path = os.path.join(self.template_path, file_name)
                shutil.copy2(file_path, dest_path)
                
                # Refresh the file list
                self._populate_file_list()
                
                # Select the new file
                for i in range(self.files_list.count()):
                    if self.files_list.item(i).text() == file_name:
                        self.files_list.setCurrentRow(i)
                        break
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add file: {str(e)}")
                
    def _remove_file_from_template(self):
        """Remove a file from the template"""
        selected_items = self.files_list.selectedItems()
        if not selected_items:
            return
            
        file_rel_path = selected_items[0].text()
        if not file_rel_path or not self.template_path:
            return
            
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                 f"Are you sure you want to remove '{file_rel_path}'?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                 
        if reply == QMessageBox.Yes:
            try:
                file_path = os.path.join(self.template_path, file_rel_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                # Refresh the file list
                self._populate_file_list()
                
                # Clear the editor
                self.file_editor.clear()
                self.selected_file = None
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove file: {str(e)}")
                
    def _get_structure_from_tree(self):
        """Build a structure dictionary from the tree widget"""
        structure = {}
        
        # Get the root item
        if self.structure_tree.topLevelItemCount() == 0:
            return structure
            
        root = self.structure_tree.topLevelItem(0)
        
        # Build the structure dictionary
        self._build_structure_dict(root, structure)
        
        return structure
        
    def _build_structure_dict(self, item, structure_dict):
        """Recursively build a dictionary from the tree item"""
        for i in range(item.childCount()):
            child = item.child(i)
            name = child.text(0)
            is_dir = child.text(1) == "Directory"
            
            if is_dir:
                structure_dict[name] = {}
                if child.childCount() > 0:
                    self._build_structure_dict(child, structure_dict[name])
            else:
                # For files, we still use an empty dict to maintain consistency
                structure_dict[name] = {}
                
    def _save_template(self):
        """Save the template and close the dialog"""
        # Get template info
        name = self.name_input.text().strip()
        category = self.category_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        
        # Validate
        if not name:
            QMessageBox.warning(self, "Error", "Template name is required")
            return
            
        if not category:
            QMessageBox.warning(self, "Error", "Category is required")
            return
            
        if not self.template_path or not os.path.isdir(self.template_path):
            QMessageBox.critical(self, "Error", "No template directory specified")
            return
            
        try:
            # Create template info
            template_info = {
                "name": name,
                "category": category,
                "description": description,
                "type": "directory",
                "created": datetime.datetime.now().isoformat()
            }
            
            # Get the structure
            structure = self._get_structure_from_tree()
            
            # Save structure if we have an app with template manager
            if self.app and hasattr(self.app, 'template_manager'):
                structure_name = f"Template_{name}"
                self.app.template_manager.save_custom_structure(structure_name, structure)
                template_info["structure_name"] = structure_name
                
            # Save template.json
            template_json_path = os.path.join(self.template_path, "template.json")
            with open(template_json_path, 'w') as f:
                json.dump(template_info, f, indent=2)
                
            # Call the callback if provided
            if self.save_callback:
                self.save_callback(self.template_path)
                
            QMessageBox.information(self, "Success", f"Template '{name}' saved successfully")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")

    def _create_buttons(self):
        """Create the dialog buttons"""
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Save button
        save_btn = QPushButton("Save Template")
        save_btn.clicked.connect(self._save_template)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(save_btn)

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

class FlowLayout(QLayout):
    """
    Custom flow layout that automatically wraps widgets to the next line
    when they don't fit in the available width.
    
    This is used for the folder cards to enable responsive wrapping.
    """
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items = []
        
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
            
    def addItem(self, item):
        self._items.append(item)
        
    def count(self):
        return len(self._items)
        
    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None
        
    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None
        
    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))
        
    def hasHeightForWidth(self):
        return True
        
    def heightForWidth(self, width):
        height = self._doLayout(QRect(0, 0, width, 0), True)
        return height
        
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)
        
    def sizeHint(self):
        return self.minimumSize()
        
    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
            
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size
        
    def _doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spacing = self.spacing()
        
        for item in self._items:
            style = item.widget().style() if item.widget() else None
            layoutSpacingX = style.layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal) if style else spacing
            layoutSpacingY = style.layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical) if style else spacing
            
            wid = item.widget()
            spaceX = layoutSpacingX if wid is not None else 0
            spaceY = layoutSpacingY if wid is not None else 0
            
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
                
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
            
        return y + lineHeight - rect.y() 