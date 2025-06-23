#!/usr/bin/env python3
"""
Menu Bar Icon Generator for Potter - From User Images
Creates proper macOS menu bar icons from user-provided light and dark images
"""

try:
    from PIL import Image
    import os
    import sys
    import argparse
except ImportError:
    print("❌ PIL (Pillow) is required to generate menu bar icons")
    print("   Install with: pip install Pillow")
    exit(1)

def create_menubar_icon_from_image(source_image_path, mode='light'):
    """Create menu bar icons from a source image for specified mode"""
    
    if not os.path.exists(source_image_path):
        print(f"❌ Source image not found: {source_image_path}")
        return False
    
    try:
        # Load the source image
        print(f"📷 Loading {mode} mode image: {source_image_path}")
        source_img = Image.open(source_image_path)
        
        # Convert to RGBA for transparency support
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
        
        print(f"   Original size: {source_img.size}")
        
        # Menu bar icon sizes (18x18 is standard for macOS menu bar)
        sizes = [16, 18, 32]  # 16 for small displays, 18 standard, 32 for retina
        
        print(f"🎨 Creating {mode} mode menu bar icons...")
        
        # Create Sources/Resources directory relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_dir = os.path.join(script_dir, "Sources", "Resources")
        os.makedirs(icon_dir, exist_ok=True)
        
        for size in sizes:
            print(f"   Creating {size}x{size} {mode} mode icon...")
            
            # Resize with high-quality resampling
            resized = source_img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save the icon
            if mode == 'light':
                icon_path = f"{icon_dir}/menubar-icon-light-{size}.png"
            else:  # dark
                icon_path = f"{icon_dir}/menubar-icon-dark-{size}.png"
            
            resized.save(icon_path, 'PNG')
            
            # Also save @2x versions for retina (up to 18px base)
            if size <= 18:
                retina_size = size * 2
                retina_resized = source_img.resize((retina_size, retina_size), Image.Resampling.LANCZOS)
                
                if mode == 'light':
                    retina_path = f"{icon_dir}/menubar-icon-light-{size}@2x.png"
                else:  # dark
                    retina_path = f"{icon_dir}/menubar-icon-dark-{size}@2x.png"
                
                retina_resized.save(retina_path, 'PNG')
        
        # If this is light mode, also create template icon (uses light image as base)
        if mode == 'light':
            print("   Creating template icon...")
            template_icon = source_img.resize((18, 18), Image.Resampling.LANCZOS)
            template_path = f"{icon_dir}/menubar-icon-template.png"
            template_icon.save(template_path, 'PNG')
            print(f"✅ Template icon saved: {template_path}")
        
        print(f"✅ {mode.capitalize()} mode menu bar icons created!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {mode} image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create menu bar icons from user images')
    parser.add_argument('--light', type=str, help='Path to light mode PNG image')
    parser.add_argument('--dark', type=str, help='Path to dark mode PNG image')
    parser.add_argument('--mode', choices=['light', 'dark', 'both'], default='both',
                       help='Which mode to generate (default: both)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode in ['light', 'both'] and not args.light:
        print("❌ Light mode image required when mode is 'light' or 'both'")
        print("   Use: --light path/to/light_image.png")
        return
    
    if args.mode in ['dark', 'both'] and not args.dark:
        print("❌ Dark mode image required when mode is 'dark' or 'both'")
        print("   Use: --dark path/to/dark_image.png")
        return
    
    success = True
    
    # Generate light mode icons
    if args.mode in ['light', 'both'] and args.light:
        if not create_menubar_icon_from_image(args.light, 'light'):
            success = False
    
    # Generate dark mode icons
    if args.mode in ['dark', 'both'] and args.dark:
        if not create_menubar_icon_from_image(args.dark, 'dark'):
            success = False
    
    if success:
        print(f"\n🎉 Success! Your new menu bar icons are ready.")
        print("\nNext steps:")
        print("1. Run 'make build' to build the app with new menu bar icons")
        print("2. The new icons will be included in the app bundle")
        
        print(f"\nGenerated icons in Sources/Resources/:")
        if args.mode in ['light', 'both']:
            print("   • menubar-icon-light-16.png + @2x")
            print("   • menubar-icon-light-18.png + @2x") 
            print("   • menubar-icon-light-32.png")
            print("   • menubar-icon-template.png")
        if args.mode in ['dark', 'both']:
            print("   • menubar-icon-dark-16.png + @2x")
            print("   • menubar-icon-dark-18.png + @2x")
            print("   • menubar-icon-dark-32.png")
    else:
        print("\n❌ Failed to create some menu bar icons.")

def show_usage_examples():
    print("\n📋 Usage Examples:")
    print("python create_menubar_icons_from_images.py --light ~/Desktop/light_icon.png --dark ~/Desktop/dark_icon.png")
    print("python create_menubar_icons_from_images.py --light ~/Desktop/light_icon.png --mode light")
    print("python create_menubar_icons_from_images.py --dark ~/Desktop/dark_icon.png --mode dark")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Menu Bar Icon Generator for Potter")
        print("Creates menu bar icons from your light and dark mode PNG images")
        show_usage_examples()
    else:
        main()