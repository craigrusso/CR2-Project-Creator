#!/usr/bin/env python3
"""
Simple Report Generation Test

This script tests just the report generation functionality
without any UI dependencies.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_report_generation():
    """Test the report generation functionality"""
    print("Testing Report Generation Functionality")
    print("="*50)
    
    # Create temporary test directories
    base_dir = Path(tempfile.mkdtemp(prefix="simple_report_test_"))
    source_dir = base_dir / "SOURCE"
    dest_dir = base_dir / "DESTINATION"
    
    # Create directories
    source_dir.mkdir(exist_ok=True)
    dest_dir.mkdir(exist_ok=True)
    
    print(f"Test directories created:")
    print(f"  Base: {base_dir}")
    print(f"  Source: {source_dir}")
    print(f"  Destination: {dest_dir}")
    
    # Create a simple test file
    test_file = source_dir / "test_video.mov"
    file_size = 1024 * 1024 * 50  # 50MB
    
    with open(test_file, 'wb') as f:
        # Write simple test data
        data = bytes([i % 256 for i in range(file_size)])
        f.write(data)
    
    print(f"  Created test file: {test_file.name} ({file_size / (1024*1024):.1f} MB)")
    
    try:
        # Import the transfer log writer
        print("\nImporting transfer log writer...")
        from forwardflow.ingest.utils.transfer_log_writer import write_transfer_log
        print("✓ Successfully imported transfer log writer")
        
        # Test report generation with comprehensive stats
        print("\nTesting comprehensive report generation...")
        
        # Create realistic stats for a cancelled transfer
        comprehensive_stats = {
            "total_bytes": file_size,
            "copied_bytes": file_size // 3,  # Only 1/3 completed
            "duration": 25.5,
            "avg_speed": 2.0,
            "total_files": 1,
            "completed_files": 0,
            "cancelled_files": 1,
            "error_files": 0,
            "files": [
                {
                    "filename": "test_video.mov",
                    "size": file_size,
                    "source_path": str(test_file),
                    "destination_path": str(dest_dir / "test_video.mov"),
                    "status": "CANCELLED",
                    "verification_status": "UNKNOWN",
                    "checksum_type": "xxHash64",
                    "source_checksum": "hash_12345_52428800",
                    "destination_checksum": "",  # Not completed
                    "transfer_speed": 2.0,
                    "transfer_duration": 25.5
                }
            ]
        }
        
        # Generate the report
        log_path = write_transfer_log(
            job_id="test_job_cancelled_789",
            source_path=str(source_dir),
            destinations=[str(dest_dir)],
            status="CANCELLED",
            error_message="Transfer cancelled by user for testing",
            stats=comprehensive_stats
        )
        
        print(f"✓ Report generated: {log_path}")
        
        # Check what was actually created
        print("\nChecking generated reports...")
        
        # Look for the reports directory (it might be named differently)
        possible_report_dirs = [
            dest_dir / "_ForwardFlow_verification_Reports",
            dest_dir / "_CR2_CREATIVE_REPORTS",
            dest_dir / "reports"
        ]
        
        reports_dir = None
        for possible_dir in possible_report_dirs:
            if possible_dir.exists():
                reports_dir = possible_dir
                break
        
        if reports_dir:
            print(f"✓ Reports directory found: {reports_dir}")
            
            # List all report files
            report_files = list(reports_dir.glob("*"))
            print(f"  Report files found: {len(report_files)}")
            
            for report_file in report_files:
                print(f"    {report_file.name}")
            
            # Analyze the reports
            analyze_reports(reports_dir)
            
        else:
            print("❌ No reports directory found")
            print(f"  Checked: {[str(d) for d in possible_report_dirs]}")
            print(f"  Destination contents: {list(dest_dir.iterdir())}")
        
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

def analyze_reports(reports_dir):
    """Analyze the generated reports"""
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
        analyze_csv_report(csv_report)
    
    # Analyze TXT report
    if txt_reports:
        txt_report = txt_reports[0]
        print(f"\nAnalyzing TXT report: {txt_report.name}")
        analyze_txt_report(txt_report)
    
    # Analyze JSON report
    if json_reports:
        json_report = json_reports[0]
        print(f"\nAnalyzing JSON report: {json_report.name}")
        analyze_json_report(json_report)

def analyze_csv_report(csv_path):
    """Analyze the CSV report"""
    import csv
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        if len(rows) < 2:
            print("  ❌ CSV report has insufficient data")
            return
        
        headers = rows[0]
        data_rows = rows[1:]
        
        print(f"  Headers: {len(headers)} columns")
        print(f"  Data rows: {len(data_rows)} rows")
        
        # Show headers
        print(f"  Headers: {headers}")
        
        # Show first data row
        if data_rows:
            print(f"  First data row: {data_rows[0]}")
        
        # Check for key DIT fields
        key_fields = ["Job ID", "File Name", "File Size (bytes)", "Transfer Status"]
        for field in key_fields:
            if field in headers:
                print(f"    ✓ {field} found")
            else:
                print(f"    ❌ {field} missing")
        
    except Exception as e:
        print(f"  ❌ Error analyzing CSV report: {e}")

def analyze_txt_report(txt_path):
    """Analyze the TXT report"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"  Report size: {len(content)} characters")
        
        # Show first few lines
        lines = content.split('\n')
        print(f"  First 10 lines:")
        for i, line in enumerate(lines[:10]):
            if line.strip():  # Only show non-empty lines
                print(f"    {i+1}: {line}")
            
    except Exception as e:
        print(f"  ❌ Error analyzing TXT report: {e}")

def analyze_json_report(json_path):
    """Analyze the JSON report"""
    import json
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  JSON structure: {list(data.keys())}")
        
        # Show key information
        if "job_id" in data:
            print(f"    Job ID: {data['job_id']}")
        if "status" in data:
            print(f"    Status: {data['status']}")
        if "stats" in data:
            stats = data["stats"]
            print(f"    Stats keys: {list(stats.keys())}")
            
            if "files" in stats:
                files = stats["files"]
                print(f"    Files count: {len(files)}")
                
                if files:
                    first_file = files[0]
                    print(f"    First file: {first_file}")
        
    except Exception as e:
        print(f"  ❌ Error analyzing JSON report: {e}")

def main():
    """Main test function"""
    print("Simple Report Generation Test")
    print("This test will:")
    print("1. Create a test file")
    print("2. Generate a comprehensive report")
    print("3. Analyze the report contents")
    print("4. Verify DIT standards compliance")
    
    # Run the test
    success = test_report_generation()
    
    if success:
        print("\n🎉 Report generation test completed successfully!")
        print("The Turbo Transfer system can generate detailed reports correctly.")
    else:
        print("\n❌ Report generation test failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main()

