#!/usr/bin/env python3
"""
EventBridge: Professional event buffering and auto-initialization for JobAggregator
Handles thread-safe event routing and prevents initialization race conditions
"""

import time
from typing import List, Dict, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass
from PyQt6.QtCore import QObject, QTimer, QMetaObject, Qt, pyqtSignal, pyqtSlot
from .job_aggregator import JobAggregator, JobSnapshot
from .event_schema import EventRouter, EventType, global_event_router
from .job_state import JobStateManager


@dataclass
class BufferedEvent:
    """Buffered event waiting for JobAggregator initialization"""
    timestamp: float
    event_type: str
    payload: dict


class EventBridge(QObject):
    """
    Professional event bridge with buffering and auto-initialization
    
    Handles the race condition where file.progress events arrive before
    JobAggregator is initialized by buffering events and auto-detecting
    job parameters for seamless initialization.
    """
    
    # Signals for thread-safe UI updates
    progress_update = pyqtSignal(dict)
    destination_update = pyqtSignal(dict)
    aggregator_ready = pyqtSignal()
    
    def __init__(self, event_handler: Optional[Callable] = None):
        super().__init__()
        
        # Event buffering
        self.event_buffer: deque = deque(maxlen=1000)  # Buffer up to 1000 events
        self.buffer_timeout_ms = 30000  # 30 second buffer timeout
        
        # JobAggregator state (legacy)
        self.job_aggregator: Optional[JobAggregator] = None
        self.is_initialized = False
        self.pending_initialization = False
        
        # JobState manager for stable progress tracking
        self.job_state_manager = JobStateManager()
        
        # Auto-detection state
        self.detected_files: Dict[str, Dict] = {}  # file_id -> file_info
        self.detected_destinations: set = set()
        self.auto_init_threshold = 3  # Auto-init after 3 unique files detected
        
        # Progress update throttling to prevent file-level updates from causing progress bar jumping
        self.last_progress_emit_time = 0.0
        self.last_progress_percent = 0.0
        self.progress_throttle_interval = 0.5  # Emit job progress max every 500ms
        self.progress_percent_threshold = 1.0  # Only emit if progress changed by at least 1%
        
        # Thread-safe timer management
        self.buffer_timer = QTimer()
        self.buffer_timer.setSingleShot(True)
        self.buffer_timer.timeout.connect(self._flush_expired_buffer)
        
        # Comprehensive event routing
        self.event_router = EventRouter()
        self.event_router.enable_debug_logging(True)  # Enable for debugging
        self.event_router.register_handler(EventType.FILE_PROGRESS, self._handle_file_progress_internal)
        self.event_router.register_handler(EventType.FILE_COMPLETED, self._handle_file_completed_internal)
        self.event_router.register_handler(EventType.JOB_PROGRESS, self._handle_job_progress_internal)
        self.event_router.register_handler(EventType.JOB_START, self._handle_job_start_internal)
        self.event_router.register_handler(EventType.JOB_STARTED, self._handle_job_started_internal)
        self.event_router.register_handler(EventType.JOB_INITIALIZED, self._handle_job_started_internal)
        self.event_router.register_handler(EventType.DEST_PROGRESS, self._handle_dest_progress_internal)
        
        # External event handler (for RustEventSink compatibility)
        self.event_handler = event_handler
        
        print("DEBUG: EventBridge initialized with comprehensive event routing")
    
    def initialize_job(self, total_files: int, destinations: List[str]) -> bool:
        """
        Initialize JobAggregator with explicit parameters
        
        Args:
            total_files: Expected number of files
            destinations: List of destination paths
            
        Returns:
            True if initialization succeeded
        """
        if self.is_initialized:
            print("DEBUG: JobAggregator already initialized, skipping")
            return True
        
        try:
            self.job_aggregator = JobAggregator(total_files, destinations)
            self.is_initialized = True
            self.pending_initialization = False
            
            # Reset progress throttling for new job
            self.last_progress_emit_time = 0.0
            self.last_progress_percent = 0.0
            
            # Process buffered events directly
            self._process_buffered_events()
            
            self.aggregator_ready.emit()
            print(f"DEBUG: EventBridge initialized JobAggregator for {total_files} files to {destinations}")
            return True
            
        except Exception as e:
            print(f"ERROR: EventBridge JobAggregator initialization failed: {e}")
            return False
    
    def emit_event(self, event_type: str, payload: dict) -> None:
        """
        Thread-safe event emission with buffering and auto-initialization
        
        Args:
            event_type: Type of event (file.progress, job.started, etc.)
            payload: Event payload dictionary
        """
        # Direct call since we're handling this properly in the main thread
        # PyQt6's QMetaObject.invokeMethod has different signature requirements
        try:
            self._handle_event_internal(event_type, payload)
        except Exception as e:
            print(f"ERROR: Event handling failed: {e}")
    
    def _handle_event_internal(self, event_type: str, payload: dict) -> None:
        """Internal event handler - always called from main thread with comprehensive routing"""
        # Use comprehensive event router for normalization and routing
        success = self.event_router.route_event(event_type, payload)
        
        if not success:
            print(f"DEBUG: Event routing failed for {event_type}")
        
        # Forward to external handler if provided (legacy compatibility)
        if self.event_handler:
            try:
                normalized_type = self.event_router.normalize_event_type(event_type)
                self.event_handler(normalized_type.value, payload)
            except Exception as e:
                print(f"ERROR: External event handler failed: {e}")
    
    def _attempt_auto_detection(self, payload: dict) -> None:
        """Attempt to auto-detect job parameters from file events"""
        if self.pending_initialization:
            return
        
        # Extract file information
        file_id = payload.get('file_id', payload.get('filename', 'unknown'))
        dest_path = payload.get('dest_path', payload.get('destination', ''))
        total_bytes = payload.get('total_bytes', 0)
        
        # Track detected files and destinations
        if file_id != 'unknown' and dest_path:
            self.detected_files[file_id] = {
                'dest_path': dest_path,
                'total_bytes': total_bytes,
                'detected_at': time.time()
            }
            self.detected_destinations.add(dest_path)
        
        # Auto-initialize if we have enough data
        unique_files = len(self.detected_files)
        destinations = list(self.detected_destinations)
        
        if unique_files >= self.auto_init_threshold and destinations:
            self.pending_initialization = True
            
            # Estimate total files (conservative approach)
            estimated_total = max(unique_files * 2, 10)  # At least double what we've seen
            
            print(f"DEBUG: Auto-detecting job parameters: {estimated_total} files to {destinations}")
            
            # Initialize with detected parameters
            QMetaObject.invokeMethod(
                self, "initialize_job",
                Qt.ConnectionType.QueuedConnection,
                estimated_total, destinations
            )
    
    
    def _handle_file_progress_internal(self, event_type: str, payload: dict) -> None:
        """Handle file progress events with comprehensive routing"""
        # If not initialized, try auto-detection and buffering
        if not self.is_initialized and not self.pending_initialization:
            self._attempt_auto_detection(payload)
            
            # Buffer the event
            buffered_event = BufferedEvent(
                timestamp=time.time(),
                event_type=event_type,
                payload=payload.copy()
            )
            self.event_buffer.append(buffered_event)
            
            # Start buffer timeout timer (thread-safe)
            if not self.buffer_timer.isActive():
                self.buffer_timer.start(self.buffer_timeout_ms)
            
            print(f"DEBUG: Event {event_type} buffered (JobAggregator not ready)")
            return
        
        # Process with JobAggregator if initialized
        if self.is_initialized and self.job_aggregator:
            try:
                file_id = payload.get('file_id', payload.get('filename', 'unknown'))
                filename = payload.get('filename', file_id)
                bytes_copied = payload.get('bytes_copied', 0)
                total_bytes = payload.get('total_bytes', 0)
                dest_path = payload.get('dest_path', payload.get('destination', ''))
                
                print(f"DEBUG: *** PAYLOAD ANALYSIS ***")
                print(f"DEBUG: payload keys: {list(payload.keys())}")
                print(f"DEBUG: file_id: '{file_id}'")
                print(f"DEBUG: dest_path extracted: '{dest_path}'")
                print(f"DEBUG: payload dest_path field: {payload.get('dest_path', 'MISSING')}")
                print(f"DEBUG: payload destination field: {payload.get('destination', 'MISSING')}")
                
                # If no dest_path in payload, use the first available destination from JobAggregator
                if not dest_path and self.job_aggregator and self.job_aggregator.destinations:
                    dest_path = self.job_aggregator.destinations[0]
                    print(f"DEBUG: Using fallback dest_path: '{dest_path}'")
                
                # Update JobAggregator and get snapshot
                snapshot = self.job_aggregator.update_file_progress(
                    file_id, bytes_copied, total_bytes, dest_path, filename
                )
                
                # Emit UI updates (thread-safe)
                self._emit_progress_updates(snapshot)
                
            except Exception as e:
                print(f"ERROR: File progress processing failed: {e}")
    
    def _handle_file_completed_internal(self, event_type: str, payload: dict) -> None:
        """Handle file completion events with comprehensive routing"""
        if not self.is_initialized or not self.job_aggregator:
            return
        
        try:
            file_id = payload.get('file_id', payload.get('filename', 'unknown'))
            filename = payload.get('filename', file_id)
            total_bytes = payload.get('total_bytes', 0)
            dest_path = payload.get('dest_path', payload.get('destination', ''))
            
            # If no dest_path in payload, use the first available destination from JobAggregator
            if not dest_path and self.job_aggregator and self.job_aggregator.destinations:
                dest_path = self.job_aggregator.destinations[0]
                print(f"DEBUG: File completion using fallback dest_path: '{dest_path}'")
            
            # Mark file as complete
            snapshot = self.job_aggregator.update_file_progress(
                file_id, total_bytes, total_bytes, dest_path, filename
            )
            
            self._emit_progress_updates(snapshot)
            
        except Exception as e:
            print(f"ERROR: File completion processing failed: {e}")
    
    def _handle_job_start_internal(self, event_type: str, payload: dict) -> None:
        """Handle job.start event with JobManifest"""
        # Initialize JobState with manifest data
        if self.job_state_manager.initialize_from_manifest(payload):
            print(f"DEBUG: ✅ JobState initialized from manifest successfully")
            
            # Also initialize legacy JobAggregator for compatibility
            total_files = payload.get('total_files', 0)
            destinations = payload.get('destinations', [])
            if total_files > 0 and destinations:
                self.initialize_job(total_files, destinations)
            
            # Emit initial progress update with stable range
            ui_payload = self.job_state_manager.get_ui_payload()
            ui_payload['job_manifest_initialized'] = True
            self.progress_update.emit(ui_payload)
        else:
            print(f"ERROR: Failed to initialize JobState from manifest")

    def _handle_job_progress_internal(self, event_type: str, payload: dict) -> None:
        """Handle job.progress events with JobState for stable progress"""
        print(f"DEBUG: EventBridge handling job.progress event")
        
        # Update JobState with progress data
        if self.job_state_manager.update_progress(payload):
            # Emit stable progress update from JobState - this is the ONLY progress update
            ui_payload = self.job_state_manager.get_ui_payload()
            self.progress_update.emit(ui_payload)
            print(f"DEBUG: JobState progress updated: {ui_payload['progress_percent']:.1f}%")
            
            # Skip legacy progress updates when JobState is working to prevent conflicts
            return
        
        # Legacy JobAggregator handling - only when JobState is not available
        if self.is_initialized and self.job_aggregator:
            snapshot = self.job_aggregator.get_current_snapshot()
            self._emit_legacy_progress_updates(snapshot)
    
    def _handle_job_started_internal(self, event_type: str, payload: dict) -> None:
        """Handle job initialization events with comprehensive routing"""
        total_files = payload.get('total_files', 0)
        destinations = payload.get('destinations', [])
        
        if total_files > 0 and destinations:
            self.initialize_job(total_files, destinations)
    
    def _handle_dest_progress_internal(self, event_type: str, payload: dict) -> None:
        """Handle destination progress events with comprehensive routing"""
        # Emit destination-specific updates
        self.destination_update.emit(payload)
    
    def _process_buffered_events(self) -> None:
        """Process all buffered events after JobAggregator initialization"""
        if not self.is_initialized or not self.job_aggregator:
            return
        
        processed_count = 0
        
        # Process events in chronological order
        while self.event_buffer:
            buffered_event = self.event_buffer.popleft()
            
            try:
                # Use event router for processing buffered events
                self.event_router.route_event(buffered_event.event_type, buffered_event.payload)
                processed_count += 1
                
            except Exception as e:
                print(f"ERROR: Processing buffered event failed: {e}")
        
        # Stop buffer timer since we've processed everything (thread-safe)
        self._stop_timer_safely('buffer_timer')
        
        print(f"DEBUG: Processed {processed_count} buffered events with event router")
    
    def _flush_expired_buffer(self) -> None:
        """Flush expired events from buffer"""
        current_time = time.time()
        timeout_threshold = current_time - (self.buffer_timeout_ms / 1000)
        
        # Remove expired events
        while self.event_buffer and self.event_buffer[0].timestamp < timeout_threshold:
            expired_event = self.event_buffer.popleft()
            print(f"DEBUG: Expired buffered event: {expired_event.event_type}")
        
        print(f"DEBUG: Buffer flushed, {len(self.event_buffer)} events remain")
    
    def _emit_legacy_progress_updates(self, snapshot: JobSnapshot) -> None:
        """Thread-safe emission of progress updates with throttling to prevent progress bar jumping"""
        current_time = time.time()
        current_percent = snapshot.job_progress_percent
        
        # Check throttling conditions to prevent progress bar jumping from file-level events
        time_elapsed = current_time - self.last_progress_emit_time
        percent_change = abs(current_percent - self.last_progress_percent)
        
        should_emit_progress = (
            time_elapsed >= self.progress_throttle_interval or  # Time threshold
            percent_change >= self.progress_percent_threshold or  # Progress threshold  
            current_percent >= 100.0 or  # Always emit completion
            current_percent == 0.0  # Always emit start
        )
        
        if should_emit_progress:
            # Emit main progress update
            progress_payload = {
                'progress_percent': snapshot.job_progress_percent,
                'completed_files': snapshot.job_completed_files,
                'total_files': snapshot.job_total_files,
                'bytes_copied': snapshot.job_bytes_copied,
                'total_bytes': snapshot.job_total_bytes,
                'current_speed_mbps': snapshot.job_current_mb_s,
                'peak_speed_mbps': snapshot.job_peak_mb_s,
                'elapsed_time': snapshot.job_elapsed_seconds,
                'filename': snapshot.current_filename,
                'eta_seconds': snapshot.job_eta_seconds
            }
            
            self.progress_update.emit(progress_payload)
            self.last_progress_emit_time = current_time
            self.last_progress_percent = current_percent
            print(f"DEBUG: Emitted job progress update: {snapshot.job_progress_percent:.1f}%, {snapshot.job_completed_files}/{snapshot.job_total_files} files")
        else:
            print(f"DEBUG: Throttled progress update: {current_percent:.1f}% (time: {time_elapsed:.2f}s, change: {percent_change:.1f}%)")
        
        # *** CRITICAL DEBUG: Check what destination data we have ***
        print(f"DEBUG: *** DESTINATION DATA CHECK ***")
        print(f"DEBUG: snapshot.destinations type: {type(snapshot.destinations)}")
        print(f"DEBUG: snapshot.destinations length: {len(snapshot.destinations) if snapshot.destinations else 'None/Empty'}")
        print(f"DEBUG: snapshot.destinations keys: {list(snapshot.destinations.keys()) if snapshot.destinations else 'None/Empty'}")
        
        # Emit per-destination updates
        if not snapshot.destinations:
            print(f"DEBUG: *** NO DESTINATIONS FOUND - This explains why destination cards show zeros ***")
            return
            
        for dest_path, dest_metrics in snapshot.destinations.items():
            dest_payload = {
                'dest_path': dest_path,
                'dest_index': 0,
                'currentSpeedMiBps': dest_metrics.current_mb_s,
                'current_speed_mbps': dest_metrics.current_mb_s,
                'peakSpeedMiBps': dest_metrics.peak_mb_s,
                'peak_speed_mbps': dest_metrics.peak_mb_s,
                'progress_percent': (dest_metrics.bytes_copied / dest_metrics.total_bytes * 100) if dest_metrics.total_bytes > 0 else 0,
                'bytes_copied': dest_metrics.bytes_copied,
                'total_bytes': dest_metrics.total_bytes,
                'etaS': dest_metrics.eta_seconds,
                'eta_seconds': dest_metrics.eta_seconds,
                'completed_files': dest_metrics.completed_files,
                'total_files': dest_metrics.total_files
            }
            
            print(f"DEBUG: Emitting destination update for {dest_path}: {dest_metrics.current_mb_s:.1f} MB/s, {dest_payload['progress_percent']:.1f}%")
            self.destination_update.emit(dest_payload)
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get comprehensive event routing statistics"""
        return {
            'buffered_events': len(self.event_buffer),
            'is_initialized': self.is_initialized,
            'detected_files': len(self.detected_files),
            'detected_destinations': len(self.detected_destinations),
            'supported_event_types': len(self.event_router.get_supported_event_types()),
            'active_handlers': len(self.event_router.handlers)
        }
    
    def get_current_snapshot(self) -> Optional[JobSnapshot]:
        """Get current JobAggregator snapshot if available"""
        if self.is_initialized and self.job_aggregator:
            return self.job_aggregator.get_current_snapshot()
        return None
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive stats for DIT report generation with full data retention"""
        if self.is_initialized and self.job_aggregator:
            # Use the enhanced reporting method that includes file records and destination data
            comprehensive_data = self.job_aggregator.get_comprehensive_stats_for_reporting()
            
            # Return in the expected format for report generation
            return {
                'total_bytes': comprehensive_data['stats']['total_bytes'],
                'copied_bytes': comprehensive_data['stats']['copied_bytes'],
                'duration': comprehensive_data['stats']['duration_seconds'],
                'avg_speed': comprehensive_data['stats']['avg_speed_mb_s'],
                'peak_speed': comprehensive_data['stats']['peak_speed_mb_s'],
                'total_files': comprehensive_data['stats']['total_files'],
                'completed_files': comprehensive_data['stats']['completed_files'],
                'cancelled_files': comprehensive_data['stats']['total_files'] - comprehensive_data['stats']['completed_files'],
                'error_files': comprehensive_data['stats']['error_files'],
                'files': comprehensive_data['files'],  # Now includes actual file records
                'destinations': comprehensive_data['destinations']  # Per-destination data
            }
        
        return {
            'total_bytes': 0,
            'copied_bytes': 0,
            'duration': 0,
            'avg_speed': 0,
            'peak_speed': 0,
            'total_files': 0,
            'completed_files': 0,
            'cancelled_files': 0,
            'error_files': 0,
            'files': [],
            'destinations': {}
        }
    
    def get_destination_completion_status(self) -> Dict[str, bool]:
        """Check which destinations have completed - for per-destination reporting"""
        if self.is_initialized and self.job_aggregator:
            return self.job_aggregator.get_destination_completion_status()
        return {}
    
    @pyqtSlot(str)
    def _stop_timer_on_ui_thread(self, timer_name: str):
        """Thread-safe timer stop method - must run on UI thread"""
        timer = getattr(self, timer_name, None)
        if timer and hasattr(timer, 'isActive') and timer.isActive():
            timer.stop()
            print(f"DEBUG: Stopped {timer_name} on UI thread")
    
    def _stop_timer_safely(self, timer_name: str):
        """Stop timer safely from any thread"""
        try:
            # Use QMetaObject.invokeMethod for thread-safe timer operations
            QMetaObject.invokeMethod(
                self, "_stop_timer_on_ui_thread", 
                Qt.ConnectionType.QueuedConnection,
                timer_name
            )
        except Exception as e:
            print(f"DEBUG: Error stopping timer {timer_name} safely: {e}")
    
    def reset_for_new_job(self) -> None:
        """Reset EventBridge for a new transfer job"""
        # Stop any running timers (thread-safe)
        self._stop_timer_safely('buffer_timer')
        
        # Clear state
        self.event_buffer.clear()
        self.detected_files.clear()
        self.detected_destinations.clear()
        
        # Reset progress throttling 
        self.last_progress_emit_time = 0.0
        self.last_progress_percent = 0.0
        
        # Reset JobAggregator
        if self.job_aggregator:
            self.job_aggregator = None
        
        # Reset JobState
        self.job_state_manager.reset()
        
        self.is_initialized = False
        self.pending_initialization = False
        
        print("DEBUG: EventBridge reset for new job")
    
    def get_event_schema_info(self) -> Dict[str, Any]:
        """Get information about supported event schemas"""
        return {
            'supported_types': self.event_router.get_supported_event_types(),
            'validation_enabled': self.event_router.validation_enabled,
            'debug_logging': self.event_router.debug_logging,
            'registered_handlers': {event_type.value: len(handlers) 
                                   for event_type, handlers in self.event_router.handlers.items()}
        }