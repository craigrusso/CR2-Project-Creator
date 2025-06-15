#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Date Sequence Dialog

Dialog for configuring date sequences for file versioning.
Extracted from the monolithic file_operations.py for better organization.
"""

import datetime
from datetime import timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QTextEdit, QDateEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont

# Import styling
from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, COMBOBOX_STYLE, SPINBOX_STYLE
from app.ui.custom_delegates import apply_hover_delegate


class DateSequenceDialog(QDialog):
    """Dialog for configuring date sequences for file versioning"""
    
    def __init__(self, parent, item):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle("Configure Date Sequence")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
        
    def _qdate_to_python(self, qdate):
        """Convert QDate to Python datetime.date safely for PyQt6"""
        if hasattr(qdate, 'toPython'):
            return qdate.toPython()
        else:
            # PyQt6 alternative - use the QDate properties
            return datetime.date(qdate.year(), qdate.month(), qdate.day())
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Date Sequence Configuration")
        self.setMinimumSize(500, 700)  # Increased height from 650 to 700 to prevent button overlap
        self.resize(600, 750)          # Increased height from 700 to 750
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
                color: {colors['text']};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)  # Reduced from 20 to 10
        
        # Title
        title = QLabel("Date Sequence Configuration")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(title)
        
        # Date format
        format_label = QLabel("Date Format:")
        format_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        format_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "YYYY_MM_DD",
            "YYYYMMDD", 
            "MM_DD_YYYY",
            "DD_MM_YYYY",
            "YYYY-MM-DD",
            "MM-DD-YYYY",
            "DD-MM-YYYY",
            "YYYY.MM.DD",
            "MM.DD.YYYY",
            "DD.MM.YYYY",
            "YYYY MM DD",
            "MM DD YYYY",
            "DD MM YYYY"
        ])
        # Apply consistent styling
        self.format_combo.setStyleSheet(COMBOBOX_STYLE)
        apply_hover_delegate(self.format_combo)
        layout.addWidget(self.format_combo)
        
        # Add some spacing before next section
        layout.addSpacing(5)
        
        # Date range
        range_label = QLabel("Date Range:")
        range_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        range_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(range_label)
        
        range_layout = QHBoxLayout()
        range_layout.setSpacing(15)
        
        start_label = QLabel("Start Date:")
        start_label.setStyleSheet(f"color: {colors['text']};")
        range_layout.addWidget(start_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QDateEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        
        # Apply standardized calendar styling
        def apply_start_calendar_style():
            calendar = self.start_date.calendarWidget()
            if calendar:
                self._apply_calendar_styling(calendar)
        
        # Connect to show calendar styling when popup opens
        self.start_date.dateChanged.connect(lambda: QTimer.singleShot(10, apply_start_calendar_style))
        
        # Apply initial styling
        QTimer.singleShot(100, apply_start_calendar_style)
        range_layout.addWidget(self.start_date)
        
        end_label = QLabel("End Date:")
        end_label.setStyleSheet(f"color: {colors['text']};")
        range_layout.addWidget(end_label)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(7))
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }}
            QDateEdit:focus {{
                border: 2px solid {colors['accent']};
            }}
        """)
        
        # Apply standardized calendar styling
        def apply_end_calendar_style():
            calendar = self.end_date.calendarWidget()
            if calendar:
                self._apply_calendar_styling(calendar)
        
        # Connect to show calendar styling when popup opens
        self.end_date.dateChanged.connect(lambda: QTimer.singleShot(10, apply_end_calendar_style))
        
        # Apply initial styling
        QTimer.singleShot(100, apply_end_calendar_style)
        range_layout.addWidget(self.end_date)
        
        layout.addLayout(range_layout)
        
        # Add some spacing before next section
        layout.addSpacing(5)
        
        # Interval
        interval_header = QLabel("Interval:")
        interval_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        interval_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(interval_header)
        
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(15)
        
        interval_label = QLabel("Every:")
        interval_label.setStyleSheet(f"color: {colors['text']};")
        interval_layout.addWidget(interval_label)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(365)
        self.interval_spin.setValue(1)
        self.interval_spin.setStyleSheet(SPINBOX_STYLE)
        interval_layout.addWidget(self.interval_spin)
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["Days", "Weeks", "Months"])
        # Apply consistent styling
        self.interval_combo.setStyleSheet(COMBOBOX_STYLE)
        apply_hover_delegate(self.interval_combo)
        interval_layout.addWidget(self.interval_combo)
        
        layout.addLayout(interval_layout)
        
        # Add some spacing before next section
        layout.addSpacing(5)
        
        # Date/Time placement options
        placement_header = QLabel("Date/Time Placement:")
        placement_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        placement_header.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(placement_header)
        
        placement_help = QLabel("Choose where to place date/time relative to PROJECT_NAME:")
        placement_help.setStyleSheet(f"color: {colors['secondary_text']};")
        layout.addWidget(placement_help)
        
        self.datetime_button_group = QButtonGroup()
        
        self.datetime_prefix_radio = QRadioButton("Before PROJECT_NAME (e.g., 20240115_MyProject)")
        self.datetime_suffix_radio = QRadioButton("After PROJECT_NAME (e.g., MyProject_20240115)")
        self.datetime_suffix_radio.setChecked(True)  # Default to suffix
        
        # Apply proper styling to radio buttons to match app theme
        radio_button_style = f"""
            QRadioButton {{
                color: {colors['text']};
                background-color: transparent;
                border: none;
                padding: 8px;
                font-size: 14px;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                background-color: {colors['card_bg']};
                border-radius: 8px;
            }}
            QRadioButton::indicator:hover {{
                border: 1px solid {colors['accent']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
                background-image: radial-gradient(white 0px, white 4px, transparent 5px);
            }}
        """
        
        self.datetime_prefix_radio.setStyleSheet(radio_button_style)
        self.datetime_suffix_radio.setStyleSheet(radio_button_style)
        
        self.datetime_button_group.addButton(self.datetime_prefix_radio, 0)
        self.datetime_button_group.addButton(self.datetime_suffix_radio, 1)
        
        self.datetime_prefix_radio.toggled.connect(self.update_preview)
        self.datetime_suffix_radio.toggled.connect(self.update_preview)
        
        placement_layout = QVBoxLayout()
        placement_layout.setSpacing(5)  # Add spacing between radio buttons
        placement_layout.addWidget(self.datetime_prefix_radio)
        placement_layout.addWidget(self.datetime_suffix_radio)
        layout.addLayout(placement_layout)
        
        # Add some spacing before preview section
        layout.addSpacing(5)
        
        # Preview
        preview_label = QLabel("Preview (first 10 dates):")
        preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        preview_label.setStyleSheet(f"""
            color: {colors['text']};
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMinimumHeight(200)  # Increased from 150 to 200
        self.preview_text.setMaximumHeight(250)  # Set a reasonable maximum
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors['card_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 12px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(self.preview_text)
        
        # Connect signals
        self.format_combo.currentTextChanged.connect(self.update_preview)
        self.start_date.dateChanged.connect(self.update_preview)
        self.end_date.dateChanged.connect(self.update_preview)
        self.interval_spin.valueChanged.connect(self.update_preview)
        self.interval_combo.currentTextChanged.connect(self.update_preview)
        
        # Initial preview
        self.update_preview()
        
        # Add some spacing before buttons
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()  # Push buttons to the right
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(BUTTON_STYLE)
        cancel_button.setMinimumSize(100, 35)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply Date Sequence")
        apply_button.clicked.connect(self.accept)
        apply_button.setStyleSheet(ACCENT_BUTTON_STYLE)
        apply_button.setMinimumSize(150, 35)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def _apply_calendar_styling(self, calendar):
        """Apply consistent calendar styling"""
        if not calendar:
            return
        
        try:
            from PyQt6.QtGui import QTextCharFormat, QColor
            from PyQt6.QtCore import Qt
            
            # Set weekend text format to be dimmer grey (not red)
            weekend_format = QTextCharFormat()
            weekend_format.setForeground(QColor('#888888'))  # Dimmer grey for weekends
            calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend_format)
            calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend_format)
            
            # Set weekday text format to white  
            weekday_format = QTextCharFormat()
            weekday_format.setForeground(QColor(colors['text']))
            for day in [Qt.DayOfWeek.Monday, Qt.DayOfWeek.Tuesday, Qt.DayOfWeek.Wednesday, 
                       Qt.DayOfWeek.Thursday, Qt.DayOfWeek.Friday]:
                calendar.setWeekdayTextFormat(day, weekday_format)
        except Exception as e:
            print(f"Error applying calendar styling: {e}")
    
    def update_preview(self):
        """Update the preview of date sequences"""
        if not hasattr(self, 'preview_text'):
            return
            
        try:
            # Get date range
            start_date = self._qdate_to_python(self.start_date.date())
            end_date = self._qdate_to_python(self.end_date.date())
            
            # Validate date range
            if start_date > end_date:
                self.preview_text.setPlainText("Preview of generated files:\n\nError: Start date must be before end date.")
                return
            
            # Get interval
            interval_value = self.interval_spin.value()
            interval_type = self.interval_combo.currentText()
            
            # Get item name and parse extension
            item_name = self.item.text(0) if self.item else "example_project"
            
            # Clean item name of icons
            if ' ' in item_name and any(item_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
                item_name = item_name.split(' ', 1)[1]
            
            # Parse filename to get base name and extension
            base_name = item_name
            extension = ""
            if '.' in item_name:
                base_name, extension = item_name.rsplit('.', 1)
                extension = '.' + extension
            
            # Generate preview dates
            dates = []
            current_date = start_date
            
            while current_date <= end_date and len(dates) < 10:  # Limit preview to 10 items
                # Format date according to selected format
                format_text = self.format_combo.currentText()
                if format_text == "YYYY_MM_DD":
                    date_str = current_date.strftime("%Y_%m_%d")
                elif format_text == "YYYYMMDD":
                    date_str = current_date.strftime("%Y%m%d")
                elif format_text == "MM_DD_YYYY":
                    date_str = current_date.strftime("%m_%d_%Y")
                elif format_text == "DD_MM_YYYY":
                    date_str = current_date.strftime("%d_%m_%Y")
                elif format_text == "YYYY-MM-DD":
                    date_str = current_date.strftime("%Y-%m-%d")
                elif format_text == "MM-DD-YYYY":
                    date_str = current_date.strftime("%m-%d-%Y")
                elif format_text == "DD-MM-YYYY":
                    date_str = current_date.strftime("%d-%m-%Y")
                elif format_text == "YYYY.MM.DD":
                    date_str = current_date.strftime("%Y.%m.%d")
                elif format_text == "MM.DD.YYYY":
                    date_str = current_date.strftime("%m.%d.%Y")
                elif format_text == "DD.MM.YYYY":
                    date_str = current_date.strftime("%d.%m.%Y")
                elif format_text == "YYYY MM DD":
                    date_str = current_date.strftime("%Y %m %d")
                elif format_text == "MM DD YYYY":
                    date_str = current_date.strftime("%m %d %Y")
                elif format_text == "DD MM YYYY":
                    date_str = current_date.strftime("%d %m %Y")
                else:
                    date_str = current_date.strftime("%Y_%m_%d")  # Default to underscore
                
                # Create example filename with placement logic
                datetime_prefix = hasattr(self, 'datetime_prefix_radio') and self.datetime_prefix_radio.isChecked()
                
                if datetime_prefix:
                    example_filename = f"{date_str}_{base_name}{extension}"
                else:
                    example_filename = f"{base_name}_{date_str}{extension}"
                dates.append(example_filename)
                
                # Move to next date
                if interval_type == "Days":
                    current_date += timedelta(days=interval_value)
                elif interval_type == "Weeks":
                    current_date += timedelta(weeks=interval_value)
                elif interval_type == "Months":
                    # Approximate month calculation
                    current_date += timedelta(days=interval_value * 30)
            
            # Update preview text
            if not dates:
                preview_text = "Preview of generated files:\n\nNo files would be generated with the current settings.\nTry adjusting the date range or interval."
            else:
                preview_text = "Preview of generated files:\n\n"
                for i, filename in enumerate(dates, 1):
                    preview_text += f"{i:2d}. {filename}\n"
                
                if len(dates) >= 10:
                    preview_text += "\n... (showing first 10 items)"
                elif len(dates) == 1:
                    preview_text += "\n(Only 1 file would be generated)"
                else:
                    preview_text += f"\n({len(dates)} files would be generated)"
            
            self.preview_text.setPlainText(preview_text)
            
        except Exception as e:
            print(f"DEBUG: Error updating date preview: {e}")
            if hasattr(self, 'preview_text'):
                self.preview_text.setPlainText("Preview of generated files:\n\nError generating preview. Please check your settings and try again.")
    
    def get_date_data(self):
        """Get the date sequence configuration data"""
        # Convert dates to ISO format strings for JSON serialization
        start_date = self._qdate_to_python(self.start_date.date())
        end_date = self._qdate_to_python(self.end_date.date())
        
        return {
            'date_format': self.format_combo.currentText(),
            'date_start': start_date,  # Keep as date object for processing
            'date_end': end_date,      # Keep as date object for processing
            'date_start_iso': start_date.isoformat(),  # Store string version for JSON
            'date_end_iso': end_date.isoformat(),      # Store string version for JSON
            'date_interval_value': self.interval_spin.value(),
            'date_interval_type': self.interval_combo.currentText(),
            'datetime_prefix': hasattr(self, 'datetime_prefix_radio') and self.datetime_prefix_radio.isChecked(),
            'uses_date_sequence': True,
            'rename_flag': True
        } 