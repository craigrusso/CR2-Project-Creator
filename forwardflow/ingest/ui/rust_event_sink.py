"""
Professional Rust Event Sink with EventBridge integration
Handles accurate multi-file progress tracking with thread-safe event routing
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QMetaObject, Qt, pyqtSlot
from .event_bridge import EventBridge
from .job_aggregator import JobSnapshot
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
        
        if normalized_type == 'dest.progress':
            dest_path = payload.get('dest_path', '')
            progress_percent = payload.get('progress_percent', 0)
            
            # Check if destination reached 100% completion
            if progress_percent >= 100.0 and dest_path and dest_path not in self._completed_destinations:
                print(f"🎯 DESTINATION COMPLETED: {dest_path} - Triggering immediate report generation")
                
                # Mark as completed
                self._completed_destinations.add(dest_path)
                
                # Emit custom signal for per-destination completion
                if hasattr(self, 'destination_completed'):
                    self.destination_completed.emit(dest_path)
                else:
                    # If signal doesn't exist, trigger report generation directly
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
        # Route all events through EventBridge (thread-safe)
        self.event_bridge.emit_event(event_type, payload)
        
        # Check for destination completion to trigger immediate reports
        self._check_destination_completion(event_type, payload)
        
        # Handle file record updates for legacy compatibility
        normalized_type = self._normalize_event_type(event_type)
        if normalized_type == 'file.progress':
            self._update_file_record(payload)
        elif normalized_type == 'file.completed':
            self._mark_file_completed(payload)
    
    def _normalize_event_type(self, event_type: str) -> str:
        """Normalize various event type formats to standard names"""
        event_type = event_type.lower().strip()
        
        # File progress events
        if event_type in ['file.progress', 'file_progress', 'fileprogress']:
            return 'file.progress'
        elif event_type in ['file.completed', 'file_completed', 'filecompleted']:
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
        
        return event_type
    
    def _update_file_record(self, payload: dict) -> None:
        """Update file records for reporting (legacy compatibility)"""
        filename = payload.get('filename', payload.get('file_id', 'unknown_file'))
        bytes_copied = payload.get('bytes_copied', 0)
        total_bytes = payload.get('total_bytes', 0)
        
        # Initialize file record if needed
        if filename not in self._file_records:
            self._file_records[filename] = {
                'filename': filename,
                'size': total_bytes,
                'bytes_copied': 0,
                'transfer_status': 'IN_PROGRESS',
                'verification_status': 'PENDING',
                'checksum_type': 'xxHash64',
                'source_checksum': '',
                'destination_checksum': '',
                'transfer_speed': 0.0,
                'transfer_duration': 0.0,
                'start_time': time.time()
            }
        
        # Update file record
        file_record = self._file_records[filename]
        file_record['bytes_copied'] = bytes_copied
        
        # Calculate transfer speed
        elapsed = time.time() - file_record['start_time']
        if elapsed > 0:
            file_record['transfer_speed'] = bytes_copied / elapsed / (1024 * 1024)  # MB/s
    
    def _mark_file_completed(self, payload: dict) -> None:
        """Mark file as completed in records (legacy compatibility)"""
        filename = payload.get('filename', payload.get('file_id', 'unknown_file'))
        
        if filename in self._file_records:
            file_record = self._file_records[filename]
            file_record['transfer_status'] = 'COMPLETED'
            file_record['verification_status'] = 'PASS'
            file_record['transfer_duration'] = time.time() - file_record['start_time']
    
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
    
