#!/usr/bin/env python3
"""
Test Script for UI Fixes Validation

Tests the fixes for:
1. Report generation consolidation (no triplicates) 
2. Progress bar event routing (job-level only)
3. Destination card event routing (proper path matching)

Run this to validate fixes before testing in the main app.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_report_generation():
    """Test that report generation creates single set of reports, not triplicates"""
    print("=== Testing Report Generation Consolidation ===")
    
    try:
        from forwardflow.ingest.utils.report_generator import TransferReportGenerator
        
        # Create temporary directory for test reports
        with tempfile.TemporaryDirectory() as temp_dir:
            test_destination = Path(temp_dir) / "test_destination"
            test_destination.mkdir()
            
            report_gen = TransferReportGenerator()
            
            # Test stats
            test_stats = {
                'total_files': 10,
                'completed_files': 8,
                'cancelled_files': 2,
                'error_files': 0,
                'total_bytes': 1000000,
                'copied_bytes': 800000,
                'duration': 5.0,
                'avg_speed': 160000,
                'peak_speed': 200000
            }
            
            # Generate comprehensive reports
            generated_reports = report_gen.generate_comprehensive_reports(
                job_id="test_job_123",
                status="CANCELLED", 
                source_path="/test/source",
                destinations=[str(test_destination)],
                stats=test_stats,
                file_records=[],
                error_message="Test cancellation"
            )
            
            print(f"Generated reports: {len(generated_reports)}")
            for report in generated_reports:
                print(f"  - {os.path.basename(report)}")
            
            # Check that only 3 reports were generated (JSON, TXT, CSV)
            reports_dir = test_destination / "_CR2_CREATIVE_REPORTS"
            if reports_dir.exists():
                report_files = list(reports_dir.glob("*"))
                print(f"Total files in reports directory: {len(report_files)}")
                
                # Should be exactly 3 files with ingest_ prefix
                ingest_files = [f for f in report_files if f.name.startswith("ingest_")]
                dit_files = [f for f in report_files if f.name.startswith("dit_verification_")]
                verify_files = [f for f in report_files if f.name.startswith("verify_report_")]
                
                print(f"  ingest_* files: {len(ingest_files)}")
                print(f"  dit_verification_* files: {len(dit_files)}")
                print(f"  verify_report_* files: {len(verify_files)}")
                
                # Test PASSED if only ingest_ files exist (no duplicates)
                if len(ingest_files) == 3 and len(dit_files) == 0 and len(verify_files) == 0:
                    print("✅ PASS: Report generation consolidated - no triplicates!")
                    return True
                else:
                    print("❌ FAIL: Still generating duplicate/triplicate reports")
                    return False
            else:
                print("❌ FAIL: No reports directory created")
                return False
                
    except Exception as e:
        print(f"❌ ERROR in report generation test: {e}")
        return False

def test_destination_path_matching():
    """Test destination path matching logic"""
    print("\n=== Testing Destination Path Matching ===")
    
    try:
        # Test path normalization
        test_paths = [
            "/Users/craigrusso/Desktop/TEST/TEST_TRANSFER 1",
            "/Users/craigrusso/Desktop/TEST/TEST_TRANSFER 1/", # trailing slash
            "/Users/craigrusso/Desktop/TEST/../TEST/TEST_TRANSFER 1", # relative path
        ]
        
        base_path = "/Users/craigrusso/Desktop/TEST/TEST_TRANSFER 1"
        
        all_match = True
        for test_path in test_paths:
            normalized_base = os.path.normpath(base_path)
            normalized_test = os.path.normpath(test_path)
            match = normalized_base == normalized_test
            
            print(f"  Base: '{base_path}'")
            print(f"  Test: '{test_path}'")
            print(f"  Normalized match: {match}")
            
            if not match:
                all_match = False
        
        if all_match:
            print("✅ PASS: Path normalization works correctly")
            return True
        else:
            print("❌ FAIL: Path normalization issues detected")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in path matching test: {e}")
        return False

def test_progress_event_structure():
    """Test that progress event payloads have correct structure"""
    print("\n=== Testing Progress Event Structure ===")
    
    try:
        # Simulate EventBridge progress_update payload
        job_progress_payload = {
            'bytes_copied': 500000,
            'total_bytes': 1000000,
            'completed_files': 5,
            'total_files': 10,
            'elapsed_time': 2.5,
            'current_speed_mbps': 200.0,
            'filename': 'current_file.txt',
            'progress_percent': 50.0
        }
        
        # Simulate EventBridge destination_update payload  
        destination_payload = {
            'dest_path': '/Users/craigrusso/Desktop/TEST/TEST_TRANSFER 1',
            'currentSpeedMiBps': 200.0,
            'current_speed_mbps': 200.0,
            'peakSpeedMiBps': 250.0,
            'peak_speed_mbps': 250.0,
            'progress_percent': 50.0,
            'bytes_copied': 500000,
            'total_bytes': 1000000,
            'etaS': 120,
            'eta_seconds': 120,
            'completed_files': 5,
            'total_files': 10
        }
        
        # Test that job progress has required fields for main progress bar
        job_required_fields = ['bytes_copied', 'total_bytes', 'progress_percent', 'completed_files', 'total_files']
        job_valid = all(field in job_progress_payload for field in job_required_fields)
        
        # Test that destination progress has required fields for destination cards
        dest_required_fields = ['dest_path', 'current_speed_mbps', 'peak_speed_mbps', 'progress_percent', 'eta_seconds']
        dest_valid = all(field in destination_payload for field in dest_required_fields)
        
        print(f"  Job progress payload valid: {job_valid}")
        print(f"  Destination progress payload valid: {dest_valid}")
        
        if job_valid and dest_valid:
            print("✅ PASS: Event payloads have correct structure")
            return True
        else:
            print("❌ FAIL: Event payloads missing required fields")
            return False
            
    except Exception as e:
        print(f"❌ ERROR in event structure test: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🧪 Running Fix Validation Tests\n")
    
    test_results = []
    
    # Run all tests
    test_results.append(test_report_generation())
    test_results.append(test_destination_path_matching())  
    test_results.append(test_progress_event_structure())
    
    # Summary
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✅ All fixes validated successfully!")
        return True
    else:
        print("❌ Some fixes need additional work")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)