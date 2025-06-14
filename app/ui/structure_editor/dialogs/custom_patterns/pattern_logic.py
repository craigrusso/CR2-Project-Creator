#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Pattern Logic Module
Handles pattern processing, validation, and preview generation
"""

import re
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox


class PatternLogic:
    """Handles pattern processing and validation logic"""
    
    def __init__(self, dialog):
        """Initialize pattern logic handler"""
        self.dialog = dialog
        
    def insert_tag(self, tag, pattern_edit, separator_combo, custom_separator_edit):
        """Insert a tag at the cursor position in pattern edit with automatic separator handling"""
        if not pattern_edit:
            return
            
        cursor_pos = pattern_edit.cursorPosition()
        current_text = pattern_edit.text()
        
        # Get the current separator
        current_separator = self.get_current_separator(separator_combo, custom_separator_edit)
        
        # Check if we need to add separator before or after
        tag_to_insert = tag
        
        # Check what's before the cursor
        text_before = current_text[:cursor_pos].rstrip()
        text_after = current_text[cursor_pos:].lstrip()
        
        # If there's a variable before cursor, add separator before tag
        if text_before and text_before.endswith('}'):
            tag_to_insert = current_separator + tag_to_insert
        
        # If there's a variable after cursor, add separator after tag
        if text_after and text_after.startswith('${'):
            tag_to_insert = tag_to_insert + current_separator
        
        # Insert the tag with separator at cursor position
        new_text = current_text[:cursor_pos] + tag_to_insert + current_text[cursor_pos:]
        pattern_edit.setText(new_text)
        
        # Move cursor to after the inserted tag
        pattern_edit.setCursorPosition(cursor_pos + len(tag_to_insert))

    def validate_pattern(self, pattern, custom_options_manager, format_managers, date_combo, time_combo):
        """Validate the pattern and return any errors"""
        if not pattern.strip():
            return ["Please enter a naming pattern"]
        
        errors = []
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            if char in pattern:
                errors.append(f"Invalid character '{char}' in pattern")
        
        # Validate custom options if present
        if custom_options_manager.has_custom_placeholders(pattern):
            custom_errors = custom_options_manager.validate_custom_options()
            errors.extend(custom_errors)
        
        # Validate format options
        format_errors = format_managers.validate_formats(pattern, date_combo, time_combo)
        errors.extend(format_errors)
        
        # Check for unknown placeholders
        known_placeholders = [
            '${PROJECT_NAME}', '${BASE}', '${DATE}', '${TIME}', 
            '${COUNTER}', '${CUSTOM}', '${CUSTOM1}', '${CUSTOM2}', '${CUSTOM3}'
        ]
        
        # Find all placeholders in pattern
        placeholders = re.findall(r'\$\{[^}]+\}', pattern)
        for placeholder in placeholders:
            if placeholder not in known_placeholders:
                errors.append(f"Unknown placeholder: {placeholder}")
        
        return errors

    def generate_sample_preview(self, pattern, custom_options_manager, format_managers, 
                               date_combo, time_combo, is_folder=False):
        """Generate a sample preview of the pattern"""
        if not pattern:
            return "Enter a pattern to see preview"
        
        try:
            # Get sample values for different placeholders
            sample_values = {
                '${PROJECT_NAME}': 'MyProject',
                '${BASE}': 'filename' if not is_folder else 'foldername',
                '${COUNTER}': '001'
            }
            
            # Add custom option values
            custom_values = custom_options_manager.get_sample_custom_values()
            sample_values.update(custom_values)
            
            # Add format values
            format_values = format_managers.get_sample_format_values(date_combo, time_combo)
            sample_values.update(format_values)
            
            # Replace placeholders in pattern
            preview = pattern
            for placeholder, value in sample_values.items():
                preview = preview.replace(placeholder, value)
            
            # Add extension for files
            if not is_folder and not preview.endswith(('.txt', '.mp4', '.jpg', '.png', '.pdf')):
                preview += '.txt'
            
            return preview
            
        except Exception as e:
            return f"Error generating preview: {str(e)}"

    def get_current_separator(self, separator_combo, custom_separator_edit):
        """Get the current separator from UI"""
        separator_text = separator_combo.currentText()
        
        if separator_text == "_ (underscore)":
            return "_"
        elif separator_text == "- (dash)":
            return "-"
        elif separator_text == ". (dot)":
            return "."
        elif separator_text == "  (space)":
            return " "
        elif separator_text == "Custom...":
            return custom_separator_edit.text() or "_"
        else:
            return "_"

    def detect_manual_separators(self, pattern):
        """Detect separators manually added to the pattern"""
        if not pattern:
            return []
        
        # Look for common separators between variables
        separators = []
        
        # Find patterns like }_{, }-{, }.{, } {
        separator_patterns = [
            (r'\}_\{', '_'),
            (r'\}-\{', '-'),
            (r'\}\.\{', '.'),
            (r'\} \{', ' ')
        ]
        
        for pattern_regex, separator in separator_patterns:
            if re.search(pattern_regex, pattern):
                separators.append(separator)
        
        return list(set(separators))  # Remove duplicates

    def update_pattern_separators(self, pattern, new_separator):
        """Update pattern to use the specified separator"""
        if not pattern:
            return pattern
        
        # Replace separators between variables
        updated_pattern = self._update_pattern_variable_separators(pattern, new_separator)
        
        return updated_pattern

    def _update_pattern_variable_separators(self, pattern, new_separator):
        """Update separators between pattern variables"""
        if not pattern:
            return pattern
        
        # Replace any separator characters between variables with the new separator
        # This handles patterns like ${VAR1}_${VAR2}, ${VAR1}-${VAR2}, etc.
        # Use a more robust pattern that handles multiple consecutive separators
        updated_pattern = re.sub(
            r'(\$\{[^}]+\})[_\-\.\s]+(\$\{[^}]+\})', 
            f'\\1{new_separator}\\2', 
            pattern
        )
        
        # Apply the replacement multiple times to handle chains of variables
        # e.g., ${A}_${B}_${C} -> ${A}X${B}X${C}
        previous_pattern = ""
        while previous_pattern != updated_pattern:
            previous_pattern = updated_pattern
            updated_pattern = re.sub(
                r'(\$\{[^}]+\})[_\-\.\s]+(\$\{[^}]+\})', 
                f'\\1{new_separator}\\2', 
                updated_pattern
            )
        
        return updated_pattern

    def apply_pattern_data(self, pattern_data, item, pattern_applier):
        """Apply pattern data to an item using the pattern applier"""
        if not pattern_data or not item or not pattern_applier:
            return False
        
        try:
            pattern_applier.apply_pattern_to_item(item, pattern_data)
            return True
        except Exception as e:
            print(f"Error applying pattern: {e}")
            return False

    def show_validation_errors(self, errors):
        """Show validation errors to the user"""
        if not errors:
            return
        
        error_message = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Pattern Validation")
        msg_box.setText(error_message)
        msg_box.exec()

    def get_pattern_complexity_score(self, pattern):
        """Calculate a complexity score for the pattern"""
        if not pattern:
            return 0
        
        score = 0
        
        # Count placeholders
        placeholders = re.findall(r'\$\{[^}]+\}', pattern)
        score += len(placeholders) * 2
        
        # Count custom placeholders (more complex)
        custom_placeholders = re.findall(r'\$\{CUSTOM\d*\}', pattern)
        score += len(custom_placeholders) * 3
        
        # Count separators
        separators = len(re.findall(r'[_\-\. ]', pattern))
        score += separators
        
        # Count static text
        static_text = re.sub(r'\$\{[^}]+\}', '', pattern)
        score += len(static_text.strip())
        
        return score

    def suggest_pattern_improvements(self, pattern):
        """Suggest improvements for the pattern"""
        suggestions = []
        
        if not pattern:
            return ["Add some pattern variables like ${PROJECT_NAME} or ${DATE}"]
        
        # Check for common issues
        if len(pattern) > 100:
            suggestions.append("Consider shortening the pattern for better readability")
        
        if not re.search(r'\$\{[^}]+\}', pattern):
            suggestions.append("Add dynamic variables like ${PROJECT_NAME} or ${DATE}")
        
        if pattern.count('_') > 5:
            suggestions.append("Consider using fewer separators for cleaner names")
        
        # Check for redundant separators
        if re.search(r'__+', pattern):
            suggestions.append("Remove double underscores")
        
        if re.search(r'--+', pattern):
            suggestions.append("Remove double dashes")
        
        return suggestions

    def is_pattern_valid_for_filesystem(self, pattern):
        """Check if pattern would create valid filesystem names"""
        if not pattern:
            return False, "Empty pattern"
        
        # Generate a sample and check it
        sample = self.generate_sample_preview(pattern, None, None, None, None)
        
        # Check length
        if len(sample) > 255:
            return False, "Generated filename too long (max 255 characters)"
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in invalid_chars:
            if char in sample:
                return False, f"Invalid character '{char}' in generated name"
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = sample.split('.')[0].upper()
        if name_without_ext in reserved_names:
            return False, f"'{name_without_ext}' is a reserved filename"
        
        return True, "Valid pattern" 