"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built here to keep ingest self-contained. The host app
calls `build_ingest_tab()` under a feature flag to add the tab.
"""

from __future__ import annotations

import os
import time
import threading
import json
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
        SLIDER_STYLE, SPEED_LABEL_STYLE, SECTION_HEADER_STYLE,
        SECONDARY_TEXT_STYLE, HEADER_LABEL_STYLE, FIELD_LABEL_STYLE,
        TIME_LABEL_STYLE, ACCENT_VALUE_STYLE, CARD_FRAME_STYLE
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
    layout.setContentsMargins(5, 5, 5, 5)  # Reduced to 5px for tight spacing
    layout.setSpacing(5)  # Reduced to 5px for tight spacing
    
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
    root.stats_update_timer.start(100)  # Update every 100ms for more responsive stats
    
    def update_elapsed_time():
        """Update elapsed time display every second"""
        if root.job_start_time and root.current_job:
            elapsed_seconds = time.time() - root.job_start_time
            elapsed_str = f"{int(elapsed_seconds//3600):02d}:{int((elapsed_seconds%3600)//60):02d}:{int(elapsed_seconds%60):02d}"
            root.elapsed_label.setText(f"Elapsed: {elapsed_str}")
    
    def update_stats():
        """Update speed and progress stats more frequently"""
        if root.job_start_time and root.current_job and hasattr(root, 'copied_bytes') and hasattr(root, 'total_bytes'):
            elapsed_seconds = time.time() - root.job_start_time
            if elapsed_seconds > 0 and root.total_bytes > 0:
                # Calculate current speed
                current_speed = (root.copied_bytes / (1024 * 1024)) / elapsed_seconds
                
                # Update progress bar
                if hasattr(root, 'total_progress'):
                    progress_percent = int((root.copied_bytes / root.total_bytes) * 100)
                    root.total_progress.setValue(progress_percent)
                    root.total_progress.setFormat(f"{progress_percent}%")  # Update the text format
                
                # Update speed label
                if hasattr(root, 'speed_label'):
                    root.speed_label.setText(f"{current_speed:.0f} MB/s")
                
                # Update current speed stat
                if hasattr(root, 'current_speed_label'):
                    root.current_speed_label.setText(f"Speed: {current_speed:.0f} MB/s")
                
                # Calculate average speed
                if hasattr(root, 'avg_speed_label'):
                    total_mb = root.total_bytes / (1024 * 1024)
                    avg_speed = total_mb / elapsed_seconds
                    root.avg_speed_label.setText(f"Avg: {avg_speed:.0f} MB/s")
                
                # Update peak speed if current speed is higher
                if hasattr(root, 'peak_speed_label'):
                    try:
                        current_peak_text = root.peak_speed_label.text()
                        if "Peak: " in current_peak_text:
                            current_peak = float(current_peak_text.split(': ')[1].split(' ')[0])
                            if current_speed > current_peak:
                                root.peak_speed_label.setText(f"Peak: {current_speed:.0f} MB/s")
                    except (ValueError, IndexError):
                        # If we can't parse the current peak, just set it
                        root.peak_speed_label.setText(f"Peak: {current_speed:.0f} MB/s")
                
                # Calculate ETA
                if hasattr(root, 'eta_label') and current_speed > 0 and root.copied_bytes < root.total_bytes:
                    remaining_bytes = root.total_bytes - root.copied_bytes
                    eta_seconds = remaining_bytes / (current_speed * 1024 * 1024)
                    if eta_seconds > 0:
                        eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                        root.eta_label.setText(f"ETA: {eta_str}")
                    else:
                        root.eta_label.setText("ETA: --:--:--")
                elif hasattr(root, 'eta_label'):
                    root.eta_label.setText("ETA: --:--:--")
                
                # Update total time label
                if hasattr(root, 'total_time_label'):
                    elapsed_str = f"{int(elapsed_seconds//3600):02d}:{int((elapsed_seconds%3600)//60):02d}:{int(elapsed_seconds%60):02d}"
                    root.total_time_label.setText(f"Total: {elapsed_str}")
                
                # Update total speed label
                if hasattr(root, 'total_speed_label'):
                    root.total_speed_label.setText(f"{current_speed:.0f} MB/s")
                
                # Force updates for all widgets
                if hasattr(root, 'total_progress'):
                    root.total_progress.repaint()
                    root.total_progress.update()
                if hasattr(root, 'speed_label'):
                    root.speed_label.repaint()
                    root.speed_label.update()
    
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
    
    # Header
    header_label = QLabel("Turbo Transfer")
    header_label.setStyleSheet(HEADER_LABEL_STYLE)
    layout.addWidget(header_label)
    
    # Source and Destinations (compact)
    paths_layout = QVBoxLayout()
    paths_layout.setSpacing(5)  # Reduced to 5px for tight spacing
    
    # Source with dropdown
    src_layout = QVBoxLayout()
    src_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    src_label = QLabel("Source:")
    src_label.setStyleSheet(FIELD_LABEL_STYLE)
    
    # Source dropdown
    src_combo = QComboBox()
    src_combo.setEditable(True)
    src_combo.setStyleSheet(COMBOBOX_STYLE)
    src_combo.setPlaceholderText("Select source folder...")
    
    # Add recent sources to dropdown
    for source in recent_sources:
        src_combo.addItem(source)
    
    # Source browse button
    src_btn = QPushButton("Browse…")
    src_btn.setObjectName("src_browse_btn")
    # Use the standard app colors
    src_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 5px 10px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {colors['hover_bg']};
            border: 1px solid {colors['accent']};
        }}
        QPushButton:pressed {{
            background-color: {colors['accent']};
            color: white;
        }}
    """)
    
    src_row = QHBoxLayout()
    src_row.setSpacing(2)  # Reduced to 2px for very tight spacing
    src_row.addWidget(src_combo, 1)
    src_row.addWidget(src_btn)
    
    src_layout.addWidget(src_label)
    src_layout.addLayout(src_row)
    paths_layout.addLayout(src_layout)
    
    # Destinations section with pinned header and scrollable content
    dest_frame = QFrame()
    dest_frame.setStyleSheet(CARD_FRAME_STYLE)
    dest_layout = QVBoxLayout(dest_frame)
    dest_layout.setSpacing(5)
    dest_layout.setContentsMargins(5, 5, 5, 5)
    
    # Destinations header (pinned to top)
    dest_header = QHBoxLayout()
    dest_label = QLabel("Destinations:")
    dest_label.setStyleSheet(FIELD_LABEL_STYLE)
    
    # Destinations dropdown
    dest_combo = QComboBox()
    dest_combo.setEditable(True)
    dest_combo.setStyleSheet(COMBOBOX_STYLE)
    dest_combo.setPlaceholderText("Select destination folder...")
    
    # Add recent destinations to dropdown
    for destination in recent_destinations:
        dest_combo.addItem(destination)
    
    add_dest_btn = QPushButton("+ Add Destination")
    add_dest_btn.setObjectName("add_dest_btn")
    add_dest_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 5px 10px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {colors['hover_bg']};
            border: 1px solid {colors['accent']};
        }}
        QPushButton:pressed {{
            background-color: {colors['accent']};
            color: white;
        }}
    """)
    
    dest_header.addWidget(dest_label)
    dest_header.addWidget(dest_combo, 1)
    dest_header.addWidget(add_dest_btn)
    dest_layout.addLayout(dest_header)
    
    # Destinations list (scrollable with expandable height)
    dest_scroll = QScrollArea()
    dest_scroll.setWidgetResizable(True)
    dest_scroll.setMinimumHeight(80)
    dest_scroll.setMaximumHeight(400)  # Increased max height for more destinations
    dest_scroll.setStyleSheet(SCROLL_AREA_STYLE)
    dest_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    dest_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    dest_container = QWidget()
    dest_container_layout = QVBoxLayout(dest_container)
    dest_container_layout.setSpacing(2)
    dest_container_layout.setContentsMargins(0, 0, 0, 0)
    dest_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    
    dest_scroll.setWidget(dest_container)
    dest_layout.addWidget(dest_scroll)
    
    paths_layout.addWidget(dest_frame)
    
    # Store references for later use
    root.dest_container = dest_container
    root.dest_container_layout = dest_container_layout
    root.destinations = []  # List of destination objects
    root.src_combo = src_combo
    root.dest_combo = dest_combo
    
    layout.addLayout(paths_layout)
    
    # Settings (compact)
    settings_layout = QHBoxLayout()
    settings_layout.setSpacing(5)  # Reduced to 5px for tight spacing
    
    # Global Preset
    preset_layout = QVBoxLayout()
    preset_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    preset_label = QLabel("Global Preset:")
    preset_label.setStyleSheet(FIELD_LABEL_STYLE)
    preset_combo = QComboBox()
    preset_combo.addItems([
        "Auto (recommended)",
        "USB/TB",
        "Network",
        "Custom"
    ])
    preset_combo.setStyleSheet(COMBOBOX_STYLE)
    preset_combo.setCurrentIndex(0)
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(preset_combo)
        print("DEBUG: Applied hover delegate to preset_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to preset_combo: {e}")
    
    preset_layout.addWidget(preset_label)
    preset_layout.addWidget(preset_combo)
    settings_layout.addLayout(preset_layout)
    
    # Verify Mode
    verify_layout = QVBoxLayout()
    verify_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    verify_label = QLabel("Verify Mode:")
    verify_label.setStyleSheet(FIELD_LABEL_STYLE)
    verify_combo = QComboBox()
    verify_combo.addItems([
        "FAST",
        "STREAM_VERIFY",
        "READBACK_VERIFY"
    ])
    verify_combo.setStyleSheet(COMBOBOX_STYLE)
    verify_combo.setCurrentIndex(0)
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(verify_combo)
        print("DEBUG: Applied hover delegate to verify_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to verify_combo: {e}")
    
    verify_layout.addWidget(verify_label)
    verify_layout.addWidget(verify_combo)
    settings_layout.addLayout(verify_layout)
    
    # Concurrency sliders
    conc_layout = QVBoxLayout()
    conc_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    conc_label = QLabel("Per-file concurrency:")
    conc_label.setStyleSheet(FIELD_LABEL_STYLE)
    conc_slider = QSlider(Qt.Orientation.Horizontal)
    conc_slider.setRange(1, 16)
    conc_slider.setValue(1)
    conc_slider.setStyleSheet(SLIDER_STYLE)
    conc_value = QLabel("1")
    conc_value.setStyleSheet(ACCENT_VALUE_STYLE)
    conc_slider.valueChanged.connect(lambda v: conc_value.setText(str(v)))
    
    conc_row = QHBoxLayout()
    conc_row.setSpacing(2)  # Reduced to 2px for very tight spacing
    conc_row.addWidget(conc_slider, 1)
    conc_row.addWidget(conc_value)
    
    conc_layout.addWidget(conc_label)
    conc_layout.addLayout(conc_row)
    settings_layout.addLayout(conc_layout)
    
    # Stream concurrency
    stream_layout = QVBoxLayout()
    stream_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    stream_label = QLabel("Stream concurrency:")
    stream_label.setStyleSheet(FIELD_LABEL_STYLE)
    stream_slider = QSlider(Qt.Orientation.Horizontal)
    stream_slider.setRange(1, 32)
    stream_slider.setValue(2)
    stream_slider.setStyleSheet(SLIDER_STYLE)
    stream_value = QLabel("2")
    stream_value.setStyleSheet(ACCENT_VALUE_STYLE)
    stream_slider.valueChanged.connect(lambda v: stream_value.setText(str(v)))
    
    stream_row = QHBoxLayout()
    stream_row.setSpacing(2)  # Reduced to 2px for very tight spacing
    stream_row.addWidget(stream_slider, 1)
    stream_row.addWidget(stream_value)
    
    stream_layout.addWidget(stream_label)
    stream_layout.addLayout(stream_row)
    settings_layout.addLayout(stream_layout)
    
    # NEW: Verification Report checkbox
    report_layout = QVBoxLayout()
    report_layout.setSpacing(2)
    report_checkbox = QCheckBox("Generate Verification Report")
    report_checkbox.setChecked(True)  # Default to enabled
    report_checkbox.setStyleSheet(f"""
        QCheckBox {{
            color: {colors['text']};
            font-size: 12px;
            spacing: 5px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['border']};
            border-radius: 3px;
            background-color: {colors['card_bg']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {colors['accent']};
            border-color: {colors['accent']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {colors['accent']};
        }}
    """)
    report_layout.addWidget(report_checkbox)
    settings_layout.addLayout(report_layout)
    
    # Store reference for later use
    root.report_checkbox = report_checkbox
    
    layout.addLayout(settings_layout)
    
    # Control buttons
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(5)  # Reduced to 5px for tight spacing
    
    start_btn = QPushButton("Start Transfer")
    start_btn.setObjectName("start_transfer_btn")
    # Use the standard app accent color - force the blue color
    start_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: #2C4F76;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: #36648B;
        }}
        QPushButton:pressed {{
            background-color: #1E3A5C;
        }}
        QPushButton:disabled {{
            background-color: #1E1E1E;
            color: #666666;
            border: 1px solid #666666;
        }}
    """)
    start_btn.setFixedHeight(40)
    start_btn.setEnabled(False)
    
    pause_btn = QPushButton("Pause")
    pause_btn.setObjectName("pause_btn")
    # Use the standard app colors
    pause_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {colors['card_bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 5px 10px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {colors['hover_bg']};
            border: 1px solid {colors['accent']};
        }}
        QPushButton:pressed {{
            background-color: {colors['accent']};
            color: white;
        }}
        QPushButton:disabled {{
            background-color: #1E1E1E;
            color: #666666;
            border: 1px solid #666666;
        }}
    """)
    pause_btn.setFixedHeight(40)
    pause_btn.setEnabled(False)
    
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setObjectName("cancel_btn")
    # Use simple styling like the working main app buttons
    cancel_btn.setStyleSheet("""
        QPushButton {
            background-color: #902A2A;
            color: white;
            border: 1px solid #732121;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #A33030;
            border: 1px solid #8A2727;
        }
        QPushButton:pressed {
            background-color: #7D2525;
        }
        QPushButton:disabled {
            background-color: #1E1E1E;
            color: #666666;
            border: 1px solid #666666;
        }
    """)
    cancel_btn.setFixedHeight(40)
    cancel_btn.setEnabled(False)
    
    buttons_layout.addWidget(start_btn)
    buttons_layout.addWidget(pause_btn)
    buttons_layout.addWidget(cancel_btn)
    
    layout.addLayout(buttons_layout)
    
    # Main progress display (clean, compact)
    progress_frame = QFrame()
    progress_frame.setStyleSheet(CARD_FRAME_STYLE)
    progress_layout = QVBoxLayout(progress_frame)
    progress_layout.setSpacing(0)  # No spacing between speed and progress bar
    progress_layout.setContentsMargins(5, 5, 5, 5)  # Reduced to 5px for tight spacing
    
    # Speed display (above progress bar, smaller and white)
    speed_label = QLabel("0 MB/s Transfer")
    speed_label.setStyleSheet(SPEED_LABEL_STYLE)
    speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    progress_layout.addWidget(speed_label)
    
    # Total progress with integrated label - now 3x taller with gradient
    total_progress = QProgressBar()
    total_progress.setRange(0, 100)
    total_progress.setValue(0)
    total_progress.setFixedHeight(60)  # 3x taller (was 20px)
    total_progress.setStyleSheet(PROGRESS_BAR_STYLE)
    total_progress.setVisible(True)  # Ensure it's visible
    total_progress.setEnabled(True)  # Ensure it's enabled
    total_progress.setFormat("%p%")  # Show percentage
    total_progress.setTextVisible(True)  # Ensure text is visible
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
    
    layout.addWidget(progress_frame)

    # Add total time and total speed labels (footer row)
    root.total_time_label = QtWidgets.QLabel("Total: 00:00")
    root.total_speed_label = QtWidgets.QLabel("— MB/s")
    stats_row = QtWidgets.QHBoxLayout()
    stats_row.addWidget(root.total_time_label)
    stats_row.addStretch(1)
    stats_row.addWidget(root.total_speed_label)
    layout.addLayout(stats_row)
    
    # Individual files section - restored from C++ engine layout
    files_frame = QFrame()
    files_frame.setStyleSheet(CARD_FRAME_STYLE)
    files_layout = QVBoxLayout(files_frame)
    files_layout.setSpacing(5)
    files_layout.setContentsMargins(5, 5, 5, 5)
    
    # Combined time and speed display section - inline to save space
    time_speed_layout = QHBoxLayout()
    time_speed_layout.setSpacing(15)
    
    # Elapsed time
    elapsed_label = QLabel("Elapsed: 00:00:00")
    elapsed_label.setStyleSheet(TIME_LABEL_STYLE)
    time_speed_layout.addWidget(elapsed_label)
    
    # ETA
    eta_label = QLabel("ETA: --:--:--")
    eta_label.setStyleSheet(TIME_LABEL_STYLE)
    time_speed_layout.addWidget(eta_label)
    
    # Current speed
    current_speed_label = QLabel("Speed: 0 MB/s")
    current_speed_label.setStyleSheet(SPEED_LABEL_STYLE)
    time_speed_layout.addWidget(current_speed_label)
    
    # Average speed
    avg_speed_label = QLabel("Avg: 0 MB/s")
    avg_speed_label.setStyleSheet(SPEED_LABEL_STYLE)
    time_speed_layout.addWidget(avg_speed_label)
    
    # Peak speed
    peak_speed_label = QLabel("Peak: 0 MB/s")
    peak_speed_label.setStyleSheet(SPEED_LABEL_STYLE)
    time_speed_layout.addWidget(peak_speed_label)
    
    time_speed_layout.addStretch()
    files_layout.addLayout(time_speed_layout)
    
    # Files header - positioned below time display
    files_header = QHBoxLayout()
    files_header.setSpacing(5)
    files_header.setContentsMargins(0, 0, 0, 5)
    files_label = QLabel("Individual Files")
    files_label.setStyleSheet(SECTION_HEADER_STYLE)
    files_count = QLabel("0 files")
    files_count.setStyleSheet(SECONDARY_TEXT_STYLE)
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
    root.speed_label = speed_label
    
    # Add status label for current file
    status_label = QLabel("Ready")
    status_label.setStyleSheet(LABEL_STYLE)
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    files_layout.addWidget(status_label)
    root.status_label = status_label
    
    # Scrollable area for file progress - more compact
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMinimumHeight(100)  # Reduced minimum height
    scroll_area.setMaximumHeight(400)  # Increased maximum height for resizability
    scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Make it resizable
    scroll_area.setStyleSheet(SCROLL_AREA_STYLE)
    
    # Files container - ensure proper layout
    files_container = QWidget()
    files_container_layout = QVBoxLayout(files_container)
    files_container_layout.setSpacing(2)  # Very tight spacing between file widgets
    files_container_layout.setContentsMargins(0, 0, 0, 0)
    files_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Align widgets to top
    
    scroll_area.setWidget(files_container)
    files_layout.addWidget(scroll_area)
    
    # Store files container references for handlers
    root.files_container_layout = files_container_layout
    root.files_count = files_count
    
    layout.addWidget(files_frame)
    
    # Destination management functions
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
            # Add to recent destinations
            add_to_recent_locations(path, is_source=False)
            
            dest_obj = {
                "path": path,
                "preset": "auto",
                "block_size": None,
                "files_in_flight": None,
                "ranges_per_file": None,
                "use_direct_io": None,
                "verify": "FAST"
            }
            root.destinations.append(dest_obj)
            create_destination_widget(dest_obj)
            check_button_states()
            
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
        dest_layout.setSpacing(5)
        dest_layout.setContentsMargins(5, 5, 5, 5)
        
        # Top row: path and controls
        top_row = QHBoxLayout()
        top_row.setSpacing(5)
        
        # Path display
        path_label = QLabel(dest_obj["path"])
        path_label.setStyleSheet(LABEL_STYLE)
        path_label.setWordWrap(True)
        top_row.addWidget(path_label, 1)
        
        # Preset dropdown
        preset_combo = QComboBox()
        preset_combo.addItems(["Auto", "USB/TB", "Network", "Custom"])
        preset_combo.setCurrentText(dest_obj["preset"])
        preset_combo.setStyleSheet(COMBOBOX_STYLE)
        preset_combo.currentTextChanged.connect(lambda text: update_dest_preset(dest_obj, text))
        top_row.addWidget(preset_combo)
        

        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #902A2A;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #A33030;
            }}
        """)
        remove_btn.clicked.connect(lambda: remove_destination(dest_obj, dest_widget))
        top_row.addWidget(remove_btn)
        
        dest_layout.addLayout(top_row)
        
        # Bottom row: progress bar
        progress_row = QHBoxLayout()
        progress_row.setSpacing(5)
        
        # Progress bar for this destination
        dest_progress = QProgressBar()
        dest_progress.setRange(0, 100)
        dest_progress.setValue(0)
        dest_progress.setFixedHeight(15)
        dest_progress.setStyleSheet(PROGRESS_BAR_STYLE)
        dest_progress.setVisible(False)
        dest_progress.setFormat(f"Dest {len(root.destinations)+1}: %p%")
        dest_progress.setTextVisible(True)
        progress_row.addWidget(dest_progress, 1)
        
        # Status label for this destination
        dest_status = QLabel("Ready")
        dest_status.setStyleSheet(SECONDARY_TEXT_STYLE)
        dest_status.setFixedWidth(80)
        progress_row.addWidget(dest_status)
        
        dest_layout.addLayout(progress_row)
        
        # Store references
        dest_obj["widget"] = dest_widget
        dest_obj["progress_bar"] = dest_progress
        dest_obj["status_label"] = dest_status
        
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
        """Cancel a specific destination"""
        print(f"DEBUG: Canceling destination: {dest_obj['path']}")
        try:
            if root.current_job and hasattr(root.current_job, 'cancel_destination'):
                root.current_job.cancel_destination(dest_obj['path'])
                print(f"DEBUG: Cancel command sent for destination: {dest_obj['path']}")
            else:
                print(f"DEBUG: No current job or job doesn't have cancel_destination method")
            
            # Update destination status
            if 'status_label' in dest_obj:
                dest_obj['status_label'].setText("Cancelled")
                
        except Exception as e:
            print(f"DEBUG: Error canceling destination: {e}")
            import traceback
            traceback.print_exc()
    
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
            
            # Update UI widgets safely
            if hasattr(root, 'total_progress') and root.total_progress:
                # Keep the progress bar at 0-100 range for percentage
                root.total_progress.setValue(0)
                root.total_progress.setVisible(True)
                print("DEBUG: Total progress bar updated")
            
            if hasattr(root, 'status_label') and root.status_label:
                root.status_label.setText(f"Copying {total_files} files ({total_bytes:,} bytes)")
                print("DEBUG: Status label updated")
            
            if hasattr(root, 'elapsed_label') and root.elapsed_label:
                root.elapsed_label.setText("00:00")
                print("DEBUG: Elapsed label updated")
            
            if hasattr(root, 'speed_label') and root.speed_label:
                root.speed_label.setText("— MB/s")
                print("DEBUG: Speed label updated")
            
            # Show destination progress bars
            if hasattr(root, 'destinations'):
                print(f"DEBUG: Showing progress bars for {len(root.destinations)} destinations")
                for i, dest_obj in enumerate(root.destinations):
                    # Show progress bar
                    if 'progress_bar' in dest_obj:
                        dest_obj['progress_bar'].setVisible(True)
                        dest_obj['progress_bar'].setValue(0)
                        print(f"DEBUG: Showed progress bar for destination {i+1}")
                    
                    # Update status
                    if 'status_label' in dest_obj:
                        dest_obj['status_label'].setText("Copying...")
                        print(f"DEBUG: Updated status for destination {i+1}")
            
            # Store data for later use
            root.job_start_time = time.time()
            root.job_data = {
                'total_bytes': total_bytes,
                'total_files': total_files,
                'start_time': time.time(),
                'copied_bytes': 0
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
            
            # Update total progress bar with percentage
            if hasattr(root, 'total_progress') and root.total_progress:
                root.total_progress.setValue(progress_percent)
                print(f"DEBUG: Total progress bar updated to {progress_percent}%")
            
            # Update destination progress bars (for multi-destination) with percentage
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                        dest_obj['progress_bar'].setValue(progress_percent)
                        print(f"DEBUG: Destination {i+1} progress bar updated to {progress_percent}%")
                        
                        # Update destination status
                        if 'status_label' in dest_obj:
                            dest_obj['status_label'].setText(f"{progress_percent}%")
            
            # Update speed and elapsed time
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

                if hasattr(root, 'speed_label') and root.speed_label and speed_mbps is not None:
                    root.speed_label.setText(f"{float(speed_mbps):.1f} MB/s")
                    print("DEBUG: Speed label updated")

                if hasattr(root, 'elapsed_label') and root.elapsed_label:
                    elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                    root.elapsed_label.setText(f"Elapsed: {elapsed_str}")
                    print("DEBUG: Elapsed label updated")
            
            # Update status
            if hasattr(root, 'status_label') and root.status_label:
                percent = (copied_bytes / total_bytes * 100) if total_bytes > 0 else 0
                root.status_label.setText(f"Copying... {percent:.1f}% ({copied_bytes:,}/{total_bytes:,} bytes)")
                print("DEBUG: Status label updated")
            
            # Update stored data
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
            
    def handle_file_started(payload):
        print(f"DEBUG: handle_file_started called with: {payload}")
        try:
            # Get filename from payload (support multiple payload shapes)
            filename = payload.get("filename") or payload.get("file_path") or "unknown"
            total_bytes = payload.get("total_bytes") or payload.get("total") or 0
            file_id = payload.get("file_id", "unknown")
            print(f"DEBUG: File started: {filename} - {total_bytes} bytes")
            
            # Create file progress widget
            if file_id not in root.file_widgets:
                file_widget = FileProgressLine(filename, total_bytes)
                root.file_widgets[file_id] = file_widget
                root.files_container_layout.addWidget(file_widget)
                root.active_files += 1
                root.files_count.setText(f"{root.active_files} files")
                print(f"DEBUG: Created file widget for {filename}, active files: {root.active_files}")
            
            # Update status label to show current file
            if hasattr(root, 'status_label') and root.status_label and filename != "unknown":
                root.status_label.setText(f"Copying: {filename}")
                print(f"DEBUG: Status updated to show file: {filename}")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_file_started: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_progress(payload):
        print(f"DEBUG: handle_file_progress called with: {payload}")
        try:
            # Get file progress data (support multiple payload shapes)
            file_label = payload.get("file_path") or payload.get("filename") or "unknown"
            file_copied = payload.get("copied_bytes")
            if file_copied is None:
                file_copied = payload.get("bytes", 0)
            file_total = payload.get("total_bytes")
            if file_total is None:
                file_total = payload.get("total", 0)
            file_id = payload.get("file_id", "unknown")
            print(f"DEBUG: File progress: {file_label} - {file_copied}/{file_total}")
            
            # Update file progress widget
            if file_id in root.file_widgets:
                root.file_widgets[file_id].update_progress(file_copied)
                print(f"DEBUG: Updated file widget progress for {file_label}")
            
            # Do not modify global job counters here; job.progress drives overall bar.
            # Optionally surface active filename in status for user feedback
            if hasattr(root, 'status_label') and root.status_label and file_label != "unknown":
                root.status_label.setText(f"Copying: {file_label}")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_file_progress: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_completed(payload):
        print(f"DEBUG: handle_file_completed called with: {payload}")
        try:
            # Get file completion data
            filename = payload.get("filename") or payload.get("file_path") or "unknown"
            bytes_copied = payload.get("bytes") or payload.get("bytes_copied") or 0
            total_bytes = payload.get("total") or payload.get("total_bytes") or 0
            file_id = payload.get("file_id", "unknown")
            print(f"DEBUG: File completed: {filename} - {bytes_copied}/{total_bytes} bytes")
            
            # Mark file as completed and schedule removal
            if file_id in root.file_widgets:
                root.file_widgets[file_id].mark_completed()
                # Schedule removal after a delay
                QTimer.singleShot(2000, lambda: _remove_file_widget(file_id))
                root.active_files -= 1
                root.files_count.setText(f"{root.active_files} files")
                print(f"DEBUG: File marked as completed, active files: {root.active_files}")
            
            # Update file count if available
            if hasattr(root, 'job_data') and root.job_data:
                root.job_data['completed_files'] = root.job_data.get('completed_files', 0) + 1
                print(f"DEBUG: Completed files: {root.job_data['completed_files']}")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_file_completed: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_dest_progress(payload):
        print(f"DEBUG: handle_dest_progress called with: {payload}")
        try:
            # Get destination progress data
            dest_index = payload.get("dest_index", 0)
            dest_path = payload.get("dest_path", "unknown")
            bytes_copied = payload.get("bytes_copied", 0)
            total_bytes = payload.get("total_bytes", 0)
            print(f"DEBUG: Destination {dest_index} progress: {dest_path} - {bytes_copied}/{total_bytes} bytes")
            
            # Update destination-specific progress bar
            if hasattr(root, 'destinations') and dest_index < len(root.destinations):
                dest_obj = root.destinations[dest_index]
                if 'progress_bar' in dest_obj and dest_obj['progress_bar']:
                    dest_obj['progress_bar'].setValue(bytes_copied)
                    print(f"DEBUG: Destination {dest_index} progress bar updated")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_dest_progress: {e}")
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
                files_count.setText(f"{root.active_files} files")
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
            
            if hasattr(root, 'status_label') and root.status_label:
                speed_mbps = speed if isinstance(speed, (int, float)) else 0
                root.status_label.setText(f"Completed! {speed_mbps:.1f} MB/s average")
                print("DEBUG: Status label updated to show completion")
            
            if hasattr(root, 'speed_label') and root.speed_label:
                speed_mbps = speed if isinstance(speed, (int, float)) else 0
                root.speed_label.setText(f"{speed_mbps:.1f} MB/s")
                print("DEBUG: Speed label updated")
            
            if hasattr(root, 'elapsed_label') and root.elapsed_label:
                elapsed_str = f"{int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                root.elapsed_label.setText(f"Elapsed: {elapsed_str}")
                print("DEBUG: Elapsed label updated")
            
            # Update destination status
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'status_label' in dest_obj:
                        dest_obj['status_label'].setText("Completed")
                    if 'progress_bar' in dest_obj:
                        dest_obj['progress_bar'].setValue(100)
                print("DEBUG: Destination controls updated")
            
            # Re-enable controls after job completion
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
            cancel_btn.setEnabled(False)
            print("DEBUG: Main controls re-enabled")
            
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
                files_container_layout.removeWidget(widget)
                widget.deleteLater()
                del root.file_widgets[file_id]
                print(f"DEBUG: Widget {file_id} removed successfully")
                print(f"DEBUG: Remaining file widgets: {list(root.file_widgets.keys())}")
                print(f"DEBUG: Container layout count: {files_container_layout.count()}")
            else:
                print(f"DEBUG: Widget {file_id} not found in root.file_widgets")
                print(f"DEBUG: Available file widgets: {list(root.file_widgets.keys())}")
                
        except Exception as e:
            print(f"DEBUG: Error in _remove_file_widget: {e}")
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
            self._timer.start(200)  # Process events every 200ms (even slower for stability)
            print(f"DEBUG: QtSink timer started with interval 200ms")
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
                        print(f"DEBUG: Processing event: {event_type}")
                        
                        # Check if widgets are still valid before processing
                        if not self._widgets_valid:
                            print(f"DEBUG: Skipping event {event_type} - widgets no longer valid")
                            continue
                        
                        # Call the actual UI handlers
                        if event_type == "job.started":
                            handle_job_started(payload)
                        elif event_type == "job.progress":
                            handle_job_progress(payload)
                        elif event_type == "file.started":
                            handle_file_started(payload)
                        elif event_type == "file.progress":
                            handle_file_progress(payload)
                        elif event_type == "file.completed":
                            handle_file_completed(payload)
                        elif event_type == "file.failed":
                            print(f"DEBUG: File failed event received - {payload.get('filename', 'unknown')} - Error: {payload.get('error', 'unknown')}")
                        elif event_type == "job.completed":
                            handle_job_completed(payload)
                        elif event_type == "job.cancelled":
                            handle_job_cancelled(payload)
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
    
    # Connect bridge signals to handlers (queued to GUI thread)
    bridge = get_bridge()
    bridge.sigJobStarted.connect(handle_job_started, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobProgress.connect(handle_job_progress, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobCompleted.connect(handle_job_completed, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobError.connect(lambda p: print("job.error", p), QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigFileStarted.connect(handle_file_started, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigFileProgress.connect(handle_file_progress, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigFileCompleted.connect(handle_file_completed, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigDestProgress.connect(handle_dest_progress, QtCore.Qt.ConnectionType.QueuedConnection)
    bridge.sigJobCancelled.connect(handle_job_cancelled, QtCore.Qt.ConnectionType.QueuedConnection)
    
    # Wire up button handlers
    def on_start():
        if not root.src_combo.currentText().strip() or not root.destinations:
            print("DEBUG: Source path is empty or no destinations added")
            return
        
        # Check if we're resuming a paused job
        if root.current_job and hasattr(root.current_job, 'resume'):
            print("DEBUG: Resuming paused job")
            on_resume()
            return
        
        # Create a unique job ID
        job_id = f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"DEBUG: Starting ingest job: {job_id}")
        
        # Update UI state
        start_btn.setEnabled(False)
        pause_btn.setEnabled(True)
        cancel_btn.setEnabled(True)
        
        def run():
            print(f"DEBUG: Starting ingest job in background thread")
            # Get job parameters from UI
            source_path = root.src_combo.currentText().strip()
            dest_paths = [dest["path"] for dest in root.destinations]
            verify_mode = verify_combo.currentText()
            global_preset = preset_combo.currentText()
            
            print(f"DEBUG: Source: {source_path}")
            print(f"DEBUG: Destinations: {dest_paths}")
            print(f"DEBUG: Verify Mode: {verify_mode}")
            print(f"DEBUG: Global Preset: {global_preset}")
            
            try:
                # Import the necessary classes for creating a proper job
                print(f"DEBUG: Importing JobSpec and JobOptions...")
                # JobSpec and JobOptions are already imported at the top
                from pathlib import Path
                print(f"DEBUG: JobSpec and JobOptions imported successfully")
                
                # Create a JobSpec with the source and multiple destinations
                print(f"DEBUG: Creating JobSpec...")
                job = JobSpec(
                    job_id=job_id,
                    source_root=source_path,
                    destination_roots=dest_paths,  # Multiple destinations
                    options=JobOptions(
                        mode="FAST" if verify_mode == "FAST" else "BALANCED",
                        verify_mode=verify_mode,
                        preset=global_preset,
                        per_file_concurrency=1,  # Will be auto-tuned per destination
                        stream_concurrency=1,    # Will be auto-tuned per destination
                        # NEW: Include verification report option
                        generate_verification_report=root.report_checkbox.isChecked()
                    )
                )
                
                print(f"DEBUG: Created JobSpec: {job}")
                
                # Use bridge emitter via engine wrapper
                sink = type("BridgeSink", (), {"emit": lambda _self, kind, payload: emit_event(kind, payload)})()
                print(f"DEBUG: Using BridgeSink")
                
                # Create and start the engine
                print(f"DEBUG: Importing PythonCopyEngine...")
                # PythonCopyEngine is already imported at the top
                print(f"DEBUG: PythonCopyEngine imported successfully")
                
                print(f"DEBUG: Creating PythonCopyEngine instance...")
                engine = PythonCopyEngine(sink=sink)
                print(f"DEBUG: PythonCopyEngine created: {engine}")
                
                # Check which engine type is being used
                if hasattr(engine, '_cpp_engine_used'):
                    print("DEBUG: C++ engine is being used")
                else:
                    print("DEBUG: Python fallback engine is being used")
                
                # Store the engine reference (not the thread)
                root.current_job = engine
                print(f"DEBUG: Engine stored in root.current_job")
                
                # Freeze controls during copy
                conc_slider.setEnabled(False)
                stream_slider.setEnabled(False)
                verify_combo.setEnabled(False)
                preset_combo.setEnabled(False)
                add_dest_btn.setEnabled(False)
                root.report_checkbox.setEnabled(False)
                print(f"DEBUG: Controls frozen")
                
                print(f"DEBUG: Starting engine with job: {job}")
                engine.start(job)
                print(f"DEBUG: Engine completed")
                
            except Exception as e:
                print(f"DEBUG: Error starting engine: {e}")
                traceback.print_exc()
                # Re-enable controls on error
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                add_dest_btn.setEnabled(True)
                root.report_checkbox.setEnabled(True)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                print(f"DEBUG: Controls re-enabled after error")

        # Start in background thread with better error handling
        try:
            job_thread = threading.Thread(target=run, daemon=True)
            job_thread.start()
            # Don't store the thread in current_job - store the engine instead
        except Exception as e:
            print(f"DEBUG: Error creating job thread: {e}")
            traceback.print_exc()
            # Re-enable controls on thread creation error
            conc_slider.setEnabled(True)
            stream_slider.setEnabled(True)
            verify_combo.setEnabled(True)
            preset_combo.setEnabled(True)
            add_dest_btn.setEnabled(True)
            root.report_checkbox.setEnabled(True)
            start_btn.setEnabled(True)
            pause_btn.setEnabled(False)
            cancel_btn.setEnabled(False)
    
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
            if root.current_job and hasattr(root.current_job, 'cancel'):
                print("DEBUG: Canceling engine")
                # Get the job ID from the engine
                if hasattr(root.current_job, 'get_current_job_id'):
                    job_id = root.current_job.get_current_job_id() or 'current'
                else:
                    job_id = 'current'
                
                root.current_job.cancel(job_id)
                print("DEBUG: Cancel command sent to engine")
                
                # Don't re-enable start button yet - wait for job.cancelled event
                # The button states will be updated when the job actually stops
                print("DEBUG: Waiting for job to actually cancel...")
            else:
                print("DEBUG: No current job or job doesn't have cancel method")
                print(f"DEBUG: root.current_job: {root.current_job}")
                if root.current_job:
                    print(f"DEBUG: Job type: {type(root.current_job)}")
                    print(f"DEBUG: Job attributes: {dir(root.current_job)}")
        except Exception as e:
            print(f"DEBUG: Error in on_cancel: {e}")
            import traceback
            traceback.print_exc()
        
        # Don't update button states here - wait for job.cancelled event
        print("DEBUG: Cancel command sent, waiting for job to stop...")
    
    def handle_job_cancelled(payload):
        """Handle job cancellation completion"""
        print(f"DEBUG: handle_job_cancelled called with: {payload}")
        try:
            # Job has been cancelled, update UI
            if hasattr(root, 'total_progress') and root.total_progress:
                root.total_progress.setValue(0)
                print("DEBUG: Progress bar reset to 0%")
            
            if hasattr(root, 'status_label') and root.status_label:
                root.status_label.setText("Cancelled")
                print("DEBUG: Status label updated to show cancellation")
            
            # Update destination status
            if hasattr(root, 'destinations'):
                for i, dest_obj in enumerate(root.destinations):
                    if 'status_label' in dest_obj:
                        dest_obj['status_label'].setText("Cancelled")
                    if 'progress_bar' in dest_obj:
                        dest_obj['progress_bar'].setValue(0)
                print("DEBUG: Destination controls updated for cancellation")
            
            # Clear file widgets
            if hasattr(root, 'file_widgets'):
                for file_id in list(root.file_widgets.keys()):
                    _remove_file_widget(file_id)
                root.active_files = 0
                files_count.setText("0 files")
                print("DEBUG: File widgets cleared")
            
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
            cancel_btn.setEnabled(False)
            print("DEBUG: Main controls re-enabled after cancellation")
            
            print("DEBUG: handle_job_cancelled completed successfully")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_cancelled: {e}")
            import traceback
            traceback.print_exc()
    
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


