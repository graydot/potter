#!/usr/bin/env python3
"""
Single Instance Checker Utility
Ensures only one instance of the application is running
"""

import os
import signal
import atexit
import logging

logger = logging.getLogger(__name__)


class SingleInstanceChecker:
    """Ensures only one instance of the application is running"""
    
    def __init__(self, app_name="potter"):
        self.app_name = app_name
        self.pid_file = os.path.expanduser(f"~/.{app_name}.pid")
        self.is_running = False
    
    def is_already_running(self):
        """Check if another instance is already running"""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if the process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                logger.warning(f"Another instance is already running (PID: {old_pid})")
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                logger.info("Removing stale PID file")
                os.remove(self.pid_file)
                return False
                
        except (ValueError, IOError) as e:
            logger.warning(f"Error reading PID file: {e}")
            # Remove corrupted PID file
            try:
                os.remove(self.pid_file)
            except:
                pass
            return False
    
    def create_pid_file(self):
        """Create a PID file for this instance"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.is_running = True
            
            # Register cleanup function
            atexit.register(self.cleanup)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            logger.info(f"Created PID file: {self.pid_file}")
            return True
        except IOError as e:
            logger.error(f"Failed to create PID file: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, cleaning up...")
        self.cleanup()
        import sys
        sys.exit(0)
    
    def cleanup(self):
        """Remove the PID file"""
        if self.is_running and os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
                logger.info("Cleaned up PID file")
            except IOError as e:
                logger.warning(f"Failed to remove PID file: {e}")
        self.is_running = False 