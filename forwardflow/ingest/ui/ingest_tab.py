"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built here to keep ingest self-contained. The host app
calls `build_ingest_tab()` under a feature flag to add the tab.
"""

from __future__ import annotations

import os
import time
import threading
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import collections # Added for rolling speed calculation

from PyQt6.QtCore import (
    QTimer,
    Qt,
    pyqtSignal,
    QObject,
    QThread,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSlider,
    QComboBox,
    QFrame,
    QSizePolicy,
    QGroupBox,
    QGridLayout,
    QFileDialog,
    QScrollArea,
    QCheckBox,
)

from .ingest_vm import IngestViewModel
from .file_progress_line import FileProgressLine
from ..engines.python_engine import PythonCopyEngine
from forwardflow.ingest.runtime.crash_first_aid import enable as _crash_enable
_crash_enable()
from forwardflow.ingest.ui.qt_safe_bridge import get_bridge, emit_event, cleanup_bridge
from PyQt6 import QtCore, QtWidgets
from ..api.models import JobSpec, JobOptions

# Import styling from the main app
try:
    from app.ui.color_scheme_pyqt import (
        colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE, DANGER_BUTTON_STYLE,
        LINEEDIT_STYLE, LABEL_STYLE, COMBOBOX_STYLE,
        GROUPBOX_STYLE, PROGRESS_BAR_STYLE, SCROLL_AREA_STYLE,
        SLIDER_STYLE, SECTION_HEADER_STYLE,
        SECONDARY_TEXT_STYLE, HEADER_LABEL_STYLE, FIELD_LABEL_STYLE,
        TIME_LABEL_STYLE, ACCENT_VALUE_STYLE, CARD_FRAME_STYLE,
        SUMMARY_METRIC_STYLE
    )
    from app.ui.custom_delegates import apply_hover_delegate
    print("DEBUG: Successfully imported centralized styles and hover delegate from app.ui.color_scheme_pyqt")
    STYLING_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Failed to import centralized styles: {e}")
    raise ImportError("Centralized styles are required for the ingest tab")


def load_recent_locations():
    """Load recent source and destination locations from config"""
    try:
        from app.core.config_manager import get_settings_path
        settings_dir = get_settings_path()
        recent_file = os.path.join(settings_dir, "recent_locations.json")
        
        if os.path.exists(recent_file):
            with open(recent_file, 'r') as f:
                data = json.load(f)
                return data.get('sources', []), data.get('destinations', [])
    except Exception as e:
        print(f"DEBUG: Failed to load recent locations: {e}")
    
    return [], []


def save_recent_locations(sources, destinations):
    """Save recent source and destination locations to config"""
    try:
        from app.core.config_manager import get_settings_path
        settings_dir = get_settings_path()
        recent_file = os.path.join(settings_dir, "recent_locations.json")
        
        data = {
            'sources': sources[:5],  # Keep last 5
            'destinations': destinations[:5]  # Keep last 5
        }
        
        with open(recent_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"DEBUG: Failed to save recent locations: {e}")


def add_to_recent_locations(path, is_source=True):
    """Add a path to recent locations"""
    sources, destinations = load_recent_locations()
    
    if is_source:
        if path in sources:
            sources.remove(path)
        sources.insert(0, path)
        sources = sources[:5]  # Keep last 5
    else:
        if path in destinations:
            destinations.remove(path)
        destinations.insert(0, path)
        destinations = destinations[:5]  # Keep last 5
    
    save_recent_locations(sources, destinations)


def build_ingest_tab():
    """Build the ingest tab UI."""
    print("DEBUG: Building ingest tab...")
    
    # Create the main widget
    root = QWidget()
    root.setObjectName("ingest_tab")  # Changed back to match expected name
    
    # Initialize file tracking
    root.file_widgets = {}
    root.active_files = 0
    root.current_job = None
    root.job_start_time = None
    root.total_bytes = 0
    root.copied_bytes = 0
    
    # Speed tracking for rolling calculations
    root._speed_samples = collections.deque(maxlen=8)  # 8×100ms ≈ 0.8 s
    root._last_speed_update = None
    root._last_bytes = 0
    
    # Load recent locations
    recent_sources, recent_destinations = load_recent_locations()
    
    # Main layout
    layout = QVBoxLayout(root)
    layout.setContentsMargins(0, 0, 0, 0)  # No margins - title goes to very top
    layout.setSpacing(6)  # Further reduced spacing between sections
    
    # Set minimum dimensions to prevent UI collapse and ensure full visibility
    root.setMinimumWidth(1000)  # Increased minimum width for better layout
    root.setMinimumHeight(700)  # Reduced minimum height to fit in smaller windows
    
    print("DEBUG: Creating IngestViewModel...")
    vm = IngestViewModel()
    print("DEBUG: IngestViewModel created successfully")
    
    # Make vm accessible to the widget
    root.vm = vm
    print("DEBUG: VM attached to root widget")
    
    # Timer for updating elapsed time display
    root.time_update_timer = QTimer()
    root.time_update_timer.timeout.connect(lambda: update_elapsed_time())
    root.time_update_timer.start(1000)  # Update every second
    
    # Timer for updating stats more frequently
    root.stats_update_timer = QTimer()
    root.stats_update_timer.timeout.connect(lambda: update_stats())
    root.stats_update_timer.start(100)  # Update every 100ms for real-time responsiveness
    
    def update_elapsed_time():
        """Update elapsed time display every second"""
        if root.job_start_time and root.current_job:
            elapsed_seconds = time.time() - root.job_start_time
            elapsed_str = f"{int(elapsed_seconds//3600):02d}:{int((elapsed_seconds%3600)//60):02d}:{int(elapsed_seconds%60):02d}"
            root.elapsed_label.setText(elapsed_str)
    
    def update_stats():
        """Update speed and progress stats less frequently to prevent UI blocking"""
        if root.job_start_time and root.current_job and hasattr(root, 'copied_bytes') and hasattr(root, 'total_bytes'):
            elapsed_seconds = time.time() - root.job_start_time
            if elapsed_seconds > 0 and root.total_bytes > 0:
                # Calculate current speed
                current_speed = (root.copied_bytes / (1024 * 1024)) / elapsed_seconds
                
                # Update progress bar (only if it exists and hasn't been updated recently)
                if hasattr(root, 'total_progress') and root.total_progress:
                    progress_percent = int((root.copied_bytes / root.total_bytes) * 100)
                    # Only update if the value has changed significantly
                    if not hasattr(root, '_last_progress_percent') or abs(progress_percent - root._last_progress_percent) >= 1:
                        root.total_progress.setValue(progress_percent)
                        root.total_progress.setFormat(f"{progress_percent}%")
                        root._last_progress_percent = progress_percent
                
                # Update current speed stat (only if it exists)
                if hasattr(root, 'current_speed_label') and root.current_speed_label:
                    root.current_speed_label.setText(f"{current_speed:.0f} MB/s")
                
                # Calculate average speed (only if it exists)
                if hasattr(root, 'avg_speed_label') and root.avg_speed_label:
                    # FIXED: Average speed should be copied_bytes / elapsed_time, not total_bytes / elapsed_time
                    avg_speed = (root.copied_bytes / elapsed_seconds) / (1024 * 1024)
                    root.avg_speed_label.setText(f"{avg_speed:.0f} MB/s")
                
                # Update peak speed if current speed is higher (only if it exists)
                if hasattr(root, 'peak_speed_label') and root.peak_speed_label:
                    try:
                        current_peak_text = root.peak_speed_label.text()
                        # Parse current peak value (format: "XXX MB/s" or "0 MB/s")
                        if " MB/s" in current_peak_text:
                            current_peak = float(current_peak_text.split(' ')[0])
                            if current_speed > current_peak:
                                root.peak_speed_label.setText(f"{current_speed:.0f} MB/s")
                        else:
                            # If we can't parse, initialize with current speed
                            root.peak_speed_label.setText(f"{current_speed:.0f} MB/s")
                    except (ValueError, IndexError):
                        # If we can't parse the current peak, just set it
                        root.peak_speed_label.setText(f"{current_speed:.0f} MB/s")
                
                # Calculate ETA (only if it exists)
                if hasattr(root, 'eta_label') and root.eta_label and current_speed > 0 and root.copied_bytes < root.total_bytes:
                    remaining_bytes = root.total_bytes - root.copied_bytes
                    eta_seconds = remaining_bytes / (current_speed * 1024 * 1024)
                    if eta_seconds > 0:
                        eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                        root.eta_label.setText(eta_str)
                    else:
                        root.eta_label.setText("--:--:--")
                elif hasattr(root, 'eta_label') and root.eta_label:
                    root.eta_label.setText("--:--:--")
                
                # Remove forced repaints - let Qt handle updates naturally
                # This prevents beachballing caused by excessive UI updates
    
    def _rolling_speed_human(self):
        """Calculate rolling speed and return human-readable string."""
        t = time.monotonic()
        if self._last_speed_update is not None:
            dt = t - self._last_speed_update
            db = self.copied_bytes - self._last_bytes
            if dt > 0:
                self._speed_samples.append(db/dt)  # bytes/sec
                mbps = (sum(self._speed_samples)/len(self._speed_samples))/(1024*1024) if self._speed_samples else 0.0
                return f"{mbps:.1f} MB/s Transfer"
        self._last_speed_update = t
        self._last_bytes = self.copied_bytes
        return "0.0 MB/s Transfer"
    
    # Title at the very top with minimal margin
    title = QLabel("Turbo Transfer")
    title.setStyleSheet(HEADER_LABEL_STYLE)
    title.setFixedHeight(30)  # Reduced height
    title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    title.setContentsMargins(10, 2, 10, 2)  # Reduced padding inside title
    layout.addWidget(title)
    
    # Paths section
    paths_layout = QVBoxLayout()
    paths_layout.setSpacing(8)  # Further reduced spacing
    paths_layout.setContentsMargins(0, 0, 0, 0)
    
    # Source section - inline layout
    src_layout = QHBoxLayout()
    src_layout.setSpacing(10)  # Spacing between label and dropdown
    src_layout.setContentsMargins(0, 0, 0, 0)
    
    src_label = QLabel("Source:")
    src_label.setStyleSheet(FIELD_LABEL_STYLE)
    src_label.setFixedHeight(38)  # Match combo box height
    src_label.setFixedWidth(60)  # Fixed width for consistency
    src_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
    
    src_combo = QComboBox()
    src_combo.setEditable(True)
    src_combo.setStyleSheet(COMBOBOX_STYLE)
    src_combo.setPlaceholderText("Select source folder...")
    src_combo.setFixedHeight(38)  # Match button height
    src_combo.setMinimumHeight(38)
    src_combo.setMaximumHeight(38)
    
    # Add recent sources to dropdown
    for source in recent_sources:
        src_combo.addItem(source)
    
    src_btn = QPushButton("Browse...")
    src_btn.setObjectName("src_btn")
    src_btn.setStyleSheet(BUTTON_STYLE)  # Use app-wide button styling
    src_btn.setFixedHeight(38)  # Fixed height for consistency
    src_btn.setFixedWidth(110)  # Fixed width for consistency
    
    src_layout.addWidget(src_label)
    src_layout.addWidget(src_combo, 1)
    src_layout.addWidget(src_btn)
    
    paths_layout.addLayout(src_layout)
    
    # Destinations section with pinned header and scrollable content
    dest_frame = QFrame()
    dest_frame.setStyleSheet(CARD_FRAME_STYLE)
    dest_layout = QVBoxLayout(dest_frame)
    dest_layout.setSpacing(8)  # Further reduced spacing
    dest_layout.setContentsMargins(12, 12, 12, 12)  # Further reduced padding
    
    # Destinations header (pinned to top)
    dest_header = QHBoxLayout()
    dest_header.setSpacing(10)  # Reduced spacing
    dest_header.setContentsMargins(0, 0, 0, 0)
    dest_label = QLabel("Destinations:")
    dest_label.setStyleSheet(FIELD_LABEL_STYLE)
    dest_label.setFixedHeight(25)  # Fixed height for consistency
    
    # Destinations dropdown - now automatically adds destinations when clicked
    dest_combo = QComboBox()
    dest_combo.setEditable(True)
    dest_combo.setStyleSheet(COMBOBOX_STYLE)
    dest_combo.setPlaceholderText("Select destination folder...")
    dest_combo.setFixedHeight(38)  # Match button height
    dest_combo.setMinimumHeight(38)
    dest_combo.setMaximumHeight(38)
    
    # Add recent destinations to dropdown
    for destination in recent_destinations:
        dest_combo.addItem(destination)
    
    # Connect dropdown selection to automatic destination addition
    def on_destination_selected(index):
        """Automatically add destination when selected from dropdown"""
        if index >= 0:
            path = dest_combo.currentText().strip()
            if path and path != dest_combo.placeholderText():
                # Check if destination already exists
                existing_paths = [dest.get("path", "") for dest in root.destinations]
                if path not in existing_paths:
                    add_destination_from_path(path)
                    # Clear the dropdown after adding
                    dest_combo.setCurrentText("")
    
    dest_combo.currentIndexChanged.connect(on_destination_selected)
    
    add_dest_btn = QPushButton("+ Add Destination")
    add_dest_btn.setObjectName("add_dest_btn")
    add_dest_btn.setStyleSheet(BUTTON_STYLE)  # Use app-wide button styling
    add_dest_btn.setFixedHeight(38)  # Fixed height for consistency
    add_dest_btn.setFixedWidth(150)  # Fixed width for consistency
    
    dest_header.addWidget(dest_label)
    dest_header.addWidget(dest_combo, 1)
    dest_header.addWidget(add_dest_btn)
    dest_layout.addLayout(dest_header, 0)  # Header stays fixed - no stretch
    
    # Destinations list (scrollable with expandable height)
    dest_scroll = QScrollArea()
    dest_scroll.setWidgetResizable(True)
    dest_scroll.setMinimumHeight(150)  # Increased minimum height to show bottom clearly
    dest_scroll.setMaximumHeight(800)  # Increased max height for more destinations when expanded
    dest_scroll.setStyleSheet(SCROLL_AREA_STYLE)
    dest_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    dest_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    dest_container = QWidget()
    dest_container_layout = QVBoxLayout(dest_container)
    dest_container_layout.setSpacing(4)  # Further reduced spacing
    dest_container_layout.setContentsMargins(6, 6, 6, 6)  # Further reduced margins
    dest_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    
    dest_scroll.setWidget(dest_container)
    dest_layout.addWidget(dest_scroll, 1)  # Scroll area gets stretch factor - this expands
    
    paths_layout.addWidget(dest_frame, 1)  # Add stretch - allow expansion
    
    # Store references for later use
    root.dest_container = dest_container
    root.dest_container_layout = dest_container_layout
    root.destinations = []  # List of destination objects
    root.src_combo = src_combo
    root.dest_combo = dest_combo
    
    layout.addLayout(paths_layout, 1)  # Add stretch - allow expansion for destinations
    
    # Settings section
    settings_container = QWidget()
    settings_container.setMinimumWidth(800)  # Increased minimum width to prevent collapse
    settings_container.setMinimumHeight(140)  # Increased height to prevent transfer settings cutoff
    settings_layout = QVBoxLayout(settings_container)
    settings_layout.setSpacing(6)  # Tighter spacing to save vertical space
    settings_layout.setContentsMargins(15, 4, 15, 8)  # Reduced top margin to bring closer to destinations
    
    # Transfer Settings
    transfer_container = QWidget()
    transfer_container.setMinimumWidth(400)  # Increased minimum width to prevent collapse
    transfer_container.setMinimumHeight(130)  # Increased height to prevent label cutoff
    transfer_settings_layout = QVBoxLayout(transfer_container)
    transfer_settings_layout.setSpacing(10)  # Increased spacing to prevent label cutoff
    
    # Transfer Settings Header with Generate Verification Report checkbox (right justified)
    header_layout = QHBoxLayout()
    header_layout.setSpacing(20)  # Increased spacing for better breathing room
    header_layout.setContentsMargins(0, 0, 0, 0)
    
    transfer_header = QLabel("Transfer Settings")
    transfer_header.setStyleSheet(SECTION_HEADER_STYLE)
    transfer_header.setFixedHeight(30)  # Increased height for better visibility
    
    # Generate Verification Report checkbox (right justified)
    report_checkbox = QCheckBox("Generate Verification Report")
    report_checkbox.setChecked(True)  # Default to enabled
    report_checkbox.setStyleSheet(f"""
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
    report_checkbox.setFixedHeight(30)
    
    header_layout.addWidget(transfer_header)
    header_layout.addStretch()  # Push checkbox to the right
    header_layout.addWidget(report_checkbox)
    
    transfer_settings_layout.addLayout(header_layout)
    
    # Single row: All controls on one line using full width
    controls_row = QHBoxLayout()
    controls_row.setSpacing(30)  # Increased spacing for better separation
    controls_row.setContentsMargins(0, 0, 0, 0)
    
    # Global Preset (expands with available space)
    preset_layout = QVBoxLayout()
    preset_layout.setSpacing(5)
    preset_label = QLabel("Global Preset:")
    preset_label.setStyleSheet(FIELD_LABEL_STYLE)
    preset_label.setFixedHeight(18)
    preset_combo = QComboBox()
    preset_combo.addItems([
        "Auto (recommended)",
        "USB/TB",
        "Network",
        "Custom"
    ])
    preset_combo.setStyleSheet(COMBOBOX_STYLE)
    preset_combo.setCurrentIndex(0)
    preset_combo.setFixedHeight(28)
    preset_combo.setMinimumWidth(150)  # Increased minimum width
    # Remove maximum width constraint to allow expansion
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(preset_combo)
        print("DEBUG: Applied hover delegate to preset_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to preset_combo: {e}")
    
    preset_layout.addWidget(preset_label)
    preset_layout.addWidget(preset_combo)
    controls_row.addLayout(preset_layout, 1)  # Add stretch factor
    
    # Verify Mode (expands with available space)
    verify_layout = QVBoxLayout()
    verify_layout.setSpacing(5)
    verify_label = QLabel("Verify Mode:")
    verify_label.setStyleSheet(FIELD_LABEL_STYLE)
    verify_label.setFixedHeight(18)
    verify_combo = QComboBox()
    verify_combo.addItems([
        "FAST",
        "STREAM_VERIFY",
        "READBACK_VERIFY"
    ])
    verify_combo.setStyleSheet(COMBOBOX_STYLE)
    verify_combo.setCurrentIndex(0)
    verify_combo.setFixedHeight(28)
    verify_combo.setMinimumWidth(140)  # Increased minimum width
    # Remove maximum width constraint to allow expansion
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(verify_combo)
        print("DEBUG: Applied hover delegate to verify_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to verify_combo: {e}")
    
    # Auto-update verification report checkbox based on verify mode
    def on_verify_mode_changed():
        current_mode = verify_combo.currentText()
        # Auto-enable verification report for verification modes other than FAST
        if current_mode in ["STREAM_VERIFY", "READBACK_VERIFY"]:
            report_checkbox.setChecked(True)
            report_checkbox.setToolTip("Verification report automatically enabled for verification modes")
        else:
            # For FAST mode, leave user's choice but show helpful tooltip
            report_checkbox.setToolTip("Optional verification report (recommended for audit trails)")
        print(f"DEBUG: Verify mode changed to {current_mode}, report checkbox: {report_checkbox.isChecked()}")
    
    # Connect the signal after the function is defined
    verify_combo.currentTextChanged.connect(on_verify_mode_changed)
    
    verify_layout.addWidget(verify_label)
    verify_layout.addWidget(verify_combo)
    controls_row.addLayout(verify_layout, 1)  # Add stretch factor
    
    # Per-file concurrency (expands with available space)
    conc_layout = QVBoxLayout()
    conc_layout.setSpacing(5)
    conc_label = QLabel("Per-file concurrency:")
    conc_label.setStyleSheet(FIELD_LABEL_STYLE)
    conc_label.setFixedHeight(18)
    conc_slider = QSlider(Qt.Orientation.Horizontal)
    conc_slider.setRange(1, 16)
    conc_slider.setValue(2)
    conc_slider.setStyleSheet(SLIDER_STYLE)
    conc_slider.setFixedHeight(22)
    conc_slider.setMinimumHeight(22)
    conc_slider.setMaximumHeight(22)
    conc_slider.setMinimumWidth(150)  # Increased minimum width
    # Remove maximum width constraint to allow expansion
    conc_value = QLabel("2")
    conc_value.setStyleSheet(ACCENT_VALUE_STYLE)
    conc_value.setFixedHeight(22)
    conc_value.setFixedWidth(25)
    conc_slider.valueChanged.connect(lambda v: conc_value.setText(str(v)))
    
    conc_row = QHBoxLayout()
    conc_row.setSpacing(8)
    conc_row.addWidget(conc_slider, 1)
    conc_row.addWidget(conc_value)
    
    conc_layout.addWidget(conc_label)
    conc_layout.addLayout(conc_row)
    controls_row.addLayout(conc_layout, 1)  # Add stretch factor
    
    # Stream concurrency (expands with available space)
    stream_layout = QVBoxLayout()
    stream_layout.setSpacing(5)
    stream_label = QLabel("Stream concurrency:")
    stream_label.setStyleSheet(FIELD_LABEL_STYLE)
    stream_label.setFixedHeight(18)
    stream_slider = QSlider(Qt.Orientation.Horizontal)
    stream_slider.setRange(1, 32)
    stream_slider.setValue(4)
    stream_slider.setStyleSheet(SLIDER_STYLE)
    stream_slider.setFixedHeight(22)
    stream_slider.setMinimumHeight(22)
    stream_slider.setMaximumHeight(22)
    stream_slider.setMinimumWidth(150)  # Increased minimum width
    # Remove maximum width constraint to allow expansion
    stream_value = QLabel("4")
    stream_value.setStyleSheet(ACCENT_VALUE_STYLE)
    stream_value.setFixedHeight(22)
    stream_value.setFixedWidth(25)
    stream_slider.valueChanged.connect(lambda v: stream_value.setText(str(v)))
    
    stream_row = QHBoxLayout()
    stream_row.setSpacing(8)
    stream_row.addWidget(stream_slider, 1)
    stream_row.addWidget(stream_value)
    
    stream_layout.addWidget(stream_label)
    stream_layout.addLayout(stream_row)
    controls_row.addLayout(stream_layout, 1)  # Add stretch factor
    
    transfer_settings_layout.addLayout(controls_row)
    
    # Add spacer to push everything to the top
    transfer_settings_layout.addStretch()
    
    # Add transfer settings to settings layout
    settings_layout.addWidget(transfer_container)
    
    # Store widget references in root for access from button handlers
    root.preset_combo = preset_combo
    root.verify_combo = verify_combo
    root.conc_slider = conc_slider
    root.stream_slider = stream_slider
    root.report_checkbox = report_checkbox
    root.src_combo = src_combo
    root.dest_combo = dest_combo
    root.dest_container_layout = dest_container_layout
    root.destinations = []
    root.current_job = None
    root.job_timer = None
    root.progress_update_timer = None
    root.src_btn = src_btn
    root.add_dest_btn = add_dest_btn
    
    # Add settings container to main layout
    layout.addWidget(settings_container, 0)  # No stretch - keep fixed size
    
    # Control buttons - moved closer to transfer settings for better layout
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(10)  # Reduced spacing
    buttons_layout.setContentsMargins(0, 10, 0, 15)  # Add some margin around buttons
    
    # Start button
    start_btn = QPushButton("Start Transfer")
    start_btn.setObjectName("start_btn")
    start_btn.setStyleSheet(ACCENT_BUTTON_STYLE)
    start_btn.setFixedHeight(45)  # Increased from 40 for better button size
    start_btn.setEnabled(False)
    
    # Pause button
    pause_btn = QPushButton("Pause")
    pause_btn.setObjectName("pause_btn")
    pause_btn.setStyleSheet(BUTTON_STYLE)
    pause_btn.setFixedHeight(45)  # Increased from 40 for better button size
    pause_btn.setEnabled(False)
    
    # Cancel button
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setObjectName("cancel_btn")
    cancel_btn.setStyleSheet(DANGER_BUTTON_STYLE)
    cancel_btn.setFixedHeight(45)  # Increased from 40 for better button size
    cancel_btn.setEnabled(False)
    
    buttons_layout.addWidget(start_btn)
    buttons_layout.addWidget(pause_btn)
    buttons_layout.addWidget(cancel_btn)
    buttons_layout.addStretch()  # Add stretch to push buttons to the left
    
    # Store button references in root for access by event handlers
    root.start_btn = start_btn  # Store start button reference
    root.pause_btn = pause_btn
    root.cancel_btn = cancel_btn
    
    layout.addLayout(buttons_layout, 0)  # No stretch - keep fixed size
    
    # Main progress display (clean, compact)
    progress_frame = QFrame()
    progress_frame.setStyleSheet(CARD_FRAME_STYLE)
    progress_frame.setMinimumHeight(60)  # Reduced height to save space
    progress_layout = QVBoxLayout(progress_frame)
    progress_layout.setSpacing(8)  # Further reduced spacing
    progress_layout.setContentsMargins(12, 12, 12, 12)  # Further reduced padding
    
    # Total progress with integrated label - prominently sized for visibility
    total_progress = QProgressBar()
    total_progress.setRange(0, 100)
    total_progress.setValue(0)
    total_progress.setFixedHeight(60)  # 2.5x taller for prominence (was 24px)
    # Custom style to override min-height constraint and make progress bar prominent
    total_progress.setStyleSheet(f"""
        QProgressBar {{
            border: 1px solid {colors['border']};
            border-radius: 3px;
            text-align: center;
            background-color: {colors['bg']};
            color: {colors['text']};
            font-size: 14px;
            font-weight: 600;
            margin: 0;
            padding: 0;
            min-height: 60px;
            max-height: 60px;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                       stop:0 #2d5a2d, 
                                       stop:0.5 #4a7c4a, 
                                       stop:1 #6ba06b);
            border-radius: 2px;
        }}
    """)
    total_progress.setVisible(True)  # Ensure it's visible
    total_progress.setEnabled(True)  # Ensure it's enabled
    total_progress.setFormat("%p%")  # Show percentage
    total_progress.setTextVisible(True)  # Ensure text is visible
    
    # Add progress bar with normal layout
    progress_layout.addWidget(total_progress)
    
    # Debug progress bar setup
    print(f"DEBUG: Progress bar created with range 0-100, height 60px")
    print(f"DEBUG: Progress bar is visible: {total_progress.isVisible()}")
    print(f"DEBUG: Progress bar is enabled: {total_progress.isEnabled()}")
    print(f"DEBUG: Progress bar size: {total_progress.size()}")
    print(f"DEBUG: Progress bar style: {total_progress.styleSheet()[:100]}...")
    print(f"DEBUG: Progress bar format: {total_progress.format()}")
    print(f"DEBUG: Progress bar text visible: {total_progress.isTextVisible()}")
    print(f"DEBUG: Progress bar initial value: {total_progress.value()}")
    
    # Add stats labels directly on top of the progress card (no separate card background)
    stats_layout = QVBoxLayout()
    stats_layout.setSpacing(1)  # Minimal spacing between header and values
    stats_layout.setContentsMargins(12, 4, 12, 4)  # Minimal padding
    
    # Create compact, direct labels without container widgets (no card backgrounds)
    # Elapsed time
    elapsed_header = QLabel("Elapsed")
    elapsed_header.setStyleSheet(f"""
        QLabel {{
            color: {colors['secondary_text']};
            font-size: 10px;
            font-weight: 500;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    elapsed_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    elapsed_label = QLabel("00:00:00")
    elapsed_label.setStyleSheet(f"""
        QLabel {{
            color: {colors['text']};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    elapsed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # ETA
    eta_header = QLabel("ETA")
    eta_header.setStyleSheet(f"""
        QLabel {{
            color: {colors['secondary_text']};
            font-size: 10px;
            font-weight: 500;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    eta_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    eta_label = QLabel("--:--:--")
    eta_label.setStyleSheet(f"""
        QLabel {{
            color: {colors['text']};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Current speed
    speed_header = QLabel("Speed")
    speed_header.setStyleSheet(f"""
        QLabel {{
            color: {colors['secondary_text']};
            font-size: 10px;
            font-weight: 500;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    speed_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    current_speed_label = QLabel("0 MB/s")
    current_speed_label.setStyleSheet(f"""
        QLabel {{
            color: {colors['text']};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    current_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Average speed
    avg_header = QLabel("Avg")
    avg_header.setStyleSheet(f"""
        QLabel {{
            color: {colors['secondary_text']};
            font-size: 10px;
            font-weight: 500;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    avg_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    avg_speed_label = QLabel("0 MB/s")
    avg_speed_label.setStyleSheet(f"""
        QLabel {{
            color: {colors['text']};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    avg_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Peak speed
    peak_header = QLabel("Peak")
    peak_header.setStyleSheet(f"""
        QLabel {{
            color: {colors['secondary_text']};
            font-size: 10px;
            font-weight: 500;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    peak_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    peak_speed_label = QLabel("0 MB/s")
    peak_speed_label.setStyleSheet(f"""
        QLabel {{
            color: {colors['text']};
            font-size: 13px;
            font-weight: 600;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            text-align: center;
            margin: 0;
            padding: 2px;
        }}
    """)
    peak_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Add headers in a row (much more compact)
    headers_layout = QHBoxLayout()
    headers_layout.setSpacing(0)
    headers_layout.setContentsMargins(0, 0, 0, 0)
    headers_layout.addWidget(elapsed_header, 1)
    headers_layout.addWidget(eta_header, 1)
    headers_layout.addWidget(speed_header, 1)
    headers_layout.addWidget(avg_header, 1)
    headers_layout.addWidget(peak_header, 1)
    
    # Add values in a row (much more compact)
    values_layout = QHBoxLayout()
    values_layout.setSpacing(0)
    values_layout.setContentsMargins(0, 0, 0, 0)
    values_layout.addWidget(elapsed_label, 1)
    values_layout.addWidget(eta_label, 1)
    values_layout.addWidget(current_speed_label, 1)
    values_layout.addWidget(avg_speed_label, 1)
    values_layout.addWidget(peak_speed_label, 1)
    
    # Add both rows to stats layout
    stats_layout.addLayout(headers_layout)
    stats_layout.addLayout(values_layout)
    
    # Add the stats layout to the progress frame instead of creating a separate frame
    progress_layout.addLayout(stats_layout)
    
    layout.addWidget(progress_frame, 0)  # No stretch - keep fixed size
    
    # Files frame - store for later use and ensure proper display
    files_frame = QFrame()
    files_frame.setStyleSheet(CARD_FRAME_STYLE)
    files_frame.setMinimumHeight(60)  # Tighter height for Transfer Status
    files_layout = QVBoxLayout(files_frame)
    files_layout.setSpacing(4)  # Tighter spacing
    files_layout.setContentsMargins(12, 6, 12, 6)  # Tighter top/bottom padding
    
    # Compact Transfer Status display
    files_header = QHBoxLayout()
    files_header.setSpacing(5)
    files_header.setContentsMargins(0, 0, 0, 0)
    files_label = QLabel("Transfer Status")
    files_label.setStyleSheet(SECTION_HEADER_STYLE)
    files_count = QLabel("0 of 0 files")
    files_count.setStyleSheet(SUMMARY_METRIC_STYLE)
    files_header.addWidget(files_label)
    files_header.addStretch()
    files_header.addWidget(files_count)
    files_layout.addLayout(files_header)
    
    # Store references to labels and progress bar for event handlers
    root.elapsed_label = elapsed_label
    root.eta_label = eta_label
    root.current_speed_label = current_speed_label
    root.avg_speed_label = avg_speed_label
    root.peak_speed_label = peak_speed_label
    root.total_progress = total_progress
    root.files_count = files_count
    

    
    # PROFESSIONAL DIT APPROACH: No complex file widgets, just clean status
    # Professional DIT tools focus on job-level progress, not individual file scrolling
    
    # Store simple file count reference
    root.files_count = files_count
    
    layout.addWidget(files_frame, 0)  # No stretch - keep compact
    
    # Destination management functions
    def add_destination_from_path(path):
        """Add a destination from a given path"""
        if path:
            # Add to recent destinations
            add_to_recent_locations(path, is_source=False)
            
            dest_obj = {
                "path": path,
                "preset": "auto",
                "block_size": None,
                "files_in_flight": None,
                "ranges_per_file": None,
                "use_direct_io": None,
                "verify": "FAST",
                "progress_bar": None  # Will be set when widget is created
            }
            root.destinations.append(dest_obj)
            create_destination_widget(dest_obj)
            check_button_states()
    
    def add_destination():
        """Add a new destination to the list"""
        # Use the dropdown value if it has text, otherwise show file dialog
        path = root.dest_combo.currentText().strip()
        if not path or path == root.dest_combo.placeholderText():
            path = QFileDialog.getExistingDirectory(
                root,
                "Select Destination Folder",
                "",
                QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )
        
        if path:
            add_destination_from_path(path)
            # Clear the dropdown
            root.dest_combo.setCurrentText("")
    
    def create_destination_widget(dest_obj):
        """Create a widget for a destination"""
        dest_widget = QFrame()
        dest_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 3px;
                padding: 5px;
            }}
        """)
        
        dest_layout = QVBoxLayout(dest_widget)
        dest_layout.setSpacing(6)  # Slightly increased spacing for better visibility
        dest_layout.setContentsMargins(8, 8, 8, 8)  # Increased padding to prevent cutoff
        
        # Top row: path and controls
        top_row = QHBoxLayout()
        top_row.setSpacing(8)  # Slightly increased spacing for better alignment
        top_row.setContentsMargins(0, 0, 0, 0)
        
        # Path display
        path_label = QLabel(dest_obj["path"])
        path_label.setStyleSheet(LABEL_STYLE)
        path_label.setWordWrap(True)
        path_label.setMinimumHeight(28)  # Match combo box height for alignment
        path_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically
        top_row.addWidget(path_label, 1)
        
        # Preset dropdown
        preset_combo = QComboBox()
        preset_combo.addItems(["Auto", "USB/TB", "Network", "Custom"])
        preset_combo.setCurrentText(dest_obj["preset"])
        preset_combo.setStyleSheet(COMBOBOX_STYLE)
        preset_combo.setFixedHeight(28)  # Fixed height to match path label
        preset_combo.setMinimumWidth(100)  # Ensure minimum width
        preset_combo.currentTextChanged.connect(lambda text: update_dest_preset(dest_obj, text))
        top_row.addWidget(preset_combo)
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)  # Slightly larger for better visibility
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #902A2A;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #A33030;
            }}
        """)
        remove_btn.clicked.connect(lambda: remove_destination(dest_obj, dest_widget))
        top_row.addWidget(remove_btn)
        
        dest_layout.addLayout(top_row)
        
        # Transfer type and buffer info row with Ready status on same line
        info_row = QHBoxLayout()
        info_row.setSpacing(15)  # Increased spacing between elements
        
        # Detect transfer type and optimal buffer size
        print(f"DEBUG: Attempting to detect transfer type for destination: {dest_obj['path']}")
        try:
            from forwardflow.ingest.utils.memory_manager import MemoryManager
            print("DEBUG: Successfully imported MemoryManager")
            memory_manager = MemoryManager()
            print("DEBUG: Created MemoryManager instance")
            transfer_type = memory_manager._detect_transfer_type(dest_obj["path"])
            print(f"DEBUG: Detected transfer type: {transfer_type}")
            optimal_buffer = memory_manager.get_optimal_buffer_size_for_destination(dest_obj["path"], "auto")
            print(f"DEBUG: Calculated optimal buffer: {optimal_buffer:.1f}MB")
            
            # Transfer type label with proper height and width to prevent cutoff
            type_label = QLabel(f"Type: {transfer_type.upper()}")
            type_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            type_label.setMinimumHeight(24)  # Increased min height to prevent cutoff
            type_label.setFixedHeight(24)
            type_label.setMinimumWidth(120)  # Increased minimum width to prevent cutoff
            info_row.addWidget(type_label)
            print(f"DEBUG: Added type label: Type: {transfer_type.upper()}")
            
            # Optimal buffer size label with proper height and width to prevent cutoff
            buffer_label = QLabel(f"Optimal Buffer: {optimal_buffer:.1f}MB")
            buffer_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            buffer_label.setMinimumHeight(24)  # Increased min height to prevent cutoff
            buffer_label.setFixedHeight(24)
            buffer_label.setMinimumWidth(150)  # Increased minimum width to prevent cutoff
            info_row.addWidget(buffer_label)
            print(f"DEBUG: Added buffer label: Optimal Buffer: {optimal_buffer:.1f}MB")
            
        except Exception as e:
            print(f"DEBUG: Could not detect transfer type for {dest_obj['path']}: {e}")
            import traceback
            traceback.print_exc()
            # Fallback labels with proper height to prevent cutoff
            type_label = QLabel("Type: Unknown")
            type_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            type_label.setMinimumHeight(24)  # Increased min height to prevent cutoff
            type_label.setFixedHeight(24)
            type_label.setMinimumWidth(120)
            info_row.addWidget(type_label)
            
            buffer_label = QLabel("Optimal Buffer: 1.0MB")
            buffer_label.setStyleSheet(SECONDARY_TEXT_STYLE)
            buffer_label.setMinimumHeight(24)  # Increased min height to prevent cutoff
            buffer_label.setFixedHeight(24)
            buffer_label.setMinimumWidth(150)
            info_row.addWidget(buffer_label)
        
        info_row.addStretch()  # Push labels to the left
        

        
        dest_layout.addLayout(info_row)
        
        # Progress bar row with enhanced information
        progress_row = QHBoxLayout()
        progress_row.setSpacing(5)
        
        # Progress bar for this destination
        dest_progress = QProgressBar()
        dest_progress.setRange(0, 100)
        dest_progress.setValue(0)
        dest_progress.setFixedHeight(20)  # Slightly taller for better visibility
        dest_progress.setStyleSheet(PROGRESS_BAR_STYLE)
        dest_progress.setVisible(False)
        dest_progress.setFormat(f"Dest {len(root.destinations)+1}: %p%")
        dest_progress.setTextVisible(True)
        progress_row.addWidget(dest_progress, 1)
        
        dest_layout.addLayout(progress_row)
        
        # Enhanced speed and status row
        speed_row = QHBoxLayout()
        speed_row.setSpacing(15)
        speed_row.setContentsMargins(0, 2, 0, 2)
        
        # Current speed label - LARGE and readable
        current_speed_label = QLabel("0 MB/s")
        current_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['accent']};
                font-size: 16px;
                font-weight: 600;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            }}
        """)
        current_speed_label.setFixedHeight(24)
        current_speed_label.setMinimumWidth(90)
        
        # Peak speed label - LARGE and readable
        peak_speed_label = QLabel("Peak: 0 MB/s")
        peak_speed_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 14px;
                font-weight: 500;
            }}
        """)
        peak_speed_label.setFixedHeight(24)
        peak_speed_label.setMinimumWidth(120)
        
        # ETA label - LARGE and readable
        eta_label = QLabel("ETA: --:--")
        eta_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 14px;
                font-weight: 500;
                font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            }}
        """)
        eta_label.setFixedHeight(24)
        eta_label.setMinimumWidth(100)
        
        # Status label (Ready, Transferring, Complete) - LARGE and readable
        status_label = QLabel("Ready")
        status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['secondary_text']};
                font-size: 14px;
                font-weight: 500;
                padding: 4px 8px;
                border-radius: 6px;
                background-color: {colors['bg']};
            }}
        """)
        status_label.setFixedHeight(24)
        status_label.setMinimumWidth(80)
        
        speed_row.addWidget(current_speed_label)
        speed_row.addWidget(peak_speed_label)
        speed_row.addWidget(eta_label)
        speed_row.addStretch()
        speed_row.addWidget(status_label)
        
        dest_layout.addLayout(speed_row)
        
        # Store references for UI updates
        dest_obj["widget"] = dest_widget
        dest_obj["progress_bar"] = dest_progress
        dest_obj["current_speed_label"] = current_speed_label
        dest_obj["peak_speed_label"] = peak_speed_label
        dest_obj["eta_label"] = eta_label
        dest_obj["status_label"] = status_label
        
        # Add to container
        root.dest_container_layout.addWidget(dest_widget)
    
    def update_dest_preset(dest_obj, preset):
        """Update destination preset"""
        dest_obj["preset"] = preset
        # Auto-classify if preset is "Auto"
        if preset == "Auto":
            dest_obj["path_type"] = classify_destination(dest_obj["path"])
        else:
            dest_obj["path_type"] = preset.lower()
    
    def cancel_destination(dest_obj):
        """Cancel a specific destination with immediate UI feedback"""
        print(f"DEBUG: Canceling destination: {dest_obj['path']}")
        try:
            # IMMEDIATE UI FEEDBACK - don't wait for engine response
            print(f"DEBUG: Providing immediate cancel feedback for destination: {dest_obj['path']}")
            
            # Immediately update destination progress bar to show canceling status
            if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                current_value = dest_obj['progress_bar'].value()
                dest_obj['progress_bar'].setFormat("Creating transfer log...")
                # Stop progress animation by setting to current value
                dest_obj['progress_bar'].setValue(current_value)
                print(f"DEBUG: Destination progress bar updated to show canceling status")
            
            # Send cancel command to engine in background thread to prevent UI blocking
            def cancel_destination_async():
                """Cancel destination in background thread to prevent UI freezing"""
                try:
                    if root.current_job and hasattr(root.current_job, 'cancel_destination'):
                        root.current_job.cancel_destination(dest_obj['path'])
                        print(f"DEBUG: Cancel command completed for destination: {dest_obj['path']}")
                    else:
                        print(f"DEBUG: No current job or job doesn't have cancel_destination method")
                        # If no engine method, reset destination progress immediately
                        if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                            dest_obj['progress_bar'].setValue(0)
                            dest_obj['progress_bar'].setFormat("Canceled")
                except Exception as e:
                    print(f"DEBUG: Error in background destination cancel: {e}")
                    # Reset destination progress on error
                    if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                        dest_obj['progress_bar'].setValue(0)
                        dest_obj['progress_bar'].setFormat("Error")
            
            # Start destination cancel operation in background thread
            import threading
            cancel_thread = threading.Thread(target=cancel_destination_async, daemon=True)
            cancel_thread.start()
            print(f"DEBUG: Destination cancel started in background thread for: {dest_obj['path']}")
                    
        except Exception as e:
            print(f"DEBUG: Error canceling destination: {e}")
            import traceback
            traceback.print_exc()
            # Reset destination progress on error
            if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                dest_obj['progress_bar'].setValue(0)
                dest_obj['progress_bar'].setFormat("Error")
    
    def remove_destination(dest_obj, widget):
        """Remove a destination"""
        root.destinations.remove(dest_obj)
        root.dest_container_layout.removeWidget(widget)
        widget.deleteLater()
        check_button_states()
    
    def classify_destination(path):
        """Classify destination as local or network"""
        import sys
        if sys.platform == "darwin":
            # macOS: statfs MNT_LOCAL
            try:
                return "network" if path.startswith(("smb://", "afp://", "nfs://")) else "local"
            except:
                return "local"
        elif sys.platform == "win32":
            # Windows: check for network drives
            try:
                return "network" if path.startswith(("\\\\", "//")) else "local"
            except:
                return "local"
        else:
            # Linux: check for network paths
            try:
                return "network" if path.startswith(("/mnt/", "/media/")) and any(x in path for x in ["smb", "nfs", "cifs"]) else "local"
            except:
                return "local"
    
    # Apply global preset logic
    def apply_global_preset():
        preset = preset_combo.currentText()
        if "USB/TB" in preset:
            # Force all destinations to USB/TB preset
            for dest_obj in root.destinations:
                dest_obj["preset"] = "USB/TB"
                dest_obj["path_type"] = "usb"
                if "widget" in dest_obj:
                    # Update the widget's preset combo
                    for child in dest_obj["widget"].children():
                        if isinstance(child, QComboBox):
                            child.setCurrentText("USB/TB")
        elif "Network" in preset:
            # Force all destinations to Network preset
            for dest_obj in root.destinations:
                dest_obj["preset"] = "Network"
                dest_obj["path_type"] = "network"
                if "widget" in dest_obj:
                    # Update the widget's preset combo
                    for child in dest_obj["widget"].children():
                        if isinstance(child, QComboBox):
                            child.setCurrentText("Network")
        else:  # Auto
            # Let each destination auto-classify
            for dest_obj in root.destinations:
                dest_obj["preset"] = "Auto"
                dest_obj["path_type"] = classify_destination(dest_obj["path"])
                if "widget" in dest_obj:
                    # Update the widget's preset combo
                    for child in dest_obj["widget"].children():
                        if isinstance(child, QComboBox):
                            child.setCurrentText("Auto")
    
    preset_combo.currentTextChanged.connect(apply_global_preset)
    
    # Define event handlers in the outer scope so they can access UI widgets
    def handle_job_started(payload):
        print(f"DEBUG: handle_job_started called with: {payload}")
        try:
            print("DEBUG: Starting handle_job_started...")
            
            # Get job data
            total_bytes = payload.get("total_bytes")
            if total_bytes is None:
                total_bytes = payload.get("total", 0)
            total_files = payload.get("total_files", 0)
            print(f"DEBUG: Job started with {total_files} files, {total_bytes} total bytes")
            
            # IMMEDIATELY enable cancel and pause buttons for responsive UI
            if hasattr(root, 'pause_btn') and root.pause_btn:
                root.pause_btn.setEnabled(True)
                print("DEBUG: Pause button enabled IMMEDIATELY")
            if hasattr(root, 'cancel_btn') and root.cancel_btn:
                root.cancel_btn.setEnabled(True)
                print("DEBUG: Cancel button enabled IMMEDIATELY")
            
            # Update UI widgets safely
            if hasattr(root, 'total_progress') and root.total_progress:
                # Keep the progress bar at 0-100 range for percentage
                root.total_progress.setValue(0)
                root.total_progress.setVisible(True)
                print("DEBUG: Total progress bar updated")
            

            
            if hasattr(root, 'elapsed_label') and root.elapsed_label:
                root.elapsed_label.setText("00:00")
                print("DEBUG: Elapsed label updated")
            

            
            # Show destination progress bars IMMEDIATELY
            if hasattr(root, 'destinations'):
                print(f"DEBUG: Showing progress bars for {len(root.destinations)} destinations")
                for i, dest_obj in enumerate(root.destinations):
                    # Show progress bar
                    if 'progress_bar' in dest_obj:
                        dest_obj['progress_bar'].setVisible(True)
                        dest_obj['progress_bar'].setValue(0)
                        print(f"DEBUG: Showed progress bar for destination {i+1}")
                    

            
            # PROFESSIONAL DIT APPROACH: No individual file widgets
            # Clear any existing file widgets and keep the files area clean
            _clear_all_file_widgets()
            

            
            print(f"DEBUG: Using professional DIT approach - job-level progress only")
            
            # Update file count display
            if hasattr(root, 'files_count') and root.files_count:
                root.files_count.setText(f"0 of {total_files} files")
                print(f"DEBUG: File count display updated to show 0 of {total_files} files")
            
            # Store data for later use
            root.job_start_time = time.time()
            root.job_data = {
                'total_bytes': total_bytes,
                'total_files': total_files,
                'start_time': time.time(),
                'copied_bytes': 0,
                'completed_files': 0  # Initialize completed files counter
            }
            
            print("DEBUG: handle_job_started completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_started: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_job_progress(payload):
        print(f"DEBUG: handle_job_progress called with: {payload}")
        try:
            # Get progress data
            copied_bytes = payload.get("copied_bytes")
            if copied_bytes is None:
                copied_bytes = payload.get("bytes_copied")
            if copied_bytes is None:
                copied_bytes = payload.get("bytes", 0)

            total_bytes = payload.get("total_bytes")
            if total_bytes is None:
                total_bytes = payload.get("total", 0)
            
            print(f"DEBUG: Raw payload keys: {list(payload.keys())}")
            print(f"DEBUG: copied_bytes from payload: {payload.get('copied_bytes')}")
            print(f"DEBUG: bytes_copied from payload: {payload.get('bytes_copied')}")
            print(f"DEBUG: Final copied_bytes value: {copied_bytes}")
            print(f"DEBUG: Job progress: {copied_bytes}/{total_bytes} bytes")
            
            # Check for file completion information in progress payload (C++ engine emits "files_completed")
            completed_files_from_payload = payload.get("files_completed")
            if completed_files_from_payload is not None:
                print(f"DEBUG: Found files_completed in engine payload: {completed_files_from_payload}")
                # Update using engine data
                if hasattr(root, 'job_data') and root.job_data:
                    root.job_data['completed_files'] = completed_files_from_payload
                    total_files = root.job_data.get('total_files', 0)
                    if hasattr(root, 'files_count') and root.files_count:
                        root.files_count.setText(f"{completed_files_from_payload} of {total_files} files")
                        print(f"DEBUG: Updated file count from engine: {completed_files_from_payload} of {total_files}")
            else:
                print(f"DEBUG: No files_completed found in engine payload - checking payload keys: {list(payload.keys())}")
            
            # Store the values in root for the update_stats function
            root.copied_bytes = copied_bytes
            root.total_bytes = total_bytes
            
            # Calculate percentage to avoid overflow - use integer division for large numbers
            if total_bytes > 0:
                progress_percent = min(int((copied_bytes * 100) // total_bytes), 100)
            else:
                progress_percent = 0
            
            # Check if we're at 100% but the job hasn't completed
            if progress_percent >= 100 and not hasattr(root, '_completion_timeout_set'):
                print("DEBUG: Progress reached 100%, setting completion timeout")
                root._completion_timeout_set = True
                # Set a timeout to force completion if the job.completed event doesn't come
                QTimer.singleShot(5000, lambda: _force_job_completion())
            
            # Batch UI updates to prevent beachballing - only update every 100ms
            current_time = time.time()
            if not hasattr(root, '_last_progress_update') or (current_time - root._last_progress_update) >= 0.1:
                root._last_progress_update = current_time
                
                # Calculate speed and elapsed time FIRST before using in destination updates
                speed_mbps = None
                elapsed = 0
                
                if hasattr(root, 'job_data') and root.job_data:
                    elapsed_from_engine = payload.get("elapsed_time")
                    if elapsed_from_engine is not None:
                        elapsed = float(elapsed_from_engine)
                    else:
                        elapsed = time.time() - root.job_data['start_time']

                    # Prefer engine-reported speed if present
                    speed_mbps = payload.get("speed_mbps")
                    if speed_mbps is None and elapsed > 0:
                        speed_mbps = (copied_bytes / elapsed) / (1024 * 1024)
                
                # Update total progress bar with percentage
                if hasattr(root, 'total_progress') and root.total_progress:
                    root.total_progress.setValue(progress_percent)
                    print(f"DEBUG: Total progress bar updated to {progress_percent}%")
                
                # Update destination progress bars and stats (for multi-destination)
                if hasattr(root, 'destinations'):
                    for i, dest_obj in enumerate(root.destinations):
                        if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                            dest_obj['progress_bar'].setValue(progress_percent)
                            print(f"DEBUG: Destination {i+1} progress bar updated to {progress_percent}%")
                            
                            # Update destination speeds with main job speeds for consistency
                            if 'current_speed_label' in dest_obj and dest_obj['current_speed_label'] and speed_mbps:
                                dest_obj['current_speed_label'].setText(f"{speed_mbps:.0f} MB/s")
                                
                            if 'peak_speed_label' in dest_obj and dest_obj['peak_speed_label']:
                                main_peak = getattr(root, '_max_speed_seen', 0)
                                dest_obj['peak_speed_label'].setText(f"Peak: {main_peak:.0f} MB/s")
                                
                            # Update destination ETA
                            if 'eta_label' in dest_obj and dest_obj['eta_label'] and speed_mbps and speed_mbps > 0:
                                remaining_bytes = max(0, total_bytes - copied_bytes)
                                eta_seconds = remaining_bytes / (speed_mbps * 1024 * 1024)
                                if eta_seconds > 0 and eta_seconds < 86400:  # Less than 24 hours
                                    eta_str = f"ETA: {int(eta_seconds//60):02d}:{int(eta_seconds%60):02d}"
                                else:
                                    eta_str = "ETA: --:--"
                                dest_obj['eta_label'].setText(eta_str)
                            elif 'eta_label' in dest_obj and dest_obj['eta_label']:
                                dest_obj['eta_label'].setText("ETA: --:--")
                            
                # Update main progress speed and ETA
                if hasattr(root, 'current_speed_label') and root.current_speed_label and speed_mbps:
                    root.current_speed_label.setText(f"{speed_mbps:.0f} MB/s")
                    root._last_main_speed = speed_mbps  # Store for destination updates
                    print(f"DEBUG: Main speed updated to {speed_mbps:.0f} MB/s")
                
                # Update peak speed (keep track of maximum speed seen)
                if hasattr(root, 'peak_speed_label') and root.peak_speed_label and speed_mbps:
                    if not hasattr(root, '_max_speed_seen'):
                        root._max_speed_seen = 0
                    root._max_speed_seen = max(root._max_speed_seen, speed_mbps)
                    root.peak_speed_label.setText(f"{root._max_speed_seen:.0f} MB/s")
                    print(f"DEBUG: Peak speed updated to {root._max_speed_seen:.0f} MB/s")
                
                # Update average speed (rolling average over time, not just current speed)
                if hasattr(root, 'avg_speed_label') and root.avg_speed_label and elapsed > 0:
                    # Calculate true average speed: total copied bytes / total elapsed time
                    avg_speed = (copied_bytes / elapsed) / (1024 * 1024)
                    root.avg_speed_label.setText(f"{avg_speed:.0f} MB/s")
                    print(f"DEBUG: Average speed updated to {avg_speed:.0f} MB/s (true average)")
                
                # Update ETA
                if hasattr(root, 'eta_label') and root.eta_label and speed_mbps and speed_mbps > 0:
                    remaining_bytes = max(0, total_bytes - copied_bytes)
                    remaining_mb = remaining_bytes / (1024 * 1024)
                    eta_seconds = remaining_mb / speed_mbps
                    eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                    root.eta_label.setText(eta_str)
                    print(f"DEBUG: ETA updated to {eta_str}")

                if hasattr(root, 'elapsed_label') and root.elapsed_label:
                    elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                    root.elapsed_label.setText(elapsed_str)
                    print("DEBUG: Elapsed label updated")
                

            
            # Update stored data (always update this)
            if hasattr(root, 'job_data'):
                root.job_data['copied_bytes'] = copied_bytes
            
            print("DEBUG: handle_job_progress completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_progress: {e}")
            import traceback
            traceback.print_exc()
    
    def _force_job_completion():
        """Force job completion if the engine doesn't emit job.completed"""
        print("DEBUG: Force job completion timeout triggered")
        try:
            # Create a fake completion payload
            fake_payload = {
                "bytes": root.copied_bytes if hasattr(root, 'copied_bytes') else 0,
                "total": root.total_bytes if hasattr(root, 'total_bytes') else 0,
                "elapsed": time.time() - root.job_start_time if hasattr(root, 'job_start_time') else 0,
                "speed": 0
            }
            print(f"DEBUG: Calling handle_job_completed with fake payload: {fake_payload}")
            handle_job_completed(fake_payload)
        except Exception as e:
            print(f"DEBUG: Error in force job completion: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_current_file(payload):
        """Handle current file updates - PROFESSIONAL DIT APPROACH"""
        print(f"DEBUG: handle_current_file called with: {payload}")
        try:
            filename = payload.get("filename", "Processing...")
            

            

            
            print(f"DEBUG: Current file display updated: {filename}")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_current_file: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_failed(payload):
        """Handle file failure alerts - PROFESSIONAL DIT APPROACH"""
        print(f"DEBUG: handle_file_failed called with: {payload}")
        try:
            filename = payload.get('filename', 'unknown')
            error = payload.get('error', 'unknown error')
            
            # Professional DIT tools show immediate alerts for failures
            print(f"ERROR: File failed: {filename} - {error}")
            

            
        except Exception as e:
            print(f"DEBUG: Error in handle_file_failed: {e}")
            import traceback
            traceback.print_exc()
            
    # No individual file completion handling in professional DIT approach
    # File completion counts are tracked in job stats and shown in job.progress
            
    def handle_dest_progress(payload):
        print(f"DEBUG: handle_dest_progress called with: {payload}")
        try:
            # Get destination progress data
            dest_index = payload.get("dest_index", 0)
            dest_path = payload.get("dest_path", "unknown")
            bytes_copied = payload.get("bytes_copied", 0)
            total_bytes = payload.get("total_bytes", 0)
            transfer_type = payload.get("transfer_type", "unknown")
            current_speed = payload.get("current_speed_mbps", 0.0)
            peak_speed = payload.get("peak_speed_mbps", 0.0)
            elapsed_time = payload.get("elapsed_time", 0.0)
            completed_files = payload.get("completed_files", 0)
            total_files = payload.get("total_files", 0)
            
            print(f"DEBUG: Destination {dest_index} ({transfer_type}) progress: {bytes_copied}/{total_bytes} bytes at {current_speed:.1f} MB/s")
            
            # Update destination-specific UI elements
            if hasattr(root, 'destinations') and dest_index < len(root.destinations):
                dest_obj = root.destinations[dest_index]
                
                # Update progress bar
                if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                    progress_bar = dest_obj['progress_bar']
                    
                    # Ensure progress bar is visible and initialized
                    if not progress_bar.isVisible():
                        progress_bar.setVisible(True)
                        progress_bar.setValue(0)
                        dest_obj.get('status_label', {}).setText("Transferring")
                    
                    # Calculate and update progress
                    if total_bytes > 0:
                        progress_percent = min(100, int((bytes_copied / total_bytes) * 100))
                        progress_bar.setValue(progress_percent)
                        progress_bar.setFormat(f"Dest {dest_index + 1}: {progress_percent}%")
                        print(f"DEBUG: Destination {dest_index} progress bar updated to {progress_percent}%")
                        
                        # Update status based on progress
                        if progress_percent >= 100:
                            if 'status_label' in dest_obj:
                                dest_obj['status_label'].setText("Complete")
                                dest_obj['status_label'].setStyleSheet(f"""
                                    QLabel {{
                                        color: {colors['text']};
                                        font-size: 10px;
                                        font-weight: 500;
                                        padding: 2px 6px;
                                        border-radius: 3px;
                                        background-color: #2d5a2d;
                                    }}
                                """)
                        elif bytes_copied > 0:
                            if 'status_label' in dest_obj:
                                dest_obj['status_label'].setText("Transferring")
                                dest_obj['status_label'].setStyleSheet(f"""
                                    QLabel {{
                                        color: {colors['text']};
                                        font-size: 10px;
                                        font-weight: 500;
                                        padding: 2px 6px;
                                        border-radius: 3px;
                                        background-color: {colors['accent']};
                                    }}
                                """)
                    else:
                        # If total_bytes is 0, show indeterminate progress
                        progress_bar.setFormat(f"Dest {dest_index + 1}: Calculating...")
                
                # FIXED: Update destination current speed from main progress
                if 'current_speed_label' in dest_obj and dest_obj['current_speed_label']:
                    # Use main job speed for consistency across all destinations  
                    main_speed = getattr(root, '_last_main_speed', current_speed)
                    dest_obj['current_speed_label'].setText(f"{main_speed:.0f} MB/s")
                
                # FIXED: Update destination peak speed from main progress
                if 'peak_speed_label' in dest_obj and dest_obj['peak_speed_label']:
                    # Use main peak speed for consistency
                    main_peak = getattr(root, '_max_speed_seen', peak_speed)
                    dest_obj['peak_speed_label'].setText(f"Peak: {main_peak:.0f} MB/s")
                
                # Calculate and update ETA
                if 'eta_label' in dest_obj and dest_obj['eta_label']:
                    if current_speed > 0 and bytes_copied < total_bytes:
                        remaining_bytes = total_bytes - bytes_copied
                        eta_seconds = remaining_bytes / (current_speed * 1024 * 1024)
                        if eta_seconds > 0 and eta_seconds < 86400:  # Less than 24 hours
                            eta_str = f"ETA: {int(eta_seconds//60):02d}:{int(eta_seconds%60):02d}"
                        else:
                            eta_str = "ETA: --:--"
                    elif bytes_copied >= total_bytes:
                        eta_str = "Complete"
                    else:
                        eta_str = "ETA: --:--"
                    dest_obj['eta_label'].setText(eta_str)
                
                print(f"DEBUG: Updated all UI elements for destination {dest_index}")

            else:
                print(f"DEBUG: Invalid destination index {dest_index} or no destinations available")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_dest_progress: {e}")
            import traceback
            traceback.print_exc()

    def handle_dest_warning(payload):
        print(f"DEBUG: handle_dest_warning called with: {payload}")
        try:
            dest_path = payload.get("dest_path", "unknown")
            warning_type = payload.get("warning_type", "unknown")
            message = payload.get("message", "Unknown warning")
            
            print(f"DEBUG: Destination warning: {dest_path} - {warning_type}: {message}")
            
            # Show immediate warning dialog for disk full
            if warning_type == "disk_full":
                def show_warning_dialog():
                    from PyQt6.QtWidgets import QMessageBox
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    msg_box.setWindowTitle("Destination Warning")
                    msg_box.setText(f"⚠️  Destination Skipped")
                    msg_box.setInformativeText(f"Transfer will continue to other destinations.\n\nSkipped: {dest_path}\nReason: {message}")
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg_box.exec()
                    print("DEBUG: Destination warning dialog shown")
                
                # Show on main thread
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, show_warning_dialog)
            
            # Update destination UI to show warning state
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if dest_obj.get("path") == dest_path:
                        print(f"DEBUG: Updating destination {i} UI for warning")
                        
                        # Update progress bar to show warning
                        if 'progress_bar' in dest_obj:
                            dest_obj['progress_bar'].setFormat(f"⚠️ SKIPPED - Disk Full")
                            dest_obj['progress_bar'].setStyleSheet("""
                                QProgressBar {
                                    background-color: #fff3e0;
                                    border: 2px solid #ff9800;
                                    border-radius: 3px;
                                    text-align: center;
                                    color: #f57c00;
                                    font-weight: bold;
                                }
                                QProgressBar::chunk {
                                    background-color: #ff9800;
                                }
                            """)
                            dest_obj['progress_bar'].setValue(0)
                        
                        # Update status label
                        if 'status_label' in dest_obj:
                            dest_obj['status_label'].setText("Skipped")
                            dest_obj['status_label'].setStyleSheet(f"""
                                QLabel {{
                                    color: #f57c00;
                                    font-size: 14px;
                                    font-weight: bold;
                                    padding: 4px 8px;
                                    border-radius: 6px;
                                    background-color: #fff3e0;
                                    border: 1px solid #ff9800;
                                }}
                            """)
                        
                        break
            
        except Exception as e:
            print(f"DEBUG: Error in handle_dest_warning: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_completed(payload):
        """Handle file completion events to update transfer status"""
        print(f"DEBUG: ===== FILE COMPLETED EVENT RECEIVED =====")
        print(f"DEBUG: handle_file_completed called with: {payload}")
        try:
            filename = payload.get("filename", "Unknown file")
            print(f"DEBUG: File completed: {filename}")
            
            # Update completed files count
            if hasattr(root, 'job_data') and root.job_data:
                root.job_data['completed_files'] = root.job_data.get('completed_files', 0) + 1
                completed_files = root.job_data['completed_files']
                total_files = root.job_data.get('total_files', 0)
                
                print(f"DEBUG: Updated completed files: {completed_files} of {total_files}")
                
                # Update file count display
                if hasattr(root, 'files_count') and root.files_count:
                    root.files_count.setText(f"{completed_files} of {total_files} files")
                    print(f"DEBUG: File count display updated to show {completed_files} of {total_files} files")
                else:
                    print(f"DEBUG: files_count widget not found or not available")
                
        except Exception as e:
            print(f"DEBUG: Error in handle_file_completed: {e}")
            import traceback
            traceback.print_exc()

    def handle_file_failed(payload):
        print(f"DEBUG: handle_file_failed called with: {payload}")
        try:
            file_id = payload.get("file_id")
            filename = payload.get("filename")
            error = payload.get("error", "Unknown error")
            print(f"DEBUG: File failed: {filename} - Error: {error}")
            
            if file_id in root.file_widgets:
                root.file_widgets[file_id].mark_failed(error)
                root.active_files -= 1
                files_count.setText(f"{root.active_files} of {root.job_data.get('total_files', 0)} files")
                print(f"DEBUG: File marked as failed, active files: {root.active_files}")
            else:
                print(f"DEBUG: File widget not found for failed file: {file_id}")
                
        except Exception as e:
            print(f"DEBUG: Error in handle_file_failed: {e}")
            import traceback
            traceback.print_exc()

    def handle_job_completed(payload):
        print(f"DEBUG: handle_job_completed called with: {payload}")
        try:
            # Get completion data - handle both C++ and Python engine formats
            bytes_copied = payload.get("bytes") or payload.get("copied_bytes", 0)
            total_bytes = payload.get("total") or payload.get("total_bytes", 0)
            elapsed = payload.get("elapsed") or payload.get("elapsed_s") or payload.get("data_elapsed_s", 0)
            speed = payload.get("speed") or payload.get("mbps", 0) or payload.get("data_mbps", 0)
            
            print(f"DEBUG: Job completed: {bytes_copied}/{total_bytes} bytes in {elapsed:.2f}s at {speed:.2f} MB/s")
            
            # Update UI to show 100% completion
            if hasattr(root, 'total_progress') and root.total_progress:
                root.total_progress.setValue(100)
                print("DEBUG: Progress bar set to 100%")
            

            

            
            if hasattr(root, 'elapsed_label') and root.elapsed_label:
                elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                root.elapsed_label.setText(elapsed_str)
                print("DEBUG: Elapsed label updated")
            
            # Update destination status and reset to 100%
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'progress_bar' in dest_obj:
                        dest_obj['progress_bar'].setValue(100)
                        dest_obj['progress_bar'].setFormat(f"Dest {i + 1}: 100%")
                print("DEBUG: Destination controls updated for completion")
            
            # Clear file widgets after a brief delay to show completion
            if hasattr(root, 'file_widgets'):
                # Mark all remaining file widgets as completed
                for file_id, widget in root.file_widgets.items():
                    widget.mark_completed()
                
                # Schedule removal of all file widgets after showing completion for 3 seconds
                QTimer.singleShot(3000, lambda: _clear_all_file_widgets())
                print("DEBUG: File widgets marked as completed and scheduled for removal")
            
            # Reset job state and re-enable controls after brief delay
            def reset_transfer_state():
                # Reset job tracking
                root.current_job = None
                root.job_start_time = None
                root.total_bytes = 0
                root.copied_bytes = 0
                root.active_files = 0
                
                # Re-enable main controls
                if hasattr(root, 'report_checkbox'):
                    root.report_checkbox.setEnabled(True)
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                add_dest_btn.setEnabled(True)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                
                # Reset progress and status displays
                if hasattr(root, 'total_progress') and root.total_progress:
                    root.total_progress.setValue(0)
                    root.total_progress.setFormat("0%")


                if hasattr(root, 'files_count') and root.files_count:
                    root.files_count.setText("0 of 0 files")
                
                print("DEBUG: Transfer state reset and controls re-enabled")
            
            # Schedule state reset after file widgets are cleared
            QTimer.singleShot(4000, reset_transfer_state)
            
            print("DEBUG: handle_job_completed completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_completed: {e}")
            import traceback
            traceback.print_exc()

    def _remove_file_widget(file_id: str):
        print(f"DEBUG: _remove_file_widget called for {file_id}")
        try:
            if file_id in root.file_widgets:
                widget = root.file_widgets[file_id]
                print(f"DEBUG: Removing widget {file_id} from layout")
                # Note: File widgets no longer used in professional DIT approach
                widget.deleteLater()
                del root.file_widgets[file_id]
                print(f"DEBUG: Widget {file_id} removed successfully")
                print(f"DEBUG: Remaining file widgets: {list(root.file_widgets.keys())}")
            else:
                print(f"DEBUG: Widget {file_id} not found in root.file_widgets")
                print(f"DEBUG: Available file widgets: {list(root.file_widgets.keys())}")
                
        except Exception as e:
            print(f"DEBUG: Error in _remove_file_widget: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_all_file_widgets():
        """Clear all file widgets from the display"""
        print("DEBUG: _clear_all_file_widgets called")
        try:
            for file_id in list(root.file_widgets.keys()):
                _remove_file_widget(file_id)
            root.active_files = 0
            if hasattr(root, 'files_count') and root.files_count:
                root.files_count.setText("0 of 0 files")
            print("DEBUG: All file widgets cleared")
        except Exception as e:
            print(f"DEBUG: Error in _clear_all_file_widgets: {e}")
            import traceback
            traceback.print_exc()

    # Create the QtSink class in the outer scope so it can reference the event handlers
    class QtSink(QObject):
        def __init__(self):
            super().__init__()
            print("DEBUG: QtSink.__init__ called")
            self.pending_events = []
            self._timer = QTimer()
            self._timer.timeout.connect(self._process_pending_events)
            self._timer.start(50)  # Process events every 50ms for real-time responsiveness
            print(f"DEBUG: QtSink timer started with interval 100ms")
            self._lock = threading.Lock()  # Add thread safety
            self._widgets_valid = True  # Track if widgets are still valid
            self._processing = False  # Prevent re-entrant processing
            self._event_count = 0  # Track total events received
        
        def emit(self, event_type: str, payload: dict) -> None:
            """Emit an event to be processed on the main thread"""
            if not self._widgets_valid:
                print(f"DEBUG: QtSink ignoring event {event_type} - widgets no longer valid")
                return
                
            self._event_count += 1
            print(f"DEBUG: QtSink received event #{self._event_count}: {event_type} with payload: {payload}")
            
            # Add thread safety
            with self._lock:
                # Add event to pending queue instead of using QTimer.singleShot
                # This avoids issues with cross-thread QTimer calls
                self.pending_events.append((event_type, payload))
                print(f"DEBUG: Event queued, pending events: {len(self.pending_events)}")
        
        def _process_pending_events(self):
            """Process pending events on the main thread"""
            if not self._widgets_valid or self._processing:
                return
                
            self._processing = True
            try:
                # Add thread safety
                with self._lock:
                    if not self.pending_events:
                        return
                    
                    # Process all pending events
                    events_to_process = self.pending_events.copy()
                    self.pending_events.clear()
                
                print(f"DEBUG: Processing {len(events_to_process)} pending events")
                
                for event_type, payload in events_to_process:
                    try:
                        print(f"DEBUG: ===== Processing event: {event_type} =====")
                        if event_type == "file.completed":
                            print(f"DEBUG: FILE COMPLETED EVENT DETECTED - calling handler")
                        
                        # Check if widgets are still valid before processing
                        if not self._widgets_valid:
                            print(f"DEBUG: Skipping event {event_type} - widgets no longer valid")
                            continue
                        
                        # Call the actual UI handlers - PROFESSIONAL DIT APPROACH
                        if event_type == "job.started":
                            handle_job_started(payload)
                        elif event_type == "job.progress":
                            handle_job_progress(payload)
                        elif event_type == "current.file":
                            handle_current_file(payload)
                        elif event_type == "file.completed":
                            handle_file_completed(payload)
                        elif event_type == "file.failed":
                            handle_file_failed(payload)  # Still handle failures for alerts
                        elif event_type == "job.completed":
                            handle_job_completed(payload)
                        elif event_type == "dest.progress":
                            handle_dest_progress(payload)
                        elif event_type == "dest.warning":
                            handle_dest_warning(payload)
                        elif event_type == "job.cancelled":
                            handle_job_cancelled(payload)
                        elif event_type == "job.error":
                            handle_job_error(payload)
                        else:
                            print(f"DEBUG: Unknown event type: {event_type}")
                    except Exception as e:
                        print(f"DEBUG: Error processing event {event_type}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Don't mark widgets as invalid for processing errors
                        # Only mark as invalid if widgets are actually destroyed
                
                print(f"DEBUG: Finished processing events")
            finally:
                self._processing = False
        
        def cleanup(self):
            """Clean up resources when the widget is destroyed"""
            print("DEBUG: QtSink cleanup called")
            self._widgets_valid = False  # Mark widgets as invalid
            try:
                if hasattr(self, '_timer') and self._timer and self._timer.isActive():
                    self._timer.stop()
                    print("DEBUG: QtSink timer stopped")
            except Exception as e:
                print(f"DEBUG: Error during cleanup: {e}")
                # Timer may have been deleted already, which is fine
        
        def closeEvent(self, event):
            """Handle close event to ensure cleanup"""
            print("DEBUG: QtSink closeEvent called")
            self.cleanup()
            super().closeEvent(event)
    
    # Create and use the QtSink instance for event processing
    qt_sink = QtSink()
    
    # Connect bridge signals to QtSink for async processing
    bridge = get_bridge()
    bridge.sigJobStarted.connect(lambda p: qt_sink.emit("job.started", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobProgress.connect(lambda p: qt_sink.emit("job.progress", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobCompleted.connect(lambda p: qt_sink.emit("job.completed", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobError.connect(lambda p: qt_sink.emit("job.error", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigFileStarted.connect(lambda p: qt_sink.emit("file.started", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigFileProgress.connect(lambda p: qt_sink.emit("file.progress", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigFileCompleted.connect(lambda p: qt_sink.emit("file.completed", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigDestProgress.connect(lambda p: qt_sink.emit("dest.progress", p), QtCore.Qt.ConnectionType.QueuedConnection)
    
    # Wire up button handlers
    def on_start():
        print("DEBUG: ===== START BUTTON CLICKED =====")
        print(f"DEBUG: Current job state: {getattr(root, 'current_job', 'None')}")
        print(f"DEBUG: Start button enabled: {start_btn.isEnabled()}")
        print(f"DEBUG: Start button text: {start_btn.text()}")
        
        try:
            if not root.src_combo.currentText().strip() or not root.destinations:
                print("DEBUG: Source path is empty or no destinations added")
                return

            print("DEBUG: Starting ingest job...")
            
            # Generate unique job ID
            job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"DEBUG: Generated job ID: {job_id}")
            
            # Get source and destinations
            source_path = root.src_combo.currentText().strip()
            dest_paths = [dest["path"] for dest in root.destinations]
            print(f"DEBUG: Source: {source_path}")
            print(f"DEBUG: Destinations: {dest_paths}")
            
            # Get verification mode
            verify_mode = root.verify_combo.currentText()
            print(f"DEBUG: Verify Mode: {verify_mode}")
            
            # Get global preset
            global_preset = root.preset_combo.currentText()
            print(f"DEBUG: Global Preset: {global_preset}")
            
            # Transfer configuration (C++ engine handles memory automatically)
            print("DEBUG: Using C++ engine auto-configuration (no memory settings needed)")
            # C++ engine uses hardcoded 1MB buffer size and manages memory automatically
            
            # Import JobSpec and JobOptions
            print("DEBUG: Importing JobSpec and JobOptions...")
            try:
                from forwardflow.ingest.api.models import JobSpec, JobOptions
                print("DEBUG: JobSpec and JobOptions imported successfully")
            except ImportError as e:
                print(f"DEBUG: Failed to import JobSpec/JobOptions: {e}")
                return
            
            # Create JobSpec with UI-configured parameters
            print("DEBUG: Creating JobSpec...")
            try:
                # Get concurrency settings from UI sliders
                per_file_concurrency = root.conc_slider.value()
                stream_concurrency = root.stream_slider.value()
                generate_report = root.report_checkbox.isChecked()
                
                print(f"DEBUG: Per-file concurrency: {per_file_concurrency}")
                print(f"DEBUG: Stream concurrency: {stream_concurrency}")
                print(f"DEBUG: Generate report: {generate_report}")
                
                job = JobSpec(
                    job_id=job_id,
                    source_root=source_path,
                    destination_roots=dest_paths,
                    options=JobOptions(
                        mode='FAST' if verify_mode == 'FAST' else 'BALANCED',
                        per_file_concurrency=per_file_concurrency,
                        stream_concurrency=stream_concurrency,
                        verify_algorithm='xxh64',
                        verify_mode=verify_mode,
                        preset=global_preset,
                        generate_verification_report=generate_report
                        # Note: C++ engine uses hardcoded 1MB buffer and manages memory automatically
                    )
                )
                print(f"DEBUG: Created JobSpec: {job}")
            except Exception as e:
                print(f"DEBUG: Failed to create JobSpec: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Store job reference
            root.current_job = job
            print(f"DEBUG: Job stored in root.current_job: {root.current_job}")
            
            # Freeze controls
            print("DEBUG: Freezing controls...")
            root.start_btn.setEnabled(False)
            root.src_combo.setEnabled(False)
            root.src_btn.setEnabled(False)
            root.dest_combo.setEnabled(False) # Changed from dest_btn to dest_combo
            root.verify_combo.setEnabled(False)
            root.preset_combo.setEnabled(False)
            print("DEBUG: Controls frozen")
            
            # Start the job in a background thread
            print("DEBUG: Starting job in background thread...")
            job_thread = threading.Thread(
                target=run_job,
                args=(job, root),
                daemon=True
            )
            job_thread.start()
            print("DEBUG: Job thread started")
            
        except Exception as e:
            print(f"DEBUG: Error in on_start: {e}")
            import traceback
            traceback.print_exc()
            # Re-enable controls on error
            start_btn.setEnabled(True)
            src_combo.setEnabled(True)
            src_btn.setEnabled(True)
            dest_combo.setEnabled(True) # Changed from dest_btn to dest_combo
            verify_combo.setEnabled(True)
            preset_combo.setEnabled(True)
    
    def on_pause():
        print("DEBUG: Pause button clicked")
        try:
            if root.current_job and hasattr(root.current_job, 'pause'):
                print("DEBUG: Pausing engine")
                # Get the job ID from the engine
                if hasattr(root.current_job, 'get_current_job_id'):
                    job_id = root.current_job.get_current_job_id() or 'current'
                else:
                    job_id = 'current'
                
                root.current_job.pause(job_id)
                print("DEBUG: Pause command sent to engine")
                
                # Update button states
                pause_btn.setEnabled(False)
                start_btn.setEnabled(True)
                print("DEBUG: Button states updated for pause")
            else:
                print("DEBUG: No current job or job doesn't have pause method")
                print(f"DEBUG: root.current_job: {root.current_job}")
                if root.current_job:
                    print(f"DEBUG: Job type: {type(root.current_job)}")
                    print(f"DEBUG: Job attributes: {dir(root.current_job)}")
        except Exception as e:
            print(f"DEBUG: Error in on_pause: {e}")
            import traceback
            traceback.print_exc()

    def on_resume():
        """Resume a paused transfer"""
        print("DEBUG: Resume button clicked")
        try:
            if root.current_job and hasattr(root.current_job, 'resume'):
                print("DEBUG: Resuming engine")
                # Get the job ID from the engine
                if hasattr(root.current_job, 'get_current_job_id'):
                    job_id = root.current_job.get_current_job_id() or 'current'
                else:
                    job_id = 'current'
                
                root.current_job.resume(job_id)
                print("DEBUG: Resume command sent to engine")
                
                # Update button states
                start_btn.setEnabled(False)
                pause_btn.setEnabled(True)
                print("DEBUG: Button states updated for resume")
            else:
                print("DEBUG: No current job or job doesn't have resume method")
        except Exception as e:
            print(f"DEBUG: Error in on_resume: {e}")
            import traceback
            traceback.print_exc()

    def on_cancel():
        print("DEBUG: Cancel button clicked")
        try:
            # IMMEDIATE UI FEEDBACK - don't wait for engine response
            print("DEBUG: Providing immediate cancel feedback")
            
            # Immediately disable cancel button to prevent double-clicks
            cancel_btn.setEnabled(False)
            cancel_btn.setText("Canceling...")
            
            # Immediately stop all progress animations and show canceling status
            if hasattr(root, 'total_progress') and root.total_progress:
                root.total_progress.setFormat("Canceling - Creating verification report...")
                # Stop progress animation by setting to current value
                current_value = root.total_progress.value()
                root.total_progress.setValue(current_value)
                print("DEBUG: Progress bar updated to show canceling status")
            
            # Update destination progress bars immediately
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                        dest_obj['progress_bar'].setFormat(f"Dest {i + 1}: Creating report...")
                        # Stop progress animation
                        current_value = dest_obj['progress_bar'].value()
                        dest_obj['progress_bar'].setValue(current_value)
                print("DEBUG: Destination progress bars updated to show canceling status")
            
            # Update file count status immediately
            if hasattr(root, 'files_count') and root.files_count:
                current_text = root.files_count.text()
                # Keep the count but add canceling status
                root.files_count.setText(f"{current_text} - Canceling transfer")
                print("DEBUG: File count updated to show canceling status")
            
            # Send cancel command to engine in background thread to prevent UI blocking
            def cancel_engine_async():
                """Cancel engine in background thread to prevent UI freezing"""
                try:
                    if root.current_job and hasattr(root.current_job, 'cancel'):
                        print("DEBUG: Sending cancel command to engine (background thread)")
                        # Get the job ID from the engine
                        if hasattr(root.current_job, 'get_current_job_id'):
                            job_id = root.current_job.get_current_job_id() or 'current'
                        else:
                            job_id = 'current'
                        
                        # Send cancel command (this may block for report generation)
                        root.current_job.cancel(job_id)
                        print("DEBUG: Cancel command completed in background thread")
                    else:
                        print("DEBUG: No current job to cancel")
                except Exception as e:
                    print(f"DEBUG: Error in background cancel: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start cancel operation in background thread to prevent beachball
            import threading
            cancel_thread = threading.Thread(target=cancel_engine_async, daemon=True)
            cancel_thread.start()
            print("DEBUG: Cancel command started in background thread")
                
        except Exception as e:
            print(f"DEBUG: Error in on_cancel: {e}")
            import traceback
            traceback.print_exc()
            # Reset UI on error
            _reset_ui_after_cancel()
        
        print("DEBUG: Cancel initiated with immediate UI feedback")
    
    def _reset_ui_after_cancel():
        """Helper function to reset UI after cancel operations"""
        try:
            # Reset cancel button
            cancel_btn.setEnabled(False)
            cancel_btn.setText("Cancel")
            
            # Reset progress displays
            if hasattr(root, 'total_progress') and root.total_progress:
                root.total_progress.setValue(0)
                root.total_progress.setFormat("0%")
            
            # Reset destination progress bars
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                        dest_obj['progress_bar'].setValue(0)
                        dest_obj['progress_bar'].setFormat(f"Dest {i + 1}: 0%")
            
            # Reset file count
            if hasattr(root, 'files_count') and root.files_count:
                root.files_count.setText("0 of 0 files")
            
            print("DEBUG: UI reset after cancel completed")
        except Exception as e:
            print(f"DEBUG: Error in _reset_ui_after_cancel: {e}")
    
    def handle_job_cancelled(payload):
        """Handle job cancellation completion"""
        print(f"DEBUG: handle_job_cancelled called with: {payload}")
        try:
            # Job has been cancelled, update UI
            if hasattr(root, 'total_progress') and root.total_progress:
                root.total_progress.setValue(100)  # Show completed transfer
                root.total_progress.setFormat("Transfer cancelled - Verification report complete")
                print("DEBUG: Progress bar updated to show verification report completion")
            

            
            # Update destination status
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'progress_bar' in dest_obj:
                        dest_obj['progress_bar'].setValue(100)
                        dest_obj['progress_bar'].setFormat(f"Dest {i + 1}: Report complete")
                print("DEBUG: Destination controls updated for cancellation")
            
            # Clear file widgets immediately
            _clear_all_file_widgets()
            print("DEBUG: File widgets cleared")
            
            # Reset job state immediately after cancellation
            def reset_after_cancel():
                # Reset job tracking
                root.current_job = None
                root.job_start_time = None
                root.total_bytes = 0
                root.copied_bytes = 0
                root.active_files = 0
                
                # Re-enable controls after job cancellation
                if hasattr(root, 'report_checkbox'):
                    root.report_checkbox.setEnabled(True)
                
                # Re-enable main controls
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                add_dest_btn.setEnabled(True)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                # Reset cancel button text and disable it
                cancel_btn.setEnabled(False)
                cancel_btn.setText("Cancel")  # Reset text back to normal
                
                # Reset additional status displays
                if hasattr(root, 'elapsed_label') and root.elapsed_label:
                    root.elapsed_label.setText("00:00:00")
                
                print("DEBUG: Main controls re-enabled after cancellation")
            
            # Reset state after a brief delay to ensure UI updates are processed
            QTimer.singleShot(500, reset_after_cancel)
            
            print("DEBUG: handle_job_cancelled completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_cancelled: {e}")
            import traceback
            traceback.print_exc()

    def handle_job_error(payload):
        print(f"DEBUG: handle_job_error called with: {payload}")
        try:
            errors = payload.get("errors", [])
            job_id = payload.get("job_id", "unknown")
            
            # Show disk space errors prominently - ensure it runs on main thread
            def show_error_dialog():
                from PyQt6.QtWidgets import QMessageBox
                if errors:
                    error_msg = "\n".join(errors)
                    print(f"DEBUG: Showing error dialog on main thread: {error_msg}")
                    
                    # Create error dialog
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Icon.Critical)
                    msg_box.setWindowTitle("Transfer Error")
                    msg_box.setText("Transfer failed!")
                    
                    # Check for disk space error specifically and make it prominent
                    if "Insufficient disk space" in error_msg:
                        msg_box.setText("❌ DISK FULL - Transfer Failed!")
                        msg_box.setInformativeText(f"Not enough space on destination drive.\n\n{error_msg}\n\nPlease free up disk space or choose a different destination.")
                        msg_box.setWindowTitle("Disk Space Error")
                    else:
                        msg_box.setInformativeText(error_msg)
                    
                    msg_box.setDetailedText(f"Job ID: {job_id}\nErrors:\n" + error_msg)
                    msg_box.exec()
                    print("DEBUG: Error dialog shown successfully")
                else:
                    print("DEBUG: No errors in payload, showing generic error")
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Icon.Critical)
                    msg_box.setWindowTitle("Transfer Error") 
                    msg_box.setText("Transfer failed due to an unknown error.")
                    msg_box.exec()
            
            # Ensure dialog shows on main thread
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, show_error_dialog)
            
            # Show error in progress bar immediately  
            if hasattr(root, 'total_progress') and root.total_progress:
                if errors and "Insufficient disk space" in str(errors):
                    root.total_progress.setFormat("❌ DISK FULL - Transfer Failed!")
                    root.total_progress.setStyleSheet("""
                        QProgressBar {
                            background-color: #ffebee;
                            border: 2px solid #f44336;
                            border-radius: 5px;
                            text-align: center;
                            color: #d32f2f;
                            font-weight: bold;
                        }
                        QProgressBar::chunk {
                            background-color: #f44336;
                        }
                    """)
                else:
                    root.total_progress.setFormat("❌ Transfer Failed!")
                    root.total_progress.setStyleSheet("""
                        QProgressBar {
                            background-color: #ffebee;
                            border: 2px solid #f44336;
                            border-radius: 5px;
                            text-align: center;
                            color: #d32f2f;
                            font-weight: bold;
                        }
                        QProgressBar::chunk {
                            background-color: #f44336;
                        }
                    """)
                root.total_progress.setValue(0)
                
            # Re-enable controls after error (similar to cancellation)
            def reset_after_error():
                # Reset job tracking
                root.current_job = None
                root.job_start_time = None
                root.total_bytes = 0
                root.copied_bytes = 0
                root.active_files = 0
                
                # Re-enable controls
                if hasattr(root, 'report_checkbox'):
                    root.report_checkbox.setEnabled(True)
                
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                add_dest_btn.setEnabled(True)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                cancel_btn.setText("Cancel")
                
                if hasattr(root, 'elapsed_label') and root.elapsed_label:
                    root.elapsed_label.setText("00:00:00")
                
                print("DEBUG: Controls re-enabled after error")
            
            # Reset state after brief delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, reset_after_error)
                
            print("DEBUG: Job error handled successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_error: {e}")
            import traceback
            traceback.print_exc()
    
    # Connect the job cancelled signal after the function is defined
    bridge.sigJobCancelled.connect(handle_job_cancelled, QtCore.Qt.ConnectionType.QueuedConnection)
    
    # Connect the job error signal directly for immediate error display
    bridge.sigJobError.connect(handle_job_error, QtCore.Qt.ConnectionType.QueuedConnection)
    
    # Wire up browse buttons
    def _browse_for_path():
        path = QFileDialog.getExistingDirectory(
            root,
            "Select Source Folder",
            root.src_combo.currentText(),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if path:
            # Add to recent sources
            add_to_recent_locations(path, is_source=True)
            
            # Update combo box
            root.src_combo.setCurrentText(path)
            print(f"DEBUG: Source path selected: {path}")
            check_button_states()
    
    # Function to check if buttons should be enabled
    def check_button_states():
        if root.src_combo.currentText().strip() and len(root.destinations) > 0:
            start_btn.setEnabled(True)
            print("DEBUG: Source and destinations selected, enabling start button")
        else:
            start_btn.setEnabled(False)
            print("DEBUG: Source or destinations not complete, disabling start button")
    
    # Connect text changed signals to check button states
    root.src_combo.currentTextChanged.connect(check_button_states)
    
    # Connect button handlers
    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)
    add_dest_btn.clicked.connect(add_destination)
    print("DEBUG: Button handlers connected")
    
    src_btn.clicked.connect(_browse_for_path)
    print("DEBUG: Browse button handlers connected")
    
    # Initial button state check
    check_button_states()
    
    return root


def run_job(job, root):
    """Run the job in a background thread with comprehensive debugging"""
    print(f"DEBUG: ===== RUN_JOB STARTED =====")
    print(f"DEBUG: Job ID: {job.job_id}")
    print(f"DEBUG: Thread ID: {threading.current_thread().ident}")
    
    try:
        # Use bridge emitter via engine wrapper
        print("DEBUG: Creating BridgeSink...")
        sink = type("BridgeSink", (), {"emit": lambda _self, kind, payload: emit_event(kind, payload)})()
        print("DEBUG: BridgeSink created")
        
        # Create and start the engine
        print("DEBUG: Importing PythonCopyEngine...")
        try:
            from forwardflow.ingest.engines.python_engine import PythonCopyEngine
            print("DEBUG: PythonCopyEngine imported successfully")
        except ImportError as e:
            print(f"DEBUG: Failed to import PythonCopyEngine: {e}")
            raise
        
        print("DEBUG: Creating PythonCopyEngine instance...")
        try:
            engine = PythonCopyEngine(sink=sink)
            print(f"DEBUG: PythonCopyEngine created: {engine}")
        except Exception as e:
            print(f"DEBUG: Failed to create PythonCopyEngine: {e}")
            raise
        
        # Check which engine type is being used
        if hasattr(engine, '_cpp_engine_used'):
            print("DEBUG: C++ engine is being used")
        else:
            print("DEBUG: Python fallback engine is being used")
        
        # Store the engine reference
        root.current_job = engine
        print("DEBUG: Engine stored in root.current_job")
        
        print("DEBUG: Starting engine with job...")
        try:
            engine.start(job)
            print("DEBUG: Engine completed successfully")
        except Exception as e:
            print(f"DEBUG: Engine failed: {e}")
            import traceback
            traceback.print_exc()
            raise
            
    except Exception as e:
        print(f"DEBUG: Error in run_job: {e}")
        import traceback
        traceback.print_exc()
        
        # Re-enable controls on error
        def reenable_controls():
            root.start_btn.setEnabled(True)
            root.src_combo.setEnabled(True)
            root.src_btn.setEnabled(True)
            root.dest_combo.setEnabled(True)
            root.verify_combo.setEnabled(True)
            root.preset_combo.setEnabled(True)
            print("DEBUG: Controls re-enabled after error")
        
        # Use QTimer to ensure this runs on the main thread
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, reenable_controls)
        
    finally:
        print("DEBUG: ===== RUN_JOB COMPLETED =====")


