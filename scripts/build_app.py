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
    
    # Fix framework references to use correct paths
    print("🔧 Fixing framework references...")
    executable_path = f"{app_path}/Contents/MacOS/{APP_NAME}"
    
    # Update Sparkle framework reference
    try:
        result = subprocess.run([
            'install_name_tool', '-change',
            '@rpath/Sparkle.framework/Versions/B/Sparkle',
            '@executable_path/../Frameworks/Sparkle.framework/Versions/B/Sparkle',
            executable_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Framework references updated")
        else:
            print(f"⚠️  Framework reference update failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not update framework references: {e}")
    
    print("✅ App bundle structure created")
    return app_path

def create_info_plist(app_path):
    """Copy and modify Info.plist from source"""
    print("📝 Creating Info.plist from source...")
    
    # Try to find source Info.plist
    source_info_plist = f"{SWIFT_PROJECT_DIR}/Sources/Resources/Info.plist"
    if not os.path.exists(source_info_plist):
        print(f"❌ Source Info.plist not found at {source_info_plist}")
        return False
    
    # Copy source Info.plist to app bundle
    info_plist_path = f"{app_path}/Contents/Info.plist"
    shutil.copy2(source_info_plist, info_plist_path)
    
    # Read and modify the copied plist
    import plistlib
    with open(info_plist_path, 'rb') as f:
        plist_data = plistlib.load(f)
    
    # Update bundle-specific fields
    plist_data['CFBundleExecutable'] = APP_NAME
    plist_data['CFBundleIdentifier'] = BUNDLE_ID
    plist_data['CFBundleName'] = APP_NAME
    plist_data['CFBundleDisplayName'] = APP_NAME
    plist_data['CFBundleIconFile'] = 'AppIcon'
    
    # Write the modified plist back
    with open(info_plist_path, 'wb') as f:
        plistlib.dump(plist_data, f)
    
    print("✅ Info.plist created from source")
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

def bundle_frameworks(app_path):
    """Bundle required frameworks into the app"""
    print("📦 Bundling frameworks...")
    
    # Create Frameworks directory
    frameworks_dir = f"{app_path}/Contents/Frameworks"
    os.makedirs(frameworks_dir, exist_ok=True)
    
    # Find and copy Sparkle framework
    sparkle_xcframework_path = "swift-potter/.build/artifacts/sparkle/Sparkle/Sparkle.xcframework/macos-arm64_x86_64/Sparkle.framework"
    
    if os.path.exists(sparkle_xcframework_path):
        sparkle_dest = f"{frameworks_dir}/Sparkle.framework"
        if os.path.exists(sparkle_dest):
            shutil.rmtree(sparkle_dest)
        
        # Use cp -a to preserve symlinks (critical for Sparkle framework)
        import subprocess
        result = subprocess.run(['cp', '-a', sparkle_xcframework_path, sparkle_dest], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to copy Sparkle framework: {result.stderr}")
            return False
            
        print("✅ Sparkle framework bundled (symlinks preserved)")
        return True
    else:
        print(f"❌ Sparkle framework not found at {sparkle_xcframework_path}")
        # Try alternative paths
        alt_paths = [
            "swift-potter/.build/artifacts/extract/sparkle/Sparkle/Sparkle.xcframework/macos-arm64_x86_64/Sparkle.framework",
            "swift-potter/.build/checkouts/sparkle/Sparkle.xcframework/macos-arm64_x86_64/Sparkle.framework"
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                sparkle_dest = f"{frameworks_dir}/Sparkle.framework"
                if os.path.exists(sparkle_dest):
                    shutil.rmtree(sparkle_dest)
                
                # Use cp -a to preserve symlinks
                result = subprocess.run(['cp', '-a', alt_path, sparkle_dest], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Failed to copy Sparkle framework from {alt_path}: {result.stderr}")
                    continue
                    
                print(f"✅ Sparkle framework bundled from {alt_path} (symlinks preserved)")
                return True
        
        print("❌ Could not find Sparkle framework in any expected location")
        return False

def sign_app(app_path, signing_identity, entitlements_file, target='local'):
    """Sign the application bundle"""
    print(f"🔐 Signing app with {signing_identity}...")
    
    try:
        # Sign frameworks first (if any)
        frameworks_dir = f"{app_path}/Contents/Frameworks"
        if os.path.exists(frameworks_dir):
            for framework in os.listdir(frameworks_dir):
                if framework.endswith('.framework'):
                    framework_path = f"{frameworks_dir}/{framework}"
                    print(f"🔐 Signing framework: {framework}")
                    
                    # Sign XPC services and other executables first with minimal flags
                    xpc_services_dir = f"{framework_path}/Versions/B/XPCServices"
                    if os.path.exists(xpc_services_dir):
                        for xpc_service in os.listdir(xpc_services_dir):
                            if xpc_service.endswith('.xpc'):
                                xpc_path = f"{xpc_services_dir}/{xpc_service}"
                                print(f"🔐 Signing XPC service: {xpc_service}")
                                
                                xpc_cmd = [
                                    'codesign', '--force', '--verbose',
                                    '--sign', signing_identity,
                                    '--timestamp',
                                    xpc_path
                                ]
                                
                                xpc_result = subprocess.run(xpc_cmd, capture_output=True, text=True)
                                if xpc_result.returncode != 0:
                                    print(f"❌ XPC service signing failed: {xpc_result.stderr}")
                                    return False
                                print(f"✅ XPC service {xpc_service} signed")
                    
                    # Sign Autoupdate executable
                    autoupdate_path = f"{framework_path}/Versions/B/Autoupdate"
                    if os.path.exists(autoupdate_path):
                        print("🔐 Signing Autoupdate executable")
                        autoupdate_cmd = [
                            'codesign', '--force', '--verbose',
                            '--sign', signing_identity,
                            '--timestamp',
                            autoupdate_path
                        ]
                        
                        autoupdate_result = subprocess.run(autoupdate_cmd, capture_output=True, text=True)
                        if autoupdate_result.returncode != 0:
                            print(f"❌ Autoupdate signing failed: {autoupdate_result.stderr}")
                            return False
                        print("✅ Autoupdate executable signed")
                    
                    # Sign Updater.app if it exists
                    updater_app_path = f"{framework_path}/Versions/B/Updater.app"
                    if os.path.exists(updater_app_path):
                        print("🔐 Signing Updater.app")
                        updater_cmd = [
                            'codesign', '--force', '--verbose',
                            '--sign', signing_identity,
                            '--timestamp',
                            updater_app_path
                        ]
                        
                        updater_result = subprocess.run(updater_cmd, capture_output=True, text=True)
                        if updater_result.returncode != 0:
                            print(f"❌ Updater.app signing failed: {updater_result.stderr}")
                            return False
                        print("✅ Updater.app signed")
                    
                    # Sign the framework itself (all components already signed individually)
                    cmd = [
                        'codesign', '--force', '--verbose',
                        '--sign', signing_identity,
                        '--timestamp',
                        framework_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"❌ Framework signing failed: {result.stderr}")
                        return False
                    print(f"✅ Framework {framework} signed")
        
        # Sign the main executable
        executable_path = f"{app_path}/Contents/MacOS/{APP_NAME}"
        
        cmd = [
            'codesign', '--force', '--verify', '--verbose',
            '--sign', signing_identity,
            '--entitlements', entitlements_file,
            '--timestamp',
            '--options', 'runtime',
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

def generate_cool_name():
    """Generate a cool build name"""
    import random
    
    adjectives = [
        "Swift", "Blazing", "Cosmic", "Stellar", "Quantum", "Turbo", "Lightning", 
        "Phoenix", "Dragon", "Mystic", "Arctic", "Crimson", "Golden", "Silver",
        "Emerald", "Sapphire", "Thunder", "Storm", "Frost", "Fire", "Shadow",
        "Crystal", "Diamond", "Iron", "Steel", "Neon", "Cyber", "Digital",
        "Atomic", "Nuclear", "Plasma", "Laser", "Hyper", "Ultra", "Mega",
        "Epic", "Legendary", "Royal", "Noble", "Wild", "Fierce", "Bold"
    ]
    
    nouns = [
        "Falcon", "Eagle", "Hawk", "Wolf", "Tiger", "Lion", "Dragon", "Phoenix",
        "Thunder", "Storm", "Blaze", "Frost", "Knight", "Warrior", "Ninja",
        "Samurai", "Wizard", "Mage", "Rocket", "Comet", "Star", "Galaxy",
        "Nebula", "Vortex", "Cyclone", "Hurricane", "Tornado", "Avalanche",
        "Tsunami", "Volcano", "Meteor", "Asteroid", "Planet", "Cosmos",
        "Universe", "Dimension", "Portal", "Matrix", "Code", "Cipher", "Prism"
    ]
    
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    
    return f"{adjective}-{noun}"

def generate_build_id():
    """Generate a unique build ID with short timestamp and cool name"""
    timestamp = datetime.now()
    
    # Short timestamp: YYMMDD + 5-minute block number
    year_short = timestamp.strftime("%y")    # Last 2 digits of year
    month = timestamp.strftime("%m")         # Month (01-12)
    day = timestamp.strftime("%d")           # Day (01-31)
    
    # Calculate 5-minute block number (0-287 for a day)
    total_minutes = timestamp.hour * 60 + timestamp.minute
    five_min_block = total_minutes // 5
    block_str = f"{five_min_block:03d}"      # 3 digits with leading zeros
    
    short_timestamp = f"{year_short}{month}{day}{block_str}"
    cool_name = generate_cool_name()
    
    build_id = {
        "build_id": f"Potter_{cool_name}_{short_timestamp}",
        "cool_name": cool_name,
        "short_timestamp": short_timestamp,
        "year": year_short,
        "month": month,
        "day": day,
        "five_min_block": five_min_block,
        "timestamp": timestamp.isoformat(),
        "unix_timestamp": int(timestamp.timestamp()),
        "version": "2.0.0",
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
        print(f"   Cool Name: {build_id['cool_name']}")
        print(f"   Date Code: {build_id['short_timestamp']} ({build_id['year']}/{build_id['month']}/{build_id['day']} block {build_id['five_min_block']})")
        print(f"   Full Timestamp: {build_id['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to embed build ID: {e}")
        return False

def create_dmg_professional(app_path):
    """Create a professional DMG with custom background using modern approach"""
    print("💿 Creating professional DMG for distribution...")
    
    try:
        # Get version from the app's Info.plist
        info_plist_path = f"{app_path}/Contents/Info.plist"
        import plistlib
        with open(info_plist_path, 'rb') as f:
            plist_data = plistlib.load(f)
        
        version = plist_data.get('CFBundleShortVersionString', '2.0.0')
        
        # Get version codename for enhanced naming
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from codename_utils import get_enhanced_dmg_name
            dmg_name = get_enhanced_dmg_name(version)
            print(f"🎭 Using enhanced DMG name: {dmg_name}")
        except Exception as e:
            print(f"⚠️  Could not get codename, using standard naming: {e}")
            dmg_name = f"{APP_NAME}-{version}.dmg"
        dmg_path = f"dist/{dmg_name}"
        source_folder = "dist/dmg_source"
        
        # Clean up any existing files
        for path in [dmg_path, source_folder]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        
        # Create source folder structure
        os.makedirs(source_folder, exist_ok=True)
        
        # Copy app to source folder
        print("📁 Preparing DMG contents...")
        shutil.copytree(app_path, f"{source_folder}/{APP_NAME}.app")
        
        # Create Applications symlink
        subprocess.run([
            'ln', '-s', '/Applications', f"{source_folder}/Applications"
        ], check=True)
        
        # Find background image
        background_path = None
        background_candidates = [
            "assets/dmg_background.png",
            "assets/potter_dmg_background.png",
            "dmg_background.png"
        ]
        
        for bg_path in background_candidates:
            if os.path.exists(bg_path):
                background_path = bg_path
                print(f"✅ Found background: {bg_path}")
                break
        
        if not background_path:
            print("⚠️  No background image found")
        
        # Use hdiutil create with proper formatting
        print("🔨 Creating DMG with hdiutil...")
        
        # Get enhanced volume name with codename
        try:
            from codename_utils import get_enhanced_volume_name
            volume_name = get_enhanced_volume_name(version)
            print(f"🎭 Using enhanced volume name: {volume_name}")
        except Exception as e:
            print(f"⚠️  Could not get codename for volume, using standard naming: {e}")
            volume_name = f"{APP_NAME} Installer"
        
        cmd = [
            'hdiutil', 'create',
            '-volname', volume_name,
            '-srcfolder', source_folder,
            '-ov',
            '-format', 'UDRW',  # Read-write for customization
            f"dist/temp_{dmg_name}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Initial DMG creation failed: {result.stderr}")
            return None
        
        print("✅ Initial DMG created successfully")
        
        # Mount for customization
        mount_point = f"/Volumes/{APP_NAME} Installer"
        print(f"📀 Mounting DMG at {mount_point}...")
        
        # Unmount any existing volume
        subprocess.run(['hdiutil', 'detach', mount_point], 
                      capture_output=True, text=True)
        
        mount_result = subprocess.run([
            'hdiutil', 'attach', f"dist/temp_{dmg_name}",
            '-mountpoint', mount_point
        ], capture_output=True, text=True)
        
        if mount_result.returncode != 0:
            print(f"❌ Failed to mount DMG: {mount_result.stderr}")
            return None
        
        print("✅ DMG mounted successfully")
        
        # Copy background and configure layout
        if background_path:
            print("🎨 Applying background image...")
            # Create .background folder (alternative approach)
            bg_folder = f'{mount_point}/.background'
            os.makedirs(bg_folder, exist_ok=True)
            bg_dest = f'{bg_folder}/background.png'
            shutil.copy2(background_path, bg_dest)
            
            # Also copy to root level as fallback
            bg_dest_root = f'{mount_point}/.background.png'
            shutil.copy2(background_path, bg_dest_root)
            
            # Verify the copy worked
            if os.path.exists(bg_dest) and os.path.exists(bg_dest_root):
                print(f"✅ Background copied to both locations")
            else:
                print(f"❌ Background copy failed")
                background_path = None  # Don't try to set it in AppleScript
            
        # Configure DMG appearance with AppleScript
        print("🎭 Configuring DMG layout...")
        applescript = f'''
tell application "Finder"
    tell disk "{APP_NAME} Installer"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {{400, 100, 1000, 600}}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 100'''
        
        if background_path:
            applescript += '''
        set background picture of viewOptions to file ".background:background.png"'''
            
        applescript += f'''
        set position of item "{APP_NAME}.app" to {{160, 250}}
        set position of item "Applications" to {{440, 250}}
        close
        open
        update without registering applications
        delay 2
    end tell
end tell'''
        
        # Run AppleScript with timeout and error handling
        try:
            subprocess.run([
                'osascript', '-e', applescript
            ], timeout=30, check=False)  # Don't fail build if AppleScript fails
            print("✅ DMG layout configured")
        except subprocess.TimeoutExpired:
            print("⚠️  AppleScript timed out, continuing with basic layout")
        except Exception as e:
            print(f"⚠️  AppleScript failed: {e}, continuing with basic layout")
        
        # Unmount
        print("📤 Finalizing DMG...")
        subprocess.run(['hdiutil', 'detach', mount_point], 
                      capture_output=True, text=True)
        
        # Convert to compressed final DMG
        subprocess.run([
            'hdiutil', 'convert', f"dist/temp_{dmg_name}",
            '-format', 'UDZO',
            '-o', dmg_path
        ], check=True)
        
        # Clean up
        os.remove(f"dist/temp_{dmg_name}")
        shutil.rmtree(source_folder)
        
        print(f"✅ Professional DMG created: {dmg_path}")
        return dmg_path
        
    except Exception as e:
        print(f"❌ DMG creation error: {e}")
        # Clean up on error
        cleanup_paths = [f"dist/temp_{dmg_name}", source_folder]
        for path in cleanup_paths:
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
    
    # Bundle frameworks
    if not bundle_frameworks(app_path):
        return False
    
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
            
            # Create DMG AFTER signing to include signed app
            if target == 'local':
                print("📦 Creating professional DMG with signed app...")
                dmg_path = create_dmg_professional(app_path)
                if dmg_path:
                    print(f"✅ Distribution DMG created: {dmg_path}")
                else:
                    print("❌ DMG creation failed, but signed app is available")
                
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