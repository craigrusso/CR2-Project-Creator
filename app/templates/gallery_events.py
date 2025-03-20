#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QInputDialog, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QApplication
from PyQt5.QtCore import Qt
import os
from PyQt5.QtGui import QIcon, QFont, QPixmap

# Import styling
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, COMBOBOX_STYLE

# Create a custom dialog class that ensures dropdowns are styled correctly
class StyledItemDialog(QDialog):
    """A custom dialog that ensures all dropdowns have the correct styling"""
    
    def __init__(self, parent, title, label, items):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 300)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add label
        layout.addWidget(QLabel(label))
        
        # Create and style the dropdown
        self.combo = QComboBox()
        self.combo.setMinimumWidth(250)
        self.combo.setStyleSheet(COMBOBOX_STYLE)  # Apply the standard style
        
        # Add items
        for item in items:
            self.combo.addItem(str(item))
            
        layout.addWidget(self.combo)
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(BUTTON_STYLE)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        self.ok_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def selectedItem(self):
        """Get the selected item"""
        return self.combo.currentText()

class GalleryEvents:
    """Event handlers for the Template Gallery"""
    
    @staticmethod
    def on_category_select(gallery, category):
        """Handle category selection"""
        gallery.current_category = category
        gallery.populate_gallery()
    
    @staticmethod
    def on_search(gallery, search_text):
        """Handle search text changes"""
        gallery.current_search = search_text
        gallery.populate_gallery()
    
    @staticmethod
    def on_template_select(gallery, template):
        """Handle template selection"""
        # Debug output
        template_name = template.get('name', 'Unknown')
        print(f"🔍 LISTENER: Template selection event for '{template_name}'")
        
        # Check if this is the same template as already selected
        if hasattr(gallery, 'selected_template') and gallery.selected_template == template:
            # If clicking the same template again, make sure its highlighted state is correct
            print(f"🔍 LISTENER: Same template already selected, ensuring highlight is correct")
            
            # Update card styling for this template to ensure it's highlighted
            if hasattr(gallery, 'template_cards') and gallery.template_cards:
                for card in gallery.template_cards:
                    if hasattr(card, 'template') and hasattr(card, 'set_selected'):
                        if card.template == template:
                            card.set_selected(True)
                            print(f"🔍 LISTENER: Re-applied highlight to selected template '{template_name}'")
                        else:
                            # Ensure other items are not selected
                            # Only if they're not in multi_selected_templates
                            if not hasattr(gallery, 'multi_selected_templates') or card.template not in gallery.multi_selected_templates:
                                card.set_selected(False)
            return
            
        # Set the selected template in gallery state
        gallery.selected_template = template
        
        # Also ensure it's set in the app object if available
        if hasattr(gallery, 'app'):
            gallery.app.selected_template = template
            print(f"🔍 LISTENER: Updated app-level selected template to '{template_name}'")
            
            # Ensure the template is set in template_gallery attribute of app too
            if hasattr(gallery.app, 'template_gallery') and gallery.app.template_gallery != gallery:
                try:
                    gallery.app.template_gallery.selected_template = template
                    print(f"🔍 LISTENER: Also updated template_gallery.selected_template to ensure consistency")
                except Exception as e:
                    print(f"Error syncing template selection to app.template_gallery: {e}")
        
        gallery.selected_folder = None  # Reset folder selection
        print(f"🔍 LISTENER: Template selection set to '{template_name}'")
        
        # Handle multi-selection differently - DON'T clear multi-selection automatically
        # Check if we're in multi-select mode
        modifiers = QApplication.keyboardModifiers()
        is_multi_select = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier | Qt.ShiftModifier))
        
        if not is_multi_select and hasattr(gallery, 'multi_selected_templates'):
            # Only clear multi-selection if we're not in multi-select mode
            if not hasattr(gallery, 'is_multi_selecting') or not gallery.is_multi_selecting:
                # Don't affect multi_selected_templates here - let the card handle it
                pass
        
        # Update card styling for all cards - proper highlighting - preserve multi-selection
        if hasattr(gallery, 'template_cards') and gallery.template_cards:
            card_count = len(gallery.template_cards)
            print(f"🔍 LISTENER: Updating styling for {card_count} template cards")
            
            for card in gallery.template_cards:
                if hasattr(card, 'template') and hasattr(card, 'set_selected'):
                    # Check if this card is in multi-selection
                    is_multi_selected = (hasattr(gallery, 'multi_selected_templates') and 
                                        card.template in gallery.multi_selected_templates)
                    
                    # Highlight the currently selected template AND any multi-selected templates
                    is_selected = (card.template == template) or is_multi_selected
                    card.set_selected(is_selected)
                    
                    if is_selected:
                        print(f"🔍 LISTENER: Setting {card.template_name()} selection state to TRUE")
                    else:
                        print(f"🔍 LISTENER: Setting {card.template_name()} selection state to FALSE")
        
        # Emit template selected event if using PyQt
        if hasattr(gallery, 'template_selected'):
            gallery.template_selected.emit(template)
    
    @staticmethod
    def on_folder_select(gallery, folder_name):
        """Handle folder selection"""
        print(f"🔍 LISTENER: Folder selection event for '{folder_name}'")
        
        # Update gallery state
        gallery.selected_folder = folder_name
        gallery.selected_template = None  # Reset template selection
        
        # Update folder card styling
        for card in gallery.folder_cards:
            if hasattr(card, 'folder_name') and hasattr(card, 'set_selected'):
                card.set_selected(card.folder_name == folder_name)
                
        print(f"🔍 LISTENER: Folder selection set to '{folder_name}'")
        
        # Update card styling for templates - none selected
        for card in gallery.template_cards:
            card.set_selected(False)
            
        # Emit the signal
        gallery.folder_selected.emit(folder_name)
    
    @staticmethod
    def on_folder_enter(gallery, folder_name):
        """Handle entering a folder"""
        print(f"🔍 LISTENER: Entering folder '{folder_name}'")
        
        # Update gallery state
        gallery.current_folder = folder_name
        gallery.selected_template = None
        gallery.selected_folder = None
        
        # Update UI and populate templates in this folder
        gallery.populate_gallery(force_refresh=True)
        
        # Update breadcrumb
        if hasattr(gallery, 'breadcrumb_label'):
            gallery.breadcrumb_label.setText(f"Folder: {folder_name}")
            gallery.breadcrumb_label.show()
            
        # Show back button
        if hasattr(gallery, 'back_button'):
            gallery.back_button.setVisible(True)
            
        print(f"🔍 LISTENER: Successfully entered folder '{folder_name}'")
    
    @staticmethod
    def on_back_to_all(gallery):
        """Handle navigation back to root view"""
        current_folder = gallery.current_folder
        print(f"🔍 LISTENER: Navigating back from folder '{current_folder}' to root view")
        
        # Reset state
        gallery.current_folder = None
        gallery.selected_template = None
        gallery.selected_folder = None
        
        # Update UI
        gallery.populate_gallery(force_refresh=True)
        
        # Hide breadcrumb
        if hasattr(gallery, 'breadcrumb_label'):
            gallery.breadcrumb_label.hide()
            
        # Hide back button
        if hasattr(gallery, 'back_button'):
            gallery.back_button.setVisible(False)
            
        print(f"🔍 LISTENER: Successfully returned to root view from folder '{current_folder}'")
    
    @staticmethod
    def on_add_template(gallery):
        """Handle add template button click"""
        try:
            # Make sure we have access to the template manager
            if not hasattr(gallery, 'app') or not hasattr(gallery.app, 'template_manager'):
                QMessageBox.warning(gallery, "Error", "Template manager not available.")
                return
                
            # Get template name from user
            template_name, ok = QInputDialog.getText(
                gallery,
                "New Template",
                "Enter template name:"
            )
            
            if not ok or not template_name:
                return
            
            # Create an empty template - no category (using 'Default' as placeholder)
            # and no file association yet
            try:
                success = gallery.app.template_manager.save_template(
                    template_name,
                    "",  # No file path yet - user will add files in the editor
                    "Standard",  # Structure type
                    "New template"  # Description
                )
                
                if success:
                    # Refresh gallery with the new template
                    gallery.populate_gallery(force_refresh=True)
                else:
                    print(f"Error adding template: Failed to save template")
            except Exception as e:
                print(f"Error adding template: {e}")
            
            # Get the newly created template
            new_template = gallery.app.template_manager.get_template_by_name(template_name)
            
            if not new_template:
                QMessageBox.warning(gallery, "Error", f"Failed to retrieve template '{template_name}' after creation.")
                gallery.populate_gallery()
                return
            
            # If we're in a folder, add the template to it
            if hasattr(gallery, 'current_folder') and gallery.current_folder:
                print(f"Adding new template '{template_name}' to current folder '{gallery.current_folder}'")
                gallery.app.template_manager.add_to_folder(gallery.current_folder, template_name)
            
            # Prompt user to select an existing structure or create a new one
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QTextEdit
            from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
            
            structure_dialog = QDialog(gallery)
            structure_dialog.setWindowTitle("Template Structure")
            structure_dialog.resize(500, 400)  # Make dialog larger to better show preview
            
            # Apply styling to the dialog
            structure_dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors.get('bg', '#1E1E1E')};
                    color: {colors.get('text', '#FFFFFF')};
                }}
                QLabel {{
                    color: {colors.get('text', '#FFFFFF')};
                }}
            """)
            
            layout = QVBoxLayout(structure_dialog)
            layout.setContentsMargins(20, 20, 20, 20)  # Add more padding
            layout.setSpacing(15)  # Increase spacing between widgets
            
            # Instruction label
            instructions = QLabel("Select a file structure for this template or create a new one:")
            instructions.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {colors.get('text', '#FFFFFF')};")
            layout.addWidget(instructions)
            
            # Get available structures - make sure we get ALL structures
            available_structures = ["Create New Structure"]
            
            # Add default structures from constants
            if hasattr(gallery.app, 'template_manager'):
                # First add default structures from constants
                from app.constants import DEFAULT_STRUCTURES
                if hasattr(gallery.app.template_manager, 'get_structure_names'):
                    # Use the method if available
                    all_structures = gallery.app.template_manager.get_structure_names()
                    available_structures.extend(all_structures)
                else:
                    # Fallback to manual loading
                    # Add default structures from constants
                    if 'DEFAULT_STRUCTURES' in dir(gallery.app.template_manager):
                        default_structures = list(gallery.app.template_manager.DEFAULT_STRUCTURES.keys())
                        available_structures.extend(default_structures)
                    
                    # Add custom structures
                    if hasattr(gallery.app.template_manager, 'custom_structures'):
                        custom_structures = []
                        # Handle custom_structures as a list of dictionaries
                        if isinstance(gallery.app.template_manager.custom_structures, list):
                            for struct in gallery.app.template_manager.custom_structures:
                                if isinstance(struct, dict) and 'name' in struct:
                                    custom_structures.append(struct['name'])
                        # Or handle it as a dictionary for backward compatibility
                        elif isinstance(gallery.app.template_manager.custom_structures, dict):
                            custom_structures = list(gallery.app.template_manager.custom_structures.keys())
                        
                        # Filter out duplicates
                        for struct in custom_structures:
                            if struct not in available_structures:
                                available_structures.append(struct)
                    
                    # Try to get built-in structures another way
                    try:
                        from app.constants import DEFAULT_STRUCTURES
                        for struct in DEFAULT_STRUCTURES.keys():
                            if struct not in available_structures:
                                available_structures.append(struct)
                    except ImportError:
                        print("Could not import DEFAULT_STRUCTURES from app.constants")
            
            # Sort alphabetically (keeping Create New Structure at the top)
            create_new = available_structures[0]
            available_structures = available_structures[1:]
            available_structures.sort()
            available_structures.insert(0, create_new)
            
            # Remove duplicates while preserving order
            unique_structures = []
            seen = set()
            for struct in available_structures:
                if struct not in seen:
                    unique_structures.append(struct)
                    seen.add(struct)
            available_structures = unique_structures
            
            # Structure selection dropdown
            structure_combo = QComboBox()
            
            # Set minimum width like in the structure editor
            structure_combo.setMinimumWidth(250)
            
            # Apply the standard style from the structure editor
            structure_combo.setStyleSheet(COMBOBOX_STYLE)
            
            for structure in available_structures:
                structure_combo.addItem(structure)
            layout.addWidget(structure_combo)
            
            # Add a preview section
            preview_label = QLabel("Structure Preview:")
            preview_label.setStyleSheet(f"font-weight: bold; margin-top: 10px; color: {colors.get('text', '#FFFFFF')};")
            layout.addWidget(preview_label)
            
            # Use QTextEdit instead of QLabel for better scrolling and formatting
            preview_text = QTextEdit()
            preview_text.setReadOnly(True)
            preview_text.setMinimumHeight(150)  # Much taller preview area
            
            # Use the app's color scheme
            preview_text.setStyleSheet(f"""
                background-color: {colors.get('card_bg', '#2A2A2A')};
                color: {colors.get('text', '#FFFFFF')};
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                border: 1px solid {colors.get('card_bg', '#2A2A2A')};
            """)
            layout.addWidget(preview_text)
            
            # Update preview when structure is selected
            def update_preview(index):
                try:
                    structure_name = structure_combo.currentText()
                    if structure_name == "Create New Structure":
                        preview_text.setText("You will create a new structure in the editor")
                        return
                    
                    # Try multiple ways to get the structure
                    structure = None
                    
                    # Method 1: Direct call to get_structure
                    if hasattr(gallery.app.template_manager, 'get_structure'):
                        try:
                            structure = gallery.app.template_manager.get_structure(structure_name)
                        except Exception as e:
                            print(f"Method 1 error: {e}")
                    
                    # Method 2: Check in custom_structures
                    if structure is None and hasattr(gallery.app.template_manager, 'custom_structures'):
                        if structure_name in gallery.app.template_manager.custom_structures:
                            structure = gallery.app.template_manager.custom_structures[structure_name]
                    
                    # Method 3: Try to get from DEFAULT_STRUCTURES
                    if structure is None:
                        try:
                            from app.constants import DEFAULT_STRUCTURES
                            if structure_name in DEFAULT_STRUCTURES:
                                structure = DEFAULT_STRUCTURES[structure_name]
                        except (ImportError, KeyError) as e:
                            print(f"Method 3 error: {e}")
                    
                    # Format and display the preview
                    if structure:
                        # Create a formatted visual representation of the structure instead of raw display
                        preview = ""
                        
                        def format_structure(items, indent=""):
                            result = []
                            
                            for item in items:
                                if isinstance(item, dict):
                                    # It's a directory with children (or empty directory)
                                    for dir_name, children in item.items():
                                        result.append(f"{indent}📁 {dir_name}/")
                                        if children:  # Only process if there are children
                                            child_result = format_structure(children, indent + "  ")
                                            if child_result:
                                                result.append(child_result)
                                elif isinstance(item, str):
                                    # It's a file or legacy empty directory
                                    if item.endswith('/'):
                                        # Legacy format folder
                                        result.append(f"{indent}📁 {item.rstrip('/')}/")
                                    # Check for folder-like patterns in string items
                                    elif '.' not in item or (item.startswith(tuple("0123456789")) and '_' in item[:4]):
                                        # Probably a folder if no extension or has numeric prefix
                                        result.append(f"{indent}📁 {item}/")
                                    # Check for common folder names
                                    elif any(keyword in item.lower() for keyword in [
                                        'folder', 'dir', 'footage', 'audio', 'video', 'gfx', 'exports',
                                        'assets', 'renders', 'project', 'images', 'documents'
                                    ]):
                                        result.append(f"{indent}📁 {item}/")
                                    else:
                                        # Regular file
                                        result.append(f"{indent}📄 {item}")
                            
                            return "\n".join(result)
                        
                        if isinstance(structure, list):
                            if not structure:
                                preview_text.setText("Empty structure")
                            else:
                                preview = format_structure(structure)
                                preview_text.setText(preview)
                        elif isinstance(structure, dict):
                            # For dictionary structures, format the keys as folders
                            preview = "\n".join([f"📁 {key}/" for key in list(structure.keys())[:10]])
                            if len(structure) > 10:
                                preview += f"\n\n... and {len(structure) - 10} more folders"
                            preview_text.setText(preview)
                        else:
                            # For any other type, convert to string safely
                            preview_text.setText(str(structure)[:500])
                    else:
                        # No structure found
                        preview_text.setText(f"Structure '{structure_name}' exists but preview is not available.\n\nYou can still use it.")
                except Exception as e:
                    print(f"Preview error for '{structure_combo.currentText()}': {e}")
                    import traceback
                    traceback.print_exc()
                    preview_text.setText("Preview not available")
            
            structure_combo.currentIndexChanged.connect(update_preview)
            # Initialize preview
            update_preview(0)
            
            # Buttons
            button_layout = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(structure_dialog.reject)
            
            select_btn = QPushButton("Select")
            select_btn.setDefault(True)
            
            # Add styling to make the select button stand out
            select_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
            cancel_btn.setStyleSheet(BUTTON_STYLE)
            
            button_layout.addStretch(1)  # Push buttons to the right
            button_layout.addWidget(cancel_btn)
            button_layout.addWidget(select_btn)
            layout.addLayout(button_layout)
            
            # Store selected structure
            selected_structure = [None]
            
            def on_select():
                selected_structure[0] = structure_combo.currentText()
                structure_dialog.accept()
            
            select_btn.clicked.connect(on_select)
            
            # Show dialog
            result = structure_dialog.exec_()
            
            if result == QDialog.Accepted and selected_structure[0]:
                structure_name = selected_structure[0]
                
                # Set structure name in template
                if structure_name != "Create New Structure":
                    new_template['structure_name'] = structure_name
                else:
                    # Create a new structure named after the template
                    new_template['structure_name'] = f"Template_{template_name}"
                
                # Open the editor immediately so user can add files and set up structure
                from app.dialogs.dialog_windows_pyqt import show_edit_template
                show_edit_template(gallery, new_template, lambda t: gallery.app.template_manager.update_template(t))
            else:
                # User cancelled, but we already created the template, so we'll just keep it
                pass
            
            # Refresh the gallery to show the new template
            
            # Force reload templates from the template manager first
            if hasattr(gallery.app, 'template_manager'):
                # Reload templates from disk to ensure we have the latest data
                if hasattr(gallery.app.template_manager, 'load_templates'):
                    print("🔍 LISTENER: Reloading templates from template manager")
                    gallery.app.template_manager.load_templates()
                
                # Also reload folders if method exists
                if hasattr(gallery.app.template_manager, 'load_folders'):
                    print("🔍 LISTENER: Reloading folders from template manager")
                    gallery.app.template_manager.load_folders()
            
            # Now refresh the gallery with force_refresh=True
            print("🔍 LISTENER: Forcing gallery refresh to show new template")
            gallery.populate_gallery(force_refresh=True)
            
            # Select the newly created template if it exists
            if new_template and hasattr(gallery, '_on_template_select'):
                print(f"🔍 LISTENER: Selecting newly created template: {template_name}")
                gallery._on_template_select(new_template)
            
        except Exception as e:
            import traceback
            print(f"Error adding template: {e}")
            print(traceback.format_exc())
            QMessageBox.warning(gallery, "Error", f"Failed to add template: {str(e)}")
    
    @staticmethod
    def on_edit_template(gallery, template_name=None):
        """Handle edit template action (from button or context menu)"""
        try:
            print(f"on_edit_template called with template_name: {template_name}")
            print(f"gallery has app? {hasattr(gallery, 'app')}")
            
            # Create a fallback template manager if needed
            if not hasattr(gallery, 'app') or gallery.app is None:
                print("Gallery app is None, creating a fallback app reference")
                from app.core.app_module_pyqt import ProjectCreatorApp
                if not hasattr(gallery, 'app') or gallery.app is None:
                    gallery.app = ProjectCreatorApp.get_instance()
                    print(f"Created fallback app: {gallery.app}")
            
            # If app exists but template_manager doesn't, try to create one
            if hasattr(gallery, 'app') and gallery.app is not None:
                if not hasattr(gallery.app, 'template_manager') or gallery.app.template_manager is None:
                    print("App template_manager is None, creating a fallback")
                    from app.templates.template_manager import TemplateManager
                    gallery.app.template_manager = TemplateManager()
                    print(f"Created fallback template_manager: {gallery.app.template_manager}")
            
            # Display debug info
            if hasattr(gallery, 'app'):
                print(f"App is: {gallery.app}")
                print(f"App has template_manager? {hasattr(gallery.app, 'template_manager')}")
                if hasattr(gallery.app, 'template_manager'):
                    print(f"Template_manager is: {gallery.app.template_manager}")
            
            # Get the template name - either directly passed or from the selected template
            if template_name is None and gallery.selected_template:
                if isinstance(gallery.selected_template, dict):
                    template_name = gallery.selected_template.get('name')
                else:
                    template_name = gallery.selected_template
                    
            print(f"Resolved template_name: {template_name}")
                    
            # If we have a template name, select it first to make sure it's the current selection
            if template_name and hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'get_template_by_name'):
                template = gallery.app.template_manager.get_template_by_name(template_name)
                if template:
                    gallery._on_template_select(template)
            
            # Now proceed with editing the selected template
            if gallery.selected_template and hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'edit_template'):
                gallery.app.template_manager.edit_template(gallery.selected_template)
                gallery.populate_gallery()
            else:
                print(f"Cannot edit template: gallery.selected_template={gallery.selected_template}, " +
                      f"has template_manager={hasattr(gallery.app, 'template_manager')}, " +
                      f"has edit_template={hasattr(gallery.app.template_manager, 'edit_template') if hasattr(gallery.app, 'template_manager') else False}")
        except Exception as e:
            import traceback
            print(f"Error editing template: {e}")
            print(traceback.format_exc())
    
    @staticmethod
    def on_delete_template(gallery, template_name=None):
        """Handle delete template action (from button, context menu, or keyboard)"""
        print(f"[DEBUG] Gallery: Delete request for template '{template_name}'")
        
        # Check if we're dealing with multi-selected templates
        has_multi = (hasattr(gallery, 'multi_selected_templates') and 
                    gallery.multi_selected_templates and 
                    len(gallery.multi_selected_templates) > 0)
        
        # Check if we need to handle multi-selection deletion
        if has_multi:
            # Create a list to hold all templates to delete
            templates_to_delete_set = set()
            templates_to_delete = []
            
            # Always include the primary selected template first
            if hasattr(gallery, 'selected_template') and gallery.selected_template:
                primary_name = gallery.selected_template.get('name', 'Unknown')
                templates_to_delete.append(gallery.selected_template)
                templates_to_delete_set.add(id(gallery.selected_template))
                print(f"[DEBUG] Gallery: Including primary selected template '{primary_name}' in multi-delete")
            
            # Add all multi-selected templates
            for template in gallery.multi_selected_templates:
                template_id = id(template)
                if template_id not in templates_to_delete_set:
                    templates_to_delete.append(template)
                    templates_to_delete_set.add(template_id)
                    print(f"[DEBUG] Gallery: Adding multi-selected template '{template.get('name', 'Unknown')}' to delete operation")
            
            # Process all templates
            template_names = []
            for template in templates_to_delete:
                if isinstance(template, dict):
                    name = template.get('name', 'Unknown')
                else:
                    name = str(template)
                
                if name and name not in template_names:
                    template_names.append(name)
            
            # Create confirmation message
            if len(template_names) == 1:
                message = f"Are you sure you want to delete template '{template_names[0]}'?"
            else:
                message = f"Are you sure you want to delete these {len(template_names)} templates?"
            
            # Show single confirmation for all templates
            confirm = QMessageBox.question(
                gallery,
                "Confirm Delete",
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Delete all templates
                if hasattr(gallery.app, 'template_manager'):
                    template_manager = gallery.app.template_manager
                    for name in template_names:
                        print(f"[DEBUG] Gallery: Deleting template '{name}' in multi-delete")
                        template_manager.delete_template(name)
                    
                    # Reset selection
                    gallery.selected_template = None
                    
                    # Clear multi-selection
                    gallery.multi_selected_templates.clear()
                    
                    # Force reload of template data
                    if hasattr(template_manager, 'load_templates'):
                        template_manager.load_templates()
                    if hasattr(template_manager, 'load_folders'):
                        template_manager.load_folders()
                    
                    # Refresh the gallery
                    gallery.populate_gallery(force_refresh=True)
                    
                    # Show success message
                    if hasattr(gallery.app, 'show_status_message'):
                        if len(template_names) == 1:
                            gallery.app.show_status_message(f"Deleted template '{template_names[0]}'", "success")
                        else:
                            gallery.app.show_status_message(f"Deleted {len(template_names)} templates", "success")
                
                return
        
        # Single template deletion (original behavior)
        # Get the template name - either directly passed or from the selected template
        if template_name is None and gallery.selected_template:
            if isinstance(gallery.selected_template, dict):
                template_name = gallery.selected_template.get('name')
            else:
                template_name = gallery.selected_template
        
        if not template_name:
            print(f"[DEBUG] Gallery: No template name provided for deletion")
            return
        
        # Check if we have a valid template manager
        if not hasattr(gallery.app, 'template_manager') or not hasattr(gallery.app.template_manager, 'delete_template'):
            print(f"[DEBUG] Gallery: Template manager not available")
            return
        
        # Get the actual template object to make sure we're using the correct name
        template_manager = gallery.app.template_manager
        template = template_manager.get_template_by_name(template_name)
        
        if not template:
            # Extra debugging for Template-# cases
            if template_name.startswith("Template-"):
                print(f"[DEBUG] Gallery: Attempting to find real template for '{template_name}'")
                # Try to find by looking through all templates
                for t in template_manager.templates + template_manager.template_directories:
                    if t.get('name') == template_name or t.get('display_name') == template_name:
                        template = t
                        break
        
        if template:
            real_template_name = template.get('name')
            print(f"[DEBUG] Gallery: Found template '{real_template_name}' for deletion")
        else:
            real_template_name = template_name
            print(f"[DEBUG] Gallery: Could not find template object for '{template_name}'")
        
        # Confirm deletion with dialog
        confirm = QMessageBox.question(
            gallery,
            "Confirm Delete",
            f"Are you sure you want to delete template '{real_template_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete the template
            print(f"[DEBUG] Gallery: Calling delete_template for '{real_template_name}'")
            success = template_manager.delete_template(real_template_name)
            
            if success:
                print(f"[DEBUG] Gallery: Successfully deleted template '{real_template_name}'")
                # If we used a different name than provided, also try to delete that
                if real_template_name != template_name:
                    print(f"[DEBUG] Gallery: Also attempting to delete '{template_name}'")
                    template_manager.delete_template(template_name)
                
                # Reset selection
                gallery.selected_template = None
                
                # Force reload of template data
                if hasattr(template_manager, 'load_templates'):
                    template_manager.load_templates()
                if hasattr(template_manager, 'load_folders'):
                    template_manager.load_folders()
                
                # Refresh the gallery
                gallery.populate_gallery(force_refresh=True)
            else:
                print(f"[DEBUG] Gallery: Failed to delete template '{real_template_name}'")
                QMessageBox.warning(gallery, "Error", f"Failed to delete template '{real_template_name}'.")
                
                # Try deletion with original name as fallback
                if real_template_name != template_name:
                    print(f"[DEBUG] Gallery: Trying fallback deletion with '{template_name}'")
                    success = template_manager.delete_template(template_name)
                    if success:
                        print(f"[DEBUG] Gallery: Fallback deletion succeeded")
                        gallery.selected_template = None
                        gallery.populate_gallery(force_refresh=True)
    
    @staticmethod
    def on_manage_templates(gallery):
        """Handle manage templates button click
        
        Note: The "Manage All" button has been removed from the UI as its functionality
        is redundant with other UI elements, but this method is kept for programmatic use
        or in case it's called from elsewhere in the codebase.
        """
        if hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'manage_templates'):
            gallery.app.template_manager.manage_templates()
            gallery.populate_gallery()
    
    @staticmethod
    def on_add_folder(gallery):
        """Handle add folder button click"""
        if hasattr(gallery.app, 'template_manager'):
            # Get folder name from dialog
            folder_name, ok = QInputDialog.getText(None, "Add Folder", "Folder Name:")
            if ok and folder_name:
                # Create the folder without asking for a category
                gallery.app.template_manager.create_folder(folder_name)
                
                # Populate gallery and force immediate UI update
                gallery.populate_gallery(force_refresh=True)
                
                # Force immediate UI refresh for both view containers
                gallery.folders_section.update()
                gallery.folders_section.repaint()
                
                # Process pending events to ensure UI is updated
                QApplication.processEvents()
    
    @staticmethod
    def on_rename_folder(gallery):
        """Handle rename folder button click"""
        if gallery.selected_folder:
            # Find the selected folder card and trigger rename
            for card in gallery.folder_cards:
                if hasattr(card, '_start_rename'):
                    card._start_rename()
                    break
    
    @staticmethod
    def on_rename_folder_requested(gallery, folder_name):
        """Handle rename folder requested signal"""
        gallery.selected_folder = folder_name
    
    @staticmethod
    def on_rename_folder_done(gallery, old_name, new_name):
        """Handle rename folder done signal"""
        if hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'rename_folder'):
            gallery.app.template_manager.rename_folder(old_name, new_name)
            gallery.selected_folder = new_name
            gallery.populate_gallery()
    
    @staticmethod
    def on_delete_folder(gallery):
        """Handle delete folder button click"""
        if gallery.selected_folder and hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'delete_folder'):
            gallery.app.template_manager.delete_folder(gallery.selected_folder)
            gallery.selected_folder = None
            gallery.populate_gallery()

    @staticmethod
    def on_icon_scale_changed(gallery, value):
        """Handle icon scale slider value change"""
        gallery.icon_scale = value
        gallery._update_card_sizes()
    
    @staticmethod
    def update_card_sizes(gallery):
        """Update card sizes based on scale"""
        # Update both folder and template cards
        gallery._update_folder_card_sizes(gallery.icon_scale)
    
    @staticmethod
    def key_press_event(gallery, event):
        """Handle keyboard events in the template gallery"""
        # Check for dialogs - safely check for attribute first
        if hasattr(gallery, 'isDialogOpen') and gallery.isDialogOpen:
            return False
            
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle undo/redo shortcuts
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key_Z:
                print(f"🔍 LISTENER: Ctrl+Z pressed")
                if hasattr(gallery.app, 'undo'):
                    gallery.app.undo()
                return True
            elif (key == Qt.Key_Y) or (modifiers & Qt.ShiftModifier and key == Qt.Key_Z):
                print(f"🔍 LISTENER: Ctrl+Y or Ctrl+Shift+Z pressed")
                if hasattr(gallery.app, 'redo'):
                    gallery.app.redo()
                return True
                
        shift_modifier = bool(modifiers & Qt.ShiftModifier)
        
        # Multi-select with arrow keys while holding Shift
        if shift_modifier and key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            print(f"🔍 LISTENER: Multi-select with arrow keys (key: {key})")
            gallery._handle_shift_arrow_selection(key)
            return True
                
        # Handle template deletion with backspace and delete keys
        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            print(f"🔍 LISTENER: Delete key pressed")

            # First, determine what we'll be deleting
            has_primary = hasattr(gallery, 'selected_template') and gallery.selected_template is not None
            has_multi = (hasattr(gallery, 'multi_selected_templates') and 
                       gallery.multi_selected_templates and 
                       len(gallery.multi_selected_templates) > 0)
            
            # If nothing to delete, do nothing
            if not has_primary and not has_multi:
                print(f"🔍 LISTENER: No templates selected for deletion")
                return True
            
            # Create a fresh set of templates to delete (using set for deduplication)
            templates_to_delete_set = set()
            templates_to_delete = []
            
            # ALWAYS include the primary selected template FIRST if it exists
            if has_primary:
                primary_name = gallery.selected_template.get('name', 'Unknown')
                templates_to_delete.append(gallery.selected_template)
                templates_to_delete_set.add(id(gallery.selected_template))  # Add object id to set for tracking
                print(f"🔍 LISTENER: Gallery - Including primary selected template in delete operation: {primary_name}")
            
            # Then add the multi-selected templates
            if has_multi:
                for template in gallery.multi_selected_templates:
                    template_id = id(template)
                    if template_id not in templates_to_delete_set:
                        templates_to_delete.append(template)
                        templates_to_delete_set.add(template_id)
                        print(f"🔍 LISTENER: Gallery - Adding multi-selected template to delete operation: {template.get('name', 'Unknown')}")
            
            # Verify total count matches expectations
            expected_count = (1 if has_primary else 0) + (len(gallery.multi_selected_templates) if has_multi else 0)
            actual_count = len(templates_to_delete)
            print(f"🔍 LISTENER: Gallery - Expected {expected_count} templates, found {actual_count} templates after deduplication")
            
            # If no templates to delete, do nothing
            if not templates_to_delete:
                print(f"🔍 LISTENER: Gallery - No templates to delete after processing")
                return True
            
            # Get template names for display and deletion
            template_names = []
            for template in templates_to_delete:
                name = template.get('name', 'Unknown')
                if name and name not in template_names:
                    template_names.append(name)
                    print(f"🔍 LISTENER: Gallery - Template to delete: '{name}'")
            
            # If no valid template names, do nothing
            if not template_names:
                print(f"🔍 LISTENER: Gallery - No valid template names found for deletion")
                return True
                
            print(f"🔍 LISTENER: Gallery - Final delete list ({len(template_names)} templates): {template_names}")
            
            # Create confirmation message
            if len(template_names) == 1:
                message = f"Are you sure you want to delete template '{template_names[0]}'?"
            else:
                message = f"Are you sure you want to delete these {len(template_names)} templates?"
            
            # Single confirmation for all templates
            confirm = QMessageBox.question(
                gallery,
                "Confirm Delete",
                message,
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Delete all templates in one operation
                if hasattr(gallery.app, 'template_manager'):
                    for name in template_names:
                        print(f"🔍 LISTENER: Gallery - Deleting template '{name}'")
                        gallery.app.template_manager.delete_template(name)
                
                # Show success message
                if hasattr(gallery.app, 'show_status_message'):
                    if len(template_names) == 1:
                        gallery.app.show_status_message(f"Deleted template '{template_names[0]}'", "success")
                    else:
                        gallery.app.show_status_message(f"Deleted {len(template_names)} templates", "success")
                
                # Reset selections
                gallery.selected_template = None
                    
                # Clear multi-selection
                if hasattr(gallery, 'multi_selected_templates'):
                    gallery.multi_selected_templates.clear()
                    
                # Reload template data
                if (hasattr(gallery.app, 'template_manager') and 
                    hasattr(gallery.app.template_manager, 'load_templates')):
                    gallery.app.template_manager.load_templates()
                    
                if (hasattr(gallery.app, 'template_manager') and 
                    hasattr(gallery.app.template_manager, 'load_folders')):
                    gallery.app.template_manager.load_folders()
                
                # Refresh the gallery
                gallery.populate_gallery(force_refresh=True)
                
            return True
        else:
            # Call the parent's keyPressEvent
            return False

    @staticmethod
    def on_move_template_to_folder(gallery, template_name, folder_name):
        """Handle moving a template to a folder"""
        print(f"🔍 LISTENER: Moving template '{template_name}' to folder '{folder_name}'")
        
        # Validate inputs
        if not template_name:
            print(f"🔍 LISTENER: Invalid template name: '{template_name}'")
            return False
        
        # Get template manager
        if not hasattr(gallery.app, 'template_manager'):
            print(f"🔍 LISTENER: Template manager not available")
            return False
        
        template_manager = gallery.app.template_manager
        
        # Check if this is a multi-template operation (comma-separated list)
        if ',' in template_name:
            # Multi-template case
            template_names = [name.strip() for name in template_name.split(',') if name.strip()]
            
            # If the gallery has a selected template that's not in this list, also include it
            if hasattr(gallery, 'selected_template') and gallery.selected_template:
                selected_name = gallery.selected_template.get('name', None)
                if selected_name and selected_name not in template_names:
                    template_names.insert(0, selected_name)
                    print(f"🔍 LISTENER: Added main selected template '{selected_name}' to move operation")
        else:
            # Single template case
            template_names = [template_name]
        
        # Process all template names
        success_count = 0
        
        for single_template_name in template_names:
            # Skip empty names
            if not single_template_name:
                continue
                
            # Check for special folder names
            if folder_name == "Root" or folder_name == "Up a Level":
                print(f"🔍 LISTENER: Moving template '{single_template_name}' to root (removing from folders)")
                
                # For Root, remove from all folders
                has_changes = False
                
                # If we're in a folder, remove from current folder
                if hasattr(gallery, 'current_folder') and gallery.current_folder:
                    print(f"🔍 LISTENER: Removing template '{single_template_name}' from folder '{gallery.current_folder}'")
                    result = template_manager.remove_from_folder(gallery.current_folder, single_template_name)
                    has_changes = has_changes or result
                else:
                    # If not in a folder, find and remove from any folder it's in
                    if hasattr(template_manager, 'folders'):
                        for folder, templates in template_manager.folders.items():
                            if single_template_name in templates:
                                print(f"🔍 LISTENER: Removing template '{single_template_name}' from folder '{folder}'")
                                result = template_manager.remove_from_folder(folder, single_template_name)
                                has_changes = has_changes or result
                
                # Count successful operations
                if has_changes:
                    success_count += 1
            else:
                # Normal folder move
                # Move template to folder
                try:
                    result = template_manager.move_template_to_folder(single_template_name, folder_name)
                    if result:
                        success_count += 1
                except Exception as e:
                    print(f"🔍 LISTENER: Error moving template to folder: {e}")
        
        # Update UI based on the results
        if success_count > 0:
            message = f"Template moved to {folder_name if folder_name not in ['Root', 'Up a Level'] else 'root'}"
            if success_count > 1:
                message = f"{success_count} templates moved to {folder_name if folder_name not in ['Root', 'Up a Level'] else 'root'}"
                
            print(f"🔍 LISTENER: {message}")
            
            # Show success message
            if hasattr(gallery.app, 'show_status_message'):
                gallery.app.show_status_message(message, "info")
            
            # Make sure the back button is visible if we're in a folder
            if hasattr(gallery, 'current_folder') and gallery.current_folder:
                if hasattr(gallery, 'back_button'):
                    gallery.back_button.setVisible(True)
                if hasattr(gallery, 'breadcrumb_label'):
                    gallery.breadcrumb_label.show()
            
            # Force refresh the gallery
            gallery.populate_gallery(force_refresh=True)
            return True
        else:
            print(f"🔍 LISTENER: No templates were moved successfully")
            return False 