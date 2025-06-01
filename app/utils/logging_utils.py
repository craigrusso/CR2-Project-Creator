#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import logging
import platform
from PyQt6.QtCore import QSettings
from logging.handlers import RotatingFileHandler
from app.core import config_manager

# Define log levels
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO  
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO  # Default to INFO for production
DEFAULT_CONSOLE_LOGGING = False  # Default console logging to OFF for production
DEFAULT_FILE_LOGGING = True
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
DEFAULT_BACKUP_COUNT = 3

# Global logger instance
_app_logger = None

def get_log_file_path():
    """Return the full path to the log file."""
    log_dir = config_manager.get_log_path()
    return os.path.join(log_dir, 'echelon.log')

def detect_and_set_environment():
    """
    Detect the current environment and set logging level accordingly.
    Returns the detected environment name: 'development', 'test', or 'production'
    """
    # Simple environment detection - can be expanded as needed
    env = os.environ.get('APP_ENV', '').lower()
    
    if env == 'test' or 'test' in sys.argv:
        set_test_mode()
        return 'test'
    elif env == 'production' or 'release' in sys.argv or 'prod' in sys.argv:
        set_production_mode()
        return 'production'
    else:
        # Default to development mode
        set_development_mode()
        return 'development'

def set_development_mode():
    """Set logging to development mode (DEBUG level)"""
    if _app_logger:
        _app_logger.setLevel(logging.DEBUG)
        for handler in _app_logger.handlers:
            handler.setLevel(logging.DEBUG)
        debug("Development logging mode enabled")

def set_test_mode():
    """Set logging to test mode (INFO level with specific handlers)"""
    if _app_logger:
        _app_logger.setLevel(logging.INFO)
        for handler in _app_logger.handlers:
            handler.setLevel(logging.INFO)
        info("Test logging mode enabled")

def set_production_mode():
    """Set logging to production mode (INFO level and above)"""
    if _app_logger:
        _app_logger.setLevel(logging.INFO)
        for handler in _app_logger.handlers:
            handler.setLevel(logging.INFO)
        info("Production logging mode enabled")

def initialize_logging(logger_name='echelon', log_level_param=None, 
                      console_logging=DEFAULT_CONSOLE_LOGGING,
                      file_logging=DEFAULT_FILE_LOGGING,
                      log_format=DEFAULT_LOG_FORMAT,
                      max_log_size=DEFAULT_MAX_LOG_SIZE,
                      backup_count=DEFAULT_BACKUP_COUNT):
    """
    Initialize the application logging system.
    
    Args:
        logger_name (str): Name of the logger
        log_level_param (int): Logging level (DEBUG, INFO, etc.)
        console_logging (bool): Whether to log to console
        file_logging (bool): Whether to log to file
        log_format (str): Format string for log messages
        max_log_size (int): Maximum log file size in bytes
        backup_count (int): Number of backup log files to keep
    
    Returns:
        logging.Logger: Configured logger instance
    """
    global _app_logger
    if _app_logger is not None: # Simplified check
        return _app_logger

    # Determine the actual log level to use
    level_to_set = DEFAULT_LOG_LEVEL # Start with a safe default

    if log_level_param is not None: # If a level was explicitly passed as argument
        if isinstance(log_level_param, str):
            val = getattr(logging, log_level_param.upper(), None)
            if isinstance(val, int):
                level_to_set = val
            # else: level_to_set remains DEFAULT_LOG_LEVEL if string is invalid
        elif isinstance(log_level_param, int):
            # We should ideally check if this int is a known log level, but for now trust direct int params.
            # The original error was `None`, not an invalid int, so this path is likely not the primary issue.
            level_to_set = log_level_param
        # else: (invalid type for log_level_param) level_to_set remains DEFAULT_LOG_LEVEL
    else: # No explicit log_level_param, so try QSettings
        settings = QSettings()
        saved_level_setting = settings.value('logging/level')

        if saved_level_setting is not None: # If a setting exists in QSettings
            if isinstance(saved_level_setting, str):
                val = getattr(logging, saved_level_setting.upper(), None)
                if isinstance(val, int): # Valid string from QSettings like "INFO"
                    level_to_set = val
                # else: level_to_set remains DEFAULT_LOG_LEVEL if string from settings is invalid
            elif isinstance(saved_level_setting, int):
                # Again, ideally validate this int. For now, trust it if it's an int from settings.
                level_to_set = saved_level_setting
            # else: (invalid type from QSettings) level_to_set remains DEFAULT_LOG_LEVEL
        # else: (no 'logging/level' in QSettings) level_to_set remains DEFAULT_LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger(logger_name)
    
    # Critical check before setting level to prevent TypeError
    if not isinstance(level_to_set, int):
        print(f"CRITICAL LOGGING ERROR: Resolved log level '{level_to_set}' (type: {type(level_to_set)}) is not an integer. Defaulting to DEBUG.")
        level_to_set = logging.DEBUG # Fallback to a known valid integer level
        
    logger.setLevel(level_to_set)
    logger.propagate = False  # Don't propagate to parent loggers
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if enabled
    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level_to_set)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if file_logging:
        try:
            log_file = get_log_file_path()
            
            # Ensure the log directory exists
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_log_size, 
                backupCount=backup_count
            )
            file_handler.setLevel(level_to_set)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Log the file location for debugging
            # debug(f"Log file initialized at: {log_file}")
        except (IOError, PermissionError) as e:
            # Print to console since logger may not be fully set up yet
            print(f"Warning: Could not set up file logging: {e}")
    
    # Store the logger for later use
    _app_logger = logger

    # Log the file location for debugging using print, NOT the app's debug() helper
    if file_logging and log_file and os.path.exists(log_file): # Check if file_logging was successful and log_file is valid
        # Use print for this initial message as logger might not be fully ready for itself.
        print(f"INFO: Log file initialized at: {log_file}")
            
    return logger

def debug(message):
    """Log a debug message"""
    global _app_logger
    if _app_logger is None: 
        initialize_logging() 
    # Ensure _app_logger is now available after initialize_logging()
    if _app_logger:
        _app_logger.debug(message)
    else: # Should not happen if initialize_logging is correct
        print(f"DEBUG (logger still None after init attempt): {message}")

def info(message):
    """Log an info message"""
    global _app_logger
    if _app_logger is None: 
        initialize_logging()
    if _app_logger:
        _app_logger.info(message)
    else:
        print(f"INFO (logger still None after init attempt): {message}")

def warning(message):
    """Log a warning message"""
    global _app_logger
    if _app_logger is None: 
        initialize_logging()
    if _app_logger:
        _app_logger.warning(message)
    else:
        print(f"WARNING (logger still None after init attempt): {message}")

def error(message):
    """Log an error message"""
    global _app_logger
    if _app_logger is None: 
        initialize_logging()
    if _app_logger:
        _app_logger.error(message)
    else:
        print(f"ERROR (logger still None after init attempt): {message}")

def critical(message):
    """Log a critical message"""
    global _app_logger
    if _app_logger is None: 
        initialize_logging()
    if _app_logger:
        _app_logger.critical(message)
    else:
        print(f"CRITICAL (logger still None after init attempt): {message}")

def exception(message):
    """Log an exception message with traceback"""
    global _app_logger
    if _app_logger is None: 
        initialize_logging()
    if _app_logger:
        _app_logger.exception(message)
    else:
        print(f"EXCEPTION (logger still None after init attempt): {message}")
        import traceback
        traceback.print_exc()

def get_logger():
    """Get the application logger instance"""
    global _app_logger
    
    if _app_logger is None:
        _app_logger = initialize_logging()
    
    return _app_logger

def set_log_level(level):
    """Set the logging level"""
    logger = get_logger()
    logger.setLevel(level)
    
    # Update all existing handlers
    for handler in logger.handlers:
        handler.setLevel(level)
    
    # Update settings
    settings = QSettings()
    level_name = logging.getLevelName(level)
    settings.setValue('logging/level', level_name)

def enable_console_logging(enabled=True):
    """Enable or disable console logging"""
    logger = get_logger()
    settings = QSettings()
    settings.setValue('logging/console_enabled', enabled)
    
    # Remove existing console handlers if any
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) 
                      and not isinstance(h, logging.FileHandler)]
    
    for handler in console_handlers:
        logger.removeHandler(handler)
    
    # Add new console handler if enabled
    if enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger.level)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

def enable_file_logging(enabled=True):
    """Enable or disable file logging"""
    logger = get_logger()
    settings = QSettings()
    settings.setValue('logging/file_enabled', enabled)
    
    # Remove existing file handlers if any
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    
    for handler in file_handlers:
        logger.removeHandler(handler)
    
    # Add new file handler if enabled
    if enabled:
        try:
            log_file = get_log_file_path()
            
            # Ensure the log directory exists
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=DEFAULT_MAX_LOG_SIZE, 
                backupCount=DEFAULT_BACKUP_COUNT
            )
            file_handler.setLevel(logger.level)
            formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, PermissionError) as e:
            # Print to console since logger may not be fully set up yet
            print(f"Warning: Could not set up file logging: {e}")

def is_debug_enabled():
    """Check if debug logging is enabled"""
    return get_logger().isEnabledFor(logging.DEBUG)

def set_development_mode():
    """Configure logging for development environment"""
    set_log_level(logging.DEBUG)
    enable_console_logging(True)
    enable_file_logging(True)
    debug("Development logging mode enabled")

def set_production_mode():
    """Configure logging for production environment"""
    set_log_level(logging.INFO)
    enable_console_logging(False)
    enable_file_logging(True)
    info("Production logging mode enabled")

# Try to detect environment automatically
def detect_and_set_environment():
    """Detect and set the appropriate environment based on how the app is running"""
    settings = QSettings()
    
    # Check if environment is explicitly specified in settings
    env = settings.value('app/environment', None)
    
    if env == 'development':
        set_development_mode()
    elif env == 'production':
        set_production_mode()
    else:
        # Auto-detect: if running from source, assume development
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            set_production_mode()
        else:
            # Running from source
            set_development_mode() 