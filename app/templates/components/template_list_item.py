#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template list item component for the template gallery.
This is a simplified version that includes just the necessary methods
to avoid crashes from missing methods.
"""

import time
import datetime
import os
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QApplication, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QMimeData, QSize, QByteArray
from PyQt5.QtGui import QFont, QPalette, QColor, QDrag, QPixmap, QIcon

from app.ui.color_scheme_pyqt import colors  # Add missing colors import
from app.constants import get_resource_path # Added get_resource_path import
from app.templates.mime_types import TEMPLATE_NAMES_MIME_TYPE, TEMPLATE_MULTI_DRAG_MIME_TYPE, TEMPLATE_MULTI_SELECTION_MIME_TYPE

# Simple, stable implementation with minimal dependencies
class TemplateListItem(QFrame):
    """List item for template in list view"""
    
    # Initialize signals
    clicked = pyqtSignal(object)  # Signal for click - passes template data
    doubleClicked = pyqtSignal(object)  # Signal for double-click - passes template data
    deleteRequested = pyqtSignal(str)  # Signal for delete request - passes template name
    multiSelectRequested = pyqtSignal(object)  # New signal for multi-selection
    dragStarted = pyqtSignal(object)  # Signal for drag start - passes template data
    moveToFolderRequested = pyqtSignal(str, str)  # Signal for moving template to folder
    editRequested = pyqtSignal(str)  # Signal for edit request - passes template name
    
    def __init__(self, template, gallery=None, row_index=None):
        super().__init__()
        
        # Set object name for styling
        self.setObjectName("TemplateListItem")
        
        # Store essential parameters
        self.template = template
        self.gallery = gallery
        self.row_index = row_index  # For striped rows
        
        # Initialize state
        self.selected = False
        self.multi_selected = False
        self.hover = False  # Initialize hover state explicitly
        self.mouse_press_pos = None  # For tracking drag
        self.clicking_multi_selected = False  # For tracking multi-selection clicks
        self.dragging = False  # Track active drag state
        self.was_multi_selected = False  # Added for tracking if item was already multi-selected
        
        # Check if template has structure
        self.has_structure = False
        if isinstance(self.template, dict):
            if 'structure' in self.template:
                structure = self.template['structure']
                if isinstance(structure, dict) and 'folders' in structure and structure['folders']:
                    self.has_structure = True
                elif isinstance(structure, list) and structure:
                    self.has_structure = True
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Configure frame appearance
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        
        # Set size policy to expand horizontally
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Icon label (template icon) - Load SVG
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(30, 30) # Keep fixed size for list view consistency
        self.icon_label.setStyleSheet("background-color: transparent;") # Ensure background is transparent
        
        icon_path = get_resource_path(os.path.join(
            "ICONS", "templates", "template_structure_icon.svg"))
            
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(QSize(24, 24)) # Use QSize, slightly smaller pixmap for padding within the 30x30 label
            if not pixmap.isNull():
                self.icon_label.setPixmap(pixmap)
            else:
                print(f"Warning: Failed to load SVG icon for list item: {icon_path}")
                # Fallback to text icon if SVG loading fails
                self.icon_label.setText("📄")
                font = QFont()
                font.setPointSize(14)
                self.icon_label.setFont(font)
                self.icon_label.setStyleSheet(f"color: {colors.get('accent', '#FFFFFF')}; background-color: transparent;") # Add color fallback
        else:
            print(f"Warning: SVG icon file not found for list item: {icon_path}")
            # Fallback to text icon if file not found
            self.icon_label.setText("📄")
            font = QFont()
            font.setPointSize(14)
            self.icon_label.setFont(font)
            self.icon_label.setStyleSheet(f"color: {colors.get('accent', '#FFFFFF')}; background-color: transparent;") # Add color fallback

        layout.addWidget(self.icon_label)
        
        # Add warning indicator for templates without structure
        if not self.has_structure:
            self.warning_label = QLabel("⚠")
            self.warning_label.setFixedSize(16, 16)
            self.warning_label.setAlignment(Qt.AlignCenter)
            self.warning_label.setStyleSheet(f"""
                color: {colors.get('error', '#FF5252')};
                background-color: transparent;
                font-weight: bold;
                font-size: 12px;
            """)
            layout.addWidget(self.warning_label)
            
            # Add tooltip to explain the warning
            self.setToolTip("This template has no folder structure defined")
        else:
            # Add a spacer to keep alignment consistent
            self.spacer_label = QLabel()
            self.spacer_label.setFixedSize(16, 16)
            layout.addWidget(self.spacer_label)
        
        # Name label
        template_name = template.get('name', 'Untitled Template') if isinstance(template, dict) else str(template)
        self.name_label = QLabel(template_name)
        self.name_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.name_label.setFixedWidth(300)  # Set initial width
        layout.addWidget(self.name_label)
        
        # Category label - new field
        category_text = template.get('category', '') if isinstance(template, dict) else ''
        self.category_label = QLabel(category_text)
        self.category_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.category_label.setFixedWidth(150)  # Set initial width to match header
        layout.addWidget(self.category_label)
        
        # Format timestamps safely
        created_timestamp = template.get('created', time.time()) if isinstance(template, dict) else time.time()
        modified_timestamp = template.get('modified', created_timestamp) if isinstance(template, dict) else time.time()
        
        created_date_str = self._format_date(created_timestamp)
        modified_date_str = self._format_date(modified_timestamp)
        
        # Created date
        self.created_date_label = QLabel(created_date_str)
        self.created_date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.created_date_label.setFixedWidth(150)  # Set initial width to match header
        layout.addWidget(self.created_date_label)
        
        # Modified date
        self.modified_date_label = QLabel(modified_date_str)
        self.modified_date_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.modified_date_label.setFixedWidth(150)  # Set initial width to match header
        layout.addWidget(self.modified_date_label)
        
        # Apply initial styling
        self._update_styling()
        
        # Install event filter for hover effects
        self.installEventFilter(self)

    def _format_date(self, timestamp):
        """Format a timestamp into a readable date string"""
        try:
            if isinstance(timestamp, (int, float)):
                dt = datetime.datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M")
            return "Unknown"
        except Exception as e:
            print(f"Error formatting date: {e}")
            return "Unknown"
            
    def _show_context_menu(self, position):
        """Display the context menu for this template"""
        template_name = self.template.get('name', '') if isinstance(self.template, dict) else str(self.template)
        
        # Look for the menu_actions module for consistent context menu styling
        try:
            from app.templates.components.menu_actions import ContextMenu
            
            # Create menu using the shared ContextMenu class
            menu = ContextMenu(self)
            
            # Add Edit action
            edit_action = QAction("Edit", self)
            edit_action.triggered.connect(lambda: self.editRequested.emit(template_name))
            menu.addAction(edit_action)
            
            # Find the parent gallery for multi-selection handling
            gallery = self.gallery
            if not gallery:
                # Try to find gallery by traversing parent hierarchy
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'multi_selected_templates'):
                        gallery = parent
                        break
                    parent = parent.parent()
            
            # Check if we're in a multi-selection state
            has_multi = (gallery and hasattr(gallery, 'multi_selected_templates') and 
                        gallery.multi_selected_templates and 
                        len(gallery.multi_selected_templates) > 0)
                        
            # Add Delete action with appropriate callback based on selection state
            if has_multi:
                delete_text = "Delete Selected Templates"
                delete_callback = lambda: self._safe_delete(gallery, template_name)
            else:
                delete_text = "Delete"
                # Call our safer method instead of _delete_multi_selected directly
                delete_callback = lambda: self._safe_delete(gallery, template_name)
                
            menu.addRedDeleteAction(
                parent=self,
                callback=delete_callback,
                text=delete_text
            )
            
            # Add separator
            menu.addSeparator()
            
            # Add duplicate template option
            duplicate_action = QAction("Duplicate", self)
            duplicate_action.triggered.connect(lambda: self._duplicate_template(template_name))
            menu.addAction(duplicate_action)
            
            # Add export template option
            export_action = QAction("Export Template...", self)
            export_action.triggered.connect(lambda: self._export_template(template_name))
            menu.addAction(export_action)
            
            # Add separator
            menu.addSeparator()
            
            # Add cache management options (consistent with other views)
            cache_menu = menu.addMenu("Cache Management")
            
            # Add recache option
            recache_action = QAction("Recache Template", self)
            recache_action.triggered.connect(lambda: self._recache_template(template_name))
            cache_menu.addAction(recache_action)
            
            # Add clear cache option
            clear_cache_action = QAction("Clear Template Cache", self)
            clear_cache_action.triggered.connect(lambda: self._clear_template_cache(template_name))
            cache_menu.addAction(clear_cache_action)
            
            # Add separator
            menu.addSeparator()
            
            # Add move actions if gallery has template_manager 
            if gallery and hasattr(gallery, 'app') and hasattr(gallery.app, 'template_manager'):
                template_manager = gallery.app.template_manager
                
                move_to_menu = ContextMenu(menu)
                move_to_menu.setTitle("Move to...")
                
                # Find current folder of this template
                current_folder = None
                if hasattr(template_manager, 'folders'):
                    for folder_name, templates in template_manager.folders.items():
                        if template_name in templates:
                            current_folder = folder_name
                            break
                
                # Add "Move to Root" option if template is in a folder
                if current_folder:
                    move_to_root_action = QAction("No Folder", self)
                    move_to_root_action.triggered.connect(lambda: self._move_template_out_of_folder(current_folder))
                    move_to_menu.addAction(move_to_root_action)
                    
                    move_to_menu.addSeparator()
                
                # Add all folders except current one
                if hasattr(template_manager, 'folders'):
                    folders = sorted(list(template_manager.folders.keys()))
                    for folder_name in folders:
                        # Skip the current folder
                        if folder_name == current_folder:
                            continue
                            
                        folder_action = QAction(folder_name, self)
                        folder_action.triggered.connect(lambda checked=False, f=folder_name: 
                                                      self.moveToFolderRequested.emit(template_name, f))
                        move_to_menu.addAction(folder_action)
                
                # Only add the Move To menu if it has items
                if not move_to_menu.isEmpty():
                    menu.addMenu(move_to_menu)
        
        except ImportError:
            # Fallback to basic menu if ContextMenu isn't available
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2A2A2A;
                    color: #FFFFFF;
                    border: 1px solid #3C3C3C;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 5px 30px 5px 20px;
                    border: 1px solid transparent;
                }
                QMenu::item:selected { 
                    background-color: #3E3E3E;
                    color: #FFFFFF;
                }
            """)
            
            # Make sure gallery is defined
            if not gallery:
                print("[ERROR] No gallery reference found for fallback menu")
                # Try to find gallery one more time
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'multi_selected_templates'):
                        gallery = parent
                        print("[INFO] Found gallery reference through parent hierarchy")
                        break
                    parent = parent.parent()
            
            print(f"[DEBUG] Fallback menu gallery reference exists: {gallery is not None}")
            
            # Create actions
            edit_action = QAction("Edit Template", self)
            delete_action = QAction("Delete Template", self)
            duplicate_action = QAction("Duplicate Template", self)
            
            # Add actions to menu
            menu.addAction(edit_action)
            menu.addAction(delete_action)
            menu.addAction(duplicate_action)
            
            # Connect actions to slots - with error handling
            edit_action.triggered.connect(lambda: self.editRequested.emit(template_name))
            
            # Use try/except for delete to prevent crashes
            delete_action.triggered.connect(lambda: self._safe_delete(gallery, template_name))
            
            # Use safer duplicate implementation
            duplicate_action.triggered.connect(lambda: self._duplicate_template(template_name))
            
        # Show the menu at the requested position
        menu.exec_(self.mapToGlobal(position))
    
    def _move_template_out_of_folder(self, current_folder):
        """Move the template out of its current folder to root"""
        template_name = self.template.get('name', '') if isinstance(self.template, dict) else str(self.template)
          
        # Find the gallery to get multi-selection info
        gallery = self.gallery
        if not gallery:
            # Try to find gallery by traversing parent hierarchy
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
        
        if not gallery:
            print(f"[ERROR] Cannot move template: invalid gallery reference")
            return
        
        # Check if we need to move multiple templates
        if gallery and hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
            # Check if this template is part of the multi-selection or if we're in multi-select mode
            is_multi_selected = False
            for t in gallery.multi_selected_templates:
                t_name = t.get('name', '') if isinstance(t, dict) else str(t)
                if t_name == template_name:
                    is_multi_selected = True
                    break
                    
            if is_multi_selected or getattr(gallery, 'is_multi_selecting', False):
                # This is a multi-selection operation
                print("🔍 LISTENER: Moving multiple templates out of folder")
                
                # Use a set to collect unique template names
                templates_to_move = set()
                
                # Add the primary selection if it exists
                if hasattr(gallery, 'selected_template') and gallery.selected_template:
                    primary_template = gallery.selected_template
                    primary_name = primary_template.get('name', '') if isinstance(primary_template, dict) else str(primary_template)
                    if primary_name:
                        templates_to_move.add(primary_name)
                        print(f"🔍 LISTENER: Adding primary selection '{primary_name}' to move list")
                    
                # Add all multi-selected templates
                if hasattr(gallery, 'multi_selected_templates'):
                    for t in gallery.multi_selected_templates:
                        t_name = t.get('name', '') if isinstance(t, dict) else str(t)
                        if t_name:
                            templates_to_move.add(t_name)
                            print(f"🔍 LISTENER: Adding multi-selected '{t_name}' to move list")

                # Use the GalleryEvents class to handle the move operation
                from app.templates.gallery_events import GalleryEvents
                GalleryEvents.on_move_template_to_folder(gallery, list(templates_to_move), None)
                print(f"🔍 LISTENER: Requested move for {len(templates_to_move)} unique templates out of folder '{current_folder}'")
                return
        
        # Single template move (fallback if not multi-selection)
        print(f"🔍 LISTENER: Moving template '{template_name}' to root (no folder)")
        
        # Use the GalleryEvents class to handle the move operation
        from app.templates.gallery_events import GalleryEvents
        GalleryEvents.on_move_template_to_folder(gallery, template_name, None)
    
    def _export_template(self, template_name):
        """Export the template to a package file"""
        if not template_name:
            return
            
        # Find gallery to get app reference
        gallery = self.gallery
        if not gallery:
            # Try to find gallery by traversing parent hierarchy
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
        
        if not gallery or not hasattr(gallery, 'app'):
            return
            
        # Use the export_template function from import_export_manager
        from app.core.import_export_manager import export_template
        
        # Show dialog to ask if files should be included
        from PyQt5.QtWidgets import QMessageBox
        
        include_files = QMessageBox.question(
            self,
            "Export Template",
            f"Would you like to include files with this template?\n\n"
            f"Including files will allow others to import the template with all its attached assets.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) == QMessageBox.Yes
        
        # Export the template
        export_template(gallery.app, template_name, include_files)
    
    def _delete_multi_selected(self, gallery):
        """Handle deletion of multiple selected templates"""
        # Make sure we're working with a valid gallery
        if not gallery or not hasattr(gallery, 'multi_selected_templates'):
            print("[ERROR] Cannot delete: invalid gallery reference or multi_selected_templates missing")
            return
            
        try:
            # Print current selection states for debugging
            if hasattr(gallery, 'selected_template') and gallery.selected_template:
                if isinstance(gallery.selected_template, dict):
                    print(f"🔍 LISTENER: Current primary selection: {gallery.selected_template.get('name', 'Unknown')}")
                else:
                    print(f"🔍 LISTENER: Current primary selection: {str(gallery.selected_template)}")
            else:
                print(f"🔍 LISTENER: No primary selection")
                
            if hasattr(gallery, 'multi_selected_templates'):
                template_names = []
                for t in gallery.multi_selected_templates:
                    if isinstance(t, dict):
                        template_names.append(t.get('name', 'Unknown'))
                    else:
                        template_names.append(str(t))
                print(f"🔍 LISTENER: Current multi-selection: {template_names}")
            
            # First, detect what we're deleting
            has_primary = hasattr(gallery, 'selected_template') and gallery.selected_template is not None
            has_multi = (hasattr(gallery, 'multi_selected_templates') and 
                       gallery.multi_selected_templates and 
                       len(gallery.multi_selected_templates) > 0)
            
            # If nothing to delete, exit
            if not has_primary and not has_multi:
                print(f"🔍 LISTENER: No templates selected for deletion")
                return
            
            # Create a fresh set of templates to delete (using set for deduplication)
            templates_to_delete_set = set()
            templates_to_delete = []
            
            # ALWAYS include the primary selected template FIRST if it exists
            if has_primary:
                if isinstance(gallery.selected_template, dict):
                    primary_name = gallery.selected_template.get('name', 'Unknown')
                else:
                    primary_name = str(gallery.selected_template)
                templates_to_delete.append(gallery.selected_template)
                templates_to_delete_set.add(id(gallery.selected_template))  # Add object id to set for tracking
                print(f"🔍 LISTENER: Including primary selected template in delete operation: {primary_name}")
            
            # Then add the multi-selected templates
            if has_multi:
                for template in gallery.multi_selected_templates:
                    template_id = id(template)
                    if template_id not in templates_to_delete_set:
                        templates_to_delete.append(template)
                        templates_to_delete_set.add(template_id)
                        if isinstance(template, dict):
                            print(f"🔍 LISTENER: Adding multi-selected template to delete operation: {template.get('name', 'Unknown')}")
                        else:
                            print(f"🔍 LISTENER: Adding multi-selected template to delete operation: {str(template)}")
            
            # Verify total count matches expectations
            expected_count = (1 if has_primary else 0) + (len(gallery.multi_selected_templates) if has_multi else 0)
            actual_count = len(templates_to_delete)
            print(f"🔍 LISTENER: Expected {expected_count} templates, found {actual_count} templates after deduplication")
            
            # If no templates to delete, exit
            if not templates_to_delete:
                print(f"🔍 LISTENER: No templates to delete after processing")
                return
            
            # Get template names for display and deletion
            template_names = []
            for template in templates_to_delete:
                if isinstance(template, dict) and 'name' in template:
                    name = template['name']
                elif isinstance(template, dict) and hasattr(template, 'get'):
                    name = template.get('name', 'Unknown')
                elif isinstance(template, str):
                    name = template
                else:
                    name = str(template)
                    
                if name and name not in template_names:
                    template_names.append(name)
                    print(f"🔍 LISTENER: Template to delete: '{name}'")
            
            # If no valid template names, exit
            if not template_names:
                print(f"🔍 LISTENER: No valid template names found for deletion")
                return
                
            print(f"🔍 LISTENER: Final delete list ({len(template_names)} templates): {template_names}")
            
            # Create confirmation message
            if len(template_names) == 1:
                message = f"Are you sure you want to delete template '{template_names[0]}'?"
            else:
                message = f"Are you sure you want to delete these {len(template_names)} templates?"
            
            # Create confirmation dialog
            from PyQt5.QtWidgets import QMessageBox
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                message,
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Find the app and template_manager
                app = None
                if hasattr(gallery, 'app'):
                    app = gallery.app
                elif hasattr(self, 'gallery') and hasattr(self.gallery, 'app'):
                    app = self.gallery.app
                
                # Check if we have a valid app and template_manager
                if app and hasattr(app, 'template_manager'):
                    success_count = 0
                    error_count = 0
                    for name in template_names:
                        try:
                            print(f"🔍 LISTENER: Deleting template '{name}'")
                            if app.template_manager.delete_template(name):
                                success_count += 1
                            else:
                                error_count += 1
                                print(f"[ERROR] Template manager failed to delete template '{name}'")
                        except Exception as e:
                            error_count += 1
                            print(f"[ERROR] Exception when deleting template '{name}': {e}")
                            import traceback
                            traceback.print_exc()
                    
                    print(f"🔍 LISTENER: Delete operation completed - Success: {success_count}, Errors: {error_count}")
                    
                    # Show success message
                    if hasattr(app, 'show_status_message'):
                        if len(template_names) == 1:
                            app.show_status_message(f"Deleted template '{template_names[0]}'", "success")
                        else:
                            app.show_status_message(f"Deleted {len(template_names)} templates", "success")
                else:
                    print("[ERROR] Cannot delete templates: app or template_manager not available")
                    
                # Clear the multi-selection
                if gallery and hasattr(gallery, 'multi_selected_templates'):
                    gallery.multi_selected_templates.clear()
                
                # Refresh the gallery if possible
                try:
                    if gallery and hasattr(gallery, 'populate_gallery'):
                        gallery.populate_gallery(force_refresh=True)
                except Exception as e:
                    print(f"[ERROR] Failed to refresh gallery after delete: {e}")
        except Exception as e:
            print(f"[ERROR] Exception in _delete_multi_selected: {e}")
            import traceback
            traceback.print_exc()

    def _duplicate_template(self, template_name):
        """Duplicate the template if gallery has the method"""
        gallery = self.gallery
        if not gallery:
            # Try to find gallery by traversing parent hierarchy
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
        
        if gallery and hasattr(gallery, 'app'):
            from app.templates.gallery_events import GalleryEvents
            GalleryEvents.on_duplicate_template(gallery, template_name)
        else:
            print(f"[ERROR] Could not duplicate template '{template_name}': Gallery not found or missing app reference")

    def _update_styling(self):
        """Update the styling of the list item based on its state"""
        try:
            # Get style sheets based on state
            # Import system-wide colors
            from app.templates.components.common_styles import CARD_NORMAL, CARD_HOVER, CARD_SELECTED
            
            # Base styling classes
            background = colors.get('card_bg', '#2A2A2A')
            text_color = colors.get('text', '#CCCCCC')
            border_style = ""
            
            # Prevent recursive repaints
            old_style = self.styleSheet()
            
            # Determine background based on row for striping
            if self.row_index is not None:
                # Alternate background colors for odd/even rows
                if self.row_index % 2 == 0:
                    background = colors.get('card_bg', '#2A2A2A')
                else:
                    background = colors.get('card_bg', '#2A2A2A')
                    # Add a slight tint for alternating
                    if background.startswith('#'):
                        # Make slightly darker
                        background = "#" + "".join([hex(max(0, int(c, 16) - 5))[2:].zfill(2) for c in [background[1:3], background[3:5], background[5:7]]])
                    
            # Handle selection states
            if self.selected or self.multi_selected:
                # Selected styling (takes precedence over hover)
                background = CARD_SELECTED  # Use the system-wide selection color
                text_color = colors.get('highlight_text', '#FFFFFF')
                # No border for selected items to match folder view
                border_style = "border: none;"
            elif self.hover:
                # Hover styling
                background = CARD_HOVER  # Use the system-wide hover color
                text_color = colors.get('text', '#FFFFFF')
                # Very subtle border on hover only
                border_style = "border: none;"
            else:
                # No border in normal state either
                border_style = "border: none;"
            
            # Set the styling directly with specificity to force override
            style_sheet = f"""
                #TemplateListItem {{
                    background-color: {background} !important;
                    color: {text_color} !important;
                    {border_style}
                    border-radius: 3px;
                    margin: 2px;
                    padding: 4px;
                }}
            """
            
            # If styling hasn't changed, don't reapply
            if style_sheet.strip() == old_style.strip():
                return
            
            # Apply the style sheet
            self.setStyleSheet(style_sheet)
            
            # Update label colors directly for immediate feedback
            for child in self.findChildren(QLabel):
                if hasattr(child, 'objectName'):
                    obj_name = child.objectName()
                    if obj_name in ['name_label', 'created_date_label', 'modified_date_label', 'icon_label']:
                        palette = child.palette()
                        palette.setColor(QPalette.WindowText, QColor(text_color))
                        palette.setColor(QPalette.Text, QColor(text_color))
                        child.setPalette(palette)
            
            # Force application but avoid recursion
            self.setAutoFillBackground(True)
            
        except Exception as e:
            print(f"Error updating list item styling: {e}")

    def setNameWidth(self, width):
        """Set the width of the name column"""
        if hasattr(self, 'name_label'):
            self.name_label.setFixedWidth(width)
            self.update()
            
    def setCategoryWidth(self, width):
        """Set the width of the category column"""
        if hasattr(self, 'category_label'):
            self.category_label.setFixedWidth(width)
            self.update()
            
    def setCreatedDateWidth(self, width):
        """Set the width of the created date column"""
        if hasattr(self, 'created_date_label'):
            self.created_date_label.setFixedWidth(width)
            self.update()
            
    def setModifiedDateWidth(self, width):
        """Set the width of the modified date column"""
        if hasattr(self, 'modified_date_label'):
            self.modified_date_label.setFixedWidth(width)
            self.update()

    def setSelected(self, selected):
        """Set the selected state of this list item"""
        if self.selected != selected:
            self.selected = selected
            self._update_styling()  # Update visual state immediately
    
    def setMultiSelected(self, multi_selected):
        """Set the multi-selected state of this list item"""
        if self.multi_selected != multi_selected:
            self.multi_selected = multi_selected
            self._update_styling()  # Update visual state immediately
    
    def setRowIndex(self, index):
        """Set the row index for striped rows"""
        self.row_index = index
        self._update_styling()
    
    def mousePressEvent(self, event):
        """Handle mouse press events to initiate selection, dragging, or context menu"""
        if event.button() == Qt.LeftButton:
            # Store press position for potential drag
            self.mouse_press_pos = event.pos()
            
            # Get modifiers for multi-select
            modifiers = event.modifiers()
            is_multi_select = bool(modifiers & (Qt.ControlModifier | Qt.ShiftModifier))
            
            # Find gallery parent
            gallery = self.gallery
            if not gallery:
                # Try to find gallery by traversing parent hierarchy
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'multi_selected_templates'):
                        gallery = parent
                        break
                    parent = parent.parent()
            
            # Check if clicking on an already multi-selected item
            self.was_multi_selected = False
            if gallery and hasattr(gallery, 'multi_selected_templates'):
                if self.template in gallery.multi_selected_templates:
                    self.was_multi_selected = True
                    self.clicking_multi_selected = True
            
            if gallery:
                # Determine modifier state for the unified handler
                is_ctrl_or_cmd = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
                is_shift = bool(modifiers & Qt.ShiftModifier)
                is_modifier_click = is_ctrl_or_cmd or is_shift
                
                # Track if we used the unified handler
                handled_by_unified_handler = False
                
                # Directly call a unified handler in the gallery
                if hasattr(gallery, 'handle_template_item_press'):
                    gallery.handle_template_item_press(self.template, is_modifier_click)
                    handled_by_unified_handler = True
                else:
                    # Fallback if the handler doesn't exist (should not happen)
                    print("ERROR: Gallery does not have handle_template_item_press method!")
                    # Basic fallback selection
                    self.setSelected(True)
                    self._update_styling()
                    
                # Only emit clicked signal if we didn't use the unified handler
                # This prevents duplicate selection processing
                if not handled_by_unified_handler:
                    self.clicked.emit(self.template)
            else:
                # No gallery parent found, just select locally (no multi-select possible)
                self.setSelected(True)
                self.clicked.emit(self.template)
            
            # Accept the event to prevent propagation
            event.accept()
            
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.pos())
            event.accept()
            
        super().mousePressEvent(event)

    def _force_ui_refresh(self):
        """Force an immediate visual update of the widget"""
        try:
            # Update style using the documented method
            self._update_styling()
            
            # Apply styling changes immediately
            self.style().unpolish(self)
            self.style().polish(self)
            
            # Set repaint flag and process immediate updates
            self.setAutoFillBackground(True)
            self.update()
            
            # Process events immediately to see the changes
            QApplication.processEvents()
        except Exception as e:
            print(f"Error forcing UI refresh: {e}")

    def mouseMoveEvent(self, event):
        """Handle mouse movement for drag operations"""
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not self.mouse_press_pos:
            return
            
        # Check drag distance
        drag_distance = (event.pos() - self.mouse_press_pos).manhattanLength()
        if drag_distance < QApplication.startDragDistance():
            return
            
        # Start drag operation
        self.dragging = True
        
        # Create mime data
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Get template data
        template_name = self.template.get('name', '') if isinstance(self.template, dict) else str(self.template)
        
        # Find the gallery to get multi-selection info
        gallery = self.gallery
        if not gallery:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
        
        # Determine if this is a multi-item drag
        is_multi_drag = False
        templates_to_drag = []
        
        if gallery:
            # Check if multi-selection list is populated OR if we clicked on primary while multi-selecting
            primary_selected = getattr(gallery, 'selected_template', None)
            multi_selected = getattr(gallery, 'multi_selected_templates', [])
            
            # A multi-drag occurs if there are items in multi_selected OR if the primary item is the one being clicked/dragged
            # AND it was part of an existing multi-selection state
            initiating_item_is_primary = (primary_selected == self.template)
            
            if multi_selected or (initiating_item_is_primary and self.was_multi_selected):
                is_multi_drag = True
                
                # Use a set to gather unique template names
                names_set = set()
                
                # Add primary selection
                if primary_selected:
                    primary_name = primary_selected.get('name', '') if isinstance(primary_selected, dict) else str(primary_selected)
                    if primary_name:
                        names_set.add(primary_name)
                        
                # Add multi-selected items
                for t in multi_selected:
                    t_name = t.get('name', '') if isinstance(t, dict) else str(t)
                    if t_name:
                        names_set.add(t_name)
                        
                templates_to_drag = list(names_set)
                print(f"🔍 LISTENER: Multi-selection drag initiated with {len(templates_to_drag)} items: {templates_to_drag}")

        # Prepare mime data
        if is_multi_drag:
            # Set special mime type for multi-drag
            mime_data.setData(TEMPLATE_MULTI_DRAG_MIME_TYPE, QByteArray(b'1'))
            
            # Store multi-selection as JSON string
            if templates_to_drag:
                import json
                json_data = json.dumps(templates_to_drag)
                mime_data.setData(TEMPLATE_MULTI_SELECTION_MIME_TYPE, json_data.encode())
                
                # Set newline-separated text format
                template_names_text = "\n".join(templates_to_drag)
                mime_data.setText(template_names_text)  # For plain text fallback
                
                # Set standardized MIME type for template names
                mime_data.setData(TEMPLATE_NAMES_MIME_TYPE, QByteArray(template_names_text.encode('utf-8')))
                
                print(f"🔍 LISTENER: Multi-selection drag mime data set for {len(templates_to_drag)} templates")
            else:
                # Should not happen, but fallback to single
                mime_data.setText(template_name)
                mime_data.setData(TEMPLATE_NAMES_MIME_TYPE, QByteArray(template_name.encode('utf-8')))
                print(f"🔍 LISTENER: Multi-drag identified but no names collected - fallback to single: {template_name}")
        else:
            # Single template drag
            mime_data.setText(template_name)
            mime_data.setData(TEMPLATE_NAMES_MIME_TYPE, QByteArray(template_name.encode('utf-8')))
            print(f"🔍 LISTENER: Single template drag: {template_name}")
        
        drag.setMimeData(mime_data)
        
        # Create pixmap for drag visualization
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        
        # Signal drag started
        self.dragStarted.emit(self.template)
        
        # Execute drag
        result = drag.exec_(Qt.MoveAction)
        
        # Reset drag state
        self.dragging = False
        
    def dropEvent(self, event):
        """Handle drop events"""
        mime_data = event.mimeData()
        
        # Check for folder drop target
        is_folder = False
        folder_name = ""
        if hasattr(self.template, 'get'):
            is_folder = self.template.get('type') == 'folder'
            if is_folder:
                folder_name = self.template.get('name', '')
                
        if not is_folder:
            # Not a folder, can't handle the drop
            event.ignore()
            return
            
        # First check for our standardized MIME type
        if mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE):
            try:
                # Get template names from MIME data
                template_names_data = mime_data.data(TEMPLATE_NAMES_MIME_TYPE).data().decode('utf-8')
                template_names = template_names_data.strip().split('\n')
                
                print(f"🔍 LISTENER: Drop detected with {len(template_names)} templates using {TEMPLATE_NAMES_MIME_TYPE}")
                
                # Move all templates to the folder
                success_count = 0
                for template_name in template_names:
                    if template_name.strip():
                        self.moveToFolderRequested.emit(template_name, folder_name)
                        success_count += 1
                        
                if success_count > 0:
                    print(f"🔍 LISTENER: Moved {success_count} templates to folder '{folder_name}'")
                    event.acceptProposedAction()
                    return
            except Exception as e:
                print(f"Error processing {TEMPLATE_NAMES_MIME_TYPE} drop: {e}")
                
        # Check for multi-selection data format (fallback)
        elif mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE):
            try:
                # Get JSON data with multi-selected templates
                multi_data = mime_data.data(TEMPLATE_MULTI_SELECTION_MIME_TYPE).data()
                import json
                template_names = json.loads(multi_data.decode())
                
                print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with data: {mime_data.text()}")
                
                # Move all templates in the multi-selection
                success_count = 0
                for template_name in template_names:
                    self.moveToFolderRequested.emit(template_name, folder_name)
                    success_count += 1
                    
                if success_count > 0:
                    print(f"🔍 LISTENER: Moved {success_count} templates to folder '{folder_name}'")
                    event.acceptProposedAction()
                    return
            except Exception as e:
                print(f"Error processing multi-selection drop: {e}")
                
        # Fallback to plain text (for backward compatibility)
        elif mime_data.hasText():
            template_name = mime_data.text().strip()
            # Handle multiple lines (sometimes drag text has newlines)
            if "\n" in template_name:
                template_names = template_name.split("\n")
                success_count = 0
                for name in template_names:
                    if name.strip():
                        self.moveToFolderRequested.emit(name.strip(), folder_name)
                        success_count += 1
                
                if success_count > 0:
                    print(f"🔍 LISTENER: Moved {success_count} templates to folder '{folder_name}' (from text data)")
                    event.acceptProposedAction()
                    return
            else:
                # Handle single template name
                print(f"🔍 LISTENER: Dropped single template '{template_name}' onto folder '{folder_name}'")
                self.moveToFolderRequested.emit(template_name, folder_name)
                event.acceptProposedAction()
                return
            
        # If we got here, we couldn't handle the drop
        event.ignore()
            
    def dragEnterEvent(self, event):
        """Handle incoming drags"""
        mime_data = event.mimeData()
        
        # Only accept drags if this item is a folder
        is_folder = False
        folder_name = ""
        if hasattr(self.template, 'get'):
            is_folder = self.template.get('type') == 'folder'
            if is_folder:
                folder_name = self.template.get('name', '')
                
        # Accept drags with any of our supported MIME types
        if is_folder and (mime_data.hasText() or 
                         mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE) or 
                         mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE) or
                         mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE)):
            # Provide visual feedback
            self.hover = True
            self._update_styling()
            
            # Log the drag event
            if mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE):
                try:
                    data = mime_data.data(TEMPLATE_NAMES_MIME_TYPE).data().decode('utf-8')
                    print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with data: {data}")
                except:
                    print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with TEMPLATE_NAMES_MIME_TYPE (data error)")
            elif mime_data.hasFormat(TEMPLATE_MULTI_SELECTION_MIME_TYPE):
                print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with TEMPLATE_MULTI_SELECTION_MIME_TYPE")
            elif mime_data.hasText():
                print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with text data: {mime_data.text()}")
                
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """Handle drag leaving this item"""
        is_folder = False
        folder_name = ""
        if hasattr(self.template, 'get'):
            is_folder = self.template.get('type') == 'folder'
            if is_folder:
                folder_name = self.template.get('name', '')
                
        if is_folder:
            print(f"🔍 LISTENER: Drag left folder '{folder_name}'")
            self.hover = False
            self._update_styling()
            
        super().dragLeaveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after click or drag"""
        if event.button() == Qt.LeftButton:
            # Skip if we were dragging
            if self.dragging:
                self.dragging = False
                self.mouse_press_pos = None
                self.was_multi_selected = False
                return
                
            # Calculate the drag distance
            drag_occurred = False
            if hasattr(self, 'mouse_press_pos') and self.mouse_press_pos:
                drag_distance = (event.pos() - self.mouse_press_pos).manhattanLength()
                drag_occurred = drag_distance >= 5  # Common threshold for drag detection
            
            # Only process clicks (not drags) and not when clicking on multi-selected items
            if not drag_occurred and not self.was_multi_selected:
                # Get gallery reference
                gallery = None
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'multi_selected_templates'):
                        gallery = parent
                        break
                    parent = parent.parent()
                
                # Get keyboard modifiers - maintain multi-selection if modifier is still pressed
                modifiers = QApplication.keyboardModifiers()
                is_modifier_pressed = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier | Qt.ShiftModifier))
                
                # Only clear multi-selection on release if no modifiers are pressed
                if not is_modifier_pressed and gallery:
                    if hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
                        # Don't clear if this was a multi-selected item (preserves ability to drag)
                        if not self.was_multi_selected:
                            gallery.multi_selected_templates.clear()
                            print(f"🔍 LISTENER: Cleared multi-selection on mouse release - no modifiers")
                    
                    # Update template selection state if method exists
                    if hasattr(gallery, '_update_template_card_selection'):
                        gallery._update_template_card_selection()
            
            # Reset state variables
            self.mouse_press_pos = None
            self.was_multi_selected = False
            self.clicking_multi_selected = False
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double click event"""
        if event.button() == Qt.LeftButton:
            template_name = self.template.get('name', '') if isinstance(self.template, dict) else str(self.template)
            print(f"🔍 LISTENER: Double-click on template: {template_name}")
            self.doubleClicked.emit(self.template)
        
        super().mouseDoubleClickEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.hover = True
        self._update_styling()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.hover = False
        self._update_styling()
        super().leaveEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events for template operations"""
        # Handle both Delete and Backspace (for Mac) for template deletion when selected
        if (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace) and self.selected:
            # If we have a gallery reference and it has multi-selection, handle accordingly
            has_multi = (self.gallery and hasattr(self.gallery, 'multi_selected_templates') and 
                        self.gallery.multi_selected_templates and 
                        len(self.gallery.multi_selected_templates) > 0)
                        
            if has_multi:
                # Use the TemplateCard's multi-selection delete logic to ensure consistent handling
                from app.templates.components.template_card import TemplateCard
                dummy_card = TemplateCard(parent=self.parent(), template=self.template, app=self.gallery.app)
                dummy_card._delete_multi_selected(self.gallery)
                # Prevent further processing of the event
                event.accept()
                return
            else:
                # Just delete this template
                if isinstance(self.template, dict) and 'name' in self.template:
                    template_name = self.template['name']
                    self.deleteRequested.emit(template_name)
                    # Prevent further processing of the event
                    event.accept()
                    return
        
        super().keyPressEvent(event)
        
    def eventFilter(self, obj, event):
        """Filter events for hover state"""
        if obj == self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self._update_styling()
            elif event.type() == QEvent.Leave:
                self.hover = False
                self._update_styling()
        return super().eventFilter(obj, event)

    def _safe_delete(self, gallery, template_name):
        """Safe wrapper for delete operation to prevent crashes"""
        try:
            print(f"[DEBUG] Safe delete called for template: {template_name}")
            
            # Check if we have a gallery
            if not gallery:
                print("[ERROR] No gallery reference for safe delete, trying to find it")
                # Try to find gallery through parent hierarchy
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'multi_selected_templates'):
                        gallery = parent
                        print("[INFO] Found gallery in safe_delete through parent hierarchy")
                        break
                    parent = parent.parent()
            
            if gallery:
                print(f"[DEBUG] Using _delete_multi_selected with gallery reference")
                self._delete_multi_selected(gallery)
            else:
                print(f"[ERROR] No gallery reference found for delete operation")
                # Last resort, try direct signal
                print(f"[WARNING] Falling back to direct deleteRequested signal")
                self.deleteRequested.emit(template_name)
        except Exception as e:
            print(f"[ERROR] Exception in _safe_delete: {e}")
            import traceback
            traceback.print_exc()
            # Last attempt - try direct signal
            try:
                print(f"[WARNING] Attempting direct deleteRequested signal after exception")
                self.deleteRequested.emit(template_name)
            except Exception as e2:
                print(f"[ERROR] Even direct deleteRequested signal failed: {e2}")
                traceback.print_exc() 

    def _recache_template(self, template_name):
        """Recache a template to update from original sources"""
        print(f"[ACTION] Recaching template: {template_name}")
        
        # Find the gallery for app reference
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'app'):
                gallery = parent
                break
            parent = parent.parent()
            
        if not gallery or not hasattr(gallery, 'app'):
            print(f"[ERROR] Cannot find app reference for recaching")
            return
            
        app = gallery.app
        
        # Check if template manager is available
        if not hasattr(app, 'template_manager'):
            print(f"[ERROR] No template manager available for recaching")
            return
            
        # Use the template manager to recache the template
        if hasattr(app.template_manager, 'recache_template'):
            success = app.template_manager.recache_template(template_name)
            
            # Show feedback to user
            from PyQt5.QtWidgets import QMessageBox
            if success:
                QMessageBox.information(None, "Recache Complete", 
                    f"Template '{template_name}' has been recached successfully.")
            else:
                QMessageBox.warning(None, "Recache Failed", 
                    f"Failed to recache template '{template_name}'.")
        else:
            print(f"[ERROR] Template manager does not support recaching")
    
    def _clear_template_cache(self, template_name):
        """Clear the cache for a template"""
        print(f"[ACTION] Clearing cache for template: {template_name}")
        
        # Find the gallery for app reference
        gallery = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'app'):
                gallery = parent
                break
            parent = parent.parent()
            
        if not gallery or not hasattr(gallery, 'app'):
            print(f"[ERROR] Cannot find app reference for clearing cache")
            return
            
        app = gallery.app
        
        # Check if template manager is available
        if not hasattr(app, 'template_manager'):
            print(f"[ERROR] No template manager available for clearing cache")
            return
            
        # Use the template manager to safely clear the cache
        if hasattr(app.template_manager, 'safe_clear_template_cache'):
            success = app.template_manager.safe_clear_template_cache(template_name)
            
            # Show feedback to user
            from PyQt5.QtWidgets import QMessageBox
            if success:
                QMessageBox.information(None, "Cache Cleared", 
                    f"Cache for template '{template_name}' has been cleared successfully.")
        else:
            print(f"[ERROR] Template manager does not support safe cache clearing") 