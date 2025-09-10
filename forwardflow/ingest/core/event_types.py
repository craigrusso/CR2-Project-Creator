"""
ForwardFlow V2.0 - Event Type Definitions

Defines the comprehensive event system for professional DIT workflows
with proper type safety and clear separation of concerns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum
import time


class EventType(Enum):
    """Core event types for the ForwardFlow V2.0 system"""
    # File-level events
    FILE_STARTED = "file.started"
    FILE_PROGRESS = "file.progress"  
    FILE_COMPLETED = "file.completed"
    FILE_ERROR = "file.error"
    FILE_HASH_CALCULATED = "file.hash_calculated"
    
    # Destination-level events
    DEST_STARTED = "dest.started"
    DEST_PROGRESS = "dest.progress"
    DEST_COMPLETED = "dest.completed"
    DEST_ERROR = "dest.error"
    
    # Job-level events
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_COMPLETED = "job.completed"
    JOB_CANCELLED = "job.cancelled"
    JOB_ERROR = "job.error"
    JOB_STRATEGY_SELECTED = "job.strategy_selected"
    
    # BLAST workflow events
    BLAST_INITIATED = "blast.initiated"
    BLAST_COMPLETED = "blast.completed"
    BLAST_DISTRIBUTION_STARTED = "blast.distribution_started"
    BLAST_DISTRIBUTION_COMPLETED = "blast.distribution_completed"
    
    # UI events
    UI_UPDATE_PROGRESS = "ui.update_progress"
    UI_UPDATE_SPEED = "ui.update_speed"
    UI_SHOW_RESUME = "ui.show_resume"
    UI_UPDATE_STATUS = "ui.update_status"
    
    # System events
    SYSTEM_RESUME_AVAILABLE = "system.resume_available"
    SYSTEM_CHECKPOINT_SAVED = "system.checkpoint_saved"


@dataclass
class TransferEvent(ABC):
    """Base class for all transfer events"""
    event_type: EventType
    timestamp: float
    job_id: str
    payload: Dict[str, Any]
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


@dataclass  
class FileEvent(TransferEvent):
    """File-level events for individual file operations"""
    file_id: str
    filename: str
    file_size: int
    bytes_copied: int = 0
    destination_path: str = ""
    source_checksum: str = ""
    destination_checksum: str = ""
    hash_algorithm: str = "xxHash64BE"
    transfer_speed_mbps: float = 0.0
    error_message: str = ""


@dataclass
class DestinationEvent(TransferEvent):
    """Destination-level events for individual destination progress"""
    destination_path: str
    destination_index: int
    progress_percent: float = 0.0
    bytes_copied: int = 0
    total_bytes: int = 0
    completed_files: int = 0
    total_files: int = 0
    current_speed_mbps: float = 0.0
    peak_speed_mbps: float = 0.0
    eta_seconds: float = 0.0
    error_message: str = ""


@dataclass
class JobEvent(TransferEvent):
    """Job-level events for overall transfer progress"""
    total_destinations: int
    completed_destinations: int = 0
    total_speed_mbps: float = 0.0  # Sum of all destination speeds
    peak_speed_mbps: float = 0.0
    progress_percent: float = 0.0  # Based on slowest destination
    eta_seconds: float = 0.0
    total_bytes: int = 0
    copied_bytes: int = 0
    total_files: int = 0
    completed_files: int = 0
    strategy_name: str = ""
    error_message: str = ""


@dataclass
class UIEvent(TransferEvent):
    """UI-specific events for main thread updates"""
    ui_component: str
    action: str
    data: Dict[str, Any]


@dataclass
class BlastEvent(TransferEvent):
    """BLAST workflow specific events"""
    blast_drive_path: str
    distribution_destinations: List[str]
    blast_progress_percent: float = 0.0
    distribution_progress_percent: float = 0.0
    phase: str = "initiated"  # initiated, blast_complete, distributing, completed


class EventPriority(Enum):
    """Event processing priorities"""
    CRITICAL = 1    # BLAST completion, errors
    HIGH = 2        # File completion, destination completion  
    NORMAL = 3      # Progress updates
    LOW = 4         # UI updates, status changes


@dataclass
class PrioritizedEvent:
    """Event wrapper with priority for queue processing"""
    event: TransferEvent
    priority: EventPriority
    
    def __lt__(self, other):
        return self.priority.value < other.priority.value