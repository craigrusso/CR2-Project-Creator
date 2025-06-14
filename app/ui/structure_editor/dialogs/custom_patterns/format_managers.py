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
        
        date_format_items = [
            "YYYYMMDD (20240115)",
            "YYYY_MM_DD (2024_01_15)",
            "YYYY-MM-DD (2024-01-15)",
            "YYYY.MM.DD (2024.01.15)",
            "YYYY MM DD (2024 01 15)",
            "MM_DD_YYYY (01_15_2024)",
            "MM-DD-YYYY (01-15-2024)",
            "MM.DD.YYYY (01.15.2024)",
            "MM DD YYYY (01 15 2024)",
            "DD_MM_YYYY (15_01_2024)",
            "DD-MM-YYYY (15-01-2024)",
            "DD.MM.YYYY (15.01.2024)",
            "DD MM YYYY (15 01 2024)"
        ]
        
        date_format_combo = ui_components.create_styled_combo_box(date_format_items)
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
        
        time_format_items = [
            "HHMMSS (143022)",
            "HH_MM_SS (14_30_22)",
            "HH-MM-SS (14-30-22)",
            "HH.MM.SS (14.30.22)",
            "HH MM SS (14 30 22)",
            "HHMM (1430)",
            "HH_MM (14_30)",
            "HH-MM (14-30)",
            "HH.MM (14.30)",
            "HH MM (14 30)"
        ]
        
        time_format_combo = ui_components.create_styled_combo_box(time_format_items)
        time_layout.addWidget(time_format_combo)
        
        time_format_group.setLayout(time_layout)
        layout.addWidget(time_format_group)
        
        return time_format_group, time_format_combo

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
            'MM': '%m',
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
        """Get current format settings"""
        settings = {}
        
        if date_combo:
            settings['date_format'] = self.get_date_format_string(date_combo.currentText())
        
        if time_combo:
            settings['time_format'] = self.get_time_format_string(time_combo.currentText())
        
        return settings

    def load_format_settings(self, pattern_data, date_combo, time_combo):
        """Load format settings from pattern data"""
        if not pattern_data:
            return
            
        # Load date format
        if date_combo and 'date_format' in pattern_data:
            date_format = pattern_data['date_format']
            for i in range(date_combo.count()):
                item_text = date_combo.itemText(i)
                if self.get_date_format_string(item_text) == date_format:
                    date_combo.setCurrentIndex(i)
                    break
        
        # Load time format
        if time_combo and 'time_format' in pattern_data:
            time_format = pattern_data['time_format']
            for i in range(time_combo.count()):
                item_text = time_combo.itemText(i)
                if self.get_time_format_string(item_text) == time_format:
                    time_combo.setCurrentIndex(i)
                    break

    def update_datetime_formats_to_separator(self, separator, date_combo, time_combo):
        """Update date and time formats to use the specified separator"""
        if date_combo:
            self._update_combo_formats_to_separator(date_combo, separator, is_date=True)
        
        if time_combo:
            self._update_combo_formats_to_separator(time_combo, separator, is_date=False)

    def _update_combo_formats_to_separator(self, combo, separator, is_date=True):
        """Update combo box formats to use the specified separator"""
        current_index = combo.currentIndex()
        
        # Get all items and convert them
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