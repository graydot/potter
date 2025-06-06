#!/usr/bin/env python3
"""
Service-Aware Component Base Class
Base class for UI components that integrate with the service layer
"""

import logging
from typing import Any, Optional, List, Tuple, Callable
from threading import Lock

logger = logging.getLogger(__name__)


class ServiceAwareComponent:
    """
    Base class for UI components that use services
    
    Provides:
    - Service dependency injection
    - Service event subscription management
    - Automatic cleanup of service subscriptions
    - Service availability checks
    - Error handling for service failures
    """
    
    def __init__(self, service_manager=None, component_name: str = None):
        """
        Initialize service-aware component
        
        Args:
            service_manager: ServiceManager instance (auto-detected if None)
            component_name: Name for logging and debugging
        """
        self.component_name = component_name or self.__class__.__name__
        self.logger = logging.getLogger(f"ui.{self.component_name.lower()}")
        
        # Service management
        self._service_manager = service_manager
        self._service_subscriptions: List[Tuple[Any, str, Callable]] = []
        self._cached_services = {}
        self._subscription_lock = Lock()
        
        # Component state
        self._is_initialized = False
        self._is_disposed = False
        
        self.logger.debug(f"Created service-aware component: {self.component_name}")
    
    @property
    def service_manager(self):
        """Get service manager instance (lazy loading)"""
        if self._service_manager is None:
            try:
                from services import get_service_manager
                self._service_manager = get_service_manager()
                self.logger.debug("Service manager loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load service manager: {e}")
                raise
        return self._service_manager
    
    def get_service(self, service_type):
        """
        Get service instance with caching
        
        Args:
            service_type: Service class or service name
            
        Returns:
            Service instance
            
        Raises:
            ServiceError: If service is not available
        """
        service_key = getattr(service_type, '__name__', str(service_type))
        
        # Check cache first
        if service_key in self._cached_services:
            return self._cached_services[service_key]
        
        try:
            service = self.service_manager.get_service(service_type)
            if service is None:
                raise RuntimeError(f"Service {service_key} is not available")
            
            # Cache the service
            self._cached_services[service_key] = service
            self.logger.debug(f"Cached service: {service_key}")
            
            return service
            
        except Exception as e:
            self.logger.error(f"Failed to get service {service_key}: {e}")
            raise
    
    def get_service_safely(self, service_type, default=None):
        """
        Get service instance safely (returns default if unavailable)
        
        Args:
            service_type: Service class or service name
            default: Default value if service unavailable
            
        Returns:
            Service instance or default value
        """
        try:
            return self.get_service(service_type)
        except Exception as e:
            self.logger.warning(f"Service {service_type} unavailable: {e}")
            return default
    
    def subscribe_to_service(self, service_type, event: str, callback: Callable):
        """
        Subscribe to service events
        
        Args:
            service_type: Service class or service name
            event: Event name to subscribe to
            callback: Callback function for event
        """
        try:
            service = self.get_service(service_type)
            
            # Check if service supports event subscription
            if not hasattr(service, 'subscribe'):
                self.logger.warning(f"Service {service_type} does not support event subscription")
                return
            
            # Subscribe to event
            service.subscribe(event, callback)
            
            # Track subscription for cleanup
            with self._subscription_lock:
                self._service_subscriptions.append((service, event, callback))
            
            self.logger.debug(f"Subscribed to {service_type}.{event}")
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {service_type}.{event}: {e}")
    
    def unsubscribe_from_service(self, service_type, event: str, callback: Callable):
        """
        Unsubscribe from service events
        
        Args:
            service_type: Service class or service name
            event: Event name to unsubscribe from
            callback: Callback function to remove
        """
        try:
            service = self.get_service(service_type)
            
            if hasattr(service, 'unsubscribe'):
                service.unsubscribe(event, callback)
            
            # Remove from tracking
            with self._subscription_lock:
                self._service_subscriptions = [
                    (s, e, c) for s, e, c in self._service_subscriptions
                    if not (s == service and e == event and c == callback)
                ]
            
            self.logger.debug(f"Unsubscribed from {service_type}.{event}")
            
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from {service_type}.{event}: {e}")
    
    def is_service_available(self, service_type) -> bool:
        """
        Check if a service is available
        
        Args:
            service_type: Service class or service name
            
        Returns:
            True if service is available and running
        """
        try:
            service = self.get_service_safely(service_type)
            if service is None:
                return False
            
            # Check if service is running
            if hasattr(service, 'is_running'):
                return service.is_running()
            
            return True
            
        except Exception:
            return False
    
    def initialize(self):
        """
        Initialize the component
        Override in subclasses for custom initialization
        """
        if self._is_initialized:
            return
        
        self.logger.debug(f"Initializing component: {self.component_name}")
        
        try:
            # Initialize services if needed
            self._initialize_services()
            
            # Custom initialization
            self._on_initialize()
            
            self._is_initialized = True
            self.logger.info(f"Component initialized: {self.component_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize component {self.component_name}: {e}")
            raise
    
    def _initialize_services(self):
        """Initialize required services - override in subclasses"""
        pass
    
    def _on_initialize(self):
        """Custom initialization logic - override in subclasses"""
        pass
    
    def cleanup(self):
        """
        Cleanup component and service subscriptions
        """
        if self._is_disposed:
            return
        
        self.logger.debug(f"Cleaning up component: {self.component_name}")
        
        try:
            # Custom cleanup
            self._on_cleanup()
            
            # Cleanup service subscriptions
            self._cleanup_service_subscriptions()
            
            # Clear cached services
            self._cached_services.clear()
            
            self._is_disposed = True
            self.logger.info(f"Component cleaned up: {self.component_name}")
            
        except Exception as e:
            self.logger.error(f"Error during component cleanup: {e}")
    
    def _cleanup_service_subscriptions(self):
        """Cleanup all service subscriptions"""
        with self._subscription_lock:
            for service, event, callback in self._service_subscriptions:
                try:
                    if hasattr(service, 'unsubscribe'):
                        service.unsubscribe(event, callback)
                except Exception as e:
                    self.logger.error(f"Error unsubscribing from {event}: {e}")
            
            self._service_subscriptions.clear()
    
    def _on_cleanup(self):
        """Custom cleanup logic - override in subclasses"""
        pass
    
    def handle_service_error(self, service_type, error: Exception, context: str = ""):
        """
        Handle service errors gracefully
        
        Args:
            service_type: Service that caused the error
            error: Exception that occurred
            context: Additional context information
        """
        service_name = getattr(service_type, '__name__', str(service_type))
        error_msg = f"Service error in {service_name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {error}"
        
        self.logger.error(error_msg)
        
        # Custom error handling
        self._on_service_error(service_type, error, context)
    
    def _on_service_error(self, service_type, error: Exception, context: str):
        """Custom service error handling - override in subclasses"""
        pass
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        return False
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        if not self._is_disposed:
            try:
                self.cleanup()
            except Exception:
                pass  # Avoid exceptions in destructor 