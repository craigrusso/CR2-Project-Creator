"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built here to keep ingest self-contained. The host app
calls `build_ingest_tab()` under a feature flag to add the tab.
"""

from __future__ import annotations

import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import collections # Added for rolling speed calculation

from PyQt6.QtCore import (
    QTimer,
    Qt,
    pyqtSignal,
    QObject,
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
)

from .ingest_vm import IngestViewModel
from .file_progress_line import FileProgressLine
from ..engines.python_engine import PythonCopyEngine
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
    root.stats_update_timer.start(500)  # Update every 500ms for more responsive stats
    
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
                    root.speed_label.setText(f"{current_speed:.0f} MB/s Transfer")
                
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
    
    # Source and Destination (compact)
    paths_layout = QHBoxLayout()
    paths_layout.setSpacing(5)  # Reduced to 5px for tight spacing
    
    # Source
    src_layout = QVBoxLayout()
    src_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    src_label = QLabel("Source:")
    src_label.setStyleSheet(FIELD_LABEL_STYLE)
    src_edit = QLineEdit()
    src_edit.setStyleSheet(LINEEDIT_STYLE)
    src_edit.setPlaceholderText("Select source folder...")
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
    src_row.addWidget(src_edit, 1)
    src_row.addWidget(src_btn)
    
    src_layout.addWidget(src_label)
    src_layout.addLayout(src_row)
    paths_layout.addLayout(src_layout)
    
    # Destination
    dst_layout = QVBoxLayout()
    dst_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    dst_label = QLabel("Destination:")
    dst_label.setStyleSheet(FIELD_LABEL_STYLE)
    dst_edit = QLineEdit()
    dst_edit.setStyleSheet(LINEEDIT_STYLE)
    dst_edit.setPlaceholderText("Select destination folder...")
    dst_btn = QPushButton("Browse…")
    dst_btn.setObjectName("dst_browse_btn")
    # Use the standard app colors
    dst_btn.setStyleSheet(f"""
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
    
    dst_row = QHBoxLayout()
    dst_row.setSpacing(2)  # Reduced to 2px for very tight spacing
    dst_row.addWidget(dst_edit, 1)
    dst_row.addWidget(dst_btn)
    
    dst_layout.addWidget(dst_label)
    dst_layout.addLayout(dst_row)
    paths_layout.addLayout(dst_layout)
    
    layout.addLayout(paths_layout)
    
    # Settings (compact)
    settings_layout = QHBoxLayout()
    settings_layout.setSpacing(5)  # Reduced to 5px for tight spacing
    
    # Verification
    verify_layout = QVBoxLayout()
    verify_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    verify_label = QLabel("Verification:")
    verify_label.setStyleSheet(FIELD_LABEL_STYLE)
    verify_combo = QComboBox()
    verify_combo.addItems([
        "None — fastest transfer",
        "xxHash64 — fast verification",
        "Cryptographic (disabled)",
    ])
    verify_combo.setStyleSheet(COMBOBOX_STYLE)
    verify_combo.setCurrentIndex(1)
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(verify_combo)
        print("DEBUG: Applied hover delegate to verify_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to verify_combo: {e}")
    
    verify_layout.addWidget(verify_label)
    verify_layout.addWidget(verify_combo)
    settings_layout.addLayout(verify_layout)
    
    # Link preset
    preset_layout = QVBoxLayout()
    preset_layout.setSpacing(2)  # Reduced to 2px for very tight spacing
    preset_label = QLabel("Link preset:")
    preset_label.setStyleSheet(FIELD_LABEL_STYLE)
    preset_combo = QComboBox()
    preset_combo.addItems(["Auto/Default", "1 GbE", "10 GbE", "25/40 GbE or IB"])
    preset_combo.setStyleSheet(COMBOBOX_STYLE)
    preset_combo.setCurrentIndex(1)
    
    # Apply hover delegate for proper hover effects
    try:
        apply_hover_delegate(preset_combo)
        print("DEBUG: Applied hover delegate to preset_combo")
    except Exception as e:
        print(f"DEBUG: Failed to apply hover delegate to preset_combo: {e}")
    
    preset_layout.addWidget(preset_label)
    preset_layout.addWidget(preset_combo)
    settings_layout.addLayout(preset_layout)
    
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
    
    layout.addWidget(files_frame)
    
    # Apply preset logic
    def apply_preset():
        preset = preset_combo.currentText()
        if "1 GbE" in preset:
            # Optimized for gigabit: more aggressive settings
            conc_slider.setValue(4)  # Increased from 1 to 4 for parallel file processing
            stream_slider.setValue(8)  # Increased from 2 to 8 for multi-stream within files
        elif "10 GbE" in preset:
            conc_slider.setValue(8)
            stream_slider.setValue(16)
        elif "25/40 GbE" in preset:
            conc_slider.setValue(16)
            stream_slider.setValue(32)
        else:  # Auto/Default
            conc_slider.setValue(4)
            stream_slider.setValue(8)
    
    preset_combo.currentTextChanged.connect(apply_preset)
    apply_preset()  # Apply initial preset
    
    # Define event handlers in the outer scope so they can access UI widgets
    def handle_job_started(payload):
        print(f"DEBUG: handle_job_started called with: {payload}")
        try:
            total_bytes = payload.get("total_bytes", 0)
            total_files = payload.get("total_files", 0)
            print(f"DEBUG: Job started with {total_files} files, {total_bytes} total bytes")
            
            # Initialize time tracking
            root.job_start_time = time.time()
            root.elapsed_label.setText("Elapsed: 00:00:00")
            root.eta_label.setText("ETA: --:--:--")
            
            # Initialize progress tracking
            root.total_bytes = total_bytes
            root.copied_bytes = 0
            
            # Reset speed metrics
            if hasattr(root, 'current_speed_label'):
                root.current_speed_label.setText("Speed: 0 MB/s")
            if hasattr(root, 'avg_speed_label'):
                root.avg_speed_label.setText("Avg: 0 MB/s")
            if hasattr(root, 'peak_speed_label'):
                root.peak_speed_label.setText("Peak: 0 MB/s")
            
            # Reset UI state
            print(f"DEBUG: Resetting UI state...")
            root.total_progress.setValue(0)
            root.speed_label.setText("0 MB/s Transfer")
            files_count.setText("0 files")
            root.active_files = 0
            
            # Clear existing file widgets
            print(f"DEBUG: Clearing existing file widgets...")
            for widget in list(root.file_widgets.values()):
                print(f"DEBUG: Removing widget: {widget}")
                files_container_layout.removeWidget(widget)
                widget.deleteLater()
            root.file_widgets.clear()
            print(f"DEBUG: UI reset completed")
            print(f"DEBUG: Files container now has {files_container_layout.count()} widgets")
            print(f"DEBUG: Progress bar value: {root.total_progress.value()}")
            print(f"DEBUG: Progress bar is visible: {root.total_progress.isVisible()}")
            print(f"DEBUG: Progress bar size: {root.total_progress.size()}")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_started: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_job_progress(payload):
        print(f"DEBUG: handle_job_progress called with: {payload}")
        try:
            # Fix field name mismatches between engine and UI
            total = int(payload.get("total_bytes", payload.get("total", 0)))
            done  = int(payload.get("bytes_copied", payload.get("bytes", 0)))
            pct   = 0 if total == 0 else int((done / total) * 100)
            
            # Update progress tracking
            root.copied_bytes = done
            root.total_bytes = total
            
            print(f"DEBUG: Setting total progress to {pct}%")
            
            # Update the progress bar - DO NOT reset to 0%
            print(f"DEBUG: About to set progress bar to {pct}%")
            print(f"DEBUG: Progress bar before update: {root.total_progress.value()}")
            root.total_progress.setValue(pct)
            root.total_progress.setFormat(f"{pct}%")  # Update the text format
            print(f"DEBUG: Progress bar value set to {pct}")
            print(f"DEBUG: Progress bar current value: {root.total_progress.value()}")
            print(f"DEBUG: Progress bar is visible: {root.total_progress.isVisible()}")
            print(f"DEBUG: Progress bar size: {root.total_progress.size()}")
            print(f"DEBUG: Progress bar range: {root.total_progress.minimum()} to {root.total_progress.maximum()}")
            print(f"DEBUG: Progress bar format: {root.total_progress.format()}")
            
            # Update speed label with rolling speed if available
            if "speed_mbps" in payload:
                mbps = payload["speed_mbps"]
                root.speed_label.setText(f"{mbps:.1f} MB/s Transfer")
                print(f"DEBUG: Speed label text set to {mbps:.1f} MB/s Transfer")
            else:
                # Use rolling speed calculation
                root.speed_label.setText(root._rolling_speed_human())
            
            # Update time displays and speed metrics
            if root.job_start_time:
                elapsed_seconds = time.time() - root.job_start_time
                elapsed_str = f"{int(elapsed_seconds//3600):02d}:{int((elapsed_seconds%3600)//60):02d}:{int(elapsed_seconds%60):02d}"
                root.elapsed_label.setText(f"Elapsed: {elapsed_str}")
                
                # Calculate ETA - only if we have speed and remaining bytes
                current_speed = (done / (1024 * 1024)) / elapsed_seconds if elapsed_seconds > 0 else 0
                if current_speed > 0 and done < total:
                    remaining_bytes = total - done
                    eta_seconds = remaining_bytes / (current_speed * 1024 * 1024)
                    if eta_seconds > 0:
                        eta_str = f"{int(eta_seconds//3600):02d}:{int((eta_seconds%3600)//60):02d}:{int(eta_seconds%60):02d}"
                        root.eta_label.setText(f"ETA: {eta_str}")
                    else:
                        root.eta_label.setText("ETA: --:--:--")
                else:
                    root.eta_label.setText("ETA: --:--:--")
                
                # Update speed metrics
                if hasattr(root, 'current_speed_label'):
                    root.current_speed_label.setText(f"Speed: {current_speed:.0f} MB/s")
                
                # Calculate average speed (simple average for now)
                if hasattr(root, 'avg_speed_label'):
                    total_mb = total / (1024 * 1024)
                    avg_speed = total_mb / elapsed_seconds if elapsed_seconds > 0 else 0
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
            
            print(f"DEBUG: Progress and speed updated successfully")
            print(f"DEBUG: total_progress new value: {root.total_progress.value()}")
            print(f"DEBUG: speed_label new text: {root.speed_label.text()}")
            
            # Force a repaint and update
            root.total_progress.repaint()
            root.total_progress.update()
            root.speed_label.repaint()
            root.speed_label.update()
            print(f"DEBUG: Progress widgets repainted and updated")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_job_progress: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_started(payload):
        print(f"DEBUG: handle_file_started called with: {payload}")
        try:
            file_id = payload.get("file_id")
            filename = payload.get("filename")
            total_bytes = payload.get("total_bytes", 0)
            print(f"DEBUG: Creating FileProgressLine for {filename} with {total_bytes} bytes")
            
            # Check if we have the necessary imports
            print(f"DEBUG: FileProgressLine import check...")
            # FileProgressLine is already imported at the top
            print(f"DEBUG: FileProgressLine imported successfully")
            
            widget = FileProgressLine(filename, total_bytes)
            print(f"DEBUG: FileProgressLine widget created: {widget}")
            
            # Store widget reference
            root.file_widgets[file_id] = widget
            print(f"DEBUG: Widget added to root.file_widgets: {file_id}")
            
            # Add widget to layout at the top (newest files appear at top)
            files_container_layout.insertWidget(0, widget)
            print(f"DEBUG: Widget added to layout at position 0")
            
            root.active_files += 1
            files_count.setText(f"{root.active_files} files")
            print(f"DEBUG: Active files count updated: {root.active_files}")
            
            # Store start time in the widget itself for speed calculation
            widget.start_time = time.time()
            print(f"DEBUG: Start time stored in widget")
            
            print(f"DEBUG: File widget added, active files: {root.active_files}")
            print(f"DEBUG: File widgets now: {list(root.file_widgets.keys())}")
            print(f"DEBUG: Widget parent: {widget.parent()}")
            print(f"DEBUG: Widget visible: {widget.isVisible()}")
            print(f"DEBUG: Widget size: {widget.size()}")
            print(f"DEBUG: Container layout count: {files_container_layout.count()}")
            
            # Force widget to be visible
            widget.show()
            widget.raise_()
            # Force a repaint of the container
            files_container.update()
            files_container.repaint()
            print(f"DEBUG: Widget visibility forced and container repainted")
            
        except Exception as e:
            print(f"DEBUG: Error in handle_file_started: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_progress(payload):
        print(f"DEBUG: handle_file_progress called with: {payload}")
        try:
            file_id = payload.get("file_id")
            copied_bytes = payload.get("bytes", 0)
            print(f"DEBUG: Updating progress for file {file_id}: {copied_bytes} bytes")
            print(f"DEBUG: Available file widgets: {list(root.file_widgets.keys())}")
            
            if file_id in root.file_widgets:
                widget = root.file_widgets[file_id]
                print(f"DEBUG: Found widget for {file_id}: {widget}")
                
                # Calculate speed using the widget's start time
                if hasattr(widget, 'start_time'):
                    elapsed = time.time() - widget.start_time
                    if elapsed > 0:
                        speed = (copied_bytes / elapsed) / (1024 * 1024)
                        print(f"DEBUG: Calculating speed: {speed:.1f} MB/s")
                        print(f"DEBUG: Calling update_progress on widget {file_id}")
                        widget.update_progress(copied_bytes, speed)
                        print(f"DEBUG: update_progress completed for {file_id}")
                    else:
                        print(f"DEBUG: No elapsed time, updating progress without speed")
                        print(f"DEBUG: Calling update_progress on widget {file_id}")
                        widget.update_progress(copied_bytes)
                        print(f"DEBUG: update_progress completed for {file_id}")
                else:
                    print(f"DEBUG: No start time, updating progress without speed")
                    print(f"DEBUG: Calling update_progress on widget {file_id}")
                    widget.update_progress(copied_bytes)
                    print(f"DEBUG: update_progress completed for {file_id}")
            else:
                print(f"DEBUG: File widget not found for file_id: {file_id}")
                print(f"DEBUG: Available file widgets: {list(root.file_widgets.keys())}")
                print(f"DEBUG: This suggests handle_file_started was not called or failed")
                
        except Exception as e:
            print(f"DEBUG: Error in handle_file_progress: {e}")
            import traceback
            traceback.print_exc()
            
    def handle_file_completed(payload):
        print(f"DEBUG: handle_file_completed called with: {payload}")
        try:
            file_id = payload.get("file_id")
            filename = payload.get("filename")
            bytes_copied = payload.get("bytes", 0)
            total_bytes = payload.get("total", 0)
            skipped = payload.get("skipped", False)
            print(f"DEBUG: File completed: {filename} ({bytes_copied}/{total_bytes} bytes, skipped: {skipped})")
            
            if file_id in root.file_widgets:
                root.file_widgets[file_id].mark_completed()
                root.active_files -= 1
                files_count.setText(f"{root.active_files} files")
                print(f"DEBUG: File marked as completed, active files: {root.active_files}")
                
                # Remove completed files after a delay
                # Use QTimer.singleShot to ensure this happens on the main thread
                QTimer.singleShot(2000, lambda f=file_id: _remove_file_widget(f))
                print(f"DEBUG: Scheduled removal of file widget {file_id} in 2 seconds")
            else:
                print(f"DEBUG: File widget not found for completed file: {file_id}")
                
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
            bytes_copied = payload.get("bytes", 0)
            total_bytes = payload.get("total", 0)
            elapsed_s = payload.get("elapsed_s", 0)
            mbps = payload.get("mbps", 0)
            print(f"DEBUG: Job completed: {bytes_copied}/{total_bytes} bytes in {elapsed_s:.1f}s at {mbps:.1f} MB/s")
            
            # Stop the timers
            if root.time_update_timer.isActive():
                root.time_update_timer.stop()
                print("DEBUG: Time update timer stopped")
            if root.stats_update_timer.isActive():
                root.stats_update_timer.stop()
                print("DEBUG: Stats update timer stopped")
            
            # Update progress to 100%
            total_progress.setValue(100)
            total_progress.setFormat("100%")  # Update the text format
            print(f"DEBUG: Progress bar set to 100%")
            
            # Show final time statistics
            if root.job_start_time:
                total_elapsed = time.time() - root.job_start_time
                total_elapsed_str = f"{int(total_elapsed//3600):02d}:{int((total_elapsed%3600)//60):02d}:{int(total_elapsed%60):02d}"
                root.elapsed_label.setText(f"Elapsed: {total_elapsed_str}")
                root.eta_label.setText("ETA: Complete")
                root.total_time_label.setText(f"Total: {total_elapsed_str}")
            
            # Re-enable start button and disable pause/cancel
            start_btn.setEnabled(True)
            pause_btn.setEnabled(False)
            cancel_btn.setEnabled(False)
            print("DEBUG: Button states updated")
            
            # Re-enable controls
            conc_slider.setEnabled(True)
            stream_slider.setEnabled(True)
            verify_combo.setEnabled(True)
            preset_combo.setEnabled(True)
            print("DEBUG: Controls re-enabled")
            
            # Clear job reference
            root.current_job = None
            print("DEBUG: Job reference cleared")
            
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
            self._timer.start(50)  # Process events every 50ms
            print(f"DEBUG: QtSink timer started with interval 50ms")
        
        def emit(self, event_type: str, payload: dict) -> None:
            print(f"DEBUG: QtSink received event: {event_type} with payload: {payload}")
            # Add event to pending queue instead of using QTimer.singleShot
            # This avoids issues with cross-thread QTimer calls
            self.pending_events.append((event_type, payload))
            print(f"DEBUG: Event queued, pending events: {len(self.pending_events)}")
        
        def _process_pending_events(self):
            """Process pending events on the main thread"""
            if not self.pending_events:
                return
            
            # Process all pending events
            events_to_process = self.pending_events.copy()
            self.pending_events.clear()
            
            print(f"DEBUG: Processing {len(events_to_process)} pending events")
            
            for event_type, payload in events_to_process:
                try:
                    print(f"DEBUG: Processing event: {event_type}")
                    if event_type == "job.started":
                        print(f"DEBUG: Calling handle_job_started")
                        handle_job_started(payload)
                    elif event_type == "job.progress":
                        print(f"DEBUG: Calling handle_job_progress with payload: {payload}")
                        handle_job_progress(payload)
                    elif event_type == "file.started":
                        print(f"DEBUG: Calling handle_file_started")
                        handle_file_started(payload)
                    elif event_type == "file.progress":
                        print(f"DEBUG: Calling handle_file_progress")
                        handle_file_progress(payload)
                    elif event_type == "file.completed":
                        print(f"DEBUG: Calling handle_file_completed")
                        handle_file_completed(payload)
                    elif event_type == "file.failed":
                        print(f"DEBUG: Calling handle_file_failed")
                        handle_file_failed(payload)
                    elif event_type == "job.completed":
                        print(f"DEBUG: Calling handle_job_completed")
                        handle_job_completed(payload)
                    else:
                        print(f"DEBUG: Unknown event type: {event_type}")
                except Exception as e:
                    print(f"DEBUG: Error processing event {event_type}: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"DEBUG: Finished processing events")
        
        def cleanup(self):
            """Clean up resources when the widget is destroyed"""
            print("DEBUG: QtSink cleanup called")
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
    
    # Create the sink instance and attach it to the root widget
    print("DEBUG: Creating QtSink instance...")
    root.qt_sink = QtSink()
    root.qt_sink.setParent(root)  # Ensure proper parenting for event loop integration
    print(f"DEBUG: QtSink instance created and attached: {root.qt_sink}")
    print(f"DEBUG: QtSink timer active: {root.qt_sink._timer.isActive()}")
    print(f"DEBUG: QtSink parent: {root.qt_sink.parent()}")
    
    # Connect the widget's destroyed signal to the QtSink cleanup
    root.destroyed.connect(root.qt_sink.cleanup)
    print("DEBUG: Connected widget destroyed signal to QtSink cleanup")
    
    # Wire up button handlers
    def on_start():
        if not src_edit.text().strip() or not dst_edit.text().strip():
            print("DEBUG: Source or destination path is empty")
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
            source_path = src_edit.text().strip()
            dest_path = dst_edit.text().strip()
            verification = verify_combo.currentText()
            conc_level = conc_slider.value()
            stream_level = stream_slider.value()
            
            print(f"DEBUG: Source: {source_path}")
            print(f"DEBUG: Destination: {dest_path}")
            print(f"DEBUG: Verification: {verification}")
            print(f"DEBUG: Concurrency: {conc_level}")
            print(f"DEBUG: Streams: {stream_level}")
            
            try:
                # Import the necessary classes for creating a proper job
                print(f"DEBUG: Importing JobSpec and JobOptions...")
                # JobSpec and JobOptions are already imported at the top
                from pathlib import Path
                print(f"DEBUG: JobSpec and JobOptions imported successfully")
                
                # Create a JobSpec with the source and destination
                print(f"DEBUG: Creating JobSpec...")
                job = JobSpec(
                    job_id=job_id,
                    source_root=source_path,
                    destination_root=dest_path,
                    options=JobOptions(
                        mode="BALANCED" if "xxHash64" in verification else "FAST",
                        per_file_concurrency=conc_level,
                        stream_concurrency=stream_level
                    )
                )
                
                print(f"DEBUG: Created JobSpec: {job}")
                
                # Use the locally created QtSink
                sink = root.qt_sink
                print(f"DEBUG: Using QtSink: {sink}")
                
                # Create and start the engine
                print(f"DEBUG: Importing PythonCopyEngine...")
                # PythonCopyEngine is already imported at the top
                print(f"DEBUG: PythonCopyEngine imported successfully")
                
                print(f"DEBUG: Creating PythonCopyEngine instance...")
                engine = PythonCopyEngine(sink=sink)
                print(f"DEBUG: PythonCopyEngine created: {engine}")
                
                # Store the engine reference (not the thread)
                root.current_job = engine
                print(f"DEBUG: Engine stored in root.current_job")
                
                # Freeze controls during copy
                conc_slider.setEnabled(False)
                stream_slider.setEnabled(False)
                verify_combo.setEnabled(False)
                preset_combo.setEnabled(False)
                print(f"DEBUG: Controls frozen")
                
                print(f"DEBUG: Starting engine with job: {job}")
                engine.start(job)
                print(f"DEBUG: Engine completed")
                
            except Exception as e:
                print(f"DEBUG: Error starting engine: {e}")
                import traceback
                traceback.print_exc()
                # Re-enable controls on error
                conc_slider.setEnabled(True)
                stream_slider.setEnabled(True)
                verify_combo.setEnabled(True)
                preset_combo.setEnabled(True)
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                print(f"DEBUG: Controls re-enabled after error")

        # Start in background thread
        job_thread = threading.Thread(target=run, daemon=True)
        job_thread.start()
        # Don't store the thread in current_job - store the engine instead
    
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
                
                # Update button states
                start_btn.setEnabled(True)
                pause_btn.setEnabled(False)
                cancel_btn.setEnabled(False)
                print("DEBUG: Button states updated for cancel")
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
        
        start_btn.setEnabled(True)
        pause_btn.setEnabled(False)
        cancel_btn.setEnabled(False)
        print("DEBUG: Button states updated")
    
    # Wire up browse buttons
    def _browse_for_path(line_edit: QLineEdit):
        path = QFileDialog.getExistingDirectory(
            root,
            "Select Source Folder",
            line_edit.text(),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if path:
            line_edit.setText(path)
            print(f"DEBUG: Source path selected: {path}")
            
            # Enable start button if both paths are selected
            if src_edit.text().strip() and dst_edit.text().strip():
                start_btn.setEnabled(True)
                print("DEBUG: Both paths selected, enabling start button")
    
    # Function to check if buttons should be enabled
    def check_button_states():
        if src_edit.text().strip() and dst_edit.text().strip():
            start_btn.setEnabled(True)
            print("DEBUG: Both paths selected, enabling start button")
        else:
            start_btn.setEnabled(False)
            print("DEBUG: Paths not complete, disabling start button")
    
    # Connect text changed signals to check button states
    src_edit.textChanged.connect(check_button_states)
    dst_edit.textChanged.connect(check_button_states)
    
    # Connect button handlers
    start_btn.clicked.connect(on_start)
    pause_btn.clicked.connect(on_pause)
    cancel_btn.clicked.connect(on_cancel)
    print("DEBUG: Button handlers connected")
    
    src_btn.clicked.connect(lambda: _browse_for_path(src_edit))
    dst_btn.clicked.connect(lambda: _browse_for_path(dst_edit))
    print("DEBUG: Browse button handlers connected")
    
    # Initial button state check
    check_button_states()
    
    return root


