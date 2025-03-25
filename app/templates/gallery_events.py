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
            return
            
        # Set the selected template in gallery state
        gallery.selected_template = template
        
        # Also ensure it's set in the app object if available
        if hasattr(gallery, 'app'):
            gallery.app.selected_template = template
            print(f"🔍 LISTENER: Updated app-level selected template to '{template_name}'")
        
        gallery.selected_folder = None  # Reset folder selection
        print(f"🔍 LISTENER: Template selection set to '{template_name}'")
        
        # Clear any multi-selection
        if hasattr(gallery, 'multi_selected_templates'):
            # Temporarily store multi-selection to deselect items
            items_to_deselect = gallery.multi_selected_templates.copy()
            gallery.multi_selected_templates.clear()
            
            # Manually update styling for previously multi-selected items
            if hasattr(gallery, 'template_cards'):
                for card in gallery.template_cards:
                    if hasattr(card, 'template') and card.template in items_to_deselect:
                        if hasattr(card, 'set_multi_selected'):
                            card.set_multi_selected(False)
        
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
            
            # Use the enhanced structure editor directly for creating new templates
            from app.ui.structure_editor_functions import show_enhanced_structure_editor
            
            # Create an empty structure with a blank name - user will set it in the editor
            structure_name = "Template_"  # Will be populated with the actual name after user sets it
            
            print(f"🔍 EDIT TEMPLATE: Starting template edit for ''")
            print(f"🔍 EDIT TEMPLATE: Template is_new=True, name='', structure_name='{structure_name}'")
            
            # Open the structure editor directly
            result, updated_structure, updated_structure_name, original_template_name, updated_template_name = show_enhanced_structure_editor(
                parent=gallery,
                structure_name=structure_name,
                structure=[],
                is_new=True,
                template_name="",
                focus_name_field=True,
                template_manager=gallery.app.template_manager,
                callback=lambda data: GalleryEvents._save_template_and_structure(gallery, data)
            )
            
            if result:
                print(f"🔍 LISTENER: Successfully created/edited template '{updated_template_name}'")
                
                # Force refresh gallery to show the new template
                print(f"🔍 LISTENER: Forcing gallery refresh to show new template")
                gallery.populate_gallery(force_refresh=True)
                
                # Select the new template
                if hasattr(gallery, 'select_template'):
                    print(f"🔍 LISTENER: Selecting saved template: {updated_template_name}")
                    gallery.select_template(updated_template_name)
            else:
                print(f"🔍 LISTENER: Template editor was cancelled or failed")
            
        except Exception as e:
            import traceback
            print(f"Error in on_add_template: {e}")
            print(traceback.format_exc())
            QMessageBox.warning(gallery, "Error", f"Failed to add template: {str(e)}")

    @staticmethod
    def _save_template_and_structure(gallery, data):
        """
        Save template and its structure in one operation
        
        Args:
            gallery: Gallery instance
            data: Data from the structure editor callback
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Make sure we have access to the template manager
            if not hasattr(gallery, 'app') or not hasattr(gallery.app, 'template_manager'):
                print("🔍 ERROR: Template manager not available")
                return False
                
            # Extract template details
            template_name = data.get('name', '')
            structure_name = data.get('structure_name', '')
            structure = data.get('structure', [])
            is_new = data.get('is_new', False)
            is_rename = data.get('is_rename', False)
            original_name = data.get('original_name', '')
            
            if not template_name:
                print("🔍 ERROR: Cannot save template - empty name")
                return False
                
            print(f"🔍 LISTENER: Saving template '{template_name}' with structure")
            
            # Handle rename operation
            if is_rename and original_name:
                print(f"🔍 LISTENER: This is a rename operation from '{original_name}' to '{template_name}'")
                
                # Perform the rename operation
                success = gallery.app.template_manager.rename_template(original_name, template_name)
                if not success:
                    print(f"🔍 ERROR: Failed to rename template from '{original_name}' to '{template_name}'")
                    return False
                    
                print(f"🔍 LISTENER: Successfully renamed template from '{original_name}' to '{template_name}'")
            
            # For new templates, create the basic template first
            if is_new:
                # Create template data
                template_data = {
                    'name': template_name,
                    'description': "Template created with structure editor",
                    'category': 'Custom',
                    'type': 'Standard',
                    'created': time.time(),
                    'modified': time.time(),
                    'tags': []
                }
                
                # Get source files from the template data if available
                source_files = []
                if hasattr(gallery, 'template_editor') and hasattr(gallery.template_editor, 'get_files'):
                    try:
                        source_files = gallery.template_editor.get_files()
                        print(f"🔍 LISTENER: Found {len(source_files)} files in template editor")
                    except Exception as e:
                        print(f"🔍 ERROR: Failed to get files from template editor: {e}")
                
                try:
                    # Save the template with the new method signature
                    print(f"🔍 LISTENER: Saving template '{template_name}' with structure")
                    success = gallery.app.template_manager.save_template(
                        template_name=template_name,
                        structure=structure,
                        template_data=template_data,
                        source_files=source_files,
                        cache_files=True
                    )
                    
                    if not success:
                        print(f"🔍 ERROR: Failed to save template '{template_name}'")
                        return False
                    
                    print(f"🔍 LISTENER: Created new template '{template_name}'")
                    
                    # Since we've already saved the structure with the template, we can skip the separate
                    # structure saving step below
                    return True
                except Exception as e:
                    print(f"🔍 ERROR: Exception while saving template: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                # For existing templates, update the structure
                if hasattr(gallery.app.template_manager, 'save_structure'):
                    # Ensure structure name matches template name
                    if not structure_name or not structure_name.startswith("Template_"):
                        structure_name = f"Template_{template_name}"
                    
                    # Save the structure with proper association to the template
                    success = gallery.app.template_manager.save_structure(structure_name, structure)
                    
                    if success:
                        print(f"🔍 LISTENER: Successfully saved structure '{structure_name}' for template '{template_name}'")
                        
                        # Associate structure with template
                        if hasattr(gallery.app.template_manager, 'associate_structure_with_template'):
                            gallery.app.template_manager.associate_structure_with_template(template_name, structure_name)
                            print(f"🔍 LISTENER: Associated structure '{structure_name}' with template '{template_name}'")
                    else:
                        print(f"🔍 ERROR: Failed to save structure '{structure_name}'")
                        return False
                else:
                    print(f"🔍 WARNING: Template manager does not support save_structure, structure not saved")
            
            # Ensure template manager reloads to have updated templates and structures
            if hasattr(gallery.app.template_manager, 'load_templates'):
                gallery.app.template_manager.load_templates()
                
            if hasattr(gallery.app.template_manager, 'load_custom_structures'):
                gallery.app.template_manager.load_custom_structures()
            
            return True
            
        except Exception as e:
            print(f"🔍 ERROR: Exception while saving template and structure: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
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
        result, updated_structure, updated_structure_name, original_template_name, updated_template_name = show_enhanced_structure_editor(
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
                            if gallery.app.template_manager.delete_template(name):
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