#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QDesktopWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QComboBox, \
     QPushButton, QLineEdit, QFrame, QGridLayout, QMessageBox, QApplication, QSizePolicy, QTabWidget, QMainWindow, QDockWidget, QToolButton, QButtonGroup
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal, QPoint

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
        self.template_item_map = {}  # Add this attribute for list view items
        self.multi_selected_templates = []  # Track multi-selected templates
        self.icon_scale = 100  # Default scale in percentage
        self.folder_view_mode = "grid"  # Default to grid view for folders
        self.template_view_mode = "grid"  # Default to grid view for templates
        self.templates_loaded = False  # Track if templates have been loaded
        
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
        
        # Connect the new structure button click event
        if hasattr(self, 'new_structure_button'):
            self.new_structure_button.clicked.connect(self._on_structure_editor)
        
        # Populate the gallery initially - do this after UI setup
        self.populate_gallery()
    
    # Gallery population methods
    def populate_gallery(self, force_refresh=False):
        """Populate the gallery with templates based on current filters"""
        if not self.template_manager:
            print("No template manager available")
            return
            
        # Skip if already loaded unless forced
        if self.templates_loaded and not force_refresh:
            return
            
        # Always reset multi-selection when refreshing gallery
        self.multi_selected_templates = []
        
        # Clear existing UI
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
                
                # Show folder navigation with back button
                if hasattr(self, 'folder_nav'):
                    self.folder_nav.setVisible(True)
                    
                # Ensure back button is visible
                if hasattr(self, 'back_button'):
                    self.back_button.setVisible(True)
                    print(f"🔍 LISTENER: Ensuring back button is visible in populate_gallery for folder '{self.current_folder}'")
                
                # Set the breadcrumb text
                if hasattr(self, 'breadcrumb_label'):
                    self.breadcrumb_label.setText(f"Folder: {self.current_folder}")
                    self.breadcrumb_label.show()
                
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
        if hasattr(self, 'templates_grid'):
            try:
                # Check if the grid is valid (not deleted) by calling count()
                count = self.templates_grid.count()
                for i in range(count-1, -1, -1):  # Loop backwards to avoid index issues
                    item = self.templates_grid.takeAt(i)
                    if item and item.widget():
                        item.widget().deleteLater()
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
                        item.widget().deleteLater()
            except (RuntimeError, AttributeError):
                # Handle case where grid has been deleted
                pass
        
        # Reset arrays
        self.folder_cards = []
        self.template_cards = []
        self.template_item_map = {}  # Clear the template item map as well
    
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
        
        # Ensure the primary selection is also counted properly
        if hasattr(self, 'selected_template') and self.selected_template:
            # Make sure primary is properly highlighted
            for card in self.template_cards:
                if hasattr(card, 'template') and card.template == self.selected_template and hasattr(card, 'set_selected'):
                    card.set_selected(True)
                    print(f"🔍 LISTENER: Ensuring primary selection '{self.selected_template.get('name', 'Unknown')}' stays highlighted")
        
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
    
    def _on_structure_editor(self):
        """Handle structure editor button click"""
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
                        # Create a basic template_manager with just what we need for the dropdown
                        class BasicTemplateManager:
                            def __init__(self):
                                self.custom_structures = {}
                            
                            def get_structure(self, name):
                                print(f"BasicTemplateManager: get_structure called with name={name}")
                                if not name:
                                    return []
                                
                                # Check if it's a built-in structure (case-insensitive)
                                name_lower = name.lower()
                                for key in DEFAULT_STRUCTURES:
                                    if key.lower() == name_lower:
                                        print(f"BasicTemplateManager: Found built-in structure: {key}")
                                        return DEFAULT_STRUCTURES[key]
                                
                                print(f"BasicTemplateManager: Structure not found: {name}")
                                return []
                        
                        parent.template_manager = BasicTemplateManager()
                    
                    # Call the original constructor
                    super().__init__(parent, **kwargs)
                    
                    # Ensure dropdown is populated with built-in structures
                    self.populate_structure_dropdown()
            
            # Create and show the editor
            editor = EnhancedStructureEditorWithFallback(
                parent_app,
                structure_name=None,
                is_new=True,
                project_type=None
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
        if hasattr(self, 'template_view_mode') and self.template_view_mode == "list":
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
                if hasattr(self, 'multi_selected_templates') and self.multi_selected_templates:
                    had_multi_selection = True
                    self.multi_selected_templates.clear()
                
                # Update card styling - essential to ensure visual state updates
                if had_selection or had_multi_selection:
                    self._update_template_card_selection()
                    print(f"🔍 LISTENER: Cleared all selections")
        
        # Let parent handle remaining events
        QWidget.mousePressEvent(self, event)
        
    def _update_template_card_selection(self):
        """Update all template card selection states based on current selection"""
        # Make sure we have cards
        if not hasattr(self, 'template_cards') or not self.template_cards:
            return
            
        print(f"🔍 LISTENER: Updating selection state for {len(self.template_cards)} template cards")
        
        # Check if we're in multi-selection mode
        in_multi_select = getattr(self, 'is_multi_selecting', False)
        print(f"🔍 LISTENER: In multi-selection mode: {in_multi_select}")
        
        # Track the primary selection for debugging
        primary_selection = None
        if hasattr(self, 'selected_template') and self.selected_template:
            primary_selection = self.selected_template.get('name', 'Unknown') if hasattr(self.selected_template, 'get') else str(self.selected_template)
        
        print(f"🔍 LISTENER: Primary selection: {primary_selection}")
        print(f"🔍 LISTENER: Multi-selection count: {len(self.multi_selected_templates) if hasattr(self, 'multi_selected_templates') else 0}")
            
        # Update each card's selection state
        for card in self.template_cards:
            # Must have template property and set_selected method
            if hasattr(card, 'template') and hasattr(card, 'set_selected'):
                # Get card's template name for debugging
                card_name = card.template.get('name', 'Unknown') if hasattr(card.template, 'get') else str(card.template)
                
                # Determine selection state
                is_primary_selected = False
                is_multi_selected = False
                
                # Check if this card's template is the selected one (primary selection)
                if hasattr(self, 'selected_template') and self.selected_template:
                    is_primary_selected = (card.template == self.selected_template)
                
                # Check for multi-selection
                if hasattr(self, 'multi_selected_templates') and self.multi_selected_templates:
                    is_multi_selected = (card.template in self.multi_selected_templates)
                
                # First update multi-selection state if supported
                if hasattr(card, 'set_multi_selected'):
                    card.set_multi_selected(is_multi_selected)
                    if is_multi_selected:
                        print(f"🔍 LISTENER: Setting '{card_name}' as multi-selected")
                        
                # Set the primary selection state:
                # 1. If it's the primary selected template, select it
                # 2. If it's in multi-selection list, select it 
                # 3. Otherwise deselect only if not in multi-selection mode
                should_be_selected = is_primary_selected or is_multi_selected
                current_selected = getattr(card, 'selected', False)
                
                # In multi-selection mode, we only change selection state from false→true, never true→false
                if in_multi_select:
                    if should_be_selected:
                        # Only set if it should be selected
                        card.set_selected(True)
                        print(f"🔍 LISTENER: Setting '{card_name}' as selected in multi-select mode")
                    # Skip deselection in multi-select mode
                else:
                    # Standard mode - set selection state directly
                    if should_be_selected:
                        print(f"🔍 LISTENER: Setting '{card_name}' as selected")
                        card.set_selected(True)
                    else:
                        print(f"🔍 LISTENER: Setting '{card_name}' as NOT selected")
                        card.set_selected(False)
    
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
        """Handle window resize events"""
        # Start/restart the resize timer to avoid excessive updates
        self.resize_timer.start()
        super().resizeEvent(event)
    
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