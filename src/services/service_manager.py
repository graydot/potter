#!/usr/bin/env python3
"""
Service Manager
Dependency injection container and service lifecycle manager
"""

import logging
from typing import Dict, Type, TypeVar, Optional, List, Any
from threading import Lock

from .base_service import BaseService
from core.exceptions import ServiceError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseService)


class ServiceManager:
    """
    Service Manager for dependency injection and lifecycle management
    
    Features:
    - Service registration and dependency injection
    - Lifecycle management (start/stop all services)
    - Service discovery and resolution
    - Configuration management
    - Health monitoring
    """
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._service_types: Dict[Type[BaseService], str] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._lock = Lock()
        self._global_config: Dict[str, Any] = {}
        
    def register_service(self, name: str, service_class_or_instance, 
                         dependencies: Optional[List[str]] = None) -> None:
        """
        Register a service with the manager
        
        Args:
            name: Name to register the service under
            service_class_or_instance: Service class or instance to register
            dependencies: List of service names this service depends on
        """
        with self._lock:
            if name in self._services:
                raise ServiceError(f"Service '{name}' is already registered")
            
            # Handle both class and instance registration
            if isinstance(service_class_or_instance, type):
                # It's a class, instantiate it
                service_instance = service_class_or_instance()
            else:
                # It's already an instance
                service_instance = service_class_or_instance
            
            # Update service name if it differs
            service_instance.name = name
            
            self._services[name] = service_instance
            self._service_types[type(service_instance)] = name
            self._dependencies[name] = dependencies or []
            
            # Apply global config to the service
            if self._global_config:
                service_instance.update_config(self._global_config)
            
            logger.info(f"📝 Registered service: {name}")
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service by type
        
        Args:
            service_type: Service class type
            
        Returns:
            Service instance
            
        Raises:
            ServiceError: If service not found
        """
        with self._lock:
            service_name = self._service_types.get(service_type)
            if service_name is None:
                raise ServiceError(f"Service of type {service_type.__name__} not registered")
            
            return self._services[service_name]
    
    def get_service_by_name(self, name: str) -> BaseService:
        """
        Get a service by name
        
        Args:
            name: Service name
            
        Returns:
            Service instance
            
        Raises:
            ServiceError: If service not found
        """
        with self._lock:
            if name not in self._services:
                raise ServiceError(f"Service '{name}' not registered")
            
            return self._services[name]
    
    def is_service_registered(self, name: str) -> bool:
        """
        Check if a service is registered
        
        Args:
            name: Service name
            
        Returns:
            bool: True if service is registered
        """
        with self._lock:
            return name in self._services
    
    def is_service_running(self, name: str) -> bool:
        """
        Check if a service is running
        
        Args:
            name: Service name
            
        Returns:
            bool: True if service is running
        """
        with self._lock:
            if name not in self._services:
                return False
            return self._services[name].is_running
    
    def start_service(self, name: str) -> bool:
        """
        Start a specific service
        
        Args:
            name: Service name to start
            
        Returns:
            bool: True if service started successfully
        """
        with self._lock:
            if name not in self._services:
                raise ServiceError(f"Service '{name}' not registered")
            
            service = self._services[name]
            
            # Start dependencies first
            dependencies = self._dependencies.get(name, [])
            for dep_name in dependencies:
                if dep_name in self._services:
                    dep_service = self._services[dep_name]
                    if not dep_service.is_running:
                        if not self.start_service(dep_name):
                            raise ServiceError(f"Failed to start dependency '{dep_name}' for service '{name}'")
            
            return service.start()
    
    def start_all_services(self) -> bool:
        """
        Start all registered services in dependency order
        
        Returns:
            bool: True if all services started successfully
        """
        logger.info("🚀 Starting all services...")
        
        # Resolve dependency order
        start_order = self._resolve_dependency_order()
        
        started_services = []
        try:
            for service_name in start_order:
                service = self._services[service_name]
                if not service.start():
                    raise ServiceError(f"Failed to start service: {service_name}")
                started_services.append(service_name)
            
            logger.info(f"✅ All {len(started_services)} services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start services: {e}")
            
            # Stop already started services in reverse order
            for service_name in reversed(started_services):
                try:
                    self._services[service_name].stop()
                except Exception as stop_error:
                    logger.error(f"Failed to stop service {service_name} during rollback: {stop_error}")
            
            raise ServiceError("Failed to start all services", details=str(e))
    
    def stop_all_services(self) -> bool:
        """
        Stop all registered services in reverse dependency order
        
        Returns:
            bool: True if all services stopped successfully
        """
        logger.info("🛑 Stopping all services...")
        
        # Stop in reverse dependency order
        start_order = self._resolve_dependency_order()
        stop_order = list(reversed(start_order))
        
        errors = []
        stopped_count = 0
        
        for service_name in stop_order:
            service = self._services[service_name]
            if service.is_running:
                try:
                    service.stop()
                    stopped_count += 1
                except Exception as e:
                    logger.error(f"Failed to stop service {service_name}: {e}")
                    errors.append(f"{service_name}: {e}")
        
        if errors:
            logger.warning(f"⚠️ Some services failed to stop cleanly: {errors}")
            return False
        else:
            logger.info(f"✅ All {stopped_count} services stopped successfully")
            return True
    
    def restart_all_services(self) -> bool:
        """
        Restart all services
        
        Returns:
            bool: True if restart successful
        """
        logger.info("🔄 Restarting all services...")
        self.stop_all_services()
        return self.start_all_services()
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all registered services
        
        Returns:
            Dict mapping service names to their status
        """
        with self._lock:
            status = {}
            for name, service in self._services.items():
                try:
                    status[name] = service.get_status()
                except Exception as e:
                    status[name] = {
                        'name': name,
                        'running': False,
                        'error': str(e)
                    }
            return status
    
    def update_global_config(self, config: Dict[str, Any]) -> None:
        """
        Update global configuration for all services
        
        Args:
            config: Global configuration dictionary
        """
        with self._lock:
            self._global_config.update(config)
            
            # Apply to all registered services
            for service in self._services.values():
                try:
                    service.update_config(config)
                except Exception as e:
                    logger.error(f"Failed to update config for {service.name}: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all services
        
        Returns:
            Health status summary
        """
        status = self.get_all_status()
        
        total_services = len(status)
        running_services = sum(1 for s in status.values() if s.get('running', False))
        healthy_services = sum(1 for s in status.values() 
                             if s.get('running', False) and 'error' not in s)
        
        health_summary = {
            'timestamp': logger.handlers[0].formatter.formatTime(logger.makeRecord(
                '', 0, '', 0, '', (), None
            )) if logger.handlers else None,
            'total_services': total_services,
            'running_services': running_services,
            'healthy_services': healthy_services,
            'overall_health': 'healthy' if healthy_services == total_services else 'degraded',
            'services': status
        }
        
        return health_summary
    
    def _resolve_dependency_order(self) -> List[str]:
        """
        Resolve service start order based on dependencies using topological sort
        
        Returns:
            List of service names in dependency order
            
        Raises:
            ServiceError: If circular dependencies detected
        """
        # Kahn's algorithm for topological sorting
        in_degree = {name: 0 for name in self._services.keys()}
        
        # Calculate in-degrees
        for service_name, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._services:
                    raise ServiceError(f"Service '{service_name}' depends on unregistered service '{dep}'")
                in_degree[service_name] += 1
        
        # Start with services that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Remove edges from current node
            for service_name, deps in self._dependencies.items():
                if current in deps:
                    in_degree[service_name] -= 1
                    if in_degree[service_name] == 0:
                        queue.append(service_name)
        
        # Check for circular dependencies
        if len(result) != len(self._services):
            remaining = set(self._services.keys()) - set(result)
            raise ServiceError(f"Circular dependency detected among services: {remaining}")
        
        return result
    
    def list_services(self) -> List[Dict[str, Any]]:
        """
        List all registered services with basic info
        
        Returns:
            List of service information
        """
        with self._lock:
            services_info = []
            for name, service in self._services.items():
                info = {
                    'name': name,
                    'type': type(service).__name__,
                    'running': service.is_running,
                    'dependencies': self._dependencies.get(name, [])
                }
                services_info.append(info)
            
            return services_info
    
    def clear_all_services(self) -> None:
        """
        Clear all registered services (stop them first if running)
        """
        self.stop_all_services()
        with self._lock:
            self._services.clear()
            self._service_types.clear()
            self._dependencies.clear()
            logger.info("🧹 Cleared all services")


# Global service manager instance
_service_manager = None
_service_manager_lock = Lock()


def get_service_manager() -> ServiceManager:
    """
    Get the global service manager instance (singleton)
    
    Returns:
        ServiceManager instance
    """
    global _service_manager
    
    if _service_manager is None:
        with _service_manager_lock:
            if _service_manager is None:
                _service_manager = ServiceManager()
                logger.info("🔧 Created global service manager")
    
    return _service_manager


def get_service(service_type: Type[T]) -> T:
    """
    Convenience function to get a service from the global manager
    
    Args:
        service_type: Service class type
        
    Returns:
        Service instance
    """
    return get_service_manager().get_service(service_type) 