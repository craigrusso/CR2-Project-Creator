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
import os
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
                        # DEBUG: Log EVERY event type we receive
                        event_type = list(event.keys())[0] if event else "UNKNOWN"
                        if event_type == "FileCompleted":
                            print(f"🚨🚨🚨 EVENT PUMP: FileCompleted DETECTED in queue! Event: {event}")
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
            print(f"🔔🔔🔔 EVENT_PUMP THREAD: FileCompleted event detected - filename={payload.get('filename', 'unknown')}")
            print(f"🔔🔔🔔 EVENT_PUMP THREAD: About to emit file_completed signal with payload: {payload}")
            self.file_completed.emit(payload)
            print(f"🔔🔔🔔 EVENT_PUMP THREAD: file_completed signal EMITTED successfully")
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
        self._peak_speed_mbps = 0.0  # Track global peak speed for DIT reports
        self._job_total_bytes: float = 0.0  # Track combined bytes across all destinations
        self._job_total_files: float = 0.0  # Track combined file count from engine
        self._destination_count: int = 0  # Track how many destinations are actively receiving data
        self._dataset_total_bytes: float = 0.0  # Expected bytes per destination
        self._destination_roots: list[str] = []
        self._last_event_timestamp: float = time.time()  # Track last processed event for idle detection

        # CRITICAL FIX: Per-destination statistics tracking
        # This allows TRUE independent destination speeds by calculating from file.completed events
        self._dest_stats = {}  # dest_index -> {dest_path, total_bytes, total_files, speeds, times, etc.}
        self._dest_stats_lock = threading.Lock()

        print("DEBUG: EventPumpManager initialized with per-destination stat tracking")

    def start_pump(self, queue_handle):
        """
        Start event pump thread with Rust queue handle

        Args:
            queue_handle: PyEventQueueHandle from Rust engine
        """
        if self.pump_thread and self.pump_thread.isRunning():
            print("DEBUG: Event pump already running - stopping first")
            self.stop_pump()

        # Reset peak speed tracking for new job
        self._peak_speed_mbps = 0.0
        self._job_total_bytes = 0.0
        self._job_total_files = 0.0
        self._dataset_total_bytes = 0.0
        self._destination_count = 0
        self._destination_roots = []
        self._last_event_timestamp = time.time()
        
        # Reset per-destination stats for new job
        with self._dest_stats_lock:
            self._dest_stats = {}

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
        self._mark_activity()

        # Convert to format expected by existing UI code
        bytes_copied = payload.get('bytes_copied', 0)
        total_bytes = payload.get('total_bytes', 0)

        if total_bytes:
            self._job_total_bytes = float(total_bytes)
            self._recalculate_dataset_total()

        total_files = payload.get('total_files', 0)
        if total_files:
            self._job_total_files = float(total_files)

        # CRITICAL FIX: Calculate progress percentage for main progress bar
        progress_percent = 0.0
        if total_bytes > 0:
            progress_percent = (bytes_copied / total_bytes) * 100.0

        # Track peak speed for DIT reports
        current_speed = payload.get('speed_mbps', 0)
        if current_speed > self._peak_speed_mbps:
            self._peak_speed_mbps = current_speed
            # Update DIT collector with new peak speed
            from ..utils.dit_data_collector import get_dit_collector
            dit_collector = get_dit_collector()
            dit_collector.update_job_stats({'peak_speed': self._peak_speed_mbps})

        update = {
            'bytes_copied': bytes_copied,
            'total_bytes': total_bytes,
            'progress_percent': progress_percent,  # CRITICAL FIX: Add percentage for progress bar
            'files_completed': payload.get('files_completed', 0),
            'total_files': payload.get('total_files', 0),
            'elapsed_s': payload.get('elapsed_s', 0),
            'speed_mbps': current_speed,
            'current_speed_mbps': payload.get('current_speed_mbps', 0),
            'peak_speed_mbps': self._peak_speed_mbps,
        }
        self._apply_destination_progress_override(update)
        self.progress_update.emit(update)

    def _handle_file_completed(self, payload: dict):
        """Handle file completed events for DIT data collection AND per-destination speed tracking"""
        print(f"🔍🔍🔍 EVENT_PUMP MANAGER: _handle_file_completed() called with payload: {payload}")
        self._mark_activity()

        # CRITICAL FIX: Update per-destination speed tracking from file completion
        # This gives us TRUE independent destination speeds, not producer speeds
        self._update_destination_speed(payload)

        # Forward to DIT collector (matches existing event format)
        from ..utils.dit_data_collector import get_dit_collector
        dit_collector = get_dit_collector()
        print(f"🔍🔍🔍 EVENT_PUMP MANAGER: Got DIT collector: {dit_collector}")

        # CRITICAL FIX: Convert Rust event format to DIT collector format
        bytes_copied = payload.get('bytes_copied', payload.get('size_bytes', 0))

        # Extract hash data - Rust sends these fields from emit_file_completed_with_hash
        source_checksum = payload.get('source_checksum', '')
        dest_checksum = payload.get('dest_checksum', payload.get('destination_checksum', ''))
        hash_algorithm = payload.get('hash_algorithm', 'unknown')

        # Log hash presence for debugging
        has_hash = bool(source_checksum)
        print(f"🔍 EventPump: FileCompleted event - file={payload.get('filename', 'unknown')} hash={source_checksum[:16] if has_hash else 'NONE'}... algo={hash_algorithm}")

        event_data = {
            'filename': payload.get('filename', ''),
            'source_path': payload.get('source_path', ''),
            'dest_path': payload.get('dest_path', ''),
            'destination_path': payload.get('dest_path', ''),  # DIT collector expects this alias
            'dest_index': payload.get('dest_index', 0),
            'bytes_copied': bytes_copied,
            'size_bytes': bytes_copied,  # DIT collector aggregates using this field
            'source_checksum': source_checksum,
            'destination_checksum': dest_checksum,
            'hash_algorithm': hash_algorithm,
            'verification_passed': payload.get('verification_passed', False),
            'status': payload.get('status', 'COMPLETED'),
            'transfer_status': payload.get('status', 'COMPLETED'),
        }

        print(f"🔍🔍🔍 EVENT_PUMP MANAGER: About to forward to DIT collector: {event_data.get('filename')}")
        dit_collector.handle_file_complete_event(event_data)
        print(f"🔍🔍🔍 EVENT_PUMP MANAGER: DIT collector called successfully")

    def _update_destination_speed(self, file_payload: dict):
        """
        Calculate per-destination speed from file completion events.
        This gives us TRUE independent destination speeds, not producer speeds.
        
        Each destination finishes files at its own rate. By tracking when each file
        completes per destination, we get accurate independent transfer speeds.
        """
        dest_index = file_payload.get('dest_index', 0)
        file_dest_path = file_payload.get('dest_path', '')
        dest_root = ''
        if 0 <= dest_index < len(self._destination_roots):
            dest_root = self._destination_roots[dest_index]
        elif self._destination_roots:
            for root in self._destination_roots:
                if file_dest_path.startswith(root):
                    dest_root = root
                    break
        if not dest_root:
            dest_root = file_dest_path
        else:
            try:
                dest_root = os.path.normpath(dest_root)
            except Exception:
                pass
        bytes_copied = file_payload.get('bytes_copied', 0)
        current_time = time.time()
        self._mark_activity()
        
        with self._dest_stats_lock:
            # Initialize destination stats if first time
            if dest_index not in self._dest_stats:
                self._dest_stats[dest_index] = {
                    'dest_root': dest_root,
                    'last_file_path': file_dest_path,
                    'total_bytes': 0,
                    'total_files': 0,
                    'expected_total_bytes': self._job_total_bytes,
                    'last_update_time': current_time,
                    'last_bytes': 0,
                    'current_speed_mbps': 0.0,
                    'peak_speed_mbps': 0.0,
                    'start_time': current_time,
                    'window_start_time': current_time,  # For moving average
                    'window_start_bytes': 0,  # For moving average
                    'completed_emitted': False,
                }
                print(f"🔥🔥🔥 DEST_STATS: Initialized stats for dest_index={dest_index}, path={dest_root}")
            
            self._destination_count = max(self._destination_count, len(self._dest_stats))
            self._recalculate_dataset_total()
            
            stats = self._dest_stats[dest_index]
            stats['last_file_path'] = file_dest_path
            if self._dataset_total_bytes > 0:
                stats['expected_total_bytes'] = self._dataset_total_bytes
            
            # Update totals
            stats['total_bytes'] += bytes_copied
            stats['total_files'] += 1
            
            # Calculate instantaneous speed (MB/s)
            time_since_last = current_time - stats['last_update_time']
            if time_since_last > 0:
                bytes_since_last = stats['total_bytes'] - stats['last_bytes']
                instantaneous_speed_mbps = (bytes_since_last / time_since_last) / (1024 * 1024)
                
                # Update current speed with smoothing (exponential moving average)
                alpha = 0.3  # Smoothing factor
                stats['current_speed_mbps'] = (alpha * instantaneous_speed_mbps + 
                                               (1 - alpha) * stats['current_speed_mbps'])
            
            # Calculate average speed from window (last 2 seconds)
            window_duration = current_time - stats['window_start_time']
            if window_duration >= 2.0:  # Reset window every 2 seconds
                window_bytes = stats['total_bytes'] - stats['window_start_bytes']
                if window_duration > 0:
                    stats['current_speed_mbps'] = (window_bytes / window_duration) / (1024 * 1024)
                stats['window_start_time'] = current_time
                stats['window_start_bytes'] = stats['total_bytes']
            
            # Update peak speed
            if stats['current_speed_mbps'] > stats['peak_speed_mbps']:
                stats['peak_speed_mbps'] = stats['current_speed_mbps']
            
            # Update last values
            stats['last_update_time'] = current_time
            stats['last_bytes'] = stats['total_bytes']
            
            # Calculate ETA (simplified)
            expected_total_bytes = stats.get('expected_total_bytes', 0.0) or self._dataset_total_bytes
            if not expected_total_bytes and self._dataset_total_bytes > 0:
                expected_total_bytes = self._dataset_total_bytes
                stats['expected_total_bytes'] = expected_total_bytes

            tolerance_bytes = max(1_048_576, expected_total_bytes * 0.002) if expected_total_bytes else 1_048_576
            eta_seconds = 0.0
            progress_percent = 0.0

            if expected_total_bytes > 0:
                remaining_bytes = max(expected_total_bytes - stats['total_bytes'], 0.0)
                progress_percent = min(
                    100.0, (stats['total_bytes'] / expected_total_bytes) * 100.0
                )
                if stats['current_speed_mbps'] > 0.01 and remaining_bytes > 0:
                    remaining_mb = remaining_bytes / (1024 * 1024)
                    eta_seconds = remaining_mb / stats['current_speed_mbps']
                if remaining_bytes <= tolerance_bytes:
                    progress_percent = 100.0
                    eta_seconds = 0.0

            elapsed_seconds = max(0.0, current_time - stats['start_time'])
            
            # Persist computed values so global progress overrides can use them
            stats['progress_percent'] = progress_percent
            stats['eta_seconds'] = eta_seconds
            
            print(
                f"🔥🔥🔥 DEST_STATS: dest_index={dest_index}, root={dest_root}, files={stats['total_files']}, "
                f"bytes={stats['total_bytes']}, speed={stats['current_speed_mbps']:.1f} MB/s, "
                f"peak={stats['peak_speed_mbps']:.1f} MB/s"
            )
            
            # Emit destination progress event to UI
            dest_progress_payload = {
                'dest_index': dest_index,
                'dest_path': dest_root,
                'current_file_path': file_dest_path,
                'bytes_copied': stats['total_bytes'],
                'total_bytes': expected_total_bytes,
                'expected_total_bytes': expected_total_bytes,
                'completed_files': stats['total_files'],
                'current_speed_mbps': stats['current_speed_mbps'],
                'currentSpeedMiBps': stats['current_speed_mbps'],  # Alias for UI compatibility
                'peak_speed_mbps': stats['peak_speed_mbps'],
                'peakSpeedMiBps': stats['peak_speed_mbps'],  # Alias for UI compatibility
                'eta_seconds': eta_seconds,
                'etaS': eta_seconds,  # Alias for UI compatibility
                'elapsed_seconds': elapsed_seconds,
                'elapsed_time': elapsed_seconds,
                'progress_percent': progress_percent,
            }
            
            print(f"🔥🔥🔥 DEST_STATS: Emitting destination_update for dest_index={dest_index}")
            self.destination_update.emit(dest_progress_payload)
            
            # CRITICAL FIX: Update DIT collector with per-destination statistics
            from ..utils.dit_data_collector import get_dit_collector
            dit_collector = get_dit_collector()
            dit_collector.update_destination_stats(
                dest_index,
                dest_root,
                {
                    'peak_speed': stats['peak_speed_mbps'],
                    'current_speed': stats['current_speed_mbps'],
                    'total_bytes': stats['total_bytes'],
                    'total_files': stats['total_files'],
                    'progress_percent': progress_percent,
                },
            )

    def _handle_dest_progress(self, payload: dict):
        """Handle destination progress events and track peak speed"""
        self._mark_activity()
        # Track peak speed from destination progress for DIT reports
        dest_peak_speed = payload.get('peak_speed_mib_s', 0) or payload.get('peak_speed_mbps', 0)
        if dest_peak_speed > self._peak_speed_mbps:
            self._peak_speed_mbps = dest_peak_speed
            # Update DIT collector with new peak speed
            from ..utils.dit_data_collector import get_dit_collector
            dit_collector = get_dit_collector()
            dit_collector.update_job_stats({'peak_speed': self._peak_speed_mbps})
            print(f"DEBUG: Updated peak speed to {self._peak_speed_mbps:.1f} MB/s from destination progress")
        
        self.destination_update.emit(payload)

    def _handle_dest_completed(self, payload: dict):
        """Handle destination completed events"""
        self._mark_activity()
        dest_path = payload.get('dest_path', '')
        if dest_path:
            self.destination_completed.emit(dest_path)
            print(f"DEBUG: Destination completed signal emitted for: {dest_path}")

    def wait_for_idle(self, idle_ms: int = 200, timeout_ms: int = 5000) -> bool:
        """Wait until the event pump has been idle for idle_ms or until timeout."""
        idle_seconds = idle_ms / 1000.0
        deadline = time.time() + (timeout_ms / 1000.0)

        while time.time() < deadline:
            inactive_duration = time.time() - self._last_event_timestamp
            if inactive_duration >= idle_seconds:
                return True
            time.sleep(0.05)

        return False

    def _recalculate_dataset_total(self) -> None:
        """Update the expected bytes per destination when inputs change."""
        if self._job_total_bytes > 0 and self._destination_count > 0:
            self._dataset_total_bytes = self._job_total_bytes / self._destination_count
            for stats in self._dest_stats.values():
                stats['expected_total_bytes'] = self._dataset_total_bytes

    def _mark_activity(self) -> None:
        """Record the timestamp of the latest processed event."""
        self._last_event_timestamp = time.time()

    def set_expected_destination_count(self, count: int) -> None:
        """Set the anticipated number of destinations for accurate progress calculations."""
        try:
            count = max(0, int(count))
        except (TypeError, ValueError):
            return
        if count == 0:
            return
        if count != self._destination_count:
            self._destination_count = count
            self._recalculate_dataset_total()

    def set_destination_roots(self, roots: list[str]) -> None:
        """Provide normalized destination roots for mapping dest_index → path."""
        if not roots:
            self._destination_roots = []
            return
        normalized = []
        for path in roots:
            try:
                normalized.append(os.path.normpath(path))
            except Exception:
                normalized.append(path)
        self._destination_roots = normalized
        self._destination_count = max(self._destination_count, len(normalized))
        self._recalculate_dataset_total()

    def _apply_destination_progress_override(self, update: dict) -> None:
        """Override job-level progress to reflect averaged destination completion."""
        with self._dest_stats_lock:
            if not self._dest_stats:
                return

            dest_stats = list(self._dest_stats.values())
            dest_count_expected = max(1, self._destination_count or len(dest_stats))

            dataset_total = self._dataset_total_bytes
            if not dataset_total:
                raw_total = update.get('total_bytes', 0) or self._job_total_bytes
                dataset_total = (raw_total / dest_count_expected) if raw_total else 0.0

            if dataset_total <= 0:
                return

            total_bytes_sum = sum(stats.get('total_bytes', 0.0) for stats in dest_stats)
            unique_bytes_copied = total_bytes_sum / dest_count_expected
            progress_percent = (unique_bytes_copied / dataset_total) * 100.0 if dataset_total > 0 else 0.0
            progress_percent = max(0.0, min(100.0, progress_percent))

            update['total_bytes'] = dataset_total
            update['bytes_copied'] = unique_bytes_copied
            update['progress_percent'] = progress_percent

            # Average current speed across destinations
            avg_current_speed = sum(stats.get('current_speed_mbps', 0.0) for stats in dest_stats) / dest_count_expected
            update['current_speed_mbps'] = max(0.0, avg_current_speed)

            # Peak speed is the best individual destination peak
            peak_speed = max((stats.get('peak_speed_mbps', 0.0) for stats in dest_stats), default=0.0)
            update['peak_speed_mbps'] = max(update.get('peak_speed_mbps', 0.0), peak_speed)

            # Derive file counts using destination metrics
            per_dest_total_files = [stats.get('total_files', 0) for stats in dest_stats if stats.get('total_files', 0)]
            per_dest_completed = [stats.get('completed_files', 0) for stats in dest_stats]

            if per_dest_total_files:
                total_files_unique = int(max(per_dest_total_files))
            else:
                total_files_unique = int(update.get('total_files', 0))

            if total_files_unique > 0:
                avg_completed = sum(per_dest_completed) / dest_count_expected
                update['total_files'] = total_files_unique
                update['files_completed'] = min(total_files_unique, int(round(avg_completed)))
