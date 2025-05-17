#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import logging
import platform
from PyQt5.QtCore import QSettings
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

def initialize_logging(logger_name='echelon', log_level=None, 
                      console_logging=DEFAULT_CONSOLE_LOGGING,
                      file_logging=DEFAULT_FILE_LOGGING,
                      log_format=DEFAULT_LOG_FORMAT,
                      max_log_size=DEFAULT_MAX_LOG_SIZE,
                      backup_count=DEFAULT_BACKUP_COUNT):
    """
    Initialize the application logging system.
    
    Args:
        logger_name (str): Name of the logger
        log_level (int): Logging level (DEBUG, INFO, etc.)
        console_logging (bool): Whether to log to console
        file_logging (bool): Whether to log to file
        log_format (str): Format string for log messages
        max_log_size (int): Maximum log file size in bytes
        backup_count (int): Number of backup log files to keep
    
    Returns:
        logging.Logger: Configured logger instance
    """
    global _app_logger

    # If already initialized, return existing logger
    if _app_logger is not None:
        return _app_logger
    
    # Get the QSettings value if available
    settings = QSettings()
    if log_level is None:
        saved_level = settings.value('logging/level')
        if saved_level is not None:
            try:
                log_level = int(saved_level)
            except (ValueError, TypeError):
                log_level = DEFAULT_LOG_LEVEL
        else:
            log_level = DEFAULT_LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    logger.propagate = False  # Don't propagate to parent loggers
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if enabled
    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
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
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Log the file location for debugging
            print(f"Log file location: {log_file}")
        except (IOError, PermissionError) as e:
            # Print to console since logger may not be fully set up yet
            print(f"Warning: Could not set up file logging: {e}")
    
    # Store the logger for later use
    _app_logger = logger
    
    return logger

def debug(message):
    """Log a debug message"""
    if _app_logger is None:
        initialize_logging()
    _app_logger.debug(message)

def info(message):
    """Log an info message"""
    if _app_logger is None:
        initialize_logging()
    _app_logger.info(message)

def warning(message):
    """Log a warning message"""
    if _app_logger is None:
        initialize_logging()
    _app_logger.warning(message)

def error(message):
    """Log an error message"""
    if _app_logger is None:
        initialize_logging()
    _app_logger.error(message)

def critical(message):
    """Log a critical message"""
    if _app_logger is None:
        initialize_logging()
    _app_logger.critical(message)

def exception(message):
    """Log an exception message with traceback"""
    if _app_logger is None:
        initialize_logging()
    _app_logger.exception(message)

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