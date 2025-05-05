#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import re

def get_template_file(app):
    """Open file dialog to select a template file or directory"""
    try:
        # Use PyQt file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            app,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai)"
        )
        
        if file_path:
            app.template_file_path = file_path
            # Create a template in the recent templates
            if hasattr(app, 'add_to_recent_templates'):
                app.add_to_recent_templates(file_path)
            
            return file_path
        return None
    except Exception as e:
        print(f"Error selecting template file: {e}")
        return None

def clear_template_file(app):
    """Clear the current template file selection"""
    try:
        app.template_file_path = ""
        
        # Update status if available
        if hasattr(app, 'show_status_message'):
            app.show_status_message("Template file cleared")
    except Exception as e:
        print(f"Error clearing template file: {e}")

def clear_structure_template(app):
    """Clear the current structure template selection"""
    try:
        if hasattr(app, 'current_template'):
            app.current_template = None
        if hasattr(app, 'selected_structure_template'):
            app.selected_structure_template = None
            
        # Update status if available
        if hasattr(app, 'show_status_message'):
            app.show_status_message("Structure template cleared")
    except Exception as e:
        print(f"Error clearing structure template: {e}")

def rename_current_template(app):
    """Rename the current template"""
    # This is a stub function to maintain compatibility
    pass

def rename_template_file(app):
    """Rename the template file displayed in the UI"""
    # This is a stub function to maintain compatibility
    pass

def sanitize_filename(filename):
    """
    Sanitize a filename for cross-platform compatibility.
    Replaces unsafe characters with safe ones.
    """
    # Replace characters not allowed in filenames across platforms
    unsafe_chars = [":", "/", "\\", "?", "*", "\"", "<", ">", "|", "'"]
    safe_filename = filename
    for char in unsafe_chars:
        safe_filename = safe_filename.replace(char, "-")

    # Replace spaces with underscores
    safe_filename = safe_filename.replace(" ", "_")

    # Trim to a reasonable length
    if len(safe_filename) > 180:
        # Keep extension if any
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:175] + ext

    return safe_filename

def _guess_file_type(file_name):
    """
    Guess the file type based on the file extension

    Args:
        file_name: The file name

    Returns:
        str: The file type
    """
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    # Video extensions
    if ext in ['.mp4', '.mov', '.avi', '.mkv', '.prproj', '.aep']:
        return 'video'
    # Audio extensions
    elif ext in ['.mp3', '.wav', '.aac', '.flac']:
        return 'audio'
    # Image extensions
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd']:
        return 'image'
    # Document extensions
    elif ext in ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.csv', '.xls', '.xlsx']:
        return 'document'
    # Code extensions
    elif ext in ['.py', '.js', '.html', '.css', '.json', '.xml']:
        return 'code'
    else:
        return 'other'

def _sanitize_template_name(name):
    """
    Sanitize a template name for use as a filename

    Args:
        name: The template name to sanitize

    Returns:
        str: The sanitized template name
    """
    if not name:
        return "unnamed_template"

    # Remove special characters and replace spaces with underscores
    sanitized = re.sub(r'[^\w\\s-]', '', name)
    sanitized = re.sub(r'[\\s-]+', '_', sanitized)

    # Ensure it's not too long (max 100 chars)
    if len(sanitized) > 100:
        sanitized = sanitized[:100]

    # Ensure we have a valid name after sanitizing
    if not sanitized:
        return "unnamed_template"

    return sanitized 