#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Core module for the Enhanced Structure Editor
Acts as the central coordinator between UI and functional components
"""

import os
import json
import time
from PyQt5.QtWidgets import QDialog, QMessageBox, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal

# Import from local modules
from .utils import _count_structure_items

class StructureEditorCore:
    """
    Core class that coordinates structure editor functionality
    
    This class acts as the coordinator between UI and functional components.
    It does not directly implement functionality but delegates to specialized modules.
    """
    
    def __init__(self, editor):
        """
        Initialize the structure editor core
        
        Args:
            editor: Reference to the parent editor
        """
        self.editor = editor
        
        # Initialize properties
        self.structure_name = getattr(editor, 'structure_name', None)
        self.original_template_name = getattr(editor, 'original_template_name', None)
        self.files_to_cache = {}
        
        # Get references to components already created in the editor
        # The structure_converter should exist in the editor
        # It is created before this class in the editor's __init__ method
        self.structure_converter = getattr(editor, 'structure_converter', None)
        if not self.structure_converter:
            print("WARNING: structure_converter not found in editor")
        
        # Initialize component references for those not yet created
        self.ui_builder = None
        self.template_handler = None
        self.file_operations = None
        self.drag_drop_handler = None
        
        # Initialize components when available
        self._init_components()
    
    def _init_components(self):
        """Initialize all components if they're available"""
        # Import here to avoid circular imports
        try:
            # Structure converter should already exist in the editor
            # It is created before this class in the editor's __init__ method
            # Do not attempt to recreate it - simply use the reference
            
            # Create UI Builder if not already created
            if not hasattr(self, 'ui_builder') or not self.ui_builder:
                from .ui_components import UIBuilder
                self.ui_builder = UIBuilder(self.editor)
                
            # Create template handler if not already created
            if not hasattr(self, 'template_handler') or not self.template_handler:
                from .template_handler import TemplateHandler
                self.template_handler = TemplateHandler(self.editor)
                
            # Create file operations if not already created
            if not hasattr(self, 'file_operations') or not self.file_operations:
                from .file_operations import FileOperations
                self.file_operations = FileOperations(self.editor)
                
            # Create drag drop handler if not already created
            if not hasattr(self, 'drag_drop_handler') or not self.drag_drop_handler:
                from .drag_drop import DragDropHandler
                self.drag_drop_handler = DragDropHandler(self.editor)
                
            # Add references to editor for backward compatibility
            if not hasattr(self.editor, 'add_file') and hasattr(self.file_operations, 'add_file'):
                self.editor.add_file = self.file_operations.add_file
                
            if not hasattr(self.editor, 'add_folder') and hasattr(self.file_operations, 'add_folder'):
                self.editor.add_folder = self.file_operations.add_folder
                
            if not hasattr(self.editor, 'delete_selected') and hasattr(self.file_operations, 'delete_selected'):
                self.editor.delete_selected = self.file_operations.delete_selected
                
            if not hasattr(self.editor, 'is_binary_file') and hasattr(self.file_operations, 'is_binary_file'):
                self.editor.is_binary_file = self.file_operations.is_binary_file
                
        except ImportError as e:
            print(f"DEBUG: Error importing component: {e}")
    
    def init_ui(self):
        """Initialize the user interface"""
        if self.ui_builder:
            return self.ui_builder.init_ui()
        return None
    
    def accept(self):
        """
        Handle dialog acceptance
        
        This method is called when the user clicks the OK button.
        It saves the structure and closes the dialog.
        """
        print(f"Accepting structure editor with template: {self.structure_name}")
        
        try:
            # Get current template name
            template_info = self.get_current_template_info()
            template_name = template_info.get('template_name', '')
            
            # Update structure name
            if template_name:
                self.structure_name = template_name
            
            # Save structure (using handler if available)
            if self.template_handler and hasattr(self.template_handler, 'save_structure'):
                success = self.template_handler.save_structure(self.structure_name)
            else:
                # Direct fallback to save
                success = self.save_structure(self.structure_name)
                
            if success:
                # Close dialog with accept
                from PyQt5.QtWidgets import QDialog
                self.editor.done(QDialog.Accepted)
            else:
                print("Error saving structure")
                
        except Exception as e:
            import traceback
            print(f"Error in accept: {e}")
            traceback.print_exc()
    
    def save_structure(self, structure_name):
        """
        Save the structure to the template manager
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self.template_handler:
            return self.template_handler.save_structure(structure_name)
            
        # Fallback to editor's save_structure method
        if hasattr(self.editor, 'save_structure'):
            return self.editor.save_structure(structure_name)
            
        return False
    
    def get_current_template_info(self):
        """
        Get the current template information
        
        Returns:
            dict: Dictionary containing template information
        """
        if self.template_handler:
            return self.template_handler.get_template_info()
            
        # Fallback to UI builder
        if self.ui_builder:
            return self.ui_builder.get_ui_values()
            
        # No template info available
        return {
            'template_name': self.structure_name or '',
            'template_category': 'Custom',
            'template_info': ''
        }
    
    def create_structure_from_tree(self):
        """
        Create a structure from the tree
        
        Returns:
            list: Structure data
        """
        if self.structure_converter:
            return self.structure_converter.create_structure_from_tree()
            
        # Fallback to editor's method
        if hasattr(self.editor, 'create_structure_from_tree'):
            return self.editor.create_structure_from_tree()
            
        return None
    
    def get_result(self):
        """
        Get the final result from the editor
        
        Returns:
            dict: Dictionary containing the structure data and template name
        """
        # Create the structure from the tree
        structure = self.create_structure_from_tree()
        
        # Get template information
        template_info = self.get_current_template_info()
        
        # Return the result as a dictionary
        return {
            'structure': structure,
            'template_name': template_info.get('template_name', ''),
            'template_category': template_info.get('template_category', 'Custom'),
            'template_info': template_info.get('template_info', '')
        } 