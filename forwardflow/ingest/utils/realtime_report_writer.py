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

    def __init__(self, job_id: str, source_path: str, destinations: List[str], expected_total_files: int = 0):
        """Initialize real-time report writer for a transfer job"""
        self.job_id = job_id
        self.source_path = source_path
        # Store destination roots as plain strings for readability/debug output
        self.destinations = [str(dest).strip() for dest in destinations]
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.finalized_destinations = set()  # Track which destinations have been finalized
        self.recorded_files = set()  # Track (filename, dest_key) to prevent duplicate file records

        # CRITICAL: Store expected total files from manifest - this should NEVER change
        self.expected_total_files = expected_total_files

        # Track statistics early so initialization helpers can access live defaults
        self.stats = {
            'total_files': expected_total_files,  # Use manifest total, not incremented count
            'completed_files': 0,
            'failed_files': 0,
            'total_bytes': 0,
            'completed_bytes': 0,
            'current_speed_mbps': 0,
            'peak_speed_mbps': 0
        }

        # Create report files immediately
        self.report_paths: Dict[str, Dict[str, str]] = {}
        self.dest_index_map: Dict[int, str] = {}
        self._initialize_report_files()

        print(f"Real-time report writer initialized for job: {job_id}")
        print(f"Report files created in {len(self.report_paths)} destinations")

    def _initialize_report_files(self) -> None:
        """Create initial report files in each destination"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"DEBUG: Initializing report files for {len(self.destinations)} destinations")
        print(f"DEBUG: Destinations: {self.destinations}")

        for index, dest_path in enumerate(self.destinations):
            try:
                original_dest = str(dest_path)
                normalized_dest = self._normalize_path(original_dest)
                
                print(f"DEBUG: Processing dest[{index}]: {original_dest}")
                print(f"DEBUG: Normalized to: {normalized_dest}")

                # Create _CR2_CREATIVE_REPORTS directory
                reports_dir = Path(original_dest) / "_CR2_CREATIVE_REPORTS"
                print(f"DEBUG: Creating reports dir: {reports_dir}")
                reports_dir.mkdir(parents=True, exist_ok=True)

                # Generate base filename
                dest_name = Path(original_dest).name.replace(" ", "_")
                base_filename = f"ingest_{timestamp}_{dest_name}"
                print(f"DEBUG: Base filename: {base_filename}")

                # Initialize JSON report
                json_path = reports_dir / f"{base_filename}.json"
                self._init_json_report(json_path)

                # Initialize CSV report
                csv_path = reports_dir / f"{base_filename}_files.csv"
                self._init_csv_report(csv_path)

                # Initialize TXT report
                txt_path = reports_dir / f"{base_filename}.txt"
                self._init_txt_report(txt_path)

                # Initialize MHL (Media Hash List) report path
                mhl_path = reports_dir / f"{base_filename}.mhl"

                self.report_paths[normalized_dest] = {
                    'json': str(json_path),
                    'csv': str(csv_path),
                    'txt': str(txt_path),
                    'mhl': str(mhl_path),
                    'root_path': original_dest
                }

                self.dest_index_map[index] = normalized_dest

                print(f"[OK] Report files initialized for dest[{index}]: {original_dest}")
                print(f"[OK] Added to dest_index_map[{index}] = {normalized_dest}")
                print(f"[OK] Added to report_paths[{normalized_dest}]")

            except Exception as e:
                print(f"[ERROR] Failed to initialize reports for {dest_path}: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"DEBUG: Initialization complete - dest_index_map: {self.dest_index_map}")
        print(f"DEBUG: Initialization complete - report_paths keys: {list(self.report_paths.keys())}")

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
        print(f"REALTIME_WRITER: add_file_completion() CALLED with data: {file_data}")

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

                print(f"REALTIME_WRITER: Extracted - file={filename}, hash={source_checksum[:16] if source_checksum else 'NONE'}, dest={dest_path}")

                # Update statistics
                self.stats['completed_files'] += 1
                if status == 'COMPLETED':
                    self.stats['completed_bytes'] += size_bytes
                elif status == 'FAILED':
                    self.stats['failed_files'] += 1

                # CRITICAL FIX: Never modify total_files - it's set from manifest and should remain constant
                # The old buggy code was: if self.stats['completed_files'] > self.stats.get('total_files', 0):
                #     self.stats['total_files'] = self.stats['completed_files']
                # This caused "42 of 42" instead of "42 of 63" when cancelled

                # Calculate transfer time
                transfer_time = time.time() - self.start_time

                # Determine which destination this file belongs to
                print(f"DEBUG: dest_index={dest_index}, dest_index_map={self.dest_index_map}")
                print(f"DEBUG: report_paths keys={list(self.report_paths.keys())}")
                
                dest_key = None
                if isinstance(dest_index, int) and dest_index in self.dest_index_map:
                    dest_key = self.dest_index_map[dest_index]
                    print(f"DEBUG: Found dest_key via index: {dest_key}")

                normalized_dest_path = self._normalize_path(dest_path)
                if not dest_key:
                    print(f"DEBUG: Trying path matching with normalized_dest_path={normalized_dest_path}")
                    dest_key = self._get_destination_key(normalized_dest_path, dest_path)
                    if dest_key:
                        print(f"DEBUG: Found dest_key via path matching: {dest_key}")

                if not dest_key:
                    print(f"⚠️ No report path found for destination: {dest_path}")
                    print(f"DEBUG: Tried index {dest_index} and path {normalized_dest_path}")
                    return

                # Check for duplicate file record for this destination
                file_dest_key = (filename, dest_key)
                if file_dest_key in self.recorded_files:
                    print(f"⚠️ DUPLICATE file.completed event for {filename} at {dest_key} - skipping")
                    return

                # Mark this file as recorded for this destination
                self.recorded_files.add(file_dest_key)
                print(f"✅ Recording file completion: {filename} for {dest_key}")

                paths = self.report_paths[dest_key]
                display_dest = paths.get('root_path', dest_key)
                print(f"REALTIME_WRITER: Report paths for {display_dest}: {paths}")

                # Update JSON report
                print(f"REALTIME_WRITER: Updating JSON report: {paths['json']}")
                self._update_json_report(paths['json'], file_data)

                # Append to CSV report
                print(f"REALTIME_WRITER: Appending to CSV report: {paths['csv']}")
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

                print(f"[OK] Report updated for: {filename} ({status})")

            except Exception as e:
                print(f"[ERROR] Error updating report for file completion: {e}")
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
            print(f"[ERROR] Error updating JSON report: {e}")

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
            print(f"[ERROR] Error appending to CSV report: {e}")

    def _append_txt_record(self, path: str, filename: str, status: str, checksum: str, algorithm: str):
        """Append a record to human-readable TXT report"""
        try:
            # Format status with visual icons
            if status == 'COMPLETED':
                status_icon = "✅ [OK]"  # Green checkmark for completed files
            elif status == 'FAILED':
                status_icon = "❌ [ERROR]"  # Red X for failed files
            else:
                status_icon = "⏭️"

            # Format hash - show FULL hash for integrity verification (no truncation)
            if checksum:
                hash_display = f"{algorithm}: {checksum}"
            else:
                hash_display = "No hash"

            with open(path, 'a', encoding='utf-8') as f:
                # Increased column width to 80 to accommodate full SHA256 hashes (64 chars + algorithm name)
                f.write(f"{status_icon} {status:<10} | {hash_display:<80} | {filename}\n")

        except Exception as e:
            print(f"[ERROR] Error appending to TXT report: {e}")

    def update_job_stats(self, stats: Dict[str, Any]):
        """Update job-level statistics"""
        with self.lock:
            # CRITICAL FIX: Preserve expected_total_files - never overwrite it
            original_total_files = self.stats.get('total_files', self.expected_total_files)
            self.stats.update(stats)
            # Restore the original total_files from manifest
            if self.expected_total_files > 0:
                self.stats['total_files'] = self.expected_total_files
            else:
                self.stats['total_files'] = original_total_files

    def finalize_destination_report(self, dest_path: str, status: str = "COMPLETED", error_message: str = None):
        """
        Finalize report for a single destination when it completes.
        This is called IMMEDIATELY when each destination finishes, enabling per-destination reporting.
        """
        with self.lock:
            # Normalize path for lookup
            normalized_dest = self._normalize_path(dest_path)
            dest_key = self._get_destination_key(normalized_dest, dest_path)

            if not dest_key:
                print(f"⚠️ Cannot finalize report for {dest_path}: No matching destination found")
                print(f"DEBUG: Tried normalized={normalized_dest}, available keys={list(self.report_paths.keys())}")
                return

            # Check if already finalized
            if dest_key in self.finalized_destinations:
                print(f"DEBUG: Destination report already finalized for {dest_path}, skipping duplicate finalization")
                return

            paths = self.report_paths.get(dest_key)
            if not paths:
                print(f"⚠️ Cannot finalize report for {dest_path}: No report paths found")
                return

            try:
                display_dest = paths.get('root_path', dest_key)
                print(f"📊 Finalizing per-destination report for: {display_dest}")

                # Update JSON with final status
                with open(paths['json'], 'r', encoding='utf-8') as f:
                    report = json.load(f)

                report['status'] = status
                report['completed'] = datetime.now().isoformat()
                report['last_updated'] = datetime.now().isoformat()

                if error_message:
                    report['error_message'] = error_message

                # Calculate statistics for this destination
                elapsed = time.time() - self.start_time
                report['stats']['duration_seconds'] = elapsed

                # Get files for this destination from the report
                dest_files = report.get('files', [])
                dest_completed_files = sum(1 for f in dest_files if f.get('status') == 'COMPLETED')
                dest_completed_bytes = sum(f.get('size_bytes', 0) for f in dest_files if f.get('status') == 'COMPLETED')

                # Update destination-specific stats
                # CRITICAL FIX: Use expected_total_files from manifest, not len(dest_files)
                # This ensures "42 of 63" instead of "42 of 42" when cancelled
                report['stats']['completed_files'] = dest_completed_files
                report['stats']['total_files'] = self.expected_total_files if self.expected_total_files > 0 else len(dest_files)
                report['stats']['completed_bytes'] = dest_completed_bytes

                print(f"🔍 DEBUG: finalize_destination_report() for {dest_path}:")
                print(f"  - Files in dest_files: {len(dest_files)}")
                print(f"  - self.expected_total_files: {self.expected_total_files}")
                print(f"  - Report stats['total_files']: {report['stats']['total_files']}")

                if elapsed > 0 and dest_completed_bytes > 0:
                    avg_speed_mbps = (dest_completed_bytes / (1024 * 1024)) / elapsed
                    report['stats']['average_speed_mbps'] = avg_speed_mbps

                # Write updated JSON
                with open(paths['json'], 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2)

                # Add completion summary to TXT report
                # Use expected_total_files for accurate reporting
                reported_total = self.expected_total_files if self.expected_total_files > 0 else len(dest_files)

                with open(paths['txt'], 'a', encoding='utf-8') as f:
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(f"Destination Transfer {status} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                    if status == "CANCELLED":
                        f.write("⚠️  TRANSFER CANCELLED BY USER\n")
                        f.write(f"Files completed before cancellation: {dest_completed_files}/{reported_total}\n")
                        f.write(f"Data transferred: {dest_completed_bytes / (1024**3):.2f} GB\n")
                        incomplete_files = reported_total - dest_completed_files
                        if incomplete_files > 0:
                            f.write(f"Files NOT transferred: {incomplete_files}\n")
                    elif status == "FAILED":
                        f.write("[ERROR] TRANSFER FAILED\n")
                        if error_message:
                            f.write(f"Error: {error_message}\n")
                        f.write(f"Files completed before failure: {dest_completed_files}/{reported_total}\n")
                        f.write(f"Data transferred: {dest_completed_bytes / (1024**3):.2f} GB\n")
                    else:
                        f.write(f"Total files: {dest_completed_files}/{reported_total}\n")
                        f.write(f"Total size: {dest_completed_bytes / (1024**3):.2f} GB\n")

                    f.write(f"Duration: {elapsed:.1f} seconds\n")
                    if dest_completed_bytes > 0 and elapsed > 0:
                        avg_speed = (dest_completed_bytes / (1024 * 1024)) / elapsed
                        f.write(f"Average speed: {avg_speed:.1f} MB/s\n")
                    f.write("=" * 80 + "\n")

                # Generate ASC MHL (Media Hash List) file - industry standard for DIT
                try:
                    from .asc_mhl_generator import ASCMHLGenerator
                    mhl_generator = ASCMHLGenerator()
                    mhl_path = paths.get('mhl')
                    if mhl_path:
                        # MHL files need the file records from the JSON report
                        mhl_file_records = report.get('files', [])
                        if mhl_generator.generate_mhl(mhl_file_records, mhl_path, process_type="transfer"):
                            print(f"   [OK] ASC MHL file generated: {mhl_path}")
                        else:
                            print(f"   WARNING: ASC MHL generation failed")
                except Exception as mhl_error:
                    print(f"   WARNING: Could not generate ASC MHL file: {mhl_error}")

                # Mark as finalized to prevent duplicate finalization
                self.finalized_destinations.add(dest_key)

                print(f"[OK] Per-destination report finalized for: {display_dest}")
                print(f"   JSON: {paths['json']}")
                print(f"   CSV: {paths['csv']}")
                print(f"   TXT: {paths['txt']}")
                print(f"   MHL: {paths.get('mhl', 'N/A')}")
                print(f"   Status: {status}")

            except Exception as e:
                print(f"[ERROR] Error finalizing report for {dest_path}: {e}")
                import traceback
                traceback.print_exc()

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

                    print(f"[OK] Reports finalized for: {display_dest}")

                except Exception as e:
                    print(f"[ERROR] Error finalizing reports for {dest_path}: {e}")

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


def start_realtime_reporting(job_id: str, source_path: str, destinations: List[str], expected_total_files: int = 0) -> RealtimeReportWriter:
    """Start a new real-time reporting session"""
    global _realtime_writer

    with _writer_lock:
        # Close previous writer if exists
        if _realtime_writer:
            _realtime_writer.finalize_reports("INTERRUPTED")

        # Create new writer
        _realtime_writer = RealtimeReportWriter(job_id, source_path, destinations, expected_total_files)
        return _realtime_writer


def stop_realtime_reporting(final_status: str = "COMPLETED", error_message: str = None):
    """Stop real-time reporting and finalize reports"""
    global _realtime_writer

    with _writer_lock:
        if _realtime_writer:
            _realtime_writer.finalize_reports(final_status, error_message)
            _realtime_writer = None
