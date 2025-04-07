#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QDesktopWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QComboBox, \
     QPushButton, QLineEdit, QFrame, QGridLayout, QMessageBox, QApplication, QSizePolicy, QTabWidget, QMainWindow, QDockWidget, QToolButton, QButtonGroup, QMenu, QAction, QShortcut, QInputDialog, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QPoint, QModelIndex, QItemSelectionModel
from PyQt5.QtGui import QKeySequence, QDrag, QPixmap, QPainter, QColor, QPalette
import re

# Import modular components
from .gallery_ui_setup import GalleryUISetup
from .gallery_folders import GalleryFoldersSetup
from .gallery_templates import GalleryTemplatesSetup
from .gallery_events import GalleryEvents
from app.core.import_export_manager import import_template
from app.ui.views.template_table_view import TemplateTableView
from app.templates.components.template_card import TemplateCard
from app.templates.components.template_folder_card import TemplateFolderCard
from app.templates.components.template_folder_list_item import TemplateFolderListItem
from app.templates.components.menu_actions import ContextMenu  # Import ContextMenu for context menus

class TemplateGallery(QWidget):
    """Main widget for displaying and managing templates"""
    
    template_selected = pyqtSignal(dict)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.parent = parent
        self.template_manager = app.template_manager if app else None
        
        # UI state tracking
        self.current_category = "All"
        self.current_folder = None
        self.current_search = ""
        self.selected_template = None
        self.selected_folder = None
        self.folder_cards = []
        self.template_cards = []
        self.multi_selected_templates = []  # Track multi-selected templates
        self.icon_scale = 100  # Default scale in percentage
        self.folder_view_mode = "grid"  # Default to grid view for folders
        self.view_mode = "grid"  # Default to grid view for templates
        self.templates_loaded = False  # Track if templates have been loaded
        
        # Add placeholder for table view instance (will be created in setup_ui)
        self.template_table_view = None
        
        # Set minimum size to ensure all UI elements are visible
        self.setMinimumSize(800, 400)
        
        # Configure size policy to always expand
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Initialize grid layouts to avoid AttributeError
        self.folders_grid = None
        self.templates_grid = None
        
        # Resize handling
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(200)  # 200ms debounce
        self.resize_timer.timeout.connect(self._handle_resize_timeout)
        
        # Set up the UI
        GalleryUISetup.setup_ui(self)
        
        # --- Connect Table View Signals --- 
        if self.template_table_view:
            print("DEBUG: Connecting TemplateTableView signals...")
            self.template_table_view.clicked.connect(self._on_table_item_clicked)
            self.template_table_view.doubleClicked.connect(self._on_table_item_double_clicked)
            self.template_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.template_table_view.customContextMenuRequested.connect(self._show_table_context_menu)
            self.template_table_view.horizontalHeader().sectionClicked.connect(self._on_table_header_clicked)
            self.template_table_view.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
        else:
            print("[ERROR] TemplateTableView instance not found after UI setup!")
        # ---------------------------------
        
        # Set up the main gallery context menu (for blank space)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_gallery_context_menu)
        
        # Populate the gallery initially - do this after UI setup and signal connection
        self.populate_gallery()
        self._setup_shortcuts()
    
    # Gallery population methods
    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates based on current filters"""
        if not self.template_manager:
            print("No template manager available")
            return
            
        # Skip if already loaded unless forced
        # Commenting this out temporarily to ensure refresh happens for testing
        # if self.templates_loaded and not force_refresh:
        #     return
        
        # Explicitly reload templates from disk right before populating
        # This guarantees we have the latest data, even if less efficient
        print(f"[DEBUG] Gallery: Forcing template reload before populating...")
        try:
            # Check for template_io within template_manager and call its load_templates
            if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'template_io') and hasattr(self.app.template_manager.template_io, 'load_templates'):
                self.app.template_manager.template_io.load_templates() # Corrected call
                print(f"[DEBUG] Gallery: Templates reloaded via template_io.")
            else:
                print(f"[WARNING] Gallery: Cannot reload templates - template_manager.template_io or template_io.load_templates missing.")
        except Exception as e:
            print(f"[ERROR] Gallery: Failed during explicit template reload: {e}")
            
        # Always reset multi-selection when refreshing gallery
        self.multi_selected_templates = []
        
        # Clear existing UI
        self.clear_gallery()
        
        # Check if we have a template_manager attribute in the app
        if hasattr(self, 'template_manager'):
            # Use template_manager if available
            # Always fetch fresh templates using the getter method
            print(f"[DEBUG] Gallery: Fetching templates using get_all_templates()...")
            if hasattr(self.app.template_manager, 'get_all_templates'):
                templates_list = self.app.template_manager.get_all_templates() # Use getter method
                print(f"[DEBUG] Gallery (Populate): Received {len(templates_list)} templates from get_all_templates(). Names: {[t.get('name', 'N/A') for t in templates_list if isinstance(t, dict)]}")
                # Convert list to dict for processing, ensuring no duplicates overwrite
                templates = {}
                for t in templates_list:
                    if isinstance(t, dict) and 'name' in t:
                        if t['name'] not in templates:
                            templates[t['name']] = t
                        else:
                             print(f"[WARNING] Gallery: Duplicate template name '{t['name']}' found during fetch. Skipping.")
                    else:
                         print(f"[WARNING] Gallery: Invalid template format found: {t}")
                print(f"[DEBUG] Gallery: Fetched {len(templates)} unique templates.")
            else:
                print("[WARNING] Gallery: template_manager missing get_all_templates method. Falling back.")
                templates = getattr(self.app.template_manager, 'templates', {}) # Fallback
                if isinstance(templates, list): # Handle list fallback
                    temp_dict = {}
                    for t in templates:
                         if isinstance(t, dict) and 'name' in t:
                              if t['name'] not in temp_dict:
                                   temp_dict[t['name']] = t
                         else:
                              print(f"[WARNING] Gallery: Invalid template format found in fallback list: {t}")
                    templates = temp_dict

            if hasattr(self.app.template_manager, 'get_folders'):
                folders = self.app.template_manager.get_folders()
            else:
                folders = []
            
            # Set visibility based on current context
            if self.current_folder:
                # Inside a folder - hide folders section, show only templates
                self.folders_section.setVisible(False)
                self.templates_section.setVisible(True)
                
                # Show folder navigation with back button
                if hasattr(self, 'folder_nav'):
                    self.folder_nav.setVisible(True)
                    
                # Ensure back button is visible
                if hasattr(self, 'back_button'):
                    self.back_button.setVisible(True)
                    print(f"🔍 LISTENER: Ensuring back button is visible in populate_gallery for folder '{self.current_folder}'")
                
                # Set the folder label text
                if hasattr(self, 'folder_label'):
                    self.folder_label.setText(f"Folder: {self.current_folder}")
                    self.folder_label.show()
                
                # Get templates in the current folder
                templates_to_show = GalleryTemplatesSetup.get_templates_in_folder(self, self.current_folder)
                
                # Populate templates section
                if self.view_mode == "grid":
                    GalleryTemplatesSetup.populate_templates_grid(self, templates_to_show)
                else:  # list mode
                    GalleryTemplatesSetup.populate_templates_list(self, templates_to_show)
            else:
                # Not in a folder - show both folders and templates
                self.folders_section.setVisible(True)
                self.templates_section.setVisible(True)
                
                # Hide folder navigation when at root
                if hasattr(self, 'folder_nav'):
                    self.folder_nav.setVisible(False)
                
                # Hide back button when at root
                if hasattr(self, 'back_button'):
                    self.back_button.setVisible(False)
                
                # Convert list templates to dict if needed
                templates_dict = {}
                if isinstance(templates, list):
                    for i, template in enumerate(templates):
                        if isinstance(template, dict) and 'name' in template:
                            templates_dict[template['name']] = template
                        else:
                            templates_dict[f"Template-{i}"] = template
                else:
                    templates_dict = templates
                
                # Get all templates that are in folders so we can exclude them from main view
                templates_in_folders = set()
                if hasattr(self.app.template_manager, 'folders'):
                    # Gather all template names that are in any folder
                    for folder_name, folder_templates in self.app.template_manager.folders.items():
                        templates_in_folders.update(folder_templates)
                
                # Filter templates by category and search
                templates_to_show = {}
                
                for name, data in templates_dict.items():
                    # Skip templates that are in folders
                    if name in templates_in_folders:
                        continue
                    
                    if self.current_category != "All" and isinstance(data, dict) and "category" in data:
                        # Apply category filter
                        if data["category"] != self.current_category:
                            continue
                    
                    # Apply search filter if there's a search term
                    if self.current_search:
                        search_term = self.current_search.lower()
                        display_name = data.get('name', name).lower() if isinstance(data, dict) else name.lower()
                        description = data.get('description', '').lower() if isinstance(data, dict) else ''
                        category = data.get('category', '').lower() if isinstance(data, dict) else ''
                        
                        # Search in name, description and category
                        if (search_term not in display_name and 
                            search_term not in description and 
                            search_term not in category):
                            continue
                    
                    # Add template to the results
                    templates_to_show[name] = data
                
                # Only populate folders if we're showing all categories or there's no search
                if self.current_category == "All" and not self.current_search:
                    # Populate folders section based on view mode
                    if self.folder_view_mode == "grid":
                        GalleryFoldersSetup.populate_folders_grid(self, folders)
                    else:  # list mode
                        GalleryFoldersSetup.populate_folders_list(self, folders)
                else:
                    # Hide folders section when filtering
                    self.folders_section.setVisible(False)
                
                # Populate templates section based on view mode
                if self.view_mode == "grid":
                    GalleryTemplatesSetup.populate_templates_grid(self, templates_to_show)
                else:  # list mode
                    GalleryTemplatesSetup.populate_templates_list(self, templates_to_show)
            
            # Update template card sizes
            self._update_card_sizes()
            
            # Update button states after populating
            self._update_button_state()
            
            # Mark as loaded
            self.templates_loaded = True
            
            # Force immediate UI refresh for both containers
            if hasattr(self, 'folders_section'):
                self.folders_section.update()
                self.folders_section.repaint()
                
            if hasattr(self, 'templates_section'):
                self.templates_section.update()
                self.templates_section.repaint()
                
            # Process events to make UI updates visible immediately
            QApplication.processEvents()

            # --- Connect signals from gallery side AFTER population ---
            # This block should only run AFTER the grid/table population logic above

            # --- Re-add Connection block ---
            for card in self.template_cards:
                card_name = card.template_name()
                if card_name:
                    pass
                # Connect directly to the main handler
                card.duplicate_requested.connect(self._on_duplicate_template)
                print(f"[DEBUG GALLERY CONNECT] Connected duplicate_requested for card '{card_name}'")
            # --- END Re-add Connection block ---

            # --- NEW: Explicitly select in List View --- 
            if self.view_mode == "list" and templates_to_show:
                 try:
                     model = self.template_table_view.model()
                     if model:
                         for row in range(model.rowCount()):
                             index = model.index(row, 0) # Assuming name is in column 0
                             item_data = model.data(index, Qt.UserRole) # Get the underlying template data
                             if isinstance(item_data, dict) and item_data.get('name') in templates_to_show:
                                 print(f"[DEBUG] Gallery: Found new template '{item_data['name']}' at row {row} in table view")
                                 # Clear existing selection and select the new row
                                 self.template_table_view.clearSelection()
                                 selection_model = self.template_table_view.selectionModel()
                                 if selection_model:
                                     selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                                     selection_model.setCurrentIndex(index, QItemSelectionModel.SelectCurrent)
                                     self.template_table_view.scrollTo(index) # Ensure it's visible
                                     print(f"[DEBUG] Gallery: Selected row {row} in table view for '{item_data['name']}'")
                                 break # Stop searching once found
                     else:
                         print("[WARNING] Gallery: Could not get table model to select new template.")
                 except Exception as e:
                     print(f"[ERROR] Gallery: Error selecting new template in table view: {e}")
            # --- END NEW LIST VIEW SELECTION --- 

    def clear_gallery(self):
        """Clear the gallery view"""
        # Clear templates section
        if hasattr(self, 'templates_grid'):
            try:
                # Check if the grid is valid (not deleted) by calling count()
                count = self.templates_grid.count()
                for i in range(count-1, -1, -1):  # Loop backwards to avoid index issues
                    item = self.templates_grid.takeAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        widget.setParent(None)
                        widget.deleteLater()
            except (RuntimeError, AttributeError):
                # Handle case where grid has been deleted
                pass
        
        # Clear folders section - be more careful checking for valid grid
        if hasattr(self, 'folders_grid'):
            try:
                # Check if the grid is valid (not deleted) by calling count()
                count = self.folders_grid.count()
                for i in range(count-1, -1, -1):  # Loop backwards to avoid index issues
                    item = self.folders_grid.takeAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        widget.setParent(None)
                        widget.deleteLater()
            except (RuntimeError, AttributeError):
                # Handle case where grid has been deleted
                pass
        
        # Reset arrays
        self.folder_cards = []
        self.template_cards = []
    
    # Event handlers - connect to the modular handlers
    def _on_category_select(self, category):
        GalleryEvents.on_category_select(self, category)
    
    def _on_search(self, search_text):
        GalleryEvents.on_search(self, search_text)
    
    def _on_template_select(self, template):
        """Handle template selection by delegating to GalleryEvents"""
        GalleryEvents.on_template_select(self, template)
        
    def on_template_multi_select(self, template, add_to_selection):
        """Handle multi-selection of templates"""
        template_name = template.get('name', 'Unknown')
        
        print(f"🔍 LISTENER: Multi-select request for '{template_name}', add_to_selection: {add_to_selection}")
        print(f"🔍 LISTENER: Current multi-selected templates: {[t.get('name', 'Unknown') for t in self.multi_selected_templates]}")
        
        # Ensure the multi_selected_templates list exists
        if not hasattr(self, 'multi_selected_templates'):
            self.multi_selected_templates = []
            
        # Also ensure we have a selected_template property
        if not hasattr(self, 'selected_template'):
            self.selected_template = None
        
        # Set multi-selecting mode flag
        self.is_multi_selecting = True
        
        # If we have a previously selected template and multi-selection is empty,
        # always add the previous selection to multi-selection list (just like grid view)
        if add_to_selection and self.selected_template and len(self.multi_selected_templates) == 0:
            # Add previous selection to multi-selection list 
            if self.selected_template not in self.multi_selected_templates:
                self.multi_selected_templates.append(self.selected_template)
                print(f"🔍 LISTENER: Adding previous primary selection to multi-selection")
        
        # Use add_to_selection parameter to determine action instead of always toggling
        if add_to_selection:
            # Add to selection if not already there
            if template not in self.multi_selected_templates:
                self.multi_selected_templates.append(template)
                print(f"🔍 LISTENER: Added template '{template_name}' to multi-selection")
            
                # Update card styling to show selected state
                for card in self.template_cards:
                    if hasattr(card, 'template') and card.template == template and hasattr(card, 'set_selected'):
                        card.set_selected(True)
        else:
            # Remove from selection if present
            if template in self.multi_selected_templates:
                self.multi_selected_templates.remove(template)
                print(f"🔍 LISTENER: Removed template '{template_name}' from multi-selection")
                
                # Update card styling to show unselected state (unless it's the primary selection)
                is_primary = (hasattr(self, 'selected_template') and self.selected_template == template)
                for card in self.template_cards:
                    if hasattr(card, 'template') and card.template == template and hasattr(card, 'set_selected'):
                        card.set_selected(is_primary)
        
        # Set this template as the primary selection
        self.selected_template = template
        print(f"🔍 LISTENER: Setting '{template_name}' as primary selection")
        
        # Update template item map for list view
        if hasattr(self, 'template_item_map') and self.template_item_map:
            # Update all list items to ensure consistent UI state
            for item_name, list_item in self.template_item_map.items():
                if not list_item or not hasattr(list_item, 'template'):
                    continue
                    
                is_selected = list_item.template == self.selected_template
                is_multi_selected = list_item.template in self.multi_selected_templates
                
                # Update selection states
                if hasattr(list_item, 'setSelected'):
                    list_item.setSelected(is_selected)
                
                if hasattr(list_item, 'setMultiSelected'):
                    list_item.setMultiSelected(is_multi_selected)
        
        # Update multi-selection styling for all cards
        for card in self.template_cards:
            if hasattr(card, 'template') and hasattr(card, 'set_multi_selected'):
                is_multi = card.template in self.multi_selected_templates
                card.set_multi_selected(is_multi)
                
        print(f"🔍 LISTENER: Final multi-selected templates: {[t.get('name', 'Unknown') for t in self.multi_selected_templates]}")
    
    def _clear_multi_selection(self):
        """Clear all multi-selected templates"""
        if hasattr(self, 'multi_selected_templates'):
            print(f"🔍 LISTENER: Clearing {len(self.multi_selected_templates)} multi-selected templates")
            
            # Update styling for previously multi-selected items
            for card in self.template_cards:
                if hasattr(card, 'template') and card.template in self.multi_selected_templates and hasattr(card, 'set_multi_selected'):
                    card.set_multi_selected(False)
            
            # Clear the list
            self.multi_selected_templates = []
    
    def _delete_selected_templates(self):
        """Delete all selected templates"""
        if not self.multi_selected_templates:
            return
            
        # Get template names
        template_names = [t.get('name', 'Unknown') for t in self.multi_selected_templates]
        
        # Confirm deletion
        from PyQt5.QtWidgets import QMessageBox
        confirm = QMessageBox.question(
            self,
            "Delete Templates",
            f"Are you sure you want to delete {len(template_names)} selected templates?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete each template
            from app.templates.gallery_events import GalleryEvents
            for template_name in template_names:
                GalleryEvents.on_delete_template(self, template_name)
                
            # Show success message
            if hasattr(self.app, 'show_status_message'):
                self.app.show_status_message(f"Deleted {len(template_names)} templates", "success")
                
            # Clear multi-selection
            self._clear_multi_selection()
            
            # Refresh gallery
            self.populate_gallery(force_refresh=True)
    
    def _on_folder_select(self, folder_name):
        GalleryEvents.on_folder_select(self, folder_name)
    
    def _on_folder_enter(self, folder_name):
        print(f"🔍 LISTENER: Entering folder '{folder_name}'")
        GalleryEvents.on_folder_enter(self, folder_name)
    
    def _on_back_to_all(self):
        print(f"🔍 LISTENER: Navigating back to all folders/templates from folder '{self.current_folder}'")
        GalleryEvents.on_back_to_all(self)
    
    def _on_add_template(self):
        GalleryEvents.on_add_template(self)
    
    def _on_edit_template(self, template_name=None):
        GalleryEvents.on_edit_template(self, template_name)
    
    def _on_delete_template(self, template_name=None):
        GalleryEvents.on_delete_template(self, template_name)
    
    def _on_manage_templates(self):
        """Handle manage templates button click
        
        Note: The "Manage All" button has been removed from the UI as its functionality
        is redundant with other UI elements, but this method is kept for programmatic use
        or in case it's called from elsewhere in the codebase.
        """
        GalleryEvents.on_manage_templates(self)
    
    def _on_add_folder(self):
        GalleryEvents.on_add_folder(self)
    
    def _on_rename_folder(self):
        GalleryEvents.on_rename_folder(self)
    
    def _on_rename_folder_requested(self, folder_name):
        GalleryEvents.on_rename_folder_requested(self, folder_name)
    
    def _on_rename_folder_done(self, old_name, new_name):
        GalleryEvents.on_rename_folder_done(self, old_name, new_name)
    
    def _on_delete_folder(self):
        """Handle delete folder button click"""
        GalleryEvents.on_delete_folder(self)
    
    def _on_structure_editor(self, template_name=None):
        """Handle structure editor button click
        
        Args:
            template_name: Optional name of the template to edit structure for
        """
        # Get the parent app if available
        parent_app = None
        if hasattr(self, 'app') and self.app is not None:
            parent_app = self.app
        elif hasattr(self, 'parent') and callable(self.parent) and self.parent() is not None:
            parent_app = self.parent()
        
        if parent_app is not None:
            # Create a custom implementation of show_enhanced_structure_editor
            # that handles missing template_manager
            from app.constants import DEFAULT_STRUCTURES
            from app.ui.structure_editor_enhanced import EnhancedStructureEditor
            
            # Create a modified editor with fallback for template_manager
            class EnhancedStructureEditorWithFallback(EnhancedStructureEditor):
                def __init__(self, parent, **kwargs):
                    # First ensure the parent has a template_manager attribute
                    if not hasattr(parent, 'template_manager') or parent.template_manager is None:
                        print("EnhancedStructureEditorWithFallback: Creating basic template manager")
                        
                        class BasicTemplateManager:
                            def __init__(self):
                                self.custom_structures = {}
                            
                            def get_structure(self, name):
                                print(f"BasicTemplateManager: Get structure called for {name}")
                                # Look for built-in structures
                                DEFAULT_STRUCTURES = {
                                    "Empty": [],
                                    "Basic": [
                                        {"type": "folder", "name": "src", "children": [
                                            {"type": "file", "name": "main.py"}
                                        ]},
                                        {"type": "file", "name": "README.md"}
                                    ]
                                }
                                
                                # Try to find the structure in our defaults
                                name_lower = name.lower() if name else ""
                                for key in DEFAULT_STRUCTURES:
                                    if key.lower() == name_lower:
                                        print(f"BasicTemplateManager: Found built-in structure: {key}")
                                        return DEFAULT_STRUCTURES[key]
                                
                                # Look in our stored custom structures
                                if name in self.custom_structures:
                                    print(f"BasicTemplateManager: Found stored structure: {name}")
                                    return self.custom_structures[name]
                                
                                print(f"BasicTemplateManager: Structure not found: {name}")
                                return []
                            
                            def save_custom_structure(self, name, structure, category="General"):
                                """Save a custom structure in memory (doesn't persist to disk)"""
                                print(f"BasicTemplateManager: Saving structure {name} with {len(structure)} items")
                                self.custom_structures[name] = structure
                                return True
                            
                            def get_categories(self):
                                """Return available categories"""
                                return ["General", "Custom", "Web Development", "Motion Graphics", "Video Editing", "VFX"]
                        
                        parent.template_manager = BasicTemplateManager()
                    
                    # Call the original constructor
                    super().__init__(parent, **kwargs)
                    
                    # Store the parent's template manager in the editor
                    self.template_manager = parent.template_manager
                
                def accept(self):
                    """Override accept to ensure template_manager is available"""
                    try:
                        # Ensure template_manager is accessible in the parent class accept method
                        print("[DEBUG] EnhancedStructureEditorWithFallback.accept: Ensuring template_manager is available")
                        
                        if not hasattr(self, 'template_manager') or self.template_manager is None:
                            print("[DEBUG] EnhancedStructureEditorWithFallback.accept: template_manager not found, getting from parent")
                            if hasattr(self.parent(), 'template_manager'):
                                self.template_manager = self.parent().template_manager
                        
                        # Call parent class accept method
                        super().accept()
                        
                    except AttributeError as e:
                        if "Template manager instance is not available" in str(e):
                            # Show a user-friendly message
                            QMessageBox.warning(self, "Save Error", 
                                "Cannot save structure: Template manager is not available. Changes will be lost.")
                            
                            print("[ERROR] Failed to save structure: Template manager instance is not available.")
                            # Just close the dialog without saving
                            super(EnhancedStructureEditor, self).accept()
                        else:
                            # Re-raise any other AttributeError
                            raise e
            
            # Load the structure if template_name is provided
            structure_name = None
            structure = []
            is_new = True
            
            if template_name:
                # Get the structure for the specified template
                if hasattr(parent_app, 'template_manager'):
                    template_manager = parent_app.template_manager
                    if hasattr(template_manager, 'get_structure'):
                        # Try variations of structure names
                        structure_name = f"Template_{template_name}"
                        structure = template_manager.get_structure(structure_name)
                        
                        # If not found, try with _ in place of spaces
                        if not structure and ' ' in template_name:
                            underscore_name = template_name.replace(' ', '_')
                            structure_name = f"Template_{underscore_name}"
                            structure = template_manager.get_structure(structure_name)
                        
                        if structure:
                            print(f"Found structure for template: {template_name}")
                            is_new = False
            
            # Create and show the editor
            editor = EnhancedStructureEditorWithFallback(
                parent_app,
                structure_name=structure_name,
                is_new=is_new,
                project_type=None,
                structure=structure,
                template_name=template_name
            )
            editor.exec_()
        else:
            QMessageBox.warning(self, "Error", "Could not access application context.")
    
    def _on_icon_scale_changed(self, value):
        GalleryEvents.on_icon_scale_changed(self, value)

    # View mode setters
    def _set_folder_view_mode(self, mode):
        GalleryFoldersSetup.set_folder_view_mode(self, mode)
    
    def _set_template_view_mode(self, mode):
        """Set template view mode between grid and list"""
        # Set the mode using the gallery setup helper
        GalleryTemplatesSetup.set_template_view_mode(self, mode)
        
        # Force refresh the gallery to ensure proper display
        self.populate_gallery(force_refresh=True)

    # UI update methods
    def _update_categories(self):
        """Update the categories dropdown"""
        if not hasattr(self, 'category_combo'):
            return
            
        # Remember current category
        current = self.category_combo.currentText()
        
        # Clear existing items
        self.category_combo.clear()
        
        # Always add "All" as the first option
        self.category_combo.addItem("All")
        
        # Get categories from project_type_manager (preferred way)
        categories = set()
        
        if hasattr(self, 'app') and hasattr(self.app, 'template_manager'):
            # Get categories from project type manager if available
            if hasattr(self.app.template_manager, 'project_type_manager'):
                project_types = self.app.template_manager.project_type_manager.get_all_project_types()
                categories.update(project_types)
                print(f"Found {len(project_types)} project types: {project_types}")
            # Fallback to get_categories method
            elif hasattr(self.app.template_manager, 'get_categories'):
                category_list = self.app.template_manager.get_categories()
                categories.update(category_list)
                print(f"Found {len(category_list)} categories from get_categories")
                
        # If no categories found yet, extract from templates as last resort
        if not categories and hasattr(self, 'app') and hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'templates'):
            templates = self.app.template_manager.templates
            
            # Handle templates as dict or list
            if isinstance(templates, dict):
                for name, data in templates.items():
                    if isinstance(data, dict) and 'category' in data and data['category']:
                        categories.add(data['category'])
            elif isinstance(templates, list):
                for template in templates:
                    if isinstance(template, dict) and 'category' in template and template['category']:
                        categories.add(template['category'])
            
            print(f"Found {len(categories)} categories from templates")
        
        # Add categories to combo box
        for category in sorted(categories):
            self.category_combo.addItem(category)
        
        print(f"Updated category dropdown with {self.category_combo.count()} items")
        
        # Try to restore the previous selection or default to "All"
        index = self.category_combo.findText(current)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentIndex(0)
    
    def _update_button_state(self):
        """Update the state of action buttons based on selection"""
        # Template buttons - edit and delete buttons removed, now using context menu
        
        # Folder buttons
        has_folder_selected = self.selected_folder is not None
        
        # Special case for rename folder - don't show the button at all
        # Delete folder button removed - using context menu and keystroke delete instead
    
    def _update_card_sizes(self):
        """Update card sizes after resize or scale change"""
        self._update_folder_card_sizes(self.icon_scale)
    
    def _update_folder_card_sizes(self, scale_percent):
        """Update the sizes of folder cards based on the scale percentage"""
        GalleryFoldersSetup.update_folder_card_sizes(self, scale_percent)
    
    def _handle_resize_timeout(self):
        """Handle resize event after a timeout to prevent excessive updates"""
        self._update_layout_after_resize()
    
    def _update_layout_after_resize(self):
        """Update layout after resizing is complete"""
        # Update grid column count and card sizes based on new size
        self._update_grid_columns()
        self._update_card_sizes()
        
        # For list view, ensure horizontal scrolling is disabled
        if hasattr(self, 'view_mode') and self.view_mode == "list":
            # Find the scroll area in the templates section
            if hasattr(self, 'templates_scroll'):
                self.templates_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def _update_grid_columns(self):
        """Update the number of columns in the grid layouts based on container width"""
        # Only repopulate if we have the necessary attributes and a template manager
        if hasattr(self, 'app') and hasattr(self.app, 'template_manager'):
            # Re-populate folders with new column count
            if self.folders_section.isVisible():
                # Re-populate the gallery to adjust column count
                self.populate_gallery(force_refresh=True)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Let the GalleryEvents handle all keyboard events including deletion
        GalleryEvents.key_press_event(self, event)
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events in the template area"""
        if event.button() == Qt.LeftButton:
            # Get keyboard modifiers for multi-selection
            modifiers = QApplication.keyboardModifiers()
            ctrl_or_cmd = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
            shift = bool(modifiers & Qt.ShiftModifier)
            
            # If event is handled by a template or folder card, defer to it
            widget_at_pos = self.childAt(event.pos())
            
            # Check if we clicked on a template card or any of its children
            is_card_click = False
            test_widget = widget_at_pos
            while test_widget:
                if test_widget in self.template_cards or test_widget in self.folder_cards:
                    is_card_click = True
                    break
                # Need to check if parent method exists and call it if it does
                if hasattr(test_widget, 'parent'):
                    if callable(test_widget.parent):
                        test_widget = test_widget.parent()
                    else:
                        test_widget = None
                else:
                    test_widget = None
            
            # If clicking on a card, let the card handle it
            if is_card_click:
                print(f"🔍 LISTENER: Click on a card - deferring to card handler")
                QWidget.mousePressEvent(self, event)
                return
            
            # Not clicking on a card - handle clearing selection
            print(f"🔍 LISTENER: Click in blank space of templates area - clearing selection")
            
            # Only clear if we're not using modifiers for multi-select
            if not ctrl_or_cmd and not shift:
                # Clear primary selection if one exists
                had_selection = False
                if hasattr(self, 'selected_template') and self.selected_template is not None:
                    had_selection = True
                    old_selection = self.selected_template
                    self.selected_template = None
                    
                    # Also clear app selection if available
                    if hasattr(self, 'app') and hasattr(self.app, 'selected_template'):
                        self.app.selected_template = None
                
                # Clear multi-selection if any exists
                had_multi_selection = False
                if hasattr(self, 'multi_selected_templates'):
                    had_multi_selection = len(self.multi_selected_templates) > 0
                    self.multi_selected_templates.clear()
                
                # Update card styling - essential to ensure visual state updates
                if had_selection or had_multi_selection:
                    # Update card visuals
                    self._update_template_card_selection()
                    
                    # Also update table view if it exists and we're in list view mode
                    if hasattr(self, 'template_table_view') and self.template_table_view and self.view_mode == 'list':
                        if self.template_table_view.selectionModel():
                            self.template_table_view.selectionModel().clearSelection()
                            
                    print(f"🔍 LISTENER: Cleared all selections")
        
        # Let parent handle remaining events
        QWidget.mousePressEvent(self, event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release in the gallery without interfering with card selections"""
        if event.button() == Qt.LeftButton:
            # Check if we clicked on a template or folder card
            widget_at_pos = self.childAt(event.pos())
            
            # If the click is on a card or any of its children, let the card handle it
            is_card_click = False
            test_widget = widget_at_pos
            while test_widget:
                if test_widget in self.template_cards or test_widget in self.folder_cards:
                    is_card_click = True
                    break
                # Need to check if parent method exists and call it if it does
                if hasattr(test_widget, 'parent'):
                    if callable(test_widget.parent):
                        test_widget = test_widget.parent()
                    else:
                        test_widget = None
                else:
                    test_widget = None
            
            # If clicking on a card, don't interfere
            if is_card_click:
                return QWidget.mouseReleaseEvent(self, event)
        
        # Let parent handle the event
        QWidget.mouseReleaseEvent(self, event)
        
    def resizeEvent(self, event):
        """Handle resize events to trigger layout updates"""
        self.resize_timer.start()
        super().resizeEvent(event)

    # Context Menu Method
    def _show_gallery_context_menu(self, position):
        # Determine the widget clicked (could be background or a card)
        widget = self.childAt(position)
        parent_widget = self # Default parent for the menu
        template_card = None
        template_name = None
        folder_card = None
        folder_name = None

        # Traverse up to find the TemplateCard or TemplateFolderCard
        temp_widget = widget
        while temp_widget is not None and temp_widget != self:
            if isinstance(temp_widget, TemplateCard):
                template_card = temp_widget
                template_name = template_card.template_name() if template_card else None
                parent_widget = template_card # Anchor menu to card
                break
            if isinstance(temp_widget, TemplateFolderCard):
                folder_card = temp_widget
                folder_name = folder_card.folder_name # Assuming folder_card has this attribute
                parent_widget = folder_card # Anchor menu to card
                break
            temp_widget = temp_widget.parent()

        # Get global position for the menu
        global_position = self.mapToGlobal(position)

        # --- Template Card Context Menu ---
        if template_card and template_name:
            print(f"DEBUG: Showing context menu for template card: '{template_name}'")
            menu = ContextMenu(parent_widget) # Use the custom menu
            
            # Determine if multi-select is active and if this card is part of it
            num_selected = len(self.multi_selected_templates) if hasattr(self, 'multi_selected_templates') else 0
            # Multi-select is true if > 1 selected, OR if 1 is selected but it's NOT the card clicked on
            is_multi_select = num_selected > 1 or (num_selected == 1 and self.multi_selected_templates[0].get('name') != template_name)
            print(f"DEBUG: Multi-select active: {is_multi_select}, Count: {num_selected}")

            # Determine which template names to process (single or multi)
            if is_multi_select:
                names_to_process = [t.get('name') for t in self.multi_selected_templates if t and t.get('name')]
                # Ensure the right-clicked card's template is included if multi-select is active
                if template_name not in names_to_process:
                     names_to_process.append(template_name) 
            else:
                names_to_process = [template_name]
            print(f"DEBUG: Names to process for Move/Delete: {names_to_process}")

            # --- Standard Actions ---
            edit_action = menu.addAction("Edit")
            
            # Use a helper function for deletion to handle single/multi logic clearly
            def delete_selected():
                 print(f"DEBUG: Context Menu Delete Triggered for: {names_to_process}")
                 GalleryEvents.on_delete_template(self, names_to_process)

            # Define the text for the delete action based on selection
            delete_action_text = "Delete Selected Templates" if is_multi_select else "Delete Template"

            # Add Delete action styled in red - Match position to List View
            menu.addRedDeleteAction(self, callback=delete_selected, text=delete_action_text)
            
            # Always add Duplicate and Export options (like in List View)
            duplicate_action = menu.addAction("Duplicate")
            export_action = menu.addAction("Export Template...")
            
            # Disable Edit action if multi-select
            edit_action.setEnabled(not is_multi_select)
            # Disable Duplicate and Export if multi-select (matching List View behavior)
            duplicate_action.setEnabled(not is_multi_select)
            export_action.setEnabled(not is_multi_select)

            # --- Move to Folder Submenu ---
            menu.addSeparator()
            move_menu = menu.addMenu("Move to...")
            folders = self.template_manager.get_folders() if self.template_manager else []

            # Add "Root (No Folder)" option
            root_action = move_menu.addAction("Root (No Folder)")
            root_action.triggered.connect(lambda: GalleryEvents.on_move_template_to_folder(
                self, names_to_process, 'root' # Pass the list of names
            ))
            move_menu.addSeparator()

            # Add folder options
            if folders:
                folder_names_to_iterate = []
                if isinstance(folders, dict):
                    folder_names_to_iterate = sorted(folders.keys())
                elif isinstance(folders, list):
                    folder_names_to_iterate = sorted(folders)
                
                for folder_name_iter in folder_names_to_iterate:
                    move_action = move_menu.addAction(folder_name_iter)
                    # Ensure lambda captures current folder name and correct names list
                    move_action.triggered.connect(lambda checked, fn=folder_name_iter, ntp=list(names_to_process): \
                        GalleryEvents.on_move_template_to_folder(self, ntp, fn))
            else:
                no_folders_action = move_menu.addAction("No folders available")
                no_folders_action.setEnabled(False)

            # --- Connect Actions ---
            primary_template = self.multi_selected_templates[0] if num_selected > 0 else None
            primary_name = primary_template.get('name') if primary_template else None
            
            if primary_name:
                 edit_action.triggered.connect(lambda: self._on_edit_template(primary_name))
                 duplicate_action.triggered.connect(lambda: self._on_duplicate_template(primary_name))
                 export_action.triggered.connect(lambda: GalleryEvents.on_export_template(self, primary_name))

            # --- Show Menu --- 
            menu.exec_(global_position)

        # --- Folder Card Context Menu ---
        elif folder_card and folder_name:
            print(f"DEBUG: Showing context menu for folder card: '{folder_name}'")
            menu = ContextMenu(parent_widget) # Use the custom menu
            # TODO: Add folder-specific actions (Rename, Delete Folder?)
            rename_action = menu.addAction("Rename")
            # delete_folder_action = menu.addAction("Delete Folder") # Consider using addRedDeleteAction
            rename_action.triggered.connect(folder_card._start_rename) # Trigger rename on the card
            
            # Placeholder for delete action
            menu.addSeparator()
            def delete_this_folder():
                GalleryEvents.on_delete_folder(self, folder_name) # Pass name
            menu.addRedDeleteAction(self, callback=delete_this_folder, text="Delete Folder")

            menu.exec_(global_position)

        # --- Background Context Menu ---
        else:
            print("DEBUG: Showing context menu for gallery background")
            menu = ContextMenu(parent_widget) # Use the custom menu
            import_action = menu.addAction("Import Template...")
            add_folder_action = menu.addAction("Add Folder")
            add_template_action = menu.addAction("Add Template")
            
            # Ensure self.app exists and is valid
            if hasattr(self, 'app') and self.app:
                import_action.triggered.connect(lambda: import_template(self.app))
                add_folder_action.triggered.connect(self._on_add_folder)
                add_template_action.triggered.connect(self._on_add_template)
            else:
                print("[WARNING] Gallery context menu: Cannot connect actions, self.app is not available.")
                import_action.setEnabled(False)
                add_folder_action.setEnabled(False)
                add_template_action.setEnabled(False)
            
            menu.exec_(global_position)

    def _on_sort_column(self, field):
        """Sort the templates list by the given field"""
        if not hasattr(self, 'current_sort_field'):
            self.current_sort_field = 'name'
        if not hasattr(self, 'current_sort_order'):
            self.current_sort_order = 'asc'
        
        # Toggle sort order if the same field is clicked twice
        if self.current_sort_field == field:
            self.current_sort_order = 'desc' if self.current_sort_order == 'asc' else 'asc'
        else:
            # Default to ascending order for new field
            self.current_sort_field = field
            self.current_sort_order = 'asc'
        
        print(f"[DEBUG] Gallery: Sorting by {self.current_sort_field} ({self.current_sort_order})")
        
        # Refresh the gallery with new sort settings
        self.populate_gallery(force_refresh=True)
    
    def select_template(self, template_name):
        """Select a template by name after the gallery is refreshed
        
        This method is used to re-select a template after a rename operation
        or other updates that require gallery refresh.
        
        Args:
            template_name: Name of the template to select
            
        Returns:
            bool: True if template was found and selected, False otherwise
        """
        print(f"🔹 GALLERY SELECT: Attempting to select template '{template_name}'")
        
        # Normalize template name for comparison - handle both with and without Template_ prefix
        clean_name = template_name
        if clean_name.startswith("Template_"):
            clean_name = clean_name[9:]  # Remove the prefix
            
        print(f"🔹 GALLERY SELECT: Using normalized name '{clean_name}' for selection")
        
        # Track if we found and selected the template
        selected = False
        
        # First check if we have any template cards
        if hasattr(self, 'template_cards') and self.template_cards:
            print(f"🔹 GALLERY SELECT: Searching {len(self.template_cards)} template cards")
            
            # Create name variations to try matching against cards
            name_variations = [
                template_name,                # Original name
                clean_name,                   # Without Template_ prefix
                f"Template_{clean_name}",     # With Template_ prefix
                template_name.replace(' ', '_'),    # With underscores
                clean_name.replace(' ', '_')  # Clean with underscores
            ]
            
            # Find the template card with the matching name
            for i, card in enumerate(self.template_cards):
                # Skip if no template property
                if not hasattr(card, 'template'):
                    print(f"🔹 GALLERY SELECT: Card {i} has no template property, skipping")
                    continue
                    
                # Get card name for comparison
                card_name = ""
                if isinstance(card.template, dict) and 'name' in card.template:
                    card_name = card.template['name']
                elif hasattr(card, 'template_name') and callable(card.template_name):
                    card_name = card.template_name()
                
                print(f"🔹 GALLERY SELECT: Checking card {i} with name '{card_name}'")
                
                # Check all variations of the name for matching
                if any(card_name == variation for variation in name_variations):
                    matching_variation = next(variation for variation in name_variations if card_name == variation)
                    print(f"🔹 GALLERY SELECT: ✅ Found card for '{template_name}' by matching '{matching_variation}', selecting it")
                    
                    # Set as the selected template
                    self.selected_template = card.template
                    
                    # Also set in app if available
                    if hasattr(self, 'app') and hasattr(self.app, 'set_selected_template'):
                        self.app.set_selected_template(card.template)
                        print(f"🔹 GALLERY SELECT: Updated app-level selected template")
                    
                    # Update card selection state
                    if hasattr(card, 'set_selected'):
                        card.set_selected(True)
                        print(f"🔹 GALLERY SELECT: Set card selected state to True")
                    else:
                        print(f"🔹 GALLERY SELECT: Card has no set_selected method")
                        
                    # Update all cards to reflect new selection
                    if hasattr(self, '_update_template_card_selection'):
                        self._update_template_card_selection()
                        print(f"🔹 GALLERY SELECT: Updated all card selection states")
                    
                    # Apply highlight effect if card supports it
                    if hasattr(card, 'apply_rename_highlight'):
                        card.apply_rename_highlight()
                        print(f"🔹 GALLERY SELECT: Applied rename highlight effect to card")
                    
                    print(f"🔹 GALLERY SELECT: Successfully selected template '{template_name}'")
                    selected = True
                    break
                else:
                    # Debug matching attempts
                    print(f"🔹 GALLERY SELECT: ❌ No match for {card_name} vs variations of {template_name}")
        else:
            print(f"🔹 GALLERY SELECT: No template cards found in gallery")
        
        # If we still haven't found it, try to find the template in the template manager
        if not selected and hasattr(self, 'app') and hasattr(self.app, 'template_manager'):
            print(f"🔹 GALLERY SELECT: Attempting to find template '{template_name}' in template manager")
            template_manager = self.app.template_manager
            
            # Try to get the template with various name formats
            template = None
            name_variations = [
                template_name,                # Original name
                clean_name,                   # Without Template_ prefix
                f"Template_{clean_name}",     # With Template_ prefix
                template_name.replace(' ', '_'),    # With underscores
                clean_name.replace(' ', '_'),  # Clean with underscores
                template_name.replace('_', ' '),    # Replace underscores with spaces
                clean_name.replace('_', ' ')   # Clean replace underscores with spaces
            ]
            
            # Try all variations
            for name in name_variations:
                print(f"🔹 GALLERY SELECT: Trying variation '{name}' in template manager")
                template = template_manager.get_template_by_name(name)
                if template:
                    print(f"🔹 GALLERY SELECT: ✅ Found template in manager with name '{name}'")
                    break
                else:
                    print(f"🔹 GALLERY SELECT: ❌ Template not found in manager with name '{name}'")
            
            if template:
                print(f"🔹 GALLERY SELECT: Found template in manager, updating UI selection")
                # Set as selected template
                self.selected_template = template
                
                # Also set in app if available
                if hasattr(self.app, 'set_selected_template'):
                    self.app.set_selected_template(template)
                    print(f"🔹 GALLERY SELECT: Updated app-level selected template from manager")
                
                # We found the template but couldn't select a card, which might mean
                # we need to refresh the gallery to show this template
                print(f"🔹 GALLERY SELECT: Template found in manager but no matching card, might need refresh")
                selected = True
            else:
                print(f"🔹 GALLERY SELECT: Template not found in manager with any name variation")
        else:
            if selected:
                print(f"🔹 GALLERY SELECT: Already selected template from template cards")
            elif not hasattr(self, 'app') or not self.app:
                print(f"🔹 GALLERY SELECT: No app object available")
            elif not hasattr(self.app, 'template_manager'):
                print(f"🔹 GALLERY SELECT: No template_manager in app")
        
        # If we get here and haven't found the template, it failed
        if not selected:
            print(f"🔹 GALLERY SELECT: Failed to find template '{template_name}' in gallery or template manager")
            
            # Last resort: Check if we need to force refresh
            if hasattr(self, 'templates_loaded'):
                print(f"🔹 GALLERY SELECT: Last resort - forcing gallery refresh and trying again")
                self.templates_loaded = False
                self.populate_gallery(force_refresh=True)
                
                # Process events to ensure refresh completes
                from PyQt5.QtWidgets import QApplication
                QApplication.processEvents()
                
                # Try selection one more time with all cards
                if hasattr(self, 'template_cards') and self.template_cards:
                    for i, card in enumerate(self.template_cards):
                        if hasattr(card, 'template') and isinstance(card.template, dict):
                            card_name = card.template.get('name', '')
                            if card_name == template_name or card_name == clean_name:
                                print(f"🔹 GALLERY SELECT: ✅ Found card in fresh gallery")
                                self.selected_template = card.template
                                
                                if hasattr(card, 'set_selected'):
                                    card.set_selected(True)
                                    
                                # Update all cards to reflect new selection
                                if hasattr(self, '_update_template_card_selection'):
                                    self._update_template_card_selection()
                                
                                # Apply highlight effect if card supports it
                                if hasattr(card, 'apply_rename_highlight'):
                                    card.apply_rename_highlight()
                                    
                                selected = True
                                break
        
        return selected 

    # --- New Handlers for Table View Signals --- 
    def _on_table_item_clicked(self, index: QModelIndex):
        """Handle single click on a row in the TemplateTableView."""
        if not index.isValid():
            return
            
        proxy_model = self.template_table_view.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        # Use source model and index for getting items
        name_item = source_model.item(source_index.row(), 0) # Assuming Name is column 0
        if name_item:
            template_name = name_item.text()
            print(f"DEBUG: Table item clicked: {template_name}")
            
            # Get the full template data using the name
            # MODIFIED: Call get_template via template_io
            template_data = self.template_manager.template_io.get_template(template_name)
            
            if template_data:
                # Use the existing selection logic
                self._on_template_select(template_data) 
            else:
                print(f"[WARNING] Could not find template data for '{template_name}'")

    def _on_table_item_double_clicked(self, index: QModelIndex):
        """Handle double click on a row in the TemplateTableView."""
        if not index.isValid():
            return

        proxy_model = self.template_table_view.model()
        source_model = proxy_model.sourceModel()
        source_index = proxy_model.mapToSource(index)
        # Use source model and index for getting items
        name_item = source_model.item(source_index.row(), 0) # Assuming Name is column 0
        if name_item:
            template_name = name_item.text()
            print(f"DEBUG: Table item double-clicked: {template_name}")
            
            # Trigger the edit action (or whatever double-click should do)
            self._on_edit_template(template_name=template_name)

    def _on_table_header_clicked(self, logicalIndex):
        """Handle click on a table header section to trigger sorting."""
        header_view = self.template_table_view.horizontalHeader()
        model = header_view.model() # Get the model associated with the header
        sort_field = model.headerData(logicalIndex, Qt.Horizontal, Qt.DisplayRole)
        
        if sort_field:
            print(f"DEBUG: Table header clicked: Index={logicalIndex}, Field='{sort_field}'")
            # Call the sorting function from GalleryTemplatesSetup
            GalleryTemplatesSetup.set_template_sort(self, sort_field)
        else:
            print(f"[WARNING] Could not get header field name for index {logicalIndex}")

    def _show_table_context_menu(self, position: QPoint):
        """Show context menu for the selected item(s) in the table view."""
        table_view = self.template_table_view
        selected_indexes = table_view.selectionModel().selectedRows() # Get selected row indexes (Column 0)
        
        selected_templates = []
        if selected_indexes:
             proxy_model = table_view.model()
             source_model = proxy_model.sourceModel()
             
             for index in selected_indexes:
                 # Map proxy index to source index
                 source_index = proxy_model.mapToSource(index)
                 # Get item from source model
                 name_item = source_model.item(source_index.row(), 0) # Assuming Name is column 0
                 if name_item:
                     template_name = name_item.text()
                     template_data = self.template_manager.get_template_by_name(template_name)
                     if template_data:
                         selected_templates.append(template_data)

        num_selected = len(selected_templates)
        print(f"DEBUG: Showing table context menu for: {[t.get('name') for t in selected_templates]}")
        print(f"DEBUG: Number of selected templates for context menu: {num_selected}")

        if num_selected == 0:
            return # Don't show menu if nothing is selected

        # Use the custom ContextMenu for consistent styling
        menu = ContextMenu(self.template_table_view)
        
        # Determine template names for actions
        if is_multi_select := (num_selected > 1):
             names_to_process = [t.get('name') for t in selected_templates if t and t.get('name')]
        else:
             # If single select, use the primary template's name
             primary_template = selected_templates[0] if selected_templates else None
             names_to_process = [primary_template.get('name')] if primary_template and primary_template.get('name') else []
        
        # --- Standard Actions (Consistent with Grid View) ---
        edit_action = menu.addAction("Edit")
        
        # Use a helper function for deletion to handle single/multi logic clearly
        def delete_selected():
             print(f"DEBUG: Context Menu Delete Triggered for: {names_to_process}")
             GalleryEvents.on_delete_template(self, names_to_process)
        
        # Define the text for the delete action based on selection
        delete_action_text = "Delete Selected Templates" if is_multi_select else "Delete Template"
        
        # Add Delete action styled in red - MOVED TO MATCH GRID VIEW ORDER
        menu.addRedDeleteAction(self, callback=delete_selected, text=delete_action_text)
        
        # Always add Duplicate and Export Template options (consistent with Grid View)
        duplicate_action = menu.addAction("Duplicate")
        export_action = menu.addAction("Export Template...")
        
        # Disable Edit action if multi-select
        edit_action.setEnabled(not is_multi_select)
        # Disable Duplicate and Export if multi-select (matching Grid View behavior)
        duplicate_action.setEnabled(not is_multi_select)
        export_action.setEnabled(not is_multi_select)

        # Add separator before Cache Management
        menu.addSeparator()
        
        # Add Cache Management section (consistent with list view)
        # Only enable for single selection to match list view behavior
        if not is_multi_select and primary_template:
            primary_name = primary_template.get('name')
            cache_menu = menu.addMenu("Cache Management")
            
            # Add recache option
            recache_action = QAction("Recache Template", self)
            recache_action.triggered.connect(lambda: self._on_recache_template(primary_name))
            cache_menu.addAction(recache_action)
            
            # Add clear cache option
            clear_cache_action = QAction("Clear Template Cache", self)
            clear_cache_action.triggered.connect(lambda: self._on_clear_template_cache(primary_name))
            cache_menu.addAction(clear_cache_action)

        # Add separator (before Move To)
        menu.addSeparator()

        # --- Move to Folder Submenu ---
        move_menu = menu.addMenu("Move to...")

        # Determine template names for move action
        # Ensure names_to_process is defined before being used in lambdas
        if is_multi_select:
             names_to_process = [t.get('name') for t in selected_templates if t and t.get('name')]
        else:
             # If single select, use the primary template's name
             primary_template = selected_templates[0] if selected_templates else None
             names_to_process = [primary_template.get('name')] if primary_template and primary_template.get('name') else []

        # Add "Root (No Folder)" option - ALWAYS add this if items are selected
        root_action = move_menu.addAction("Root (No Folder)")
        # Ensure names_to_process is captured correctly by the lambda
        root_action.triggered.connect(lambda checked, ntp=list(names_to_process): GalleryEvents.on_move_template_to_folder(
            self, ntp, 'root'
        ))
        # Enable based on whether items are selected, not if in folder
        root_action.setEnabled(bool(names_to_process)) 

        # Add separator if folders exist
        folders = self.template_manager.get_folders() if hasattr(self.template_manager, 'get_folders') else []
        if folders:
             move_menu.addSeparator()

        # Get available folders and iterate
        if folders:
            folder_names_to_iterate = []
            if isinstance(folders, dict):
                folder_names_to_iterate = sorted(folders.keys())
            elif isinstance(folders, list):
                folder_names_to_iterate = sorted(folders) # Assume list of names
            else:
                print(f"[WARNING] _show_table_context_menu: Unexpected type for folders: {type(folders)}")
                folder_names_to_iterate = []
            
            # Iterate over the determined list of folder names
            for folder_name in folder_names_to_iterate:
                # FIX: Explicitly skip the CURRENT folder as a destination
                if self.current_folder and folder_name == self.current_folder:
                     continue
                      
                folder_action = move_menu.addAction(folder_name)
                # Ensure names_to_process is captured correctly by the lambda
                folder_action.triggered.connect(lambda checked, name=folder_name, ntp=list(names_to_process): 
                    GalleryEvents.on_move_template_to_folder(self, ntp, name)
                )

        # --- Connect Actions ---
        primary_template = self.multi_selected_templates[0] if num_selected > 0 else None
        primary_name = primary_template.get('name') if primary_template else None
        
        if primary_name:
             edit_action.triggered.connect(lambda: self._on_edit_template(primary_name))
             # Connect duplicate/export only if they were created
             duplicate_action.triggered.connect(lambda: self._on_duplicate_template(primary_name))
             export_action.triggered.connect(lambda: GalleryEvents.on_export_template(self, primary_name))
        
        # --- Show Menu --- 
        menu.exec_(self.template_table_view.viewport().mapToGlobal(position))

    # --- Unified Selection Handler (Restored) ---
    def handle_template_item_press(self, template, is_modifier_click):
        """Handles clicks on template items (cards or list rows) for selection."""
        template_name = template.get('name') if isinstance(template, dict) else None
        if not template_name:
            print("ERROR: Template item press with invalid template data.")
            return

        print(f"🔍 LISTENER: Handling press for '{template_name}', modifier: {is_modifier_click}")

        # Determine current selection state
        is_currently_primary_selected = self.selected_template and self.selected_template.get('name') == template_name
        is_currently_multi_selected = template in self.multi_selected_templates

        if not is_modifier_click:
            # --- Single Click (No Modifiers) ---
            if not is_currently_multi_selected:
                 self.multi_selected_templates = []
                 print(f"🔍 LISTENER: Single click on non-multi-selected item - clearing multi-select.")
            else:
                 print(f"🔍 LISTENER: Single click on multi-selected item - preserving multi-select for potential drag.")
                 
            self.selected_template = template
            print(f"🔍 LISTENER: Single click - setting primary selection to '{template_name}'")

        else:
            # --- Modifier Click (Ctrl/Cmd or Shift) ---
            if is_currently_primary_selected and len(self.multi_selected_templates) <= 1:
                 if template not in self.multi_selected_templates:
                      self.multi_selected_templates.append(template)
                 print(f"🔍 LISTENER: Modifier click on primary - starting multi-select with '{template_name}'")
            elif is_currently_multi_selected:
                 self.multi_selected_templates.remove(template)
                 if is_currently_primary_selected:
                      self.selected_template = None
                 print(f"🔍 LISTENER: Modifier click - deselecting '{template_name}' from multi-select")
            else:
                 if template not in self.multi_selected_templates:
                      self.multi_selected_templates.append(template)
                 print(f"🔍 LISTENER: Modifier click - adding '{template_name}' to multi-select")
                 if len(self.multi_selected_templates) == 1 and self.selected_template and self.selected_template not in self.multi_selected_templates:
                     self.multi_selected_templates.insert(0, self.selected_template)
                     print(f"🔍 LISTENER: Ensuring original primary '{self.selected_template.get('name')}' is in multi-select")

        self._update_selection_ui()
        self.template_selected.emit(self.selected_template if self.selected_template else {}) # Emit primary selection

    # --- End Unified Selection Handler ---
    
    # --- Update Selection UI (Restored) ---
    def _update_selection_ui(self):
        """Updates the visual selection state of all items (cards/rows)."""
        from PyQt5.QtCore import QModelIndex, QItemSelectionModel, Qt
        from PyQt5.QtWidgets import QAbstractItemView
        
        print(f"🔍 LISTENER: Updating template selection UI")
        is_multi_select_mode = len(self.multi_selected_templates) > 1
        primary_selected_name = self.selected_template.get('name') if self.selected_template else None
        multi_selected_names = {t.get('name') for t in self.multi_selected_templates if isinstance(t, dict)}

        print(f"🔍 LISTENER: In multi-selection mode: {is_multi_select_mode}")
        print(f"🔍 LISTENER: Primary selection: {primary_selected_name}")
        print(f"🔍 LISTENER: Multi-selection count: {len(multi_selected_names)}")

        # Update Template Cards
        for card in self.template_cards:
            card_template_name = card.template_name()
            is_primary = card_template_name == primary_selected_name
            is_multi = card_template_name in multi_selected_names

            print(f"🔍 LISTENER: Setting multi-selection state of '{card_template_name}' to {is_multi}")
            card.set_multi_selected(is_multi) # Set multi-selected first

            if is_primary:
                 print(f"🔍 LISTENER: Setting '{card_template_name}' as selected")
                 card.set_selected(True)
            else:
                 if not is_multi:
                     print(f"🔍 LISTENER: Setting '{card_template_name}' as NOT selected")
                     card.set_selected(False)

        # Update Table View (if it exists and is visible)
        if self.template_table_view and self.template_table_view.isVisible():
            model = self.template_table_view.model() # Use the proxy model
            selection_model = self.template_table_view.selectionModel()
            if not model or not selection_model:
                print("WARNING: No model or selection model found for table view during UI update")
                return

            selection_model.blockSignals(True)
            selection_model.clear() # Clear existing selection first
            print(f"🔍 LISTENER (UI Update): Cleared table selection model.")

            primary_row_index = -1 # Track the row index of the primary selection

            for row in range(model.rowCount()):
                index = model.index(row, 0) # Get index for the Name column
                if not index.isValid(): continue
                item_name = model.data(index, Qt.DisplayRole)

                should_select_row = False
                if item_name == primary_selected_name:
                     should_select_row = True
                     primary_row_index = row
                     print(f"🔍 LISTENER (UI Update): Marking row {row} ({item_name}) for selection (Primary).")
                elif item_name in multi_selected_names:
                     should_select_row = True
                     print(f"🔍 LISTENER (UI Update): Marking row {row} ({item_name}) for selection (Multi).")

                if should_select_row:
                    selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                    print(f"🔍 LISTENER (UI Update): Selected row {row} in table model.")

            if primary_row_index != -1:
                 primary_model_index = model.index(primary_row_index, 0)
                 if primary_model_index.isValid():
                     self.template_table_view.setFocus() # Ensure table has focus before setting index/scrolling
                     self.template_table_view.setCurrentIndex(primary_model_index)
                     print(f"🔍 LISTENER (UI Update): Set current table index to row {primary_row_index}.")
                     self.template_table_view.scrollTo(primary_model_index, QAbstractItemView.PositionAtCenter) # Scroll to selected
            else:
                 self.template_table_view.setCurrentIndex(QModelIndex()) # Clear current index if no primary selection
                 print(f"🔍 LISTENER (UI Update): Cleared current table index.")

            selection_model.blockSignals(False)
            print(f"🔍 LISTENER (UI Update): Unblocked table selection signals.")

        print(f"DEBUG: Finished updating selection UI")
    # --- End Update Selection UI ---
    
    # --- Table Selection Handler (Restored) ---
    def _on_table_selection_changed(self, selected, deselected):
        """Handles selection changes in the TemplateTableView."""
        if self.template_table_view and self.template_table_view.selectionModel():
             self.template_table_view.selectionModel().blockSignals(True)
        
        selected_indexes = self.template_table_view.selectionModel().selectedRows() 
        proxy_model = self.template_table_view.model()
        if not proxy_model:
             if self.template_table_view and self.template_table_view.selectionModel():
                  self.template_table_view.selectionModel().blockSignals(False) # Unblock before returning
             return 
             
        source_model = proxy_model.sourceModel()
        if not source_model:
             if self.template_table_view and self.template_table_view.selectionModel():
                  self.template_table_view.selectionModel().blockSignals(False) # Unblock before returning
             return
        
        current_selection_names = set()
        new_multi_selected_templates = []
        primary_selection_candidate = None
        primary_index = self.template_table_view.currentIndex() 

        for index in selected_indexes:
            if index.isValid():
                source_index = proxy_model.mapToSource(index)
                name_item = source_model.item(source_index.row(), 0) 
                if name_item:
                    template_name = name_item.text()
                    current_selection_names.add(template_name)
                    template_data = None
                    if hasattr(self.template_manager, 'template_io') and self.template_manager.template_io:
                         template_data = self.template_manager.template_io.get_template(template_name)
                         
                    if template_data:
                        if template_data not in new_multi_selected_templates:
                             new_multi_selected_templates.append(template_data)
                        if source_index.row() == proxy_model.mapToSource(primary_index).row():
                             primary_selection_candidate = template_data
                    else:
                         print(f"[WARNING] _on_table_selection_changed: Could not find template data for '{template_name}' via template_io")

        print(f"[DEBUG] Table Selection Changed. Names: {current_selection_names}")
        self.multi_selected_templates = new_multi_selected_templates
        
        if primary_selection_candidate:
             self.selected_template = primary_selection_candidate
             print(f"[DEBUG] Table Selection: Primary set to focused item '{primary_selection_candidate.get('name')}'")
        elif len(self.multi_selected_templates) == 1:
             self.selected_template = self.multi_selected_templates[0]
             print(f"[DEBUG] Table Selection: Primary set to single selected item '{self.selected_template.get('name')}'")
        elif len(self.multi_selected_templates) > 1:
             self.selected_template = self.multi_selected_templates[-1] 
             print(f"[DEBUG] Table Selection: Primary set to last of multi-select '{self.selected_template.get('name')}'")
        else:
             self.selected_template = None # Clear primary if selection is cleared
             print(f"[DEBUG] Table Selection: Primary selection cleared.")

        self._update_selection_ui() # Ensure UI reflects the potentially changed selection
        self.template_selected.emit(self.selected_template if self.selected_template else {}) # Emit primary

        if self.template_table_view and self.template_table_view.selectionModel():
             self.template_table_view.selectionModel().blockSignals(False)
             
    # --- End Table Selection Handler ---

    # --- Duplicate Template Handler (Restored) ---
    def _on_duplicate_template(self, template_name):
        """Handles the request to duplicate a template."""
        print(f"[DEBUG] Received duplicate request for '{template_name}'")
        if not template_name:
            print("[WARNING] Duplicate request with no template name.")
            return

        # Generate new name using finder-like naming pattern (name, name copy, name copy 2, etc.)
        base_name = template_name
        
        # Check if the template name already ends with " copy" or " copy N"
        import re
        copy_pattern = re.compile(r'^(.*?) copy( \d+)?$')
        match = copy_pattern.match(template_name)
        
        if match:
            # If it's already a copy, use the original base name
            base_name = match.group(1)
            
        # Start with "base_name copy"
        new_name = f"{base_name} copy"
        
        # If that name exists, try "base_name copy 2", "base_name copy 3", etc.
        if any(t.get('name') == new_name for t in self.template_manager.template_io.templates.values()):
            counter = 1
            while True:
                new_name = f"{base_name} copy {counter}"
                if not any(t.get('name') == new_name for t in self.template_manager.template_io.templates.values()):
                    break
                counter += 1
            
        # Proceed with duplication
        try:
            # Check if we're in a folder and should place the duplicate there
            current_folder = self.current_folder if hasattr(self, 'current_folder') else None
            
            # Duplicate the template
            success = self.template_manager.duplicate_template(template_name, new_name)
            if success:
                print(f"[INFO] Successfully duplicated '{template_name}' as '{new_name}'")
                
                # If we're in a folder, add the new template to this folder
                if current_folder:
                    print(f"[DEBUG] Adding duplicated template '{new_name}' to current folder '{current_folder}'")
                    if hasattr(self.template_manager, 'move_template_to_folder'):
                        self.template_manager.move_template_to_folder(new_name, current_folder)
                
                # Refresh the gallery to show the new template
                self.populate_gallery(force_refresh=True)
                
                # Select the newly created template
                self.select_template(new_name)
                
                # Update selected template (property) so subsequent duplications use this template
                template = self.template_manager.get_template_by_name(new_name)
                if template:
                    self.selected_template = template
                    # Make sure the UI knows this is the selected template
                    self._update_selection_ui()
                    # Emit signal that this template was selected
                    self.template_selected.emit(template)
                
                print(f"[DEBUG] Set newly duplicated template '{new_name}' as selected")
                
                if hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"Duplicated '{template_name}' as '{new_name}'", "success")
            else:
                print(f"[ERROR] Failed to duplicate '{template_name}'")
                if hasattr(self.app, 'show_status_message'):
                    self.app.show_status_message(f"Failed to duplicate '{template_name}'", "error")
        except Exception as e:
            print(f"[ERROR] Exception while duplicating '{template_name}': {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self.app, 'show_status_message'):
                self.app.show_status_message(f"Error duplicating '{template_name}': {e}", "error")
    # --- End Duplicate Template Handler ---
    
    # --- Shortcut Setup and Handling (Restored) ---
    def _setup_shortcuts(self):
        """Sets up keyboard shortcuts for the gallery."""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        duplicate_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        duplicate_shortcut.activated.connect(self._handle_duplicate_shortcut)
        print("[DEBUG] Duplicate shortcut (Ctrl+D / Cmd+D) connected.")
        
    def _handle_duplicate_shortcut(self):
        """Handles the activation of the duplicate keyboard shortcut."""
        print("[DEBUG] Duplicate shortcut activated.")
        
        selected_template = self.get_primary_selected_template() # Use helper to get primary selection
        multi_select_count = len(self.multi_selected_templates)

        if selected_template and multi_select_count <= 1:
             template_name = selected_template.get('name')
             if template_name:
                 print(f"[DEBUG] Triggering duplication for '{template_name}' via shortcut.")
                 self._on_duplicate_template(template_name=template_name)
             else:
                 print("[WARNING] Duplicate shortcut: Selected item has no name.")
        elif multi_select_count > 1:
             print("[DEBUG] Duplicate shortcut ignored: Multiple templates selected.")
             if hasattr(self.app, 'show_status_message'):
                 self.app.show_status_message("Duplicate shortcut requires a single selection.", "info", 2000)
        else:
             print("[DEBUG] Duplicate shortcut ignored: No template selected.")
             if hasattr(self.app, 'show_status_message'):
                 self.app.show_status_message("Select a template to duplicate.", "info", 2000)
                 
    def get_primary_selected_template(self):
         if self.selected_template:
             return self.selected_template
         if len(self.multi_selected_templates) == 1:
             return self.multi_selected_templates[0]
         return None 
    # --- End Shortcut Setup and Handling ---

    # ... (Keep remaining class methods like __init__, populate_gallery, clear_gallery, event handlers, context menus etc.) ...

    def _update_template_card_selection(self):
        """Updates the visual selection state of template cards in the grid view."""
        print(f"🔍 LISTENER: Updating template card selection visuals")
        primary_selected_name = self.selected_template.get('name') if self.selected_template else None
        multi_selected_names = {t.get('name') for t in self.multi_selected_templates if isinstance(t, dict)}

        for card in self.template_cards:
            if not hasattr(card, 'template') or not hasattr(card, 'template_name'):
                continue # Skip invalid cards
                
            card_template_name = card.template_name()
            is_primary = card_template_name == primary_selected_name
            is_multi = card_template_name in multi_selected_names

            # Set multi-selected state first (for styling priority)
            if hasattr(card, 'set_multi_selected'):
                card.set_multi_selected(is_multi)

            # Set primary selection state
            if hasattr(card, 'set_selected'):
                if is_primary:
                    card.set_selected(True)
                elif not is_multi: # Only deselect if not multi-selected either
                    card.set_selected(False)
            
        print(f"🔍 LISTENER: Finished updating card visuals")
        # Force UI update if necessary (though set_selected/set_multi_selected should handle it)
        # self.templates_scroll_content.update()

    def _filter_templates(self):
        """Filter templates based on search text and category"""
        # Delegate to gallery_events
        from app.templates.gallery_events import GalleryEvents
        GalleryEvents.on_filter_templates(self)
    
    def _on_recache_all_templates(self):
        """Handle recaching all templates"""
        from app.templates.gallery_events import GalleryEvents
        GalleryEvents.on_recache_all_templates(self)
    
    def _on_clear_all_caches(self):
        """Handle clearing all template caches"""
        from app.templates.gallery_events import GalleryEvents
        GalleryEvents.on_clear_all_caches(self)
    
    def _on_check_missing_originals(self):
        """Handle checking for templates with missing original files"""
        from app.templates.gallery_events import GalleryEvents
        GalleryEvents.on_check_missing_originals(self)
    
    def _set_view_mode(self, mode):
        """Change the view mode"""
        # Check if we have a view mode property
        if not hasattr(self, 'view_mode'):
            self.view_mode = "card"
        
        # Only proceed if the mode is different
        if self.view_mode == mode:
            return
        
        # Update the view mode
        self.view_mode = mode
        
        # Update UI to reflect the change
        if hasattr(self, 'card_view_action'):
            self.card_view_action.setChecked(mode == "card")
        if hasattr(self, 'list_view_action'):
            self.list_view_action.setChecked(mode == "list")
        if hasattr(self, 'table_view_action'):
            self.table_view_action.setChecked(mode == "table")
        
        # Refresh the gallery with the new view mode
        self.populate_gallery(force_refresh=True)
    
    def _toggle_animations(self, enabled=None):
        """Toggle animations on or off"""
        # Check if we have an animations_enabled property
        if not hasattr(self, 'animations_enabled'):
            self.animations_enabled = True
        
        # If enabled is provided, use it; otherwise toggle
        if enabled is not None:
            self.animations_enabled = enabled
        else:
            self.animations_enabled = not self.animations_enabled
        
        # Update UI to reflect the change
        if hasattr(self, 'animations_action'):
            self.animations_action.setChecked(self.animations_enabled)
    
    def statusBar(self):
        """Get the status bar from the parent application"""
        if hasattr(self, 'app') and hasattr(self.app, 'statusBar'):
            return self.app.statusBar()
        return None

    def _on_recache_template(self, template_name):
        """Recache a specific template to update from original sources"""
        print(f"[ACTION] Recaching template: {template_name}")
        
        # Call the template manager's recache method
        if hasattr(self.template_manager, 'recache_template'):
            success = self.template_manager.recache_template(template_name)
            
            # Show feedback to user
            from PyQt5.QtWidgets import QMessageBox
            if success:
                QMessageBox.information(self, "Recache Complete", 
                    f"Template '{template_name}' has been recached successfully.")
            else:
                QMessageBox.warning(self, "Recache Failed", 
                    f"Failed to recache template '{template_name}'.")
        else:
            print(f"[ERROR] Template manager does not support recaching")
    
    def _on_clear_template_cache(self, template_name):
        """Clear the cache for a specific template"""
        print(f"[ACTION] Clearing cache for template: {template_name}")
        
        # Call the template manager's safe clear cache method
        if hasattr(self.template_manager, 'safe_clear_template_cache'):
            success = self.template_manager.safe_clear_template_cache(template_name)
            
            # Show feedback to user (only on success, since the safe method shows its own warnings)
            from PyQt5.QtWidgets import QMessageBox
            if success:
                QMessageBox.information(self, "Cache Cleared", 
                    f"Cache for template '{template_name}' has been cleared successfully.")
        else:
            print(f"[ERROR] Template manager does not support safe cache clearing")