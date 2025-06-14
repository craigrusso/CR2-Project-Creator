#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Batch project creation management component
"""

import re
from PyQt6.QtWidgets import QMessageBox


class BatchManager:
    """Handles batch project creation operations"""
    
    def __init__(self, app_instance):
        """Initialize the batch manager"""
        self.app = app_instance
    
    def process_batch_projects(self):
        """Process batch project creation from the text input"""
        # Get text from batch input
        if not hasattr(self.app, 'batch_text_edit'):
            QMessageBox.warning(self.app, "Error", "Batch text input not found")
            return
            
        batch_text = self.app.batch_text_edit.toPlainText().strip()
        
        if not batch_text:
            QMessageBox.information(self.app, "No Projects", "Please enter project names in the text area.")
            return
        
        # Parse project names
        project_names = self._parse_project_names(batch_text)
        
        if not project_names:
            QMessageBox.warning(self.app, "Invalid Input", "No valid project names found.")
            return
        
        # Get current template
        current_template = self._get_current_template()
        if not current_template:
            QMessageBox.warning(self.app, "No Template", "Please select a template before creating projects.")
            return
        
        # Check for custom options
        if current_template:
            self.app.check_template_for_custom_options(current_template)
            
            # If custom options are required, check if user has made valid selections
            if (hasattr(self.app, 'custom_options_widget') and 
                self.app.custom_options_widget and 
                self.app.custom_options_widget.is_visible and 
                len(self.app.custom_options_widget.combo_widgets) > 0):
                
                # Check if user has made valid selections for all required custom options
                selected_values = self.app.custom_options_widget.get_selected_values()
                has_valid_selections = True
                
                # Check each combo widget to ensure a valid selection is made
                for combo_key, combo_widget in self.app.custom_options_widget.combo_widgets.items():
                    current_text = combo_widget.currentText()
                    # Check if selection is empty or placeholder text
                    if not current_text or current_text.startswith("Select ") or current_text == "":
                        has_valid_selections = False
                        break
                
                if not has_valid_selections:
                    # Custom options are required but user hasn't made selections
                    QMessageBox.information(
                        self.app, 
                        "Custom Options Required", 
                        "This template requires custom options. Please make your selections below and then try creating projects again."
                    )
                    return
                
                print(f"DEBUG: Custom options validated successfully: {selected_values}")
        
        # Generate final list with sequences if enabled
        final_projects = []
        
        if hasattr(self.app, 'enable_versioning') and self.app.enable_versioning.isChecked():
            # Generate sequences for each base project name
            for base_name in project_names:
                sequences = self._generate_sequence_names(base_name)
                final_projects.extend(sequences)
        else:
            # Use original names
            final_projects = project_names
        
        # Confirm with user if many projects
        if len(final_projects) > 10:
            reply = QMessageBox.question(
                self.app,
                "Confirm Batch Creation",
                f"You are about to create {len(final_projects)} projects. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Proceed with enhanced batch creation
        self._handle_enhanced_batch_creation(final_projects)
    
    def _parse_project_names(self, text):
        """Parse project names from text input"""
        # Split by newlines, commas, or semicolons and clean up
        project_names = re.split(r'[\n,;]+', text)
        project_names = [name.strip() for name in project_names if name.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in project_names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        
        return unique_names
    
    def _get_current_template(self):
        """Get the currently selected template"""
        if hasattr(self.app, 'template_gallery'):
            selected_templates = self.app.template_gallery.get_selected_templates()
            if selected_templates:
                template_name = selected_templates[0]
                
                # Get template data
                template_data = self.app.template_manager.get_template_by_name(template_name)
                if template_data:
                    return template_data
        
        return None
    
    def _generate_sequence_names(self, base_name):
        """Generate sequence variations for a base project name"""
        if not hasattr(self.app, 'sequence_type'):
            return [base_name]
        
        sequence_type = self.app.sequence_type.currentText()
        position = self.app.name_position.currentText() if hasattr(self.app, 'name_position') else "Suffix"
        
        sequences = []
        
        if sequence_type == "Date Sequences":
            sequences = self._generate_date_sequences(base_name, position)
        elif sequence_type == "Version Numbers":
            sequences = self._generate_version_sequences(base_name, position)
        elif sequence_type == "Sequential Numbers":
            sequences = self._generate_sequential_numbers(base_name, position)
        else:
            sequences = [base_name]
        
        return sequences
    
    def _generate_date_sequences(self, base_name, position):
        """Generate date-based sequences"""
        sequences = []
        
        if hasattr(self.app, 'start_date') and hasattr(self.app, 'project_count'):
            from PyQt6.QtCore import QDate
            start_date = self.app.start_date.date()
            count = self.app.project_count.value()
            interval = self.app.date_interval.value()
            
            for i in range(count):
                current_date = start_date.addDays(i * interval)
                date_str = current_date.toString("yyyyMMdd")
                
                if position == "Prefix":
                    project_name = f"{date_str}_{base_name}"
                else:  # Suffix
                    project_name = f"{base_name}_{date_str}"
                
                sequences.append(project_name)
        else:
            # Fallback if UI elements not available
            sequences = [base_name]
        
        return sequences
    
    def _generate_version_sequences(self, base_name, position):
        """Generate version number sequences"""
        sequences = []
        
        if hasattr(self.app, 'version_count'):
            count = self.app.version_count.value()
            
            for i in range(1, count + 1):
                version_str = f"v{i:02d}"
                
                if position == "Prefix":
                    project_name = f"{version_str}_{base_name}"
                else:  # Suffix
                    project_name = f"{base_name}_{version_str}"
                
                sequences.append(project_name)
        else:
            sequences = [base_name]
        
        return sequences
    
    def _generate_sequential_numbers(self, base_name, position):
        """Generate sequential number sequences"""
        sequences = []
        
        if hasattr(self.app, 'sequence_count'):
            count = self.app.sequence_count.value()
            
            for i in range(1, count + 1):
                number_str = f"{i:03d}"
                
                if position == "Prefix":
                    project_name = f"{number_str}_{base_name}"
                else:  # Suffix
                    project_name = f"{base_name}_{number_str}"
                
                sequences.append(project_name)
        else:
            sequences = [base_name]
        
        return sequences
    
    def _handle_enhanced_batch_creation(self, project_names):
        """Handle the enhanced batch creation process"""
        # Get output directory
        output_dir = self.app.get_current_output_dir()
        if not output_dir:
            QMessageBox.warning(self.app, "No Output Directory", "Please select an output directory.")
            return
        
        # Get template data
        current_template = self._get_current_template()
        if not current_template:
            QMessageBox.warning(self.app, "No Template", "Please select a template.")
            return
        
        # Show progress and create projects
        self.app.status_manager.show_loading_message(f"Creating {len(project_names)} projects...")
        
        try:
            # Use the project builder for batch creation
            results = self.app.project_builder.batch_create_projects(
                project_names=project_names,
                template_name=current_template.get('name'),
                structure_name=None,
                output_dir=output_dir,
                template_data=current_template
            )
            
            # Store results for later viewing
            self.app.batch_results = results
            
            # Show status
            successful_count = results.get('successful_count', 0)
            total_count = results.get('total_count', len(project_names))
            
            self.app.status_manager.show_batch_creation_status(successful_count, total_count)
            
            # Show results dialog
            from app.dialogs.dialog_windows_pyqt import show_batch_results
            show_batch_results(self.app, results)
            
            # Clear the text input on success
            if successful_count > 0:
                self.app.batch_text_edit.clear()
                
                # Reset custom options widget
                if hasattr(self.app, 'reset_custom_options_widget'):
                    self.app.reset_custom_options_widget()
            
        except Exception as e:
            error_msg = f"Error during batch creation: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.app.status_manager.show_error_message(error_msg)
            QMessageBox.critical(self.app, "Batch Creation Error", error_msg) 