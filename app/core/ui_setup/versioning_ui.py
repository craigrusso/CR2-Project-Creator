#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                           QCheckBox, QDateEdit, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from app.ui.color_scheme_pyqt import colors, COMBOBOX_STYLE


class VersioningUI:
    """Handles versioning UI creation and management"""
    
    def __init__(self, main_window):
        """Initialize with reference to main window"""
        self.main_window = main_window
    
    def create_versioning_widget(self):
        """Create the versioning options widget"""
        # Create versioning container
        versioning_container = QWidget()
        versioning_layout = QVBoxLayout(versioning_container)
        versioning_layout.setContentsMargins(0, 10, 0, 0)
        
        # Enable versioning checkbox
        self.main_window.enable_versioning = QCheckBox("Create sequence variations for each project")
        self.main_window.enable_versioning.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                font-weight: bold;
                spacing: 8px;
                padding: 8px 4px;
                min-height: 20px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border']};
                border-radius: 3px;
                background-color: {colors['card_bg']};
                margin-right: 4px;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {colors['accent']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent']};
                border: 1px solid {colors['accent']};
            }}
        """)
        self.main_window.enable_versioning.toggled.connect(self.main_window._toggle_versioning_options)
        versioning_layout.addWidget(self.main_window.enable_versioning)
        
        # Create basic versioning options (simplified for now)
        self.main_window.versioning_options = QWidget()
        options_layout = QHBoxLayout(self.main_window.versioning_options)
        options_layout.setContentsMargins(20, 10, 0, 0)
        
        # Type selection
        type_label = QLabel("Type:")
        type_label.setStyleSheet(f"color: {colors['text']};")
        self.main_window.sequence_type = QComboBox()
        self.main_window.sequence_type.addItems(["Date Sequences", "Version Numbers", "Sequential Numbers"])
        self.main_window.sequence_type.setStyleSheet(COMBOBOX_STYLE)
        
        # Position selection
        position_label = QLabel("Position:")
        position_label.setStyleSheet(f"color: {colors['text']};")
        self.main_window.name_position = QComboBox()
        self.main_window.name_position.addItems(["Suffix", "Prefix"])
        self.main_window.name_position.setStyleSheet(COMBOBOX_STYLE)
        
        options_layout.addWidget(type_label)
        options_layout.addWidget(self.main_window.sequence_type)
        options_layout.addWidget(position_label)
        options_layout.addWidget(self.main_window.name_position)
        options_layout.addStretch()
        
        versioning_layout.addWidget(self.main_window.versioning_options)
        
        # Create simple options widgets (placeholders for now)
        self._create_date_options()
        self._create_version_options()
        self._create_number_options()
        
        # Options container
        self.main_window.options_container = QWidget()
        options_container_layout = QVBoxLayout(self.main_window.options_container)
        options_container_layout.addWidget(self.main_window.date_options)
        options_container_layout.addWidget(self.main_window.version_options)
        options_container_layout.addWidget(self.main_window.number_options)
        
        versioning_layout.addWidget(self.main_window.options_container)
        
        # Initially hide options
        self.main_window.versioning_options.hide()
        self.main_window.options_container.hide()
        
        return versioning_container
    
    def _create_date_options(self):
        """Create date sequence options"""
        self.main_window.date_options = QWidget()
        layout = QHBoxLayout(self.main_window.date_options)
        
        # Start date
        layout.addWidget(QLabel("Start Date:"))
        self.main_window.start_date = QDateEdit()
        self.main_window.start_date.setDate(QDate.currentDate())
        layout.addWidget(self.main_window.start_date)
        
        # Count
        layout.addWidget(QLabel("Count:"))
        self.main_window.date_count = QSpinBox()
        self.main_window.date_count.setRange(1, 1000)
        self.main_window.date_count.setValue(5)
        layout.addWidget(self.main_window.date_count)
        
        # Interval
        layout.addWidget(QLabel("Interval:"))
        self.main_window.date_interval = QSpinBox()
        self.main_window.date_interval.setRange(1, 365)
        self.main_window.date_interval.setValue(1)
        layout.addWidget(self.main_window.date_interval)
        
        # Interval type
        self.main_window.date_interval_type = QComboBox()
        self.main_window.date_interval_type.addItems(["Days", "Weeks", "Months"])
        layout.addWidget(self.main_window.date_interval_type)
        
        # Format
        self.main_window.date_format = QComboBox()
        self.main_window.date_format.addItems([
            "YYYY-MM-DD (2025-01-15)", 
            "YYYYMMDD (20250115)", 
            "MM-DD-YYYY (01-15-2025)",
            "DD-MM-YYYY (15-01-2025)",
            "YYYY_MM_DD (2025_01_15)",
            "MM_DD_YYYY (01_15_2025)",
            "DD_MM_YYYY (15_01_2025)",
            "YYYY.MM.DD (2025.01.15)",
            "MM.DD.YYYY (01.15.2025)",
            "DD.MM.YYYY (15.01.2025)"
        ])
        layout.addWidget(self.main_window.date_format)
        
        layout.addStretch()
        self.main_window.date_options.hide()
    
    def _create_version_options(self):
        """Create version number options"""
        self.main_window.version_options = QWidget()
        layout = QHBoxLayout(self.main_window.version_options)
        
        # Count
        layout.addWidget(QLabel("Count:"))
        self.main_window.version_count = QSpinBox()
        self.main_window.version_count.setRange(1, 1000)
        self.main_window.version_count.setValue(3)
        layout.addWidget(self.main_window.version_count)
        
        # Format
        layout.addWidget(QLabel("Format:"))
        self.main_window.version_format = QComboBox()
        self.main_window.version_format.addItems(["V1, V2", "v1, v2", "Ver1, Ver2"])
        layout.addWidget(self.main_window.version_format)
        
        layout.addStretch()
        self.main_window.version_options.hide()
    
    def _create_number_options(self):
        """Create sequential number options"""
        self.main_window.number_options = QWidget()
        layout = QHBoxLayout(self.main_window.number_options)
        
        # Start
        layout.addWidget(QLabel("Start:"))
        self.main_window.number_start = QSpinBox()
        self.main_window.number_start.setRange(0, 9999)
        self.main_window.number_start.setValue(1)
        layout.addWidget(self.main_window.number_start)
        
        # Count
        layout.addWidget(QLabel("Count:"))
        self.main_window.number_count = QSpinBox()
        self.main_window.number_count.setRange(1, 1000)
        self.main_window.number_count.setValue(5)
        layout.addWidget(self.main_window.number_count)
        
        # Format
        layout.addWidget(QLabel("Format:"))
        self.main_window.number_format = QComboBox()
        self.main_window.number_format.addItems(["1, 2, 3", "01, 02, 03", "001, 002, 003"])
        layout.addWidget(self.main_window.number_format)
        
        layout.addStretch()
        self.main_window.number_options.hide()
    
    def toggle_versioning_options(self, enabled):
        """Toggle visibility of versioning options"""
        if enabled:
            self.main_window.versioning_options.show()
            self.main_window.options_container.show()
        else:
            self.main_window.versioning_options.hide()
            self.main_window.options_container.hide()
    
    def update_versioning_options(self):
        """Update which versioning options are visible based on sequence type"""
        if not hasattr(self.main_window, 'sequence_type'):
            return
            
        sequence_type = self.main_window.sequence_type.currentText()
        
        # Hide all options first
        self.main_window.date_options.hide()
        self.main_window.version_options.hide()
        self.main_window.number_options.hide()
        
        # Show relevant options
        if sequence_type == "Date Sequences":
            self.main_window.date_options.show()
        elif sequence_type == "Version Numbers":
            self.main_window.version_options.show()
        elif sequence_type == "Sequential Numbers":
            self.main_window.number_options.show() 