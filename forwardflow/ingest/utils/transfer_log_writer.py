#!/usr/bin/env python3
"""
Transfer Log Writer

Utility for writing transfer logs when operations are cancelled or completed.
"""

import os
import json
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
            reports_dir = base_destination.parent / reports_folder_name
        else:
            # Fallback to user's home directory if no destinations
            reports_dir = Path.home() / reports_folder_name
        
        # Create the reports directory
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        log_filename = f"verify_report_{timestamp}.txt"
        log_path = reports_dir / log_filename
        
        # Create human-readable report content
        report_content = f"""ForwardFlow Verification Report
Job ID: {job_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== TRANSFER SUMMARY ===
Status: {status}
Source Path: {source_path}
Destinations: {', '.join(destinations)}
Total Destinations: {len(destinations)}

"""
        
        # Add error message if present
        if error_message:
            report_content += f"Error: {error_message}\n\n"
        
        # Add statistics if available
        if stats:
            report_content += "=== TRANSFER STATISTICS ===\n"
            for key, value in stats.items():
                report_content += f"{key}: {value}\n"
            report_content += "\n"
        
        # Add system information
        report_content += f"""=== SYSTEM INFORMATION ===
Platform: {os.name}
Python Version: {os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}
Timestamp: {datetime.now().isoformat()}
"""
        
        # Write the report file
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Also create a JSON version for machine readability
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
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: Transfer reports written to: {reports_dir}")
        print(f"DEBUG: TXT report: {log_path}")
        print(f"DEBUG: JSON report: {json_path}")
        return str(log_path)
        
    except Exception as e:
        print(f"DEBUG: Error writing transfer log: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback path if we can't write to the reports directory
        return f"/tmp/transfer_log_{job_id}_{int(time.time())}.txt"


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
        for log_file in reports_dir.glob("verify_report_*.txt"):
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
                # Also delete the corresponding JSON file
                json_file = log_file.replace('.txt', '.json')
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
