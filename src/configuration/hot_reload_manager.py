#!/usr/bin/env python3
"""
Hot Reload Manager
Automatic configuration reloading with file watchers
"""

import os
import threading
import time
import logging
from typing import Dict, Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HotReloadManager:
    """
    Manages hot-reloading of configuration files
    
    Features:
    - File system watching
    - Automatic reload on changes
    - Change debouncing
    - Event callbacks
    """
    
    def __init__(self, config_manager):
        """
        Initialize hot reload manager
        
        Args:
            config_manager: ConfigurationManager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger("config.hotreload")
        
        # Watching state
        self.watchers: Dict[str, threading.Thread] = {}
        self.watching_files: Dict[str, float] = {}  # file_path -> last_modified
        self.is_watching = False
        
        # Debouncing
        self.debounce_delay = 1.0  # seconds
        self.pending_reloads: Dict[str, float] = {}  # file_path -> scheduled_time
        
        # Callbacks
        self.reload_callbacks: Dict[str, Callable] = {}
        
        # Control
        self._stop_event = threading.Event()
        self._main_watcher = None
    
    def start_watching(self) -> bool:
        """
        Start watching configuration files for changes
        
        Returns:
            True if watching started successfully
        """
        try:
            if self.is_watching:
                self.logger.warning("Hot reload manager is already watching")
                return True
            
            # Start main watcher thread
            self._stop_event.clear()
            self._main_watcher = threading.Thread(target=self._watch_loop, daemon=True)
            self._main_watcher.start()
            
            # Watch configuration source files
            self._setup_source_watchers()
            
            self.is_watching = True
            self.logger.info("Hot reload manager started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting hot reload manager: {e}")
            return False
    
    def stop_watching(self):
        """Stop watching configuration files"""
        try:
            self._stop_event.set()
            self.is_watching = False
            
            # Wait for main watcher to stop
            if self._main_watcher and self._main_watcher.is_alive():
                self._main_watcher.join(timeout=2.0)
            
            # Clear watchers
            self.watchers.clear()
            self.watching_files.clear()
            self.pending_reloads.clear()
            
            self.logger.info("Hot reload manager stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping hot reload manager: {e}")
    
    def watch_file(self, file_path: str, callback: Callable = None) -> bool:
        """
        Watch a specific file for changes
        
        Args:
            file_path: Path to file to watch
            callback: Optional callback for when file changes
            
        Returns:
            True if file is now being watched
        """
        try:
            file_path = os.path.abspath(file_path)
            
            if not os.path.exists(file_path):
                self.logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Get initial modification time
            self.watching_files[file_path] = os.path.getmtime(file_path)
            
            # Register callback if provided
            if callback:
                self.reload_callbacks[file_path] = callback
            
            self.logger.debug(f"Watching file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error watching file '{file_path}': {e}")
            return False
    
    def unwatch_file(self, file_path: str):
        """Stop watching a specific file"""
        file_path = os.path.abspath(file_path)
        
        if file_path in self.watching_files:
            del self.watching_files[file_path]
        
        if file_path in self.reload_callbacks:
            del self.reload_callbacks[file_path]
        
        if file_path in self.pending_reloads:
            del self.pending_reloads[file_path]
        
        self.logger.debug(f"Stopped watching file: {file_path}")
    
    def set_debounce_delay(self, delay: float):
        """
        Set debounce delay for file change events
        
        Args:
            delay: Delay in seconds
        """
        self.debounce_delay = max(0.1, delay)
        self.logger.debug(f"Set debounce delay to {self.debounce_delay} seconds")
    
    def force_reload(self, file_path: str = None):
        """
        Force reload of configuration
        
        Args:
            file_path: Specific file to reload (if None, reloads all)
        """
        if file_path:
            self._handle_file_change(file_path, force=True)
        else:
            self.config_manager.reload()
        
        self.logger.info(f"Forced reload of {'all configuration' if not file_path else file_path}")
    
    def _setup_source_watchers(self):
        """Set up watchers for configuration source files"""
        for source in self.config_manager.sources:
            if hasattr(source, 'file_path'):
                # File-based source
                file_path = str(source.file_path)
                if os.path.exists(file_path):
                    self.watch_file(file_path)
                else:
                    # Watch parent directory for file creation
                    parent_dir = os.path.dirname(file_path)
                    if os.path.exists(parent_dir):
                        self.watch_file(parent_dir)
    
    def _watch_loop(self):
        """Main watching loop"""
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # Check for file changes
                self._check_file_changes()
                
                # Process pending reloads
                self._process_pending_reloads(current_time)
                
                # Sleep for a short interval
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error in watch loop: {e}")
                time.sleep(1.0)
    
    def _check_file_changes(self):
        """Check all watched files for changes"""
        for file_path, last_modified in list(self.watching_files.items()):
            try:
                if os.path.exists(file_path):
                    current_modified = os.path.getmtime(file_path)
                    
                    if current_modified > last_modified:
                        # File was modified
                        self.watching_files[file_path] = current_modified
                        self._schedule_reload(file_path)
                else:
                    # File was deleted
                    self.logger.warning(f"Watched file was deleted: {file_path}")
                    self.unwatch_file(file_path)
                    
            except Exception as e:
                self.logger.error(f"Error checking file '{file_path}': {e}")
    
    def _schedule_reload(self, file_path: str):
        """Schedule a debounced reload for a file"""
        current_time = time.time()
        scheduled_time = current_time + self.debounce_delay
        
        self.pending_reloads[file_path] = scheduled_time
        
        self.logger.debug(f"Scheduled reload for {file_path} at {scheduled_time}")
    
    def _process_pending_reloads(self, current_time: float):
        """Process pending reloads that are ready"""
        ready_reloads = []
        
        for file_path, scheduled_time in list(self.pending_reloads.items()):
            if current_time >= scheduled_time:
                ready_reloads.append(file_path)
                del self.pending_reloads[file_path]
        
        # Process ready reloads
        for file_path in ready_reloads:
            self._handle_file_change(file_path)
    
    def _handle_file_change(self, file_path: str, force: bool = False):
        """Handle file change event"""
        try:
            self.logger.info(f"Configuration file changed: {file_path}")
            
            # Call specific callback if registered
            if file_path in self.reload_callbacks:
                try:
                    self.reload_callbacks[file_path](file_path)
                except Exception as e:
                    self.logger.error(f"Error in reload callback for '{file_path}': {e}")
            
            # Determine which source to reload
            source_name = self._get_source_for_file(file_path)
            
            if source_name:
                # Reload specific source
                success = self.config_manager.reload(source_name)
                if success:
                    self.logger.info(f"Reloaded configuration source: {source_name}")
                else:
                    self.logger.error(f"Failed to reload configuration source: {source_name}")
            else:
                # Reload all configuration
                success = self.config_manager.reload()
                if success:
                    self.logger.info("Reloaded all configuration")
                else:
                    self.logger.error("Failed to reload configuration")
            
        except Exception as e:
            self.logger.error(f"Error handling file change for '{file_path}': {e}")
    
    def _get_source_for_file(self, file_path: str) -> Optional[str]:
        """Get configuration source name for a file path"""
        file_path = os.path.abspath(file_path)
        
        for source in self.config_manager.sources:
            if hasattr(source, 'file_path'):
                source_file_path = os.path.abspath(str(source.file_path))
                if source_file_path == file_path:
                    return source.name
        
        return None
    
    def get_watch_status(self) -> Dict[str, Any]:
        """
        Get status of hot reload manager
        
        Returns:
            Dictionary with watch status information
        """
        return {
            'is_watching': self.is_watching,
            'watched_files_count': len(self.watching_files),
            'watched_files': list(self.watching_files.keys()),
            'pending_reloads_count': len(self.pending_reloads),
            'pending_reloads': list(self.pending_reloads.keys()),
            'debounce_delay': self.debounce_delay,
            'callbacks_count': len(self.reload_callbacks)
        } 