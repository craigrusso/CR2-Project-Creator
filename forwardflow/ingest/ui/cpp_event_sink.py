#!/usr/bin/env python3
"""
C++ Event Sink Wrapper
Converts C++ engine events to Python-readable format for the UI
"""

import ctypes
import time
from typing import Dict, Any, Optional
from .qt_safe_bridge import emit_event


class CppEventSink:
    """Wrapper that converts C++ engine events to Python format"""
    
    def __init__(self):
        self.job_id = None
        self.job_start_time = None
        
        # Event throttling to prevent UI freezing
        self.last_progress_update = 0
        self.progress_throttle_ms = 100  # Update progress max every 100ms
        self.last_file_update = 0
        self.file_throttle_ms = 500      # Update file progress max every 500ms
        
        # Track current job stats
        self.current_job_stats = {
            'total_bytes': 0,
            'bytes_copied': 0,
            'total_files': 0,
            'files_completed': 0,
            'start_time': None,
            'current_speed': 0.0
        }
        
    def __call__(self, event_type: str, payload) -> None:
        """Convert C++ event to Python format and emit through bridge"""
        try:
            # Check if event should be throttled
            if self._should_throttle_event(event_type):
                return
                
            # Convert C++ payload to Python dict
            python_payload = self._convert_cpp_payload(event_type, payload)
            if python_payload:
                # Update our internal stats tracking
                self._update_internal_stats(event_type, python_payload)
                
                # Emit the event through the bridge
                emit_event(event_type, python_payload)
                print(f"DEBUG: C++ event converted and emitted: {event_type}")
            else:
                print(f"DEBUG: C++ event skipped (no payload): {event_type}")
                
        except Exception as e:
            print(f"DEBUG: Error in C++ event sink for {event_type}: {e}")
            import traceback
            traceback.print_exc()
    
    def _should_throttle_event(self, event_type: str) -> bool:
        """Check if event should be throttled to prevent UI freezing"""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        if event_type == "job.progress":
            if current_time - self.last_progress_update < self.progress_throttle_ms:
                return True
            self.last_progress_update = current_time
            return False
            
        elif event_type == "file.progress":
            if current_time - self.last_file_update < self.file_throttle_ms:
                return True
            self.last_file_update = current_time
            return False
            
        # Never throttle important events
        return False
    
    def _convert_cpp_payload(self, event_type: str, payload) -> Optional[Dict[str, Any]]:
        """Convert C++ payload to Python dictionary"""
        try:
            if event_type == "job.started":
                return self._convert_job_started(payload)
            elif event_type == "job.progress":
                return self._convert_job_progress(payload)
            elif event_type == "job.completed":
                return self._convert_job_completed(payload)
            elif event_type == "job.cancelled":
                return self._convert_job_cancelled(payload)
            elif event_type == "job.error":
                return self._convert_job_error(payload)
            elif event_type == "file.started":
                return self._convert_file_started(payload)
            elif event_type == "file.completed":
                return self._convert_file_completed(payload)
            elif event_type == "file.progress":
                return self._convert_file_progress(payload)
            elif event_type == "dest.progress":
                return self._convert_dest_progress(payload)
            elif event_type == "dest.warning":
                return self._convert_dest_warning(payload)
            else:
                print(f"DEBUG: Unknown event type: {event_type}")
                return None
                
        except Exception as e:
            print(f"DEBUG: Error converting payload for {event_type}: {e}")
            return None
    
    def _convert_job_started(self, payload) -> Dict[str, Any]:
        """Convert job started payload from C++ struct"""
        try:
            # The C++ engine sends a struct with total_bytes, total_files, job_id
            # We need to access the raw memory as the correct C++ types
            if payload:
                # Cast to the expected C++ struct layout
                # struct JobStartedPayload { size_t total_bytes; int total_files; const char* job_id; }
                total_bytes = ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents.value
                total_files = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_int)).contents.value
                
                self.current_job_stats['total_bytes'] = total_bytes
                self.current_job_stats['total_files'] = total_files
                self.current_job_stats['start_time'] = time.time()
                
                return {
                    "total_bytes": total_bytes,
                    "total_files": total_files,
                    "job_id": self.job_id or "unknown"
                }
            else:
                return {
                    "total_bytes": 0,
                    "total_files": 0,
                    "job_id": "unknown"
                }
        except Exception as e:
            print(f"DEBUG: Error converting job_started: {e}")
            return {"total_bytes": 0, "total_files": 0, "job_id": "unknown"}
    
    def _convert_job_progress(self, payload) -> Dict[str, Any]:
        """Convert job progress payload from C++ struct"""
        try:
            if payload:
                # struct JobProgressPayload { size_t bytes_copied; size_t total_bytes; int files_completed; int total_files; double elapsed; double speed_mbps; }
                bytes_copied = ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents.value
                total_bytes = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)).contents.value
                files_completed = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_int)).contents.value
                total_files = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t) + ctypes.sizeof(ctypes.c_int), ctypes.POINTER(ctypes.c_int)).contents.value
                elapsed = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t) + 2 * ctypes.sizeof(ctypes.c_int), ctypes.POINTER(ctypes.c_double)).contents.value
                speed_mbps = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t) + 2 * ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_double), ctypes.POINTER(ctypes.c_double)).contents.value
                
                # Update internal stats
                self.current_job_stats['bytes_copied'] = bytes_copied
                self.current_job_stats['files_completed'] = files_completed
                self.current_job_stats['current_speed'] = speed_mbps
                
                return {
                    "bytes_copied": bytes_copied,
                    "total_bytes": total_bytes,
                    "files_completed": files_completed,
                    "total_files": total_files,
                    "elapsed": elapsed,
                    "speed_mbps": speed_mbps
                }
            else:
                return {"bytes_copied": 0, "total_bytes": 0, "files_completed": 0, "total_files": 0}
        except Exception as e:
            print(f"DEBUG: Error converting job_progress: {e}")
            return {"bytes_copied": 0, "total_bytes": 0, "files_completed": 0, "total_files": 0}
    
    def _convert_job_completed(self, payload) -> Dict[str, Any]:
        """Convert job completed payload from C++ struct"""
        try:
            if payload:
                # struct JobCompletedPayload { size_t bytes_copied; size_t total_bytes; double elapsed; double speed_mbps; }
                bytes_copied = ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents.value
                total_bytes = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)).contents.value
                elapsed = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_double)).contents.value
                speed = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t) + ctypes.sizeof(ctypes.c_double), ctypes.POINTER(ctypes.c_double)).contents.value
                
                return {
                    "bytes_copied": bytes_copied,
                    "total_bytes": total_bytes,
                    "elapsed": elapsed,
                    "speed": speed
                }
            else:
                return {"bytes_copied": 0, "total_bytes": 0, "elapsed": 0.0, "speed": 0.0}
        except Exception as e:
            print(f"DEBUG: Error converting job_completed: {e}")
            return {"bytes_copied": 0, "total_bytes": 0, "elapsed": 0.0, "speed": 0.0}
    
    def _convert_job_cancelled(self, payload) -> Dict[str, Any]:
        """Convert job cancelled payload from C++ struct"""
        try:
            if payload:
                # struct JobCancelledPayload { size_t bytes_copied; size_t total_bytes; double elapsed; double cancelled_at; }
                bytes_copied = ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents.value
                total_bytes = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)).contents.value
                elapsed = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_double)).contents.value
                cancelled_at = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_size_t)).contents) + 2 * ctypes.sizeof(ctypes.c_size_t) + ctypes.sizeof(ctypes.c_double), ctypes.POINTER(ctypes.c_double)).contents.value
                
                return {
                    "bytes_copied": bytes_copied,
                    "total_bytes": total_bytes,
                    "elapsed": elapsed,
                    "cancelled_at": cancelled_at
                }
            else:
                return {"bytes_copied": 0, "total_bytes": 0, "elapsed": 0.0, "cancelled_at": 0.0}
        except Exception as e:
            print(f"DEBUG: Error converting job_cancelled: {e}")
            return {"bytes_copied": 0, "total_bytes": 0, "elapsed": 0.0, "cancelled_at": 0.0}
    
    def _convert_job_error(self, payload) -> Dict[str, Any]:
        """Convert job error payload from C++ struct"""
        try:
            if payload:
                # struct JobErrorPayload { const char* error; }
                error_ptr = ctypes.cast(payload, ctypes.POINTER(ctypes.c_char_p)).contents.value
                error_msg = ctypes.string_at(error_ptr).decode('utf-8') if error_ptr else "Unknown error"
                return {"error": error_msg}
            else:
                return {"error": "Unknown error occurred"}
        except Exception as e:
            print(f"DEBUG: Error converting job_error: {e}")
            return {"error": "Unknown error occurred"}
    
    def _convert_file_started(self, payload) -> Dict[str, Any]:
        """Convert file started payload from C++ struct"""
        try:
            if payload:
                # struct FileStartedPayload { const char* filename; size_t file_size; }
                filename_ptr = ctypes.cast(payload, ctypes.POINTER(ctypes.c_char_p)).contents.value
                filename = ctypes.string_at(filename_ptr).decode('utf-8') if filename_ptr else "unknown"
                file_size = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_char_p)).contents) + ctypes.sizeof(ctypes.c_char_p), ctypes.POINTER(ctypes.c_size_t)).contents.value
                
                return {
                    "filename": filename,
                    "file_size": file_size
                }
            else:
                return {"filename": "unknown", "file_size": 0}
        except Exception as e:
            print(f"DEBUG: Error converting file_started: {e}")
            return {"filename": "unknown", "file_size": 0}
    
    def _convert_file_completed(self, payload) -> Dict[str, Any]:
        """Convert file completed payload from C++ struct"""
        try:
            if payload:
                # struct FileCompletedPayload { const char* filename; size_t bytes; }
                filename_ptr = ctypes.cast(payload, ctypes.POINTER(ctypes.c_char_p)).contents.value
                filename = ctypes.string_at(filename_ptr).decode('utf-8') if filename_ptr else "unknown"
                bytes_copied = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_char_p)).contents) + ctypes.sizeof(ctypes.c_char_p), ctypes.POINTER(ctypes.c_size_t)).contents.value
                
                return {
                    "filename": filename,
                    "bytes_copied": bytes_copied
                }
            else:
                return {"filename": "unknown", "bytes_copied": 0}
        except Exception as e:
            print(f"DEBUG: Error converting file_completed: {e}")
            return {"filename": "unknown", "bytes_copied": 0}
    
    def _convert_file_progress(self, payload) -> Dict[str, Any]:
        """Convert file progress payload from C++ struct using PyBind11 bindings"""
        try:
            print(f"DEBUG: _convert_file_progress called with payload type: {type(payload)}")
            print(f"DEBUG: _convert_file_progress payload value: {payload}")
            print(f"DEBUG: _convert_file_progress payload repr: {repr(payload)}")

            if payload:
                # payload is now a PyBind11-exposed FileProgressPayload object
                # We can access its fields directly
                filename = payload.filename if payload.filename else "unknown"
                bytes_copied = payload.bytes_copied
                total_bytes = payload.total_bytes
                progress_percent = payload.progress_percent
                
                print(f"DEBUG: Successfully converted file_progress: {filename} - {bytes_copied}/{total_bytes} bytes ({progress_percent:.1f}%)")
                
                return {
                    "filename": filename,
                    "bytes_copied": bytes_copied,
                    "total_bytes": total_bytes,
                    "progress_percent": progress_percent
                }
            else:
                return {"filename": "unknown", "bytes_copied": 0, "total_bytes": 0, "progress_percent": 0.0}
        except Exception as e:
            print(f"DEBUG: Error converting file_progress: {e}")
            import traceback
            traceback.print_exc()
            return {"filename": "unknown", "bytes_copied": 0, "total_bytes": 0, "progress_percent": 0.0}
    
    def _convert_dest_progress(self, payload) -> Dict[str, Any]:
        """Convert destination progress payload from C++ struct"""
        try:
            if payload:
                # struct DestProgressPayload { int dest_index; const char* dest_path; size_t bytes_copied; size_t total_bytes; int completed_files; int total_files; double current_speed_mbps; double elapsed_time; }
                dest_index = ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents.value
                dest_path_ptr = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int), ctypes.POINTER(ctypes.c_char_p)).contents.value
                dest_path = ctypes.string_at(dest_path_ptr).decode('utf-8') if dest_path_ptr else ""
                bytes_copied = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p), ctypes.POINTER(ctypes.c_size_t)).contents.value
                total_bytes = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p) + ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)).contents.value
                completed_files = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p) + 2 * ctypes.sizeof(ctypes.c_size_t), ctypes.POINTER(ctypes.c_int)).contents.value
                total_files = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p) + 2 * ctypes.sizeof(ctypes.c_size_t) + ctypes.sizeof(ctypes.c_int), ctypes.POINTER(ctypes.c_int)).contents.value
                current_speed = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p) + 2 * ctypes.sizeof(ctypes.c_size_t) + 2 * ctypes.sizeof(ctypes.c_int), ctypes.POINTER(ctypes.c_double)).contents.value
                elapsed_time = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p) + 2 * ctypes.sizeof(ctypes.c_size_t) + 2 * ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_double), ctypes.POINTER(ctypes.c_double)).contents.value
                
                return {
                    "dest_index": dest_index,
                    "dest_path": dest_path,
                    "bytes_copied": bytes_copied,
                    "total_bytes": total_bytes,
                    "completed_files": completed_files,
                    "total_files": total_files,
                    "current_speed_mbps": current_speed,
                    "elapsed_time": elapsed_time
                }
            else:
                return {"dest_index": 0, "dest_path": "", "bytes_copied": 0, "total_bytes": 0, "completed_files": 0, "total_files": 0, "current_speed_mbps": 0.0, "elapsed_time": 0.0}
        except Exception as e:
            print(f"DEBUG: Error converting dest_progress: {e}")
            return {"dest_index": 0, "dest_path": "", "bytes_copied": 0, "total_bytes": 0, "completed_files": 0, "total_files": 0, "current_speed_mbps": 0.0, "elapsed_time": 0.0}
    
    def _convert_dest_warning(self, payload) -> Dict[str, Any]:
        """Convert destination warning payload from C++ struct"""
        try:
            if payload:
                # struct DestWarningPayload { int dest_index; const char* dest_path; const char* warning_message; }
                dest_index = ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents.value
                dest_path_ptr = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int), ctypes.POINTER(ctypes.c_char_p)).contents.value
                dest_path = ctypes.string_at(dest_path_ptr).decode('utf-8') if dest_path_ptr else ""
                warning_ptr = ctypes.cast(ctypes.addressof(ctypes.cast(payload, ctypes.POINTER(ctypes.c_int)).contents) + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p)).contents.value
                warning_message = ctypes.string_at(warning_ptr).decode('utf-8') if warning_ptr else "Unknown warning"
                
                return {
                    "dest_index": dest_index,
                    "dest_path": dest_path,
                    "warning_message": warning_message
                }
            else:
                return {"dest_index": 0, "dest_path": "", "warning_message": "Unknown warning"}
        except Exception as e:
            print(f"DEBUG: Error converting dest_warning: {e}")
            return {"dest_index": 0, "dest_path": "", "warning_message": "Unknown warning"}
    
    def _update_internal_stats(self, event_type: str, payload: Dict[str, Any]):
        """Update internal stats tracking"""
        try:
            if event_type == "job.started":
                self.current_job_stats['total_bytes'] = payload.get('total_bytes', 0)
                self.current_job_stats['total_files'] = payload.get('total_files', 0)
                self.current_job_stats['start_time'] = time.time()
            elif event_type == "job.progress":
                self.current_job_stats['bytes_copied'] = payload.get('bytes_copied', 0)
                self.current_job_stats['files_completed'] = payload.get('files_completed', 0)
                self.current_job_stats['current_speed'] = payload.get('speed_mbps', 0.0)
        except Exception as e:
            print(f"DEBUG: Error updating internal stats: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current job statistics"""
        return self.current_job_stats.copy()
