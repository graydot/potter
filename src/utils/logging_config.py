#!/usr/bin/env python3
"""
Logging Configuration for Potter
Centralized logging setup with rotation and proper formatting
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Manages logging configuration for Potter"""
    
    # Log levels
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # Default configuration
    DEFAULT_LEVEL = 'INFO'
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __init__(self, log_dir: Optional[Path] = None, app_name: str = 'potter'):
        """
        Initialize logging configuration
        
        Args:
            log_dir: Directory for log files (auto-determined if None)
            app_name: Application name for log file
        """
        self.app_name = app_name
        self.log_dir = log_dir or self._get_default_log_dir()
        self.log_file = self.log_dir / f'{app_name}.log'
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_default_log_dir(self) -> Path:
        """Get default log directory based on environment"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            return Path.home() / 'Library' / 'Logs'
        else:
            # Running from source
            return Path(__file__).parent.parent.parent
    
    def setup_logging(self, 
                      level: str = DEFAULT_LEVEL,
                      console: bool = True,
                      file: bool = True,
                      max_bytes: int = DEFAULT_MAX_BYTES,
                      backup_count: int = DEFAULT_BACKUP_COUNT,
                      format_string: str = DEFAULT_FORMAT) -> None:
        """
        Set up logging configuration
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console: Enable console logging
            file: Enable file logging
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            format_string: Log message format
        """
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.LEVELS.get(level.upper(), logging.INFO))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(format_string)
        
        # Add console handler if enabled
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(root_logger.level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(root_logger.level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Configure specific loggers
        self._configure_module_loggers()
        
        logging.info(f"Logging configured: level={level}, file={self.log_file}")
    
    def _configure_module_loggers(self) -> None:
        """Configure logging levels for specific modules"""
        # Reduce noise from third-party libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        
        # Set specific levels for Potter modules if needed
        # logging.getLogger('potter.ui').setLevel(logging.DEBUG)
    
    def get_log_file_path(self) -> Path:
        """Get the current log file path"""
        return self.log_file
    
    def get_log_files(self) -> list[Path]:
        """Get all log files including rotated ones"""
        files = [self.log_file]
        
        # Add rotated files
        for i in range(1, self.DEFAULT_BACKUP_COUNT + 1):
            rotated_file = self.log_dir / f'{self.app_name}.log.{i}'
            if rotated_file.exists():
                files.append(rotated_file)
        
        return files
    
    def clear_logs(self) -> None:
        """Clear all log files"""
        for log_file in self.get_log_files():
            try:
                log_file.unlink()
                logging.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logging.error(f"Failed to delete log file {log_file}: {e}")
    
    def get_log_size(self) -> int:
        """Get total size of all log files in bytes"""
        total_size = 0
        for log_file in self.get_log_files():
            if log_file.exists():
                total_size += log_file.stat().st_size
        return total_size
    
    def format_log_size(self) -> str:
        """Get formatted string of total log size"""
        size = self.get_log_size()
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"


# Global logging configuration instance
_logging_config: Optional[LoggingConfig] = None


def get_logging_config() -> LoggingConfig:
    """Get or create global logging configuration"""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    return _logging_config


def setup_logging(**kwargs) -> None:
    """
    Convenience function to set up logging
    
    Args:
        **kwargs: Arguments passed to LoggingConfig.setup_logging()
    """
    config = get_logging_config()
    config.setup_logging(**kwargs)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name) 