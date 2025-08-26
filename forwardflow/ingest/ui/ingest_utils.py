"""Utility functions for the Ingest Tab"""

import os
import json
from pathlib import Path
from typing import List, Tuple


def load_recent_locations() -> Tuple[List[str], List[str]]:
    """Load recent source and destination locations from config"""
    try:
        from app.core.config_manager import get_settings_path
        settings_dir = get_settings_path()
        recent_file = os.path.join(settings_dir, "recent_locations.json")
        
        if os.path.exists(recent_file):
            with open(recent_file, 'r') as f:
                data = json.load(f)
                return data.get('sources', []), data.get('destinations', [])
    except Exception as e:
        print(f"DEBUG: Failed to load recent locations: {e}")
    
    return [], []


def save_recent_locations(sources: List[str], destinations: List[str]) -> None:
    """Save recent source and destination locations to config"""
    try:
        from app.core.config_manager import get_settings_path
        settings_dir = get_settings_path()
        recent_file = os.path.join(settings_dir, "recent_locations.json")
        
        data = {
            'sources': sources[:5],  # Keep last 5
            'destinations': destinations[:5]  # Keep last 5
        }
        
        with open(recent_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"DEBUG: Failed to save recent locations: {e}")


def add_to_recent_locations(path: str, is_source: bool = True) -> None:
    """Add a path to recent locations"""
    sources, destinations = load_recent_locations()
    
    if is_source:
        if path in sources:
            sources.remove(path)
        sources.insert(0, path)
        sources = sources[:5]  # Keep last 5
    else:
        if path in destinations:
            destinations.remove(path)
        destinations.insert(0, path)
        destinations = destinations[:5]  # Keep last 5
    
    save_recent_locations(sources, destinations)


def detect_transfer_type(destination_path: str) -> str:
    """Detect transfer type based on destination path"""
    try:
        # Simple detection based on volume name
        volume_name = Path(destination_path).parts[1] if len(Path(destination_path).parts) > 1 else ""
        
        if "SSD" in volume_name.upper() or "NVME" in volume_name.upper():
            return "usb_ssd"
        elif "HDD" in volume_name.upper() or "HD" in volume_name.upper():
            return "usb_hdd"
        elif "NETWORK" in volume_name.upper() or "NAS" in volume_name.upper():
            return "network"
        else:
            return "local"
    except Exception:
        return "local"


def calculate_optimal_buffer(transfer_type: str) -> float:
    """Calculate optimal buffer size based on transfer type"""
    buffer_sizes = {
        "usb_ssd": 4.0,
        "usb_hdd": 2.0,
        "network": 1.0,
        "local": 8.0
    }
    return buffer_sizes.get(transfer_type, 2.0)
