#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QDesktopWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QComboBox, \
     QPushButton, QLineEdit, QFrame, QGridLayout, QMessageBox, QApplication, QSizePolicy, QTabWidget, QMainWindow, QDockWidget, QToolButton, QButtonGroup, QMenu, QAction, QShortcut, QInputDialog, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QPoint, QModelIndex, QItemSelectionModel, QItemSelection
from PyQt5.QtGui import QKeySequence, QDrag, QPixmap, QPainter, QColor, QPalette
import re
import os
import json

# Import modular components
from app.templates.gallery_ui_setup import GalleryUISetup
from app.templates.gallery_folders import GalleryFoldersSetup
from app.templates.gallery_templates import GalleryTemplatesSetup
from app.templates.gallery_events import GalleryEvents
from app.core.import_export_manager import import_template
from app.ui.views.template_table_view import TemplateTableView
from app.ui.gallery.components.template_card import TemplateCard
from app.ui.gallery.components.template_folder_card import TemplateFolderCard
from app.templates.components.template_folder_list_item import TemplateFolderListItem
from app.templates.components.menu_actions import ContextMenu
from app.gallery.selection_manager import GallerySelectionManager # Add this import

class TemplateGallery(QWidget):
    """Main widget for displaying and managing templates"""
    
    template_selected = pyqtSignal(dict)
    folder_selected = pyqtSignal(str)
    
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.parent = parent
        self.template_manager = app.template_manager if app else None
        
        # Initialize selection manager
        self.selection_manager = GallerySelectionManager(self)
        # Connect its signal to a handler that will update the UI
        self.selection_manager.selection_changed.connect(self._handle_selection_manager_update)
        
        # UI state tracking - some of this will be deprecated by selection_manager
        self.current_category = "All"
        self.current_folder = None
        self.current_search = ""
        # self.selected_template = None # Managed by selection_manager
        self.selected_folder = None # This is for folders, not templates
        self.folder_cards = []
        self.template_cards = []
        # self.multi_selected_templates = []  # Managed by selection_manager
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
    
    def _handle_selection_manager_update(self, primary_selected, multi_selected_list):
        """Called when the GallerySelectionManager signals a change in selection."""
        print(f"🔍 GALLERY: Selection Manager reported update. Primary: {primary_selected.get('name') if primary_selected else 'None'}, Multi: {[t.get('name') for t in multi_selected_list]}")
        
        # _update_selection_ui is now the canonical method for updating all selection visuals
        # Call it via a single shot timer to allow the current event cycle to complete.
        if hasattr(self, '_update_selection_ui'):
            QTimer.singleShot(0, self._update_selection_ui)
        
        # Update button state immediately is fine
        self._update_button_state()

        if primary_selected:
            self.template_selected.emit(primary_selected)
        else:
            self.template_selected.emit({})

    # Gallery population methods
    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates based on current filters"""
        if not self.template_manager:
            print("No template manager available")
            return

        print(f"[DEBUG] Gallery: Populating gallery. Current folder: {self.current_folder}, View mode: {self.view_mode}")
        
        # Always reload templates and folder structures from the manager
        # This ensures data freshness, especially after operations like add/delete/rename
        if hasattr(self.app.template_manager, 'template_io') and hasattr(self.app.template_manager.template_io, 'load_templates'):
            self.app.template_manager.template_io.load_templates() # Ensure templates are fresh from the IO layer
            print("[DEBUG] Gallery: Templates reloaded via template_io.")
        else:
            print("[ERROR] Gallery: Could not call template_io.load_templates. Template data may be stale.")
            
        if hasattr(self.app.template_manager, 'load_folders') and callable(self.app.template_manager.load_folders):
            self.app.template_manager.load_folders() # Ensure folder structure is fresh
            print("[DEBUG] Gallery: Folders reloaded via template_manager.load_folders().")
        else:
            print("[ERROR] Gallery: Could not call template_manager.load_folders. Folder data may be stale.")

        all_templates_list = self.app.template_manager.get_all_templates()
        # self.app.template_manager.folders is expected to be a dict like: {"FolderName": ["template_name1", ...]}
        # self.app.template_manager.get_folders() returns a list of folder names.
        actual_folders_dict = self.app.template_manager.folders if hasattr(self.app.template_manager, 'folders') else {}
        folder_names_list = list(actual_folders_dict.keys()) if isinstance(actual_folders_dict, dict) else []

        items_for_table = []

        # 1. Add Folder Items
        if isinstance(actual_folders_dict, dict):
            for folder_name in actual_folders_dict.keys(): # Iterate keys of the actual dictionary
                items_for_table.append({
                    'name': folder_name,
                    'is_folder': True,
                    'parent_folder': None, # Folders are always at the root level in this implementation
                    'category': 'Folder', # Special category for filtering/display
                    'created': None, # No timestamps for folders
                    'modified': None
                })
        
        # 2. Add Template Items
        # Create a reverse map for quick lookup of a template's folder
        template_to_folder_map = {}
        if isinstance(actual_folders_dict, dict):
            for folder_name, template_names_in_folder in actual_folders_dict.items():
                if isinstance(template_names_in_folder, list):
                    for tmpl_name in template_names_in_folder:
                        template_to_folder_map[tmpl_name] = folder_name

        if isinstance(all_templates_list, list):
            for template_dict in all_templates_list:
                if not isinstance(template_dict, dict) or 'name' not in template_dict:
                    print(f"[WARNING] Gallery: Invalid template format found: {template_dict}")
                    continue

                template_name = template_dict['name']
                parent_folder = template_to_folder_map.get(template_name, "ROOT") # "ROOT" if not in any folder

                # Prepare template item data, ensuring all expected keys by populate_data are present
                item_data = {
                    'name': template_name,
                    'is_folder': False,
                    'parent_folder': parent_folder,
                    'category': template_dict.get('category'),
                    'created': template_dict.get('created'),
                    'modified': template_dict.get('modified'),
                    'structure': template_dict.get('structure'), # Should be bool or evaluated to bool
                    # Add any other fields expected by template_table_view.populate_data or its delegates
                }
                items_for_table.append(item_data)
        
        # Store items for potential reuse (e.g., in delayed population)
        self.current_templates_to_display = items_for_table
        
        # Setup visibility of sections and navigation based on current state
        if self.current_folder:
            # Inside a specific folder view
            if hasattr(self, 'folders_section') and self.folders_section.isVisible():
                 self.folders_section.setVisible(False) # Hide folders section when inside a folder
            if hasattr(self, 'templates_section') and not self.templates_section.isVisible():
                 self.templates_section.setVisible(True)

            # Show folder navigation elements
            if hasattr(self, 'folder_nav') and not self.folder_nav.isVisible():
                self.folder_nav.setVisible(True)
            if hasattr(self, 'back_button') and not self.back_button.isVisible():
                self.back_button.setVisible(True)
                print(f"🔍 LISTENER: Ensuring back button is visible for folder '{self.current_folder}'")
            if hasattr(self, 'folder_label'):
                self.folder_label.setText(f"Folder: {self.current_folder}")
                if not self.folder_label.isVisible(): self.folder_label.show()
        else:
            # Root view (not inside a folder)
            # Always hide folder navigation elements at root level
            if hasattr(self, 'folder_nav') and self.folder_nav.isVisible():
                 self.folder_nav.setVisible(False)
            if hasattr(self, 'back_button') and self.back_button.isVisible():
                 self.back_button.setVisible(False)
            if hasattr(self, 'folder_label') and self.folder_label.isVisible():
                 self.folder_label.hide()

            # Show folders section at root level unless filtering by category/search
            if self.current_category == "All" and not self.current_search:
                # No filtering - show folders section
                if hasattr(self, 'folders_section') and not self.folders_section.isVisible():
                     self.folders_section.setVisible(True)
                
                # Populate folders section based on folder_view_mode
                folder_list_for_ui = [{'name': fn, 'is_folder': True} for fn in folder_names_list]
                if self.folder_view_mode == "grid":
                    GalleryFoldersSetup.populate_folders_grid(self, folder_list_for_ui)
                else:  # list mode for folders
                    GalleryFoldersSetup.populate_folders_list(self, folder_list_for_ui)
            else:
                # Filtering by category or search - hide folders section
                if hasattr(self, 'folders_section') and self.folders_section.isVisible():
                     self.folders_section.setVisible(False)

        # Prepare the filtered templates list for the current context (template view):
        if self.current_folder:
            # Inside a folder - show only templates belonging to that folder
            templates_for_current_view = [
                item for item in items_for_table 
                if not item['is_folder'] and item['parent_folder'] == self.current_folder
            ]
        else:
            # Root view - handling depends on view mode
            if self.view_mode == "grid":
                # For grid view at root, show only ROOT templates (not in folders)
                templates_for_root_grid = [
                    item for item in items_for_table 
                    if not item['is_folder'] and item['parent_folder'] == "ROOT"
                ]
                
                # Apply category and search filters for templates in grid view
                filtered_templates = []
                for item in templates_for_root_grid:
                    passes_category = True
                    if self.current_category != "All" and "category" in item:
                        passes_category = (item["category"] == self.current_category)
                    
                    passes_search = True
                    if self.current_search:
                        search_term = self.current_search.lower()
                        name = item.get('name', '').lower()
                        description = item.get('description', '').lower()
                        category = item.get('category', '').lower()
                        passes_search = (search_term in name or 
                                         search_term in description or 
                                         search_term in category)
                    
                    if passes_category and passes_search:
                        filtered_templates.append(item)
                
                templates_for_current_view = filtered_templates
            else:
                # For list view, we should ONLY show templates at the root level (no folders)
                # Templates that are inside folders should not be visible at root level
                root_templates_only = [
                    item for item in items_for_table 
                    if not item['is_folder'] and item['parent_folder'] == "ROOT"
                ]
                
                # Apply category and search filters to root-level templates
                filtered_templates = []
                for item in root_templates_only:
                    passes_category = True
                    if self.current_category != "All" and "category" in item:
                        passes_category = (item["category"] == self.current_category)
                    
                    passes_search = True
                    if self.current_search:
                        search_term = self.current_search.lower()
                        name = item.get('name', '').lower()
                        description = item.get('description', '').lower()
                        category = item.get('category', '').lower()
                        passes_search = (search_term in name or 
                                         search_term in description or 
                                         search_term in category)
                    
                    if passes_category and passes_search:
                        filtered_templates.append(item)
                
                templates_for_current_view = filtered_templates
                print(f"[DEBUG] List View: Filtered to {len(filtered_templates)} root-level templates (NO folders)")

        # Populate the appropriate view based on current mode
        if self.view_mode == "grid":
            GalleryTemplatesSetup.populate_templates_grid(self, templates_for_current_view)
        else:  # list mode (TemplateTableView)
            # Pass the filtered items to populate_templates_list
            GalleryTemplatesSetup.populate_templates_list(self, templates_for_current_view)
            
            # Configure the proxy model filter
            if hasattr(self.template_table_view, 'model') and self.template_table_view.model():
                proxy_model = self.template_table_view.model()
                if hasattr(proxy_model, 'set_current_filter_folder'):
                    proxy_model.set_current_filter_folder(self.current_folder)
                else:
                    print("[ERROR] Proxy model does not have set_current_filter_folder method.")
            else:
                print("[ERROR] Could not get proxy model to set filter folder.")

        # Final UI updates
        self._update_card_sizes()
        self._update_button_state()
        self.templates_loaded = True
        
        if hasattr(self, 'templates_section'): # Ensure sections are updated
            self.templates_section.update()
            self.templates_section.repaint()
        QApplication.processEvents()
    
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
    
    def _on_template_select(self, template_data):
        """Handle template selection by delegating to GalleryEvents, being mindful of multi-selection state."""
        template_name = template_data.get('name', 'Unknown') if isinstance(template_data, dict) else 'Unknown'
        
        # Default to clearing multi-selection for a standard click.
        should_clear_multi = True 

        # If the clicked item is already part of an existing multi-selection in the manager,
        # a simple click on it (which this is, as _on_table_item_clicked doesn't pass modifiers)
        # should ideally not clear the other selected items if the user intends to drag the group
        # or perform a context menu action on them.
        # The QTableView's selection model (handled by _on_table_selection_changed) will ultimately
        # determine the selection state based on actual user interaction with modifiers.
        # This logic here tries to prevent _this_ specific call path from prematurely destroying
        # a multi-selection state in the manager that might be valid.
        
        is_part_of_manager_multi_select = False
        if self.selection_manager and self.selection_manager.multi_selected_templates: # Check if selection_manager and list exist
            if any(t.get('name') == template_name for t in self.selection_manager.multi_selected_templates):
                is_part_of_manager_multi_select = True
        
        if is_part_of_manager_multi_select:
            # If the clicked item is already in the manager's multi-select list,
            # this specific call path should not clear the multi-selection.
            # It will effectively just ensure this item is primary.
            print(f"[DEBUG] GalleryWidget._on_template_select: Clicked '{template_name}' is part of manager's multi-select. Setting clear_multi=False.")
            should_clear_multi = False
        # else:
            # Clicked item is not part of an existing multi-selection in the manager,
            # or there is no multi-selection. So, this click should result in a single selection.
            # print(f"[DEBUG] GalleryWidget._on_template_select: Clicked '{template_name}' is NOT part of manager's multi-select or no multi-select. Setting clear_multi=True.")
            # should_clear_multi remains True

        GalleryEvents.on_template_select(self, template_data, clear_multi=should_clear_multi)
        
    def on_template_multi_select(self, template, add_to_selection):
        """Handles multi-selection of templates by delegating to SelectionManager.
        
        Args:
            template: The template data (dict) of the clicked item.
            add_to_selection: Boolean, True if Ctrl/Cmd modifier was active, indicating an intention
                              to add/toggle selection. False implies a simple click (though this method
                              is typically called with True for modifier clicks from cards).
        """
        template_name = template.get('name', 'Unknown')
        # print(f"[INFO] GalleryWidget: on_template_multi_select for '{template_name}', add_to_selection: {add_to_selection}. Delegating to SelectionManager.")

        # add_to_selection (from card click) directly corresponds to is_ctrl_cmd_modifier
        # Shift modifier is not explicitly passed from card clicks in current setup, so False.
        self.selection_manager.handle_item_interaction(
            template_data=template,
            is_ctrl_cmd_modifier=add_to_selection, # True if Ctrl/Cmd was pressed
            is_shift_modifier=False # Cards don't explicitly send shift state this way
        )

    def _clear_multi_selection(self):
        """Clear all multi-selected templates - NOW USES SELECTION MANAGER"""
        print(f"[DEPRECATED] _clear_multi_selection. Use SelectionManager.")
        self.selection_manager.clear_multi_selection_list(emit_signal=True)

    def _delete_selected_templates(self):
        """Delete all selected templates"""
        # Use selection_manager to get multi_selected_templates
        if not self.selection_manager.multi_selected_templates:
            return
            
        # Get template names
        template_names = [t.get('name', 'Unknown') for t in self.selection_manager.multi_selected_templates]
        
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
                
            # Clear multi-selection (via manager)
            # self._clear_multi_selection() # Old way
            self.selection_manager.clear_all_selections(emit_signal=True)
            
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
    
    def _on_edit_template(self, template_name=None, template=None):
        """Handle edit template button click in template gallery
        
        Can be called with either:
        - template_name: String name of the template to edit
        - template: Complete template object dictionary including structure
        
        The function will ensure the proper structure is loaded in both cases.
        """
        print(f"🔹 GALLERY EVENTS: Edit template requested")
        
        # If a full template object is provided, use it directly
        if template is not None and isinstance(template, dict):
            print(f"🔹 GALLERY EVENTS: Using provided template object for '{template.get('name', 'Unknown')}'")
            # Make sure the template has a structure (should have been loaded by the caller)
            if 'structure' not in template or not template['structure']:
                print(f"⚠️ GALLERY EVENTS: Template object doesn't have structure, loading it")
                # Get structure name from template
                structure_name = template.get('structure_name')
                if not structure_name:
                    template_name = template.get('name', '')
                    structure_name = f"Template_{template_name}"
                
                # Try to load the structure
                if hasattr(self, 'template_manager') and hasattr(self.template_manager, 'get_structure'):
                    structure = self.template_manager.get_structure(structure_name)
                    if structure:
                        template['structure'] = structure
                        print(f"🔹 GALLERY EVENTS: Successfully loaded structure for template")
                    else:
                        print(f"⚠️ GALLERY EVENTS: No structure found for template, using empty structure")
                        template['structure'] = []
            
            # Now pass just the template name to GalleryEvents
            template_name = template.get('name', '')
            if template_name:
                template_with_structure = template  # Save for later use
                
                try:
                    # Call the gallery events handler with the template name first
                    # This ensures it follows the correct code path for obtaining the structure
                    GalleryEvents.on_edit_template(self, template_name)
                except Exception as e:
                    # If there's an error, we'll try a direct approach using our template with structure
                    print(f"⚠️ GALLERY EVENTS: Error in regular edit path: {e}, trying direct approach")
                    from app.ui.structure_editor_functions import show_enhanced_structure_editor
                    
                    # Open the structure editor directly with our template's structure
                    result, updated_structure, updated_structure_name, _, updated_template_name, category, description = show_enhanced_structure_editor(
                        parent=self,
                        structure_name=template_with_structure.get('structure_name', f"Template_{template_name}"),
                        structure=template_with_structure.get('structure', []),
                        is_new=False,
                        template_name=template_name,
                        focus_name_field=False,
                        template_manager=self.template_manager if hasattr(self, 'template_manager') else None
                    )
                    
                    if result:
                        print(f"🔍 LISTENER: Successfully edited template '{updated_template_name}'")
                        
                        # Force refresh gallery to show the updated template
                        self.populate_gallery(force_refresh=True)
                        
                        # Select the updated template
                        if hasattr(self, 'select_template'):
                            self.select_template(updated_template_name)
            return
            
        # Use either the provided template name or get it from the selected template
        if template_name is None and hasattr(self, 'selected_template') and self.selected_template:
            template_name = self.selected_template.get('name', '')
            
        # Make sure we have a template name
        if not template_name:
            print(f"⚠️ GALLERY EVENTS: No template selected for editing")
            return
            
        # Delegate to the GalleryEvents handler which will load the structure
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
        """Handle icon scale slider changes"""
        # This method is called when the icon scale slider changes.
        # It updates the icon_scale attribute and then calls the
        # GalleryEvents handler to update the UI.
        self.icon_scale = value
        self._update_folder_card_sizes(value) # Changed line

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
        # Add debug print for key press events
        print(f"[DEBUG] Gallery keyPressEvent: key={event.key()}, modifiers={event.modifiers()}")
        
        # Let the GalleryEvents handle all keyboard events including deletion.
        # GalleryEvents.key_press_event should return True if it handled the event (e.g., accepted it).
        if GalleryEvents.key_press_event(self, event):
            # If GalleryEvents handled the event (returned True and accepted it),
            # we might not need to do anything further or call super().
            # The event.accept() within key_press_event should prevent propagation to parent widgets.
            # For clarity, explicitly return here if handled.
            return 
        
        # If the event was not handled by GalleryEvents (returned False or None),
        # or if it didn't accept the event, allow default processing by the base class.
        super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events by delegating to GalleryEvents for blank space clicks."""
        # Delegate to GalleryEvents for logic regarding blank space clicks.
        # GalleryEvents.mouse_press_event will return True if it handled the event (e.g., cleared selection).
        handled_by_events = False
        if hasattr(GalleryEvents, 'mouse_press_event'): # Ensure method exists
            # Pass self (the gallery instance) which now has selection_manager
            handled_by_events = GalleryEvents.mouse_press_event(self, event) 
        
        # If GalleryEvents did not handle the event (e.g., it was a card click, or not relevant),
        # or if the event was ignored by GalleryEvents, let the base class handle it for normal propagation
        # (e.g., to allow card clicks to be processed by cards themselves).
        if not handled_by_events and not event.isAccepted():
            super().mousePressEvent(event)
        # If handled_by_events is True and event was accepted by GalleryEvents, we do nothing more here.
        
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
            num_selected = len(self.selection_manager.multi_selected_templates) # Use manager
            # Multi-select is true if > 1 selected, OR if 1 is selected but it's NOT the card clicked on
            is_multi_select = num_selected > 1 or \
                              (num_selected == 1 and self.selection_manager.multi_selected_templates[0].get('name') != template_name)
            print(f"DEBUG: Multi-select active: {is_multi_select}, Count: {num_selected}")

            # Determine which template names to process (single or multi)
            if is_multi_select:
                names_to_process = [t.get('name') for t in self.selection_manager.multi_selected_templates if t and t.get('name')]
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

            # Add "No Folder" option
            root_action = move_menu.addAction("No Folder")
            root_action.triggered.connect(lambda: GalleryEvents.on_move_template_to_folder(
                self, names_to_process, None # Pass None instead of 'root'
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
            # Use manager for primary_template
            primary_template = self.selection_manager.selected_template if num_selected == 1 and not is_multi_select else \
                               (self.selection_manager.multi_selected_templates[0] if num_selected > 0 else None)
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
                    self.selection_manager.set_primary_selection(card.template if 'card' in locals() else template) # New
                    
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
                self.selection_manager.set_primary_selection(template)
                
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
                                self.selection_manager.set_primary_selection(card.template)
                                
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
        name_item = source_model.item(source_index.row(), 0) # Assuming Name is column 0

        if not name_item:
            print(f"[WARNING] _on_table_item_clicked: Could not get name_item for index {index.row()}, {index.column()}")
            return

        template_name = name_item.text()
        # print(f"DEBUG: Table item clicked: {template_name}") # Reduced verbosity
        
        template_data = self.template_manager.get_template_by_name(template_name)
        
        if template_data:
            # Ensure structure is loaded into template_data, as subsequent handlers might expect it.
            current_structure = template_data.get('structure')
            if not current_structure: # Only load if not already present or is an empty list/None
                structure_to_set = None
                structure_name_from_template = template_data.get('structure_name', f"Template_{template_name}")
                loaded_structure = self.template_manager.get_structure(structure_name_from_template)
                
                if loaded_structure:
                    structure_to_set = loaded_structure
                else: 
                    loaded_structure = self.template_manager.get_structure(template_name)
                    if loaded_structure:
                         structure_to_set = loaded_structure

                if not structure_to_set and 'file_path' in template_data and os.path.exists(template_data['file_path']):
                    try:
                        with open(template_data['file_path'], 'r', encoding='utf-8') as f:
                            raw_file_data = json.load(f)
                            if isinstance(raw_file_data, dict) and 'structure' in raw_file_data:
                                structure_to_set = raw_file_data['structure']
                    except Exception: # nosec B110
                        pass 

                template_data['structure'] = structure_to_set if structure_to_set is not None else []
                # if structure_to_set is not None:
                #     print(f"DEBUG: _on_table_item_clicked: Loaded/ensured structure for '{template_name}'")
                # else:
                #     print(f"DEBUG: _on_table_item_clicked: No structure found for '{template_name}', using empty list.")
            
            # The selection logic below is removed because _on_table_selection_changed (connected to the
            # table's selectionModel().selectionChanged signal) is now the primary way the gallery_widget
            # syncs with the table view's selection state. _on_table_selection_changed
            # correctly uses keyboard modifiers and updates the GallerySelectionManager.
            # Keeping the logic below would cause interference or redundant processing.
            # The original logic was:
            # is_currently_selected_in_manager = False
            # if self.selection_manager:
            #     clicked_item_name = template_data.get('name')
            #     if self.selection_manager.selected_template and self.selection_manager.selected_template.get('name') == clicked_item_name:
            #         is_currently_selected_in_manager = True
            #     elif any(t.get('name') == clicked_item_name for t in self.selection_manager.multi_selected_templates):
            #         is_currently_selected_in_manager = True

            # if is_currently_selected_in_manager:
            #     print(f"[DEBUG] _on_table_item_clicked: Clicked item '{template_name}' IS in manager's selection. Setting as primary (preserving multi-select).")
            #     GalleryEvents.on_template_select(self, template_data, clear_multi=False)
            # else:
            #     print(f"[DEBUG] _on_table_item_clicked: Clicked item '{template_name}' is NOT in manager's selection. No action taken by _on_table_item_clicked.")
            #     pass
            pass # Explicitly do nothing regarding selection in this click handler.
        else:
            print(f"[WARNING] _on_table_item_clicked: Could not find template data for '{template_name}'")

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
            
            # Get the complete template data with structure
            template_data = self.template_manager.get_template_by_name(template_name)
            
            # Ensure the structure is loaded
            if template_data:
                # Try multiple approaches to get the structure
                
                # 1. First try explicitly getting the structure from template_manager
                structure_name = template_data.get('structure_name', f"Template_{template_name}")
                structure = self.template_manager.get_structure(structure_name)
                
                # 2. If that didn't work, try alternate structure name
                if not structure:
                    structure = self.template_manager.get_structure(template_name)
                
                # 3. If still no structure, try to extract it directly from the template file
                if not structure and 'file_path' in template_data and os.path.exists(template_data['file_path']):
                    try:
                        print(f"DEBUG: Attempting to extract structure directly from template file: {template_data['file_path']}")
                        with open(template_data['file_path'], 'r', encoding='utf-8') as f:
                            raw_template_data = json.load(f)
                            if isinstance(raw_template_data, dict) and 'structure' in raw_template_data:
                                structure = raw_template_data['structure']
                                print(f"DEBUG: Successfully extracted structure from template file")
                    except Exception as extract_err:
                        print(f"DEBUG: Error extracting structure from template file: {extract_err}")
                
                # 4. If we have a structure now, set it on the template data
                if structure:
                    template_data['structure'] = structure
                    print(f"DEBUG: Successfully loaded structure for template '{template_name}'")
                else:
                    print(f"⚠️ GALLERY EVENTS: No structure found for template, using empty structure")
                    # Initialize with empty structure - can be edited in the structure editor
                    template_data['structure'] = []
            
                # Trigger the edit action with the complete template data
                self._on_edit_template(template=template_data)
            else:
                print(f"⚠️ GALLERY EVENTS: Could not find template '{template_name}'")
        else:
            print(f"⚠️ GALLERY EVENTS: Could not find template '{template_name}'")

    def _on_table_header_clicked(self, logicalIndex):
        """Handle click on a table header section to trigger sorting."""
        header_view = self.template_table_view.horizontalHeader()
        model = header_view.model() # Get the model associated with the header
        sort_field = model.headerData(logicalIndex, Qt.Horizontal, Qt.DisplayRole)
        
        if sort_field:
            print(f"DEBUG: Table header clicked: Index={logicalIndex}, Field='{sort_field}'")
            # Call the sorting function from GalleryTemplatesSetup
            GalleryTemplatesSetup.set_template_sort(self, sort_field)
            
            # After sorting, ensure we're using correct filtered data (only root templates, not subfolder ones)
            self.populate_gallery(force_refresh=True)
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
        # Check if index at click position is valid
        index_at_pos = table_view.indexAt(position)
        is_blank_area = not index_at_pos.isValid()
        
        print(f"DEBUG: Showing table context menu for: {[t.get('name') for t in selected_templates]}")
        print(f"DEBUG: Number of selected templates for context menu: {num_selected}")
        print(f"DEBUG: Clicked on blank area: {is_blank_area}")

        # Use the custom ContextMenu for consistent styling
        menu = ContextMenu(self.template_table_view)
        
        # --- If clicked on a blank area, show background context menu ---
        if is_blank_area:
            print("DEBUG: Showing context menu for table background")
            import_action = menu.addAction("Import Template...")
            add_folder_action = menu.addAction("Add Folder")
            add_template_action = menu.addAction("Add Template")
            
            # Ensure self.app exists and is valid
            if hasattr(self, 'app') and self.app:
                import_action.triggered.connect(lambda: import_template(self.app))
                add_folder_action.triggered.connect(self._on_add_folder)
                add_template_action.triggered.connect(self._on_add_template)
            else:
                print("[WARNING] Table context menu: Cannot connect actions, self.app is not available.")
                import_action.setEnabled(False)
                add_folder_action.setEnabled(False)
                add_template_action.setEnabled(False)
            
            menu.exec_(self.template_table_view.viewport().mapToGlobal(position))
            return
        
        # If no items are selected, don't show the item context menu
        if num_selected == 0:
            return
            
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
             # GalleryEvents.on_delete_template(self, names_to_process)
             # Instead of passing names_to_process, call on_delete_template with no parameter
             # It will use the selection manager internally to determine what to delete
             GalleryEvents.on_delete_template(self)
        
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

        # Add "No Folder" option - ALWAYS add this if items are selected
        root_action = move_menu.addAction("No Folder")
        # Ensure names_to_process is captured correctly by the lambda
        root_action.triggered.connect(lambda checked, ntp=list(names_to_process): GalleryEvents.on_move_template_to_folder(
            self, ntp, None # Pass None instead of 'root'
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
        # Use manager for primary_template
        primary_template = self.selection_manager.selected_template if num_selected == 1 and not is_multi_select else \
                           (self.selection_manager.multi_selected_templates[0] if num_selected > 0 else None)
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
        """Handles clicks on template items (cards or list rows) by delegating to SelectionManager."""
        template_name = template.get('name') if isinstance(template, dict) else None
        if not template_name:
            print("[ERROR] TemplateGallery: Template item press with invalid template data.")
            return

        # print(f"🔍 GALLERY: Delegating press for '{template_name}', modifier: {is_modifier_click} to SelectionManager")
        self.selection_manager.handle_item_interaction(
            template_data=template,
            is_ctrl_cmd_modifier=is_modifier_click,
            is_shift_modifier=False # Assuming old is_modifier_click did not distinguish Shift
        )
        # The selection_manager will emit selection_changed, which gallery_widget listens to 
        # via _handle_selection_manager_update, which then calls _update_selection_ui and emits template_selected.

    # --- End Unified Selection Handler ---
    
    # --- Update Selection UI (Restored) ---
    def _update_selection_ui(self):
        """Updates the visual selection state of all items (cards/rows)."""
        from PyQt5.QtCore import QModelIndex, QItemSelectionModel, Qt
        from PyQt5.QtWidgets import QAbstractItemView
        
        print(f"[DEBUG _update_selection_ui] START")
        # Access selection state through the selection_manager
        primary_template = self.selection_manager.selected_template
        multi_templates = self.selection_manager.multi_selected_templates

        is_multi_select_mode = len(multi_templates) > 1
        primary_selected_name = primary_template.get('name') if primary_template else None
        multi_selected_names = {t.get('name') for t in multi_templates if isinstance(t, dict) and t.get('name')}

        # print(f"[DEBUG _update_selection_ui] Primary: {primary_selected_name}, Multi count: {len(multi_selected_names)}, Is multi mode: {is_multi_select_mode}")

        # Update Template Cards
        for card in self.template_cards:
            card_template_name = card.template_name()
            is_primary = card_template_name == primary_selected_name
            is_multi = card_template_name in multi_selected_names

            # print(f"[DEBUG _update_selection_ui]  Card '{card_template_name}': is_primary={is_primary}, is_multi_selected_for_style={is_multi}")
            card.set_multi_selected(is_multi) # Style for being part of a multi-selection
            card.set_selected(is_primary)    # Style for being the primary selection (takes precedence if also multi)

        # Update Table View (if it exists and is visible)
        if self.template_table_view and self.template_table_view.isVisible():
            model = self.template_table_view.model() # Use the proxy model
            selection_model = self.template_table_view.selectionModel()
            if not model or not selection_model:
                print("WARNING: No model or selection model found for table view during UI update")
                return

            # --- IMPORTANT CHANGE: --- # 
            # The table view's selection is now primarily driven by user interaction (clicks + modifiers)
            # and QTableView's native ExtendedSelection behavior. _on_table_selection_changed reads this
            # native selection and updates GallerySelectionManager.
            # Therefore, _update_selection_ui (called from manager updates) should NOT try to reset/
            # re-apply selection to the table view itself, as it should already be visually correct.
            # We only need to ensure the *current focused index* in the table matches the manager's primary.

            selection_model.blockSignals(True) # Still good to block signals during sync

            primary_model_index_to_set = QModelIndex()
            if primary_selected_name:
                # Find the row for the primary_selected_name
                for row in range(model.rowCount()):
                    index = model.index(row, 0)
                    if index.isValid() and model.data(index, Qt.DisplayRole) == primary_selected_name:
                        primary_model_index_to_set = index
                        break
            
            # Sync the focused item (currentIndex)
            if primary_model_index_to_set.isValid():
                # --- MODIFIED SECTION START ---
                # Only explicitly select if not already selected by the table's model
                if not selection_model.isSelected(primary_model_index_to_set):
                    selection_model.select(primary_model_index_to_set, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                    print(f"[DEBUG _update_selection_ui] Table: Explicitly selected primary index r{primary_model_index_to_set.row()} ({primary_selected_name}) because it wasn't selected in the view's model.")
                else:
                    print(f"[DEBUG _update_selection_ui] Table: Primary index r{primary_model_index_to_set.row()} ({primary_selected_name}) already selected in view's model. Not re-selecting.")
                # --- MODIFIED SECTION END ---

                if self.template_table_view.currentIndex() != primary_model_index_to_set:
                    self.template_table_view.setFocus() 
                    self.template_table_view.setCurrentIndex(primary_model_index_to_set)
                    print(f"[DEBUG _update_selection_ui] Table: Synced current table index to row {primary_model_index_to_set.row()} ({primary_selected_name}).")
                    # RE-ASSERT SELECTION for the new current index if it should be selected
                    if primary_selected_name in multi_selected_names: # Check against the manager's state
                        selection_model.select(primary_model_index_to_set, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                        print(f"[DEBUG _update_selection_ui] Table: Re-asserted selection for newly set current index r{primary_model_index_to_set.row()} ({primary_selected_name}).")
                else:
                    print(f"[DEBUG _update_selection_ui] Table: Primary index r{primary_model_index_to_set.row()} ({primary_selected_name}) is already current. Not resetting currentIndex.")
                    # EVEN IF ALREADY CURRENT, RE-ASSERT SELECTION if it should be selected according to manager
                    if primary_selected_name in multi_selected_names and not selection_model.isSelected(primary_model_index_to_set):
                        selection_model.select(primary_model_index_to_set, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                        print(f"[DEBUG _update_selection_ui] Table: Re-asserted selection for already current index r{primary_model_index_to_set.row()} ({primary_selected_name}) as it was not selected in view.")

                 # Optional: scroll to it if it was set by other means (e.g. card click)
                 # self.template_table_view.scrollTo(primary_model_index_to_set, QAbstractItemView.PositionAtCenter)
            elif not primary_selected_name and self.template_table_view.currentIndex().isValid():
                 self.template_table_view.setCurrentIndex(QModelIndex()) # Clear current index if manager has no primary
                 print(f"[DEBUG _update_selection_ui] Table: Cleared current table index as manager has no primary.")

            # No longer clearing and re-selecting rows here.
            # No longer calling repaint() here, native selection change should handle it.

            selection_model.blockSignals(False)
            print(f"[DEBUG _update_selection_ui] Table: Unblocked table selection signals. Current focused index: r{self.template_table_view.currentIndex().row()}")

        print(f"[DEBUG _update_selection_ui] END")
    # --- End Update Selection UI ---
    
    # --- Table Selection Handler (Restored) ---
    def _on_table_selection_changed(self, selected, deselected):
        """Handles selection changes in the TemplateTableView by informing the SelectionManager.

        Args:
            selected (QItemSelection): The items that were just selected.
            deselected (QItemSelection): The items that were just deselected.
        """
        print(f"[DEBUG _on_table_selection_changed] START")
        # print(f"  Selected: {len(selected.indexes())} indexes, Deselected: {len(deselected.indexes())} indexes")

        if not self.template_table_view or not self.template_table_view.model():
            print("[WARN] GalleryWidget: Table view or model not available in _on_table_selection_changed.")
            return

        proxy_model = self.template_table_view.model()
        source_model = proxy_model.sourceModel()
        if not source_model:
            print("[WARN] GalleryWidget: Source model not available.")
            return

        current_modifiers = QApplication.keyboardModifiers()
        is_ctrl_cmd_click = (current_modifiers & Qt.ControlModifier) or (current_modifiers & Qt.MetaModifier)
        is_shift_click = bool(current_modifiers & Qt.ShiftModifier)

        # --- Helper to get template data from a QModelIndex (proxy) ---
        def get_template_data_from_proxy_index(proxy_idx):
            if proxy_idx.isValid():
                source_idx = proxy_model.mapToSource(proxy_idx)
                name_item = source_model.item(source_idx.row(), 0) # Assuming Name is column 0
                if name_item:
                    template_name = name_item.text()
                    return self.template_manager.get_template_by_name(template_name)
            return None

        # Get names of items just selected and deselected
        just_selected_data = [get_template_data_from_proxy_index(idx) for idx in selected.indexes() if idx.column() == 0]
        just_deselected_data = [get_template_data_from_proxy_index(idx) for idx in deselected.indexes() if idx.column() == 0]
        just_selected_data = [d for d in just_selected_data if d] # Filter out Nones
        just_deselected_data = [d for d in just_deselected_data if d] # Filter out Nones
        
        # print(f"  Modifiers: {current_modifiers}, Ctrl/Cmd: {is_ctrl_cmd_click}, Shift: {is_shift_click}")
        # print(f"  Just selected: {[d['name'] for d in just_selected_data]}")
        # print(f"  Just deselected: {[d['name'] for d in just_deselected_data]}")

        # --- Case 1: Special Handling for Single Cmd-Deselect ---
        # This is when Ctrl/Cmd is held (no Shift), exactly one item is deselected, and no items are selected.
        if is_ctrl_cmd_click and not is_shift_click and len(just_deselected_data) == 1 and not just_selected_data:
            item_to_remove = just_deselected_data[0]
            item_to_remove_name = item_to_remove.get('name')
            print(f"  HANDLING: Single Cmd-Deselect for '{item_to_remove_name}'")

            prev_manager_multi_list = list(self.selection_manager.multi_selected_templates)
            prev_manager_primary = self.selection_manager.selected_template
            
            # Construct new multi-list by removing the item
            final_multi_list = [t for t in prev_manager_multi_list if t.get('name') != item_to_remove_name]
            final_primary = None

            if final_multi_list:
                # If previous primary is still in the list, keep it
                if prev_manager_primary and any(t.get('name') == prev_manager_primary.get('name') for t in final_multi_list):
                    final_primary = prev_manager_primary
                else:
                    # Try to set primary to the table's current focused item, if it's in our new list
                    current_focused_proxy_idx = self.template_table_view.currentIndex()
                    focused_template_data = get_template_data_from_proxy_index(current_focused_proxy_idx)
                    if focused_template_data and any(t.get('name') == focused_template_data.get('name') for t in final_multi_list):
                        final_primary = focused_template_data
                    else:
                        # Fallback: Pick the first item in the new multi-list
                        final_primary = final_multi_list[0]
            
            # print(f"  New Primary (Cmd-Deselect): {final_primary.get('name') if final_primary else 'None'}")
            # print(f"  New Multi (Cmd-Deselect): {[t.get('name') for t in final_multi_list]}")
            
            self.selection_manager.set_selection_state(
                primary_template_data=final_primary,
                multi_selected_list=final_multi_list,
                emit_signal=True
            )

        # --- Case 2: Standard Handling for all other selection changes ---
        else:
            # print("  HANDLING: Standard selection logic")
            # Get all currently selected rows' data from the table's current state
            selected_row_indexes = self.template_table_view.selectionModel().selectedRows()
            current_table_multi_selection_data = []
            for proxy_idx in selected_row_indexes:
                template_data = get_template_data_from_proxy_index(proxy_idx)
                if template_data and template_data not in current_table_multi_selection_data:
                    current_table_multi_selection_data.append(template_data)
            
            # Determine the primary selection candidate based on the table's current (focused) index
            primary_template_candidate = None
            current_focused_proxy_idx = self.template_table_view.currentIndex()
            if current_focused_proxy_idx.isValid(): # Check if the index itself is valid
                 focused_template_data = get_template_data_from_proxy_index(current_focused_proxy_idx)
                 if focused_template_data and any(t.get('name') == focused_template_data.get('name') for t in current_table_multi_selection_data):
                     primary_template_candidate = focused_template_data
            
            # If no specific primary from focus, but there's a selection, pick the first one from the table's selection
            if not primary_template_candidate and current_table_multi_selection_data:
                primary_template_candidate = current_table_multi_selection_data[0]

            # print(f"  New Primary (Standard): {primary_template_candidate.get('name') if primary_template_candidate else 'None'}")
            # print(f"  New Multi (Standard): {[t.get('name') for t in current_table_multi_selection_data]}")

            self.selection_manager.set_selection_state(
                primary_template_data=primary_template_candidate,
                multi_selected_list=current_table_multi_selection_data,
                emit_signal=True
            )
        
        primary_name_for_log = self.selection_manager.selected_template.get('name') if self.selection_manager.selected_template else 'None'
        multi_count_for_log = len(self.selection_manager.multi_selected_templates)
        print(f"[DEBUG _on_table_selection_changed] END - Manager Updated. Primary: {primary_name_for_log}, Multi Count: {multi_count_for_log}")
             
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
        
        # Get multi-selected count from selection_manager
        multi_select_count = 0
        if hasattr(self, 'selection_manager'):
            multi_select_count = len(self.selection_manager.multi_selected_templates)

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
         """Get the primary selected template, using selection_manager if available"""
         # First try using selection_manager
         if hasattr(self, 'selection_manager'):
             return self.selection_manager.selected_template
             
         # Fall back to legacy methods if selection_manager is not available
         if hasattr(self, 'selected_template') and self.selected_template:
             return self.selected_template
             
         if hasattr(self, 'multi_selected_templates') and len(self.multi_selected_templates) == 1:
             return self.multi_selected_templates[0]
             
         return None
    # --- End Shortcut Setup and Handling ---

    # ... (Keep remaining class methods like __init__, populate_gallery, clear_gallery, event handlers, context menus etc.) ...

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
