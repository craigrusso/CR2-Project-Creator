#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
UI Components Module for Structure Editor
Handles building and managing UI elements
"""

import os
import json
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu, QAction,
    QMessageBox, QTextEdit, QComboBox, QCheckBox, QSplitter, QWidget, 
    QSizePolicy, QGroupBox, QFormLayout, QFrame, QTabWidget, QFileDialog, QInputDialog, QListWidget, QDialog, QApplication, QStyle
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPainter

# Import the main application colors
from app.ui.color_scheme_pyqt import APP_COLORS, BUTTON_STYLE, ACCENT_BUTTON_STYLE, CONTEXT_MENU_STYLE

# Colors for UI consistency - using main app colors
colors = APP_COLORS

class StructureEditorTree(QTreeWidget):
    """Enhanced QTreeWidget for structure editing with improved styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Name"])
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setDropIndicatorShown(True)
        self.setIndentation(20)
        
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
        
        # Disable focus rectangle on macOS
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        
        # Make all items editable with the right triggers
        self.setEditTriggers(QTreeWidget.DoubleClicked | 
                             QTreeWidget.EditKeyPressed | 
                             QTreeWidget.SelectedClicked)
    
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
            painter.drawText(rect, Qt.AlignCenter, self.placeholder_text)
            
            painter.restore()

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
        self.root_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
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
                folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
                
                # Recursively add children
                if 'children' in item:
                    self._populate_tree(item['children'], folder_item)
            elif isinstance(item, str):
                # File item
                file_item = QTreeWidgetItem(parent_item)
                file_item.setText(0, item)
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
            else:
                # Dictionary with folder name as key
                for folder_name, children in item.items():
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, folder_name)
                    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
                    folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
                    
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
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
            parent_item.setExpanded(True)
    
    def _add_file(self):
        """Add a new file to the selected item"""
        selected_items = self.tree.selectedItems()
        parent_item = selected_items[0] if selected_items else self.root_item
        
        file_name, ok = QInputDialog.getText(self, "New File", "File name:")
        
        if ok and file_name:
            file_item = QTreeWidgetItem(parent_item)
            file_item.setText(0, file_name)
            file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
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
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
        
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
                    file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
                    file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
            
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
            is_folder = child.icon(0).cacheKey() == QApplication.style().standardIcon(QStyle.SP_DirIcon).cacheKey()
            
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
        
        # Emit signal with name and structure
        self.structureChanged.emit(self.structure_name, structure)
        
        # Accept and close
        self.accept()

class UIBuilder:
    """
    Builds and manages the UI for the Enhanced Structure Editor
    """
    
    def __init__(self, editor, structure_name=None):
        """
        Initialize the UI builder
        
        Args:
            editor: The parent editor instance
            structure_name: Optional name of the structure (for template name field)
        """
        self.editor = editor
        self.structure_name = structure_name
        self.tree = None
        self.template_name_field = None
        self.template_category_field = None
        self.template_info_field = None
        self.search_field = None
        
        # Get categories from template_manager if available
        self.categories = self._get_categories()
        print(f"UIBuilder: Initialized with {len(self.categories)} categories: {self.categories}")
    
    def _get_categories(self):
        """Get categories from the application's template manager"""
        # Try to get app reference from editor
        app = None
        if hasattr(self.editor, 'app'):
            app = self.editor.app
        elif hasattr(self.editor, 'parent') and callable(self.editor.parent) and hasattr(self.editor.parent(), 'app'):
            app = self.editor.parent().app
            
        # Get template manager from app
        if app and hasattr(app, 'template_manager') and hasattr(app.template_manager, 'get_categories'):
            # Get categories from template manager (single source of truth)
            categories = app.template_manager.get_categories()
            print(f"UIBuilder: Retrieved {len(categories)} categories from template_manager")
            return categories
            
        # Fallback to default categories
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        print("UIBuilder: Using default categories from constants")
        return list(DEFAULT_TEMPLATE_CATEGORIES)
    
    def init_ui(self):
        """
        Initialize the complete user interface
        
        Returns:
            QLayout: The main layout
        """
        # Create main layout - don't attach to any widget yet
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create a fixed area for the top part of the form (name, category, search)
        fixed_info_panel = QWidget()
        fixed_info_layout = QVBoxLayout(fixed_info_panel)
        fixed_info_layout.setContentsMargins(5, 5, 5, 5)
        fixed_info_layout.setSpacing(10)
        
        # Create header label
        header_label = QLabel("Template Information")
        header_label.setFont(QFont(header_label.font().family(), 12, QFont.Bold))
        header_label.setStyleSheet(f"color: {colors['text']}; padding-bottom: 5px;")
        fixed_info_layout.addWidget(header_label)
        
        # Create a fixed form for name, category and search
        fixed_form = QFormLayout()
        fixed_form.setContentsMargins(0, 0, 0, 0)
        fixed_form.setSpacing(10)
        fixed_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        fixed_form.setLabelAlignment(Qt.AlignRight)
        
        # Helper function to create labels with consistent styling
        def create_label(text):
            label = QLabel(text)
            label.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
            return label
        
        # Template name field
        self.template_name_field = QLineEdit()
        self.template_name_field.setPlaceholderText("Enter template name")
        self.template_name_field.setText(self.structure_name)
        self.template_name_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        
        # Connect template name change signal if the editor has a method for it
        if hasattr(self.editor, '_on_template_name_changed'):
            self.template_name_field.textChanged.connect(self.editor._on_template_name_changed)
        
        fixed_form.addRow(create_label("Template Name:"), self.template_name_field)
        
        # Template category field
        self.template_category_field = QComboBox()
        self.template_category_field.addItems(self.categories)
        self.template_category_field.setCurrentIndex(0)  # Default to "Custom"
        self.template_category_field.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                padding-right: 20px;  /* Make space for the dropdown arrow */
                min-width: 120px;
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
                image: url(app/assets/css/dropdown_arrow.svg);
                width: 16px;
                height: 16px;
            }}
            QComboBox::down-arrow:on {{
                image: url(app/assets/css/dropdown_arrow_up.svg);
            }}
        """)
        
        # Create a horizontal layout for category dropdown and manage button
        category_layout = QHBoxLayout()
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(5)
        category_layout.addWidget(self.template_category_field)
        
        # Add manage categories button
        manage_categories_btn = QPushButton("Manage")
        manage_categories_btn.setFixedWidth(80)
        manage_categories_btn.setStyleSheet(self._get_button_style('action'))
        manage_categories_btn.clicked.connect(self._manage_categories)
        category_layout.addWidget(manage_categories_btn)
        
        fixed_form.addRow(create_label("Category:"), category_layout)
        
        fixed_info_layout.addLayout(fixed_form)
        
        # Create description panel with stretch
        description_panel = QWidget()
        description_panel.setObjectName("description_panel")  # Set object name for testing
        description_layout = QVBoxLayout(description_panel)
        description_layout.setContentsMargins(5, 0, 5, 5)
        
        # Template description field
        self.template_info_field = QTextEdit()
        self.template_info_field.setPlaceholderText("Enter template description")
        self.template_info_field.setMinimumHeight(60)
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
        
        # Description form layout
        description_form = QFormLayout()
        description_form.setContentsMargins(0, 0, 0, 0)
        description_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        description_form.setLabelAlignment(Qt.AlignRight)
        description_form.addRow(create_label("Description:"), self.template_info_field)
        
        description_layout.addLayout(description_form)
        
        # Create a container for both info panels
        info_container = QWidget()
        info_container_layout = QVBoxLayout(info_container)
        info_container_layout.setContentsMargins(0, 0, 0, 0)
        info_container_layout.setSpacing(0)
        
        # Add fixed panel and description panel to container
        info_container_layout.addWidget(fixed_info_panel)
        info_container_layout.addWidget(description_panel, 1)  # Give stretch to description panel
        
        # Create structure section
        structure_layout = QVBoxLayout()
        
        # Create structure header with search box
        structure_header_layout = QHBoxLayout()
        structure_header_layout.setContentsMargins(0, 0, 0, 0)
        structure_header_layout.setSpacing(10)
        
        # Structure header label
        structure_header = QLabel("Project Structure")
        structure_header.setFont(QFont(structure_header.font().family(), 12, QFont.Bold))
        structure_header.setStyleSheet(f"color: {colors['text']}; padding-top: 10px; padding-bottom: 5px;")
        structure_header_layout.addWidget(structure_header)
        
        # Add stretch to push search to right side
        structure_header_layout.addStretch(1)
        
        # Create search layout for structure section
        search_structure_layout = QHBoxLayout()
        search_structure_layout.setContentsMargins(0, 0, 0, 0)
        search_structure_layout.setSpacing(5)
        
        # Add magnifying glass icon instead of "Search:" label
        magnifying_glass = QLabel("🔍")
        magnifying_glass.setStyleSheet(f"color: {colors['text']}; font-size: 16px;")
        search_structure_layout.addWidget(magnifying_glass)
        
        # Create the search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Filter structure...")
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                min-width: 150px;
                max-width: 200px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        self.search_field.textChanged.connect(self._filter_structure)
        search_structure_layout.addWidget(self.search_field)
        
        # Clear button for search
        clear_btn = QPushButton("×")
        clear_btn.setToolTip("Clear search")
        clear_btn.setFixedSize(30, 30)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors['text']};
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 22px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
                color: {colors['highlight_text']};
            }}
        """)
        clear_btn.clicked.connect(self._clear_search)
        search_structure_layout.addWidget(clear_btn)
        
        # Add search layout to header layout
        structure_header_layout.addLayout(search_structure_layout)
        
        # Add the header layout to the main structure layout
        structure_layout.addLayout(structure_header_layout)
        
        # Create the structure tree widget
        self.tree = StructureEditorTree()
        
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
        add_file_btn.clicked.connect(lambda: self.editor.add_file() if hasattr(self.editor, 'add_file') else None)
        button_layout.addWidget(add_file_btn)
        
        # Add Folder button
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setStyleSheet(self._get_button_style('default'))
        add_folder_btn.clicked.connect(lambda: self.editor.add_folder() if hasattr(self.editor, 'add_folder') else None)
        button_layout.addWidget(add_folder_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self._get_button_style('danger'))
        delete_btn.clicked.connect(lambda: self.editor.delete_selected() if hasattr(self.editor, 'delete_selected') else None)
        button_layout.addWidget(delete_btn)
        
        # Add button layout to structure layout
        structure_layout.addLayout(button_layout)
        
        # Add structure stats display
        self.stats_label = QLabel("0 items (0 files, 0 folders)")
        self.stats_label.setStyleSheet(f"color: {colors['secondary_text']}; font-size: 11px; padding: 5px 0;")
        structure_layout.addWidget(self.stats_label)
        
        # Create structure panel
        structure_panel = QWidget()
        structure_panel.setLayout(structure_layout)
        
        # Create a QSplitter to allow resizing of template info and structure sections
        splitter = QSplitter(Qt.Vertical)
        
        # Add info container and structure panel to splitter
        splitter.addWidget(info_container)
        splitter.addWidget(structure_panel)
        
        # Set initial sizes to give more space to the structure section
        splitter.setSizes([200, 400])  # Adjusted to give more space to structure section
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Connect selection changed signal to update stats
        self.tree.itemSelectionChanged.connect(self._update_structure_stats)
        
        # Wait a moment before updating stats (let tree fully initialize)
        QTimer.singleShot(100, self._update_structure_stats)
        
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
                    image: url(app/assets/css/dropdown_arrow.svg);
                    width: 16px;
                    height: 16px;
                }}
                QComboBox::down-arrow:on {{
                    image: url(app/assets/css/dropdown_arrow_up.svg);
                }}
                QComboBox QAbstractItemView {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    selection-background-color: {colors['highlight_bg']};
                    selection-color: {colors['highlight_text']};
                }}
            """)
        
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
            
            # Actions for selected item
            if item:
                add_file_here = menu.addAction("Add File Here")
                add_folder_here = menu.addAction("Add Folder Here")
                menu.addSeparator()
                rename_item = menu.addAction("Rename")
                
                # Add project name option for files
                if not item.childCount(): # It's a file (no children)
                    menu.addSeparator()
                    # Add options for file renaming with project name
                    use_project_name = menu.addAction("Use Project Name for File")
                    use_project_name.setCheckable(True)
                    
                    # Check if item has flag for using project name
                    if item.data(0, Qt.UserRole) and 'uses_project_name' in item.data(0, Qt.UserRole):
                        use_project_name.setChecked(item.data(0, Qt.UserRole)['uses_project_name'])
                    
                menu.addSeparator()
                delete_item = menu.addAction("Delete")
                
                # Connect signals for item-related actions
                add_file_here.triggered.connect(lambda: self.editor.add_file(item))
                add_folder_here.triggered.connect(lambda: self.editor.add_folder(item))
                rename_item.triggered.connect(lambda: self._rename_item(item))
                delete_item.triggered.connect(lambda: self.editor._delete_item(item))
                
                # Connect project name action if it exists
                if not item.childCount():
                    use_project_name.triggered.connect(lambda: self._toggle_project_name_for_file(item))
            else:
                # Global actions
                add_file = menu.addAction("Add File")
                add_folder = menu.addAction("Add Folder")
                menu.addSeparator()
                import_structure = menu.addAction("Import Structure...")
                
                # Connect signals for global actions
                add_file.triggered.connect(self.editor.add_file)
                add_folder.triggered.connect(self.editor.add_folder)
                import_structure.triggered.connect(self._import_structure)
            
            # Show the menu at the cursor position
            menu.exec_(self.tree.viewport().mapToGlobal(position))
            
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
            if file_dialog.exec_():
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
        """
        Show dialog to manage template categories
        """
        try:
            # Import the category manager dialog
            from app.ui.structure_editor.category_manager import CategoryManager
            
            # Get app and template manager reference
            app = None
            if hasattr(self.editor, 'app'):
                app = self.editor.app
            elif hasattr(self.editor, 'parent') and callable(self.editor.parent) and hasattr(self.editor.parent(), 'app'):
                app = self.editor.parent().app
                
            # Get template manager
            template_manager = None
            if app and hasattr(app, 'template_manager'):
                template_manager = app.template_manager
            
            # Get current categories - use template_manager as source of truth
            if template_manager and hasattr(template_manager, 'get_categories'):
                categories = template_manager.get_categories()
                print(f"UIBuilder: Getting categories from app's template_manager: {categories}")
            else:
                # Try to create a template manager instance if needed
                from app.templates.template_manager import TemplateManager
                template_manager = TemplateManager()
                categories = template_manager.get_categories() if hasattr(template_manager, 'get_categories') else ["Custom"]
                print(f"UIBuilder: Created new template_manager instance to get categories: {categories}")
            
            # Show the dialog with the right parent
            category_manager = CategoryManager(self.editor, categories)
            result = category_manager.exec()
            
            # If dialog was accepted, refresh categories
            if result == category_manager.Accepted:
                # Get updated categories
                updated_categories = category_manager.get_categories()
                print(f"UIBuilder: Categories updated in manager: {updated_categories}")
                
                # Update the categories in our builder
                self.categories = updated_categories
                
                # Refresh the category dropdown
                if hasattr(self, 'template_category_field') and self.template_category_field:
                    # Store current category
                    current_category = self.template_category_field.currentText()
                    
                    # Update combobox
                    self.template_category_field.clear()
                    self.template_category_field.addItems(updated_categories)
                    
                    # Restore selection if possible, otherwise use first category
                    index = self.template_category_field.findText(current_category)
                    if index >= 0:
                        self.template_category_field.setCurrentIndex(index)
                    elif self.template_category_field.count() > 0:
                        self.template_category_field.setCurrentIndex(0)
                    
                    print(f"UIBuilder: Updated category dropdown with {len(updated_categories)} items")
        except Exception as e:
            print(f"ERROR in _manage_categories: {e}")
            import traceback
            traceback.print_exc()
    
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
                if child.childCount() > 0 or (hasattr(child, 'data') and child.data(0, Qt.UserRole) and 
                   isinstance(child.data(0, Qt.UserRole), dict) and child.data(0, Qt.UserRole).get('type') == 'folder'):
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
        """Initialize the category dropdown with project types"""
        # print(f"[INIT DROPDOWN DEBUG] Running _init_category_dropdown") # Removed debug print
        # Always get fresh categories from the template manager
        self.categories = self._get_categories()
        print(f"UIBuilder: Initializing category dropdown with {len(self.categories)} categories: {self.categories}")
        
        # Create and configure the combo box
        self.template_category_field = QComboBox()
        self.template_category_field.setObjectName("template_category_field")  # Give it a name to identify later
        
        # Add "No Category" as the first option
        self.template_category_field.addItem("No Category")
        
        # Split categories into default and custom
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        default_categories = []
        custom_categories = []
        
        for category in self.categories:
            if category in DEFAULT_TEMPLATE_CATEGORIES:
                default_categories.append(category)
            elif category != "No Category":  # Already added at the beginning
                custom_categories.append(category)
        
        # Add default categories first
        for category in default_categories:
            if category != "No Category":  # Already added as the first item
                self.template_category_field.addItem(category)
        
        # Add a separator if there are custom categories
        if custom_categories:
            self.template_category_field.insertSeparator(self.template_category_field.count())
            
        # Add custom categories after divider
        for category in custom_categories:
            self.template_category_field.addItem(category)
        
        # Set the default index to 'No Category' after adding all items
        no_cat_index = self.template_category_field.findText("No Category")
        if no_cat_index >= 0:
            # print(f"[INIT DROPDOWN DEBUG] Setting default index to {no_cat_index} ('No Category')") # Removed debug print
            self.template_category_field.setCurrentIndex(no_cat_index)
        else:
            # Fallback to index 0 if 'No Category' isn't found (shouldn't happen)
            # print(f"[INIT DROPDOWN DEBUG] 'No Category' not found, setting default index to 0") # Removed debug print
            self.template_category_field.setCurrentIndex(0)

    def set_ui_values(self, template_data):
        """Set UI values based on template data"""
        # print(f"[SET UI DEBUG] Setting UI values with data: {template_data}") # Removed debug print
        
        # Set template name
        if 'template_name' in template_data and self.template_name_field:
            self.template_name_field.setText(template_data['template_name'])
            
        # Set template category
        if self.template_category_field:
            category = None
            
            # Check various possible keys for category information
            if 'template_category' in template_data:
                category = template_data['template_category']
            elif 'category' in template_data:
                category = template_data['category']
            elif 'type' in template_data:  # Some templates use "type" for category
                category = template_data['type']
                
            # If category is None or empty, select "No Category"
            if not category:
                category_to_select = "No Category"
            else:
                category_to_select = category.strip()
            
            dropdown_items = [self.template_category_field.itemText(i) for i in range(self.template_category_field.count())]
            print(f"[SET UI DEBUG] Attempting to select category: '{category_to_select}'")
            print(f"[SET UI DEBUG] Dropdown items: {dropdown_items}")
            
            # Find and select the matching category
            # Use Qt.MatchFixedString for exact match
            index = self.template_category_field.findText(category_to_select, Qt.MatchFixedString)
            
            print(f"[SET UI DEBUG] Found index for '{category_to_select}': {index}")
            
            if index >= 0:
                self.template_category_field.setCurrentIndex(index)
                print(f"[SET UI DEBUG] Set dropdown index to {index} ('{category_to_select}')")
                self.template_category_field.update()
                self.template_category_field.repaint()
                QApplication.processEvents()
                print(f"[SET UI DEBUG] Forced UI update after setting index {index}")
            else:
                # If the specific category isn't found, fallback to "No Category"
                index_no_category = self.template_category_field.findText("No Category")
                print(f"[SET UI DEBUG] Fallback: Index for 'No Category': {index_no_category}")
                if index_no_category >= 0:
                    self.template_category_field.setCurrentIndex(index_no_category)
                    print(f"[SET UI DEBUG] Set dropdown index to fallback {index_no_category} ('No Category')")
                    self.template_category_field.update()
                    self.template_category_field.repaint()
                    QApplication.processEvents()
                    print(f"[SET UI DEBUG] Forced UI update after setting fallback index {index_no_category}")
                else:
                    self.template_category_field.setCurrentIndex(0) # Absolute fallback
                    print(f"[SET UI DEBUG] Set dropdown index to absolute fallback 0 ('{self.template_category_field.itemText(0)}')")
                    self.template_category_field.update()
                    self.template_category_field.repaint()
                    QApplication.processEvents()
                    print(f"[SET UI DEBUG] Forced UI update after setting absolute fallback index 0")
            
        # Set template description
        if ('template_info' in template_data or 'description' in template_data) and self.template_info_field:
            description = template_data.get('template_info', template_data.get('description', ''))
            self.template_info_field.setText(description)

        # Log the final index after setting everything
        # final_category_index = self.template_category_field.currentIndex()
        # print(f"[SET UI DEBUG] Final category index at end of set_ui_values: {final_category_index} ('{self.template_category_field.currentText()}')") # Removed final check

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