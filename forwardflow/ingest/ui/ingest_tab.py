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
    # Remove tab pane padding (Templates has no padding)
    root.setStyleSheet("""
        QWidget#ingest_tab {
            margin: 0px;
            padding: 0px;
        }
    """)
    
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
    
    # Main layout - two-column design (ZERO padding like templates tab)
    layout = QVBoxLayout(root)
    layout.setContentsMargins(0, 0, 0, 0)  # NO padding - match templates
    layout.setSpacing(0)

    # Set minimum dimensions to prevent UI collapse and ensure full visibility
    root.setMinimumWidth(1100)  # Wider for two-column layout
    root.setMinimumHeight(700)

    print("DEBUG: Creating IngestViewModel...")
    vm = IngestViewModel()
    print("DEBUG: IngestViewModel created successfully")

    # Make vm accessible to the widget
    root.vm = vm
    print("DEBUG: VM attached to root widget")

    # DISABLED: Timers cause GIL deadlock with Rust worker thread
    # Use event-driven updates from event pump instead
    # root.time_update_timer = QTimer()
    # root.time_update_timer.timeout.connect(lambda: update_elapsed_time())
    # root.time_update_timer.start(1000)  # Update every second

    # DISABLED: Timers cause GIL deadlock with Rust worker thread
    # Use event-driven updates from event pump instead
    # root.stats_update_timer = QTimer()
    # root.stats_update_timer.timeout.connect(lambda: update_stats())
    # root.stats_update_timer.start(100)  # Update every 100ms for real-time responsiveness

    def update_elapsed_time():
        """Update elapsed time display every second"""
        if root.job_start_time and root.current_job:
            elapsed_seconds = time.time() - root.job_start_time
            elapsed_str = f"{int(elapsed_seconds//3600):02d}:{int((elapsed_seconds%3600)//60):02d}:{int(elapsed_seconds%60):02d}"
            if hasattr(root, 'elapsed_label') and root.elapsed_label:
                root.elapsed_label.setText(elapsed_str)

    def update_stats():
        """Update ONLY elapsed time - all other stats are handled by event system"""
        # CRITICAL FIX: Remove all speed/progress updates from timer to prevent conflicts
        # Only update elapsed time which doesn't conflict with event-driven updates
        pass  # All stats now handled by event system

    # Title row - left side "Turbo Transfer", right side stays empty for now
    title_row = QHBoxLayout()
    title_row.setSpacing(0)
    title_row.setContentsMargins(5, 5, 5, 5)

    title = QLabel("Turbo Transfer")
    title.setStyleSheet(HEADER_LABEL_STYLE)
    title.setMinimumHeight(32)
    title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    title_row.addWidget(title, 30)  # Left side 30%
    title_row.addStretch(70)  # Right side 70% (destinations will align here)

    layout.addLayout(title_row)

    # Create the refactored components
    print("DEBUG: Creating SourceDestinationSection...")
    source_dest_section = SourceDestinationSection(root, recent_sources, recent_destinations)

    print("DEBUG: Creating OptionsSection...")
    options_section = OptionsSection(root)

    print("DEBUG: Creating ControlSection...")
    control_section = ControlSection(root)

    print("DEBUG: Creating ProgressSection...")
    progress_section = ProgressSection(root)

    # Two-column layout: Left (settings + progress), Right (destinations ONLY)
    main_content = QHBoxLayout()
    main_content.setSpacing(0)
    main_content.setContentsMargins(5, 0, 5, 5)  # Minimal margins like Templates

    # LEFT COLUMN: Source, Settings, Controls, and Progress
    left_column = QVBoxLayout()
    left_column.setSpacing(8)
    left_column.setContentsMargins(0, 0, 6, 0)  # Small right margin for gap

    # Source selection (left column)
    left_column.addWidget(source_dest_section.get_source_widget())

    # Settings (left column)
    left_column.addWidget(options_section)

    # Controls (left column)
    left_column.addWidget(control_section)

    # Progress section (left column) - moved from bottom
    left_column.addWidget(progress_section)

    # Add stretch to push everything to top
    left_column.addStretch()

    # RIGHT COLUMN: Destinations ONLY (full height)
    right_column = QVBoxLayout()
    right_column.setSpacing(0)
    right_column.setContentsMargins(0, 0, 0, 0)

    # Destinations (right column - takes full right side)
    right_column.addWidget(source_dest_section.get_destinations_widget(), 1)  # Stretch to fill

    # Add columns to main content (30% left for controls+progress, 70% right for destinations)
    main_content.addLayout(left_column, 30)
    main_content.addLayout(right_column, 70)

    layout.addLayout(main_content, 1)  # Main content gets all space
    
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
            # DISABLED: Timer causes GIL deadlock with Rust worker thread
            # Event pump handles all event processing now
            # self._timer = QTimer()
            # self._timer.timeout.connect(self._process_pending_events)
            # self._timer.start(100)  # Process events every 100ms to prevent UI flooding
            # print(f"DEBUG: QtSink timer started with interval 100ms")
            self._lock = threading.Lock()  # Add thread safety
            self._widgets_valid = True  # Track if widgets are still valid
            self._processing = False  # Prevent re-entrant processing
            self._event_count = 0  # Track total events received
            
            # Event throttling to prevent UI freezing
            self._last_progress_update = 0
            self._progress_throttle_ms = 100  # Update progress max every 100ms
            self._last_file_update = 0
            self._file_throttle_ms = 500  # Update file progress max every 500ms
            self._last_dest_update = 0
            self._dest_throttle_ms = 200  # Update destination progress max every 200ms
        
        def emit(self, event_type: str, payload: dict) -> None:
            """Emit an event to be processed on the main thread"""
            if not self._widgets_valid:
                print(f"DEBUG: QtSink ignoring event {event_type} - widgets no longer valid")
                return
            
            # Check if event should be throttled to prevent UI freezing
            if self._should_throttle_event(event_type):
                return
                
            self._event_count += 1
            print(f"DEBUG: QtSink received event #{self._event_count}: {event_type} with payload: {payload}")
            
            # Add thread safety
            with self._lock:
                # Add event to pending queue instead of using QTimer.singleShot
                # This avoids issues with cross-thread QTimer calls
                self.pending_events.append((event_type, payload))
                print(f"DEBUG: Event queued, pending events: {len(self.pending_events)}")
        
        def _should_throttle_event(self, event_type: str) -> bool:
            """Check if event should be throttled to prevent UI freezing"""
            current_time = time.time() * 1000  # Convert to milliseconds
            
            if event_type == "job.progress":
                if current_time - self._last_progress_update < self._progress_throttle_ms:
                    return True
                self._last_progress_update = current_time
                return False
                
            elif event_type == "file.progress":
                if current_time - self._last_file_update < self._file_throttle_ms:
                    return True
                self._last_file_update = current_time
                return False
                
            elif event_type == "dest.progress":
                if current_time - self._last_dest_update < self._dest_throttle_ms:
                    return True
                self._last_dest_update = current_time
                return False
                
            # Never throttle important events
            return False
        
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
                    
                    # Process only a limited number of events per cycle to prevent UI blocking
                    max_events_per_cycle = 10  # Limit to prevent UI freezing
                    events_to_process = self.pending_events[:max_events_per_cycle]
                    self.pending_events = self.pending_events[max_events_per_cycle:]
                
                print(f"DEBUG: Processing {len(events_to_process)} pending events (max {max_events_per_cycle} per cycle)")
                
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
                            # CRITICAL FIX: Use single progress update path to prevent blinking
                            progress_section.handle_progress_update(payload)
                        elif event_type == "dest.progress":
                            source_dest_section.handle_destination_progress(payload)
                        elif event_type == "current.file":
                            progress_section.handle_current_file(payload)
                        elif event_type == "file.started":
                            progress_section.handle_file_started(payload)
                        elif event_type == "file.progress":
                            progress_section.handle_file_progress(payload)
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





