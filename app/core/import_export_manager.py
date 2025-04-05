#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import shutil
import zipfile
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox
from app.constants import APP_NAME # Import the APP_NAME constant

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
        if dialog.exec_() != QDialog.Accepted:
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
        
        # Success message
        QMessageBox.information(
            app,
            "Import Successful",
            f"{import_type} imported successfully!\nPlease restart the application for changes to take effect."
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
    print(f"[EXPORT_DEBUG] Template data: {json.dumps(template, indent=2)}")
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
        
        # Check if this template has a structure
        structure_name = f"Template_{template_name.replace(' ', '_').replace('/', '-').replace('\\', '-')}"
        folder_structure = template.get("structure")
        
        # If no structure in template, try to get it from custom structures
        if not folder_structure and hasattr(app.template_manager, 'get_custom_structure'):
            folder_structure = app.template_manager.get_custom_structure(structure_name)
            
            # If a structure was found, add it to the template data for export
            if folder_structure:
                template["structure"] = folder_structure
                print(f"Added structure from custom structures to template export: {structure_name}")
                
                # Update the template JSON with the structure
                with open(os.path.join(template_export_dir, "template.json"), 'w') as f:
                    json.dump(template, f, indent=2)
        
        # Export attached files if requested
        if include_files:
            files_dir = os.path.join(template_export_dir, "files")
            os.makedirs(files_dir, exist_ok=True)
            # --- DEBUG LOGGING START ---
            print(f"[EXPORT_DEBUG] Created files directory: {files_dir}")
            # --- DEBUG LOGGING END ---
            
            # First check if we have cached files
            has_cached_files = False
            cached_path = template.get("cached_path")
            original_path_from_template = template.get("path")
            # --- DEBUG LOGGING START ---
            print(f"[EXPORT_DEBUG] Checking for cached files. Cached path from template: {cached_path}")
            # --- DEBUG LOGGING END ---
            
            if cached_path and os.path.exists(cached_path):
                try:
                    # --- DEBUG LOGGING START ---
                    print(f"[EXPORT_DEBUG] Cached path exists: {cached_path}")
                    # --- DEBUG LOGGING END ---
                    # Use cached files if available
                    if os.path.isdir(cached_path) and os.listdir(cached_path):  # Check if directory and not empty
                        has_cached_files = True
                        print(f"[EXPORT_DEBUG] Using cached files from: {cached_path}")
                        
                        # --- CORRECTED: Define source as the 'files' subdirectory within the cache ---
                        cached_files_source_dir = os.path.join(cached_path, 'files')
                        
                        # Check if the actual files subdirectory exists
                        if os.path.isdir(cached_files_source_dir):
                            print(f"[EXPORT_DEBUG] Copying contents from: {cached_files_source_dir}")
                            # Copy all cached files from the 'files' subdirectory
                            for item in os.listdir(cached_files_source_dir):
                                # --- CORRECTED: Source path is now inside cache's 'files' dir ---
                                src_path = os.path.join(cached_files_source_dir, item)
                                dst_path = os.path.join(files_dir, item) # Destination remains the temp 'files' dir
                                
                                try:
                                    if os.path.isfile(src_path):
                                        print(f"[EXPORT_DEBUG] Copying cached file: {src_path} -> {dst_path}")
                                        shutil.copy2(src_path, dst_path)
                                    elif os.path.isdir(src_path):
                                        print(f"[EXPORT_DEBUG] Copying cached directory: {src_path} -> {dst_path}")
                                        # --- CORRECTED: Ensure destination doesn't exist for copytree ---
                                        if os.path.exists(dst_path):
                                            shutil.rmtree(dst_path)
                                        shutil.copytree(src_path, dst_path)
                                except Exception as copy_error:
                                    print(f"[EXPORT_DEBUG] ERROR copying cached item {item}: {copy_error}")
                        else:
                             print(f"[EXPORT_DEBUG] WARN: 'files' subdirectory not found within cache path: {cached_files_source_dir}")
                             has_cached_files = False # Mark as failed if files dir is missing
                    else:
                        print(f"[EXPORT_DEBUG] Cached path is not a directory or is empty: {cached_path}")
                except Exception as e:
                    print(f"[EXPORT_DEBUG] Error processing cached files from {cached_path}: {e}")
                    has_cached_files = False
            else:
                print(f"[EXPORT_DEBUG] Cached path not found or doesn't exist: {cached_path}")
            
            # Fall back to original path if needed
            # --- DEBUG LOGGING START ---
            print(f"[EXPORT_DEBUG] Checking fallback path. has_cached_files: {has_cached_files}, original_path: {original_path_from_template}")
            # --- DEBUG LOGGING END ---
            if not has_cached_files and original_path_from_template and os.path.exists(original_path_from_template):
                original_path = original_path_from_template
                print(f"[EXPORT_DEBUG] Using original files (fallback) from: {original_path}")
                
                # Check if path is a file or directory
                if os.path.isfile(original_path):
                    try:
                        # Single file template
                        dst_path = os.path.join(files_dir, os.path.basename(original_path))
                        print(f"[EXPORT_DEBUG] Copying original file: {original_path} -> {dst_path}")
                        shutil.copy2(original_path, dst_path)
                    except Exception as copy_error:
                        print(f"[EXPORT_DEBUG] ERROR copying original file {original_path}: {copy_error}")
                elif os.path.isdir(original_path):
                    # Directory template - copy all contents
                    try:
                        for item in os.listdir(original_path):
                            src_path = os.path.join(original_path, item)
                            dst_path = os.path.join(files_dir, item)
                            
                            try:
                                if os.path.isfile(src_path):
                                    print(f"[EXPORT_DEBUG] Copying original dir item (file): {src_path} -> {dst_path}")
                                    shutil.copy2(src_path, dst_path)
                                elif os.path.isdir(src_path):
                                    print(f"[EXPORT_DEBUG] Copying original dir item (dir): {src_path} -> {dst_path}")
                                    shutil.copytree(src_path, dst_path)
                            except Exception as copy_error:
                                print(f"[EXPORT_DEBUG] ERROR copying original directory item {item}: {copy_error}")
                    except Exception as list_error:
                         print(f"[EXPORT_DEBUG] ERROR listing original directory {original_path}: {list_error}")
            else:
                 print(f"[EXPORT_DEBUG] Not falling back to original path.")
        else:
             print(f"[EXPORT_DEBUG] include_files is False, skipping file export.")
        
        # --- DEBUG LOGGING START ---
        print(f"[EXPORT_DEBUG] Contents of temp directory ({temp_dir}) before zipping:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f'{subindent}{f}')
        # --- DEBUG LOGGING END ---
        
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
    Import a template from a package file.
    
    Args:
        app: The main application instance
        file_path: Path to the template package file (optional)
    """
    if not hasattr(app, 'template_manager'):
        QMessageBox.warning(app, "Import Error", "Template manager not available.")
        return
    
    # Ask user for the import file if not provided
    if not file_path:
        file_path, _ = QFileDialog.getOpenFileName(
            app,
            "Import Template",
            os.path.expanduser("~/Desktop"),
            "ZIP Files (*.zip)"
        )
    
    if not file_path:
        return  # User canceled
    
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
            return
            
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
            return
        
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
                return
            
            # Get template data
            template_json_path = os.path.join(temp_dir, "template", "template.json")
            if not os.path.exists(template_json_path):
                QMessageBox.warning(
                    app,
                    "Import Error",
                    "Invalid template file. Template data not found."
                )
                return
            
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
                return
            
            # Get template name and check if it already exists
            template_name = template_data.get("name", "Imported Template")
            if app.template_manager.get_template_by_name(template_name):
                # Ask user if they want to overwrite
                msgbox = QMessageBox(app)
                msgbox.setWindowTitle("Template Exists")
                msgbox.setText(f"A template named '{template_name}' already exists.")
                msgbox.setInformativeText("Do you want to overwrite it with the imported template?")
                msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgbox.setDefaultButton(QMessageBox.No)
                
                if msgbox.exec_() != QMessageBox.Yes:
                    # Ask for a new name
                    from PyQt5.QtWidgets import QInputDialog
                    new_name, ok = QInputDialog.getText(
                        app,
                        "Rename Template",
                        "Enter a new name for the imported template:",
                        text=f"{template_name} (Imported)"
                    )
                    
                    if not ok or not new_name:
                        return  # User canceled
                    
                    template_name = new_name
                    template_data["name"] = template_name
            
            # Process template files and structures
            template_files_dir = os.path.join(temp_dir, "template", "files")
            
            # Check for structure data in the template
            folder_structure = template_data.get("structure")
            if folder_structure:
                print(f"Found folder structure in template: {template_name}")
                
                # If this template has a structure, ensure it's saved as a custom structure
                structure_name = f"Template_{template_name.replace(' ', '_').replace('/', '-').replace('\\', '-')}"
                if hasattr(app.template_manager, 'save_custom_structure'):
                    app.template_manager.save_custom_structure(structure_name, folder_structure)
                    print(f"Saved imported folder structure as custom structure: {structure_name}")
                
            # Process attached files if included
            if metadata.get("includes_files", False) and os.path.exists(template_files_dir):
                # Create a directory for the imported template files
                templates_dir = app.template_manager.paths.get("templates_dir")
                safe_name = template_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                
                # Create cache directory
                cache_dir = os.path.join(templates_dir, "cache", safe_name)
                os.makedirs(cache_dir, exist_ok=True)
                
                # Create the import directory (temporary location for import)
                import_dir = os.path.join(templates_dir, f"imported_{safe_name}")
                
                # Ensure directory is unique
                counter = 1
                original_import_dir = import_dir
                while os.path.exists(import_dir):
                    import_dir = f"{original_import_dir}_{counter}"
                    counter += 1
                
                # Create the directory and copy files
                os.makedirs(import_dir, exist_ok=True)
                
                # Copy all files from the template package
                for item in os.listdir(template_files_dir):
                    src_path = os.path.join(template_files_dir, item)
                    dst_path = os.path.join(import_dir, item)
                    cache_path = os.path.join(cache_dir, item)
                    
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dst_path)
                        # Also copy to cache
                        shutil.copy2(src_path, cache_path)
                    elif os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                        # Also copy to cache
                        if os.path.exists(cache_path):
                            shutil.rmtree(cache_path)
                        shutil.copytree(src_path, cache_path)
                
                # Update template path and cached path
                template_data["path"] = import_dir
                template_data["cached_path"] = cache_dir
            
            # Import the template
            success = app.template_manager.update_template(template_data)
            
            if success:
                QMessageBox.information(
                    app,
                    "Import Successful",
                    f"Template '{template_name}' imported successfully!"
                )
                
                # Update UI
                if hasattr(app, 'template_gallery') and hasattr(app.template_gallery, 'populate_gallery'):
                    app.template_gallery.populate_gallery(force_refresh=True)
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
                return
            
            # Check if package includes templates
            if not metadata.get("includes_templates", False):
                QMessageBox.warning(
                    app,
                    "Import Error",
                    "This package does not contain templates."
                )
                return
            
            # Call the regular import package function with templates only
            import_package(app, import_settings=False, import_templates=True) 