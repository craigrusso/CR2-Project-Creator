#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt5.QtWidgets import QInputDialog, QMessageBox
from PyQt5.QtCore import Qt

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
        # Unselect all templates
        if hasattr(gallery, 'selected_template') and gallery.selected_template == template:
            # If clicking the same template again, don't do anything
            return
            
        gallery.selected_template = template
        gallery.selected_folder = None  # Reset folder selection
        
        # Update button states
        gallery.edit_button.setEnabled(True)
        gallery.delete_button.setEnabled(True)
        gallery.delete_folder_button.setEnabled(False)
        
        # Update card styling
        for card in gallery.template_cards:
            # Check if the card represents the selected template
            if hasattr(card, 'template') and card.template == template:
                card.set_selected(True)
            else:
                card.set_selected(False)
                
        # Emit the signal
        gallery.template_selected.emit(template)
    
    @staticmethod
    def on_folder_select(gallery, folder_name):
        """Handle folder selection"""
        if hasattr(gallery, 'selected_folder') and gallery.selected_folder == folder_name:
            # If clicking the same folder again, don't do anything
            return
            
        gallery.selected_folder = folder_name
        gallery.selected_template = None  # Reset template selection
        
        # Update button states
        gallery.edit_button.setEnabled(False)
        gallery.delete_button.setEnabled(False)
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
        if hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'add_template'):
            gallery.app.template_manager.add_template()
            gallery.populate_gallery()
    
    @staticmethod
    def on_edit_template(gallery):
        """Handle edit template button click"""
        if gallery.selected_template and hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'edit_template'):
            gallery.app.template_manager.edit_template(gallery.selected_template)
            gallery.populate_gallery()
    
    @staticmethod
    def on_delete_template(gallery):
        """Handle delete template button click"""
        if gallery.selected_template and hasattr(gallery.app, 'template_manager') and hasattr(gallery.app.template_manager, 'delete_template'):
            gallery.app.template_manager.delete_template(gallery.selected_template)
            gallery.selected_template = None
            gallery.populate_gallery()
    
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
        # Handle delete or backspace key when a folder is selected
        if gallery.selected_folder and (event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace):
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
        else:
            # Call the parent's keyPressEvent
            pass  # This will be handled in the refactored main class 