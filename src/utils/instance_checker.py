#!/usr/bin/env python3
"""
Single Instance Checker Utility
Ensures only one instance of the application is running
Supports build version comparison for smart instance management
"""

import os
import signal
import atexit
import logging
import json
import sys
from datetime import datetime

logger = logging.getLogger(__name__)


def load_build_id():
    """Load build ID from the current app bundle"""
    try:
        # Try to find build ID file in app bundle first
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle - the build_id.json is in the app bundle's Resources directory
            # sys.executable points to: Potter.app/Contents/MacOS/Potter
            # We need: Potter.app/Contents/Resources/build_id.json
            executable_path = sys.executable
            if executable_path.endswith('Potter'):
                # Navigate from MacOS/Potter to Resources/build_id.json
                app_contents_path = os.path.dirname(executable_path)  # Contents/MacOS
                app_contents_path = os.path.dirname(app_contents_path)  # Contents
                resources_path = os.path.join(app_contents_path, 'Resources')
                build_id_file = os.path.join(resources_path, 'build_id.json')
                
                if os.path.exists(build_id_file):
                    with open(build_id_file, 'r') as f:
                        return json.load(f)
            
            # Fallback: try in _MEIPASS (shouldn't be needed but just in case)
            build_id_file = os.path.join(sys._MEIPASS, 'build_id.json')
            if os.path.exists(build_id_file):
                with open(build_id_file, 'r') as f:
                    return json.load(f)
        else:
            # Running from source (development)
            build_id_file = os.path.join(os.path.dirname(__file__), '..', '..', 'build_id.json')
            if os.path.exists(build_id_file):
                with open(build_id_file, 'r') as f:
                    return json.load(f)
        
        # Fallback: generate a development build ID
        return {
            "build_id": "dev_build",
            "timestamp": datetime.now().isoformat(),
            "unix_timestamp": int(datetime.now().timestamp()),
            "version": "development"
        }
            
    except Exception as e:
        logger.warning(f"Could not load build ID: {e}")
        return {
            "build_id": "unknown_build",
            "timestamp": datetime.now().isoformat(),
            "unix_timestamp": int(datetime.now().timestamp()),
            "version": "unknown"
        }


def show_build_conflict_dialog(current_build, running_build):
    """Show dialog when different builds are detected"""
    try:
        # Try to use macOS native dialog
        from AppKit import NSAlert, NSAlertFirstButtonReturn, NSApplication
        from datetime import datetime
        
        logger.info("Attempting to show build conflict dialog")
        
        # Ensure NSApplication is initialized
        app = NSApplication.sharedApplication()
        logger.info("NSApplication initialized for build conflict dialog")
        
        # Determine which build is newer
        current_ts = current_build.get('timestamp', '')
        running_ts = running_build.get('timestamp', '')
        
        if current_ts and running_ts:
            current_time = datetime.fromisoformat(current_ts.replace('Z', '+00:00'))
            running_time = datetime.fromisoformat(running_ts.replace('Z', '+00:00'))
            
            if current_time > running_time:
                age_info = "A newer build is available."
                action_info = "Replace the older running instance?"
            elif current_time < running_time:
                age_info = "A newer build is currently running."
                action_info = "Replace with this older build?"
            else:
                age_info = "The same build is currently running."
                action_info = "Replace the running instance?"
        else:
            age_info = "Different builds detected."
            action_info = "Replace the running instance?"
        
        # Format timestamps for display
        current_dt = datetime.fromisoformat(current_build.get('timestamp', ''))
        running_dt = datetime.fromisoformat(running_build.get('timestamp', ''))
        
        current_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        running_str = running_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create alert
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Potter Instance Conflict")
        alert.setInformativeText_(
            f"{age_info}\n\n"
            f"Running: {running_build.get('build_id', 'unknown')} ({running_str})\n"
            f"Current: {current_build.get('build_id', 'unknown')} ({current_str})\n\n"
            f"{action_info}"
        )
        alert.addButtonWithTitle_("Replace Running Instance")
        alert.addButtonWithTitle_("Keep Running Instance")
        
        logger.info("Build conflict alert configured, showing modal dialog...")
        
        # Show dialog
        response = alert.runModal()
        
        logger.info(f"Build conflict dialog response: {response} (NSAlertFirstButtonReturn: {NSAlertFirstButtonReturn})")
        
        # NSAlertFirstButtonReturn is the first button (Replace)
        result = response == NSAlertFirstButtonReturn
        logger.info(f"User choice: {'Replace' if result else 'Keep'} running instance")
        return result
        
    except ImportError:
        # If PyObjC not available, don't prompt user in terminal for GUI app
        logger.error("PyObjC not available - cannot show GUI dialog")
        logger.error("Potter Instance Conflict:")
        logger.error(f"Running: {running_build.get('build_id', 'unknown')}")
        logger.error(f"Current: {current_build.get('build_id', 'unknown')}")
        logger.error("Unable to resolve conflict without GUI - keeping running instance")
        return False
    except Exception as e:
        # Handle any other errors gracefully
        logger.error(f"Error showing build conflict dialog: {e}")
        logger.error("Keeping running instance due to dialog error")
        return False


class SingleInstanceChecker:
    """Ensures only one instance of the application is running with build awareness"""
    
    def __init__(self, app_name="potter"):
        self.app_name = app_name
        self.pid_file = os.path.expanduser(f"~/.{app_name}.pid")
        self.build_file = os.path.expanduser(f"~/.{app_name}.build")
        self.is_running = False
        self.current_build = load_build_id()
    
    def get_running_build_info(self):
        """Get build info of currently running instance"""
        try:
            if os.path.exists(self.build_file):
                with open(self.build_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read running build info: {e}")
        return None
    
    def save_build_info(self):
        """Save current build info to build file"""
        try:
            with open(self.build_file, 'w') as f:
                json.dump(self.current_build, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Could not save build info: {e}")
            return False
    
    def is_already_running(self):
        """Check if another instance is already running and handle build conflicts"""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if the process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                
                # Process exists, check build compatibility
                running_build = self.get_running_build_info()
                
                if running_build:
                    current_build_id = self.current_build.get('build_id', 'unknown')
                    running_build_id = running_build.get('build_id', 'unknown')
                    
                    if current_build_id == running_build_id:
                        # Same build - show GUI dialog asking user what to do
                        logger.info(f"Same build already running (PID: {old_pid})")
                        
                        should_replace = self.show_same_build_dialog(old_pid)
                        
                        if should_replace:
                            # Kill the old instance
                            try:
                                logger.info(f"Terminating old instance (PID: {old_pid})")
                                os.kill(old_pid, signal.SIGTERM)
                                
                                # Wait a moment for graceful shutdown
                                import time
                                time.sleep(1)
                                
                                # Force kill if still running
                                try:
                                    os.kill(old_pid, 0)
                                    logger.warning("Forcing termination of old instance")
                                    os.kill(old_pid, signal.SIGKILL)
                                    time.sleep(0.5)
                                except OSError:
                                    pass  # Process already terminated
                                
                                # Clean up old files
                                self.cleanup_old_files()
                                return False  # Allow new instance to start
                                
                            except OSError as e:
                                logger.error(f"Could not terminate old instance: {e}")
                                return True  # Fail to start if can't kill old
                        else:
                            # User chose to keep old instance
                            logger.info("User chose to keep running instance")
                            return True
                    else:
                        # Different builds, ask user what to do
                        logger.info(f"Different build detected - Running: {running_build_id}, Current: {current_build_id}")
                        
                        should_replace = show_build_conflict_dialog(self.current_build, running_build)
                        
                        if should_replace:
                            # Kill the old instance
                            try:
                                logger.info(f"Terminating old instance (PID: {old_pid})")
                                os.kill(old_pid, signal.SIGTERM)
                                
                                # Wait a moment for graceful shutdown
                                import time
                                time.sleep(1)
                                
                                # Force kill if still running
                                try:
                                    os.kill(old_pid, 0)
                                    logger.warning("Forcing termination of old instance")
                                    os.kill(old_pid, signal.SIGKILL)
                                    time.sleep(0.5)
                                except OSError:
                                    pass  # Process already terminated
                                
                                # Clean up old files
                                self.cleanup_old_files()
                                return False  # Allow new instance to start
                                
                            except OSError as e:
                                logger.error(f"Could not terminate old instance: {e}")
                                return True  # Fail to start if can't kill old
                        else:
                            # User chose to keep old instance
                            logger.info("User chose to keep running instance")
                            return True
                else:
                    # No build info for running instance, treat as same build and show dialog
                    logger.warning(f"Another instance is already running (PID: {old_pid}) - no build info")
                    should_replace = self.show_same_build_dialog(old_pid)
                    
                    if should_replace:
                        try:
                            logger.info(f"Terminating old instance (PID: {old_pid})")
                            os.kill(old_pid, signal.SIGTERM)
                            import time
                            time.sleep(1)
                            try:
                                os.kill(old_pid, 0)
                                os.kill(old_pid, signal.SIGKILL)
                                time.sleep(0.5)
                            except OSError:
                                pass
                            self.cleanup_old_files()
                            return False
                        except OSError as e:
                            logger.error(f"Could not terminate old instance: {e}")
                            return True
                    else:
                        return True
                    
            except OSError:
                # Process doesn't exist, remove stale files
                logger.info("Removing stale instance files")
                self.cleanup_old_files()
                return False
                
        except (ValueError, IOError) as e:
            logger.warning(f"Error reading PID file: {e}")
            # Remove corrupted files
            self.cleanup_old_files()
            return False
    
    def show_same_build_dialog(self, pid):
        """Show dialog when the same build is already running"""
        try:
            # Try to use macOS native dialog
            from AppKit import NSAlert, NSAlertFirstButtonReturn, NSApplication
            
            logger.info(f"Attempting to show same build dialog for PID {pid}")
            
            # Ensure NSApplication is initialized (required for modal dialogs)
            app = NSApplication.sharedApplication()
            logger.info("NSApplication initialized for dialog")
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Potter is Already Running")
            alert.setInformativeText_(
                f"Potter is already running (Process ID: {pid}).\n\n"
                f"Would you like to quit the running instance and start a new one?\n\n"
                f"Note: Any unsaved work in the running instance will be lost."
            )
            alert.addButtonWithTitle_("Quit Running & Start New")
            alert.addButtonWithTitle_("Keep Running Instance")
            
            logger.info("Alert configured, showing modal dialog...")
            
            # Show dialog
            response = alert.runModal()
            
            logger.info(f"Dialog response: {response} (NSAlertFirstButtonReturn: {NSAlertFirstButtonReturn})")
            
            # NSAlertFirstButtonReturn is the first button (Quit & Start New)
            result = response == NSAlertFirstButtonReturn
            logger.info(f"User choice: {'Replace' if result else 'Keep'} running instance")
            return result
            
        except ImportError:
            # If PyObjC not available, show a simple terminal fallback
            # This should rarely happen in a macOS GUI app, but just in case
            logger.warning("PyObjC not available, using simple fallback")
            print(f"\nPotter is already running (PID: {pid})")
            print("This application requires GUI interaction. Please quit the running instance manually.")
            return False
    
    def cleanup_old_files(self):
        """Clean up stale PID and build files"""
        for file_path in [self.pid_file, self.build_file]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def create_pid_file(self):
        """Create a PID file and build file for this instance"""
        try:
            # Create PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # Save build info
            self.save_build_info()
            
            self.is_running = True
            
            # Register cleanup function
            atexit.register(self.cleanup)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            logger.info(f"Created instance files - PID: {self.pid_file}, Build: {self.build_file}")
            logger.info(f"Build ID: {self.current_build.get('build_id', 'unknown')}")
            return True
            
        except IOError as e:
            logger.error(f"Failed to create instance files: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, cleaning up...")
        self.cleanup()
        import sys
        sys.exit(0)
    
    def cleanup(self):
        """Remove the PID and build files"""
        if self.is_running:
            self.cleanup_old_files()
            logger.info("Cleaned up instance files")
        self.is_running = False 