"""Options Section for Ingest Tab"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider, QCheckBox, QPushButton, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

try:
    from app.ui.color_scheme_pyqt import (
        colors, COMBOBOX_STYLE, GROUPBOX_STYLE, FIELD_LABEL_STYLE,
        SLIDER_STYLE, ACCENT_VALUE_STYLE, SECTION_HEADER_STYLE, BUTTON_STYLE
    )
    from app.ui.custom_delegates import apply_hover_delegate
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


class OptionsSection(QWidget):
    """Transfer Settings Section with collapsible advanced options"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._advanced_visible = False
        self.setup_ui()

    def setup_ui(self):
        """Setup the transfer settings UI - clean, no borders"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with checkbox
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        transfer_header = QLabel("Transfer Settings")
        transfer_header.setStyleSheet(SECTION_HEADER_STYLE)
        transfer_header.setFixedHeight(22)

        # Generate Verification Report checkbox
        self.report_checkbox = QCheckBox("Verification Report")
        self.report_checkbox.setChecked(True)
        self.report_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {colors['text']};
                font-size: 11px;
                spacing: 4px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
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

        header_layout.addWidget(transfer_header)
        header_layout.addStretch()
        header_layout.addWidget(self.report_checkbox)
        layout.addLayout(header_layout)

        # Preset and Checksum side-by-side to save vertical space
        settings_row = QHBoxLayout()
        settings_row.setSpacing(8)

        # Preset column (left)
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(4)
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet(FIELD_LABEL_STYLE)
        preset_label.setMinimumHeight(18)
        preset_label.setMaximumHeight(18)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Auto (recommended)",
            "USB/TB",
            "Network",
            "Custom"
        ])
        self.preset_combo.setStyleSheet(COMBOBOX_STYLE)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.setFixedHeight(32)

        try:
            apply_hover_delegate(self.preset_combo)
        except Exception as e:
            print(f"DEBUG: Failed to apply hover delegate to preset_combo: {e}")

        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)

        # Checksum column (right)
        checksum_layout = QVBoxLayout()
        checksum_layout.setSpacing(4)
        verify_label = QLabel("Checksum:")
        verify_label.setStyleSheet(FIELD_LABEL_STYLE)
        verify_label.setMinimumHeight(18)
        verify_label.setMaximumHeight(18)

        self.verify_combo = QComboBox()
        self.verify_combo.addItems([
            "xxHash64BE (Netflix)",
            "xxHash128 (Fast)",
            "SHA-256",
            "SHA-3",
            "MD5 (Legacy)"
        ])
        self.verify_combo.setStyleSheet(COMBOBOX_STYLE)
        self.verify_combo.setCurrentIndex(0)
        self.verify_combo.setFixedHeight(32)

        try:
            apply_hover_delegate(self.verify_combo)
        except Exception as e:
            print(f"DEBUG: Failed to apply hover delegate to verify_combo: {e}")

        checksum_layout.addWidget(verify_label)
        checksum_layout.addWidget(self.verify_combo)

        # Add both columns to row (equal widths)
        settings_row.addLayout(preset_layout, 1)
        settings_row.addLayout(checksum_layout, 1)
        layout.addLayout(settings_row)

        # Collapsible Advanced Settings
        advanced_toggle = QPushButton("▶ Advanced")
        advanced_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {colors['text']};
                border: none;
                text-align: left;
                padding: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {colors['accent']};
            }}
        """)
        advanced_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        advanced_toggle.setFixedHeight(24)
        advanced_toggle.clicked.connect(self._toggle_advanced)
        layout.addWidget(advanced_toggle)
        self._advanced_toggle = advanced_toggle

        # Advanced settings container (initially hidden)
        self._advanced_container = QFrame()
        self._advanced_container.setVisible(False)
        advanced_layout = QHBoxLayout(self._advanced_container)
        advanced_layout.setSpacing(12)
        advanced_layout.setContentsMargins(0, 4, 0, 0)

        # Per-file concurrency
        conc_layout = QVBoxLayout()
        conc_layout.setSpacing(4)
        conc_label = QLabel("Per-file concurrency:")
        conc_label.setStyleSheet(FIELD_LABEL_STYLE)
        conc_label.setFixedHeight(18)
        self.conc_slider = QSlider(Qt.Orientation.Horizontal)
        self.conc_slider.setRange(1, 16)
        self.conc_slider.setValue(2)
        self.conc_slider.setStyleSheet(SLIDER_STYLE)
        self.conc_slider.setFixedHeight(20)
        self.conc_value = QLabel("2")
        self.conc_value.setStyleSheet(ACCENT_VALUE_STYLE)
        self.conc_value.setFixedHeight(20)
        self.conc_value.setFixedWidth(24)
        self.conc_slider.valueChanged.connect(lambda v: self.conc_value.setText(str(v)))

        conc_row = QHBoxLayout()
        conc_row.setSpacing(6)
        conc_row.addWidget(self.conc_slider, 1)
        conc_row.addWidget(self.conc_value)

        conc_layout.addWidget(conc_label)
        conc_layout.addLayout(conc_row)
        advanced_layout.addLayout(conc_layout, 1)

        # Stream concurrency
        stream_layout = QVBoxLayout()
        stream_layout.setSpacing(4)
        stream_label = QLabel("Stream concurrency:")
        stream_label.setStyleSheet(FIELD_LABEL_STYLE)
        stream_label.setFixedHeight(18)
        self.stream_slider = QSlider(Qt.Orientation.Horizontal)
        self.stream_slider.setRange(1, 32)
        self.stream_slider.setValue(4)
        self.stream_slider.setStyleSheet(SLIDER_STYLE)
        self.stream_slider.setFixedHeight(20)
        self.stream_value = QLabel("4")
        self.stream_value.setStyleSheet(ACCENT_VALUE_STYLE)
        self.stream_value.setFixedHeight(20)
        self.stream_value.setFixedWidth(24)
        self.stream_slider.valueChanged.connect(lambda v: self.stream_value.setText(str(v)))

        stream_row = QHBoxLayout()
        stream_row.setSpacing(6)
        stream_row.addWidget(self.stream_slider, 1)
        stream_row.addWidget(self.stream_value)

        stream_layout.addWidget(stream_label)
        stream_layout.addLayout(stream_row)
        advanced_layout.addLayout(stream_layout, 1)

        layout.addWidget(self._advanced_container)

        # BLAST Cache Drive Selection
        blast_layout = QVBoxLayout()
        blast_layout.setSpacing(4)
        blast_layout.setContentsMargins(0, 8, 0, 0)

        blast_label = QLabel("BLAST Cache (Optional):")
        blast_label.setStyleSheet(FIELD_LABEL_STYLE)
        blast_label.setMinimumHeight(18)
        blast_label.setMaximumHeight(18)
        blast_label.setToolTip("Select a fast SSD for cache-and-distribute workflow.\nLeave empty for direct parallel copying.")

        blast_control_row = QHBoxLayout()
        blast_control_row.setSpacing(6)

        self.blast_cache_display = QLabel("None selected")
        self.blast_cache_display.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                background-color: {colors['bg']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
        """)
        self.blast_cache_display.setFixedHeight(32)

        self.blast_browse_button = QPushButton("Browse...")
        self.blast_browse_button.setStyleSheet(BUTTON_STYLE)
        self.blast_browse_button.setFixedHeight(32)
        self.blast_browse_button.setFixedWidth(80)
        self.blast_browse_button.clicked.connect(self._select_blast_cache_drive)

        self.blast_clear_button = QPushButton("Clear")
        self.blast_clear_button.setStyleSheet(BUTTON_STYLE)
        self.blast_clear_button.setFixedHeight(32)
        self.blast_clear_button.setFixedWidth(60)
        self.blast_clear_button.clicked.connect(self._clear_blast_cache_drive)

        blast_control_row.addWidget(self.blast_cache_display, 1)
        blast_control_row.addWidget(self.blast_browse_button)
        blast_control_row.addWidget(self.blast_clear_button)

        blast_layout.addWidget(blast_label)
        blast_layout.addLayout(blast_control_row)
        layout.addLayout(blast_layout)

        self._blast_cache_path = None

    def _toggle_advanced(self):
        """Toggle advanced settings visibility"""
        self._advanced_visible = not self._advanced_visible
        self._advanced_container.setVisible(self._advanced_visible)
        self._advanced_toggle.setText("▼ Advanced" if self._advanced_visible else "▶ Advanced")
    
    def get_verification_algorithm(self) -> str:
        """Convert display name to actual algorithm name for engine"""
        display_text = self.verify_combo.currentText()

        # Map display names to actual algorithm names
        algorithm_mapping = {
            "xxHash64BE (Netflix Standard)": "xxhash64be",
            "xxHash64BE (Netflix)": "xxhash64be",
            "xxHash128 (Fast, Secure)": "xxhash128",
            "xxHash128 (Fast)": "xxhash128",
            "SHA-256 (Secure)": "sha256",
            "SHA-256": "sha256",
            "SHA-3 (Latest Standard)": "sha3",
            "SHA-3": "sha3",
            "MD5 (Legacy Compatible)": "md5",
            "MD5 (Legacy)": "md5"
        }

        return algorithm_mapping.get(display_text, "xxhash64be")  # Default to Netflix standard
    
    def _select_blast_cache_drive(self):
        """Open directory selector for BLAST cache drive"""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setWindowTitle("Select BLAST Cache Drive")
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        if dialog.exec():
            selected_dirs = dialog.selectedFiles()
            if selected_dirs:
                cache_path = selected_dirs[0]
                self._blast_cache_path = cache_path
                
                # Update display with shortened path
                import os
                display_path = os.path.basename(cache_path) if cache_path else cache_path
                self.blast_cache_display.setText(f"📦 {display_path}")
                self.blast_cache_display.setToolTip(f"BLAST Cache: {cache_path}\n\nThis will enable cache-and-distribute workflow:\n• Copy from source to cache drive first\n• Then distribute to all destinations in parallel\n• Allows source removal during distribution")
                
                print(f"DEBUG: BLAST cache drive selected: {cache_path}")
    
    def _clear_blast_cache_drive(self):
        """Clear BLAST cache drive selection"""
        self._blast_cache_path = None
        self.blast_cache_display.setText("None selected")
        self.blast_cache_display.setToolTip("Select a fast SSD for cache-and-distribute workflow.\nLeave empty for direct parallel copying.")
        print("DEBUG: BLAST cache drive cleared - using direct copying mode")
    
    def get_blast_cache_drive(self) -> str:
        """Get the selected BLAST cache drive path"""
        return self._blast_cache_path
