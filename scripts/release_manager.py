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

def update_appcast(version, dmg_path, release_notes, actual_dmg_name):
    """Update or create appcast.xml file"""
    print("📡 Updating appcast.xml...")
    
    # Ensure releases directory exists
    os.makedirs(RELEASES_DIR, exist_ok=True)
    
    appcast_path = f"{RELEASES_DIR}/appcast.xml"
    
    # Use the actual DMG filename passed in
    download_url = f"{GITHUB_REPO_URL}/releases/download/v{version}/{actual_dmg_name}"
    print(f"🎭 Using actual DMG filename for download URL: {actual_dmg_name}")
    
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
    """Create GitHub release using gh CLI in the potter repo"""
    print(f"🚀 Creating GitHub release v{version}...")
    
    potter_dir = "../potter"
    if not os.path.exists(potter_dir):
        print(f"❌ Potter repo not found at {potter_dir}")
        return False
    
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
        
        # Change to potter directory to create release there
        original_cwd = os.getcwd()
        os.chdir(potter_dir)
        
        # Create absolute path to DMG from potter repo perspective  
        dmg_absolute_path = os.path.abspath(os.path.join(original_cwd, dmg_path))
        
        # Create tag first
        print(f"🏷️  Creating tag v{version} in potter repo...")
        subprocess.run(['git', 'tag', f'v{version}'], check=False)  # Don't fail if tag exists
        subprocess.run(['git', 'push', 'origin', f'v{version}'], check=False)  # Don't fail if already pushed
        
        # Create release
        cmd = [
            'gh', 'release', 'create', f'v{version}',
            dmg_absolute_path,
            '--title', release_title,
            '--notes', release_notes
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Return to original directory
        os.chdir(original_cwd)
        
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

def prompt_git_push():
    """Prompt user to push commits to remote repositories (default: N)"""
    print("\n" + "=" * 60)
    print("🚀 PUSH TO REMOTE REPOSITORIES")
    print("=" * 60)
    print("This will push commits on master to remote for:")
    print("  • Potter (swift-potter repo)")
    print("  • Your blog (graydot.github.io repo)")
    print()
    
    try:
        response = input("Push commits to remote? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            print("📤 Pushing commits to remote repositories...")
            
            # Push potter repo (current directory)
            try:
                print("📤 Pushing Potter repo...")
                subprocess.run(['git', 'push'], check=True, cwd='.')
                subprocess.run(['git', 'push', '--tags'], check=True, cwd='.')
                print("✅ Potter repo pushed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to push Potter repo: {e}")
                return False
            
            return True
        else:
            print("⏭️  Skipping push to remote (user chose N)")
            return False
            
    except (EOFError, KeyboardInterrupt):
        print("\n⏭️  Skipping push to remote (interrupted)")
        return False

def update_potter_webpage(version):
    """Update the Potter webpage download link with the new version"""
    print("\n📱 Updating Potter webpage...")
    
    webpage_path = os.path.expanduser("~/Workspace/graydot.github.io/products/potter.html")
    blog_repo_path = os.path.expanduser("~/Workspace/graydot.github.io")
    
    # Check if webpage exists
    if not os.path.exists(webpage_path):
        print(f"⚠️  Potter webpage not found at {webpage_path}")
        return False
    
    # Check if blog repo exists
    if not os.path.exists(blog_repo_path):
        print(f"⚠️  Blog repo not found at {blog_repo_path}")
        return False
    
    try:
        # Read current webpage content
        with open(webpage_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update the download link to point to the latest release
        # Target the anchor with id="potter-download-link"
        
        # Get the enhanced DMG name for the download link
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from codename_utils import get_enhanced_dmg_name
            dmg_name = get_enhanced_dmg_name(version)
        except Exception:
            dmg_name = f"Potter-{version}.dmg"
        
        download_url = f"https://github.com/graydot/potter/releases/latest/download/{dmg_name}"
        
        # Replace the href attribute in the element with id="potter-download-link"
        # Handle different attribute orders with two patterns
        
        # Pattern 1: href before id (most common)
        pattern1 = r'(<a[^>]*href=")[^"]*("[^>]*id="potter-download-link")'
        replacement1 = f'\\1{download_url}\\2'
        
        # Pattern 2: id before href
        pattern2 = r'(<a[^>]*id="potter-download-link"[^>]*href=")[^"]*(")'
        replacement2 = f'\\1{download_url}\\2'
        
        # Try both patterns
        updated_content = re.sub(pattern1, replacement1, content)
        if updated_content == content:
            updated_content = re.sub(pattern2, replacement2, content)
        
        if updated_content == content:
            print("⚠️  No potter-download-link found to update in Potter webpage")
            return False
        
        # Write updated content
        with open(webpage_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Updated Potter webpage download link to {dmg_name}")
        
        # Commit and push the blog repo
        try:
            original_cwd = os.getcwd()
            os.chdir(blog_repo_path)
            
            # Add the changed file
            subprocess.run(['git', 'add', 'products/potter.html'], check=True)
            
            # Commit changes
            commit_msg = f"Update Potter download link to v{version}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push changes
            subprocess.run(['git', 'push'], check=True)
            
            print("✅ Potter webpage changes pushed to blog repo")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit/push blog changes: {e}")
            return False
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Failed to update Potter webpage: {e}")
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
        # Get current version's codename
        try:
            from codename_utils import get_codename_for_version
            current_codename = get_codename_for_version(current_version)
            print(f"📋 Current version: {current_version} - {current_codename}")
        except Exception:
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
    
    # Get new version's codename
    try:
        from codename_utils import get_codename_for_version
        new_codename = get_codename_for_version(new_version)
        print(f"🆕 New version: {new_version} - {new_codename}")
    except Exception:
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
    
    # Determine expected DMG name upfront
    try:
        from codename_utils import get_enhanced_dmg_name
        expected_dmg_name = get_enhanced_dmg_name(new_version)
        print(f"🎭 Expected DMG name: {expected_dmg_name}")
    except Exception as e:
        print(f"⚠️  Could not get enhanced DMG name, using standard naming: {e}")
        expected_dmg_name = f"{APP_NAME}-{new_version}.dmg"
    
    expected_dmg_path = f"dist/{expected_dmg_name}"
    
    # Build app
    if not args.skip_build:
        if not build_app():
            print("❌ Build failed, aborting release")
            sys.exit(1)
        
        # Delay to ensure DMG file is fully written and not locked
        import time
        time.sleep(3)
        print("⏳ Waiting for DMG file to be ready...")
        
        # Verify the expected DMG was created
        if not os.path.exists(expected_dmg_path):
            print(f"❌ Expected DMG not found: {expected_dmg_path}")
            sys.exit(1)
        
        dmg_path = expected_dmg_path
        actual_dmg_name = expected_dmg_name
    else:
        # Skip build - try to find existing DMG
        if os.path.exists(expected_dmg_path):
            dmg_path = expected_dmg_path
            actual_dmg_name = expected_dmg_name
            print(f"✅ Using existing DMG: {dmg_path}")
        else:
            # Try to find any DMG in dist directory
            import glob
            dmg_files = glob.glob("dist/*.dmg")
            if dmg_files:
                dmg_path = sorted(dmg_files)[-1]  # Use the most recent
                actual_dmg_name = os.path.basename(dmg_path)
                print(f"🔍 Found existing DMG: {dmg_path}")
                print(f"⚠️  Note: Using {actual_dmg_name} instead of expected {expected_dmg_name}")
            else:
                print(f"❌ No DMG file found in dist/ directory")
                print(f"   Expected: {expected_dmg_path}")
                sys.exit(1)
    
    print(f"📦 Using DMG: {dmg_path}")
    
    # Update appcast with actual DMG name
    appcast_path = update_appcast(new_version, dmg_path, release_notes, actual_dmg_name)
    
    # Copy appcast to potter repo and commit
    copy_appcast_to_potter_repo(new_version)
    
    # Create GitHub release
    if not args.skip_github:
        create_github_release(new_version, dmg_path, release_notes)
    
    # Commit changes
    commit_version_changes(new_version)
    
    # Prompt to push to remote
    push_to_remote = prompt_git_push()
    
    # If user chose not to push, abort the release
    if not push_to_remote:
        print("\n❌ Release process aborted!")
        print("=" * 50)
        print("🚨 Release was not completed because changes were not pushed to remote.")
        print("📋 To complete the release manually:")
        print("1. Push Potter repo: git push && git push --tags")
        print("2. Push blog repo changes (if any)")
        print("3. Verify the GitHub release was created")
        print("4. Update Potter webpage download link manually")
        sys.exit(1)
    
    # Update Potter webpage since we pushed to remote
    update_potter_webpage(new_version)
    
    print("\n🎉 Release process completed!")
    print("=" * 50)
    print(f"📋 Version: {new_version}")
    print(f"📦 DMG: {dmg_path}")
    print(f"📡 Appcast: {appcast_path}")
    print(f"🔗 Releases: {GITHUB_REPO_URL}/releases")
    print()
    print("📋 Next steps:")
    print("1. Test the DMG installation")
    print("2. ✅ Repositories pushed to remote")
    print("3. ✅ Potter webpage updated with new download link")
    print("4. Verify auto-update works with new appcast")

if __name__ == "__main__":
    main()