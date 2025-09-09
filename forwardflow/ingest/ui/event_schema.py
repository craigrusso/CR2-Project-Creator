#!/usr/bin/env python3
"""
Comprehensive Event Schema and Routing for ForwardFlow Transfer System
Defines all event types, payloads, and validation rules
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import time


class EventType(Enum):
    """Standardized event types for the transfer system"""
    
    # File-level events
    FILE_PROGRESS = "file.progress"
    FILE_COMPLETED = "file.completed" 
    FILE_STARTED = "file.started"
    FILE_ERROR = "file.error"
    FILE_CANCELLED = "file.cancelled"
    FILE_VERIFIED = "file.verified"
    
    # Job-level events
    JOB_START = "job.start"          # New: job manifest initialization
    JOB_STARTED = "job.started"
    JOB_INITIALIZED = "job.initialized"
    JOB_PROGRESS = "job.progress"
    JOB_COMPLETED = "job.completed"
    JOB_CANCELLED = "job.cancelled"
    JOB_ERROR = "job.error"
    JOB_PAUSED = "job.paused"
    JOB_RESUMED = "job.resumed"
    
    # Destination-level events
    DEST_PROGRESS = "dest.progress"
    DEST_COMPLETED = "dest.completed"
    DEST_ERROR = "dest.error"
    DEST_DISCOVERED = "dest.discovered"
    
    # System events
    SYSTEM_HEARTBEAT = "system.heartbeat"
    SYSTEM_STATUS = "system.status"
    SYSTEM_DEBUG = "system.debug"
    SYSTEM_ERROR = "system.error"
    
    # Engine events
    ENGINE_STARTED = "engine.started"
    ENGINE_STOPPED = "engine.stopped"
    ENGINE_ERROR = "engine.error"
    ENGINE_STATS = "engine.stats"
    
    # Legacy compatibility
    PROGRESS_UPDATE = "progress_update"  # Maps to JOB_PROGRESS
    FILEPROGRESS = "fileprogress"       # Maps to FILE_PROGRESS
    FILECOMPLETED = "filecompleted"     # Maps to FILE_COMPLETED


@dataclass
class BaseEventPayload:
    """Base payload for all events"""
    timestamp: float = field(default_factory=time.time)
    event_id: str = ""
    source: str = "forwardflow"


@dataclass 
class FileEventPayload(BaseEventPayload):
    """Payload for file-level events"""
    file_id: str = ""
    filename: str = ""
    bytes_copied: int = 0
    total_bytes: int = 0
    dest_path: str = ""
    source_path: str = ""
    transfer_speed_mbps: float = 0.0
    checksum: str = ""
    checksum_type: str = "xxHash64"
    error_message: str = ""


@dataclass
class JobStartPayload(BaseEventPayload):
    """Payload for job.start event - immutable manifest"""
    job_id: str = ""
    total_files: int = 0
    total_bytes: int = 0
    destination_count: int = 0
    total_target_bytes: int = 0
    source_path: str = ""
    destinations: List[str] = field(default_factory=list)

@dataclass
class JobProgressPayload(BaseEventPayload):
    """Payload for job.progress event - aggregate progress"""
    job_id: str = ""
    bytes_copied: int = 0
    total_target_bytes: int = 0
    completed_files: int = 0
    total_files: int = 0
    current_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: float = 0.0

@dataclass
class JobEventPayload(BaseEventPayload):
    """Payload for job-level events (legacy compatibility)"""
    job_id: str = ""
    total_files: int = 0
    completed_files: int = 0
    cancelled_files: int = 0
    error_files: int = 0
    total_bytes: int = 0
    copied_bytes: int = 0
    progress_percent: float = 0.0
    current_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    avg_speed_mbps: float = 0.0
    eta_seconds: float = 0.0
    elapsed_seconds: float = 0.0
    destinations: List[str] = field(default_factory=list)
    current_filename: str = ""


@dataclass
class DestinationEventPayload(BaseEventPayload):
    """Payload for destination-level events"""
    dest_path: str = ""
    dest_index: int = 0
    progress_percent: float = 0.0
    bytes_copied: int = 0
    total_bytes: int = 0
    completed_files: int = 0
    total_files: int = 0
    current_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    eta_seconds: float = 0.0
    transfer_type: str = "unknown"
    error_message: str = ""


@dataclass 
class SystemEventPayload(BaseEventPayload):
    """Payload for system-level events"""
    system_status: str = ""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    message: str = ""
    level: str = "info"  # debug, info, warning, error


class EventRouter:
    """
    Comprehensive event router with schema validation and normalization
    """
    
    # Event type normalization map
    EVENT_TYPE_MAP = {
        # File events
        'file.progress': EventType.FILE_PROGRESS,
        'file_progress': EventType.FILE_PROGRESS,
        'fileprogress': EventType.FILE_PROGRESS,
        'fileProgress': EventType.FILE_PROGRESS,
        
        'file.completed': EventType.FILE_COMPLETED,
        'file.complete': EventType.FILE_COMPLETED,
        'file_completed': EventType.FILE_COMPLETED,
        'file_complete': EventType.FILE_COMPLETED,
        'filecompleted': EventType.FILE_COMPLETED,
        'filecomplete': EventType.FILE_COMPLETED,
        'fileCompleted': EventType.FILE_COMPLETED,
        
        'file.started': EventType.FILE_STARTED,
        'file_started': EventType.FILE_STARTED,
        'filestarted': EventType.FILE_STARTED,
        
        'file.error': EventType.FILE_ERROR,
        'file_error': EventType.FILE_ERROR,
        'fileerror': EventType.FILE_ERROR,
        
        'file.cancelled': EventType.FILE_CANCELLED,
        'file_cancelled': EventType.FILE_CANCELLED,
        'filecancelled': EventType.FILE_CANCELLED,
        
        'file.verified': EventType.FILE_VERIFIED,
        'file_verified': EventType.FILE_VERIFIED,
        'fileverified': EventType.FILE_VERIFIED,
        
        # Job events
        'job.start': EventType.JOB_START,
        'job_start': EventType.JOB_START,
        'jobstart': EventType.JOB_START,
        'jobStart': EventType.JOB_START,
        
        'job.started': EventType.JOB_STARTED,
        'job_started': EventType.JOB_STARTED,
        'jobstarted': EventType.JOB_STARTED,
        'jobStarted': EventType.JOB_STARTED,
        
        'job.initialized': EventType.JOB_INITIALIZED,
        'job_initialized': EventType.JOB_INITIALIZED,
        'jobinitialized': EventType.JOB_INITIALIZED,
        'jobInitialized': EventType.JOB_INITIALIZED,
        
        'job.progress': EventType.JOB_PROGRESS,
        'job_progress': EventType.JOB_PROGRESS,
        'jobprogress': EventType.JOB_PROGRESS,
        'jobProgress': EventType.JOB_PROGRESS,
        'progress_update': EventType.JOB_PROGRESS,
        'progressUpdate': EventType.JOB_PROGRESS,
        
        'job.completed': EventType.JOB_COMPLETED,
        'job_completed': EventType.JOB_COMPLETED,
        'jobcompleted': EventType.JOB_COMPLETED,
        'jobCompleted': EventType.JOB_COMPLETED,
        
        'job.cancelled': EventType.JOB_CANCELLED,
        'job_cancelled': EventType.JOB_CANCELLED,
        'jobcancelled': EventType.JOB_CANCELLED,
        'jobCancelled': EventType.JOB_CANCELLED,
        
        'job.error': EventType.JOB_ERROR,
        'job_error': EventType.JOB_ERROR,
        'joberror': EventType.JOB_ERROR,
        'jobError': EventType.JOB_ERROR,
        
        'job.paused': EventType.JOB_PAUSED,
        'job_paused': EventType.JOB_PAUSED,
        'jobpaused': EventType.JOB_PAUSED,
        
        'job.resumed': EventType.JOB_RESUMED,
        'job_resumed': EventType.JOB_RESUMED,
        'jobresumed': EventType.JOB_RESUMED,
        
        # Destination events
        'dest.progress': EventType.DEST_PROGRESS,
        'dest_progress': EventType.DEST_PROGRESS,
        'destprogress': EventType.DEST_PROGRESS,
        'destination_progress': EventType.DEST_PROGRESS,
        'destinationProgress': EventType.DEST_PROGRESS,
        
        'dest.completed': EventType.DEST_COMPLETED,
        'dest_completed': EventType.DEST_COMPLETED,
        'destcompleted': EventType.DEST_COMPLETED,
        'destination_completed': EventType.DEST_COMPLETED,
        
        'dest.error': EventType.DEST_ERROR,
        'dest_error': EventType.DEST_ERROR,
        'desterror': EventType.DEST_ERROR,
        'destination_error': EventType.DEST_ERROR,
        
        'dest.discovered': EventType.DEST_DISCOVERED,
        'dest_discovered': EventType.DEST_DISCOVERED,
        'destdiscovered': EventType.DEST_DISCOVERED,
        
        # System events
        'system.heartbeat': EventType.SYSTEM_HEARTBEAT,
        'heartbeat': EventType.SYSTEM_HEARTBEAT,
        
        'system.status': EventType.SYSTEM_STATUS,
        'status': EventType.SYSTEM_STATUS,
        
        'system.debug': EventType.SYSTEM_DEBUG,
        'debug': EventType.SYSTEM_DEBUG,
        
        'system.error': EventType.SYSTEM_ERROR,
        'system_error': EventType.SYSTEM_ERROR,
        
        # Engine events
        'engine.started': EventType.ENGINE_STARTED,
        'engine_started': EventType.ENGINE_STARTED,
        'enginestarted': EventType.ENGINE_STARTED,
        
        'engine.stopped': EventType.ENGINE_STOPPED,
        'engine_stopped': EventType.ENGINE_STOPPED,
        'enginestopped': EventType.ENGINE_STOPPED,
        
        'engine.error': EventType.ENGINE_ERROR,
        'engine_error': EventType.ENGINE_ERROR,
        'engineerror': EventType.ENGINE_ERROR,
        
        'engine.stats': EventType.ENGINE_STATS,
        'engine_stats': EventType.ENGINE_STATS,
        'enginestats': EventType.ENGINE_STATS,
    }
    
    def __init__(self):
        self.handlers: Dict[EventType, List[callable]] = {}
        self.validation_enabled = True
        self.debug_logging = False
    
    def normalize_event_type(self, event_type: str) -> EventType:
        """
        Normalize event type string to standard EventType enum
        
        Args:
            event_type: Raw event type string from various sources
            
        Returns:
            Normalized EventType enum value
        """
        if isinstance(event_type, EventType):
            return event_type
            
        # Normalize string
        normalized = event_type.lower().strip()
        
        # Look up in mapping
        if normalized in self.EVENT_TYPE_MAP:
            return self.EVENT_TYPE_MAP[normalized]
        
        # Try case-insensitive search
        for key, value in self.EVENT_TYPE_MAP.items():
            if key.lower() == normalized:
                return value
        
        # Log unknown event type for debugging
        if self.debug_logging:
            print(f"DEBUG: Unknown event type: {event_type}, treating as system.debug")
        
        return EventType.SYSTEM_DEBUG
    
    def validate_payload(self, event_type: EventType, payload: Dict[str, Any]) -> bool:
        """
        Validate event payload against schema
        
        Args:
            event_type: Normalized event type
            payload: Event payload dictionary
            
        Returns:
            True if payload is valid, False otherwise
        """
        if not self.validation_enabled:
            return True
        
        try:
            # Basic validation - check for required fields based on event type
            if event_type in [EventType.FILE_PROGRESS, EventType.FILE_COMPLETED, EventType.FILE_STARTED]:
                required_fields = ['file_id', 'bytes_copied', 'total_bytes']
                for field in required_fields:
                    if field not in payload and 'filename' not in payload:
                        if self.debug_logging:
                            print(f"DEBUG: Missing required field '{field}' for {event_type.value}")
                        return False
            
            elif event_type in [EventType.JOB_PROGRESS, EventType.JOB_STARTED, EventType.JOB_COMPLETED]:
                if 'total_files' not in payload and 'progress_percent' not in payload:
                    if self.debug_logging:
                        print(f"DEBUG: Missing job-level fields for {event_type.value}")
                    return False
            
            elif event_type in [EventType.DEST_PROGRESS, EventType.DEST_COMPLETED]:
                if 'dest_path' not in payload:
                    if self.debug_logging:
                        print(f"DEBUG: Missing dest_path for {event_type.value}")
                    return False
            
            return True
            
        except Exception as e:
            if self.debug_logging:
                print(f"DEBUG: Payload validation error: {e}")
            return False
    
    def route_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Route event to appropriate handlers with schema validation
        
        Args:
            event_type: Raw event type string
            payload: Event payload dictionary
            
        Returns:
            True if event was successfully routed, False otherwise
        """
        try:
            # Normalize event type
            normalized_type = self.normalize_event_type(event_type)
            
            # Validate payload
            if not self.validate_payload(normalized_type, payload):
                if self.debug_logging:
                    print(f"DEBUG: Invalid payload for {event_type} -> {normalized_type.value}")
                return False
            
            # Add routing metadata to payload
            routing_payload = payload.copy()
            routing_payload['_original_event_type'] = event_type
            routing_payload['_normalized_event_type'] = normalized_type.value
            routing_payload['_routing_timestamp'] = time.time()
            
            # Call registered handlers
            if normalized_type in self.handlers:
                for handler in self.handlers[normalized_type]:
                    try:
                        handler(normalized_type.value, routing_payload)
                    except Exception as e:
                        if self.debug_logging:
                            print(f"DEBUG: Handler error for {normalized_type.value}: {e}")
                        continue
            
            # Log successful routing
            if self.debug_logging:
                print(f"DEBUG: Successfully routed {event_type} -> {normalized_type.value}")
            
            return True
            
        except Exception as e:
            if self.debug_logging:
                print(f"DEBUG: Event routing error: {e}")
            return False
    
    def register_handler(self, event_type: EventType, handler: callable):
        """Register a handler for specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: EventType, handler: callable):
        """Unregister a handler for specific event type"""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def clear_handlers(self, event_type: Optional[EventType] = None):
        """Clear handlers for specific event type or all handlers"""
        if event_type:
            self.handlers[event_type] = []
        else:
            self.handlers.clear()
    
    def enable_debug_logging(self, enabled: bool = True):
        """Enable or disable debug logging"""
        self.debug_logging = enabled
    
    def enable_validation(self, enabled: bool = True):
        """Enable or disable payload validation"""
        self.validation_enabled = enabled
    
    def get_supported_event_types(self) -> List[str]:
        """Get list of all supported event type strings"""
        return list(self.EVENT_TYPE_MAP.keys())
    
    def get_schema_for_event_type(self, event_type: EventType) -> Dict[str, Any]:
        """Get expected schema for a specific event type"""
        schemas = {
            EventType.FILE_PROGRESS: {
                "required": ["file_id", "bytes_copied", "total_bytes"],
                "optional": ["filename", "dest_path", "source_path", "transfer_speed_mbps", "checksum", "error_message"]
            },
            EventType.FILE_COMPLETED: {
                "required": ["file_id", "total_bytes"],
                "optional": ["filename", "dest_path", "checksum", "checksum_type", "transfer_speed_mbps"]
            },
            EventType.JOB_PROGRESS: {
                "required": ["progress_percent"],
                "optional": ["total_files", "completed_files", "total_bytes", "copied_bytes", "current_speed_mbps", "eta_seconds"]
            },
            EventType.JOB_STARTED: {
                "required": ["job_id"],
                "optional": ["total_files", "destinations", "source_path"]
            },
            EventType.DEST_PROGRESS: {
                "required": ["dest_path"],
                "optional": ["progress_percent", "bytes_copied", "total_bytes", "current_speed_mbps", "eta_seconds"]
            }
        }
        
        return schemas.get(event_type, {"required": [], "optional": []})


# Global event router instance
global_event_router = EventRouter()