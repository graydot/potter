#!/usr/bin/env python3
"""
Menu Bar Icon Generator for Potter
Creates menu bar icons that match the app icon design
"""

try:
    from PIL import Image, ImageDraw
    import os
except ImportError:
    print("❌ PIL (Pillow) is required to generate menu bar icons")
    print("   Install with: pip install Pillow")
    exit(1)

def draw_pot_menubar_icon(size, for_dark_mode=False):
    """Draw a Potter pot icon optimized for menu bar"""
    
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors based on theme
    if for_dark_mode:
        # White pot for dark mode menu bar
        pot_color = '#ffffff'
        rim_color = '#f5f5f5'
        base_color = '#e5e5e5'
        handle_color = '#b5b5b5'
        steam_color = '#cccccc'
    else:
        # Black pot for light mode menu bar  
        pot_color = '#1a1a1a'
        rim_color = '#000000'
        base_color = '#0d0d0d'
        handle_color = '#4a4a4a'
        steam_color = '#666666'
    
    # Calculate dimensions for menu bar size
    scale = size / 18.0  # Scale to menu bar size
    center_x = size // 2
    center_y = int(size * 0.52)
    
    pot_width = int(size * 0.6)
    pot_height = int(size * 0.35)
    
    # Draw steam particles (simplified for small size)
    if size >= 16:
        steam_particles = [
            (center_x - int(3 * scale), center_y - int(8 * scale), max(1, int(1 * scale))),
            (center_x + int(1 * scale), center_y - int(9 * scale), max(1, int(1 * scale))),
            (center_x + int(4 * scale), center_y - int(7 * scale), max(1, int(1 * scale))),
        ]
        
        for sx, sy, sr in steam_particles:
            draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=steam_color)
    
    # Draw main pot body
    pot_body = [
        center_x - pot_width//2, center_y - pot_height//2,
        center_x + pot_width//2, center_y + pot_height//2
    ]
    draw.ellipse(pot_body, fill=pot_color)
    
    # Draw pot rim
    rim_height = max(2, int(2 * scale))
    rim = [
        center_x - pot_width//2 - int(1 * scale), center_y - pot_height//2 - rim_height//2,
        center_x + pot_width//2 + int(1 * scale), center_y - pot_height//2 + rim_height//2
    ]
    draw.ellipse(rim, fill=rim_color)
    
    # Draw pot spout
    if size >= 14:
        spout_width = max(2, int(2.5 * scale))
        spout_height = max(1, int(1.2 * scale))
        spout = [
            center_x + pot_width//2 - int(1 * scale), center_y - pot_height//2,
            center_x + pot_width//2 - int(1 * scale) + spout_width, center_y - pot_height//2 + spout_height
        ]
        draw.ellipse(spout, fill=rim_color)
    
    # Draw pot base
    base_width = int(pot_width * 0.8)
    base_height = max(1, int(1.5 * scale))
    base = [
        center_x - base_width//2, center_y + pot_height//2 - base_height//2,
        center_x + base_width//2, center_y + pot_height//2 + base_height//2
    ]
    draw.ellipse(base, fill=base_color)
    
    # Draw handle (simple rectangle)
    if size >= 14:
        handle_thickness = max(1, int(1 * scale))
        handle_height = max(3, int(4 * scale))
        handle = [
            center_x + pot_width//2 + int(1 * scale), center_y - handle_height//2,
            center_x + pot_width//2 + int(1 * scale) + handle_thickness, center_y + handle_height//2
        ]
        draw.rectangle(handle, fill=handle_color)
    
    return img

def create_menubar_icons():
    """Create menu bar icons for Potter"""
    
    print("🎨 Creating Potter menu bar icons...")
    
    # Menu bar icon sizes (18x18 is standard for macOS menu bar)
    sizes = [16, 18, 32]  # 16 for small displays, 18 standard, 32 for retina
    
    # Create Sources/Resources directory
    icon_dir = "Sources/Resources"
    os.makedirs(icon_dir, exist_ok=True)
    
    for size in sizes:
        print(f"   Creating {size}x{size} menu bar icons...")
        
        # Light mode icon (black pot)
        light_icon = draw_pot_menubar_icon(size, for_dark_mode=False)
        light_path = f"{icon_dir}/menubar-icon-light-{size}.png"
        light_icon.save(light_path, 'PNG')
        
        # Dark mode icon (white pot)
        dark_icon = draw_pot_menubar_icon(size, for_dark_mode=True)
        dark_path = f"{icon_dir}/menubar-icon-dark-{size}.png"
        dark_icon.save(dark_path, 'PNG')
        
        # Also save @2x versions for retina
        if size <= 18:
            retina_size = size * 2
            
            light_retina = draw_pot_menubar_icon(retina_size, for_dark_mode=False)
            light_retina_path = f"{icon_dir}/menubar-icon-light-{size}@2x.png"
            light_retina.save(light_retina_path, 'PNG')
            
            dark_retina = draw_pot_menubar_icon(retina_size, for_dark_mode=True)
            dark_retina_path = f"{icon_dir}/menubar-icon-dark-{size}@2x.png"
            dark_retina.save(dark_retina_path, 'PNG')
    
    print("✅ Menu bar icons created!")
    print(f"   Icons saved in: {icon_dir}/")
    
    # Create a standard 18x18 template icon (black, for system template)
    template_icon = draw_pot_menubar_icon(18, for_dark_mode=False)
    template_path = f"{icon_dir}/menubar-icon-template.png"
    template_icon.save(template_path, 'PNG')
    print(f"✅ Template icon saved: {template_path}")

if __name__ == "__main__":
    create_menubar_icons()