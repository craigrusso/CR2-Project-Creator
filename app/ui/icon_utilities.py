#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Icon Utilities Module
Provides centralized icon handling with platform-specific icons for files and folders
"""

import os
import platform
import subprocess
import tempfile
import ctypes
import io
import sys
import logging
from enum import Enum
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QStyle, QFileIconProvider, QTreeWidget
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter
from PyQt6.QtCore import QFileInfo, QSize, Qt, QByteArray, QBuffer
from app.constants import get_resource_path
from app.ui.color_scheme_pyqt import APP_COLORS

# Configure logger
logger = logging.getLogger(__name__)

def debug(msg):
    """Log a debug message"""
    logger.debug(msg)
    
def warning(msg):
    """Log a warning message"""
    logger.warning(msg)

# Platform detection
PLATFORM = platform.system()  # 'Darwin', 'Windows', 'Linux'

# Try to import platform-specific modules if available
USE_NATIVE_PLATFORM_ICONS = False

# macOS specific imports
if PLATFORM == "Darwin":
    try:
        # Only attempt on macOS - silently fail on other platforms
        import rubicon.objc
        USE_NATIVE_PLATFORM_ICONS = True
        debug("Native macOS icon support available")
    except ImportError:
        warning("rubicon.objc not available, falling back to Qt icons on macOS")

# Windows specific imports
elif PLATFORM == "Windows":
    try:
        # Windows-specific icon extraction (optional)
        import win32com.client
        import win32api
        import win32con
        import win32ui
        import win32gui
        USE_NATIVE_PLATFORM_ICONS = True
        debug("Native Windows icon support available")
    except ImportError:
        warning("win32com not available, falling back to Qt icons on Windows")

class IconProvider:
    """Centralized icon provider for the application"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(IconProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the icon provider with platform-specific settings"""
        if self._initialized:
            return
            
        self._initialized = True
        self._system = PLATFORM
        self._icon_provider = QFileIconProvider()
        
        # Initialize file type mappings with generic system icons
        self._init_file_type_mappings()
        
        # Platform-specific folder icons
        self._folder_icon = None
        self._folder_open_icon = None
        self._init_platform_specific_folder_icons()
        
        # Cache to avoid repeating expensive icon lookups
        self._icon_cache = {}
        
        # Platform-specific initialization
        self._init_platform_specific()
    
    def _init_platform_specific(self):
        """Initialize platform-specific components"""
        # macOS-specific initialization
        if self._system == "Darwin" and USE_NATIVE_PLATFORM_ICONS:
            try:
                # Import needed modules inside the method to prevent errors on non-macOS platforms
                from rubicon.objc import ObjCClass
                NSWorkspace = ObjCClass('NSWorkspace')
                self._workspace = NSWorkspace.sharedWorkspace
                
                # Also initialize UTI-related classes for better file type handling
                self._UTTypeRef = ObjCClass('UTType') if hasattr(rubicon.objc, 'PyObjCClass') else None
                debug("macOS NSWorkspace initialized for icon retrieval")
            except Exception as e:
                warning(f"Could not initialize macOS NSWorkspace: {e}")
                self._workspace = None
                self._UTTypeRef = None
        else:
            self._workspace = None
            self._UTTypeRef = None
            
        # Windows-specific initialization
        if self._system == "Windows" and USE_NATIVE_PLATFORM_ICONS:
            try:
                self._shell = win32com.client.Dispatch("Shell.Application")
                debug("Windows Shell Application initialized for icon retrieval")
            except Exception as e:
                warning(f"Could not initialize Windows Shell: {e}")
                self._shell = None
        else:
            self._shell = None
    
    def _init_file_type_mappings(self):
        """Initialize file type mappings with system standard icons"""
        # File type constants - using standard system icons
        self.VIDEO_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.AUDIO_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume)
        self.IMAGE_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        self.DOC_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.CODE_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        self.GENERIC_FILE_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self.PDF_ICON = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        
        # Create a mapping of common application-specific file extensions
        self.APP_SPECIFIC_EXTENSIONS = {
            # Adobe
            '.prproj', '.aep', '.aepx', '.psd', '.ai', '.indd',  
            # Microsoft Office
            '.docx', '.xlsx', '.pptx',  
            # Apple apps
            '.fcpx', '.fcpxml', '.motion', '.logic',  
            # Video editing
            '.drp', '.dra',  # DaVinci Resolve
            '.avp', '.avb',  # Avid
            # 3D/VFX
            '.blend',  # Blender
            '.c4d',  # Cinema 4D
            '.nk',  # Nuke
            '.hip',  # Houdini
            '.ma', '.mb',  # Maya
            # Audio
            '.ptx', '.pts',  # Pro Tools
            # Media files
            '.mov', '.mp4', '.mxf', '.wav', '.aif'
        }
        
        # Extension to icon mappings - for fallback when native icons fail
        self._extension_mappings = {
            # Video files
            '.mp4': self.VIDEO_ICON, 
            '.mov': self.VIDEO_ICON, 
            '.avi': self.VIDEO_ICON, 
            '.mkv': self.VIDEO_ICON, 
            '.mxf': self.VIDEO_ICON, 
            '.webm': self.VIDEO_ICON, 
            '.wmv': self.VIDEO_ICON, 
            '.flv': self.VIDEO_ICON,
            
            # Audio files
            '.mp3': self.AUDIO_ICON, 
            '.wav': self.AUDIO_ICON, 
            '.aac': self.AUDIO_ICON, 
            '.flac': self.AUDIO_ICON, 
            '.ogg': self.AUDIO_ICON, 
            '.m4a': self.AUDIO_ICON, 
            '.aif': self.AUDIO_ICON, 
            '.aiff': self.AUDIO_ICON,
            
            # Image files
            '.jpg': self.IMAGE_ICON, 
            '.jpeg': self.IMAGE_ICON, 
            '.png': self.IMAGE_ICON, 
            '.gif': self.IMAGE_ICON, 
            '.bmp': self.IMAGE_ICON, 
            '.tiff': self.IMAGE_ICON, 
            '.tif': self.IMAGE_ICON, 
            '.svg': self.IMAGE_ICON,
            
            # Document files
            '.pdf': self.PDF_ICON,
            '.doc': self.DOC_ICON, 
            '.docx': self.DOC_ICON, 
            '.txt': self.DOC_ICON, 
            '.rtf': self.DOC_ICON, 
            '.xls': self.DOC_ICON, 
            '.xlsx': self.DOC_ICON, 
            '.ppt': self.DOC_ICON, 
            '.pptx': self.DOC_ICON,
            
            # Code files
            '.py': self.CODE_ICON,
            '.js': self.CODE_ICON,
            '.html': self.CODE_ICON,
            '.css': self.CODE_ICON,
            '.cpp': self.CODE_ICON,
            '.h': self.CODE_ICON,
            '.java': self.CODE_ICON,
            '.swift': self.CODE_ICON,
            
            # Adobe files - we rely on native icon retrieval for these
            '.prproj': self.VIDEO_ICON,  # Fallback only
            '.aep': self.VIDEO_ICON,  # Fallback only
            '.psd': self.IMAGE_ICON,  # Fallback only
            '.ai': self.IMAGE_ICON,  # Fallback only
            '.indd': self.DOC_ICON,  # Fallback only
            
            # Video editing files
            '.drp': self.VIDEO_ICON,  # DaVinci Resolve
            '.dra': self.VIDEO_ICON,  # DaVinci Resolve
            '.avp': self.VIDEO_ICON,  # Avid
            '.avb': self.VIDEO_ICON,  # Avid
            '.fcpx': self.VIDEO_ICON,  # Final Cut Pro
            '.fcpxml': self.VIDEO_ICON,  # Final Cut Pro
            
            # 3D and VFX files
            '.blend': self.CODE_ICON,  # Blender
            '.c4d': self.CODE_ICON,  # Cinema 4D
            '.nk': self.CODE_ICON,  # Nuke
            '.hip': self.CODE_ICON,  # Houdini
            '.ma': self.CODE_ICON,  # Maya
            '.mb': self.CODE_ICON,  # Maya
            
            # Audio editing files
            '.ptx': self.AUDIO_ICON,  # Pro Tools
            '.pts': self.AUDIO_ICON,  # Pro Tools
            '.logic': self.AUDIO_ICON,  # Logic Pro
        }
    
    def _init_platform_specific_folder_icons(self):
        """Initialize folder icons using QApplication.style().standardIcon"""
        if self._system == "Windows" and USE_NATIVE_PLATFORM_ICONS and self._shell:
            try:
                # On Windows, use shell32.dll folder icons directly
                # This provides more native-looking folder icons compared to Qt's SP_DirIcon
                import win32gui
                import win32con
                import win32ui
                
                # Get system folder icon (SHGFI_SMALLICON = 0x1, SHGFI_ICON = 0x100)
                SHGFI_ICON = 0x100
                SHGFI_SMALLICON = 0x1
                SHGFI_LARGEICON = 0x0
                SHGFI_SHELLICONSIZE = 0x4
                
                # Get closed folder icon
                folder_info = win32gui.SHGetFileInfo("C:\\", 0, SHGFI_ICON | SHGFI_SMALLICON)
                folder_icon_handle = folder_info[0]
                if folder_icon_handle:
                    # Convert the icon handle to QIcon
                    folder_pixmap = QPixmap.fromWinHICON(folder_icon_handle)
                    self._folder_icon = QIcon(folder_pixmap)
                    # Clean up the icon handle
                    win32gui.DestroyIcon(folder_icon_handle)
                else:
                    # Fallback to Qt's standard icon
                    self._folder_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                
                # Get open folder icon (if possible)
                # Try to get shell32.dll's open folder icon
                open_folder_info = win32gui.SHGetFileInfo("C:\\", 0, SHGFI_ICON | SHGFI_SMALLICON | win32con.FILE_ATTRIBUTE_DIRECTORY)
                open_folder_icon_handle = open_folder_info[0]
                if open_folder_icon_handle:
                    # Convert the icon handle to QIcon
                    open_folder_pixmap = QPixmap.fromWinHICON(open_folder_icon_handle)
                    self._folder_open_icon = QIcon(open_folder_pixmap)
                    # Clean up the icon handle
                    win32gui.DestroyIcon(open_folder_icon_handle)
                else:
                    # Fallback to the closed folder icon
                    self._folder_open_icon = self._folder_icon
                
                debug(f"Windows folder icons initialized using shell32.dll")
            except Exception as e:
                warning(f"Error initializing Windows folder icons: {e}")
                # Fallback to Qt's standard icons
                self._folder_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
                self._folder_open_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
                
                # If SP_DirOpenIcon is null, fallback to SP_DirIcon
                if self._folder_open_icon.isNull():
                    warning("SP_DirOpenIcon is null, using SP_DirIcon for open folder state as well.")
                    self._folder_open_icon = self._folder_icon
        else:
            # For non-Windows platforms, use Qt's standard icons
            # Directly use Qt's standard icons, which should provide a native look.
            self._folder_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            self._folder_open_icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)

            # If SP_DirOpenIcon is null (e.g., on some styles/platforms), fallback to SP_DirIcon for the open state.
            if self._folder_open_icon.isNull():
                warning("SP_DirOpenIcon is null, using SP_DirIcon for open folder state as well.")
                self._folder_open_icon = self._folder_icon # Fallback to the closed icon if open one isn't available

        debug(f"Folder icon initialized for {self._system}")
    
    def get_folder_icon(self, is_open=False):
        """Get platform-specific folder icon"""
        return self._folder_open_icon if is_open else self._folder_icon
    
    def _create_temp_file_if_needed(self, ext):
        """
        Create a temporary file with the given extension if needed
        
        Args:
            ext (str): The file extension
            
        Returns:
            str: Path to the temporary file
        """
        # Create a temporary file with the given extension
        fd, temp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)  # Close the file descriptor
        
        # Platform specific file type setup
        if self._system == "Darwin" and ext in self.APP_SPECIFIC_EXTENSIONS:
            try:
                # Adobe file formats - add specific UTI metadata
                if ext == '.prproj':
                    # Set file type for Premiere Pro project
                    subprocess.run(['xattr', '-w', 'com.apple.FinderInfo', '50505250', temp_path], 
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Set creator code
                    subprocess.run(['xattr', '-w', 'com.apple.metadata:kMDItemCreator', '50505250', temp_path],
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Add UTI type
                    subprocess.run(['xattr', '-w', 'com.apple.metadata:kMDItemContentType', 'com.adobe.premiereproject', temp_path],
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Add magic bytes for better recognition
                    with open(temp_path, 'w') as f:
                        f.write("PPRO")
                    
                elif ext in ['.aep', '.aepx']:
                    # Set file type for After Effects project
                    subprocess.run(['xattr', '-w', 'com.apple.FinderInfo', '41454020', temp_path], 
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Set creator code
                    subprocess.run(['xattr', '-w', 'com.apple.metadata:kMDItemCreator', '41454020', temp_path],
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Add UTI type
                    subprocess.run(['xattr', '-w', 'com.apple.metadata:kMDItemContentType', 'com.adobe.aftereffects.project', temp_path],
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Add magic bytes for better recognition
                    with open(temp_path, 'w') as f:
                        f.write("AEFX")
                        
                elif ext == '.psd':
                    # Set file type for Photoshop file
                    subprocess.run(['xattr', '-w', 'com.apple.FinderInfo', '38425053', temp_path], 
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Set creator code
                    subprocess.run(['xattr', '-w', 'com.apple.metadata:kMDItemCreator', '38425053', temp_path],
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Add UTI type
                    subprocess.run(['xattr', '-w', 'com.apple.metadata:kMDItemContentType', 'com.adobe.photoshop-image', temp_path],
                                  check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # Add basic PSD header
                    with open(temp_path, 'wb') as f:
                        f.write(b'8BPS')
                        
                # For other application-specific extensions, we could add similar handling
                
            except Exception as e:
                warning(f"Failed to set file type: {e}")
                
        # Windows file association tagging would go here if needed
                
        return temp_path
    
    def _get_macos_native_icon(self, filepath):
        """Use macOS native APIs to get the icon for a file path - macOS specific"""
        if not USE_NATIVE_PLATFORM_ICONS or not self._workspace or self._system != "Darwin":
            return None
            
        try:
            # Import needed modules inside the method to prevent errors on non-macOS platforms
            from rubicon.objc import ObjCClass, at
            NSString = ObjCClass('NSString')
            NSFileManager = ObjCClass('NSFileManager')
            fileManager = NSFileManager.defaultManager
            
            # Get file extension for special handling
            _, ext = os.path.splitext(filepath.lower())
            
            # Try to get icon for the exact file if it exists
            if os.path.exists(filepath):
                file_path = NSString.stringWithString_(filepath)
                ns_image = self._workspace.iconForFile_(file_path)
                if ns_image:
                    # If we have a valid image, convert it to QIcon
                    return self._nsimage_to_qicon(ns_image)
            
            # If file doesn't exist or we couldn't get an icon, try application-specific handling
            if ext in self.APP_SPECIFIC_EXTENSIONS:
                # Try to find the associated application
                app_bundle_id = None
                app_path = None
                
                # Map extensions to bundle IDs
                if ext == '.prproj':
                    app_bundle_id = 'com.adobe.PremierePro'
                    app_paths = [
                        "/Applications/Adobe Premiere Pro 2023/Adobe Premiere Pro 2023.app",
                        "/Applications/Adobe Premiere Pro CC/Adobe Premiere Pro CC.app",
                        "/Applications/Adobe Premiere Pro/Adobe Premiere Pro.app"
                    ]
                    for path in app_paths:
                        if os.path.exists(path):
                            app_path = path
                            break
                
                elif ext in ['.aep', '.aepx']:
                    app_bundle_id = 'com.adobe.AfterEffects'
                    app_paths = [
                        "/Applications/Adobe After Effects 2023/Adobe After Effects 2023.app",
                        "/Applications/Adobe After Effects CC/Adobe After Effects CC.app",
                        "/Applications/Adobe After Effects/Adobe After Effects.app"
                    ]
                    for path in app_paths:
                        if os.path.exists(path):
                            app_path = path
                            break
                
                elif ext == '.psd':
                    app_bundle_id = 'com.adobe.Photoshop'
                    app_paths = [
                        "/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app",
                        "/Applications/Adobe Photoshop CC/Adobe Photoshop CC.app",
                        "/Applications/Adobe Photoshop/Adobe Photoshop.app"
                    ]
                    for path in app_paths:
                        if os.path.exists(path):
                            app_path = path
                            break
                            
                # Add more application mapping as needed
                
                # If we found the application path, try to get its icon
                if app_path and os.path.exists(app_path):
                    debug(f"Using icon from application: {app_path}")
                    app_path_ns = NSString.stringWithString_(app_path)
                    ns_image = self._workspace.iconForFile_(app_path_ns)
                    if ns_image:
                        return self._nsimage_to_qicon(ns_image)
            
            # Last resort: try with the temporary file
            file_path = NSString.stringWithString_(filepath)
            ns_image = self._workspace.iconForFile_(file_path)
            if ns_image:
                return self._nsimage_to_qicon(ns_image)
                
            return None
        except Exception as e:
            warning(f"Error getting native macOS icon: {e}")
            return None
    
    def _nsimage_to_qicon(self, ns_image):
        """Convert an NSImage to a QIcon"""
        if not ns_image:
            return None

        try:
            from rubicon.objc import ObjCClass, at
            
            # Try multiple conversion methods for better compatibility
            qicon = QIcon()
            
            try:
                # Method 1: Convert to PNG representation
                NSData = ObjCClass('NSData')
                data = ns_image.TIFFRepresentation
                bitmap_rep = ObjCClass('NSBitmapImageRep').imageRepWithData_(data)
                png_data = bitmap_rep.representationUsingType_properties_(4, None)  # 4 is NSPNGFileType
                
                if png_data:
                    # Convert NSData to bytes
                    length = png_data.length
                    c_bytes_ptr = png_data.bytes
                    png_bytes = ctypes.string_at(c_bytes_ptr, length)
                    
                    # Create QImage from PNG data
                    qimg = QImage()
                    qimg.loadFromData(QByteArray(png_bytes))
                    
                    # Create QIcon from the QImage
                    if not qimg.isNull():
                        pixmap = QPixmap.fromImage(qimg)
                        qicon.addPixmap(pixmap)
                        return qicon
            except Exception as e:
                debug(f"Method 1 (PNG) failed: {str(e)}")
                
            # If we reach here, the PNG method failed, try direct TIFF loading
            try:
                data = ns_image.TIFFRepresentation
                if data:
                    length = data.length
                    c_bytes_ptr = data.bytes
                    tiff_bytes = ctypes.string_at(c_bytes_ptr, length)
                    
                    qimg = QImage()
                    qimg.loadFromData(QByteArray(tiff_bytes))
                    
                    if not qimg.isNull():
                        pixmap = QPixmap.fromImage(qimg)
                        qicon.addPixmap(pixmap)
                        return qicon
            except Exception as e:
                debug(f"Method 2 (TIFF) failed: {str(e)}")
            
            # If all else fails, return fallback icon
            return self.get_fallback_icon()
            
        except Exception as e:
            logging.warning(f"Error converting NSImage to QIcon: {str(e)}")
            return self.get_fallback_icon()
    
    def get_fallback_icon(self):
        """Return a fallback icon when native icon retrieval fails"""
        if self._system == "Darwin":
            return self._icon_provider.icon(QFileIconProvider.IconType.File)
        else:
            return QIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
    
    def _get_windows_native_icon(self, filepath):
        """Use Windows Shell API to get the icon for a file path - Windows specific"""
        if not USE_NATIVE_PLATFORM_ICONS or not self._shell or self._system != "Windows":
            return None
            
        try:
            # Get file extension
            _, ext = os.path.splitext(filepath)
            
            # Create the temporary file so Windows can determine its type
            temp_file = None
            if not os.path.exists(filepath):
                temp_file = self._create_temp_file_if_needed(ext)
                target_path = temp_file
            else:
                target_path = filepath
                
            # Make sure the path is absolute
            if not os.path.isabs(target_path):
                target_path = os.path.abspath(target_path)
                
            # Get file info from shell
            folder = self._shell.NameSpace(os.path.dirname(target_path))
            file_item = folder.ParseName(os.path.basename(target_path))
            
            if file_item is not None:
                # Try to get icon through Windows Shell
                try:
                    icon = QIcon(QFileIconProvider().icon(QFileInfo(target_path)))
                    
                    # Clean up temp file if created
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                            
                    return icon
                except Exception as e:
                    warning(f"Error getting Windows icon: {e}")
                    
            # Clean up temp file if created
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
            return None
        except Exception as e:
            warning(f"Error getting native Windows icon: {e}")
            
            # Clean up temp file if created and still exists
            if 'temp_file' in locals() and temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
            return None
    
    def get_file_icon(self, filename):
        """
        Get the appropriate icon for a file based on its extension - cross-platform
        
        Args:
            filename (str): Name or path of the file
            
        Returns:
            QIcon: Icon for the file type
        """
        # Check cache first
        if filename in self._icon_cache:
            return self._icon_cache[filename]
            
        # Extract file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Check for project name placeholders
        is_project_file = '{PROJECT_NAME}' in filename and '.' in filename
        if is_project_file:
            # Extract extension from project file
            parts = filename.split('.')
            if len(parts) > 1:
                ext = '.' + parts[-1].split()[0]  # Get extension before any emoji
        
        # Create a temporary file for icon extraction if needed
        temp_file = None
        try:
            if not os.path.exists(filename) or is_project_file:
                temp_file = self._create_temp_file_if_needed(ext)
                target_path = temp_file
            else:
                target_path = filename
                
            # Try platform-specific icon retrieval first
            platform_icon = None
            
            if self._system == "Darwin" and USE_NATIVE_PLATFORM_ICONS:
                platform_icon = self._get_macos_native_icon(target_path)
            elif self._system == "Windows" and USE_NATIVE_PLATFORM_ICONS:
                platform_icon = self._get_windows_native_icon(target_path)
                
            if platform_icon and not platform_icon.isNull():
                self._icon_cache[filename] = platform_icon
                
                # Clean up temp file if created
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                        
                return platform_icon
                
            # Cross-platform fallback using Qt's QFileIconProvider
            if target_path:
                file_info = QFileInfo(target_path)
                system_icon = self._icon_provider.icon(file_info)
                
                if not system_icon.isNull():
                    self._icon_cache[filename] = system_icon
                    
                    # Clean up temp file if created
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                            
                    return system_icon
                    
        except Exception as e:
            warning(f"Error getting file icon: {e}")
        finally:
            # Clean up temp file in the finally block to ensure it happens
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        # If all else fails, use our predefined icons based on extension
        if ext in self._extension_mappings:
            icon = self._extension_mappings[ext]
            self._icon_cache[filename] = icon
            return icon
        
        # Last resort - use generic file icon
        self._icon_cache[filename] = self.GENERIC_FILE_ICON
        return self.GENERIC_FILE_ICON

# Global convenience functions
def get_folder_icon(is_open=False):
    """Get platform-specific folder icon"""
    return IconProvider().get_folder_icon(is_open)

def get_file_icon(filename):
    """Get icon for file type"""
    return IconProvider().get_file_icon(filename)

def clear_icon_cache():
    """Clear the icon cache to force reloading of all icons"""
    provider = IconProvider()
    provider._icon_cache.clear()
    debug("Icon cache cleared")
    
    # Force immediate refresh of all tree widgets in the application
    # app = QApplication.instance() # Removed UI update from here
    # if app:
    #     for widget in app.allWidgets():
    #         if isinstance(widget, QTreeWidget):
    #             # Update all visible tree items
    #             for i in range(widget.topLevelItemCount()):
    #                 _refresh_widget_item_icons(widget.topLevelItem(i))
    
    return True

def _refresh_widget_item_icons(item):
    """Helper function to recursively refresh icons for tree widget items"""
    if not item:
        return
        
    # Force icon update based on item data or text
    item_data = item.data(0, Qt.ItemDataRole.UserRole)
    item_name = item.text(0)
    
    # First try to identify by explicit data type
    if isinstance(item_data, dict) and 'type' in item_data:
        # Use the explicit type information
        item_type = item_data.get('type')
        
        if item_type == 'folder':
            # It's a folder - use appropriate folder icon based on expanded state
            is_expanded = item.isExpanded()
            item.setIcon(0, get_folder_icon(is_expanded))
        else:
            # It's a file - use appropriate file icon
            filename = item_data.get('name', item_name)
            item.setIcon(0, get_file_icon(filename))
    else:
        # Fallback to heuristic identification
        if item.childCount() > 0:
            # Has children, likely a folder
            is_expanded = item.isExpanded()
            item.setIcon(0, get_folder_icon(is_expanded))
        else:
            # No children, likely a file
            # Check if the item has a file extension
            if '.' in item_name and not item_name.endswith('/'):
                # Has extension, definitely a file
                item.setIcon(0, get_file_icon(item_name))
            else:
                # No extension, but no children either
                # Default to folder icon since it's ambiguous
                item.setIcon(0, get_folder_icon(False))
            
    # Recursively refresh children's icons
    for i in range(item.childCount()):
        _refresh_widget_item_icons(item.child(i)) 