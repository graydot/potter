#!/usr/bin/env python3
"""
Base Service Interface
Defines the common interface and functionality for all services
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from threading import Lock

from core.exceptions import ServiceError

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Base class for all services in the Potter application
    
    Provides common functionality like:
    - Lifecycle management (start/stop)
    - Error handling
    - Thread safety
    - Configuration management
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service
        
        Args:
            name: Service name for logging and identification
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._is_running = False
        self._lock = Lock()
        self.logger = logging.getLogger(f"services.{name}")
        
    @property
    def is_running(self) -> bool:
        """Check if service is currently running"""
        with self._lock:
            return self._is_running
    
    def start(self) -> bool:
        """
        Start the service
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        with self._lock:
            if self._is_running:
                self.logger.warning(f"Service {self.name} is already running")
                return True
                
            try:
                self._start_service()
                self._is_running = True
                self.logger.info(f"✅ Service {self.name} started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Failed to start service {self.name}: {e}")
                raise ServiceError(f"Failed to start {self.name} service", details=str(e))
    
    def stop(self) -> bool:
        """
        Stop the service
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._lock:
            if not self._is_running:
                self.logger.warning(f"Service {self.name} is not running")
                return True
                
            try:
                self._stop_service()
                self._is_running = False
                self.logger.info(f"🛑 Service {self.name} stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Failed to stop service {self.name}: {e}")
                raise ServiceError(f"Failed to stop {self.name} service", details=str(e))
    
    def restart(self) -> bool:
        """
        Restart the service
        
        Returns:
            bool: True if restarted successfully, False otherwise
        """
        self.logger.info(f"🔄 Restarting service {self.name}")
        if self.is_running:
            self.stop()
        return self.start()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service status information
        
        Returns:
            Dict with service status details
        """
        status = {
            'name': self.name,
            'running': self.is_running,
            'config': self.config.copy()
        }
        
        # Add service-specific status
        try:
            service_status = self._get_service_status()
            status.update(service_status)
        except Exception as e:
            self.logger.warning(f"Failed to get service-specific status: {e}")
            status['status_error'] = str(e)
            
        return status
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update service configuration
        
        Args:
            new_config: New configuration dictionary
        """
        with self._lock:
            old_config = self.config.copy()
            self.config.update(new_config)
            
            try:
                self._handle_config_update(old_config, self.config)
                self.logger.info(f"📝 Updated configuration for service {self.name}")
            except Exception as e:
                # Rollback on error
                self.config = old_config
                self.logger.error(f"❌ Failed to update config for {self.name}: {e}")
                raise ServiceError(f"Failed to update {self.name} config", details=str(e))
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    def _start_service(self) -> None:
        """
        Start the service implementation
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def _stop_service(self) -> None:
        """
        Stop the service implementation
        Must be implemented by subclasses
        """
        pass
    
    def _get_service_status(self) -> Dict[str, Any]:
        """
        Get service-specific status information
        Optional override for subclasses
        
        Returns:
            Dict with service-specific status
        """
        return {}
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """
        Handle configuration updates
        Optional override for subclasses
        
        Args:
            old_config: Previous configuration
            new_config: New configuration
        """
        pass
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', running={self.is_running})>" 