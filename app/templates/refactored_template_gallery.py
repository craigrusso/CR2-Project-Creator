#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Bridge module to integrate the refactored template gallery components
with the existing application structure.
"""

import os
import sys
from PyQt5.QtWidgets import QApplication

# Import from refactored modules
from app.templates.template_gallery import TemplateGallery
from app.templates.components import TemplateFolderCard

def create_template_gallery(app):
    """
    Create and return a template gallery widget.
    
    This function maintains compatibility with the original template_gallery_ui_pyqt.py.
    """
    # Make sure the app object has the template_manager attribute
    if not hasattr(app, 'template_manager'):
        from app.templates.template_manager import TemplateManager
        app.template_manager = TemplateManager()
        
    # Create the gallery with the app object that has the template_manager
    gallery = TemplateGallery(app=app)
    return gallery

def select_template_from_gallery(app, template):
    """
    Select a template from the gallery.
    
    This function maintains compatibility with the original template_gallery_ui_pyqt.py.
    """
    if app and hasattr(app, 'template_gallery'):
        # Emit the template_selected signal with the template data
        if isinstance(app.template_gallery, TemplateGallery):
            app.template_gallery.template_selected.emit(template)
            return True
    return False 