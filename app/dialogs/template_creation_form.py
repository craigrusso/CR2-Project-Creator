#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QLineEdit, QComboBox, QGridLayout,
                           QMessageBox, QFileDialog, QGroupBox, QTextEdit,
                           QFrame, QWidget, QTabWidget, QScrollArea, QFormLayout,
                           QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyle)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QFontMetrics, QColor, QStandardItemModel, QStandardItem
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, COMBOBOX_STYLE, ACCENT_BUTTON_STYLE
from app.templates.template_manager import TemplateManager
from app.templates.components import get_system_font, SYSTEM_FONT
from app.utils.template_validator import TemplateValidator
from PyQt6.QtWidgets import QApplication
from app.constants import get_resource_path, DEFAULT_TEMPLATE_CATEGORIES
from app.templates.category_update_manager import get_instance as get_category_update_manager_instance
from app.templates.category_combobox_updater import update_single_combobox

class TemplateCreationForm(QDialog):
    """
    Dialog for creating or editing a template.
    """
    
    # Signal emitted when template is created or edited
    template_created = pyqtSignal(dict)
    template_edited = pyqtSignal(dict)
    
    def __init__(self, parent=None, template=None, template_manager=None, callback=None):
        super().__init__(parent)
        self.setWindowTitle("Template Creator")
        self.resize(700, 800)
        self.template = template or {}
        self.template_manager = template_manager
        self.callback = callback
        self.is_editing = bool(template and template.get("name"))
        
        # Get the app instance from parent
        self.app = None
        if parent and hasattr(parent, 'app'):
            self.app = parent.app
        
        # Get the category update manager
        self.category_update_manager = get_category_update_manager_instance(self.app)
        
        # Track when the dialog was last updated
        self.last_category_update = 0
        
        # Set the window flags to make it modal
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set window title based on mode
        if self.is_editing:
            template_name = template.get("name", "Unknown")
            self.setWindowTitle(f"Edit Template: {template_name}")
        else:
            self.setWindowTitle("Create New Template")
        
        # Set up the UI
        self.init_ui()
        
        # Fill form with template data if editing
        if self.is_editing:
            self.load_template_data()
            
    def showEvent(self, event):
        """Override showEvent to refresh category combobox when dialog is shown"""
        super().showEvent(event)
        
        # Request an update from CategoryUpdateManager if available
        if hasattr(self, 'category_update_manager') and self.category_update_manager:
            print("[Template Form] Dialog shown - requesting CategoryUpdateManager refresh")
            self.category_update_manager.force_immediate_global_update()
        
        # Ensure type combo is populated with the latest categories
        if hasattr(self, 'type_combo'):
            print("[FIXED] Dialog shown - refreshing category combobox")
            self.populate_type_combo()
            
            # If editing, make sure the correct category is selected
            if self.is_editing:
                template_type = self.template.get("type", self.template.get("structure_type", ""))
                if template_type:
                    index = self.type_combo.findText(template_type)
                    if index >= 0:
                        self.type_combo.setCurrentIndex(index)
                        print(f"[FIXED] Restored selection to '{template_type}'")
        
        # Process events to ensure UI is updated
        QApplication.processEvents()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #333;
            }
            QTabBar::tab {
                background-color: #444;
                color: #ddd;
                padding: 8px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #555;
                color: white;
                border-top: 2px solid #2C4F76;
            }
            QTabBar::tab:hover:!selected {
                background-color: #505050;
            }
        """)
        
        # Create basic info tab
        self.basic_info_tab = QWidget()
        self.setup_basic_info_tab()
        self.tabs.addTab(self.basic_info_tab, "Basic Info")
        
        # Create files tab if editing
        if self.is_editing:
            self.files_tab = QWidget()
            self.setup_files_tab()
            self.tabs.addTab(self.files_tab, "Files")
            
            # Create structure tab
            self.structure_tab = QWidget()
            self.setup_structure_tab()
            self.tabs.addTab(self.structure_tab, "Structure")
            
        # Add tabs to main layout
        main_layout.addWidget(self.tabs)
        
        # Add buttons at the bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("Save Template")
        self.save_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.save_button.clicked.connect(self.save_template)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
    def setup_basic_info_tab(self):
        """Set up the basic info tab"""
        layout = QFormLayout(self.basic_info_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Template Name
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumHeight(30)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #444;
                color: white;
                selection-background-color: #666;
            }
            QLineEdit:focus {
                border: 1px solid #888;
            }
        """)
        
        # Project Type (formerly Category)
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("template_category_combo_box")  # Set object name for identification
        self.type_combo.setModel(QStandardItemModel(self.type_combo))  # Explicitly set QStandardItemModel
        self.type_combo.setMinimumHeight(30)
        
        # Add project types - FIXED: ensure we get the latest categories
        self.populate_type_combo()
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setMinimumHeight(100)
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #444;
                color: white;
                selection-background-color: #666;
            }
            QTextEdit:focus {
                border: 1px solid #888;
            }
        """)
        
        # Source file/folder
        self.path_layout = QHBoxLayout()
        
        self.path_edit = QLineEdit()
        self.path_edit.setMinimumHeight(30)
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background-color: #3a3a3a;
                color: #ccc;
            }
        """)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setStyleSheet(BUTTON_STYLE)
        self.browse_button.clicked.connect(self.browse_for_path)
        
        self.path_layout.addWidget(self.path_edit, 5)
        self.path_layout.addWidget(self.browse_button, 1)
        
        # Add fields to form layout
        layout.addRow("Template Name:", self.name_edit)
        layout.addRow("Project Type:", self.type_combo)
        layout.addRow("Description:", self.desc_edit)
        layout.addRow("Source File/Folder:", self.path_layout)
        
    def populate_type_combo(self):
        """Populate the type_combo (category) dropdown using the centralized updater."""
        log_prefix = "[TemplateForm PopulateTypeCombo]"
        print(f"{log_prefix} Populating category combobox (type_combo). ObjectName: {self.type_combo.objectName()}")

        categories = []
        if self.template_manager and hasattr(self.template_manager, 'get_categories'):
            categories = self.template_manager.get_categories()
            print(f"{log_prefix} Fetched {len(categories)} categories from template_manager: {categories}")
        else:
            categories = list(DEFAULT_TEMPLATE_CATEGORIES)
            print(f"{log_prefix} Using default categories: {categories}")

        # Ensure "No Category" is an option if not already present
        if "No Category" not in categories:
            categories.append("No Category")
            print(f"{log_prefix} Added 'No Category' to list.")
        
        current_selection = None
        if self.is_editing and self.template:
            # Prioritize 'category' field, then 'type', then 'structure_type' for backward compatibility
            current_selection = self.template.get("category", self.template.get("type", self.template.get("structure_type")))
            if not current_selection:
                 current_selection = "No Category" # Default if editing but no category saved
            print(f"{log_prefix} Editing mode. Current selection to restore: '{current_selection}'")
        elif not self.is_editing:
            current_selection = "No Category" # Default for new templates
            print(f"{log_prefix} New template mode. Default selection: '{current_selection}'")

        # Use the centralized function to update the combobox
        # This will handle model, items, selection, and styling (including hover delegate)
        update_single_combobox(self.type_combo, categories, current_category=current_selection, force_default_style=True)
        print(f"{log_prefix} Called update_single_combobox. Current text: {self.type_combo.currentText()}")

        # Verify that the model is QStandardItemModel after update
        if not isinstance(self.type_combo.model(), QStandardItemModel):
            print(f"{log_prefix} WARNING: Model is {type(self.type_combo.model())} NOT QStandardItemModel after update_single_combobox. This might break delegate styling.")
            # Force it again if necessary, though update_single_combobox should handle this
            # self.type_combo.setModel(QStandardItemModel(self.type_combo))
            # update_single_combobox(self.type_combo, categories, current_category=current_selection, force_default_style=True) # Re-populate if model was reset
        else:
            print(f"{log_prefix} Model is QStandardItemModel, as expected.")

        # Ensure item view has correct styling (delegate handles hover, but popup style might be global)
        # This is mostly handled by global theme and apply_hover_delegate in update_single_combobox
        # view = self.type_combo.view()
        # if view:
        #     view.setStyleSheet(LISTVIEW_POPUP_STYLE) # Example from color_scheme

    def browse_for_path(self):
        """Open file dialog to browse for source file or folder"""
        print("DEBUG: browse_for_path called")
        
        # Create file dialog
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)  # Allow selection of any file or folder
        dialog.setOptions(QFileDialog.DontUseNativeDialog | QFileDialog.ReadOnly)
        
        # Add button to select a directory
        dialog.setOption(QFileDialog.ShowDirsOnly, False)  # Show both files and directories
        
        # Show the dialog
        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                print(f"DEBUG: Selected path: {path}")
                self.path_edit.setText(path)
                
                # Auto-populate name field if empty
                if not self.name_edit.text():
                    import os
                    name = os.path.basename(path)
                    if os.path.isfile(path):
                        # Remove extension for files
                        name = os.path.splitext(name)[0]
                    # Convert underscores to spaces and capitalize words
                    name = name.replace("_", " ").title()
                    self.name_edit.setText(name)
                    print(f"DEBUG: Auto-populated name: {name}")
        
    def setup_files_tab(self):
        """Set up the files tab with tree view of template files"""
        layout = QVBoxLayout(self.files_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Instructions label
        instructions = QLabel("Template Files:")
        instructions.setFont(QFont(SYSTEM_FONT, 12))
        instructions.setStyleSheet("color: white;")
        layout.addWidget(instructions)
        
        # Tree widget for files
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Type", "Size"])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #555;
                background-color: #444;
                color: white;
                alternate-background-color: #505050;
                selection-background-color: #666;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #666;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
        """)
        
        # Add buttons for file operations
        button_layout = QHBoxLayout()
        
        self.add_file_button = QPushButton("Add Files...")
        self.add_file_button.setStyleSheet(BUTTON_STYLE)
        self.add_file_button.clicked.connect(self.add_files)
        
        self.remove_file_button = QPushButton("Remove Selected")
        self.remove_file_button.setStyleSheet(BUTTON_STYLE)
        self.remove_file_button.clicked.connect(self.remove_files)
        
        button_layout.addWidget(self.add_file_button)
        button_layout.addWidget(self.remove_file_button)
        button_layout.addStretch(1)
        
        layout.addWidget(self.file_tree)
        layout.addLayout(button_layout)
        
    def setup_structure_tab(self):
        """Set up the structure tab"""
        layout = QVBoxLayout(self.structure_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Instructions label
        instructions = QLabel("Template Structure:")
        instructions.setFont(QFont(SYSTEM_FONT, 12))
        instructions.setStyleSheet("color: white;")
        layout.addWidget(instructions)
        
        # Tree widget for structure
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels(["Name", "Type"])
        self.structure_tree.setAlternatingRowColors(True)
        self.structure_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #555;
                background-color: #444;
                color: white;
                alternate-background-color: #505050;
                selection-background-color: #666;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #666;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }
        """)
        
        # Add buttons for structure operations
        button_layout = QHBoxLayout()
        
        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.setStyleSheet(BUTTON_STYLE)
        self.add_folder_button.clicked.connect(self.add_folder)
        
        self.remove_struct_button = QPushButton("Remove Selected")
        self.remove_struct_button.setStyleSheet(BUTTON_STYLE)
        self.remove_struct_button.clicked.connect(self.remove_structure_item)
        
        button_layout.addWidget(self.add_folder_button)
        button_layout.addWidget(self.remove_struct_button)
        button_layout.addStretch(1)
        
        layout.addWidget(self.structure_tree)
        layout.addLayout(button_layout)
        
    def load_template_data(self):
        """Load existing template data into the form"""
        self.name_edit.setText(self.template.get("name", ""))
        
        # Handle template type/structure_type (formerly category)
        template_type = self.template.get("type", self.template.get("structure_type", ""))
        if template_type:
            index = self.type_combo.findText(template_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        
        self.desc_edit.setText(self.template.get("description", ""))
        self.path_edit.setText(self.template.get("path", self.template.get("file", "")))
        
        # Load files and structure if available
        if self.is_editing:
            self.load_files()
            self.load_structure()
        
    def save_template(self):
        """Save the template"""
        from app.utils.template_validator import TemplateValidator
        from PyQt6.QtWidgets import QMessageBox
        
        print("DEBUG: Starting save_template")
        
        # Get values from form
        name = self.name_edit.text().strip()
        project_type = self.type_combo.currentText()
        description = self.desc_edit.toPlainText().strip()
        path = self.path_edit.text()
        
        print(f"DEBUG: Initial values - name='{name}', type='{project_type}', path='{path}'")
        
        # Handle empty name before creating template data
        if not name:
            name = TemplateValidator.generate_default_name()
            print(f"DEBUG: Generated default name: {name}")
            QMessageBox.information(self, "Auto-generated Name", 
                                  f"No template name was provided. Your template will be saved as '{name}'.\n\n"
                                  "You can rename it later from the template gallery.")
            self.name_edit.setText(name)
            # Force UI update
            QApplication.processEvents()
        
        # Create template data
        template = {
            "name": name,
            "type": project_type,
            "description": description,
            "path": path
        }
        
        # Get structured files if editing
        if self.is_editing and hasattr(self, 'structure_tree'):
            structure = self.get_structure_from_tree()
            template["structure"] = structure
            
        # Set uuid if editing
        if self.is_editing and "uuid" in self.template:
            template["uuid"] = self.template["uuid"]
        
        # Set created timestamp if editing
        if self.is_editing and "created" in self.template:
            template["created"] = self.template["created"]
        
        print(f"DEBUG: Template data before save: {template}")
        
        # Save template through template manager
        success = False
        try:
            if self.is_editing:
                print("DEBUG: Updating existing template")
                # Update existing template
                if hasattr(self.template_manager, 'update_template'):
                    success = self.template_manager.update_template(template)
                else:
                    # Fallback to save_template
                    success = self.template_manager.save_template(
                        name,
                        path,
                        project_type,
                        description
                    )
            else:
                print("DEBUG: Creating new template")
                # Create new template
                success = self.template_manager.save_template(
                    name,
                    path,
                    project_type,
                    description
                )
                
            print(f"DEBUG: Save result - success={success}")
            
            if success:
                if self.callback:
                    print("DEBUG: Calling callback")
                    self.callback(template)
                
                if self.is_editing:
                    print("DEBUG: Emitting template_edited signal")
                    self.template_edited.emit(template)
                else:
                    print("DEBUG: Emitting template_created signal")
                    self.template_created.emit(template)
                    
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save the template. Please try again.")
        except Exception as e:
            print(f"ERROR saving template: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save the template: {str(e)}")

    def focusInEvent(self, event):
        """Override focusInEvent to refresh category combobox when dialog regains focus"""
        super().focusInEvent(event)
        
        # Get current time to check if it's been a while since last update
        import time
        current_time = time.time()
        
        # If it's been more than 0.5 seconds since last update, refresh
        if current_time - self.last_category_update > 0.5:
            print("[Template Form] Dialog gained focus - refreshing categories")
            
            # Use the populate_type_combo method to ensure proper formatting
            if hasattr(self, 'type_combo'):
                self.populate_type_combo()
            
            # Update timestamp
            self.last_category_update = current_time
        
        # Process events to ensure UI is updated
        QApplication.processEvents()

    def get_structure_from_tree(self):
        """Extract structure data from the tree widget"""
        if not hasattr(self, 'structure_tree'):
            return []
        
        structure = []
        root = self.structure_tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            item = root.child(i)
            structure.append(self._build_structure_from_item(item))
        
        return structure
    
    def _build_structure_from_item(self, item):
        """Build structure dictionary from a tree item"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        # Create clean structure dictionary
        structure_dict = {
            'name': item.text(0),
            'type': 'folder' if item.childCount() > 0 else 'file'
        }
        
        # Copy only essential data, avoiding nested user_data
        essential_keys = [
            'original_path', 'path', 'rename_flag', 'uses_project_name',
            'is_binary', 'pattern', 'separator', 'custom_separator',
            'date_format_text', 'time_format_text', 'uses_custom_pattern'
        ]
        
        for key in essential_keys:
            if key in item_data and key != 'user_data':
                structure_dict[key] = item_data[key]
        
        # Handle children for folders
        if item.childCount() > 0:
            children = []
            for i in range(item.childCount()):
                child = item.child(i)
                children.append(self._build_structure_from_item(child))
            structure_dict['children'] = children
        
        return structure_dict
    
    def load_files(self):
        """Load files from template data"""
        # This method would populate the files tab if it exists
        # For now, it's a placeholder to prevent AttributeError
        pass
    
    def load_structure(self):
        """Load structure from template data into the tree widget"""
        if not hasattr(self, 'structure_tree') or not self.template:
            return
        
        structure = self.template.get('structure', [])
        if not structure:
            return
        
        self.structure_tree.clear()
        
        for item_data in structure:
            self._add_structure_item_to_tree(item_data, self.structure_tree.invisibleRootItem())
        
        self.structure_tree.expandAll()
    
    def _add_structure_item_to_tree(self, item_data, parent_item):
        """Add a structure item to the tree widget"""
        if not isinstance(item_data, dict):
            return
        
        name = item_data.get('name', 'Unknown')
        item = QTreeWidgetItem([name, item_data.get('type', 'file')])
        
        # Store clean data without nested user_data
        clean_data = {}
        for key, value in item_data.items():
            if key not in ['children', 'user_data'] and not isinstance(value, dict) or key in ['custom_options']:
                clean_data[key] = value
        
        item.setData(0, Qt.ItemDataRole.UserRole, clean_data)
        
        if parent_item == self.structure_tree.invisibleRootItem():
            self.structure_tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        
        # Add children if they exist
        children = item_data.get('children', [])
        for child_data in children:
            self._add_structure_item_to_tree(child_data, item)
    
    def add_folder(self):
        """Add a new folder to the structure tree"""
        if not hasattr(self, 'structure_tree'):
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        folder_name, ok = QInputDialog.getText(self, 'Add Folder', 'Enter folder name:')
        if ok and folder_name.strip():
            item = QTreeWidgetItem([folder_name.strip(), 'folder'])
            item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'folder'})
            
            # Add to selected item or root
            selected_items = self.structure_tree.selectedItems()
            if selected_items:
                parent = selected_items[0]
                # If selected item is a file, add to its parent
                if parent.childCount() == 0 and parent.parent():
                    parent = parent.parent()
                parent.addChild(item)
                parent.setExpanded(True)
            else:
                self.structure_tree.addTopLevelItem(item)
    
    def remove_structure_item(self):
        """Remove selected item from structure tree"""
        if not hasattr(self, 'structure_tree'):
            return
        
        selected_items = self.structure_tree.selectedItems()
        for item in selected_items:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.structure_tree.indexOfTopLevelItem(item)
                if index >= 0:
                    self.structure_tree.takeTopLevelItem(index)

def show_template_creation_form(parent):
    """Show the enhanced template creation form"""
    dialog = TemplateCreationForm(parent)
    return dialog.exec() 