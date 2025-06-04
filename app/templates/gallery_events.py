#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import QInputDialog, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QApplication, QLineEdit
from PyQt6.QtCore import Qt, QTimer
import os
from PyQt6.QtGui import QIcon, QFont, QPixmap
import time
import re

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

# Custom styled dialog for adding folders
class StyledFolderDialog(QDialog):
    """A custom styled dialog for adding folders"""
    
    def __init__(self, parent, title, label_text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        
        # Set dialog styling to match app theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Add label (not in an outlined container)
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                background-color: transparent;
                border: none;
                padding: 0px 0px 5px 0px;
                font-size: 14px;
            }}
        """)
        layout.addWidget(label)
        
        # Add text field
        self.text_field = QLineEdit()
        self.text_field.setMinimumWidth(250)
        self.text_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
                min-height: 25px;
            }}
            QLineEdit:focus {{
                border: 1px solid {colors['accent']};
            }}
        """)
        layout.addWidget(self.text_field)
        
        # Add spacing before buttons
        layout.addSpacing(15)
        
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
    
    def getText(self):
        """Get the entered text"""
        return self.text_field.text()
    
    @staticmethod
    def get_folder_name(parent, title, label_text):
        """Static method to create and show the dialog and return the result"""
        dialog = StyledFolderDialog(parent, title, label_text)
        dialog.text_field.setFocus() # Set focus to the text field
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return dialog.getText(), True
        else:
            return "", False

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
    def on_template_select(gallery, template_data, clear_multi=True):
        """Handle template selection"""
        template_name = template_data.get('name', 'Unknown') if isinstance(template_data, dict) else 'Unknown'
        print(f"\n=== TEMPLATE SELECTION EVENT (GalleryEvents for '{template_name}') ===")

        if not hasattr(gallery, 'selection_manager'):
            print("[ERROR] GalleryEvents.on_template_select: gallery has no selection_manager!")
            return

        # If this template is already the primary selection and no multi-selection exists,
        # there's likely no state change needed from this event alone.
        # The selection manager handles emitting signals even if data is same, if requested.
        # if gallery.selection_manager.is_selected(template_data) and not gallery.selection_manager.multi_selected_templates:
        #     print(f"🔍 GALLERY EVENTS: Template '{template_name}' already primary selection, no multi-select. No change.")
        #     # Ensure UI is consistent; selection_manager.set_primary_selection will emit if needed.
        #     gallery.selection_manager.set_primary_selection(template_data, emit_signal=True)
        #     return

        # When a template is selected (e.g., by a single click, not part of multi-select gesture):
        # 1. It becomes the primary selection.
        # 2. Any existing multi-selection should be cleared unless clear_multi=False
        if clear_multi:
            gallery.selection_manager.clear_selection(emit_signal=False)  # Clear selections, don't signal yet
            gallery.selection_manager.set_primary_selection(template_data, emit_signal=True)  # Set primary with signal
        else:
            # For multi-selection (ctrl/cmd+click or shift+click)
            # Set primary but don't clear existing multi-selection
            gallery.selection_manager.set_primary_selection(template_data, emit_signal=True, clear_multi=False)

        # The old logic for updating app.template_file_path should ideally move
        # to be a subscriber of selection_manager.selection_changed, or be handled
        # within set_primary_selection if it's a core part of that action.
        # For now, keep it here if gallery_widget._handle_selection_manager_update doesn't do it.
        # This is duplicated in selection_manager.set_primary_selection, needs cleanup.
        if hasattr(gallery, 'app') and gallery.app and isinstance(template_data, dict):
            template_path = template_data.get('path')
            if not template_path and hasattr(gallery.app, 'template_manager'): # Try to get from manager
                manager_template_info = gallery.app.template_manager.get_template_by_name(template_name)
                if manager_template_info:
                    template_path = manager_template_info.get('path')
            
            if template_path:
                gallery.app.template_file_path = template_path
                print(f"✓ GALLERY EVENTS: Updated app.template_file_path to '{template_path}'")
            else:
                print("❌ GALLERY EVENTS: Could not determine template path for app.template_file_path")

        # The gallery.template_selected.emit(template_data) is now handled by
        # gallery_widget._handle_selection_manager_update when it receives the signal.

        print(f"🔍 GALLERY EVENTS: Selection set to '{template_name}' via manager. UI update will follow signal.")
        print("=== END TEMPLATE SELECTION EVENT (GalleryEvents) ===\n")
    
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
        
        # Update folder label
        if hasattr(gallery, 'folder_label'):
            gallery.folder_label.setText(f"Folder: {folder_name}")
            gallery.folder_label.show()
            
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
        
        # Hide folder label
        if hasattr(gallery, 'folder_label'):
            gallery.folder_label.setText("")
            gallery.folder_label.hide()
            
        # Hide back button
        if hasattr(gallery, 'back_button'):
            gallery.back_button.setVisible(False)
            
        # Hide folder notice label
        if hasattr(gallery, 'folder_notice_label'):
            gallery.folder_notice_label.setText("")
            gallery.folder_notice_label.setVisible(False)
            
        print(f"🔍 LISTENER: Successfully returned to root view from folder '{current_folder}'")
    
    @staticmethod
    def on_add_folder(gallery):
        """Handle adding a new folder"""
        print(f"🔍 LISTENER: Adding a new folder")
        
        # Use custom styled dialog instead of QInputDialog
        folder_name, ok = StyledFolderDialog.get_folder_name(gallery, "Add Folder", "Enter folder name:")
        
        if ok and folder_name:
            # Validate the folder name (allow letters, numbers, underscores, hyphens, and spaces)
            if not re.match(r'^[a-zA-Z0-9_\- ]+$', folder_name):
                QMessageBox.warning(gallery, "Invalid Folder Name", 
                    "Folder name can only contain letters, numbers, underscores, hyphens, and spaces.")
                return
            
            # Check if template_manager is available
            if hasattr(gallery, 'template_manager') and gallery.template_manager:
                if gallery.template_manager.folder_exists(folder_name):
                    QMessageBox.warning(gallery, "Folder Exists", 
                        f"A folder named '{folder_name}' already exists.")
                    return
                
                # Create the folder using template_manager
                success = gallery.template_manager.add_folder(folder_name)
                if success:
                    print(f"🔍 LISTENER: Successfully created folder '{folder_name}'")
                    
                    # Update the UI to reflect the change
                    gallery.populate_gallery(force_refresh=True)
                else:
                    QMessageBox.warning(gallery, "Folder Creation Failed", 
                        f"Could not create folder '{folder_name}'.")
            else:
                QMessageBox.warning(gallery, "Folder Creation Failed", 
                    "Template manager is not available.")
                print("❌ LISTENER: Template manager is not available")
    
    @staticmethod
    def on_rename_folder(gallery):
        """Handle rename folder button click"""
        print(f"🔍 LISTENER: Rename folder requested")
        
        # Check if a folder is selected
        if not hasattr(gallery, 'selected_folder') or not gallery.selected_folder:
            QMessageBox.warning(gallery, "No Folder Selected", "Please select a folder to rename.")
            return
            
        # Get the selected folder
        folder_name = gallery.selected_folder
        
        # Trigger the rename process
        GalleryEvents.on_rename_folder_requested(gallery, folder_name)
                
    @staticmethod
    def on_rename_folder_requested(gallery, folder_name):
        """Handle rename folder request for the specified folder"""
        print(f"🔍 LISTENER: Rename folder requested for '{folder_name}'")
        
        # Use QInputDialog to get the new folder name
        new_name, ok = QInputDialog.getText(gallery, "Rename Folder", 
                                           "Enter new folder name:", 
                                           text=folder_name)
        
        if ok and new_name:
            # Validate the folder name (allow letters, numbers, underscores, hyphens, and spaces)
            if not re.match(r'^[a-zA-Z0-9_\- ]+$', new_name):
                QMessageBox.warning(gallery, "Invalid Folder Name", 
                    "Folder name can only contain letters, numbers, underscores, hyphens, and spaces.")
                return
                
            # Skip if name is the same
            if new_name == folder_name:
                return
                
            # Check if template manager is available
            if hasattr(gallery, 'template_manager') and gallery.template_manager:
                if gallery.template_manager.folder_exists(new_name):
                    QMessageBox.warning(gallery, "Folder Exists", 
                        f"A folder named '{new_name}' already exists.")
                    return
                    
                # Proceed with folder rename
                GalleryEvents.on_rename_folder_done(gallery, folder_name, new_name)
            else:
                QMessageBox.warning(gallery, "Folder Rename Failed", 
                    "Template manager is not available.")
                print("❌ LISTENER: Template manager is not available")
                
    @staticmethod
    def on_rename_folder_done(gallery, old_name, new_name):
        """Handle folder rename operation"""
        print(f"🔍 LISTENER: Renaming folder from '{old_name}' to '{new_name}'")
        
        # Rename the folder using the template manager
        if hasattr(gallery, 'template_manager') and gallery.template_manager:
            success = gallery.template_manager.rename_folder(old_name, new_name)
            
            if success:
                print(f"🔍 LISTENER: Successfully renamed folder from '{old_name}' to '{new_name}'")
                
                # Update the gallery to reflect changes
                gallery.populate_gallery(force_refresh=True)
                
                # Update selected folder if needed
                if gallery.selected_folder == old_name:
                    gallery.selected_folder = new_name
            else:
                QMessageBox.warning(gallery, "Folder Rename Failed", 
                    f"Could not rename folder from '{old_name}' to '{new_name}'.")
        else:
            QMessageBox.warning(gallery, "Folder Rename Failed", 
                "Template manager is not available.")
            print("❌ LISTENER: Template manager is not available")
            
    @staticmethod
    def on_delete_folder(gallery, folder_name):
        """Handle deletion of a folder."""
        if not hasattr(gallery, 'template_manager') or not gallery.template_manager:
            QMessageBox.warning(gallery, "Operation Failed", "Template manager is not available")
            return
        
        # Don't allow deleting default folders
        if folder_name in ["General", "Development", "Business"]:
            QMessageBox.warning(gallery, "Error", f"'{folder_name}' is a default folder and cannot be deleted.")
            return
        
        # Delete the folder without confirmation dialog
        success = gallery.template_manager.delete_folder(folder_name)
        
        if success:
            # Save folder name for message
            folder_name = gallery.selected_folder
            # Update the UI (folder is gone)
            gallery.populate_gallery(force_refresh=True)
            # Reset selection
            gallery.selected_folder = None
            # Notify user
            if hasattr(gallery, 'app') and hasattr(gallery.app, 'show_status_message'):
                gallery.app.show_status_message(f"Folder '{folder_name}' deleted", "info")
        else:
            QMessageBox.warning(gallery, "Delete Failed", f"Failed to delete folder '{folder_name}'.")

    @staticmethod
    def on_move_template_to_folder(gallery, template_names, target_folder=None):
        """Move specified templates to the target folder."""
        if not gallery.template_manager:
            print("ERROR: Template manager not available.")
            return

        if not isinstance(template_names, list):
            template_names = [template_names] # Ensure it's a list

        moved_count = 0
        for template_name in template_names:
            if not template_name: # Skip if name is empty or None
                continue

            # Find current folder of the template
            current_template_folder = None
            for folder, templates_in_folder in gallery.template_manager.folders.items():
                if template_name in templates_in_folder:
                    current_template_folder = folder
                    break
            
            print(f"Moving '{template_name}'. Current folder: {current_template_folder}, Target folder: {target_folder}")

            # Case 1: Moving to root (target_folder is None or empty string)
            if target_folder is None or target_folder == "":
                if current_template_folder:
                    print(f"  Action: Moving '{template_name}' from '{current_template_folder}' to root.")
                    # Pass None to signify moving to root (no specific folder)
                    gallery.template_manager.move_template_to_folder(template_name, None)
                    moved_count += 1
                else:
                    print(f"  Info: '{template_name}' is already in root. No action needed.")
            # Case 2: Moving to a specific folder
            else:
                if current_template_folder == target_folder:
                    print(f"  Info: '{template_name}' is already in target folder '{target_folder}'. No action needed.")
                    continue # Skip if already in the target folder
                
                # Move directly to the new folder
                print(f"  Action: Moving '{template_name}' from '{current_template_folder}' to '{target_folder}'.")
                gallery.template_manager.move_template_to_folder(template_name, target_folder)
                moved_count += 1

        if moved_count > 0:
            gallery.template_manager.save_folders() # Save changes to folders.json
            gallery.populate_gallery(force_refresh=True)
            current_view_name = target_folder if target_folder else "root view"
            if hasattr(gallery, 'app') and hasattr(gallery.app, 'show_status_message'):
                gallery.app.show_status_message(f"Moved {moved_count} template(s) to {current_view_name}", "success")
            print(f"Successfully moved {moved_count} templates.")
        else:
            if hasattr(gallery, 'app') and hasattr(gallery.app, 'show_status_message'):
                gallery.app.show_status_message(f"No templates needed to be moved.", "info")
            print("No templates were moved (either already in target or no valid names provided).")
    
    @staticmethod
    def on_add_template(gallery):
        """Handle add template button click"""
        print(f"🔍 LISTENER: Add template button clicked")
        # Use the enhanced structure editor for adding new templates
        try:
            from app.ui.structure_editor_functions import show_enhanced_structure_editor
            
            print(f"🔍 EDIT TEMPLATE: Starting template edit for ''")
            print(f"🔍 EDIT TEMPLATE: Template is_new=True, name='', structure_name='Template_'")
            
            # Expect 7 return values now
            result, updated_structure, updated_structure_name, _, updated_template_name, saved_category, saved_description = show_enhanced_structure_editor(
                parent=gallery, # Pass the main window as parent
                is_new=True,
                template_manager=gallery.app.template_manager # Pass template manager instance
            )

            if result and updated_template_name:
                print(f"🔍 LISTENER: Saving new template '{updated_template_name}' with category '{saved_category}'")
                
                # Ensure structure name has Template_ prefix
                if not updated_structure_name.startswith("Template_"):
                    updated_structure_name = f"Template_{updated_template_name}"
                
                # --- Save structure file --- (This might be redundant if save_template handles it)
                # structure_save_success = gallery.app.template_manager.save_custom_structure(
                #     name=updated_structure_name,
                #     structure=updated_structure,
                #     category=saved_category,
                #     description=saved_description
                # )
                # if not structure_save_success:
                #     print(f"❌ LISTENER: Failed to save structure for new template '{updated_template_name}'")
                    # Optionally show an error message
                    # QMessageBox.warning(self.parent_widget, "Save Error", ...)
                    # return # Don't proceed if structure save fails
                
                # --- Save main template file ---    
                # Now save the main template file, linking to the saved structure
                print(f"🔷 GALLERY LISTENER: Saving main template file: Name='{updated_template_name}', Category='{saved_category}'")
                
                # Construct the template data dictionary
                template_data = {
                    "name": updated_template_name,
                    "structure_name": updated_structure_name, # Link to the saved structure
                    "structure": updated_structure,
                    "category": saved_category,
                    "description": saved_description,
                    "type": "Standard", # Assuming default type, adjust if needed
                    # created/modified timestamps are likely handled within save_template
                }
                
                # Call save_template with the individual parameters instead of the dictionary
                save_success, save_message = gallery.app.template_manager.save_template(
                    template_name=updated_template_name,
                    structure=updated_structure,
                    category=saved_category,
                    description=saved_description,
                    template_type="Standard"
                )

                if save_success:
                    print(f"🔍 LISTENER: Successfully created template '{updated_template_name}'")
                    
                    # If we're in a folder, add the new template to the current folder
                    if hasattr(gallery, 'current_folder') and gallery.current_folder:
                        print(f"[DEBUG] Adding new template '{updated_template_name}' to current folder '{gallery.current_folder}'")
                        
                        template_manager = gallery.app.template_manager
                        # Use the move_template_to_folder method which removes it from any other folders first
                        if hasattr(template_manager, 'move_template_to_folder'):
                            success = template_manager.move_template_to_folder(updated_template_name, gallery.current_folder)
                            if success:
                                print(f"[DEBUG] Successfully added template '{updated_template_name}' to folder '{gallery.current_folder}'")
                            else:
                                print(f"[DEBUG] Failed to add template '{updated_template_name}' to folder '{gallery.current_folder}'")
                        # Fallback to add_to_folder if move_template_to_folder isn't available
                        elif hasattr(template_manager, 'add_to_folder'):
                            success = template_manager.add_to_folder(gallery.current_folder, updated_template_name)
                            if success:
                                print(f"[DEBUG] Successfully added template '{updated_template_name}' to folder '{gallery.current_folder}'")
                            else:
                                print(f"[DEBUG] Failed to add template '{updated_template_name}' to folder '{gallery.current_folder}'")
                    
                    # Refresh the gallery view
                    if gallery and hasattr(gallery, 'populate_gallery'):
                        print("🔍 LISTENER: Forcing gallery refresh to show new template")
                        gallery.populate_gallery(force_refresh=True)
                        # Select the newly created template
                        QTimer.singleShot(100, lambda name=updated_template_name: gallery.select_template(name))
                    else:
                        print("🔍 LISTENER: Gallery object not available for refresh")
                else:
                    print(f"❌ LISTENER: Failed to save new template '{updated_template_name}'")
                    error_message = save_message if save_message else "Failed to save template. Please check that the template has a valid name and structure."
                    QMessageBox.warning(gallery, "Save Error", f"Could not save the new template file for {updated_template_name}. Error: {error_message}")
            else:
                print("🔍 LISTENER: Add template cancelled or failed")
        except Exception as e:
            print(f"Error adding template: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(gallery, "Error", f"An error occurred while adding the template: {e}")

    @staticmethod
    def on_edit_template(gallery, template_name=None):
        """Handle edit template button click in template gallery"""
        print(f"🔹 GALLERY EVENTS: Edit template requested")
        
        # Ensure gallery has required components
        if not hasattr(gallery, 'app'):
            print(f"❌ GALLERY EVENTS: Gallery missing app reference")
            return
        
        if not hasattr(gallery.app, 'template_manager'):
            print(f"❌ GALLERY EVENTS: App missing template manager")
            return
        
        # Use either the provided template name or get it from the selected template
        if template_name is None and hasattr(gallery, 'selected_template') and gallery.selected_template:
            template_name = gallery.selected_template.get('name', '')
        
        # Make sure we have a template name
        if not template_name:
            print(f"⚠️ GALLERY EVENTS: No template selected for editing")
            return
        
        print(f"🔹 GALLERY EVENTS: Editing template: '{template_name}'")
        
        # Determine structure name based on template name
        structure_name = f"Template_{template_name}"
        
        # Try to get the structure from template manager
        structure = None
        if hasattr(gallery.app.template_manager, 'get_structure'):
            # Try with the template name with Template_ prefix
            structure = gallery.app.template_manager.get_structure(structure_name)
            if structure:
                print(f"🔹 GALLERY EVENTS: Found structure using structure_name: '{structure_name}'")
            else:
                # Try with just the template name
                structure = gallery.app.template_manager.get_structure(template_name)
                if structure:
                    print(f"🔹 GALLERY EVENTS: Found structure using template name directly: '{template_name}'")
                    structure_name = template_name
                else:
                    print(f"⚠️ GALLERY EVENTS: No structure found for template, using empty structure")
                    structure = []
        else:
            print(f"⚠️ GALLERY EVENTS: Template manager doesn't support get_structure, using empty structure")
            structure = []
            
        # Use the enhanced structure editor directly
        from app.ui.structure_editor_functions import show_enhanced_structure_editor
        
        print(f"🔍 EDIT TEMPLATE: Starting template edit for '{template_name}'")
        print(f"🔍 EDIT TEMPLATE: Template is_new=False, name='{template_name}', structure_name='{structure_name}'")
        
        # Open the structure editor
        result, updated_structure, updated_structure_name, original_template_name, updated_template_name, category, description = show_enhanced_structure_editor(
            parent=gallery,
            structure_name=structure_name,
            structure=structure,
            is_new=False,
            template_name=template_name,
            focus_name_field=False,
            template_manager=gallery.app.template_manager,
            callback=lambda data: GalleryEvents._save_template_and_structure(gallery, data)
        )
        
        if result:
            print(f"🔍 LISTENER: Successfully edited template '{updated_template_name}'")
            
            # Check if this was a rename operation
            if template_name != updated_template_name:
                print(f"🔍 LISTENER: Template was renamed from '{template_name}' to '{updated_template_name}'")
                
            # Force refresh gallery to show the updated template
            print(f"🔍 LISTENER: Forcing gallery refresh to show updated template")
            gallery.populate_gallery(force_refresh=True)
            
            # Select the updated template
            if hasattr(gallery, 'select_template'):
                print(f"🔍 LISTENER: Selecting updated template: {updated_template_name}")
                gallery.select_template(updated_template_name)
        else:
            print(f"🔍 LISTENER: Template editor was cancelled or failed")
    
    @staticmethod
    def on_delete_template(gallery):
        """Delete the selected template(s) identified by the gallery's selection_manager."""
        if not hasattr(gallery, 'selection_manager') or not gallery.selection_manager:
            print("[ERROR] GalleryEvents.on_delete_template: gallery has no selection_manager!")
            QMessageBox.warning(gallery, "Error", "Selection manager not available.")
            return

        template_manager = gallery.template_manager
        if not template_manager:
            QMessageBox.warning(gallery, "Error", "Template manager not available.")
            return

        templates_to_delete_objs = []
        template_display_names = []

        multi_selected = gallery.selection_manager.multi_selected_templates
        primary_selected = gallery.selection_manager.selected_template

        if multi_selected: 
            templates_to_delete_objs.extend(list(multi_selected)) 
        elif primary_selected:
            templates_to_delete_objs.append(primary_selected)
        
        if not templates_to_delete_objs:
            # This case should ideally be caught by key_press_event before calling this
            # or if called from somewhere else (e.g. context menu) that also checks selection.
            print(f"[DEBUG] GalleryEvents.on_delete_template: No templates identified for deletion by selection_manager.")
            # QMessageBox.information(gallery, "No Template Selected", "No template selected to delete.") # Consider if this is needed or if caller handles
            return

        for t_obj in templates_to_delete_objs:
            if isinstance(t_obj, dict) and 'name' in t_obj:
                template_display_names.append(t_obj['name'])
            # Add handling for other types if necessary, though selection_manager should store dicts

        if not template_display_names: # Should not happen if templates_to_delete_objs had items
            print(f"[WARNING] GalleryEvents.on_delete_template: Could not extract names from selected template objects.")
            return

        # --- CONFIRMATION DIALOG ---
        count = len(template_display_names)
        item_text = "template" if count == 1 else "templates"
        message = f"Are you sure you want to delete the selected {count} {item_text}?\n\n"
        message += "\n".join(f"- {name}" for name in template_display_names)
        
        # Ensure QMessageBox is imported if not at the top of the file
        # from PyQt6.QtWidgets import QMessageBox 
        reply = QMessageBox.question(gallery, "Confirm Template Deletion", message, 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            print(f"[DEBUG] Gallery: Deletion of {count} template(s) cancelled by user.")
            return
        # --- END CONFIRMATION DIALOG ---

        actually_deleted_names = []
        errors = []

        for template_obj_to_delete in templates_to_delete_objs:
            name_to_delete = None
            if isinstance(template_obj_to_delete, dict):
                name_to_delete = template_obj_to_delete.get('name')
            # elif isinstance(template_obj_to_delete, str): # Unlikely with current selection_manager
            #     name_to_delete = template_obj_to_delete
            
            if not name_to_delete:
                errors.append("An item in the selection could not be identified by name for deletion.")
                print(f"[WARNING] Could not get name for template object: {template_obj_to_delete}")
                continue

            try:
                print(f"[DEBUG] Gallery: Attempting to delete template '{name_to_delete}' via template_manager")
                success = template_manager.delete_template(name_to_delete)
                if success:
                    print(f"[DEBUG] Gallery: Successfully deleted template '{name_to_delete}' via template_manager.")
                    actually_deleted_names.append(name_to_delete)
                else:
                    print(f"[WARNING] Gallery: template_manager.delete_template reported failure for '{name_to_delete}'.")
                    errors.append(f"Could not delete '{name_to_delete}'.") # template_manager should log specifics
            except Exception as e:
                print(f"[ERROR] Gallery: Exception during deletion of '{name_to_delete}': {e}")
                # import traceback # Already imported in key_press_event, consider if needed here
                # traceback.print_exc()
                errors.append(f"Error deleting '{name_to_delete}': {e}")

        if actually_deleted_names:
            # Important: Clear selection in the manager *before* repopulating gallery.
            # Repopulating might auto-select something, which would be based on old selection state if not cleared.
            gallery.selection_manager.clear_selection(emit_signal=False) # Don't emit signal yet
            
            gallery.populate_gallery(force_refresh=True) 
            # populate_gallery reloads data and rebuilds UI. If it causes new auto-selection,
            # selection_manager will emit its selection_changed signal then.

            if hasattr(gallery.app, 'show_status_message'):
                gallery.app.show_status_message(f"Deleted {len(actually_deleted_names)} template(s): {', '.join(actually_deleted_names)}.", "success", duration=5000)
        
        if errors:
            # Ensure QMessageBox is imported
            # from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(gallery, "Deletion Errors", "Some templates could not be deleted:\n\n" + "\n".join(errors))

        # Ensure overall UI consistency after operations
        if hasattr(gallery, '_update_selection_ui'):
            gallery._update_selection_ui() # This should be triggered by selection_manager.selection_changed
        if hasattr(gallery, '_update_button_state'):
            gallery._update_button_state()
    
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
    def on_recache_all_templates(gallery):
        """Handle recaching all templates"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Check if template manager has cache_manager
        if (not hasattr(gallery.app, 'template_manager') or 
            not hasattr(gallery.app.template_manager, 'cache_manager')):
            QMessageBox.warning(
                gallery, 
                "Cache Manager Not Available", 
                "The cache manager is not available. Cannot recache templates.",
                QMessageBox.Ok
            )
            return
        
        # Show confirmation dialog
        result = QMessageBox.question(
            gallery, 
            "Recache All Templates", 
            "This will recache all templates by finding and caching their original files again.\n\n"
            "This process might take some time depending on the number of templates and files. "
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Show progress dialog
            from app.templates.cache_manager import RecacheProgressDialog
            
            dialog = RecacheProgressDialog(
                gallery.app.template_manager.cache_manager,
                None,  # None means recache all templates
                gallery
            )
            dialog.exec()
    
    @staticmethod
    def on_clear_all_caches(gallery):
        """Handle clearing all template caches"""
        # Check if template manager has safe_clear_all_caches method
        if (not hasattr(gallery.app, 'template_manager') or 
            not hasattr(gallery.app.template_manager, 'safe_clear_all_caches')):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                gallery, 
                "Cache Manager Not Available", 
                "The safe cache manager is not available. Cannot safely clear all caches.",
                QMessageBox.Ok
            )
            return
        
        # Use the safe_clear_all_caches method
        success = gallery.app.template_manager.safe_clear_all_caches()
        
        if success:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                gallery, 
                "Caches Cleared", 
                "All template caches have been cleared.",
                QMessageBox.Ok
            )
    
    @staticmethod
    def on_check_missing_originals(gallery):
        """Handle checking for templates with missing original files"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Check if template manager has find_templates_with_missing_originals method
        if (not hasattr(gallery.app, 'template_manager') or 
            not hasattr(gallery.app.template_manager, 'find_templates_with_missing_originals')):
            QMessageBox.warning(
                gallery, 
                "Cache Manager Not Available", 
                "The cache manager is not available. Cannot check for missing originals.",
                QMessageBox.Ok
            )
            return
        
        # Show a progress message
        from PyQt6.QtWidgets import QApplication
        gallery.statusBar().showMessage("Checking for templates with missing original files...")
        QApplication.processEvents()
        
        # Find templates with missing originals
        templates_with_missing = gallery.app.template_manager.find_templates_with_missing_originals()
        
        # Clear status message
        gallery.statusBar().clearMessage()
        
        if not templates_with_missing:
            QMessageBox.information(
                gallery, 
                "Check Complete", 
                "No templates with missing original files were found.",
                QMessageBox.Ok
            )
            return
        
        # Show the MissingOriginalsDialog
        from app.templates.cache_manager import MissingOriginalsDialog
        
        dialog = MissingOriginalsDialog(
            gallery.app.template_manager.cache_manager,
            templates_with_missing,
            gallery
        )
        dialog.exec()
    
    @staticmethod
    def _save_template_and_structure(gallery, data):
        """Save template and associated structure"""
        try:
            print(f"🔍 GALLERY LISTENER: Attempting to save template '{data['name']}' and its structure")
            
            # Save the structure first
            # structure_save_success = gallery.app.template_manager.save_custom_structure(
            #     name=data.get('structure_name', f"Template_{data['name'].replace(' ', '_')}"),
            #     structure=data.get('structure', {}),
            #     category=data.get('category', "General"),
            #     description=data.get('description', "")
            # )
            # if not structure_save_success:
            #     print(f"❌ GALLERY LISTENER: Failed to save structure for template '{data['name']}'")
            #     return False
            
            # Save the main template file with individual parameters
            save_success, save_message = gallery.app.template_manager.save_template(
                template_name=data['name'],
                structure=data.get('structure', []),
                category=data.get('category', "General"),
                description=data.get('description', ""),
                template_type=data.get('type', "Standard"),
                original_name=data.get('original_name')  # Pass the original_name for rename operations
            )

            if save_success:
                # Refresh gallery to show changes
                if hasattr(gallery, 'refresh_gallery'):
                    gallery.refresh_gallery()
                else:
                    # Fallback to populate_gallery if refresh_gallery doesn't exist
                    gallery.populate_gallery(force_refresh=True)
                print(f"✅ GALLERY LISTENER: Successfully saved template '{data['name']}'")
                return True
            else:
                print(f"❌ GALLERY LISTENER: Failed to save template '{data['name']}'. Error: {save_message}")
                return False
        except Exception as e:
            print(f"Error saving template and structure: {e}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def on_structure_edit(gallery, template_name):
        """Handle editing structure for template"""
        print(f"🔍 LISTENER: Structure edit requested for '{template_name}'")
        if hasattr(gallery, '_on_structure_editor'):
            gallery._on_structure_editor(template_name)
        else:
            print("❌ LISTENER: No _on_structure_editor method found in gallery")
            QMessageBox.warning(gallery, "Not Implemented", "Structure editing is not implemented yet.")
    
    @staticmethod
    def on_export_template(gallery, template_name):
        """Handle exporting a template"""
        print(f"🔍 LISTENER: Export requested for '{template_name}'")
        
        if not template_name or not hasattr(gallery, 'template_manager'):
            QMessageBox.warning(gallery, "Error", "Cannot export template: No template selected or template manager not available.")
            return
            
        # Get template data
        template_data = gallery.template_manager.get_template_by_name(template_name)
        if not template_data:
            QMessageBox.warning(gallery, "Error", f"Could not find template '{template_name}'.")
            return
            
        # Export template
        try:
            # Show dialog to ask if files should be included
            include_files = QMessageBox.question(
                gallery,
                "Export Template",
                f"Would you like to include files with this template?\n\n"
                f"Including files will allow others to import the template with all its attached assets.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            ) == QMessageBox.Yes
            
            # Use the export_template function from import_export_manager directly
            from app.core.import_export_manager import export_template
            export_template(gallery.app, template_name, include_files)
        except Exception as e:
            QMessageBox.critical(gallery, "Error", f"Error exporting template: {str(e)}")
    
    @staticmethod
    def on_duplicate_template(gallery, template_name):
        """Handle duplicating a template without a dialog, automatically generating a name."""
        print(f"🔍 LISTENER: Duplicate requested for '{template_name}' (auto-name, context menu style name generation)")

        if not template_name or not hasattr(gallery, 'template_manager') or not hasattr(gallery.template_manager, 'template_io'):
            QMessageBox.warning(gallery, "Error", "Cannot duplicate template: Template manager or TemplateIO not available.")
            return

        template_manager = gallery.template_manager

        # Align naming with Cmd+D shortcut: "copy", "copy 2", etc.
        base_new_name = f"{template_name} copy" # Changed from (Copy)
        new_name = base_new_name
        counter = 1 # Start with base_new_name (suffixless or 'copy'), counter for 'copy 2', 'copy 3'
        
        # Check if "Template Name copy" exists
        if template_manager.template_io.get_template(new_name):
            # If "Template Name copy" exists, start with "Template Name copy 2"
            counter = 2 
            new_name = f"{template_name} copy {counter}"
            # Loop to find next available "Template Name copy N"
            while template_manager.template_io.get_template(new_name):
                counter += 1
                new_name = f"{template_name} copy {counter}"
        # If "Template Name copy" does not exist, new_name (base_new_name) is already correctly set.
        
        print(f"🔍 LISTENER: Generated unique name for duplicate: '{new_name}'")
            
        # Duplicate template
        try:
            if hasattr(template_manager, 'duplicate_template'):
                success = template_manager.duplicate_template(template_name, new_name)
                if success:
                    # If duplicating within a folder, ensure the new template is added to this folder.
                    if gallery.current_folder and hasattr(template_manager, 'move_template_to_folder'):
                        print(f"[DEBUG] Context Duplicate: Moving new template '{new_name}' to current folder '{gallery.current_folder}'")
                        # Use move_template_to_folder to ensure it's correctly placed and removed from others if necessary
                        # (though for a brand new template, it's effectively an add).
                        moved_to_folder = template_manager.move_template_to_folder(new_name, gallery.current_folder)
                        if not moved_to_folder:
                            print(f"[WARNING] Context Duplicate: Failed to move '{new_name}' to folder '{gallery.current_folder}'")

                    if hasattr(gallery.app, 'show_status_message'):
                        gallery.app.show_status_message(f"Template '{template_name}' duplicated as '{new_name}'.", "success")
                    else:
                        QMessageBox.information(gallery, "Success", f"Template '{template_name}' duplicated as '{new_name}'.")
                    gallery.populate_gallery(force_refresh=True)
                    QTimer.singleShot(100, lambda: gallery.select_template(new_name))
                else:
                    if hasattr(gallery.app, 'show_status_message'):
                        gallery.app.show_status_message(f"Failed to duplicate template '{template_name}'. Error during duplication process.", "error")
                    else:
                        QMessageBox.warning(gallery, "Error", f"Failed to duplicate template '{template_name}'. Error during duplication process.")
            else:
                QMessageBox.warning(gallery, "Not Implemented", "Duplicate functionality is not implemented in the template manager.")
        except Exception as e:
            if hasattr(gallery.app, 'show_status_message'):
                gallery.app.show_status_message(f"Error duplicating template: {str(e)}", "error")
            else:
                QMessageBox.critical(gallery, "Error", f"Error duplicating template: {str(e)}")
            print(f"[ERROR] Exception in on_duplicate_template: {e}")
            import traceback
            traceback.print_exc()
    
    @staticmethod
    def on_rename_template(gallery, template_name):
        """Handle template rename requests"""
        print(f"🔍 LISTENER: Rename requested for '{template_name}'")
        
        if not template_name or not hasattr(gallery, 'template_manager'):
            QMessageBox.warning(gallery, "Error", "Cannot rename template: No template selected or template manager not available.")
            return
            
        # Ask for new name
        new_name, ok = QInputDialog.getText(
            gallery,
            "Rename Template",
            "Enter new name for the template:",
            text=template_name
        )
        
        if not ok or not new_name or new_name == template_name:
            return  # User cancelled or no change
            
        # Rename template
        try:
            if hasattr(gallery.template_manager, 'rename_template'):
                success = gallery.template_manager.rename_template(template_name, new_name)
                if success:
                    QMessageBox.information(gallery, "Success", f"Template '{template_name}' renamed to '{new_name}'.")
                    gallery.populate_gallery(force_refresh=True)
                    gallery.select_template(new_name) # Select the renamed template
                else:
                    QMessageBox.warning(gallery, "Error", f"Failed to rename template '{template_name}'.")
            else:
                QMessageBox.warning(gallery, "Not Implemented", "Rename functionality is not implemented yet.")
        except Exception as e:
            QMessageBox.critical(gallery, "Error", f"Error renaming template: {str(e)}")

    @staticmethod
    def mouse_press_event(gallery, event):
        """Handle mouse press events in the template gallery area for blank space clicks."""
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return False

        modifiers = QApplication.keyboardModifiers()
        is_modifier_active = bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier | Qt.KeyboardModifier.ShiftModifier))

        widget_at_pos = gallery.childAt(event.pos())
        is_card_click = False
        current_widget = widget_at_pos
        while current_widget and current_widget != gallery:
            template_cards_exist = hasattr(gallery, 'template_cards') and gallery.template_cards
            folder_cards_exist = hasattr(gallery, 'folder_cards') and gallery.folder_cards
            if (template_cards_exist and current_widget in gallery.template_cards) or \
               (folder_cards_exist and current_widget in gallery.folder_cards):
                is_card_click = True
                break
            parent = current_widget.parent()
            if parent == current_widget: break
            current_widget = parent

        if is_card_click or is_modifier_active:
            event.ignore()
            return False

        # If we reach here, it's a simple left-click on a blank area without modifiers.
        # Use the selection manager to clear selections.
        if hasattr(gallery, 'selection_manager'):
            # Check if there was any selection to clear to avoid redundant signals/updates
            current_primary = gallery.selection_manager.selected_template
            current_multi = gallery.selection_manager.multi_selected_templates
            if current_primary or current_multi:
                gallery.selection_manager.clear_selection(emit_signal=True) # This will trigger UI update via signal
                # print(f"🔍 GALLERY EVENTS (Mouse Press): Cleared all selections via manager.")
                event.accept()
                return True
            else:
                # No selection to clear, event not really handled in a way that changes state
                event.ignore()
                return False
        else:
            # Fallback or error if no selection_manager - should not happen in normal operation
            print("[ERROR] GalleryEvents.mouse_press_event: gallery has no selection_manager!")
            event.ignore()
            return False

    @staticmethod
    def key_press_event(gallery, event):
        """Handle key press events in the gallery"""
        from PyQt6.QtCore import Qt
        
        try:
            if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
                # Determine what is selected for deletion
                templates_to_delete_from_selection_manager = []
                if hasattr(gallery, 'selection_manager') and gallery.selection_manager:
                    multi_selected = gallery.selection_manager.multi_selected_templates
                    primary_selected = gallery.selection_manager.selected_template
                    if multi_selected:
                        templates_to_delete_from_selection_manager.extend(multi_selected)
                    elif primary_selected:
                        templates_to_delete_from_selection_manager.append(primary_selected)

                is_folder_view_active = hasattr(gallery, 'current_folder') and gallery.current_folder
                is_folder_card_selected = hasattr(gallery, 'selected_folder') and gallery.selected_folder

                # Priority 1: Template Deletion if templates are selected
                if templates_to_delete_from_selection_manager:
                    # If we are in a folder view, ensure the selected templates are indeed part of that folder
                    # This check might be redundant if selection manager correctly reflects the current view context
                    # For now, we assume selection manager is the source of truth for what is selected.
                    print(f"[DEBUG] Delete/Backspace key pressed, {len(templates_to_delete_from_selection_manager)} template(s) identified by SelectionManager.")
                    GalleryEvents.on_delete_template(gallery) 
                    event.accept()
                    return True
                
                # Priority 2: Folder deletion if a folder card is selected AND no templates are selected
                # (The `gallery.selected_folder` attribute is typically set when a folder CARD is explicitly clicked and selected)
                elif is_folder_card_selected and not templates_to_delete_from_selection_manager:
                    print(f"[DEBUG] Delete/Backspace key pressed, folder card selected: {gallery.selected_folder}")
                    
                    if gallery.selected_folder in getattr(gallery.template_manager, 'DEFAULT_FOLDERS', ["General", "Development", "Business"]):
                        QMessageBox.warning(gallery, "Error", 
                            f"'{gallery.selected_folder}' is a default folder and cannot be deleted.")
                        event.accept()
                        return True
                    
                    reply = QMessageBox.question(gallery, "Confirm Folder Deletion",
                                                 f"Are you sure you want to delete the folder '{gallery.selected_folder}' and all its templates?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        event.accept()
                        return True

                    if hasattr(gallery, 'template_manager') and gallery.template_manager:
                        folder_name_to_delete = gallery.selected_folder 
                        success = gallery.template_manager.delete_folder(folder_name_to_delete)
                        
                        if success:
                            gallery.populate_gallery(force_refresh=True)
                            gallery.selected_folder = None 
                            if hasattr(gallery.app, 'show_status_message'):
                                gallery.app.show_status_message(f"Folder '{folder_name_to_delete}' deleted", "info")
                        else:
                            QMessageBox.warning(gallery, "Delete Failed", 
                                f"Failed to delete folder '{folder_name_to_delete}'.")
                        event.accept()
                        return True
                    else: 
                        event.accept()
                        return True
                else:
                    print(f"[DEBUG] Delete/Backspace key pressed, but no templates or folder card selected for deletion.")
                    pass 

        except Exception as e:
            print(f"[ERROR] Error handling key press event in GalleryEvents: {e}")
            import traceback
            traceback.print_exc()
        
        return False 