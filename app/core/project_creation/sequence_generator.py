#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import datetime
from datetime import timedelta


class SequenceGenerator:
    """Handles generating sequence names for batch project creation"""
    
    @staticmethod
    def generate_sequence_names(base_name, ui_widgets):
        """Generate sequence names based on current settings
        
        Args:
            base_name (str): The base project name
            ui_widgets (dict): Dictionary containing UI widget references
                - enable_versioning: QCheckBox
                - sequence_type: QComboBox  
                - name_position: QComboBox
                - start_date: QDateEdit
                - date_count: QSpinBox
                - date_interval: QSpinBox
                - date_interval_type: QComboBox
                - date_format: QComboBox
                - version_count: QSpinBox
                - version_format: QComboBox
                - version_digits: QSpinBox
                - number_start: QSpinBox
                - number_count: QSpinBox
                - number_format: QComboBox
        
        Returns:
            list: List of generated sequence names
        """
        if not ui_widgets['enable_versioning'].isChecked():
            return [base_name]
        
        sequence_type = ui_widgets['sequence_type'].currentText()
        position = ui_widgets['name_position'].currentText()
        names = []
        
        if sequence_type == "Date Sequences":
            names = SequenceGenerator._generate_date_sequence(base_name, position, ui_widgets)
        elif sequence_type == "Version Numbers":
            names = SequenceGenerator._generate_version_sequence(base_name, position, ui_widgets)
        elif sequence_type == "Sequential Numbers":
            names = SequenceGenerator._generate_number_sequence(base_name, position, ui_widgets)
        
        return names
    
    @staticmethod
    def _generate_date_sequence(base_name, position, ui_widgets):
        """Generate date sequence names"""
        # Generate date sequence
        qdate = ui_widgets['start_date'].date()
        start_date = datetime.date(qdate.year(), qdate.month(), qdate.day())
        count = ui_widgets['date_count'].value()
        interval = ui_widgets['date_interval'].value()
        interval_type = ui_widgets['date_interval_type'].currentText()
        format_text = ui_widgets['date_format'].currentText()
        
        # Extract format
        if "YYYY-MM-DD" in format_text:
            date_format = "%Y-%m-%d"
        elif "YYYYMMDD" in format_text:
            date_format = "%Y%m%d"
        elif "MM-DD-YYYY" in format_text:
            date_format = "%m-%d-%Y"
        elif "DD-MM-YYYY" in format_text:
            date_format = "%d-%m-%Y"
        elif "YYYY_MM_DD" in format_text:
            date_format = "%Y_%m_%d"
        elif "MM_DD_YYYY" in format_text:
            date_format = "%m_%d_%Y"
        elif "DD_MM_YYYY" in format_text:
            date_format = "%d_%m_%Y"
        elif "YYYY.MM.DD" in format_text:
            date_format = "%Y.%m.%d"
        elif "MM.DD.YYYY" in format_text:
            date_format = "%m.%d.%Y"
        elif "DD.MM.YYYY" in format_text:
            date_format = "%d.%m.%Y"
        elif "YYYY MM DD" in format_text:
            date_format = "%Y %m %d"
        elif "MM DD YYYY" in format_text:
            date_format = "%m %d %Y"
        elif "DD MM YYYY" in format_text:
            date_format = "%d %m %Y"
        else:
            date_format = "%Y-%m-%d"
        
        names = []
        current_date = start_date
        for i in range(count):
            date_str = current_date.strftime(date_format)
            
            if "Suffix" in position:
                name = f"{base_name}_{date_str}"
            elif "Prefix" in position:
                name = f"{date_str}_{base_name}"
            else:
                name = date_str
            
            names.append(name)
            
            # Calculate next date
            if interval_type == "Days":
                current_date += timedelta(days=interval)
            elif interval_type == "Weeks":
                current_date += timedelta(weeks=interval)
            elif interval_type == "Months":
                # Approximate month calculation
                current_date += timedelta(days=interval * 30)
        
        return names
    
    @staticmethod
    def _generate_version_sequence(base_name, position, ui_widgets):
        """Generate version sequence names"""
        count = ui_widgets['version_count'].value()
        format_prefix = ui_widgets['version_format'].currentText()
        leading_zeros = ui_widgets['version_digits'].currentText()
        
        names = []
        for i in range(1, count + 1):
            # Format number based on leading zeros setting
            if leading_zeros == "NONE":
                num_str = str(i)
            elif leading_zeros == "1":
                num_str = f"{i:02d}"  # 1 leading zero = 2 digits total
            elif leading_zeros == "2":
                num_str = f"{i:03d}"  # 2 leading zeros = 3 digits total
            elif leading_zeros == "3":
                num_str = f"{i:04d}"  # 3 leading zeros = 4 digits total
            else:
                num_str = str(i)
            
            version_str = f"{format_prefix}{num_str}"
            
            if "Suffix" in position:
                name = f"{base_name}_{version_str}"
            elif "Prefix" in position:
                name = f"{version_str}_{base_name}"
            else:
                name = version_str
            
            names.append(name)
        
        return names
    
    @staticmethod
    def _generate_number_sequence(base_name, position, ui_widgets):
        """Generate number sequence names"""
        start = ui_widgets['number_start'].value()
        count = ui_widgets['number_count'].value()
        format_text = ui_widgets['number_format'].currentText()
        
        names = []
        for i in range(count):
            num = start + i
            
            if "4 digits" in format_text:
                num_str = f"{num:04d}"
            elif "3 digits" in format_text:
                num_str = f"{num:03d}"
            elif "2 digits" in format_text:
                num_str = f"{num:02d}"
            else:  # no padding
                num_str = str(num)
            
            if "Suffix" in position:
                name = f"{base_name}_{num_str}"
            elif "Prefix" in position:
                name = f"{num_str}_{base_name}"
            else:
                name = num_str
            
            names.append(name)
        
        return names 