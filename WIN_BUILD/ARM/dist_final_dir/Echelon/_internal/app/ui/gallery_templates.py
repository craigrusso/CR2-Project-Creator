import os
import sys
import json
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QLineEdit, QMessageBox, QGridLayout, QScrollArea,
    QSizePolicy, QFrame, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor

# Import the enhanced structure editor
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_operations import TemplateOperations

class TemplatesGallery(QWidget):
    def handle_template_edit(self, template_name):
        """Handle editing a template"""
        print(f"DEBUG: Direct edit of template: {template_name}")
        
        # Construct the template name for the editor
        structure_name = f"Template_{template_name}" if not template_name.startswith("Template_") else template_name
        
        # Show the enhanced structure editor
        from app.ui.structure_editor_functions import show_enhanced_structure_editor
        success, structure, new_name = show_enhanced_structure_editor(
            self, 
            structure_name=structure_name,
            is_new=False
        )
        
        if success and new_name:
            # Get the template manager
            if hasattr(self, 'app') and hasattr(self.app, 'template_manager'):
                # First save the structure
                structure_save_success = self.app.template_manager.save_custom_structure(
                    name=new_name,
                    structure=structure
                )
                
                if not structure_save_success:
                    print(f"DEBUG: Failed to save structure for template '{new_name}'")
                    return False
                
                # Create a proper template data object
                template_data = {
                    'name': new_name,
                    'structure': structure,
                    'modified': time.time(),
                    'category': 'Custom',  # Default category
                    # Add original_name if this is a rename operation
                    'original_name': template_name if template_name != new_name else None
                }
                
                # Save the template with the updated structure
                template_save_success = self.app.template_manager.save_template(template_data)
                
                if template_save_success:
                    print(f"DEBUG: Successfully saved template '{new_name}'")
                    # Force refresh of gallery
                    if hasattr(self, 'populate_gallery'):
                        self.populate_gallery(force_refresh=True)
                    return True
                else:
                    print(f"DEBUG: Failed to save template '{new_name}'")
                    return False
        
        return success

    def _update_template_references(self, old_name, new_name):
        """Update all references to a template name in internal data structures"""
        print(f"DEBUG: Updating all references from '{old_name}' to '{new_name}'")
        
        # Update template references in the templates list
        if hasattr(self, 'templates') and isinstance(self.templates, list):
            for i, template in enumerate(self.templates):
                if template.get('name') == old_name:
                    print(f"DEBUG: Updating template at index {i} from '{old_name}' to '{new_name}'")
                    self.templates[i]['name'] = new_name
        
        # If this template is selected, update the selection
        if hasattr(self, 'selected_templates') and isinstance(self.selected_templates, set):
            if old_name in self.selected_templates:
                self.selected_templates.remove(old_name)
                self.selected_templates.add(new_name)
                print(f"DEBUG: Updated selection from '{old_name}' to '{new_name}'")
        
        # If there's a parent with a template manager, ensure it's updated too
        if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'template_manager'):
            self.parent.template_manager.update_references(old_name, new_name)

    def handle_template_renamed(self, old_name, new_name):
        """Handle a template being renamed"""
        print(f"INFO: Template renamed from '{old_name}' to '{new_name}'")
        
        # Update any references to this template in our UI
        # This might be in selected templates or elsewhere
        for i, template in enumerate(self.templates):
            if template.get('name') == old_name:
                print(f"INFO: Updating template reference from '{old_name}' to '{new_name}'")
                self.templates[i]['name'] = new_name
                
        # If this template is selected, update the selection
        if old_name in self.selected_templates:
            self.selected_templates.remove(old_name)
            self.selected_templates.add(new_name)
            print(f"INFO: Updated selection from '{old_name}' to '{new_name}'")
            
        # Make sure to refresh the UI
        self.refresh_templates()
        # Scroll to the renamed template
        self.scroll_to_template(new_name)
            
    def refresh_templates(self):
        """Refresh the templates grid"""
        print("DEBUG: Refreshing templates grid")
        
        # Reload templates from the template manager
        if hasattr(self, 'template_manager'):
            self.templates = self.template_manager.get_all_templates()
            print(f"DEBUG: Loaded {len(self.templates)} templates from template manager")
            
            # Clear the grid and rebuild it
            self.clear_grid()
            self.populate_grid()
            
            # Emit signal that templates have been refreshed
            if hasattr(self, 'templates_refreshed') and callable(self.templates_refreshed):
                self.templates_refreshed.emit()
        else:
            print("ERROR: Cannot refresh templates - template_manager not available")
            
    def scroll_to_template(self, template_name):
        """Scroll to make a specific template visible"""
        # Find the template card in the grid
        for i in range(self.templates_grid.count()):
            item = self.templates_grid.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'template_name') and widget.template_name == template_name:
                    # Scroll to this widget
                    self.scroll_area.ensureWidgetVisible(widget)
                    # Highlight the widget
                    if hasattr(widget, 'highlight'):
                        widget.highlight()
                    return True
        return False 