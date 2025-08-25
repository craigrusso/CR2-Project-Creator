#!/usr/bin/env python3
"""
Memory Manager for Ingest Engine
Handles adaptive memory allocation and buffer size optimization
"""

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("WARNING: psutil not available. Memory management will use fallback values.")

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MemoryConfig:
    """Memory configuration for transfer operations"""
    buffer_size_mb: float
    max_concurrent_buffers: int
    total_memory_mb: float
    available_memory_mb: float
    memory_allocation_percent: float
    adaptive_enabled: bool


class MemoryManager:
    """Manages memory allocation for transfer operations"""
    
    def __init__(self):
        self.system_memory = self._get_system_memory()
        self.current_config = None
    
    def _get_system_memory(self) -> float:
        """Get total system memory in MB"""
        if PSUTIL_AVAILABLE:
            try:
                # Get total physical memory
                total_memory = psutil.virtual_memory().total / (1024 * 1024)
                
                # For Apple Silicon with unified memory, this should be accurate
                # For other systems, this will also be accurate
                print(f"DEBUG: Detected system memory: {total_memory:.1f}MB")
                return total_memory
            except Exception as e:
                print(f"DEBUG: Error getting memory via psutil: {e}")
        
        # Fallback to 32GB for modern systems (was 16GB)
        print("DEBUG: Using fallback memory value: 32GB")
        return 32768.0
    
    def get_available_memory(self) -> float:
        """Get currently available memory in MB"""
        if PSUTIL_AVAILABLE:
            try:
                available = psutil.virtual_memory().available / (1024 * 1024)
                print(f"DEBUG: Available memory: {available:.1f}MB")
                return available
            except Exception as e:
                print(f"DEBUG: Error getting available memory: {e}")
        
        # Fallback to 25% of total memory
        fallback = self.system_memory * 0.25
        print(f"DEBUG: Using fallback available memory: {fallback:.1f}MB")
        return fallback
    
    def calculate_buffer_size(self, preset: str, allocation_percent: float, adaptive: bool = True) -> float:
        """Calculate optimal buffer size based on preset and memory allocation"""
        
        # Base buffer sizes for each preset
        preset_sizes = {
            "conservative": 0.5,    # 512KB
            "balanced": 1.0,        # 1MB
            "aggressive": 2.0,      # 2MB
            "maximum": 4.0,         # 4MB
        }
        
        if preset == "auto" or adaptive:
            # Adaptive sizing based on available memory and system performance
            available_memory = self.get_available_memory()
            total_memory = self.system_memory
            
            # Calculate optimal buffer size based on available memory
            if available_memory > total_memory * 0.5:  # More than 50% available
                base_size = 2.0  # 2MB
            elif available_memory > total_memory * 0.25:  # More than 25% available
                base_size = 1.0  # 1MB
            else:  # Less than 25% available
                base_size = 0.5  # 512KB
            
            # Adjust based on allocation percentage
            adjusted_size = base_size * (allocation_percent / 15.0)  # 15% is baseline
            
            # Clamp to reasonable bounds
            return max(0.5, min(4.0, adjusted_size))
        else:
            # Use fixed preset size
            return preset_sizes.get(preset, 1.0)
    
    def get_optimal_config(self, 
                          buffer_preset: str = "auto",
                          memory_percent: float = 15.0,
                          adaptive: bool = True) -> MemoryConfig:
        """Get optimal memory configuration for current system state"""
        
        buffer_size = self.calculate_buffer_size(buffer_preset, memory_percent, adaptive)
        available_memory = self.get_available_memory()
        
        # Calculate how many concurrent buffers we can support
        memory_per_buffer = buffer_size
        max_buffers = int((available_memory * memory_percent / 100.0) / memory_per_buffer)
        
        # Ensure we have at least 1 buffer
        max_buffers = max(1, max_buffers)
        
        # For very large transfers, limit concurrent buffers to prevent memory exhaustion
        if max_buffers > 16:
            max_buffers = 16
        
        config = MemoryConfig(
            buffer_size_mb=buffer_size,
            max_concurrent_buffers=max_buffers,
            total_memory_mb=self.system_memory,
            available_memory_mb=available_memory,
            memory_allocation_percent=memory_percent,
            adaptive_enabled=adaptive
        )
        
        self.current_config = config
        return config
    
    def get_transfer_parameters(self, config: MemoryConfig) -> Dict[str, Any]:
        """Convert memory config to transfer engine parameters"""
        return {
            "block_size": int(config.buffer_size_mb * 1024 * 1024),
            "files_in_flight": min(config.max_concurrent_buffers, 4),  # Cap at 4 files
            "ranges_per_file": max(1, config.max_concurrent_buffers // 2),  # Use remaining for ranges
            "use_direct_io": config.buffer_size_mb >= 2.0,  # Use direct I/O for large buffers
            "adaptive_parameters": config.adaptive_enabled
        }
    
    def monitor_memory_usage(self) -> Dict[str, float]:
        """Monitor current memory usage and return statistics"""
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                return {
                    "total_mb": memory.total / (1024 * 1024),
                    "available_mb": memory.available / (1024 * 1024),
                    "used_mb": memory.used / (1024 * 1024),
                    "percent_used": memory.percent,
                    "percent_available": 100 - memory.percent
                }
            except:
                pass
        
        # Fallback values when psutil is not available
        return {
            "total_mb": self.system_memory,
            "available_mb": self.system_memory * 0.25,
            "used_mb": self.system_memory * 0.75,
            "percent_used": 75.0,
            "percent_available": 25.0
        }
    
    def should_throttle(self, config: MemoryConfig) -> bool:
        """Check if we should throttle transfers due to low memory"""
        available = self.get_available_memory()
        threshold = self.system_memory * 0.1  # 10% threshold
        
        return available < threshold
    
    def get_memory_warning(self, config: MemoryConfig) -> Optional[str]:
        """Get memory warning message if needed"""
        available = self.get_available_memory()
        total = self.system_memory
        
        if available < total * 0.05:  # Less than 5% available
            return f"Critical: Only {available:.1f}MB available. Consider closing other applications."
        elif available < total * 0.1:  # Less than 10% available
            return f"Warning: Low memory ({available:.1f}MB available). Transfer may be slower."
        elif available < total * 0.2:  # Less than 20% available
            return f"Note: Limited memory ({available:.1f}MB available). Consider reducing buffer size."
        
        return None

    def get_optimal_buffer_size_for_destination(self, destination_path: str, preset: str = "auto") -> float:
        """Get optimal buffer size for a specific destination based on transfer type"""
        
        # Detect transfer type based on destination path
        transfer_type = self._detect_transfer_type(destination_path)
        
        # Enhanced buffer sizes for each transfer type based on real-world performance
        type_buffers = {
            "usb_ssd": 4.0,         # 4MB for USB SSD (high throughput)
            "thunderbolt_ssd": 8.0,  # 8MB for Thunderbolt SSD (maximum throughput)
            "network_nas": 1.0,      # 1MB for NAS (1GbE = ~125MB/s, smaller buffers better)
            "local_ssd": 8.0,        # 8MB for local SSD (maximum throughput)
            "local_hdd": 2.0,        # 2MB for local HDD (balanced)
            "cloud": 0.5,            # 512KB for cloud (conservative, high latency)
            "unknown": 2.0           # 2MB default (balanced)
        }
        
        # Get base size for detected transfer type
        base_size = type_buffers.get(transfer_type, 2.0)
        
        # Apply preset adjustments
        if preset == "conservative":
            base_size *= 0.5
        elif preset == "balanced":
            base_size *= 1.0
        elif preset == "aggressive":
            base_size *= 1.5
        elif preset == "maximum":
            base_size *= 2.0
        
        # Clamp to reasonable bounds (0.5MB to 16MB)
        final_size = max(0.5, min(16.0, base_size))
        
        print(f"DEBUG: Destination {destination_path} - Type: {transfer_type}, Buffer: {final_size:.1f}MB")
        return final_size
    
    def get_optimal_transfer_params_for_destination(self, destination_path: str, preset: str = "auto") -> Dict[str, Any]:
        """Get complete optimized transfer parameters for a specific destination"""
        transfer_type = self._detect_transfer_type(destination_path)
        buffer_size = self.get_optimal_buffer_size_for_destination(destination_path, preset)
        
        # Enhanced transfer parameters based on destination type
        if transfer_type == "usb_ssd":
            # USB SSD: High throughput, moderate concurrency
            params = {
                "block_size": int(buffer_size * 1024 * 1024),
                "files_in_flight": 2,
                "ranges_per_file": 4,
                "use_direct_io": True,
                "transfer_type": transfer_type,
                "expected_speed_mbps": 400,  # Typical USB 3.0+ SSD speed
                "priority": "high"  # Complete faster destinations first
            }
        elif transfer_type == "thunderbolt_ssd":
            # Thunderbolt SSD: Maximum throughput and concurrency
            params = {
                "block_size": int(buffer_size * 1024 * 1024),
                "files_in_flight": 4,
                "ranges_per_file": 8,
                "use_direct_io": True,
                "transfer_type": transfer_type,
                "expected_speed_mbps": 1000,  # Thunderbolt 3+ speed
                "priority": "highest"
            }
        elif transfer_type == "network_nas":
            # 1GbE NAS: Lower throughput, network-optimized
            params = {
                "block_size": int(buffer_size * 1024 * 1024),
                "files_in_flight": 1,  # Single file for network stability
                "ranges_per_file": 2,   # Limited parallelism for network
                "use_direct_io": False,  # Buffered I/O better for network
                "transfer_type": transfer_type,
                "expected_speed_mbps": 110,  # Realistic 1GbE throughput
                "priority": "normal"
            }
        else:
            # Default parameters for unknown types
            params = {
                "block_size": int(buffer_size * 1024 * 1024),
                "files_in_flight": 2,
                "ranges_per_file": 2,
                "use_direct_io": buffer_size >= 4.0,
                "transfer_type": transfer_type,
                "expected_speed_mbps": 200,  # Conservative estimate
                "priority": "normal"
            }
        
        print(f"DEBUG: Transfer params for {destination_path} ({transfer_type}): {params}")
        return params
    
    def _detect_transfer_type(self, path: str) -> str:
        """Detect the type of transfer based on destination path with enhanced detection"""
        path_lower = path.lower()
        
        print(f"DEBUG: Analyzing path for transfer type detection: {path}")
        
        # Enhanced USB/External SSD detection
        if any(usb_indicator in path_lower for usb_indicator in ["usb", "flash", "thumb"]):
            print(f"DEBUG: Detected USB drive from path indicators")
            return "usb_ssd"  # Modern USB drives are usually SSDs
        
        # Thunderbolt detection - typically high-speed SSDs
        if any(tb_indicator in path_lower for tb_indicator in ["thunderbolt", "tb", "tbolt"]):
            print(f"DEBUG: Detected Thunderbolt connection")
            return "thunderbolt_ssd"
        
        # Enhanced Network/NAS detection
        if any(net_indicator in path_lower for net_indicator in ["smb://", "afp://", "nfs://", "//", "\\\\", "network", "nas", "server"]):
            print(f"DEBUG: Detected network storage from protocol indicators")
            return "network_nas"
        
        # Cloud detection
        if any(cloud_indicator in path_lower for cloud_indicator in ["onedrive", "dropbox", "google", "icloud", "cloud"]):
            print(f"DEBUG: Detected cloud storage")
            return "cloud"
        
        # Enhanced macOS /Volumes detection with filesystem analysis
        if path.startswith("/Volumes/"):
            volume_name = path.split("/")[2] if len(path.split("/")) > 2 else ""
            volume_name_lower = volume_name.lower()
            
            print(f"DEBUG: Analyzing volume: {volume_name}")
            
            # Common NAS names and patterns
            nas_indicators = [
                "synology", "qnap", "drobo", "buffalo", "western", "wd", "seagate",
                "nas", "server", "storage", "network", "shared", "diskstation",
                "cr2_creative", "creative"  # User's specific NAS
            ]
            
            # Common external SSD/USB indicators
            external_ssd_indicators = [
                "ssd", "samsung", "sandisk", "crucial", "kingston", "portable",
                "external", "backup", "usb", "cr_drive"  # User's specific USB SSD
            ]
            
            # Check for NAS indicators first
            if any(nas_ind in volume_name_lower for nas_ind in nas_indicators):
                print(f"DEBUG: Detected NAS from volume name: {volume_name}")
                return "network_nas"
            
            # Check for external SSD indicators
            if any(ssd_ind in volume_name_lower for ssd_ind in external_ssd_indicators):
                print(f"DEBUG: Detected external SSD from volume name: {volume_name}")
                return "usb_ssd"
            
            # Try to get filesystem information for better detection
            try:
                import os
                import subprocess
                
                # Use diskutil on macOS to get more information
                result = subprocess.run(
                    ["diskutil", "info", path], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                
                if result.returncode == 0:
                    info_lower = result.stdout.lower()
                    
                    # Look for connection type indicators in diskutil output
                    if any(indicator in info_lower for indicator in ["smb", "afp", "nfs", "network"]):
                        print(f"DEBUG: Detected network storage from diskutil info")
                        return "network_nas"
                    elif any(indicator in info_lower for indicator in ["usb", "external"]):
                        print(f"DEBUG: Detected USB/external storage from diskutil info")
                        return "usb_ssd"
                    elif "thunderbolt" in info_lower:
                        print(f"DEBUG: Detected Thunderbolt storage from diskutil info")
                        return "thunderbolt_ssd"
                        
            except Exception as e:
                print(f"DEBUG: Could not get diskutil info: {e}")
            
            # Default for /Volumes/ - assume external SSD if can't determine otherwise
            print(f"DEBUG: Defaulting to external SSD for volume: {volume_name}")
            return "usb_ssd"
        
        # Check if it's internal storage
        if path.startswith(("/Users/", "/Applications/", "/System/", "/Library/")):
            print(f"DEBUG: Detected internal storage")
            return "local_ssd"
        
        # Default to local SSD for unknown paths
        print(f"DEBUG: Defaulting to local SSD for unknown path")
        return "local_ssd"
