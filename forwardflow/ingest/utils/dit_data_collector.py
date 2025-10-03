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
        self.job_stats: Dict[str, Any] = {}
        self.destination_stats: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.job_id: Optional[str] = None
        self.start_time: Optional[float] = None

    def reset(self, job_id: str):
        """Reset collector for new job"""
        with self.lock:
            self.file_records_dict.clear()
            self.job_stats.clear()
            self.destination_stats.clear()
            self.job_id = job_id
            self.start_time = time.time()
            print(f"DEBUG: DITDataCollector reset for job: {job_id}")
            print(f"🔍 DEBUG: Collector instance {id(self)} reset - file_records cleared")
    
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
    
    def update_destination_stats(self, dest_path: str, stats: Dict[str, Any]):
        """Update destination-specific statistics"""
        with self.lock:
            self.destination_stats[dest_path] = stats
    
    def get_file_records(self) -> List[Dict[str, Any]]:
        """Get all collected file records"""
        with self.lock:
            file_records_list = list(self.file_records_dict.values())
            print(f"🔍 DEBUG: get_file_records() called - returning {len(file_records_list)} records")
            print(f"🔍 DEBUG: Current job_id: {self.job_id}")
            print(f"🔍 DEBUG: Collector instance ID: {id(self)}")
            if file_records_list:
                print(f"🔍 DEBUG: Sample record: {file_records_list[0].get('filename', 'unknown')}")
                print(f"🔍 DEBUG: Sample record has hash: {file_records_list[0].get('source_checksum', 'NONE')}")
            return file_records_list
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics"""
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
    
    def get_destination_details(self) -> Dict[str, Any]:
        """Get destination-specific details"""
        with self.lock:
            return self.destination_stats.copy()
    
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
