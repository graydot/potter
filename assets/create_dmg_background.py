#!/usr/bin/env python3
"""
DMG Background Image Generator for Potter
Creates a professional-looking background for the DMG installer
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
except ImportError:
    print("❌ PIL (Pillow) is required to generate the DMG background")
    print("   Install with: pip install Pillow")
    exit(1)

def draw_cauldron_icon(draw, center_x, center_y):
    """Draw a magical cauldron icon with gradient colors"""
    
    # Scale factor for the icon
    scale = 0.8
    
    # Colors for gradient effect
    cauldron_colors = ['#8B5CF6', '#EC4899', '#F97316']  # Purple to pink to orange
    rim_color = '#FBBF24'  # Golden rim
    particle_colors = ['#F97316', '#EC4899', '#8B5CF6']
    
    # Draw magical particles above the cauldron
    particles = [
        (center_x - 30, center_y - 60, 4, 4),
        (center_x - 10, center_y - 70, 6, 6),
        (center_x + 15, center_y - 65, 3, 3),
        (center_x + 5, center_y - 50, 4, 4),
        (center_x - 20, center_y - 45, 3, 3),
        (center_x + 25, center_y - 50, 4, 4),
    ]
    
    for i, (px, py, pw, ph) in enumerate(particles):
        color = particle_colors[i % len(particle_colors)]
        draw.ellipse([px-pw//2, py-ph//2, px+pw//2, py+ph//2], fill=color)
    
    # Draw cauldron body (gradient effect by drawing multiple ellipses)
    cauldron_width = 80
    cauldron_height = 60
    
    # Create gradient effect
    for i in range(cauldron_height):
        progress = i / cauldron_height
        if progress < 0.5:
            # Purple to pink
            color_progress = progress * 2
            r = int(139 + (236 - 139) * color_progress)
            g = int(92 + (72 - 92) * color_progress)
            b = int(246 + (153 - 246) * color_progress)
        else:
            # Pink to orange
            color_progress = (progress - 0.5) * 2
            r = int(236 + (249 - 236) * color_progress)
            g = int(72 + (115 - 72) * color_progress)
            b = int(153 + (22 - 153) * color_progress)
        
        color = f'#{r:02x}{g:02x}{b:02x}'
        y_pos = center_y - cauldron_height//2 + i
        width_at_y = cauldron_width * (0.7 + 0.3 * (1 - abs(i - cauldron_height//2) / (cauldron_height//2)))
        
        draw.ellipse([
            center_x - width_at_y//2, y_pos,
            center_x + width_at_y//2, y_pos + 2
        ], fill=color)
    
    # Draw cauldron rim (golden)
    draw.ellipse([
        center_x - cauldron_width//2 - 5, center_y - cauldron_height//2 - 5,
        center_x + cauldron_width//2 + 5, center_y - cauldron_height//2 + 5
    ], fill=rim_color)
    
    # Draw cauldron legs
    leg_color = '#D97706'  # Darker orange
    leg_positions = [center_x - 30, center_x, center_x + 30]
    leg_y = center_y + cauldron_height//2 + 10
    
    for leg_x in leg_positions:
        draw.ellipse([leg_x - 4, leg_y - 3, leg_x + 4, leg_y + 3], fill=leg_color)
    
    # Draw handle
    handle_color = '#FFFFFF'
    draw.rectangle([
        center_x - 2, center_y - 10,
        center_x + 2, center_y + 10
    ], fill=handle_color)

def create_dmg_background():
    """Create a professional DMG background image"""
    
    # Image dimensions (standard DMG window size)
    width, height = 600, 400
    
    # Create base image with light gradient
    img = Image.new('RGB', (width, height), color='#f8f9fa')
    draw = ImageDraw.Draw(img)
    
    # Create subtle gradient background
    for y in range(height):
        # Light gradient from top to bottom
        shade = int(248 - (y / height) * 8)  # Subtle gradient
        color = (shade, shade + 1, shade + 2)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 28)
        subtitle_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
        instruction_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
    except OSError:
        # Fallback to default fonts
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        instruction_font = ImageFont.load_default()
    
    # Colors - magical theme
    primary_color = '#2c3e50'
    secondary_color = '#7f8c8d'
    accent_color = '#8B5CF6'  # Purple for magical theme
    
    # Draw magical cauldron icon in the center
    draw_cauldron_icon(draw, width//2, height//2 - 30)
    
    # Draw title
    title_text = "Potter"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = 30
    draw.text((title_x, title_y), title_text, fill=primary_color, font=title_font)
    
    # Draw subtitle
    subtitle_text = "AI-Powered Text Processing for macOS"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + 40
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill=secondary_color, font=subtitle_font)
    
    # Draw instruction text
    instruction_text = "Drag Potter to Applications to install"
    instruction_bbox = draw.textbbox((0, 0), instruction_text, font=instruction_font)
    instruction_width = instruction_bbox[2] - instruction_bbox[0]
    instruction_x = (width - instruction_width) // 2
    instruction_y = height - 50
    draw.text((instruction_x, instruction_y), instruction_text, fill=secondary_color, font=instruction_font)
    
    # Draw arrow
    arrow_start_x = 200
    arrow_end_x = 400
    arrow_y = 220
    arrow_thickness = 4
    
    # Arrow shaft
    draw.line([(arrow_start_x, arrow_y), (arrow_end_x - 20, arrow_y)], 
              fill=accent_color, width=arrow_thickness)
    
    # Arrow head
    arrow_size = 15
    arrow_points = [
        (arrow_end_x, arrow_y),
        (arrow_end_x - arrow_size, arrow_y - arrow_size//2),
        (arrow_end_x - arrow_size, arrow_y + arrow_size//2)
    ]
    draw.polygon(arrow_points, fill=accent_color)
    
    # Add some decorative elements
    # Small dots pattern in corners
    dot_color = '#ecf0f1'
    dot_size = 2
    
    # Top-left corner dots
    for i in range(5):
        for j in range(3):
            x = 20 + i * 8
            y = 20 + j * 8
            draw.ellipse([x-dot_size, y-dot_size, x+dot_size, y+dot_size], fill=dot_color)
    
    # Bottom-right corner dots
    for i in range(5):
        for j in range(3):
            x = width - 60 + i * 8
            y = height - 40 + j * 8
            draw.ellipse([x-dot_size, y-dot_size, x+dot_size, y+dot_size], fill=dot_color)
    
    return img

def main():
    """Main function to create and save the DMG background"""
    print("🎨 Creating DMG background image...")
    
    # Create the image
    img = create_dmg_background()
    
    # Save the image
    output_path = 'dmg_background.png'
    img.save(output_path, 'PNG')
    
    print(f"✅ DMG background saved as: {output_path}")
    print(f"   Size: {img.size[0]}x{img.size[1]} pixels")
    
    # Also save a @2x version for high-DPI displays
    retina_img = img.resize((1200, 800), Image.Resampling.LANCZOS)
    retina_path = 'dmg_background@2x.png'
    retina_img.save(retina_path, 'PNG')
    
    print(f"✅ High-DPI version saved as: {retina_path}")
    print("📦 These images can be used as DMG backgrounds")

if __name__ == "__main__":
    main() 