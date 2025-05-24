#!/usr/bin/env python3
"""
Build script to create a standalone Rephrasely.app for macOS
This creates a proper .app bundle that only needs accessibility permissions for itself
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_app():
    """Build the Rephrasely.app bundle"""
    print("🔨 Building Rephrasely.app...")
    print("=" * 50)
    
    # Clean previous builds
    if os.path.exists('dist'):
        print("🧹 Cleaning previous build...")
        shutil.rmtree('dist')
    
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Create the app bundle using PyInstaller
    print("📦 Creating app bundle...")
    
    # PyInstaller command to create a macOS app bundle
    cmd = [
        'pyinstaller',
        '--onedir',                    # Create a directory bundle
        '--windowed',                  # Don't show console window
        '--name=Rephrasely',          # App name
        '--icon=app_icon.icns',       # App icon (we'll create this)
        '--osx-bundle-identifier=com.rephrasely.app',  # Bundle identifier
        '--add-data=.env:.',          # Include .env file
        '--add-data=cocoa_settings.py:.',  # Include Cocoa settings UI module
        '--hidden-import=six.moves',  # Explicitly include six.moves
        '--hidden-import=six.moves.urllib',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=pynput.mouse',
        '--hidden-import=pyobjc-framework-Cocoa',
        '--hidden-import=pyobjc-framework-Quartz',
        '--hidden-import=pyobjc-framework-Foundation',
        '--hidden-import=pyobjc-framework-AppKit',
        '--hidden-import=pyobjc-framework-ApplicationServices',
        '--collect-all=pynput',       # Include all pynput modules
        '--collect-all=pyobjc',       # Include all pyobjc modules
        '--paths=/System/Library/Frameworks/Tk.framework/Versions/8.5/Resources/Scripts',  # macOS tkinter path
        '--paths=/usr/local/lib/python3.13/site-packages',  # Python packages path
        'rephrasely.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ App bundle created successfully!")
        print("Build output:", result.stdout if result.stdout else "No output")
        
        # Check if the app was created
        app_path = 'dist/Rephrasely.app'
        bundle_path = 'dist/Rephrasely'
        
        if os.path.exists(app_path):
            # Fix the Info.plist after PyInstaller creates it
            fix_info_plist(app_path)
            
            # Re-sign the app after modifying Info.plist
            print("🔐 Re-signing app bundle...")
            try:
                subprocess.run(['codesign', '--force', '--deep', '--sign', '-', app_path], 
                             check=True, capture_output=True, text=True)
                print("✅ App bundle re-signed successfully")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Code signing failed: {e}")
                print("App may not launch via double-click")
            
            # Make sure executable permissions are correct
            executable_path = f"{app_path}/Contents/MacOS/Rephrasely"
            if os.path.exists(executable_path):
                os.chmod(executable_path, 0o755)
            
            print(f"✅ Rephrasely.app created at: {os.path.abspath(app_path)}")
            return True
        elif os.path.exists(bundle_path):
            print(f"⚠️  Bundle created but not as .app, converting...")
            # Convert the bundle to a proper .app
            create_app_bundle_from_directory(bundle_path)
            return True
        else:
            print("❌ App bundle was not created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        print(f"Build output: {e.stdout}")
        return False

def fix_info_plist(app_path):
    """Fix the Info.plist file after PyInstaller creates it"""
    info_plist_path = f"{app_path}/Contents/Info.plist"
    
    # Create proper Info.plist for background app that can be double-clicked
    info_plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Rephrasely</string>
    <key>CFBundleIdentifier</key>
    <string>com.rephrasely.app</string>
    <key>CFBundleName</key>
    <string>Rephrasely</string>
    <key>CFBundleDisplayName</key>
    <string>Rephrasely</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>app_icon.icns</string>
    <key>LSUIElement</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Rephrasely needs access to send keystroke events for pasting processed text.</string>
    <key>NSSystemAdministrationUsageDescription</key>
    <string>Rephrasely needs system access to monitor global hotkeys.</string>
    <key>LSEnvironment</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>.</string>
    </dict>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>"""
    
    with open(info_plist_path, 'w') as f:
        f.write(info_plist_content)
    
    print("✅ Fixed Info.plist for double-click launching")

def create_app_bundle_from_directory(bundle_path):
    """Convert PyInstaller directory to proper .app bundle"""
    print("🔄 Converting to proper .app bundle...")
    
    app_path = 'dist/Rephrasely.app'
    
    # Create .app structure
    os.makedirs(f"{app_path}/Contents/MacOS", exist_ok=True)
    os.makedirs(f"{app_path}/Contents/Resources", exist_ok=True)
    
    # Copy executable and dependencies
    shutil.copytree(bundle_path, f"{app_path}/Contents/MacOS", dirs_exist_ok=True)
    
    # Create proper Info.plist for background app
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Rephrasely</string>
    <key>CFBundleIdentifier</key>
    <string>com.rephrasely.app</string>
    <key>CFBundleName</key>
    <string>Rephrasely</string>
    <key>CFBundleDisplayName</key>
    <string>Rephrasely</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>app_icon.icns</string>
    <key>LSUIElement</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Rephrasely needs access to send keystroke events for pasting processed text.</string>
    <key>NSSystemAdministrationUsageDescription</key>
    <string>Rephrasely needs system access to monitor global hotkeys.</string>
    <key>LSEnvironment</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>.</string>
    </dict>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>"""
    
    with open(f"{app_path}/Contents/Info.plist", 'w') as f:
        f.write(info_plist)
    
    # Copy icon if it exists
    if os.path.exists('app_icon.icns'):
        shutil.copy2('app_icon.icns', f"{app_path}/Contents/Resources/")
    
    # Copy environment and settings files
    for file in ['.env', 'cocoa_settings.py']:
        if os.path.exists(file):
            shutil.copy2(file, f"{app_path}/Contents/MacOS/")
    
    # Make sure the executable is executable
    executable_path = f"{app_path}/Contents/MacOS/Rephrasely"
    if os.path.exists(executable_path):
        os.chmod(executable_path, 0o755)
    
    # Re-sign the app after creating the bundle
    print("🔐 Re-signing app bundle...")
    try:
        subprocess.run(['codesign', '--force', '--deep', '--sign', '-', app_path], 
                     check=True, capture_output=True, text=True)
        print("✅ App bundle re-signed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Code signing failed: {e}")
        print("App may not launch via double-click")
    
    # Remove the old directory
    shutil.rmtree(bundle_path)
    
    print(f"✅ Proper .app bundle created at: {os.path.abspath(app_path)}")

def create_app_icon():
    """Create a professional app icon with clean clipboard and AI sparkle"""
    print("🎨 Creating app icon...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a high-resolution icon
        size = 512
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Simple background circle (subtle gray)
        margin = 40
        draw.ellipse([margin, margin, size-margin, size-margin], fill=(240, 240, 240, 220))
        
        # Scale everything proportionally
        scale = size / 64
        
        # Main clipboard/copy icon (centered, black and white)
        clip_x = int(18 * scale)
        clip_y = int(12 * scale)
        clip_w = int(28 * scale)
        clip_h = int(36 * scale)
        
        # Clipboard body (white with black outline)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='black', width=int(3 * scale))
        
        # Clipboard top clip (black)
        clip_top_x = clip_x + int(8 * scale)
        clip_top_y = clip_y - int(4 * scale)
        clip_top_w = int(12 * scale)
        clip_top_h = int(6 * scale)
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='black')
        
        # Document lines (gray)
        line_x = clip_x + int(4 * scale)
        line_w = int(20 * scale)
        line_h = int(2 * scale)
        line_color = '#666666'
        
        draw.rectangle([line_x, clip_y + int(8 * scale), line_x + line_w, clip_y + int(8 * scale) + line_h], 
                      fill=line_color)
        draw.rectangle([line_x, clip_y + int(14 * scale), line_x + line_w, clip_y + int(14 * scale) + line_h], 
                      fill=line_color)
        draw.rectangle([line_x, clip_y + int(20 * scale), line_x + int(16 * scale), clip_y + int(20 * scale) + line_h], 
                      fill=line_color)
        draw.rectangle([line_x, clip_y + int(26 * scale), line_x + int(18 * scale), clip_y + int(26 * scale) + line_h], 
                      fill=line_color)
        
        # AI Sparkle at bottom right (inspired by the provided icon)
        sparkle_x = int(44 * scale)
        sparkle_y = int(44 * scale)
        sparkle_size = int(8 * scale)
        
        # Create the 4-pointed diamond star with blue gradient effect
        # Main diamond shape
        points = [
            (sparkle_x, sparkle_y - sparkle_size),  # Top
            (sparkle_x + sparkle_size, sparkle_y),   # Right
            (sparkle_x, sparkle_y + sparkle_size),   # Bottom
            (sparkle_x - sparkle_size, sparkle_y)    # Left
        ]
        
        # Draw the sparkle with gradient-like effect
        # Outer layer (darker blue)
        draw.polygon(points, fill='#4A90E2')
        
        # Inner layer (lighter blue) - smaller diamond
        inner_size = sparkle_size - int(2 * scale)
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#7BB3F0')
        
        # Center highlight (very light blue/white)
        center_size = sparkle_size - int(4 * scale)
        if center_size > 0:
            center_points = [
                (sparkle_x, sparkle_y - center_size),
                (sparkle_x + center_size, sparkle_y),
                (sparkle_x, sparkle_y + center_size),
                (sparkle_x - center_size, sparkle_y)
            ]
            draw.polygon(center_points, fill='#B8D4F1')
        
        # Save as PNG first
        image.save('app_icon.png')
        
        # Convert to .icns using macOS built-in tool
        if os.path.exists('app_icon.png'):
            # Create iconset directory
            os.makedirs('app_icon.iconset', exist_ok=True)
            
            # Generate different sizes
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            for size in sizes:
                resized = image.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(f'app_icon.iconset/icon_{size}x{size}.png')
                if size <= 512:  # Also create @2x versions
                    resized.save(f'app_icon.iconset/icon_{size//2}x{size//2}@2x.png')
            
            # Convert to .icns
            try:
                subprocess.run(['iconutil', '-c', 'icns', 'app_icon.iconset'], check=True)
                print("✅ Clean AI app icon created successfully")
                
                # Clean up
                shutil.rmtree('app_icon.iconset')
                os.remove('app_icon.png')
                return True
            except subprocess.CalledProcessError:
                print("⚠️  Could not create .icns file, using PNG instead")
                os.rename('app_icon.png', 'app_icon.icns')
                return True
        
    except ImportError:
        print("⚠️  PIL not available, creating simple icon...")
        # Create a simple text-based icon
        with open('app_icon.icns', 'w') as f:
            f.write('')  # Empty file, PyInstaller will use default
        return True
    
    except Exception as e:
        print(f"⚠️  Could not create icon: {e}")
        # Create empty icon file
        with open('app_icon.icns', 'w') as f:
            f.write('')
        return True

def main():
    """Main build process"""
    print("🔄 Rephrasely App Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('rephrasely.py'):
        print("❌ Error: rephrasely.py not found. Please run this from the project directory.")
        return False
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found. You'll need to configure your API key later.")
    
    # Create app icon
    create_app_icon()
    
    # Build the app
    if build_app():
        print("\n🎉 Build completed successfully!")
        print("\n📋 Next steps:")
        print("1. Open dist/Rephrasely.app")
        print("2. macOS will ask for accessibility permissions")
        print("3. Grant permissions only to Rephrasely.app (not Terminal!)")
        print("4. The app will run independently")
        print("\n💡 To install: drag Rephrasely.app to your Applications folder")
        print("💡 To run: double-click Rephrasely.app or use Spotlight")
        
        # Clean up build files
        print("\n🧹 Cleaning up build files...")
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists('Rephrasely.spec'):
            os.remove('Rephrasely.spec')
        if os.path.exists('app_icon.icns'):
            os.remove('app_icon.icns')
        
        return True
    else:
        print("\n❌ Build failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 