#!/usr/bin/env python3
"""
Logging Service
Centralized logging with service integration and advanced features
"""

import logging
import logging.handlers
from typing import Dict, Any, Optional, List, Callable
from threading import Lock
from pathlib import Path
import json
import time
from datetime import datetime, timedelta

from .base_service import BaseService
from core.exceptions import ServiceError

logger = logging.getLogger(__name__)


class LogBuffer:
    """Buffer for storing recent log entries"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.entries: List[Dict[str, Any]] = []
        self.lock = Lock()
    
    def add(self, record: logging.LogRecord) -> None:
        """Add a log record to the buffer"""
        with self.lock:
            entry = {
                'timestamp': record.created,
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'process': record.process
            }
            
            # Add exception info if present
            if record.exc_info:
                import traceback
                entry['exception'] = ''.join(traceback.format_exception(*record.exc_info))
            
            self.entries.append(entry)
            
            # Trim buffer if needed
            if len(self.entries) > self.max_size:
                self.entries = self.entries[-self.max_size:]
    
    def get_recent(self, count: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries"""
        with self.lock:
            entries = self.entries.copy()
        
        # Filter by level if specified
        if level:
            level_num = getattr(logging, level.upper(), logging.INFO)
            entries = [e for e in entries if logging.getLevelName(e['level']) >= level_num]
        
        return entries[-count:]
    
    def clear(self) -> None:
        """Clear the buffer"""
        with self.lock:
            self.entries.clear()


class ServiceLogHandler(logging.Handler):
    """Custom log handler for service integration"""
    
    def __init__(self, logging_service: 'LoggingService'):
        super().__init__()
        self.logging_service = logging_service
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record"""
        try:
            # Add to buffer
            self.logging_service._log_buffer.add(record)
            
            # Notify callbacks
            self.logging_service._notify_log_callbacks(record)
            
        except Exception:
            # Avoid recursive logging errors
            pass


class LoggingService(BaseService):
    """
    Service for centralized logging management
    
    Features:
    - Centralized log configuration
    - Multiple log handlers (file, console, buffer)
    - Log level management per logger
    - Log rotation and archival
    - Real-time log monitoring
    - Log search and filtering
    - Performance metrics logging
    - Service-specific logging
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("logging", {})
        
        self.settings_manager = settings_manager
        
        # Log buffer for recent entries
        self._log_buffer = LogBuffer(max_size=2000)
        
        # Handlers and loggers
        self._handlers: Dict[str, logging.Handler] = {}
        self._custom_loggers: Dict[str, logging.Logger] = {}
        self._handler_lock = Lock()
        
        # Log callbacks
        self._log_callbacks: List[Callable[[logging.LogRecord], None]] = []
        self._callbacks_lock = Lock()
        
        # Log file management
        self._log_dir = Path.home() / ".potter" / "logs"
        self._main_log_file = self._log_dir / "potter.log"
        self._service_log_file = self._log_dir / "services.log"
        self._error_log_file = self._log_dir / "errors.log"
        
        # Configuration
        self._log_level = logging.INFO
        self._max_file_size = 10 * 1024 * 1024  # 10MB
        self._backup_count = 5
        self._console_logging = True
        
        # Performance tracking
        self._performance_metrics: Dict[str, List[float]] = {}
        self._metrics_lock = Lock()
        
    def _start_service(self) -> None:
        """Start the logging service"""
        # Create log directory
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration from settings
        self._load_logging_config()
        
        # Set up handlers
        self._setup_log_handlers()
        
        # Configure root logger
        self._configure_root_logger()
        
        # Set up service-specific loggers
        self._setup_service_loggers()
        
        self.logger.info("📋 Logging service started")
    
    def _stop_service(self) -> None:
        """Stop the logging service"""
        # Clean up handlers
        self._cleanup_handlers()
        
        # Clear callbacks
        with self._callbacks_lock:
            self._log_callbacks.clear()
        
        # Clear buffer
        self._log_buffer.clear()
        
        self.logger.info("📋 Logging service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get logging service specific status"""
        with self._handler_lock:
            handler_info = {
                name: {
                    'type': type(handler).__name__,
                    'level': handler.level,
                    'formatter': str(handler.formatter) if handler.formatter else None
                }
                for name, handler in self._handlers.items()
            }
        
        return {
            'log_dir': str(self._log_dir),
            'log_level': logging.getLevelName(self._log_level),
            'console_logging': self._console_logging,
            'buffer_size': len(self._log_buffer.entries),
            'handlers': handler_info,
            'custom_loggers': len(self._custom_loggers),
            'log_callbacks': len(self._log_callbacks),
            'performance_metrics': len(self._performance_metrics)
        }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        config_changed = False
        
        if 'log_level' in new_config:
            self._log_level = getattr(logging, new_config['log_level'].upper(), logging.INFO)
            config_changed = True
        
        if 'console_logging' in new_config:
            self._console_logging = new_config['console_logging']
            config_changed = True
        
        if 'max_log_file_size' in new_config:
            self._max_file_size = new_config['max_log_file_size']
            config_changed = True
        
        if config_changed:
            self._reconfigure_logging()
    
    def get_recent_logs(self, count: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent log entries
        
        Args:
            count: Number of entries to return
            level: Minimum log level to include
            
        Returns:
            List of log entries
        """
        return self._log_buffer.get_recent(count, level)
    
    def search_logs(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search log entries
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of matching log entries
        """
        recent_logs = self._log_buffer.get_recent(1000)  # Search in recent entries
        
        query_lower = query.lower()
        matches = []
        
        for entry in recent_logs:
            if (query_lower in entry['message'].lower() or 
                query_lower in entry['logger'].lower() or
                query_lower in entry.get('module', '').lower()):
                matches.append(entry)
                
                if len(matches) >= max_results:
                    break
        
        return matches
    
    def set_log_level(self, logger_name: str, level: str) -> bool:
        """
        Set log level for a specific logger
        
        Args:
            logger_name: Name of the logger
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            bool: True if set successfully
        """
        try:
            log_level = getattr(logging, level.upper())
            target_logger = logging.getLogger(logger_name)
            target_logger.setLevel(log_level)
            
            self.logger.info(f"Set log level for '{logger_name}' to {level}")
            return True
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Invalid log level '{level}': {e}")
            return False
    
    def add_log_callback(self, callback: Callable[[logging.LogRecord], None]) -> None:
        """
        Add a callback for log entries
        
        Args:
            callback: Function to call for each log record
        """
        with self._callbacks_lock:
            if callback not in self._log_callbacks:
                self._log_callbacks.append(callback)
                self.logger.debug("Added log callback")
    
    def remove_log_callback(self, callback: Callable[[logging.LogRecord], None]) -> None:
        """
        Remove a log callback
        
        Args:
            callback: Callback to remove
        """
        with self._callbacks_lock:
            if callback in self._log_callbacks:
                self._log_callbacks.remove(callback)
                self.logger.debug("Removed log callback")
    
    def log_performance_metric(self, metric_name: str, duration: float) -> None:
        """
        Log a performance metric
        
        Args:
            metric_name: Name of the metric
            duration: Duration in seconds
        """
        with self._metrics_lock:
            if metric_name not in self._performance_metrics:
                self._performance_metrics[metric_name] = []
            
            self._performance_metrics[metric_name].append(duration)
            
            # Keep only recent metrics (last 1000)
            if len(self._performance_metrics[metric_name]) > 1000:
                self._performance_metrics[metric_name] = self._performance_metrics[metric_name][-1000:]
        
        self.logger.debug(f"Performance metric '{metric_name}': {duration:.3f}s")
    
    def get_performance_stats(self, metric_name: str) -> Dict[str, float]:
        """
        Get performance statistics for a metric
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Dict with min, max, avg, count statistics
        """
        with self._metrics_lock:
            durations = self._performance_metrics.get(metric_name, [])
        
        if not durations:
            return {'count': 0}
        
        return {
            'count': len(durations),
            'min': min(durations),
            'max': max(durations),
            'avg': sum(durations) / len(durations),
            'recent_avg': sum(durations[-100:]) / min(len(durations), 100)
        }
    
    def export_logs(self, file_path: Path, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None, level: Optional[str] = None) -> bool:
        """
        Export logs to a file
        
        Args:
            file_path: Output file path
            start_time: Start time for export
            end_time: End time for export
            level: Minimum log level
            
        Returns:
            bool: True if exported successfully
        """
        try:
            logs = self._log_buffer.get_recent(10000, level)
            
            # Filter by time range if specified
            if start_time or end_time:
                filtered_logs = []
                for log_entry in logs:
                    log_time = datetime.fromtimestamp(log_entry['timestamp'])
                    
                    if start_time and log_time < start_time:
                        continue
                    if end_time and log_time > end_time:
                        continue
                    
                    filtered_logs.append(log_entry)
                
                logs = filtered_logs
            
            # Export to JSON
            with open(file_path, 'w') as f:
                json.dump({
                    'export_time': datetime.now().isoformat(),
                    'start_time': start_time.isoformat() if start_time else None,
                    'end_time': end_time.isoformat() if end_time else None,
                    'level_filter': level,
                    'count': len(logs),
                    'logs': logs
                }, f, indent=2)
            
            self.logger.info(f"Exported {len(logs)} log entries to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            return False
    
    def rotate_logs(self) -> bool:
        """
        Manually rotate log files
        
        Returns:
            bool: True if rotated successfully
        """
        try:
            with self._handler_lock:
                for handler in self._handlers.values():
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        handler.doRollover()
            
            self.logger.info("Manually rotated log files")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rotating logs: {e}")
            return False
    
    def _setup_log_handlers(self) -> None:
        """Set up log handlers"""
        with self._handler_lock:
            # Clear existing handlers
            self._handlers.clear()
            
            # File handler for main log
            main_handler = logging.handlers.RotatingFileHandler(
                self._main_log_file,
                maxBytes=self._max_file_size,
                backupCount=self._backup_count
            )
            main_handler.setLevel(self._log_level)
            main_handler.setFormatter(self._create_detailed_formatter())
            self._handlers['main_file'] = main_handler
            
            # File handler for service logs
            service_handler = logging.handlers.RotatingFileHandler(
                self._service_log_file,
                maxBytes=self._max_file_size,
                backupCount=self._backup_count
            )
            service_handler.setLevel(self._log_level)
            service_handler.setFormatter(self._create_detailed_formatter())
            service_handler.addFilter(self._create_service_filter())
            self._handlers['service_file'] = service_handler
            
            # Error file handler
            error_handler = logging.handlers.RotatingFileHandler(
                self._error_log_file,
                maxBytes=self._max_file_size,
                backupCount=self._backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(self._create_detailed_formatter())
            self._handlers['error_file'] = error_handler
            
            # Console handler
            if self._console_logging:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(self._log_level)
                console_handler.setFormatter(self._create_console_formatter())
                self._handlers['console'] = console_handler
            
            # Service integration handler
            service_handler = ServiceLogHandler(self)
            service_handler.setLevel(logging.DEBUG)
            self._handlers['service_integration'] = service_handler
    
    def _configure_root_logger(self) -> None:
        """Configure the root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Let handlers filter
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our handlers
        with self._handler_lock:
            for handler in self._handlers.values():
                root_logger.addHandler(handler)
    
    def _setup_service_loggers(self) -> None:
        """Set up service-specific loggers"""
        service_names = [
            'api', 'theme', 'notification', 'validation', 'hotkey',
            'permission', 'window', 'settings', 'logging'
        ]
        
        for service_name in service_names:
            logger_name = f"services.{service_name}"
            service_logger = logging.getLogger(logger_name)
            service_logger.setLevel(self._log_level)
            self._custom_loggers[service_name] = service_logger
    
    def _create_detailed_formatter(self) -> logging.Formatter:
        """Create detailed log formatter"""
        return logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_console_formatter(self) -> logging.Formatter:
        """Create console log formatter"""
        return logging.Formatter(
            fmt='%(levelname)s - %(name)s - %(message)s'
        )
    
    def _create_service_filter(self) -> logging.Filter:
        """Create filter for service logs"""
        class ServiceFilter(logging.Filter):
            def filter(self, record):
                return record.name.startswith('services.')
        
        return ServiceFilter()
    
    def _load_logging_config(self) -> None:
        """Load logging configuration from settings"""
        if not self.settings_manager:
            return
        
        try:
            self._log_level = getattr(
                logging, 
                self.settings_manager.get('log_level', 'INFO').upper(),
                logging.INFO
            )
            
            self._console_logging = self.settings_manager.get('console_logging', True)
            self._max_file_size = self.settings_manager.get('max_log_file_size', 10 * 1024 * 1024)
            self._backup_count = self.settings_manager.get('log_backup_count', 5)
            
        except Exception as e:
            self.logger.error(f"Error loading logging config: {e}")
    
    def _reconfigure_logging(self) -> None:
        """Reconfigure logging with new settings"""
        self._setup_log_handlers()
        self._configure_root_logger()
        self.logger.info("Reconfigured logging")
    
    def _cleanup_handlers(self) -> None:
        """Clean up log handlers"""
        with self._handler_lock:
            for handler in self._handlers.values():
                try:
                    handler.close()
                except Exception as e:
                    print(f"Error closing handler: {e}")
            
            self._handlers.clear()
    
    def _notify_log_callbacks(self, record: logging.LogRecord) -> None:
        """Notify log callbacks"""
        with self._callbacks_lock:
            callbacks = self._log_callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(record)
            except Exception:
                # Avoid recursive logging
                pass 