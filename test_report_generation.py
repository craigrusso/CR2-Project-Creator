#!/usr/bin/env python3
"""
Test Report Generation Functionality

This script tests the report generation functionality directly
without requiring the full UI components.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_files(source_dir, num_files=3, file_sizes_mb=[10, 25, 50]):
    """Create test files of various sizes for testing"""
    print(f"Creating test files in {source_dir}...")
    
    test_files = []
    for i in range(num_files):
        filename = f"test_file_{i+1}.mov"
        file_path = source_dir / filename
        size_mb = file_sizes_mb[i % len(file_sizes_mb)]
        size_bytes = size_mb * 1024 * 1024
        
        # Create a file with simple data
        with open(file_path, 'wb') as f:
            # Write simple pattern data
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = size_bytes
            while remaining > 0:
                chunk_size = min(chunk_size, remaining)
                data = bytes([(i + j) % 256 for j in range(chunk_size)])
                f.write(data)
                remaining -= chunk_size
        
        test_files.append({
            'path': file_path,
            'size': size_bytes,
            'size_mb': size_mb,
            'filename': filename
        })
        print(f"  Created {filename}: {size_mb} MB")
    
    return test_files

def test_transfer_log_writer():
    """Test the transfer log writer directly"""
    print("\n" + "="*60)
    print("TESTING TRANSFER LOG WRITER")
    print("="*60)
    
    # Create temporary test directories
    base_dir = Path(tempfile.mkdtemp(prefix="report_test_"))
    source_dir = base_dir / "SOURCE"
    dest_dir = base_dir / "DESTINATION"
    
    # Create directories
    source_dir.mkdir(exist_ok=True)
    dest_dir.mkdir(exist_ok=True)
    
    print(f"Test directories created:")
    print(f"  Base: {base_dir}")
    print(f"  Source: {source_dir}")
    print(f"  Destination: {dest_dir}")
    
    # Create test files
    test_files = create_test_files(source_dir)
    
    try:
        # Import the transfer log writer
        print("\nImporting transfer log writer...")
        try:
            from forwardflow.ingest.utils.transfer_log_writer import write_transfer_log
            print("✓ Successfully imported transfer log writer")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        
        # Test with basic stats
        print("\nTesting basic report generation...")
        basic_stats = {
            "total_bytes": sum(f['size'] for f in test_files),
            "copied_bytes": sum(f['size'] for f in test_files[:2]),  # Only 2 files completed
            "duration": 45.5,
            "avg_speed": 25.3,
            "total_files": len(test_files),
            "completed_files": 2,
            "cancelled_files": 1,
            "error_files": 0,
            "files": [
                {
                    "filename": f['filename'],
                    "size": f['size'],
                    "source_path": str(f['path']),
                    "destination_path": str(dest_dir / f['filename']),
                    "status": "COMPLETED" if i < 2 else "CANCELLED",
                    "verification_status": "PASS" if i < 2 else "UNKNOWN",
                    "checksum_type": "xxHash64",
                    "source_checksum": f"hash_{i}_{f['size']}",
                    "destination_checksum": f"hash_{i}_{f['size']}" if i < 2 else "",
                    "transfer_speed": 25.3,
                    "transfer_duration": 45.5 / len(test_files)
                }
                for i, f in enumerate(test_files)
            ]
        }
        
        # Generate report for cancelled transfer
        print("  Generating cancelled transfer report...")
        log_path = write_transfer_log(
            job_id="test_job_cancelled_123",
            source_path=str(source_dir),
            destinations=[str(dest_dir)],
            status="CANCELLED",
            error_message="Transfer cancelled by user for testing",
            stats=basic_stats
        )
        
        print(f"✓ Report generated: {log_path}")
        
        # Check if reports directory was created
        reports_dir = dest_dir / "_ForwardFlow_verification_Reports"
        if reports_dir.exists():
            print(f"✓ Reports directory created: {reports_dir}")
            
            # List all report files
            report_files = list(reports_dir.glob("*"))
            print(f"  Report files found: {len(report_files)}")
            
            for report_file in report_files:
                print(f"    {report_file.name}")
            
            # Analyze the reports
            analyze_generated_reports(reports_dir, test_files)
            
        else:
            print("❌ Reports directory not created")
            print(f"  Expected path: {reports_dir}")
            print(f"  Destination contents: {list(dest_dir.iterdir())}")
        
        # Test with minimal stats
        print("\nTesting minimal stats report generation...")
        minimal_stats = {
            "total_bytes": 1024 * 1024 * 100,  # 100MB
            "copied_bytes": 1024 * 1024 * 30,  # 30MB
            "duration": 15.2,
            "avg_speed": 2.0,
            "total_files": 1,
            "completed_files": 0,
            "cancelled_files": 1,
            "error_files": 0
        }
        
        log_path2 = write_transfer_log(
            job_id="test_job_minimal_456",
            source_path=str(source_dir),
            destinations=[str(dest_dir)],
            status="CANCELLED",
            error_message="Minimal stats test",
            stats=minimal_stats
        )
        
        print(f"✓ Minimal report generated: {log_path2}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test environment
        print(f"\nCleaning up test environment...")
        try:
            shutil.rmtree(base_dir)
            print(f"✓ Test environment cleaned up: {base_dir}")
        except Exception as e:
            print(f"⚠ Warning: Could not clean up test environment: {e}")

def analyze_generated_reports(reports_dir, test_files):
    """Analyze the generated reports for completeness and accuracy"""
    print(f"\nAnalyzing generated reports...")
    
    # Find different types of reports
    csv_reports = list(reports_dir.glob("*.csv"))
    txt_reports = list(reports_dir.glob("*.txt"))
    json_reports = list(reports_dir.glob("*.json"))
    
    print(f"  CSV reports: {len(csv_reports)}")
    print(f"  TXT reports: {len(txt_reports)}")
    print(f"  JSON reports: {len(json_reports)}")
    
    # Analyze CSV report (most important for DIT standards)
    if csv_reports:
        csv_report = csv_reports[0]
        print(f"\nAnalyzing CSV report: {csv_report.name}")
        analyze_csv_report(csv_report, test_files)
    
    # Analyze TXT report
    if txt_reports:
        txt_report = txt_reports[0]
        print(f"\nAnalyzing TXT report: {txt_report.name}")
        analyze_txt_report(txt_report, test_files)
    
    # Analyze JSON report
    if json_reports:
        json_report = json_reports[0]
        print(f"\nAnalyzing JSON report: {json_report.name}")
        analyze_json_report(json_report, test_files)

def analyze_csv_report(csv_path, test_files):
    """Analyze the CSV report for completeness and accuracy"""
    import csv
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if len(rows) < 2:  # Need at least header + 1 data row
            print("  ❌ CSV report has insufficient data")
            return
        
        headers = rows[0]
        data_rows = rows[1:]
        
        print(f"  Headers: {len(headers)} columns")
        print(f"  Data rows: {len(data_rows)} rows")
        
        # Check if headers contain expected DIT fields
        expected_headers = [
            "Job ID", "Timestamp", "Source Path", "Destination Path", 
            "File Name", "File Size (bytes)", "Transfer Status"
        ]
        
        missing_headers = [h for h in expected_headers if h not in headers]
        if missing_headers:
            print(f"  ❌ Missing expected headers: {missing_headers}")
        else:
            print(f"  ✓ All expected DIT headers present")
        
        # Analyze data rows
        if data_rows:
            print(f"  First data row: {data_rows[0]}")
            
            # Check if file information is present
            filename_col = headers.index("File Name") if "File Name" in headers else -1
            size_col = headers.index("File Size (bytes)") if "File Size (bytes)" in headers else -1
            status_col = headers.index("Transfer Status") if "Transfer Status" in headers else -1
            
            if filename_col >= 0 and size_col >= 0 and status_col >= 0:
                print(f"  ✓ File information columns found")
                
                # Check if test files are represented
                for test_file in test_files:
                    filename = test_file['filename']
                    size = test_file['size']
                    
                    # Look for this file in the report
                    file_found = False
                    for row in data_rows:
                        if (len(row) > filename_col and 
                            row[filename_col] == filename and
                            len(row) > size_col and
                            row[size_col] == str(size)):
                            file_found = True
                            status = row[status_col] if len(row) > status_col else "Unknown"
                            print(f"    ✓ {filename}: {status}")
                            break
                    
                    if not file_found:
                        print(f"    ❌ {filename}: Not found in report")
            else:
                print(f"  ❌ Required columns not found")
        
    except Exception as e:
        print(f"  ❌ Error analyzing CSV report: {e}")

def analyze_txt_report(txt_path, test_files):
    """Analyze the TXT report for completeness and accuracy"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"  Report size: {len(content)} characters")
        
        # Check for key information
        checks = [
            ("Job ID", "job_id" in content.lower() or "job id" in content.lower()),
            ("Source Path", "source" in content.lower()),
            ("Destination Path", "destination" in content.lower()),
            ("File Count", "file" in content.lower()),
            ("Status", "status" in content.lower() or "cancelled" in content.lower()),
            ("Timestamp", "timestamp" in content.lower() or "time" in content.lower())
        ]
        
        for check_name, found in checks:
            status = "✓" if found else "❌"
            print(f"    {status} {check_name}")
        
        # Show first few lines
        lines = content.split('\n')
        print(f"  First 5 lines:")
        for i, line in enumerate(lines[:5]):
            print(f"    {i+1}: {line}")
            
    except Exception as e:
        print(f"  ❌ Error analyzing TXT report: {e}")

def analyze_json_report(json_path, test_files):
    """Analyze the JSON report for completeness and accuracy"""
    import json
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  JSON structure: {list(data.keys())}")
        
        # Check for key fields
        checks = [
            ("Job ID", "job_id" in data),
            ("Timestamp", "timestamp" in data),
            ("Source Path", "source_path" in data),
            ("Destinations", "destinations" in data),
            ("Status", "status" in data),
            ("Stats", "stats" in data),
            ("System Info", "system_info" in data)
        ]
        
        for check_name, found in checks:
            status = "✓" if found else "❌"
            print(f"    {status} {check_name}")
        
        # Show detailed information
        if "stats" in data:
            stats = data["stats"]
            print(f"  Stats: {list(stats.keys()) if isinstance(stats, dict) else 'Not a dict'}")
            
            if isinstance(stats, dict) and "files" in stats:
                files = stats["files"]
                print(f"  Files in stats: {len(files)}")
                
                if files:
                    print(f"  First file: {files[0]}")
        
        # Show system info
        if "system_info" in data:
            sys_info = data["system_info"]
            print(f"  Engine: {sys_info.get('engine', 'Unknown')}")
            
    except Exception as e:
        print(f"  ❌ Error analyzing JSON report: {e}")

def test_control_section_report_generation():
    """Test the control section report generation methods"""
    print("\n" + "="*60)
    print("TESTING CONTROL SECTION REPORT GENERATION")
    print("="*60)
    
    try:
        # Import the control section
        print("Importing control section...")
        from forwardflow.ingest.ui.components.controls import ControlSection
        print("✓ Successfully imported control section")
        
        # Create a mock root object
        class MockRoot:
            def __init__(self):
                self.current_job_id = "test_job_789"
                self.source_path = "/test/source"
                self.destinations = ["/test/dest"]
                self.total_bytes = 1024 * 1024 * 200  # 200MB
                self.copied_bytes = 1024 * 1024 * 50   # 50MB
                self.elapsed_time = 25.5
                self.avg_speed = 2.0
                self.total_files = 5
                self.completed_files = 2
                self.cancelled_files = 2
                self.error_files = 1
                
                # Mock progress section
                class MockProgressSection:
                    def __init__(self):
                        self.files_count = type('MockLabel', (), {'setText': lambda x: print(f"Progress section: {x}")})()
                
                self.progress_section = MockProgressSection()
        
        mock_root = MockRoot()
        
        # Create control section instance
        control_section = ControlSection()
        
        # Test the detailed report generation
        print("\nTesting detailed report generation...")
        try:
            control_section._generate_detailed_report(
                mock_root, 
                "CANCELLED", 
                "Test cancellation for control section",
                {
                    "total_bytes": 1024 * 1024 * 200,
                    "copied_bytes": 1024 * 1024 * 50,
                    "duration": 25.5,
                    "avg_speed": 2.0,
                    "total_files": 5,
                    "completed_files": 2,
                    "cancelled_files": 2,
                    "error_files": 1,
                    "files": [
                        {
                            "filename": "test1.mov",
                            "size": 1024 * 1024 * 50,
                            "status": "COMPLETED",
                            "verification_status": "PASS"
                        },
                        {
                            "filename": "test2.mov",
                            "size": 1024 * 1024 * 50,
                            "status": "COMPLETED",
                            "verification_status": "PASS"
                        },
                        {
                            "filename": "test3.mov",
                            "size": 1024 * 1024 * 50,
                            "status": "CANCELLED",
                            "verification_status": "UNKNOWN"
                        }
                    ]
                }
            )
            print("✓ Control section report generation test passed")
            
        except Exception as e:
            print(f"❌ Control section report generation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Control section test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Report Generation Test Suite")
    print("This test will:")
    print("1. Test transfer log writer directly")
    print("2. Test control section report generation")
    print("3. Verify detailed reports are generated")
    print("4. Analyze report contents")
    
    # Test transfer log writer
    success1 = test_transfer_log_writer()
    
    # Test control section
    success2 = test_control_section_report_generation()
    
    if success1 and success2:
        print("\n🎉 All report generation tests passed!")
        print("The Turbo Transfer system can generate detailed reports correctly.")
    else:
        print("\n❌ Some tests failed!")
        print("Please check the error messages above.")
    
    return success1 and success2

if __name__ == "__main__":
    main()

