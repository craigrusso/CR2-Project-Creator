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
        print(f"on_template_select called with template: {template}")
        
        # Check if this is the same template as already selected
        if hasattr(gallery, 'selected_template') and gallery.selected_template == template:
            # If clicking the same template again, don't do anything
            print("Same template selected, no change needed")
            return
            
        # Set the selected template in multiple places to ensure consistency
        gallery.selected_template = template
        
        # Also ensure it's set in the app object if available
        if hasattr(gallery, 'app'):
            gallery.app.selected_template = template
            print("App-level selected_template has been updated")
        
        gallery.selected_folder = None  # Reset folder selection
        print(f"Selected template set to: {template}")
        
        # Update card styling for all cards
        if hasattr(gallery, 'template_cards') and gallery.template_cards:
            card_count = len(gallery.template_cards)
            print(f"Updating card styling for {card_count} cards")
            for card in gallery.template_cards:
                if hasattr(card, 'template') and card.template == template:
                    print(f"Setting card selected for template: {template}")
                    card.set_selected(True)
                else:
                    card.set_selected(False)
        
        # Also ensure the template selection state is reapplied after grid repopulation
        # by forcing a gallery refresh
        gallery.populate_gallery(force_refresh=False)  # No need to reload data, just refresh UI
        
        # Emit template selected event if using PyQt
        if hasattr(gallery, 'template_selected'):
            gallery.template_selected.emit(template)
    
    @staticmethod
    def on_folder_select(gallery, folder_name):
        """Handle folder selection"""
        if hasattr(gallery, 'selected_folder') and gallery.selected_folder == folder_name:
            # If clicking the same folder again, don't do anything
            return
            
        gallery.selected_folder = folder_name
        gallery.selected_template = None  # Reset template selection
        
        # Update button states (removed edit and delete buttons)
        gallery.delete_folder_button.setEnabled(True)
        
        # Update card styling for folders
        for card in gallery.folder_cards:
            if hasattr(card, 'folder_name') and card.folder_name == folder_name:
                card.set_selected(True)
            else:
                card.set_selected(False)
                
        # Update card styling for templates - none selected
        for card in gallery.template_cards:
            card.set_selected(False)
            
        # Emit the signal
        gallery.folder_selected.emit(folder_name)
    
    @staticmethod
    def on_folder_enter(gallery, folder_name):
        """Handle folder double-click/enter"""
        # Set the current folder and refresh the view
        gallery.current_folder = folder_name
        
        # Update the folder label
        gallery.folder_label.setText(f"Current Folder: {folder_name}")
        
        # Show the folder navigation bar
        gallery.folder_nav.setVisible(True)
        
        # Hide the folders section
        gallery.folders_section.setVisible(False)
        
        # Refresh to show only templates in this folder
        gallery.populate_gallery()
    
    @staticmethod
    def on_back_to_all(gallery):
        """Handle back to all folders button"""
        # Reset the current folder
        gallery.current_folder = None
        
        # Hide the folder navigation bar
        gallery.folder_nav.setVisible(False)
        
        # Show the folders section
        gallery.folders_section.setVisible(True)
        
        # Refresh to show all folders and templates
        gallery.populate_gallery()
    
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
            success = gallery.app.template_manager.save_template(
                template_name,
                "Default",  # Using Default instead of category since categories are no longer used
                "",  # No file yet - user will add files in the editor
                "Standard"
            )
            
            if not success:
                QMessageBox.warning(gallery, "Error", f"Failed to create template '{template_name}'.")
                return
            
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
                                        result.append(f"{indent}📁 {item.rstrip('/')}/")
                                    else:
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
            gallery.populate_gallery()
            
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
        """Handle manage templates button click"""
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
                # Get categories using our custom dropdown dialog for proper styling
                categories = gallery.app.template_manager.get_categories() if hasattr(gallery.app.template_manager, 'get_categories') else ["Video Editing", "Motion Graphics", "Design", "Audio", "Custom"]
                
                # Create and show our custom styled dialog
                dialog = StyledItemDialog(
                    gallery,
                    "Select Category",
                    "Choose folder category:",
                    categories
                )
                
                if dialog.exec_() == QDialog.Accepted:
                    category = dialog.selectedItem()
                    # Create the folder
                    gallery.app.template_manager.create_folder(folder_name, category)
                    gallery.populate_gallery()
                else:
                    # If user cancels selecting a category, just create with default
                    gallery.app.template_manager.create_folder(folder_name)
                    gallery.populate_gallery()
    
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
        """Handle keyboard shortcuts"""
        # Delete key handling
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Handle folder deletion
            if gallery.selected_folder:
                # Don't allow deleting default folders
                if gallery.selected_folder in ["General", "Development", "Business"]:
                    QMessageBox.warning(gallery, "Error", f"'{gallery.selected_folder}' is a default folder and cannot be deleted.")
                    return
                    
                # Show confirmation dialog
                confirm = QMessageBox.question(
                    gallery,
                    "Confirm Delete",
                    f"Are you sure you want to delete folder '{gallery.selected_folder}'?\n"
                    "Templates in this folder will remain available but will be moved to the root.",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if confirm == QMessageBox.Yes:
                    # Delete folder
                    if hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'delete_folder'):
                        gallery.app.template_manager.delete_folder(gallery.selected_folder)
                        gallery.selected_folder = None
                        gallery.populate_gallery(force_refresh=True)
            
            # Handle template deletion
            elif gallery.selected_template:
                template_name = None
                if isinstance(gallery.selected_template, dict):
                    template_name = gallery.selected_template.get('name')
                else:
                    template_name = gallery.selected_template
                    
                if template_name:
                    # Show confirmation dialog
                    confirm = QMessageBox.question(
                        gallery,
                        "Confirm Delete",
                        f"Are you sure you want to delete template '{template_name}'?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if confirm == QMessageBox.Yes:
                        # Delete template
                        if hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'delete_template'):
                            gallery.app.template_manager.delete_template(template_name)
                            gallery.selected_template = None
                            gallery.populate_gallery()
        else:
            # Call the parent's keyPressEvent
            pass  # This will be handled in the refactored main class 

    @staticmethod
    def on_move_template_to_folder(gallery, template_name, folder_name):
        """Handle moving a template to a folder"""
        print(f"[DEBUG] Gallery: Moving template '{template_name}' to folder '{folder_name}'")
        
        # Validate inputs
        if not template_name or not folder_name:
            print(f"[DEBUG] Gallery: Invalid template or folder name: '{template_name}', '{folder_name}'")
            return False
        
        # Get template manager
        if not hasattr(gallery.app, 'template_manager'):
            print(f"[DEBUG] Gallery: Template manager not available")
            return False
        
        template_manager = gallery.app.template_manager
        
        # Move template to folder
        try:
            result = template_manager.move_template_to_folder(template_name, folder_name)
            
            if result:
                print(f"[DEBUG] Gallery: Successfully moved template '{template_name}' to folder '{folder_name}'")
                # Show success message
                if hasattr(gallery.app, 'show_status_message'):
                    gallery.app.show_status_message(f"Template '{template_name}' moved to folder '{folder_name}'", "info")
                
                # Force refresh the gallery
                gallery.populate_gallery(force_refresh=True)
                return True
            else:
                print(f"[DEBUG] Gallery: Failed to move template '{template_name}' to folder '{folder_name}'")
                if hasattr(gallery.app, 'show_status_message'):
                    gallery.app.show_status_message(f"Failed to move template '{template_name}' to folder '{folder_name}'", "error")
                return False
        except Exception as e:
            import traceback
            print(f"[DEBUG] Gallery: Error moving template to folder: {e}")
            traceback.print_exc()
            return False 