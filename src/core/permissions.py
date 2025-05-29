#!/usr/bin/env python3
"""
Permission Management Module
Handles macOS accessibility permissions and system integration
"""

import subprocess
import logging

logger = logging.getLogger(__name__)

# macOS permission checking
try:
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
    from ApplicationServices import AXIsProcessTrusted
    MACOS_PERMISSIONS_AVAILABLE = True
except ImportError:
    MACOS_PERMISSIONS_AVAILABLE = False
    logger.warning("macOS permission checking not available")


class PermissionManager:
    """Manages macOS accessibility permissions and system integration"""
    
    def __init__(self):
        self.macos_available = MACOS_PERMISSIONS_AVAILABLE
    
    def check_accessibility_permissions(self):
        """Check if the app has accessibility permissions"""
        if not self.macos_available:
            logger.warning("macOS permissions checking not available")
            return False
        
        try:
            # Use the proper accessibility API to check permissions
            is_trusted = AXIsProcessTrusted()
            logger.debug(f"AXIsProcessTrusted() returned: {is_trusted}")
            
            # Force a more aggressive check - try to actually use accessibility features
            if is_trusted:
                try:
                    # Additional verification - try to access window list which requires accessibility permission
                    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                    if window_list and len(window_list) > 0:
                        # Extra verification: try to access detailed window information
                        try:
                            # Try to access window owner information - this typically requires accessibility permission
                            for window in window_list[:3]:  # Check first 3 windows
                                owner_name = window.get('kCGWindowOwnerName', '')
                                window_name = window.get('kCGWindowName', '')
                                if owner_name or window_name:
                                    logger.debug(f"Window access verified: owner={owner_name}, name={window_name}")
                                    break
                            else:
                                logger.warning("Could not access window details despite window list being available")
                                return False
                            
                            logger.debug(f"Window list verification successful: {len(window_list)} windows")
                            return True
                        except Exception as e:
                            logger.warning(f"Failed to access window details: {e}")
                            return False
                    else:
                        logger.warning("AXIsProcessTrusted=True but window list is empty - permission might not be fully granted yet")
                        return False
                except Exception as e:
                    logger.warning(f"Window list verification failed despite AXIsProcessTrusted=True: {e}")
                    return False
            else:
                logger.debug("AXIsProcessTrusted() returned False - no accessibility permission")
                return False
                
        except ImportError as e:
            logger.warning(f"ApplicationServices not available: {e}")
            # Fallback method - try to get window list directly (but be more strict)
            try:
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                if window_list and len(window_list) > 5:  # Require more windows to reduce false positives
                    # Try to access window details to verify real accessibility
                    accessible_windows = 0
                    for window in window_list[:5]:
                        owner_name = window.get('kCGWindowOwnerName', '')
                        if owner_name:
                            accessible_windows += 1
                    
                    has_permission = accessible_windows >= 2  # Require at least 2 accessible windows
                    logger.debug(f"Fallback window list check: {has_permission} (accessible windows: {accessible_windows})")
                    return has_permission
                else:
                    logger.debug("Fallback window list check: insufficient windows")
                    return False
            except Exception as e2:
                logger.warning(f"Fallback window list check failed: {e2}")
                return False
        except Exception as e:
            logger.warning(f"Accessibility permission check failed: {e}")
            return False
    
    def get_permission_status(self):
        """Get current permission status"""
        return {
            "accessibility": self.check_accessibility_permissions(),
            "macos_available": self.macos_available
        }
    
    def open_system_preferences_security(self):
        """Open System Preferences to Security & Privacy"""
        try:
            # For macOS 13+ (Ventura and later), it's System Settings
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
        except Exception as e:
            logger.error(f"Failed to open System Preferences: {e}")
            # Fallback to general System Preferences
            try:
                subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            except Exception as e2:
                logger.error(f"Failed to open System Preferences fallback: {e2}")
    
    def request_permissions(self, show_preferences_callback=None):
        """Request necessary permissions from the user"""
        logger.info("Checking permissions...")
        
        permissions = self.get_permission_status()
        
        if not permissions["accessibility"]:
            logger.warning("Accessibility permission not granted")
            logger.info("Opening settings to show permission status and grant access...")
            
            # Show settings if callback provided
            if show_preferences_callback:
                show_preferences_callback()
                return True
            else:
                print("⚠️  Accessibility permission required!")
                print("   Needed for: global hotkey monitoring only")
                print("   Potter will process text already in your clipboard")
                print("   Please grant permission in System Settings > Privacy & Security > Accessibility")
                print("   The app will continue running and check for permissions periodically")
                return True
        
        return True 