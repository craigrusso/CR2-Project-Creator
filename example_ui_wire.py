"""
Example UI event handling for the Rust high-performance engine.

This demonstrates how to safely wire the engine events to the UI
with proper Qt main thread marshaling.
"""

from typing import Dict, Any
from rust_engine_loader import get_engine

class ExampleUI:
    """Example UI class showing how to handle engine events safely"""
    
    def __init__(self):
        self.engine = get_engine()
        self.model = {
            'bytesCopied': 0,
            'totalBytes': 0,
            'completedFiles': 0,
            'totalFiles': 0,
            'avgSpeedMiBps': 0.0,
            'currentSpeedMiBps': 0.0,
            'peakSpeedMiBps': 0.0,
        }
        self.view = None  # Would be your actual UI view
        
        # Set up event handling
        self.engine.set_event_sink(self.on_event)
    
    def on_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Handle engine events safely on the Qt main thread.
        This method is called by the engine wrapper which ensures
        proper thread marshaling.
        """
        if event_type == "progress_update":
            # Update UI model/state here (Qt main thread already via wrapper)
            self.model['bytesCopied'] = payload.get("bytesCopied", 0)
            self.model['totalBytes'] = payload.get("totalBytes", 0)
            self.model['completedFiles'] = payload.get("completedFiles", 0)
            self.model['totalFiles'] = payload.get("totalFiles", 0)
            self.model['avgSpeedMiBps'] = payload.get("avgSpeedMiBps", 0.0)
            
            # Update UI view
            if self.view:
                self.view.repaint_progress(self.model)
                
        elif event_type == "file_progress":
            # Update individual file progress
            file_id = payload.get("fileId")
            if self.view and file_id:
                self.view.update_file_row(file_id, payload)
                
        elif event_type == "file_completed":
            # Mark file as completed
            filename = payload.get("filename")
            if self.view and filename:
                self.view.mark_file_done(filename)
                
        elif event_type == "dest_progress":
            # Update destination-specific progress
            dest_index = payload.get("dest_index", 0)
            if self.view:
                self.view.update_destination_progress(dest_index, payload)
    
    def start_copy_operation(self, job_config: Dict[str, Any]) -> None:
        """Start a copy operation with the engine"""
        try:
            # Create CopyJob object (would be done by your job creation logic)
            from rust_high_perf_engine import CopyJob
            job = CopyJob()
            job.source_paths = job_config.get('source_paths', [])
            job.destination_paths = job_config.get('destination_paths', [])
            job.job_id = job_config.get('job_id', 'unknown')
            # ... set other job parameters
            
            # Start the copy operation
            result = self.engine.copy_files(job)
            print(f"Copy operation completed: {result}")
            
        except Exception as e:
            print(f"Copy operation failed: {e}")

# Example usage:
if __name__ == "__main__":
    ui = ExampleUI()
    
    # Example job configuration
    job_config = {
        'source_paths': ['/path/to/source'],
        'destination_paths': ['/path/to/dest1', '/path/to/dest2'],
        'job_id': 'test_job_001'
    }
    
    # Start copy operation
    ui.start_copy_operation(job_config)
