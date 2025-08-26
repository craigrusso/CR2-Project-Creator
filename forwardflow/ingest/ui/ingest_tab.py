"""PyQt6 Ingest tab builder for Phase 1.

Lightweight UI built using refactored components to keep ingest self-contained. 
The host app calls `build_ingest_tab()` under a feature flag to add the tab.
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
import collections

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

from forwardflow.ingest.runtime.crash_first_aid import enable as _crash_enable
_crash_enable()
from forwardflow.ingest.ui.qt_safe_bridge import get_bridge, emit_event, cleanup_bridge
from PyQt6 import QtCore, QtWidgets
from ..api.models import JobSpec, JobOptions

# Import the refactored components
from .components import (
    SourceDestinationSection,
    OptionsSection,
    ProgressSection,
    ControlSection
)

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
    """Build the ingest tab UI using refactored components."""
    print("DEBUG: Building ingest tab with refactored components...")
    
    # Create the main widget
    root = QWidget()
    root.setObjectName("ingest_tab")
    
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
            if hasattr(root, 'elapsed_label') and root.elapsed_label:
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
                    total_mb = root.total_bytes / (1024 * 1024)
                    avg_speed = total_mb / elapsed_seconds
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
    

    
    # Create the refactored components
    print("DEBUG: Creating SourceDestinationSection...")
    source_dest_section = SourceDestinationSection(root, recent_sources, recent_destinations)
    layout.addWidget(source_dest_section, 1)  # Add stretch - allow expansion for destinations
    
    print("DEBUG: Creating OptionsSection...")
    options_section = OptionsSection(root)
    layout.addWidget(options_section, 0)  # No stretch - keep fixed size
    
    print("DEBUG: Creating ControlSection...")
    control_section = ControlSection(root)
    layout.addWidget(control_section, 0)  # No stretch - keep fixed size
    
    print("DEBUG: Creating ProgressSection...")
    progress_section = ProgressSection(root)
    layout.addWidget(progress_section, 0)  # No stretch - keep fixed size
    
    # Store references to components for access from event handlers
    root.source_dest_section = source_dest_section
    root.options_section = options_section
    root.control_section = control_section
    root.progress_section = progress_section
    
    # Create the QtSink class for event processing
    class QtSink(QObject):
        def __init__(self):
            super().__init__()
            print("DEBUG: QtSink.__init__ called")
            self.pending_events = []
            self._timer = QTimer()
            self._timer.timeout.connect(self._process_pending_events)
            self._timer.start(50)  # Process events every 50ms for real-time responsiveness
            print(f"DEBUG: QtSink timer started with interval 50ms")
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
                        
                        # Check if widgets are still valid before processing
                        if not self._widgets_valid:
                            print(f"DEBUG: Skipping event {event_type} - widgets no longer valid")
                            continue
                        
                        # Delegate event handling to the appropriate component
                        if event_type == "job.started":
                            progress_section.handle_job_started(payload)
                        elif event_type == "job.progress":
                            progress_section.handle_job_progress(payload)
                        elif event_type == "current.file":
                            progress_section.handle_current_file(payload)
                        elif event_type == "file.completed":
                            progress_section.handle_file_completed(payload)
                        elif event_type == "file.failed":
                            progress_section.handle_file_failed(payload)
                        elif event_type == "job.completed":
                            progress_section.handle_job_completed(payload)
                        elif event_type == "job.cancelled":
                            progress_section.handle_job_cancelled(payload)
                        else:
                            print(f"DEBUG: Unknown event type: {event_type}")
                    except Exception as e:
                        print(f"DEBUG: Error processing event {event_type}: {e}")
                        import traceback
                        traceback.print_exc()
                
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
    bridge.sigJobCancelled.connect(lambda p: qt_sink.emit("job.cancelled", p), QtCore.Qt.ConnectionType.QueuedConnection)
    
    # Wire up the control section button handlers
    control_section.setup_button_handlers(root, source_dest_section, options_section, progress_section)
    
    print("DEBUG: Ingest tab built successfully with refactored components")
    return root





