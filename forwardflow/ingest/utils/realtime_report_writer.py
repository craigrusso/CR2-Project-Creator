#!/usr/bin/env python3
"""
Real-time DIT Report Writer for Transfer Operations
Writes report data incrementally as each file completes - industry standard for professional DIT workflows
"""

import json
import os
import time
import csv
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class RealtimeReportWriter:
    """
    Professional real-time report writer that updates reports as each file completes.
    This ensures data is never lost and reports are always current.
    """

    def __init__(self, job_id: str, source_path: str, destinations: List[str]):
        """Initialize real-time report writer for a transfer job"""
        self.job_id = job_id
        self.source_path = source_path
        # Store destination roots as plain strings for readability/debug output
        self.destinations = [str(dest).strip() for dest in destinations]
        self.start_time = time.time()
        self.lock = threading.Lock()

        # Create report files immediately
        self.report_paths: Dict[str, Dict[str, str]] = {}
        self.dest_index_map: Dict[int, str] = {}
        self._initialize_report_files()

        # Track statistics
        self.stats = {
            'total_files': 0,
            'completed_files': 0,
            'failed_files': 0,
            'total_bytes': 0,
            'completed_bytes': 0,
            'current_speed_mbps': 0,
            'peak_speed_mbps': 0
        }

        print(f"📝 Real-time report writer initialized for job: {job_id}")
        print(f"📁 Report files created in {len(self.report_paths)} destinations")

    def _initialize_report_files(self) -> None:
        """Create initial report files in each destination"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"📝 DEBUG: Initializing report files for {len(self.destinations)} destinations")
        print(f"📝 DEBUG: Destinations: {self.destinations}")

        for index, dest_path in enumerate(self.destinations):
            try:
                original_dest = str(dest_path)
                normalized_dest = self._normalize_path(original_dest)
                
                print(f"📝 DEBUG: Processing dest[{index}]: {original_dest}")
                print(f"📝 DEBUG: Normalized to: {normalized_dest}")

                # Create _CR2_CREATIVE_REPORTS directory
                reports_dir = Path(original_dest) / "_CR2_CREATIVE_REPORTS"
                print(f"📝 DEBUG: Creating reports dir: {reports_dir}")
                reports_dir.mkdir(parents=True, exist_ok=True)

                # Generate base filename
                dest_name = Path(original_dest).name.replace(" ", "_")
                base_filename = f"ingest_{timestamp}_{dest_name}"
                print(f"📝 DEBUG: Base filename: {base_filename}")

                # Initialize JSON report
                json_path = reports_dir / f"{base_filename}.json"
                self._init_json_report(json_path)

                # Initialize CSV report
                csv_path = reports_dir / f"{base_filename}_files.csv"
                self._init_csv_report(csv_path)

                # Initialize TXT report
                txt_path = reports_dir / f"{base_filename}.txt"
                self._init_txt_report(txt_path)

                self.report_paths[normalized_dest] = {
                    'json': str(json_path),
                    'csv': str(csv_path),
                    'txt': str(txt_path),
                    'root_path': original_dest
                }

                self.dest_index_map[index] = normalized_dest

                print(f"✅ Report files initialized for dest[{index}]: {original_dest}")
                print(f"✅ Added to dest_index_map[{index}] = {normalized_dest}")
                print(f"✅ Added to report_paths[{normalized_dest}]")

            except Exception as e:
                print(f"❌ Failed to initialize reports for {dest_path}: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"📝 DEBUG: Initialization complete - dest_index_map: {self.dest_index_map}")
        print(f"📝 DEBUG: Initialization complete - report_paths keys: {list(self.report_paths.keys())}")

    def _init_json_report(self, path: Path):
        """Initialize JSON report structure"""
        report = {
            "job_id": self.job_id,
            "status": "IN_PROGRESS",
            "generated": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "source_path": str(self.source_path),
            "destination": str(path.parent.parent),
            "stats": self.stats.copy(),
            "files": [],
            "metadata": {
                "report_version": "2.1",
                "dit_standard_version": "2025.1",
                "generator": "ForwardFlow Real-time Engine",
                "realtime": True,
                "checksum_algorithm": "xxHash64BE"
            }
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

    def _init_csv_report(self, path: Path):
        """Initialize CSV report with headers"""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'filename', 'source_path', 'dest_path',
                'size_bytes', 'status', 'source_checksum', 'dest_checksum',
                'hash_algorithm', 'verification_passed', 'transfer_time_s'
            ])

    def _init_txt_report(self, path: Path):
        """Initialize human-readable TXT report"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write("ForwardFlow Real-time Transfer Report\n")
            f.write(f"Job ID: {self.job_id}\n")
            f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {self.source_path}\n")
            f.write(f"Destination: {path.parent.parent}\n")
            f.write("=" * 80 + "\n\n")
            f.write("STATUS | HASH | FILENAME\n")
            f.write("-" * 80 + "\n")

    def add_file_completion(self, file_data: Dict[str, Any]):
        """
        Add a file completion record to all report formats in real-time.
        This is called immediately when each file completes.
        """
        print(f"📝📝📝 REALTIME_WRITER: add_file_completion() CALLED with data: {file_data}")

        with self.lock:
            try:
                # Extract file information
                filename = file_data.get('filename', 'unknown')
                source_path = file_data.get('source_path', '')
                dest_path = file_data.get('dest_path', '')
                dest_index = file_data.get('dest_index')
                size_bytes = file_data.get('size_bytes', file_data.get('bytes_copied', 0))
                source_checksum = file_data.get('source_checksum', '')
                dest_checksum = file_data.get('dest_checksum', file_data.get('destination_checksum', ''))
                hash_algorithm = file_data.get('hash_algorithm', 'unknown')
                verification_passed = file_data.get('verification_passed', False)
                status = file_data.get('status', 'COMPLETED')

                print(f"📝📝📝 REALTIME_WRITER: Extracted - file={filename}, hash={source_checksum[:16] if source_checksum else 'NONE'}, dest={dest_path}")

                # Update statistics
                self.stats['completed_files'] += 1
                if status == 'COMPLETED':
                    self.stats['completed_bytes'] += size_bytes
                elif status == 'FAILED':
                    self.stats['failed_files'] += 1
                # Ensure total_files never lags behind completed count
                if self.stats['completed_files'] > self.stats.get('total_files', 0):
                    self.stats['total_files'] = self.stats['completed_files']

                # Calculate transfer time
                transfer_time = time.time() - self.start_time

                # Determine which destination this file belongs to
                print(f"📝 DEBUG: dest_index={dest_index}, dest_index_map={self.dest_index_map}")
                print(f"📝 DEBUG: report_paths keys={list(self.report_paths.keys())}")
                
                dest_key = None
                if isinstance(dest_index, int) and dest_index in self.dest_index_map:
                    dest_key = self.dest_index_map[dest_index]
                    print(f"📝 DEBUG: Found dest_key via index: {dest_key}")

                normalized_dest_path = self._normalize_path(dest_path)
                if not dest_key:
                    print(f"📝 DEBUG: Trying path matching with normalized_dest_path={normalized_dest_path}")
                    dest_key = self._get_destination_key(normalized_dest_path, dest_path)
                    if dest_key:
                        print(f"📝 DEBUG: Found dest_key via path matching: {dest_key}")

                if not dest_key:
                    print(f"⚠️ No report path found for destination: {dest_path}")
                    print(f"📝 DEBUG: Tried index {dest_index} and path {normalized_dest_path}")
                    return

                paths = self.report_paths[dest_key]
                display_dest = paths.get('root_path', dest_key)
                print(f"📝📝📝 REALTIME_WRITER: Report paths for {display_dest}: {paths}")

                # Update JSON report
                print(f"📝📝📝 REALTIME_WRITER: Updating JSON report: {paths['json']}")
                self._update_json_report(paths['json'], file_data)

                # Append to CSV report
                print(f"📝📝📝 REALTIME_WRITER: Appending to CSV report: {paths['csv']}")
                self._append_csv_record(paths['csv'], {
                    'timestamp': datetime.now().isoformat(),
                    'filename': filename,
                    'source_path': source_path,
                    'dest_path': dest_path,
                    'size_bytes': size_bytes,
                    'status': status,
                    'source_checksum': source_checksum,
                    'dest_checksum': dest_checksum,
                    'hash_algorithm': hash_algorithm,
                    'verification_passed': verification_passed,
                    'transfer_time_s': transfer_time
                })

                # Append to TXT report
                self._append_txt_record(paths['txt'], filename, status, source_checksum, hash_algorithm)

                print(f"✅ Report updated for: {filename} ({status})")

            except Exception as e:
                print(f"❌ Error updating report for file completion: {e}")
                import traceback
                traceback.print_exc()

    def _update_json_report(self, path: str, file_data: Dict[str, Any]):
        """Update JSON report with new file record"""
        try:
            # Read existing report
            with open(path, 'r', encoding='utf-8') as f:
                report = json.load(f)

            # Add file record
            report['files'].append(file_data)

            # Update statistics
            report['stats'] = self.stats.copy()
            report['last_updated'] = datetime.now().isoformat()

            # Calculate elapsed time and speed
            elapsed = time.time() - self.start_time
            if elapsed > 0 and self.stats['completed_bytes'] > 0:
                avg_speed_mbps = (self.stats['completed_bytes'] / (1024 * 1024)) / elapsed
                report['stats']['average_speed_mbps'] = avg_speed_mbps

            # Write updated report
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            print(f"❌ Error updating JSON report: {e}")

    def _append_csv_record(self, path: str, record: Dict[str, Any]):
        """Append a record to CSV report"""
        try:
            with open(path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    record['timestamp'],
                    record['filename'],
                    record['source_path'],
                    record['dest_path'],
                    record['size_bytes'],
                    record['status'],
                    record['source_checksum'],
                    record['dest_checksum'],
                    record['hash_algorithm'],
                    record['verification_passed'],
                    record['transfer_time_s']
                ])
        except Exception as e:
            print(f"❌ Error appending to CSV report: {e}")

    def _append_txt_record(self, path: str, filename: str, status: str, checksum: str, algorithm: str):
        """Append a record to human-readable TXT report"""
        try:
            # Format status
            if status == 'COMPLETED':
                status_icon = "✅"
            elif status == 'FAILED':
                status_icon = "❌"
            else:
                status_icon = "⏭️"

            # Format hash
            if checksum:
                hash_display = f"{algorithm}: {checksum[:16]}..."
            else:
                hash_display = "No hash"

            with open(path, 'a', encoding='utf-8') as f:
                f.write(f"{status_icon} {status:<10} | {hash_display:<30} | {filename}\n")

        except Exception as e:
            print(f"❌ Error appending to TXT report: {e}")

    def update_job_stats(self, stats: Dict[str, Any]):
        """Update job-level statistics"""
        with self.lock:
            self.stats.update(stats)

    def finalize_reports(self, final_status: str = "COMPLETED", error_message: str = None):
        """Finalize all reports with final status and statistics"""
        with self.lock:
            for dest_path, paths in self.report_paths.items():
                try:
                    display_dest = paths.get('root_path', dest_path)
                    # Update JSON with final status
                    with open(paths['json'], 'r', encoding='utf-8') as f:
                        report = json.load(f)

                    report['status'] = final_status
                    report['completed'] = datetime.now().isoformat()
                    report['stats'] = self.stats.copy()

                    if error_message:
                        report['error_message'] = error_message

                    # Calculate final statistics
                    elapsed = time.time() - self.start_time
                    report['stats']['duration_seconds'] = elapsed

                    if elapsed > 0 and self.stats['completed_bytes'] > 0:
                        avg_speed_mbps = (self.stats['completed_bytes'] / (1024 * 1024)) / elapsed
                        report['stats']['average_speed_mbps'] = avg_speed_mbps

                    with open(paths['json'], 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2)

                    # Add summary to TXT report
                    with open(paths['txt'], 'a', encoding='utf-8') as f:
                        f.write("\n" + "=" * 80 + "\n")
                        f.write(f"Transfer {final_status} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Total files: {self.stats['completed_files']}/{self.stats['total_files']}\n")
                        f.write(f"Total size: {self.stats['completed_bytes'] / (1024**3):.2f} GB\n")
                        f.write(f"Duration: {elapsed:.1f} seconds\n")
                        if self.stats['completed_bytes'] > 0:
                            avg_speed = (self.stats['completed_bytes'] / (1024 * 1024)) / elapsed
                            f.write(f"Average speed: {avg_speed:.1f} MB/s\n")

                    print(f"✅ Reports finalized for: {display_dest}")

                except Exception as e:
                    print(f"❌ Error finalizing reports for {dest_path}: {e}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_path(path: Any) -> str:
        """Return a normalized absolute path string for reliable comparisons."""
        try:
            path_obj = Path(path).expanduser()
        except TypeError:
            path_obj = Path(str(path)).expanduser()

        absolute = path_obj if path_obj.is_absolute() else path_obj.absolute()
        normalized = os.path.normpath(str(absolute))
        return os.path.normcase(normalized)

    @staticmethod
    def _path_is_within(child: str, parent: str) -> bool:
        """Return True if child path is the same as or nested under parent."""
        try:
            common = os.path.commonpath([child, parent])
            return common == parent
        except ValueError:
            return False

    def _get_destination_key(self, normalized_dest_path: str, raw_dest_path: Optional[str] = None) -> Optional[str]:
        """Find the normalized destination root matching the provided file path."""
        if not normalized_dest_path:
            return None

        if normalized_dest_path in self.report_paths:
            return normalized_dest_path

        for dest_root in self.report_paths.keys():
            if self._path_is_within(normalized_dest_path, dest_root):
                return dest_root

        try:
            path_obj = Path(normalized_dest_path)
            for parent in path_obj.parents:
                parent_norm = self._normalize_path(parent)
                if parent_norm in self.report_paths:
                    return parent_norm
        except Exception:
            pass

        if raw_dest_path:
            try:
                raw_normalized = os.path.normpath(str(raw_dest_path))
                for dest_root, paths in self.report_paths.items():
                    original_root = paths.get('root_path', dest_root)
                    original_normalized = os.path.normpath(str(original_root))
                    if self._path_is_within(raw_normalized, original_normalized):
                        return dest_root
            except Exception:
                pass

        lowered_child = normalized_dest_path.lower()
        for dest_root, paths in self.report_paths.items():
            if lowered_child.startswith(dest_root.lower()):
                return dest_root
            root_path = paths.get('root_path')
            if root_path and lowered_child.startswith(os.path.normpath(str(root_path)).lower()):
                return dest_root

        if raw_dest_path:
            lowered_raw = os.path.normpath(str(raw_dest_path)).lower()
            for dest_root, paths in self.report_paths.items():
                root_path = paths.get('root_path', dest_root)
                if lowered_raw.startswith(os.path.normpath(str(root_path)).lower()):
                    return dest_root

        return None


# Global instance management
_realtime_writer = None
_writer_lock = threading.Lock()


def get_realtime_writer() -> Optional[RealtimeReportWriter]:
    """Get the current real-time report writer instance"""
    global _realtime_writer
    return _realtime_writer


def start_realtime_reporting(job_id: str, source_path: str, destinations: List[str]) -> RealtimeReportWriter:
    """Start a new real-time reporting session"""
    global _realtime_writer

    with _writer_lock:
        # Close previous writer if exists
        if _realtime_writer:
            _realtime_writer.finalize_reports("INTERRUPTED")

        # Create new writer
        _realtime_writer = RealtimeReportWriter(job_id, source_path, destinations)
        return _realtime_writer


def stop_realtime_reporting(final_status: str = "COMPLETED", error_message: str = None):
    """Stop real-time reporting and finalize reports"""
    global _realtime_writer

    with _writer_lock:
        if _realtime_writer:
            _realtime_writer.finalize_reports(final_status, error_message)
            _realtime_writer = None
