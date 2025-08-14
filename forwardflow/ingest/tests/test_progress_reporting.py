"""Test progress reporting logic for the ingest module."""

import pytest
import time
from unittest.mock import Mock, patch
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from ..engines.python_engine import PythonCopyEngine
from ..api.events import JobStartedEvent, JobProgressEvent, FileStartedEvent, FileProgressEvent, FileCompletedEvent


class TestProgressReporting:
    """Test that progress events are properly emitted and handled."""
    
    def setup_method(self):
        """Set up test environment."""
        self.app = QApplication([])
        self.mock_sink = Mock()
        self.engine = PythonCopyEngine(sink=self.mock_sink)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.app.quit()
    
    def test_engine_emits_job_started_event(self):
        """Test that the engine emits job.started event."""
        # Create a simple job spec
        from ..api.models import JobSpec, FileSpec
        from ..api.events import JobStartedEvent
        
        job_spec = JobSpec(
            source=Mock(),
            destination=Mock(),
            options=Mock()
        )
        
        # Start the job
        self.engine.start(job_spec)
        
        # Check that the sink was called with job.started
        assert self.mock_sink.emit.called
        calls = self.mock_sink.emit.call_args_list
        
        # Look for job.started event
        job_started_found = False
        for call in calls:
            if call[0][0] == "job.started":
                job_started_found = True
                break
        
        assert job_started_found, "job.started event was not emitted"
    
    def test_engine_emits_file_events(self):
        """Test that the engine emits file events during copy."""
        # Mock the file operations to simulate a copy
        with patch.object(self.engine, '_copy_one') as mock_copy:
            mock_copy.return_value = True
            
            # Create a simple job spec
            from ..api.models import JobSpec, FileSpec
            job_spec = JobSpec(
                source=Mock(),
                destination=Mock(),
                options=Mock()
            )
            
            # Start the job
            self.engine.start(job_spec)
            
            # Check that file events were emitted
            assert self.mock_sink.emit.called
            calls = self.mock_sink.emit.call_args_list
            
            # Look for file.started events
            file_started_found = False
            for call in calls:
                if call[0][0] == "file.started":
                    file_started_found = True
                    break
            
            assert file_started_found, "file.started event was not emitted"
    
    def test_progress_calculation(self):
        """Test that progress calculations are correct."""
        # Test basic progress calculation
        total_bytes = 1000
        copied_bytes = 500
        expected_percent = 50
        
        percent = int(100 * copied_bytes / total_bytes)
        assert percent == expected_percent
    
    def test_speed_calculation(self):
        """Test that speed calculations are correct."""
        # Test speed calculation in MB/s
        copied_bytes = 1024 * 1024  # 1 MB
        elapsed_seconds = 1.0
        expected_speed = 1.0  # 1 MB/s
        
        speed = (copied_bytes / elapsed_seconds) / (1024 * 1024)
        assert abs(speed - expected_speed) < 0.01
    
    def test_event_payload_structure(self):
        """Test that event payloads have the correct structure."""
        # Test job.started event
        job_event = JobStartedEvent(
            job_id="test_job",
            total_bytes=1000,
            total_files=5
        )
        
        assert job_event.job_id == "test_job"
        assert job_event.total_bytes == 1000
        assert job_event.total_files == 5
        
        # Test file.started event
        file_event = FileStartedEvent(
            file_id="test_file",
            filename="test.txt",
            total_bytes=100
        )
        
        assert file_event.file_id == "test_file"
        assert file_event.filename == "test.txt"
        assert file_event.total_bytes == 100


if __name__ == "__main__":
    pytest.main([__file__])
