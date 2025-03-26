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
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

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
        self.categories = ["Custom", "Audio", "Video", "Photography", "Graphics", "Writing", "Development", "Other"]
    
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
        
        # Create template information panel
        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create header label
        header_label = QLabel("Template Information")
        header_label.setFont(QFont(header_label.font().family(), 12, QFont.Bold))
        header_label.setStyleSheet(f"color: {colors['text']}; padding-bottom: 5px;")
        info_layout.addWidget(header_label)
        
        # Create form layout
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
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
        
        form_layout.addRow(create_label("Template Name:"), self.template_name_field)
        
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
        
        form_layout.addRow(create_label("Category:"), self.template_category_field)
        
        # Template description field
        self.template_info_field = QTextEdit()
        self.template_info_field.setPlaceholderText("Enter template description")
        self.template_info_field.setMaximumHeight(60)
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
        
        form_layout.addRow(create_label("Description:"), self.template_info_field)
        
        # Add predefined structure selection
        self.predefined_label = QLabel("Predefined:")
        self.predefined_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
        
        self.predefined_combo = QComboBox()
        self.predefined_combo.addItem("Custom")
        self.predefined_combo.addItem("Basic")
        self.predefined_combo.addItem("Web App")
        self.predefined_combo.addItem("Mobile App")
        self.predefined_combo.addItem("Documentation")
        self.predefined_combo.addItem("Library")
        self.predefined_combo.setCurrentIndex(0)
        self.predefined_combo.currentIndexChanged.connect(self._load_predefined_structure)
        self.predefined_combo.setStyleSheet(f"""
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
        
        predef_layout = QHBoxLayout()
        predef_layout.addWidget(self.predefined_combo)
        
        # Add save-as-preset button
        save_preset_btn = QPushButton("Save as Preset")
        save_preset_btn.clicked.connect(self._save_as_preset)
        save_preset_btn.setStyleSheet(self._get_button_style('action'))
        predef_layout.addWidget(save_preset_btn)
        
        form_layout.addRow(self.predefined_label, predef_layout)
        
        # Add search field for filtering
        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"color: {colors['text']}; font-weight: bold;")
        
        search_layout = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Filter structure...")
        self.search_field.setStyleSheet(f"""
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
        self.search_field.textChanged.connect(self._filter_structure)
        
        clear_search_btn = QPushButton("Clear")
        clear_search_btn.clicked.connect(self._clear_search)
        clear_search_btn.setStyleSheet(self._get_button_style('action'))
        
        search_layout.addWidget(self.search_field)
        search_layout.addWidget(clear_search_btn)
        
        form_layout.addRow(search_label, search_layout)
        
        # Add form layout to info layout
        info_layout.addLayout(form_layout)
        
        # ------------------- Project Structure Section --------------------- #
        # Create project structure header and controls
        structure_header = QLabel("Project Structure")
        structure_header.setFont(QFont(structure_header.font().family(), 12, QFont.Bold))
        structure_header.setStyleSheet(f"color: {colors['text']}; padding-top: 15px; padding-bottom: 5px;")
        info_layout.addWidget(structure_header)
        
        # Add helpful instruction text
        instruction_text = QLabel("Create and organize your project structure by adding files and folders. Drag items to rearrange.")
        instruction_text.setWordWrap(True)
        instruction_text.setStyleSheet(f"color: {colors['secondary_text']}; font-style: italic; margin-bottom: 8px;")
        info_layout.addWidget(instruction_text)
        
        # Add structure operation buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 10)
        
        # Create structure buttons
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self.editor.add_file)
        add_file_btn.setStyleSheet(self._get_button_style('action'))
        add_file_btn.setIcon(QIcon.fromTheme("document-new"))
        
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.editor.add_folder)
        add_folder_btn.setStyleSheet(self._get_button_style('action'))
        add_folder_btn.setIcon(QIcon.fromTheme("folder-new"))
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.editor.delete_selected)
        delete_btn.setStyleSheet(self._get_button_style('danger'))
        delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        
        # Add structure buttons to layout
        button_layout.addWidget(add_file_btn)
        button_layout.addWidget(add_folder_btn)
        button_layout.addWidget(delete_btn)
        
        # Add spacer
        button_layout.addStretch()
        
        info_layout.addLayout(button_layout)
        
        # Use the tree from the editor if it exists, otherwise create a new one
        if hasattr(self.editor, 'tree') and self.editor.tree:
            self.tree = self.editor.tree
            print("DEBUG: Using existing tree widget")
        else:
            # Create a new tree widget
            self.tree = StructureEditorTree()
            self.tree.setMinimumWidth(400)
            self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
            self.tree.setDragEnabled(True)
            self.tree.setAcceptDrops(True)
            self.tree.setDropIndicatorShown(True)
            self.tree.setDragDropMode(QTreeWidget.InternalMove)
            self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
            self.tree.setAlternatingRowColors(True)
            self.tree.setAnimated(True)
            self.tree.setIndentation(20)
            
            # Set tree on editor for other components to access
            self.editor.tree = self.tree
        
        # Configure tree widget
        self.tree.setHeaderHidden(True)  # Hide the header completely
        
        # Set icon size for better visibility
        self.tree.setIconSize(QSize(18, 18))
        
        # Ensure branch indicators are visible
        self.tree.setRootIsDecorated(True)
        self.tree.setItemsExpandable(True)
        
        # Apply enhanced tree styling using our centralized function
        try:
            from app.ui.tree_styling import apply_enhanced_tree_styling
            apply_enhanced_tree_styling(self.tree)
            print("DEBUG: Applied enhanced tree styling")
        except ImportError:
            # Fallback styling if the import fails
            self.tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    outline: none;
                    alternate-background-color: #2A2A2A;
                }}
                QTreeWidget::item {{
                    padding: 5px;
                    border-bottom: 1px solid {colors['border']};
                    min-height: 22px;
                }}
                QTreeWidget::item:hover {{
                    background-color: {colors['hover_bg']};
                }}
                QTreeWidget::item:selected {{
                    background-color: {colors['highlight_bg']};
                    color: {colors['highlight_text']};
                }}
                
                /* Style branch indicators to ensure they're visible */
                QTreeWidget::branch {{
                    background-color: transparent;
                }}
                QTreeWidget::branch:has-children:!has-siblings:closed,
                QTreeWidget::branch:closed:has-children:has-siblings {{
                    image: url(app/assets/css/branch-closed.svg);
                    width: 15px;
                    height: 15px;
                }}
                QTreeWidget::branch:open:has-children:!has-siblings,
                QTreeWidget::branch:open:has-children:has-siblings {{
                    image: url(app/assets/css/branch-open.svg);
                    width: 15px;
                    height: 15px;
                }}
                
                /* Style for folder and file display */
                QTreeWidget::item:has-children {{
                    font-weight: bold;
                }}
            """)
        
        # Add tree directly to info panel
        info_layout.addWidget(self.tree, 1)  # Give the tree a stretch factor of 1 to fill available space
        
        # Add status bar with structure statistics
        self.status_bar = QLabel("No items in structure")
        self.status_bar.setStyleSheet(f"color: {colors['secondary_text']}; font-style: italic; padding: 5px;")
        info_layout.addWidget(self.status_bar)
        
        # Connect tree signals to update status bar
        self.tree.model().rowsInserted.connect(self._update_structure_stats)
        self.tree.model().rowsRemoved.connect(self._update_structure_stats)
        
        # Add info panel to main layout
        main_layout.addWidget(info_panel)
        
        # Apply styling
        self._apply_styling()
        
        # Initial update of structure stats
        self._update_structure_stats()
        
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
        Show a context menu for the tree items
        
        Args:
            position: The position to show the menu
        """
        if not self.tree:
            return
            
        # Get selected items
        selected_items = self.tree.selectedItems()
        
        # Create menu
        menu = QMenu()
        
        # Determine if we have selected items
        if selected_items:
            # Add options for selected items
            add_file_action = QAction("Add File", self.editor)
            add_file_action.triggered.connect(lambda: self.editor.add_file(selected_items[0]))
            menu.addAction(add_file_action)
            
            add_folder_action = QAction("Add Folder", self.editor)
            add_folder_action.triggered.connect(lambda: self.editor.add_folder(selected_items[0]))
            menu.addAction(add_folder_action)
            
            menu.addSeparator()
            
            rename_action = QAction("Rename", self.editor)
            rename_action.triggered.connect(lambda: self._rename_item(selected_items[0]))
            menu.addAction(rename_action)
            
            menu.addSeparator()
            
            delete_action = QAction("Delete", self.editor)
            delete_action.triggered.connect(self.editor.delete_selected)
            menu.addAction(delete_action)
        else:
            # Add options for no selection (root level)
            add_file_action = QAction("Add File", self.editor)
            add_file_action.triggered.connect(lambda: self.editor.add_file())
            menu.addAction(add_file_action)
            
            add_folder_action = QAction("Add Folder", self.editor)
            add_folder_action.triggered.connect(lambda: self.editor.add_folder())
            menu.addAction(add_folder_action)
        
        # Show the menu
        menu.exec_(self.tree.mapToGlobal(position))
    
    def _rename_item(self, item):
        """
        Rename the selected item
        
        Args:
            item: The item to rename
        """
        if not item:
            return
            
        # Get the current name
        current_name = item.text(0)
        
        # Get a new name using input dialog
        new_name, ok = QInputDialog.getText(
            self.editor,
            "Rename Item",
            "Enter new name:",
            text=current_name
        )
        
        if ok and new_name:
            # Update the item text
            item.setText(0, new_name)
            
            # Update the item data
            item_data = item.data(0, Qt.UserRole)
            if isinstance(item_data, dict):
                item_data["name"] = new_name
                item.setData(0, Qt.UserRole, item_data)
    
    def _import_structure(self):
        """Import structure from file"""
        if hasattr(self.editor, "structure_converter"):
            # Get file path from dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self.editor,
                "Import Structure",
                os.path.expanduser("~"),
                "JSON Files (*.json);;All Files (*.*)"
            )
            
            if file_path:
                try:
                    # Load structure from file
                    with open(file_path, 'r') as f:
                        structure = json.load(f)
                    
                    # Load structure into tree
                    self.editor.structure_converter.load_structure(structure)
                    
                    # Show success message
                    QMessageBox.information(
                        self.editor,
                        "Import Successful",
                        "Structure imported successfully."
                    )
                except Exception as e:
                    # Show error message
                    QMessageBox.critical(
                        self.editor,
                        "Import Error",
                        f"Failed to import structure: {str(e)}"
                    )
    
    def _manage_structures(self):
        """Show dialog to manage structure presets"""
        try:
            # Import needed modules
            from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                      QPushButton, QListWidget, QMessageBox, QInputDialog)
            from PyQt5.QtCore import Qt
            
            # Create dialog
            dialog = QDialog(self.editor)
            dialog.setWindowTitle("Manage Structure Presets")
            dialog.resize(500, 400)
            
            # Create layout
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            # Add title
            title = QLabel("Structure Presets")
            title.setStyleSheet("font-size: 16px; font-weight: bold;")
            layout.addWidget(title)
            
            # Add description
            description = QLabel("Manage your saved structure presets.")
            description.setWordWrap(True)
            layout.addWidget(description)
            
            # Add list of structures
            structures_list = QListWidget()
            structures_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {colors['card_bg']};
                    color: {colors['text']};
                    border: 1px solid {colors['border']};
                    border-radius: 4px;
                    padding: 5px;
                }}
                QListWidget::item {{
                    padding: 8px;
                    border-bottom: 1px solid {colors['border']};
                }}
                QListWidget::item:selected {{
                    background-color: {colors['highlight_bg']};
                    color: {colors['highlight_text']};
                }}
                QListWidget::item:hover {{
                    background-color: {colors['hover_bg']};
                }}
            """)
            layout.addWidget(structures_list)
            
            # Populate list with available structures
            available_structures = self._get_available_structures()
            for structure in available_structures:
                structures_list.addItem(structure)
            
            # Add button row
            button_layout = QHBoxLayout()
            
            # Add rename button
            rename_btn = QPushButton("Rename")
            rename_btn.setStyleSheet(self._get_button_style())
            rename_btn.clicked.connect(lambda: self._rename_structure(structures_list, dialog))
            
            # Add delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet(self._get_button_style('danger'))
            delete_btn.clicked.connect(lambda: self._delete_structure(structures_list, dialog))
            
            # Add close button
            close_btn = QPushButton("Close")
            close_btn.setStyleSheet(self._get_button_style())
            close_btn.clicked.connect(dialog.accept)
            close_btn.setDefault(True)
            
            # Add buttons to layout
            button_layout.addWidget(rename_btn)
            button_layout.addWidget(delete_btn)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            # Show dialog
            dialog.exec_()
            
            # Refresh preset structures in combo box
            self._refresh_presets()
            
        except Exception as e:
            print(f"ERROR managing structures: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_available_structures(self):
        """Get list of available structure presets"""
        structures = []
        
        # Try to get structures from template manager
        try:
            from app.templates.template_manager import TemplateManager
            template_manager = TemplateManager()
            
            # Get all structures
            all_structures = []
            if hasattr(template_manager, 'get_structures'):
                all_structures = template_manager.get_structures()
            elif hasattr(template_manager, 'custom_structures'):
                all_structures = list(template_manager.custom_structures.keys())
            
            # Filter and clean structure names
            for structure_name in all_structures:
                if structure_name.startswith("Template_"):
                    display_name = structure_name[len("Template_"):]
                    structures.append(display_name)
                else:
                    structures.append(structure_name)
            
            print(f"DEBUG: Found {len(structures)} available structures")
        except Exception as e:
            print(f"ERROR getting structures: {e}")
            import traceback
            traceback.print_exc()
        
        return sorted(structures)
    
    def _rename_structure(self, list_widget, parent_dialog):
        """Rename selected structure"""
        # Get selected structure
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(parent_dialog, "Selection Required", "Please select a structure to rename")
            return
        
        # Get structure name
        structure_name = selected_items[0].text()
        
        # Ask for new name
        new_name, ok = QInputDialog.getText(
            parent_dialog, 
            "Rename Structure", 
            "Enter new name:",
            text=structure_name
        )
        
        if not ok or not new_name or new_name == structure_name:
            return
        
        # Rename structure in template manager
        try:
            from app.templates.template_manager import TemplateManager
            template_manager = TemplateManager()
            
            # Format names with Template_ prefix
            old_name = f"Template_{structure_name}"
            new_name_with_prefix = f"Template_{new_name}"
            
            # Perform rename
            success = False
            if hasattr(template_manager, 'rename_structure'):
                success = template_manager.rename_structure(old_name, new_name_with_prefix)
            elif hasattr(template_manager, 'rename_custom_structure'):
                success = template_manager.rename_custom_structure(old_name, new_name_with_prefix)
            
            if success:
                QMessageBox.information(parent_dialog, "Success", f"Structure renamed to '{new_name}'")
                
                # Update list
                selected_items[0].setText(new_name)
                
                # Update the predefined combo
                if hasattr(self, 'predefined_combo'):
                    # Save current selection
                    current_index = self.predefined_combo.currentIndex()
                    current_data = self.predefined_combo.currentData()
                    
                    # Update dropdown
                    self._refresh_presets()
                    
                    # Try to restore previous selection
                    if current_data:
                        index = self.predefined_combo.findData(current_data)
                        if index >= 0:
                            self.predefined_combo.setCurrentIndex(index)
            else:
                QMessageBox.warning(parent_dialog, "Error", f"Failed to rename structure")
        except Exception as e:
            QMessageBox.critical(parent_dialog, "Error", f"Error renaming structure: {str(e)}")
    
    def _delete_structure(self, list_widget, parent_dialog):
        """Delete selected structure"""
        # Get selected structure
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(parent_dialog, "Selection Required", "Please select a structure to delete")
            return
        
        # Get structure name
        structure_name = selected_items[0].text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            parent_dialog,
            "Confirm Deletion",
            f"Are you sure you want to delete the structure '{structure_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Delete structure in template manager
        try:
            from app.templates.template_manager import TemplateManager
            template_manager = TemplateManager()
            
            # Format name with Template_ prefix
            full_name = f"Template_{structure_name}"
            
            # Perform delete
            success = False
            if hasattr(template_manager, 'delete_structure'):
                success = template_manager.delete_structure(full_name)
            elif hasattr(template_manager, 'delete_custom_structure'):
                success = template_manager.delete_custom_structure(full_name)
            
            if success:
                QMessageBox.information(parent_dialog, "Success", f"Structure '{structure_name}' deleted")
                
                # Remove from list
                row = list_widget.row(selected_items[0])
                list_widget.takeItem(row)
                
                # Update the predefined combo
                if hasattr(self, 'predefined_combo'):
                    self._refresh_presets()
            else:
                QMessageBox.warning(parent_dialog, "Error", f"Failed to delete structure")
        except Exception as e:
            QMessageBox.critical(parent_dialog, "Error", f"Error deleting structure: {str(e)}")

    def _manage_categories(self):
        """Show dialog to manage template categories"""
        try:
            # Import the category manager
            from app.ui.structure_editor.category_manager import manage_categories
            
            # Show the dialog and get updated categories
            updated_categories = manage_categories(self.editor, self.categories)
            
            # Update the categories if dialog was not canceled
            if updated_categories:
                self.categories = updated_categories
                
                # Update the category dropdown
                if hasattr(self, 'template_category_field'):
                    # Save current selection
                    current = self.template_category_field.currentText()
                    
                    # Update dropdown
                    self.template_category_field.clear()
                    self.template_category_field.addItems(self.categories)
                    
                    # Try to restore current selection
                    index = self.template_category_field.findText(current)
                    if index >= 0:
                        self.template_category_field.setCurrentIndex(index)
                    else:
                        # Default to first item
                        self.template_category_field.setCurrentIndex(0)
                
                print("DEBUG: Categories updated")
                
        except Exception as e:
            print(f"ERROR managing categories: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_presets(self):
        """Refresh the preset structures from template manager"""
        try:
            # Skip if no preset combo exists
            if not hasattr(self, 'preset_combo') or not self.preset_combo:
                return
                
            # Clear existing items
            self.preset_combo.clear()
            
            # Add "Select a preset" option
            self.preset_combo.addItem("Select a preset...")
            
            # Import template manager to get structures
            try:
                from app.templates.template_manager import TemplateManager
                template_manager = TemplateManager()
                
                # Get all structures
                structures = []
                if hasattr(template_manager, 'get_structures'):
                    structures = template_manager.get_structures()
                elif hasattr(template_manager, 'custom_structures'):
                    structures = list(template_manager.custom_structures.keys())
                
                # Filter and sort structures
                presets = []
                for structure_name in structures:
                    # Skip non-template structures and current structure
                    if (not structure_name.startswith("Template_") or 
                        structure_name == f"Template_{self.structure_name}"):
                        continue
                    
                    # Add to presets list
                    display_name = structure_name
                    if structure_name.startswith("Template_"):
                        display_name = structure_name[len("Template_"):]
                        
                    presets.append((display_name, structure_name))
                
                # Sort by display name
                presets.sort(key=lambda x: x[0].lower())
                
                # Add to combo box
                for display_name, structure_name in presets:
                    self.preset_combo.addItem(display_name, structure_name)
                    
                print(f"DEBUG: Refreshed {len(presets)} preset structures")
            except Exception as e:
                print(f"ERROR refreshing presets: {e}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"ERROR in _refresh_presets: {e}")
            import traceback
            traceback.print_exc()
            
    def _load_predefined_structure(self, index):
        """Load a predefined structure from the dropdown"""
        try:
            # Get the structure identifier from the combo box
            structure_id = self.predefined_combo.currentData()
            
            if not structure_id:
                # Custom structure selected, do nothing
                return
            
            # Confirm if the user wants to replace the current structure
            reply = QMessageBox.question(
                self.editor,
                "Load Predefined Structure",
                "This will replace your current structure with a predefined template. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                # Reset combo to index 0 (Custom Structure)
                self.predefined_combo.setCurrentIndex(0)
                return
            
            # Load the predefined structure based on the identifier
            if structure_id == "basic":
                structure = [
                    {"type": "folder", "name": "src", "children": [
                        {"type": "file", "name": "main.py"},
                        {"type": "file", "name": "utils.py"}
                    ]},
                    {"type": "folder", "name": "docs", "children": [
                        {"type": "file", "name": "README.md"}
                    ]},
                    {"type": "file", "name": "config.json"}
                ]
            elif structure_id == "webapp":
                structure = [
                    {"type": "folder", "name": "src", "children": [
                        {"type": "folder", "name": "components", "children": [
                            {"type": "file", "name": "App.js"},
                            {"type": "file", "name": "Header.js"},
                            {"type": "file", "name": "Footer.js"}
                        ]},
                        {"type": "folder", "name": "styles", "children": [
                            {"type": "file", "name": "main.css"}
                        ]},
                        {"type": "file", "name": "index.js"}
                    ]},
                    {"type": "folder", "name": "public", "children": [
                        {"type": "file", "name": "index.html"},
                        {"type": "file", "name": "favicon.ico"}
                    ]},
                    {"type": "file", "name": "package.json"},
                    {"type": "file", "name": "README.md"}
                ]
            elif structure_id == "mobile":
                structure = [
                    {"type": "folder", "name": "app", "children": [
                        {"type": "folder", "name": "src", "children": [
                            {"type": "folder", "name": "screens", "children": [
                                {"type": "file", "name": "HomeScreen.js"},
                                {"type": "file", "name": "ProfileScreen.js"}
                            ]},
                            {"type": "folder", "name": "components", "children": [
                                {"type": "file", "name": "Button.js"},
                                {"type": "file", "name": "Card.js"}
                            ]},
                            {"type": "file", "name": "App.js"}
                        ]},
                        {"type": "folder", "name": "assets", "children": [
                            {"type": "file", "name": "logo.png"}
                        ]}
                    ]},
                    {"type": "file", "name": "package.json"},
                    {"type": "file", "name": "app.json"}
                ]
            elif structure_id == "docs":
                structure = [
                    {"type": "folder", "name": "docs", "children": [
                        {"type": "file", "name": "index.md"},
                        {"type": "file", "name": "getting-started.md"},
                        {"type": "file", "name": "api-reference.md"}
                    ]},
                    {"type": "folder", "name": "examples", "children": [
                        {"type": "file", "name": "basic.md"},
                        {"type": "file", "name": "advanced.md"}
                    ]},
                    {"type": "file", "name": "README.md"}
                ]
            elif structure_id == "library":
                structure = [
                    {"type": "folder", "name": "src", "children": [
                        {"type": "file", "name": "index.js"},
                        {"type": "file", "name": "core.js"}
                    ]},
                    {"type": "folder", "name": "tests", "children": [
                        {"type": "file", "name": "index.test.js"}
                    ]},
                    {"type": "folder", "name": "docs", "children": [
                        {"type": "file", "name": "API.md"}
                    ]},
                    {"type": "file", "name": "package.json"},
                    {"type": "file", "name": "LICENSE"},
                    {"type": "file", "name": "README.md"}
                ]
            else:
                # Unknown structure ID, reset to custom
                self.predefined_combo.setCurrentIndex(0)
                return
            
            # Load the structure into the editor - safely
            if hasattr(self.editor, 'structure_converter') and self.editor.structure_converter:
                try:
                    # Check if the tree widget is still valid
                    if hasattr(self.editor.structure_converter, 'tree') and self.editor.structure_converter.tree:
                        self.editor.structure_converter.load_structure(structure)
                        print(f"DEBUG: Loaded predefined structure: {structure_id}")
                    else:
                        print("ERROR: Tree widget no longer available")
                except Exception as e:
                    import traceback
                    print(f"ERROR loading structure: {e}")
                    traceback.print_exc()
            
            # Update template category based on structure type
            structure_categories = {
                "basic": "General",
                "webapp": "Web Development",
                "mobile": "Mobile",
                "docs": "Documentation",
                "library": "Development"
            }
            
            if structure_id in structure_categories:
                # Find the category index
                category = structure_categories[structure_id]
                index = self.template_category_field.findText(category)
                if index >= 0:
                    self.template_category_field.setCurrentIndex(index)
        
        except Exception as e:
            import traceback
            print(f"ERROR in _load_predefined_structure: {e}")
            traceback.print_exc()

    def _save_as_preset(self):
        """Save the current structure as a new preset"""
        # Get the current structure from the tree
        structure = None
        if hasattr(self.editor, 'structure_converter'):
            try:
                # Use get_structure method instead of create_structure_from_tree
                # This method has been tested and works properly with the current tree
                structure = self.editor.structure_converter.get_structure()
            except Exception as e:
                print(f"ERROR getting structure for preset: {e}")
                import traceback
                traceback.print_exc()
        
        if not structure:
            QMessageBox.warning(
                self.editor,
                "Save Preset",
                "No structure available to save as preset."
            )
            return
        
        # Prompt for preset name
        preset_name, ok = QInputDialog.getText(
            self.editor,
            "Save Preset",
            "Enter a name for this preset:"
        )
        
        if not ok or not preset_name:
            return
        
        # Prompt for preset category
        preset_category, ok = QInputDialog.getItem(
            self.editor,
            "Save Preset",
            "Select a category for this preset:",
            self.categories,
            0,
            False
        )
        
        if not ok:
            return
        
        # Save the preset using the structure manager
        try:
            # Find the parent application
            parent = self.editor
            while parent and not hasattr(parent, 'structure_manager'):
                parent = parent.parent()
            
            if parent and hasattr(parent, 'structure_manager'):
                success = parent.structure_manager.save_preset(
                    preset_name, 
                    structure, 
                    preset_category
                )
                
                if success:
                    QMessageBox.information(
                        self.editor,
                        "Save Preset",
                        f"Preset '{preset_name}' saved successfully."
                    )
                    
                    # Add the preset to the dropdown
                    self.predefined_combo.addItem(preset_name, preset_name)
                else:
                    QMessageBox.warning(
                        self.editor,
                        "Save Preset",
                        f"Failed to save preset '{preset_name}'."
                    )
            else:
                QMessageBox.warning(
                    self.editor,
                    "Save Preset",
                    "Structure manager not available."
                )
        except Exception as e:
            QMessageBox.critical(
                self.editor,
                "Save Preset",
                f"Error saving preset: {str(e)}"
            )
    
    def get_ui_values(self):
        """
        Get values from UI fields
        
        Returns:
            dict: Dictionary of UI values
        """
        try:
            values = {}
            
            # Get template name
            if self.template_name_field:
                template_name = self.template_name_field.text().strip()
                values['template_name'] = template_name
                print(f"DEBUG: get_ui_values template_name = '{template_name}'")
            
            # Get category
            if self.template_category_field:
                category = self.template_category_field.currentText()
                values['category'] = category
                print(f"DEBUG: get_ui_values category = '{category}'")
            
            # Get description
            if self.template_info_field:
                description = self.template_info_field.toPlainText().strip()
                values['description'] = description
            
            return values
        except Exception as e:
            print(f"ERROR getting UI values: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def update_ui_values(self, values):
        """
        Update UI fields with new values
        
        Args:
            values: Dictionary of values to update
        """
        try:
            # Update template name field
            if 'template_name' in values and self.template_name_field:
                # Handle Template_ prefix - remove it for display
                template_name = values['template_name']
                if template_name.startswith('Template_'):
                    template_name = template_name[9:]  # Remove Template_ prefix
                
                self.template_name_field.setText(template_name)
                print(f"DEBUG: Updated template name field to '{template_name}'")
            
            # Update category field
            if 'category' in values and self.template_category_field:
                category = values['category']
                index = self.template_category_field.findText(category)
                if index >= 0:
                    self.template_category_field.setCurrentIndex(index)
                    print(f"DEBUG: Updated category field to '{category}'")
            
            # Update description field
            if 'description' in values and self.template_info_field:
                self.template_info_field.setPlainText(values['description'])
                print(f"DEBUG: Updated description field")
            
        except Exception as e:
            print(f"ERROR updating UI values: {e}")
            import traceback
            traceback.print_exc()

    def set_ui_values(self, values):
        """
        Set values in UI fields
        
        Args:
            values: Dictionary containing values to set
        """
        # Set template name
        if self.template_name_field and 'template_name' in values:
            self.template_name_field.setText(values['template_name'])
            
        # Set template category
        if self.template_category_field and 'category' in values:
            index = self.template_category_field.findText(values['category'])
            if index >= 0:
                self.template_category_field.setCurrentIndex(index)
            
        # Set template info
        if self.template_info_field and 'description' in values:
            self.template_info_field.setPlainText(values['description'])
        
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
            self.status_bar.setText("No items in structure")
        else:
            self.status_bar.setText(f"Total: {total_items} items ({folders} folders, {files} files)") 