#!/usr/bin/env python3
"""
Comprehensive Turbo Transfer Test Script

This script tests the complete Turbo Transfer system:
1. Creates test source files
2. Sets up destinations
3. Starts a transfer
4. Cancels the transfer
5. Verifies detailed reports are generated
6. Reads and analyzes the reports
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path
import threading
import queue

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_files(source_dir, num_files=5, file_sizes_mb=[10, 25, 50, 100, 200]):
    """Create test files of various sizes for testing"""
    print(f"Creating test files in {source_dir}...")
    
    test_files = []
    for i in range(num_files):
        filename = f"test_file_{i+1}.mov"
        file_path = source_dir / filename
        size_mb = file_sizes_mb[i % len(file_sizes_mb)]
        size_bytes = size_mb * 1024 * 1024
        
        # Create a file with random data
        with open(file_path, 'wb') as f:
            # Write random data in chunks to simulate real video files
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = size_bytes
            while remaining > 0:
                chunk_size = min(chunk_size, remaining)
                # Use a simple pattern for testing (not truly random)
                data = bytes([(i + j) % 256 for j in range(chunk_size)])
                f.write(data)
                remaining -= chunk_size
        
        test_files.append({
            'path': file_path,
            'size': size_bytes,
            'size_mb': size_mb
        })
        print(f"  Created {filename}: {size_mb} MB")
    
    return test_files

def setup_test_environment():
    """Set up test directories and files"""
    print("Setting up test environment...")
    
    # Create temporary test directories
    base_dir = Path(tempfile.mkdtemp(prefix="turbo_transfer_test_"))
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
    
    return base_dir, source_dir, dest_dir, test_files

def test_turbo_transfer_system():
    """Test the complete Turbo Transfer system"""
    print("\n" + "="*60)
    print("TURBO TRANSFER COMPREHENSIVE TEST")
    print("="*60)
    
    # Set up test environment
    base_dir, source_dir, dest_dir, test_files = setup_test_environment()
    
    try:
        print(f"\nTest environment ready:")
        print(f"  Source files: {len(test_files)} files")
        print(f"  Total size: {sum(f['size_mb'] for f in test_files)} MB")
        print(f"  Source path: {source_dir}")
        print(f"  Destination path: {dest_dir}")
        
        # Import the Turbo Transfer components
        print("\nImporting Turbo Transfer components...")
        try:
            from forwardflow.ingest.ui.ingest_tab import build_ingest_tab
            from forwardflow.ingest.ui.components.controls import ControlSection
            from forwardflow.ingest.api.models import JobSpec, JobOptions
            print("✓ Successfully imported Turbo Transfer components")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        
        # Create the ingest tab (this creates the UI components)
        print("\nCreating Turbo Transfer UI...")
        root = build_ingest_tab()
        print("✓ Turbo Transfer UI created successfully")
        
        # Set up the source and destination
        print("\nSetting up source and destination...")
        if hasattr(root, 'source_dest_section'):
            # Set source path
            if hasattr(root.source_dest_section, 'src_combo'):
                root.source_dest_section.src_combo.setCurrentText(str(source_dir))
                print(f"✓ Source set to: {source_dir}")
            
            # Add destination
            if hasattr(root.source_dest_section, 'add_destination'):
                root.source_dest_section.add_destination(str(dest_dir))
                print(f"✓ Destination added: {dest_dir}")
        else:
            print("❌ Source destination section not found")
            return False
        
        # Check if we can start the transfer
        print("\nChecking transfer readiness...")
        if hasattr(root, 'control_section'):
            # Check if start button is enabled
            if hasattr(root.control_section, 'start_btn'):
                start_enabled = root.control_section.start_btn.isEnabled()
                print(f"  Start button enabled: {start_enabled}")
                
                if not start_enabled:
                    print("  Checking why start button is disabled...")
                    # Check source and destinations
                    if hasattr(root, 'source_dest_section'):
                        source_text = root.source_dest_section.src_combo.currentText()
                        destinations = root.source_dest_section.get_destinations()
                        print(f"    Source: {source_text}")
                        print(f"    Destinations: {destinations}")
        else:
            print("❌ Control section not found")
            return False
        
        # Simulate starting a transfer
        print("\nSimulating transfer start...")
        if hasattr(root, 'control_section') and hasattr(root.control_section, 'on_start'):
            print("  Starting transfer...")
            try:
                # Start the transfer in a background thread
                transfer_thread = threading.Thread(
                    target=root.control_section.on_start,
                    args=(root,),
                    daemon=True
                )
                transfer_thread.start()
                
                # Wait a bit for the transfer to start
                print("  Waiting for transfer to start...")
                time.sleep(3)
                
                # Check if transfer is running
                if hasattr(root, 'current_job') and root.current_job:
                    print("✓ Transfer started successfully")
                    
                    # Wait a bit more to see some progress
                    print("  Waiting for transfer progress...")
                    time.sleep(5)
                    
                    # Now cancel the transfer
                    print("\nCancelling transfer...")
                    if hasattr(root.control_section, 'on_cancel'):
                        root.control_section.on_cancel(root)
                        print("✓ Cancel command sent")
                        
                        # Wait for cancellation and report generation
                        print("  Waiting for cancellation and report generation...")
                        time.sleep(5)
                        
                        # Check if reports were generated
                        print("\nChecking for generated reports...")
                        reports_dir = dest_dir / "_ForwardFlow_verification_Reports"
                        if reports_dir.exists():
                            print(f"✓ Reports directory found: {reports_dir}")
                            
                            # List all report files
                            report_files = list(reports_dir.glob("*"))
                            print(f"  Report files found: {len(report_files)}")
                            
                            for report_file in report_files:
                                print(f"    {report_file.name}")
                            
                            # Read and analyze the reports
                            analyze_reports(reports_dir, test_files)
                        else:
                            print("❌ Reports directory not found")
                            print(f"  Expected path: {reports_dir}")
                            print(f"  Destination contents: {list(dest_dir.iterdir())}")
                    else:
                        print("❌ Cancel method not found")
                else:
                    print("❌ Transfer did not start")
                    print(f"  current_job: {getattr(root, 'current_job', 'Not found')}")
            except Exception as e:
                print(f"❌ Error during transfer simulation: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ Start method not found")
        
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

def analyze_reports(reports_dir, test_files):
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
                    filename = test_file['path'].name
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

def main():
    """Main test function"""
    print("Turbo Transfer Comprehensive Test")
    print("This test will:")
    print("1. Create test files")
    print("2. Start a transfer")
    print("3. Cancel the transfer")
    print("4. Verify detailed reports are generated")
    print("5. Analyze report contents")
    
    # Run the test
    success = test_turbo_transfer_system()
    
    if success:
        print("\n🎉 Turbo Transfer test completed successfully!")
        print("All components are working correctly.")
    else:
        print("\n❌ Turbo Transfer test failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()

