#!/usr/bin/env python3
"""
DIT Data Collector for Transfer Operations
Collects file.complete events and builds comprehensive file records for DIT reports
"""

import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading


class DITDataCollector:
    """Collects DIT-compliant data during transfers for comprehensive reporting"""

    def __init__(self):
        # Use dict keyed by (filename, dest_path) to track unique files and allow updates
        self.file_records_dict: Dict[tuple, Dict[str, Any]] = {}
        
        # CRITICAL FIX: Per-destination file tracking for independent reports
        # Key: dest_index (int) -> Value: Dict of (filename, dest_path) -> file_record
        self.files_by_destination: Dict[int, Dict[tuple, Dict[str, Any]]] = {}
        
        self.job_stats: Dict[str, Any] = {}
        self.destination_stats: Dict[int, Dict[str, Any]] = {}
        self.destination_paths: Dict[int, str] = {}
        self.lock = threading.Lock()
        self.job_id: Optional[str] = None
        self.start_time: Optional[float] = None

    def reset(self, job_id: str):
        """Reset collector for new job"""
        with self.lock:
            self.file_records_dict.clear()
            self.files_by_destination.clear()  # CRITICAL FIX: Clear per-destination tracking
            self.job_stats.clear()
            self.destination_stats.clear()
            self.destination_paths.clear()
            self.job_id = job_id
            self.start_time = time.time()
            print(f"DEBUG: DITDataCollector reset for job: {job_id}")
            print(f"🔍 DEBUG: Collector instance {id(self)} reset - file_records and per-dest tracking cleared")
    
    def handle_file_complete_event(self, payload: Dict[str, Any]):
        """Handle file.complete events from Rust engine - updates existing records if hash data arrives later"""
        with self.lock:
            try:
                # Extract file completion data
                filename = payload.get('filename', 'unknown')
                source_path = payload.get('source_path', '')
                dest_path = payload.get('dest_path', '')
                size_bytes = payload.get('size_bytes', 0)
                source_checksum = payload.get('source_checksum', '')
                destination_checksum = payload.get('destination_checksum', '')
                hash_algorithm = payload.get('hash_algorithm', 'unknown')
                if not hash_algorithm or hash_algorithm.lower() == 'none':
                    hash_algorithm = 'unknown'
                verification_passed = payload.get('verification_passed', False)
                transfer_status = payload.get('transfer_status', 'COMPLETED')
                status = payload.get('status', 'COMPLETED')
                dest_index = payload.get('dest_index', payload.get('destination_index', 0))

                if not dest_path and dest_index in self.destination_paths:
                    dest_path = self.destination_paths[dest_index]

                if dest_path and dest_index not in self.destination_paths:
                    self.destination_paths[dest_index] = dest_path

                if not dest_path:
                    print(f"WARNING: DITDataCollector received file without destination path (index={dest_index}, file={filename})")
                    dest_path = f"destination_{dest_index}"

                # Use (filename, dest_path) as unique key to allow updates
                record_key = (filename, dest_path)

                # Check if we already have a record for this file
                existing_record = self.file_records_dict.get(record_key)

                if existing_record:
                    # UPDATE existing record - only overwrite fields if new data has values
                    if source_checksum:  # Update hash only if non-empty
                        existing_record['source_checksum'] = source_checksum
                        existing_record['checksum'] = source_checksum
                    if destination_checksum:
                        existing_record['destination_checksum'] = destination_checksum
                    if hash_algorithm and hash_algorithm != 'none':
                        existing_record['hash_algorithm'] = hash_algorithm
                    existing_record['verification_passed'] = verification_passed
                    existing_record['transfer_status'] = transfer_status
                    existing_record['status'] = status
                    existing_record['modification_time'] = time.time()
                    existing_record['dest_index'] = dest_index
                    existing_record['bytes_copied'] = size_bytes or existing_record.get('bytes_copied', 0)

                    print(f"DEBUG: DITDataCollector UPDATED file.complete: {filename} (hash={'YES' if source_checksum else 'NO'})")
                else:
                    # CREATE new record
                    file_record = {
                        'filename': filename,
                        'source_path': source_path,
                        'dest_path': dest_path,
                        'destination_path': dest_path,  # Alternative field name for compatibility
                        'dest_index': dest_index,
                        'size': size_bytes,
                        'size_bytes': size_bytes,  # Alternative field name for compatibility
                        'bytes_copied': size_bytes,
                        'source_checksum': source_checksum,
                        'destination_checksum': destination_checksum,
                        'checksum': source_checksum,  # Use source as primary checksum
                        'hash_algorithm': hash_algorithm,
                        'verification_passed': verification_passed,
                        'transfer_status': transfer_status,
                        'status': status,
                        'transfer_time': time.time() - (self.start_time or time.time()),
                        'modification_time': time.time(),
                        'error_message': ''
                    }

                    self.file_records_dict[record_key] = file_record
                    print(f"DEBUG: DITDataCollector CREATED file.complete: {filename} ({size_bytes} bytes, hash={'YES' if source_checksum else 'NO'})")

                # CRITICAL FIX: Also store in per-destination tracking
                if dest_index not in self.files_by_destination:
                    self.files_by_destination[dest_index] = {}
                
                self.files_by_destination[dest_index][record_key] = self.file_records_dict[record_key]
                print(f"🔥 DEBUG: File also stored for dest_index={dest_index}")

                print(f"🔍 DEBUG: File record in collector instance {id(self)} - total records now: {len(self.file_records_dict)}")

            except Exception as e:
                print(f"ERROR: DITDataCollector failed to handle file.complete event: {e}")
                import traceback
                traceback.print_exc()
    
    def update_job_stats(self, stats: Dict[str, Any]):
        """Update job-level statistics"""
        with self.lock:
            self.job_stats.update(stats)
            print(f"DEBUG: DIT Collector job stats updated: {stats}")
    
    def update_destination_stats(self, dest_index: int, dest_path: str, stats: Dict[str, Any]):
        """Update destination-specific statistics"""
        with self.lock:
            self.destination_stats[dest_index] = {**stats, 'dest_path': dest_path}
            if dest_path:
                self.destination_paths[dest_index] = dest_path
    
    def get_file_records(self) -> List[Dict[str, Any]]:
        """Get all collected file records (global - use get_file_records_for_destination for per-dest)"""
        with self.lock:
            file_records_list = list(self.file_records_dict.values())
            print(f"🔍 DEBUG: get_file_records() called - returning {len(file_records_list)} records")
            print(f"🔍 DEBUG: Current job_id: {self.job_id}")
            print(f"🔍 DEBUG: Collector instance ID: {id(self)}")
            if file_records_list:
                print(f"🔍 DEBUG: Sample record: {file_records_list[0].get('filename', 'unknown')}")
                print(f"🔍 DEBUG: Sample record has hash: {file_records_list[0].get('source_checksum', 'NONE')}")
            return file_records_list
    
    def get_file_records_for_destination(self, dest_index: int) -> List[Dict[str, Any]]:
        """Get file records for a specific destination - CRITICAL for independent reports"""
        with self.lock:
            if dest_index not in self.files_by_destination:
                print(f"🔥 DEBUG: No files found for dest_index={dest_index}")
                return []
            
            dest_files = list(self.files_by_destination[dest_index].values())
            print(f"🔥 DEBUG: get_file_records_for_destination(dest_index={dest_index}) returning {len(dest_files)} files")
            return dest_files
    
    def get_all_destination_indices(self) -> List[int]:
        """Get list of all destination indices that have files"""
        with self.lock:
            return list(self.files_by_destination.keys())
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics (global - use get_stats_for_destination for per-dest)"""
        with self.lock:
            # Calculate derived statistics from dictionary values
            file_records_list = list(self.file_records_dict.values())
            total_files = len(file_records_list)
            completed_files = sum(1 for r in file_records_list if r.get('status') == 'COMPLETED')
            failed_files = sum(1 for r in file_records_list if r.get('status') == 'FAILED')
            cancelled_files = sum(1 for r in file_records_list if r.get('status') == 'CANCELLED')

            total_bytes = sum(r.get('size_bytes', 0) for r in file_records_list)
            completed_bytes = sum(r.get('size_bytes', 0) for r in file_records_list if r.get('status') == 'COMPLETED')
            
            elapsed_time = (time.time() - self.start_time) if self.start_time else 0.0
            average_speed_mbps = (completed_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0.0
            
            stats = {
                'total_files': total_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'cancelled_files': cancelled_files,
                'error_files': failed_files,  # Alias for compatibility
                'total_bytes': total_bytes,
                'completed_bytes': completed_bytes,
                'copied_bytes': completed_bytes,  # Alias for compatibility
                'elapsed_time': elapsed_time,
                'duration': elapsed_time,  # Alias for compatibility
                'average_speed_mbps': average_speed_mbps,
                'avg_speed': average_speed_mbps,  # Alias for compatibility
                'peak_speed': self.job_stats.get('peak_speed', 0.0),
            }
            
            # Merge with existing job stats
            stats.update(self.job_stats)
            return stats
    
    def get_stats_for_destination(self, dest_index: int) -> Dict[str, Any]:
        """Get statistics for a specific destination - CRITICAL for independent reports"""
        with self.lock:
            dest_files_map = self.files_by_destination.get(dest_index)
            if not dest_files_map:
                return {
                    'total_files': 0,
                    'completed_files': 0,
                    'failed_files': 0,
                    'cancelled_files': 0,
                    'error_files': 0,
                    'total_bytes': 0,
                    'completed_bytes': 0,
                    'copied_bytes': 0,
                    'elapsed_time': 0.0,
                    'duration': 0.0,
                    'average_speed_mbps': 0.0,
                    'avg_speed': 0.0,
                    'peak_speed': 0.0,
                    'dest_path': self.destination_paths.get(dest_index, ''),
                }
            
            file_records_list = list(dest_files_map.values())
            total_files = len(file_records_list)
            completed_files = sum(1 for r in file_records_list if r.get('status') == 'COMPLETED')
            failed_files = sum(1 for r in file_records_list if r.get('status') == 'FAILED')
            cancelled_files = sum(1 for r in file_records_list if r.get('status') == 'CANCELLED')

            total_bytes = sum(r.get('size_bytes', 0) for r in file_records_list)
            completed_bytes = sum(r.get('size_bytes', 0) for r in file_records_list if r.get('status') == 'COMPLETED')
            
            elapsed_time = (time.time() - self.start_time) if self.start_time else 0.0
            average_speed_mbps = (completed_bytes / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0.0
            
            destination_stats = self.destination_stats.get(dest_index, {})
            peak_speed = destination_stats.get('peak_speed', 0.0)
            
            stats = {
                'total_files': total_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'cancelled_files': cancelled_files,
                'error_files': failed_files,
                'total_bytes': total_bytes,
                'completed_bytes': completed_bytes,
                'copied_bytes': completed_bytes,
                'elapsed_time': elapsed_time,
                'duration': elapsed_time,
                'average_speed_mbps': average_speed_mbps,
                'avg_speed': average_speed_mbps,
                'peak_speed': peak_speed,
                'dest_path': self.destination_paths.get(dest_index, ''),
            }
            
            print(f"🔥 DEBUG: get_stats_for_destination(dest_index={dest_index}): {total_files} files, {completed_bytes} bytes, {average_speed_mbps:.1f} MB/s avg, {peak_speed:.1f} MB/s peak")
            
            return stats
    
    def get_destination_details(self) -> Dict[str, Any]:
        """Get destination-specific details"""
        with self.lock:
            return {
                idx: {
                    **stats,
                    'dest_path': self.destination_paths.get(idx, ''),
                }
                for idx, stats in self.destination_stats.items()
            }
    
    def has_data(self) -> bool:
        """Check if collector has any data"""
        with self.lock:
            return len(self.file_records_dict) > 0


# Global singleton instance
_dit_collector = None
_collector_lock = threading.Lock()


def get_dit_collector() -> DITDataCollector:
    """Get the global DIT data collector instance"""
    global _dit_collector

    with _collector_lock:
        if _dit_collector is None:
            _dit_collector = DITDataCollector()
            print(f"DEBUG: Created global DITDataCollector instance {id(_dit_collector)}")

        print(f"🔍 DEBUG: Returning DIT collector instance {id(_dit_collector)}")
        return _dit_collector


def reset_dit_collector(job_id: str):
    """Reset the global DIT data collector for new job"""
    collector = get_dit_collector()
    collector.reset(job_id)
