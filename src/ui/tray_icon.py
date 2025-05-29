#!/usr/bin/env python3
"""
Tray Icon UI Module
Handles system tray icon creation and menu management
"""

import sys
import logging
from typing import Callable, Dict, Optional
import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class TrayIconManager:
    """Manages system tray icon and menu"""
    
    def __init__(self, 
                 app_name: str = "Potter",
                 on_mode_change: Callable[[str], None] = None,
                 on_preferences: Callable[[], None] = None,
                 on_notifications_toggle: Callable[[], None] = None,
                 on_quit: Callable[[], None] = None):
        self.app_name = app_name
        self.tray_icon = None
        self.is_processing = False
        self.current_icon_image = None
        
        # Callbacks
        self.on_mode_change = on_mode_change
        self.on_preferences = on_preferences
        self.on_notifications_toggle = on_notifications_toggle
        self.on_quit = on_quit
    
    def create_normal_icon(self) -> Image.Image:
        """Create the normal icon"""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Simple background circle (subtle gray)
        draw.ellipse([4, 4, 60, 60], fill=(240, 240, 240, 220))
        
        # Main clipboard/copy icon (centered, black and white)
        clip_x, clip_y = 18, 12
        clip_w, clip_h = 28, 36
        
        # Clipboard body (white with black outline)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='black', width=2)
        
        # Clipboard top clip (black)
        clip_top_x = clip_x + 8
        clip_top_y = clip_y - 4
        clip_top_w = 12
        clip_top_h = 6
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='black')
        
        # Document lines (gray)
        line_x = clip_x + 4
        line_w = 20
        line_h = 2
        line_color = '#666666'
        
        draw.rectangle([line_x, clip_y + 8, line_x + line_w, clip_y + 8 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 14, line_x + line_w, clip_y + 14 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + 16, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 26, line_x + 18, clip_y + 26 + line_h], fill=line_color)
        
        # AI Sparkle at bottom right
        sparkle_x, sparkle_y = 44, 44
        sparkle_size = 8
        
        # Create the 4-pointed diamond star with blue gradient effect
        points = [
            (sparkle_x, sparkle_y - sparkle_size),  # Top
            (sparkle_x + sparkle_size, sparkle_y),   # Right
            (sparkle_x, sparkle_y + sparkle_size),   # Bottom
            (sparkle_x - sparkle_size, sparkle_y)    # Left
        ]
        
        # Draw the sparkle with gradient-like effect
        draw.polygon(points, fill='#4A90E2')  # Outer layer (darker blue)
        
        # Inner layer (lighter blue) - smaller diamond
        inner_size = sparkle_size - 2
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#7BB3F0')
        
        # Center highlight (very light blue/white)
        center_size = sparkle_size - 4
        center_points = [
            (sparkle_x, sparkle_y - center_size),
            (sparkle_x + center_size, sparkle_y),
            (sparkle_x, sparkle_y + center_size),
            (sparkle_x - center_size, sparkle_y)
        ]
        draw.polygon(center_points, fill='#B8D4F1')
        
        self.current_icon_image = image
        return image
    
    def create_spinner_icon(self) -> Image.Image:
        """Create a spinning/processing icon"""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Background circle (slightly more vibrant to show activity)
        draw.ellipse([4, 4, 60, 60], fill=(250, 250, 250, 240))
        
        # Main clipboard/copy icon (same as normal but with blue highlights)
        clip_x, clip_y = 18, 12
        clip_w, clip_h = 28, 36
        
        # Clipboard body (white with blue outline to show activity)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='#4A90E2', width=2)
        
        # Clipboard top clip (blue)
        clip_top_x = clip_x + 8
        clip_top_y = clip_y - 4
        clip_top_w = 12
        clip_top_h = 6
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='#4A90E2')
        
        # Document lines (blue to show processing)
        line_x = clip_x + 4
        line_w = 20
        line_h = 2
        line_color = '#4A90E2'
        
        draw.rectangle([line_x, clip_y + 8, line_x + line_w, clip_y + 8 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 14, line_x + line_w, clip_y + 14 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + 16, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 26, line_x + 18, clip_y + 26 + line_h], fill=line_color)
        
        # Animated sparkle (larger and more prominent)
        sparkle_x, sparkle_y = 44, 44
        sparkle_size = 10
        
        # Create the 4-pointed diamond star with bright processing colors
        points = [
            (sparkle_x, sparkle_y - sparkle_size),  # Top
            (sparkle_x + sparkle_size, sparkle_y),   # Right
            (sparkle_x, sparkle_y + sparkle_size),   # Bottom
            (sparkle_x - sparkle_size, sparkle_y)    # Left
        ]
        
        # Draw the sparkle with bright processing colors
        draw.polygon(points, fill='#FF6B35')  # Orange-red for activity
        
        # Inner layer 
        inner_size = sparkle_size - 2
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#FFB347')  # Light orange
        
        # Center highlight
        center_size = sparkle_size - 4
        center_points = [
            (sparkle_x, sparkle_y - center_size),
            (sparkle_x + center_size, sparkle_y),
            (sparkle_x, sparkle_y + center_size),
            (sparkle_x - center_size, sparkle_y)
        ]
        draw.polygon(center_points, fill='#FFF8DC')  # Almost white yellow
        
        self.current_icon_image = image
        return image

    def create_menu(self, current_mode: str, available_modes: list, permissions: Dict, 
                   notifications_enabled: bool) -> pystray.Menu:
        """Create the tray icon menu"""
        
        # Determine what entity has permission (Python vs Potter app)
        permission_entity = f"{self.app_name}.app" if getattr(sys, 'frozen', False) else "Python"
        
        # Create menu items
        menu_items = [
            pystray.MenuItem(f"Mode: {current_mode.title()}", lambda *args: None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]
        
        # Add permission status indicators
        if permissions.get("accessibility", False):
            accessibility_status = f"✅ {permission_entity} has access"
        else:
            accessibility_status = f"❌ {permission_entity} needs access"
        
        accessibility_item = pystray.MenuItem(f"Accessibility: {accessibility_status}", 
                                            self._handle_permissions_check)
        
        # Add notification toggle
        notifications_status = "✅" if notifications_enabled else "❌"
        notifications_item = pystray.MenuItem(f"Notifications: {notifications_status}", 
                                            self._handle_notifications_toggle)
        
        menu_items.extend([
            accessibility_item,
            notifications_item,
            pystray.Menu.SEPARATOR,
        ])
        
        # Add mode switching options
        for mode in available_modes:
            def make_mode_handler(mode_name):
                return lambda *args: self._handle_mode_change(mode_name)
            
            def make_mode_checker(mode_name):
                return lambda *args: current_mode == mode_name
            
            menu_items.append(
                pystray.MenuItem(
                    mode.title(), 
                    make_mode_handler(mode),
                    checked=make_mode_checker(mode)
                )
            )
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Preferences...", self._handle_preferences),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._handle_quit)
        ])
        
        return pystray.Menu(*menu_items)
    
    def create_tray_icon(self, current_mode: str, available_modes: list, 
                        permissions: Dict, notifications_enabled: bool):
        """Create the system tray icon"""
        image = self.create_normal_icon()
        menu = self.create_menu(current_mode, available_modes, permissions, notifications_enabled)
        
        self.tray_icon = pystray.Icon(self.app_name, image, f"{self.app_name} - AI Text Processor", menu)
        logger.info("✅ Tray icon created")
    
    def update_menu(self, current_mode: str, available_modes: list, 
                   permissions: Dict, notifications_enabled: bool):
        """Update the tray icon menu"""
        if self.tray_icon:
            new_menu = self.create_menu(current_mode, available_modes, permissions, notifications_enabled)
            self.tray_icon.menu = new_menu
            logger.debug("Tray icon menu updated")
    
    def set_processing_state(self, processing: bool):
        """Set processing state and update icon"""
        self.is_processing = processing
        if self.tray_icon:
            # Create the appropriate icon
            if processing:
                logger.debug("🔄 Setting spinner icon for processing state")
                icon_image = self.create_spinner_icon()
            else:
                logger.debug("✅ Setting normal icon for idle state")
                icon_image = self.create_normal_icon()
            
            # Update the tray icon
            try:
                self.tray_icon.icon = icon_image
                logger.debug(f"Icon updated successfully, processing={processing}")
            except Exception as e:
                logger.error(f"Failed to update tray icon: {e}")
        else:
            logger.warning("No tray icon available to update")
    
    def run(self):
        """Start the tray icon event loop (blocking)"""
        if self.tray_icon:
            try:
                self.tray_icon.run()
            except KeyboardInterrupt:
                logger.info("🛑 Tray icon interrupted")
            except Exception as e:
                logger.error(f"❌ Tray icon run failed: {e}")
        else:
            logger.error("No tray icon to run")
    
    def stop(self):
        """Stop the tray icon"""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
                logger.info("🛑 Tray icon stopped")
            except Exception as e:
                logger.error(f"Failed to stop tray icon: {e}")
    
    # Event handlers
    def _handle_mode_change(self, mode: str):
        """Handle mode change from menu"""
        if self.on_mode_change:
            self.on_mode_change(mode)
    
    def _handle_preferences(self, *args):
        """Handle preferences menu item"""
        if self.on_preferences:
            self.on_preferences()
    
    def _handle_notifications_toggle(self, *args):
        """Handle notifications toggle menu item"""
        if self.on_notifications_toggle:
            self.on_notifications_toggle()
    
    def _handle_permissions_check(self, *args):
        """Handle permissions check menu item"""
        if self.on_preferences:
            # Open preferences to show permission status
            self.on_preferences()
    
    def _handle_quit(self, *args):
        """Handle quit menu item"""
        if self.on_quit:
            self.on_quit() 