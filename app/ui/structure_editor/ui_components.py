#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
UI Components Module for Structure Editor
Handles building and managing UI elements
"""

import os
import json
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu,
    QMessageBox, QTextEdit, QComboBox, QCheckBox, QSplitter, QWidget, 
    QSizePolicy, QGroupBox, QFormLayout, QFrame, QTabWidget, QFileDialog, QInputDialog, QListWidget, QDialog, QApplication, QStyle, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer, QSettings, QObject
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QPainter, QDrag, QDropEvent, QPixmap, QCursor, QStandardItemModel, QStandardItem, QAction

# Import the main application colors
from app.ui.color_scheme_pyqt import APP_COLORS, BUTTON_STYLE, ACCENT_BUTTON_STYLE, CONTEXT_MENU_STYLE

# Colors for UI consistency - using main app colors
colors = APP_COLORS

# Import default categories constant
from app.constants import DEFAULT_TEMPLATE_CATEGORIES, get_resource_path

# Import the centralized updater function
from app.templates.category_combobox_updater import update_single_combobox

# Import folder icon utilities - added for proper Windows folder icons
from app.ui.icon_utilities import get_folder_icon, get_file_icon

import platform

class StructureEditorTree(QTreeWidget):
    """Enhanced QTreeWidget for structure editing with improved styling"""
    
    def __init__(self, parent=None, context_menu_handler=None):
        super().__init__(parent)
        self.context_menu_handler = context_menu_handler
        self.setHeaderLabels(["Name"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setIndentation(20)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        if self.context_menu_handler:
            self.customContextMenuRequested.connect(self.context_menu_handler)
        # self.setAttribute(Qt.WA_MacShowFocusRect, False) # Commented out for Qt6 compatibility
        
        # Import folder icon utilities - added for proper Windows folder icons
        self.get_folder_icon = get_folder_icon  # Store reference to the function
        self.get_file_icon = get_file_icon  # Store reference to the function
        
        # Connect item expanded/collapsed signals to update folder icons
        self.itemExpanded.connect(self._update_folder_icon)
        self.itemCollapsed.connect(self._update_folder_icon)
        
        # Add placeholder text attribute
        self.placeholder_text = "Drop Files and Folders Here"
        self.placeholder_visible = True
        
        # Apply enhanced styling while ensuring branch indicators remain visible
        self.setStyleSheet(f"""
            QTreeWidget {{
                border: 1px solid {colors['border']};
                background-color: white;
                outline: none;
            }}
            
            QTreeWidget::item {{
                border: none !important;
                padding: 5px;
                border-radius: 3px;
                outline: none;
            }}
            
            QTreeWidget::item:hover {{
                background-color: {colors['hover_bg']};
                border: none !important;
            }}
            
            QTreeWidget::item:selected {{
                background-color: {colors['highlight_bg']};
                color: {colors['highlight_text']};
                border: none !important;
            }}
            
            /* Style branch when selected for consistent color */
            QTreeWidget::branch:selected {{
                background-color: {colors['highlight_bg']};
            }}
            
            /* Style branch indicators to ensure they're visible */
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'><path fill='%23666666' d='M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z'/></svg>");
                width: 15px;
                height: 15px;
            }}
            
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'><path fill='%23666666' d='M7 10l5 5 5-5z'/></svg>");
                width: 15px;
                height: 15px;
            }}
            
            QTreeWidget QLineEdit {{
                background-color: white;
                selection-background-color: {colors['highlight_bg']};
                border: 1px solid {colors['accent']};
                border-radius: 3px;
                padding: 1px 2px;
            }}
        """)
        
        # Ensure branch indicators are visible
        self.setRootIsDecorated(True)
        self.setItemsExpandable(True)
        
        # Make all items editable with the right triggers
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked |
                             QAbstractItemView.EditTrigger.EditKeyPressed |
                             QAbstractItemView.EditTrigger.SelectedClicked)
    
    def setPlaceholderText(self, text):
        """Set the placeholder text to display when tree is empty"""
        self.placeholder_text = text
        self.update()
    
    def paintEvent(self, event):
        """Override paint event to draw placeholder text when tree is empty"""
        super().paintEvent(event)
        
        # Check if tree is empty (no root items)
        if self.invisibleRootItem().childCount() == 0 and self.placeholder_text:
            painter = QPainter(self.viewport())
            painter.save()
            
            # Set up font and color for placeholder
            font = painter.font()
            font.setPointSize(14)  # Larger font
            font.setItalic(True)
            painter.setFont(font)
            painter.setPen(QColor(colors.get('secondary_text', '#777777')))
            
            # Calculate text rectangle and draw centered text
            rect = self.viewport().rect()
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.placeholder_text)
            
            painter.restore()

    def _update_folder_icon(self, item):
        """Update folder icon based on item state"""
        # Get the item data to determine its type
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = None
        
        # Extract type information from item data
        if isinstance(item_data, dict) and 'type' in item_data:
            item_type = item_data.get('type')
        
        # If it's explicitly a folder or has children, use folder icon
        if item_type == 'folder' or item.childCount() > 0:
            is_expanded = item.isExpanded()
            item.setIcon(0, self.get_folder_icon(is_expanded))
        else:
            # For files, use the file icon based on filename
            filename = item.text(0)
            item.setIcon(0, self.get_file_icon(filename))
        
        # Also update child items recursively
        for i in range(item.childCount()):
            child = item.child(i)
            self._update_folder_icon(child)

class StructureEditor(QDialog):
    """Dialog for editing project structure"""
    
    structureChanged = pyqtSignal(str, list)  # emitted when structure is saved (name, structure)
    
    def __init__(self, parent=None, structure_name="", structure=None, is_new=False):
        super().__init__(parent)
        
        self.structure_name = structure_name
        self.structure = structure or []
        self.is_new = is_new
        
        # Setup dialog
        self.setWindowTitle("Structure Editor")
        self.resize(800, 600)
        
        # Initialize UI
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        # Structure name section
        name_layout = QHBoxLayout()
        self.layout.addLayout(name_layout)
        
        name_label = QLabel("Structure Name:")
        name_layout.addWidget(name_label)
        
        self.name_input = QInputDialog.getText(
            self, "Structure Name", 
            "Enter name for this structure:", 
            text=self.structure_name
        )
        
        if not self.name_input[1]:  # User cancelled
            self.reject()
            return
            
        self.structure_name = self.name_input[0]
        
        # Structure tree title
        tree_label = QLabel("Structure Tree:")
        tree_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(tree_label)
        
        # Use our enhanced tree widget
        self.tree = StructureEditorTree(self)
        
        # Set a placeholder message for empty tree
        self.tree.setPlaceholderText("Drop Files and Folders Here")
        
        # Add a root item
        self.root_item = QTreeWidgetItem(self.tree)
        self.root_item.setText(0, "Project Root")
        self.root_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        self.root_item.setExpanded(True)
        
        # Populate tree with existing structure if available
        if self.structure:
            self._populate_tree(self.structure, self.root_item)
            
        self.layout.addWidget(self.tree)
        
        # Buttons for manipulating tree
        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        button_layout.addWidget(add_folder_btn)
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_file)
        button_layout.addWidget(add_file_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_item)
        button_layout.addWidget(remove_btn)
        
        import_btn = QPushButton("Import Folder")
        import_btn.clicked.connect(self._import_folder)
        button_layout.addWidget(import_btn)
        
        # Save/Cancel buttons
        action_layout = QHBoxLayout()
        self.layout.addLayout(action_layout)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        action_layout.addWidget(self.cancel_button)
        
        action_layout.addStretch()
        
        self.save_button = QPushButton("Save Structure")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._save_structure)
        action_layout.addWidget(self.save_button)
    
    def _populate_tree(self, structure, parent_item=None):
        """Populate the tree with the structure data"""
        if not structure:
            return

        for item in structure:
            if isinstance(item, dict):
                # Folder with name and children
                folder_item = QTreeWidgetItem(parent_item)
                folder_item.setText(0, item['name'])
                folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Recursively add children
                if 'children' in item:
                    self._populate_tree(item['children'], folder_item)
            elif isinstance(item, str):
                # File item
                file_item = QTreeWidgetItem(parent_item)
                file_item.setText(0, item)
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)
            else:
                # Dictionary with folder name as key
                for folder_name, children in item.items():
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, folder_name)
                    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    
                    # Recursively add children
                    if isinstance(children, list):
                        self._populate_tree(children, folder_item)
    
    def _add_folder(self):
        """Add a new folder to the selected item"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.root_item
        
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        
        if ok and folder_name:
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, folder_name)
            
            # Set folder data
            folder_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "name": folder_name})
            
            # Set proper folder icon immediately
            try:
                from app.ui.icon_utilities import get_folder_icon
                folder_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
            except ImportError:
                # Fallback to standard icon
                folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            
            folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Force immediate icon refresh to ensure proper system folder icon
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(folder_item)
            except ImportError:
                pass
            
            parent_item.setExpanded(True)
    
    def _add_file(self):
        """Add a new file to the selected item"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.root_item
        
        file_name, ok = QInputDialog.getText(self, "New File", "File name:")
        
        if ok and file_name:
            file_item = QTreeWidgetItem(parent_item)
            file_item.setText(0, file_name)
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)
            parent_item.setExpanded(True)
    
    def _remove_item(self):
        """Remove the selected item(s)"""
        selected_items = self.tree.selectedItems()
        
        if not selected_items:
            return
            
        for item in selected_items:
            if item == self.root_item:
                QMessageBox.warning(self, "Cannot Remove", "The root item cannot be removed")
                continue
                
            parent = item.parent() or self.tree.invisibleRootItem()
            parent.removeChild(item)
    
    def _import_folder(self):
        """Import structure from a filesystem folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Folder to Import", "", QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:
            return
            
        # Get the target parent item
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.root_item
        
        # Import the folder structure
        self._import_folder_structure(folder_path, parent_item)
    
    def _import_folder_structure(self, folder_path, parent_item):
        """Import a folder structure recursively"""
        folder_name = os.path.basename(folder_path)
        
        # Create folder item
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, folder_name)
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        try:
            # Get all items in the folder
            items = os.listdir(folder_path)
            
            # Process directories first
            for item in sorted(items):
                if item.startswith('.'):  # Skip hidden items
                    continue
                    
                item_path = os.path.join(folder_path, item)
                
                if os.path.isdir(item_path):
                    # Recursive call for subdirectories
                    self._import_folder_structure(item_path, folder_item)
                else:
                    # Add file
                    file_item = QTreeWidgetItem(folder_item)
                    file_item.setText(0, item)
                    file_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                    file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Expand the folder
            folder_item.setExpanded(True)
            
        except Exception as e:
            print(f"Error importing folder structure: {e}")
    
    def _build_structure(self, item):
        """Build the structure data from the tree item"""
        result = []
        
        for i in range(item.childCount()):
            child = item.child(i)
            
            if child.childCount() > 0:
                # It's a folder with children
                folder_dict = {child.text(0): []}
                self._build_structure(child, folder_dict[child.text(0)])
                result.append(folder_dict)
            elif QIcon.hasThemeIcon(child.icon(0).name()):
                # It's a folder (has folder icon)
                result.append({child.text(0): []})
            else:
                # It's a file
                result.append(child.text(0))
        
        return result
    
    def _build_structure(self, parent_item, result=None):
        """
        Build structure data recursively
        
        Args:
            parent_item: The parent item to process
            result: The result list to add items to
            
        Returns:
            The structure as a list
        """
        if result is None:
            result = []
            
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            
            # Check if it has a folder icon
            is_folder = child.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon).cacheKey()
            
            if is_folder:
                if child.childCount() > 0:
                    # Folder with children
                    folder_dict = {child.text(0): []}
                    self._build_structure(child, folder_dict[child.text(0)])
                    result.append(folder_dict)
                else:
                    # Empty folder
                    result.append({child.text(0): []})
            else:
                # File
                result.append(child.text(0))
                
        return result
    
    def _save_structure(self):
        """Save the structure and close the dialog"""
        if not self.structure_name:
            self.structure_name, ok = QInputDialog.getText(
                self, "Structure Name", "Enter name for this structure:"
            )
            
            if not ok or not self.structure_name:
                return
        
        # Build structure from tree
        structure = self._build_structure(self.root_item)
        
        # Force icon refresh before saving to ensure all icons are properly displayed
        if hasattr(self, 'drag_drop_handler') and self.drag_drop_handler:
            self.drag_drop_handler.refresh_icons()
            
        # Emit signal with name and structure
        self.structureChanged.emit(self.structure_name, structure)
        
        # Accept and close
        self.accept()

class UIBuilder(QObject):
    """
    Builds and manages the UI for the Enhanced Structure Editor
    """
    
    # Define a signal to request opening the category manager
    manage_categories_requested = pyqtSignal()
    
    def __init__(self, editor, structure_name=None):
        """
        Initialize the UI builder
        
        Args:
            editor: The parent editor instance
            structure_name: Optional name of the structure (for template name field)
        """
        super().__init__() # Call QObject constructor
        self.editor = editor
        self.structure_name = structure_name
        self.tree = None
        self.template_name_field = None
        self.template_category_field = None
        self.template_info_field = None
        self.search_field = None
        
        # Get template manager from editor's app reference
        self.template_manager = None
        if hasattr(self.editor, 'app') and hasattr(self.editor.app, 'template_manager'):
            self.template_manager = self.editor.app.template_manager
        else:
            # Fallback if app or manager isn't directly accessible (should not happen in normal flow)
            print("Warning: UIBuilder could not access template_manager via editor.app")
            # Attempt to create a standalone instance (may lack full context)
            try:
                from app.templates.template_manager import TemplateManager
                self.template_manager = TemplateManager()
            except ImportError:
                 print("Critical Error: Cannot import TemplateManager in UIBuilder")
                 # Handle error appropriately, maybe raise exception or disable category features
                 # For now, use a default list
                 self.categories = ["Custom"]
                 
        # Fetch categories from template manager if available
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
             self.categories = self.template_manager.get_categories()
             print(f"UIBuilder: Retrieved {len(self.categories)} categories from template_manager")
        else:
             print("UIBuilder: Using default category list as template_manager was not found or lacked get_categories")
             self.categories = ["Custom"]
             
        # Initialize QSettings to check for hide defaults
        self.settings = QSettings()
        
        # Filter categories based on setting BEFORE populating dropdown
        self.categories_to_display = self.categories[:]
        hide_defaults = self.settings.value("CategoryManager/hideDefaultCategories", False, type=bool)
        if hide_defaults:
            self.categories_to_display = [cat for cat in self.categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
            print(f"UIBuilder: Hiding defaults, categories to display: {self.categories_to_display}")
        else:
            print(f"UIBuilder: Not hiding defaults, categories to display: {self.categories_to_display}")

        print(f"UIBuilder: Initialized with {len(self.categories)} categories: {self.categories}")
        
        self.init_ui()
    
    def init_ui(self):
        """
        Initialize the complete user interface
        
        Returns:
            QLayout: The main layout
        """
        # Layouts
        main_layout = QVBoxLayout()
        top_section_layout = QHBoxLayout()
        # Use QFormLayout for the top form fields
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setContentsMargins(5, 5, 5, 5)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(10)

        buttons_layout = QVBoxLayout()
        structure_section_layout = QVBoxLayout()

        # --- Name Field ---
        self.template_name_field = QLineEdit()
        self.template_name_field.setPlaceholderText("Enter template name...")
        
        # Set initial template name if available from the editor
        template_name = None
        
        # Try to get the template name from different sources in the editor
        if hasattr(self.editor, '_template_name') and self.editor._template_name:
            template_name = self.editor._template_name
            print(f"DEBUG (UIBuilder): Found template name in editor._template_name: '{template_name}'")
        elif hasattr(self.editor, 'template_name') and self.editor.template_name:
            template_name = self.editor.template_name
            print(f"DEBUG (UIBuilder): Found template name in editor.template_name: '{template_name}'")
        elif hasattr(self.editor, 'get_template_name') and callable(self.editor.get_template_name):
            template_name = self.editor.get_template_name()
            print(f"DEBUG (UIBuilder): Retrieved template name from editor.get_template_name(): '{template_name}'")
        elif hasattr(self.editor, 'structure_name') and self.editor.structure_name:
            if self.editor.structure_name.startswith("Template_"):
                template_name = self.editor.structure_name[len("Template_"):]
                print(f"DEBUG (UIBuilder): Derived template name from editor.structure_name: '{template_name}'")
        
        # Set the template name field if we found a valid name
        if template_name:
            print(f"DEBUG (UIBuilder): Setting template name field to: '{template_name}'")
            self.template_name_field.setText(template_name)
        else:
            print("DEBUG (UIBuilder): No template name found, leaving field empty")
        
        name_label = QLabel("Template Name:")
        name_label.setStyleSheet("border: none; padding: 5px 0px; background-color: transparent;")
        form_layout.addRow(name_label, self.template_name_field)

        # --- Category Field ---
        self.template_category_field = QComboBox()
        self.template_category_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.template_category_field.setEditable(False) # Typically non-editable
        self.template_category_field.setObjectName("template_category_combo_box")

        # Call the refactored _init_category_dropdown to populate the combo box
        self._init_category_dropdown()
        # --- End Category Dropdown Population ---

        # Manage Categories Button
        self.manage_categories_btn = QPushButton("Manage")
        self.manage_categories_btn.setToolTip("Add, remove, or manage template categories")
        # Apply the action button style directly when creating the button
        self.manage_categories_btn.setStyleSheet(self._get_button_style('action'))
        # Connect button click to emit the new signal
        self.manage_categories_btn.clicked.connect(self.manage_categories_requested.emit)
        # Add horizontal layout for category dropdown and manage button
        category_layout = QHBoxLayout()
        category_layout.addWidget(self.template_category_field, 1) # Allow dropdown to expand
        category_layout.addWidget(self.manage_categories_btn)
        category_layout.setSpacing(5) # Reduce spacing between combo and button
        category_label = QLabel("Category:")
        category_label.setStyleSheet("border: none; padding: 5px 0px; background-color: transparent;")
        form_layout.addRow(category_label, category_layout)

        # --- Description Field ---
        self.template_info_field = QTextEdit()
        self.template_info_field.setPlaceholderText("Enter template description")
        self.template_info_field.setFixedHeight(80) # Set a fixed height
        self.template_info_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Expand horizontally only
        self.template_info_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
            QTextEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        description_label = QLabel("Description:")
        description_label.setStyleSheet("border: none; padding: 5px 0px; background-color: transparent;")
        form_layout.addRow(description_label, self.template_info_field)

        # Add the form layout to the top section
        top_section_layout.addLayout(form_layout, 1) # Allow form to take up space

        # Create structure section
        structure_layout = QVBoxLayout()
        
        # Create structure header with search box
        structure_header_layout = QHBoxLayout()
        structure_header_layout.setContentsMargins(0, 0, 0, 0)
        structure_header_layout.setSpacing(10)
        
        # Structure header label
        structure_header = QLabel("Project Structure")
        structure_header.setFont(QFont(structure_header.font().family(), 12, QFont.Weight.Bold))
        structure_header.setStyleSheet(f"color: {colors['text']}; padding-top: 10px; padding-bottom: 5px; border: none; background-color: transparent;")
        structure_header_layout.addWidget(structure_header)
        
        # Create search layout for structure section
        search_structure_layout = QHBoxLayout()
        search_structure_layout.setContentsMargins(0, 0, 0, 0)
        search_structure_layout.setSpacing(5)
        
        # Add magnifying glass icon instead of "Search:" label
        magnifying_glass = QLabel("🔍")
        magnifying_glass.setStyleSheet(f"color: {colors['text']}; font-size: 16px; border: none;")
        search_structure_layout.addWidget(magnifying_glass)
        
        # Create the search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search for file or folder in structure...")
        self.search_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                min-width: 500px; /* Increased width */
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        self.search_field.textChanged.connect(self._filter_structure)

        # Add clear button to search field
        clear_action = self.search_field.addAction(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_LineEditClearButton), QLineEdit.ActionPosition.TrailingPosition)
        clear_action.triggered.connect(self._clear_search)
        # Make the clear action visible only when there's text
        self.search_field.textChanged.connect(lambda text: clear_action.setVisible(bool(text)))
        clear_action.setVisible(False) # Initially hidden

        search_structure_layout.addWidget(self.search_field) # REMOVED stretch factor from here
        
        # Add search layout to header layout
        structure_header_layout.addLayout(search_structure_layout, 1) # ADDED stretch factor here for the whole search layout

        # Add the header layout to the main structure layout
        structure_layout.addLayout(structure_header_layout)
        
        # Create the structure tree widget
        self.tree = StructureEditorTree(context_menu_handler=None)
        
        # Set a placeholder message for empty tree
        self.tree.setPlaceholderText("Drop Files and Folders Here")
        
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                alternate-background-color: {colors['card_bg_alt']};
            }}
            QTreeWidget::item {{
                color: {colors['text']};
                padding: 5px;
                margin: 2px 0px;
            }}
            QTreeWidget::item:selected {{
                background-color: {colors['highlight_bg']};
                color: {colors['highlight_text']};
            }}
        """)
        
        # Apply custom delegate to the tree
        try:
            from app.ui.tree_item_delegate import TreeItemDelegate
            custom_delegate = TreeItemDelegate(self.tree)
            self.tree.setItemDelegate(custom_delegate)
            print("DEBUG: Applied custom tree item delegate")
        except Exception as e:
            print(f"ERROR: Could not apply custom delegate: {e}")
        
        # Set up text helper
        self.tree.setHeaderHidden(False)
        self.tree.setHeaderLabels(["Create and organize your project structure by adding files and folders. Drag items to rearrange."])
        self.tree.header().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {colors['card_bg']};
                color: {colors['secondary_text']};
                border: none;
                font-style: italic;
                padding: 5px;
                font-size: 12px;
            }}
        """)
        
        structure_layout.addWidget(self.tree, 1)  # Give tree a stretch factor of 1
        
        # Add button layout
        button_layout = QHBoxLayout()
        
        # Add File button
        add_file_btn = QPushButton("Add File")
        add_file_btn.setStyleSheet(self._get_button_style('default'))
        
        # Create a proper slot function to avoid lambda issues in PyQt6
        def create_add_file_slot():
            def add_file_slot():
                try:
                    # Ensure self.editor exists and has the add_file method
                    if hasattr(self, 'editor') and hasattr(self.editor, 'add_file'):
                        self.editor.add_file()
                    else:
                        print("ERROR: Editor or add_file method not found!")
                except Exception as e:
                    print(f"Error in add file slot: {e}")
                    import traceback
                    traceback.print_exc()
            return add_file_slot
            
        add_file_btn.clicked.connect(create_add_file_slot())
        button_layout.addWidget(add_file_btn)
        
        # Add Folder button
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setStyleSheet(self._get_button_style('default'))
        
        # Create a proper slot function for add_folder
        def create_add_folder_slot():
            def add_folder_slot():
                try:
                    if hasattr(self, 'editor') and hasattr(self.editor, 'add_folder'):
                        self.editor.add_folder()
                    else:
                        print("ERROR: Editor or add_folder method not found!")
                except Exception as e:
                    print(f"Error in add folder slot: {e}")
                    import traceback
                    traceback.print_exc()
            return add_folder_slot
            
        add_folder_btn.clicked.connect(create_add_folder_slot())
        button_layout.addWidget(add_folder_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self._get_button_style('danger'))
        
        # Create a proper slot function for delete
        def create_delete_slot():
            def delete_slot():
                try:
                    if hasattr(self, 'editor') and hasattr(self.editor, 'delete_selected'):
                        self.editor.delete_selected()
                    else:
                        print("ERROR: Editor or delete_selected method not found!")
                except Exception as e:
                    print(f"Error in delete slot: {e}")
                    import traceback
                    traceback.print_exc()
            return delete_slot
            
        delete_btn.clicked.connect(create_delete_slot())
        button_layout.addWidget(delete_btn)
        
        # Add button layout to structure layout
        structure_layout.addLayout(button_layout)
        
        # Add structure stats display
        self.stats_label = QLabel("0 items (0 files, 0 folders)")
        self.stats_label.setStyleSheet(f"color: {colors['secondary_text']}; font-size: 11px; padding: 5px 0;")
        structure_layout.addWidget(self.stats_label)
        
        # Create structure panel widget
        structure_panel = QWidget()
        structure_panel.setLayout(structure_layout)

        # --- Final Assembly using Splitter ---
        # Create a splitter to separate the form from the structure tree
        splitter = QSplitter(Qt.Orientation.Vertical) # Split vertically

        # Create container widget for the top form section
        top_widget = QWidget()
        top_widget.setLayout(top_section_layout)
        # Set a reasonable initial height, but allow shrinking
        top_widget.setFixedHeight(200) 
        top_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        splitter.addWidget(top_widget)

        # Create container widget for the bottom structure section
        bottom_widget = QWidget()
        bottom_widget.setLayout(structure_layout)
        bottom_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(bottom_widget)

        # Set initial sizes for splitter sections (adjust ratio as needed)
        splitter.setSizes([200, 400]) # Give more space to structure tree initially
        # Prevent sections from collapsing completely
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter, 1) # Add splitter to main layout, allow stretching

        self._apply_styling()
        return main_layout
    
    def _get_button_style(self, button_type='default'):
        """
        Get styling for different button types
        
        Args:
            button_type: Type of button ('default', 'primary', 'danger', 'action')
            
        Returns:
            str: Button style sheet
        """
        # Use the main app button styles when possible
        if button_type == 'primary':
            return ACCENT_BUTTON_STYLE
        
        if button_type == 'danger':
            return f"""
                QPushButton {{
                    background-color: #902A2A;
                    color: white;
                    border: 1px solid #732121;
                    border-radius: 3px;
                    padding: 5px 15px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #A33030;
                    border: 1px solid #8A2727;
                }}
                QPushButton:pressed {{
                    background-color: #7D2525;
                }}
            """
        
        if button_type == 'action':
            return f"""
                QPushButton {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 5px 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors['hover_bg']};
                    border: 1px solid {colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['highlight_bg']};
                    color: {colors['highlight_text']};
                }}
            """
        
        # Default button style
        return BUTTON_STYLE
    
    def _apply_styling(self):
        """Apply consistent styling to UI elements"""
        if self.template_name_field:
            self.template_name_field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {colors.get('input_bg', colors['card_bg'])};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 5px;
                    selection-background-color: {colors['highlight_bg']};
                    selection-color: {colors['highlight_text']};
                }}
                QLineEdit:focus {{
                    border: 1px solid {colors['accent']};
                }}
            """)
        
        # Get dropdown arrow SVGs for styling ComboBoxes
        dropdown_arrow_path, dropdown_arrow_up_path = self._get_dropdown_arrows()
        
        # Use resource path helper to get the absolute paths
        arrow_path = dropdown_arrow_path
        arrow_up_path = dropdown_arrow_up_path
        
        if self.template_category_field:
            self.template_category_field.setStyleSheet(f"""
                QComboBox {{
                    background-color: {colors.get('input_bg', colors['card_bg'])};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 5px;
                    padding-right: 20px;  /* Make space for the dropdown arrow */
                    min-width: 100px;
                }}
                QComboBox:hover {{
                    border: 1px solid {colors['accent']};
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left: 1px solid {colors['border']};
                }}
                QComboBox::down-arrow {{
                    image: url("{arrow_path}");
                    width: 16px;
                    height: 16px;
                }}
                QComboBox::down-arrow:on {{
                    image: url("{arrow_up_path}");
                }}
                QComboBox QAbstractItemView {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    selection-background-color: {colors['highlight_bg']};
                    selection-color: {colors['highlight_text']};
                }}
            """)
        
        # Apply styling to the Manage Categories button
        if hasattr(self, 'manage_categories_btn') and self.manage_categories_btn:
            # Use the 'action' style from _get_button_style for the Manage button
            self.manage_categories_btn.setStyleSheet(self._get_button_style('action'))
        
        if self.template_info_field:
            self.template_info_field.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {colors.get('input_bg', colors['card_bg'])};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 5px;
                    selection-background-color: {colors['highlight_bg']};
                    selection-color: {colors['highlight_text']};
                }}
                QTextEdit:focus {{
                    border: 1px solid {colors['accent']};
                }}
            """)
        
        if self.search_field:
            self.search_field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {colors.get('input_bg', colors['card_bg'])};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 3px;
                    padding: 5px;
                    selection-background-color: {colors['highlight_bg']};
                    selection-color: {colors['highlight_text']};
                }}
                QLineEdit:focus {{
                    border: 1px solid {colors['accent']};
                }}
            """)
        
        # Use the centralized enhanced styling for the tree widget
        if self.tree:
            try:
                from app.ui.tree_styling import apply_enhanced_tree_styling
                apply_enhanced_tree_styling(self.tree)
            except ImportError:
                # Fallback to the styling defined in the init_ui method
                pass
    
    def _filter_structure(self, text):
        """Filter tree items based on search text"""
        if not self.tree:
            print("ERROR: Tree widget not available for filtering")
            return
        
        # If search text is empty, show all items
        if not text:
            self._show_all_items(self.tree.invisibleRootItem())
            return
        
        # Convert search text to lowercase for case-insensitive search
        search_text = text.lower()
        
        # Get root item
        root = self.tree.invisibleRootItem()
        
        # Process all top-level items
        for i in range(root.childCount()):
            child = root.child(i)
            self._filter_tree_item(child, search_text)

    def _filter_tree_item(self, item, search_text):
        """
        Recursively filter a tree item and its children
        Returns True if item or any of its children match the search
        """
        # By default, we'll hide this item
        matches = False
        
        # Check if this item matches
        if search_text in item.text(0).lower():
            matches = True
        
        # Check all children
        for i in range(item.childCount()):
            child = item.child(i)
            # If any child matches, this item matches
            if self._filter_tree_item(child, search_text):
                matches = True
        
        # Show or hide based on matches
        item.setHidden(not matches)
        
        # Return match status
        return matches

    def _show_all_items(self, item):
        """Recursively show all items in the tree"""
        # Show this item
        item.setHidden(False)
        
        # Show all children
        for i in range(item.childCount()):
            self._show_all_items(item.child(i))
    
    def _clear_search(self):
        """Clear the search field"""
        self.search_field.clear()
    
    def _show_context_menu(self, position):
        """
        Show context menu for tree widget items
        
        Args:
            position: Position where the context menu should be shown
        """
        try:
            item = self.tree.itemAt(position)
            
            # Create context menu
            menu = QMenu()
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 5px 15px;
                    border-radius: 3px;
                }}
                QMenu::item:selected {{
                    background-color: {colors['highlight_bg']};
                    color: {colors['highlight_text']};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {colors['border']};
                    margin: 5px 2px;
                }}
            """)
            
            # Add item-specific actions if an item is clicked
            if item:
                menu.addSeparator()
                rename_action = menu.addAction("Rename")
                rename_action.triggered.connect(lambda bound_item=item: self.tree.editItem(bound_item, 0))

                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(lambda bound_item=item: self.editor.file_operations.delete_item_confirmed(bound_item))
                    
                # Ensure the item's visual state is up-to-date before reading its data
                self.tree.viewport().update(self.tree.visualItemRect(item))

                # Add "Use Project Name" or "Revert to Original Name" action for files
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(item_data, dict) and item_data.get('type') == 'file':
                    menu.addSeparator()
                    action_text = "Revert to Original Name" if item_data.get('rename_flag') or item_data.get('uses_project_name') else "Use Project Name"
                    use_project_name_action = menu.addAction(action_text)
                    use_project_name_action.setEnabled(True)
                    # CORRECTED CONNECTION: Connect to the editor's method
                    use_project_name_action.triggered.connect(lambda bound_item=item: self.editor._toggle_project_name_for_file(bound_item))
                
                    # Add new placeholder actions
                    prepend_action = menu.addAction("Prepend Project Name")
                    prepend_action.setEnabled(False) # Placeholder

                    append_action = menu.addAction("Append Project Name")
                    append_action.setEnabled(False) # Placeholder

                    custom_action = menu.addAction("Custom Rename...")
                    custom_action.setEnabled(False) # Placeholder
                else:
                    use_project_name_action = None
                    rename_action = None
                    delete_action = None
            
            # Show the menu at the cursor position
            menu.exec(self.tree.viewport().mapToGlobal(position))
            
        except Exception as e:
            print(f"ERROR showing context menu: {e}")
            import traceback
            traceback.print_exc()

    def _rename_item(self, item):
        """
        Rename an item in the tree
        
        Args:
            item: The tree item to rename
        """
        if not item:
            return
        
        # Edit the item
        self.tree.editItem(item, 0)

    def _import_structure(self):
        """
        Import structure from a file
        
        This allows importing structures from:
        - JSON files (direct structure data)
        - Structure files from other templates
        """
        try:
            # Create file dialog
            file_dialog = QFileDialog()
            file_dialog.setWindowTitle("Import Structure")
            file_dialog.setNameFilter("Structure Files (*.json);;All Files (*)")
            file_dialog.setFileMode(QFileDialog.ExistingFile)
            
            # Show dialog and get selected file
            if file_dialog.exec():
                file_paths = file_dialog.selectedFiles()
                if not file_paths:
                    return
                    
                file_path = file_paths[0]
                
                # Try to load the structure from the file
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                        # Extract structure data from various formats
                        structure = None
                        
                        # Format 1: Direct structure array
                        if isinstance(data, list):
                            structure = data
                        
                        # Format 2: Structure in 'structure' field
                        elif isinstance(data, dict) and 'structure' in data:
                            structure = data['structure']
                        
                        # Format 3: Structure in 'directories' field (legacy)
                        elif isinstance(data, dict) and 'directories' in data:
                            structure = data['directories']
                        
                        # If we found a structure, confirm and load it
                        if structure:
                            reply = QMessageBox.question(
                                self.editor,
                                "Import Structure",
                                "This will replace your current structure with the imported one. Continue?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            
                            if reply == QMessageBox.Yes:
                                # Load the structure
                                if hasattr(self.editor, 'structure_converter'):
                                    self.editor.structure_converter.load_structure(structure)
                                    print(f"DEBUG: Imported structure from: {file_path}")
                        else:
                            QMessageBox.warning(
                                self.editor,
                                "Import Structure",
                                "The selected file does not contain a valid structure."
                            )
                except Exception as e:
                    QMessageBox.critical(
                        self.editor,
                        "Import Error",
                        f"Error importing structure: {str(e)}"
                    )
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"ERROR in _import_structure: {e}")
            import traceback
            traceback.print_exc()

    def _manage_categories(self):
        """Open the category management dialog"""
        from app.dialogs.category_management_dialog import CategoryManagementDialog
        
        # Correctly get template_manager instance
        template_manager = None
        if hasattr(self.editor, 'template_manager'): # Check editor first
            template_manager = self.editor.template_manager
        elif hasattr(self.editor, 'app') and hasattr(self.editor.app, 'template_manager'): # Then check app via editor
            template_manager = self.editor.app.template_manager
            
        if not template_manager:
             print("ERROR in _manage_categories: Could not find template_manager instance.")
             QMessageBox.critical(self.editor, "Error", "Could not access category data.")
             return

        # Get current categories to pass to manager
        # Use template_manager as the source of truth for initial load
        manager_categories = template_manager.get_categories()
        print(f"UIBuilder: Opening category manager with initial categories: {manager_categories}")
        
        manager = CategoryManagementDialog(parent=self.editor)
        if manager.exec() == QDialog.Accepted:
            # Categories are saved via ProjectTypeManager now.
            # Dropdowns are updated dynamically via _update_ui_dropdowns 
            # when the setting changes or categories are added/removed in the manager.
            # No need to manually update this specific dropdown here.
            print(f"UIBuilder: Category manager closed (Accepted). Dropdown updates handled by manager.")
            
            # We might still want to update the internal list used by UIBuilder if needed elsewhere
            self.categories = template_manager.get_categories()

            # Optional: Re-select the current category if it still exists, 
            # just to ensure selection is preserved after potential list changes.
            current_selection = self.template_category_field.currentText()
            index = self.template_category_field.findText(current_selection)
            if index != -1:
                self.template_category_field.setCurrentIndex(index)
            elif self.template_category_field.count() > 0:
                self.template_category_field.setCurrentIndex(0)

    def _update_structure_stats(self):
        """Update the status bar with structure statistics"""
        if not hasattr(self, 'tree') or not self.tree:
            return
            
        # Count total items
        total_items = 0
        folders = 0
        files = 0
        
        # Get root item
        root = self.tree.invisibleRootItem()
        
        # Recursive function to count items
        def count_items(item):
            nonlocal total_items, folders, files
            
            # Process all children
            for i in range(item.childCount()):
                child = item.child(i)
                total_items += 1
                
                # Determine if it's a file or folder based on icon
                if child.childCount() > 0 or (hasattr(child, 'data') and child.data(0, Qt.ItemDataRole.UserRole) and 
                   isinstance(child.data(0, Qt.ItemDataRole.UserRole), dict) and child.data(0, Qt.ItemDataRole.UserRole).get('type') == 'folder'):
                    folders += 1
                else:
                    files += 1
                    
                # Process children recursively
                count_items(child)
        
        # Count items
        count_items(root)
        
        # Update status bar
        if total_items == 0:
            self.stats_label.setText("No items in structure")
        else:
            self.stats_label.setText(f"Total: {total_items} items ({folders} folders, {files} files)")

    def _init_category_dropdown(self):
        """Initialize the category dropdown with project types using the centralized updater"""
        print(f"[DEBUG] _init_category_dropdown START - (UIBuilder will use update_single_combobox)")
        
        # Ensure self.template_category_field exists (it should be created in init_ui before this call)
        if not hasattr(self, 'template_category_field') or self.template_category_field is None:
            print(f"[ERROR] _init_category_dropdown: self.template_category_field is not initialized.")
            # As a fallback, create it, though this indicates a logic flow issue.
            self.template_category_field = QComboBox()
            self.template_category_field.setObjectName("template_category_combo_box_fallback")
            print(f"[WARNING] UIBuilder: Created FALLBACK QComboBox with ID: {self.template_category_field.objectName()}")
        else:
            print(f"[DEBUG] UIBuilder: Using existing QComboBox with ID: {self.template_category_field.objectName()}")


        self.categories = self._get_categories()
        print(f"[DEBUG] Categories retrieved for UIBuilder: {len(self.categories)} categories: {self.categories}")
        
        # self.template_category_field = QComboBox() # REMOVE THIS LINE - use the one from init_ui
        # self.template_category_field.setObjectName("template_category_combo_box")
        # print(f"[DEBUG] UIBuilder: Created new QComboBox with ID: {self.template_category_field.objectName()}")

        # Use the centralized updater
        # Initially select "No Category" if possible, or the first available actual category.
        initial_selection = "No Category"
        if not self.categories or "No Category" not in self.categories:
            # If "No Category" isn't in the fetched list (it should be added by manager ideally)
            # or if categories are empty, this ensures robust handling by update_single_combobox
            pass # update_single_combobox handles empty or specific No Category logic

        update_single_combobox(
            combo=self.template_category_field,             categories=self.categories,             current_category=initial_selection,             force_default_style=True        )
        
        print(f"[DEBUG] _init_category_dropdown COMPLETE (UIBuilder) - Items in dropdown: {self.template_category_field.count()}")
        print(f"[DEBUG] Current selection (UIBuilder): '{self.template_category_field.currentText()}'")

    def set_ui_values(self, template_data):
        """Set UI values based on template data"""
        print(f"[DEBUG] set_ui_values START with data: {template_data}")
        
        # Debug: Check if dropdown exists before setting values
        dropdown_exists = hasattr(self, 'template_category_field') and self.template_category_field is not None
        print(f"[DEBUG] Dropdown exists: {dropdown_exists}")
        
        if dropdown_exists:
            print(f"[DEBUG] Current dropdown state BEFORE changes:")
            print(f"[DEBUG] - Items count: {self.template_category_field.count()}")
            print(f"[DEBUG] - Current index: {self.template_category_field.currentIndex()}")
            print(f"[DEBUG] - Current text: '{self.template_category_field.currentText()}'")
            all_items = [self.template_category_field.itemText(i) for i in range(self.template_category_field.count())]
            print(f"[DEBUG] - All items: {all_items}")
        
        # Set template name
        if 'template_name' in template_data and self.template_name_field:
            self.template_name_field.setText(template_data['template_name'])
            print(f"[DEBUG] Set template name to: '{template_data['template_name']}'")
            
        # Set template category
        if self.template_category_field:
            category = None
            
            # Check various possible keys for category information
            if 'template_category' in template_data:
                category = template_data['template_category']
                print(f"[DEBUG] Found category in 'template_category': '{category}'")
            elif 'category' in template_data:
                category = template_data['category']
                print(f"[DEBUG] Found category in 'category': '{category}'")
            elif 'type' in template_data:  # Some templates use "type" for category
                category = template_data['type']
                print(f"[DEBUG] Found category in 'type': '{category}'")
            else:
                print(f"[DEBUG] No category found in template data")
                
            # If category is None or empty, select "No Category"
            if not category:
                category_to_select = "No Category"
                print(f"[DEBUG] Empty category, will select 'No Category'")
            else:
                category_to_select = category.strip()
                print(f"[DEBUG] Will try to select: '{category_to_select}'")
            
            dropdown_items = [self.template_category_field.itemText(i) for i in range(self.template_category_field.count())]
            print(f"[DEBUG] Dropdown items: {dropdown_items}")
            
            # Find and select the matching category
            # Use Qt.MatchFlag.MatchFixedString for exact match
            index = self.template_category_field.findText(category_to_select, Qt.MatchFlag.MatchFixedString)
            
            print(f"[DEBUG] Found index for '{category_to_select}': {index}")
            
            if index >= 0:
                print(f"[DEBUG] BEFORE setCurrentIndex({index}): currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                self.template_category_field.setCurrentIndex(index)
                print(f"[DEBUG] AFTER setCurrentIndex({index}): currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                self.template_category_field.update()
                self.template_category_field.repaint()
                QApplication.processEvents()
                print(f"[DEBUG] After UI update: currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
            else:
                # If the specific category isn't found, fallback to "No Category"
                index_no_category = self.template_category_field.findText("No Category")
                print(f"[DEBUG] Fallback: Index for 'No Category': {index_no_category}")
                if index_no_category >= 0:
                    print(f"[DEBUG] BEFORE fallback setCurrentIndex({index_no_category}): currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                    self.template_category_field.setCurrentIndex(index_no_category)
                    print(f"[DEBUG] AFTER fallback setCurrentIndex({index_no_category}): currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                    self.template_category_field.update()
                    self.template_category_field.repaint()
                    QApplication.processEvents()
                    print(f"[DEBUG] After fallback UI update: currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                else:
                    print(f"[DEBUG] BEFORE absolute fallback setCurrentIndex(0): currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                    self.template_category_field.setCurrentIndex(0) # Absolute fallback
                    print(f"[DEBUG] AFTER absolute fallback setCurrentIndex(0): currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
                    self.template_category_field.update()
                    self.template_category_field.repaint()
                    QApplication.processEvents()
                    print(f"[DEBUG] After absolute fallback UI update: currentIndex={self.template_category_field.currentIndex()}, currentText='{self.template_category_field.currentText()}'")
            
        # Set template description
        if ('template_info' in template_data or 'description' in template_data) and self.template_info_field:
            description = template_data.get('template_info', template_data.get('description', ''))
            self.template_info_field.setText(description)
            print(f"[DEBUG] Set description: {description[:50]}{'...' if len(description) > 50 else ''}")

        # Final state check
        if dropdown_exists:
            print(f"[DEBUG] Final dropdown state AFTER all changes:")
            print(f"[DEBUG] - Items count: {self.template_category_field.count()}")
            print(f"[DEBUG] - Current index: {self.template_category_field.currentIndex()}")
            print(f"[DEBUG] - Current text: '{self.template_category_field.currentText()}'")
            all_items = [self.template_category_field.itemText(i) for i in range(self.template_category_field.count())]
            print(f"[DEBUG] - All items: {all_items}")
        
        print(f"[DEBUG] set_ui_values END")

    def get_ui_values(self):
        """Retrieve values from the UI fields"""
        template_info = {}
        
        # Get template name
        if self.template_name_field:
            template_info['template_name'] = self.template_name_field.text().strip()
            
        # Get template category
        if self.template_category_field:
            selected_category_text = self.template_category_field.currentText()
            # Store empty string if "No Category" is selected
            if selected_category_text == "No Category":
                template_info['template_category'] = ""
                template_info['category'] = ""
            else:
                template_info['template_category'] = selected_category_text
                template_info['category'] = selected_category_text
            
        # Get template description
        if self.template_info_field:
            template_info['template_info'] = self.template_info_field.toPlainText().strip()
            # Also store as description for compatibility
            template_info['description'] = template_info['template_info']
            
        return template_info 

    def _get_categories(self):
        """
        Get available template categories from the template manager
        
        Returns:
            list: List of categories
        """
        print(f"[DEBUG] _get_categories START")
        
        categories = []
        
        # Try to get from template manager (primary source)
        if hasattr(self, 'template_manager') and self.template_manager:
            # Check if the template manager has get_categories method
            if hasattr(self.template_manager, 'get_categories'):
                try:
                    categories = self.template_manager.get_categories()
                    print(f"[DEBUG] Retrieved {len(categories)} categories from template_manager: {categories}")
                except Exception as e:
                    print(f"[DEBUG] Error getting categories from template_manager: {e}")
            else:
                print(f"[DEBUG] template_manager doesn't have get_categories method")
        else:
            print(f"[DEBUG] No template_manager available in UIBuilder")
            
        # If we still don't have categories, check alternate sources
        if not categories:
            # Try to get from editor.app
            if hasattr(self, 'editor') and hasattr(self.editor, 'app'):
                if hasattr(self.editor.app, 'template_manager'):
                    try:
                        categories = self.editor.app.template_manager.get_categories()
                        print(f"[DEBUG] Retrieved {len(categories)} categories from editor.app.template_manager: {categories}")
                    except Exception as e:
                        print(f"[DEBUG] Error getting categories from editor.app.template_manager: {e}")
            
            # If still no categories, use default
            if not categories:
                # Import default categories from constants
                from app.constants import DEFAULT_TEMPLATE_CATEGORIES
                categories = list(DEFAULT_TEMPLATE_CATEGORIES)
                print(f"[DEBUG] Using DEFAULT_TEMPLATE_CATEGORIES: {categories}")
                
                # Make sure we have at least "Custom" category
                if "Custom" not in categories:
                    categories.append("Custom")
                    print(f"[DEBUG] Added 'Custom' to categories")
                    
                # Add 'No Category' for templates without a category
                if "No Category" not in categories:
                    categories.append("No Category")
                    print(f"[DEBUG] Added 'No Category' to categories")
        
        # Check for category filtering settings
        hide_defaults = QSettings().value("CategoryManager/hideDefaultCategories", False, type=bool)
        if hide_defaults:
            from app.constants import DEFAULT_TEMPLATE_CATEGORIES
            original_count = len(categories)
            categories = [cat for cat in categories if cat not in DEFAULT_TEMPLATE_CATEGORIES]
            print(f"[DEBUG] Hide defaults setting is ON - filtered from {original_count} to {len(categories)} categories")
        
        print(f"[DEBUG] _get_categories FINAL result: {categories}")
        return categories 

    def _get_dropdown_arrows(self):
        """
        Get the appropriate dropdown arrow paths for the current platform,
        using resource paths.
        
        Returns:
            tuple: (arrow_path, arrow_up_path) with resolved paths
        """
        # Use different arrows for Windows vs. macOS/Linux
        if platform.system() == "Windows":
            # For Windows, use white arrows for better contrast on dark backgrounds
            dropdown_arrow_path = get_resource_path("app/assets/css/dropdown_arrow_windows.svg")
            dropdown_arrow_up_path = get_resource_path("app/assets/css/dropdown_arrow_up_windows.svg")
            
            # If the Windows-specific arrows don't exist, fall back to regular ones
            if not os.path.exists(dropdown_arrow_path):
                dropdown_arrow_path = get_resource_path("app/assets/css/dropdown_arrow.svg")
                dropdown_arrow_up_path = get_resource_path("app/assets/css/dropdown_arrow_up.svg")
        else:
            # Default arrows for macOS/Linux
            dropdown_arrow_path = get_resource_path("app/assets/css/dropdown_arrow.svg")
            dropdown_arrow_up_path = get_resource_path("app/assets/css/dropdown_arrow_up.svg")
        
        # For Qt stylesheets, always use forward slashes regardless of platform
        dropdown_arrow_path = dropdown_arrow_path.replace('\\', '/')
        dropdown_arrow_up_path = dropdown_arrow_up_path.replace('\\', '/')
        
        return dropdown_arrow_path, dropdown_arrow_up_path 