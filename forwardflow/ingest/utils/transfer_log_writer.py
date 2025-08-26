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


def write_transfer_log(
    job_id: str,
    source_path: str,
    destinations: List[str],
    status: str = "COMPLETED",
    error_message: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None
) -> str:
    """
    Write a transfer log file
    
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
        # Create logs directory if it doesn't exist
        logs_dir = Path.home() / "Library" / "Application Support" / "ForwardFlow" / "TransferLogs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"transfer_log_{job_id}_{timestamp}.json"
        log_path = logs_dir / log_filename
        
        # Create log data
        log_data = {
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
        
        # Write log file
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"DEBUG: Transfer log written to: {log_path}")
        return str(log_path)
        
    except Exception as e:
        print(f"DEBUG: Error writing transfer log: {e}")
        # Return a fallback path if we can't write to the logs directory
        return f"/tmp/transfer_log_{job_id}_{int(time.time())}.json"


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
    List all available transfer logs
    
    Returns:
        List[str]: List of log file paths
    """
    try:
        logs_dir = Path.home() / "Library" / "Application Support" / "ForwardFlow" / "TransferLogs"
        if not logs_dir.exists():
            return []
        
        log_files = []
        for log_file in logs_dir.glob("transfer_log_*.json"):
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
                deleted_count += 1
            except Exception as e:
                print(f"DEBUG: Error deleting log file {log_file}: {e}")
        
        print(f"DEBUG: Cleaned up {deleted_count} old transfer logs")
        return deleted_count
        
    except Exception as e:
        print(f"DEBUG: Error cleaning up transfer logs: {e}")
        return 0
