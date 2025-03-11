#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt

# Import QtWidgets conditionally - for compatibility with different PyQt versions
try:
    from PyQt5.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton
except ImportError:
    # Fallback for older PyQt versions
    from PyQt5.QtGui import QFrame, QLabel, QLineEdit, QPushButton

from app.ui.ui_components_pyqt import ScrollableFrame
from app.templates.components import TemplateCard

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
            from app.dialogs.dialog_windows_pyqt import show_edit_template
            
            # Show the edit template dialog with a callback to update the template
            show_edit_template(None, template, lambda t: self.update_template(t))
            return True
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
        
        # Icon - use emoji for simplicity
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
        from PyQt5.QtWidgets import QDialog, QFrame, QLabel, QLineEdit, QPushButton, QOptionMenu, QStringVar
        
        if not app.template_file_path:
            QMessageBox.warning(app, "Warning", "Please select a template file first")
            return
            
        if not app.project_name.text().strip():
            QMessageBox.warning(app, "Warning", "Please enter a project name to use as template name")
            return
        
        # Create dialog
        dialog = QDialog(app)
        dialog.setWindowTitle("Save as Template")
        dialog.setGeometry(400, 300, 400, 300)
        dialog.setModal(True)
        dialog.exec_()
        
        frame = QFrame(dialog, padx=20, pady=20)
        frame.pack(fill=Qt.Expanding, expand=True)
        
        # Template name
        name_label = QLabel(frame, text="Template Name:", alignment=Qt.AlignLeft)
        name_label.pack(fill=Qt.Expanding, pady=(0, 5))
        
        name_var = QStringVar(value=app.project_name.text().strip())
        name_entry = QLineEdit(frame, textvariable=name_var)
        name_entry.pack(fill=Qt.Expanding, pady=(0, 15))
        
        # Category
        category_label = QLabel(frame, text="Template Category:", alignment=Qt.AlignLeft)
        category_label.pack(fill=Qt.Expanding, pady=(0, 5))
        
        categories = self.get_categories()
        if not categories:
            categories = ["Video Editing", "Motion Graphics", "Design", "Audio", "Custom"]
            
        category_var = QStringVar(value="Standard")
        category_menu = QOptionMenu(frame, category_var, *categories)
        category_menu.pack(fill=Qt.Expanding, pady=(0, 15))
        
        # Description
        desc_label = QLabel(frame, text="Description (optional):", alignment=Qt.AlignLeft)
        desc_label.pack(fill=Qt.Expanding, pady=(0, 5))
        
        desc_var = QStringVar()
        desc_entry = QLineEdit(frame, textvariable=desc_var)
        desc_entry.pack(fill=Qt.Expanding, pady=(0, 20))
        
        # Buttons
        button_frame = QFrame(frame)
        button_frame.pack(fill=Qt.Expanding)
        
        def save_template():
            name = name_var.get().strip()
            category = category_var.get()
            description = desc_var.get().strip()
            
            if not name:
                QMessageBox.warning(app, "Warning", "Template name is required")
                return
                
            # Save template
            success = self.save_template(
                name, 
                category, 
                app.template_file_path,
                "Standard",
                description
            )
            
            if success:
                QMessageBox.information(app, "Success", f"Template '{name}' saved successfully")
                
                # Update the gallery
                if hasattr(app, 'template_gallery'):
                    app.template_gallery.populate_gallery(force_refresh=True)
            else:
                QMessageBox.warning(app, "Warning", f"Failed to save template '{name}'")
        
        cancel_button = QPushButton(button_frame, text="Cancel", clicked=dialog.reject)
        cancel_button.pack(side=Qt.Left, padx=(0, 5))
        save_button = QPushButton(button_frame, text="Save", clicked=save_template)
        save_button.pack(side=Qt.Right)
        
        # Set focus to name entry
        name_entry.setFocus()
    
    def import_template_ui(self, app):
        """Show UI for importing a template"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
        
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
        
        # Show dialog to confirm name and category
        template_name = QInputDialog.getText(app, "Import Template", "Template name:", text=name)
        
        if not template_name:
            return
            
        # Import the template
        success = self.import_template_file(file_path, template_name)
        
        if success:
            QMessageBox.information(app, "Success", f"Template '{template_name}' imported successfully")
            
            # Update the gallery
            if hasattr(app, 'template_gallery'):
                app.template_gallery.populate_gallery(force_refresh=True)
        else:
            QMessageBox.warning(app, "Warning", f"Failed to import template '{template_name}'")
    
    def manage_templates_ui(self, app):
        """Show UI for managing templates"""
        from PyQt5.QtWidgets import QDialog, QFrame, QLabel, QListWidget, QPushButton, QScrollBar, QListWidgetItem
        
        # Create dialog
        dialog = QDialog(app)
        dialog.setWindowTitle("Manage Templates")
        dialog.setGeometry(500, 400, 500, 400)
        dialog.setModal(True)
        dialog.exec_()
        
        frame = QFrame(dialog, padx=20, pady=20)
        frame.pack(fill=Qt.Expanding, expand=True)
        
        Label(frame, text="Templates", font=("Segoe UI", 14, "bold")).pack(anchor=Qt.AlignLeft, pady=(0, 15))
        
        # List with scrollbar
        list_frame = QFrame(frame)
        list_frame.pack(fill=Qt.Expanding, expand=True, pady=(0, 15))
        
        scrollbar = QScrollBar(list_frame)
        scrollbar.setOrientation(Qt.Vertical)
        scrollbar.pack(side=Qt.Right, fill=Qt.Expanding)
        
        template_listbox = QListWidget(list_frame)
        template_listbox.setViewMode(QListWidget.IconMode)
        template_listbox.setIconSize(QSize(64, 64))
        template_listbox.setResizeMode(QListWidget.Adjust)
        template_listbox.setGridSize(QSize(128, 128))
        template_listbox.itemClicked.connect(lambda: delete_template())
        template_listbox.itemDoubleClicked.connect(lambda: rename_template())
        template_listbox.addItems([f"{template['name']} ({template['category']})" for template in self.templates])
        template_listbox.addItems([f"{template['name']} ({template['category']})" for template in self.template_directories])
        
        # Button frame
        button_frame = QFrame(frame)
        button_frame.pack(fill=Qt.Expanding)
        
        def delete_template():
            selected = template_listbox.selectedIndexes()
            if not selected:
                QMessageBox.warning(app, "Warning", "Please select a template to delete")
                return
                
            index = selected[0].row()
            if index < 0 or index >= len(self.templates) + len(self.template_directories):
                return
                
            template = self.templates[index] if index < len(self.templates) else self.template_directories[index - len(self.templates)]
            template_name = template["name"]
            
            # Confirm deletion
            confirm = QMessageBox.question(app, "Confirm Deletion", 
                                        f"Are you sure you want to delete the template '{template_name}'?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.No:
                return
                
            # Delete the template
            success = self.delete_template(template_name)
            
            if success:
                QMessageBox.information(app, "Success", f"Template '{template_name}' deleted successfully")
                template_listbox.takeItem(index)
                
                # Update the gallery
                if hasattr(app, 'template_gallery'):
                    app.template_gallery.populate_gallery(force_refresh=True)
            else:
                QMessageBox.warning(app, "Warning", f"Failed to delete template '{template_name}'")
        
        def rename_template():
            selected = template_listbox.selectedIndexes()
            if not selected:
                QMessageBox.warning(app, "Warning", "Please select a template to rename")
                return
                
            index = selected[0].row()
            if index < 0 or index >= len(self.templates) + len(self.template_directories):
                return
                
            template = self.templates[index] if index < len(self.templates) else self.template_directories[index - len(self.templates)]
            old_name = template["name"]
            
            # Get new name
            new_name = QInputDialog.getText(app, "Rename Template", "Enter new name:", text=old_name)
            
            if not new_name or new_name == old_name:
                return
                
            # Rename the template
            success = self.rename_template(old_name, new_name)
            
            if success:
                QMessageBox.information(app, "Success", f"Template renamed to '{new_name}'")
                template_listbox.takeItem(index)
                template_listbox.insertItem(index, QListWidgetItem(f"{new_name} ({template['category']})"))
                
                # Update the gallery
                if hasattr(app, 'template_gallery'):
                    app.template_gallery.populate_gallery(force_refresh=True)
            else:
                QMessageBox.warning(app, "Warning", f"Failed to rename template")
        
        Button(button_frame, text="Delete", clicked=delete_template).pack(side=Qt.Left, padx=(0, 5))
        Button(button_frame, text="Rename", clicked=rename_template).pack(side=Qt.Left, padx=(0, 5))
        Button(button_frame, text="Close", clicked=dialog.accept).pack(side=Qt.Right) 