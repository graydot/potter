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

def draw_cauldron_app_icon(size):
    """Draw a cauldron icon optimized for the given size"""
    
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale everything based on icon size
    scale = size / 512.0
    
    # Colors for the cauldron
    cauldron_colors = {
        'purple': '#8B5CF6',
        'pink': '#EC4899', 
        'orange': '#F97316',
        'gold': '#FBBF24',
        'dark_orange': '#D97706'
    }
    
    # Calculate dimensions
    center_x = size // 2
    center_y = int(size * 0.55)  # Slightly below center
    
    cauldron_width = int(size * 0.6)
    cauldron_height = int(size * 0.4)
    
    # Draw magical particles above cauldron
    if size >= 64:  # Only show particles on larger icons
        particles = [
            (center_x - int(30 * scale), center_y - int(80 * scale), int(8 * scale)),
            (center_x + int(10 * scale), center_y - int(90 * scale), int(6 * scale)),
            (center_x + int(35 * scale), center_y - int(75 * scale), int(5 * scale)),
            (center_x - int(10 * scale), center_y - int(65 * scale), int(6 * scale)),
            (center_x + int(20 * scale), center_y - int(55 * scale), int(4 * scale)),
        ]
        
        particle_colors = [cauldron_colors['orange'], cauldron_colors['pink'], 
                          cauldron_colors['purple'], cauldron_colors['pink'], 
                          cauldron_colors['orange']]
        
        for i, (px, py, pr) in enumerate(particles):
            color = particle_colors[i % len(particle_colors)]
            draw.ellipse([px-pr, py-pr, px+pr, py+pr], fill=color)
    
    # Draw cauldron body with gradient effect
    gradient_steps = max(20, cauldron_height // 4)
    
    for i in range(gradient_steps):
        progress = i / gradient_steps
        
        # Create three-color gradient: purple -> pink -> orange
        if progress < 0.5:
            # Purple to pink
            t = progress * 2
            r = int(139 + (236 - 139) * t)
            g = int(92 + (72 - 92) * t) 
            b = int(246 + (153 - 246) * t)
        else:
            # Pink to orange
            t = (progress - 0.5) * 2
            r = int(236 + (249 - 236) * t)
            g = int(72 + (115 - 72) * t)
            b = int(153 + (22 - 153) * t)
        
        color = (r, g, b)
        
        # Calculate y position and width for this slice
        y_offset = int(progress * cauldron_height)
        y_pos = center_y - cauldron_height//2 + y_offset
        
        # Make cauldron wider at the middle, narrower at top/bottom
        width_factor = 0.6 + 0.4 * (1 - abs(progress - 0.5) * 2)
        slice_width = int(cauldron_width * width_factor)
        
        slice_height = max(1, cauldron_height // gradient_steps + 1)
        
        draw.ellipse([
            center_x - slice_width//2, y_pos,
            center_x + slice_width//2, y_pos + slice_height
        ], fill=color)
    
    # Draw golden rim
    rim_height = max(2, int(8 * scale))
    draw.ellipse([
        center_x - cauldron_width//2 - int(4 * scale), 
        center_y - cauldron_height//2 - rim_height//2,
        center_x + cauldron_width//2 + int(4 * scale), 
        center_y - cauldron_height//2 + rim_height//2
    ], fill=cauldron_colors['gold'])
    
    # Draw cauldron legs
    leg_size = max(2, int(6 * scale))
    leg_y = center_y + cauldron_height//2 + int(8 * scale)
    leg_spacing = cauldron_width // 3
    
    for leg_offset in [-leg_spacing, 0, leg_spacing]:
        leg_x = center_x + leg_offset
        draw.ellipse([
            leg_x - leg_size, leg_y - leg_size//2,
            leg_x + leg_size, leg_y + leg_size//2
        ], fill=cauldron_colors['dark_orange'])
    
    # Draw handle (white rectangle)
    if size >= 32:  # Only show handle on larger icons
        handle_width = max(1, int(3 * scale))
        handle_height = max(4, int(16 * scale))
        draw.rectangle([
            center_x - handle_width//2, center_y - handle_height//2,
            center_x + handle_width//2, center_y + handle_height//2
        ], fill='white')
    
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
        
        icon = draw_cauldron_app_icon(size)
        
        # Save as PNG
        icon_path = f"{icon_dir}/potter-icon-{size}.png"
        icon.save(icon_path, 'PNG')
        
        # Also save @2x versions for retina
        if size <= 512:
            retina_icon = draw_cauldron_app_icon(size * 2)
            retina_path = f"{icon_dir}/potter-icon-{size}@2x.png"
            retina_icon.save(retina_path, 'PNG')
    
    print("✅ App icon set created!")
    print(f"   Icons saved in: {icon_dir}/")
    
    # Create a 128px version specifically for alerts
    alert_icon = draw_cauldron_app_icon(128)
    alert_path = f"{icon_dir}/potter-alert-icon.png"
    alert_icon.save(alert_path, 'PNG')
    print(f"✅ Alert icon saved: {alert_path}")

if __name__ == "__main__":
    create_app_icon_set()