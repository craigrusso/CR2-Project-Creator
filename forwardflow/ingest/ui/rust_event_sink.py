"""
Professional Rust Event Sink with EventBridge integration
Handles accurate multi-file progress tracking with thread-safe event routing
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QMetaObject, Qt, pyqtSlot
from .event_bridge import EventBridge
from .job_aggregator import JobSnapshot
from ..utils.dit_data_collector import get_dit_collector
from typing import Optional, List, Dict, Any
import time


class RustEventSink(QObject):
    """Professional event sink with EventBridge for thread-safe progress tracking"""
    
    # Progress update signals
    progress_update = pyqtSignal(dict)
    destination_update = pyqtSignal(dict)
    destination_completed = pyqtSignal(str)  # Signal for immediate per-destination reporting
    
    def __init__(self):
        super().__init__()
        
        # Use EventBridge for thread-safe event handling
        self.event_bridge = EventBridge()
        
        # Connect EventBridge signals to our signals
        self.event_bridge.progress_update.connect(self.progress_update.emit)
        self.event_bridge.destination_update.connect(self.destination_update.emit)
        
        # Legacy compatibility - file records for reporting
        self._file_records = {}  # filename -> file record with verification info
        
        # Per-destination completion tracking for immediate report generation
        self._completed_destinations = set()  # Track which destinations are complete
        self._last_destination_check = {}     # Track destination progress for completion detection
        
        # Thread-safe timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(False)
        self.update_timer.timeout.connect(self._periodic_update)
        
        print("DEBUG: Professional RustEventSink with EventBridge initialized")
    
    def _check_destination_completion(self, event_type: str, payload: dict) -> None:
        """Check if a destination has completed and trigger immediate report generation"""
        normalized_type = self._normalize_event_type(event_type)
        dest_path = payload.get('dest_path', payload.get('destination_path', ''))
        
        # Handle direct destination completion events
        if normalized_type == 'dest.completed':
            if dest_path and dest_path not in self._completed_destinations:
                print(f"🎯 DESTINATION COMPLETED (direct): {dest_path} - Triggering immediate report generation")
                self._trigger_completion_signal(dest_path)
        
        # Handle destination progress events that reach 100%
        elif normalized_type == 'dest.progress':
            progress_percent = payload.get('progress_percent', 0)
            
            # Check if destination reached 100% completion
            if progress_percent >= 100.0 and dest_path and dest_path not in self._completed_destinations:
                print(f"🎯 DESTINATION COMPLETED (100% progress): {dest_path} - Triggering immediate report generation")
                self._trigger_completion_signal(dest_path)
    
    def _trigger_completion_signal(self, dest_path: str) -> None:
        """Trigger destination completion signal and mark as completed"""
        # Mark as completed
        self._completed_destinations.add(dest_path)
        
        # Emit custom signal for per-destination completion
        if hasattr(self, 'destination_completed'):
            self.destination_completed.emit(dest_path)
            print(f"DEBUG: destination_completed signal emitted for {dest_path}")
        else:
            # If signal doesn't exist, trigger report generation directly
            print(f"DEBUG: destination_completed signal not available, calling direct trigger")
            self._trigger_destination_report(dest_path)
    
    def initialize_job(self, total_files: int, destinations: List[str]) -> None:
        """Initialize EventBridge for a new transfer job"""
        # Direct initialization - we're already in the main thread
        self.event_bridge.initialize_job(total_files, destinations)
        
        # Clear file records and destination completion tracking
        self._file_records.clear()
        self._completed_destinations.clear()
        self._last_destination_check.clear()
        
        # Start periodic update timer
        if not self.update_timer.isActive():
            self.update_timer.start(1000)  # Update every 1 second
        
        print(f"DEBUG: EventBridge initialized for {total_files} files to {destinations}")
    
    def emit(self, event_type: str, payload: dict) -> None:
        """Handle events from Rust engine with thread-safe EventBridge routing"""
        # CRITICAL FIX: Route file.complete events to DIT data collector
        if event_type == 'file.complete':
            dit_collector = get_dit_collector()
            dit_collector.handle_file_complete_event(payload)
            print(f"🎯 DIT COLLECTOR: Captured file.complete event for {payload.get('filename', 'unknown')}")
        
        # CRITICAL FIX: Route job progress events to DIT collector for stats
        elif event_type in ['job.progress', 'job_progress', 'progress_update']:
            dit_collector = get_dit_collector()
            dit_collector.update_job_stats({
                'total_bytes': payload.get('total_bytes', 0),
                'copied_bytes': payload.get('copied_bytes', payload.get('bytes_copied', 0)),
                'total_files': payload.get('total_files', 0),
                'completed_files': payload.get('completed_files', payload.get('files_completed', 0)),
                'elapsed_time': payload.get('elapsed', payload.get('elapsed_time', 0)),
                'current_speed': payload.get('speed_mbps', payload.get('speed', 0)),
                'peak_speed': max(dit_collector.job_stats.get('peak_speed', 0), payload.get('speed_mbps', payload.get('speed', 0)))
            })
        
        # Log destination events for debugging
        if 'dest' in event_type.lower() or 'destination' in event_type.lower():
            print(f"🔍 RustEventSink.emit() DESTINATION EVENT: type='{event_type}', payload={payload}")
        
        # Log file completion events for debugging
        elif 'completed' in event_type.lower() or event_type.lower().endswith('.completed'):
            print(f"🔍 RustEventSink.emit() COMPLETION EVENT: type='{event_type}', payload={payload}")
        
        # Log periodic job progress events (less verbose)
        elif 'progress' in event_type.lower() or 'job' in event_type.lower():
            # Only log every 20th progress event to avoid spam
            if not hasattr(self, '_progress_event_counter'):
                self._progress_event_counter = 0
            self._progress_event_counter += 1
            if self._progress_event_counter % 20 == 0:
                print(f"🔍 RustEventSink.emit() PROGRESS EVENT (every 20th): type='{event_type}', payload_keys={list(payload.keys())}")
        
        # Route all events through EventBridge (thread-safe)
        self.event_bridge.emit_event(event_type, payload)
        
        # Check for destination completion to trigger immediate reports
        self._check_destination_completion(event_type, payload)
        
        # Handle file record updates for comprehensive tracking
        normalized_type = self._normalize_event_type(event_type)
        if normalized_type == 'file.started':
            self._add_file_started(payload)
        elif normalized_type == 'file.progress':
            self._update_file_record(payload)
        elif normalized_type == 'file.completed':
            self._mark_file_completed(payload)
    
    def _normalize_event_type(self, event_type: str) -> str:
        """Normalize various event type formats to standard names"""
        event_type = event_type.lower().strip()
        
        # File lifecycle events  
        if event_type in ['file.started', 'file_started', 'filestarted']:
            return 'file.started'
        elif event_type in ['file.progress', 'file_progress', 'fileprogress']:
            return 'file.progress'
        elif event_type in ['file.completed', 'file_completed', 'filecompleted', 'file.complete', 'file_complete', 'filecomplete']:
            return 'file.completed'
        
        # Job progress events  
        elif event_type in ['job.progress', 'job_progress', 'jobprogress', 'progress_update']:
            return 'job.progress'
        elif event_type in ['job.start', 'job_start', 'jobstart']:
            return 'job.start'
        elif event_type in ['job.started', 'job_started', 'jobstarted']:
            return 'job.started'
        
        # Destination events
        elif event_type in ['dest_progress', 'destination_progress']:
            return 'dest.progress'
        elif event_type in ['dest.completed', 'dest_completed', 'destination_completed']:
            return 'dest.completed'
        
        return event_type
    
    # REMOVED: Duplicate _update_file_record method - less comprehensive than the one below
    # The correct _update_file_record method is defined later with better progress tracking
    
    def _add_file_started(self, payload: dict) -> None:
        """Add file record when transfer starts"""
        filename = payload.get('filename', payload.get('file_id', 'unknown_file'))
        
        if filename not in self._file_records:
            self._file_records[filename] = {
                'filename': filename,
                'source_path': payload.get('source_path', ''),
                'destination_path': payload.get('destination_path', ''),
                'size': payload.get('file_bytes', payload.get('total_bytes', payload.get('file_size', 0))),
                'size_bytes': payload.get('file_bytes', payload.get('total_bytes', payload.get('file_size', 0))),
                'transfer_status': 'IN_PROGRESS',
                'verification_status': 'PENDING',
                'checksum_algorithm': 'xxHash64BE',
                'source_checksum': '',
                'destination_checksum': '',
                'transfer_speed_mbps': 0.0,
                'transfer_duration_s': 0.0,
                'status': 'in_progress',
                'start_time': time.time(),
                'error_message': ''
            }
            print(f"DEBUG: 📂 Added file record for: {filename}")

    def _update_file_record(self, payload: dict) -> None:
        """Update file record with progress information"""
        filename = payload.get('filename', payload.get('file_id', 'unknown_file'))
        
        # Ensure file record exists - create if missing  
        if filename not in self._file_records:
            self._add_file_started(payload)
        
        file_record = self._file_records[filename]
        
        # Update progress information (CRITICAL FIX: Handle Rust engine field names)
        if 'file_bytes_copied' in payload:
            bytes_copied = payload['file_bytes_copied']
            file_record['bytes_copied'] = bytes_copied  # CRITICAL FIX: Actually update bytes_copied field!
            total_bytes = file_record['size']
            if total_bytes > 0:
                file_record['progress_percent'] = (bytes_copied / total_bytes) * 100.0
        elif 'bytes_copied' in payload:  # Fallback for legacy format
            bytes_copied = payload['bytes_copied']
            file_record['bytes_copied'] = bytes_copied
            total_bytes = file_record['size']
            if total_bytes > 0:
                file_record['progress_percent'] = (bytes_copied / total_bytes) * 100.0
        
        # Update transfer speed if available
        if 'speed_mbps' in payload:
            file_record['transfer_speed_mbps'] = payload['speed_mbps']
    
    def _mark_file_completed(self, payload: dict) -> None:
        """Mark file as completed in records with comprehensive data"""
        filename = payload.get('filename', payload.get('file_id', 'unknown_file'))
        
        # Ensure file record exists
        if filename not in self._file_records:
            self._add_file_started(payload)
        
        file_record = self._file_records[filename]
        
        # CRITICAL FIX: Ensure bytes_copied is set to full file size for completed files
        if 'file_bytes' in payload:
            file_record['size'] = payload['file_bytes']
            file_record['bytes_copied'] = payload['file_bytes']  # Full file copied
        elif file_record.get('size', 0) > 0:
            file_record['bytes_copied'] = file_record['size']  # Use existing size
        
        file_record['transfer_status'] = 'COMPLETED'
        file_record['verification_status'] = 'PASS'  
        file_record['status'] = 'completed'  # This is the key field for DIT reports!
        file_record['transfer_duration_s'] = time.time() - file_record['start_time']
        file_record['progress_percent'] = 100.0  # Explicitly set to 100% for completed files
        
        # Add hash information from payload if available
        if 'source_checksum' in payload:
            file_record['source_checksum'] = payload['source_checksum']
        if 'destination_checksum' in payload:
            file_record['destination_checksum'] = payload['destination_checksum']
        if 'checksum' in payload:
            file_record['source_checksum'] = payload['checksum']
            file_record['destination_checksum'] = payload['checksum']
        
        # Handle hash values from Rust engine (NEW FORMAT)
        if 'source_hash' in payload:
            file_record['source_checksum'] = payload['source_hash']
        if 'dest_hash' in payload:
            file_record['destination_checksum'] = payload['dest_hash'] 
        if 'hash_algorithm' in payload:
            file_record['hash_algorithm'] = payload['hash_algorithm']
        if 'verification_passed' in payload:
            file_record['verification_status'] = 'PASS' if payload['verification_passed'] else 'FAIL'
            
        # Debug hash capture
        hash_info = f"source: {file_record.get('source_checksum', 'N/A')}, dest: {file_record.get('destination_checksum', 'N/A')}"
        print(f"DEBUG: Hash captured for {filename}: {hash_info}")
        
        print(f"DEBUG: ✅ Marked file COMPLETED: {filename} (status: {file_record['status']})")
    
    def _periodic_update(self) -> None:
        """Periodic update for UI refresh (thread-safe)"""
        # This runs on the main thread via QTimer
        snapshot = self.event_bridge.get_current_snapshot()
        if snapshot:
            # Update file records with current progress
            for dest_path, dest_metrics in snapshot.destinations.items():
                # Update transfer speeds in file records
                for filename in self._file_records:
                    if self._file_records[filename]['transfer_status'] == 'IN_PROGRESS':
                        elapsed = time.time() - self._file_records[filename]['start_time']
                        if elapsed > 0:
                            bytes_copied = self._file_records[filename]['bytes_copied']
                            self._file_records[filename]['transfer_speed'] = bytes_copied / elapsed / (1024 * 1024)
    
    
    
    def __call__(self, event_type: str, payload: dict) -> None:
        """Handle events from Rust engine - fallback for callable interface"""
        self.emit(event_type, payload)
    
    # Legacy compatibility methods for existing code
    def get_file_records(self) -> List[Dict[str, Any]]:
        """Get file records for report generation (legacy compatibility)"""
        return list(self._file_records.values())
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive stats (legacy compatibility)"""
        # Get stats from EventBridge
        bridge_stats = self.event_bridge.get_comprehensive_stats()
        
        # Merge with file records
        bridge_stats['files'] = self.get_file_records()
        return bridge_stats
    
    def start_safe_timers(self) -> None:
        """Start timers safely from main thread"""
        if not self.update_timer.isActive():
            self.update_timer.start(1000)
    
    @pyqtSlot()
    def _stop_timers_on_ui_thread(self):
        """Stop timers on UI thread - thread-safe"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            print("DEBUG: RustEventSink update timer stopped on UI thread")
    
    def stop_safe_timers(self) -> None:
        """Stop timers safely from any thread"""
        try:
            # Use QMetaObject.invokeMethod for thread-safe timer operations
            QMetaObject.invokeMethod(
                self, "_stop_timers_on_ui_thread", 
                Qt.ConnectionType.QueuedConnection
            )
        except Exception as e:
            print(f"DEBUG: Error stopping RustEventSink timers safely: {e}")
    
    def reset_for_new_job(self) -> None:
        """Reset for new transfer job with thread-safe cleanup"""
        # Stop timers safely
        self.stop_safe_timers()
        
        # Reset EventBridge
        self.event_bridge.reset_for_new_job()
        
        # Clear file records and destination completion tracking
        self._file_records.clear()
        self._completed_destinations.clear()
        self._last_destination_check.clear()
    
    def _trigger_destination_report(self, dest_path: str) -> None:
        """Trigger immediate report generation for a completed destination"""
        print(f"📊 Triggering immediate DIT report for destination: {dest_path}")
        
        # This will be connected to the controls for actual report generation
        # For now, just emit the signal - controls will handle the actual report generation
        pass
    
