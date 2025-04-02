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
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QMimeData, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QDrag, QPixmap, QIcon

from app.ui.color_scheme_pyqt import colors  # Add missing colors import
from app.constants import get_resource_path # Added get_resource_path import

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
                delete_callback = lambda: self._delete_multi_selected(gallery)
            else:
                delete_text = "Delete"
                delete_callback = lambda: self.deleteRequested.emit(template_name)
                
            menu.addRedDeleteAction(
                parent=self,
                callback=delete_callback,
                text=delete_text
            )
            
            # Add separator
            menu.addSeparator()
            
            # Add export template option
            export_action = QAction("Export Template...", self)
            export_action.triggered.connect(lambda: self._export_template(template_name))
            menu.addAction(export_action)
            
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
                    move_to_root_action = QAction("Root (No Folder)", self)
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
            
            # Create actions
            edit_action = QAction("Edit Template", self)
            delete_action = QAction("Delete Template", self)
            duplicate_action = QAction("Duplicate Template", self)
            
            # Add actions to menu
            menu.addAction(edit_action)
            menu.addAction(delete_action)
            menu.addAction(duplicate_action)
            
            # Connect actions to slots
            edit_action.triggered.connect(lambda: self.editRequested.emit(template_name))
            delete_action.triggered.connect(lambda: self.deleteRequested.emit(template_name))
            duplicate_action.triggered.connect(lambda: self._duplicate_template())
            
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
                success_count = 0
                
                # Add the primary selection to the list if it exists
                if gallery.selected_template:
                    sel_name = gallery.selected_template.get('name', '') if isinstance(gallery.selected_template, dict) else str(gallery.selected_template)
                    print(f"🔍 LISTENER: Adding primary selection to templates to move out of folder")
                    
                # Move each template in the multi-selection
                for t in gallery.multi_selected_templates:
                    t_name = t.get('name', '') if isinstance(t, dict) else str(t)
                    print(f"🔍 LISTENER: Adding multi-selected template to templates to move out of folder")
                    self.moveToFolderRequested.emit(t_name, "")
                    success_count += 1
                    
                print(f"🔍 LISTENER: Moving {success_count} templates out of folder '{current_folder}'")
                return
        
        # Single template move
        print(f"🔍 LISTENER: Moving template '{template_name}' to root (no folder)")
        self.moveToFolderRequested.emit(template_name, "")
    
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
            return
            
        # Get the list of selected templates
        selected_templates = list(gallery.multi_selected_templates)
        
        # Don't proceed if nothing is selected
        if not selected_templates:
            return
            
        # Create confirmation dialog
        from PyQt5.QtWidgets import QMessageBox
        confirm_msg = QMessageBox()
        confirm_msg.setIcon(QMessageBox.Warning)
        
        # Customize message based on number of templates
        if len(selected_templates) == 1:
            template_name = selected_templates[0].get('name', '') if isinstance(selected_templates[0], dict) else str(selected_templates[0])
            confirm_msg.setWindowTitle("Delete Template")
            confirm_msg.setText(f"Are you sure you want to delete the template '{template_name}'?")
        else:
            confirm_msg.setWindowTitle("Delete Multiple Templates")
            confirm_msg.setText(f"Are you sure you want to delete {len(selected_templates)} templates?")
        
        confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_msg.setDefaultButton(QMessageBox.No)
        
        # If confirmed, delete all selected templates
        if confirm_msg.exec_() == QMessageBox.Yes:
            for template in selected_templates:
                template_name = template.get('name', '') if isinstance(template, dict) else str(template)
                # Emit the delete signal for each template
                self.deleteRequested.emit(template_name)
            
            # Clear the multi-selection
            gallery.multi_selected_templates.clear()

    def _duplicate_template(self):
        """Duplicate the template if gallery has the method"""
        if hasattr(self.gallery, 'duplicate_template'):
            template_name = self.template.get('name', '') if isinstance(self.template, dict) else str(self.template)
            self.gallery.duplicate_template(template_name)
        else:
            print("Template duplication not supported by gallery")

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
                # Handle multi-selection with Ctrl/Cmd or Shift
                if is_multi_select:
                    if hasattr(gallery, 'is_multi_selecting'):
                        gallery.is_multi_selecting = True
                    
                    # Emit multi-select signal
                    self.multiSelectRequested.emit(self.template)
                else:
                    # Normal click behavior
                    # Clear multi-selection if not clicking on a multi-selected item
                    if not self.was_multi_selected:
                        if hasattr(gallery, 'multi_selected_templates'):
                            gallery.multi_selected_templates.clear()
                        
                        # Turn off multi-selection mode
                        if hasattr(gallery, 'is_multi_selecting'):
                            gallery.is_multi_selecting = False
                        
                        # Use the shared event handler for template selection
                        from app.templates.gallery_events import GalleryEvents
                        GalleryEvents.on_template_select(gallery, self.template)
                    
                    # Emit clicked signal to update selection state
                    self.clicked.emit(self.template)
                
                # Update all list items in the gallery
                if hasattr(gallery, 'template_item_map'):
                    for item_name, list_item in list(gallery.template_item_map.items()):
                        try:
                            is_this_item_selected = (gallery.selected_template == list_item.template) if hasattr(gallery, 'selected_template') else False
                            is_this_item_multi_selected = (list_item.template in gallery.multi_selected_templates) if hasattr(gallery, 'multi_selected_templates') else False
                            
                            # Update item state
                            list_item.setSelected(is_this_item_selected)
                            list_item.setMultiSelected(is_this_item_multi_selected)
                            
                            # Force visual update
                            list_item._update_styling()
                        except Exception as e:
                            print(f"Error updating item {item_name}: {e}")
                
                # Also update template cards if in grid view
                if hasattr(gallery, 'template_cards'):
                    for card in gallery.template_cards:
                        if not card or not hasattr(card, 'template'):
                            continue
                            
                        is_card_selected = (gallery.selected_template == card.template) if hasattr(gallery, 'selected_template') else False
                        is_card_multi_selected = (card.template in gallery.multi_selected_templates) if hasattr(gallery, 'multi_selected_templates') else False
                        
                        # Update card state
                        if hasattr(card, 'set_selected'):
                            card.set_selected(is_card_selected)
                        elif hasattr(card, 'setSelected'):
                            card.setSelected(is_card_selected)
                            
                        # Set multi-selection
                        if hasattr(card, 'set_multi_selected'):
                            card.set_multi_selected(is_card_multi_selected)
                        elif hasattr(card, 'setMultiSelected'):
                            card.setMultiSelected(is_card_multi_selected)
                            
                        # Update card styling
                        if hasattr(card, '_update_styling'):
                            card._update_styling()
            else:
                # No gallery parent found, just use normal selection
                self.clicked.emit(self.template)
                self.setSelected(True)
                self._update_styling()
            
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
        
        # Set data for internal drag
        mime_data.setText(template_name)
        mime_data.setObjectName("template")
        
        # Find the gallery to get multi-selection info
        gallery = self.gallery
        if not gallery:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'multi_selected_templates'):
                    gallery = parent
                    break
                parent = parent.parent()
        
        # Check if this is part of a multi-selection or we're multi-selecting
        include_multi = False
        
        if gallery and hasattr(gallery, 'multi_selected_templates') and gallery.multi_selected_templates:
            # Check specifically if this template is in the multi-selection list
            for t in gallery.multi_selected_templates:
                t_name = t.get('name', '') if isinstance(t, dict) else str(t)
                if t_name == template_name:
                    include_multi = True
                    print(f"🔍 LISTENER: Multi-selection drag initiated from list item '{template_name}'")
                    break
        
        if include_multi and gallery and hasattr(gallery, 'multi_selected_templates'):
            multi_selected_names = []
            for t in gallery.multi_selected_templates:
                t_name = t.get('name', '') if isinstance(t, dict) else str(t)
                multi_selected_names.append(t_name)
            
            # Store multi-selection as JSON string
            if multi_selected_names:
                import json
                json_data = json.dumps(multi_selected_names)
                mime_data.setData("application/x-template-multi-selection", json_data.encode())
                mime_data.setText("\n".join(multi_selected_names))  # For plain text fallback
                print(f"🔍 LISTENER: Multi-selection drag with {len(multi_selected_names)} templates: {multi_selected_names}")
        else:
            # Single template drag
            print(f"🔍 LISTENER: Dragging 1 selected template")
        
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
            
        # Check for multi-selection data first
        if mime_data.hasFormat("application/x-template-multi-selection"):
            try:
                # Get JSON data with multi-selected templates
                multi_data = mime_data.data("application/x-template-multi-selection").data()
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
                
        # Fallback to single template
        if mime_data.hasText():
            template_name = mime_data.text().strip()
            # Handle multiple lines (sometimes drag text has newlines)
            if "\n" in template_name:
                template_name = template_name.split("\n")[0].strip()
                
            print(f"🔍 LISTENER: Dropped single template '{template_name}' onto folder '{folder_name}'")
            self.moveToFolderRequested.emit(template_name, folder_name)
            event.acceptProposedAction()
            
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
                
        if is_folder and (mime_data.hasText() or mime_data.hasFormat("application/x-template-multi-selection")):
            if mime_data.hasFormat("application/x-template-multi-selection"):
                print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with data: {mime_data.text()}")
            else:
                print(f"🔍 LISTENER: Drag entered folder '{folder_name}' with data: {mime_data.text()}")
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