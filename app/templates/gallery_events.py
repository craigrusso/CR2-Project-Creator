#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QInputDialog, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTextEdit, QApplication
from PyQt5.QtCore import Qt, QTimer
import os
from PyQt5.QtGui import QIcon, QFont, QPixmap
import time

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
        print(f"\n=== TEMPLATE SELECTION DEBUG ===")
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
                            card.set_selected(False)
            
            # Ensure app-level selection is synchronized even for same template
            if hasattr(gallery, 'app'):
                gallery.app.selected_template = template
                print(f"🔍 LISTENER: Re-synchronized app-level selected template to '{template_name}'")
                
                # Also ensure template_file_path is set
                if isinstance(template, dict):
                    if 'path' in template:
                        gallery.app.template_file_path = template['path']
                        print(f"🔍 LISTENER: Re-synchronized app-level template file path to '{template['path']}'")
                    else:
                        # Try to get the path from the template manager
                        if hasattr(gallery.app, 'template_manager'):
                            template_info = gallery.app.template_manager.get_template_by_name(template.get('name', ''))
                            if template_info and 'path' in template_info:
                                gallery.app.template_file_path = template_info['path']
                                print(f"🔍 LISTENER: Re-synchronized app-level template file path from template manager")
                            else:
                                print("❌ LISTENER: Could not find template path in template manager")
            return
            
        # Set the selected template in gallery state
        gallery.selected_template = template
        print(f"🔍 LISTENER: Updated gallery selected template to '{template_name}'")
        
        # Also ensure it's set in the app object if available
        if hasattr(gallery, 'app'):
            gallery.app.selected_template = template
            print(f"🔍 LISTENER: Updated app-level selected template to '{template_name}'")
            
            # Also update template_file_path if available
            template_path = None
            
            # Method 1: Try to get path directly from template
            if isinstance(template, dict) and 'path' in template:
                template_path = template['path']
                print(f"✓ LISTENER: Found template path in template object: '{template_path}'")
            
            # Method 2: Try to get path from template manager
            if not template_path and hasattr(gallery.app, 'template_manager'):
                template_info = gallery.app.template_manager.get_template_by_name(template.get('name', ''))
                if template_info and 'path' in template_info:
                    template_path = template_info['path']
                    print(f"✓ LISTENER: Found template path in template manager: '{template_path}'")
                else:
                    print("❌ LISTENER: Could not find template path in template manager")
                    
                    # Method 3: Try to find the template file in the templates directory
                    if hasattr(gallery.app.template_manager, 'paths'):
                        templates_dir = gallery.app.template_manager.paths.get('templates_dir')
                        if templates_dir:
                            # Try different filename variations
                            template_name = template.get('name', '')
                            normalized_name = template_name.replace(" ", "_")
                            possible_paths = [
                                os.path.join(templates_dir, f"{template_name}.json"),
                                os.path.join(templates_dir, f"{normalized_name}.json"),
                                os.path.join(templates_dir, f"Template_{normalized_name}.json")
                            ]
                            
                            for path in possible_paths:
                                if os.path.exists(path):
                                    template_path = path
                                    print(f"✓ LISTENER: Found template path in templates directory: '{template_path}'")
                                    break
            
            # Update app's template_file_path if we found a path
            if template_path:
                gallery.app.template_file_path = template_path
                print(f"✓ LISTENER: Updated app-level template file path to '{template_path}'")
            else:
                print("❌ LISTENER: Could not find template path")
        
        gallery.selected_folder = None  # Reset folder selection
        print(f"🔍 LISTENER: Template selection set to '{template_name}'")
        
        # Update card styling for all cards - proper highlighting
        if hasattr(gallery, 'template_cards') and gallery.template_cards:
            card_count = len(gallery.template_cards)
            print(f"🔍 LISTENER: Updating styling for {card_count} template cards")
            
            for card in gallery.template_cards:
                if hasattr(card, 'template') and hasattr(card, 'set_selected'):
                    # Highlight only the currently selected template
                    is_selected = (card.template == template)
                    card.set_selected(is_selected)
                    if is_selected:
                        print(f"🔍 LISTENER: Setting {card.template_name()} selection state to TRUE")
                    else:
                        print(f"🔍 LISTENER: Setting {card.template_name()} selection state to FALSE")
        
        # Emit template selected event if using PyQt
        if hasattr(gallery, 'template_selected'):
            gallery.template_selected.emit(template)
            
        print("=== END TEMPLATE SELECTION DEBUG ===\n")
    
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
                structure_save_success = gallery.app.template_manager.save_custom_structure(
                    name=updated_structure_name,
                    structure=updated_structure,
                    category=saved_category,
                    description=saved_description
                )
                if not structure_save_success:
                    print(f"❌ LISTENER: Failed to save structure for new template '{updated_template_name}'")
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
                
                # Call save_template with the dictionary
                save_success = gallery.app.template_manager.save_template(template_data)

                if save_success:
                    print(f"🔍 LISTENER: Successfully created template '{updated_template_name}'")
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
                    QMessageBox.warning(gallery, "Save Error", f"Could not save the new template file for {updated_template_name}. Error: {save_message}")
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
            
            try:
                # Check that we're calling the right method with the right parameters
                if not hasattr(template_manager, 'delete_template'):
                    print(f"[ERROR] Gallery: template_manager does not have delete_template method")
                    QMessageBox.warning(gallery, "Error", f"Cannot delete template - template manager missing required method.")
                    return
                
                # Call the delete method, safely catching any exceptions
                success = template_manager.delete_template(real_template_name)
                
                print(f"[DEBUG] Gallery: delete_template returned: {success}")
                
                if success:
                    print(f"[DEBUG] Gallery: Successfully deleted template '{real_template_name}'")
                    # If we used a different name than provided, also try to delete that
                    if real_template_name != template_name:
                        print(f"[DEBUG] Gallery: Also attempting to delete '{template_name}'")
                        template_manager.delete_template(template_name)
                    
                    # Reset selection
                    gallery.selected_template = None
                    
                    # Clear multi-selection if applicable
                    if hasattr(gallery, 'multi_selected_templates'):
                        gallery.multi_selected_templates.clear()
                    
                    # Force reload of template data
                    if hasattr(template_manager, 'load_templates'):
                        print(f"[DEBUG] Gallery: Reloading templates after deletion")
                        template_manager.load_templates()
                    if hasattr(template_manager, 'load_folders'):
                        print(f"[DEBUG] Gallery: Reloading folders after deletion")
                        template_manager.load_folders()
                    
                    # Show success message if possible
                    if hasattr(gallery.app, 'show_status_message'):
                        gallery.app.show_status_message(f"Deleted template '{real_template_name}'", "success")
                    
                    # Refresh the gallery with a short delay to ensure the UI updates
                    print(f"[DEBUG] Gallery: Refreshing gallery display after deletion")
                    QTimer.singleShot(100, lambda: gallery.populate_gallery(force_refresh=True))
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
            except Exception as e:
                print(f"[ERROR] Gallery: Exception during template deletion: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.warning(gallery, "Error", f"Error deleting template: {str(e)}")
    
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
                    success_count = 0
                    failed_count = 0
                    
                    # Add delays between deletions to avoid UI locks
                    for i, name in enumerate(template_names):
                        print(f"🔍 LISTENER: Gallery - Deleting template '{name}'")
                        try:
                            # MODIFIED: Call delete_template via template_io
                            if gallery.app.template_manager.template_io.delete_template(name):
                                success_count += 1
                                print(f"🔍 LISTENER: Gallery - Successfully deleted template '{name}'")
                            else:
                                failed_count += 1
                                print(f"🔍 LISTENER: Gallery - Failed to delete template '{name}'")
                        except Exception as e:
                            failed_count += 1
                            print(f"🔍 LISTENER: Gallery - Exception during deletion of '{name}': {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Show appropriate success/failure message
                    if hasattr(gallery.app, 'show_status_message'):
                        if success_count == len(template_names):
                            if len(template_names) == 1:
                                gallery.app.show_status_message(f"Deleted template '{template_names[0]}'", "success")
                            else:
                                gallery.app.show_status_message(f"Deleted {success_count} templates", "success")
                        elif success_count > 0:
                            gallery.app.show_status_message(f"Deleted {success_count} templates, {failed_count} failed", "warning")
                        else:
                            gallery.app.show_status_message(f"Failed to delete templates", "error")
                
                    # Reset selections
                    gallery.selected_template = None
                        
                    # Clear multi-selection
                    if hasattr(gallery, 'multi_selected_templates'):
                        gallery.multi_selected_templates.clear()
                        
                    # Reload template data
                    if (hasattr(gallery.app, 'template_manager') and 
                        hasattr(gallery.app.template_manager, 'load_templates')):
                        print(f"🔍 LISTENER: Gallery - Reloading templates after deletion")
                        gallery.app.template_manager.load_templates()
                        
                    if (hasattr(gallery.app, 'template_manager') and 
                        hasattr(gallery.app.template_manager, 'load_folders')):
                        print(f"🔍 LISTENER: Gallery - Reloading folders after deletion")
                        gallery.app.template_manager.load_folders()
                    
                    # Refresh the gallery with a slight delay to ensure UI updates
                    print(f"🔍 LISTENER: Gallery - Refreshing gallery after deletion")
                    QTimer.singleShot(100, lambda: gallery.populate_gallery(force_refresh=True))
                
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
        
        # Process the single template name received from the signal
        success_count = 0
        single_template_name = template_name # Rename for clarity within this block
        
        # Skip empty names
        if not single_template_name:
            print(f"🔍 LISTENER: Invalid template name received: '{single_template_name}'")
            return False
            
        # Check for special folder names ("Root" means move out of current folder)
        # Note: folder_name comes directly from the signal emitter
        # In _move_template_out_of_folder, it's always ""
        if folder_name == "" or folder_name == "Root" or folder_name == "Up a Level":
            print(f"🔍 LISTENER: Moving template '{single_template_name}' to root (removing from folders)")
            
            # Find which folder the template is currently in
            current_folder_of_template = None
            if hasattr(template_manager, 'folders'):
                for folder, templates in template_manager.folders.items():
                    if single_template_name in templates:
                        current_folder_of_template = folder
                        break
            
            # Remove from the folder it was found in
            if current_folder_of_template:
                print(f"🔍 LISTENER: Removing template '{single_template_name}' from folder '{current_folder_of_template}'")
                result = template_manager.remove_from_folder(current_folder_of_template, single_template_name)
                if result:
                    success_count = 1 # Only one template processed per call
            else:
                print(f"🔍 LISTENER: Template '{single_template_name}' not found in any folder, cannot move to root.")
        else:
            # Normal folder move (to a specific named folder)
            print(f"🔍 LISTENER: Moving template '{single_template_name}' to specific folder '{folder_name}'")
            try:
                result = template_manager.move_template_to_folder(single_template_name, folder_name)
                if result:
                    success_count = 1 # Only one template processed per call
            except Exception as e:
                print(f"🔍 LISTENER: Error moving template '{single_template_name}' to folder '{folder_name}': {e}")
        
        # Update UI only if the move was successful for this template
        if success_count > 0:
            target_display = "root" if folder_name == "" else folder_name
            message = f"Template '{single_template_name}' moved to {target_display}"
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
            
            # Force refresh the gallery - Delay slightly to allow multiple moves to potentially complete
            # before the full refresh happens. This might make the UI feel slightly smoother.
            QTimer.singleShot(50, lambda: gallery.populate_gallery(force_refresh=True))
            return True
        else:
            print(f"🔍 LISTENER: Template '{single_template_name}' move failed or was unnecessary.")

    @staticmethod
    def _save_template_and_structure(gallery, data):
        """Handle saving a template and its structure"""
        try:
            # Save the structure
            structure_save_success = gallery.app.template_manager.save_custom_structure(
                name=data['structure_name'],
                structure=data['structure'],
                category=data['category'],
                description=data['description']
            )
            if not structure_save_success:
                print(f"❌ GALLERY LISTENER: Failed to save structure for template '{data['name']}'")
                return False
            
            # Save the main template file
            save_success = gallery.app.template_manager.save_template(data)

            if save_success:
                # Refresh gallery to show changes
                gallery.refresh_gallery()
                print(f"✅ GALLERY LISTENER: Successfully saved template '{data['name']}'")
                return True
            else:
                print(f"❌ GALLERY LISTENER: Failed to save template '{data['name']}'")
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
            
        # Get export path from user
        export_path, _ = QFileDialog.getSaveFileName(
            gallery,
            "Export Template",
            os.path.expanduser("~") + f"/{template_name}.json",
            "Template Files (*.json)"
        )
        
        if not export_path:
            return  # User cancelled
            
        # Get template data
        template_data = gallery.template_manager.get_template_by_name(template_name)
        if not template_data:
            QMessageBox.warning(gallery, "Error", f"Could not find template '{template_name}'.")
            return
            
        # Export template
        try:
            if hasattr(gallery.template_manager, 'export_template'):
                success = gallery.template_manager.export_template(template_name, export_path)
                if success:
                    QMessageBox.information(gallery, "Success", f"Template '{template_name}' exported successfully.")
                else:
                    QMessageBox.warning(gallery, "Error", f"Failed to export template '{template_name}'.")
            else:
                QMessageBox.warning(gallery, "Not Implemented", "Export functionality is not implemented yet.")
        except Exception as e:
            QMessageBox.critical(gallery, "Error", f"Error exporting template: {str(e)}")
    
    @staticmethod
    def on_duplicate_template(gallery, template_name):
        """Handle duplicating a template"""
        print(f"🔍 LISTENER: Duplicate requested for '{template_name}'")
        
        if not template_name or not hasattr(gallery, 'template_manager'):
            QMessageBox.warning(gallery, "Error", "Cannot duplicate template: No template selected or template manager not available.")
            return
            
        # Ask for new name
        new_name, ok = QInputDialog.getText(
            gallery,
            "Duplicate Template",
            "Enter name for the duplicate template:",
            text=f"{template_name} (Copy)"
        )
        
        if not ok or not new_name:
            return  # User cancelled
            
        # Duplicate template
        try:
            if hasattr(gallery.template_manager, 'duplicate_template'):
                success = gallery.template_manager.duplicate_template(template_name, new_name)
                if success:
                    QMessageBox.information(gallery, "Success", f"Template '{template_name}' duplicated as '{new_name}'.")
                    gallery.populate_gallery(force_refresh=True)
                else:
                    QMessageBox.warning(gallery, "Error", f"Failed to duplicate template '{template_name}'.")
            else:
                QMessageBox.warning(gallery, "Not Implemented", "Duplicate functionality is not implemented yet.")
        except Exception as e:
            QMessageBox.critical(gallery, "Error", f"Error duplicating template: {str(e)}")
    
    @staticmethod
    def on_rename_template(gallery, template_name):
        """Handle renaming a template"""
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
                else:
                    QMessageBox.warning(gallery, "Error", f"Failed to rename template '{template_name}'.")
            else:
                QMessageBox.warning(gallery, "Not Implemented", "Rename functionality is not implemented yet.")
        except Exception as e:
            QMessageBox.critical(gallery, "Error", f"Error renaming template: {str(e)}") 