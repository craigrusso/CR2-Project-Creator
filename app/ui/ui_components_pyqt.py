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
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLineEdit, QFrame, QScrollArea,
                            QToolTip, QSizePolicy, QFileDialog, QDialog,
                            QCheckBox, QListWidget, QListWidgetItem,
                            QTextEdit, QTreeWidget, QTreeWidgetItem,
                            QMessageBox, QInputDialog, QGridLayout, QTabWidget,
                            QApplication, QStyle, QMainWindow, QGroupBox,
                            QRadioButton, QComboBox, QProgressBar, QSplitter,
                            QMenu, QListView, QStyledItemDelegate,
                            QStyleOptionViewItem, QAbstractItemView, QSpacerItem,
                            QDateEdit, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, pyqtSignal, QEvent, QUrl, QMimeData, QDate
from PyQt6.QtGui import QFont, QCursor, QIcon, QColor, QPalette, QDragEnterEvent, QDropEvent, QPixmap, QPainter, QPen, QFontMetrics, QStandardItemModel, QStandardItem, QDesktopServices, QAction

from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, LINEEDIT_STYLE, LABEL_STYLE
from app.ui.tree_styling import apply_tree_styling, setup_tree_for_structure_editing
from app.utils.utils import normalize_path_for_storage
from app.constants import get_resource_path, APP_NAME, APP_VERSION_NUMBER

# Constants for styling
BLUE_HIGHLIGHT = "#3066BE"
GRAY_BG = "#2F2F2F"

# Get suitable system font for different platforms
def get_system_font():
    """Return an appropriate system font based on platform"""
    system = platform.system()
    if system == "Windows":
        return "Segoe UI, Arial, sans-serif"
    elif system == "Darwin":  # macOS
        return "Helvetica"
    else:  # Linux and others
        return "Ubuntu, DejaVu Sans, Liberation Sans, Arial, sans-serif"

# System font to use throughout the app
UI_FONT = get_system_font()

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
            title_label.setFont(QFont(UI_FONT, 12, QFont.Weight.Bold))
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
            self.label.setFont(QFont(UI_FONT, 10))
            self.label.setStyleSheet(LABEL_STYLE)
            self.layout.addWidget(self.label)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search terms...")
        # Updated style to remove borders for a cleaner look
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: none;
                padding: 5px;
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                background-color: {colors['hover_bg']};
            }}
        """)
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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
            self.icon_label.setFont(QFont(UI_FONT, 24))
            self.icon_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
            
            self.title_label = QLabel(self.template_name)
            self.title_label.setFont(QFont(UI_FONT, 10, QFont.Weight.Bold))
            self.title_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
            self.title_label.setWordWrap(True)
            
            # Simple template label 
            self.template_label = QLabel("Template")
            self.template_label.setFont(QFont(UI_FONT, 9))
            self.template_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
            self.template_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
            
            # Path label (truncated if too long)
            display_path = template_path
            if len(display_path) > 40:
                display_path = "..." + display_path[-40:]
            
            self.path_label = QLabel(display_path)
            self.path_label.setFont(QFont(UI_FONT, 8))
            self.path_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignCenter)
            self.path_label.setWordWrap(True)
            
            # Empty widget for bottom space
            empty = QWidget()
            empty.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
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
                self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self.remove_btn.clicked.connect(lambda: self.remove_callback(self.template_path))
                self.remove_btn.setToolTip("Remove from recent templates")
                
                # Place in top-right corner
                self.grid.addWidget(self.remove_btn, 0, 0, 1, 1, Qt.AlignmentFlagFlagFlagFlagFlag.AlignRight | Qt.AlignmentFlagFlagFlagFlagFlag.AlignTop)
                
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
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
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
    A dialog for editing a folder and file structure.
    """
    def __init__(self, parent=None, structure=None, save_callback=None, title="Edit Structure", app=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self.app = app
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Structure"])
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.layout.addWidget(self.tree)
        
        # Connect drag and drop events
        self.tree.dragEnterEvent = self._tree_dragEnterEvent
        self.tree.dragMoveEvent = self._tree_dragMoveEvent
        self.tree.dropEvent = self._tree_dropEvent

        # Setup tree for structure editing (icons, context menus, etc.)
        setup_tree_for_structure_editing(self.tree, self)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.clicked.connect(self._add_folder)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_folder)
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self._rename_folder)
        self.import_button = QPushButton("Import from Folder")
        self.import_button.clicked.connect(self._import_from_folder)
        
        button_layout.addWidget(self.add_folder_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.rename_button)
        button_layout.addWidget(self.import_button)
        self.layout.addLayout(button_layout)
        
        # Save and Cancel buttons
        save_cancel_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_structure)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        save_cancel_layout.addStretch(1)
        save_cancel_layout.addWidget(self.save_button)
        save_cancel_layout.addWidget(self.cancel_button)
        self.layout.addLayout(save_cancel_layout)
        
        # Set initial structure
        self.structure = structure or []
        self.save_callback = save_callback
        
        # Populate tree with initial structure
        self._populate_tree()

    def _populate_tree(self):
        """Populate the tree widget with the structure"""
        self.tree.clear()
        self._add_tree_items(self.tree, self.structure)
        self.tree.expandAll()

    def _add_tree_items(self, parent_item, structure_dict):
        """Recursively add items to the tree"""
        if isinstance(structure_dict, dict):
            for name, content in structure_dict.items():
                item = QTreeWidgetItem([name])
                parent_item.addChild(item)
                if isinstance(content, dict):
                    # Folder
                    item.setIcon(0, QIcon(get_resource_path("icons/folder.png")))
                    self._add_tree_items(item, content)
                else:
                    # File
                    item.setIcon(0, QIcon(get_resource_path("icons/file.png")))
        elif isinstance(structure_dict, list): # New format
             for item_data in structure_dict:
                name = item_data.get("name", "Unnamed")
                item = QTreeWidgetItem([name])
                if isinstance(parent_item, QTreeWidget):
                    parent_item.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                
                item.setData(0, Qt.ItemDataRole.UserRole, item_data)

                if item_data.get("type") == "folder":
                    item.setIcon(0, QIcon(get_resource_path("icons/folder.png")))
                    if "children" in item_data:
                        self._add_tree_items(item, item_data["children"])
                else:
                    item.setIcon(0, QIcon(get_resource_path("icons/file.png")))


    def _add_folder(self):
        """Add a new folder to the tree"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.tree.invisibleRootItem()
        
        # Prompt for folder name
        name, ok = QInputDialog.getText(self, "Add Folder", "Enter folder name:")
        if ok and name:
            item = QTreeWidgetItem([name])
            item.setIcon(0, QIcon(get_resource_path("icons/folder.png")))
            item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "name": name})
            if isinstance(parent_item, QTreeWidget):
                 parent_item.addTopLevelItem(item)
            else:
                 parent_item.addChild(item)
            parent_item.setExpanded(True)
            
            # Select the new folder
            self.tree.clearSelection()
            item.setSelected(True)

    def _remove_folder(self):
        """Remove the selected folder"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        if item.parent():
            item.parent().removeChild(item)
        else:
            self.tree.invisibleRootItem().removeChild(item)

    def _rename_folder(self):
        """Rename the selected folder"""
        # Get selected item
        selected_item = self.tree.currentItem()
        if not selected_item:
            return
            
        # Prompt for new name
        old_name = selected_item.text(0)
        new_name, ok = QInputDialog.getText(self, "Rename Folder", "Enter new name:", text=old_name)
        
        if ok and new_name:
            selected_item.setText(0, new_name)

    def _get_structure_from_tree(self):
        """Get the structure from the tree widget"""
        structure = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            # This is where the recursive building starts
            self._build_structure_from_item(item, structure)
        return structure

    def _build_structure_from_item(self, item, parent_list):
        """Recursively build structure from tree items"""
        data = self._build_structure_dict(item)
        parent_list.append(data)

    def _build_structure_dict(self, item):
        """Build a dictionary for a single item"""
        item_text = item.text(0)
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}

        # Start with the basic info
        structure_dict = {
            'name': item_text
        }

        # Selectively copy data from item_data
        if isinstance(item_data, dict):
            # Keys relevant for both files and folders
            for key in ['pattern', 'uses_custom_pattern', 'rename_flag',
                        'date_format_text', 'time_format_text',
                        'separator', 'separator_type', 'custom_separator',
                        'custom_options', 'uses_project_name']:
                if key in item_data:
                    structure_dict[key] = item_data[key]

        if item.childCount() > 0:
            structure_dict['type'] = 'folder'
            
            # Folder-specific keys
            if isinstance(item_data, dict):
                for key in ['sequence']:
                    if key in item_data:
                        structure_dict[key] = item_data[key]

            children = []
            for i in range(item.childCount()):
                child = item.child(i)
                children.append(self._build_structure_dict(child))
            structure_dict['children'] = children
        else:
            structure_dict['type'] = 'file'
            # File-specific keys
            if isinstance(item_data, dict):
                for key in ['original_path', 'cache_path', 'is_binary', 'content']:
                    if key in item_data:
                        structure_dict[key] = item_data[key]
            
        return structure_dict

    def save_structure(self):
        """Save the structure and close the dialog"""
        # Get structure from tree
        structure = self._get_structure_from_tree()
        
        if self.save_callback:
            self.save_callback(structure)
        
        self.structure = structure
        self.accept()

    def _tree_dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(QTreeWidget, self.tree).dragEnterEvent(event)

    def _tree_dragMoveEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(QTreeWidget, self.tree).dragMoveEvent(event)

    def _tree_dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            # Get the position of the drop
            pos = event.position().toPoint()
            
            # Get the item at the drop position
            parent_item = self.tree.itemAt(pos)
            
            # If dropped on empty space, use the root as parent
            if not parent_item:
                parent_item = self.tree.invisibleRootItem()
            
            # If dropped on a file, use its parent
            if parent_item and parent_item.childCount() == 0 and parent_item.parent():
                parent_item = parent_item.parent()

            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self._process_dropped_directory(path, parent_item)
                else: # It's a file
                    item = QTreeWidgetItem([os.path.basename(path)])
                    item.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "source_path": path})
                    parent_item.addChild(item)
                    parent_item.setExpanded(True)
            event.acceptProposedAction()
        else:
            # Let the default QTreeWidget handle internal moves
             super(QTreeWidget, self.tree).dropEvent(event)

    def _process_dropped_directory(self, dir_path, parent_item):
        """Recursively process a dropped directory"""
        dir_name = os.path.basename(dir_path)
        
        # Create a top-level item for the directory
        dir_item = QTreeWidgetItem([dir_name])
        dir_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder"})
        
        # Add to the parent item
        if parent_item == self.tree.invisibleRootItem():
            self.tree.addTopLevelItem(dir_item)
        else:
            parent_item.addChild(dir_item)
        
        # Recursively add contents
        try:
            for entry in os.scandir(dir_path):
                if entry.is_dir():
                    self._process_dropped_directory(entry.path, dir_item)
                elif entry.is_file():
                    file_item = QTreeWidgetItem([entry.name])
                    file_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "source_path": entry.path})
                    dir_item.addChild(file_item)
        except OSError as e:
            QMessageBox.warning(self, "Error Reading Directory", f"Could not read directory:\n{dir_path}\n\nError: {e}")

        dir_item.setExpanded(True)

    def _get_relative_item_path(self, item):
        """Get the path of an item relative to the root of the structure."""
        path_parts = []
        current = item
        while current:
            path_parts.insert(0, current.text(0))
            current = current.parent()
        
        # Find the top-level item this item belongs to
        top_level_item = item
        while top_level_item.parent():
            top_level_item = top_level_item.parent()
            
        # Get root directory path from top-level item's data if it exists
        root_data = top_level_item.data(0, Qt.ItemDataRole.UserRole)
        root_dir = ""
        if isinstance(root_data, dict) and "source_path" in root_data:
            root_dir = os.path.dirname(root_data["source_path"])
        
        relative_path = os.path.join(*path_parts)
        return os.path.join(root_dir, relative_path) if root_dir else relative_path

    def _import_from_folder(self):
        """Import structure from a folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Import")
        if folder_path:
            self._process_dropped_directory(folder_path, self.tree.invisibleRootItem())
            self.tree.expandAll()

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
        structure_widget = QWidget()
        structure_layout = QVBoxLayout(structure_widget)
        structure_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create buttons for adding files and folders
        button_layout = QHBoxLayout()
        
        add_folder_button = QPushButton("Add Folder")
        add_folder_button.clicked.connect(self._add_folder)
        button_layout.addWidget(add_folder_button)
        
        add_file_button = QPushButton("Add File")
        add_file_button.clicked.connect(self._add_file)
        button_layout.addWidget(add_file_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self._remove_selected)
        button_layout.addWidget(remove_button)
        
        button_layout.addStretch()
        structure_layout.addLayout(button_layout)
        
        # Create tree widget for template structure
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels(["Name"])
        self.structure_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        
        # Set object name for debugging
        self.structure_tree.setObjectName("TemplateDirectoryStructureTree")
        
        # Apply centralized styling to ensure consistent appearance and no blue borders
        setup_tree_for_structure_editing(self.structure_tree)
        
        # Add a root item for the project
        root_item = QTreeWidgetItem(self.structure_tree)
        root_item.setText(0, self.template_path or "Template Root")
        root_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        root_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder"})
        root_item.setFlags(root_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Make root editable
        
        # Expand root by default
        self.structure_tree.expandItem(root_item)
        
        # Connect item changed signal to handler
        self.structure_tree.itemChanged.connect(self._handle_item_changed)
        
        structure_layout.addWidget(self.structure_tree)
        self.tabs.addTab(structure_widget, "Structure")
    
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
        """Check if a file is a text file"""
        # Common text file extensions
        text_extensions = ['.txt', '.html', '.css', '.js', '.py', '.md', '.json', '.xml', '.csv', '.ini', '.cfg']
        
        # Check by extension first
        _, ext = os.path.splitext(file_path)
        if ext.lower() in text_extensions:
            return True
        
        # Try to read the file as text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read a chunk of the file
                chunk = f.read(1024)
                # Check for null bytes (common in binary files)
                if '\0' in chunk:
                    return False
                # Try to decode as UTF-8
                return True
        except:
            # If there's an error reading as text, assume it's binary
            return False
    
    def _add_folder(self):
        # Get the currently selected item as the parent
        selected_items = self.structure_tree.selectedItems()
        if selected_items:
            parent_item = selected_items[0]
            # Only allow adding folders to other folders
            if parent_item.data(0, Qt.ItemDataRole.UserRole) and parent_item.data(0, Qt.ItemDataRole.UserRole).get("type") != "folder":
                QMessageBox.warning(self, "Invalid Selection", "You can only add folders to other folders.")
                return
        else:
            # If nothing is selected, use the root item
            parent_item = self.structure_tree.topLevelItem(0)
        
        # Use input dialog to get folder name
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not folder_name:
            return
        
        # Create new folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, folder_name)
        
        # Set proper folder icon immediately
        try:
            from app.ui.icon_utilities import get_folder_icon
            folder_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
        except ImportError:
            # Fallback to standard icon
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        
        folder_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder"})
        folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Make folder editable
        
        # Force immediate icon refresh to ensure proper system folder icon
        try:
            from app.ui.tree_styling import update_item_icon
            update_item_icon(folder_item)
        except ImportError:
            pass
        
        # Expand the parent to show the new folder
        parent_item.setExpanded(True)
        
        # Select the new folder
        self.structure_tree.clearSelection()
        folder_item.setSelected(True)
    
    def _add_file(self):
        # Create file dialog to select file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*);;Text Files (*.txt);;Python Files (*.py);;HTML Files (*.html);;CSS Files (*.css);;JavaScript Files (*.js)"
        )
        
        if not file_path:
            return
        
        # Get the file name from the path
        file_name = os.path.basename(file_path)
        
        # Create a suggested name with {{PROJECT_NAME}} placeholder
        # if the file name contains the word "project" or similar
        suggested_name = file_name
        if "project" in file_name.lower():
            base, ext = os.path.splitext(file_name)
            suggested_name = "{{PROJECT_NAME}}" + ext
        
        # Ask user for the file name to use in the template
        template_file_name, ok = QInputDialog.getText(
            self,
            "Template File Name",
            "Name for this file in the template:",
            text=suggested_name
        )
        
        if not ok or not template_file_name:
            return
        
        # Get the selected target directory in our structure
        selected_items = self.structure_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            
            # If selected item is a file, use its parent
            if selected_item.data(0, Qt.ItemDataRole.UserRole) and selected_item.data(0, Qt.ItemDataRole.UserRole).get("type") != "folder":
                parent_item = selected_item.parent()
            else:
                parent_item = selected_item
        else:
            # If nothing is selected, use the root item
            parent_item = self.structure_tree.topLevelItem(0)
        
        # Create new file item
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, template_file_name)
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        file_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "source_path": file_path})
        file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Make file editable
        
        # Expand the parent to show the new file
        parent_item.setExpanded(True)
        
        # If template directory exists, we can immediately copy the file
        if self.template_path and os.path.isdir(self.template_path):
            target_path = self._get_item_path(file_item)
            
            # Create parent directories if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Copy the file, replacing placeholders if it's a text file
            try:
                if self._is_text_file(file_path):
                    self._replace_placeholders(file_path, target_path)
                else:
                    # Use C++ engine for file copy
                    try:
                        from app.utils.cpp_enhanced_copy import copy_file
                        stats = copy_file(file_path, target_path)
                        if stats.copied_files == 0:
                            raise RuntimeError("C++ copy engine failed to copy file")
                    except ImportError:
                        raise RuntimeError("C++ copy engine not available - this is the only engine")
            except Exception as e:
                QMessageBox.warning(self, "Error Copying File", f"Could not copy file: {str(e)}")
    
    def _remove_selected(self):
        """Remove selected item from the structure tree"""
        selected_items = self.structure_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            if item != self.structure_tree.topLevelItem(0):  # Don't remove the root
                parent = item.parent() or self.structure_tree.invisibleRootItem()
                parent.removeChild(item)
    
    def _handle_item_changed(self, item, column):
        """Handle item change in the structure tree"""
        if column == 0:
            new_text = item.text(0)
            if new_text:
                # Update the structure dictionary
                self._update_structure_from_tree()
            else:
                # If the item is empty, remove it from the structure
                self._remove_selected()
    
    def _update_structure_from_tree(self):
        """Update the structure dictionary from the tree"""
        structure = {}
        self._build_structure_from_tree(self.structure_tree.topLevelItem(0), structure)
        self.structure = structure
    
    def _replace_placeholders(self, source_path, target_path):
        """Replace placeholders in text files"""
        try:
            if not self._is_text_file(source_path):
                return
            
            # Read the file content
            with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Replace placeholders with their template versions
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            current_year = datetime.datetime.now().strftime("%Y")
            
            # Replace direct project name references with the placeholder
            content = content.replace("{{DATE}}", current_date)
            content = content.replace("{{YEAR}}", current_year)
            
            # Write back the content
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error replacing placeholders in {source_path}: {e}")
    
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
    
    def save_template(self):
        """Save the template and close the dialog"""
        print("\n[DEBUG] TemplateDirectoryEditor.save_template: Starting save operation")
        
        # Validate basic info
        name = self.name_input.text().strip()
        category = self.category_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        
        print(f"[DEBUG] Template info - name: {name}, category: {category}")
        
        # Handle empty template name
        if not name:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"UNTITLED_{timestamp}"
            # Inform user about auto-generated name
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Auto-generated Name", 
                              f"No template name was provided. Your template will be saved as '{name}'.\n\n"
                              "You can rename it later from the template gallery.")
            # Update the name field with the generated name
            self.name_input.setText(name)
            
        if not category:
            QMessageBox.warning(self, "Validation Error", "Category is required")
            return
        
        # Create structure name
        structure_name = f"Template_{name}"
        print(f"[DEBUG] Structure name: {structure_name}")
        
        # Get structure from tree
        structure = self._get_structure_from_tree()
        print(f"[DEBUG] Structure from tree: {structure}")
        
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
            print(f"[DEBUG] Saving template.json to: {self.template_path}")
            # Save template.json
            template_json_path = os.path.join(self.template_path, "template.json")
            with open(template_json_path, 'w') as f:
                json.dump(self.template_info, f, indent=2)
            print("[DEBUG] template.json saved successfully")
                
            # Also save the structure definition
            parent = self.parent()
            if parent and hasattr(parent, 'template_manager'):
                print(f"[DEBUG] Saving structure via template manager: {structure_name}")
                success = parent.template_manager.save_custom_structure(structure_name, structure)
                print(f"[DEBUG] Structure save result: {success}")
            else:
                print("[WARNING] No template manager found to save structure")
            
            # Call the save callback if provided
            if self.save_callback:
                print("[DEBUG] Calling save callback")
                self.save_callback(self.template_path)
                
            print("[DEBUG] Template save completed successfully")
            self.accept()
            
        except Exception as e:
            print(f"[ERROR] Failed to save template: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")
            return

    def _tree_dragEnterEvent(self, event):
        """Custom drag enter event for the tree widget"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # For internal drag/drop operations
            QTreeWidget.dragEnterEvent(self.structure_tree, event)
            
    def _tree_dragMoveEvent(self, event):
        """Custom drag move event for the tree widget"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # For internal drag/drop operations
            QTreeWidget.dragMoveEvent(self.structure_tree, event)
            
    def _tree_dropEvent(self, event):
        """Custom drop event for the tree widget"""
        if event.mimeData().hasUrls():
            # Get drop position
            drop_item = self.structure_tree.itemAt(event.pos())
            if not drop_item:
                drop_item = self.structure_tree.topLevelItem(0)  # Root item
                
            # Process the dropped URLs
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                
                # Make sure path exists
                if not os.path.exists(file_path):
                    continue
                    
                # If it's a directory, import its structure
                if os.path.isdir(file_path):
                    self._process_dropped_directory(file_path, drop_item)
                    
            # Accept the drop action
            event.acceptProposedAction()
        else:
            # For internal drag/drop operations
            QTreeWidget.dropEvent(self.structure_tree, event)
            
    def _process_dropped_directory(self, dir_path, parent_item):
        """Process a dropped directory and add it to the structure"""
        dir_name = os.path.basename(dir_path)
        
        # Create a folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, dir_name)
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        folder_item.setData(0, Qt.ItemDataRole.UserRole, "folder")  # Mark as folder
        folder_item.setExpanded(True)
        
        # Recursively process subdirectories
        try:
            # First, process folders to keep them at the top
            folders = []
            files = []
            
            # Sort items into folders and files
            for item in sorted(os.listdir(dir_path)):
                # Skip hidden files (starting with '.')
                if item.startswith('.'):
                    continue
                    
                item_full_path = os.path.join(dir_path, item)
                if os.path.isdir(item_full_path):
                    folders.append(item_full_path)
                else:
                    files.append(item_full_path)
            
            # Process folders first
            for folder_path in folders:
                self._process_dropped_directory(folder_path, folder_item)
                
            # Then process files
            for file_path in files:
                file_name = os.path.basename(file_path)
                file_item = QTreeWidgetItem(folder_item)
                file_item.setText(0, file_name)
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                file_item.setData(0, Qt.ItemDataRole.UserRole, "file")  # Mark as file
                
                # Copy the file to the template cache directory
                if self.template_path and os.path.isdir(self.template_path):
                    # Get structure name
                    structure_name = os.path.basename(self.template_path)
                    # Clean up structure name for cache directory
                    safe_name = structure_name.replace(" ", "_").replace("/", "-").replace("\\", "-").replace("'", "")
                    
                    # Determine cache directory path
                    templates_dir = os.path.dirname(os.path.dirname(self.template_path))
                    cache_dir = os.path.join(templates_dir, "cache", safe_name)
                    
                    # Get the relative path from the item in the tree to maintain folder structure
                    relative_path = self._get_relative_item_path(file_item)
                    
                    if relative_path:
                        # Create the full cache path including the relative path
                        cached_file_path = os.path.join(cache_dir, relative_path)
                        # Ensure the directory structure exists
                        os.makedirs(os.path.dirname(cached_file_path), exist_ok=True)
                    else:
                        # No relative path, use direct cache directory
                        os.makedirs(cache_dir, exist_ok=True)
                        cached_file_path = os.path.join(cache_dir, file_name)
                    
                    # Copy file to cache using C++ engine
                    try:
                        print(f"Copying file to cache: {file_path} -> {cached_file_path}")
                        from app.utils.cpp_enhanced_copy import copy_file
                        stats = copy_file(file_path, cached_file_path)
                        if stats.copied_files > 0:
                            print(f"Successfully cached file: {cached_file_path}")
                        else:
                            raise RuntimeError("C++ copy engine failed to copy file")
                    except ImportError:
                        raise RuntimeError("C++ copy engine not available - this is the only engine")
                    except Exception as e:
                        print(f"Error copying file to cache: {e}")
        except Exception as e:
            print(f"Error processing directory contents: {e}")
    
    def _get_relative_item_path(self, item):
        """
        Get the relative path of an item in the tree structure
        
        Args:
            item: The tree item to get the path for
            
        Returns:
            str: The relative path of the item from the project root, or None if not found
        """
        if not item:
            return None
            
        path_parts = []
        current = item
        
        # Find the root item
        root_item = None
        if hasattr(self, 'root_item'):
            root_item = self.root_item
        elif hasattr(self, 'tree') and self.tree.topLevelItemCount() > 0:
            root_item = self.tree.topLevelItem(0)
        elif hasattr(self, 'structure_tree') and self.structure_tree.topLevelItemCount() > 0:
            root_item = self.structure_tree.topLevelItem(0)
            
        # If no root item identified, return None
        if not root_item:
            print("Warning: Could not identify root item in tree")
            return None
            
        # Build the path by walking up the tree
        while current and current != root_item:
            path_parts.insert(0, current.text(0))
            current = current.parent()
            
        # If we reached the top without finding the root, the path is incomplete
        if not current or current != root_item:
            return None
            
        # Combine path parts and normalize
        if path_parts:
            return normalize_path_for_storage(os.path.join(*path_parts))
        else:
            return None

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
            # Copy the file to the template directory using C++ engine
            dest_path = os.path.join(self.template_path, filename)
            try:
                from app.utils.cpp_enhanced_copy import copy_file
                stats = copy_file(file_path, dest_path)
                if stats.copied_files > 0:
                    # Refresh file list
                    self._populate_file_list(self.template_path)
                    # Select the new file
                    for i in range(self.files_list.count()):
                        if self.files_list.item(i).text() == filename:
                            self.files_list.setCurrentRow(i)
                            break
                else:
                    raise RuntimeError("C++ copy engine failed to copy file")
            except ImportError:
                raise RuntimeError("C++ copy engine not available - this is the only engine")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add file: {str(e)}")

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
        header.setFont(QFont(UI_FONT, 16, QFont.Weight.Bold))
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
        try:
            # Strip formatting on paste to keep names readable
            self.text_edit.setAcceptRichText(False)
        except Exception:
            pass
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
        
        self.create_button = QPushButton("Create Project(s)")
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
        
        # Check for a template - either from template_file_path or selected_template
        has_template = False
        
        # Check for selected template from gallery first
        if hasattr(parent, 'selected_template') and parent.selected_template:
            has_template = True
        # Then check for template file path as fallback
        elif hasattr(parent, 'template_file_path') and parent.template_file_path:
            has_template = True
        # Finally check if there's a template gallery with selected template
        elif hasattr(parent, 'template_gallery') and hasattr(parent.template_gallery, 'get_selected_template'):
            try:
                selected_template = parent.template_gallery.get_selected_template()
                if selected_template:
                    has_template = True
            except Exception as e:
                print(f"Error checking gallery template: {e}")
        
        if not has_template:
            missing_requirements.append("No template selected")
        
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
        
        # Show confirmation with count only for larger batches
        if len(project_names) >= 10:
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

# --- Update Notification Banner --- 
class UpdateNotificationBanner(QFrame):
    """A simple banner to notify the user about available updates."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UpdateNotificationBanner")
        self.setFixedHeight(40) # Fixed height for the banner
        self.setStyleSheet(f"""
            #UpdateNotificationBanner {{
                background-color: {colors['highlight_bg']}; /* Use highlight_bg as accent_light isn't defined */
                border-radius: 4px;
                border: 1px solid {colors['accent']};
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 13px;
                padding-left: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)

        self.icon_label = QLabel("✨") # Placeholder icon
        layout.addWidget(self.icon_label)

        self.message_label = QLabel("") # Message will be set dynamically
        layout.addWidget(self.message_label, 1) # Stretch message label

        self.download_button = QPushButton("Download Now")
        self.download_button.setStyleSheet(ACCENT_BUTTON_STYLE) # Use existing accent style
        self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_button.setFixedHeight(28)
        self.download_button.clicked.connect(self._open_download_page)
        layout.addWidget(self.download_button)

        self.close_button = QPushButton("✕") # Close symbol
        self.close_button.setFlat(True)
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet("QPushButton { border: none; font-size: 16px; color: #AAAAAA; } QPushButton:hover { color: #FFFFFF; }")
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.hide)
        layout.addWidget(self.close_button)

        self.hide() # Initially hidden

    def show_message(self, version_string):
        """Sets the message and shows the banner."""
        self.message_label.setText(f"<b>Update Available:</b> Version {version_string} is ready to download.")
        self.show()

    def _open_download_page(self):
        """Opens the download webpage in the default browser."""
        url = QUrl("https://www.cr2creative.com/downloads.html")
        QDesktopServices.openUrl(url) 