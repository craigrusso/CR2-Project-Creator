#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import datetime
import json
import subprocess
import re
import platform
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLineEdit, QFrame, QScrollArea,
                            QToolTip, QSizePolicy, QFileDialog, QDialog,
                            QCheckBox, QListWidget, QListWidgetItem,
                            QTextEdit, QTreeWidget, QTreeWidgetItem,
                            QMessageBox, QInputDialog, QGridLayout)
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
        
        # Setup window
        self.setWindowTitle("Template Editor")
        self.resize(700, 550)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # TODO: Implement the template directory editor UI
        # This will include:
        # - Tabs for structure/files/placeholders
        # - Template name and description fields
        # - Folder structure editor
        # - File content editor
        # - Placeholder editor
        
        # For now, just add a placeholder message
        placeholder = QLabel("Template Directory Editor - To Be Implemented")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet(f"color: {colors['text']}; font-size: 18px;")
        self.layout.addWidget(placeholder)
        
        # Add buttons
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
    
    def save_template(self):
        """Save the template and close the dialog"""
        if self.save_callback:
            self.save_callback(self.template_path)
        self.accept()

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