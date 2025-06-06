#!/usr/bin/env python3
"""
UI Service Manager
Manages UI component lifecycle and service integration
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from threading import Lock
import weakref

logger = logging.getLogger(__name__)


class UIServiceManager:
    """
    UI-specific service management and component lifecycle
    
    Features:
    - UI component registration and lifecycle management
    - Service dependency management for UI
    - Theme change propagation
    - Error handling and recovery
    - UI update coordination
    - Component cleanup management
    """
    
    def __init__(self, service_manager):
        """
        Initialize UI service manager
        
        Args:
            service_manager: Core ServiceManager instance
        """
        self.service_manager = service_manager
        self.logger = logging.getLogger("ui.service_manager")
        
        # UI component management
        self._ui_components: List[Any] = []
        self._component_registry: Dict[str, Any] = {}
        self._component_lock = Lock()
        
        # Event handlers
        self._theme_change_handlers: List[Callable] = []
        self._settings_change_handlers: List[Callable] = []
        self._error_handlers: List[Callable] = []
        
        # State
        self._is_initialized = False
        self._is_shutting_down = False
        
        self.logger.info("UI Service Manager created")
    
    def initialize(self):
        """Initialize UI service manager"""
        if self._is_initialized:
            return
        
        self.logger.info("Initializing UI Service Manager...")
        
        try:
            # Set up service event subscriptions
            self._setup_service_subscriptions()
            
            self._is_initialized = True
            self.logger.info("UI Service Manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize UI Service Manager: {e}")
            raise
    
    def _setup_service_subscriptions(self):
        """Set up subscriptions to service events"""
        try:
            # Subscribe to theme service events
            theme_service = self.service_manager.get_service("theme")
            if theme_service and hasattr(theme_service, 'subscribe'):
                theme_service.subscribe('theme_changed', self._on_theme_changed)
                self.logger.debug("Subscribed to theme change events")
            
            # Subscribe to settings service events
            settings_service = self.service_manager.get_service("settings")
            if settings_service and hasattr(settings_service, 'subscribe'):
                settings_service.subscribe('settings_changed', self._on_settings_changed)
                self.logger.debug("Subscribed to settings change events")
                
        except Exception as e:
            self.logger.warning(f"Could not set up all service subscriptions: {e}")
    
    def register_ui_component(self, component, component_id: str = None):
        """
        Register UI component for lifecycle management
        
        Args:
            component: UI component instance
            component_id: Optional unique identifier for the component
        """
        if self._is_shutting_down:
            self.logger.warning("Cannot register component during shutdown")
            return
        
        with self._component_lock:
            # Use weak reference to avoid circular references
            weak_ref = weakref.ref(component, self._component_cleanup_callback)
            self._ui_components.append(weak_ref)
            
            if component_id:
                self._component_registry[component_id] = weak_ref
            
            component_name = getattr(component, 'component_name', component.__class__.__name__)
            self.logger.debug(f"Registered UI component: {component_name}")
            
            # Initialize component if it supports it
            if hasattr(component, 'initialize') and not getattr(component, '_is_initialized', False):
                try:
                    component.initialize()
                except Exception as e:
                    self.logger.error(f"Failed to initialize component {component_name}: {e}")
    
    def unregister_ui_component(self, component_id: str):
        """
        Unregister UI component
        
        Args:
            component_id: Component identifier
        """
        with self._component_lock:
            if component_id in self._component_registry:
                weak_ref = self._component_registry[component_id]
                component = weak_ref()
                
                if component:
                    # Cleanup component
                    if hasattr(component, 'cleanup'):
                        try:
                            component.cleanup()
                        except Exception as e:
                            self.logger.error(f"Error cleaning up component {component_id}: {e}")
                
                # Remove from registry
                del self._component_registry[component_id]
                
                # Remove from components list
                self._ui_components = [ref for ref in self._ui_components if ref != weak_ref]
                
                self.logger.debug(f"Unregistered UI component: {component_id}")
    
    def get_component(self, component_id: str):
        """
        Get registered component by ID
        
        Args:
            component_id: Component identifier
            
        Returns:
            Component instance or None if not found
        """
        with self._component_lock:
            weak_ref = self._component_registry.get(component_id)
            if weak_ref:
                return weak_ref()
            return None
    
    def _component_cleanup_callback(self, weak_ref):
        """Callback for component garbage collection"""
        with self._component_lock:
            if weak_ref in self._ui_components:
                self._ui_components.remove(weak_ref)
    
    def add_theme_change_handler(self, handler: Callable[[Dict], None]):
        """
        Add handler for theme changes
        
        Args:
            handler: Function to call when theme changes
        """
        self._theme_change_handlers.append(handler)
        self.logger.debug("Added theme change handler")
    
    def add_settings_change_handler(self, handler: Callable[[Dict], None]):
        """
        Add handler for settings changes
        
        Args:
            handler: Function to call when settings change
        """
        self._settings_change_handlers.append(handler)
        self.logger.debug("Added settings change handler")
    
    def add_error_handler(self, handler: Callable[[Exception, str], None]):
        """
        Add handler for UI errors
        
        Args:
            handler: Function to call when UI errors occur
        """
        self._error_handlers.append(handler)
        self.logger.debug("Added error handler")
    
    def _on_theme_changed(self, theme_info: Dict):
        """Handle theme change events"""
        self.logger.debug(f"Theme changed: {theme_info}")
        
        # Notify all components
        self._notify_components('_on_theme_changed', theme_info)
        
        # Call registered handlers
        for handler in self._theme_change_handlers:
            try:
                handler(theme_info)
            except Exception as e:
                self.logger.error(f"Error in theme change handler: {e}")
    
    def _on_settings_changed(self, settings: Dict):
        """Handle settings change events"""
        self.logger.debug("Settings changed")
        
        # Notify all components
        self._notify_components('_on_settings_changed', settings)
        
        # Call registered handlers
        for handler in self._settings_change_handlers:
            try:
                handler(settings)
            except Exception as e:
                self.logger.error(f"Error in settings change handler: {e}")
    
    def _notify_components(self, method_name: str, *args, **kwargs):
        """
        Notify all components of an event
        
        Args:
            method_name: Method name to call on components
            *args, **kwargs: Arguments to pass to method
        """
        with self._component_lock:
            # Create a copy to avoid modification during iteration
            components = list(self._ui_components)
        
        for weak_ref in components:
            component = weak_ref()
            if component is None:
                continue
            
            try:
                if hasattr(component, method_name):
                    method = getattr(component, method_name)
                    method(*args, **kwargs)
            except Exception as e:
                component_name = getattr(component, 'component_name', component.__class__.__name__)
                self.logger.error(f"Error notifying component {component_name}: {e}")
    
    def handle_ui_error(self, error: Exception, context: str = ""):
        """
        Handle UI errors
        
        Args:
            error: Exception that occurred
            context: Context information
        """
        error_msg = f"UI Error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {error}"
        
        self.logger.error(error_msg)
        
        # Notify error handlers
        for handler in self._error_handlers:
            try:
                handler(error, context)
            except Exception as e:
                self.logger.error(f"Error in error handler: {e}")
    
    def refresh_all_components(self):
        """Refresh all registered components"""
        self.logger.debug("Refreshing all UI components")
        self._notify_components('refresh')
    
    def update_all_themes(self):
        """Update theme for all components"""
        try:
            theme_service = self.service_manager.get_service("theme")
            if theme_service:
                theme_info = theme_service.get_current_theme()
                self._on_theme_changed(theme_info)
        except Exception as e:
            self.logger.error(f"Failed to update themes: {e}")
    
    def validate_all_components(self):
        """Validate all components using ValidationService"""
        self.logger.debug("Validating all UI components")
        
        try:
            validation_service = self.service_manager.get_service("validation")
            if not validation_service:
                self.logger.warning("Validation service not available")
                return
            
            self._notify_components('validate')
            
        except Exception as e:
            self.logger.error(f"Failed to validate components: {e}")
    
    def get_component_status(self) -> Dict[str, Any]:
        """
        Get status of all registered components
        
        Returns:
            Dictionary with component status information
        """
        with self._component_lock:
            active_components = []
            dead_components = 0
            
            for weak_ref in self._ui_components:
                component = weak_ref()
                if component is None:
                    dead_components += 1
                else:
                    component_name = getattr(component, 'component_name', component.__class__.__name__)
                    is_initialized = getattr(component, '_is_initialized', False)
                    active_components.append({
                        'name': component_name,
                        'initialized': is_initialized,
                        'type': component.__class__.__name__
                    })
            
            return {
                'total_registered': len(self._ui_components),
                'active_components': len(active_components),
                'dead_references': dead_components,
                'components': active_components,
                'theme_handlers': len(self._theme_change_handlers),
                'settings_handlers': len(self._settings_change_handlers),
                'error_handlers': len(self._error_handlers)
            }
    
    def shutdown(self):
        """Shutdown UI service manager and cleanup all components"""
        if self._is_shutting_down:
            return
        
        self.logger.info("Shutting down UI Service Manager...")
        self._is_shutting_down = True
        
        try:
            # Cleanup all registered components
            with self._component_lock:
                components = list(self._ui_components)
            
            for weak_ref in components:
                component = weak_ref()
                if component and hasattr(component, 'cleanup'):
                    try:
                        component_name = getattr(component, 'component_name', component.__class__.__name__)
                        self.logger.debug(f"Cleaning up component: {component_name}")
                        component.cleanup()
                    except Exception as e:
                        self.logger.error(f"Error during component cleanup: {e}")
            
            # Clear all references
            with self._component_lock:
                self._ui_components.clear()
                self._component_registry.clear()
            
            # Clear handlers
            self._theme_change_handlers.clear()
            self._settings_change_handlers.clear()
            self._error_handlers.clear()
            
            self.logger.info("UI Service Manager shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error during UI Service Manager shutdown: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        if not self._is_shutting_down:
            try:
                self.shutdown()
            except Exception:
                pass  # Avoid exceptions in destructor 