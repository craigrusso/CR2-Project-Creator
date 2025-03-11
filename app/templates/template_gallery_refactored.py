#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer, Qt

# Import modular components
from .gallery_ui_setup import GalleryUISetup
from .gallery_folders import GalleryFoldersSetup
from .gallery_templates import GalleryTemplatesSetup
from .gallery_events import GalleryEvents

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
        self.icon_scale = 100  # Default scale in percentage
        self.folder_view_mode = "grid"  # Default to grid view for folders
        self.template_view_mode = "grid"  # Default to grid view for templates
        self.templates_loaded = False  # Track if templates have been loaded
        
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
        
        # Populate the gallery initially - do this after UI setup
        self.populate_gallery()
    
    # Gallery population methods
    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates and folders"""
        # Make sure UI is set up before populating
        if not hasattr(self, 'folders_grid') or self.folders_grid is None or not hasattr(self, 'templates_grid') or self.templates_grid is None:
            # UI not fully set up yet, defer population
            return
            
        self.clear_gallery()
        
        # Check if we have a template_manager attribute in the app
        if hasattr(self.app, 'template_manager'):
            # Use template_manager if available
            if hasattr(self.app.template_manager, 'templates'):
                templates = self.app.template_manager.templates
            else:
                templates = {}
                
            if hasattr(self.app.template_manager, 'get_folders'):
                folders = self.app.template_manager.get_folders()
            else:
                folders = []
            
            # Set visibility based on current context
            if self.current_folder:
                # Inside a folder - hide folders section, show only templates
                self.folders_section.setVisible(False)
                self.templates_section.setVisible(True)
                
                # Get templates in the current folder
                templates_to_show = GalleryTemplatesSetup.get_templates_in_folder(self, self.current_folder)
                
                # Populate templates section
                if self.template_view_mode == "grid":
                    GalleryTemplatesSetup.populate_templates_grid(self, templates_to_show)
                else:  # list mode
                    GalleryTemplatesSetup.populate_templates_list(self, templates_to_show)
            else:
                # Not in a folder - show both folders and templates
                self.folders_section.setVisible(True)
                self.templates_section.setVisible(True)
                
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
                if self.template_view_mode == "grid":
                    GalleryTemplatesSetup.populate_templates_grid(self, templates_to_show)
                else:  # list mode
                    GalleryTemplatesSetup.populate_templates_list(self, templates_to_show)
            
            # Update template card sizes
            self._update_card_sizes()
            
            # Update button states after populating
            self._update_button_state()
            
            # Mark as loaded
            self.templates_loaded = True
    
    def clear_gallery(self):
        """Clear the gallery view"""
        # Clear templates section
        if hasattr(self, 'templates_grid') and self.templates_grid:
            while self.templates_grid.count():
                item = self.templates_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Clear folders section
        if hasattr(self, 'folders_grid') and self.folders_grid:
            while self.folders_grid.count():
                item = self.folders_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Reset arrays
        self.folder_cards = []
        self.template_cards = []
    
    # Event handlers - connect to the modular handlers
    def _on_category_select(self, category):
        GalleryEvents.on_category_select(self, category)
    
    def _on_search(self, search_text):
        GalleryEvents.on_search(self, search_text)
    
    def _on_template_select(self, template):
        GalleryEvents.on_template_select(self, template)
    
    def _on_folder_select(self, folder_name):
        GalleryEvents.on_folder_select(self, folder_name)
    
    def _on_folder_enter(self, folder_name):
        GalleryEvents.on_folder_enter(self, folder_name)
    
    def _on_back_to_all(self):
        GalleryEvents.on_back_to_all(self)
    
    def _on_add_template(self):
        GalleryEvents.on_add_template(self)
    
    def _on_edit_template(self):
        GalleryEvents.on_edit_template(self)
    
    def _on_delete_template(self):
        GalleryEvents.on_delete_template(self)
    
    def _on_manage_templates(self):
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
        GalleryEvents.on_delete_folder(self)
    
    def _on_icon_scale_changed(self, value):
        GalleryEvents.on_icon_scale_changed(self, value)

    # View mode setters
    def _set_folder_view_mode(self, mode):
        GalleryFoldersSetup.set_folder_view_mode(self, mode)
    
    def _set_template_view_mode(self, mode):
        GalleryTemplatesSetup.set_template_view_mode(self, mode)

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
        
        # Get unique categories from template manager
        if hasattr(self.app, 'template_manager') and hasattr(self.app.template_manager, 'templates'):
            categories = set()
            
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
            
            # Add categories to combo box
            for category in sorted(categories):
                self.category_combo.addItem(category)
        
        # Try to restore the previous selection or default to "All"
        index = self.category_combo.findText(current)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        else:
            self.category_combo.setCurrentIndex(0)
    
    def _update_button_state(self):
        """Update the state of action buttons based on selection"""
        # Template buttons
        has_template_selected = self.selected_template is not None
        self.edit_button.setEnabled(has_template_selected)
        self.delete_button.setEnabled(has_template_selected)
        
        # Folder buttons
        has_folder_selected = self.selected_folder is not None
        
        # Special case for rename folder - don't show the button at all
        # Only enable folder delete if a folder is selected
        self.delete_folder_button.setEnabled(has_folder_selected)
    
    def _update_card_sizes(self):
        """Update card sizes after resize or scale change"""
        self._update_folder_card_sizes(self.icon_scale)
    
    def _update_folder_card_sizes(self, scale_percent):
        """Update the sizes of folder cards based on the scale percentage"""
        GalleryFoldersSetup.update_folder_card_sizes(self, scale_percent)
    
    def _handle_resize_timeout(self):
        """Handle resize event after debounce timeout"""
        self._update_layout_after_resize()
    
    def _update_layout_after_resize(self):
        """Update layout after resize"""
        # Recalculate card sizes after resize
        self._update_card_sizes()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        GalleryEvents.key_press_event(self, event)
        super().keyPressEvent(event) 