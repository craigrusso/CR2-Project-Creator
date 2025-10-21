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
import math
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
        self._last_job_bytes: float = 0.0  # Producer-side bytes emitted so far
        self._engine_progress_bytes: float = 0.0
        self._engine_total_target_bytes: float = 0.0
        self._last_bucket_bytes: float = 0.0
        self._source_total_files: int = 0

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
        self._last_event_timestamp = time.time()
        self._last_job_bytes = 0.0
        self._engine_progress_bytes = 0.0
        self._engine_total_target_bytes = 0.0
        self._last_bucket_bytes = 0.0
        self._source_total_files = 0
        
        # Reset per-destination stats for new job
        with self._dest_stats_lock:
            self._dest_stats = {}
            self._initialize_dest_stats_locked()

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

        self._engine_progress_bytes = float(bytes_copied or 0)
        if total_bytes:
            self._engine_total_target_bytes = float(total_bytes)
            self._job_total_bytes = float(total_bytes)
            self._recalculate_dataset_total()

        total_files = payload.get('total_files', 0)
        if total_files:
            self._job_total_files = float(total_files)

        if self._job_total_files:
            dest_count_estimate = max(1, self._destination_count or len(self._dest_stats) or len(self._destination_roots))
            estimated_sources = int(self._job_total_files / dest_count_estimate)
            if estimated_sources > 0:
                self._source_total_files = max(self._source_total_files, estimated_sources)

        self._last_job_bytes = float(bytes_copied)
        self._engine_progress_bytes = float(bytes_copied)
        if total_bytes:
            self._engine_total_target_bytes = float(total_bytes)
            self._job_total_bytes = float(total_bytes)
            self._recalculate_dataset_total()

        # CRITICAL FIX: DO NOT calculate progress from engine bytes - this is producer-side progress
        # The engine reports total bytes WRITTEN across all destinations, which hits 100% 
        # before all destinations finish READING those bytes.
        # Instead, let _apply_destination_progress_override() calculate TRUE aggregate progress
        # from per-destination completion stats.
        
        # Track peak speed for DIT reports
        current_speed = payload.get('speed_mbps', 0)
        if current_speed > self._peak_speed_mbps:
            self._peak_speed_mbps = current_speed
            # Update DIT collector with new peak speed
            from ..utils.dit_data_collector import get_dit_collector
            dit_collector = get_dit_collector()
            dit_collector.update_job_stats({'peak_speed': self._peak_speed_mbps})

        # Calculate progress from engine bytes (producer-side progress)
        # This will be overridden by per-destination aggregate if available
        if total_bytes > 0:
            engine_progress = min(100.0, (bytes_copied / total_bytes) * 100.0)
        else:
            engine_progress = 0.0

        update = {
            'bytes_copied': bytes_copied,
            'total_bytes': total_bytes,
            'progress_percent': engine_progress,
            'files_completed': payload.get('files_completed', 0),
            'total_files': payload.get('total_files', 0),
            'elapsed_s': payload.get('elapsed_s', 0),
            'speed_mbps': current_speed,
            'current_speed_mbps': payload.get('current_speed_mbps', 0),
            'peak_speed_mbps': self._peak_speed_mbps,
        }
        # CRITICAL: Override with TRUE aggregate progress from all destinations if available
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

    def _update_dest_stats_from_progress(self, payload: dict) -> None:
        """Update per-destination statistics from dest.progress payloads."""
        try:
            dest_index = payload.get('dest_index', payload.get('destination_index', 0))
            if not isinstance(dest_index, int):
                dest_index = int(dest_index)
        except Exception:
            dest_index = 0

        bytes_copied = float(payload.get('bytes_copied', payload.get('completed_bytes', 0.0)) or 0.0)
        total_bytes = float(payload.get('total_bytes', payload.get('expected_total_bytes', 0.0)) or 0.0)
        current_speed = float(payload.get('current_speed_mbps', payload.get('currentSpeedMiBps', 0.0)) or 0.0)
        peak_speed = float(payload.get('peak_speed_mbps', payload.get('peakSpeedMiBps', 0.0)) or 0.0)
        completed_files = int(payload.get('completed_files', payload.get('files_completed', 0)) or 0)
        total_files = int(payload.get('total_files', payload.get('files_total', 0)) or 0)
        eta_seconds = float(payload.get('eta_seconds', payload.get('etaS', 0.0)) or 0.0)
        elapsed_seconds = float(payload.get('elapsed_seconds', payload.get('elapsed_time', 0.0)) or 0.0)
        progress_percent = payload.get('progress_percent')
        dest_path = (
            payload.get('dest_path')
            or payload.get('destination_path')
            or ''
        )

        now = time.time()
        with self._dest_stats_lock:
            stats = self._ensure_dest_stat_entry_locked(dest_index, now=now)

            if dest_path:
                try:
                    stats['dest_root'] = os.path.normpath(dest_path)
                except Exception:
                    stats['dest_root'] = dest_path

            stats['total_bytes'] = max(0.0, bytes_copied)
            expected = max(total_bytes, stats.get('expected_total_bytes', 0.0))
            stats['expected_total_bytes'] = expected
            stats['inflight_bytes'] = max(0.0, expected - stats['total_bytes'])

            stats['current_speed_mbps'] = max(0.0, current_speed)
            stats['peak_speed_mbps'] = max(stats.get('peak_speed_mbps', 0.0), peak_speed, current_speed)

            if progress_percent is not None:
                stats['progress_percent'] = progress_percent
            elif expected > 0:
                stats['progress_percent'] = min(100.0, (stats['total_bytes'] / expected) * 100.0)
            else:
                stats['progress_percent'] = 0.0

            stats['completed_files'] = max(stats.get('completed_files', 0), completed_files)
            stats['total_files'] = max(stats.get('total_files', 0), total_files)
            stats['eta_seconds'] = max(0.0, eta_seconds)
            if elapsed_seconds > 0.0:
                stats['elapsed_seconds'] = max(stats.get('elapsed_seconds', 0.0), elapsed_seconds)
            else:
                stats['elapsed_seconds'] = max(stats.get('elapsed_seconds', 0.0), now - stats.get('start_time', now))

            stats['last_update_time'] = now
            stats['last_bytes'] = stats['total_bytes']

            self._destination_count = max(self._destination_count, dest_index + 1, len(self._destination_roots))
            self._recalculate_dataset_total()

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
            stats = self._ensure_dest_stat_entry_locked(dest_index, now=current_time)
            if dest_root:
                stats['dest_root'] = dest_root
            stats['last_file_path'] = file_dest_path or stats.get('last_file_path', '')
            
            self._destination_count = max(self._destination_count, len(self._dest_stats))
            self._recalculate_dataset_total()
            
            if self._dataset_total_bytes > 0:
                stats['expected_total_bytes'] = self._dataset_total_bytes
            
            previous_total = stats.get('total_bytes', 0.0)
            stats['total_bytes'] = previous_total + bytes_copied
            inflight_before = stats.get('inflight_bytes', 0.0) or 0.0
            stats['inflight_bytes'] = max(0.0, inflight_before - bytes_copied)

            stats['total_files'] = stats.get('total_files', 0) + 1
            # Mirror completed count so global progress calculations work
            stats['completed_files'] = stats['total_files']
            
            # Calculate instantaneous speed (MB/s)
            last_update = stats.get('last_update_time', current_time)
            time_since_last = current_time - last_update
            if time_since_last > 0:
                bytes_since_last = stats['total_bytes'] - stats.get('last_bytes', previous_total)
                instantaneous_speed_mbps = (bytes_since_last / time_since_last) / (1024 * 1024)
                
                # Update current speed with smoothing (exponential moving average)
                alpha = 0.3  # Smoothing factor
                stats['current_speed_mbps'] = (alpha * instantaneous_speed_mbps + 
                                               (1 - alpha) * stats['current_speed_mbps'])
            
            # Calculate average speed from window (last 2 seconds)
            window_duration = current_time - stats['window_start_time']
            if window_duration >= 2.0:  # Reset window every 2 seconds
                window_bytes = stats['total_bytes'] - stats.get('window_start_bytes', 0.0)
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
            combined_bytes = stats['total_bytes'] + stats.get('inflight_bytes', 0.0)
            combined_progress_percent = 0.0
            remaining_bytes = 0.0
            combined_remaining = 0.0

            if expected_total_bytes > 0:
                remaining_bytes = max(expected_total_bytes - stats['total_bytes'], 0.0)
                combined_remaining = max(expected_total_bytes - combined_bytes, 0.0)

                progress_percent = min(
                    100.0, (stats['total_bytes'] / expected_total_bytes) * 100.0
                )
                combined_progress_percent = min(
                    100.0, (combined_bytes / expected_total_bytes) * 100.0
                )

                active_remaining = max(combined_remaining, remaining_bytes)
                if stats['current_speed_mbps'] > 0.01 and active_remaining > 0:
                    remaining_mb = remaining_bytes / (1024 * 1024)
                    eta_seconds = remaining_mb / stats['current_speed_mbps']
                if remaining_bytes <= tolerance_bytes:
                    progress_percent = 100.0
                    if stats['current_speed_mbps'] <= 0.01 or combined_remaining <= tolerance_bytes:
                        eta_seconds = 0.0
                if combined_remaining <= tolerance_bytes:
                    combined_progress_percent = 100.0

            elapsed_seconds = max(0.0, current_time - stats['start_time'])

            if progress_percent >= 100.0:
                stats['current_speed_mbps'] = 0.0
            
            # Persist computed values so global progress overrides can use them
            stats['progress_percent'] = progress_percent
            stats['eta_seconds'] = eta_seconds
            stats['elapsed_seconds'] = elapsed_seconds
            stats['combined_progress_percent'] = combined_progress_percent
            stats['combined_bytes'] = combined_bytes
            stats['remaining_bytes'] = remaining_bytes if expected_total_bytes else 0.0
            
            print(
                f"🔥🔥🔥 DEST_STATS: dest_index={dest_index}, root={dest_root}, files={stats['total_files']}, "
                f"bytes={combined_bytes}, speed={stats['current_speed_mbps']:.1f} MB/s, "
                f"peak={stats['peak_speed_mbps']:.1f} MB/s"
            )
            
            # Emit destination progress event to UI
            dest_progress_payload = {
                'dest_index': dest_index,
                'dest_path': dest_root,
                'current_file_path': file_dest_path,
                'bytes_copied': stats['total_bytes'],
                'inflight_bytes': stats.get('inflight_bytes', 0.0),
                'combined_bytes': combined_bytes,
                'completed_bytes': stats['total_bytes'],
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
                'combined_progress_percent': combined_progress_percent,
                'remaining_bytes': stats.get('remaining_bytes', 0.0),
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
        self._update_dest_stats_from_progress(payload)
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
        
        # CRITICAL FIX: Also emit overall progress update calculated from all destinations
        # This ensures the main progress bar continues updating even if JobProgress events stop
        self._emit_aggregated_progress_from_destinations()

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

    def _initialize_dest_stats_locked(self) -> None:
        """Ensure per-destination stats exist for all known destinations."""
        dest_count = max(self._destination_count, len(self._destination_roots))
        if dest_count <= 0:
            return

        now = time.time()
        for dest_index in range(dest_count):
            self._ensure_dest_stat_entry_locked(dest_index, now=now)

    def _ensure_dest_stat_entry_locked(self, dest_index: int, *, now: Optional[float] = None) -> dict:
        """Get or create the stats record for a destination (lock must be held)."""
        stats = self._dest_stats.get(dest_index)
        if stats is not None:
            return stats

        if now is None:
            now = time.time()

        dest_root = ""
        if dest_index < len(self._destination_roots):
            dest_root = self._destination_roots[dest_index]

        expected_total = self._dataset_total_bytes or 0.0
        stats = {
            'dest_root': dest_root,
            'last_file_path': '',
            'total_bytes': 0.0,
            'inflight_bytes': 0.0,
            'total_files': 0,
            'completed_files': 0,
            'expected_total_bytes': expected_total,
            'last_update_time': now,
            'last_bytes': 0.0,
            'current_speed_mbps': 0.0,
            'peak_speed_mbps': 0.0,
            'start_time': now,
            'window_start_time': now,
            'window_start_bytes': 0.0,
            'progress_percent': 0.0,
            'eta_seconds': 0.0,
            'elapsed_seconds': 0.0,
            'completed_emitted': False,
        }
        self._dest_stats[dest_index] = stats
        return stats

    def _distribute_job_bytes(self, job_delta: float) -> None:
        """Spread producer-side byte deltas across destination inflight counters."""
        if job_delta <= 0:
            return

        with self._dest_stats_lock:
            dest_count = max(self._destination_count, len(self._dest_stats))
            if dest_count <= 0:
                dest_count = max(self._destination_count, len(self._destination_roots))
            if dest_count <= 0:
                return

            per_dest = job_delta / dest_count
            now = time.time()

            for dest_index in range(dest_count):
                stats = self._ensure_dest_stat_entry_locked(dest_index, now=now)
                expected = stats.get('expected_total_bytes', self._dataset_total_bytes)
                completed = stats.get('total_bytes', 0.0)
                inflight = stats.get('inflight_bytes', 0.0)

                # Skip if destination already accounted for full dataset
                if expected and (completed + inflight) >= expected:
                    continue

                stats['inflight_bytes'] = inflight + per_dest
                # Clamp to expected total bytes when available to avoid runaway accumulation
                if expected:
                    combined = stats['total_bytes'] + stats['inflight_bytes']
                    if combined > expected:
                        stats['inflight_bytes'] = max(0.0, expected - stats['total_bytes'])

                stats['elapsed_seconds'] = max(0.0, now - stats.get('start_time', now))

            self._destination_count = max(self._destination_count, dest_count)

    def _recalculate_dataset_total(self) -> None:
        """Update the expected bytes per destination when inputs change."""
        if self._job_total_bytes > 0 and self._destination_count > 0:
            self._dataset_total_bytes = self._job_total_bytes / self._destination_count
            for stats in self._dest_stats.values():
                stats['expected_total_bytes'] = self._dataset_total_bytes
                inflight = stats.get('inflight_bytes', 0.0)
                if inflight is None:
                    inflight = 0.0
                combined = stats.get('total_bytes', 0.0) + inflight
                if combined > self._dataset_total_bytes:
                    stats['inflight_bytes'] = max(
                        0.0, self._dataset_total_bytes - stats.get('total_bytes', 0.0)
                    )

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
            with self._dest_stats_lock:
                self._initialize_dest_stats_locked()

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
        with self._dest_stats_lock:
            self._initialize_dest_stats_locked()

    def _emit_aggregated_progress_from_destinations(self) -> None:
        """Emit an overall progress update calculated from all destination stats.
        
        This is called when a destination progress update comes in, ensuring the
        main progress bar continues updating even when JobProgress events stop.
        """
        # Create a basic progress update dict that will be populated by _apply_destination_progress_override
        with self._dest_stats_lock:
            if not self._dest_stats:
                return
            
            # Calculate aggregates from destinations
            total_bytes = 0.0
            total_completed = 0.0
            current_time = time.time()
            
            for stats in self._dest_stats.values():
                total_bytes += stats.get('expected_total_bytes', 0.0)
                total_completed += stats.get('total_bytes', 0.0)
            
            if total_bytes <= 0:
                total_bytes = self._job_total_bytes or self._dataset_total_bytes
            
            # Create update dict with basic info
            update = {
                'bytes_copied': total_completed,
                'total_bytes': total_bytes,
                'progress_percent': 0.0,  # Will be calculated by override
                'files_completed': self._engine_files_completed,
                'total_files': self._job_total_files,
                'elapsed_s': current_time - self._job_start_time if self._job_start_time else 0,
                'speed_mbps': 0.0,  # Will be calculated by override
                'current_speed_mbps': 0.0,  # Will be calculated by override
                'peak_speed_mbps': self._peak_speed_mbps,
            }
            
        # Let override calculate accurate aggregate values
        self._apply_destination_progress_override(update)
        
        # Emit the aggregated progress
        self.progress_update.emit(update)
    
    def _apply_destination_progress_override(self, update: dict) -> None:
        """Override job-level progress so the summary reflects true aggregate transfer state."""
        with self._dest_stats_lock:
            if not self._dest_stats:
                return

            dest_stats = list(self._dest_stats.values())
            if not dest_stats:
                return

            original_bytes = float(update.get('bytes_copied', 0.0) or 0.0)
            original_total_bytes = float(update.get('total_bytes', 0.0) or 0.0)
            original_progress = float(update.get('progress_percent', 0.0) or 0.0)
            original_current_speed = update.get('current_speed_mbps', 0.0)
            original_speed = update.get('speed_mbps', original_current_speed)
            original_peak = update.get('peak_speed_mbps', 0.0)
            original_elapsed = update.get('elapsed_s', 0.0)
            original_eta = update.get('eta_seconds', update.get('eta', 0.0))
            original_total_files = update.get('total_files', 0)

            dest_count_expected = max(1, self._destination_count or len(dest_stats) or len(self._destination_roots))

            dataset_total = self._dataset_total_bytes
            if not dataset_total and dest_count_expected:
                raw_total = update.get('total_bytes', 0) or self._job_total_bytes
                dataset_total = (raw_total / dest_count_expected) if raw_total else 0.0

            total_expected = 0.0
            total_completed_only = 0.0
            total_inflight = 0.0
            active_speed_sum = 0.0
            elapsed_candidates = []
            eta_candidates = []
            peak_candidates = [update.get('peak_speed_mbps', 0.0)]
            write_ops_completed = 0

            for stats in dest_stats:
                expected = stats.get('expected_total_bytes', 0.0)
                if expected <= 0.0:
                    expected = dataset_total
                total_expected += expected

                completed = max(0.0, stats.get('total_bytes', 0.0))
                completed = min(completed, expected)
                inflight = max(0.0, min(expected - completed, stats.get('inflight_bytes', 0.0)))

                total_completed_only += completed
                total_inflight += inflight
                write_ops_completed += stats.get('completed_files', 0)

                progress = stats.get('progress_percent', 0.0)
                speed = max(0.0, stats.get('current_speed_mbps', 0.0))
                if progress < 100.0 and speed > 0.0:
                    active_speed_sum += speed

                peak_candidates.append(stats.get('peak_speed_mbps', 0.0))
                elapsed_candidates.append(stats.get('elapsed_seconds', 0.0))

                remaining = max(expected - (completed + inflight), 0.0)
                if progress >= 100.0 or remaining <= 0.0:
                    eta_candidates.append(0.0)
                elif speed > 0.01:
                    eta_candidates.append((remaining / (1024 * 1024)) / speed)

            if total_expected <= 0.0:
                total_expected = (
                    self._engine_total_target_bytes
                    or self._job_total_bytes
                    or update.get('total_bytes', 0)
                    or (dataset_total * dest_count_expected)
                )

            if total_expected <= 0.0:
                return

            engine_bytes = max(
                float(self._engine_progress_bytes or 0.0),
                original_bytes,
                self._last_bucket_bytes,
            )

            inflight_allowance = min(total_inflight, max(0.0, total_expected - total_completed_only))
            bucket_candidate = min(total_expected, total_completed_only)
            bucket_bytes = max(self._last_bucket_bytes, bucket_candidate)
            self._last_bucket_bytes = bucket_bytes

            dest_progress_percent = 0.0
            if total_expected > 0:
                dest_progress_percent = max(0.0, min(100.0, (bucket_bytes / total_expected) * 100.0))

            print(
                f"DEBUG: Progress calc - completed={total_completed_only:.0f}, inflight={total_inflight:.0f}, "
                f"bucket={bucket_bytes:.0f}, expected={total_expected:.0f}, "
                f"progress={dest_progress_percent:.1f}%, active_speed_sum={active_speed_sum:.1f}, "
                f"original_speed={original_speed:.1f}"
            )

            update['total_bytes'] = max(original_total_bytes, total_expected)
            update['bytes_copied'] = max(original_bytes, bucket_bytes)
            update['progress_percent'] = max(original_progress, dest_progress_percent)

            if active_speed_sum > 0.0:
                update['current_speed_mbps'] = active_speed_sum
            elif original_speed > 0.0:
                update['current_speed_mbps'] = original_speed
            else:
                update['current_speed_mbps'] = 0.0
            update['speed_mbps'] = update['current_speed_mbps']
            update['peak_speed_mbps'] = max(peak_candidates + [original_peak]) if peak_candidates else original_peak

            if elapsed_candidates:
                update['elapsed_s'] = max(original_elapsed, max(elapsed_candidates))
            else:
                update['elapsed_s'] = original_elapsed

            if eta_candidates:
                update['eta_seconds'] = max(eta_candidates)
            else:
                remaining_bytes = max(total_expected - bucket_bytes, 0.0)
                if update['current_speed_mbps'] > 0.01:
                    update['eta_seconds'] = (remaining_bytes / (1024 * 1024)) / update['current_speed_mbps']
                else:
                    update['eta_seconds'] = original_eta

            write_ops_total = int(max(original_total_files, write_ops_completed))
            if self._job_total_files and dest_count_expected:
                estimated_from_engine = int(self._job_total_files / dest_count_expected)
                if estimated_from_engine > 0:
                    self._source_total_files = max(self._source_total_files, estimated_from_engine)
                write_ops_total = max(write_ops_total, int(self._job_total_files))
            if self._source_total_files and dest_count_expected:
                write_ops_total = max(write_ops_total, self._source_total_files * dest_count_expected)

            if not write_ops_total and dest_count_expected and write_ops_completed:
                write_ops_total = dest_count_expected * max(1, math.ceil(write_ops_completed / dest_count_expected))

            if write_ops_total < write_ops_completed:
                write_ops_total = write_ops_completed

            source_total_est = 0
            if self._source_total_files:
                source_total_est = self._source_total_files
            elif write_ops_total and dest_count_expected:
                source_total_est = max(1, write_ops_total // dest_count_expected)
            elif self._job_total_files and dest_count_expected:
                source_total_est = max(1, int(self._job_total_files // dest_count_expected))

            if source_total_est:
                self._source_total_files = max(self._source_total_files, source_total_est)

            source_completed = 0
            if self._source_total_files and dest_count_expected:
                source_completed = min(
                    self._source_total_files,
                    write_ops_completed // dest_count_expected,
                )

            update['total_files'] = write_ops_total
            update['files_completed'] = write_ops_completed
            update['write_ops_total'] = write_ops_total
            update['write_ops_completed'] = write_ops_completed
            update['destinations_active'] = dest_count_expected
            if self._source_total_files:
                update['display_files_total'] = self._source_total_files
                update['display_files_completed'] = source_completed
            else:
                update['display_files_total'] = write_ops_total
                update['display_files_completed'] = write_ops_completed
