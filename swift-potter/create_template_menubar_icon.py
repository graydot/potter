#!/usr/bin/env python3
"""
Template Menu Bar Icon Generator for Potter
Creates a proper template icon from user's light image for macOS menu bar
Template icons are monochrome black on transparent background
"""

try:
    from PIL import Image, ImageOps
    import os
    import sys
except ImportError:
    print("❌ PIL (Pillow) is required to generate template icons")
    print("   Install with: pip install Pillow")
    exit(1)

def create_template_icon_from_image(source_image_path):
    """Create a template menu bar icon from a source image"""
    
    if not os.path.exists(source_image_path):
        print(f"❌ Source image not found: {source_image_path}")
        return False
    
    try:
        # Load the source image
        print(f"📷 Loading source image: {source_image_path}")
        source_img = Image.open(source_image_path)
        print(f"   Original size: {source_img.size}")
        
        # Convert to RGBA for transparency support
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
        
        # Create template icon (monochrome black on transparent)
        # First convert to grayscale to get the luminance
        grayscale = ImageOps.grayscale(source_img)
        
        # Create a new RGBA image
        template_img = Image.new('RGBA', source_img.size, (0, 0, 0, 0))
        
        # For each pixel, if it's not transparent in original, make it black in template
        for y in range(source_img.height):
            for x in range(source_img.width):
                original_pixel = source_img.getpixel((x, y))
                if len(original_pixel) == 4:  # RGBA
                    r, g, b, a = original_pixel
                    if a > 50:  # If not transparent (lowered threshold)
                        # Make it pure black with original alpha
                        template_img.putpixel((x, y), (0, 0, 0, a))
                else:  # RGB
                    # For RGB, use brightness to determine if pixel should be black
                    brightness = (r + g + b) / 3
                    if brightness < 200:  # If not very bright (likely content)
                        template_img.putpixel((x, y), (0, 0, 0, 255))
        
        print("🎨 Creating template menu bar icon...")
        
        # Menu bar icon sizes (18x18 is standard)
        sizes = [16, 18, 32]
        
        # Create Sources/Resources directory
        icon_dir = "Sources/Resources"
        os.makedirs(icon_dir, exist_ok=True)
        
        for size in sizes:
            print(f"   Creating {size}x{size} template icon...")
            
            # Resize with high-quality resampling
            resized = template_img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save the template icon
            icon_path = f"{icon_dir}/menubar-icon-template-{size}.png"
            resized.save(icon_path, 'PNG')
            
            # Also save @2x versions for retina (up to 18px base)
            if size <= 18:
                retina_size = size * 2
                retina_resized = template_img.resize((retina_size, retina_size), Image.Resampling.LANCZOS)
                retina_path = f"{icon_dir}/menubar-icon-template-{size}@2x.png"
                retina_resized.save(retina_path, 'PNG')
        
        # Create the main template icon (18px)
        template_18 = template_img.resize((18, 18), Image.Resampling.LANCZOS)
        template_path = f"{icon_dir}/menubar-icon-template.png"
        template_18.save(template_path, 'PNG')
        print(f"✅ Main template icon saved: {template_path}")
        
        print("✅ Template menu bar icon created!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Template Menu Bar Icon Generator for Potter")
        print("Creates a proper macOS template icon from your image")
        print("")
        print("Usage: python create_template_menubar_icon.py <path_to_image>")
        print("Example: python create_template_menubar_icon.py ~/Desktop/my_light_icon.png")
        return
    
    source_image = sys.argv[1]
    
    if create_template_icon_from_image(source_image):
        print("\\n🎉 Success! Your template menu bar icon is ready.")
        print("\\nNext steps:")
        print("1. Run 'make build' to build the app with the new template icon")
        print("2. The template icon will automatically adapt to light/dark mode")
        print("\\nNote: Template icons are monochrome and work best with simple, recognizable shapes")
    else:
        print("\\n❌ Failed to create template icon.")

if __name__ == "__main__":
    main()