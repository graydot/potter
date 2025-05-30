#!/usr/bin/env python3
"""
Common dialog utilities for Potter
Centralizes alert dialogs, restart functionality, and system interactions
"""

import os
import sys
import subprocess
import tempfile
from typing import Optional, Tuple
from Foundation import *
from AppKit import *


class DialogHelper:
    """Helper class for creating common dialog types"""
    
    @staticmethod
    def show_alert(title: str, message: str, style=None, buttons: list = None) -> int:
        """
        Show a standard alert dialog
        
        Args:
            title: Alert title
            message: Alert message
            style: Alert style (NSAlertStyleInformational, NSAlertStyleWarning, NSAlertStyleCritical)
            buttons: List of button titles (default: ["OK"])
            
        Returns:
            Button index pressed (0 = first button, 1 = second button, etc.)
        """
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        
        if style:
            alert.setAlertStyle_(style)
        else:
            alert.setAlertStyle_(NSAlertStyleInformational)
        
        if buttons:
            for button_title in buttons:
                alert.addButtonWithTitle_(button_title)
        else:
            alert.addButtonWithTitle_("OK")
        
        return alert.runModal()
    
    @staticmethod
    def show_confirmation(title: str, message: str, confirm_text: str = "Confirm", 
                         cancel_text: str = "Cancel") -> bool:
        """
        Show a confirmation dialog
        
        Returns:
            True if user confirmed, False if cancelled
        """
        result = DialogHelper.show_alert(
            title, message, 
            style=NSAlertStyleWarning,
            buttons=[confirm_text, cancel_text]
        )
        return result == NSAlertFirstButtonReturn
    
    @staticmethod
    def show_error(title: str, message: str):
        """Show an error dialog"""
        DialogHelper.show_alert(title, message, style=NSAlertStyleCritical)
    
    @staticmethod
    def show_info(title: str, message: str):
        """Show an info dialog"""
        DialogHelper.show_alert(title, message, style=NSAlertStyleInformational)


class RestartHelper:
    """Helper class for application restart functionality"""
    
    @staticmethod
    def restart_application() -> bool:
        """
        Restart the Potter application
        
        Returns:
            True if restart was initiated successfully, False otherwise
        """
        try:
            if getattr(sys, 'frozen', False):
                # Running as app bundle
                return RestartHelper._restart_app_bundle()
            else:
                # Running as script - show manual restart message
                return RestartHelper._show_manual_restart_message()
        except Exception as e:
            print(f"Debug - Error restarting app: {e}")
            return False
    
    @staticmethod
    def _restart_app_bundle() -> bool:
        """Restart app bundle mode"""
        try:
            app_path = sys.executable
            # Find the .app bundle root
            while app_path and not app_path.endswith('.app'):
                app_path = os.path.dirname(app_path)
            
            if not app_path or not app_path.endswith('.app'):
                DialogHelper.show_error(
                    "Restart Failed",
                    "Could not find app bundle path for restart."
                )
                return False
            
            # Create a restart script that waits for the current process to exit
            current_pid = os.getpid()
            restart_script = f'''#!/bin/bash
# Wait for current process to exit
while kill -0 {current_pid} 2>/dev/null; do
    sleep 0.1
done
# Small additional delay to ensure clean exit
sleep 0.5
# Restart the app
open "{app_path}"
# Clean up this script
rm "$0"
'''
            
            # Write the script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(restart_script)
                script_path = f.name
            
            # Make the script executable
            os.chmod(script_path, 0o755)
            
            # Launch the restart script in background
            subprocess.Popen(['/bin/bash', script_path], 
                           start_new_session=True,
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            print(f"Debug - Restart script launched: {script_path}")
            
            # Schedule a clean exit without NSApplication calls
            # This avoids the main thread safety issues that cause OS freezes
            import threading
            import time
            
            def delayed_exit():
                time.sleep(0.3)  # Give restart script time to start monitoring
                # Use sys.exit which is safer than NSApplication.terminate
                sys.exit(0)
            
            # Start exit in a separate thread - but use sys.exit not NSApplication
            threading.Thread(target=delayed_exit, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"Debug - Error in app bundle restart: {e}")
            return False
    
    @staticmethod
    def _show_manual_restart_message() -> bool:
        """Show manual restart message for development mode"""
        DialogHelper.show_info(
            "Manual Restart Required",
            "Please manually restart Potter for the changes to take effect."
        )
        return True


class SystemHelper:
    """Helper class for system interactions and AppleScript execution"""
    
    @staticmethod
    def run_applescript(script: str, timeout: int = 10) -> Tuple[bool, str, str]:
        """
        Run AppleScript and return results
        
        Args:
            script: AppleScript code to execute
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run([
                'osascript', '-e', script
            ], capture_output=True, text=True, timeout=timeout)
            
            return (
                result.returncode == 0,
                result.stdout.strip(),
                result.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return False, "", "Script timed out"
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def check_login_items() -> Tuple[bool, list]:
        """
        Check current login items
        
        Returns:
            Tuple of (success, list_of_login_items)
        """
        success, stdout, stderr = SystemHelper.run_applescript(
            'tell application "System Events" to get the name of every login item'
        )
        
        if success:
            # Parse the comma-separated list
            items = [item.strip() for item in stdout.split(',') if item.strip()]
            return True, items
        else:
            return False, []
    
    @staticmethod
    def add_login_item(app_path: str = "/Applications/Potter.app") -> bool:
        """Add Potter to login items"""
        success, stdout, stderr = SystemHelper.run_applescript(
            f'tell application "System Events" to make login item at end with properties {{path:"{app_path}", hidden:false}}'
        )
        
        if success:
            print("Debug - Successfully added to login items")
        else:
            print(f"Debug - Failed to add to login items: {stderr}")
        
        return success
    
    @staticmethod
    def remove_login_item(app_name: str = "Potter") -> bool:
        """Remove Potter from login items"""
        # Try primary removal method
        success, stdout, stderr = SystemHelper.run_applescript(
            f'tell application "System Events" to delete login item "{app_name}"'
        )
        
        if success:
            print("Debug - Successfully removed from login items")
            return True
        
        # Try alternative removal method
        print(f"Debug - First removal attempt failed: {stderr}")
        success, stdout, stderr = SystemHelper.run_applescript(
            f'tell application "System Events" to delete every login item whose name is "{app_name}"'
        )
        
        if success:
            print("Debug - Successfully removed from login items (alternative method)")
        else:
            print(f"Debug - All removal attempts failed: {stderr}")
        
        return success
    
    @staticmethod
    def check_system_events_permission() -> bool:
        """Check if we have System Events permission"""
        success, stdout, stderr = SystemHelper.run_applescript(
            'tell application "System Events" to get name of first process'
        )
        
        if success:
            print("Debug - System Events permission: granted")
        else:
            print(f"Debug - System Events permission denied: {stderr}")
        
        return success


# Convenience functions for backward compatibility
def show_alert(title: str, message: str, style=None, buttons: list = None) -> int:
    """Convenience function for showing alerts"""
    return DialogHelper.show_alert(title, message, style, buttons)

def show_confirmation(title: str, message: str, confirm_text: str = "Confirm", 
                     cancel_text: str = "Cancel") -> bool:
    """Convenience function for showing confirmations"""
    return DialogHelper.show_confirmation(title, message, confirm_text, cancel_text)

def restart_app() -> bool:
    """Convenience function for restarting the app"""
    return RestartHelper.restart_application()

def run_applescript(script: str, timeout: int = 10) -> Tuple[bool, str, str]:
    """Convenience function for running AppleScript"""
    return SystemHelper.run_applescript(script, timeout) 