#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Format Managers Module
Handles date and time format options for custom patterns
"""

import re
from datetime import datetime
from PyQt6.QtWidgets import QVBoxLayout


class FormatManagers:
    """Handles date and time format management"""
    
    def __init__(self, dialog):
        """Initialize format managers"""
        self.dialog = dialog
        self.colors = None
        
    def setup_styles(self):
        """Setup color scheme"""
        from app.ui.color_scheme_pyqt import colors
        self.colors = colors
        
    def create_date_format_group(self, layout):
        """Create the date format options group"""
        if not self.colors:
            self.setup_styles()
            
        from .pattern_ui_components import PatternUIComponents
        ui_components = PatternUIComponents(self.dialog)
        ui_components.setup_styles()
        
        date_format_group = ui_components.create_group_box("Date Format Options (for ${DATE})", visible=False)
        date_layout = QVBoxLayout()
        
        date_help = ui_components.create_help_label("Choose how the ${DATE} tag will be formatted:")
        date_layout.addWidget(date_help)
        
        # Get ALL format options (with all separator types)
        date_format_items = self._get_all_date_format_options()
        
        date_format_combo = ui_components.create_styled_combo_box(date_format_items)
        
        # Set initial selection based on current master separator
        initial_index = self._get_initial_date_format_index()
        if 0 <= initial_index < len(date_format_items):
            date_format_combo.setCurrentIndex(initial_index)
        
        date_layout.addWidget(date_format_combo)
        
        date_format_group.setLayout(date_layout)
        layout.addWidget(date_format_group)
        
        return date_format_group, date_format_combo
        
    def create_time_format_group(self, layout):
        """Create the time format options group"""
        if not self.colors:
            self.setup_styles()
            
        from .pattern_ui_components import PatternUIComponents
        ui_components = PatternUIComponents(self.dialog)
        ui_components.setup_styles()
        
        time_format_group = ui_components.create_group_box("Time Format Options (for ${TIME})", visible=False)
        time_layout = QVBoxLayout()
        
        time_help = ui_components.create_help_label("Choose how the ${TIME} tag will be formatted:")
        time_layout.addWidget(time_help)
        
        # Get ALL format options (with all separator types)
        time_format_items = self._get_all_time_format_options()
        
        time_format_combo = ui_components.create_styled_combo_box(time_format_items)
        
        # Set initial selection based on current master separator
        initial_index = self._get_initial_time_format_index()
        if 0 <= initial_index < len(time_format_items):
            time_format_combo.setCurrentIndex(initial_index)
        
        time_layout.addWidget(time_format_combo)
        
        time_format_group.setLayout(time_layout)
        layout.addWidget(time_format_group)
        
        return time_format_group, time_format_combo

    def _get_current_separator(self):
        """Get the current separator from the dialog"""
        if hasattr(self.dialog, 'separator_controller'):
            return self.dialog.separator_controller.get_current_separator()
        elif hasattr(self.dialog, 'pattern_logic') and hasattr(self.dialog, 'separator_combo') and hasattr(self.dialog, 'custom_separator_edit'):
            return self.dialog.pattern_logic.get_current_separator(
                self.dialog.separator_combo, 
                self.dialog.custom_separator_edit
            )
        else:
            return "_"  # Default fallback

    def _get_all_date_format_options(self):
        """Get all date format options (with all separator types)"""
        if hasattr(self.dialog, 'separator_controller'):
            return self.dialog.separator_controller.get_all_format_options(is_date=True)
        else:
            # Fallback to comprehensive hardcoded list with more format options
            return [
                "YYYYMMDD (20240115)",
                "YYYY_MM_DD (2024_01_15)",
                "MM_DD_YYYY (01_15_2024)",
                "DD_MM_YYYY (15_01_2024)",
                "YYYY-MM-DD (2024-01-15)",
                "MM-DD-YYYY (01-15-2024)",
                "DD-MM-YYYY (15-01-2024)",
                "YYYY.MM.DD (2024.01.15)",
                "MM.DD.YYYY (01.15.2024)",
                "DD.MM.YYYY (15.01.2024)",
                "YYYY MM DD (2024 01 15)",
                "MM DD YYYY (01 15 2024)",
                "DD MM YYYY (15 01 2024)",
            ]

    def _get_all_time_format_options(self):
        """Get all time format options (with all separator types)"""
        if hasattr(self.dialog, 'separator_controller'):
            return self.dialog.separator_controller.get_all_format_options(is_date=False)
        else:
            # Fallback to comprehensive hardcoded list with more format options
            return [
                "HHMMSS (143022)",
                "HHMM (1430)",
                "HH_MM_SS (14_30_22)",
                "HH_MM (14_30)",
                "HH-MM-SS (14-30-22)",
                "HH-MM (14-30)",
                "HH.MM.SS (14.30.22)",
                "HH.MM (14.30)",
                "HH MM SS (14 30 22)",
                "HH MM (14 30)"
            ]

    def _get_initial_date_format_index(self):
        """Get the initial date format index based on current master separator"""
        if hasattr(self.dialog, 'separator_controller'):
            current_separator = self.dialog.separator_controller.get_current_separator()
            return self.dialog.separator_controller.get_default_format_index_for_separator(current_separator, is_date=True)
        else:
            return 1  # Default to YYYY_MM_DD if no controller

    def _get_initial_time_format_index(self):
        """Get the initial time format index based on current master separator"""
        if hasattr(self.dialog, 'separator_controller'):
            current_separator = self.dialog.separator_controller.get_current_separator()
            return self.dialog.separator_controller.get_default_format_index_for_separator(current_separator, is_date=False)
        else:
            return 2  # Default to HH_MM_SS if no controller

    def _get_date_format_items_for_separator(self, separator):
        """Get date format items using the specified separator (DEPRECATED - use _get_all_date_format_options)"""
        return self._get_all_date_format_options()

    def _get_time_format_items_for_separator(self, separator):
        """Get time format items using the specified separator (DEPRECATED - use _get_all_time_format_options)"""
        return self._get_all_time_format_options()

    def has_date_placeholder(self, pattern):
        """Check if pattern contains ${DATE} placeholder"""
        return "${DATE}" in pattern if pattern else False

    def has_time_placeholder(self, pattern):
        """Check if pattern contains ${TIME} placeholder"""
        return "${TIME}" in pattern if pattern else False

    def get_date_format_string(self, combo_text):
        """Extract date format string from combo box text"""
        if not combo_text:
            return "YYYYMMDD"
            
        # Extract format from combo text (before the parentheses)
        format_match = re.match(r'^([^(]+)', combo_text.strip())
        if format_match:
            return format_match.group(1).strip()
        return "YYYYMMDD"

    def get_time_format_string(self, combo_text):
        """Extract time format string from combo box text"""
        if not combo_text:
            return "HHMMSS"
            
        # Extract format from combo text (before the parentheses)
        format_match = re.match(r'^([^(]+)', combo_text.strip())
        if format_match:
            return format_match.group(1).strip()
        return "HHMMSS"

    def format_date_sample(self, format_string):
        """Generate a sample date string based on format"""
        now = datetime.now()
        
        # Map format patterns to strftime patterns
        format_mapping = {
            'YYYY': '%Y',
            'YY': '%y',    # 2-digit year
            'MM': '%m',
            'mo': '%m',    # Month (same as MM for now)
            'DD': '%d',
            'HH': '%H',
            'SS': '%S'
        }
        
        # Convert format string to strftime format
        strftime_format = format_string
        for pattern, replacement in format_mapping.items():
            strftime_format = strftime_format.replace(pattern, replacement)
        
        try:
            return now.strftime(strftime_format)
        except:
            return "20240115"  # Fallback

    def format_time_sample(self, format_string):
        """Generate a sample time string based on format"""
        now = datetime.now()
        
        # Map format patterns to strftime patterns
        format_mapping = {
            'HH': '%H',
            'MM': '%M',
            'SS': '%S'
        }
        
        # Convert format string to strftime format
        strftime_format = format_string
        for pattern, replacement in format_mapping.items():
            strftime_format = strftime_format.replace(pattern, replacement)
        
        try:
            return now.strftime(strftime_format)
        except:
            return "143022"  # Fallback

    def get_format_settings(self, date_combo, time_combo):
        """Get current date and time format settings from UI"""
        return {
            "date_format_text": date_combo.currentText() if date_combo and date_combo.currentText() else "",
            "time_format_text": time_combo.currentText() if time_combo and time_combo.currentText() else ""
        }

    def load_format_settings(self, pattern_data, date_combo, time_combo):
        """Load date and time format settings into UI from pattern_data"""
        if pattern_data and isinstance(pattern_data, dict):
            date_format_text = pattern_data.get("date_format_text")
            if date_format_text:
                # Find the index of the text in the combo box and set it
                index = date_combo.findText(date_format_text)
                if index != -1:
                    date_combo.setCurrentIndex(index)

            time_format_text = pattern_data.get("time_format_text")
            if time_format_text:
                index = time_combo.findText(time_format_text)
                if index != -1:
                    time_combo.setCurrentIndex(index)

    def update_datetime_formats_to_separator(self, separator, date_combo, time_combo):
        """
        Updates the available date and time formats based on the selected separator.
        (DEPRECATED - all formats are now shown regardless of separator)
        """
        if date_combo:
            self._update_combo_formats_to_separator(date_combo, separator, is_date=True)
        
        if time_combo:
            self._update_combo_formats_to_separator(time_combo, separator, is_date=False)

    def _update_combo_formats_to_separator(self, combo, separator, is_date=True):
        """Update combo box formats to use the specified separator"""
        current_index = combo.currentIndex()
        
        # Get new format items using the separator controller if available
        if hasattr(self.dialog, 'separator_controller'):
            new_items = self.dialog.separator_controller.create_formats_with_separator(separator, is_date)
        else:
            # Fallback to manual conversion
            new_items = []
            for i in range(combo.count()):
                item_text = combo.itemText(i)
                new_format = self._convert_format_to_separator(item_text, separator, is_date)
                new_items.append(new_format)
        
        # Update combo box
        combo.clear()
        combo.addItems(new_items)
        
        # Restore selection if possible
        if 0 <= current_index < len(new_items):
            combo.setCurrentIndex(current_index)

    def _convert_format_to_separator(self, current_format, new_separator, is_date=True):
        """Convert a format string to use a new separator"""
        # Extract the format part (before parentheses) and example part
        parts = current_format.split(' (')
        if len(parts) != 2:
            return current_format
        
        format_part = parts[0]
        example_part = parts[1].rstrip(')')
        
        # Replace separators in format part
        if is_date:
            # For date formats, replace common separators
            old_separators = ['_', '-', '.', ' ']
        else:
            # For time formats, replace common separators
            old_separators = ['_', '-', '.', ' ']
        
        new_format_part = format_part
        for old_sep in old_separators:
            new_format_part = new_format_part.replace(old_sep, new_separator)
        
        # Generate new example
        if is_date:
            new_example = self.format_date_sample(new_format_part)
        else:
            new_example = self.format_time_sample(new_format_part)
        
        return f"{new_format_part} ({new_example})"

    def validate_formats(self, pattern, date_combo, time_combo):
        """Validate format settings"""
        errors = []
        
        if self.has_date_placeholder(pattern) and date_combo:
            if not date_combo.currentText():
                errors.append("Please select a date format")
        
        if self.has_time_placeholder(pattern) and time_combo:
            if not time_combo.currentText():
                errors.append("Please select a time format")
        
        return errors

    def get_sample_format_values(self, date_combo, time_combo):
        """Get sample values for format placeholders"""
        sample_values = {}
        
        if date_combo and date_combo.currentText():
            date_format = self.get_date_format_string(date_combo.currentText())
            sample_values['${DATE}'] = self.format_date_sample(date_format)
        else:
            sample_values['${DATE}'] = "20240115"
        
        if time_combo and time_combo.currentText():
            time_format = self.get_time_format_string(time_combo.currentText())
            sample_values['${TIME}'] = self.format_time_sample(time_format)
        else:
            sample_values['${TIME}'] = "143022"
        
        return sample_values 