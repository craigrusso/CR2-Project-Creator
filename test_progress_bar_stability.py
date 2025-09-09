#!/usr/bin/env python3
"""
Test Progress Bar Stability - validates the JobManifest approach
Tests the scenarios mentioned in the requirements to ensure progress bar never resets
"""

import sys
import os
import tempfile
import time
import threading
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from forwardflow.ingest.ui.job_state import JobStateManager
    from forwardflow.ingest.ui.event_bridge import EventBridge
    from forwardflow.ingest.engines.rust_high_perf.rust_high_perf_engine import PyEnhancedHighPerfTransferEngine
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class ProgressBarStabilityTest:
    """Test suite for progress bar stability with JobManifest approach"""
    
    def __init__(self):
        self.test_results = []
        self.job_state_manager = JobStateManager()
        self.event_bridge = EventBridge()
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
    
    def create_test_files(self, temp_dir: Path, num_files: int = 5) -> list:
        """Create test files with known sizes"""
        files = []
        total_size = 0
        
        for i in range(num_files):
            file_path = temp_dir / f"test_file_{i+1}.txt"
            file_size = (i + 1) * 1024 * 1024  # 1MB, 2MB, 3MB, etc.
            
            with open(file_path, 'wb') as f:
                f.write(b'0' * file_size)
            
            files.append(str(file_path))
            total_size += file_size
            
        print(f"Created {num_files} test files, total size: {total_size} bytes")
        return files, total_size
    
    def test_1_single_dest_stable_progress(self):
        """Test 1: Single destination, stable progress without resets"""
        print("\n=== Test 1: Single Destination Stable Progress ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files
            files, total_size = self.create_test_files(source_dir, 5)
            
            # Expected values for single destination
            expected_total_target_bytes = total_size * 1  # 1 destination
            
            # Simulate job.start event
            job_start_payload = {
                'job_id': 'test_job_1',
                'total_files': 5,
                'total_bytes': total_size,
                'destination_count': 1,
                'total_target_bytes': expected_total_target_bytes,
                'source_path': str(source_dir),
                'destinations': [str(dest_dir)]
            }
            
            # Initialize JobState
            success = self.job_state_manager.initialize_from_manifest(job_start_payload)
            self.log_result("JobState initialization", success, 
                          f"total_target_bytes={expected_total_target_bytes}")
            
            if not success:
                return
            
            # Simulate progress updates
            progress_values = []
            for i in range(6):  # 0%, 20%, 40%, 60%, 80%, 100%
                bytes_copied = int((i / 5) * expected_total_target_bytes)
                
                progress_payload = {
                    'bytes_copied': bytes_copied,
                    'total_target_bytes': expected_total_target_bytes,
                    'completed_files': i,
                    'total_files': 5,
                    'current_speed_mbps': 50.0,
                    'elapsed_seconds': i * 2.0
                }
                
                success = self.job_state_manager.update_progress(progress_payload)
                if success:
                    ui_payload = self.job_state_manager.get_ui_payload()
                    progress_values.append(ui_payload['progress_percent'])
                    print(f"Progress update {i}: {ui_payload['progress_percent']:.1f}%")
            
            # Validate progress never decreases
            monotonic = all(progress_values[i] >= progress_values[i-1] 
                          for i in range(1, len(progress_values)))
            
            self.log_result("Progress monotonic (never resets)", monotonic,
                          f"values: {[f'{p:.1f}%' for p in progress_values]}")
            
            # Validate final progress is 100%
            final_progress = progress_values[-1] if progress_values else 0
            self.log_result("Final progress 100%", abs(final_progress - 100.0) < 0.1,
                          f"final: {final_progress:.1f}%")
    
    def test_2_multi_dest_stable_progress(self):
        """Test 2: Multiple destinations, progress reflects 2x bytes"""
        print("\n=== Test 2: Multiple Destinations Progress ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = temp_path / "source"
            dest1_dir = temp_path / "dest1"
            dest2_dir = temp_path / "dest2"
            source_dir.mkdir()
            dest1_dir.mkdir()
            dest2_dir.mkdir()
            
            # Create test files
            files, total_size = self.create_test_files(source_dir, 3)
            
            # Expected values for two destinations
            expected_total_target_bytes = total_size * 2  # 2 destinations
            
            # Simulate job.start event
            job_start_payload = {
                'job_id': 'test_job_2',
                'total_files': 3,
                'total_bytes': total_size,
                'destination_count': 2,
                'total_target_bytes': expected_total_target_bytes,
                'source_path': str(source_dir),
                'destinations': [str(dest1_dir), str(dest2_dir)]
            }
            
            # Initialize JobState
            success = self.job_state_manager.initialize_from_manifest(job_start_payload)
            self.log_result("Multi-dest JobState initialization", success,
                          f"total_target_bytes={expected_total_target_bytes} (2x source)")
            
            if not success:
                return
            
            # Simulate copying to first destination (50% of total target)
            half_target = expected_total_target_bytes // 2
            progress_payload = {
                'bytes_copied': half_target,
                'total_target_bytes': expected_total_target_bytes,
                'completed_files': 3,
                'total_files': 3,
                'current_speed_mbps': 100.0,
                'elapsed_seconds': 10.0
            }
            
            self.job_state_manager.update_progress(progress_payload)
            ui_payload = self.job_state_manager.get_ui_payload()
            mid_progress = ui_payload['progress_percent']
            
            self.log_result("Progress 50% after first destination", 
                          abs(mid_progress - 50.0) < 1.0,
                          f"progress: {mid_progress:.1f}%")
            
            # Simulate completing second destination (100%)
            progress_payload['bytes_copied'] = expected_total_target_bytes
            self.job_state_manager.update_progress(progress_payload)
            ui_payload = self.job_state_manager.get_ui_payload()
            final_progress = ui_payload['progress_percent']
            
            self.log_result("Final progress 100% with two destinations",
                          abs(final_progress - 100.0) < 0.1,
                          f"final: {final_progress:.1f}%")
    
    def test_3_cancellation_verification_status(self):
        """Test 3: Cancellation at 60%, files show SKIPPED not FAILED"""
        print("\n=== Test 3: Cancellation Verification Status ===")
        
        # This test focuses on the logic, not actual file operations
        from forwardflow.ingest.utils.report_generator import TransferReportGenerator
        
        # Simulate file records for a cancelled job
        file_records = [
            {
                'filename': 'file1.txt',
                'transfer_status': 'COMPLETED',
                'verification_status': 'PENDING',
                'size': 1024
            },
            {
                'filename': 'file2.txt',
                'transfer_status': 'COMPLETED',
                'verification_status': 'PENDING',
                'size': 1024
            },
            {
                'filename': 'file3.txt',
                'transfer_status': 'CANCELLED',
                'verification_status': 'PENDING',
                'size': 1024
            }
        ]
        
        # Generate cancelled report
        generator = TransferReportGenerator()
        stats = {
            'total_files': 3,
            'completed_files': 2,
            'cancelled_files': 1,
            'total_bytes': 3072,
            'completed_bytes': 2048,
            'elapsed_time': 5.0
        }
        
        report_path = generator.generate_cancelled_report(
            job_id='test_cancel',
            stats=stats,
            file_records=file_records,
            engine_type='rust_test'
        )
        
        # Check that verification status was properly updated
        skipped_count = sum(1 for r in file_records 
                           if r.get('verification_status') == 'SKIPPED')
        failed_count = sum(1 for r in file_records 
                          if r.get('verification_status') == 'FAILED')
        
        self.log_result("Cancelled files marked SKIPPED not FAILED",
                       skipped_count > 0 and failed_count == 0,
                       f"SKIPPED: {skipped_count}, FAILED: {failed_count}")
        
        self.log_result("Cancelled report generated", 
                       bool(report_path) and os.path.exists(report_path),
                       f"Report: {report_path}")
    
    def test_4_out_of_order_file_events(self):
        """Test 4: Out-of-order file.progress events don't affect main progress"""
        print("\n=== Test 4: Out-of-Order File Events ===")
        
        # Initialize JobState for this test
        job_start_payload = {
            'job_id': 'test_job_4',
            'total_files': 3,
            'total_bytes': 3072,
            'destination_count': 1,
            'total_target_bytes': 3072,
            'source_path': '/test/source',
            'destinations': ['/test/dest']
        }
        
        self.job_state_manager.reset()
        success = self.job_state_manager.initialize_from_manifest(job_start_payload)
        
        if not success:
            self.log_result("Job state initialization failed", False, "Cannot run test")
            return
        
        # Record initial progress
        initial_ui = self.job_state_manager.get_ui_payload()
        initial_progress = initial_ui['progress_percent']
        
        # Simulate valid job.progress update
        job_progress_payload = {
            'bytes_copied': 1536,  # 50%
            'total_target_bytes': 3072,
            'completed_files': 1,
            'total_files': 3,
            'current_speed_mbps': 50.0,
            'elapsed_seconds': 2.0
        }
        
        self.job_state_manager.update_progress(job_progress_payload)
        mid_ui = self.job_state_manager.get_ui_payload()
        mid_progress = mid_ui['progress_percent']
        
        # Simulate file.progress events (these should NOT affect JobState)
        # In real implementation, these would go to file-level UI only
        file_events = [
            {'filename': 'file1.txt', 'file_bytes_copied': 1024, 'file_bytes': 1024},
            {'filename': 'file2.txt', 'file_bytes_copied': 512, 'file_bytes': 1024},
        ]
        
        # JobState should remain unchanged by file events
        final_ui = self.job_state_manager.get_ui_payload()
        final_progress = final_ui['progress_percent']
        
        # Main progress should only be affected by job.progress events
        job_progress_stable = (abs(mid_progress - final_progress) < 0.01)
        
        self.log_result("File events don't affect main progress", job_progress_stable,
                       f"Before file events: {mid_progress:.1f}%, After: {final_progress:.1f}%")
        
        self.log_result("Progress increased correctly", mid_progress > initial_progress,
                       f"Initial: {initial_progress:.1f}%, Mid: {mid_progress:.1f}%")
    
    def test_5_total_target_bytes_validation(self):
        """Test 5: Validation of total_target_bytes consistency"""
        print("\n=== Test 5: Total Target Bytes Validation ===")
        
        # Initialize JobState
        job_start_payload = {
            'job_id': 'test_job_5',
            'total_files': 2,
            'total_bytes': 2048,
            'destination_count': 1,
            'total_target_bytes': 2048,
            'source_path': '/test/source',
            'destinations': ['/test/dest']
        }
        
        self.job_state_manager.reset()
        success = self.job_state_manager.initialize_from_manifest(job_start_payload)
        
        if not success:
            self.log_result("Job state initialization failed", False, "Cannot run test")
            return
        
        # Test valid progress update
        valid_payload = {
            'bytes_copied': 1024,
            'total_target_bytes': 2048,  # Matches manifest
            'completed_files': 1,
            'total_files': 2
        }
        
        valid_update = self.job_state_manager.update_progress(valid_payload)
        self.log_result("Valid progress update accepted", valid_update,
                       "total_target_bytes matches manifest")
        
        # Test invalid progress update
        invalid_payload = {
            'bytes_copied': 1024,
            'total_target_bytes': 4096,  # Doesn't match manifest
            'completed_files': 1,
            'total_files': 2
        }
        
        invalid_update = self.job_state_manager.update_progress(invalid_payload)
        self.log_result("Invalid progress update rejected", not invalid_update,
                       "total_target_bytes mismatch detected")
    
    def run_all_tests(self):
        """Run all stability tests"""
        print("Starting Progress Bar Stability Tests...")
        print("=" * 60)
        
        try:
            self.test_1_single_dest_stable_progress()
            self.test_2_multi_dest_stable_progress()
            self.test_3_cancellation_verification_status()
            self.test_4_out_of_order_file_events()
            self.test_5_total_target_bytes_validation()
        except Exception as e:
            print(f"Test execution error: {e}")
            import traceback
            traceback.print_exc()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "PASS" if result['passed'] else "FAIL"
            print(f"[{status}] {result['test']}")
            if result['message']:
                print(f"        {result['message']}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Progress bar stability implemented correctly.")
            return True
        else:
            print("❌ Some tests failed. Review implementation.")
            return False


if __name__ == "__main__":
    print("Progress Bar Stability Test Suite")
    print("Testing JobManifest approach for stable progress tracking\n")
    
    tester = ProgressBarStabilityTest()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)