#!/usr/bin/env python3
"""
Swift Potter App Builder with Code Signing Support
Creates distributable app bundle from Swift Potter project
"""

import os
import sys
import subprocess
import shutil
import json
import argparse
from pathlib import Path
import uuid
from datetime import datetime

# Build configuration
BUNDLE_ID = "com.potter.swift"
APP_NAME = "Potter"
SWIFT_PROJECT_DIR = "swift-potter"

def get_signing_config():
    """Get code signing configuration from environment"""
    config = {
        # Developer ID (for local distribution)
        'developer_id_app': os.getenv('DEVELOPER_ID_APPLICATION'),
        'developer_id_installer': os.getenv('DEVELOPER_ID_INSTALLER'),
        
        # App Store (for App Store distribution)
        'mac_app_store': os.getenv('MAC_APP_STORE_CERTIFICATE'),
        'mac_installer': os.getenv('MAC_INSTALLER_CERTIFICATE'),
        
        # Team and notarization
        'team_id': os.getenv('APPLE_TEAM_ID'),
        'apple_id': os.getenv('APPLE_ID'),
        'app_password': os.getenv('APPLE_APP_PASSWORD'),
        'asc_provider': os.getenv('ASC_PROVIDER'),
        
        # API Key for App Store Connect
        'api_key_id': os.getenv('ASC_API_KEY_ID'),
        'api_issuer_id': os.getenv('ASC_API_ISSUER_ID'),
        'api_key_path': os.getenv('ASC_API_KEY_PATH'),
    }
    
    return config

def check_signing_requirements(target='local'):
    """Check if signing requirements are met"""
    config = get_signing_config()
    
    if target == 'local':
        required = ['developer_id_app', 'team_id']
        optional = ['apple_id', 'app_password']  # For notarization
    elif target == 'appstore':
        required = ['mac_app_store', 'team_id']
        optional = ['api_key_id', 'api_issuer_id']
    else:
        return False, "Invalid target"
    
    missing_required = [key for key in required if not config.get(key)]
    missing_optional = [key for key in optional if not config.get(key)]
    
    if missing_required:
        return False, f"Missing required environment variables: {', '.join(missing_required)}"
    
    if missing_optional:
        print(f"⚠️  Optional variables missing: {', '.join(missing_optional)}")
        if target == 'local':
            print("   Without these, notarization will be skipped")
        elif target == 'appstore':
            print("   Without these, App Store upload will be skipped")
    
    return True, "All requirements met"

def create_entitlements_file(target='local'):
    """Create entitlements file based on target"""
    if target == 'local':
        # More permissive entitlements for local distribution
        entitlements = {
            "com.apple.security.app-sandbox": False,
            "com.apple.security.cs.allow-jit": True,
            "com.apple.security.cs.allow-unsigned-executable-memory": True,
            "com.apple.security.cs.disable-library-validation": True,
            "com.apple.security.automation.apple-events": True,
            "com.apple.security.device.accessibility": True,
            "com.apple.security.network.client": True,
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

def run_swift_tests():
    """Run Swift tests and return True if all tests pass"""
    print("🧪 Running Swift test suite before build...")
    print("=" * 50)
    
    if not os.path.exists(SWIFT_PROJECT_DIR):
        print(f"❌ Swift project directory not found: {SWIFT_PROJECT_DIR}")
        return False
    
    try:
        # Change to Swift project directory
        original_cwd = os.getcwd()
        os.chdir(SWIFT_PROJECT_DIR)
        
        # Run Swift tests
        result = subprocess.run(
            ['swift', 'test', '--parallel'],
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout for tests
        )
        
        # Return to original directory
        os.chdir(original_cwd)
        
        # Print test output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All Swift tests passed! Proceeding with build...")
            return True
        else:
            print("❌ Swift tests failed! Build aborted.")
            print("💡 Fix failing tests before building")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Swift tests timed out after 3 minutes")
        os.chdir(original_cwd)
        return False
    except Exception as e:
        print(f"❌ Error running Swift tests: {e}")
        os.chdir(original_cwd)
        return False

def build_swift_executable():
    """Build the Swift executable"""
    print("🔨 Building Swift executable...")
    
    if not os.path.exists(SWIFT_PROJECT_DIR):
        print(f"❌ Swift project directory not found: {SWIFT_PROJECT_DIR}")
        return False
    
    try:
        # Change to Swift project directory
        original_cwd = os.getcwd()
        os.chdir(SWIFT_PROJECT_DIR)
        
        # Build in release mode
        result = subprocess.run(
            ['swift', 'build', '-c', 'release'],
            capture_output=True,
            text=True
        )
        
        # Return to original directory
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            print("✅ Swift executable built successfully!")
            return True
        else:
            print(f"❌ Swift build failed: {result.stderr}")
            if result.stdout:
                print(f"Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error building Swift executable: {e}")
        os.chdir(original_cwd)
        return False

def create_app_bundle():
    """Create the macOS app bundle structure"""
    print("📦 Creating app bundle structure...")
    
    app_path = f"dist/{APP_NAME}.app"
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Create app bundle structure
    os.makedirs(f"{app_path}/Contents/MacOS", exist_ok=True)
    os.makedirs(f"{app_path}/Contents/Resources", exist_ok=True)
    
    # Copy Swift executable
    swift_executable = f"{SWIFT_PROJECT_DIR}/.build/release/Potter"
    if not os.path.exists(swift_executable):
        print(f"❌ Swift executable not found: {swift_executable}")
        return False
    
    shutil.copy2(swift_executable, f"{app_path}/Contents/MacOS/{APP_NAME}")
    
    # Make executable
    os.chmod(f"{app_path}/Contents/MacOS/{APP_NAME}", 0o755)
    
    print("✅ App bundle structure created")
    return app_path

def create_info_plist(app_path):
    """Create Info.plist for the app bundle"""
    print("📝 Creating Info.plist...")
    
    info_plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>{BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Potter needs access to send Apple Events for system automation.</string>
    <key>NSSystemAdministrationUsageDescription</key>
    <string>Potter needs system access to monitor global hotkeys.</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>"""
    
    info_plist_path = f"{app_path}/Contents/Info.plist"
    with open(info_plist_path, 'w') as f:
        f.write(info_plist_content)
    
    print("✅ Info.plist created")
    return True

def copy_app_icon(app_path):
    """Copy app icon to the bundle"""
    print("🎨 Adding app icon...")
    
    # Look for icon files in various locations
    icon_paths = [
        'swift-potter/Resources/AppIcon.icns',
        'assets/AppIcon.icns',
        'assets/icon.icns',
        'icon.icns'
    ]
    
    icon_source = None
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            icon_source = icon_path
            break
    
    if icon_source:
        shutil.copy2(icon_source, f"{app_path}/Contents/Resources/AppIcon.icns")
        print(f"✅ App icon copied from {icon_source}")
    else:
        print("⚠️  No app icon found, using default")
    
    return True

def sign_app(app_path, signing_identity, entitlements_file, target='local'):
    """Sign the application bundle"""
    print(f"🔐 Signing app with {signing_identity}...")
    
    try:
        # Sign the main executable first
        executable_path = f"{app_path}/Contents/MacOS/{APP_NAME}"
        
        cmd = [
            'codesign', '--force', '--verify', '--verbose',
            '--sign', signing_identity,
            '--entitlements', entitlements_file,
            '--timestamp',
            '--options', 'runtime',  # Required for notarization
            executable_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Executable signing failed: {result.stderr}")
            return False
        
        # Sign the main app bundle
        cmd = [
            'codesign', '--force', '--verify', '--verbose',
            '--sign', signing_identity,
            '--entitlements', entitlements_file,
            '--timestamp',
            '--options', 'runtime',
            app_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ App bundle signing failed: {result.stderr}")
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

def generate_build_id():
    """Generate a unique build ID with timestamp"""
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    build_id = {
        "build_id": f"swift_potter_{timestamp_str}_{unique_id}",
        "timestamp": timestamp.isoformat(),
        "unix_timestamp": int(timestamp.timestamp()),
        "version": "1.0.0",
        "platform": "swift"
    }
    
    return build_id

def embed_build_id(app_path):
    """Embed build ID into the app bundle"""
    try:
        build_id = generate_build_id()
        
        resources_path = f"{app_path}/Contents/Resources"
        os.makedirs(resources_path, exist_ok=True)
        
        build_id_file = f"{resources_path}/build_id.json"
        
        with open(build_id_file, 'w') as f:
            json.dump(build_id, f, indent=2)
        
        print(f"✅ Build ID embedded: {build_id['build_id']}")
        print(f"   Timestamp: {build_id['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to embed build ID: {e}")
        return False

def create_dmg(app_path):
    """Create a DMG file for distribution with custom background and Applications shortcut"""
    print("💿 Creating DMG for distribution...")
    
    try:
        dmg_name = f"{APP_NAME}-1.0.dmg"
        dmg_path = f"dist/{dmg_name}"
        temp_dmg = f"dist/temp_{dmg_name}"
        
        # Remove existing DMGs
        for path in [dmg_path, temp_dmg]:
            if os.path.exists(path):
                os.remove(path)
        
        # Create temporary DMG folder
        temp_folder = "dist/dmg_temp"
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        os.makedirs(temp_folder)
        
        # Copy app to temp folder
        shutil.copytree(app_path, f"{temp_folder}/{APP_NAME}.app")
        
        # Create Applications shortcut
        subprocess.run([
            'ln', '-s', '/Applications', f"{temp_folder}/Applications"
        ], check=True)
        
        # Check for custom background
        background_path = None
        background_candidates = [
            "assets/dmg_background.png",
            "assets/potter_dmg_background.png",
            "dmg_background.png"
        ]
        
        for bg_path in background_candidates:
            if os.path.exists(bg_path):
                background_path = bg_path
                break
        
        # Create initial DMG
        cmd = [
            'hdiutil', 'create',
            '-size', '100m',
            '-fs', 'HFS+',
            '-volname', APP_NAME,
            '-srcfolder', temp_folder,
            temp_dmg
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ DMG creation failed: {result.stderr}")
            return None
        
        # Mount the DMG for customization (read-write)
        mount_result = subprocess.run([
            'hdiutil', 'attach', temp_dmg, '-mountpoint', '/Volumes/Potter', '-readwrite'
        ], capture_output=True, text=True)
        
        if mount_result.returncode == 0:
            print("🎨 Customizing DMG layout...")
            
            # Copy background if available
            if background_path:
                shutil.copy2(background_path, '/Volumes/Potter/.background.png')
                
            # Create .DS_Store for custom layout (using basic positioning)
            ds_store_script = f'''
tell application "Finder"
    tell disk "{APP_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {{400, 100, 900, 400}}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 100
        set position of item "{APP_NAME}.app" of container window to {{150, 200}}
        set position of item "Applications" of container window to {{350, 200}}
        '''
            
            if background_path:
                ds_store_script += f'''
        set background picture of viewOptions to file ".background.png"
                '''
            
            ds_store_script += '''
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
'''
            
            # Apply layout using AppleScript
            try:
                subprocess.run([
                    'osascript', '-e', ds_store_script
                ], check=False)  # Don't fail if AppleScript fails
            except:
                pass
            
            # Unmount
            subprocess.run(['hdiutil', 'detach', '/Volumes/Potter'], check=False)
        
        # Convert to final compressed DMG
        subprocess.run([
            'hdiutil', 'convert', temp_dmg,
            '-format', 'UDZO',
            '-o', dmg_path
        ], check=True)
        
        # Clean up
        os.remove(temp_dmg)
        shutil.rmtree(temp_folder)
        
        print(f"✅ DMG created: {dmg_path}")
        return dmg_path
            
    except Exception as e:
        print(f"❌ DMG creation error: {e}")
        # Clean up on error
        for path in [temp_dmg, "dist/dmg_temp"]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        return None

def build_app(target='local', skip_tests=False):
    """Main build function"""
    
    # Run tests first unless skipped
    if not skip_tests:
        if not run_swift_tests():
            return False
    
    print(f"🔄 Swift Potter App Builder ({target} target)")
    print("=" * 60)
    
    # Check signing requirements
    requirements_ok, message = check_signing_requirements(target)
    if not requirements_ok:
        print(f"❌ {message}")
        print("\n💡 Set up environment variables for code signing:")
        print("   export DEVELOPER_ID_APPLICATION='Developer ID Application: Your Name'")
        print("   export APPLE_TEAM_ID='YOUR_TEAM_ID'")
        return False
    print(f"✅ {message}")
    
    config = get_signing_config()
    
    # Build Swift executable
    if not build_swift_executable():
        return False
    
    # Create app bundle
    app_path = create_app_bundle()
    if not app_path:
        return False
    
    # Create Info.plist
    if not create_info_plist(app_path):
        return False
    
    # Copy app icon
    copy_app_icon(app_path)
    
    # Embed build ID
    embed_build_id(app_path)
    
    # Code signing
    entitlements_file = create_entitlements_file(target)
    
    if target == 'local':
        signing_identity = config['developer_id_app']
    else:  # appstore
        signing_identity = config['mac_app_store']
    
    if sign_app(app_path, signing_identity, entitlements_file, target):
        if verify_signature(app_path):
            print("✅ App successfully signed and verified")
            
            # Notarization (for local distribution)
            if target == 'local':
                if notarize_app(app_path, config):
                    print("✅ App notarized successfully")
                else:
                    print("⚠️  Notarization failed - app may trigger security warnings")
            
            # Create DMG for local distribution
            if target == 'local':
                dmg_path = create_dmg(app_path)
                if dmg_path:
                    print(f"✅ Distribution DMG created: {dmg_path}")
                
        else:
            print("❌ Signature verification failed")
            return False
    else:
        print("❌ Code signing failed")
        return False
    
    # Clean up entitlements file
    if os.path.exists(entitlements_file):
        os.remove(entitlements_file)
    
    print("✅ Swift Potter.app created at:", os.path.abspath(app_path))
    
    return True

def main():
    """Main build process with CLI support"""
    parser = argparse.ArgumentParser(description='Swift Potter App Builder')
    parser.add_argument('--target', choices=['local', 'appstore'], default='local',
                       help='Build target: local (for local distribution) or appstore (for App Store)')
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip running tests before building')
    
    args = parser.parse_args()
    
    # Show environment setup instructions if no signing certificates configured
    config = get_signing_config()
    if not config.get('developer_id_app') and not config.get('mac_app_store'):
        print("🔧 **CODE SIGNING SETUP REQUIRED**")
        print("=" * 60)
        print("To enable code signing, set these environment variables:")
        print("")
        print("For local distribution:")
        print("  export DEVELOPER_ID_APPLICATION='Developer ID Application: Your Name (TEAM_ID)'")
        print("  export APPLE_TEAM_ID='YOUR_TEAM_ID'")
        print("")
        print("For notarization (recommended for local distribution):")
        print("  export APPLE_ID='your@apple.id'")
        print("  export APPLE_APP_PASSWORD='app-specific-password'")
        print("")
        print("For App Store distribution:")
        print("  export MAC_APP_STORE_CERTIFICATE='3rd Party Mac Developer Application: Your Name (TEAM_ID)'")
        print("  export MAC_INSTALLER_CERTIFICATE='3rd Party Mac Developer Installer: Your Name (TEAM_ID)'")
        print("")
        print("💡 All builds are signed and notarized for security")
        print("=" * 60)
        print("")
    
    success = build_app(
        target=args.target,
        skip_tests=args.skip_tests
    )
    
    if success:
        print("\n🎉 Swift Potter build completed successfully!")
        if args.target == 'local':
            print("📋 Next steps for local testing:")
            print("  1. Test the signed app: open dist/Potter.app")
            print("  2. Install to Applications: cp -r dist/Potter.app /Applications/")
            print("  3. Distribute via DMG: dist/Potter-1.0.dmg")
        elif args.target == 'appstore':
            print("📋 Next steps for App Store:")
            print("  1. Check App Store Connect for upload status")
            print("  2. Submit for review in App Store Connect")
        sys.exit(0)
    else:
        print("\n❌ Swift Potter build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()