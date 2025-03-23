#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QPixmap, QPainter

# Import QtWidgets conditionally - for compatibility with different PyQt versions
try:
    from PyQt5.QtWidgets import QLineEdit, QPushButton
except ImportError:
    # Fallback for older PyQt versions
    from PyQt5.QtGui import QLineEdit, QPushButton

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

class UIOperations:
    """
    UI-related operations for template management
    """
    
    def create_new_template(self, parent):
        """Create a new empty template via UI action"""
        try:
            # Import here to avoid circular imports
            from app.dialogs.dialog_windows_pyqt import show_edit_template
            from app.ui.structure_editor_enhanced import show_enhanced_structure_editor
            
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
            
            # Show the enhanced structure editor directly
            success, structure, structure_name = show_enhanced_structure_editor(
                parent, 
                structure_name="",  # Empty structure name initially
                structure=[],
                is_new=True
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
                from PyQt5.QtWidgets import QMessageBox
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
    
    def edit_template(self, template):
        """Show dialog to edit an existing template"""
        if not template:
            return False
            
        try:
            # Import here to avoid circular imports
            from app.ui.structure_editor_enhanced import show_enhanced_structure_editor
            
            # Show the enhanced structure editor directly
            success, structure, structure_name = show_enhanced_structure_editor(
                None, 
                structure_name=template.get('structure_name', f"Template_{template.get('name', 'Unknown')}"),
                structure=template.get('structure', []),
                is_new=False
            )
            
            if success and structure:
                # Update the template with the structure
                updated_template = template.copy()
                updated_template['structure'] = structure
                updated_template['structure_name'] = structure_name
                
                # Save the template
                self.update_template(updated_template)
                
                return True
            
            return False
        except Exception as e:
            print(f"Error editing template: {e}")
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
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               "assets", "icons", "template_structure_icon.svg")
        
        if os.path.exists(icon_path):
            try:
                from PyQt5.QtSvg import QSvgRenderer
                
                # Create a renderer for the SVG
                with open(icon_path, 'r') as f:
                    svg_content = f.read()
                
                renderer = QSvgRenderer(QByteArray(svg_content.encode()))
                if renderer.isValid():
                    # Create a pixmap to render to
                    pixmap = QPixmap(40, 40)
                    pixmap.fill(Qt.transparent)  # Make the background transparent
                    
                    # Paint the SVG on the pixmap
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    icon_label = QLabel(card)
                    icon_label.setPixmap(pixmap)
                    icon_label.setStyleSheet(f"background: {colors['card_bg']}")
                    icon_label.pack(side=Qt.LeftToRight, padx=10, pady=10)
                    
                    # Make icon clickable too
                    if select_callback:
                        icon_label.mousePressEvent = lambda e: select_callback(template)
                        icon_label.enterEvent = lambda e: self._on_card_hover_enter(card)
                        icon_label.leaveEvent = lambda e: self._on_card_hover_leave(card)
                else:
                    # Fallback to emoji if renderer is not valid
                    icon = template.get("icon", "📂")
                    icon_label = QLabel(card, text=icon, font=("Segoe UI", 24),
                                   bg=colors["card_bg"], fg=colors["text"])
                    icon_label.pack(side=Qt.LeftToRight, padx=10, pady=10)
                    
                    # Make icon clickable too
                    if select_callback:
                        icon_label.mousePressEvent = lambda e: select_callback(template)
                        icon_label.enterEvent = lambda e: self._on_card_hover_enter(card)
                        icon_label.leaveEvent = lambda e: self._on_card_hover_leave(card)
            except Exception as e:
                print(f"ERROR: Failed to load SVG icon: {e}")
                # Fallback to emoji if SVG loading fails
                icon = template.get("icon", "📂")
                icon_label = QLabel(card, text=icon, font=("Segoe UI", 24),
                               bg=colors["card_bg"], fg=colors["text"])
                icon_label.pack(side=Qt.LeftToRight, padx=10, pady=10)
                
                # Make icon clickable too
                if select_callback:
                    icon_label.mousePressEvent = lambda e: select_callback(template)
                    icon_label.enterEvent = lambda e: self._on_card_hover_enter(card)
                    icon_label.leaveEvent = lambda e: self._on_card_hover_leave(card)
        else:
            # Fallback to emoji if file doesn't exist
            icon = template.get("icon", "📂")
            icon_label = QLabel(card, text=icon, font=("Segoe UI", 24),
                               bg=colors["card_bg"], fg=colors["text"])
            icon_label.pack(side=Qt.LeftToRight, padx=10, pady=10)
            
            # Make icon clickable too
            if select_callback:
                icon_label.mousePressEvent = lambda e: select_callback(template)
                icon_label.enterEvent = lambda e: self._on_card_hover_enter(card)
                icon_label.leaveEvent = lambda e: self._on_card_hover_leave(card)
        
        # Info section
        info_frame = QFrame(card, bg=colors["card_bg"])
        info_frame.pack(side=Qt.LeftToRight, fill=Qt.Expanding, expand=True, pady=10)
        
        # Name
        name_label = QLabel(info_frame, text=template.get("name", "Unnamed Template"), 
                               font=("Segoe UI", 11, "bold"),
                               bg=colors["card_bg"], fg=colors["text"], anchor="w")
        name_label.pack(fill=Qt.Expanding)
        
        # Category
        category_label = QLabel(info_frame, text=template.get("category", "Custom"), 
                                   font=("Segoe UI", 9),
                                   bg=colors["card_bg"], fg=colors["secondary_text"], anchor="w")
        category_label.pack(fill=Qt.Expanding)
        
        # Description
        desc_label = QLabel(info_frame, text=template.get("description", ""), 
                               font=("Segoe UI", 9),
                               bg=colors["card_bg"], fg=colors["text"], 
                               anchor="w", justify=Qt.Left, wrapLength=350)
        desc_label.pack(fill=Qt.Expanding)
        
        # Make all labels clickable
        if select_callback:
            for label in [name_label, category_label, desc_label]:
                label.mousePressEvent = lambda e: select_callback(template)
                label.enterEvent = lambda e: self._on_card_hover_enter(card)
                label.leaveEvent = lambda e: self._on_card_hover_leave(card)
        
        return card
        
    def _on_card_hover_enter(self, card):
        """Handle hover enter for template card"""
        # Skip if card is already highlighted
        if hasattr(card, 'is_highlighted') and card.is_highlighted:
            return
            
        # Light grey hover effect
        hover_bg = "#303030"  # Slightly lighter than card_bg
        
        # Update the card and all its children - border should match background (no blue outline)
        card.setStyleSheet(f"background-color: {hover_bg}; border: 1px solid {hover_bg};")
        icon_label = card.findChild(QLabel, "icon_label")
        icon_label.setStyleSheet(f"background-color: {hover_bg};")
        info_frame = card.findChild(QFrame, "info_frame")
        info_frame.setStyleSheet(f"background-color: {hover_bg};")
        
        # Update all info frame widgets
        for widget in info_frame.findChildren(QLabel):
            widget.setStyleSheet(f"background-color: {hover_bg};")
        
        # Set cursor
        card.setCursor(Qt.PointingHandCursor)
    
    def _on_card_hover_leave(self, card):
        """Handle hover leave for template card"""
        # Skip if card is highlighted
        if hasattr(card, 'is_highlighted') and card.is_highlighted:
            return
            
        # Reset to card background
        card.setStyleSheet(f"background-color: {colors['card_bg']}; border: 1px solid {colors['card_bg']};")
        icon_label = card.findChild(QLabel, "icon_label")
        icon_label.setStyleSheet(f"background-color: {colors['card_bg']};")
        info_frame = card.findChild(QFrame, "info_frame")
        info_frame.setStyleSheet(f"background-color: {colors['card_bg']};")
        
        # Reset all info frame widgets with appropriate colors
        name_label = info_frame.findChild(QLabel, "name_label")
        name_label.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']};")
        category_label = info_frame.findChild(QLabel, "category_label")
        category_label.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['secondary_text']};")
        desc_label = info_frame.findChild(QLabel, "desc_label")
        desc_label.setStyleSheet(f"background-color: {colors['card_bg']}; color: {colors['text']};")
        
        # Reset cursor
        card.setCursor(Qt.ArrowCursor)
    
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
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                    QLineEdit, QPushButton, QComboBox, QMessageBox)
        from PyQt5.QtCore import Qt
        
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
                from app.templates.template_operations import TemplateOperations
                success = TemplateOperations.save_template(self, name, category, file_path, structure_type, description)
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"Failed to save template: {str(e)}")
                return
            
            if success:
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
        dialog.exec_()
    
    def import_template_ui(self, app):
        """Show UI for importing a template"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout
        
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
        if dialog.exec_() == QDialog.Accepted:
            # If dialog accepted, trigger updates
            if hasattr(app, 'template_updated') and app.template_updated is not None:
                app.template_updated.emit()
    
    def manage_templates_ui(self, app):
        """Show UI for managing templates"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QListWidget, QFrame,
                                   QSizePolicy, QMessageBox, QInputDialog)
        from PyQt5.QtCore import Qt, QSize
        from PyQt5.QtGui import QFont
        
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
        dialog.exec_()
    
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
            result = TemplateOperations.save_template(self, name, file_path, structure_type, description)
            
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
            from PyQt5.QtWidgets import QApplication
            
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