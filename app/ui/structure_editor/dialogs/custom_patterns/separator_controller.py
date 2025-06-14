#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Separator Controller Module
Centralizes separator management and synchronization across UI components
"""

class SeparatorController:
    """
    Centralized controller for managing separator synchronization.
    
    This class ensures that when the master separator changes, all related
    UI components (date formats, time formats, etc.) are updated to match.
    """
    
    def __init__(self, dialog):
        """Initialize the separator controller"""
        self.dialog = dialog
        self.current_separator = "_"  # Default separator
        
    def set_master_separator(self, separator):
        """
        Set the master separator and update all dependent components.
        
        Args:
            separator (str): The new separator to use
        """
        if separator == self.current_separator:
            return  # No change needed
            
        old_separator = self.current_separator
        self.current_separator = separator
        
        # Update existing pattern text
        self._update_pattern_text()
        
        # Update currently selected date and time formats to use new separator
        self._update_current_format_selections(old_separator, separator)
        
        # Trigger preview update
        if hasattr(self.dialog, '_update_preview'):
            self.dialog._update_preview()
    
    def get_current_separator(self):
        """Get the current master separator"""
        return self.current_separator
    
    def initialize_from_ui(self, separator_combo, custom_separator_edit):
        """
        Initialize the master separator from the UI state.
        
        Args:
            separator_combo: The separator dropdown widget
            custom_separator_edit: The custom separator input widget
        """
        separator_text = separator_combo.currentText()
        
        if separator_text == "_ (underscore)":
            self.current_separator = "_"
        elif separator_text == "- (dash)":
            self.current_separator = "-"
        elif separator_text == ". (dot)":
            self.current_separator = "."
        elif separator_text == "  (space)":
            self.current_separator = " "
        elif separator_text == "Custom...":
            self.current_separator = custom_separator_edit.text() or "_"
        else:
            self.current_separator = "_"
    
    def get_all_format_options(self, is_date=True):
        """
        Get all possible format options (with all separator types).
        
        Args:
            is_date (bool): True for date formats, False for time formats
            
        Returns:
            list: List of all format strings with examples
        """
        if is_date:
            base_formats = [
                # No separator formats first
                ("YYYYMMDD", "20240115"),
                # Underscore formats
                ("YYYY_MM_DD", "2024_01_15"),
                ("MM_DD_YYYY", "01_15_2024"),
                ("DD_MM_YYYY", "15_01_2024"),
                ("mo_DD_YY", "01_15_24"),  # Month, day, 2-digit year
                ("DD_mo_YY", "15_01_24"),  # Day, month, 2-digit year
                ("YY_MM_DD", "24_01_15"),  # 2-digit year first
                # Dash formats
                ("YYYY-MM-DD", "2024-01-15"),
                ("MM-DD-YYYY", "01-15-2024"),
                ("DD-MM-YYYY", "15-01-2024"),
                ("mo-DD-YY", "01-15-24"),
                ("DD-mo-YY", "15-01-24"),
                ("YY-MM-DD", "24-01-15"),
                # Dot formats
                ("YYYY.MM.DD", "2024.01.15"),
                ("MM.DD.YYYY", "01.15.2024"),
                ("DD.MM.YYYY", "15.01.2024"),
                ("mo.DD.YY", "01.15.24"),
                ("DD.mo.YY", "15.01.24"),
                ("YY.MM.DD", "24.01.15"),
                # Space formats
                ("YYYY MM DD", "2024 01 15"),
                ("MM DD YYYY", "01 15 2024"),
                ("DD MM YYYY", "15 01 2024"),
                ("mo DD YY", "01 15 24"),
                ("DD mo YY", "15 01 24"),
                ("YY MM DD", "24 01 15")
            ]
        else:
            base_formats = [
                # No separator formats first
                ("HHMMSS", "143022"),
                ("HHMM", "1430"),
                # Underscore formats
                ("HH_MM_SS", "14_30_22"),
                ("HH_MM", "14_30"),
                # Dash formats
                ("HH-MM-SS", "14-30-22"),
                ("HH-MM", "14-30"),
                # Dot formats
                ("HH.MM.SS", "14.30.22"),
                ("HH.MM", "14.30"),
                # Space formats
                ("HH MM SS", "14 30 22"),
                ("HH MM", "14 30")
            ]
        
        # Create format strings
        all_formats = []
        for format_pattern, example_pattern in base_formats:
            all_formats.append(f"{format_pattern} ({example_pattern})")
        
        return all_formats
    
    def get_default_format_index_for_separator(self, separator, is_date=True):
        """
        Get the default format index that should be selected for the given separator.
        
        Args:
            separator (str): The separator to match
            is_date (bool): True for date formats, False for time formats
            
        Returns:
            int: Index of the default format for this separator
        """
        all_formats = self.get_all_format_options(is_date)
        
        # Default format patterns for each separator
        if is_date:
            if separator == "_":
                target_pattern = "YYYY_MM_DD"
            elif separator == "-":
                target_pattern = "YYYY-MM-DD"
            elif separator == ".":
                target_pattern = "YYYY.MM.DD"
            elif separator == " ":
                target_pattern = "YYYY MM DD"
            else:  # No separator or unknown
                target_pattern = "YYYYMMDD"
        else:  # time
            if separator == "_":
                target_pattern = "HH_MM_SS"
            elif separator == "-":
                target_pattern = "HH-MM-SS"
            elif separator == ".":
                target_pattern = "HH.MM.SS"
            elif separator == " ":
                target_pattern = "HH MM SS"
            else:  # No separator or unknown
                target_pattern = "HHMMSS"
        
        # Find the index of the target pattern
        for i, format_str in enumerate(all_formats):
            if format_str.startswith(target_pattern + " "):
                return i
        
        return 0  # Fallback to first option
    
    def convert_current_format_to_separator(self, current_format, new_separator):
        """
        Convert the currently selected format to use the new separator.
        
        Args:
            current_format (str): Current format string (e.g., "YYYY_MM_DD (2024_01_15)")
            new_separator (str): New separator to use
            
        Returns:
            str: Converted format string
        """
        if not current_format or "(" not in current_format:
            return current_format
        
        # Extract the pattern part (before parentheses)
        format_part = current_format.split(" (")[0]
        
        # Get the base pattern without any separators
        base_pattern = self._extract_base_pattern(format_part)
        
        # Reconstruct with new separator
        new_format = self._apply_separator_to_base_pattern(base_pattern, new_separator)
        
        # Generate new example
        new_example = self._generate_example_for_pattern(new_format)
        
        return f"{new_format} ({new_example})"
    
    def _extract_base_pattern(self, format_pattern):
        """
        Extract the base pattern structure without separators.
        
        Args:
            format_pattern (str): Pattern like "YYYY_MM_DD" or "HH-MM-SS"
            
        Returns:
            tuple: (components, is_date) e.g., (["YYYY", "MM", "DD"], True)
        """
        # Remove all common separators
        clean_pattern = format_pattern
        for sep in ['_', '-', '.', ' ']:
            clean_pattern = clean_pattern.replace(sep, '|')
        
        # Split by our placeholder separator
        components = clean_pattern.split('|')
        components = [c for c in components if c]  # Remove empty strings
        
        # Determine if it's a date or time pattern
        is_date = any(comp in ['YYYY', 'YY', 'MM', 'mo', 'DD'] for comp in components)
        
        return components, is_date
    
    def _apply_separator_to_base_pattern(self, components_tuple, separator):
        """
        Apply separator to base pattern components.
        
        Args:
            components_tuple: (components, is_date) from _extract_base_pattern
            separator (str): Separator to apply
            
        Returns:
            str: Pattern with separator applied
        """
        components, is_date = components_tuple
        
        if len(components) <= 1:
            return components[0] if components else ""
        
        # Join components with separator
        return separator.join(components)
    
    def _generate_example_for_pattern(self, pattern):
        """
        Generate an example for a pattern.
        
        Args:
            pattern (str): Pattern like "YYYY-MM-DD" or "HH.MM.SS"
            
        Returns:
            str: Example like "2024-01-15" or "14.30.22"
        """
        from datetime import datetime
        now = datetime.now()
        
        # Replace pattern components with actual values
        result = pattern
        result = result.replace('YYYY', now.strftime('%Y'))
        result = result.replace('MM', now.strftime('%m'))
        result = result.replace('DD', now.strftime('%d'))
        result = result.replace('HH', now.strftime('%H'))
        result = result.replace('mm', now.strftime('%M'))  # Minute in time patterns
        result = result.replace('SS', now.strftime('%S'))
        
        # Handle the case where MM might be month or minute
        if 'HH' in pattern and 'MM' in result and 'DD' not in pattern:
            # It's a time pattern, MM should be minutes
            result = result.replace('MM', now.strftime('%M'))
        
        return result
    
    def _update_pattern_text(self):
        """Update the pattern text to use the current separator"""
        if not hasattr(self.dialog, 'pattern_edit') or not hasattr(self.dialog, 'pattern_logic'):
            return
            
        current_pattern = self.dialog.pattern_edit.text()
        if current_pattern.strip():
            updated_pattern = self.dialog.pattern_logic.update_pattern_separators(
                current_pattern, self.current_separator
            )
            self.dialog.pattern_edit.setText(updated_pattern)
    
    def _update_current_format_selections(self, old_separator, new_separator):
        """
        Update the currently selected date and time formats to use new separator.
        
        Args:
            old_separator (str): Previous separator
            new_separator (str): New separator to use
        """
        # Update date format if it exists and is visible
        if hasattr(self.dialog, 'date_combo') and self.dialog.date_combo:
            current_date_format = self.dialog.date_combo.currentText()
            
            if current_date_format:
                # Extract the pattern from the current format
                current_pattern = current_date_format.split(" (")[0] if "(" in current_date_format else current_date_format
                
                # Convert pattern to new separator
                converted_pattern = self._convert_pattern_to_separator(current_pattern, new_separator)
                
                # Find the format in dropdown that matches this pattern
                target_index = self._find_format_index_by_pattern(self.dialog.date_combo, converted_pattern)
                
                if target_index >= 0:
                    self.dialog.date_combo.setCurrentIndex(target_index)
        
        # Update time format if it exists and is visible
        if hasattr(self.dialog, 'time_combo') and self.dialog.time_combo:
            current_time_format = self.dialog.time_combo.currentText()
            
            if current_time_format:
                # Extract the pattern from the current format
                current_pattern = current_time_format.split(" (")[0] if "(" in current_time_format else current_time_format
                
                # Convert pattern to new separator
                converted_pattern = self._convert_pattern_to_separator(current_pattern, new_separator)
                
                # Find the format in dropdown that matches this pattern
                target_index = self._find_format_index_by_pattern(self.dialog.time_combo, converted_pattern)
                
                if target_index >= 0:
                    self.dialog.time_combo.setCurrentIndex(target_index)

    def _convert_pattern_to_separator(self, pattern, separator):
        """
        Convert a format pattern to use the specified separator.
        
        Args:
            pattern (str): Format pattern like "YYYY_MM_DD" or "HH-MM-SS"
            separator (str): New separator to use
            
        Returns:
            str: Pattern with new separator
        """
        if not pattern:
            return pattern
        
        # Remove all separators and split by components
        clean_pattern = pattern
        for sep in ['_', '-', '.', ' ']:
            clean_pattern = clean_pattern.replace(sep, '|')
        
        components = [c for c in clean_pattern.split('|') if c]
        
        if len(components) <= 1:
            return pattern  # No separators to change
        
        # Rejoin with new separator
        return separator.join(components)

    def _find_format_index_by_pattern(self, combo, target_pattern):
        """
        Find the index of a format in the combo that matches the target pattern.
        
        Args:
            combo: The combo box to search
            target_pattern (str): The pattern to find (e.g., "YYYY.MM.DD")
            
        Returns:
            int: Index of matching format, or -1 if not found
        """
        if not combo or not target_pattern:
            return -1
        
        for i in range(combo.count()):
            item_text = combo.itemText(i)
            # Extract pattern from format string (everything before the parentheses)
            item_pattern = item_text.split(" (")[0] if "(" in item_text else item_text
            
            if item_pattern == target_pattern:
                return i
        
        return -1 