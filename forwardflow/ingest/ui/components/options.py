"""Options Section for Ingest Tab"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt

try:
    from app.ui.color_scheme_pyqt import (
        colors, COMBOBOX_STYLE, GROUPBOX_STYLE, FIELD_LABEL_STYLE,
        SLIDER_STYLE, ACCENT_VALUE_STYLE, SECTION_HEADER_STYLE
    )
    from app.ui.custom_delegates import apply_hover_delegate
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class OptionsSection(QWidget):
    """Transfer Settings Section with exact original design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the transfer settings UI"""
        self.setMinimumWidth(800)
        self.setMinimumHeight(140)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(15, 4, 15, 8)
        
        # Transfer Settings
        transfer_container = QWidget()
        transfer_container.setMinimumWidth(400)
        transfer_container.setMinimumHeight(130)
        transfer_settings_layout = QVBoxLayout(transfer_container)
        transfer_settings_layout.setSpacing(10)
        
        # Transfer Settings Header with Generate Verification Report checkbox (right justified)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        transfer_header = QLabel("Transfer Settings")
        transfer_header.setStyleSheet(SECTION_HEADER_STYLE)
        transfer_header.setFixedHeight(30)
        
        # Generate Verification Report checkbox (right justified)
        self.report_checkbox = QCheckBox("Generate Verification Report")
        self.report_checkbox.setChecked(True)  # Default to enabled
        self.report_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {colors['border']};
                background-color: {colors['card_bg']};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {colors['accent']};
                background-color: {colors['accent']};
                border-radius: 3px;
            }}
        """)
        self.report_checkbox.setFixedHeight(30)
        
        header_layout.addWidget(transfer_header)
        header_layout.addStretch()  # Push checkbox to the right
        header_layout.addWidget(self.report_checkbox)
        
        transfer_settings_layout.addLayout(header_layout)
        
        # Single row: All controls on one line using full width
        controls_row = QHBoxLayout()
        controls_row.setSpacing(30)
        controls_row.setContentsMargins(0, 0, 0, 0)
        
        # Global Preset (expands with available space)
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(5)
        preset_label = QLabel("Global Preset:")
        preset_label.setStyleSheet(FIELD_LABEL_STYLE)
        preset_label.setFixedHeight(18)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Auto (recommended)",
            "USB/TB",
            "Network",
            "Custom"
        ])
        self.preset_combo.setStyleSheet(COMBOBOX_STYLE)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.setFixedHeight(28)
        self.preset_combo.setMinimumWidth(150)
        
        # Apply hover delegate for proper hover effects
        try:
            apply_hover_delegate(self.preset_combo)
            print("DEBUG: Applied hover delegate to preset_combo")
        except Exception as e:
            print(f"DEBUG: Failed to apply hover delegate to preset_combo: {e}")
        
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        controls_row.addLayout(preset_layout, 1)
        
        # Verify Mode (expands with available space)
        verify_layout = QVBoxLayout()
        verify_layout.setSpacing(5)
        verify_label = QLabel("Verify Mode:")
        verify_label.setStyleSheet(FIELD_LABEL_STYLE)
        verify_label.setFixedHeight(18)
        self.verify_combo = QComboBox()
        self.verify_combo.addItems([
            "FAST",
            "STREAM_VERIFY",
            "READBACK_VERIFY"
        ])
        self.verify_combo.setStyleSheet(COMBOBOX_STYLE)
        self.verify_combo.setCurrentIndex(0)
        self.verify_combo.setFixedHeight(28)
        self.verify_combo.setMinimumWidth(140)
        
        # Apply hover delegate for proper hover effects
        try:
            apply_hover_delegate(self.verify_combo)
            print("DEBUG: Applied hover delegate to verify_combo")
        except Exception as e:
            print(f"DEBUG: Failed to apply hover delegate to verify_combo: {e}")
        
        # Auto-update verification report checkbox based on verify mode
        def on_verify_mode_changed():
            current_mode = self.verify_combo.currentText()
            # Auto-enable verification report for verification modes other than FAST
            if current_mode in ["STREAM_VERIFY", "READBACK_VERIFY"]:
                self.report_checkbox.setChecked(True)
                self.report_checkbox.setToolTip("Verification report automatically enabled for verification modes")
            else:
                # For FAST mode, leave user's choice but show helpful tooltip
                self.report_checkbox.setToolTip("Optional verification report (recommended for audit trails)")
            print(f"DEBUG: Verify mode changed to {current_mode}, report checkbox: {self.report_checkbox.isChecked()}")
        
        # Connect the signal after the function is defined
        self.verify_combo.currentTextChanged.connect(on_verify_mode_changed)
        
        verify_layout.addWidget(verify_label)
        verify_layout.addWidget(self.verify_combo)
        controls_row.addLayout(verify_layout, 1)
        
        # Per-file concurrency (expands with available space)
        conc_layout = QVBoxLayout()
        conc_layout.setSpacing(5)
        conc_label = QLabel("Per-file concurrency:")
        conc_label.setStyleSheet(FIELD_LABEL_STYLE)
        conc_label.setFixedHeight(18)
        self.conc_slider = QSlider(Qt.Orientation.Horizontal)
        self.conc_slider.setRange(1, 16)
        self.conc_slider.setValue(2)
        self.conc_slider.setStyleSheet(SLIDER_STYLE)
        self.conc_slider.setFixedHeight(22)
        self.conc_slider.setMinimumHeight(22)
        self.conc_slider.setMaximumHeight(22)
        self.conc_slider.setMinimumWidth(150)
        self.conc_value = QLabel("2")
        self.conc_value.setStyleSheet(ACCENT_VALUE_STYLE)
        self.conc_value.setFixedHeight(22)
        self.conc_value.setFixedWidth(25)
        self.conc_slider.valueChanged.connect(lambda v: self.conc_value.setText(str(v)))
        
        conc_row = QHBoxLayout()
        conc_row.setSpacing(8)
        conc_row.addWidget(self.conc_slider, 1)
        conc_row.addWidget(self.conc_value)
        
        conc_layout.addWidget(conc_label)
        conc_layout.addLayout(conc_row)
        controls_row.addLayout(conc_layout, 1)
        
        # Stream concurrency (expands with available space)
        stream_layout = QVBoxLayout()
        stream_layout.setSpacing(5)
        stream_label = QLabel("Stream concurrency:")
        stream_label.setStyleSheet(FIELD_LABEL_STYLE)
        stream_label.setFixedHeight(18)
        self.stream_slider = QSlider(Qt.Orientation.Horizontal)
        self.stream_slider.setRange(1, 32)
        self.stream_slider.setValue(4)
        self.stream_slider.setStyleSheet(SLIDER_STYLE)
        self.stream_slider.setFixedHeight(22)
        self.stream_slider.setMinimumHeight(22)
        self.stream_slider.setMaximumHeight(22)
        self.stream_slider.setMinimumWidth(150)
        self.stream_value = QLabel("4")
        self.stream_value.setStyleSheet(ACCENT_VALUE_STYLE)
        self.stream_value.setFixedHeight(22)
        self.stream_value.setFixedWidth(25)
        self.stream_slider.valueChanged.connect(lambda v: self.stream_value.setText(str(v)))
        
        stream_row = QHBoxLayout()
        stream_row.setSpacing(8)
        stream_row.addWidget(self.stream_slider, 1)
        stream_row.addWidget(self.stream_value)
        
        stream_layout.addWidget(stream_label)
        stream_layout.addLayout(stream_row)
        controls_row.addLayout(stream_layout, 1)
        
        transfer_settings_layout.addLayout(controls_row)
        
        # Add spacer to push everything to the top
        transfer_settings_layout.addStretch()
        
        # Add transfer settings to main layout
        layout.addWidget(transfer_container)
