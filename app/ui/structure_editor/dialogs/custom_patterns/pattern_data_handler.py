#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Pattern Data Handler Module
Handles loading and saving pattern data for custom patterns dialog
"""

from PyQt6.QtCore import Qt


class PatternDataHandler:
    """Handles pattern data loading and saving"""
    
    def __init__(self, dialog):
        """Initialize pattern data handler"""
        self.dialog = dialog
        
    def get_pattern_data(self, pattern_edit, custom_options_manager, format_managers, 
                        separator_combo, custom_separator_edit, date_combo, time_combo):
        """Get all pattern data from the dialog"""
        pattern_data = {
            'pattern': pattern_edit.text().strip(),
            'uses_custom_pattern': True,
            'rename_flag': True
        }
        
        # Add separator data
        pattern_data['separator'] = self._get_current_separator(separator_combo, custom_separator_edit)
        pattern_data['separator_type'] = separator_combo.currentText()
        if separator_combo.currentText() == "Custom...":
            pattern_data['custom_separator'] = custom_separator_edit.text()
        
        # Add custom options data
        custom_options = custom_options_manager.get_custom_options_data()
        if custom_options:
            pattern_data['custom_options'] = custom_options
        
        # Add format settings
        format_settings = format_managers.get_format_settings(date_combo, time_combo)
        pattern_data.update(format_settings)
        
        return pattern_data

    def load_existing_pattern_data(self, item, pattern_edit, custom_options_manager, 
                                  format_managers, separator_combo, custom_separator_edit,
                                  date_combo, time_combo, custom_editors_layout):
        """Load existing pattern data from item"""
        if not item:
            return
        
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Load basic pattern
            if 'pattern' in item_data:
                pattern_edit.setText(item_data['pattern'])
            
            # Load separator settings
            self._load_separator_settings(item_data, separator_combo, custom_separator_edit)
            
            # Load format settings
            format_managers.load_format_settings(item_data, date_combo, time_combo)
            
            # Load custom options (must be done after pattern is loaded)
            pattern = pattern_edit.text()
            if pattern:
                custom_placeholders = custom_options_manager.get_custom_placeholders(pattern)
                if custom_placeholders:
                    custom_options_manager.update_custom_editors(custom_placeholders, custom_editors_layout)
                    custom_options_manager.load_custom_options_data(item_data)
            
        except Exception as e:
            print(f"Error loading pattern data: {e}")

    def _load_separator_settings(self, pattern_data, separator_combo, custom_separator_edit):
        """Load separator settings from pattern data"""
        if not pattern_data:
            return
        
        # Load separator type
        separator_type = pattern_data.get('separator_type', '_ (underscore)')
        
        # Find and set the separator in combo
        for i in range(separator_combo.count()):
            if separator_combo.itemText(i) == separator_type:
                separator_combo.setCurrentIndex(i)
                break
        
        # Load custom separator if needed
        if separator_type == "Custom..." and 'custom_separator' in pattern_data:
            custom_separator_edit.setText(pattern_data['custom_separator'])
            custom_separator_edit.setVisible(True)

    def _get_current_separator(self, separator_combo, custom_separator_edit):
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

    def save_pattern_to_item(self, item, pattern_data):
        """Save pattern data to item"""
        if not item or not pattern_data:
            return False
        
        try:
            # Get existing item data
            existing_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Update with pattern data
            existing_data.update(pattern_data)
            
            # Ensure original name is preserved
            if 'original_name' not in existing_data:
                existing_data['original_name'] = item.text(0)
            
            # Save back to item
            item.setData(0, Qt.ItemDataRole.UserRole, existing_data)
            
            return True
            
        except Exception as e:
            print(f"Error saving pattern to item: {e}")
            return False

    def clear_pattern_data(self, item):
        """Clear pattern data from item"""
        if not item:
            return
        
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Remove pattern-related keys
            pattern_keys = [
                'pattern', 'uses_custom_pattern', 'rename_flag',
                'separator', 'separator_type', 'custom_separator',
                'custom_options', 'date_format', 'time_format'
            ]
            
            for key in pattern_keys:
                item_data.pop(key, None)
            
            # Restore original name if available
            if 'original_name' in item_data:
                item.setText(0, item_data['original_name'])
            
            item.setData(0, Qt.ItemDataRole.UserRole, item_data)
            
        except Exception as e:
            print(f"Error clearing pattern data: {e}")

    def has_pattern_data(self, item):
        """Check if item has pattern data"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('uses_custom_pattern', False)

    def get_pattern_summary(self, item):
        """Get a summary of the pattern applied to item"""
        if not item:
            return "No pattern"
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        if not item_data.get('uses_custom_pattern'):
            return "No pattern"
        
        pattern = item_data.get('pattern', '')
        if not pattern:
            return "Empty pattern"
        
        # Count placeholders
        import re
        placeholders = re.findall(r'\$\{[^}]+\}', pattern)
        
        summary_parts = []
        summary_parts.append(f"Pattern: {pattern[:30]}{'...' if len(pattern) > 30 else ''}")
        summary_parts.append(f"Variables: {len(placeholders)}")
        
        if 'custom_options' in item_data:
            custom_count = len(item_data['custom_options'])
            summary_parts.append(f"Custom options: {custom_count}")
        
        return " | ".join(summary_parts)

    def export_pattern_data(self, item):
        """Export pattern data for sharing or backup"""
        if not item:
            return None
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        if not item_data.get('uses_custom_pattern'):
            return None
        
        # Extract only pattern-related data
        pattern_export = {}
        pattern_keys = [
            'pattern', 'separator', 'separator_type', 'custom_separator',
            'custom_options', 'date_format', 'time_format'
        ]
        
        for key in pattern_keys:
            if key in item_data:
                pattern_export[key] = item_data[key]
        
        return pattern_export

    def import_pattern_data(self, item, pattern_data):
        """Import pattern data from external source"""
        if not item or not pattern_data:
            return False
        
        try:
            # Validate pattern data
            if 'pattern' not in pattern_data:
                return False
            
            # Get existing item data
            existing_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Add pattern data
            existing_data.update(pattern_data)
            existing_data['uses_custom_pattern'] = True
            existing_data['rename_flag'] = True
            
            # Save to item
            item.setData(0, Qt.ItemDataRole.UserRole, existing_data)
            
            return True
            
        except Exception as e:
            print(f"Error importing pattern data: {e}")
            return False

    def validate_pattern_data(self, pattern_data):
        """Validate pattern data structure"""
        if not isinstance(pattern_data, dict):
            return False, "Pattern data must be a dictionary"
        
        if 'pattern' not in pattern_data:
            return False, "Pattern data must contain 'pattern' key"
        
        pattern = pattern_data['pattern']
        if not isinstance(pattern, str) or not pattern.strip():
            return False, "Pattern must be a non-empty string"
        
        # Validate custom options if present
        if 'custom_options' in pattern_data:
            custom_options = pattern_data['custom_options']
            if not isinstance(custom_options, dict):
                return False, "Custom options must be a dictionary"
            
            for placeholder, options in custom_options.items():
                if not isinstance(options, list):
                    return False, f"Options for {placeholder} must be a list"
                
                if not options:
                    return False, f"Options for {placeholder} cannot be empty"
        
        return True, "Valid pattern data"

    def get_pattern_statistics(self, item):
        """Get statistics about the pattern"""
        if not item:
            return {}
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        pattern = item_data.get('pattern', '')
        
        if not pattern:
            return {}
        
        import re
        
        stats = {
            'pattern_length': len(pattern),
            'placeholder_count': len(re.findall(r'\$\{[^}]+\}', pattern)),
            'custom_placeholder_count': len(re.findall(r'\$\{CUSTOM\d*\}', pattern)),
            'separator_count': len(re.findall(r'[_\-\. ]', pattern)),
            'static_text_length': len(re.sub(r'\$\{[^}]+\}', '', pattern).strip()),
            'has_date': '${DATE}' in pattern,
            'has_time': '${TIME}' in pattern,
            'has_project_name': '${PROJECT_NAME}' in pattern,
            'has_base': '${BASE}' in pattern,
            'has_counter': '${COUNTER}' in pattern
        }
        
        return stats 