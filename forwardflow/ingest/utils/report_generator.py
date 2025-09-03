#!/usr/bin/env python3
"""
Report Generator for Transfer Operations
Generates industry-standard DIT (Data Ingest Transfer) reports
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class TransferReportGenerator:
    """Generates comprehensive transfer reports for completed, cancelled, or failed jobs"""
    
    def __init__(self, reports_folder: str = "transfer_reports"):
        self.reports_folder = Path(reports_folder)
        self.reports_folder.mkdir(exist_ok=True)
    
    def generate_job_report(self, 
                           job_id: str,
                           status: str,
                           stats: Dict[str, Any],
                           destination_details: Optional[Dict[str, Any]] = None,
                           file_records: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a comprehensive job report"""
        
        timestamp = datetime.now().isoformat()
        report_id = f"{job_id}_{int(time.time())}"
        
        # Create the report structure
        report = {
            "report_id": report_id,
            "job_id": job_id,
            "timestamp": timestamp,
            "status": status,
            "summary": {
                "total_files": stats.get("total_files", 0),
                "completed_files": stats.get("completed_files", 0),
                "cancelled_files": stats.get("cancelled_files", 0),
                "error_files": stats.get("error_files", 0),
                "total_bytes": stats.get("total_bytes", 0),
                "completed_bytes": stats.get("completed_bytes", 0),
                "elapsed_time_seconds": stats.get("elapsed_time", 0.0),
                "average_speed_mbps": stats.get("average_speed_mbps", 0.0)
            },
            "destinations": destination_details or {},
            "file_records": file_records or [],
            "metadata": {
                "report_version": "1.0",
                "generator": "ForwardFlow Transfer Engine",
                "platform": os.name,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
        }
        
        # Calculate additional metrics
        if report["summary"]["elapsed_time_seconds"] > 0:
            report["summary"]["throughput_gbps"] = (
                report["summary"]["completed_bytes"] / 
                (1024**3 * report["summary"]["elapsed_time_seconds"])
            )
        else:
            report["summary"]["throughput_gbps"] = 0.0
        
        # Calculate success rate
        total_files = report["summary"]["total_files"]
        if total_files > 0:
            report["summary"]["success_rate_percent"] = (
                report["summary"]["completed_files"] / total_files * 100.0
            )
        else:
            report["summary"]["success_rate_percent"] = 0.0
        
        # Write the report to file
        report_filename = f"{report_id}_{status}.json"
        report_path = self.reports_folder / report_filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"DEBUG: Transfer report written to: {report_path}")
            return str(report_path)
            
        except Exception as e:
            print(f"DEBUG: Failed to write report: {e}")
            return ""
    
    def generate_cancelled_report(self, 
                                 job_id: str,
                                 copied_bytes: int,
                                 total_bytes: int,
                                 elapsed_time: float,
                                 destinations: List[str]) -> str:
        """Generate a report for cancelled transfers"""
        
        stats = {
            "total_files": 0,  # Will be filled by C++ engine
            "completed_files": 0,
            "cancelled_files": 0,
            "error_files": 0,
            "total_bytes": total_bytes,
            "completed_bytes": copied_bytes,
            "elapsed_time": elapsed_time,
            "average_speed_mbps": (copied_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
        }
        
        destination_details = {}
        for dest_path in destinations:
            destination_details[dest_path] = {
                "transfer_type": "unknown",
                "copied_bytes": copied_bytes,
                "completed_files": 0,
                "peak_speed_mbps": 0.0,
                "average_speed_mbps": stats["average_speed_mbps"]
            }
        
        return self.generate_job_report(
            job_id=job_id,
            status="cancelled",
            stats=stats,
            destination_details=destination_details
        )
    
    def generate_completed_report(self, 
                                 job_id: str,
                                 copied_bytes: int,
                                 total_bytes: int,
                                 elapsed_time: float,
                                 destinations: List[str]) -> str:
        """Generate a report for completed transfers"""
        
        stats = {
            "total_files": 0,  # Will be filled by C++ engine
            "completed_files": 0,
            "cancelled_files": 0,
            "error_files": 0,
            "total_bytes": total_bytes,
            "completed_bytes": copied_bytes,
            "elapsed_time": elapsed_time,
            "average_speed_mbps": (copied_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
        }
        
        destination_details = {}
        for dest_path in destinations:
            destination_details[dest_path] = {
                "transfer_type": "unknown",
                "copied_bytes": copied_bytes,
                "completed_files": 0,
                "peak_speed_mbps": 0.0,
                "average_speed_mbps": stats["average_speed_mbps"]
            }
        
        return self.generate_job_report(
            job_id=job_id,
            status="completed",
            stats=stats,
            destination_details=destination_details
        )
    
    def generate_error_report(self, 
                             job_id: str,
                             error_message: str,
                             copied_bytes: int = 0,
                             total_bytes: int = 0,
                             elapsed_time: float = 0.0) -> str:
        """Generate a report for failed transfers"""
        
        stats = {
            "total_files": 0,
            "completed_files": 0,
            "cancelled_files": 0,
            "error_files": 0,
            "total_bytes": total_bytes,
            "completed_bytes": copied_bytes,
            "elapsed_time": elapsed_time,
            "average_speed_mbps": 0.0
        }
        
        # Add error information to the report
        error_details = {
            "error_message": error_message,
            "error_timestamp": datetime.now().isoformat(),
            "error_type": "transfer_failure"
        }
        
        report = self.generate_job_report(
            job_id=job_id,
            status="error",
            stats=stats
        )
        
        # Add error details to the report file
        if report:
            try:
                with open(report, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                report_data["error_details"] = error_details
                
                with open(report, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
                    
            except Exception as e:
                print(f"DEBUG: Failed to add error details to report: {e}")
        
        return report
    
    def get_reports_folder(self) -> str:
        """Get the reports folder path"""
        return str(self.reports_folder)
    
    def list_reports(self) -> List[str]:
        """List all available reports"""
        try:
            return [f.name for f in self.reports_folder.glob("*.json")]
        except Exception as e:
            print(f"DEBUG: Failed to list reports: {e}")
            return []
    
    def cleanup_old_reports(self, max_age_days: int = 30) -> int:
        """Clean up reports older than specified days"""
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            cleaned_count = 0
            
            for report_file in self.reports_folder.glob("*.json"):
                if report_file.stat().st_mtime < cutoff_time:
                    report_file.unlink()
                    cleaned_count += 1
            
            print(f"DEBUG: Cleaned up {cleaned_count} old reports")
            return cleaned_count
            
        except Exception as e:
            print(f"DEBUG: Failed to cleanup old reports: {e}")
            return 0

