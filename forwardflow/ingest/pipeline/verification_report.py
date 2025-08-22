"""Verification report generation for ForwardFlow ingest system.

Generates comprehensive verification reports in both human-readable TXT
and machine-readable CSV formats after transfer job completion.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TextIO
import threading

from ..logging import get_logger


@dataclass
class VerificationRecord:
    """Single file verification record."""
    filename: str
    source_path: str
    destination_path: str
    file_size_bytes: int
    hash_type: str
    source_hash: Optional[str]
    destination_hash: Optional[str]
    status: str  # "PASS" or "FAIL"
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class VerificationReport:
    """Complete verification report for a transfer job."""
    job_id: str
    job_start_time: datetime
    job_end_time: Optional[datetime] = None
    total_files: int = 0
    passed_files: int = 0
    failed_files: int = 0
    total_bytes: int = 0
    records: List[VerificationRecord] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def add_record(self, record: VerificationRecord) -> None:
        """Add a verification record thread-safely."""
        with self._lock:
            self.records.append(record)
            self.total_files += 1
            if record.status == "PASS":
                self.passed_files += 1
            else:
                self.failed_files += 1
            self.total_bytes += record.file_size_bytes
    
    def finalize(self, end_time: Optional[datetime] = None) -> None:
        """Mark the report as complete."""
        with self._lock:
            self.job_end_time = end_time or datetime.now()


class VerificationReportManager:
    """Manages verification report generation and writing."""
    
    def __init__(self, destination_root: Path):
        self.destination_root = Path(destination_root)
        self.reports_dir = self.destination_root / "_ForwardFlow_Reports"
        self._logger = get_logger("forwardflow.ingest.verification_report")
        self._active_reports: Dict[str, VerificationReport] = {}
        self._lock = threading.Lock()
        
        # Ensure reports directory exists
        self._ensure_reports_directory()
    
    def _ensure_reports_directory(self) -> None:
        """Create the reports directory if it doesn't exist."""
        try:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"Reports directory ready: {self.reports_dir}")
        except Exception as e:
            self._logger.error(f"Failed to create reports directory: {e}")
            # Don't raise - we'll handle this gracefully
    
    def start_job_report(self, job_id: str, start_time: datetime) -> None:
        """Start tracking verification for a new job."""
        with self._lock:
            report = VerificationReport(
                job_id=job_id,
                job_start_time=start_time
            )
            self._active_reports[job_id] = report
            self._logger.info(f"Started verification report for job: {job_id}")
    
    def add_verification_record(self, job_id: str, record: VerificationRecord) -> None:
        """Add a verification record to an active job report."""
        with self._lock:
            if job_id in self._active_reports:
                self._active_reports[job_id].add_record(record)
                self._logger.debug(f"Added verification record for {record.filename} in job {job_id}")
            else:
                self._logger.warning(f"Attempted to add verification record to unknown job: {job_id}")
    
    def finalize_job_report(self, job_id: str, end_time: Optional[datetime] = None) -> None:
        """Mark a job report as complete and write reports to disk."""
        with self._lock:
            if job_id not in self._active_reports:
                self._logger.warning(f"Attempted to finalize unknown job report: {job_id}")
                return
            
            report = self._active_reports[job_id]
            report.finalize(end_time)
            
            # Write reports asynchronously to avoid blocking
            threading.Thread(
                target=self._write_reports,
                args=(job_id, report),
                daemon=True,
                name=f"report-writer-{job_id}"
            ).start()
    
    def _write_reports(self, job_id: str, report: VerificationReport) -> None:
        """Write TXT and CSV reports to disk."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            base_filename = f"verify_report_{timestamp}"
            
            # Write TXT report
            txt_path = self.reports_dir / f"{base_filename}.txt"
            self._write_txt_report(txt_path, report)
            
            # Write CSV report
            csv_path = self.reports_dir / f"{base_filename}.csv"
            self._write_csv_report(csv_path, report)
            
            self._logger.info(f"Verification reports written for job {job_id}: {txt_path}, {csv_path}")
            
            # Clean up the report from memory
            with self._lock:
                if job_id in self._active_reports:
                    del self._active_reports[job_id]
                    
        except Exception as e:
            self._logger.error(f"Failed to write verification reports for job {job_id}: {e}")
            # Emit event for UI notification
            self._emit_report_failed_event(job_id, str(e))
    
    def _write_txt_report(self, filepath: Path, report: VerificationReport) -> None:
        """Write human-readable TXT report."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                self._write_txt_header(f, report)
                
                for record in report.records:
                    self._write_txt_record(f, record)
                    f.write("\n")  # Blank line between records
                    
                self._write_txt_summary(f, report)
                
        except Exception as e:
            self._logger.error(f"Failed to write TXT report {filepath}: {e}")
            raise
    
    def _write_txt_header(self, f: TextIO, report: VerificationReport) -> None:
        """Write TXT report header."""
        f.write("=" * 80 + "\n")
        f.write("FORWARDFLOW VERIFICATION REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Job ID: {report.job_id}\n")
        f.write(f"Start Time: {report.job_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if report.job_end_time:
            f.write(f"End Time: {report.job_end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            duration = report.job_end_time - report.job_start_time
            f.write(f"Duration: {duration}\n")
        f.write(f"Total Files: {report.total_files}\n")
        f.write(f"Passed: {report.passed_files}\n")
        f.write(f"Failed: {report.failed_files}\n")
        f.write(f"Total Size: {self._format_bytes(report.total_bytes)}\n")
        f.write("=" * 80 + "\n\n")
    
    def _write_txt_record(self, f: TextIO, record: VerificationRecord) -> None:
        """Write a single TXT record."""
        f.write(f"File: {record.filename}\n")
        f.write(f"Source: {record.source_path}\n")
        f.write(f"Destination: {record.destination_path}\n")
        f.write(f"Size: {self._format_bytes(record.file_size_bytes)}\n")
        f.write(f"HashType: {record.hash_type}\n")
        f.write(f"SourceHash: {record.source_hash or 'N/A'}\n")
        f.write(f"DestHash: {record.destination_hash or 'N/A'}\n")
        f.write(f"Status: {record.status}\n")
        f.write(f"Timestamp: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if record.error_message:
            f.write(f"Error: {record.error_message}\n")
    
    def _write_txt_summary(self, f: TextIO, report: VerificationReport) -> None:
        """Write TXT report summary."""
        f.write("=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Files Processed: {report.total_files}\n")
        f.write(f"Verification Passed: {report.passed_files}\n")
        f.write(f"Verification Failed: {report.failed_files}\n")
        f.write(f"Success Rate: {(report.passed_files / report.total_files * 100):.1f}%\n")
        f.write(f"Total Data Size: {self._format_bytes(report.total_bytes)}\n")
        f.write("=" * 80 + "\n")
    
    def _write_csv_report(self, filepath: Path, report: VerificationReport) -> None:
        """Write machine-readable CSV report."""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'File', 'Source', 'Destination', 'Size', 'HashType',
                    'SourceHash', 'DestHash', 'Status', 'Timestamp', 'Error'
                ])
                
                # Write records
                for record in report.records:
                    writer.writerow([
                        record.filename,
                        record.source_path,
                        record.destination_path,
                        record.file_size_bytes,
                        record.hash_type,
                        record.source_hash or 'N/A',
                        record.destination_hash or 'N/A',
                        record.status,
                        record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        record.error_message or ''
                    ])
                    
        except Exception as e:
            self._logger.error(f"Failed to write CSV report {filepath}: {e}")
            raise
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human-readable string."""
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        value = float(bytes_value)
        
        while value >= 1024.0 and unit_index < len(units) - 1:
            value /= 1024.0
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(value)} {units[unit_index]}"
        else:
            return f"{value:.1f} {units[unit_index]}"
    
    def _emit_report_failed_event(self, job_id: str, error: str) -> None:
        """Emit report.failed event for UI notification."""
        # This will be handled by the event system
        # The actual emission happens in the engine via the event sink
        pass
    
    def get_job_report(self, job_id: str) -> Optional[VerificationReport]:
        """Get the current report for a job (for debugging/testing)."""
        with self._lock:
            return self._active_reports.get(job_id)
    
    def cleanup_job(self, job_id: str) -> None:
        """Clean up a job report (called on job cancellation/failure)."""
        with self._lock:
            if job_id in self._active_reports:
                del self._active_reports[job_id]
                self._logger.info(f"Cleaned up verification report for job: {job_id}")
