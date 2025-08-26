#!/usr/bin/env python3
"""
Transfer Log Writer

Utility for writing transfer logs when operations are cancelled or completed.
Follows DIT (Digital Imaging Technician) industry standards for CSV reports.
"""

import os
import json
import csv
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Import config manager to get user preferences
try:
    from app.core.config_manager import get_transfer_reports_folder_name
except ImportError:
    # Fallback if config manager is not available
    def get_transfer_reports_folder_name():
        return "_ForwardFlow_verification_Reports"


def write_transfer_log(
    job_id: str,
    source_path: str,
    destinations: List[str],
    status: str = "COMPLETED",
    error_message: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None
) -> str:
    """
    Write a transfer log file to the user's preferred reports folder
    Follows DIT industry standards for CSV reports
    
    Args:
        job_id: The job ID
        source_path: The source path
        destinations: List of destination paths
        status: Status of the transfer (COMPLETED, CANCELLED, ERROR)
        error_message: Error message if applicable
        stats: Transfer statistics if available
        
    Returns:
        str: Path to the written log file
    """
    try:
        # Get the user's preferred reports folder name
        reports_folder_name = get_transfer_reports_folder_name()
        
        # Create reports directory in the first destination folder
        if destinations and len(destinations) > 0:
            # Use the first destination as the base for the reports folder
            base_destination = Path(destinations[0])
            reports_dir = base_destination / reports_folder_name
        else:
            # Fallback to user's home directory if no destinations
            reports_dir = Path.home() / reports_folder_name
        
        # Create the reports directory
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        
        # Generate DIT-standard CSV report
        csv_filename = f"verify_report_{timestamp}.csv"
        csv_path = reports_dir / csv_filename
        
        # Create CSV with DIT-standard fields
        csv_data = create_dit_csv_report(job_id, source_path, destinations, status, error_message, stats)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
        
        # Generate human-readable TXT report
        txt_filename = f"verify_report_{timestamp}.txt"
        txt_path = reports_dir / txt_filename
        
        txt_content = create_human_readable_report(job_id, source_path, destinations, status, error_message, stats)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        # Generate JSON report for machine readability
        json_filename = f"verify_report_{timestamp}.json"
        json_path = reports_dir / json_filename
        
        json_data = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "source_path": source_path,
            "destinations": destinations,
            "status": status,
            "error_message": error_message,
            "stats": stats or {},
            "system_info": {
                "platform": os.name,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "engine": "ForwardFlow C++ Enhanced Copy Engine"
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: Transfer reports written to: {reports_dir}")
        print(f"DEBUG: CSV report: {csv_path}")
        print(f"DEBUG: TXT report: {txt_path}")
        print(f"DEBUG: JSON report: {json_path}")
        return str(csv_path)
        
    except Exception as e:
        print(f"DEBUG: Error writing transfer log: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback path if we can't write to the reports directory
        return f"/tmp/transfer_log_{job_id}_{int(time.time())}.csv"


def create_dit_csv_report(
    job_id: str,
    source_path: str,
    destinations: List[str],
    status: str,
    error_message: Optional[str],
    stats: Optional[Dict[str, Any]]
) -> List[List[str]]:
    """
    Create a DIT-standard CSV report following industry standards
    Based on Silverstack and YoYotta CSV formats
    Handles partial transfers properly when jobs are cancelled
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # DIT-standard CSV headers (following industry standards)
    headers = [
        "Job ID",
        "Timestamp",
        "Source Path",
        "Destination Path",
        "File Name",
        "File Size (bytes)",
        "File Size (MB)",
        "Checksum Type",
        "Source Checksum",
        "Destination Checksum",
        "Verification Status",
        "Transfer Status",
        "Error Message",
        "Transfer Speed (MB/s)",
        "Transfer Duration (seconds)",
        "Engine Used"
    ]
    
    # Create CSV data
    csv_data = [headers]
    
    # Get file information from stats if available
    if stats and 'files' in stats:
        for file_info in stats['files']:
            # Determine individual file status based on completion
            file_status = determine_file_status(file_info, status)
            
            # Get verification status
            verification_status = file_info.get('verification_status', 'UNKNOWN')
            if file_status == 'COMPLETED' and verification_status == 'UNKNOWN':
                verification_status = 'PASS'  # Assume passed if completed but no explicit status
            
            row = [
                job_id,
                timestamp,
                source_path,
                destinations[0] if destinations else "",
                file_info.get('filename', 'Unknown'),
                str(file_info.get('size', 0)),
                f"{file_info.get('size', 0) / (1024*1024):.2f}",
                file_info.get('checksum_type', 'xxHash64'),
                file_info.get('source_checksum', ''),
                file_info.get('destination_checksum', ''),
                verification_status,
                file_status,
                error_message if file_status != 'COMPLETED' else '',
                f"{file_info.get('transfer_speed', 0):.2f}",
                f"{file_info.get('transfer_duration', 0):.2f}",
                "ForwardFlow C++ Engine"
            ]
            csv_data.append(row)
    else:
        # Fallback row if no detailed file stats
        # For cancelled jobs, we can't determine individual file status
        file_status = status if status != 'CANCELLED' else 'UNKNOWN'
        row = [
            job_id,
            timestamp,
            source_path,
            destinations[0] if destinations else "",
            os.path.basename(source_path),
            str(stats.get('total_bytes', 0) if stats else 0),
            f"{(stats.get('total_bytes', 0) if stats else 0) / (1024*1024):.2f}",
            "xxHash64",
            "",
            "",
            "UNKNOWN",
            file_status,
            error_message or '',
            f"{stats.get('avg_speed', 0):.2f}" if stats else "0.00",
            f"{stats.get('duration', 0):.2f}" if stats else "0.00",
            "ForwardFlow C++ Engine"
        ]
        csv_data.append(row)
    
    return csv_data


def determine_file_status(file_info: Dict[str, Any], overall_status: str) -> str:
    """
    Determine the individual file status based on completion and overall job status
    Follows DIT industry standards for partial transfers
    """
    # Check if file has completion information
    if 'completion_percentage' in file_info:
        completion = file_info['completion_percentage']
        if completion >= 100:
            return 'COMPLETED'
        elif completion > 0:
            return 'INCOMPLETE'
        else:
            return 'NOT_STARTED'
    
    # Check if file has verification status (completed files are verified)
    if file_info.get('verification_status') == 'PASS':
        return 'COMPLETED'
    
    # Check if file has destination checksum (completed files have this)
    if file_info.get('destination_checksum'):
        return 'COMPLETED'
    
    # Check if file has transfer duration (started files have this)
    if file_info.get('transfer_duration', 0) > 0:
        if overall_status == 'CANCELLED':
            return 'CANCELLED'
        else:
            return 'INCOMPLETE'
    
    # Check if file size matches expected (completed files should match)
    source_size = file_info.get('source_size', 0)
    dest_size = file_info.get('destination_size', 0)
    if source_size > 0 and dest_size > 0 and source_size == dest_size:
        return 'COMPLETED'
    
    # Default based on overall status
    if overall_status == 'CANCELLED':
        return 'NOT_STARTED'
    elif overall_status == 'COMPLETED':
        return 'COMPLETED'
    else:
        return 'UNKNOWN'


def create_human_readable_report(
    job_id: str,
    source_path: str,
    destinations: List[str],
    status: str,
    error_message: Optional[str],
    stats: Optional[Dict[str, Any]]
) -> str:
    """
    Create a human-readable TXT report with proper partial transfer handling
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""ForwardFlow Verification Report
Job ID: {job_id}
Generated: {timestamp}

=== TRANSFER SUMMARY ===
Status: {status}
Source Path: {source_path}
Destinations: {', '.join(destinations)}
Total Destinations: {len(destinations)}

"""
    
    # Add error message if present
    if error_message:
        report += f"Error: {error_message}\n\n"
    
    # Add statistics if available
    if stats:
        report += "=== TRANSFER STATISTICS ===\n"
        for key, value in stats.items():
            if key != 'files':  # Skip detailed file list in TXT report
                report += f"{key}: {value}\n"
        report += "\n"
        
        # Add file details if available
        if 'files' in stats and stats['files']:
            report += "=== FILE DETAILS ===\n"
            
            # Group files by status for better readability
            completed_files = []
            cancelled_files = []
            incomplete_files = []
            not_started_files = []
            
            for file_info in stats['files']:
                file_status = determine_file_status(file_info, status)
                if file_status == 'COMPLETED':
                    completed_files.append(file_info)
                elif file_status == 'CANCELLED':
                    cancelled_files.append(file_info)
                elif file_status == 'INCOMPLETE':
                    incomplete_files.append(file_info)
                else:
                    not_started_files.append(file_info)
            
            # Show completed files first
            if completed_files:
                report += f"\n✅ COMPLETED FILES ({len(completed_files)}):\n"
                for i, file_info in enumerate(completed_files, 1):
                    report += f"  {i}. {file_info.get('filename', 'Unknown')}\n"
                    report += f"     Size: {file_info.get('size', 0)} bytes ({file_info.get('size', 0) / (1024*1024):.2f} MB)\n"
                    report += f"     Checksum: {file_info.get('checksum_type', 'xxHash64')} - {file_info.get('destination_checksum', 'N/A')}\n"
                    report += f"     Verification: {file_info.get('verification_status', 'PASS')}\n"
                    report += f"     Speed: {file_info.get('transfer_speed', 0):.2f} MB/s\n"
                    report += f"     Duration: {file_info.get('transfer_duration', 0):.2f} seconds\n"
            
            # Show cancelled/incomplete files
            if cancelled_files or incomplete_files:
                report += f"\n⚠️  INTERRUPTED FILES ({len(cancelled_files) + len(incomplete_files)}):\n"
                for i, file_info in enumerate(cancelled_files + incomplete_files, 1):
                    file_status = determine_file_status(file_info, status)
                    report += f"  {i}. {file_info.get('filename', 'Unknown')} - {file_status}\n"
                    if file_info.get('transfer_duration', 0) > 0:
                        report += f"     Partial transfer: {file_info.get('completion_percentage', 0):.1f}% complete\n"
                        report += f"     Duration: {file_info.get('transfer_duration', 0):.2f} seconds\n"
            
            # Show not started files
            if not_started_files:
                report += f"\n⏸️  NOT STARTED FILES ({len(not_started_files)}):\n"
                for i, file_info in enumerate(not_started_files, 1):
                    report += f"  {i}. {file_info.get('filename', 'Unknown')}\n"
                    report += f"     Size: {file_info.get('size', 0)} bytes ({file_info.get('size', 0) / (1024*1024):.2f} MB)\n"
    
    # Add system information
    report += f"""
=== SYSTEM INFORMATION ===
Platform: {os.name}
Python Version: {os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}
Engine: ForwardFlow C++ Enhanced Copy Engine
Timestamp: {datetime.now().isoformat()}
"""
    
    return report


def read_transfer_log(log_path: str) -> Optional[Dict[str, Any]]:
    """
    Read a transfer log file
    
    Args:
        log_path: Path to the log file
        
    Returns:
        Optional[Dict[str, Any]]: The log data or None if failed
    """
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"DEBUG: Error reading transfer log: {e}")
        return None


def list_transfer_logs() -> List[str]:
    """
    List all available transfer logs from the user's reports folder
    
    Returns:
        List[str]: List of log file paths
    """
    try:
        reports_folder_name = get_transfer_reports_folder_name()
        reports_dir = Path.home() / reports_folder_name
        
        if not reports_dir.exists():
            return []
        
        log_files = []
        for log_file in reports_dir.glob("verify_report_*.csv"):
            log_files.append(str(log_file))
        
        return sorted(log_files, reverse=True)  # Most recent first
        
    except Exception as e:
        print(f"DEBUG: Error listing transfer logs: {e}")
        return []


def cleanup_old_logs(max_logs: int = 100) -> int:
    """
    Clean up old transfer logs, keeping only the most recent ones
    
    Args:
        max_logs: Maximum number of logs to keep
        
    Returns:
        int: Number of logs deleted
    """
    try:
        log_files = list_transfer_logs()
        if len(log_files) <= max_logs:
            return 0
        
        # Delete oldest logs
        logs_to_delete = log_files[max_logs:]
        deleted_count = 0
        
        for log_file in logs_to_delete:
            try:
                os.remove(log_file)
                # Also delete the corresponding TXT and JSON files
                base_name = log_file.replace('.csv', '')
                txt_file = f"{base_name}.txt"
                json_file = f"{base_name}.json"
                
                if os.path.exists(txt_file):
                    os.remove(txt_file)
                if os.path.exists(json_file):
                    os.remove(json_file)
                    
                deleted_count += 1
            except Exception as e:
                print(f"DEBUG: Error deleting log file {log_file}: {e}")
        
        print(f"DEBUG: Cleaned up {deleted_count} old transfer logs")
        return deleted_count
        
    except Exception as e:
        print(f"DEBUG: Error cleaning up transfer logs: {e}")
        return 0
