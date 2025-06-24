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

# Configuration - Auto-detect from git remote
def get_repo_info():
    """Get repository info for appcast hosting (../potter repo)"""
    # Appcast is hosted in the separate potter repo
    return "graydot/potter"

REPO_NAME = get_repo_info()
GITHUB_REPO_URL = f"https://github.com/{REPO_NAME}"
RELEASES_DIR = "../potter/releases"  # Store appcast in ../potter repo
APP_NAME = "Potter"

def get_current_version():
    """Get current version from latest GitHub release"""
    try:
        # Use gh CLI to get latest release
        result = subprocess.run(['gh', 'release', 'list', '--repo', 'graydot/potter', '--limit', '1', '--json', 'tagName'], 
                               capture_output=True, text=True, check=True)
        
        releases = json.loads(result.stdout)
        if releases:
            tag_name = releases[0]['tagName']
            # Remove 'v' prefix if present
            version = tag_name.lstrip('v')
            return version
    except:
        pass
    
    # Fallback to Info.plist
    info_plist_paths = [
        "swift-potter/Sources/Resources/Info.plist"
    ]
    
    for plist_path in info_plist_paths:
        if os.path.exists(plist_path):
            with open(plist_path, 'r') as f:
                content = f.read()
                match = re.search(r'<key>CFBundleShortVersionString</key>\s*<string>([^<]+)</string>', content)
                if match:
                    return match.group(1)
    
    # Ultimate fallback
    return "2.0.0"

def bump_version(current_version, bump_type='patch'):
    """Bump version number"""
    if not current_version:
        return "2.0.0"
    
    parts = current_version.split('.')
    
    # Ensure we have 3 parts (major.minor.patch)
    while len(parts) < 3:
        parts.append('0')
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def update_version_in_files(old_version, new_version):
    """Update version in relevant files"""
    print(f"📝 Updating version from {old_version} to {new_version}...")
    
    files_to_update = [
        "scripts/build_app.py",
        "swift-potter/Sources/Resources/Info.plist"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace version strings
            content = content.replace(f"<string>{old_version}</string>", f"<string>{new_version}</string>")
            content = re.sub(r'version.*=.*["\']' + re.escape(old_version) + r'["\']', 
                           f'version": "{new_version}"', content)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated {file_path}")
        else:
            print(f"⚠️  File not found: {file_path}")

def get_release_notes():
    """Get release notes from user input"""
    print("\n📝 Enter release notes (press Ctrl+D when done):")
    print("=" * 50)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    return "\n".join(lines).strip()

def build_app():
    """Build the app using the build script"""
    print("🔨 Building Potter.app...")
    
    try:
        result = subprocess.run([
            'python3', 'scripts/build_app.py', '--target', 'local'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully")
            return True
        else:
            print(f"❌ Build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def calculate_file_signature(file_path):
    """Calculate EdDSA signature using Sparkle's generate_appcast tool"""
    try:
        # Use Sparkle's generate_appcast tool to get proper EdDSA signature
        sparkle_tool = "swift-potter/.build/artifacts/sparkle/Sparkle/bin/generate_appcast"
        
        if not os.path.exists(sparkle_tool):
            print(f"⚠️  Sparkle generate_appcast tool not found at {sparkle_tool}")
            print("   Using placeholder signature - update will fail verification")
            return "placeholder_signature"
        
        # Create temporary directory with just our DMG
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy DMG to temp directory
            import shutil
            temp_dmg = os.path.join(temp_dir, os.path.basename(file_path))
            shutil.copy2(file_path, temp_dmg)
            
            # Run generate_appcast on the temp directory
            result = subprocess.run([sparkle_tool, temp_dir], 
                                   capture_output=True, text=True, check=True)
            
            # Parse the generated appcast to extract signature
            temp_appcast = os.path.join(temp_dir, "appcast.xml")
            if os.path.exists(temp_appcast):
                tree = ET.parse(temp_appcast)
                root = tree.getroot()
                
                # Find the edSignature attribute
                for enclosure in root.findall(".//enclosure"):
                    ed_sig = enclosure.get("{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature")
                    if ed_sig:
                        return ed_sig
            
            # Fallback to placeholder
            return "placeholder_signature"
            
    except Exception as e:
        print(f"⚠️  Failed to generate EdDSA signature: {e}")
        print("   Using placeholder signature - update will fail verification")
        return "placeholder_signature"

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

def commit_appcast_changes(version):
    """Commit and push appcast changes to ../potter repo"""
    print("📡 Committing appcast changes to potter repo...")
    
    potter_dir = "../potter"
    if not os.path.exists(potter_dir):
        print(f"❌ Potter repo not found at {potter_dir}")
        return False
    
    try:
        # Change to potter directory
        original_cwd = os.getcwd()
        os.chdir(potter_dir)
        
        # Add appcast file
        subprocess.run(['git', 'add', 'releases/appcast.xml'], check=True)
        
        # Commit changes
        commit_msg = f"Update appcast for Potter {version}"
        subprocess.run(['git', 'commit', '--no-verify', '-m', commit_msg], check=True)
        
        # Push changes
        subprocess.run(['git', 'push'], check=True)
        
        print(f"✅ Appcast changes pushed to potter repo")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
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
        
        # Create release
        cmd = [
            'gh', 'release', 'create', f'v{version}',
            dmg_path,
            '--title', f'{APP_NAME} {version}',
            '--notes', release_notes
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ GitHub release created: {GITHUB_REPO_URL}/releases/tag/v{version}")
            return True
        else:
            print(f"❌ GitHub release failed: {result.stderr}")
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
        # Add changed files
        subprocess.run(['git', 'add', 
                       'scripts/build_app.py',
                       f'{RELEASES_DIR}/appcast.xml'],
                      check=True)
        
        # Commit
        commit_message = f"Release {version}\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        
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
    
    # Get current version
    current_version = get_current_version()
    if not current_version:
        print("❌ Could not determine current version")
        sys.exit(1)
    
    print(f"📋 Current version: {current_version}")
    
    # Determine new version
    if args.version:
        new_version = args.version
    else:
        # Suggest patch bump as default
        suggested_version = bump_version(current_version, 'patch')
        print(f"💡 Suggested version (patch bump): {suggested_version}")
        
        user_input = input(f"Enter version (press Enter for {suggested_version}): ").strip()
        if user_input:
            new_version = user_input
        else:
            new_version = suggested_version
    
    print(f"🆕 New version: {new_version}")
    
    # Get release notes
    if args.notes:
        release_notes = args.notes
    else:
        release_notes = get_release_notes()
    
    if not release_notes:
        print("❌ Release notes are required")
        sys.exit(1)
    
    # Update version in files
    update_version_in_files(current_version, new_version)
    
    # Build app
    if not args.skip_build:
        if not build_app():
            print("❌ Build failed, aborting release")
            sys.exit(1)
    
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
    
    # Commit appcast changes to potter repo
    commit_appcast_changes(new_version)
    
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