#!/usr/bin/env python3
"""
Comprehensive Test Suite for ForwardFlow Turbo Transfer System
Tests all acceptance criteria with 60+ file job simulation
"""

import sys
import os
import time
import random
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import threading
import uuid

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from forwardflow.ingest.ui.event_bridge import EventBridge
from forwardflow.ingest.ui.rust_event_sink import RustEventSink
from forwardflow.ingest.ui.job_aggregator import JobAggregator
from forwardflow.ingest.ui.event_schema import EventRouter, EventType
from forwardflow.ingest.utils.report_generator import TransferReportGenerator


class AcceptanceCriteriaValidator:
    """
    Validates all acceptance criteria for the comprehensive fix
    """
    
    def __init__(self):
        self.test_results = {}
        self.test_files = []
        self.temp_dirs = []
        
    def setup_test_environment(self) -> Dict[str, str]:
        """Setup test environment with 60+ files"""
        print("🔧 Setting up test environment...")
        
        # Create temporary directories
        source_dir = tempfile.mkdtemp(prefix="ff_test_source_")
        dest_dir1 = tempfile.mkdtemp(prefix="ff_test_dest1_")
        dest_dir2 = tempfile.mkdtemp(prefix="ff_test_dest2_")
        
        self.temp_dirs = [source_dir, dest_dir1, dest_dir2]
        
        # Create 64 test files of varying sizes
        total_files = 64
        file_sizes = [
            # Small files (1-10KB)
            *[random.randint(1024, 10240) for _ in range(20)],
            # Medium files (100KB - 1MB)
            *[random.randint(102400, 1048576) for _ in range(30)],
            # Large files (1-10MB)
            *[random.randint(1048576, 10485760) for _ in range(14)]
        ]
        
        source_path = Path(source_dir)
        for i in range(total_files):
            file_path = source_path / f"test_file_{i:03d}.bin"
            file_size = file_sizes[i]
            
            # Create file with random content
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
            
            self.test_files.append({
                'path': str(file_path),
                'name': file_path.name,
                'size': file_size,
                'index': i
            })
        
        print(f"✅ Created {total_files} test files totaling {sum(file_sizes) / 1024 / 1024:.1f} MB")
        
        return {
            'source': source_dir,
            'dest1': dest_dir1,
            'dest2': dest_dir2
        }
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("🧹 Cleaning up test environment...")
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Failed to cleanup {temp_dir}: {e}")
    
    def test_event_bridge_initialization(self) -> bool:
        """Test EventBridge initialization and auto-detection"""
        print("🔍 Testing EventBridge initialization...")
        
        try:
            # Test 1: EventBridge auto-initialization
            event_bridge = EventBridge()
            
            # Simulate early file.progress events before initialization
            test_events = [
                {
                    'type': 'file.progress',
                    'payload': {
                        'file_id': f'file_{i}',
                        'filename': f'test_file_{i:03d}.bin',
                        'bytes_copied': random.randint(1024, 10240),
                        'total_bytes': random.randint(10240, 102400),
                        'dest_path': '/test/dest1'
                    }
                }
                for i in range(5)
            ]
            
            # Send events before initialization
            for event in test_events:
                event_bridge.emit_event(event['type'], event['payload'])
            
            # Check buffering
            stats = event_bridge.get_event_statistics()
            buffered_count = stats['buffered_events']
            
            print(f"  ✓ Buffered {buffered_count} events before initialization")
            
            # Test auto-initialization
            if buffered_count >= 3:  # Auto-init threshold
                time.sleep(0.1)  # Allow auto-init to trigger
                stats_after = event_bridge.get_event_statistics()
                
                if stats_after['is_initialized']:
                    print("  ✅ Auto-initialization triggered successfully")
                    self.test_results['event_bridge_auto_init'] = True
                else:
                    print("  ❌ Auto-initialization failed to trigger")
                    self.test_results['event_bridge_auto_init'] = False
            
            # Test explicit initialization
            success = event_bridge.initialize_job(64, ['/test/dest1', '/test/dest2'])
            
            if success:
                print("  ✅ Explicit initialization successful")
                self.test_results['event_bridge_explicit_init'] = True
            else:
                print("  ❌ Explicit initialization failed")
                self.test_results['event_bridge_explicit_init'] = False
            
            # Test schema validation
            schema_info = event_bridge.get_event_schema_info()
            supported_types = len(schema_info['supported_types'])
            
            if supported_types > 20:  # Should have many supported event types
                print(f"  ✅ Comprehensive schema support: {supported_types} event types")
                self.test_results['event_schema_comprehensive'] = True
            else:
                print(f"  ❌ Limited schema support: {supported_types} event types")
                self.test_results['event_schema_comprehensive'] = False
            
            return True
            
        except Exception as e:
            print(f"  ❌ EventBridge test failed: {e}")
            self.test_results['event_bridge_test'] = False
            return False
    
    def test_job_aggregator_progress_tracking(self) -> bool:
        \"\"\"Test JobAggregator monotonic progress and metrics\"\"\"\n        print(\"📊 Testing JobAggregator progress tracking...\")\n        \n        try:\n            total_files = 64\n            destinations = ['/test/dest1', '/test/dest2']\n            \n            # Create JobAggregator\n            aggregator = JobAggregator(total_files, destinations)\n            \n            # Test 1: Monotonic progress validation\n            last_progress = 0.0\n            monotonic_violations = 0\n            \n            # Simulate file transfers with progress updates\n            for i in range(total_files):\n                file_id = f'file_{i:03d}'\n                total_bytes = random.randint(1024, 1048576)\n                dest_path = destinations[i % len(destinations)]\n                filename = f'test_file_{i:03d}.bin'\n                \n                # Simulate progressive transfer\n                for progress_fraction in [0.25, 0.5, 0.75, 1.0]:\n                    bytes_copied = int(total_bytes * progress_fraction)\n                    \n                    snapshot = aggregator.update_file_progress(\n                        file_id, bytes_copied, total_bytes, dest_path, filename\n                    )\n                    \n                    # Check monotonic progress\n                    if snapshot.job_progress_percent < last_progress:\n                        monotonic_violations += 1\n                        print(f\"    ⚠️ Progress regression: {last_progress:.1f}% → {snapshot.job_progress_percent:.1f}%\")\n                    \n                    last_progress = snapshot.job_progress_percent\n                \n                # Small delay for realistic timing\n                time.sleep(0.001)\n            \n            # Validate final state\n            final_snapshot = aggregator.get_current_snapshot()\n            \n            # Test Results\n            results = {\n                'monotonic_progress': monotonic_violations == 0,\n                'total_files_correct': final_snapshot.job_total_files == total_files,\n                'completed_files_correct': final_snapshot.job_completed_files == total_files,\n                'progress_100_percent': abs(final_snapshot.job_progress_percent - 100.0) < 0.1,\n                'destination_metrics': len(final_snapshot.destinations) == len(destinations),\n                'speed_calculations': final_snapshot.job_avg_mb_s > 0,\n                'eta_reasonable': final_snapshot.job_eta_seconds >= 0\n            }\n            \n            print(f\"    Monotonic progress: {'✅' if results['monotonic_progress'] else '❌'} ({monotonic_violations} violations)\")\n            print(f\"    Total files: {'✅' if results['total_files_correct'] else '❌'} ({final_snapshot.job_total_files}/{total_files})\")\n            print(f\"    Completed files: {'✅' if results['completed_files_correct'] else '❌'} ({final_snapshot.job_completed_files}/{total_files})\")\n            print(f\"    Final progress: {'✅' if results['progress_100_percent'] else '❌'} ({final_snapshot.job_progress_percent:.1f}%)\")\n            print(f\"    Destination metrics: {'✅' if results['destination_metrics'] else '❌'} ({len(final_snapshot.destinations)}/{len(destinations)})\")\n            print(f\"    Speed calculations: {'✅' if results['speed_calculations'] else '❌'} ({final_snapshot.job_avg_mb_s:.1f} MB/s)\")\n            print(f\"    ETA reasonable: {'✅' if results['eta_reasonable'] else '❌'} ({final_snapshot.job_eta_seconds:.1f}s)\")\n            \n            # Store results\n            self.test_results.update({\n                f'aggregator_{key}': value for key, value in results.items()\n            })\n            \n            return all(results.values())\n            \n        except Exception as e:\n            print(f\"  ❌ JobAggregator test failed: {e}\")\n            import traceback\n            traceback.print_exc()\n            return False\n    \n    def test_rust_event_sink_integration(self) -> bool:\n        \"\"\"Test RustEventSink integration with EventBridge\"\"\"\n        print(\"🔗 Testing RustEventSink integration...\")\n        \n        try:\n            # Create RustEventSink with EventBridge integration\n            event_sink = RustEventSink()\n            \n            # Test initialization\n            total_files = 64\n            destinations = ['/test/dest1', '/test/dest2']\n            event_sink.initialize_job(total_files, destinations)\n            \n            # Simulate events from Rust engine\n            test_events = [\n                {\n                    'type': 'file.progress',\n                    'payload': {\n                        'file_id': f'file_{i}',\n                        'filename': f'test_file_{i:03d}.bin',\n                        'bytes_copied': random.randint(1024, 10240),\n                        'total_bytes': random.randint(10240, 102400),\n                        'dest_path': destinations[i % len(destinations)]\n                    }\n                }\n                for i in range(10)\n            ]\n            \n            # Process events\n            for event in test_events:\n                event_sink.emit(event['type'], event['payload'])\n            \n            # Allow processing time\n            time.sleep(0.1)\n            \n            # Get comprehensive stats\n            stats = event_sink.get_comprehensive_stats()\n            file_records = event_sink.get_file_records()\n            \n            # Validate integration\n            results = {\n                'stats_available': stats['total_files'] > 0 or stats['total_bytes'] > 0,\n                'file_records_created': len(file_records) > 0,\n                'event_bridge_active': hasattr(event_sink, 'event_bridge') and event_sink.event_bridge is not None,\n                'timers_running': hasattr(event_sink, 'update_timer') and event_sink.update_timer.isActive()\n            }\n            \n            print(f\"    Stats available: {'✅' if results['stats_available'] else '❌'}\")\n            print(f\"    File records: {'✅' if results['file_records_created'] else '❌'} ({len(file_records)} records)\")\n            print(f\"    EventBridge integration: {'✅' if results['event_bridge_active'] else '❌'}\")\n            print(f\"    Timers active: {'✅' if results['timers_running'] else '❌'}\")\n            \n            # Store results\n            self.test_results.update({\n                f'event_sink_{key}': value for key, value in results.items()\n            })\n            \n            # Test cleanup\n            event_sink.reset_for_new_job()\n            \n            return all(results.values())\n            \n        except Exception as e:\n            print(f\"  ❌ RustEventSink test failed: {e}\")\n            import traceback\n            traceback.print_exc()\n            return False\n    \n    def test_report_generation(self, test_dirs: Dict[str, str]) -> bool:\n        \"\"\"Test comprehensive report generation\"\"\"\n        print(\"📋 Testing report generation...\")\n        \n        try:\n            # Create report generator\n            report_gen = TransferReportGenerator()\n            \n            # Create mock job data\n            job_id = f\"test_job_{uuid.uuid4().hex[:8]}\"\n            source_path = test_dirs['source']\n            destinations = [test_dirs['dest1'], test_dirs['dest2']]\n            \n            # Create comprehensive stats\n            total_bytes = sum(f['size'] for f in self.test_files)\n            stats = {\n                'total_bytes': total_bytes,\n                'copied_bytes': total_bytes,\n                'duration': 120.5,\n                'avg_speed': total_bytes / (1024 * 1024) / 120.5,\n                'peak_speed': (total_bytes / (1024 * 1024) / 120.5) * 1.5,\n                'total_files': len(self.test_files),\n                'completed_files': len(self.test_files),\n                'cancelled_files': 0,\n                'error_files': 0\n            }\n            \n            # Create file records\n            file_records = [\n                {\n                    'filename': f['name'],\n                    'size': f['size'],\n                    'bytes_copied': f['size'],\n                    'transfer_status': 'COMPLETED',\n                    'verification_status': 'PASS',\n                    'checksum_type': 'xxHash64',\n                    'source_checksum': f'hash_{i:08x}',\n                    'destination_checksum': f'hash_{i:08x}',\n                    'transfer_speed': random.uniform(10.0, 100.0),\n                    'transfer_duration': random.uniform(1.0, 10.0)\n                }\n                for i, f in enumerate(self.test_files)\n            ]\n            \n            # Generate comprehensive reports\n            generated_reports = report_gen.generate_comprehensive_reports(\n                job_id=job_id,\n                status=\"COMPLETED\",\n                source_path=source_path,\n                destinations=destinations,\n                stats=stats,\n                file_records=file_records\n            )\n            \n            # Validate reports\n            results = {\n                'reports_generated': len(generated_reports) > 0,\n                'cr2_subfolders_created': False,\n                'json_report_exists': False,\n                'txt_report_exists': False,\n                'csv_report_exists': False,\n                'report_content_valid': False\n            }\n            \n            # Check for _CR2_CREATIVE_REPORTS subfolders\n            for dest in destinations:\n                reports_dir = Path(dest) / \"_CR2_CREATIVE_REPORTS\"\n                if reports_dir.exists():\n                    results['cr2_subfolders_created'] = True\n                    \n                    # Check for different report formats\n                    json_files = list(reports_dir.glob(\"*.json\"))\n                    txt_files = list(reports_dir.glob(\"*.txt\"))\n                    csv_files = list(reports_dir.glob(\"*.csv\"))\n                    \n                    results['json_report_exists'] = len(json_files) > 0\n                    results['txt_report_exists'] = len(txt_files) > 0\n                    results['csv_report_exists'] = len(csv_files) > 0\n                    \n                    # Validate content of JSON report\n                    if json_files:\n                        try:\n                            import json\n                            with open(json_files[0], 'r') as f:\n                                report_data = json.load(f)\n                            \n                            content_valid = (\n                                report_data.get('job_id') == job_id and\n                                report_data.get('status') == 'COMPLETED' and\n                                len(report_data.get('files', [])) == len(self.test_files)\n                            )\n                            results['report_content_valid'] = content_valid\n                        except Exception as e:\n                            print(f\"    ⚠️ Error validating report content: {e}\")\n                    \n                    break\n            \n            print(f\"    Reports generated: {'✅' if results['reports_generated'] else '❌'} ({len(generated_reports)} reports)\")\n            print(f\"    CR2 subfolders: {'✅' if results['cr2_subfolders_created'] else '❌'}\")\n            print(f\"    JSON reports: {'✅' if results['json_report_exists'] else '❌'}\")\n            print(f\"    TXT reports: {'✅' if results['txt_report_exists'] else '❌'}\")\n            print(f\"    CSV reports: {'✅' if results['csv_report_exists'] else '❌'}\")\n            print(f\"    Content valid: {'✅' if results['report_content_valid'] else '❌'}\")\n            \n            # Store results\n            self.test_results.update({\n                f'report_{key}': value for key, value in results.items()\n            })\n            \n            return all(results.values())\n            \n        except Exception as e:\n            print(f\"  ❌ Report generation test failed: {e}\")\n            import traceback\n            traceback.print_exc()\n            return False\n    \n    def test_thread_safety(self) -> bool:\n        \"\"\"Test thread safety of timer management and event handling\"\"\"\n        print(\"🔒 Testing thread safety...\")\n        \n        try:\n            event_sink = RustEventSink()\n            event_sink.initialize_job(64, ['/test/dest1', '/test/dest2'])\n            \n            errors = []\n            \n            def worker_thread(thread_id: int):\n                \"\"\"Worker thread that generates events\"\"\"\n                try:\n                    for i in range(10):\n                        event_sink.emit('file.progress', {\n                            'file_id': f'thread_{thread_id}_file_{i}',\n                            'filename': f'thread_{thread_id}_file_{i}.bin',\n                            'bytes_copied': random.randint(1024, 10240),\n                            'total_bytes': random.randint(10240, 102400),\n                            'dest_path': '/test/dest1'\n                        })\n                        time.sleep(0.001)\n                except Exception as e:\n                    errors.append(f\"Thread {thread_id}: {e}\")\n            \n            # Start multiple threads\n            threads = []\n            for i in range(5):\n                t = threading.Thread(target=worker_thread, args=(i,))\n                threads.append(t)\n                t.start()\n            \n            # Wait for completion\n            for t in threads:\n                t.join()\n            \n            # Test safe timer operations\n            try:\n                event_sink.start_safe_timers()\n                event_sink.stop_safe_timers()\n                timer_safety = True\n            except Exception as e:\n                errors.append(f\"Timer safety: {e}\")\n                timer_safety = False\n            \n            results = {\n                'no_thread_errors': len(errors) == 0,\n                'timer_safety': timer_safety\n            }\n            \n            print(f\"    Thread safety: {'✅' if results['no_thread_errors'] else '❌'} ({len(errors)} errors)\")\n            print(f\"    Timer safety: {'✅' if results['timer_safety'] else '❌'}\")\n            \n            if errors:\n                for error in errors[:3]:  # Show first 3 errors\n                    print(f\"      ⚠️ {error}\")\n            \n            # Store results\n            self.test_results.update({\n                f'thread_safety_{key}': value for key, value in results.items()\n            })\n            \n            return all(results.values())\n            \n        except Exception as e:\n            print(f\"  ❌ Thread safety test failed: {e}\")\n            return False\n    \n    def run_comprehensive_test(self) -> Dict[str, Any]:\n        \"\"\"Run all acceptance criteria tests\"\"\"\n        print(\"\\n\" + \"=\"*60)\n        print(\"🚀 COMPREHENSIVE TURBO TRANSFER TEST SUITE\")\n        print(\"=\"*60)\n        \n        test_dirs = None\n        try:\n            # Setup\n            test_dirs = self.setup_test_environment()\n            \n            # Run all tests\n            tests = [\n                (\"EventBridge Initialization\", self.test_event_bridge_initialization),\n                (\"JobAggregator Progress Tracking\", self.test_job_aggregator_progress_tracking),\n                (\"RustEventSink Integration\", self.test_rust_event_sink_integration),\n                (\"Report Generation\", lambda: self.test_report_generation(test_dirs)),\n                (\"Thread Safety\", self.test_thread_safety)\n            ]\n            \n            overall_success = True\n            for test_name, test_func in tests:\n                print(f\"\\n🧪 {test_name}\")\n                success = test_func()\n                if not success:\n                    overall_success = False\n                    print(f\"  ❌ {test_name} FAILED\")\n                else:\n                    print(f\"  ✅ {test_name} PASSED\")\n            \n            # Summary\n            print(\"\\n\" + \"=\"*60)\n            print(\"📊 TEST SUMMARY\")\n            print(\"=\"*60)\n            \n            passed_tests = sum(1 for v in self.test_results.values() if v)\n            total_tests = len(self.test_results)\n            \n            print(f\"Total Tests: {total_tests}\")\n            print(f\"Passed: {passed_tests}\")\n            print(f\"Failed: {total_tests - passed_tests}\")\n            print(f\"Success Rate: {passed_tests/total_tests*100:.1f}%\")\n            \n            # Detailed results\n            print(\"\\nDetailed Results:\")\n            for test, result in self.test_results.items():\n                status = \"✅ PASS\" if result else \"❌ FAIL\"\n                print(f\"  {test}: {status}\")\n            \n            if overall_success:\n                print(\"\\n🎉 ALL ACCEPTANCE CRITERIA PASSED!\")\n            else:\n                print(\"\\n⚠️ Some acceptance criteria failed. Review results above.\")\n            \n            return {\n                'overall_success': overall_success,\n                'passed_tests': passed_tests,\n                'total_tests': total_tests,\n                'detailed_results': self.test_results\n            }\n            \n        finally:\n            # Cleanup\n            if test_dirs:\n                self.cleanup_test_environment()\n\n\nif __name__ == \"__main__\":\n    validator = AcceptanceCriteriaValidator()\n    results = validator.run_comprehensive_test()\n    \n    # Exit with appropriate code\n    sys.exit(0 if results['overall_success'] else 1)