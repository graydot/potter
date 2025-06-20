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

def create_dmg_background():
    """Create a professional DMG background image"""
    
    # Image dimensions (updated for taller DMG window)
    width, height = 600, 500
    
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
    
    # Colors
    primary_color = '#2c3e50'
    secondary_color = '#7f8c8d'
    accent_color = '#3498db'
    
    # Remove all text elements for cleaner look
    
    # Draw arrow from Potter (left) to Applications (right)
    # Adjust positions to match new DMG layout (160,250) and (440,250)
    arrow_start_x = 160  # Potter position guide  
    arrow_end_x = 440    # Applications position guide
    arrow_y = 250
    arrow_thickness = 2
    
    # Arrow shaft (smaller)
    draw.line([(arrow_start_x, arrow_y), (arrow_end_x - 12, arrow_y)], 
              fill=accent_color, width=arrow_thickness)
    
    # Arrow head pointing right (toward Applications) - smaller
    arrow_size = 8
    arrow_points = [
        (arrow_end_x, arrow_y),
        (arrow_end_x - arrow_size, arrow_y - arrow_size//2),
        (arrow_end_x - arrow_size, arrow_y + arrow_size//2)
    ]
    draw.polygon(arrow_points, fill=accent_color)
    
    # Remove position guide text for cleaner look
    
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
    retina_img = img.resize((1200, 1000), Image.Resampling.LANCZOS)
    retina_path = 'dmg_background@2x.png'
    retina_img.save(retina_path, 'PNG')
    
    print(f"✅ High-DPI version saved as: {retina_path}")
    print("📦 These images can be used as DMG backgrounds")

if __name__ == "__main__":
    main() 