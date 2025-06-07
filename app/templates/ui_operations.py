#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import time
import shutil
import json
import inspect
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
    QLabel, QFileDialog, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QFont

# Import QtWidgets conditionally - for compatibility with different PyQt versions
try:
    from PyQt6.QtWidgets import QLineEdit, QComboBox
except ImportError:
    # Fallback for older PyQt versions
    from PyQt6.QtGui import QLineEdit, QComboBox

from app.ui.ui_components_pyqt import ScrollableFrame
from app.templates.components import TemplateCard
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, COMBOBOX_STYLE

# Import colors from appropriate module
try:
    from app.ui.theme import colors
except ImportError:
    # Default colors if theme not available
    colors = {
        "card_bg": "#252525",
        "text": "#FFFFFF",
        "secondary_text": "#AAAAAA"
    }

# Import from constants instead
from app.constants import get_resource_path

class UIOperations:
    """
    UI-related operations for template management
    """
    
    def create_new_template(self, parent):
        """Create a new empty template via UI action"""
        try:
            # Import here to avoid circular imports
            from app.dialogs.dialog_windows_pyqt import show_edit_template
            from app.ui.structure_editor_functions import show_enhanced_structure_editor
            
            # Create a new template with default values but no name yet
            new_template = {
                "name": "",  # Empty name initially
                "category": "Custom",
                "description": "A new custom template",
                "type": "Standard",
                "structure_type": "Standard",
                "icon": "📂",
                "created": "",
                "is_new_template": True  # Flag to indicate this is a new template being created
            }
            
            # Get the template manager - either use this instance or get from parent
            template_manager = self
            if parent and hasattr(parent, 'template_manager'):
                template_manager = parent.template_manager
            elif hasattr(self, 'template_manager'):
                template_manager = self.template_manager
                
            print(f"Creating template with template_manager: {template_manager}")
            
            # Show the enhanced structure editor directly - ENSURE WE PASS THE TEMPLATE MANAGER
            success, structure, structure_name, _, _, _, _ = show_enhanced_structure_editor(
                parent=parent, 
                structure_name="",  # Empty structure name initially
                structure=[],
                is_new=True,
                template_manager=template_manager  # Explicitly pass template_manager just like gallery does
            )
            
            if success and structure:
                # Update the template with the structure
                new_template['structure'] = structure
                new_template['structure_name'] = structure_name
                
                # Get the template name from the structure name
                # The structure name should now have a valid name since we validated in the editor
                template_name = structure_name
                if structure_name.startswith("Template_"):
                    template_name = structure_name[len("Template_"):]
                
                # Only save if a name was provided 
                if template_name:
                    new_template['name'] = template_name
                    
                    # Save the template
                    self.update_template(new_template)
                    
                    # Trigger template update to refresh UI
                    if hasattr(parent, 'template_updated') and parent.template_updated is not None:
                        parent.template_updated.emit()
                        
                    return True
                
            return False
        except Exception as e:
            print(f"Error creating new template: {e}")
            if parent:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(parent, "Error", f"Failed to create template: {str(e)}")
            return False
    
    def add_template(self):
        """Show dialog to add a new template"""
        try:
            # Import here to avoid circular imports
            from app.dialogs.dialog_windows_pyqt import show_edit_template
            
            # Create a new template with default values
            new_template = {
                "name": "New Template",
                "category": "Custom",
                "description": "",
                "type": "Standard",
                "structure_type": "Standard",
                "icon": "📂",
                "created": ""
            }
            
            # Show the edit template dialog with a callback to update the template
            show_edit_template(None, new_template, lambda t: self.update_template(t))
            return True
        except Exception as e:
            print(f"Error adding template: {e}")
            return False
    
    def update_template(self, template):
        """
        Update or save an existing template
        
        Args:
            template (dict): Template data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate template has required fields
            if not isinstance(template, dict) or 'name' not in template or 'structure' not in template:
                print(f"Error: Invalid template data for update")
                return False
                
            # Log the save action
            print(f"UIOperations.update_template: Saving template '{template.get('name')}'")
            
            # Call save_template to persist the template
            return self.save_template(template)
            
        except Exception as e:
            print(f"Error updating template: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def import_template(self, template_data):
        """
        Import a template and save it to disk, handling UI updates
        
        Args:
            template_data (dict): Template data to import
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not isinstance(template_data, dict):
                print("ERROR: UIOperations: Template data must be a dictionary")
                return False
                
            template_name = template_data.get('name')
            if not template_name:
                print("ERROR: UIOperations: Template name is required")
                return False
                
            print(f"DEBUG: UIOperations: Importing template '{template_name}'")
            
            # Save the template using template_io.save_template
            if hasattr(self.template_manager, 'template_io') and hasattr(self.template_manager.template_io, 'save_template'):
                success = self.template_manager.template_io.save_template(template_data)
                
                if success:
                    print(f"✅ UIOperations: Successfully imported template '{template_name}'")
                    
                    # Update UI
                    if self.gallery_manager:
                        print(f"DEBUG: UIOperations: Refreshing gallery after template import")
                        self.gallery_manager.refresh_gallery()
                        
                        # Emit template updated signal if available
                        if hasattr(self.app, 'template_updated') and self.app.template_updated is not None:
                            self.app.template_updated.emit()
                    
                    return True
                else:
                    print(f"ERROR: UIOperations: Failed to import template '{template_name}'")
                    return False
            else:
                print("ERROR: UIOperations: template_io.save_template not available")
                return False
        except Exception as e:
            print(f"ERROR: UIOperations: Error importing template: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def edit_template(self, template_data):
        """
        Edit an existing template. This opens the Structure Editor by default,
        unless called from import_template (then it skips that step).
        
        Args:
            template_data: The template data to edit
            
        Returns:
            bool: True if the edit was successful, False otherwise
        """
        caller = inspect.currentframe().f_back.f_code.co_name
        print(f"🔍 EDIT_TEMPLATE: Called from {caller}")
        
        # Skip showing structure editor if called from import_template
        if caller == "import_template":
            print(f"🔍 EDIT_TEMPLATE: Detected call from import_template, skipping structure editor")
            return self.update_template(template_data)
            
        # Continue with normal structure editor flow
        try:
            # Get or create structure name
            template_name = template_data.get("name", "")
            structure_name = template_data.get("structure_name", "")
            
            if not structure_name:
                structure_name = template_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                
            # Configure the structure editor
            show_editor = True
            structure_editor_result = False
            
            # Show the structure editor
            if show_editor:
                structure = template_data.get("structure", [])
                
                editor = EnhancedStructureEditor(
                    parent=self.app,
                    structure_name=structure_name,
                    template_name=template_name,
                    is_new=False
                )
                
                editor.set_template_data(template_data)
                
                if structure:
                    editor.set_initial_structure(structure)
                    
                # Show the editor dialog
                if editor.exec() == QDialog.Accepted:
                    # Get updated data
                    updated_structure = editor.get_structure()
                    updated_name = editor.get_template_name()
                    updated_category = editor.get_category()
                    updated_description = editor.get_description()
                    
                    # Update the template data
                    updated_template = template_data.copy()
                    updated_template["name"] = updated_name
                    updated_template["structure"] = updated_structure
                    updated_template["category"] = updated_category
                    updated_template["description"] = updated_description
                    updated_template["modified"] = time.time()
                    
                    # Handle rename if needed
                    if template_name != updated_name:
                        # TBD: Handle rename logic
                        pass
                        
                    # Save the updated template
                    structure_editor_result = self.update_template(updated_template)
                    
                    if not structure_editor_result:
                        # Show error
                        QMessageBox.warning(
                            self.app,
                            "Template Update Failed",
                            f"Failed to update template '{template_name}'."
                        )
                
                return structure_editor_result
            else:
                # Skip editor, just update 
                return self.update_template(template_data)
                
        except Exception as e:
            print(f"Error editing template: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_template_list_frame(self, parent):
        """Create a scrollable frame for template list"""
        template_list_frame = ScrollableFrame(parent, bg=parent["bg"])
        template_list_frame.pack(fill="both", expand=True)
        return template_list_frame
    
    def create_template_card(self, parent, template, select_callback=None, **kwargs):
        """Create a card for a template"""
        # Create frame with rounded corners
        card = QFrame(parent, bg=colors["card_bg"], bd=0, **kwargs)
        card.template = template
        
        # Configure rounded corners using border styling
        card.setStyleSheet(f"background-color: {colors['card_bg']}; border: 1px solid {colors['card_bg']};")
        
        # Make entire card clickable
        if select_callback:
            card.mousePressEvent = lambda e: select_callback(template)
            
            # Add hover effects
            card.enterEvent = lambda e: self._on_card_hover_enter(card)
            card.leaveEvent = lambda e: self._on_card_hover_leave(card)
        
        # Icon - use SVG icon if available, fallback to emoji
        if item_type == "folder":
            icon_path = get_resource_path(os.path.join(
                "app", "assets", "icons", "folder_icon.svg"))
        elif item_type == "file":
            icon_path = get_resource_path(os.path.join(
                "app", "assets", "icons", "file_icon.svg"))
        else:  # Default or unknown
            icon_path = get_resource_path(os.path.join(
                "app", "assets", "icons", "templates", "template_structure_icon.svg"))

        icon_widget = None # Placeholder for the icon widget (QLabel or QSvgWidget)

        if icon_path and os.path.exists(icon_path):
            try:
                from PyQt6.QtSvg import QSvgWidget
                icon_widget = QSvgWidget(icon_path)
                icon_widget.setFixedSize(24, 24) # Or desired size
            except ImportError:
                print("WARN: Could not import QSvgWidget. SVG icons may not display.")
                # Fallback if QSvgWidget is not available or fails
                icon = template.get("icon", "📂") # Fallback emoji
                icon_widget = QLabel(icon)
                # Set appropriate styling for QLabel fallback

        else:
            print(f"WARN: Tree icon not found at {icon_path}")
            # Fallback to emoji if icon file doesn't exist
            icon = template.get("icon", "📂") # Fallback emoji
            icon_widget = QLabel(icon)
            # Set appropriate styling for QLabel fallback

        # Add the created icon_widget to the layout or use it as needed
        # Example: item.setIcon(0, QIcon(icon_path)) if using QTreeWidget item icons
        # Or add icon_widget to a layout in your custom widget

        # Info section (will be added next)
        info_frame = QFrame(card)
        info_frame.setObjectName("info_frame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # Name
        name_label = QLabel(template.get("name", "Unnamed Template"))
        name_label.setObjectName("name_label")
        name_font = QFont(SYSTEM_FONT, 11)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignLeft | Qt.AlignmentFlagFlagFlagFlagFlag.AlignTop)
        info_layout.addWidget(name_label)
        
        # Category
        category_label = QLabel(template.get("category", "Custom"))
        category_label.setObjectName("category_label")
        category_font = QFont(SYSTEM_FONT, 9)
        category_label.setFont(category_font)
        category_label.setStyleSheet(f"color: {colors['secondary_text']}; background: transparent;")
        category_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignLeft | Qt.AlignmentFlagFlagFlagFlagFlag.AlignTop)
        info_layout.addWidget(category_label)
        
        # Description
        desc_label = QLabel(template.get("description", ""))
        desc_label.setObjectName("desc_label")
        desc_font = QFont(SYSTEM_FONT, 9)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet(f"color: {colors['text']}; background: transparent;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlagFlagFlagFlagFlag.AlignLeft | Qt.AlignmentFlagFlagFlagFlagFlag.AlignTop)
        info_layout.addWidget(desc_label, 1)

        # Add info frame to hbox layout
        hbox = QHBoxLayout(card)
        hbox.setContentsMargins(10, 5, 10, 5)
        hbox.setSpacing(10)

        hbox.addWidget(icon_widget)
        
        hbox.addWidget(info_frame, 1)
        
        # Make card and all labels clickable
        if select_callback:
            # Connect press event for the card itself
            card.mousePressEvent = lambda e, tmpl=template: self._handle_card_click(e, tmpl, card, select_callback)
            
            # Use event filter for children to handle hover and clicks robustly
            for widget in [icon_widget, name_label, category_label, desc_label, info_frame]:
                widget.installEventFilter(card)

        # Install event filter on the card itself for hover effects
        card.installEventFilter(card)
        card.setAttribute(Qt.WA_Hover)

        return card
        
    def eventFilter(self, watched, event):
        """Event filter to handle hover and clicks for card and children."""
        if watched.parent() == self and event.type() == QEvent.MouseButtonPress:
             # Propagate click from child to parent card's handler
             self.mousePressEvent(event)
             return True # Event handled

        if watched == self: # Check if the event is for the card itself
            if event.type() == QEvent.HoverEnter:
                self._on_card_hover_enter(self)
                return True
            elif event.type() == QEvent.HoverLeave:
                 self._on_card_hover_leave(self)
                 return True

        return super(UIOperations, self).eventFilter(watched, event) # Call base class filter

    def _handle_card_click(self, event, template, card, select_callback):
         """Centralized handler for card clicks."""
         if event.button() == Qt.MouseButton.LeftButton:
             select_callback(template)
             # We don't need to explicitly call hover enter/leave here usually
             # Selection change should trigger style updates

    def _on_card_hover_enter(self, card):
        """Handle hover enter for template card"""
        # Skip if card is already highlighted (selected)
        if hasattr(card, 'is_highlighted') and card.is_highlighted:
            return
        
        # Apply hover style using the style sheet for consistency
        card.setProperty("hovering", True)
        self._refresh_style(card)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_card_hover_leave(self, card):
        """Handle hover leave for template card"""
        # Skip if card is highlighted (selected)
        if hasattr(card, 'is_highlighted') and card.is_highlighted:
            # If leaving while selected, ensure selected style remains
            card.setProperty("hovering", False)
            self._refresh_style(card) # Refresh to apply selected style if needed
            return # Keep pointing hand if selected? Or reset? Let's reset for now.

        # Apply normal style
        card.setProperty("hovering", False)
        self._refresh_style(card)
        card.setCursor(Qt.CursorShape.ArrowCursor)

    def _refresh_style(self, card):
         """Refreshes the stylesheet of the card based on its state."""
         card.style().unpolish(card)
         card.style().polish(card)
         card.update()

    def update_ui_folder_dropdown(self, app):
        """Update the folder dropdown in the UI"""
        # Skip if app doesn't have the dropdown
        if not hasattr(app, 'folder_dropdown'):
            return
            
        folders = self.get_folders()
        if not folders:
            return
            
        # Clear existing menu
        menu = app.folder_dropdown.getMenu()
        menu.clear()
            
        # Add all folders to dropdown
        for folder_name in folders:
            def create_command(folder_name):
                # Return a function that sets the current folder
                def command():
                    # Set the current folder
                    self.current_folder = folder_name
                    # Update the dropdown text
                    app.folder_var.set(folder_name)
                    # Refresh the template gallery with templates from the selected folder
                    if hasattr(app, 'template_gallery'):
                        app.template_gallery.populate_gallery(
                            templates=self.get_folder_templates(folder_name),
                            force_refresh=True
                        )
                return command
                
            # Add command to menu
            menu.add_command(label=folder_name, command=create_command(folder_name))
    
    def save_template_ui(self, app):
        """Show UI for saving a template"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QLineEdit, QPushButton, QComboBox, QMessageBox)
        from PyQt6.QtCore import Qt
        
        # Check if we should prompt for a template file
        template_file_path = getattr(app, 'template_file_path', None)
        if not template_file_path:
            # Allow creating a blank template without a template file
            if not hasattr(app, 'project_name') or not app.project_name.text().strip():
                # We need a project name at minimum
                QMessageBox.information(app, "Template Information", 
                                    "You are creating a blank template. You can add content to it later.")
        
        # Create dialog
        dialog = QDialog(app)
        dialog.setWindowTitle("Save Template")
        dialog.resize(400, 300)
        
        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Template name
        name_label = QLabel("Template Name:")
        main_layout.addWidget(name_label)
        
        name_field = QLineEdit()
        if hasattr(app, 'project_name'):
            name_field.setText(app.project_name.text().strip())
        main_layout.addWidget(name_field)
        
        # Add some spacing
        spacer = QLabel("")
        spacer.setFixedHeight(10)
        main_layout.addWidget(spacer)
        
        # Category
        category_label = QLabel("Category:")
        main_layout.addWidget(category_label)
        
        # Get available categories or use defaults
        categories = self.get_categories() if hasattr(self, 'get_categories') else ["Video Editing", "Motion Graphics", "Design", "Audio", "Custom"]
        
        category_combo = QComboBox()
        category_combo.addItems(categories)
        category_combo.setCurrentText("Custom")  # Default to Custom
        category_combo.setStyleSheet(COMBOBOX_STYLE)
        main_layout.addWidget(category_combo)
        
        # Add some spacing
        spacer2 = QLabel("")
        spacer2.setFixedHeight(10)
        main_layout.addWidget(spacer2)
        
        # Description
        desc_label = QLabel("Description (optional):")
        main_layout.addWidget(desc_label)
        
        desc_field = QLineEdit()
        desc_field.setText("")
        main_layout.addWidget(desc_field)
        
        # Add some spacing
        spacer3 = QLabel("")
        spacer3.setFixedHeight(20)
        main_layout.addWidget(spacer3)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        
        save_button = QPushButton("Save")
        save_button.setDefault(True)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
        
        def save_template():
            name = name_field.text().strip()
            category = category_combo.currentText()
            description = desc_field.text().strip()
            
            if not name:
                QMessageBox.warning(dialog, "Error", "Please enter a template name")
                return
            
            # Get the structure type from the app
            structure_type = app.structure_combo.currentText() if hasattr(app, 'structure_combo') else "Standard"
            
            # Get template file path if available
            file_path = getattr(app, 'template_file_path', "")
            
            # Save to the template manager
            success = False
            try:
                # Call the base class save_template method from TemplateOperations
                print(f"UIOperations.save_template: Calling save_template with name='{name}', path='{file_path}', type='{structure_type}'")
                # result = TemplateOperations.save_template(self, name, file_path, structure_type, description) # OLD Incorrect call
                
                # Delegate saving to TemplateIO instance
                if hasattr(self, 'template_io') and self.template_io:
                    # TemplateIO.save_template might return a tuple (bool, message) or just bool
                    save_result = self.template_io.save_template(template)
                    if isinstance(save_result, tuple):
                        result = save_result[0] # Get the boolean success status
                    else:
                        result = save_result # Assume boolean return
                else:
                    print("ERROR: UIOperations.save_template - TemplateIO not found on self.")
                    result = False
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"Failed to save template: {str(e)}")
                return
            
            if result:
                # Add to recent templates
                try:
                    from app.core.project_operations import add_to_recent_templates
                    add_to_recent_templates(app, name)
                except Exception as e:
                    print(f"Warning: Could not add to recent templates: {e}")
                
                # Show success message
                QMessageBox.information(dialog, "Success", f"Template '{name}' saved successfully")
                
                # Close the dialog
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Failed to save template")
        
        save_button.clicked.connect(save_template)
        
        # Set focus to name field
        name_field.setFocus()
        
        # Execute the dialog
        dialog.exec()
    
    def import_template_ui(self, app):
        """Show UI for importing a template"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            app,
            "Select Template File",
            "",
            "Project Files (*.prproj;*.aep;*.aepx;*.psd;*.ai);;Adobe Premiere (*.prproj);;After Effects (*.aep;*.aepx);;Photoshop (*.psd);;Illustrator (*.ai);;All Files (*.*)"
        )
        
        if not file_path:
            return
            
        # Get filename as default template name
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        
        # Create dialog for template details
        dialog = QDialog(app)
        dialog.setWindowTitle("Import Template")
        dialog.resize(400, 300)
        
        # Main layout
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Template name
        layout.addWidget(QLabel("Template Name:"))
        name_field = QLineEdit(name)
        layout.addWidget(name_field)
        
        # Template category
        layout.addWidget(QLabel("Category:"))
        categories = self.get_categories() if hasattr(self, 'get_categories') else ["Video Editing", "Motion Graphics", "Design", "Audio", "Custom"]
        category_combo = QComboBox()
        category_combo.addItems(categories)
        category_combo.setCurrentText("Custom")  # Default to Custom
        category_combo.setStyleSheet(COMBOBOX_STYLE)
        layout.addWidget(category_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        import_btn = QPushButton("Import")
        import_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(import_btn)
        layout.addLayout(button_layout)
        
        def on_import():
            template_name = name_field.text().strip()
            category = category_combo.currentText()
            
            if not template_name:
                QMessageBox.warning(dialog, "Error", "Please enter a template name")
                return
            
            # Import the template
            success = self.import_template_file(file_path, template_name, category)
            
            if success:
                QMessageBox.information(dialog, "Success", f"Template '{template_name}' imported successfully")
                dialog.accept()
                
                # Update the gallery if it exists
                if hasattr(app, 'template_gallery') and app.template_gallery:
                    try:
                        app.template_gallery.populate_gallery(force_refresh=True)
                    except Exception as e:
                        print(f"Error updating gallery: {e}")
            else:
                QMessageBox.warning(dialog, "Error", f"Failed to import template '{template_name}'")
        
        import_btn.clicked.connect(on_import)
        
        # Focus the name field
        name_field.setFocus()
        
        # Execute the dialog
        if dialog.exec() == QDialog.Accepted:
            # If dialog accepted, trigger updates
            if hasattr(app, 'template_updated') and app.template_updated is not None:
                app.template_updated.emit()
    
    def manage_templates_ui(self, app):
        """Show UI for managing templates"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QListWidget, QFrame,
                                   QSizePolicy, QMessageBox, QInputDialog)
        from PyQt6.QtCore import Qt, QSize
        from PyQt6.QtGui import QFont
        
        # Create dialog
        dialog = QDialog(app)
        dialog.setWindowTitle("Manage Templates")
        dialog.resize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # Create header
        header_label = QLabel("Templates")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)
        
        # Create template list
        template_list = QListWidget()
        template_list.setViewMode(QListWidget.IconMode)
        template_list.setIconSize(QSize(64, 64))
        template_list.setResizeMode(QListWidget.Adjust)
        template_list.setGridSize(QSize(128, 128))
        template_list.setMinimumHeight(300)
        main_layout.addWidget(template_list)
        
        # Populate list - use the templates and template_directories attributes
        all_templates = []
        if hasattr(self, 'templates'):
            all_templates.extend(self.templates)
        if hasattr(self, 'template_directories'):
            all_templates.extend(self.template_directories)
        
        for template in all_templates:
            name = template.get('name', 'Unknown')
            category = template.get('category', 'Custom')
            template_list.addItem(f"{name} ({category})")
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Delete button
        delete_btn = QPushButton("Delete")
        
        def delete_template():
            selected_items = template_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(dialog, "Warning", "Please select a template to delete")
                return
                
            selected_item = selected_items[0]
            template_name = selected_item.text().split(" (")[0]
            
            confirm = QMessageBox.question(
                dialog,
                "Confirm Delete",
                f"Are you sure you want to delete template '{template_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                success = self.delete_template(template_name)
                if success:
                    # Remove from list
                    row = template_list.row(selected_item)
                    template_list.takeItem(row)
                    QMessageBox.information(dialog, "Success", f"Template '{template_name}' deleted")
                else:
                    QMessageBox.warning(dialog, "Error", f"Failed to delete template '{template_name}'")
        
        delete_btn.clicked.connect(delete_template)
        button_layout.addWidget(delete_btn)
        
        # Rename button
        rename_btn = QPushButton("Rename")
        
        def rename_template():
            selected_items = template_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(dialog, "Warning", "Please select a template to rename")
                return
                
            selected_item = selected_items[0]
            template_name = selected_item.text().split(" (")[0]
            
            new_name, ok = QInputDialog.getText(
                dialog,
                "Rename Template",
                "New name:",
                text=template_name
            )
            
            if ok and new_name:
                success = self.rename_template(template_name, new_name)
                if success:
                    # Update list
                    category = selected_item.text().split(" (")[1].rstrip(")")
                    selected_item.setText(f"{new_name} ({category})")
                    QMessageBox.information(dialog, "Success", f"Template renamed to '{new_name}'")
                else:
                    QMessageBox.warning(dialog, "Error", f"Failed to rename template")
        
        rename_btn.clicked.connect(rename_template)
        button_layout.addWidget(rename_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Execute dialog
        dialog.exec()
    
    def save_template(self, template):
        """Save a template object from the UI"""
        if not template or not isinstance(template, dict):
            print("Invalid template object")
            return False
            
        try:
            name = template.get("name", "")
            file_path = template.get("path", "") or template.get("file", "")
            structure_type = template.get("type", "") or template.get("structure_type", "Standard")
            description = template.get("description", "")
            
            # Validate required fields
            if not name:
                print("Error: Cannot save template with empty name")
                return False
            
            # Call the base class save_template method from TemplateOperations
            print(f"UIOperations.save_template: Calling save_template with name='{name}', path='{file_path}', type='{structure_type}'")
            # result = TemplateOperations.save_template(self, name, file_path, structure_type, description) # OLD Incorrect call
            
            # Delegate saving to TemplateIO instance
            if hasattr(self, 'template_io') and self.template_io:
                # TemplateIO.save_template might return a tuple (bool, message) or just bool
                save_result = self.template_io.save_template(template)
                if isinstance(save_result, tuple):
                    result = save_result[0] # Get the boolean success status
                else:
                    result = save_result # Assume boolean return
            else:
                print("ERROR: UIOperations.save_template - TemplateIO not found on self.")
                result = False
            
            # Add to recent templates if successful
            if result and hasattr(self, 'add_to_recent_templates'):
                self.add_to_recent_templates(name)
                
            return result
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def manage_templates(self, parent=None):
        """Show dialog to manage all templates, folders, and structures
        
        Note: The "Manage All" button has been removed from the UI as its functionality
        is redundant with other UI elements, but this method is kept for programmatic use
        or in case it's called from elsewhere in the codebase.
        """
        try:
            # Import here to avoid circular imports
            from app.dialogs.dialog_windows_pyqt import show_manage_templates
            from PyQt6.QtWidgets import QApplication
            
            # Parent must be a QWidget, not TemplateManager
            # If no proper parent provided, use the active window or None
            if parent is None or not hasattr(parent, 'isWidgetType') or not parent.isWidgetType():
                parent = QApplication.activeWindow()
                
            # Show the manage templates dialog - pass template manager as second parameter
            show_manage_templates(parent, self, None)
            return True
        except Exception as e:
            print(f"Error showing manage templates dialog: {e}")
            import traceback
            traceback.print_exc()
            return False 

def get_template_icon(template_type=None):
    """Get the QIcon for a given template type (placeholder)."""
    # Placeholder: Correct the path for the default icon
    icon_path = get_resource_path(os.path.join(
        "app", "assets", "icons", "templates", "template_structure_icon.svg")) # Corrected path
    
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    else:
        print(f"Warning: Default template icon not found at {icon_path}")
        # Return an empty QIcon or a placeholder if needed
        return QIcon() # Return empty icon 