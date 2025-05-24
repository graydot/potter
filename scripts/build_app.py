#!/usr/bin/env python3
"""
Enhanced Potter App Builder with Code Signing Support
Supports both GitHub releases and App Store distribution
"""

import os
import sys
import subprocess
import shutil
import json
import tempfile
import time
import argparse
from pathlib import Path

# Build configuration
BUNDLE_ID = "com.rephrasely.app"
APP_NAME = "Potter"

def get_signing_config():
    """Get code signing configuration from environment"""
    config = {
        # Developer ID (for GitHub releases)
        'developer_id_app': os.getenv('DEVELOPER_ID_APPLICATION'),
        'developer_id_installer': os.getenv('DEVELOPER_ID_INSTALLER'),
        
        # App Store (for App Store distribution)
        'mac_app_store': os.getenv('MAC_APP_STORE_CERTIFICATE'),
        'mac_installer': os.getenv('MAC_INSTALLER_CERTIFICATE'),
        
        # Team and notarization
        'team_id': os.getenv('APPLE_TEAM_ID'),
        'apple_id': os.getenv('APPLE_ID'),
        'app_password': os.getenv('APPLE_APP_PASSWORD'),  # App-specific password
        'asc_provider': os.getenv('ASC_PROVIDER'),  # App Store Connect provider
        
        # API Key for App Store Connect (alternative to app password)
        'api_key_id': os.getenv('ASC_API_KEY_ID'),
        'api_issuer_id': os.getenv('ASC_API_ISSUER_ID'),
        'api_key_path': os.getenv('ASC_API_KEY_PATH'),
    }
    
    return config

def check_signing_requirements(target='github'):
    """Check if signing requirements are met"""
    config = get_signing_config()
    
    if target == 'github':
        required = ['developer_id_app', 'team_id']
        optional = ['apple_id', 'app_password']  # For notarization
    elif target == 'appstore':
        required = ['mac_app_store', 'team_id']
        optional = ['api_key_id', 'api_issuer_id']  # For upload
    else:
        return False, "Invalid target"
    
    missing_required = [key for key in required if not config.get(key)]
    missing_optional = [key for key in optional if not config.get(key)]
    
    if missing_required:
        return False, f"Missing required environment variables: {', '.join(missing_required)}"
    
    if missing_optional:
        print(f"⚠️  Optional variables missing: {', '.join(missing_optional)}")
        if target == 'github':
            print("   Without these, notarization will be skipped")
        elif target == 'appstore':
            print("   Without these, App Store upload will be skipped")
    
    return True, "All requirements met"

def create_entitlements_file(target='github'):
    """Create entitlements file based on target"""
    if target == 'github':
        # More permissive entitlements for GitHub releases
        entitlements = {
            "com.apple.security.app-sandbox": False,
            "com.apple.security.cs.allow-jit": True,
            "com.apple.security.cs.allow-unsigned-executable-memory": True,
            "com.apple.security.cs.disable-library-validation": True,
            "com.apple.security.automation.apple-events": True,
            "com.apple.security.device.accessibility": True,
        }
    else:  # appstore
        # Restricted entitlements for App Store
        entitlements = {
            "com.apple.security.app-sandbox": True,
            "com.apple.security.automation.apple-events": True,
            "com.apple.security.device.accessibility": True,
            "com.apple.security.files.user-selected.read-write": True,
            "com.apple.security.network.client": True,
        }
    
    # Create entitlements plist
    entitlements_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
"""
    
    for key, value in entitlements.items():
        value_str = "true" if value else "false"
        entitlements_content += f"    <key>{key}</key>\n    <{value_str}/>\n"
    
    entitlements_content += """</dict>
</plist>
"""
    
    entitlements_file = f"entitlements_{target}.plist"
    with open(entitlements_file, 'w') as f:
        f.write(entitlements_content)
    
    return entitlements_file

def sign_app(app_path, signing_identity, entitlements_file, target='github'):
    """Sign the application bundle"""
    print(f"🔐 Signing app with {signing_identity}...")
    
    try:
        # Sign all frameworks and libraries first
        for root, dirs, files in os.walk(app_path):
            for file in files:
                file_path = os.path.join(root, file)
                if (file.endswith('.dylib') or file.endswith('.so') or 
                    'Frameworks' in root):
                    try:
                        subprocess.run([
                            'codesign', '--force', '--verify', '--verbose',
                            '--sign', signing_identity,
                            '--timestamp',
                            file_path
                        ], check=True, capture_output=True)
                    except subprocess.CalledProcessError:
                        pass  # Some files might not be signable
        
        # Sign the main app bundle
        cmd = [
            'codesign', '--force', '--verify', '--verbose',
            '--sign', signing_identity,
            '--entitlements', entitlements_file,
            '--timestamp',
            '--options', 'runtime',  # Required for notarization
            app_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Signing failed: {result.stderr}")
            return False
        
        print("✅ App signed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Signing error: {e}")
        return False

def verify_signature(app_path):
    """Verify the app signature"""
    print("🔍 Verifying signature...")
    
    try:
        # Verify signature
        result = subprocess.run([
            'codesign', '--verify', '--deep', '--strict', '--verbose=2',
            app_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Signature verification passed")
            
            # Check if it will pass Gatekeeper
            gatekeeper_result = subprocess.run([
                'spctl', '--assess', '--type', 'execute', '--verbose',
                app_path
            ], capture_output=True, text=True)
            
            if gatekeeper_result.returncode == 0:
                print("✅ Gatekeeper assessment passed")
                return True
            else:
                print(f"⚠️  Gatekeeper assessment: {gatekeeper_result.stderr}")
                print("   App may need notarization")
                return True  # Still considered success, just needs notarization
        else:
            print(f"❌ Signature verification failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def notarize_app(app_path, config):
    """Notarize the app with Apple"""
    if not config.get('apple_id') or not config.get('app_password'):
        print("⚠️  Skipping notarization - Apple ID or app password not provided")
        return True
    
    print("📝 Submitting app for notarization...")
    
    try:
        # Create a zip file for notarization
        zip_path = app_path.replace('.app', '.zip')
        subprocess.run([
            'ditto', '-c', '-k', '--keepParent',
            app_path, zip_path
        ], check=True)
        
        # Submit for notarization using notarytool
        cmd = [
            'xcrun', 'notarytool', 'submit',
            zip_path,
            '--apple-id', config['apple_id'],
            '--password', config['app_password'],
            '--team-id', config.get('team_id', ''),
            '--wait'
        ]
        
        print("🕐 Submitting for notarization (this may take several minutes)...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Notarization successful!")
            
            # Staple the ticket
            staple_cmd = ['xcrun', 'stapler', 'staple', app_path]
            staple_result = subprocess.run(staple_cmd, capture_output=True, text=True)
            
            if staple_result.returncode == 0:
                print("✅ Notarization ticket stapled")
            else:
                print("⚠️  Failed to staple ticket, but notarization was successful")
            
            # Clean up zip file
            os.remove(zip_path)
            return True
        else:
            print(f"❌ Notarization failed: {result.stderr}")
            print(f"Output: {result.stdout}")
            os.remove(zip_path)
            return False
        
    except Exception as e:
        print(f"❌ Notarization error: {e}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return False

def create_app_store_package(app_path, config):
    """Create App Store package"""
    if not config.get('mac_installer'):
        print("⚠️  Skipping App Store package - installer certificate not provided")
        return None
    
    print("📦 Creating App Store package...")
    
    try:
        pkg_path = app_path.replace('.app', '.pkg')
        
        cmd = [
            'productbuild', '--component', app_path, '/Applications',
            '--sign', config['mac_installer'],
            pkg_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Package creation failed: {result.stderr}")
            return None
        
        print(f"✅ App Store package created: {pkg_path}")
        return pkg_path
        
    except Exception as e:
        print(f"❌ Package creation error: {e}")
        return None

def upload_to_app_store(pkg_path, config):
    """Upload package to App Store Connect"""
    if not pkg_path:
        return False
    
    # Check for API key method first (preferred)
    if config.get('api_key_id') and config.get('api_issuer_id') and config.get('api_key_path'):
        print("🚀 Uploading to App Store Connect (API Key method)...")
        
        cmd = [
            'xcrun', 'altool', '--upload-app',
            '--type', 'osx',
            '--file', pkg_path,
            '--apiKey', config['api_key_id'],
            '--apiIssuer', config['api_issuer_id']
        ]
        
    elif config.get('apple_id') and config.get('app_password'):
        print("🚀 Uploading to App Store Connect (Apple ID method)...")
        
        cmd = [
            'xcrun', 'altool', '--upload-app',
            '--type', 'osx',
            '--file', pkg_path,
            '--username', config['apple_id'],
            '--password', config['app_password']
        ]
        
        if config.get('asc_provider'):
            cmd.extend(['--asc-provider', config['asc_provider']])
    else:
        print("⚠️  Skipping App Store upload - credentials not provided")
        return True
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Successfully uploaded to App Store Connect")
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def modify_info_plist_for_target(app_path, target):
    """Modify Info.plist based on target"""
    info_plist_path = os.path.join(app_path, 'Contents', 'Info.plist')
    
    if not os.path.exists(info_plist_path):
        print(f"⚠️  Info.plist not found at {info_plist_path}")
        return
    
    if target == 'appstore':
        # App Store specific modifications
        print("📝 Configuring Info.plist for App Store...")
        
        # Add App Store specific keys
        subprocess.run([
            'plutil', '-replace', 'LSApplicationCategoryType',
            '-string', 'public.app-category.productivity',
            info_plist_path
        ])
        
        # Ensure proper bundle version format
        subprocess.run([
            'plutil', '-replace', 'CFBundleVersion',
            '-string', '1.0.0',
            info_plist_path
        ])
    
    print("✅ Info.plist configured")

def build_app(target='github', skip_signing=False, skip_notarization=False):
    """Main build function with signing support"""
    print(f"🔄 Enhanced Potter App Builder ({target} target)")
    print("=" * 60)
    
    # Check signing requirements
    if not skip_signing:
        requirements_ok, message = check_signing_requirements(target)
        if not requirements_ok:
            print(f"❌ {message}")
            print("\n💡 To build without signing, use --skip-signing")
            print("💡 Set up environment variables for code signing:")
            print("   export DEVELOPER_ID_APPLICATION='Developer ID Application: Your Name'")
            print("   export APPLE_TEAM_ID='YOUR_TEAM_ID'")
            return False
        print(f"✅ {message}")
    
    config = get_signing_config()
    
    # API key information (keep this for reference)
    print("ℹ️  Note: API key should be configured in app settings after installation")
    
    # Create app icon
    print("🎨 Creating app icon...")
    if create_app_icon():
        print("✅ Clean AI app icon created successfully")
    else:
        print("⚠️  Using default icon")
    
    print(f"🔨 Building Potter.app ({target} target)...")
    print("=" * 60)
    
    # Clean previous builds
    print("🧹 Cleaning previous dist...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Create dist structure
    os.makedirs("dist/app", exist_ok=True)
    
    # PyInstaller command - output to dist/app
    cmd = [
        'pyinstaller',
        '--distpath=dist/app',
        '--workpath=build',
        '--onedir',
        '--windowed',
        '--name=Potter',
        '--icon=app_icon.icns',
        '--osx-bundle-identifier=' + BUNDLE_ID,
        '--add-data=src/cocoa_settings.py:.',
        '--hidden-import=six.moves',
        '--hidden-import=six.moves.urllib',
        '--hidden-import=six',
        '--hidden-import=objc',
        '--hidden-import=Foundation',
        '--hidden-import=AppKit',
        '--hidden-import=UserNotifications',
        '--hidden-import=ApplicationServices',
        '--hidden-import=Quartz',
        '--clean',
        'src/potter.py'
    ]
    
    print("📦 Creating app bundle...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ PyInstaller failed: {result.stderr}")
        return False
    
    print("✅ App bundle created successfully!")
    print(f"Build output: {result.stdout if result.stdout else 'No output'}")
    
    app_path = "dist/app/Potter.app"
    
    # Fix Info.plist for double-click launching
    if fix_info_plist(app_path):
        print("✅ Fixed Info.plist for double-click launching")
    
    # Modify Info.plist for target
    modify_info_plist_for_target(app_path, target)
    
    # Code signing
    if not skip_signing:
        entitlements_file = create_entitlements_file(target)
        
        if target == 'github':
            signing_identity = config['developer_id_app']
        else:  # appstore
            signing_identity = config['mac_app_store']
        
        if sign_app(app_path, signing_identity, entitlements_file, target):
            if verify_signature(app_path):
                print("✅ App successfully signed and verified")
                
                # Notarization (for GitHub releases)
                if target == 'github' and not skip_notarization:
                    if notarize_app(app_path, config):
                        print("✅ App notarized successfully")
                    else:
                        print("⚠️  Notarization failed, but build continues")
                
                # App Store package creation
                if target == 'appstore':
                    pkg_path = create_app_store_package(app_path, config)
                    if pkg_path:
                        if upload_to_app_store(pkg_path, config):
                            print("✅ App Store upload completed")
                        else:
                            print("⚠️  App Store upload failed")
                    
            else:
                print("⚠️  Signature verification failed")
        else:
            print("⚠️  Code signing failed")
        
        # Clean up entitlements file
        if os.path.exists(entitlements_file):
            os.remove(entitlements_file)
    
    print("✅ Potter.app created at:", os.path.abspath(app_path))
    
    return True

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

def fix_info_plist(app_path):
    """Fix the Info.plist file after PyInstaller creates it"""
    info_plist_path = f"{app_path}/Contents/Info.plist"
    
    # Create proper Info.plist for background app that can be double-clicked
    info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Potter</string>
    <key>CFBundleIdentifier</key>
    <string>com.rephrasely.app</string>
    <key>CFBundleName</key>
    <string>Potter</string>
    <key>CFBundleDisplayName</key>
    <string>Potter</string>
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
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Potter needs access to send keystroke events for pasting processed text.</string>
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

def main():
    """Main build process with CLI support"""
    parser = argparse.ArgumentParser(description='Enhanced Potter App Builder')
    parser.add_argument('--target', choices=['github', 'appstore'], default='github',
                       help='Build target: github (for GitHub releases) or appstore (for App Store)')
    parser.add_argument('--skip-signing', action='store_true',
                       help='Skip code signing (for development builds)')
    parser.add_argument('--skip-notarization', action='store_true',
                       help='Skip notarization (faster builds for testing)')
    
    args = parser.parse_args()
    
    # Show environment setup instructions if no signing certificates configured
    config = get_signing_config()
    if not args.skip_signing and not config.get('developer_id_app') and not config.get('mac_app_store'):
        print("🔧 **CODE SIGNING SETUP REQUIRED**")
        print("=" * 60)
        print("To enable code signing, set these environment variables:")
        print("")
        print("For GitHub releases:")
        print("  export DEVELOPER_ID_APPLICATION='Developer ID Application: Your Name (TEAM_ID)'")
        print("  export APPLE_TEAM_ID='YOUR_TEAM_ID'")
        print("")
        print("For notarization (optional but recommended):")
        print("  export APPLE_ID='your@apple.id'")
        print("  export APPLE_APP_PASSWORD='app-specific-password'")
        print("")
        print("For App Store distribution:")
        print("  export MAC_APP_STORE_CERTIFICATE='3rd Party Mac Developer Application: Your Name (TEAM_ID)'")
        print("  export MAC_INSTALLER_CERTIFICATE='3rd Party Mac Developer Installer: Your Name (TEAM_ID)'")
        print("")
        print("For App Store Connect uploads:")
        print("  export ASC_API_KEY_ID='your-api-key-id'")
        print("  export ASC_API_ISSUER_ID='your-issuer-id'")
        print("  export ASC_API_KEY_PATH='/path/to/AuthKey_KEYID.p8'")
        print("")
        print("💡 Add --skip-signing to build without code signing")
        print("=" * 60)
        print("")
    
    success = build_app(
        target=args.target,
        skip_signing=args.skip_signing,
        skip_notarization=args.skip_notarization
    )
    
    if success:
        print("\n🎉 Build completed successfully!")
        if args.target == 'github':
            print("📋 Next steps for GitHub release:")
            print("  1. Test the signed app: open dist/app/Potter.app")
            print("  2. Create DMG: ./scripts/test_dmg_creation.sh")
            print("  3. Upload to GitHub releases")
        elif args.target == 'appstore':
            print("📋 Next steps for App Store:")
            print("  1. Check App Store Connect for upload status")
            print("  2. Submit for review in App Store Connect")
        sys.exit(0)
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 