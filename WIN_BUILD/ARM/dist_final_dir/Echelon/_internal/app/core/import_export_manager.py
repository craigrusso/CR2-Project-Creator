#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox, QInputDialog
from app.constants import APP_NAME # Import the APP_NAME constant
import sys
import re
import time
from app.ui.dialog_styling import StyledMessageBox, StyledInputDialog
try:
    from app.utils.utils import normalize_path_for_storage
except ImportError:
    # Fallback if not available
    def normalize_path_for_storage(path):
        """Normalize a path for storage with forward slashes"""
        if not path:
            return ""
        norm_path = os.path.normpath(path)
        return norm_path.replace('\\', '/')

def export_package(app, include_settings=True, include_templates=True):
    """
    Export application settings and/or templates to a package file.
    
    Args:
        app: The main application instance
        include_settings: Whether to include settings in the export
        include_templates: Whether to include templates in the export
    """
    # First check if there's anything to export
    if not include_settings and not include_templates:
        QMessageBox.warning(app, "Export Error", "Nothing selected for export.")
        return
    
    # Determine export type for dialog title
    export_type = "Package"
    if include_settings and not include_templates:
        export_type = "Settings"
    elif include_templates and not include_settings:
        export_type = "Templates"
    
    # Ask user where to save the export file
    file_path, _ = QFileDialog.getSaveFileName(
        app,
        f"Export {export_type}",
        os.path.expanduser(f"~/Desktop/{APP_NAME}_Export.zip"), # Use APP_NAME for the default filename
        "ZIP Files (*.zip)"
    )
    
    if not file_path:
        return  # User canceled
    
    # Add .zip extension if not present
    if not file_path.lower().endswith('.zip'):
        file_path += '.zip'
    
    # Create temporary directory for export files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create metadata file with export information
        metadata = {
            "export_date": datetime.now().isoformat(),
            "app_version": app.app_version if hasattr(app, 'app_version') else "Unknown",
            "includes_settings": include_settings,
            "includes_templates": include_templates
        }
        
        with open(os.path.join(temp_dir, "export_metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Get path to templates directory
        templates_dir = None
        if hasattr(app, 'template_manager') and hasattr(app.template_manager, 'paths'):
            templates_dir = app.template_manager.paths.get("templates_dir")
        
        # Get path to config directory
        config_dir = None
        if hasattr(app, 'settings'):
            config_dir = os.path.dirname(app.settings.fileName())
        
        # Export templates if requested
        if include_templates and templates_dir and os.path.exists(templates_dir):
            export_templates_dir = os.path.join(temp_dir, "templates")
            os.makedirs(export_templates_dir, exist_ok=True)
            
            # Copy all template files
            for item in os.listdir(templates_dir):
                src_path = os.path.join(templates_dir, item)
                dst_path = os.path.join(export_templates_dir, item)
                
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
            
            # Export custom structures if available
            if hasattr(app, 'template_manager') and hasattr(app.template_manager, 'paths'):
                custom_structures_dir = app.template_manager.paths.get("custom_structures_dir")
                if custom_structures_dir and os.path.exists(custom_structures_dir):
                    export_structures_dir = os.path.join(temp_dir, "structures")
                    os.makedirs(export_structures_dir, exist_ok=True)
                    
                    # Copy all structure files
                    for item in os.listdir(custom_structures_dir):
                        src_path = os.path.join(custom_structures_dir, item)
                        dst_path = os.path.join(export_structures_dir, item)
                        
                        if os.path.isfile(src_path):
                            shutil.copy2(src_path, dst_path)
                        elif os.path.isdir(src_path):
                            shutil.copytree(src_path, dst_path)
        
        # Export settings if requested
        if include_settings and config_dir and os.path.exists(config_dir):
            export_settings_dir = os.path.join(temp_dir, "settings")
            os.makedirs(export_settings_dir, exist_ok=True)
            
            # Copy all settings files
            for item in os.listdir(config_dir):
                src_path = os.path.join(config_dir, item)
                dst_path = os.path.join(export_settings_dir, item)
                
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
        
        # Create ZIP file with all exported data
        try:
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path_full = os.path.join(root, file)
                        arcname = os.path.relpath(file_path_full, temp_dir)
                        zipf.write(file_path_full, arcname)
            
            QMessageBox.information(
                app, 
                "Export Successful", 
                f"{export_type} exported successfully!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                app,
                "Export Error",
                f"An error occurred during export: {str(e)}"
            )

def import_package(app, import_settings=True, import_templates=True):
    """
    Import application settings and/or templates from a package file.
    
    Args:
        app: The main application instance
        import_settings: Whether to import settings
        import_templates: Whether to import templates
    """
    # First check if there's anything to import
    if not import_settings and not import_templates:
        QMessageBox.warning(app, "Import Error", "Nothing selected for import.")
        return
    
    # Determine import type for dialog title
    import_type = "Package"
    if import_settings and not import_templates:
        import_type = "Settings"
    elif import_templates and not import_settings:
        import_type = "Templates"
    
    # Ask user for the import file
    file_path, _ = QFileDialog.getOpenFileName(
        app,
        f"Import {import_type}",
        os.path.expanduser("~/Desktop"),
        "ZIP Files (*.zip)"
    )
    
    if not file_path:
        return  # User canceled
    
    # Create temporary directory for extracted files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract ZIP file
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                zipf.extractall(temp_dir)
        except Exception as e:
            QMessageBox.critical(
                app,
                "Import Error",
                f"Failed to extract import file: {str(e)}"
            )
            return
        
        # Verify metadata file exists
        metadata_path = os.path.join(temp_dir, "export_metadata.json")
        if not os.path.exists(metadata_path):
            QMessageBox.warning(
                app,
                "Import Error",
                "Invalid import file. Metadata not found."
            )
            return
        
        # Load metadata
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            QMessageBox.critical(
                app,
                "Import Error",
                f"Failed to read metadata: {str(e)}"
            )
            return
        
        # Verify package contents
        if import_settings and not metadata.get("includes_settings", False):
            QMessageBox.warning(
                app,
                "Import Warning",
                "The selected package does not contain settings."
            )
            import_settings = False
        
        if import_templates and not metadata.get("includes_templates", False):
            QMessageBox.warning(
                app,
                "Import Warning",
                "The selected package does not contain templates."
            )
            import_templates = False
        
        # If nothing to import after verification, exit
        if not import_settings and not import_templates:
            QMessageBox.warning(
                app,
                "Import Error",
                "Nothing to import from the selected package."
            )
            return
        
        # Show confirmation dialog with options
        dialog = QDialog(app)
        dialog.setWindowTitle(f"Import {import_type}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Information label
        info_label = QLabel(f"You're about to import the following from the package:")
        layout.addWidget(info_label)
        
        # Options
        settings_checkbox = None
        templates_checkbox = None
        merge_checkbox = None
        
        if import_settings:
            settings_checkbox = QCheckBox("Settings")
            settings_checkbox.setChecked(True)
            layout.addWidget(settings_checkbox)
        
        if import_templates:
            templates_checkbox = QCheckBox("Templates")
            templates_checkbox.setChecked(True)
            layout.addWidget(templates_checkbox)
            
            # Option to merge or replace templates
            merge_checkbox = QCheckBox("Merge with existing templates (otherwise replace)")
            merge_checkbox.setChecked(True)
            layout.addWidget(merge_checkbox)
        
        # Warning label
        warning_label = QLabel("Warning: This operation may overwrite your existing settings and/or templates.")
        warning_label.setStyleSheet("color: red;")
        layout.addWidget(warning_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec() != QDialog.Accepted:
            return  # User canceled
        
        # Get user options
        if settings_checkbox:
            import_settings = settings_checkbox.isChecked()
        
        if templates_checkbox:
            import_templates = templates_checkbox.isChecked()
        
        merge_templates = merge_checkbox.isChecked() if merge_checkbox else True
        
        # If nothing selected, exit
        if not import_settings and not import_templates:
            QMessageBox.warning(
                app,
                "Import Error",
                "Nothing selected for import."
            )
            return
        
        # Import templates if requested
        if import_templates:
            templates_src = os.path.join(temp_dir, "templates")
            if os.path.exists(templates_src):
                try:
                    # Get destination directory
                    templates_dst = None
                    if hasattr(app, 'template_manager') and hasattr(app.template_manager, 'paths'):
                        templates_dst = app.template_manager.paths.get("templates_dir")
                    
                    if templates_dst:
                        if merge_templates:
                            # Merge templates by copying individual files
                            for item in os.listdir(templates_src):
                                src_path = os.path.join(templates_src, item)
                                dst_path = os.path.join(templates_dst, item)
                                
                                if os.path.isfile(src_path):
                                    shutil.copy2(src_path, dst_path)
                                elif os.path.isdir(src_path):
                                    if os.path.exists(dst_path):
                                        # Merge directory contents
                                        for subitem in os.listdir(src_path):
                                            sub_src = os.path.join(src_path, subitem)
                                            sub_dst = os.path.join(dst_path, subitem)
                                            
                                            if os.path.isfile(sub_src):
                                                shutil.copy2(sub_src, sub_dst)
                                            elif os.path.isdir(sub_src):
                                                if not os.path.exists(sub_dst):
                                                    shutil.copytree(sub_src, sub_dst)
                                    else:
                                        # Directory doesn't exist, just copy it
                                        shutil.copytree(src_path, dst_path)
                        else:
                            # Replace existing templates
                            if os.path.exists(templates_dst):
                                shutil.rmtree(templates_dst)
                            shutil.copytree(templates_src, templates_dst)
                    
                    # Import custom structures if available
                    structures_src = os.path.join(temp_dir, "structures")
                    if os.path.exists(structures_src):
                        structures_dst = None
                        if hasattr(app, 'template_manager') and hasattr(app.template_manager, 'paths'):
                            structures_dst = app.template_manager.paths.get("custom_structures_dir")
                            
                        if structures_dst:
                            if merge_templates:
                                # Merge structures by copying individual files
                                for item in os.listdir(structures_src):
                                    src_path = os.path.join(structures_src, item)
                                    dst_path = os.path.join(structures_dst, item)
                                    
                                    if os.path.isfile(src_path):
                                        shutil.copy2(src_path, dst_path)
                                    elif os.path.isdir(src_path):
                                        if os.path.exists(dst_path):
                                            # Merge directory contents
                                            for subitem in os.listdir(src_path):
                                                sub_src = os.path.join(src_path, subitem)
                                                sub_dst = os.path.join(dst_path, subitem)
                                                
                                                if os.path.isfile(sub_src):
                                                    shutil.copy2(sub_src, sub_dst)
                                                elif os.path.isdir(sub_src):
                                                    if not os.path.exists(sub_dst):
                                                        shutil.copytree(sub_src, sub_dst)
                                        else:
                                            # Directory doesn't exist, just copy it
                                            shutil.copytree(src_path, dst_path)
                            else:
                                # Replace existing structures
                                if os.path.exists(structures_dst):
                                    for item in os.listdir(structures_dst):
                                        item_path = os.path.join(structures_dst, item)
                                        if os.path.isfile(item_path):
                                            os.remove(item_path)
                                        elif os.path.isdir(item_path):
                                            shutil.rmtree(item_path)
                                            
                                # Copy all structure files
                                for item in os.listdir(structures_src):
                                    src_path = os.path.join(structures_src, item)
                                    dst_path = os.path.join(structures_dst, item)
                                    
                                    if os.path.isfile(src_path):
                                        shutil.copy2(src_path, dst_path)
                                    elif os.path.isdir(src_path):
                                        shutil.copytree(src_path, dst_path)
                except Exception as e:
                    QMessageBox.critical(
                        app,
                        "Import Error",
                        f"Failed to import templates: {str(e)}"
                    )
        
        # Import settings if requested
        if import_settings:
            settings_src = os.path.join(temp_dir, "settings")
            if os.path.exists(settings_src):
                try:
                    # Get destination directory
                    settings_dst = None
                    if hasattr(app, 'settings'):
                        settings_dst = os.path.dirname(app.settings.fileName())
                    
                    if settings_dst:
                        # Copy all settings files
                        for item in os.listdir(settings_src):
                            src_path = os.path.join(settings_src, item)
                            dst_path = os.path.join(settings_dst, item)
                            
                            if os.path.isfile(src_path):
                                shutil.copy2(src_path, dst_path)
                            elif os.path.isdir(src_path):
                                if os.path.exists(dst_path):
                                    shutil.rmtree(dst_path)
                                shutil.copytree(src_path, dst_path)
                except Exception as e:
                    QMessageBox.critical(
                        app,
                        "Import Error",
                        f"Failed to import settings: {str(e)}"
                    )
        
        # Success message - use our styled message box
        StyledMessageBox.show_information(
            app,
            "Import Successful",
            f"{import_type} imported successfully!",
            "Please restart the application for changes to take effect."
        )
        
        # Reload templates if template manager exists
        if import_templates and hasattr(app, 'template_manager'):
            # Reload templates
            if hasattr(app.template_manager, 'load_templates'):
                app.template_manager.load_templates()
            
            # Reload preferences
            if hasattr(app.template_manager, 'load_preferences'):
                app.template_manager.load_preferences()
            
            # Update UI
            if hasattr(app, 'template_gallery') and hasattr(app.template_gallery, 'populate_gallery'):
                app.template_gallery.populate_gallery(force_refresh=True)

def export_template(app, template_name, include_files=True):
    """
    Export a single template to a package file.
    
    Args:
        app: The main application instance
        template_name: Name of the template to export
        include_files: Whether to include attached files
    """
    if not template_name or not hasattr(app, 'template_manager'):
        QMessageBox.warning(app, "Export Error", "Invalid template or template manager not available.")
        return
    
    # Get the template
    template = app.template_manager.get_template_by_name(template_name)
    if not template:
        QMessageBox.warning(app, "Export Error", f"Template '{template_name}' not found.")
        return
    
    # --- DEBUG LOGGING START ---
    print(f"[EXPORT_DEBUG] Exporting template: {template_name}")
    print(f"[EXPORT_DEBUG] include_files flag: {include_files}")
    # --- DEBUG LOGGING END ---
    
    # Ask user where to save the export file
    safe_name = template_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_path, _ = QFileDialog.getSaveFileName(
        app,
        f"Export Template: {template_name}",
        os.path.expanduser(f"~/Desktop/{safe_name}.zip"),
        "ZIP Files (*.zip)"
    )
    
    if not file_path:
        return  # User canceled
    
    # Add .zip extension if not present
    if not file_path.lower().endswith('.zip'):
        file_path += '.zip'
    
    # Create temporary directory for export files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create metadata file with export information
        metadata = {
            "export_date": datetime.now().isoformat(),
            "app_version": app.app_version if hasattr(app, 'app_version') else "Unknown",
            "template_name": template_name,
            "includes_files": include_files
        }
        
        # --- DEBUG LOGGING START ---
        metadata_path = os.path.join(temp_dir, "template_metadata.json")
        print(f"[EXPORT_DEBUG] Writing metadata to: {metadata_path}")
        # --- DEBUG LOGGING END ---
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Copy template JSON
        template_export_dir = os.path.join(temp_dir, "template")
        os.makedirs(template_export_dir, exist_ok=True)
        
        # --- DEBUG LOGGING START ---
        template_json_path = os.path.join(template_export_dir, "template.json")
        print(f"[EXPORT_DEBUG] Writing template JSON to: {template_json_path}")
        # --- DEBUG LOGGING END ---
        # Save template data to a JSON file
        with open(template_json_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Check for structure data in the template
        folder_structure = template.get("structure")
        if folder_structure:
            print(f"[EXPORT_DEBUG] Found folder structure in template: {template_name}")
            
            # If this template has a structure, ensure it's saved as a custom structure
            structure_name = f"Template_{template_name.replace(' ', '_').replace('/', '-').replace('\\', '-')}"
            if hasattr(app.template_manager, 'save_custom_structure'):
                app.template_manager.save_custom_structure(structure_name, folder_structure)
                print(f"[EXPORT_DEBUG] Saved folder structure as custom structure: {structure_name}")
        
        # Export attached files if requested
        if include_files:
            files_dir = os.path.join(template_export_dir, "files")
            os.makedirs(files_dir, exist_ok=True)
            print(f"[EXPORT_DEBUG] Created files directory: {files_dir}")
            
            # Track file export success
            files_exported = 0
            files_failed = 0
            
            # Create a temporary directory to store files for export
            with tempfile.TemporaryDirectory() as files_temp_dir:
                # Get the file entries from the template
                file_entries = template.get("files", [])
                
                if file_entries and isinstance(file_entries, list):
                    print(f"[EXPORT_DEBUG] Template has {len(file_entries)} file entries in its files array")
                    
                    # Process each file entry
                    for file_entry in file_entries:
                        if not isinstance(file_entry, dict):
                            print(f"[EXPORT_DEBUG] Skipping non-dictionary file entry: {file_entry}")
                            continue
                        
                        # Get file name and folder structure
                        file_name = file_entry.get("file_name", "")
                        folder_in_template = file_entry.get("folder", "")
                        
                        if not file_name:
                            print(f"[EXPORT_DEBUG] Skipping entry without file_name: {file_entry}")
                            continue
                        
                        # Create target directory structure if needed
                        target_dir = files_dir
                        if folder_in_template:
                            target_dir = os.path.join(files_dir, folder_in_template)
                            os.makedirs(target_dir, exist_ok=True)
                        
                        dest_path = os.path.join(target_dir, file_name)
                        export_success = False
                        
                        # PRIORITY 1: Try original path first
                        original_path = file_entry.get("original_path")
                        if original_path and os.path.exists(original_path):
                            try:
                                print(f"[EXPORT_DEBUG] Copying original file: {original_path} -> {dest_path}")
                                shutil.copy2(original_path, dest_path)
                                files_exported += 1
                                export_success = True
                            except Exception as e:
                                print(f"[EXPORT_DEBUG] Error copying original file {original_path}: {e}")
                                # Don't increment files_failed yet, try other paths
                        
                        # PRIORITY 2: If original path fails, try cached_path if available
                        if not export_success:
                            cached_path = file_entry.get("cached_path")
                            if cached_path and os.path.exists(cached_path):
                                try:
                                    print(f"[EXPORT_DEBUG] Copying cached file: {cached_path} -> {dest_path}")
                                    shutil.copy2(cached_path, dest_path)
                                    files_exported += 1
                                    export_success = True
                                except Exception as e:
                                    print(f"[EXPORT_DEBUG] Error copying cached file {cached_path}: {e}")
                                    # Still don't increment files_failed, try the last method
                        
                        # PRIORITY 3: Try the base template path as a last resort
                        if not export_success and template.get("path"):
                            original_path = template.get("path")
                            # If original path is a file, copy it directly
                            if os.path.isfile(original_path):
                                try:
                                    print(f"[EXPORT_DEBUG] Copying template file: {original_path} -> {dest_path}")
                                    shutil.copy2(original_path, dest_path)
                                    files_exported += 1
                                    export_success = True
                                except Exception as e:
                                    print(f"[EXPORT_DEBUG] Error copying template file {original_path}: {e}")
                                    files_failed += 1
                            # If path is a directory, look for the file in it
                            elif os.path.isdir(original_path):
                                potential_file_path = os.path.join(original_path, file_name)
                                if os.path.exists(potential_file_path):
                                    try:
                                        print(f"[EXPORT_DEBUG] Copying file from template directory: {potential_file_path} -> {dest_path}")
                                        shutil.copy2(potential_file_path, dest_path)
                                        files_exported += 1
                                        export_success = True
                                    except Exception as e:
                                        print(f"[EXPORT_DEBUG] Error copying file from template directory {potential_file_path}: {e}")
                                        files_failed += 1
                                else:
                                    print(f"[EXPORT_DEBUG] File not found in template directory: {potential_file_path}")
                                    files_failed += 1
                        elif not export_success:
                            # If we've tried all methods and failed, increment the failure counter
                            files_failed += 1
                            print(f"[EXPORT_DEBUG] Failed to export file: {file_name} - No valid source found")
                
                # FALLBACK: If no files were exported using the files array, try the template path directly
                if files_exported == 0 and template.get("path") and os.path.exists(template.get("path")):
                    original_path = template.get("path")
                    print(f"[EXPORT_DEBUG] No files exported yet. Trying template path: {original_path}")
                    
                    if os.path.isfile(original_path):
                        # Single file template
                        try:
                            dest_path = os.path.join(files_dir, os.path.basename(original_path))
                            print(f"[EXPORT_DEBUG] Copying single template file: {original_path} -> {dest_path}")
                            shutil.copy2(original_path, dest_path)
                            files_exported += 1
                        except Exception as e:
                            print(f"[EXPORT_DEBUG] Error copying template file {original_path}: {e}")
                            files_failed += 1
                    elif os.path.isdir(original_path):
                        # Directory template - copy all contents maintaining folder structure
                        try:
                            for root, dirs, files in os.walk(original_path):
                                for file in files:
                                    src_file = os.path.join(root, file)
                                    # Calculate relative path to maintain folder structure
                                    rel_path = os.path.relpath(src_file, original_path)
                                    dest_file = os.path.join(files_dir, rel_path)
                                    
                                    # Create parent directories if needed
                                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                                    
                                    try:
                                        print(f"[EXPORT_DEBUG] Copying directory file: {src_file} -> {dest_file}")
                                        shutil.copy2(src_file, dest_file)
                                        files_exported += 1
                                    except Exception as e:
                                        print(f"[EXPORT_DEBUG] Error copying directory file {src_file}: {e}")
                                        files_failed += 1
                        except Exception as e:
                            print(f"[EXPORT_DEBUG] Error processing directory {original_path}: {e}")
                
                # LAST RESORT: Try to use the cached files if no files have been exported yet
                if files_exported == 0 and template.get("cached_path"):
                    # Get the base cache directory and template cache directory
                    base_cache_dir = template.get("cached_path")
                    template_name_safe = template_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                    
                    # Construct the template-specific cache directory path
                    if base_cache_dir and os.path.exists(base_cache_dir):
                        template_cache_dir = os.path.join(base_cache_dir, template_name_safe)
                        cached_files_dir = os.path.join(template_cache_dir, "files")
                        
                        print(f"[EXPORT_DEBUG] Trying cache directory: {cached_files_dir}")
                        
                        if os.path.exists(cached_files_dir) and os.path.isdir(cached_files_dir):
                            try:
                                # Walk through the cache directory and copy files maintaining folder structure
                                for root, dirs, files in os.walk(cached_files_dir):
                                    for file in files:
                                        src_path = os.path.join(root, file)
                                        rel_path = os.path.relpath(src_path, cached_files_dir)
                                        dest_path = os.path.join(files_dir, rel_path)
                                        
                                        # Ensure destination directory exists
                                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                        
                                        try:
                                            print(f"[EXPORT_DEBUG] Copying from cache: {src_path} -> {dest_path}")
                                            shutil.copy2(src_path, dest_path)
                                            files_exported += 1
                                        except Exception as e:
                                            print(f"[EXPORT_DEBUG] Error copying cached file {src_path}: {e}")
                                            files_failed += 1
                            except Exception as e:
                                print(f"[EXPORT_DEBUG] Error processing cache directory {cached_files_dir}: {e}")
                        else:
                            print(f"[EXPORT_DEBUG] Cache files directory not found: {cached_files_dir}")
                    else:
                        print(f"[EXPORT_DEBUG] Base cache directory not found or invalid: {base_cache_dir}")
            
            # Summary of file export
            if files_exported > 0:
                print(f"[EXPORT_DEBUG] Successfully exported {files_exported} files (failed: {files_failed})")
            else:
                print(f"[EXPORT_DEBUG] Warning: No files were exported (failed attempts: {files_failed})")
                if not include_files:
                    print(f"[EXPORT_DEBUG] Note: Files were not included because include_files=False")
        else:
            print(f"[EXPORT_DEBUG] include_files is False, skipping file export.")
        
        # --- DEBUG LOGGING: Show contents of temp directory before zipping ---
        print(f"[EXPORT_DEBUG] Contents of temp directory ({temp_dir}) before zipping:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f'{subindent}{f}')
        
        # Create ZIP file with all exported data
        try:
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path_full = os.path.join(root, file)
                        arcname = os.path.relpath(file_path_full, temp_dir)
                        zipf.write(file_path_full, arcname)
            
            QMessageBox.information(
                app, 
                "Export Successful", 
                f"Template '{template_name}' exported successfully!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                app,
                "Export Error",
                f"An error occurred during export: {str(e)}"
            )

def import_template(app, file_path=None):
    """
    Import a template from a package file or directory.
    
    Args:
        app: The main application instance
        file_path: Optional path to zip file or directory to import
    
    Returns:
        True if import was successful, False otherwise
    """
    if not hasattr(app, 'template_manager'):
        QMessageBox.warning(app, "Import Error", "Template manager not available.")
        return False
    
    # Ask user for the import file if not provided
    if not file_path:
        file_path, _ = QFileDialog.getOpenFileName(
            app,
            "Import Template",
            os.path.expanduser("~/Desktop"),
            "ZIP Files (*.zip)"
        )
    
    if not file_path:
        return False  # User canceled
    
    # Store the source zip file path for later reference
    source_zip_path = os.path.abspath(file_path)
    print(f"[IMPORT_DEBUG] Source ZIP file path: {source_zip_path}")
    
    # Create temporary directory for extracted files
    with tempfile.TemporaryDirectory() as temp_dir:
        # --- DEBUG LOGGING START ---
        print(f"[IMPORT_DEBUG] Created temporary directory for extraction: {temp_dir}")
        # --- DEBUG LOGGING END ---
        
        # Extract ZIP file
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                print(f"[IMPORT_DEBUG] Attempting to extract ZIP file: {file_path}") # DEBUG
                zipf.extractall(temp_dir)
                print(f"[IMPORT_DEBUG] ZIP file extracted successfully.") # DEBUG
        except Exception as e:
            # --- DEBUG LOGGING START ---
            print(f"[IMPORT_DEBUG] CRITICAL ERROR during ZIP extraction: {str(e)}")
            import traceback
            traceback.print_exc()
            # --- DEBUG LOGGING END ---
            QMessageBox.critical(
                app,
                "Import Error",
                f"Failed to extract template file: {str(e)}"
            )
            return False
            
        # --- DEBUG LOGGING START ---
        print(f"[IMPORT_DEBUG] Contents of temp directory ({temp_dir}) after extraction:")
        try:
            for root, dirs, files in os.walk(temp_dir):
                level = root.replace(temp_dir, '').count(os.sep)
                indent = ' ' * 4 * (level)
                print(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 4 * (level + 1)
                for f in files:
                    print(f'{subindent}{f}')
        except Exception as walk_e:
             print(f"[IMPORT_DEBUG] ERROR walking temp directory: {walk_e}")       
        # --- DEBUG LOGGING END ---
        
        # Check if this is a template package or a full export
        template_metadata_path = os.path.join(temp_dir, "template_metadata.json")
        export_metadata_path = os.path.join(temp_dir, "export_metadata.json")
        
        # --- DEBUG LOGGING START ---
        print(f"[IMPORT_DEBUG] Checking for template metadata at: {template_metadata_path}")
        # --- DEBUG LOGGING END ---
        is_template_package = os.path.exists(template_metadata_path)
        # --- DEBUG LOGGING START ---
        print(f"[IMPORT_DEBUG] Result of os.path.exists(template_metadata_path): {is_template_package}")
        # --- DEBUG LOGGING END ---
        
        # --- DEBUG LOGGING START ---
        print(f"[IMPORT_DEBUG] Checking for export metadata at: {export_metadata_path}")
        # --- DEBUG LOGGING END ---
        is_full_export = os.path.exists(export_metadata_path)
        # --- DEBUG LOGGING START ---
        print(f"[IMPORT_DEBUG] Result of os.path.exists(export_metadata_path): {is_full_export}")
        # --- DEBUG LOGGING END ---
        
        if not is_template_package and not is_full_export:
            # --- DEBUG LOGGING START ---
            print(f"[IMPORT_DEBUG] Neither metadata file found. Raising error.")
            # --- DEBUG LOGGING END ---
            QMessageBox.warning(
                app,
                "Import Error",
                "Invalid template file. Metadata not found."
            )
            return False
        
        # Handle template package
        if is_template_package:
            # Load metadata
            try:
                with open(template_metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                QMessageBox.critical(
                    app,
                    "Import Error",
                    f"Failed to read template metadata: {str(e)}"
                )
                return False
            
            # Get template data
            template_json_path = os.path.join(temp_dir, "template", "template.json")
            if not os.path.exists(template_json_path):
                QMessageBox.warning(
                    app,
                    "Import Error",
                    "Invalid template file. Template data not found."
                )
                return False
            
            # Load template data
            try:
                with open(template_json_path, 'r') as f:
                    template_data = json.load(f)
            except Exception as e:
                QMessageBox.critical(
                    app,
                    "Import Error",
                    f"Failed to read template data: {str(e)}"
                )
                return False
            
            # Get template name and check if it already exists
            template_name = template_data.get("name", "Imported Template")
            if app.template_manager.get_template_by_name(template_name):
                # Ask user if they want to overwrite using our styled message box
                result = StyledMessageBox.show_question(
                    app,
                    "Template Exists",
                    f"A template named '{template_name}' already exists.",
                    "Do you want to overwrite it with the imported template?"
                )
                
                if result != QMessageBox.Yes:
                    # Ask for a new name using our styled input dialog
                    new_name, ok = StyledInputDialog.get_text(
                        app,
                        "Rename Template",
                        "Enter a new name for the imported template:",
                        f"{template_name} (Imported)"
                    )
                    
                    if not ok or not new_name:
                        return False  # User canceled
                    
                    template_name = new_name
                    template_data["name"] = template_name
            
            # Process template files and structures
            template_files_dir = os.path.join(temp_dir, "template", "files")
            
            # Check for structure data in the template
            folder_structure = template_data.get("structure")
            if folder_structure:
                print(f"[IMPORT_DEBUG] Found folder structure in template: {template_name}")
                
                # If this template has a structure, ensure it's saved as a custom structure
                structure_name = f"Template_{template_name.replace(' ', '_').replace('/', '-').replace('\\', '-')}"
                if hasattr(app.template_manager, 'save_custom_structure'):
                    try:
                        app.template_manager.save_custom_structure(structure_name, folder_structure)
                        template_data["structure_name"] = structure_name
                        print(f"[IMPORT_DEBUG] Saved imported folder structure as custom structure: {structure_name}")
                    except Exception as e:
                        print(f"[IMPORT_DEBUG] Error saving structure: {e}")
            
            # Process attached files if included
            if metadata.get("includes_files", False) and os.path.exists(template_files_dir):
                print(f"[IMPORT_DEBUG] Processing included files from {template_files_dir}")
                
                # Get the cache directory path from the template manager
                template_manager = app.template_manager
                
                # Clean template name for file system use
                safe_name = template_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                
                # Determine the cache directory based on the template manager's paths
                cache_base_dir = None
                if hasattr(template_manager, 'paths') and template_manager.paths.get("cache_dir"):
                    cache_base_dir = template_manager.paths.get("cache_dir")
                else:
                    # If no cache_dir in paths, try to use template_manager.file_cache_manager
                    if hasattr(template_manager, 'file_cache_manager') and hasattr(template_manager.file_cache_manager, 'cache_dir'):
                        cache_base_dir = template_manager.file_cache_manager.cache_dir
                
                if not cache_base_dir:
                    print(f"[IMPORT_DEBUG] Warning: No cache directory found. Using templates dir as fallback.")
                    templates_dir = template_manager.paths.get("templates_dir")
                    cache_base_dir = os.path.join(templates_dir, "cache")
                    os.makedirs(cache_base_dir, exist_ok=True)
                
                # Create template-specific cache directory
                template_cache_dir = os.path.join(cache_base_dir, safe_name)
                os.makedirs(template_cache_dir, exist_ok=True)
                print(f"[IMPORT_DEBUG] Template cache directory: {template_cache_dir}")
                
                # Initialize files array for the template
                files_array = []
                files_exported = 0
                files_failed = 0
                
                # Dictionary to track imported files by relative path
                # This helps prevent duplicates in the files array
                imported_files = {}
                
                # Walk the template_files_dir to collect all files
                for root, dirs, files in os.walk(template_files_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        # Get the relative path from template_files_dir
                        rel_path = os.path.relpath(src_path, template_files_dir)
                        
                        # Skip if we've already processed this relative path
                        if rel_path in imported_files:
                            print(f"[IMPORT_DEBUG] Skipping duplicate file: {rel_path}")
                            continue
                        
                        # Determine the folder path for file_info
                        folder_path = os.path.dirname(rel_path)
                        if folder_path and not folder_path.endswith('/'):
                            folder_path += '/'
                        
                        # Create cache directory structure if needed
                        cache_file_dir = os.path.join(template_cache_dir, os.path.dirname(rel_path))
                        os.makedirs(cache_file_dir, exist_ok=True)
                        
                        # Copy file to cache
                        try:
                            # Determine the full path for the target file within the hierarchical structure
                            rel_path = os.path.relpath(src_path, template_files_dir)
                            folder_path = os.path.dirname(rel_path)
                            
                            # Create target directory in cache structure
                            cache_file_dir = os.path.join(template_cache_dir, folder_path)
                            os.makedirs(cache_file_dir, exist_ok=True)
                            
                            # Set path for cached file in hierarchical structure
                            cache_file_path = os.path.join(cache_file_dir, os.path.basename(rel_path))
                            
                            print(f"[IMPORT_DEBUG] Copying file to cache: {src_path} -> {cache_file_path}")
                            shutil.copy2(src_path, cache_file_path)
                            
                            # Create file info for files_array - use proper original path
                            # Check if this file from structure has a matching original_path 
                            original_file_path = ""
                            
                            # Extract the relative path within the template structure
                            rel_path_in_structure = os.path.join(folder_path, os.path.basename(rel_path)) if folder_path else rel_path
                            
                            # Look in the structure to find the true original path of this file
                            structure = template_data.get("structure", [])
                            
                            # Function to search the structure recursively for matching file path
                            def find_original_path_in_structure(items, file_rel_path):
                                if not items:
                                    return None
                                    
                                for item in items:
                                    if item.get('type') == 'folder':
                                        folder_name = item.get('name', '')
                                        children = item.get('children', [])
                                        
                                        # Check if this is the folder containing our file
                                        if folder_name and file_rel_path.startswith(folder_name + '/'):
                                            # Look for file in this folder's children
                                            file_name = os.path.basename(file_rel_path)
                                            for child in children:
                                                if child.get('type') == 'file' and child.get('name') == file_name:
                                                    # Found the file - get its original path
                                                    return child.get('original_path')
                                            
                                            # If not found in direct children, recurse deeper
                                            result = find_original_path_in_structure(children, file_rel_path[len(folder_name)+1:])
                                            if result:
                                                return result
                                                
                                    elif item.get('type') == 'file':
                                        # Handle top-level files
                                        if item.get('name') == os.path.basename(file_rel_path):
                                            return item.get('original_path')
                                            
                                return None
                            
                            # Try to find the original path in the structure
                            true_original_path = find_original_path_in_structure(structure, rel_path_in_structure)
                            
                            # Use the found original path if available, otherwise fall back to our sources
                            if true_original_path:
                                original_file_path = true_original_path
                                print(f"[IMPORT_DEBUG] Found true original path in structure: {original_file_path}")
                            elif src_path.startswith(temp_dir):
                                # This is a file from a zip import but we couldn't find original in structure
                                rel_path_in_zip = os.path.relpath(src_path, temp_dir)
                                original_file_path = f"Imported from: {source_zip_path}:{rel_path_in_zip}"
                                print(f"[IMPORT_DEBUG] Using fallback ZIP source path: {original_file_path}")
                            else:
                                # This is a direct file, use actual path
                                original_file_path = src_path
                                print(f"[IMPORT_DEBUG] Using direct file path: {original_file_path}")
                            
                            file_info = {
                                'file_name': os.path.basename(rel_path),
                                'folder': folder_path,
                                'original_path': original_file_path,  # Use true original path from structure when available
                                'cached_path': cache_file_path,  # Store path to file in cache
                                'file_type': os.path.splitext(rel_path)[1][1:] if os.path.splitext(rel_path)[1] else '',
                                'size': os.path.getsize(src_path),
                                'is_binary': src_path.endswith(('.bin', '.exe', '.dll', '.so', '.dylib', '.prproj', '.aep')),
                                'path': normalize_path_for_storage(rel_path)  # Store relative path within template
                            }
                            
                            # Check if this file should be registered for automatic renaming
                            # Files in the structure with rename_flag and uses_project_name set to True should be renamed
                            if folder_structure:
                                # Try to find this file in the structure to see if it's set for renaming
                                try:
                                    # Check if file should have a rename flag by examining the structure
                                    file_path = file_info.get('path', '')
                                    if file_path:
                                        # Make file path matching consistent
                                        file_path = normalize_path_for_storage(file_path)
                                        file_name = os.path.basename(file_path)
                                        folder_path = os.path.dirname(file_path)
                                        
                                        # Look through the structure to find a matching file and check rename flags
                                        def find_in_structure(items, folder_path, file_name):
                                            if not items:
                                                return False
                                                
                                            for item in items:
                                                if item.get('type') == 'folder':
                                                    # Current folder path
                                                    current_folder = item.get('name', '')
                                                    
                                                    # Check if this folder has the file we're looking for
                                                    if 'children' in item:
                                                        # For files directly in this folder
                                                        if not folder_path or folder_path == current_folder:
                                                            for child in item.get('children', []):
                                                                if child.get('type') == 'file' and child.get('name') == file_name:
                                                                    # Found a match - update file_info with rename flags
                                                                    file_info['rename_flag'] = child.get('rename_flag', False)
                                                                    file_info['uses_project_name'] = child.get('uses_project_name', False)
                                                                    return True
                                                        
                                                        # Look deeper in the structure
                                                        remaining_path = folder_path
                                                        if folder_path.startswith(current_folder + '/'):
                                                            remaining_path = folder_path[len(current_folder) + 1:]
                                                        
                                                        # Recursive search in children
                                                        if find_in_structure(item.get('children', []), remaining_path, file_name):
                                                            return True
                                                
                                                elif item.get('type') == 'file' and item.get('name') == file_name:
                                                    # Direct match (top-level file)
                                                    file_info['rename_flag'] = item.get('rename_flag', False)
                                                    file_info['uses_project_name'] = item.get('uses_project_name', False)
                                                    return True
                                                    
                                            return False
                                            
                                        # Call the inner function to find matching file
                                        find_in_structure(folder_structure, folder_path, file_name)
                                except Exception as e:
                                    print(f"[IMPORT_DEBUG] Warning: Could not check rename flag: {e}")
                                    # Continue processing the file even if rename flag check fails
                            
                            # Add to files_array and track in imported_files
                            files_array.append(file_info)
                            imported_files[rel_path] = file_info
                            files_exported += 1
                            
                        except Exception as e:
                            print(f"[IMPORT_DEBUG] Error copying file to cache: {e}")
                            files_failed += 1
                
                # Update the template data with files array and cache info
                template_data["files"] = files_array
                template_data["cached_path"] = cache_base_dir
                print(f"[IMPORT_DEBUG] Files processed: {files_exported} successful, {files_failed} failed")
            else:
                print(f"[IMPORT_DEBUG] No files included in template or files directory not found")
            
            # Import the template - use UIOperations.import_template when available
            success = False
            if hasattr(app, 'ui_operations') and hasattr(app.ui_operations, 'import_template'):
                # Use the dedicated import_template method
                print(f"[IMPORT_DEBUG] Importing template '{template_name}' using ui_operations.import_template")
                success = app.ui_operations.import_template(template_data)
            elif hasattr(app.template_manager.template_io, 'save_template'):
                # Use the direct save_template method that accepts a dict
                print(f"[IMPORT_DEBUG] Saving template '{template_name}' using template_io.save_template")
                success = app.template_manager.template_io.save_template(template_data)
            else:
                # Last resort - use template_manager.save_template
                print(f"[IMPORT_DEBUG] Saving template '{template_name}' using template_manager.save_template")
                success, _ = app.template_manager.save_template(template_data)
            
            if success:
                QMessageBox.information(
                    app,
                    "Import Successful",
                    f"Template '{template_name}' imported successfully!"
                )
                
                # The ui_operations.import_template method already handles UI refresh
                # Only refresh UI if we used one of the fallback methods
                if not hasattr(app, 'ui_operations') or not hasattr(app.ui_operations, 'import_template'):
                    # Update UI - force refresh
                    if hasattr(app, 'template_gallery') and hasattr(app.template_gallery, 'populate_gallery'):
                        print(f"[IMPORT_DEBUG] Refreshing template gallery UI")
                        app.template_gallery.populate_gallery(force_refresh=True)
                        
                        # Emit template updated signal if available
                        if hasattr(app, 'template_updated') and app.template_updated is not None:
                            print(f"[IMPORT_DEBUG] Emitting template_updated signal")
                            app.template_updated.emit()
            else:
                QMessageBox.warning(
                    app,
                    "Import Error",
                    f"Failed to import template '{template_name}'."
                )
            
        # Handle full export package that might contain templates
        elif is_full_export:
            # Load metadata
            try:
                with open(export_metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                QMessageBox.critical(
                    app,
                    "Import Error",
                    f"Failed to read export metadata: {str(e)}"
                )
                return False
            
            # Check if package includes templates
            if not metadata.get("includes_templates", False):
                QMessageBox.warning(
                    app,
                    "Import Error",
                    "This package does not contain templates."
                )
                return False
            
            # Call the regular import package function with templates only
            import_package(app, import_settings=False, import_templates=True) 

    @staticmethod
    def _check_file_for_rename_flag(structure, file_info):
        """
        Check if a file should be marked for renaming based on the structure.
        Updates file_info in place if the file should be renamed.
        
        Args:
            structure (list): The folder structure containing file information
            file_info (dict): The file info dictionary to update
            
        Returns:
            bool: True if file was found and updated, False otherwise
        """
        file_path = file_info.get('path', '')
        if not file_path:
            return False
            
        # Make file path matching consistent
        file_path = normalize_path_for_storage(file_path)
        file_name = os.path.basename(file_path)
        folder_path = os.path.dirname(file_path)
        
        # Recursively search the structure for matching file
        found = ImportExportManager._find_file_in_structure(structure, folder_path, file_name, file_info)
        return found
        
    @staticmethod
    def _find_file_in_structure(items, folder_path, file_name, file_info):
        """
        Recursively search the structure for a file and update file_info if found.
        
        Args:
            items (list): List of structure items to search
            folder_path (str): Relative folder path to match
            file_name (str): File name to match
            file_info (dict): File info to update if match found
            
        Returns:
            bool: True if file was found and updated, False otherwise
        """
        if not items:
            return False
            
        for item in items:
            if item.get('type') == 'folder':
                # Current folder path
                current_folder = item.get('name', '')
                
                # Check if this folder has the file we're looking for
                if 'children' in item:
                    # For files directly in this folder
                    if not folder_path or folder_path == current_folder:
                        for child in item.get('children', []):
                            if child.get('type') == 'file' and child.get('name') == file_name:
                                # Found a match - update file_info with rename flags
                                file_info['rename_flag'] = child.get('rename_flag', False)
                                file_info['uses_project_name'] = child.get('uses_project_name', False)
                                return True
                    
                    # Look deeper in the structure, adjusting the folder path as needed
                    remaining_path = folder_path
                    if folder_path.startswith(current_folder + '/'):
                        remaining_path = folder_path[len(current_folder) + 1:]
                    
                    # Recursive search in children
                    if ImportExportManager._find_file_in_structure(item.get('children', []), remaining_path, file_name, file_info):
                        return True
            
            elif item.get('type') == 'file' and item.get('name') == file_name:
                # Direct match (top-level file)
                file_info['rename_flag'] = item.get('rename_flag', False)
                file_info['uses_project_name'] = item.get('uses_project_name', False)
                return True
                
        return False 