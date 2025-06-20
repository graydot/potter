#!/usr/bin/env python3
"""
App Icon Generator for Potter
Creates proper macOS app icons from the cauldron design
"""

try:
    from PIL import Image, ImageDraw
    import os
except ImportError:
    print("❌ PIL (Pillow) is required to generate app icons")
    print("   Install with: pip install Pillow")
    exit(1)

def draw_potter_app_icon(size):
    """Draw an orange Potter pot icon optimized for the given size"""
    
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale everything based on icon size
    scale = size / 512.0
    
    # Colors for the Potter pot
    pot_colors = {
        'orange': '#F97316',      # Primary orange
        'dark_orange': '#EA580C', # Darker orange for shadows
        'light_orange': '#FB923C', # Lighter orange for highlights
        'rim_orange': '#DC2626',   # Darker red-orange for rim
        'handle': '#78716C',       # Gray for handle
        'steam': '#F3F4F6'         # Light gray for steam
    }
    
    # Calculate dimensions
    center_x = size // 2
    center_y = int(size * 0.52)  # Slightly below center
    
    pot_width = int(size * 0.65)
    pot_height = int(size * 0.45)
    
    # Draw magical steam above pot
    if size >= 64:  # Only show steam on larger icons
        steam_particles = [
            (center_x - int(25 * scale), center_y - int(85 * scale), int(6 * scale)),
            (center_x + int(8 * scale), center_y - int(95 * scale), int(5 * scale)),
            (center_x + int(30 * scale), center_y - int(80 * scale), int(4 * scale)),
            (center_x - int(8 * scale), center_y - int(70 * scale), int(5 * scale)),
            (center_x + int(18 * scale), center_y - int(60 * scale), int(4 * scale)),
        ]
        
        for i, (sx, sy, sr) in enumerate(steam_particles):
            # Vary opacity for steam effect
            alpha = 200 - (i * 30)
            steam_color = (*[int(c) for c in bytes.fromhex(pot_colors['steam'][1:])], alpha)
            draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=steam_color)
    
    # Draw pot body (rounded bottom pot shape)
    pot_top = center_y - pot_height//2
    pot_bottom = center_y + pot_height//2
    
    # Main pot body with gradient effect
    gradient_steps = max(15, pot_height // 3)
    
    for i in range(gradient_steps):
        progress = i / gradient_steps
        
        # Create orange gradient from light to dark (top to bottom)
        if progress < 0.3:
            # Light orange at top
            color = pot_colors['light_orange']
        elif progress < 0.7:
            # Main orange in middle
            color = pot_colors['orange']
        else:
            # Dark orange at bottom for shadow
            color = pot_colors['dark_orange']
        
        # Calculate y position and width for this slice
        y_offset = int(progress * pot_height)
        y_pos = pot_top + y_offset
        
        # Make pot slightly wider in the middle, curved like a real pot
        width_factor = 0.85 + 0.15 * (1 - abs(progress - 0.5) * 2)
        slice_width = int(pot_width * width_factor)
        
        slice_height = max(1, pot_height // gradient_steps + 2)
        
        # Convert hex color to RGB
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        
        draw.ellipse([
            center_x - slice_width//2, y_pos,
            center_x + slice_width//2, y_pos + slice_height
        ], fill=rgb)
    
    # Draw pot rim (darker orange)
    rim_height = max(3, int(10 * scale))
    rim_color = tuple(int(pot_colors['rim_orange'][i:i+2], 16) for i in (1, 3, 5))
    draw.ellipse([
        center_x - pot_width//2 - int(6 * scale), 
        pot_top - rim_height//2,
        center_x + pot_width//2 + int(6 * scale), 
        pot_top + rim_height//2
    ], fill=rim_color)
    
    # Draw pot spout/pour lip
    if size >= 32:
        spout_width = int(12 * scale)
        spout_height = int(6 * scale)
        spout_x = center_x + pot_width//2 - int(5 * scale)
        spout_y = pot_top - int(2 * scale)
        
        draw.ellipse([
            spout_x, spout_y,
            spout_x + spout_width, spout_y + spout_height
        ], fill=rim_color)
    
    # Draw pot base/bottom
    base_width = int(pot_width * 0.8)
    base_height = max(2, int(6 * scale))
    base_color = tuple(int(pot_colors['dark_orange'][i:i+2], 16) for i in (1, 3, 5))
    draw.ellipse([
        center_x - base_width//2, 
        pot_bottom - base_height//2,
        center_x + base_width//2, 
        pot_bottom + base_height//2
    ], fill=base_color)
    
    # Draw handle (simple rectangular handle)
    if size >= 32:
        handle_color = tuple(int(pot_colors['handle'][i:i+2], 16) for i in (1, 3, 5))
        handle_thickness = max(2, int(4 * scale))
        handle_height = int(25 * scale)
        
        # Handle position (right side of pot)
        handle_x = center_x + pot_width//2 + int(2 * scale)
        handle_y = center_y - int(5 * scale)
        
        # Draw handle as a simple rectangle
        draw.rectangle([
            handle_x, handle_y - handle_height//2,
            handle_x + handle_thickness, handle_y + handle_height//2
        ], fill=handle_color)
    
    return img

def create_app_icon_set():
    """Create a complete set of app icons for macOS"""
    
    # macOS app icon sizes
    icon_sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    print("🎨 Creating Potter app icon set...")
    
    # Create Sources/Resources/AppIcon directory
    icon_dir = "Sources/Resources/AppIcon"
    os.makedirs(icon_dir, exist_ok=True)
    
    for size in icon_sizes:
        print(f"   Creating {size}x{size} icon...")
        
        icon = draw_potter_app_icon(size)
        
        # Save as PNG
        icon_path = f"{icon_dir}/potter-icon-{size}.png"
        icon.save(icon_path, 'PNG')
        
        # Also save @2x versions for retina
        if size <= 512:
            retina_icon = draw_potter_app_icon(size * 2)
            retina_path = f"{icon_dir}/potter-icon-{size}@2x.png"
            retina_icon.save(retina_path, 'PNG')
    
    print("✅ App icon set created!")
    print(f"   Icons saved in: {icon_dir}/")
    
    # Create a 128px version specifically for alerts
    alert_icon = draw_potter_app_icon(128)
    alert_path = f"{icon_dir}/potter-alert-icon.png"
    alert_icon.save(alert_path, 'PNG')
    print(f"✅ Alert icon saved: {alert_path}")

if __name__ == "__main__":
    create_app_icon_set()