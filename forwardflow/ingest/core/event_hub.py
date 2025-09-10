"""
ForwardFlow V2.0 - Professional EventHub Implementation

Thread-safe, high-performance event distribution system for professional
DIT workflows. Separates concerns across specialized handlers running
on dedicated threads for optimal performance and reliability.
"""

import threading
import queue
from queue import PriorityQueue, Queue
from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time
import weakref

from .event_types import (
    TransferEvent, FileEvent, DestinationEvent, JobEvent, UIEvent, BlastEvent,
    EventType, EventPriority, PrioritizedEvent
)


class EventHandler(threading.Thread):
    """Base class for specialized event handlers"""
    
    def __init__(self, name: str, event_queue: Queue, max_queue_size: int = 10000):
        super().__init__(name=name, daemon=True)
        self.event_queue = event_queue
        self.max_queue_size = max_queue_size
        self._stop_event = threading.Event()
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._processing_stats = {
            'events_processed': 0,
            'events_dropped': 0,
            'avg_processing_time_ms': 0.0,
            'last_processing_time': 0.0
        }
        
    def register_handler(self, event_type: EventType, handler: Callable[[TransferEvent], None]):
        """Register a handler function for a specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
    def unregister_handler(self, event_type: EventType, handler: Callable):
        """Unregister a specific handler"""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
                
    def stop(self):
        """Signal the handler thread to stop"""
        self._stop_event.set()
        
    def run(self):
        """Main event processing loop"""
        print(f"DEBUG: {self.name} event handler started")
        
        while not self._stop_event.is_set():
            try:
                # Get event with timeout to allow checking stop condition
                if isinstance(self.event_queue, PriorityQueue):
                    prioritized_event = self.event_queue.get(timeout=0.1)
                    event = prioritized_event.event
                else:
                    event = self.event_queue.get(timeout=0.1)
                    
                self._process_event(event)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"ERROR: {self.name} event handler error: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"DEBUG: {self.name} event handler stopped")
        
    def _process_event(self, event: TransferEvent):
        """Process a single event"""
        start_time = time.time()
        
        try:
            if event.event_type in self._handlers:
                for handler in self._handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"ERROR: Handler {handler.__name__} failed: {e}")
                        
            self._processing_stats['events_processed'] += 1
            
        except Exception as e:
            print(f"ERROR: Event processing failed: {e}")
            
        finally:
            processing_time = (time.time() - start_time) * 1000  # ms
            self._update_processing_stats(processing_time)
            
    def _update_processing_stats(self, processing_time_ms: float):
        """Update processing performance statistics"""
        self._processing_stats['last_processing_time'] = time.time()
        
        # Running average of processing times
        current_avg = self._processing_stats['avg_processing_time_ms']
        processed_count = self._processing_stats['events_processed']
        
        if processed_count == 1:
            self._processing_stats['avg_processing_time_ms'] = processing_time_ms
        else:
            # Weighted average favoring recent measurements
            weight = 0.1
            self._processing_stats['avg_processing_time_ms'] = (
                (1 - weight) * current_avg + weight * processing_time_ms
            )
            
    def get_stats(self) -> Dict[str, any]:
        """Get processing statistics for monitoring"""
        return self._processing_stats.copy()


class FileEventHandler(EventHandler):
    """Specialized handler for file-level events"""
    
    def __init__(self):
        super().__init__("FileEventHandler", PriorityQueue(), max_queue_size=50000)
        
        # Register default handlers
        self.register_handler(EventType.FILE_STARTED, self._handle_file_started)
        self.register_handler(EventType.FILE_PROGRESS, self._handle_file_progress)
        self.register_handler(EventType.FILE_COMPLETED, self._handle_file_completed)
        self.register_handler(EventType.FILE_ERROR, self._handle_file_error)
        self.register_handler(EventType.FILE_HASH_CALCULATED, self._handle_hash_calculated)
        
    def _handle_file_started(self, event: FileEvent):
        """Handle file transfer start"""
        print(f"📂 FILE STARTED: {event.filename} ({event.file_size:,} bytes)")
        
    def _handle_file_progress(self, event: FileEvent):
        """Handle file transfer progress (throttled logging)"""
        if hasattr(self, '_last_progress_log'):
            if time.time() - self._last_progress_log < 1.0:  # Log once per second max
                return
        
        progress_percent = (event.bytes_copied / event.file_size * 100) if event.file_size > 0 else 0
        print(f"📈 FILE PROGRESS: {event.filename} - {progress_percent:.1f}% @ {event.transfer_speed_mbps:.1f} MB/s")
        self._last_progress_log = time.time()
        
    def _handle_file_completed(self, event: FileEvent):
        """Handle file transfer completion"""
        print(f"✅ FILE COMPLETED: {event.filename}")
        if event.source_checksum:
            print(f"   Hash: {event.source_checksum} ({event.hash_algorithm})")
            
    def _handle_file_error(self, event: FileEvent):
        """Handle file transfer error"""
        print(f"❌ FILE ERROR: {event.filename} - {event.error_message}")
        
    def _handle_hash_calculated(self, event: FileEvent):
        """Handle hash calculation completion"""
        print(f"🔐 HASH CALCULATED: {event.filename} - {event.source_checksum}")


class DestinationEventHandler(EventHandler):
    """Specialized handler for destination-level events"""
    
    def __init__(self):
        super().__init__("DestinationEventHandler", Queue(), max_queue_size=10000)
        
        # Register default handlers  
        self.register_handler(EventType.DEST_STARTED, self._handle_dest_started)
        self.register_handler(EventType.DEST_PROGRESS, self._handle_dest_progress)
        self.register_handler(EventType.DEST_COMPLETED, self._handle_dest_completed)
        self.register_handler(EventType.DEST_ERROR, self._handle_dest_error)
        
    def _handle_dest_started(self, event: DestinationEvent):
        """Handle destination transfer start"""
        print(f"🎯 DESTINATION STARTED: {event.destination_path}")
        
    def _handle_dest_progress(self, event: DestinationEvent):
        """Handle destination progress updates"""
        print(f"🚀 DEST PROGRESS: {event.destination_path} - "
              f"{event.progress_percent:.1f}% @ {event.current_speed_mbps:.1f} MB/s")
        
    def _handle_dest_completed(self, event: DestinationEvent):
        """Handle destination completion - triggers immediate DIT report generation"""
        print(f"🎉 DESTINATION COMPLETED: {event.destination_path}")
        print(f"   Final stats: {event.bytes_copied:,} bytes, Peak: {event.peak_speed_mbps:.1f} MB/s")
        
        # TODO: Trigger immediate DIT report generation for this destination
        
    def _handle_dest_error(self, event: DestinationEvent):
        """Handle destination transfer error"""
        print(f"❌ DESTINATION ERROR: {event.destination_path} - {event.error_message}")


class JobEventHandler(EventHandler):
    """Specialized handler for job-level events"""
    
    def __init__(self):
        super().__init__("JobEventHandler", Queue(), max_queue_size=5000)
        
        # Register default handlers
        self.register_handler(EventType.JOB_STARTED, self._handle_job_started)
        self.register_handler(EventType.JOB_PROGRESS, self._handle_job_progress)
        self.register_handler(EventType.JOB_COMPLETED, self._handle_job_completed)
        self.register_handler(EventType.JOB_CANCELLED, self._handle_job_cancelled)
        self.register_handler(EventType.JOB_ERROR, self._handle_job_error)
        self.register_handler(EventType.JOB_STRATEGY_SELECTED, self._handle_strategy_selected)
        
    def _handle_job_started(self, event: JobEvent):
        """Handle job start"""
        print(f"🚀 JOB STARTED: {event.job_id} - Strategy: {event.strategy_name}")
        print(f"   Destinations: {event.total_destinations}, Files: {event.total_files}")
        
    def _handle_job_progress(self, event: JobEvent):
        """Handle job-level progress updates"""
        print(f"📊 JOB PROGRESS: {event.progress_percent:.1f}% - "
              f"TOTAL SPEED: {event.total_speed_mbps:.1f} MB/s "
              f"({event.completed_files}/{event.total_files} files)")
        
    def _handle_job_completed(self, event: JobEvent):
        """Handle job completion"""
        print(f"🎉 JOB COMPLETED: {event.job_id}")
        print(f"   Total bytes: {event.copied_bytes:,}, Peak speed: {event.peak_speed_mbps:.1f} MB/s")
        
    def _handle_job_cancelled(self, event: JobEvent):
        """Handle job cancellation"""
        print(f"⏹️ JOB CANCELLED: {event.job_id}")
        
    def _handle_job_error(self, event: JobEvent):
        """Handle job-level error"""
        print(f"❌ JOB ERROR: {event.job_id} - {event.error_message}")
        
    def _handle_strategy_selected(self, event: JobEvent):
        """Handle transfer strategy selection"""
        print(f"🧠 STRATEGY SELECTED: {event.strategy_name} for job {event.job_id}")


class EventHub:
    """
    Professional thread-safe event distribution hub for ForwardFlow V2.0
    
    Manages specialized event handlers on separate threads for optimal
    performance and proper separation of concerns in DIT workflows.
    """
    
    def __init__(self):
        self._handlers: Dict[str, EventHandler] = {}
        self._running = False
        self._stats = {
            'total_events_emitted': 0,
            'events_by_type': {},
            'start_time': time.time()
        }
        
        # Initialize specialized handlers
        self.file_handler = FileEventHandler()
        self.dest_handler = DestinationEventHandler() 
        self.job_handler = JobEventHandler()
        
        self._handlers['file'] = self.file_handler
        self._handlers['destination'] = self.dest_handler
        self._handlers['job'] = self.job_handler
        
        # UI events handled on main thread via direct callbacks
        self._ui_callbacks: List[Callable[[UIEvent], None]] = []
        
    def start(self):
        """Start all event handler threads"""
        if self._running:
            return
            
        print("DEBUG: Starting EventHub with specialized handlers...")
        
        for name, handler in self._handlers.items():
            handler.start()
            print(f"DEBUG: Started {name} handler thread")
            
        self._running = True
        print("DEBUG: EventHub fully operational")
        
    def stop(self):
        """Stop all event handler threads"""
        if not self._running:
            return
            
        print("DEBUG: Stopping EventHub...")
        
        for name, handler in self._handlers.items():
            handler.stop()
            
        # Wait for threads to complete
        for name, handler in self._handlers.items():
            handler.join(timeout=5.0)
            if handler.is_alive():
                print(f"WARNING: {name} handler did not stop cleanly")
            else:
                print(f"DEBUG: {name} handler stopped successfully")
                
        self._running = False
        print("DEBUG: EventHub stopped")
        
    def emit_event(self, event: TransferEvent, priority: EventPriority = EventPriority.NORMAL):
        """
        Emit an event to the appropriate specialized handler
        
        Events are routed based on type to dedicated handler threads:
        - FileEvent -> FileEventHandler (Thread 1)
        - DestinationEvent -> DestinationEventHandler (Thread 2) 
        - JobEvent -> JobEventHandler (Thread 3)
        - UIEvent -> Main thread callbacks (Thread 0)
        """
        if not self._running:
            print("WARNING: EventHub not running, dropping event")
            return
            
        self._update_stats(event)
        
        try:
            # Route to appropriate handler based on event type
            if isinstance(event, FileEvent):
                prioritized = PrioritizedEvent(event, priority)
                self.file_handler.event_queue.put(prioritized, block=False)
                
            elif isinstance(event, DestinationEvent):
                self.dest_handler.event_queue.put(event, block=False)
                
            elif isinstance(event, JobEvent):
                self.job_handler.event_queue.put(event, block=False)
                
            elif isinstance(event, UIEvent):
                # UI events processed immediately on main thread
                self._handle_ui_event(event)
                
            else:
                print(f"WARNING: Unknown event type: {type(event)}")
                
        except queue.Full:
            print(f"WARNING: Event queue full, dropping {type(event).__name__}")
            self._stats['events_dropped'] = self._stats.get('events_dropped', 0) + 1
            
    def register_ui_callback(self, callback: Callable[[UIEvent], None]):
        """Register callback for UI events (main thread only)"""
        self._ui_callbacks.append(callback)
        
    def _handle_ui_event(self, event: UIEvent):
        """Handle UI events on main thread"""
        for callback in self._ui_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"ERROR: UI callback failed: {e}")
                
    def _update_stats(self, event: TransferEvent):
        """Update emission statistics"""
        self._stats['total_events_emitted'] += 1
        
        event_type_name = event.event_type.value
        if event_type_name not in self._stats['events_by_type']:
            self._stats['events_by_type'][event_type_name] = 0
        self._stats['events_by_type'][event_type_name] += 1
        
    def get_performance_stats(self) -> Dict[str, any]:
        """Get comprehensive performance statistics"""
        uptime = time.time() - self._stats['start_time']
        
        stats = {
            'hub_stats': {
                'uptime_seconds': uptime,
                'total_events_emitted': self._stats['total_events_emitted'],
                'events_per_second': self._stats['total_events_emitted'] / uptime if uptime > 0 else 0,
                'events_by_type': self._stats['events_by_type'],
                'running': self._running
            },
            'handler_stats': {}
        }
        
        # Get stats from each handler
        for name, handler in self._handlers.items():
            stats['handler_stats'][name] = handler.get_stats()
            
        return stats
        
    def register_file_handler(self, event_type: EventType, handler: Callable[[FileEvent], None]):
        """Register custom file event handler"""
        self.file_handler.register_handler(event_type, handler)
        
    def register_dest_handler(self, event_type: EventType, handler: Callable[[DestinationEvent], None]):
        """Register custom destination event handler"""  
        self.dest_handler.register_handler(event_type, handler)
        
    def register_job_handler(self, event_type: EventType, handler: Callable[[JobEvent], None]):
        """Register custom job event handler"""
        self.job_handler.register_handler(event_type, handler)