"""
GIL-Free Event Pump for Rust → Python → Qt Communication

This module provides a dedicated background thread that polls the Rust event queue
and emits Qt signals WITHOUT blocking the main thread or file copy operations.

Architecture:
    Rust Copy Thread → Lock-Free Queue → Event Pump Thread → Qt Main Thread
                        (NO GIL)            (50ms polling)     (UI updates)

This completely eliminates GIL deadlock during file transfers.
"""

import json
import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QThread


class EventPumpThread(QThread):
    """Background thread that polls Rust event queue and emits Qt signals"""

    # Signals for different event types
    job_started = pyqtSignal(dict)
    job_progress = pyqtSignal(dict)
    file_started = pyqtSignal(dict)
    file_progress = pyqtSignal(dict)
    file_completed = pyqtSignal(dict)
    dest_progress = pyqtSignal(dict)
    dest_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(dict)

    def __init__(self, queue_handle):
        """
        Initialize event pump thread

        Args:
            queue_handle: PyEventQueueHandle from Rust engine
        """
        super().__init__()
        self.queue_handle = queue_handle
        self._running = False
        self._poll_interval_ms = 50  # 50ms = 20 updates/second (smooth for UI)

        print("DEBUG: EventPumpThread initialized with queue handle")

    def run(self):
        """Main event pump loop - runs on background thread"""
        self._running = True
        print("DEBUG: EventPumpThread started - polling every 50ms")

        event_count = 0

        while self._running:
            try:
                # Drain all pending events from queue (non-blocking)
                events_json = self.queue_handle.drain_all_events()

                if events_json:
                    event_count += len(events_json)
                    if event_count % 20 == 0:
                        print(f"DEBUG: EventPump processed {event_count} total events")

                # Process each event and emit appropriate signal
                for event_json in events_json:
                    try:
                        event = json.loads(event_json)
                        self._route_event(event)
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: Failed to parse event JSON: {e}")

                # Sleep to avoid CPU spinning (50ms = 20 updates/second)
                time.sleep(self._poll_interval_ms / 1000.0)

            except Exception as e:
                print(f"DEBUG: Error in event pump loop: {e}")
                import traceback
                traceback.print_exc()

        print(f"DEBUG: EventPumpThread stopped - processed {event_count} total events")

    def _route_event(self, event: dict):
        """Route event to appropriate Qt signal based on type"""
        # Event format from Rust: {"EventType": {fields...}}
        # Example: {"JobStarted": {"job_id": "abc", ...}}

        if not event:
            return

        # Get event type (first key in dict)
        event_type = list(event.keys())[0]
        payload = event[event_type]

        # Route to appropriate signal
        if event_type == "JobStarted":
            self.job_started.emit(payload)
        elif event_type == "JobProgress":
            self.job_progress.emit(payload)
        elif event_type == "FileStarted":
            self.file_started.emit(payload)
        elif event_type == "FileProgress":
            self.file_progress.emit(payload)
        elif event_type == "FileCompleted":
            self.file_completed.emit(payload)
        elif event_type == "DestProgress":
            self.dest_progress.emit(payload)
        elif event_type == "DestCompleted":
            self.dest_completed.emit(payload)
        elif event_type == "Error":
            self.error_occurred.emit(payload)
        else:
            print(f"DEBUG: Unknown event type: {event_type}")

    def stop(self):
        """Stop the event pump thread gracefully"""
        print("DEBUG: Stopping EventPumpThread...")
        self._running = False
        self.wait()  # Wait for thread to finish
        print("DEBUG: EventPumpThread stopped")


class EventPumpManager(QObject):
    """Manages event pump thread lifecycle and provides signal forwarding"""

    # Forward signals from pump thread to UI
    progress_update = pyqtSignal(dict)
    destination_update = pyqtSignal(dict)
    destination_completed = pyqtSignal(str)
    file_completed = pyqtSignal(dict)  # CRITICAL FIX: Forward file completion events for DIT collector

    def __init__(self):
        super().__init__()
        self.pump_thread: Optional[EventPumpThread] = None
        self._queue_handle = None
        print("DEBUG: EventPumpManager initialized")

    def start_pump(self, queue_handle):
        """
        Start event pump thread with Rust queue handle

        Args:
            queue_handle: PyEventQueueHandle from Rust engine
        """
        if self.pump_thread and self.pump_thread.isRunning():
            print("DEBUG: Event pump already running - stopping first")
            self.stop_pump()

        print("DEBUG: Starting event pump thread...")
        self._queue_handle = queue_handle
        self.pump_thread = EventPumpThread(queue_handle)

        # Connect pump thread signals to our forwarding signals
        self.pump_thread.job_progress.connect(self._handle_job_progress)
        self.pump_thread.file_completed.connect(self._handle_file_completed)  # For DIT data collection
        self.pump_thread.file_completed.connect(self.file_completed.emit)  # CRITICAL FIX: Forward raw file_completed events
        self.pump_thread.dest_progress.connect(self._handle_dest_progress)
        self.pump_thread.dest_completed.connect(self._handle_dest_completed)

        # Start the pump thread
        self.pump_thread.start()
        print("DEBUG: Event pump thread started successfully")

    def stop_pump(self):
        """Stop event pump thread gracefully"""
        if self.pump_thread and self.pump_thread.isRunning():
            print("DEBUG: Stopping event pump thread...")
            self.pump_thread.stop()
            self.pump_thread = None
            print("DEBUG: Event pump thread stopped")

    def _handle_job_progress(self, payload: dict):
        """Handle job progress events and emit as progress_update"""
        # Convert to format expected by existing UI code
        bytes_copied = payload.get('bytes_copied', 0)
        total_bytes = payload.get('total_bytes', 0)

        # CRITICAL FIX: Calculate progress percentage for main progress bar
        progress_percent = 0.0
        if total_bytes > 0:
            progress_percent = (bytes_copied / total_bytes) * 100.0

        update = {
            'bytes_copied': bytes_copied,
            'total_bytes': total_bytes,
            'progress_percent': progress_percent,  # CRITICAL FIX: Add percentage for progress bar
            'files_completed': payload.get('files_completed', 0),
            'total_files': payload.get('total_files', 0),
            'elapsed_s': payload.get('elapsed_s', 0),
            'speed_mbps': payload.get('speed_mbps', 0),
            'current_speed_mbps': payload.get('current_speed_mbps', 0),
            'peak_speed_mbps': payload.get('peak_speed_mbps', 0),
        }
        self.progress_update.emit(update)

    def _handle_file_completed(self, payload: dict):
        """Handle file completed events for DIT data collection"""
        # Forward to DIT collector (matches existing event format)
        from ..utils.dit_data_collector import get_dit_collector
        dit_collector = get_dit_collector()

        # CRITICAL FIX: Convert Rust event format to DIT collector format
        bytes_copied = payload.get('bytes_copied', 0)
        event_data = {
            'filename': payload.get('filename', ''),
            'source_path': payload.get('source_path', ''),
            'dest_path': payload.get('dest_path', ''),
            'destination_path': payload.get('dest_path', ''),  # DIT collector expects this
            'bytes_copied': bytes_copied,
            'size_bytes': bytes_copied,  # CRITICAL FIX: DIT collector expects 'size_bytes'
            'source_checksum': payload.get('source_checksum', ''),
            'destination_checksum': payload.get('dest_checksum', ''),
            'hash_algorithm': 'xxhash64be',  # Default algorithm
            'verification_passed': payload.get('verification_passed', False),
            'status': 'COMPLETED',
            'transfer_status': 'COMPLETED',
        }

        print(f"DEBUG: EventPump forwarding file.completed to DIT collector: {event_data.get('filename')} ({bytes_copied} bytes)")
        dit_collector.handle_file_complete_event(event_data)

    def _handle_dest_progress(self, payload: dict):
        """Handle destination progress events"""
        self.destination_update.emit(payload)

    def _handle_dest_completed(self, payload: dict):
        """Handle destination completed events"""
        dest_path = payload.get('dest_path', '')
        if dest_path:
            self.destination_completed.emit(dest_path)
            print(f"DEBUG: Destination completed signal emitted for: {dest_path}")
