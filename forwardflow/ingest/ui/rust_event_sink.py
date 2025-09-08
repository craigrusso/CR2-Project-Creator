"""
Simplified Rust Event Sink
Only handles simple progress updates for UI
"""

from PyQt6.QtCore import QObject, pyqtSignal


class RustEventSink(QObject):
    """Simplified event sink for Rust engine - only handles UI progress updates"""
    
    # Simple progress update signal
    progress_update = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        print("DEBUG: Simplified RustEventSink initialized")
    
    def emit(self, event_type: str, payload: dict) -> None:
        """Handle events from Rust engine - called by engine via emit() method"""
        print(f"DEBUG: RustEventSink.emit called with event: {event_type}")
        print(f"DEBUG: Event payload: {payload}")
        
        if event_type in ['job.progress', 'progress_update', 'dest_progress', 'file_progress']:
            # Convert Rust engine events to format expected by progress section
            converted_payload = self._convert_rust_event(event_type, payload)
            self.progress_update.emit(converted_payload)
        else:
            print(f"DEBUG: Unknown event type: {event_type}")
    
    def __call__(self, event_type: str, payload: dict) -> None:
        """Handle events from Rust engine - fallback for callable interface"""
        self.emit(event_type, payload)
    
    def _convert_rust_event(self, event_type: str, payload: dict) -> dict:
        """Convert Rust engine events to format expected by progress section"""
        print(f"DEBUG: Converting event {event_type} with payload: {payload}")
        
        if event_type == 'job.progress':
            # Calculate elapsed time if not provided
            import time
            if not hasattr(self, '_job_start_time'):
                self._job_start_time = time.time()
            elapsed_time = time.time() - self._job_start_time
            
            # Calculate speed if we have bytes and time
            bytes_copied = payload.get('bytes_copied', 0)
            speed_mbps = 0.0
            if elapsed_time > 0 and bytes_copied > 0:
                speed_mbps = (bytes_copied / (1024 * 1024)) / elapsed_time
            
            # Convert job progress to format expected by progress section
            converted = {
                'job_id': payload.get('job_id', 'unknown'),
                'progress_percent': payload.get('progress_percent', 0.0),
                'completed_files': payload.get('files_copied', payload.get('completed_files', 0)),
                'total_files': payload.get('total_files', 0),
                'bytes_copied': bytes_copied,
                'total_bytes': payload.get('total_bytes', 0),
                'current_speed_mbps': payload.get('speed_mbps', payload.get('current_speed_mbps', speed_mbps)),
                'elapsed_time': payload.get('elapsed_time', elapsed_time),
                'filename': payload.get('filename', ''),  # Add filename for current file display
            }
            print(f"DEBUG: Converted job.progress to: {converted}")
            return converted
        elif event_type == 'dest_progress':
            # Convert dest_progress to file_progress format
            return {
                'filename': payload.get('destPath', 'Unknown'),
                'bytes_copied': payload.get('bytesCopied', 0),
                'total_bytes': payload.get('totalBytes', 0),
                'progress_percent': (payload.get('bytesCopied', 0) / max(payload.get('totalBytes', 1), 1)) * 100,
                'completed_files': payload.get('completedFiles', 0),
                'total_files': payload.get('totalFiles', 0),
                'current_speed_mbps': payload.get('currentSpeedMiBps', 0.0),
                'peak_speed_mbps': payload.get('peakSpeedMiBps', 0.0),
                'elapsed_time': payload.get('elapsedS', 0.0)
            }
        elif event_type == 'file_progress':
            # Already in correct format
            return payload
        else:
            # Default progress_update format
            return payload