#!/usr/bin/env python3
"""
Potter Release Manager with Auto-Update Support
Handles version bumping, building, appcast generation, and GitHub releases
"""

import os
import sys
import subprocess
import json
import argparse
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import re

# Import our deterministic version manager
from version_manager import get_current_version, set_version, bump_version

# Configuration - Auto-detect from git remote
def get_repo_info():
    """Get repository info for appcast hosting (../potter repo)"""
    # Appcast is hosted in the separate potter repo
    return "graydot/potter"

REPO_NAME = get_repo_info()
GITHUB_REPO_URL = f"https://github.com/{REPO_NAME}"
RELEASES_DIR = "releases"  # Generate appcast locally first
APP_NAME = "Potter"

# Removed old messy version management - now using deterministic version_manager.py

def get_release_notes():
    """Get release notes from user input with codename theming"""
    # Get current codename for theming
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from codename_utils import get_current_codename
        codename = get_current_codename()
        print(f"\n🎭 This release codename: {codename}")
    except Exception as e:
        print(f"⚠️  Could not get codename: {e}")
        codename = "Unknown"
    
    print(f"\n📝 Enter release notes for '{codename}' (press Ctrl+D when done):")
    print("=" * 60)
    print(f"💡 Tip: Consider theming your notes around '{codename}' for consistency!")
    print("=" * 60)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    user_notes = "\n".join(lines).strip()
    
    # If user provided notes, enhance them with codename context
    if user_notes:
        enhanced_notes = f"## 🎭 {codename}\n\n{user_notes}"
        if codename.lower() not in user_notes.lower():
            enhanced_notes += f"\n\n*This release is codenamed **{codename}** - bringing AI-powered text processing with creative flair to macOS.*"
        return enhanced_notes
    else:
        # Provide a default template if no notes were provided
        return f"""## 🎭 {codename}

*{codename}* brings enhanced AI-powered text processing to macOS with improved performance and reliability.

### What's New
- Performance improvements and bug fixes
- Enhanced LLM integration
- Better error handling and user experience

*This release is codenamed **{codename}** - continuing Potter's tradition of elegant, powerful text processing.*"""

def build_app():
    """Build the app using the build script with proper signing for release"""
    print("🔨 Building signed Potter.app for release...")
    
    try:
        # Use make build which already has proper code signing configured
        result = subprocess.run([
            'make', 'build'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Signed build completed successfully")
            return True
        else:
            print(f"❌ Build failed with return code {result.returncode}")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def calculate_file_signature(file_path):
    """Calculate EdDSA signature using Sparkle's generate_appcast tool"""
    # Use Sparkle's generate_appcast tool to get proper EdDSA signature
    sparkle_tool = "swift-potter/.build/artifacts/sparkle/Sparkle/bin/generate_appcast"
    
    if not os.path.exists(sparkle_tool):
        raise FileNotFoundError(f"❌ Sparkle generate_appcast tool not found at {sparkle_tool}")
    
    # Create temporary directory with properly named DMG
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy DMG to temp directory with version in filename (required by Sparkle)
        import shutil
        from pathlib import Path
        
        # Extract version from filename or use default
        original_name = Path(file_path).stem
        version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', original_name)
        if version_match:
            version_str = version_match.group(1)
        else:
            raise ValueError(f"❌ Could not extract version from DMG filename: {original_name}")
        
        # Sparkle expects files like AppName-Version.dmg
        temp_dmg = os.path.join(temp_dir, f"Potter-{version_str}.dmg")
        shutil.copy2(file_path, temp_dmg)
        
        # Run generate_appcast on the temp directory
        result = subprocess.run([sparkle_tool, temp_dir], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"❌ generate_appcast failed with exit code {result.returncode}"
            if result.stdout:
                error_msg += f"\nSTDOUT: {result.stdout}"
            if result.stderr:
                error_msg += f"\nSTDERR: {result.stderr}"
            
            # Additional debugging info
            error_msg += f"\nTrying to process DMG: {file_path}"
            error_msg += f"\nTemp directory: {temp_dir}"
            error_msg += f"\nTemp DMG created: {temp_dmg}"
            error_msg += f"\nTemp DMG exists: {os.path.exists(temp_dmg)}"
            if os.path.exists(temp_dmg):
                error_msg += f"\nTemp DMG size: {os.path.getsize(temp_dmg)} bytes"
            
            print(error_msg)
            raise subprocess.CalledProcessError(result.returncode, [sparkle_tool, temp_dir], error_msg)
        
        # Parse the generated appcast to extract signature
        temp_appcast = os.path.join(temp_dir, "appcast.xml")
        if not os.path.exists(temp_appcast):
            raise FileNotFoundError(f"❌ generate_appcast did not create appcast.xml in {temp_dir}")
            
        tree = ET.parse(temp_appcast)
        root = tree.getroot()
        
        # Find the edSignature attribute
        for enclosure in root.findall(".//enclosure"):
            ed_sig = enclosure.get("{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature")
            if ed_sig:
                print(f"✅ Generated EdDSA signature: {ed_sig[:20]}...")
                return ed_sig
        
        raise ValueError("❌ No EdDSA signature found in generated appcast")

def get_file_size(file_path):
    """Get file size in bytes"""
    return os.path.getsize(file_path)

def create_appcast_entry(version, dmg_path, release_notes, download_url):
    """Create appcast entry for this version"""
    file_size = get_file_size(dmg_path)
    signature = calculate_file_signature(dmg_path)
    pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
    
    return {
        "version": version,
        "download_url": download_url,
        "file_size": file_size,
        "signature": signature,
        "pub_date": pub_date,
        "release_notes": release_notes
    }

def update_appcast(version, dmg_path, release_notes):
    """Update or create appcast.xml file"""
    print("📡 Updating appcast.xml...")
    
    # Ensure releases directory exists
    os.makedirs(RELEASES_DIR, exist_ok=True)
    
    appcast_path = f"{RELEASES_DIR}/appcast.xml"
    download_url = f"{GITHUB_REPO_URL}/releases/download/v{version}/{APP_NAME}-{version}.dmg"
    
    # Create new entry
    entry = create_appcast_entry(version, dmg_path, release_notes, download_url)
    
    # Load existing appcast or create new one
    if os.path.exists(appcast_path):
        tree = ET.parse(appcast_path)
        root = tree.getroot()
        channel = root.find('channel')
    else:
        # Create new appcast
        root = ET.Element('rss', version='2.0', attrib={
            'xmlns:sparkle': 'http://www.andymatuschak.org/xml-namespaces/sparkle',
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
        })
        
        channel = ET.SubElement(root, 'channel')
        ET.SubElement(channel, 'title').text = f"{APP_NAME} Updates"
        ET.SubElement(channel, 'description').text = f"Updates for {APP_NAME}"
        ET.SubElement(channel, 'language').text = "en"
        ET.SubElement(channel, 'link').text = GITHUB_REPO_URL
        
        tree = ET.ElementTree(root)
    
    # Add new item
    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = f"{APP_NAME} {version}"
    ET.SubElement(item, 'description').text = f"<![CDATA[{release_notes}]]>"
    ET.SubElement(item, 'pubDate').text = entry['pub_date']
    
    enclosure = ET.SubElement(item, 'enclosure')
    enclosure.set('url', entry['download_url'])
    enclosure.set('length', str(entry['file_size']))
    enclosure.set('type', 'application/octet-stream')
    enclosure.set('{http://www.andymatuschak.org/xml-namespaces/sparkle}version', version)
    enclosure.set('{http://www.andymatuschak.org/xml-namespaces/sparkle}shortVersionString', version)
    enclosure.set('{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature', entry['signature'])
    
    # Write appcast
    ET.indent(tree, space="  ", level=0)
    tree.write(appcast_path, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ Updated appcast: {appcast_path}")
    return appcast_path

def copy_appcast_to_potter_repo(version):
    """Copy appcast to ../potter repo and commit"""
    print("📡 Copying appcast to potter repo...")
    
    potter_dir = "../potter"
    if not os.path.exists(potter_dir):
        print(f"❌ Potter repo not found at {potter_dir}")
        return False
    
    try:
        # Copy appcast file
        local_appcast = f"{RELEASES_DIR}/appcast.xml"
        potter_releases_dir = f"{potter_dir}/releases"
        potter_appcast = f"{potter_releases_dir}/appcast.xml"
        
        # Ensure potter releases directory exists
        os.makedirs(potter_releases_dir, exist_ok=True)
        
        # Copy file
        import shutil
        shutil.copy2(local_appcast, potter_appcast)
        print(f"✅ Copied appcast to {potter_appcast}")
        
        # Change to potter directory
        original_cwd = os.getcwd()
        os.chdir(potter_dir)
        
        # Add appcast file
        subprocess.run(['git', 'add', 'releases/appcast.xml'], check=True)
        
        # Commit changes
        commit_msg = f"Update appcast for Potter {version}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Push changes
        subprocess.run(['git', 'push'], check=True)
        
        print(f"✅ Appcast changes pushed to potter repo")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Copy operation failed: {e}")
        return False
    finally:
        # Return to original directory
        os.chdir(original_cwd)

def create_github_release(version, dmg_path, release_notes):
    """Create GitHub release using gh CLI"""
    print(f"🚀 Creating GitHub release v{version}...")
    
    try:
        # Check if gh CLI is available
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
        
        # Get enhanced release title with codename
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from codename_utils import get_enhanced_release_title
            release_title = get_enhanced_release_title(version)
            print(f"🎭 Using enhanced release title: {release_title}")
        except Exception as e:
            print(f"⚠️  Could not get codename for release title, using standard naming: {e}")
            release_title = f'{APP_NAME} {version}'
        
        # Create release
        cmd = [
            'gh', 'release', 'create', f'v{version}',
            dmg_path,
            '--title', release_title,
            '--notes', release_notes
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ GitHub release created: {GITHUB_REPO_URL}/releases/tag/v{version}")
            return True
        else:
            stderr = result.stderr.strip()
            if "already exists" in stderr:
                print(f"⚠️  GitHub release v{version} already exists - skipping creation")
                print(f"🔗 Existing release: {GITHUB_REPO_URL}/releases/tag/v{version}")
                return True
            else:
                print(f"❌ GitHub release failed: {stderr}")
                return False
            
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI (gh) not found. Please install it to create releases automatically.")
        print(f"💡 Manual steps:")
        print(f"   1. Go to {GITHUB_REPO_URL}/releases/new")
        print(f"   2. Tag: v{version}")
        print(f"   3. Upload: {dmg_path}")
        print(f"   4. Release notes: {release_notes}")
        return False
    except Exception as e:
        print(f"❌ GitHub release error: {e}")
        return False

def commit_version_changes(version):
    """Commit version changes to git"""
    print("📝 Committing version changes...")
    
    try:
        # Add changed files (only local files, not appcast which is in ../potter)
        subprocess.run(['git', 'add', 
                       'scripts/build_app.py',
                       'swift-potter/Sources/Resources/Info.plist'],
                      check=True)
        
        # Commit
        commit_message = f"Release {version}"
        
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        print("✅ Version changes committed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git commit failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Potter Release Manager')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch'], 
                       default='patch', help='Version bump type')
    parser.add_argument('--version', help='Specific version to release')
    parser.add_argument('--notes', help='Release notes (or will prompt)')
    parser.add_argument('--skip-build', action='store_true', 
                       help='Skip building (use existing build)')
    parser.add_argument('--skip-github', action='store_true', 
                       help='Skip GitHub release creation')
    
    args = parser.parse_args()
    
    print("🎭 Potter Release Manager")
    print("=" * 50)
    
    # Get current version from authoritative source (Info.plist)
    try:
        current_version = get_current_version()
        print(f"📋 Current version: {current_version}")
    except Exception as e:
        print(f"❌ Could not read current version: {e}")
        sys.exit(1)
    
    # Determine new version
    if args.version:
        new_version = args.version
        # Validate format
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            print(f"❌ Invalid version format: {new_version}. Must be X.Y.Z")
            sys.exit(1)
    else:
        # Use bump type to determine version automatically
        try:
            suggested_version = bump_version(current_version, args.bump)
            print(f"💡 Suggested version ({args.bump} bump): {suggested_version}")
            
            # If running non-interactively (e.g., from make), use suggested version
            try:
                user_input = input(f"Enter version (press Enter for {suggested_version}): ").strip()
                if user_input:
                    new_version = user_input
                    # Validate format
                    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
                        print(f"❌ Invalid version format: {new_version}. Must be X.Y.Z")
                        sys.exit(1)
                else:
                    new_version = suggested_version
            except EOFError:
                # Non-interactive mode, use suggested version
                new_version = suggested_version
                print(f"Non-interactive mode: using {new_version}")
        except Exception as e:
            print(f"❌ Could not bump version: {e}")
            sys.exit(1)
    
    print(f"🆕 New version: {new_version}")
    
    # Get release notes
    if args.notes:
        release_notes = args.notes
    else:
        release_notes = get_release_notes()
    
    if not release_notes:
        print("❌ Release notes are required")
        sys.exit(1)
    
    # Update version in authoritative source
    try:
        set_version(new_version)
        print(f"✅ Version updated to {new_version}")
    except Exception as e:
        print(f"❌ Could not update version: {e}")
        sys.exit(1)
    
    # Build app
    if not args.skip_build:
        if not build_app():
            print("❌ Build failed, aborting release")
            sys.exit(1)
        
        # Delay to ensure DMG file is fully written and not locked
        import time
        time.sleep(3)
        print("⏳ Waiting for DMG file to be ready...")
    
    # Find DMG file
    dmg_path = f"dist/{APP_NAME}-{new_version}.dmg"
    if not os.path.exists(dmg_path):
        # Try current version DMG
        dmg_path = f"dist/{APP_NAME}-{current_version}.dmg"
        if not os.path.exists(dmg_path):
            # Try generic DMG name
            dmg_path = f"dist/{APP_NAME}-2.0.dmg"
            if not os.path.exists(dmg_path):
                print(f"❌ DMG file not found. Expected: dist/{APP_NAME}-{new_version}.dmg")
                sys.exit(1)
    
    print(f"📦 Using DMG: {dmg_path}")
    
    # Update appcast
    appcast_path = update_appcast(new_version, dmg_path, release_notes)
    
    # Copy appcast to potter repo and commit
    copy_appcast_to_potter_repo(new_version)
    
    # Create GitHub release
    if not args.skip_github:
        create_github_release(new_version, dmg_path, release_notes)
    
    # Commit changes
    commit_version_changes(new_version)
    
    print("\n🎉 Release process completed!")
    print("=" * 50)
    print(f"📋 Version: {new_version}")
    print(f"📦 DMG: {dmg_path}")
    print(f"📡 Appcast: {appcast_path}")
    print(f"🔗 Releases: {GITHUB_REPO_URL}/releases")
    print()
    print("📋 Next steps:")
    print("1. Test the DMG installation")
    print("2. Push changes to GitHub: git push && git push --tags")
    print("3. Verify auto-update works with new appcast")
    print("4. Update any external download links")

if __name__ == "__main__":
    main()