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
                 on_process_click: Callable[[], None] = None,
                 on_quit: Callable[[], None] = None):
        self.app_name = app_name
        self.tray_icon = None
        self.is_processing = False
        self.has_error = False
        self.last_error_message = None
        self.current_icon_image = None
        
        # Callbacks
        self.on_mode_change = on_mode_change
        self.on_preferences = on_preferences
        self.on_notifications_toggle = on_notifications_toggle
        self.on_process_click = on_process_click
        self.on_quit = on_quit
    
    def create_normal_icon(self) -> Image.Image:
        """Create the normal icon with clipboard and magic wand"""
        # Make icon bigger for better visibility
        image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Simple background circle (subtle gray, larger)
        draw.ellipse([8, 8, 120, 120], fill=(240, 240, 240, 220))
        
        # Main clipboard/copy icon (left side, larger)
        clip_x, clip_y = 20, 24
        clip_w, clip_h = 40, 48
        
        # Clipboard body (white with black outline)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='black', width=3)
        
        # Clipboard top clip (black)
        clip_top_x = clip_x + 12
        clip_top_y = clip_y - 6
        clip_top_w = 16
        clip_top_h = 8
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='black')
        
        # Document lines (gray, larger)
        line_x = clip_x + 6
        line_w = 28
        line_h = 3
        line_color = '#666666'
        
        draw.rectangle([line_x, clip_y + 12, line_x + line_w, clip_y + 12 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + line_w, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 28, line_x + 22, clip_y + 28 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 36, line_x + 24, clip_y + 36 + line_h], fill=line_color)
        
        # Magic wand (right side) - indicating LLM processing capability
        wand_start_x, wand_start_y = 75, 75
        wand_end_x, wand_end_y = 95, 55
        wand_width = 4
        
        # Wand shaft (brown/wooden color)
        draw.line([(wand_start_x, wand_start_y), (wand_end_x, wand_end_y)], 
                 fill='#8B4513', width=wand_width)
        
        # Wand tip (metallic silver)
        tip_x, tip_y = wand_end_x, wand_end_y
        draw.ellipse([tip_x-3, tip_y-3, tip_x+3, tip_y+3], fill='#C0C0C0')
        
        # Magic sparkles around wand tip
        sparkle_positions = [
            (wand_end_x + 8, wand_end_y - 2),
            (wand_end_x + 3, wand_end_y - 8),
            (wand_end_x - 3, wand_end_y + 3),
            (wand_end_x + 12, wand_end_y + 5)
        ]
        
        for sparkle_x, sparkle_y in sparkle_positions:
            # 4-pointed star sparkle
            sparkle_size = 4
            points = [
                (sparkle_x, sparkle_y - sparkle_size),  # Top
                (sparkle_x + sparkle_size//2, sparkle_y),   # Right  
                (sparkle_x, sparkle_y + sparkle_size),   # Bottom
                (sparkle_x - sparkle_size//2, sparkle_y)    # Left
            ]
            draw.polygon(points, fill='#FFD700')  # Gold color for magic
        
        # AI Sparkle at bottom right (larger)
        sparkle_x, sparkle_y = 88, 88
        sparkle_size = 12
        
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
        inner_size = sparkle_size - 3
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#7BB3F0')
        
        # Center highlight (very light blue/white)
        center_size = sparkle_size - 6
        center_points = [
            (sparkle_x, sparkle_y - center_size),
            (sparkle_x + center_size, sparkle_y),
            (sparkle_x, sparkle_y + center_size),
            (sparkle_x - center_size, sparkle_y)
        ]
        draw.polygon(center_points, fill='#B8D4F1')
        
        self.current_icon_image = image
        return image
    
    def create_error_icon(self) -> Image.Image:
        """Create an error icon with red exclamation mark"""
        # Make icon bigger for better visibility
        image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Red background circle to indicate error
        draw.ellipse([8, 8, 120, 120], fill=(255, 100, 100, 220))  # Red background
        
        # Main clipboard/copy icon (same as normal but with red tinting)
        clip_x, clip_y = 20, 24
        clip_w, clip_h = 40, 48
        
        # Clipboard body (white with red outline to show error)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='#DC143C', width=3)  # Dark red outline
        
        # Clipboard top clip (red)
        clip_top_x = clip_x + 12
        clip_top_y = clip_y - 6
        clip_top_w = 16
        clip_top_h = 8
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='#DC143C')
        
        # Document lines (red to show error)
        line_x = clip_x + 6
        line_w = 28
        line_h = 3
        line_color = '#DC143C'
        
        draw.rectangle([line_x, clip_y + 12, line_x + line_w, clip_y + 12 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + line_w, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 28, line_x + 22, clip_y + 28 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 36, line_x + 24, clip_y + 36 + line_h], fill=line_color)
        
        # Large red exclamation mark on the right side
        excl_x, excl_y = 85, 35
        excl_width = 8
        excl_height = 35
        
        # Exclamation mark body (thick red line)
        draw.rectangle([excl_x, excl_y, excl_x + excl_width, excl_y + excl_height - 12], 
                      fill='white')
        
        # Exclamation mark dot
        dot_y = excl_y + excl_height - 8
        draw.rectangle([excl_x, dot_y, excl_x + excl_width, dot_y + 8], 
                      fill='white')
        
        # Add white border to exclamation mark for visibility
        draw.rectangle([excl_x-1, excl_y-1, excl_x + excl_width+1, excl_y + excl_height - 12+1], 
                      outline='white', width=1)
        draw.rectangle([excl_x-1, dot_y-1, excl_x + excl_width+1, dot_y + 8+1], 
                      outline='white', width=1)
        
        self.current_icon_image = image
        return image
    
    def create_spinner_icon(self) -> Image.Image:
        """Create a spinning/processing icon"""
        # Make icon bigger to match normal icon
        image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Background circle (slightly more vibrant to show activity, larger)
        draw.ellipse([8, 8, 120, 120], fill=(250, 250, 250, 240))
        
        # Main clipboard/copy icon (same as normal but with blue highlights, larger)
        clip_x, clip_y = 20, 24
        clip_w, clip_h = 40, 48
        
        # Clipboard body (white with blue outline to show activity)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='#4A90E2', width=3)
        
        # Clipboard top clip (blue)
        clip_top_x = clip_x + 12
        clip_top_y = clip_y - 6
        clip_top_w = 16
        clip_top_h = 8
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='#4A90E2')
        
        # Document lines (blue to show processing, larger)
        line_x = clip_x + 6
        line_w = 28
        line_h = 3
        line_color = '#4A90E2'
        
        draw.rectangle([line_x, clip_y + 12, line_x + line_w, clip_y + 12 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + line_w, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 28, line_x + 22, clip_y + 28 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 36, line_x + 24, clip_y + 36 + line_h], fill=line_color)
        
        # Magic wand (right side) - more animated during processing
        wand_start_x, wand_start_y = 75, 75
        wand_end_x, wand_end_y = 95, 55
        wand_width = 4
        
        # Wand shaft (glowing brown during processing)
        draw.line([(wand_start_x, wand_start_y), (wand_end_x, wand_end_y)], 
                 fill='#D2691E', width=wand_width)  # Lighter brown for glow effect
        
        # Wand tip (bright silver with glow)
        tip_x, tip_y = wand_end_x, wand_end_y
        draw.ellipse([tip_x-4, tip_y-4, tip_x+4, tip_y+4], fill='#E0E0E0')  # Larger glowing tip
        
        # More prominent magic sparkles during processing
        sparkle_positions = [
            (wand_end_x + 10, wand_end_y - 3),
            (wand_end_x + 5, wand_end_y - 10),
            (wand_end_x - 5, wand_end_y + 5),
            (wand_end_x + 15, wand_end_y + 8),
            (wand_end_x + 2, wand_end_y + 2)  # Extra sparkle during processing
        ]
        
        for sparkle_x, sparkle_y in sparkle_positions:
            # 4-pointed star sparkle (bigger during processing)
            sparkle_size = 5
            points = [
                (sparkle_x, sparkle_y - sparkle_size),  # Top
                (sparkle_x + sparkle_size//2, sparkle_y),   # Right  
                (sparkle_x, sparkle_y + sparkle_size),   # Bottom
                (sparkle_x - sparkle_size//2, sparkle_y)    # Left
            ]
            draw.polygon(points, fill='#FFD700')  # Gold color for magic
        
        # Animated sparkle (larger and more prominent)
        sparkle_x, sparkle_y = 88, 88
        sparkle_size = 15
        
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
        inner_size = sparkle_size - 4
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#FFB347')  # Light orange
        
        # Center highlight
        center_size = sparkle_size - 8
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
        menu_items = []
        
        # Add error message at top if there's an error
        if self.has_error and self.last_error_message:
            error_text = f"❌ Error: {self.last_error_message[:50]}.." if len(self.last_error_message) > 50 else f"❌ Error: {self.last_error_message}"
            menu_items.extend([
                pystray.MenuItem(error_text, lambda *args: None, enabled=False),
                pystray.MenuItem("Clear Error", lambda *args: self.set_error_state(False)),
                pystray.Menu.SEPARATOR,
            ])
        
        menu_items.extend([
            pystray.MenuItem(f"Mode: {current_mode.title()}", lambda *args: None, enabled=False),
            pystray.Menu.SEPARATOR,
        ])
        
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
        
        # Create menu with custom handling for left click
        def create_custom_menu():
            # Create a function that handles different mouse buttons
            def handle_click(icon, item):
                # This gets called on left click - trigger processing
                logger.info("🖱️ Menu item click detected - triggering LLM processing")
                logger.info("🖱️ Icon: %s, Item: %s", icon, item)
                self._handle_process_click()
            
            # Create the menu for right-click
            regular_menu_items = []
            
            # Add error message at top if there's an error
            if self.has_error and self.last_error_message:
                error_text = f"❌ Error: {self.last_error_message[:50]}.." if len(self.last_error_message) > 50 else f"❌ Error: {self.last_error_message}"
                regular_menu_items.extend([
                    pystray.MenuItem(error_text, lambda *args: None, enabled=False),
                    pystray.MenuItem("Clear Error", lambda *args: self.set_error_state(False)),
                    pystray.Menu.SEPARATOR,
                ])
            
            # Get current state for menu
            current_mode = self.text_processor.get_current_mode() if hasattr(self, 'text_processor') else "default"
            available_modes = ["default", "creative", "professional"] if hasattr(self, 'text_processor') else []
            permissions = {"accessibility": True} if hasattr(self, 'permission_manager') else {}
            notifications_enabled = True if hasattr(self, 'notification_manager') else True
            
            # Add regular menu items
            permission_entity = f"{self.app_name}.app" if getattr(sys, 'frozen', False) else "Python"
            
            regular_menu_items.extend([
                pystray.MenuItem("🖱️ Left-click to process text", handle_click, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(f"Mode: {current_mode.title()}", lambda *args: None, enabled=False),
                pystray.Menu.SEPARATOR,
            ])
            
            # Add permission status
            if permissions.get("accessibility", False):
                accessibility_status = f"✅ {permission_entity} has access"
            else:
                accessibility_status = f"❌ {permission_entity} needs access"
            
            accessibility_item = pystray.MenuItem(f"Accessibility: {accessibility_status}", 
                                                self._handle_permissions_check)
            
            notifications_status = "✅" if notifications_enabled else "❌"
            notifications_item = pystray.MenuItem(f"Notifications: {notifications_status}", 
                                                self._handle_notifications_toggle)
            
            regular_menu_items.extend([
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
                
                regular_menu_items.append(
                    pystray.MenuItem(
                        mode.title(), 
                        make_mode_handler(mode),
                        checked=make_mode_checker(mode)
                    )
                )
            
            regular_menu_items.extend([
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Preferences...", self._handle_preferences),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._handle_quit)
            ])
            
            return pystray.Menu(*regular_menu_items)
        
        menu = create_custom_menu()
        
        # Use a simple menu approach where the first item triggers processing
        # This is the most reliable way to handle left clicks in pystray
        process_menu_item = pystray.MenuItem(
            "Process Clipboard Text", 
            self._handle_process_click, 
            default=True  # This makes it the default action for left-click
        )
        
        # Create a new menu with process item first
        new_menu_items = [process_menu_item, pystray.Menu.SEPARATOR]
        
        # Add all the existing menu items
        for item in menu:
            new_menu_items.append(item)
        
        final_menu = pystray.Menu(*new_menu_items)
        
        # Create icon with the menu that has processing as default
        logger.info("🔧 Creating tray icon with processing as default menu action")
        self.tray_icon = pystray.Icon(
            self.app_name, 
            image, 
            f"{self.app_name} - AI Text Processor (Left-click to process, Right-click for menu)",
            final_menu
        )
        logger.info("✅ Tray icon created with processing menu item as default")
    
    def update_menu(self, current_mode: str, available_modes: list, 
                   permissions: Dict, notifications_enabled: bool):
        """Update the tray icon menu"""
        if self.tray_icon:
            new_menu = self.create_menu(current_mode, available_modes, permissions, notifications_enabled)
            self.tray_icon.menu = new_menu
            logger.debug("Tray icon menu updated")
    
    def clear_error(self):
        """Clear the error state"""
        self.set_error_state(False)
    
    def set_processing_state(self, processing: bool):
        """Set processing state and update icon"""
        self.is_processing = processing
        self.update_icon()
    
    def set_error_state(self, has_error: bool, error_message: str = None):
        """Set error state and update icon"""
        self.has_error = has_error
        if has_error and error_message:
            self.last_error_message = error_message
            logger.error(f"🚨 Tray icon entering error state: {error_message}")
        elif not has_error:
            self.last_error_message = None
            logger.info("✅ Tray icon clearing error state")
        self.update_icon()
    
    def update_icon(self):
        """Update the tray icon based on current state"""
        if self.tray_icon:
            # Create the appropriate icon based on state priority: error > processing > normal
            if self.has_error:
                logger.debug("🚨 Setting error icon for error state")
                icon_image = self.create_error_icon()
            elif self.is_processing:
                logger.debug("🔄 Setting spinner icon for processing state")
                icon_image = self.create_spinner_icon()
            else:
                logger.debug("✅ Setting normal icon for idle state")
                icon_image = self.create_normal_icon()
            
            # Update the tray icon
            try:
                self.tray_icon.icon = icon_image
                logger.debug(f"Icon updated successfully, error={self.has_error}, processing={self.is_processing}")
            except Exception as e:
                logger.error(f"Failed to update tray icon: {e}")
        else:
            logger.warning("No tray icon available to update")
    
    def run(self):
        """Start the tray icon event loop (blocking)"""
        logger.info("🚀 Starting tray icon run method...")
        if self.tray_icon:
            logger.info("🎯 Tray icon exists, starting event loop...")
            logger.info("🔧 Tray icon default_action: %s", getattr(self.tray_icon, 'default_action', 'NOT SET'))
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
    def _handle_process_click(self, *args):
        """Handle left-click on tray icon to trigger LLM processing"""
        logger.info("🖱️ Tray icon _handle_process_click called with args: %s", args)
        logger.info("🖱️ on_process_click callback: %s", self.on_process_click)
        if self.on_process_click:
            logger.info("🖱️ Calling on_process_click callback...")
            try:
                self.on_process_click()
                logger.info("🖱️ on_process_click callback completed successfully")
            except Exception as e:
                logger.error("🖱️ Error in on_process_click callback: %s", e)
        else:
            logger.warning("No process click handler configured")
    
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