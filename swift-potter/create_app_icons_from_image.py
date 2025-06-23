#!/usr/bin/env python3
"""
App Icon Generator for Potter - From User Image
Creates proper macOS app icons from a user-provided image
"""

try:
    from PIL import Image
    import os
    import sys
except ImportError:
    print("❌ PIL (Pillow) is required to generate app icons")
    print("   Install with: pip install Pillow")
    exit(1)

def create_app_icon_from_image(source_image_path):
    """Create a complete set of app icons from a source image"""
    
    if not os.path.exists(source_image_path):
        print(f"❌ Source image not found: {source_image_path}")
        return False
    
    try:
        # Load the source image
        print(f"📷 Loading source image: {source_image_path}")
        source_img = Image.open(source_image_path)
        
        # Convert to RGBA for transparency support
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
        
        print(f"   Original size: {source_img.size}")
        
        # macOS app icon sizes
        icon_sizes = [16, 32, 64, 128, 256, 512, 1024]
        
        print("🎨 Creating Potter app icon set...")
        
        # Create Sources/Resources/AppIcon directory
        icon_dir = "Sources/Resources/AppIcon"
        os.makedirs(icon_dir, exist_ok=True)
        
        for size in icon_sizes:
            print(f"   Creating {size}x{size} icon...")
            
            # Resize with high-quality resampling
            resized = source_img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG
            icon_path = f"{icon_dir}/potter-icon-{size}.png"
            resized.save(icon_path, 'PNG')
            
            # Also save @2x versions for retina (up to 512px base)
            if size <= 512:
                retina_size = size * 2
                retina_resized = source_img.resize((retina_size, retina_size), Image.Resampling.LANCZOS)
                retina_path = f"{icon_dir}/potter-icon-{size}@2x.png"
                retina_resized.save(retina_path, 'PNG')
        
        # Create a 128px version specifically for alerts
        alert_icon = source_img.resize((128, 128), Image.Resampling.LANCZOS)
        alert_path = f"{icon_dir}/potter-alert-icon.png"
        alert_icon.save(alert_path, 'PNG')
        print(f"✅ Alert icon saved: {alert_path}")
        
        # Create ICNS file for main app icon
        print("📦 Creating ICNS file for main app icon...")
        
        # Use the 1024px version as the base for ICNS
        main_icon = source_img.resize((1024, 1024), Image.Resampling.LANCZOS)
        icns_path = "../assets/AppIcon.icns"
        
        # Save as ICNS (requires Pillow with ICNS support)
        try:
            main_icon.save(icns_path, 'ICNS')
            print(f"✅ ICNS file saved: {icns_path}")
        except Exception as e:
            print(f"⚠️  Could not create ICNS file directly: {e}")
            print("   You can use online converter or macOS Preview to convert the 1024px PNG to ICNS")
            
            # Save a 1024px PNG as fallback
            fallback_path = "../assets/AppIcon-1024.png"
            main_icon.save(fallback_path, 'PNG')
            print(f"   Saved 1024px PNG for manual conversion: {fallback_path}")
        
        print("✅ App icon set created!")
        print(f"   Icons saved in: {icon_dir}/")
        print(f"   Main app icon: {icns_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_app_icons_from_image.py <path_to_image>")
        print("Example: python create_app_icons_from_image.py ~/Desktop/my_icon.jpg")
        return
    
    source_image = sys.argv[1]
    
    if create_app_icon_from_image(source_image):
        print("\n🎉 Success! Your new app icons are ready.")
        print("\nNext steps:")
        print("1. Run 'make build' to build the app with new icons")
        print("2. The new icons will be included in the app bundle")
    else:
        print("\n❌ Failed to create app icons.")

if __name__ == "__main__":
    main()